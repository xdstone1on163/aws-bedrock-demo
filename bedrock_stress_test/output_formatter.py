"""
输出格式化器
美化终端输出，展示统计结果
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from models import Statistics, PerformanceMetrics
from model_configs import ModelConfig


class OutputFormatter:
    """输出格式化器"""

    def __init__(self):
        self.console = Console()

    def print_welcome(self, model_name: str = "DeepSeek V3"):
        """打印欢迎信息"""
        welcome_text = f"""
        AWS Bedrock 大模型性能测试工具

        测试模型: {model_name}
        测试区域: us-east-2
        """
        panel = Panel(welcome_text.strip(), title="欢迎", border_style="cyan")
        self.console.print(panel)

    def print_statistics(self, context_size: str, stats: Statistics):
        """
        打印统计结果表格

        Args:
            context_size: 上下文大小
            stats: Statistics对象
        """
        print(f"\n{'='*80}")
        print(f"统计结果: {context_size} 上下文")
        print(f"{'='*80}\n")

        # 创建TTFT表格
        ttft_table = Table(title=f"TTFT 统计 (Time To First Token)", show_header=True, header_style="bold magenta")
        ttft_table.add_column("指标", style="cyan", width=15)
        ttft_table.add_column("数值", style="green", width=20)

        ttft_table.add_row("平均值", f"{stats.mean_ttft_ms:.2f} ms")
        ttft_table.add_row("标准差", f"{stats.std_ttft_ms:.2f} ms")
        ttft_table.add_row("中位数 (P50)", f"{stats.median_ttft_ms:.2f} ms")
        ttft_table.add_row("P95", f"{stats.p95_ttft_ms:.2f} ms")
        ttft_table.add_row("P99", f"{stats.p99_ttft_ms:.2f} ms")
        ttft_table.add_row("最小值", f"{stats.min_ttft_ms:.2f} ms")
        ttft_table.add_row("最大值", f"{stats.max_ttft_ms:.2f} ms")

        self.console.print(ttft_table)
        print()

        # 创建吞吐量表格
        throughput_table = Table(title="吞吐量统计 (Tokens Per Second)", show_header=True, header_style="bold magenta")
        throughput_table.add_column("指标", style="cyan", width=15)
        throughput_table.add_column("数值", style="green", width=20)

        throughput_table.add_row("平均值", f"{stats.mean_throughput_tps:.2f} tps")
        throughput_table.add_row("标准差", f"{stats.std_throughput_tps:.2f} tps")
        throughput_table.add_row("中位数 (P50)", f"{stats.median_throughput_tps:.2f} tps")
        throughput_table.add_row("P95", f"{stats.p95_throughput_tps:.2f} tps")
        throughput_table.add_row("P99", f"{stats.p99_throughput_tps:.2f} tps")
        throughput_table.add_row("最小值", f"{stats.min_throughput_tps:.2f} tps")
        throughput_table.add_row("最大值", f"{stats.max_throughput_tps:.2f} tps")

        self.console.print(throughput_table)
        print()

        # 创建汇总信息表格
        summary_table = Table(title="测试汇总", show_header=True, header_style="bold magenta")
        summary_table.add_column("项目", style="cyan", width=20)
        summary_table.add_column("数值", style="green", width=20)

        summary_table.add_row("总测试次数", str(stats.total_tests))
        summary_table.add_row("成功次数", str(stats.total_tests - stats.failed_tests))
        summary_table.add_row("失败次数", str(stats.failed_tests))
        summary_table.add_row("成功率", f"{stats.success_rate:.2f}%")
        summary_table.add_row("总输入tokens", f"{stats.total_input_tokens:,}")
        summary_table.add_row("总输出tokens", f"{stats.total_output_tokens:,}")

        self.console.print(summary_table)
        print()

    def print_comparison_table(self, results_dict: dict):
        """
        打印多个上下文大小的对比表格

        Args:
            results_dict: {context_size: Statistics} 字典
        """
        print(f"\n{'='*80}")
        print("所有上下文大小对比")
        print(f"{'='*80}\n")

        # 创建对比表格
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("上下文大小", style="cyan", width=12)
        table.add_column("平均TTFT", style="green", width=12)
        table.add_column("P95 TTFT", style="green", width=12)
        table.add_column("平均吞吐量", style="yellow", width=15)
        table.add_column("P95吞吐量", style="yellow", width=15)
        table.add_column("成功率", style="blue", width=10)

        for context_size, stats in results_dict.items():
            table.add_row(
                context_size,
                f"{stats.mean_ttft_ms:.1f} ms",
                f"{stats.p95_ttft_ms:.1f} ms",
                f"{stats.mean_throughput_tps:.2f} tps",
                f"{stats.p95_throughput_tps:.2f} tps",
                f"{stats.success_rate:.1f}%"
            )

        self.console.print(table)
        print()

    def print_quick_result(self, metrics: PerformanceMetrics):
        """
        打印快速验证模式的结果

        Args:
            metrics: PerformanceMetrics对象
        """
        print(f"\n{'='*80}")
        print("快速验证结果")
        print(f"{'='*80}\n")

        if metrics.error_message:
            self.console.print(f"[bold red]❌ 测试失败:[/bold red] {metrics.error_message}")
            return

        # 性能指标
        perf_table = Table(show_header=True, header_style="bold magenta")
        perf_table.add_column("指标", style="cyan", width=20)
        perf_table.add_column("数值", style="green", width=30)

        perf_table.add_row("TTFT", f"{metrics.ttft_ms:.2f} ms")
        perf_table.add_row("总时长", f"{metrics.total_time_ms:.2f} ms")
        perf_table.add_row("输入tokens", f"{metrics.input_tokens:,}")
        perf_table.add_row("输出tokens", f"{metrics.output_tokens:,}")
        perf_table.add_row("吞吐量", f"{metrics.tokens_per_sec:.2f} tokens/sec")
        perf_table.add_row("平均每token耗时", f"{metrics.avg_ms_per_token:.2f} ms/token")
        perf_table.add_row("HTTP状态码", str(metrics.http_status_code))

        self.console.print(perf_table)
        print()

        # 响应内容
        if metrics.response_text:
            response_preview = metrics.response_text[:500]
            if len(metrics.response_text) > 500:
                response_preview += "... [已截断]"

            response_panel = Panel(
                response_preview,
                title="模型响应 (前500字符)",
                border_style="green"
            )
            self.console.print(response_panel)

    def print_error(self, message: str):
        """打印错误信息"""
        self.console.print(f"\n[bold red]❌ 错误:[/bold red] {message}\n")

    def print_info(self, message: str):
        """打印提示信息"""
        self.console.print(f"[bold blue]ℹ️  {message}[/bold blue]")

    def print_model_info(self, config: ModelConfig):
        """打印模型元信息"""
        table = Table(title="模型信息", show_header=True, header_style="bold magenta")
        table.add_column("项目", style="cyan", width=20)
        table.add_column("数值", style="green", width=40)

        table.add_row("模型名称", config.display_name)
        table.add_row("模型ID", config.model_id)
        table.add_row("提供商", config.provider)
        table.add_row("最大上下文", f"{config.max_context:,} tokens ({config.max_context // 1000}K)")

        self.console.print(table)
        print()

    def print_success(self, message: str):
        """打印成功信息"""
        self.console.print(f"[bold green]✓ {message}[/bold green]")
