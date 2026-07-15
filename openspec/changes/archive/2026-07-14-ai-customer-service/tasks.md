## 1. 后端基础：数据模型与依赖
- [x] 1.1 安装后端依赖：langchain、langchain-ollama、langgraph、llama-index、llama-index-vector-stores-chroma、chromadb、sse-starlette
- [x] 1.2 创建 Conversation / Message / FAQDocument SQLAlchemy 模型

## 2. 后端核心：LangChain 集成层
- [x] 2.1 实现 ChatOllama / OllamaEmbeddings 封装（基于 langchain-ollama）
- [x] 2.2 实现 StreamCallbackHandler（LangChain token 事件 → SSE 队列）
- [x] 2.3 实现 prompt 模板 + OutputParser（意图分类 JSON 输出）

## 3. 后端核心：LlamaIndex RAG 管线
- [x] 3.1 实现 FaqIndexService（MD 上传 → 切片 → VectorStoreIndex 构建）
- [x] 3.2 实现 FaqRetriever（语义检索 top_k=3，相似度阈值过滤）
- [x] 3.3 实现 FAQ 文档 CRUD（List/Delete + ChromaDB collection 同步）

## 4. 后端核心：LangGraph 工作流
- [x] 4.1 定义 ConversationState TypedDict + 状态图节点
- [x] 4.2 实现 classify_intent 节点（调用 LangChain 意图分类）
- [x] 4.3 实现 retrieve_faq → answer_faq 节点链
- [x] 4.4 实现 collect_refund_info → process_refund 状态机
- [x] 4.5 实现 handle_greeting / handoff_human 节点

## 5. 后端核心：数据模型与仓库
- [x] 5.1 创建 Conversation / Message / FAQDocument SQLAlchemy 模型（已在 1.2）
- [x] 5.2 实现会话与消息管理服务（CRUD）

## 6. 后端 API：Web 端
- [x] 6.1 创建 `POST /api/web/ai/chat` SSE 流式聊天接口（驱动 LangGraph）
- [x] 6.2 创建 `GET /api/web/ai/conversations` 获取会话列表
- [x] 6.3 创建 `GET /api/web/ai/conversations/:id/messages` 获取消息历史
- [x] 6.4 在 main.py 注册新路由

## 7. 后端 API：Admin 端
- [x] 7.1 创建 FAQ 文档 CRUD API（上传/列表/删除）
- [x] 7.2 创建客服会话列表 API
- [x] 7.3 创建 Admin 发送消息 API
- [x] 7.4 在 main.py 注册新路由

## 8. Web 前端：AI 客服聊天界面
- [x] 8.1 替换占位页为聊天界面（消息列表 + 输入框组件）
- [x] 8.2 实现消息气泡组件（买家/AI/Admin/系统消息样式）
- [x] 8.3 实现 SSE 流式渲染（ReadableStream 逐块追加）
- [x] 8.4 实现自动滚动到底部 + 上滑加载历史

## 9. Admin 前端：FAQ 管理
- [x] 9.1 创建 FAQ 列表页面（展示文档列表 + 删除按钮）
- [x] 9.2 实现 MD 文件上传组件
- [x] 9.3 侧边栏新增「FAQ 管理」导航项

## 10. Admin 前端：客服消息
- [x] 10.1 创建客服会话列表页面
- [x] 10.2 实现点击会话弹出聊天窗口
- [x] 10.3 实现 Admin 发送消息功能
- [x] 10.4 侧边栏新增「客服消息」导航项

## 11. SDK 扩展
- [x] 11.1 在 SDK 中新增 AI 客服相关 API 函数（chat、conversations、messages）
