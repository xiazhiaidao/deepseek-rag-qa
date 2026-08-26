# DeepSeek API 调用指南

本文档是示例知识库中关于 DeepSeek 兼容 API 的调用说明，内容基于本项目默认配置的 OpenAI 兼容网关。

## 基本信息

- **Base URL**：`https://tokenrhythm.studio/v1`
- **对话接口**：`POST /chat/completions`
- **认证方式**：请求头 `Authorization: Bearer <API_KEY>`
- **推荐模型**：`deepseek-v4-flash`（快速、成本低，适合 RAG 问答）

## 使用 Python OpenAI SDK 调用

安装 OpenAI SDK 后，可以用如下代码调用：

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://tokenrhythm.studio/v1",
    api_key="sk-your-api-key",
)

resp = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "你是一个助手。"},
        {"role": "user", "content": "你好"},
    ],
)
print(resp.choices[0].message.content)
```

## 使用 LangChain 调用

本项目在 RAG 管线中通过 `langchain-openai` 集成：

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key="sk-your-api-key",
    base_url="https://tokenrhythm.studio/v1",
    temperature=0.3,
)
print(llm.invoke("你好").content)
```

## 注意事项

1. **API Key 不要提交到 Git**：统一放在项目根目录 `.env`，该文件已被 `.gitignore` 忽略。
2. **该网关主要提供 Chat 能力**：Embedding 等能力需要本地模型完成，本项目默认使用 `BAAI/bge-small-zh-v1.5` 本地向量化。
3. **超时与错误处理**：建议在服务端捕获 LLM 调用异常，避免把原始错误直接暴露给前端。
4. **模型选择**：`deepseek-v4-flash` 适合日常问答；追求更强能力可参考 `/v1/models` 中可用的其他模型。

## 快速验证连通性

```bash
curl https://tokenrhythm.studio/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好"}]}'
```