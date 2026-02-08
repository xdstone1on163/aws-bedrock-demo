"""model_configs.py 单元测试"""
import pytest
from model_configs import get_model_config, get_valid_context_sizes, MODELS, ALL_CONTEXT_SIZES, ModelConfig


class TestGetModelConfig:
    def test_valid_model(self):
        config = get_model_config("deepseek-v3.1")
        assert isinstance(config, ModelConfig)
        assert config.model_id == "deepseek.v3-v1:0"
        assert config.display_name == "DeepSeek V3.1"

    def test_case_insensitive(self):
        config = get_model_config("DeepSeek-V3.1")
        assert config.model_id == "deepseek.v3-v1:0"

    def test_invalid_model_raises(self):
        with pytest.raises(ValueError, match="不支持的模型"):
            get_model_config("nonexistent-model")

    def test_all_models_have_required_fields(self):
        for name, config in MODELS.items():
            assert config.model_id, f"{name} missing model_id"
            assert config.display_name, f"{name} missing display_name"
            assert config.provider, f"{name} missing provider"
            assert config.max_context > 0, f"{name} invalid max_context"


class TestGetValidContextSizes:
    def test_deepseek_v3_1(self):
        sizes = get_valid_context_sizes("deepseek-v3.1")
        assert "8K" in sizes
        assert "128K" in sizes
        # DeepSeek V3.1 max_context=128000, 164K=164000 > 128000
        assert "164K" not in sizes

    def test_kimi_supports_256k(self):
        sizes = get_valid_context_sizes("kimi2.5")
        assert "256K" in sizes
        assert "360K" not in sizes  # 360K=360000 > 256000

    def test_invalid_model_raises(self):
        with pytest.raises(ValueError):
            get_valid_context_sizes("fake-model")


class TestAllContextSizes:
    def test_sorted_ascending(self):
        tokens = [t for _, t in ALL_CONTEXT_SIZES]
        assert tokens == sorted(tokens), "ALL_CONTEXT_SIZES should be sorted ascending"

    def test_labels_match_tokens(self):
        for label, tokens in ALL_CONTEXT_SIZES:
            assert label.endswith("K")
            expected_k = tokens // 1000
            assert label == f"{expected_k}K"
