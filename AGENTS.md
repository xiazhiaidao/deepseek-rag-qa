# AGENTS.md

本仓库是一个 **DeepSeek RAG 问答机器人**（FastAPI + 本地向量检索 + DeepSeek 兼容 API）。

AI 编码工具（Trae / Claude Code / Codex 等）开始工作前，**必须先阅读 `HANDOFF.md`**，
其中包含当前状态、运行命令、API 说明、环境变量、已踩坑记录和待办事项。

## 红线

- 真实 API Key 只允许存在于本地 `.env`，禁止写入代码、文档或提交到 git。
- 不要删除 `data/models/`、`data/vector_index/`，否则需要重新联网下载/生成。
- 修改后至少运行 `scripts/demo.py` 或启动服务做一次健康检查。
