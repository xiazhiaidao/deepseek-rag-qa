"""离线验证检索阈值、拒答和来源透传；不下载模型、不调用付费 API。"""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.config import settings
from app.rag.pipeline import RAGPipeline


@pytest.mark.parametrize("scores", [[], [0.1, 0.34], [0.35, 0.9, 0.1]])
def test_retrieval_threshold_and_abstention(monkeypatch, scores):
    monkeypatch.setattr(settings, "score_threshold", 0.35)
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.embeddings = Mock()
    pipeline.vectorstore = Mock()
    pipeline.vectorstore.similarity_search_with_score.return_value = [
        ("RAG 结合检索与生成。", {"source": f"rag-{i}.md"}, score)
        for i, score in enumerate(scores)
    ]
    pipeline.llm = Mock()
    pipeline.llm.invoke.return_value = SimpleNamespace(content="RAG 结合检索与生成。")

    result = pipeline.ask("什么是 RAG？")

    expected = [score for score in scores if score >= 0.35]
    assert [source["score"] for source in result["sources"]] == expected
    assert result["top_k"] == len(expected)
    if expected:
        pipeline.llm.invoke.assert_called_once()
        prompt = pipeline.llm.invoke.call_args.args[0][1]["content"]
        assert "rag-2.md" not in prompt
        assert "RAG 结合检索与生成。" in prompt
    else:
        pipeline.llm.invoke.assert_not_called()
        assert "无法回答" in result["answer"]
