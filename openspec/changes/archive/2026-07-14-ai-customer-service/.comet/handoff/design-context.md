# Comet Design Handoff

- Change: ai-customer-service
- Phase: design
- Mode: compact
- Context hash: 7dcfc525e6a50b4f6654e8f357a5fd2f047fe326d9c8985ae64a2be45435ac52

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/ai-customer-service/proposal.md

- Source: openspec/changes/ai-customer-service/proposal.md
- Lines: 1-37
- SHA256: 8e60066c6818b5e7bffe35d49d2fa2aba06802d835f43f6615c1fe6192e1192d

```md
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
```

## openspec/changes/ai-customer-service/design.md

- Source: openspec/changes/ai-customer-service/design.md
- Lines: 1-82
- SHA256: 343feb1e02d673101e853f405d4ef37a77b20fadd54c8f5de07641ced32f11a1

[TRUNCATED]

```md
## Context

当前占位 AI 客服页（`/ai`）仅显示"即将上线"。需要实现完整的智能客服系统，涉及 Web 前端、Admin 后台和 Python 后端三个端，以及 Ollama 本地大模型和向量数据库集成。

## Goals / Non-Goals

**Goals:**
- 买家端聊天界面（微信风格），流式渲染 AI 回复
- 意图识别路由（Ollama Qwen2.5:7b 经 LangChain）将用户输入分类为 FAQ/退单/人工
- Admin FAQ 管理（MD 上传 → LlamaIndex 索引 → ChromaDB 向量存储 → 语义检索）
- Admin 客服消息列表 + 弹窗回复
- 退单模拟（订单号/原因/金额 → 返回成功）
- 消息持久化（SQLite），买家端会话历史恢复
- Admin Sidebar 新增「FAQ 管理」「客服消息」导航

**Non-Goals:**
- 多模型切换、模型微调
- 图片/文件消息
- 消息队列
- 已读回执、在线状态、打字指示
- 真实退款流程

## Decisions

### Decision: 后端 AI 引擎 = LangChain + LlamaIndex + LangGraph

三层架构：
- **LangChain**：LLM 抽象层（`ChatOllama`、`OllamaEmbeddings`、prompt templates、streaming callbacks）
- **LlamaIndex**：RAG 管线（文档索引、向量检索、QA engine）
- **LangGraph**：工作流引擎（`StateGraph` 定义意图路由、退单状态机、FAQ 问答流程）

替代方案：直接 httpx 调用 Ollama + 手写路由逻辑 → 三层框架提高了可维护性和扩展性，但增加了依赖体积。

### Decision: SSE 流式传输（FastAPI StreamingResponse + LangChain Callback）

AI 回复和 Admin 消息均使用 SSE 流式传输。LangChain `BaseCallbackHandler` 将 `on_llm_new_token` 事件转发到 SSE 队列。

替代方案：WebSocket 双向通信 → 当前阶段人工客服回复为单向推送（Admin → Buyer），SSE 更简单，与 FastAPI 原生兼容。

### Decision: ChromaDB + OllamaEmbeddings 作向量存储（通过 LlamaIndex）

FAQ MD 文档经 LlamaIndex `SentenceSplitter` 切分后，使用 `OllamaEmbeddings`（nomic-embed-text）生成向量，通过 `ChromaVectorStore` 存入 ChromaDB。

替代方案：pgvector → 需要 PostgreSQL，当前 SQLite 环境不适用。

### Decision: 意图识别用 LangChain prompt + OutputParser

用户输入通过 `ChatOllama` + `ChatPromptTemplate` + `StructuredOutputParser` 结构化输出 JSON `{"intent": "faq|refund|human|greeting", "confidence": N}`。

替代方案：传统 NLP 分类器 → 需要训练数据和模型部署，LLM prompt 更灵活且冷启动友好。

### Decision: 消息模型设计

```python
class Conversation(Base):
    id: int PK
    buyer_id: int FK -> users.id
    status: str  # active / resolved / waiting_human
    created_at: datetime
    updated_at: datetime

class Message(Base):
    id: int PK
    conversation_id: int FK -> conversations.id
    sender: str  # "buyer" / "ai" / "admin"
    content: str
    msg_type: str  # "text" / "system"
    created_at: datetime
```

## Risks / Trade-offs

- [Risk] 三个框架依赖繁重 → Mitigation：仅引入必需模块（langchain-ollama 而非全量 langchain）
- [Risk] Ollama 未运行或响应慢 → Mitigation：LangChain 连接超时 30s，异常捕获后返回"AI 服务暂不可用"
- [Risk] ChromaDB 缺少中文嵌入模型支持 → Mitigation：使用 Ollama nomic-embed-text（支持中文），备选 bge-small-zh-v1.5
- [Risk] SQLite 高并发写入性能 → Mitigation：初期消息量小足够；后续可迁至 PostgreSQL
- [Risk] MD 文件上传格式不统一 → Mitigation：限制 MD 大小 5MB，要求 UTF-8 编码

## Open Questions

```

Full source: openspec/changes/ai-customer-service/design.md

## openspec/changes/ai-customer-service/tasks.md

- Source: openspec/changes/ai-customer-service/tasks.md
- Lines: 1-89
- SHA256: 264bfbe72f2a42b90afc734cdf66c1024319d9fd6e959f19ca42e862b16dc2bb

[TRUNCATED]

```md
## 1. 后端基础：数据模型与依赖
- [ ] 1.1 安装后端依赖：langchain、langchain-ollama、langgraph、llama-index、llama-index-vector-stores-chroma、chromadb、sse-starlette
- [ ] 1.2 创建 Conversation / Message SQLAlchemy 模型
- [ ] 1.3 创建数据库迁移

## 2. 后端核心：LangChain 集成层
- [ ] 2.1 实现 ChatOllama / OllamaEmbeddings 封装（基于 langchain-ollama）
- [ ] 2.2 实现 StreamCallbackHandler（LangChain token 事件 → SSE 队列）
- [ ] 2.3 实现 prompt 模板 + OutputParser（意图分类 JSON 输出）

## 3. 后端核心：LlamaIndex RAG 管线
- [ ] 3.1 实现 FaqIndexService（MD 上传 → 切片 → VectorStoreIndex 构建）
- [ ] 3.2 实现 FaqRetriever（语义检索 top_k=3，相似度阈值过滤）
- [ ] 3.3 实现 FAQ 文档 CRUD（List/Delete + ChromaDB collection 同步）

## 4. 后端核心：LangGraph 工作流
- [ ] 4.1 定义 ConversationState TypedDict + 状态图节点
- [ ] 4.2 实现 classify_intent 节点（调用 LangChain 意图分类）
- [ ] 4.3 实现 retrieve_faq → answer_faq 节点链
- [ ] 4.4 实现 collect_refund_info → process_refund 状态机
- [ ] 4.5 实现 handle_greeting / handoff_human 节点

## 5. 后端核心：数据模型
- [ ] 5.1 创建 Conversation / Message / FAQDocument SQLAlchemy 模型
- [ ] 5.2 实现会话与消息管理服务（CRUD）

## 6. 后端 API：Web 端
- [ ] 6.1 创建 `POST /api/web/ai/chat` SSE 流式聊天接口（驱动 LangGraph）
- [ ] 6.2 创建 `GET /api/web/ai/conversations` 获取会话列表
- [ ] 6.3 创建 `GET /api/web/ai/conversations/:id/messages` 获取消息历史
- [ ] 6.4 在 main.py 注册新路由

## 7. 后端 API：Admin 端
- [ ] 7.1 创建 FAQ 文档 CRUD API（上传/列表/删除）
- [ ] 7.2 创建客服会话列表 API
- [ ] 7.3 创建 Admin 发送消息 API（SSE 推送给买家）
- [ ] 7.4 在 main.py 注册新路由

## 8. Web 前端：AI 客服聊天界面
- [ ] 8.1 替换占位页为聊天界面（消息列表 + 输入框组件）
- [ ] 8.2 实现消息气泡组件（买家/AI/Admin/系统消息样式）
- [ ] 8.3 实现 SSE 流式渲染（ReadableStream 逐块追加）
- [ ] 8.4 实现自动滚动到底部 + 上滑加载历史

## 9. Admin 前端：FAQ 管理
- [ ] 9.1 创建 FAQ 列表页面（展示文档列表 + 删除按钮）
- [ ] 9.2 实现 MD 文件上传组件
- [ ] 9.3 侧边栏新增「FAQ 管理」导航项

## 10. Admin 前端：客服消息
- [ ] 10.1 创建客服会话列表页面
- [ ] 10.2 实现点击会话弹出聊天窗口
- [ ] 10.3 实现 Admin 发送消息功能
- [ ] 10.4 侧边栏新增「客服消息」导航项

## 11. SDK 扩展
- [ ] 11.1 在 SDK 中新增 AI 客服相关 API 函数（chat、conversations、messages）

## 3. 后端 API：Web 端
- [ ] 3.1 创建 `POST /api/web/ai/chat` SSE 流式聊天接口
- [ ] 3.2 创建 `GET /api/web/ai/conversations` 获取会话列表
- [ ] 3.3 创建 `GET /api/web/ai/conversations/:id/messages` 获取消息历史
- [ ] 3.4 在 main.py 注册新路由

## 4. 后端 API：Admin 端
- [ ] 4.1 创建 FAQ 文档 CRUD API（上传/列表/删除）
- [ ] 4.2 创建客服会话列表 API
- [ ] 4.3 创建 Admin 发送消息 API（SSE 推送给买家）
- [ ] 4.4 在 main.py 注册新路由

## 5. Web 前端：AI 客服聊天界面
- [ ] 5.1 替换占位页为聊天界面（消息列表 + 输入框组件）
- [ ] 5.2 实现消息气泡组件（买家/AI/Admin/系统消息样式）
- [ ] 5.3 实现 SSE 流式渲染（ReadableStream 逐块追加）
- [ ] 5.4 实现自动滚动到底部 + 上滑加载历史

## 6. Admin 前端：FAQ 管理
- [ ] 6.1 创建 FAQ 列表页面（展示文档列表 + 删除按钮）
- [ ] 6.2 实现 MD 文件上传组件
- [ ] 6.3 侧边栏新增「FAQ 管理」导航项
```

Full source: openspec/changes/ai-customer-service/tasks.md

## openspec/changes/ai-customer-service/specs/ai-customer-service/spec.md

- Source: openspec/changes/ai-customer-service/specs/ai-customer-service/spec.md
- Lines: 1-97
- SHA256: a255c6a4bc95d7e7aa51c4870c3146939d962e2249113c2269a92eecfb040344

[TRUNCATED]

```md
## ADDED Requirements

### Requirement: Buyer Chat Interface
买家端 Web 聊天页面 SHALL 提供微信风格的即时消息体验，包含消息气泡列表和底部输入框。进入页面后 SHALL 自动滚动到底部。上滑 SHALL 加载历史消息。

#### Scenario: Enter chat page
- **WHEN** 买家导航到 /ai
- **THEN** 显示聊天界面，消息列表自动滚动到底部

#### Scenario: Load history
- **WHEN** 买家在消息列表上滑
- **THEN** 加载更多历史消息

#### Scenario: Send message
- **WHEN** 买家在输入框输入文本并点击发送
- **THEN** 消息以买家气泡格式显示在列表中

### Requirement: Intent Routing
后端 SHALL 使用 Ollama Qwen2.5:7b 对买家每条消息进行意图分类，路由到对应处理逻辑（FAQ / 退单 / 人工 / 问候）。

#### Scenario: FAQ intent
- **WHEN** 买家提问关于产品功能或使用的问题
- **THEN** 系统路由到 FAQ 知识库检索

#### Scenario: Refund intent
- **WHEN** 买家提出退单请求
- **THEN** 系统路由到退单模拟流程

#### Scenario: Human handoff
- **WHEN** 买家明确要求人工服务或无法识别的复杂问题
- **THEN** 系统标记会话为待人工处理，并通知买家已转接

#### Scenario: Greeting
- **WHEN** 买家发送问候语
- **THEN** 系统返回欢迎消息

### Requirement: FAQ Knowledge Base
Admin 后台 SHALL 支持上传 Markdown 文档管理 FAQ 知识库。上传的文档 SHALL 自动切片并向量化存储到 ChromaDB。Admin 可以查看和删除已上传的文档。

#### Scenario: Upload FAQ document
- **WHEN** Admin 在 FAQ 管理页面选择 MD 文件并上传
- **THEN** 文档被切分成片段，生成向量嵌入后存入 ChromaDB

#### Scenario: List FAQ documents
- **WHEN** Admin 打开 FAQ 管理页面
- **THEN** 显示所有已上传文档的列表（文件名、上传时间、片段数）

#### Scenario: Delete FAQ document
- **WHEN** Admin 在文档列表点击删除
- **THEN** 文档及其所有向量片段从 ChromaDB 移除

### Requirement: AI Q&A
系统 SHALL 对 FAQ 意图的消息进行语义相似度检索，将最相关片段作为上下文发送给 Ollama，生成最终答案并通过 SSE 流式返回给买家。

#### Scenario: FAQ match found
- **WHEN** 买家提问且 FAQ 知识库中匹配到高相似度片段
- **THEN** AI 基于检索到的上下文生成答案，逐块推送到前端

#### Scenario: No FAQ match
- **WHEN** FAQ 知识库中无足够相似片段
- **THEN** 系统转人工处理

### Requirement: Human Agent Chat
Admin 后台 SHALL 展示所有需要人工处理的会话列表。Admin 点击某个会话 SHALL 弹出聊天窗口，输入消息后发送给买家。买家端 SHALL 实时收到 Admin 回复。

#### Scenario: View conversations
- **WHEN** Admin 打开客服消息页面
- **THEN** 显示所有待处理和已处理的会话列表

#### Scenario: Admin reply
- **WHEN** Admin 在弹窗中输入消息并发送
- **THEN** 消息保存到对应会话，买家端通过 SSE 收到回复

### Requirement: Refund Simulation
系统 SHALL 在意图识别为退单后，引导买家输入订单号、退款原因、退款金额，然后返回退单处理成功。

#### Scenario: Submit refund
- **WHEN** 买家完成退单信息输入
- **THEN** 系统返回"退单申请已提交，处理成功"

```

Full source: openspec/changes/ai-customer-service/specs/ai-customer-service/spec.md

