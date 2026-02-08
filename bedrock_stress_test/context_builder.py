"""
上下文生成器
模拟RAG场景，生成不同大小的测试上下文
"""
from typing import Dict
import random


class ContextBuilder:
    """上下文构建器，生成模拟RAG场景的测试数据"""

    # 模拟的文档主题
    TOPICS = [
        "云计算架构", "机器学习算法", "数据库优化", "网络安全",
        "微服务设计", "容器编排", "分布式系统", "API设计",
        "性能优化", "代码重构", "测试策略", "DevOps实践",
        "前端框架", "后端开发", "移动应用", "区块链技术",
        "人工智能", "大数据处理", "实时计算", "消息队列"
    ]

    # 技术词汇库（用于填充内容）
    TECH_TERMS = [
        "scalability", "latency", "throughput", "consistency", "availability",
        "partition tolerance", "microservices", "containerization", "orchestration",
        "load balancing", "caching", "sharding", "replication", "failover",
        "monitoring", "observability", "tracing", "metrics", "logging",
        "authentication", "authorization", "encryption", "compliance", "governance"
    ]

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        粗略估算token数量
        经验值：英文约4字符/token，中文约1.5字符/token
        这里采用混合估算
        """
        return len(text) // 4

    @staticmethod
    def generate_document(doc_id: int, target_tokens: int) -> str:
        """
        生成单个模拟文档

        Args:
            doc_id: 文档编号
            target_tokens: 目标token数量

        Returns:
            文档内容字符串
        """
        topic = random.choice(ContextBuilder.TOPICS)
        content_parts = []

        content_parts.append(f"# 文档 {doc_id}: {topic}\n\n")

        # 生成段落，直到达到目标token数
        current_text = "\n".join(content_parts)
        paragraph_count = 0

        while ContextBuilder.estimate_tokens(current_text) < target_tokens:
            paragraph_count += 1

            # 生成段落标题
            content_parts.append(f"## 第 {paragraph_count} 节\n\n")

            # 生成段落内容
            sentences = random.randint(3, 6)
            for _ in range(sentences):
                # 生成句子
                sentence_words = random.sample(ContextBuilder.TECH_TERMS, k=random.randint(5, 10))
                sentence = f"本节讨论 {' 和 '.join(sentence_words[:3])} 的相关概念。"
                content_parts.append(sentence + " ")

                # 添加一些技术细节
                detail_words = random.sample(ContextBuilder.TECH_TERMS, k=random.randint(8, 15))
                detail = f"在实践中，{', '.join(detail_words)} 等技术点需要重点关注。"
                content_parts.append(detail + " ")

            content_parts.append("\n\n")

            # 添加代码示例（增加token密度）
            if paragraph_count % 3 == 0:
                content_parts.append("```python\n")
                content_parts.append("# 示例代码\n")
                content_parts.append("def example_function():\n")
                content_parts.append("    result = process_data(input_data)\n")
                content_parts.append("    return result\n")
                content_parts.append("```\n\n")

            current_text = "".join(content_parts)

        return current_text

    @staticmethod
    def build_rag_context(num_docs: int, tokens_per_doc: int) -> str:
        """
        构建RAG风格的上下文

        Args:
            num_docs: 文档数量
            tokens_per_doc: 每个文档的目标token数

        Returns:
            完整的上下文字符串
        """
        context_parts = ["## 检索上下文\n\n"]
        context_parts.append(f"以下是检索到的 {num_docs} 个相关文档：\n\n")

        for i in range(1, num_docs + 1):
            doc_content = ContextBuilder.generate_document(i, tokens_per_doc)
            context_parts.append(doc_content)
            context_parts.append("\n" + "="*80 + "\n\n")

        context_parts.append("## 问题\n\n")
        context_parts.append("请根据以上检索到的文档内容，总结关键技术要点。")

        return "".join(context_parts)

    @staticmethod
    def get_test_contexts() -> Dict[str, str]:
        """
        生成所有测试上下文梯度

        Returns:
            字典 {context_size: context_string}
        """
        contexts = {}

        # 8K context = 4篇文档 × 2K tokens/篇
        contexts["8K"] = ContextBuilder.build_rag_context(num_docs=4, tokens_per_doc=2000)

        # 32K context = 10篇文档 × 3K tokens/篇
        contexts["32K"] = ContextBuilder.build_rag_context(num_docs=10, tokens_per_doc=3200)

        # 64K context = 20篇文档 × 3K tokens/篇
        contexts["64K"] = ContextBuilder.build_rag_context(num_docs=20, tokens_per_doc=3200)

        # 128K context = 40篇文档 × 3K tokens/篇
        contexts["128K"] = ContextBuilder.build_rag_context(num_docs=40, tokens_per_doc=3200)

        # 196K context = 61篇文档 × 3.2K tokens/篇（适用于MiniMax等模型接近上限测试）
        contexts["196K"] = ContextBuilder.build_rag_context(num_docs=61, tokens_per_doc=3200)

        # 200K context = 63篇文档 × 3.2K tokens/篇（适用于GLM 4.7等模型接近上限测试）
        contexts["200K"] = ContextBuilder.build_rag_context(num_docs=63, tokens_per_doc=3200)

        # 256K context = 80篇文档 × 3K tokens/篇（适用于MiniMax M2等超长上下文模型）
        contexts["256K"] = ContextBuilder.build_rag_context(num_docs=80, tokens_per_doc=3200)

        # 360K context = 112篇文档 × 3K tokens/篇（适用于MiniMax M2等超长上下文模型）
        contexts["360K"] = ContextBuilder.build_rag_context(num_docs=112, tokens_per_doc=3200)

        return contexts

    @staticmethod
    def get_specific_context(size: str) -> str:
        """
        获取特定大小的上下文

        Args:
            size: 上下文大小 (8K, 32K, 64K, 128K, 196K, 200K, 256K, 360K)

        Returns:
            上下文字符串
        """
        size_config = {
            "8K": (4, 2000),
            "32K": (10, 3200),
            "64K": (20, 3200),
            "128K": (40, 3200),
            "196K": (61, 3200),
            "200K": (63, 3200),
            "256K": (80, 3200),
            "360K": (112, 3200),
        }

        if size not in size_config:
            raise ValueError(f"不支持的上下文大小: {size}. 支持的大小: {list(size_config.keys())}")

        num_docs, tokens_per_doc = size_config[size]
        return ContextBuilder.build_rag_context(num_docs, tokens_per_doc)
