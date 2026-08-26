"""ORM 模型：聊天历史持久化。"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True, default="default", nullable=False)
    role = Column(String(16), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)