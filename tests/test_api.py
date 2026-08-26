"""API 冒烟测试：用 fake pipeline 隔离真实 Embedding/LLM 调用。"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app.config import settings


class FakeVectorstore:
    def count(self):
        return 3


class FakePipeline:
    def __init__(self):
        self.vectorstore = FakeVectorstore()

    def ask(self, question):
        return {
            "answer": "这是一条测试回答。",
            "sources": [
                {"source": "test.md", "score": 0.9, "text": "知识块内容片段"}
            ],
            "top_k": 1,
        }

    def ingest_document(self, path):
        return 5

    def ingest_knowledge_dir(self, directory):
        return {}

    def stats(self):
        return {
            "chunk_count": 3,
            "embedding_model": "fake",
            "llm_model": "fake",
            "top_k": 4,
        }


@pytest.fixture(autouse=True)
def fake_pipeline(monkeypatch):
    monkeypatch.setattr(app_main, "get_pipeline", lambda: FakePipeline())
    yield


@pytest.fixture()
def client():
    # with 语句会触发 lifespan（init_db + 自动导入检查）
    with TestClient(app_main.app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["chunk_count"] == 3
    assert isinstance(data["llm_configured"], bool)


def test_chat_ok(client):
    r = client.post("/api/chat", json={"message": "你好", "session_id": "t1"})
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "这是一条测试回答。"
    assert data["sources"][0]["source"] == "test.md"
    assert data["session_id"] == "t1"


def test_chat_blank_message_rejected(client):
    r = client.post("/api/chat", json={"message": "   "})
    assert r.status_code == 400
    assert "不能为空" in r.json()["detail"]


def test_chat_missing_message_rejected(client):
    r = client.post("/api/chat", json={"session_id": "x"})
    assert r.status_code == 422


def test_ingest_ok(client):
    r = client.post(
        "/api/ingest",
        files={"file": ("hello.md", b"# hello", "text/markdown")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["chunk_count"] == 5
    assert data["filename"] == "hello.md"


def test_ingest_unsupported_type(client):
    r = client.post(
        "/api/ingest",
        files={"file": ("evil.exe", b"MZ", "application/octet-stream")},
    )
    assert r.status_code == 415


def test_ingest_too_large(client):
    r = client.post(
        "/api/ingest",
        files={"file": ("big.md", b"x" * (10 * 1024 * 1024 + 1), "text/markdown")},
    )
    assert r.status_code == 413


def test_ingest_path_traversal_sanitized(client):
    uploads = settings.upload_dir
    uploads.mkdir(parents=True, exist_ok=True)

    r = client.post(
        "/api/ingest",
        files={"file": ("../../evil.md", b"# x", "text/markdown")},
    )
    assert r.status_code == 200

    # 不允许逃逸出 uploads 目录
    escaped = (uploads.parent.parent.parent / "evil.md").resolve()
    assert not escaped.exists()

    # 文件名应被清洗为 evil.md 并落在 uploads 内
    target = uploads / "evil.md"
    assert target.exists()
    target.unlink(missing_ok=True)


def test_sessions_messages(client):
    client.post("/api/chat", json={"message": "你好", "session_id": "hist"})
    r = client.get("/api/sessions/hist/messages")
    assert r.status_code == 200
    rows = r.json()
    assert rows[0]["role"] == "user"
    assert rows[0]["content"] == "你好"
    assert rows[-1]["role"] == "assistant"


def test_index_page_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "DeepSeek RAG" in r.text
