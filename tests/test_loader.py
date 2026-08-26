"""文档加载器单元测试：txt / md / 不支持类型。"""
import pytest

from app.rag.loader import load_document


def test_load_txt(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("你好，世界", encoding="utf-8")
    assert load_document(f) == "你好，世界"


def test_load_markdown(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# 标题\n\n正文内容", encoding="utf-8")
    text = load_document(f)
    assert "标题" in text and "正文内容" in text


def test_load_markdown_extension(tmp_path):
    f = tmp_path / "a.markdown"
    f.write_text("内容", encoding="utf-8")
    assert load_document(f) == "内容"


def test_unsupported_type_raises(tmp_path):
    f = tmp_path / "a.xlsx"
    f.write_bytes(b"not really xlsx")
    with pytest.raises(ValueError):
        load_document(f)


def test_gbk_txt_falls_back_gracefully(tmp_path):
    # errors="ignore" 保证乱码编码不抛异常
    f = tmp_path / "gbk.txt"
    f.write_bytes("中文内容".encode("gbk"))
    text = load_document(f)
    assert isinstance(text, str)
