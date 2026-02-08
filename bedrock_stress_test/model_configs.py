"""模型配置定义"""
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置数据类"""
    model_id: str           # Bedrock模型ID
    display_name: str       # 显示名称
    provider: str           # 提供商
    max_context: int        # 最大上下文token数


# 支持的模型
MODELS = {
    "deepseek-v3.1": ModelConfig(
        model_id="deepseek.v3-v1:0",
        display_name="DeepSeek V3.1",
        provider="DeepSeek",
        max_context=128000
    ),
    "minimax2.0": ModelConfig(
        model_id="minimax.minimax-m2",
        display_name="MiniMax 2.0",
        provider="MiniMax",
        max_context=196608  # MiniMax M2实际支持192K上下文（196608 tokens）
    ),
    "deepseek-v3.2": ModelConfig(
        model_id="deepseek.v3.2",
        display_name="DeepSeek V3.2",
        provider="DeepSeek",
        max_context=164000
    ),
    "glm4.7": ModelConfig(
        model_id="zai.glm-4.7",
        display_name="GLM 4.7",
        provider="智谱AI",
        max_context=203000
    ),
    "minimax2.1": ModelConfig(
        model_id="minimax.minimax-m2.1",
        display_name="MiniMax 2.1",
        provider="MiniMax",
        max_context=196608
    ),
    "kimi2.5": ModelConfig(
        model_id="moonshotai.kimi-k2.5",
        display_name="Kimi 2.5",
        provider="Moonshot",
        max_context=256000
    ),
}


ALL_CONTEXT_SIZES = [
    ("8K", 8000), ("32K", 32000), ("64K", 64000),
    ("128K", 128000), ("196K", 196000), ("200K", 200000),
    ("256K", 256000), ("360K", 360000),
]


def get_model_config(model_name: str) -> ModelConfig:
    """
    获取模型配置

    Args:
        model_name: 模型名称（如deepseek-v3.1, minimax2.0）

    Returns:
        ModelConfig对象

    Raises:
        ValueError: 如果模型不支持
    """
    if model_name.lower() not in MODELS:
        raise ValueError(
            f"不支持的模型: {model_name}. "
            f"支持的模型: {', '.join(MODELS.keys())}"
        )
    return MODELS[model_name.lower()]


def get_valid_context_sizes(model_name: str) -> list[str]:
    """获取模型支持的上下文大小列表"""
    config = get_model_config(model_name)
    return [size for size, tokens in ALL_CONTEXT_SIZES if tokens <= config.max_context]
