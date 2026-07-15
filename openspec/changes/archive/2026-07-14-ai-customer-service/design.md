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

- Ollama API base URL 的配置方式（环境变量 `OLLAMA_BASE_URL`）？
- FAQ 文档是否需要按用户角色隔离（buyer vs admin）？
