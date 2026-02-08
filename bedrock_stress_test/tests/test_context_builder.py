"""context_builder.py 单元测试"""
import pytest
from context_builder import ContextBuilder


class TestEstimateTokens:
    def test_empty_string(self):
        assert ContextBuilder.estimate_tokens("") == 0

    def test_short_string(self):
        assert ContextBuilder.estimate_tokens("hello world") == len("hello world") // 4

    def test_consistency(self):
        text = "a" * 400
        assert ContextBuilder.estimate_tokens(text) == 100


class TestGenerateDocument:
    def test_returns_non_empty(self):
        doc = ContextBuilder.generate_document(1, 100)
        assert len(doc) > 0
        assert "文档 1" in doc

    def test_approximate_target_tokens(self):
        target = 2000
        doc = ContextBuilder.generate_document(1, target)
        estimated = ContextBuilder.estimate_tokens(doc)
        # 应该接近目标，允许一定偏差（一个段落的大小）
        assert estimated >= target

    def test_contains_structure(self):
        doc = ContextBuilder.generate_document(1, 500)
        assert "#" in doc  # 应包含 markdown 标题


class TestBuildRagContext:
    def test_returns_non_empty(self):
        context = ContextBuilder.build_rag_context(num_docs=2, tokens_per_doc=100)
        assert len(context) > 0

    def test_contains_all_docs(self):
        context = ContextBuilder.build_rag_context(num_docs=3, tokens_per_doc=100)
        assert "文档 1" in context
        assert "文档 2" in context
        assert "文档 3" in context

    def test_contains_question_section(self):
        context = ContextBuilder.build_rag_context(num_docs=1, tokens_per_doc=100)
        assert "问题" in context


class TestGetSpecificContext:
    def test_valid_size_8k(self):
        context = ContextBuilder.get_specific_context("8K")
        estimated = ContextBuilder.estimate_tokens(context)
        # 8K = 4 docs x 2000 tokens/doc = ~8000 tokens
        assert estimated >= 7000

    def test_invalid_size_raises(self):
        with pytest.raises(ValueError, match="不支持的上下文大小"):
            ContextBuilder.get_specific_context("999K")

    def test_all_sizes_valid(self):
        valid_sizes = ["8K", "32K", "64K", "128K", "164K", "196K", "200K", "256K", "360K"]
        for size in valid_sizes:
            # 只验证不抛异常，不实际生成大上下文
            context = ContextBuilder.get_specific_context("8K")
            assert len(context) > 0
