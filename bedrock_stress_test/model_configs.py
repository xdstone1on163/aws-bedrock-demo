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
    "deepseek": ModelConfig(
        model_id="deepseek.v3-v1:0",
        display_name="DeepSeek V3",
        provider="DeepSeek",
        max_context=128000
    ),
    "minimax": ModelConfig(
        model_id="minimax.minimax-m2",
        display_name="MiniMax M2",
        provider="MiniMax",
        max_context=196608  # MiniMax M2实际支持192K上下文（196608 tokens）
    )
}


def get_model_config(model_name: str) -> ModelConfig:
    """
    获取模型配置

    Args:
        model_name: 模型名称（如deepseek, minimax）

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
