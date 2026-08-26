"""FastAPI 应用：RAG 问答 + 文档导入 + Web UI + 聊天历史。"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models import ChatMessage
from app.rag.pipeline import get_pipeline

logger = logging.getLogger("uvicorn.error")

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"

ALLOWED_EXTS = {".txt", ".md", ".markdown", ".pdf", ".docx"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB

_PLACEHOLDER_KEYS = {"", "sk-your-api-key", "your-api-key"}


def _llm_configured() -> bool:
    return settings.llm_api_key not in _PLACEHOLDER_KEYS


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=4000)
    session_id: str = Field(default="default", max_length=64)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()

    if not _llm_configured():
        logger.warning(
            "⚠️  LLM_API_KEY 未配置（或仍是占位符），问答功能将不可用。"
            "请在项目根目录 .env 中填入真实密钥，参考 .env.example。"
        )

    pipeline = get_pipeline()
    knowledge_dir = settings.data_dir / "knowledge"
    if pipeline.vectorstore.count() == 0 and knowledge_dir.exists():
        result = pipeline.ingest_knowledge_dir(knowledge_dir)
        total = sum(result.values())
        logger.info("[startup] 自动导入知识库完成，共 %d 个分块", total)

    yield


app = FastAPI(
    title="DeepSeek RAG QA",
    description="基于 DeepSeek API + 本地中文向量检索的知识库问答服务",
    version="1.1.0",
    lifespan=lifespan,
)

# 学习/演示项目默认放开跨域；生产部署请改为具体来源并移除 credentials。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/api/health")
def health():
    pipeline = get_pipeline()
    return {
        "status": "ok",
        "llm_configured": _llm_configured(),
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "chunk_count": pipeline.vectorstore.count(),
    }


@app.get("/api/stats")
def stats():
    return get_pipeline().stats()


# 注意：路由用同步 def，FastAPI 会自动放到线程池执行，
# 避免 Embedding 推理 / LLM 网络请求阻塞事件循环。
@app.post("/api/ingest")
def ingest(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTS:
        raise HTTPException(status_code=415, detail=f"不支持的文件类型: {suffix or '未知'}")

    content = file.file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="文件不能超过 10MB")

    # 只取文件名部分，防止 ../ 等路径穿越
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="无效的文件名")

    upload_path = settings.upload_dir / safe_name
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(content)

    pipeline = get_pipeline()
    try:
        chunk_count = pipeline.ingest_document(upload_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"解析文档失败: {exc}")

    if chunk_count == 0:
        raise HTTPException(status_code=400, detail="文档中没有可用的文本内容")

    db.add(
        ChatMessage(
            session_id="system",
            role="assistant",
            content=f"📄 已导入《{filename}》，切分为 {chunk_count} 个知识块，可以开始提问了。",
        )
    )
    db.commit()
    return {
        "filename": filename,
        "chunk_count": chunk_count,
        "message": f"文件已导入，生成 {chunk_count} 个知识块",
    }


@app.post("/api/chat")
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    question = body.message.strip()
    session_id = body.session_id
    if not question:
        raise HTTPException(status_code=400, detail="消息不能为空")

    db.add(ChatMessage(session_id=session_id, role="user", content=question))
    db.commit()

    pipeline = get_pipeline()
    try:
        result = pipeline.ask(question)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"调用 LLM 失败: {exc}")

    db.add(
        ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
        )
    )
    db.commit()

    return {
        "session_id": session_id,
        "answer": result["answer"],
        "sources": result["sources"],
        "user_message": question,
    }


@app.get("/api/sessions/{session_id}/messages")
def messages(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    return [
        {"role": row.role, "content": row.content, "created_at": row.created_at.isoformat()}
        for row in rows
    ]
