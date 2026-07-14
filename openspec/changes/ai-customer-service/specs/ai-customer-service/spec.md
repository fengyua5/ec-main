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

### Requirement: Conversation Persistence
所有消息 SHALL 持久化到 SQLite 数据库。买家重新进入聊天页面 SHALL 恢复最近会话的完整消息历史。

#### Scenario: Restore conversation
- **WHEN** 已发送过消息的买家重新进入 /ai
- **THEN** 显示最近会话的全部历史消息，并自动滚动到底部

### Requirement: Admin Sidebar Navigation
Admin 侧边栏 SHALL 新增「FAQ 管理」和「客服消息」两个导航项。

#### Scenario: Navigate to FAQ management
- **WHEN** Admin 点击侧边栏「FAQ 管理」
- **THEN** 跳转到 FAQ 管理页面

#### Scenario: Navigate to chat
- **WHEN** Admin 点击侧边栏「客服消息」
- **THEN** 跳转到客服会话列表页面
