"""performance_tester.py 的 calculate_statistics 单元测试"""
import pytest
from models import PerformanceMetrics, Statistics
from performance_tester import PerformanceTester


def _make_metrics(ttft_ms=100.0, total_time_ms=500.0, output_tokens=20,
                  tokens_per_sec=50.0, error_message=None):
    return PerformanceMetrics(
        ttft_ms=ttft_ms, total_time_ms=total_time_ms, input_tokens=10,
        output_tokens=output_tokens, tokens_per_sec=tokens_per_sec,
        avg_ms_per_token=20.0, response_text="", http_status_code=200,
        error_message=error_message
    )


class TestCalculateStatistics:
    def test_basic_stats(self):
        results = [
            _make_metrics(ttft_ms=100, tokens_per_sec=50),
            _make_metrics(ttft_ms=200, tokens_per_sec=40),
            _make_metrics(ttft_ms=150, tokens_per_sec=45),
        ]
        stats = PerformanceTester.calculate_statistics(results)
        assert stats.total_tests == 3
        assert stats.failed_tests == 0
        assert stats.success_rate == 100.0
        assert stats.mean_ttft_ms == pytest.approx(150.0)
        assert stats.min_ttft_ms == 100.0
        assert stats.max_ttft_ms == 200.0

    def test_filters_failed_results(self):
        results = [
            _make_metrics(ttft_ms=100, tokens_per_sec=50),
            _make_metrics(error_message="ThrottlingException"),
            _make_metrics(ttft_ms=200, tokens_per_sec=40),
        ]
        stats = PerformanceTester.calculate_statistics(results)
        assert stats.total_tests == 3
        assert stats.failed_tests == 1
        assert stats.success_rate == pytest.approx(66.666, rel=0.01)

    def test_all_failed_raises(self):
        results = [
            _make_metrics(error_message="Error1"),
            _make_metrics(error_message="Error2"),
        ]
        with pytest.raises(ValueError, match="没有成功的测试结果"):
            PerformanceTester.calculate_statistics(results)

    def test_single_result(self):
        results = [_make_metrics(ttft_ms=100, tokens_per_sec=50)]
        stats = PerformanceTester.calculate_statistics(results)
        assert stats.total_tests == 1
        assert stats.mean_ttft_ms == 100.0
        assert stats.std_ttft_ms == 0.0
