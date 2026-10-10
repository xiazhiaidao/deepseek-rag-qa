"""应用配置：从 .env 读取，支持环境变量覆盖。"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 网关（OpenAI 兼容）
    llm_base_url: str = "https://tokenrhythm.studio/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-v4-flash"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024

    # RAG
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dim: int = 512
    top_k: int = 4
    score_threshold: float = Field(default=0.35, ge=-1.0, le=1.0)
    chunk_size: int = 500
    chunk_overlap: int = 80

    # Hugging Face 镜像（国内/受限网络环境）
    hf_endpoint: str = "https://hf-mirror.com"
    # 禁用 HF Xet 存储通道，避免镜像/受限网络下 CAS 401
    hf_hub_disable_xet: bool = True

    # 数据目录
    data_dir: Path = Path("./data")

    # 数据库（默认 SQLite，可切换 MySQL）
    chat_db_url: str = "sqlite:///./data/chat.db"

    @property
    def upload_dir(self) -> Path:
        return Path(self.data_dir) / "uploads"

    @property
    def vector_index_dir(self) -> Path:
        return Path(self.data_dir) / "vector_index"

    @property
    def model_cache_dir(self) -> Path:
        return Path(self.data_dir) / "models"


settings = Settings()
