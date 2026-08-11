# AI 客服长期记忆（核心记忆块）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 AI 客服增加买家级长期记忆：每买家一条持久记忆块（称呼/偏好/历史/待办），跨会话注入上下文；两个写入时机（会话结束 + 明确要求记忆）均含价值判断，失败降级不影响聊天。

**Architecture:** 新增 `buyer_memory` 表 + `backend/app/domain/ai/memory/` 模块（repo/service/prompts）。引擎在 `process_message` 中注入记忆块为 SystemMessage；新增 `POST /conversations/{id}/close` 供前端会话结束时触发记忆抽取；买家端 `GET /conversations` 改为只返回 active 会话，前端离开页面时 sendBeacon 触发 close。

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy / SQLite / Ollama Qwen2.5:7b / pytest / TypeScript (Next.js)

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `backend/app/models/buyer_memory.py` | 新建 `BuyerMemory` ORM 模型 |
| `backend/app/models/__init__.py` | 导出 `BuyerMemory` |
| `backend/app/domain/ai/memory/__init__.py` | 模块入口 |
| `backend/app/domain/ai/memory/memory_repo.py` | CRUD：`get_by_buyer` / `upsert` / `list_all` |
| `backend/app/domain/ai/memory/memory_service.py` | 领域服务：`update_memory` / `get_memory_block` |
| `backend/app/domain/ai/memory/prompts.py` | LLM 提示词 |
| `backend/app/api/web/ai.py` | 新增 `POST /conversations/{id}/close`；买家端只返回 active |
| `backend/app/domain/ai/workflow/engine.py` | `process_message` 注入记忆块 + 显式记忆关键词检测 |
| `backend/app/core/config.py` | 新增 `ai_memory_budget_tokens` 配置 |
| `apps/web/app/(main)/ai/hooks/use-sse-chat.ts` | 页面卸载时 sendBeacon 触发 close |
| `packages/sdk/src/ai.ts` | 新增 `closeConversation` 函数 |

---

## Task 1: BuyerMemory 模型

**Files:**
- Create: `backend/app/models/buyer_memory.py`
- Modify: `backend/app/models/__init__.py:1-8`

- [ ] **Step 1: 创建 BuyerMemory 模型**

`backend/app/models/buyer_memory.py`:

```python
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class BuyerMemory(Base):
    __tablename__ = "buyer_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [ ] **Step 2: 注册 BuyerMemory**

`backend/app/models/__init__.py` 追加 `from app.models.buyer_memory import BuyerMemory`，并加入 `__all__`。

- [ ] **Step 3: 运行确认建表通过**

Run: `cd backend && uv run pytest tests/test_after_sale_case.py -q`
Expected: PASS（`create_all` 会同时建 `buyer_memory` 表）

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/buyer_memory.py backend/app/models/__init__.py
git commit -m "feat(memory): 新增 BuyerMemory ORM 模型"
```

---

## Task 2: memory_repo.py

**Files:**
- Create: `backend/app/domain/ai/memory/__init__.py`
- Create: `backend/app/domain/ai/memory/memory_repo.py`
- Test: `backend/tests/test_buyer_memory.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_buyer_memory.py`:

```python
import pytest
from app.domain.ai.memory.memory_repo import get_by_buyer, upsert, list_all
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def test_get_by_buyer_returns_none_when_missing() -> None:
    db = SessionLocal()
    try:
        result = get_by_buyer(db, buyer_id=999)
        assert result is None
    finally:
        db.close()


def test_upsert_creates_new() -> None:
    db = SessionLocal()
    try:
        result = upsert(db, buyer_id=1, content="【称呼/身份】李女士", expected_version=0)
        assert result is True
        mem = get_by_buyer(db, buyer_id=1)
        assert mem is not None
        assert mem.content == "【称呼/身份】李女士"
        assert mem.version == 1
    finally:
        db.close()


def test_upsert_updates_same_version() -> None:
    db = SessionLocal()
    try:
        upsert(db, buyer_id=2, content="v1", expected_version=0)
        result = upsert(db, buyer_id=2, content="v2", expected_version=1)
        assert result is True
        mem = get_by_buyer(db, buyer_id=2)
        assert mem.content == "v2"
        assert mem.version == 2
    finally:
        db.close()


def test_upsert_rejects_stale_version() -> None:
    db = SessionLocal()
    try:
        upsert(db, buyer_id=3, content="v1", expected_version=0)
        result = upsert(db, buyer_id=3, content="v2", expected_version=0)
        assert result is False
        mem = get_by_buyer(db, buyer_id=3)
        assert mem.content == "v1"
        assert mem.version == 1
    finally:
        db.close()


def test_list_all_returns_all() -> None:
    db = SessionLocal()
    try:
        upsert(db, buyer_id=10, content="a", expected_version=0)
        upsert(db, buyer_id=11, content="b", expected_version=0)
        items = list_all(db)
        assert len(items) == 2
    finally:
        db.close()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && uv run pytest tests/test_buyer_memory.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 创建 memory_repo.py**

`backend/app/domain/ai/memory/__init__.py`:

```python
from app.domain.ai.memory.memory_repo import get_by_buyer, upsert, list_all

__all__ = ["get_by_buyer", "upsert", "list_all"]
```

`backend/app/domain/ai/memory/memory_repo.py`:

```python
from sqlalchemy.orm import Session
from app.models.buyer_memory import BuyerMemory


def get_by_buyer(db: Session, buyer_id: int) -> BuyerMemory | None:
    return db.query(BuyerMemory).filter(BuyerMemory.buyer_id == buyer_id).first()


def upsert(db: Session, buyer_id: int, content: str, expected_version: int) -> bool:
    existing = get_by_buyer(db, buyer_id)
    if existing is None:
        mem = BuyerMemory(buyer_id=buyer_id, content=content, version=1)
        db.add(mem)
        db.commit()
        return True
    if existing.version != expected_version:
        return False
    existing.content = content
    existing.version += 1
    db.commit()
    return True


def list_all(db: Session, limit: int = 50) -> list[BuyerMemory]:
    return db.query(BuyerMemory).order_by(BuyerMemory.updated_at.desc()).limit(limit).all()
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && uv run pytest tests/test_buyer_memory.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/domain/ai/memory/ backend/tests/test_buyer_memory.py
git commit -m "feat(memory): 新增 memory_repo CRUD（get/upsert/list）"
```

---

## Task 3: memory prompts

**Files:**
- Create: `backend/app/domain/ai/memory/prompts.py`

- [ ] **Step 1: 创建 prompts.py**

`backend/app/domain/ai/memory/prompts.py`:

```python
from langchain_core.prompts import ChatPromptTemplate

MEMORY_UPDATE_SYSTEM_PROMPT = """你是一个长期记忆更新器。你的任务是将对话中对用户有价值的信息合并到记忆块中。

规则：
1. 价值判断：只保留跨会话可复用的持久事实（称呼、偏好、长期话题、未完结待办）。
2. 丢弃：一次性闲聊、临时订单号（除非关联未完结待办）、重复信息。
3. 输出格式：严格按以下四类输出，没有的类别写"暂无"：
【称呼/身份】xxx
【偏好】xxx
【历史事件】xxx
【待办/前情】xxx
4. 如果旧记忆块已有信息，保留并合并新信息，不要丢失旧事实。
5. 如果对话中没有值得记住的信息，返回 {"changed": false}。

返回 JSON 格式：
{"changed": true/false, "content": "新记忆块文本（changed=true 时）"}"""

memory_update_prompt = ChatPromptTemplate.from_messages([
    ("system", MEMORY_UPDATE_SYSTEM_PROMPT),
    ("human", "旧记忆块：\n{old_memory}\n\n对话内容：\n{conversation}"),
])

MEMORY_INJECT_PREFIX = "以下是用户长期信息，仅在相关时自然使用，不要主动炫耀：\n"
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/domain/ai/memory/prompts.py
git commit -m "feat(memory): 新增记忆抽取与注入提示词"
```

---

## Task 4: memory_service.py

**Files:**
- Create: `backend/app/domain/ai/memory/memory_service.py`
- Test: `backend/tests/test_memory_update.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_memory_update.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.domain.ai.memory.memory_service import update_memory, get_memory_block
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


class TestUpdateMemory:
    @pytest.mark.asyncio
    async def test_changed_persists_new_memory(self) -> None:
        db = SessionLocal()
        try:
            with patch("app.domain.ai.memory.memory_service.get_chat_llm") as mock_llm_cls, \
                 patch("app.domain.ai.memory.memory_service.memory_update_prompt") as mock_prompt:
                mock_chain = AsyncMock()
                mock_chain.ainvoke.return_value = MagicMock(
                    content='{"changed": true, "content": "【称呼/身份】李女士\\n【偏好】偏好纯棉"}'
                )
                mock_prompt.__or__.return_value = mock_chain

                from langchain_core.messages import HumanMessage, AIMessage
                messages = [
                    HumanMessage(content="我叫李女士，我喜欢纯棉的"),
                    AIMessage(content="好的，李女士，纯棉的确实舒适。"),
                ]

                result = await update_memory(db, buyer_id=1, conversation_messages=messages)
                assert result.changed is True
                assert "李女士" in result.content

                from app.domain.ai.memory.memory_repo import get_by_buyer
                mem = get_by_buyer(db, buyer_id=1)
                assert mem is not None
                assert "李女士" in mem.content
                assert mem.version == 1
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_unchanged_does_not_persist(self) -> None:
        db = SessionLocal()
        try:
            with patch("app.domain.ai.memory.memory_service.get_chat_llm") as mock_llm_cls, \
                 patch("app.domain.ai.memory.memory_service.memory_update_prompt") as mock_prompt:
                mock_chain = AsyncMock()
                mock_chain.ainvoke.return_value = MagicMock(
                    content='{"changed": false}'
                )
                mock_prompt.__or__.return_value = mock_chain

                from langchain_core.messages import HumanMessage, AIMessage
                messages = [
                    HumanMessage(content="今天天气怎么样"),
                    AIMessage(content="抱歉，我是客服，无法回答天气问题。"),
                ]

                result = await update_memory(db, buyer_id=99, conversation_messages=messages)
                assert result.changed is False

                from app.domain.ai.memory.memory_repo import get_by_buyer
                mem = get_by_buyer(db, buyer_id=99)
                assert mem is None
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_llm_failure_returns_error(self) -> None:
        db = SessionLocal()
        try:
            with patch("app.domain.ai.memory.memory_service.get_chat_llm") as mock_llm_cls, \
                 patch("app.domain.ai.memory.memory_service.memory_update_prompt") as mock_prompt:
                mock_chain = AsyncMock()
                mock_chain.ainvoke.side_effect = RuntimeError("ollama down")
                mock_prompt.__or__.return_value = mock_chain

                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content="test")]

                result = await update_memory(db, buyer_id=1, conversation_messages=messages)
                assert result.changed is False
                assert result.error is not None
        finally:
            db.close()


class TestGetMemoryBlock:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_memory(self) -> None:
        db = SessionLocal()
        try:
            result = await get_memory_block(db, buyer_id=999)
            assert result is None
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_returns_content_when_exists(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.memory.memory_repo import upsert
            upsert(db, buyer_id=1, content="【称呼/身份】王五", expected_version=0)
            result = await get_memory_block(db, buyer_id=1)
            assert result is not None
            assert "王五" in result
        finally:
            db.close()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && uv run pytest tests/test_memory_update.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 创建 memory_service.py**

`backend/app/domain/ai/memory/memory_service.py`:

```python
import json
import logging
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.ai.llm.chat import get_chat_llm
from app.domain.ai.memory.memory_repo import get_by_buyer, upsert
from app.domain.ai.memory.prompts import memory_update_prompt, MEMORY_INJECT_PREFIX

logger = logging.getLogger(__name__)


@dataclass
class MemoryUpdateResult:
    changed: bool
    content: str | None
    error: str | None


def _format_conversation(messages: list[BaseMessage]) -> str:
    lines = []
    for m in messages:
        if isinstance(m, HumanMessage):
            lines.append(f"用户: {m.content}")
        elif isinstance(m, AIMessage):
            lines.append(f"客服: {m.content}")
    return "\n".join(lines)


async def update_memory(
    db: Session,
    buyer_id: int,
    conversation_messages: list[BaseMessage],
) -> MemoryUpdateResult:
    existing = get_by_buyer(db, buyer_id)
    old_memory = existing.content if existing else ""
    expected_version = existing.version if existing else 0

    conversation_text = _format_conversation(conversation_messages)

    try:
        llm = get_chat_llm(temperature=0, streaming=False)
        chain = memory_update_prompt | llm
        response = await chain.ainvoke({
            "old_memory": old_memory or "（暂无）",
            "conversation": conversation_text,
        })
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        if not data.get("changed"):
            return MemoryUpdateResult(changed=False, content=None, error=None)

        new_content = data.get("content", "").strip()
        if not new_content:
            return MemoryUpdateResult(changed=False, content=None, error=None)

        ok = upsert(db, buyer_id, new_content, expected_version)
        if not ok:
            logger.warning("记忆更新乐观锁冲突，buyer_id=%d，本次跳过", buyer_id)
            return MemoryUpdateResult(changed=False, content=None, error="version conflict")

        return MemoryUpdateResult(changed=True, content=new_content, error=None)

    except Exception as e:
        logger.warning("记忆更新失败: %s", e)
        return MemoryUpdateResult(changed=False, content=None, error=str(e))


async def get_memory_block(db: Session, buyer_id: int) -> str | None:
    existing = get_by_buyer(db, buyer_id)
    if not existing or not existing.content:
        return None
    from app.domain.ai.workflow.compaction import estimate_tokens
    tokens = estimate_tokens(existing.content)
    if tokens <= settings.ai_memory_budget_tokens:
        return MEMORY_INJECT_PREFIX + existing.content
    chars = existing.content
    while chars and estimate_tokens(chars) > settings.ai_memory_budget_tokens:
        chars = chars[:-1]
    return MEMORY_INJECT_PREFIX + chars.strip() + "..."
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && uv run pytest tests/test_memory_update.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/domain/ai/memory/memory_service.py backend/tests/test_memory_update.py
git commit -m "feat(memory): 新增 memory_service（LLM 抽取 + 预算截断）"
```

---

## Task 5: 配置项

**Files:**
- Modify: `backend/app/core/config.py:15-30`

- [ ] **Step 1: 新增配置项**

`backend/app/core/config.py` 在 `ai_history_keep_recent_tokens` 后追加：

```python
    ai_memory_budget_tokens: int = 500
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/core/config.py
git commit -m "feat(memory): 新增 ai_memory_budget_tokens 配置项"
```

---

## Task 6: 引擎集成（记忆注入 + 显式记忆检测）

**Files:**
- Modify: `backend/app/domain/ai/workflow/engine.py:48-143`
- Test: `backend/tests/test_ai_memory_injection.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_ai_memory_injection.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.domain.ai.workflow.engine import ChatEngine
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


class TestMemoryInjection:
    @pytest.mark.asyncio
    async def test_injects_memory_as_system_message(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
            conv_repo = ConversationRepository()
            msg_repo = MessageRepository()
            conv = conv_repo.create(db, buyer_id=1)
            msg_repo.create(db, conv.id, "user", "你好")

            with patch("app.domain.ai.workflow.engine.get_memory_block") as mock_get, \
                 patch("app.domain.ai.workflow.engine.trim_history") as mock_trim, \
                 patch.object(ChatEngine, "_detect_memory_request", return_value=False):
                mock_get.return_value = "以下是用户长期信息\n【称呼/身份】李女士"
                mock_trim.return_value = MagicMock(
                    messages=[HumanMessage(content="你好")],
                    trimmed=False,
                )

                with patch.object(ChatEngine, "graph") as mock_graph:
                    mock_graph.ainvoke = AsyncMock(return_value={
                        "flow": {"intent": "greeting", "response": "你好李女士！"},
                        "skills": {"refund": {}, "after_sale": {}, "faq": {"context": []}},
                        "mcp": {},
                    })

                    engine_inst = ChatEngine()
                    events = []
                    async for event in engine_inst.process_message(db, conv.id, "你好"):
                        events.append(event)

                    call_args = mock_graph.ainvoke.call_args
                    state = call_args[0][0]
                    msgs = state["messages"]
                    assert any(isinstance(m, SystemMessage) and "李女士" in m.content for m in msgs)
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_no_memory_no_injection(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
            conv_repo = ConversationRepository()
            msg_repo = MessageRepository()
            conv = conv_repo.create(db, buyer_id=2)
            msg_repo.create(db, conv.id, "user", "你好")

            with patch("app.domain.ai.workflow.engine.get_memory_block") as mock_get, \
                 patch("app.domain.ai.workflow.engine.trim_history") as mock_trim, \
                 patch.object(ChatEngine, "_detect_memory_request", return_value=False):
                mock_get.return_value = None
                mock_trim.return_value = MagicMock(
                    messages=[HumanMessage(content="你好")],
                    trimmed=False,
                )

                with patch.object(ChatEngine, "graph") as mock_graph:
                    mock_graph.ainvoke = AsyncMock(return_value={
                        "flow": {"intent": "greeting", "response": "你好！"},
                        "skills": {"refund": {}, "after_sale": {}, "faq": {"context": []}},
                        "mcp": {},
                    })

                    engine_inst = ChatEngine()
                    events = []
                    async for event in engine_inst.process_message(db, conv.id, "你好"):
                        events.append(event)

                    call_args = mock_graph.ainvoke.call_args
                    state = call_args[0][0]
                    msgs = state["messages"]
                    assert not any(isinstance(m, SystemMessage) and "长期信息" in m.content for m in msgs)
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_explicit_memory_request_triggers_update(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
            conv_repo = ConversationRepository()
            msg_repo = MessageRepository()
            conv = conv_repo.create(db, buyer_id=3)
            msg_repo.create(db, conv.id, "user", "我叫张三")

            with patch("app.domain.ai.workflow.engine.get_memory_block") as mock_get, \
                 patch("app.domain.ai.workflow.engine.trim_history") as mock_trim, \
                 patch("app.domain.ai.workflow.engine.update_memory") as mock_update, \
                 patch.object(ChatEngine, "_detect_memory_request", return_value=True):
                mock_get.return_value = None
                mock_trim.return_value = MagicMock(
                    messages=[HumanMessage(content="我叫张三")],
                    trimmed=False,
                )
                mock_update.return_value = MagicMock(changed=True, content="【称呼/身份】张三", error=None)

                with patch.object(ChatEngine, "graph") as mock_graph:
                    mock_graph.ainvoke = AsyncMock(return_value={
                        "flow": {"intent": "greeting", "response": "你好！"},
                        "skills": {"refund": {}, "after_sale": {}, "faq": {"context": []}},
                        "mcp": {},
                    })

                    engine_inst = ChatEngine()
                    events = []
                    async for event in engine_inst.process_message(db, conv.id, "记住我叫张三"):
                        events.append(event)

                    mock_update.assert_called_once()
        finally:
            db.close()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && uv run pytest tests/test_ai_memory_injection.py -v`
Expected: FAIL（`get_memory_block`/`update_memory` 未导入）

- [ ] **Step 3: 修改 engine.py**

在 `backend/app/domain/ai/workflow/engine.py` 添加导入和修改 `process_message`：

```python
from app.domain.ai.memory.memory_service import get_memory_block, update_memory

_MEMORY_KEYWORDS = ("记住", "请记住", "以后叫我", "备注", "帮我记着")
```

在 `process_message` 方法开头（`db_messages` 加载之后、`trim_history` 之前）插入记忆加载逻辑：

```python
        conv_repo = ConversationRepository()
        conv = conv_repo.get_by_id(db, conversation_id)
        buyer_id = conv.buyer_id if conv else 1

        memory_block = await get_memory_block(db, buyer_id)
        is_memory_request = self._detect_memory_request(user_message)
```

在 `lc_messages` 构建时，先插入 memory_block（如有），再 append trimmed + user_message：

```python
        lc_messages: list = []
        if memory_block:
            lc_messages.append(SystemMessage(content=memory_block))
        lc_messages.extend(trimmed.messages)
        lc_messages.append(HumanMessage(content=user_message))
```

在 `process_message` 末尾（`yield {"type": "done"}` 之前），加入显式记忆更新：

```python
        if is_memory_request:
            all_msgs = list(trimmed.messages) + [HumanMessage(content=user_message)]
            if result.get("flow", {}).get("response"):
                from langchain_core.messages import AIMessage
                all_msgs.append(AIMessage(content=result["flow"]["response"]))
            mem_result = await update_memory(db, buyer_id, all_msgs)
            if mem_result.changed:
                response = result["flow"].get("response", "")
                result["flow"]["response"] = response + "好的，我已记下。"
```

添加辅助方法：

```python
    @staticmethod
    def _detect_memory_request(user_message: str) -> bool:
        return any(kw in user_message for kw in _MEMORY_KEYWORDS)
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && uv run pytest tests/test_ai_memory_injection.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: 运行全量回归**

Run: `cd backend && uv run pytest tests/test_ai_workflow.py tests/test_compaction.py -q`
Expected: PASS（注入 SystemMessage 不影响现有图路由）

- [ ] **Step 6: 提交**

```bash
git add backend/app/domain/ai/workflow/engine.py backend/tests/test_ai_memory_injection.py
git commit -m "feat(memory): 引擎集成记忆注入与显式记忆检测"
```

---

## Task 7: API close 端点 + 买家端只返回 active 会话

**Files:**
- Modify: `backend/app/api/web/ai.py:61-99`
- Test: `backend/tests/test_ai_api_web.py`

- [ ] **Step 1: 写失败测试**

在 `backend/tests/test_ai_api_web.py` 末尾追加：

```python
def test_list_conversations_only_active() -> None:
    repo = ConversationRepository()
    db = SessionLocal()
    try:
        conv1 = repo.create(db, buyer_id=1)
        conv2 = repo.create(db, buyer_id=1)
        repo.update_status(db, conv2.id, "closed")
    finally:
        db.close()

    response = client.get("/api/v1/web/ai/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 1
    assert data["conversations"][0]["id"] == conv1.id


def test_close_conversation() -> None:
    repo = ConversationRepository()
    db = SessionLocal()
    try:
        conv = repo.create(db, buyer_id=1)
        conv_id = conv.id
    finally:
        db.close()

    with patch("app.api.web.ai.ChatEngine.process_message") as mock_process:
        async def _empty_gen(*args, **kwargs):
            return
            yield  # make it async generator
        mock_process.side_effect = _empty_gen

        response = client.post(f"/api/v1/web/ai/conversations/{conv_id}/close")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"


def test_close_nonexistent_conversation() -> None:
    with patch("app.api.web.ai.ChatEngine.process_message") as mock_process:
        async def _empty_gen(*args, **kwargs):
            return
            yield
        mock_process.side_effect = _empty_gen

        response = client.post("/api/v1/web/ai/conversations/99999/close")
        assert response.status_code == 404
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && uv run pytest tests/test_ai_api_web.py -v -k "active or close"`
Expected: FAIL（close 端点不存在）

- [ ] **Step 3: 修改 api/web/ai.py**

在文件顶部添加导入：

```python
from app.domain.ai.memory.memory_service import update_memory
from langchain_core.messages import AIMessage, HumanMessage
```

修改 `list_conversations` 函数（`backend/app/api/web/ai.py:84-87`）：

```python
@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(db: Session = Depends(get_db)) -> ConversationListResponse:
    repo = ConversationRepository()
    all_convs = repo.list_by_buyer(db, buyer_id=1)
    active = [c for c in all_convs if c.status == "active"]
    return ConversationListResponse(conversations=active)
```

在文件末尾添加 close 端点：

```python
@router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> dict:
    repo = ConversationRepository()
    conv = repo.get_by_id(db, conversation_id)
    if conv is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_repo = MessageRepository()
    db_messages = msg_repo.list_by_conversation(db, conversation_id, limit=200)
    conversation_messages = []
    for msg in db_messages:
        if msg.sender == "user":
            conversation_messages.append(HumanMessage(content=msg.content))
        elif msg.sender == "ai":
            conversation_messages.append(AIMessage(content=msg.content))

    if conversation_messages:
        await update_memory(db, conv.buyer_id, conversation_messages)

    repo.update_status(db, conversation_id, "closed")
    return {"id": conversation_id, "status": "closed"}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && uv run pytest tests/test_ai_api_web.py -v`
Expected: 所有测试 PASS（含新增 3 个）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/web/ai.py backend/tests/test_ai_api_web.py
git commit -m "feat(memory): 新增 close 端点 + 买家端只返回 active 会话"
```

---

## Task 8: 前端 sendBeacon

**Files:**
- Modify: `apps/web/app/(main)/ai/hooks/use-sse-chat.ts:35-37`

- [ ] **Step 1: 修改 use-sse-chat.ts**

在 `useEffect(() => { loadConversation(); }, [])` 之后、`handleWorkerMessage` 之前，加入离开页面时的 close beacon：

```typescript
  useEffect(() => {
    const handleUnload = () => {
      if (!conversationId) return;
      const url = `${client.baseUrl}/api/v1/web/ai/conversations/${conversationId}/close`;
      navigator.sendBeacon(url, new Blob([], { type: "application/json" }));
    };
    window.addEventListener("beforeunload", handleUnload);
    return () => {
      window.removeEventListener("beforeunload", handleUnload);
      handleUnload();
    };
  }, [conversationId]);
```

- [ ] **Step 2: 提交**

```bash
git add apps/web/app/(main)/ai/hooks/use-sse-chat.ts
git commit -m "feat(memory): 买家端离开页面时 sendBeacon 触发 close"
```

---

## Task 9: SDK 补充 closeConversation

**Files:**
- Modify: `packages/sdk/src/ai.ts:145-168`

- [ ] **Step 1: 在 ai.ts 末尾追加**

```typescript
/** Close a conversation (triggers memory extraction) */
export function closeConversation(
  client: ApiClient,
  conversationId: number,
): Promise<{ id: number; status: string }> {
  return client.request<{ id: number; status: string }>(
    `/api/v1/web/ai/conversations/${conversationId}/close`,
    { method: "POST" },
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add packages/sdk/src/ai.ts
git commit -m "feat(memory): SDK 补充 closeConversation"
```

---

## Task 10: 全量测试回归

- [ ] **Step 1: 运行全量测试**

Run: `cd backend && uv run pytest tests/ -q`
Expected: 全部 PASS

- [ ] **Step 2: 检查 lint/typecheck**

Run: `pnpm check:backend`
Expected: 无报错

- [ ] **Step 3: 最终提交（如有遗漏修复）**

---

## 依赖关系

```
Task 1 (模型) → Task 2 (repo) → Task 3 (prompts) → Task 4 (service)
                                                            ↓
                                              Task 5 (config) → Task 6 (engine)
                                                            ↓
                                              Task 7 (API) → Task 8 (前端)
                                                            ↓
                                              Task 9 (SDK)
                                                            ↓
                                              Task 10 (全量回归)
```

Task 1-4 严格串行；Task 5 可与 Task 6 并行；Task 7-9 可并行；Task 10 在最后。
