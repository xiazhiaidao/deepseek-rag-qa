"""命令行导入工具：python scripts/ingest.py <file-or-dir>"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from app.rag.pipeline import get_pipeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="导入文件或目录到 DeepSeek RAG 知识库")
    parser.add_argument("path", help="文件路径或目录路径")
    args = parser.parse_args()

    pipeline = get_pipeline()
    target = Path(args.path).resolve()
    if target.is_dir():
        result = pipeline.ingest_knowledge_dir(target)
        print(f"目录导入完成，共导入 {len(result)} 个文件")
        for name, chunks in result.items():
            print(f"  - {name}: {chunks} 个知识块")
    elif target.is_file():
        chunks = pipeline.ingest_document(target)
        print(f"{target.name} 导入完成，生成 {chunks} 个知识块")
    else:
        print(f"路径不存在: {target}")
        raise SystemExit(1)

    print(f"当前知识库总量: {pipeline.vectorstore.count()} 个分块")


if __name__ == "__main__":
    main()