# DeepSeek RAG QA 交接文档（HANDOFF）

> 本文件是给 Trae / Claude / Codex / 任何 AI 编码工具继续开发用的“唯一入口”文档。
> 请先读完本文件，再对项目做任何改动。

---

## 1. 项目一句话

一个基于 **DeepSeek 兼容 API + 本地向量检索（RAG）** 的智能问答机器人：
上传知识文档 → 本地切块 Embedding → 向量检索 Top-K → 大模型生成带引用的中文回答。

---

## 2. 当前状态（已实测通过 ✅）

| 项目 | 状态 |
|---|---|
| 后端服务 | FastAPI 可正常启动 |
| `/api/health` | 返回 `ok`，知识库共 **8 个分块** |
| `/api/chat` | 中文 UTF-8 请求实测返回 **HTTP 200** 和中文答案 |
| 向量索引 | 已持久化到 `data/vector_index/`（8 chunks） |
| Embedding 模型 | `BAAI/bge-small-zh-v1.5` 已缓存到 `data/models/`（约 95MB），后续启动可离线加载 |
| 聊天记录 | SQLite `data/chat.db` 已可写入/查询 |
| 自动化测试 | pytest **28 个用例全部通过**（`tests/`，含 API 冒烟测试） |
| CI | GitHub Actions 已配置（`.github/workflows/ci.yml`） |
| 验证用 8765 服务 | 已停止，临时 pid/log/bin 已清理 |
| 正式端口 | **8000**（`scripts/run.bat` 默认） |

---

## 3. 技术栈

- **语言/框架**：Python 3.10、FastAPI、Uvicorn、Pydantic-settings
- **LLM 接入**：OpenAI SDK + LangChain `ChatOpenAI`，Base URL 指向 OpenAI 兼容网关
- **模型**：`deepseek-v4-flash`（聊天）、`BAAI/bge-small-zh-v1.5`（本地向量，dim=512）
- **向量检索**：FastEmbed + 自研 `NumpyVectorStore`（余弦相似度，numpy + JSON 持久化）
- **存储**：SQLAlchemy + SQLite（默认）/ MySQL（可选）
- **文档解析**：pypdf、python-docx
- **前端**：原生 HTML/CSS/JS 暗色聊天 UI（`web/`）

---

## 4. 目录结构

```
deepseek-rag-qa/
├── app/
│   ├── main.py              # FastAPI 入口与全部 API 路由
│   ├── config.py            # 环境变量配置（Pydantic-settings）
│   ├── database.py          # SQLAlchemy engine/session
│   ├── models.py            # ORM 模型（ChatMessage）
│   └── rag/
│       ├── embeddings.py    # 本地 Embedding（HF 镜像环境变量在这里设置）
│       ├── vectorstore.py   # NumpyVectorStore 持久化向量库
│       ├── chunker.py       # 文本切块
│       ├── loader.py        # txt/md/pdf/docx 加载
│       └── pipeline.py      # ingest / ask / stats 核心管线
├── data/
│   ├── knowledge/           # 示例知识库（rag-intro.md, deepseek-api.md）
│   ├── vector_index/        # 已生成的向量索引（勿删）
│   ├── models/              # 本地 embedding 模型缓存（勿删）
│   └── chat.db              # SQLite 聊天记录
├── scripts/
│   ├── run.bat              # Windows 一键启动
│   ├── demo.py              # 端到端 CLI 演示
│   ├── ingest.py            # 命令行导入文档
│   └── smoke_utf8.py        # 原始 UTF-8 API 冒烟测试
├── tests/                   # pytest 单元 + API 测试（28 用例）
├── web/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .github/workflows/       # GitHub Actions CI
├── .env                     # 真实密钥，已被 .gitignore 忽略
├── .env.example             # 环境变量模板（提交到 git）
├── .gitignore
├── requirements.txt
├── requirements-dev.txt     # 测试依赖（pytest、httpx）
├── LICENSE                  # MIT
└── HANDOFF.md               # 本文档
```

---

## 5. 快速开始（Windows）

```bat
cd /d D:\github项目\deepseek-rag-qa
scripts\run.bat
```

`run.bat` 会自动：
1. 用 `py -3.10` 创建 `.venv`（若不存在）
2. 安装 `requirements.txt`
3. 启动 `http://127.0.0.1:8000`（带 `--reload`）

手动启动方式：

```bat
py -3.10 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后打开：<http://127.0.0.1:8000>

---

## 6. API 说明

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 + 知识库分块数 |
| GET | `/api/stats` | 知识库统计 |
| POST | `/api/ingest` | 上传文档（multipart，字段 `file`，支持 txt/md/pdf/docx，≤10MB） |
| POST | `/api/chat` | RAG 问答 |
| GET | `/api/sessions/{session_id}/messages` | 查看某会话历史 |

### `/api/chat` 请求体（注意字段是 `message`，不是 `question`）

```json
{
  "message": "RAG 是什么？",
  "session_id": "handoff-test"
}
```

### 响应结构

```json
{
  "answer": "……中文回答……",
  "sources": [
    {"source": "rag-intro.md", "score": 0.5974, "text": "……（前 200 字截断）"}
  ],
  "session_id": "handoff-test"
}
```

> 注意：`sources[].text`（不是 `content`），`score` 为余弦相关度 0~1。

### curl 验证

```bash
curl -X POST http://127.0.0.1:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"RAG 是什么？\",\"session_id\":\"handoff-test\"}"
```

---

## 7. 环境变量（关键！）

`.env` 文件在项目根目录，**真实 API Key 只存在于 `.env`，已被 `.gitignore` 忽略，绝不能写进代码或文档**。
模板见 `.env.example`。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_BASE_URL` | 无 | 必须设为 `https://tokenrhythm.studio/v1` |
| `LLM_API_KEY` | 无 | 真实密钥，仅放 `.env` |
| `LLM_MODEL` | `deepseek-v4-flash` | 聊天模型 |
| `LLM_TEMPERATURE` | `0.3` | 生成温度 |
| `LLM_MAX_TOKENS` | `1024` | 最大生成 token |
| `EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 本地 embedding 模型 |
| `EMBEDDING_DIM` | `512` | 向量维度 |
| `TOP_K` | `4` | 检索召回数量 |
| `CHUNK_SIZE` | `500` | 切块大小 |
| `CHUNK_OVERLAP` | `80` | 切块重叠 |
| `HF_ENDPOINT` | `https://hf-mirror.com` | HuggingFace 镜像，**必须** |
| `HF_HUB_DISABLE_XET` | `1` | 禁用 HF Xet 下载，**必须** |
| `DATA_DIR` | `./data` | 数据目录 |
| `CHAT_DB_URL` | `sqlite:///./data/chat.db` | 数据库；MySQL 可改为 `mysql+pymysql://user:pass@host/db` |

---

## 8. 已踩过的坑（务必记住）

1. **网关不支持 `/v1/embeddings`**（返回 `400 MODEL_CAPABILITY_NOT_SUPPORTED`）
   → Embedding 必须用本地 `fastembed` + `BAAI/bge-small-zh-v1.5`。
2. **必须设置 HF 镜像环境变量**
   → `HF_ENDPOINT=https://hf-mirror.com` 和 `HF_HUB_DISABLE_XET=1` 缺一不可，否则模型下载超时或 401。
3. **`/api/chat` 字段是 `message`**
   → 传 `{"question": ...}` 会返回 400「消息不能为空」。
4. **Windows 控制台 GBK 编码**
   → 运行脚本前执行 `chcp 65001`；项目内脚本已用 `stdout.reconfigure(encoding="utf-8")` 处理。
5. **首次启动要联网下载模型**
   → 现在模型已缓存到 `data/models/`，后续启动可离线。不要删除 `data/models/` 和 `data/vector_index/`。
6. **API Key 不可硬编码**
   → 所有密钥一律从 `.env` 读取；提交代码前确认 `.env` 未被 git 追踪。

---

## 9. 已验证记录

- 知识库：`data/knowledge/` 下 2 个示例文档，共切 **8 个分块**。
- `/api/chat` 实测问题「RAG 是什么？」：
  - HTTP 200
  - 返回中文回答
  - Top 来源：`rag-intro.md`（相关度 0.5974）、`rag-intro.md`（0.466）、`deepseek-api.md`（0.449）、`deepseek-api.md`（0.440）
- 真实 API Key 已用 `deepseek-v4-flash` 验证可正常对话。

---

## 10. 待办（下一步）

按优先级：

- [x] 写 `README.md`（项目介绍、快速开始、目录结构）
- [x] 补 Docker 部署文件（`Dockerfile`、`docker-compose.yml`、`.dockerignore`）
- [x] git 初始化并提交（确认 `.env` 被忽略）
- [x] 补自动化测试与 CI（pytest + GitHub Actions）
- [ ] **部署上线**：先查可用服务器 / git remote，再决定部署方式
- [ ] 接入流式输出（SSE），改善长回答体验
- [ ] 前端会话管理（新建/切换/删除）与 Markdown 渲染
- [ ] 增加 rerank 精排，检索结果加最低相关度阈值过滤
- [ ] 投递岗位：Python 后端 / AI 应用 / LLM 实习生，替换 README 联系方式与 LICENSE 版权名

---

## 11. 给 AI 编码工具的指令（Trae/Claude/Codex 通用）

- 动手前先读本文件。
- 任何改动都不要把真实 API Key 写进代码/文档/提交。
- 改动后至少跑一次：
  ```bat
  .venv\Scripts\python.exe scripts\demo.py
  ```
- 如果改动了后端，启动服务后验证：
  ```bat
  curl http://127.0.0.1:8000/api/health
  ```
- 如果删除/重建了 `data/vector_index` 或 `data/models`，需要联网重新下载/生成，速度会慢很多。

---

## 12. 快速验证清单

```bat
:: 1) CLI 端到端验证（无需启动 Web 服务）
.venv\Scripts\python.exe scripts\demo.py

:: 2) 启动服务
scripts\run.bat

:: 3) 健康检查
curl http://127.0.0.1:8000/api/health

:: 4) 中文问答
curl -X POST http://127.0.0.1:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"RAG 是什么？\",\"session_id\":\"handoff-test\"}"
```

---

*交接状态：2026 年 8 月更新；自动化测试已通过，README/HANDOFF 已同步。*
