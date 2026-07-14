---
comet_change: ai-customer-service
role: technical-design
canonical_spec: openspec
---

# AI 智能客服系统设计

## 目标

为 EC Main 平台提供完整的 AI 智能客服能力，涵盖买家端 Web 实时聊天、Admin FAQ 知识库管理和人工客服消息处理。

## 架构

```
┌──────────────────────────────────────────────────────────┐
│                   前端应用层                               │
│  ┌──────────────────┐  ┌───────────────────────────────┐ │
│  │  apps/web        │  │  apps/admin                   │ │
│  │  /ai 聊天页面     │  │  /faq FAQ 管理               │ │
│  │  微信风格气泡     │  │  /chat 客服消息列表           │ │
│  │  SSE 流式渲染     │  │  弹窗回复                     │ │
│  └───────┬──────────┘  └───────────┬───────────────────┘ │
│          │                        │                      │
│  ┌───────┴────────────────────────┴───────────────────┐  │
│  │  packages/sdk (ai 方法)                             │  │
│  └───────────────────────┬───────────────────────────┘  │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                   后端 API 层                            │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  /api/v1/web/ai/*    买家 AI 客服               │    │
│  │  POST /chat          SSE 流式聊天              │    │
│  │  GET /conversations   会话列表                  │    │
│  │  GET /conversations/:id/messages 消息历史       │    │
│  └──────────────────────┬──────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  /api/v1/admin/ai/*  Admin FAQ 管理             │    │
│  │  POST /faq           上传 MD 文档               │    │
│  │  GET /faq            文档列表                   │    │
│  │  DELETE /faq/:id     删除文档                   │    │
│  └──────────────────────┬──────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  /api/v1/admin/chat/* Admin 客服消息            │    │
│  │  GET /conversations    会话列表                 │    │
│  │  POST /reply          发送消息 (SSE 推送)       │    │
│  └──────────────────────┬──────────────────────────┘    │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                  服务层（AI 引擎）                        │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  LangGraph 工作流引擎（app/domain/ai/workflow/） │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │  StateGraph                              │   │    │
│  │  │  ├─ classify_intent    意图分类节点       │   │    │
│  │  │  ├─ handle_greeting    问候处理节点       │   │    │
│  │  │  ├─ retrieve_faq       FAQ 检索节点       │   │    │
│  │  │  ├─ answer_faq         AI 问答节点        │   │    │
│  │  │  ├─ collect_refund     退单信息收集节点   │   │    │
│  │  │  ├─ process_refund     退单处理节点       │   │    │
│  │  │  └─ handoff_human      转人工节点         │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  └──────────────────────┬──────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  LlamaIndex RAG 管线（app/domain/ai/rag/）      │    │
│  │  ├─ FaqIndex        文档索引（VectorStoreIndex） │    │
│  │  ├─ FaqRetriever    语义检索（top_k=3）         │    │
│  │  └─ FaqQueryEngine  FAQ QA 引擎                │    │
│  └──────────────────────┬──────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  LangChain 集成层（app/domain/ai/llm/）         │    │
│  │  ├─ ChatOllama       Qwen2.5:7b 对话模型       │    │
│  │  ├─ OllamaEmbeddings nomic-embed-text 嵌入      │    │
│  │  ├─ prompts.py       提示词模板                 │    │
│  │  └─ streaming.py     流式回调处理器             │    │
│  └──────────────────────┬──────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  app/domain/ai/models/                          │    │
│  │  └─ conversation.py  会话 + 消息仓库            │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                  数据层                                  │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  SQLite                                         │    │
│  │  ┌─────────────┐  ┌──────────────────┐          │    │
│  │  │ conversations│  │ messages         │          │    │
│  │  └─────────────┘  └──────────────────┘          │    │
│  └──────────────────────┬──────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  ChromaDB (文件型, chroma_data/)                │    │
│  │  ┌──────────────────────────────────────┐       │    │
│  │  │ FAQ 文档切片 + 向量嵌入（LlamaIndex 管理）│   │    │
│  │  └──────────────────────────────────────┘       │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Ollama (localhost:11434)                         │   │
│  │  ┌────────────────┐  ┌──────────────────────┐   │   │
│  │  │ Qwen2.5:7b     │  │ nomic-embed-text      │   │   │
│  │  │ (LangChain)    │  │ (LangChain Embeddings)│   │   │
│  │  └────────────────┘  └──────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## 组件说明

### 1. LangGraph 工作流引擎（Workflow Engine）

整个 AI 客服的核心是一个 LangGraph `StateGraph`，定义对话状态和节点路由。每条买家消息驱动一次图执行。

**State 定义：**

```python
class ConversationState(TypedDict):
    messages: list           # 对话历史
    intent: str              # 当前意图分类结果
    confidence: float        # 置信度
    refund_info: dict        # 退单收集信息 {"order_no", "reason", "amount"}
    faq_context: list        # FAQ 检索到的相关片段
    response: str            # 本次回复内容
```

**节点与边：**

```
buyer_input
    │
    ▼
classify_intent  ──── LLM prompt 分类
    │
    ├── greeting  →  handle_greeting  →  response
    ├── faq       →  retrieve_faq ──→ answer_faq ──→ response
    │                              │ (无匹配)
    │                              └──→ handoff_human
    ├── refund    →  collect_refund_info ──→ process_refund ──→ response
    │                                 │ (信息未齐)
    │                                 └──→ 等待用户补充
    └── human     →  handoff_human ──→ response
```

- `classify_intent`: 使用 LangChain `ChatOllama` + `ChatPromptTemplate` 进行意图分类，返回 JSON 格式 `{"intent": "...", "confidence": N}`
- `retrieve_faq`: 调用 LlamaIndex `FaqRetriever` 语义检索
- `answer_faq`: 拼接 prompt（system + FAQ 上下文 + 用户问题），通过 `ChatOllama` 流式生成
- `collect_refund_info`: 状态机收集，未齐则返回引导消息
- `handoff_human`: 标记会话 `waiting_human`，返回转接通知

### 2. LlamaIndex RAG 管线（FAQ Knowledge Base）

Admin 上传 Markdown 文档 → 文档解析 → 切片 → 向量化 → 索引存储。

**索引流程（Admin 上传时触发）：**

```
MD 文档 → SimpleDirectoryReader
        → SentenceSplitter (chunk_size=256, chunk_overlap=50)
        → OllamaEmbeddings (nomic-embed-text)
        → ChromaVectorStore → VectorStoreIndex
```

**检索流程（FAQ 节点触发）：**

```
VectorStoreIndex.as_retriever(similarity_top_k=3)
    → 余弦相似度匹配
    → 相似度 < 0.6 时视为无匹配 → handoff_human
    → 返回 top_k 文本片段作为 LLM 上下文
```

**文档管理：** FAQDocument 表记录文档元数据，ChromaDB collection_id 关联向量数据。删除文档时清除对应 collection。

### 3. LangChain 集成层（LLM Abstraction）

统一管理所有 Ollama 调用：

| 用途 | 组件 | 行为 |
|------|------|------|
| 意图分类 | `ChatOllama(model="qwen2.5:7b", temperature=0)` | 非流式，JSON 输出 |
| FAQ 问答 | `ChatOllama(model="qwen2.5:7b", temperature=0.3)` | 流式，SSE 推送 |
| 退单引导 | `ChatOllama(model="qwen2.5:7b", temperature=0.5)` | 非流式，对话式引导 |
| 文本嵌入 | `OllamaEmbeddings(model="nomic-embed-text")` | 批量/单次嵌入 |

**流式处理：**

```python
class SSECallbackHandler(BaseCallbackHandler):
    """将 LangChain stream 事件转换为 SSE 格式推送给前端"""
    def on_llm_new_token(self, token, **kwargs):
        sse_queue.put({"type": "token", "content": token})
```

### 4. 人工客服转接

- `handoff_human` 节点标记会话 `status = waiting_human`
- 给买家发送系统消息："正在为您转接人工客服..."
- Admin 后台 /chat 页面出现该会话
- Admin 点击会话弹窗回复，消息通过 SSE 推送至买家端
- 管理员回复后会话 status 恢复为 active（可选）

### 5. 退单模拟（LangGraph 多轮交互）

退单流程在 LangGraph 中实现为状态机，通过 `collect_refund_info` 节点逐步收集：

```
collect_refund_info 节点执行逻辑：
1. 检查 state.refund_info 缺少哪些字段
2. 缺少 order_no  → 返回 "请提供订单号"
3. 缺少 reason    → 返回 "请提供退款原因"
4. 缺少 amount    → 返回 "请输入退款金额"
5. 全部齐备      → 切换至 process_refund 节点

process_refund 节点：
1. 返回 "退单申请已提交，处理成功"
2. 记录退单信息到数据库（预留扩展）
3. 会话 status 不变，可继续提问
```

## 数据模型

```
Conversation
├── id: Integer (PK, auto-increment)
├── buyer_id: Integer (FK -> users.id)
├── status: String (active / waiting_human / resolved)
├── created_at: DateTime
└── updated_at: DateTime

Message
├── id: Integer (PK, auto-increment)
├── conversation_id: Integer (FK -> conversations.id)
├── sender: String (buyer / ai / admin)
├── content: Text
├── msg_type: String (text / system)
└── created_at: DateTime

FAQDocument
├── id: Integer (PK, auto-increment)
├── filename: String
├── chunk_count: Integer
├── created_at: DateTime
└── chroma_collection_id: String
```

## API 设计

### Web 端 AI 客服

```
POST /api/v1/web/ai/chat
  Request:  { "conversation_id": int|null, "content": "string" }
  Response: SSE stream (text/event-stream)
    data: {"type": "token", "content": "..."}
    data: {"type": "done"}
    data: {"type": "intent", "value": "faq|refund|human|greeting"}

GET /api/v1/web/ai/conversations
  Response: { "conversations": [...] }

GET /api/v1/web/ai/conversations/{id}/messages
  Response: { "messages": [...] }
```

### Admin FAQ 管理

```
POST /api/v1/admin/ai/faq
  Request: multipart/form-data (file: .md)
  Response: { "id": int, "filename": "string", "chunk_count": int }

GET /api/v1/admin/ai/faq
  Response: { "documents": [...] }

DELETE /api/v1/admin/ai/faq/{id}
  Response: { "success": true }
```

### Admin 客服消息

```
GET /api/v1/admin/ai/conversations
  Response: { "conversations": [...] }

POST /api/v1/admin/ai/conversations/{id}/reply
  Request: { "content": "string" }
  Response: SSE push to buyer

GET /api/v1/admin/ai/conversations/{id}/messages
  Response: { "messages": [...] }
```

## 关键技术选型

| 决策 | 选型 | 替代方案 | 理由 |
|------|------|---------|------|
| 工作流引擎 | LangGraph (StateGraph) | 手写路由逻辑 | 可视化状态机，便于扩展和维护 |
| RAG 管线 | LlamaIndex | 直接 ChromaDB 查询 | 索引/检索/QA 一站式，SentenceSplitter 中文好 |
| LLM 集成 | LangChain (ChatOllama) | 直接 httpx 调用 | 流式回调、prompt 模板、输出解析器统一管理 |
| 向量数据库 | ChromaDB (persistent) | pgvector | SQLite 环境，无需额外数据库服务 |
| 文本嵌入 | Ollama nomic-embed-text via LangChain | sentence-transformers | 与 Ollama 统一管理，减少依赖 |
| 流式传输 | SSE (FastAPI StreamingResponse) | WebSocket | AI 回复 + Admin 消息均为单向推送，SSE 更简单 |
| 意图识别 | LangChain prompt + OutputParser | 传统 NLP 分类器 | 无需训练数据，冷启动友好 |
| Ollama 地址 | 环境变量 OLLAMA_BASE_URL | 硬编码 | 灵活支持不同环境 |
| 消息持久化 | SQLite | PostgreSQL | 初期量小，后续可迁移 |

## 后端依赖

```txt
# LLM / AI 框架
langchain>=0.3.0
langchain-ollama>=0.2.0
langgraph>=0.2.0
llama-index>=0.12.0
llama-index-vector-stores-chroma>=0.3.0
llama-index-embeddings-langchain>=0.3.0

# 向量存储
chromadb>=0.5.0

# Web
fastapi>=0.115.0
sse-starlette>=2.0.0

# 其他
sqlalchemy>=2.0.0
httpx>=0.27.0
```

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| Ollama 未运行 | 后端捕获 LangChain 连接异常，返回"AI 服务暂不可用" |
| Ollama 响应慢 | 设置 30s 超时，超时后转人工 |
| 中文嵌入质量 | 使用 nomic-embed-text（中文支持），备选 bge-small-zh-v1.5 |
| SQLite 并发 | 初期消息量小；设置 WAL 模式优化 |
| MD 文件格式不一致 | 限制 5MB，UTF-8 编码，解析失败报友好错误 |
| 买家身份暂缺 | 使用 buyer_id=1 或临时 buyer_token 占位，后续完善 |
