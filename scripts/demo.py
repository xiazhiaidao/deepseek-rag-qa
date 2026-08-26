"""端到端演示脚本：自动导入示例知识库并提问。

用法：
  python scripts/demo.py
"""
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

from app.config import settings  # noqa: E402
from app.rag.pipeline import get_pipeline  # noqa: E402

QUESTIONS = [
    "什么是 RAG？它解决了什么问题？",
    "这个项目的 DeepSeek API 应该怎么调用？",
    "向量检索在 RAG 里起到什么作用？",
]


def main():
    pipeline = get_pipeline()
    knowledge_dir = settings.data_dir / "knowledge"

    if pipeline.vectorstore.count() == 0:
        print("📚 自动导入示例知识库...")
        result = pipeline.ingest_knowledge_dir(knowledge_dir)
        for name, chunks in result.items():
            print(f"  - {name}: {chunks} 个知识块")
    else:
        print(f"📚 知识库已存在，共 {pipeline.vectorstore.count()} 个分块，跳过导入")

    print("\n🤖 开始端到端问答演示\n" + "=" * 60)
    for q in QUESTIONS:
        print(f"\n【问题】{q}")
        print("-" * 60)
        try:
            result = pipeline.ask(q)
            print(f"【回答】\n{result['answer']}")
            print("-" * 60)
            print(f"【引用 {result['top_k']} 个知识块】")
            for src in result["sources"]:
                print(f"  · {src['source']} (相关度 {src['score']:.2f})")
        except Exception as exc:
            print(f"❌ 调用失败: {exc}")

    print("\n✅ 演示完成。也可以运行 scripts/run.bat 启动 Web UI 体验。")


if __name__ == "__main__":
    main()