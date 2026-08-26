"""NumpyVectorStore 单元测试：增删查、持久化、排序、维度校验。"""
import numpy as np
import pytest

from app.rag.vectorstore import NumpyVectorStore


def test_add_and_count(tmp_path):
    vs = NumpyVectorStore(tmp_path, dim=4)
    ids = vs.add_embeddings(["你好", "世界"], [[0.1] * 4, [0.2] * 4])
    assert vs.count() == 2
    assert len(ids) == 2
    assert vs.ids[0] == ids[0]


def test_persist_and_reload(tmp_path):
    vs = NumpyVectorStore(tmp_path, dim=4)
    vs.add_embeddings(["你好"], [[0.1] * 4], metadatas=[{"source": "a.md"}])
    vs2 = NumpyVectorStore(tmp_path, dim=4)
    assert vs2.count() == 1
    assert vs2.texts[0] == "你好"
    assert vs2.metadatas[0]["source"] == "a.md"


def test_similarity_ranking(tmp_path):
    vs = NumpyVectorStore(tmp_path, dim=2)
    vs.add_embeddings(["a", "b"], [[1.0, 0.0], [0.0, 1.0]])
    results = vs.similarity_search_with_score([1.0, 0.0], k=2)
    assert results[0][0] == "a"
    assert results[0][2] > results[1][2]
    assert 0.0 <= results[0][2] <= 1.0


def test_empty_store_returns_empty(tmp_path):
    vs = NumpyVectorStore(tmp_path, dim=4)
    assert vs.similarity_search_with_score([0.1] * 4) == []
    assert vs.count() == 0


def test_dim_mismatch_raises(tmp_path):
    vs = NumpyVectorStore(tmp_path, dim=4)
    with pytest.raises(ValueError):
        vs.add_embeddings(["x"], [[0.1] * 3])


def test_corrupted_index_starts_empty(tmp_path):
    (tmp_path / "vectors.npy").write_bytes(b"corrupted-bytes")
    (tmp_path / "chunks.json").write_text("{not valid json", encoding="utf-8")
    vs = NumpyVectorStore(tmp_path, dim=4)
    assert vs.count() == 0
    assert vs.vectors.shape == (0, 4)


def test_k_larger_than_store(tmp_path):
    vs = NumpyVectorStore(tmp_path, dim=2)
    vs.add_embeddings(["a"], [[1.0, 0.0]])
    results = vs.similarity_search_with_score([1.0, 0.0], k=10)
    assert len(results) == 1


def test_numpy_math_consistency():
    # 归一化后余弦相似度 = 点积
    v = np.asarray([3.0, 4.0], dtype=np.float32)
    norm = np.linalg.norm(v)
    assert np.isclose((v / norm).tolist(), [0.6, 0.8]).all()
