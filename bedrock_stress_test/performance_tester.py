"""
性能测试器
执行多次测试并计算统计指标
"""
import time
import numpy as np
from typing import List
from tqdm import tqdm

from models import PerformanceMetrics, Statistics
from bedrock_client import BedrockClient
from context_builder import ContextBuilder


class PerformanceTester:
    """性能测试主逻辑"""

    def __init__(self, client: BedrockClient, system_prompt: str = "你是一个helpful助手。"):
        """
        初始化性能测试器

        Args:
            client: BedrockClient实例
            system_prompt: 系统提示词
        """
        self.client = client
        self.system_prompt = system_prompt

    def run_single_test(
        self,
        user_prompt: str,
        max_tokens: int = 2048,
        verbose: bool = True,
        delay_sec: int = 1
    ) -> PerformanceMetrics:
        """
        执行单次测试

        Args:
            user_prompt: 用户提示词（可以包含大上下文）
            max_tokens: 最大输出token数
            verbose: 是否显示详细日志
            delay_sec: 测试后延迟秒数（避免限流）

        Returns:
            PerformanceMetrics对象
        """
        call_start = time.perf_counter()

        metrics = self.client.invoke_with_timing(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            verbose=verbose,
            retain_response=False
        )

        # 自适应延迟：扣除 API 调用已消耗的时间
        call_duration = time.perf_counter() - call_start
        remaining_delay = delay_sec - call_duration
        if remaining_delay > 0:
            time.sleep(remaining_delay)

        return metrics

    def run_multiple_tests(
        self,
        context_size: str,
        iterations: int,
        max_tokens: int = 2048,
        verbose: bool = False,
        warmup: int = 1,
        delay_sec: int = 1
    ) -> List[PerformanceMetrics]:
        """
        执行多次测试

        Args:
            context_size: 上下文大小 (8K, 32K, 64K, 128K)
            iterations: 测试次数
            max_tokens: 最大输出token数
            verbose: 是否显示每次测试的详细日志
            warmup: 预热次数（不计入统计）
            delay_sec: 每次测试后延迟秒数

        Returns:
            PerformanceMetrics列表
        """
        print(f"\n{'='*80}")
        print(f"开始测试: {context_size} 上下文")
        print(f"测试次数: {iterations} 次 (预热: {warmup} 次)")
        print(f"{'='*80}\n")

        # 生成测试上下文
        context = ContextBuilder.get_specific_context(context_size)
        actual_tokens = ContextBuilder.estimate_tokens(context)
        print(f"[上下文] 大小: {context_size} (估算 {actual_tokens} tokens)")

        # 预热测试
        if warmup > 0:
            print(f"\n[预热] 开始 {warmup} 次预热测试...")
            for i in range(warmup):
                print(f"[预热] 第 {i+1}/{warmup} 次")
                self.run_single_test(
                    user_prompt=context,
                    max_tokens=max_tokens,
                    verbose=False,
                    delay_sec=delay_sec
                )
            print(f"[预热] 完成\n")

        # 正式测试
        results = []
        print(f"[测试] 开始 {iterations} 次性能测试...\n")

        for i in tqdm(range(iterations), desc=f"{context_size} 测试进度"):
            if verbose:
                print(f"\n--- 第 {i+1}/{iterations} 次测试 ---")

            metrics = self.run_single_test(
                user_prompt=context,
                max_tokens=max_tokens,
                verbose=verbose,
                delay_sec=delay_sec
            )

            results.append(metrics)

            # 简洁输出每次结果（非verbose模式）
            if not verbose:
                status = "✓" if metrics.error_message is None else "✗"
                print(f"  [{status}] 测试 {i+1}: TTFT={metrics.ttft_ms:.0f}ms | "
                      f"吞吐量={metrics.tokens_per_sec:.1f} tps | "
                      f"输出={metrics.output_tokens} tokens")

        print(f"\n[测试] 完成 {iterations} 次测试")
        return results

    @staticmethod
    def calculate_statistics(results: List[PerformanceMetrics]) -> Statistics:
        """
        计算统计指标

        Args:
            results: PerformanceMetrics列表

        Returns:
            Statistics对象
        """
        # 过滤掉失败的测试
        successful_results = [r for r in results if r.error_message is None]

        if not successful_results:
            raise ValueError("没有成功的测试结果，无法计算统计指标")

        # 提取指标
        ttft_values = np.array([r.ttft_ms for r in successful_results])
        throughput_values = np.array([r.tokens_per_sec for r in successful_results])

        # 计算统计值
        return Statistics(
            # TTFT统计
            mean_ttft_ms=float(np.mean(ttft_values)),
            std_ttft_ms=float(np.std(ttft_values)),
            median_ttft_ms=float(np.median(ttft_values)),
            p95_ttft_ms=float(np.percentile(ttft_values, 95)),
            p99_ttft_ms=float(np.percentile(ttft_values, 99)),
            min_ttft_ms=float(np.min(ttft_values)),
            max_ttft_ms=float(np.max(ttft_values)),

            # 吞吐量统计
            mean_throughput_tps=float(np.mean(throughput_values)),
            std_throughput_tps=float(np.std(throughput_values)),
            median_throughput_tps=float(np.median(throughput_values)),
            p95_throughput_tps=float(np.percentile(throughput_values, 95)),
            p99_throughput_tps=float(np.percentile(throughput_values, 99)),
            min_throughput_tps=float(np.min(throughput_values)),
            max_throughput_tps=float(np.max(throughput_values)),

            # 其他统计
            total_input_tokens=sum(r.input_tokens for r in successful_results),
            total_output_tokens=sum(r.output_tokens for r in successful_results),
            total_tests=len(results),
            failed_tests=len(results) - len(successful_results),
            success_rate=len(successful_results) / len(results) * 100
        )
