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

## 7. Admin 前端：客服消息
- [ ] 7.1 创建客服会话列表页面
- [ ] 7.2 实现点击会话弹出聊天窗口
- [ ] 7.3 实现 Admin 发送消息功能
- [ ] 7.4 侧边栏新增「客服消息」导航项

## 8. SDK 扩展
- [ ] 8.1 在 SDK 中新增 AI 客服相关 API 函数（chat、conversations、messages）
