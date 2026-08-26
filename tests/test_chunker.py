"""文本切块器单元测试。"""
from app.rag.chunker import create_splitter


def test_long_text_split_into_multiple_chunks():
    splitter = create_splitter(chunk_size=100, chunk_overlap=10)
    text = "这是第一句话。" * 300
    chunks = splitter.split_text(text)
    assert len(chunks) > 1


def test_short_text_single_chunk():
    splitter = create_splitter()
    chunks = splitter.split_text("你好，世界")
    assert len(chunks) == 1


def test_chunk_size_respected():
    splitter = create_splitter(chunk_size=200, chunk_overlap=20)
    text = "这是一段比较长的中文测试文本，" * 100
    chunks = splitter.split_text(text)
    # 允许轻微超出（切分点落在分隔符上）
    assert all(len(c) <= 260 for c in chunks)


def test_empty_text_returns_no_chunks():
    splitter = create_splitter()
    assert splitter.split_text("") == []


def test_separators_keep_chinese_punctuation():
    # 中文标点应被保留在切块结尾
    splitter = create_splitter(chunk_size=50, chunk_overlap=0)
    text = "第一句。第二句！第三句？"
    chunks = splitter.split_text(text)
    assert any(c.endswith("。") or c.endswith("！") or c.endswith("？") for c in chunks)
