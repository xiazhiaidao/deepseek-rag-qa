"""pytest 共享配置：在导入 app 之前把数据目录与数据库隔离到 tests/.tmp_data。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DATA = Path(__file__).resolve().parent / ".tmp_data"
TEST_DATA.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DATA_DIR", str(TEST_DATA))
os.environ.setdefault("CHAT_DB_URL", f"sqlite:///{TEST_DATA.as_posix()}/test_chat.db")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
