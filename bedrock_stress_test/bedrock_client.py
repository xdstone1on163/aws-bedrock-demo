"""
AWS Bedrock客户端封装
负责管理Bedrock连接和API调用，测量性能指标
"""
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Tuple
from models import PerformanceMetrics

# 应用层重试配置
APP_RETRY_MAX_ATTEMPTS = 3
APP_RETRY_BASE_DELAY = 1.0  # 秒


class BedrockClient:
    """Bedrock API客户端封装类"""

    def __init__(self, region: str = "us-east-2", model_id: str = "deepseek.v3-v1:0",
                 boto3_client=None):
        """
        初始化Bedrock客户端

        Args:
            region: AWS区域
            model_id: 模型ID
            boto3_client: 可选的 boto3 client 实例（用于测试时依赖注入）
        """
        self.region = region
        self.model_id = model_id

        if boto3_client is not None:
            self.client = boto3_client
        else:
            # 禁用 SDK 级重试，改为应用层重试以避免重试延迟污染 TTFT 测量
            config = Config(
                region_name=region,
                read_timeout=300,  # 5分钟超时
                connect_timeout=10,
                retries={'max_attempts': 1, 'mode': 'standard'}
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

            masked_id = f"****{account_id[-4:]}" if len(account_id) >= 4 else "****"
            print(f"[验证] AWS账户: {masked_id}")
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
        verbose: bool = True,
        retain_response: bool = True
    ) -> PerformanceMetrics:
        """
        调用模型并测量性能指标，带应用层重试

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            max_tokens: 最大输出token数
            temperature: 温度参数
            verbose: 是否显示详细日志
            retain_response: 是否保留完整响应文本（performance 模式可关闭以节省内存）

        Returns:
            PerformanceMetrics对象
        """
        if verbose:
            self._print_request_info(system_prompt, user_prompt, max_tokens, temperature)

        messages = [
            {
                "role": "user",
                "content": [{"text": user_prompt}]
            }
        ]

        system_list = [{"text": system_prompt}] if system_prompt else []

        last_error = None
        for attempt in range(APP_RETRY_MAX_ATTEMPTS):
            try:
                # 每次重试都重新计时，确保 TTFT 不被重试延迟污染
                t_start = time.perf_counter()

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
                    if attempt > 0:
                        print(f"[响应] 第 {attempt + 1} 次尝试成功")
                    print(f"[响应] HTTP状态码: 200 OK")
                    print(f"[响应] 开始接收流式响应...")

                # 处理流式响应
                ttft_ms = None
                first_token_received = False
                response_text = ""
                output_tokens = 0
                input_tokens = 0

                try:
                    for event in response['stream']:
                        if 'contentBlockDelta' in event and not first_token_received:
                            ttft_ms = (time.perf_counter() - t_start) * 1000
                            first_token_received = True
                            if verbose:
                                print(f"[响应] 第一个token已接收 (TTFT: {ttft_ms:.2f}ms)")

                        if 'contentBlockDelta' in event:
                            delta = event['contentBlockDelta'].get('delta', {})
                            if 'text' in delta:
                                if retain_response:
                                    response_text += delta['text']

                        if 'metadata' in event:
                            metadata = event['metadata']
                            usage = metadata.get('usage', {})
                            input_tokens = usage.get('inputTokens', 0)
                            output_tokens = usage.get('outputTokens', 0)
                finally:
                    # 确保流在异常路径也被关闭
                    stream = response.get('stream')
                    if hasattr(stream, 'close'):
                        stream.close()

                total_time_ms = (time.perf_counter() - t_start) * 1000

                if verbose:
                    print(f"[响应] 流式响应完成")

                if ttft_ms is None:
                    ttft_ms = total_time_ms

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
                )

            except ClientError as e:
                error_code = e.response['Error']['Code']
                http_status = e.response['ResponseMetadata']['HTTPStatusCode']
                error_message = e.response['Error']['Message']
                last_error = e

                # 可重试的错误码：限流、服务端错误
                retryable = error_code in ('ThrottlingException', 'ServiceUnavailableException',
                                           'ModelTimeoutException') or http_status >= 500

                if retryable and attempt < APP_RETRY_MAX_ATTEMPTS - 1:
                    delay = APP_RETRY_BASE_DELAY * (2 ** attempt)
                    if verbose:
                        print(f"[重试] {error_code} (HTTP {http_status})，{delay:.1f}s 后重试...")
                    time.sleep(delay)
                    continue

                if verbose:
                    print(f"[错误] HTTP状态码: {http_status}")
                    print(f"[错误] 错误代码: {error_code}")
                    print(f"[错误] 错误信息: {error_message}")

                return PerformanceMetrics(
                    ttft_ms=0,
                    total_time_ms=0,
                    input_tokens=0,
                    output_tokens=0,
                    tokens_per_sec=0,
                    avg_ms_per_token=0,
                    response_text="",
                    http_status_code=http_status,
                    error_message=f"{error_code}: {error_message}"
                )

            except Exception as e:
                last_error = e
                if attempt < APP_RETRY_MAX_ATTEMPTS - 1:
                    delay = APP_RETRY_BASE_DELAY * (2 ** attempt)
                    if verbose:
                        print(f"[重试] {type(e).__name__}: {e}，{delay:.1f}s 后重试...")
                    time.sleep(delay)
                    continue

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
                    error_message=str(e)
                )

        # 不应到达这里，但作为安全兜底
        return PerformanceMetrics(
            ttft_ms=0, total_time_ms=0, input_tokens=0, output_tokens=0,
            tokens_per_sec=0, avg_ms_per_token=0, response_text="",
            http_status_code=500,
            error_message=f"重试 {APP_RETRY_MAX_ATTEMPTS} 次后仍失败: {last_error}"
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
