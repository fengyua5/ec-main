## Why

买家端 /ai 目前是占位页，缺少真正的智能客服功能。需要一个工业级的 AI 客服系统，支持 FAQ 自助查询、LLM 智能问答、人工客服转接和退单处理。

## What Changes

- **后端 AI 客服 API**：意图识别路由（Ollama Qwen2.5:7b）、FAQ 向量匹配、人工客服消息管理、退单模拟
- **买家 Web 聊天界面**：微信风格聊天 UI，消息列表 + 输入框，流式渲染 AI 回复，会话历史恢复
- **Admin FAQ 管理**：上传 MD 文档 → 切片 → 向量化存储，知识库管理界面
- **Admin 客服消息**：消息列表页面，点击弹窗回复买家消息
- **退单模拟**：买家输入订单号/原因/金额 → 后端返回成功
- **SDK 扩展**：新增客服相关 API 函数

## Capabilities

### New Capabilities
- `ai-customer-service`: AI 智能客服系统，包含意图识别路由、FAQ 向量知识库、流式 AI 对话、人工客服转接、退单模拟

### Modified Capabilities

（无）

## Impact

- `backend/app/api/web/ai.py` — AI 客服 Web API（聊天、历史、退单）
- `backend/app/api/admin/ai.py` — Admin FAQ 管理 API
- `backend/app/api/admin/chat.py` — Admin 客服消息 API
- `backend/app/domain/ai/` — 意图识别、FAQ 向量搜索、消息管理领域逻辑
- `backend/app/models/conversation.py` — 会话和消息模型
- `backend/app/main.py` — 注册新路由
- `backend/requirements.txt` — 新增 ollama、chromadb、langchain 等依赖
- `apps/web/app/(main)/ai/page.tsx` — 替换为聊天界面
- `apps/web/app/(main)/ai/components/` — 聊天气泡、输入框、消息列表组件
- `apps/admin/app/(main)/faq/page.tsx` — FAQ 管理页面
- `apps/admin/app/(main)/chat/page.tsx` — 客服消息列表页面
- `apps/admin/app/components/sidebar.tsx` — 新增 FAQ/客服导航项
- `packages/sdk/src/ai.ts` — 新增 AI 客服 SDK 函数
