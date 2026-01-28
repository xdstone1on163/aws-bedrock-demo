"""
AWS Bedrock客户端封装
负责管理Bedrock连接和API调用，测量性能指标
"""
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Tuple, Optional
from models import PerformanceMetrics


class BedrockClient:
    """Bedrock API客户端封装类"""

    def __init__(self, region: str = "us-east-2", model_id: str = "deepseek.v3-v1:0"):
        """
        初始化Bedrock客户端

        Args:
            region: AWS区域
            model_id: 模型ID
        """
        self.region = region
        self.model_id = model_id

        # 配置更长的超时时间，适应大上下文场景
        config = Config(
            region_name=region,
            read_timeout=300,  # 5分钟超时
            connect_timeout=10,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )

        self.client = boto3.client('bedrock-runtime', config=config)

    def verify_credentials(self) -> Tuple[bool, str]:
        """
        验证AWS凭证和模型可用性

        Returns:
            (是否成功, 消息)
        """
        try:
            # 验证AWS凭证
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            account_id = identity['Account']

            print(f"[验证] AWS账户: {account_id}")
            print(f"[验证] 模型ID: {self.model_id}")
            print(f"[验证] 区域: {self.region}")

            return True, "凭证验证成功"

        except ClientError as e:
            error_msg = f"AWS凭证验证失败: {e.response['Error']['Message']}"
            return False, error_msg
        except Exception as e:
            return False, f"验证失败: {str(e)}"

    def invoke_with_timing(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        verbose: bool = True
    ) -> PerformanceMetrics:
        """
        调用模型并测量性能指标

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            max_tokens: 最大输出token数
            temperature: 温度参数
            verbose: 是否显示详细日志

        Returns:
            PerformanceMetrics对象
        """
        if verbose:
            self._print_request_info(system_prompt, user_prompt, max_tokens, temperature)

        try:
            # 准备请求参数
            messages = [
                {
                    "role": "user",
                    "content": [{"text": user_prompt}]
                }
            ]

            # 如果有system prompt，添加到消息中
            system_list = []
            if system_prompt:
                system_list = [{"text": system_prompt}]

            # 开始计时
            t_start = time.perf_counter()

            # 调用流式API
            response = self.client.converse_stream(
                modelId=self.model_id,
                messages=messages,
                system=system_list if system_list else None,
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            )

            if verbose:
                print(f"[响应] HTTP状态码: 200 OK")
                print(f"[响应] 开始接收流式响应...")

            # 处理流式响应
            ttft_ms = None
            first_token_received = False
            response_text = ""
            output_tokens = 0
            input_tokens = 0
            request_id = None

            for event in response['stream']:
                # 捕获第一个token的时间（TTFT）
                if 'contentBlockDelta' in event and not first_token_received:
                    ttft_ms = (time.perf_counter() - t_start) * 1000
                    first_token_received = True
                    if verbose:
                        print(f"[响应] 第一个token已接收 (TTFT: {ttft_ms:.2f}ms)")

                # 累积响应文本
                if 'contentBlockDelta' in event:
                    delta = event['contentBlockDelta'].get('delta', {})
                    if 'text' in delta:
                        response_text += delta['text']

                # 提取token使用量和请求ID
                if 'metadata' in event:
                    metadata = event['metadata']
                    usage = metadata.get('usage', {})
                    input_tokens = usage.get('inputTokens', 0)
                    output_tokens = usage.get('outputTokens', 0)

                if 'messageStop' in event or 'metadata' in event:
                    # 从响应元数据中提取request_id（如果可用）
                    pass

            # 计算总时间
            total_time_ms = (time.perf_counter() - t_start) * 1000

            if verbose:
                print(f"[响应] 流式响应完成")

            # 计算性能指标
            if ttft_ms is None:
                ttft_ms = total_time_ms  # 如果没有捕获到第一个token，使用总时间

            generation_time_ms = total_time_ms - ttft_ms
            tokens_per_sec = output_tokens / (generation_time_ms / 1000) if generation_time_ms > 0 else 0
            avg_ms_per_token = generation_time_ms / output_tokens if output_tokens > 0 else 0

            if verbose:
                self._print_completion_info(input_tokens, output_tokens, ttft_ms, tokens_per_sec)

            return PerformanceMetrics(
                ttft_ms=ttft_ms,
                total_time_ms=total_time_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tokens_per_sec=tokens_per_sec,
                avg_ms_per_token=avg_ms_per_token,
                response_text=response_text,
                http_status_code=200,
                request_id=request_id
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            http_status = e.response['ResponseMetadata']['HTTPStatusCode']
            error_message = e.response['Error']['Message']

            if verbose:
                print(f"[错误] HTTP状态码: {http_status}")
                print(f"[错误] 错误代码: {error_code}")
                print(f"[错误] 错误信息: {error_message}")

            # 返回错误指标
            return PerformanceMetrics(
                ttft_ms=0,
                total_time_ms=0,
                input_tokens=0,
                output_tokens=0,
                tokens_per_sec=0,
                avg_ms_per_token=0,
                response_text="",
                http_status_code=http_status,
                request_id=None,
                error_message=f"{error_code}: {error_message}"
            )

        except Exception as e:
            if verbose:
                print(f"[错误] 未知错误: {str(e)}")

            return PerformanceMetrics(
                ttft_ms=0,
                total_time_ms=0,
                input_tokens=0,
                output_tokens=0,
                tokens_per_sec=0,
                avg_ms_per_token=0,
                response_text="",
                http_status_code=500,
                request_id=None,
                error_message=str(e)
            )

    def _print_request_info(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float):
        """打印请求信息"""
        print("=" * 80)
        print(f"[请求] 模型: {self.model_id}")
        print(f"[请求] 区域: {self.region}")

        # System prompt
        if system_prompt:
            if len(system_prompt) > 100:
                print(f"[请求] System Prompt: {system_prompt[:100]}...")
            else:
                print(f"[请求] System Prompt: {system_prompt}")

        # User prompt - 处理超长输入
        input_tokens_estimate = len(user_prompt) // 4
        if input_tokens_estimate > 1000:
            print(f"[请求] User Prompt: [过长，已省略] (估算 {input_tokens_estimate} tokens)")
            print(f"[请求] User Prompt摘要: {user_prompt[:200]}... [截断]")
        else:
            print(f"[请求] User Prompt: {user_prompt}")

        print(f"[请求] 配置: maxTokens={max_tokens}, temperature={temperature}")

    def _print_completion_info(self, input_tokens: int, output_tokens: int, ttft_ms: float, tokens_per_sec: float):
        """打印完成信息"""
        print(f"[完成] 输入tokens: {input_tokens}")
        print(f"[完成] 输出tokens: {output_tokens}")
        print(f"[完成] TTFT: {ttft_ms:.2f}ms")
        print(f"[完成] 吞吐量: {tokens_per_sec:.2f} tokens/sec")
        print("=" * 80)
