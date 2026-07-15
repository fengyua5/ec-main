---
change: order-refund-mcp
design-doc: docs/superpowers/specs/2026-07-14-order-refund-mcp-design.md
base-ref: d836b11168a1976c8a3832254c4c74bd3e635018
---

# 订单退款 MCP 服务实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将订单退款能力从模拟处理升级为真实 MCP 服务——通过 `check_order` / `process_refund` 两个 MCP 工具查询订单状态并执行条件退款。

**Architecture:** LangGraph 工作流中 `collect_refund_info` 填完信息后路由至新增 `check_order_mcp` 节点，调用 MCP Server 查询订单。`pending_delivery` 状态进入 `process_refund_mcp` 执行退款；`in_delivery`/`not_found` 直接回复拒绝信息；MCP 异常时降级到原有 `process_refund` 模拟逻辑。MCP Server 以 Python stdio 子进程方式运行，由模块级单例 Client 管理生命周期。

**Tech Stack:** Python 3.11+, LangGraph, FastMCP (mcp Python SDK), SQLAlchemy, SQLite, pytest-asyncio

---

## 文件结构

### 创建的文件
| 文件 | 职责 |
|------|------|
| `backend/app/models/order.py` | `Order` SQLAlchemy 模型 |
| `backend/app/mcp/__init__.py` | MCP 包初始化 |
| `backend/app/mcp/server.py` | FastMCP Server，注册 `check_order` / `process_refund` 工具 |
| `backend/app/mcp/client.py` | MCP Client 单例，管理 stdio 子进程生命周期 |
| `backend/app/db/seed.py` | 种子数据：创建三种状态的订单 |

### 修改的文件
| 文件 | 修改内容 |
|------|----------|
| `backend/app/models/__init__.py` | 导出 `Order` |
| `backend/pyproject.toml` | 添加 `mcp` 依赖 |
| `backend/app/domain/ai/workflow/state.py` | `ConversationState` 重构为三层命名空间 |
| `backend/app/domain/ai/workflow/nodes.py` | `collect_refund_info` 路由变更，新增 `check_order_mcp` / `process_refund_mcp` |
| `backend/app/domain/ai/workflow/graph.py` | 注册新节点 + 新条件边路由 |
| `backend/app/domain/ai/workflow/engine.py` | MCP Client 懒加载集成 |
| `backend/app/main.py` | lifespan 中调用种子数据 |
| `backend/tests/test_ai_workflow.py` | 新增 MCP 工作流测试 |

---

## Task 1: Order 数据模型与种子数据

**Files:**
- Create: `backend/app/models/order.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/db/seed.py`

- [ ] **Step 1.1：创建 Order 模型**

`backend/app/models/order.py`：

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Order(Base):
    __tablename__ = "orders"

    order_no: Mapped[str] = mapped_column(String(50), primary_key=True)
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- [ ] **Step 1.2：在 `__init__.py` 中导出 Order**

`backend/app/models/__init__.py`：

```python
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.faq_document import FAQDocument
from app.models.order import Order

__all__ = ["User", "Conversation", "Message", "FAQDocument", "Order"]
```

- [ ] **Step 1.3：创建种子数据脚本**

`backend/app/db/seed.py`：

```python
import logging
from sqlalchemy.orm import Session
from app.models.order import Order

logger = logging.getLogger(__name__)

SEED_ORDERS = [
    Order(order_no="ORD-PENDING-001", buyer_id=1, amount="199.00", status="pending_delivery"),
    Order(order_no="ORD-IN-DELIVERY-001", buyer_id=1, amount="299.00", status="in_delivery"),
    Order(order_no="ORD-DELIVERED-001", buyer_id=1, amount="399.00", status="delivered"),
]


def seed_orders(db: Session) -> None:
    existing = db.query(Order).count()
    if existing > 0:
        logger.info("种子数据: orders 表已有 %d 条记录，跳过", existing)
        return
    for order in SEED_ORDERS:
        db.add(order)
    db.commit()
    logger.info("种子数据: 已插入 %d 条订单", len(SEED_ORDERS))
```

- [ ] **Step 1.4：在 lifespan 中调用种子数据**

`backend/app/main.py`：

```python
from app.db.session import SessionLocal
from app.db.seed import seed_orders

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_orders(db)
    finally:
        db.close()
    yield
```

---

## Task 2: ConversationState 三层命名空间重构

**Files:**
- Modify: `backend/app/domain/ai/workflow/state.py`
- Modify: `backend/app/domain/ai/workflow/nodes.py`
- Modify: `backend/app/domain/ai/workflow/graph.py`
- Modify: `backend/app/domain/ai/workflow/engine.py`
- Modify: `backend/tests/test_ai_workflow.py`

> **说明：** 本 Task 将扁平 state 拆为 `flow` / `skills` / `mcp` 三层。旧字段映射：`intent`→`flow["intent"]`，`confidence`→`flow["confidence"]`，`conversation_id`→`flow["conversation_id"]`，`response`→`flow["response"]`，`refund_info`→`skills["refund"]`，`faq_context`→`skills["faq"]["context"]`。`mcp` 为新加层。

- [ ] **Step 2.1：重构 state.py**

```python
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    flow: dict
    skills: dict[str, Any]
    mcp: dict
```

- [ ] **Step 2.2：更新 `make_state` 辅助函数（测试用）**

`backend/tests/test_ai_workflow.py`（替换原 `make_state`）：

```python
def make_state(**overrides) -> ConversationState:
    defaults: ConversationState = {
        "messages": [],
        "flow": {"intent": None, "confidence": 0.0, "conversation_id": None, "response": ""},
        "skills": {"refund": {}, "faq": {"context": []}},
        "mcp": {},
    }
    defaults.update(overrides)
    return defaults
```

- [ ] **Step 2.3：更新所有节点函数**

`backend/app/domain/ai/workflow/nodes.py`——每个节点中字段访问路径变更：

```python
# classify_intent
return {"flow": {"intent": intent, "confidence": confidence}}

# handle_greeting
return {"flow": {"response": GREETING_RESPONSE}}

# retrieve_faq
return {"skills": {"faq": {"context": results}}}  # 空结果时
# 或
return {"skills": {"faq": {"context": []}}, "flow": {"intent": "human"}}

# answer_faq
faq_context = state.get("skills", {}).get("faq", {}).get("context", [])
return {"flow": {"response": response.content}}

# collect_refund_info
refund_info = dict(state.get("skills", {}).get("refund", {}))
...
return {"skills": {"refund": refund_info}, "flow": {"response": "请输入退款原因：", ...}}

# process_refund
refund_info = state.get("skills", {}).get("refund", {})
return {"flow": {"response": "退单申请已提交，处理成功！"}}

# handoff_human
conv_id = state.get("flow", {}).get("conversation_id")
return {"flow": {"response": "正在为您转接人工客服，请稍候..."}}
```

- [ ] **Step 2.4：更新 graph.py 路由函数**

```python
def _route_after_intent(state: ConversationState) -> str:
    flow = state.get("flow", {})
    return flow.get("intent", "human") or "human"

def _route_after_faq(state: ConversationState) -> str:
    flow = state.get("flow", {})
    return flow.get("intent", "faq") or "faq"

def _route_after_refund(state: ConversationState) -> str:
    refund = state.get("skills", {}).get("refund", {})
    if all(k in refund for k in ("order_no", "reason", "amount")):
        return "process_refund"  # 暂时保持原目标，Task 5 将改为 check_order_mcp
    return END
```

- [ ] **Step 2.5：更新 engine.py state 构造**

`backend/app/domain/ai/workflow/engine.py`：

```python
state: ConversationState = {
    "messages": lc_messages,
    "flow": {
        "intent": None,
        "confidence": 0.0,
        "conversation_id": conversation_id,
        "response": "",
    },
    "skills": {
        "refund": refund_info,
        "faq": {"context": []},
    },
    "mcp": {},
}
```

更新 engine.py 中读取 result 的代码：

```python
result = await self.graph.ainvoke(state)

updated_refund = result.get("skills", {}).get("refund", {})
if updated_refund and updated_refund != refund_info:
    self.msg_repo.create(db, conversation_id, "system", json.dumps(updated_refund, ensure_ascii=False), msg_type="refund_info")

yield {"type": "intent", "value": result.get("flow", {}).get("intent")}
yield {"type": "token", "content": result.get("flow", {}).get("response", "")}
yield {"type": "done"}
```

- [ ] **Step 2.6：更新已有测试中的访问路径**

`backend/tests/test_ai_workflow.py` 中所有 `state["intent"]`→`state["flow"]["intent"]`，`state["refund_info"]`→`state["skills"]["refund"]`，`state["faq_context"]`→`state["skills"]["faq"]["context"]`，`state["response"]`→`state["flow"]["response"]`，`state["conversation_id"]`→`state["flow"]["conversation_id"]`。

关键变更点：

```python
# test_state_defaults
assert state["flow"]["intent"] is None
assert state["flow"]["confidence"] == 0.0
assert state["skills"]["refund"] == {}
assert state["skills"]["faq"]["context"] == []
assert state["flow"]["response"] == ""

# test_state_with_values
state = make_state(flow={"intent": "faq", "confidence": 0.9, "response": "hello"})

# 测试 refund 收集
state = make_state(
    skills={"refund": {"order_no": "123", "reason": "defective", "amount": "50"}, "faq": {"context": []}},
    messages=[HumanMessage(content="50")],
)

# test_process_refund — 结果中的 response 现在在 flow 下
result.get("flow", {}).get("response", "")
```

- [ ] **Step 2.7：运行测试确认重构未破坏功能**

```bash
cd backend && python -m pytest tests/test_ai_workflow.py -v
```

预期：所有重构后的测试 PASS。

---

## Task 3: MCP Server

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/app/mcp/__init__.py`
- Create: `backend/app/mcp/server.py`

- [ ] **Step 3.1：添加 mcp 依赖**

`backend/pyproject.toml` `dependencies` 中追加：

```toml
  "mcp>=1.0.0",
```

安装依赖：

```bash
cd backend && pip install "mcp>=1.0.0"
```

- [ ] **Step 3.2：创建 MCP 包初始化**

`backend/app/mcp/__init__.py`：空文件。

- [ ] **Step 3.3：实现 MCP Server**

`backend/app/mcp/server.py`：

```python
import json
import logging

from mcp.server.fastmcp import FastMCP

from app.db.session import SessionLocal
from app.models.order import Order

logger = logging.getLogger(__name__)

mcp = FastMCP("order-refund")


@mcp.tool()
def check_order(order_id: str) -> str:
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_no == order_id).first()
        if not order:
            result = {"status": "not_found", "amount": "", "message": "未找到该订单"}
        else:
            result = {
                "status": order.status,
                "amount": order.amount,
                "message": f"订单 {order_id} 状态: {order.status}",
            }
        logger.info("MCP check_order: order_id=%s → %s", order_id, result["status"])
        return json.dumps(result, ensure_ascii=False)
    finally:
        db.close()


@mcp.tool()
def process_refund(order_id: str, reason: str, amount: str) -> str:
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_no == order_id).first()
        if not order:
            result = {"success": False, "message": "未找到该订单"}
        elif order.status != "pending_delivery":
            result = {
                "success": False,
                "message": f"订单状态为 {order.status}，不可退款",
            }
        else:
            order.status = "refunded"
            db.commit()
            result = {"success": True, "message": "退款成功"}
        logger.info(
            "MCP process_refund: order_id=%s reason=%s amount=%s → %s",
            order_id, reason[:20], amount, result,
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        db.rollback()
        logger.error("MCP process_refund 异常: %s", e)
        return json.dumps({"success": False, "message": "退款处理异常"})
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Task 4: MCP Client

**Files:**
- Create: `backend/app/mcp/client.py`

- [ ] **Step 4.1：实现 MCP Client 单例**

`backend/app/mcp/client.py`：

```python
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._stdio = None
        self._read = None
        self._write = None

    async def start(self) -> None:
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "app.mcp.server"],
        )
        self._stdio = stdio_client(server_params)
        self._read, self._write = await self._stdio.__aenter__()
        self._session = await ClientSession(self._read, self._write).__aenter__()
        await self._session.initialize()
        logger.info("MCP Client 已启动")

    async def stop(self) -> None:
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None
        if self._stdio:
            await self._stdio.__aexit__(None, None, None)
            self._stdio = None
        logger.info("MCP Client 已停止")

    async def check_order(self, order_id: str) -> dict:
        if not self._session:
            raise RuntimeError("MCP Client 未初始化")
        result = await self._session.call_tool("check_order", {"order_id": order_id})
        text = result.content[0].text
        return json.loads(text)

    async def process_refund(self, order_id: str, reason: str, amount: str) -> dict:
        if not self._session:
            raise RuntimeError("MCP Client 未初始化")
        result = await self._session.call_tool(
            "process_refund",
            {"order_id": order_id, "reason": reason, "amount": amount},
        )
        text = result.content[0].text
        return json.loads(text)


_client: MCPClient | None = None


async def get_client() -> MCPClient:
    global _client
    if _client is None:
        _client = MCPClient()
        await _client.start()
    return _client
```

---

## Task 5: LangGraph 工作流集成

**Files:**
- Modify: `backend/app/domain/ai/workflow/nodes.py`
- Modify: `backend/app/domain/ai/workflow/graph.py`
- Modify: `backend/app/domain/ai/workflow/engine.py`

- [ ] **Step 5.1：修改 `collect_refund_info` 路由目标**

`graph.py` 中 `_route_after_refund` 返回值改为 `"check_order_mcp"`：

```python
def _route_after_refund(state: ConversationState) -> str:
    refund = state.get("skills", {}).get("refund", {})
    if all(k in refund for k in ("order_no", "reason", "amount")):
        return "check_order_mcp"
    return END
```

- [ ] **Step 5.2：新增 `check_order_mcp` 节点**

`backend/app/domain/ai/workflow/nodes.py`：

```python
async def check_order_mcp(state: ConversationState) -> dict:
    from app.mcp.client import get_client

    refund = state.get("skills", {}).get("refund", {})
    order_no = refund.get("order_no", "")
    flow = dict(state.get("flow", {}))
    mcp = dict(state.get("mcp", {}))

    try:
        client = await get_client()
        result = await client.check_order(order_no)
        status = result.get("status", "not_found")
        mcp["order_status"] = status
        logger.info("MCP 订单查询: order_no=%s status=%s", order_no, status)

        if status == "in_delivery":
            flow["response"] = "订单在配送中，无法退款"
        elif status in ("not_found", None):
            flow["response"] = "未找到该订单"
    except Exception as e:
        logger.error("MCP check_order 调用异常: %s", e)
        mcp["error"] = str(e)
        mcp["order_status"] = "not_found"
        flow["response"] = "订单查询服务暂时不可用"

    return {"mcp": mcp, "flow": flow}
```

- [ ] **Step 5.3：新增 `process_refund_mcp` 节点**

`backend/app/domain/ai/workflow/nodes.py`：

```python
async def process_refund_mcp(state: ConversationState) -> dict:
    from app.mcp.client import get_client

    refund = state.get("skills", {}).get("refund", {})
    flow = dict(state.get("flow", {}))
    mcp = dict(state.get("mcp", {}))

    try:
        client = await get_client()
        result = await client.process_refund(
            refund.get("order_no", ""),
            refund.get("reason", ""),
            refund.get("amount", ""),
        )
        mcp["refund_success"] = result.get("success", False)
        if result.get("success"):
            flow["response"] = "退款成功"
            logger.info("MCP 退款成功: order_no=%s", refund.get("order_no"))
        else:
            flow["response"] = result.get("message", "退款处理失败")
            logger.warning("MCP 退款失败: %s", result.get("message"))
    except Exception as e:
        logger.error("MCP process_refund 调用异常: %s", e)
        mcp["error"] = str(e)
        flow["response"] = "退款处理失败，请稍后再试"

    return {"mcp": mcp, "flow": flow}
```

- [ ] **Step 5.4：添加 `check_order_mcp` → 条件边路由函数**

`backend/app/domain/ai/workflow/graph.py`：

```python
def _route_after_check_order(state: ConversationState) -> str:
    mcp = state.get("mcp", {})
    if mcp.get("error"):
        return "process_refund"
    if mcp.get("order_status") == "pending_delivery":
        return "process_refund_mcp"
    return END
```

- [ ] **Step 5.5：在 `build_chat_graph` 中注册新节点和边**

```python
def build_chat_graph() -> StateGraph:
    workflow = StateGraph(ConversationState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("handle_greeting", handle_greeting)
    workflow.add_node("retrieve_faq", retrieve_faq)
    workflow.add_node("answer_faq", answer_faq)
    workflow.add_node("collect_refund_info", collect_refund_info)
    workflow.add_node("process_refund", process_refund)
    workflow.add_node("handoff_human", handoff_human)
    workflow.add_node("check_order_mcp", check_order_mcp)
    workflow.add_node("process_refund_mcp", process_refund_mcp)

    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        _route_after_intent,
        {
            "greeting": "handle_greeting",
            "faq": "retrieve_faq",
            "refund": "collect_refund_info",
            "human": "handoff_human",
        },
    )

    workflow.add_conditional_edges(
        "retrieve_faq",
        _route_after_faq,
        {
            "faq": "answer_faq",
            "human": "handoff_human",
        },
    )

    workflow.add_conditional_edges(
        "collect_refund_info",
        _route_after_refund,
        {
            "check_order_mcp": "check_order_mcp",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "check_order_mcp",
        _route_after_check_order,
        {
            "process_refund_mcp": "process_refund_mcp",
            "process_refund": "process_refund",
            END: END,
        },
    )

    workflow.add_edge("handle_greeting", END)
    workflow.add_edge("answer_faq", END)
    workflow.add_edge("process_refund", END)
    workflow.add_edge("process_refund_mcp", END)
    workflow.add_edge("handoff_human", END)

    return workflow.compile()
```

- [ ] **Step 5.6：更新 `ChatEngine` 集成 MCP 生命周期**

`backend/app/domain/ai/workflow/engine.py`——在 `__init__` 中不再启动 MCP（懒加载由节点自己完成），仅在 `__del__` 中清理：

```python
class ChatEngine:
    def __init__(self) -> None:
        self.graph = build_chat_graph()
        self.conv_repo = ConversationRepository()
        self.msg_repo = MessageRepository()

    async def process_message(
        self, db: Session, conversation_id: int, user_message: str,
    ) -> AsyncGenerator[dict, None]:
        db_messages = self.msg_repo.list_by_conversation(db, conversation_id)

        lc_messages: list = []
        refund_info: dict = {}
        for msg in db_messages:
            if msg.sender == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.sender == "ai":
                lc_messages.append(AIMessage(content=msg.content))
            elif msg.sender == "system" and msg.msg_type == "refund_info":
                try:
                    refund_info = json.loads(msg.content)
                except (json.JSONDecodeError, TypeError):
                    refund_info = {}

        lc_messages.append(HumanMessage(content=user_message))

        state: ConversationState = {
            "messages": lc_messages,
            "flow": {"intent": None, "confidence": 0.0, "conversation_id": conversation_id, "response": ""},
            "skills": {"refund": refund_info, "faq": {"context": []}},
            "mcp": {},
        }

        result = await self.graph.ainvoke(state)

        self.msg_repo.create(db, conversation_id, "user", user_message)
        if result.get("flow", {}).get("response"):
            self.msg_repo.create(db, conversation_id, "ai", result["flow"]["response"])

        updated_refund = result.get("skills", {}).get("refund", {})
        if updated_refund and updated_refund != refund_info:
            self.msg_repo.create(
                db, conversation_id, "system",
                json.dumps(updated_refund, ensure_ascii=False),
                msg_type="refund_info",
            )

        yield {"type": "intent", "value": result.get("flow", {}).get("intent")}
        yield {"type": "token", "content": result.get("flow", {}).get("response", "")}
        yield {"type": "done"}
```

---

## Task 6: 验证

**Files:**
- Modify: `backend/tests/test_ai_workflow.py`

- [ ] **Step 6.1：编写 check_order_mcp 节点单元测试**

`backend/tests/test_ai_workflow.py` 中 `TestNodes` 类新增：

```python
@pytest.mark.asyncio
async def test_check_order_mcp_pending_delivery(self) -> None:
    with patch("app.domain.ai.workflow.nodes.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.check_order.return_value = {"status": "pending_delivery", "amount": "199.00", "message": "待配送"}
        mock_get_client.return_value = mock_client

        from app.domain.ai.workflow.nodes import check_order_mcp
        state = make_state(
            skills={"refund": {"order_no": "ORD-PENDING-001", "reason": "bad", "amount": "50"}, "faq": {"context": []}},
        )
        result = await check_order_mcp(state)
        assert result["mcp"]["order_status"] == "pending_delivery"
        assert "response" not in result.get("flow", {})

@pytest.mark.asyncio
async def test_check_order_mcp_in_delivery(self) -> None:
    with patch("app.domain.ai.workflow.nodes.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.check_order.return_value = {"status": "in_delivery", "amount": "299.00", "message": "配送中"}
        mock_get_client.return_value = mock_client

        from app.domain.ai.workflow.nodes import check_order_mcp
        state = make_state(
            skills={"refund": {"order_no": "ORD-IN-DELIVERY-001", "reason": "bad", "amount": "50"}, "faq": {"context": []}},
        )
        result = await check_order_mcp(state)
        assert result["mcp"]["order_status"] == "in_delivery"
        assert "配送中" in result["flow"]["response"]

@pytest.mark.asyncio
async def test_check_order_mcp_not_found(self) -> None:
    with patch("app.domain.ai.workflow.nodes.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.check_order.return_value = {"status": "not_found", "amount": "", "message": "未找到"}
        mock_get_client.return_value = mock_client

        from app.domain.ai.workflow.nodes import check_order_mcp
        state = make_state(
            skills={"refund": {"order_no": "NONEXIST", "reason": "bad", "amount": "50"}, "faq": {"context": []}},
        )
        result = await check_order_mcp(state)
        assert result["mcp"]["order_status"] == "not_found"
        assert "未找到" in result["flow"]["response"]

@pytest.mark.asyncio
async def test_check_order_mcp_error_fallback(self) -> None:
    with patch("app.domain.ai.workflow.nodes.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.check_order.side_effect = RuntimeError("Connection refused")
        mock_get_client.return_value = mock_client

        from app.domain.ai.workflow.nodes import check_order_mcp
        state = make_state(
            skills={"refund": {"order_no": "ORD-PENDING-001", "reason": "bad", "amount": "50"}, "faq": {"context": []}},
        )
        result = await check_order_mcp(state)
        assert result["mcp"]["error"] is not None
        assert "不可用" in result["flow"]["response"]
```

- [ ] **Step 6.2：编写 process_refund_mcp 节点单元测试**

```python
@pytest.mark.asyncio
async def test_process_refund_mcp_success(self) -> None:
    with patch("app.domain.ai.workflow.nodes.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.process_refund.return_value = {"success": True, "message": "退款成功"}
        mock_get_client.return_value = mock_client

        from app.domain.ai.workflow.nodes import process_refund_mcp
        state = make_state(
            skills={"refund": {"order_no": "ORD-PENDING-001", "reason": "bad", "amount": "50"}, "faq": {"context": []}},
        )
        result = await process_refund_mcp(state)
        assert result["mcp"]["refund_success"] is True
        assert "退款成功" in result["flow"]["response"]

@pytest.mark.asyncio
async def test_process_refund_mcp_failure(self) -> None:
    with patch("app.domain.ai.workflow.nodes.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.process_refund.side_effect = RuntimeError("MCP error")
        mock_get_client.return_value = mock_client

        from app.domain.ai.workflow.nodes import process_refund_mcp
        state = make_state(
            skills={"refund": {"order_no": "ORD-PENDING-001", "reason": "bad", "amount": "50"}, "faq": {"context": []}},
        )
        result = await process_refund_mcp(state)
        assert result["mcp"]["error"] is not None
        assert "失败" in result["flow"]["response"]
```

- [ ] **Step 6.3：添加图层面路由测试**

`TestGraphRoutingLogic` 类新增：

```python
def test_route_after_refund_redirects_to_check_order_mcp(self) -> None:
    from app.domain.ai.workflow.graph import _route_after_refund
    state = make_state(skills={"refund": {"order_no": "1", "reason": "a", "amount": "b"}, "faq": {"context": []}})
    assert _route_after_refund(state) == "check_order_mcp"

def test_route_after_check_order_pending_delivery(self) -> None:
    from app.domain.ai.workflow.graph import _route_after_check_order
    state = make_state(mcp={"order_status": "pending_delivery"})
    assert _route_after_check_order(state) == "process_refund_mcp"

def test_route_after_check_order_in_delivery(self) -> None:
    from app.domain.ai.workflow.graph import _route_after_check_order
    from langgraph.graph import END
    state = make_state(mcp={"order_status": "in_delivery"})
    assert _route_after_check_order(state) == END

def test_route_after_check_order_not_found(self) -> None:
    from app.domain.ai.workflow.graph import _route_after_check_order
    from langgraph.graph import END
    state = make_state(mcp={"order_status": "not_found"})
    assert _route_after_check_order(state) == END

def test_route_after_check_order_error_fallback(self) -> None:
    from app.domain.ai.workflow.graph import _route_after_check_order
    state = make_state(mcp={"error": "connection failed", "order_status": "not_found"})
    assert _route_after_check_order(state) == "process_refund"
```

- [ ] **Step 6.4：图编译测试——验证新节点已注册**

`TestGraph` 类中更新 `test_has_all_nodes`：

```python
expected = {
    "classify_intent",
    "handle_greeting",
    "retrieve_faq",
    "answer_faq",
    "collect_refund_info",
    "process_refund",
    "handoff_human",
    "check_order_mcp",
    "process_refund_mcp",
}
```

- [ ] **Step 6.5：全量运行测试**

```bash
cd backend && python -m pytest tests/ -v
```

预期：所有测试 PASS，0 failure。

---

## 自检清单

### 1. Spec 覆盖检查

| 设计文档要求 | 对应任务 | 状态 |
|-------------|---------|------|
| Order 数据模型 (order_no, buyer_id, amount, status, created_at) | Task 1.1 | ✓ |
| 种子数据：三种状态各一条 | Task 1.3 | ✓ |
| MCP Server stdio 模式 | Task 3.3 | ✓ |
| `check_order` 工具：查询 SQLite orders 表 | Task 3.3 | ✓ |
| `process_refund` 工具：验证状态后标记退款 | Task 3.3 | ✓ |
| ChatEngine 子进程模式 | Task 4.1 (Client) + Task 5.6 | ✓ |
| ConversationState 三层重构 (flow/skills/mcp) | Task 2 | ✓ |
| `collect_refund_info` 填入后转 `check_order_mcp` | Task 5.1 | ✓ |
| `check_order_mcp` 节点 | Task 5.2 | ✓ |
| `process_refund_mcp` 节点 | Task 5.3 | ✓ |
| 条件边: proceed_refund / reject / not_found | Task 5.4 + 5.5 | ✓ |
| 降级: MCP 异常时回退 process_refund | Task 5.2 + 5.4 | ✓ |
| 测试覆盖四种场景 | Task 6 | ✓ |

### 2. 占位符扫描

无 "TBD"、"TODO"、"implement later"、"// ..." 占位符。

### 3. 类型一致性

- `ConversationState` 字段路径在所有节点、路由、engine 中统一为 `flow`/`skills`/`mcp`
- `check_order` 返回 JSON 格式：(`status`, `amount`, `message`)
- `process_refund` 返回 JSON 格式：(`success`, `message`)
- 路由函数名和返回值字符串与 `add_conditional_edges` 映射一致

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-14-order-refund-mcp.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — 我按任务分派独立 subagent，任务间 review，快速迭代

**2. Inline Execution** — 在当前 session 中依次执行，批量 checkpoint

**选择哪种方式？**
