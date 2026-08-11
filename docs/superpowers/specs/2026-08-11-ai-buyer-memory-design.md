# AI 客服长期记忆设计（核心记忆块）

日期：2026-08-11

## 背景

现有 AI 智能客服（`backend/app/domain/ai`）已有会话级"短期记忆"：每次 `process_message` 从 SQLite 加载会话消息，经 `trim_history`（超预算则对旧消息 LLM 摘要）压缩后注入上下文。但记忆不跨会话：买家换一次会话说"我叫李女士"，新会话又要重复。

本次为 AI 客服增加**买家级长期记忆**：跨会话记住称呼/偏好/历史事件/待办前情，新会话自动带上，无需重复提问。

## 目标

- 每个买家一条持久记忆块，内容为分类结构化事实（称呼/偏好/历史/待办）。
- 新会话开始时，记忆块以 `SystemMessage` 注入上下文，AI 可自然使用但不主动炫耀。
- 两个写入时机，均含"价值判断"（不值得长期保留的事实不写入）：
  - 会话结束（买家离开聊天页，前端 beacon 触发 close）。
  - 用户明确要求记忆（如"请记住我叫李女士"）。
- 记忆抽取/写入失败绝不影响当轮聊天回复（降级日志）。
- 无管理界面，记忆不在前端展示，仅在 AI 回复中体现。

## 方案选型

对比三种业界做法：

| 方案 | 做法 | 取舍 |
|---|---|---|
| A ✅ | **核心记忆块**（MemGPT 式）：每买家一条 LLM 维护的文本记忆块，读写 SQLite，LLM 合并更新。 | 简单、可控、适合 Qwen2.5:7b 小模型与 MVP 规模；检索粒度为整块，非逐条相关检索 |
| B | 向量语义记忆：历史会话切片向量化存 ChromaDB，运行时检索相关片段 | 召回精确，但 7b 下质量/成本难控，MVP 偏重 |
| C | A+B 混合（MemGPT 完整形态） | 最接近业界最佳实践，但 scope 最大 |

**选定方案 A**：核心记忆块是长期记忆的本质形态，也是后续演进 B/C 的坚实基础。

## 设计

### 1. 数据模型（新表 `buyer_memory`）

`backend/app/models/buyer_memory.py`：

```python
class BuyerMemory(Base):
    __tablename__ = "buyer_memory"

    id: int (PK, autoincrement)
    buyer_id: int (Integer, UniqueIndex)   # 一买家一条记忆块
    content: Text                            # 记忆块正文（分类结构化文本）
    version: int (Integer, default=1)        # 乐观锁版本，防并发覆盖
    created_at: datetime
    updated_at: datetime
```

在 `models/__init__.py` 注册。SQLite 建表遵循现有约定（测试 fixture 统一 `create_all`，开发库由 migrate 处理）。

### 2. 记忆块内容格式

`content` 为 LLM 输出的分类文本，固定四类（没有的类别写"暂无"或省略单行）：

```
【称呼/身份】李女士
【偏好】偏好纯棉材质，关心发货时效
【历史事件】2026-08 曾咨询 ORD-xxx 退款进度
【待办/前情】退款 ORD-xxx 尚未到账，可能再次咨询
```

### 3. 新模块 `backend/app/domain/ai/memory/`

- `__init__.py`：导出领域服务与 repo。
- `memory_repo.py`：CRUD。
  - `get_by_buyer(db, buyer_id) -> BuyerMemory | None`
  - `upsert(db, buyer_id, content, expected_version) -> bool`：版本乐观锁——新买家插入（version=1）；旧买家若传参版本与库中当前版本不一致返回 `False` 不写，一致则更新并 `version += 1`。
  - `list_all(db, limit)`（预留，Admin 后续可扩展查看）。
- `memory_service.py`：
  - `update_memory(db, buyer_id, conversation_messages) -> MemoryUpdateResult`：LLM 合并更新（见下）。
  - `get_memory_block(db, buyer_id) -> str | None`：取当前记忆块，超 `ai_memory_budget_tokens` 预算时按字符硬截断兜底。
- `prompts.py`：
  - `MEMORY_UPDATE_SYSTEM_PROMPT`：价值判断指令 + 输出格式（`{"changed": bool, "content": "新记忆块"}`）。
  - `MEMORY_INJECT_SYSTEM_PROMPT`：注入模板"以下是用户长期信息，仅在相关时自然使用，不要主动炫耀"。

`update_memory` 流程：

1. 取旧记忆块（无则用空模板）。
2. LLM 指令输入「旧记忆块 + 本轮对话（用户/客服消息按轮排列）」，输出 JSON。
3. `changed=false` → 返回 `changed=False`，**不写库**。
4. `changed=true` → `upsert`。
5. LLM 报错 / JSON 解析失败 → `logger.warning`，返回失败结果，**不影响调用方**。

`MemoryUpdateResult`：

```python
@dataclass
class MemoryUpdateResult:
    changed: bool
    content: str | None   # changed=True 时为新记忆块；否则 None
    error: str | None
```

### 4. 写入时机

**时机 A：会话结束（前端 beacon）**

当前会话生命周期缺陷：前端总是复用最新 active 会话，不存在"会话关闭"。补一个显式关闭点：

- 后端新增 `POST /api/v1/web/ai/conversations/{id}/close`：
  - 会话 `status -> "closed"`。
  - 对该会话**全部** user/ai 消息执行 `update_memory`（价值判断会丢弃无需长期保留的内容）。
  - close 后该会话不再被复用为"本次会话"。
- 前端 `use-sse-chat` 页面卸载 / 离开导航时用 `navigator.sendBeacon` 触发 close（不阻塞、失败静默）。sendBeacon 仅支持 POST，body 可为空。

**配套调整（保证关闭语义成立）**：买家端 `GET /api/v1/web/ai/conversations` 只返回 active 会话。前端 `loadConversation` 因此只会续接 active 会话；无 active 会话时 `conversationId=null`，发消息时后端新建 active 会话。这样每次访问形成一个清晰的会话边界，closed 会话永不续接，也不会把整段跨天历史塞进上下文中（历史沉淀进记忆块）。

**时机 B：用户明确要求记忆**

`process_message` 开头做轻量检测（关键词：记住 / 请记住 / 以后叫我 / 备注 / 帮我记着…），命中则同一轮内同步执行 `update_memory`，并把"已记下"写进 AI 回复。检测为启发式：关键词命中不代表一定要写入，最终写入与否仍由 `update_memory` 的价值判断决定。

### 5. 引擎集成（`engine.py` / `api/web/ai.py`）

- `ChatEngine.process_message`：
  1. 先按 `conversation_id` 取会话拿到 `buyer_id`（`ConversationRepository.get_by_id`；会话新建时 buyer_id 来自请求上下文，沿用现有 buyer_id=1 的占位逻辑）。
  2. 载入 `get_memory_block`，非空时插为 `SystemMessage` 置于 `trim_history` 结果之前。
  3. 若命中"明确要求记忆"关键词，`await update_memory(...)`；成功且 changed 时在回复文案末尾追加一句确认（如"好的，我已记下。"）。
  4. 其余流程不变（FAQ 检索 / 售后 / 意图等），记忆注入不影响现有路由。
- `api/web/ai.py`：新增 `POST /conversations/{id}/close`，返回关闭结果与是否更新记忆。

### 6. 配置（`core/config.py`）

- `ai_memory_budget_tokens: int = 500`：记忆注入的 token 预算，超预算硬截断。

### 7. 错误处理

- LLM 抽取失败 / 超时 → 降级，不影响聊天（`update_memory` 内部 catch，返回 `error`）。
- 记忆块超预算 → `get_memory_block` 截断兜底。
- upsert 乐观锁冲突 → 本次放弃更新但记录日志，不重试（避免并发风暴）。

## 测试

- `test_buyer_memory.py`（新）：`get_by_buyer` / 首次插入 / 版本乐观锁（旧版本写失败）/ upsert 成功后 version+1。
- `test_memory_update.py`（新）：mock LLM——有价值事实 → changed=True 且落库；无价值闲聊 → changed=False 不落库；LLM 报错 → 返回 error 不抛异常。
- `test_ai_memory_injection.py`（新）：记忆块注入为 SystemMessage 且位于 trim 摘要之前；无记忆块时不注入；显式记忆命中返回确认文案。
- `test_ai_workflow.py`：现有意图路由回归（注入 SystemMessage 不破坏 FAQ/售后/人工路由）。
- `test_api_ai.py` / 相应 API 测试：`POST /conversations/{id}/close` 标记 closed 并触发记忆抽取。

## 风险与注意

- close 依赖前端 beacon，浏览器崩溃/强杀可能丢失"会话结束"；因 Memory store 每轮也可被后续 close 与新会话 close 覆盖，能力可接受（MVP 不做后台兜底任务）。
- 7b 模型 JSON 输出可能不稳定 → 解析失败按"不写入"降级，并记录日志便于调优提示词。
- 记忆注入会占用上下文预算，需保证 `ai_memory_budget_tokens` + 现有保留预算之和仍小于上下文窗口。
- 会话关闭后旧会话的"新消息"不会触碰记忆（closed 即冻结），避免重复抽取。