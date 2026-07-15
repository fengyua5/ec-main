# Brainstorm Summary

- Change: ai-customer-service
- Date: 2026-07-14

## 确认的技术方案

后端 FastAPI SSE 流式传输 + Ollama Qwen2.5:7b 意图识别 + ChromaDB 向量 FAQ 检索 + SQLite 消息持久化。买家 Web 端微信风格聊天 UI，Admin 端 FAQ 管理 + 客服消息列表弹窗回复。

## 关键取舍与风险

| 决策 | 选型 | 原因 |
|---|---|---|
| 流式传输 | SSE | 比 WebSocket 轻量，单向推送足够 |
| 向量存储 | ChromaDB | 文件型，无需独立服务 |
| 意图识别 | LLM prompt 分类 | 冷启动友好，无需训练数据 |
| 消息存储 | SQLite | 初期量小，后续可迁 PostgreSQL |

## 测试策略

- 意图识别 prompt edge case 测试
- FAQ 检索准确度测试
- SSE 流式传输完整性测试
- Admin CRUD 功能测试

## Spec Patch

无
