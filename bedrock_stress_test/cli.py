#!/usr/bin/env python3
"""
AWS Bedrock DeepSeek V3 性能测试工具 - 命令行入口

用法:
    快速验证模式:
        python cli.py --mode quick --system "你是助手" --user "你好"
        python cli.py --mode quick  # 交互式输入

    性能测试模式:
        python cli.py --mode performance --iterations 10
        python cli.py --mode performance --iterations 5 --context-sizes 8K,32K
"""
import argparse
import sys
from typing import List

from bedrock_client import BedrockClient
from performance_tester import PerformanceTester
from output_formatter import OutputFormatter
from model_configs import get_model_config, MODELS


def quick_mode(args):
    """快速验证模式"""
    formatter = OutputFormatter()

    # 解析模型配置
    if args.model_id:
        # 用户提供了自定义model_id，使用它
        model_id = args.model_id
        model_display_name = args.model_id
    elif args.model:
        # 用户选择了预定义模型
        config = get_model_config(args.model)
        model_id = config.model_id
        model_display_name = config.display_name
    else:
        # 默认使用DeepSeek
        config = get_model_config("deepseek")
        model_id = config.model_id
        model_display_name = config.display_name

    formatter.print_welcome(model_display_name)

    # 获取system prompt和user prompt
    if args.system and args.user:
        system_prompt = args.system
        user_prompt = args.user
    else:
        # 交互式输入
        print("\n请输入测试参数:\n")
        system_prompt = input("System Prompt (回车使用默认): ").strip()
        if not system_prompt:
            system_prompt = "你是一个helpful助手。"

        user_prompt = input("User Prompt: ").strip()
        if not user_prompt:
            formatter.print_error("User Prompt不能为空")
            sys.exit(1)

    # 创建客户端
    client = BedrockClient(region=args.region, model_id=model_id)

    # 验证凭证
    success, message = client.verify_credentials()
    if not success:
        formatter.print_error(message)
        sys.exit(1)

    formatter.print_success(message)

    # 执行测试
    print("\n开始快速验证测试...\n")
    metrics = client.invoke_with_timing(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=args.max_tokens,
        verbose=True
    )

    # 显示结果
    formatter.print_quick_result(metrics)

    if metrics.error_message:
        sys.exit(1)


def performance_mode(args):
    """性能测试模式"""
    formatter = OutputFormatter()

    # 解析模型配置
    if args.model_id:
        # 用户提供了自定义model_id，使用它
        model_id = args.model_id
        model_display_name = args.model_id
    elif args.model:
        # 用户选择了预定义模型
        config = get_model_config(args.model)
        model_id = config.model_id
        model_display_name = config.display_name
    else:
        # 默认使用DeepSeek
        config = get_model_config("deepseek")
        model_id = config.model_id
        model_display_name = config.display_name

    formatter.print_welcome(model_display_name)

    # 创建客户端
    client = BedrockClient(region=args.region, model_id=model_id)

    # 验证凭证
    success, message = client.verify_credentials()
    if not success:
        formatter.print_error(message)
        sys.exit(1)

    formatter.print_success(message)

    # 解析要测试的上下文大小
    if args.context_sizes:
        context_sizes = [s.strip() for s in args.context_sizes.split(',')]
    else:
        context_sizes = ["8K", "32K", "64K", "128K"]

    # 验证上下文大小
    valid_sizes = ["8K", "32K", "64K", "128K", "256K", "360K"]
    for size in context_sizes:
        if size not in valid_sizes:
            formatter.print_error(f"无效的上下文大小: {size}. 支持的大小: {', '.join(valid_sizes)}")
            sys.exit(1)

    # 成本估算提示
    total_tests = len(context_sizes) * args.iterations
    if args.warmup:
        total_tests += len(context_sizes) * args.warmup

    print(f"\n[提示] 本次测试将执行:")
    print(f"  - 上下文大小: {', '.join(context_sizes)}")
    print(f"  - 每个大小测试次数: {args.iterations} 次")
    if args.warmup:
        print(f"  - 预热次数: {args.warmup} 次")
    print(f"  - 总API调用次数: {total_tests} 次")
    print(f"  - 预计耗时: 根据网络和模型响应时间而定\n")

    if not args.yes:
        confirm = input("是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            sys.exit(0)

    # 创建性能测试器
    tester = PerformanceTester(
        client=client,
        system_prompt=args.system_prompt
    )

    # 执行测试
    all_results = {}

    for context_size in context_sizes:
        try:
            # 运行多次测试
            results = tester.run_multiple_tests(
                context_size=context_size,
                iterations=args.iterations,
                max_tokens=args.max_tokens,
                verbose=args.verbose,
                warmup=args.warmup,
                delay_sec=args.delay
            )

            # 计算统计指标
            stats = PerformanceTester.calculate_statistics(results)
            all_results[context_size] = stats

            # 显示统计结果
            formatter.print_statistics(context_size, stats)

        except Exception as e:
            formatter.print_error(f"测试 {context_size} 时发生错误: {str(e)}")
            continue

    # 如果测试了多个上下文大小，显示对比表格
    if len(all_results) > 1:
        formatter.print_comparison_table(all_results)

    formatter.print_success("所有测试完成!")


def main():
    parser = argparse.ArgumentParser(
        description="AWS Bedrock DeepSeek V3 性能测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  快速验证:
    %(prog)s --mode quick --model deepseek --system "你是助手" --user "你好"
    %(prog)s --mode quick --model minimax --system "你是助手" --user "你好"

  性能测试:
    %(prog)s --mode performance --model deepseek --iterations 10
    %(prog)s --mode performance --model minimax --iterations 5 --context-sizes 8K,32K

  自定义模型ID:
    %(prog)s --mode quick --model-id "custom.model-id" --user "测试"
        """
    )

    # 基本参数
    parser.add_argument(
        "--mode",
        type=str,
        choices=["quick", "performance"],
        required=True,
        help="运行模式: quick(快速验证) 或 performance(性能测试)"
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-2",
        help="AWS区域 (默认: us-east-2)"
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=list(MODELS.keys()),
        help=f"选择模型 (可选: {', '.join(MODELS.keys())})"
    )

    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help="自定义模型ID（高级选项，会覆盖--model）"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="最大输出token数 (默认: 2048)"
    )

    # Quick模式参数
    parser.add_argument(
        "--system",
        type=str,
        help="System prompt (仅用于quick模式)"
    )

    parser.add_argument(
        "--user",
        type=str,
        help="User prompt (仅用于quick模式)"
    )

    # Performance模式参数
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="每个上下文大小的测试次数 (默认: 10)"
    )

    parser.add_argument(
        "--context-sizes",
        type=str,
        help="要测试的上下文大小，逗号分隔 (例如: 8K,32K,64K,128K) (默认: 全部)"
    )

    parser.add_argument(
        "--system-prompt",
        type=str,
        default="你是一个helpful助手。",
        help="性能测试使用的system prompt (默认: '你是一个helpful助手。')"
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="每个上下文大小的预热次数 (默认: 1)"
    )

    parser.add_argument(
        "--delay",
        type=int,
        default=1,
        help="每次测试后的延迟秒数，避免限流 (默认: 1)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示每次测试的详细日志"
    )

    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="跳过确认提示，直接开始测试"
    )

    args = parser.parse_args()

    # 根据模式执行
    try:
        if args.mode == "quick":
            quick_mode(args)
        elif args.mode == "performance":
            performance_mode(args)
    except KeyboardInterrupt:
        print("\n\n用户中断，测试已停止")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[错误] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
