"""
数据模型定义
包含性能指标和统计数据的数据类
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PerformanceMetrics:
    """单次测试的性能指标"""
    ttft_ms: float              # Time to first token (毫秒)
    total_time_ms: float        # 总响应时间
    input_tokens: int           # 输入token数（从API返回）
    output_tokens: int          # 输出token数
    tokens_per_sec: float       # 吞吐量 (tokens/sec)
    avg_ms_per_token: float     # 平均每token耗时
    response_text: str          # 完整响应文本
    http_status_code: int       # HTTP响应状态码
    error_message: Optional[str] = None  # 错误信息（如果有）


@dataclass
class Statistics:
    """多次测试的统计指标"""
    # TTFT统计
    mean_ttft_ms: float
    std_ttft_ms: float
    median_ttft_ms: float
    p95_ttft_ms: float
    p99_ttft_ms: float
    min_ttft_ms: float
    max_ttft_ms: float

    # 吞吐量统计
    mean_throughput_tps: float
    std_throughput_tps: float
    median_throughput_tps: float
    p95_throughput_tps: float
    p99_throughput_tps: float
    min_throughput_tps: float
    max_throughput_tps: float

    # 其他统计
    total_input_tokens: int
    total_output_tokens: int
    total_tests: int
    failed_tests: int
    success_rate: float
