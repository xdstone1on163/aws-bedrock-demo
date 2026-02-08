"""models.py 单元测试"""
import pytest
from models import PerformanceMetrics, Statistics


class TestPerformanceMetrics:
    def test_creation_with_defaults(self):
        m = PerformanceMetrics(
            ttft_ms=100.0, total_time_ms=500.0, input_tokens=10,
            output_tokens=20, tokens_per_sec=50.0, avg_ms_per_token=20.0,
            response_text="hello", http_status_code=200
        )
        assert m.ttft_ms == 100.0
        assert m.error_message is None

    def test_creation_with_error(self):
        m = PerformanceMetrics(
            ttft_ms=0, total_time_ms=0, input_tokens=0,
            output_tokens=0, tokens_per_sec=0, avg_ms_per_token=0,
            response_text="", http_status_code=429,
            error_message="ThrottlingException"
        )
        assert m.error_message == "ThrottlingException"
        assert m.http_status_code == 429


class TestStatistics:
    def test_creation(self):
        s = Statistics(
            mean_ttft_ms=100.0, std_ttft_ms=10.0, median_ttft_ms=95.0,
            p95_ttft_ms=120.0, p99_ttft_ms=130.0, min_ttft_ms=80.0, max_ttft_ms=140.0,
            mean_throughput_tps=50.0, std_throughput_tps=5.0, median_throughput_tps=48.0,
            p95_throughput_tps=60.0, p99_throughput_tps=65.0,
            min_throughput_tps=40.0, max_throughput_tps=70.0,
            total_input_tokens=1000, total_output_tokens=500,
            total_tests=10, failed_tests=1, success_rate=90.0
        )
        assert s.total_tests == 10
        assert s.success_rate == 90.0
