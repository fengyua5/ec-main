# Langfuse 监控接入设计

日期：2026-08-05
状态：已批准（用户确认端口 5000）

## 背景与目标

项目已接入 RAG 智能客服（FAQ 检索 + LLM 回答），但目前没有任何可观测性手段，无法评估检索质量与回答质量。目标是在项目中接入 Langfuse 监控：

1. 自动追踪对话链路中的 LLM 调用（意图识别、FAQ 回答），获得 token 用量、耗时、输入输出。
2. 记录 RAG 检索细节（查询、召回 chunk、分数、来源、是否转人工），便于在面板上人工判断召回是否准确、回答是否基于证据。
3. 无密钥时优雅降级，不影响现有业务链路。

评估方式：第一阶段采用人工分析（在 Langfuse 面板查看每条 trace 的召回与回答），暂不配置自动评分或 RAGAS 指标。

## 现状梳理

- LLM 为本地 Ollama：`qwen2.5:7b`（聊天）、`nomic-embed-text`（向量），统一封装在 `backend/app/domain/ai/llm/chat.py`。
- 对话工作流为 LangGraph：`ChatEngine.process_message` → `graph.ainvoke(state)`（`backend/app/domain/ai/workflow/engine.py`）。图中 `classify_intent`、`answer_faq` 两个节点调用 LLM。
- RAG 检索：`FaqRetriever.retrieve`（`backend/app/domain/ai/rag/retriever.py`），向量召回 + BM25 + RRF 融合，无 LLM 精排。检索在 `retrieve_faq` 节点内完成，结果写入 `state.skills.faq.context`（含 content、score、source）。
- 依赖栈：langchain>=0.3、langchain-ollama、langgraph>=0.2，尚未引入 langfuse。
- `infra/` 下已有 `sqlite` 组件模式（`infra/sqlite/README.md`），Langfuse 沿用该模式放 `infra/langfuse/`。

## 方案选择

采用 **方案 A：langfuse CallbackHandler 自动追踪 + 手动补检索元数据**。

- 用 `langfuse.callback.CallbackHandler`，通过 `graph.ainvoke(state, config={"callbacks": [handler]})` 自动捕获两个 LLM 调用，在面板获得标准 LLM 视图（token、耗时、输入输出）。
- 检索细节（召回 chunk、score、来源、是否转人工）在 graph 结束后用 `handler.get_span().update(metadata=...)` 挂到同一 trace。
- 无密钥返回 `None`，链路零侵入优雅降级。

备选方案（不采用）：
- 纯 SDK 手动追踪：LLM 调用不会被自动捕获，拿不到标准 LLM 视图，且 `process_message` 为 async generator，手动埋点麻烦。
- 日志埋点后离线导入：无法实时观测，多一套导入脚本，过度设计。

## 架构与组件

### 1. Langfuse 部署（`infra/langfuse/`）

新增 `infra/langfuse/docker-compose.yml`：postgres（Langfuse 元数据）+ langfuse 服务容器，映射宿主机端口 **5000**。新增 `infra/langfuse/README.md` 说明启动步骤、初始化账号、面板访问地址。

- 面板地址：`http://localhost:5000`
- `LANGFUSE_HOST` 默认值：`http://localhost:5000`

### 2. 后端配置（`backend/app/core/config.py` + `backend/.env.example`）

新增配置项：

| 配置键 | 默认值 | 说明 |
| --- | --- | --- |
| `LANGFUSE_PUBLIC_KEY` | `""` | Langfuse 项目公钥 |
| `LANGFUSE_SECRET_KEY` | `""` | Langfuse 项目私钥 |
| `LANGFUSE_HOST` | `http://localhost:5000` | Langfuse 服务地址 |

三个值缺任意一个（公钥/私钥为空或 HOST 为空）即视为未配置，追踪自动禁用。

### 3. 追踪工厂（新增 `backend/app/domain/ai/llm/tracing.py`）

`get_langfuse_handler()`：

- 校验配置是否完整；不完整则记录一条 info 日志并返回 `None`。
- 完整则创建 `Langfuse` 客户端（传入公钥、私钥、host）与 `CallbackHandler(langfuse=client)`，模块级缓存为单例，保证并发安全。
- 导出 `is_langfuse_enabled()` 供测试断言。

### 4. 引擎接线（`backend/app/domain/ai/workflow/engine.py`）

`ChatEngine.process_message`：

- 调用 `get_langfuse_handler()`；handler 非空时 `graph.ainvoke(state, config={"callbacks": [handler]})`。
- graph 返回后，从 `result` 提取检索统计：
  - `skills.faq.context`：top-N 召回（每条 content、score、source）
  - `flow.intent`：意图判定（faq / human / greeting / refund），其中 `human` 表示检索失败转人工
  - 用户查询与最终回答作为 trace 的 input/output
- `handler.get_span().update(metadata={"retrieval": {...}})` 写入 trace metadata。
- 其余流程（消息落库、SSE 事件 yield）不变。

检索 metadata 结构（写入 trace span 的 metadata）:

```
{
  "retrieval": {
    "query": "<用户问题>",
    "intent": "<faq|human|...>",
    "hits": [
      {"content": "<chunk 文本>", "score": 0.xx, "source": "<来源文件>"}
    ],
    "hit_count": 3
  }
}
```

### 5. 依赖

`backend/pyproject.toml` 新增 `langfuse>=2.0`。

## 数据流

```
用户提问
  → ChatEngine.process_message
      → graph.ainvoke(config={"callbacks": [handler]})
          ├─ classify_intent 节点 (LLM)  → 自动 span
          ├─ retrieve_faq 节点 (检索)     → 结果进 state.skills.faq.context
          └─ answer_faq 节点 (LLM)       → 自动 span
      → handler.get_span().update(metadata=retrieval 统计)
      → yield SSE 事件（不变）
```

## 错误处理

- 未配置密钥：`get_langfuse_handler()` 返回 `None`，graph 不带 callbacks，链路与现在完全一致，仅在日志提示。
- Langfuse 服务不可达：Langfuse SDK 默认异步批量上报，失败不抛异常到业务链路；同时 handler 仅在 graph 调用期间生效，不影响 SSE 输出。
- `handler.get_span()` 取不到 span（极端情况）：用 `try/except` 包裹，异常仅记日志，不影响主流程。

## 测试

- 新增 `backend/tests/test_langfuse_tracing.py`：
  1. 配置完整时 `get_langfuse_handler()` 返回非 None。
  2. 缺少公钥/私钥/HOST 任一 → 返回 None。
  3. mock `CallbackHandler`，断言 `graph.ainvoke` 收到含 callbacks 的 config。
  4. mock `handler.get_span()`，断言检索 metadata 写入（hits、intent、hit_count）。
- 现有 104 个测试保持通过（未配置时链路不变）。

## 验证方式

1. `docker compose -f infra/langfuse/docker-compose.yml up -d`，访问 `http://localhost:5000` 完成初始化账号、创建项目、获取公钥/私钥。
2. 在 `backend/.env` 填入密钥，重启后端。
3. 在 AI 客服页提问，观察 Langfuse 面板出现 trace：LLM 两个 span + 检索 metadata。
4. 面板上按 trace 逐条检查：召回 chunk 是否相关、回答是否基于召回内容、意图判定是否合理。
