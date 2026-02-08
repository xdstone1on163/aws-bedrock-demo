# AWS Bedrock 大模型性能测试工具

一个为AWS Bedrock上的大语言模型设计的性能测试工具，支持**DeepSeek V3.1/V3.2**、**MiniMax 2.0/2.1**、**GLM 4.7**、**Kimi 2.5**等模型，重点测量大上下文场景下的**TTFT（Time To First Token）**和**输出token吞吐量**。

## 功能特性

- ✅ **多模型支持**: 支持DeepSeek V3.1/V3.2、MiniMax 2.0/2.1、GLM 4.7、Kimi 2.5，易于扩展
- ✅ **快速验证模式**: 快速测试模型是否正常响应
- ✅ **性能压测模式**: 系统性测量不同上下文大小下的性能表现
- ✅ **多梯度测试**: 支持8K/32K/64K/128K/164K/196K/200K/256K/360K上下文测试
- ✅ **统计分析**: 自动计算平均值、标准差、P50/P95/P99等指标
- ✅ **实时输出**: 终端美化输出，实时显示测试进度
- ✅ **可配置测试次数**: 通过`--iterations`参数灵活控制测试次数
- ✅ **预热机制**: 避免冷启动影响测试结果
- ✅ **限流保护**: 自动延迟避免API限流

## 安装

### 1. 克隆或下载项目

```bash
cd bedrock_stress_test
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置AWS凭证

确保你的AWS凭证已正确配置：

```bash
# 方式1: 使用AWS CLI配置
aws configure

# 方式2: 设置环境变量
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-2
```

### 4. 验证模型可用性

```bash
# 验证你的AWS账号是否有权限访问模型
aws bedrock list-foundation-models --region us-east-2 | grep deepseek
```

## 使用方法

### 快速验证模式

用于快速测试模型是否正常响应：

```bash
# DeepSeek V3.1测试
python cli.py --mode quick --model deepseek-v3.1 \
  --system "你是一个helpful助手" \
  --user "你好，请介绍一下自己"

# MiniMax 2.0测试
python cli.py --mode quick --model minimax2.0 \
  --system "你是一个helpful助手" \
  --user "你好，请介绍一下自己"

# 交互式输入模式（默认使用DeepSeek）
python cli.py --mode quick

# 自定义模型ID（高级用法）
python cli.py --mode quick --model-id "custom.model-id" \
  --system "你是助手" \
  --user "测试"
```

**输出示例**:
```
[请求] 模型: deepseek.v3-v1:0
[请求] 区域: us-east-2
[请求] System Prompt: 你是一个helpful助手
[请求] User Prompt: 你好，请介绍一下自己
[响应] HTTP状态码: 200 OK
[响应] 第一个token已接收 (TTFT: 145.23ms)
[完成] 输入tokens: 25
[完成] 输出tokens: 150
[完成] TTFT: 145.23ms
[完成] 吞吐量: 42.5 tokens/sec
```

### 性能测试模式

用于系统性测量不同上下文大小下的性能表现：

```bash
# DeepSeek V3.1性能测试（默认测试8K-128K）
python cli.py --mode performance --model deepseek-v3.1 --iterations 10

# MiniMax 2.0性能测试（最大支持128K）
python cli.py --mode performance --model minimax2.0 --iterations 5 \
  --context-sizes 8K,32K,64K,128K

# 完整参数示例
python cli.py --mode performance --model deepseek-v3.1 \
  --iterations 20 \
  --context-sizes 8K,32K,64K,128K \
  --warmup 2 \
  --delay 2 \
  --verbose
```

**重要参数说明**:
- `--iterations N`: **指定每个上下文大小的测试次数**（默认10次，可自定义任意次数）
- `--context-sizes`: 指定要测试的上下文大小（默认全部）
- `--warmup N`: 预热次数，避免冷启动影响（默认1次）
- `--delay N`: 每次测试后延迟秒数，避免限流（默认1秒）
- `--verbose`: 显示每次测试的详细日志
- `-y, --yes`: 跳过确认提示，直接开始测试
- `--debug`: 显示完整错误堆栈信息（调试用）

**输出示例**:
```
================================================================================
开始测试: 8K 上下文
测试次数: 10 次 (预热: 1 次)
================================================================================

[上下文] 大小: 8K (估算 8234 tokens)

[预热] 开始 1 次预热测试...
[预热] 完成

[测试] 开始 10 次性能测试...

8K 测试进度: 100%|████████████████████| 10/10 [00:45<00:00,  4.5s/it]

  [✓] 测试 1: TTFT=145ms | 吞吐量=42.3 tps | 输出=1843 tokens
  [✓] 测试 2: TTFT=152ms | 吞吐量=41.8 tps | 输出=1856 tokens
  ...

================================================================================
统计结果: 8K 上下文
================================================================================

                    TTFT 统计 (Time To First Token)
┌────────────────┬──────────────────────┐
│ 指标           │ 数值                 │
├────────────────┼──────────────────────┤
│ 平均值         │ 148.50 ms            │
│ 标准差         │ 12.30 ms             │
│ 中位数 (P50)   │ 147.00 ms            │
│ P95            │ 165.00 ms            │
│ P99            │ 170.00 ms            │
│ 最小值         │ 135.00 ms            │
│ 最大值         │ 172.00 ms            │
└────────────────┴──────────────────────┘

                    吞吐量统计 (Tokens Per Second)
┌────────────────┬──────────────────────┐
│ 指标           │ 数值                 │
├────────────────┼──────────────────────┤
│ 平均值         │ 42.10 tps            │
│ 标准差         │ 2.50 tps             │
│ 中位数 (P50)   │ 42.30 tps            │
│ P95            │ 45.20 tps            │
│ P99            │ 46.10 tps            │
│ 最小值         │ 38.50 tps            │
│ 最大值         │ 46.80 tps            │
└────────────────┴──────────────────────┘
```

## 命令行参数完整列表

```bash
python cli.py --help
```

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 运行模式: `quick` 或 `performance` | **必需** |
| `--region` | AWS区域 | `us-east-2` |
| `--model` | 选择模型: `deepseek-v3.1`, `minimax2.0`, `deepseek-v3.2`, `glm4.7`, `minimax2.1`, `kimi2.5` | `deepseek-v3.1` |
| `--model-id` | 自定义模型ID（高级选项，覆盖--model） | 无 |
| `--max-tokens` | 最大输出token数 | `2048` |

### Quick模式专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--system` | System prompt | 交互式输入 |
| `--user` | User prompt | 交互式输入 |

### Performance模式专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--iterations` | **每个上下文大小的测试次数** | `10` |
| `--context-sizes` | 要测试的上下文大小（逗号分隔） | `8K,32K,64K,128K` |
| `--system-prompt` | 性能测试使用的system prompt | `你是一个helpful助手。` |
| `--warmup` | 预热次数 | `1` |
| `--delay` | 每次测试后延迟秒数 | `1` |
| `--verbose` | 显示详细日志 | `False` |
| `-y, --yes` | 跳过确认提示 | `False` |
| `--debug` | 显示完整错误堆栈信息 | `False` |

## 项目结构

```
bedrock_stress_test/
├── cli.py                    # 命令行入口（主程序）
├── bedrock_client.py         # Bedrock API封装（应用层重试 + TTFT精确测量）
├── performance_tester.py     # 测试逻辑（自适应延迟）
├── context_builder.py        # 上下文生成器（RAG风格）
├── output_formatter.py       # Rich美化输出
├── models.py                 # 数据类定义
├── model_configs.py          # 模型配置（ID、上下文限制等）
├── requirements.txt          # 依赖项（含版本上下限）
├── requirements.lock         # 精确版本锁定
├── pyproject.toml            # pytest配置
├── tests/                    # 单元测试
│   ├── test_models.py
│   ├── test_model_configs.py
│   ├── test_context_builder.py
│   └── test_performance_tester.py
└── README.md
```

## 测试策略

### 上下文生成策略

模拟真实RAG（Retrieval-Augmented Generation）场景，而不是简单堆积文本：

- **8K context** = 4篇文档 × 2K tokens/篇
- **32K context** = 10篇文档 × 3.2K tokens/篇
- **64K context** = 20篇文档 × 3.2K tokens/篇
- **128K context** = 40篇文档 × 3.2K tokens/篇
- **164K context** = 51篇文档 × 3.2K tokens/篇（DeepSeek V3.2接近上限测试）
- **196K context** = 61篇文档 × 3.2K tokens/篇（MiniMax接近上限测试）
- **200K context** = 63篇文档 × 3.2K tokens/篇（GLM 4.7接近上限测试）
- **256K context** = 80篇文档 × 3.2K tokens/篇
- **360K context** = 112篇文档 × 3.2K tokens/篇

### 性能指标

1. **TTFT (Time To First Token)**: 从发送请求到收到第一个token的时间
2. **吞吐量 (Tokens Per Second)**: 生成token的速度（不包含TTFT）
3. **统计指标**: 平均值、标准差、中位数、P95、P99

### 预热机制

默认在正式测试前执行1次预热请求，避免冷启动影响测试结果。可通过`--warmup`参数调整。

## 支持的模型

工具目前支持以下Bedrock模型：

| 模型名称 | 模型ID | 提供商 | 最大上下文 | 推荐测试梯度 |
|---------|--------|-------|----------|------------|
| deepseek-v3.1 | `deepseek.v3-v1:0` | DeepSeek | 128K tokens | 8K, 32K, 64K, 128K |
| deepseek-v3.2 | `deepseek.v3.2` | DeepSeek | 164K tokens | 8K, 32K, 64K, 128K, **164K** |
| minimax2.0 | `minimax.minimax-m2` | MiniMax | **192K tokens** (196608) | 8K, 32K, 64K, 128K, **164K, 196K** |
| minimax2.1 | `minimax.minimax-m2.1` | MiniMax | **192K tokens** (196608) | 8K, 32K, 64K, 128K, **164K, 196K** |
| glm4.7 | `zai.glm-4.7` | 智谱AI | 203K tokens | 8K, 32K, 64K, 128K, **164K, 196K, 200K** |
| kimi2.5 | `moonshotai.kimi-k2.5` | Moonshot | 256K tokens | 8K, 32K, 64K, 128K, **164K, 196K, 200K**, 256K |

### 如何添加新模型

如果需要添加其他Bedrock模型，编辑 `model_configs.py`：

```python
MODELS["new-model"] = ModelConfig(
    model_id="provider.model-id",
    display_name="Display Name",
    provider="Provider",
    max_context=128000
)
```

### MiniMax 2.0 性能特点

MiniMax 2.0在实际使用中的最大上下文限制为192K tokens（196608），与DeepSeek V3.1相比有更大的上下文窗口：

```bash
# MiniMax 2.0完整测试（含196K接近上限梯度）
python cli.py --mode performance --model minimax2.0 \
  --iterations 5 \
  --context-sizes 8K,32K,64K,128K,196K \
  --delay 2
```

**性能特点**：
- **超高吞吐量**：实测可达800+ tokens/sec（远超DeepSeek V3的40-50 tps）
- **较长TTFT**：首token延迟约1.5-2秒（略高于DeepSeek）
- **更大上下文**：192K比DeepSeek的128K更大，适合长文档处理

**注意**：虽然某些文档声称支持400K，但实际API限制为196608 tokens，超出会返回400错误。

## 常见问题

### Q: 如何验证模型ID是否正确？

```bash
# 列出所有可用的DeepSeek模型
aws bedrock list-foundation-models --region us-east-2 \
  --by-provider deepseek \
  --query 'modelSummaries[*].[modelId,modelName]' \
  --output table
```

### Q: 为什么需要预热（warmup）？

第一次请求通常有冷启动延迟，会严重影响TTFT测量的准确性。预热可以确保测试结果更接近真实场景。

### Q: 如何避免API限流？

- 使用`--delay`参数增加测试间隔（默认1秒）
- 减少`--iterations`测试次数
- 如果遇到`ThrottlingException`，建议增加延迟到2-3秒

### Q: 测试会产生多少费用？

费用取决于：
1. 输入token数量（上下文大小）
2. 输出token数量（限制在2048以内）
3. 测试次数（--iterations参数）

**示例估算**（假设定价为每1M输入tokens $1，每1M输出tokens $2）：
- 1次8K测试 ≈ 8K输入 + 2K输出 = $0.012
- 10次全梯度测试（8K+32K+64K+128K） ≈ $2-5

建议先用`--iterations 2 --context-sizes 8K`进行小规模测试。

### Q: 可以自定义测试次数吗？

**可以！**使用`--iterations N`参数指定测试次数，例如：

```bash
# 只测试3次（快速验证）
python cli.py --mode performance --iterations 3

# 测试50次（更精确的统计）
python cli.py --mode performance --iterations 50

# 针对不同上下文大小测试不同次数（需要多次运行）
python cli.py --mode performance --iterations 5 --context-sizes 8K
python cli.py --mode performance --iterations 20 --context-sizes 128K
```

### Q: 如何导出测试结果？

当前版本支持终端输出，可以通过重定向保存：

```bash
python cli.py --mode performance --iterations 10 > results.txt 2>&1
```

未来版本计划支持JSON格式导出。

## 技术细节

### TTFT精确测量

使用`converse_stream` API监听事件流，捕获第一个`contentBlockDelta`事件的时间戳。SDK级重试已禁用（`max_attempts=1`），改为应用层重试（最多3次，指数退避），每次重试前重置计时器，确保TTFT测量不被重试延迟污染：

```python
for attempt in range(APP_RETRY_MAX_ATTEMPTS):
    t_start = time.perf_counter()  # 每次重试都重新计时
    response = client.converse_stream(...)
    for event in response['stream']:
        if 'contentBlockDelta' in event and not first_token_received:
            ttft = (time.perf_counter() - t_start) * 1000
            first_token_received = True
```

### 吞吐量计算

排除TTFT后的纯生成时间：

```python
generation_time_ms = total_time_ms - ttft_ms
tokens_per_sec = output_tokens / (generation_time_ms / 1000)
```

### Token估算

使用粗略估算（1 token ≈ 4 chars），实际token数从API响应的`usage`字段获取。

### 运行测试

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## 许可证

MIT License

## 反馈和贡献

如有问题或建议，欢迎提交Issue或Pull Request。
