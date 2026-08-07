# 售后增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在售后模块新增「订单号槽位补充」「取消订单子意图」「退款确认环节」与「售后 case 落库」，并统一取消/退款的状态校验口径为 `in_delivery` 起禁。

**Architecture:** 在现有 langgraph 售后图（`after_sale`）上扩展：新增 `ensure_order_no`（统一订单号槽位）、`confirm_after_sale`（通用确认节点）、`cancel_order_mcp`（取消执行）节点；`check_order_mcp` 改为从统一槽位读订单号并按子意图返回不同拒绝文案；新增 `AfterSaleCase` 模型与领域服务，退款/取消成功后落库。状态机 `VALID_TRANSITIONS` 收紧为 `in_delivery` 起不可流转，前端 `order-constants.ts` 同步。

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy / langgraph / MCP (stdio) / pytest / TypeScript (Next.js 管理端)。

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `backend/app/models/after_sale_case.py` | 新建 `AfterSaleCase` ORM 模型（表 `after_sale_cases`） |
| `backend/app/models/__init__.py` | 导出 `AfterSaleCase` |
| `backend/app/domain/after_sale/__init__.py` | 新建领域服务：`create_case` / `list_cases_by_buyer` |
| `backend/app/domain/orders/__init__.py` | `VALID_TRANSITIONS`：`in_delivery` 由 `{"delivered"}` 改为 `set()` |
| `backend/app/domain/ai/llm/prompts.py` | `SUB_INTENT_SYSTEM_PROMPT` 增补 `cancel_order` |
| `backend/app/domain/ai/workflow/nodes.py` | 新增 `ensure_order_no` / `confirm_after_sale` / `cancel_order_mcp`；改造 `collect_order_no` / `collect_refund_info` / `check_order_mcp` / `process_refund_mcp` |
| `backend/app/domain/ai/workflow/graph.py` | 售后子意图路由改为四分支，新增 ensure/confirm/cancel 节点与路由函数 |
| `backend/app/domain/ai/workflow/engine.py` | 无改动（`after_sale_info` 持久化已支持） |
| `apps/admin/app/(main)/orders/order-constants.ts` | `in_delivery` 可流转目标改为空 |
| 测试 | `test_ai_workflow.py` / `test_order_domain.py` / `test_mcp_server.py` / `test_after_sale_case.py`（新） |

---

### Task 1: 状态机收紧（VALID_TRANSITIONS）

**Files:**
- Modify: `backend/app/domain/orders/__init__.py:14-21`
- Test: `backend/tests/test_order_domain.py:29-41`

- [ ] **Step 1: 更新测试期望**

`backend/tests/test_order_domain.py`:

```python
def test_next_statuses_in_delivery() -> None:
    assert get_next_statuses("in_delivery") == []


def test_validate_transition_allows_legal() -> None:
    validate_transition("pending_payment", "pending_delivery")
    validate_transition("pending_delivery", "in_delivery")


def test_validate_transition_rejects_in_delivery_move() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_transition("in_delivery", "delivered")
    assert exc.value.status_code == 400
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && uv run pytest tests/test_order_domain.py -q`
Expected: `test_next_statuses_in_delivery` FAIL（返回 `["delivered"]` 而非 `[]`），`test_validate_transition_allows_legal` FAIL（`in_delivery→delivered` 不再被允许）。

- [ ] **Step 3: 修改 VALID_TRANSITIONS**

`backend/app/domain/orders/__init__.py:14-21`:

```python
VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending_payment": {"pending_delivery", "cancelled"},
    "pending_delivery": {"in_delivery", "cancelled", "refunded"},
    "in_delivery": set(),
    "delivered": set(),
    "cancelled": set(),
    "refunded": set(),
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd backend && uv run pytest tests/test_order_domain.py -q`
Expected: PASS

- [ ] **Step 5: 同步前端状态常量**

`apps/admin/app/(main)/orders/order-constants.ts` — 将 `in_delivery: ["delivered"]` 改为 `in_delivery: []`：

```typescript
in_delivery: [],
```

- [ ] **Step 6: 提交**

```bash
git add backend/app/domain/orders/__init__.py backend/tests/test_order_domain.py apps/admin/app/\(main\)/orders/order-constants.ts
git commit -m "feat: 收紧订单状态机，in_delivery 起不可流转"
```

---

### Task 2: 售后 Case 模型与领域服务

**Files:**
- Create: `backend/app/models/after_sale_case.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/domain/after_sale/__init__.py`
- Test: `backend/tests/test_after_sale_case.py`

- [ ] **Step 1: 写失败测试**

`backend/tests/test_after_sale_case.py`（新建）:

```python
import pytest
from app.models.after_sale_case import AfterSaleCase
from app.domain.after_sale import create_case, list_cases_by_buyer
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def test_create_case_persists() -> None:
    db = SessionLocal()
    try:
        case = create_case(
            db,
            order_no="ORD-CASE-001",
            buyer_id=7,
            case_type="refund",
            amount="199.00",
            reason="质量问题",
        )
        assert case.id is not None
        assert case.order_no == "ORD-CASE-001"
        assert case.buyer_id == 7
        assert case.case_type == "refund"
        assert case.amount == "199.00"
        assert case.reason == "质量问题"
        assert case.status == "processed"
        assert case.created_at is not None
    finally:
        db.close()


def test_create_case_minimal() -> None:
    db = SessionLocal()
    try:
        case = create_case(db, order_no="ORD-CASE-002", buyer_id=3, case_type="cancel")
        assert case.case_type == "cancel"
        assert case.amount is None
        assert case.reason is None
    finally:
        db.close()


def test_list_cases_by_buyer() -> None:
    db = SessionLocal()
    try:
        create_case(db, order_no="ORD-CASE-003", buyer_id=5, case_type="refund")
        create_case(db, order_no="ORD-CASE-004", buyer_id=5, case_type="cancel")
        create_case(db, order_no="ORD-CASE-005", buyer_id=9, case_type="refund")
        cases = list_cases_by_buyer(db, 5)
        assert len(cases) == 2
        assert {c.order_no for c in cases} == {"ORD-CASE-003", "ORD-CASE-004"}
    finally:
        db.close()
```

- [ ] **Step 2: 运行确认失败**

Run: `cd backend && uv run pytest tests/test_after_sale_case.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.after_sale_case'`

- [ ] **Step 3: 建模型**

`backend/app/models/after_sale_case.py`（新建）:

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class AfterSaleCase(Base):
    __tablename__ = "after_sale_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(50), nullable=False)
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    case_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

`backend/app/models/__init__.py` — 追加:

```python
from app.models.after_sale_case import AfterSaleCase

__all__ = ["User", "Conversation", "Message", "FAQDocument", "Order", "AfterSaleCase"]
```

- [ ] **Step 4: 建领域服务**

`backend/app/domain/after_sale/__init__.py`（新建）:

```python
from sqlalchemy.orm import Session

from app.models.after_sale_case import AfterSaleCase


def create_case(
    db: Session,
    *,
    order_no: str,
    buyer_id: int,
    case_type: str,
    amount: str | None = None,
    reason: str | None = None,
) -> AfterSaleCase:
    case = AfterSaleCase(
        order_no=order_no,
        buyer_id=buyer_id,
        case_type=case_type,
        amount=amount,
        reason=reason,
        status="processed",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def list_cases_by_buyer(db: Session, buyer_id: int) -> list[AfterSaleCase]:
    return db.query(AfterSaleCase).filter(
        AfterSaleCase.buyer_id == buyer_id,
    ).order_by(
        AfterSaleCase.created_at.desc(),
    ).all()
```

- [ ] **Step 5: 运行确认通过**

Run: `cd backend && uv run pytest tests/test_after_sale_case.py -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/models/after_sale_case.py backend/app/models/__init__.py backend/app/domain/after_sale/__init__.py backend/tests/test_after_sale_case.py
git commit -m "feat: 新增售后 case 模型与领域服务"
```

---

### Task 3: 子意图 prompt 增补 cancel_order

**Files:**
- Modify: `backend/app/domain/ai/llm/prompts.py:13-20`
- Test: `backend/tests/test_ai_workflow.py`

- [ ] **Step 1: 更新 prompt**

`backend/app/domain/ai/llm/prompts.py` — `SUB_INTENT_SYSTEM_PROMPT` 的分类类别改为：

```python
SUB_INTENT_SYSTEM_PROMPT = """你是一个售后子意图分类器。用户的诉求已被判定为售后，你的任务是对用户的消息进一步细分，只返回 JSON 格式的结果。
分类类别：
- "query_order": 用户要查询订单状态或订单详情
- "cancel_order": 用户要取消订单（要求订单未发货）
- "update_order": 用户要修改订单（例如修改订单状态）
- "refund": 用户要申请退款或退货

返回格式（只返回 JSON，不要其他内容）：
{{"sub_intent": "query_order|cancel_order|update_order|refund", "confidence": 0.0-1.0}}"""
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/domain/ai/llm/prompts.py
git commit -m "feat: 子意图增补 cancel_order"
```

---

### Task 4: 售后节点改造（nodes.py）

**Files:**
- Modify: `backend/app/domain/ai/workflow/nodes.py`
- Test: `backend/tests/test_ai_workflow.py`

本任务改动较大，按节点拆分步骤。

- [ ] **Step 1: 新增 ensure_order_no 节点**

先在 `nodes.py` 顶部补充 import：

```python
import re

from app.db.session import SessionLocal
from app.domain.after_sale import create_case
```

在 `enter_after_sale` 之后新增（使用统一槽位 `after_sale.order_no`，正则匹配 `ORD-\S+`）：

```python
_ORDER_NO_PATTERN = re.compile(r"ORD-\S+")


async def ensure_order_no(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    if after_sale.get("order_no"):
        return {"skills": {"after_sale": after_sale}}

    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""
    match = _ORDER_NO_PATTERN.search(last_msg)
    if match:
        after_sale["order_no"] = match.group(0)
        logger.info("售后槽位: 识别到订单号 '%s'", match.group(0))
        return {"skills": {"after_sale": after_sale}}
    logger.info("售后槽位: 未识别到订单号，询问用户")
    return {
        "flow": {"response": "请提供订单号（格式 ORD-xxx）："},
        "skills": {"after_sale": after_sale},
    }
```

注意：`nodes.py` 顶部需新增 `import re`。

- [ ] **Step 2: 新增 confirm_after_sale 节点**

```python
_YES_WORDS = {"是", "确认", "好的", "可以", "确定", "嗯", "对", "是的"}
_NO_WORDS = {"否", "不", "取消", "别", "算了", "不要", "不是"}


def _classify_confirm(text: str) -> str | None:
    stripped = text.strip().strip("？！。，,").lower()
    if stripped in _YES_WORDS or stripped.startswith(("确认", "是的", "好的", "可以")):
        return "yes"
    if stripped in _NO_WORDS or stripped.startswith(("不要", "算了", "不是")):
        return "no"
    return None


async def confirm_after_sale(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    sub_intent = after_sale.get("sub_intent", "")
    order_id = after_sale.get("order_no", "")
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""

    verdict = _classify_confirm(last_msg)
    if verdict == "yes":
        after_sale["confirmed"] = True
        logger.info("售后确认: 用户确认 %s 订单 %s", sub_intent, order_id)
        return {"skills": {"after_sale": after_sale}}
    if verdict == "no":
        after_sale["confirmed"] = False
        logger.info("售后确认: 用户取消操作 %s", sub_intent)
        return {
            "flow": {"response": f"已为您取消「{sub_intent}」操作。"},
            "skills": {"after_sale": after_sale},
        }

    if sub_intent == "refund":
        amount = state.get("skills", {}).get("refund", {}).get("amount", "?")
        return {
            "flow": {"response": f"订单 {order_id} 金额 ¥{amount}，确认退款吗？（回复「确认」或「否」）"},
            "skills": {"after_sale": after_sale},
        }
    return {
        "flow": {"response": f"确认取消订单 {order_id} 吗？（回复「确认」或「否」）"},
        "skills": {"after_sale": after_sale},
    }
```

- [ ] **Step 3: 新增 cancel_order_mcp 节点**

```python
async def cancel_order_mcp(state: ConversationState) -> dict:
    after_sale = state.get("skills", {}).get("after_sale", {})
    order_id = after_sale.get("order_no", "")
    if not order_id:
        return {"mcp": {"cancel_success": False, "error": "缺少订单号"}, "flow": {"response": "缺少订单号，请重新输入。"}}

    client = MCPClient.get_instance()
    try:
        result = await client.update_order_status(order_id, "cancelled")
        if result.get("success"):
            logger.info("MCP cancel_order: order=%s 已取消", order_id)
            buyer_id = state.get("mcp", {}).get("order_buyer_id", 0)
            db = SessionLocal()
            try:
                create_case(db, order_no=order_id, buyer_id=buyer_id, case_type="cancel")
            finally:
                db.close()
            return {"mcp": {"cancel_success": True}, "flow": {"response": f"订单 {order_id} 已成功取消。"}}
        else:
            logger.warning("MCP cancel_order: order=%s 取消失败: %s", order_id, result.get("message", ""))
            return {"mcp": {"cancel_success": False}, "flow": {"response": f"订单取消失败：{result.get('message', '未知错误')}"}}
    except Exception as e:
        logger.error("MCP cancel_order 异常: %s", e)
        return {"mcp": {"cancel_success": False, "error": str(e)}, "flow": {"intent": "human"}}
```

- [ ] **Step 4: 改造 collect_order_no（从统一槽位取）**

`collect_order_no` 改为读取 `after_sale.order_no`：

```python
async def collect_order_no(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    query_order = dict(after_sale.get("query_order", {}))
    order_no = after_sale.get("order_no", "")
    query_order["order_no"] = order_no
    after_sale["query_order"] = query_order
    logger.info("售后查询: 从统一槽位取订单号 '%s'", order_no)
    return {"skills": {"after_sale": after_sale}}
```

- [ ] **Step 5: 改造 collect_refund_info（只收集原因/金额）**

`collect_refund_info` 不再从消息取订单号，改为从统一槽位取：

```python
async def collect_refund_info(state: ConversationState) -> dict:
    after_sale = dict(state.get("skills", {}).get("after_sale", {}))
    order_no = after_sale.get("order_no", "")
    refund_info = dict(state.get("skills", {}).get("refund", {}))
    if order_no:
        refund_info["order_no"] = order_no
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""

    if "reason" not in refund_info:
        refund_info["reason"] = last_msg
        logger.info("退单收集: 已记录退款原因 '%s'", last_msg[:30])
        return {"flow": {"response": "请输入退款金额："}, "skills": {"refund": refund_info}}

    if "amount" not in refund_info:
        refund_info["amount"] = last_msg
        logger.info("退单收集: 已记录退款金额 '%s'", last_msg[:30])
        return {"skills": {"refund": refund_info}}

    logger.info("退单收集: 信息已完整，准备提交流程")
    return {"skills": {"refund": refund_info}}
```

- [ ] **Step 6: 改造 check_order_mcp（统一槽位 + 子意图文案 + buyer_id）**

```python
async def check_order_mcp(state: ConversationState) -> dict:
    after_sale = state.get("skills", {}).get("after_sale", {})
    sub_intent = after_sale.get("sub_intent", "refund")
    order_id = after_sale.get("order_no", "")
    if not order_id:
        return {"mcp": {"order_status": "not_found", "error": "缺少订单号"}, "flow": {"response": "未提供订单号，请重新输入。"}}

    client = MCPClient.get_instance()
    try:
        result = await client.check_order(order_id)
        status = result.get("status", "not_found")
        buyer_id = result.get("buyer_id", 0)
        logger.info("MCP check_order: order=%s status=%s", order_id, status)

        if status == "pending_payment" or status == "pending_delivery":
            return {"mcp": {"order_status": status, "order_buyer_id": buyer_id}}
        if status == "in_delivery" or status == "delivered":
            if sub_intent == "refund":
                msg = "您的订单已发货/签收，暂时无法退款，请通过售后渠道处理。"
            else:
                msg = "您的订单已发货/配送中，无法取消。"
            return {"mcp": {"order_status": status}, "flow": {"response": msg}}
        return {"mcp": {"order_status": "not_found"}, "flow": {"response": f"未找到订单 {order_id}，请确认订单号是否正确。"}}
    except Exception as e:
        logger.error("MCP check_order 异常: %s", e)
        return {"mcp": {"order_status": "error", "error": str(e)}, "flow": {"intent": "human"}}
```

> 注：原实现 `status == "pending_delivery"` 返回空 response；现仅 `pending_payment`/`pending_delivery` 视为可操作状态（统一口径）。`order_buyer_id` 存入 `mcp`，供 `process_refund_mcp` / `cancel_order_mcp` 创建 case。

- [ ] **Step 7: 改造 process_refund_mcp（成功后创建 case）**

`process_refund_mcp` 退款成功后调用 `create_case`：

```python
async def process_refund_mcp(state: ConversationState) -> dict:
    refund_info = state.get("skills", {}).get("refund", {})
    order_id = refund_info.get("order_no", "")
    reason = refund_info.get("reason", "")
    amount = refund_info.get("amount", "")

    client = MCPClient.get_instance()
    try:
        result = await client.process_refund(order_id, reason, amount)
        if result.get("success"):
            logger.info("MCP process_refund: order=%s 退款成功", order_id)
            buyer_id = state.get("mcp", {}).get("order_buyer_id", 0)
            db = SessionLocal()
            try:
                create_case(db, order_no=order_id, buyer_id=buyer_id, case_type="refund", amount=amount, reason=reason)
            finally:
                db.close()
            return {"mcp": {"refund_success": True}, "flow": {"response": f"退款成功！订单 {order_id} 已退款 {amount} 元。（原因：{reason}）"}}
        else:
            logger.warning("MCP process_refund: order=%s 退款失败: %s", order_id, result.get("message", ""))
            return {"mcp": {"refund_success": False}, "flow": {"response": f"退款失败：{result.get('message', '未知错误')}"}}
    except Exception as e:
        logger.error("MCP process_refund 异常: %s", e)
        return {"mcp": {"refund_success": False, "error": str(e)}, "flow": {"intent": "human"}}
```

- [ ] **Step 8: 运行现有测试，确认预期失败**

Run: `cd backend && uv run pytest tests/test_ai_workflow.py -q`
Expected: 多处 FAIL（graph 尚未接新节点、check_order_mcp 逻辑变更）。此为预期，Task 5 修正 graph 后恢复。

- [ ] **Step 9: 提交**

```bash
git add backend/app/domain/ai/workflow/nodes.py
git commit -m "feat: 售后节点新增 ensure_order_no/confirm/cancel_order_mcp 并改造查询与退款节点"
```

---

### Task 5: Graph 路由改造（graph.py）

**Files:**
- Modify: `backend/app/domain/ai/workflow/graph.py`
- Test: `backend/tests/test_ai_workflow.py`

- [ ] **Step 1: 新增路由函数**

```python
def _route_after_ensure(state: ConversationState) -> str:
    after_sale = state.get("skills", {}).get("after_sale", {})
    if not after_sale.get("order_no"):
        return END
    return after_sale.get("sub_intent", "query_order")


def _route_after_confirm(state: ConversationState) -> str:
    after_sale = state.get("skills", {}).get("after_sale", {})
    if after_sale.get("confirmed"):
        sub_intent = after_sale.get("sub_intent", "")
        return "cancel_order_mcp" if sub_intent == "cancel_order" else "process_refund_mcp"
    return END
```

- [ ] **Step 2: 更新 _route_after_after_sale 支持四子意图**

```python
def _route_after_after_sale(state: ConversationState) -> str:
    after_sale = state.get("skills", {}).get("after_sale", {})
    sub_intent = after_sale.get("sub_intent", "query_order")
    if sub_intent in ("query_order", "cancel_order", "update_order", "refund"):
        return sub_intent
    return "query_order"
```

- [ ] **Step 3: 更新 check_order_mcp 后的路由**

`_route_after_check` 改为统一判断可操作状态，进入确认节点：

```python
def _route_after_check(state: ConversationState) -> str:
    mcp = state.get("mcp", {})
    status = mcp.get("order_status", "")
    if status in ("pending_payment", "pending_delivery"):
        return "confirm_after_sale"
    return END
```

- [ ] **Step 4: 更新 build_chat_graph**

新增节点注册与边：

```python
    workflow.add_node("ensure_order_no", ensure_order_no)
    workflow.add_node("confirm_after_sale", confirm_after_sale)
    workflow.add_node("cancel_order_mcp", cancel_order_mcp)
```

`enter_after_sale` 条件边改为四分支（都先经 `ensure_order_no`）：

```python
    workflow.add_conditional_edges(
        "enter_after_sale",
        _route_after_after_sale,
        {
            "query_order": "ensure_order_no",
            "cancel_order": "ensure_order_no",
            "update_order": "ensure_order_no",
            "refund": "ensure_order_no",
        },
    )
```

`ensure_order_no` 后按子意图路由（若未识别订单号则 END）：

```python
    workflow.add_conditional_edges(
        "ensure_order_no",
        _route_after_ensure,
        {
            "query_order": "collect_order_no",
            "cancel_order": "check_order_mcp",
            "update_order": "collect_update_order_info",
            "refund": "collect_refund_info",
            END: END,
        },
    )
```

`check_order_mcp` 后路由（可操作 → confirm，否则 END）：

```python
    workflow.add_conditional_edges(
        "check_order_mcp",
        _route_after_check,
        {
            "confirm_after_sale": "confirm_after_sale",
            END: END,
        },
    )
```

`confirm_after_sale` 后路由：

```python
    workflow.add_conditional_edges(
        "confirm_after_sale",
        _route_after_confirm,
        {
            "cancel_order_mcp": "cancel_order_mcp",
            "process_refund_mcp": "process_refund_mcp",
            END: END,
        },
    )
```

`cancel_order_mcp` 结束边：

```python
    workflow.add_edge("cancel_order_mcp", END)
```

同时更新 import 列表，加入 `ensure_order_no` / `confirm_after_sale` / `cancel_order_mcp`。

- [ ] **Step 5: 运行确认编译**

Run: `cd backend && uv run pytest tests/test_ai_workflow.py::TestGraph::test_build_compiles -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/domain/ai/workflow/graph.py
git commit -m "feat: graph 接入售后四子意图路由与确认环节"
```

---

### Task 6: 修复/更新测试（test_ai_workflow.py）

**Files:**
- Modify: `backend/tests/test_ai_workflow.py`

设计文档列出的新节点测试。更新旧断言（`ensure_order_no` 统一槽位改变了「消息即订单号」假设）。

- [ ] **Step 1: 新增 ensure_order_no 测试**

在 `TestNodes` 中追加：

```python
    @pytest.mark.asyncio
    async def test_ensure_order_no_matches_pattern(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "query_order"}},
            messages=[HumanMessage(content="查一下 ORD-123")],
        )
        result = await ensure_order_no(state)
        assert result["skills"]["after_sale"]["order_no"] == "ORD-123"

    @pytest.mark.asyncio
    async def test_ensure_order_no_asks_when_missing(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "query_order"}},
            messages=[HumanMessage(content="帮我查订单")],
        )
        result = await ensure_order_no(state)
        assert "请提供订单号" in result["flow"]["response"]
        assert "order_no" not in result["skills"]["after_sale"]

    @pytest.mark.asyncio
    async def test_ensure_order_no_skips_when_present(self) -> None:
        state = make_state(
            skills={"after_sale": {"sub_intent": "query_order", "order_no": "ORD-999"}},
            messages=[],
        )
        result = await ensure_order_no(state)
        assert result["skills"]["after_sale"]["order_no"] == "ORD-999"
```

- [ ] **Step 2: 新增 confirm_after_sale 测试**

```python
    @pytest.mark.asyncio
    async def test_confirm_after_sale_yes(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "cancel_order", "order_no": "ORD-1"}},
            messages=[HumanMessage(content="确认")],
        )
        result = await confirm_after_sale(state)
        assert result["skills"]["after_sale"]["confirmed"] is True

    @pytest.mark.asyncio
    async def test_confirm_after_sale_no(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "cancel_order", "order_no": "ORD-1"}},
            messages=[HumanMessage(content="不要")],
        )
        result = await confirm_after_sale(state)
        assert result["skills"]["after_sale"]["confirmed"] is False
        assert "取消" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_confirm_after_sale_asks_again(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "cancel_order", "order_no": "ORD-1"}},
            messages=[HumanMessage(content="随便")],
        )
        result = await confirm_after_sale(state)
        assert "确认" in result["flow"]["response"]
        assert "confirmed" not in result["skills"]["after_sale"]
```

- [ ] **Step 3: 新增 cancel_order 流程测试（graph 层）**

在 `TestGraph` 中追加：

```python
    @pytest.mark.asyncio
    async def test_cancel_order_full_flow(self) -> None:
        """cancel_order：查单通过 → 确认 → 取消成功"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_instance.update_order_status = AsyncMock(
                return_value={"success": True, "message": "ok"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "cancel_order", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            # Turn 1: 提供订单号 → 查单 → 询问确认
            state = make_state(messages=[HumanMessage(content="取消订单 ORD-777")])
            result = await graph.ainvoke(state)
            assert "确认" in result.get("flow", {}).get("response", "")
            assert result["skills"]["after_sale"]["order_no"] == "ORD-777"

            # Turn 2: 确认 → 取消成功
            state2 = make_state(
                skills={"after_sale": result["skills"]["after_sale"]},
                messages=[
                    HumanMessage(content="取消订单 ORD-777"),
                    HumanMessage(content="确认"),
                ],
            )
            result2 = await graph.ainvoke(state2)
            assert result2["mcp"]["cancel_success"] is True
            assert "取消" in result2.get("flow", {}).get("response", "")

    @pytest.mark.asyncio
    async def test_cancel_order_rejected_when_in_delivery(self) -> None:
        """配送中订单取消被拒"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "in_delivery", "buyer_id": 7}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "cancel_order", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()
            state = make_state(messages=[HumanMessage(content="取消订单 ORD-777")])
            result = await graph.ainvoke(state)
            assert "无法取消" in result.get("flow", {}).get("response", "")
```

- [ ] **Step 4: 更新 refund 全流程测试（加入确认环节）**

`test_refund_full_flow` 或等价测试：在 check_order 通过后，需再给一轮「确认」才能退款。参考 Task 5 graph 路由，新增：

```python
    @pytest.mark.asyncio
    async def test_refund_requires_confirmation(self) -> None:
        """退款需确认后才执行"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_instance.process_refund = AsyncMock(
                return_value={"success": True, "message": "退款成功"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "refund", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            # Turn 1: 订单号 + 原因 + 金额 → 查单 → 询问确认
            state = make_state(messages=[HumanMessage(content="ORD-888 商品坏了 199")])
            result = await graph.ainvoke(state)
            assert "确认退款" in result.get("flow", {}).get("response", "")

            # Turn 2: 确认 → 退款成功
            state2 = make_state(
                skills={"refund": result["skills"]["refund"], "after_sale": result["skills"]["after_sale"]},
                messages=[
                    HumanMessage(content="ORD-888 商品坏了 199"),
                    HumanMessage(content="确认"),
                ],
            )
            result2 = await graph.ainvoke(state2)
            assert result2["mcp"]["refund_success"] is True
            assert "退款成功" in result2.get("flow", {}).get("response", "")
```

> 注：Turn 1 中 `ORD-888 商品坏了 199` 命中订单号正则；`collect_refund_info` 将整句当 reason，金额从下一轮收集。若单轮测试不易收敛，可将 Turn 1 消息拆为多轮（见 Task 6 Step 5 的精确多轮版）。

- [ ] **Step 5: 更新现有 refund 多轮测试**

`test_refund_multi_turn_flow` 需调整：订单号现由 `ensure_order_no` 正则提取，`collect_refund_info` 只收原因/金额，且中途需确认。更新为：

```python
    @pytest.mark.asyncio
    async def test_refund_multi_turn_flow(self) -> None:
        """多轮退款：订单号 → 原因 → 金额 → 确认 → 退款"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_instance.process_refund = AsyncMock(
                return_value={"success": True, "message": "退款成功"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "refund", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            def run(turn_messages):
                state = make_state(messages=turn_messages)
                return graph.ainvoke(state)

            # Turn 1: 提供订单号（ensure_order_no 提取 ORD-1001）→ 进入 collect_refund_info 问原因
            result1 = await run([HumanMessage(content="退款 ORD-1001")])
            assert result1["skills"]["after_sale"]["order_no"] == "ORD-1001"
            assert "退款金额" in result1.get("flow", {}).get("response", "")

            # Turn 2: 原因 + 金额 → 查单 → 问确认
            state2 = make_state(
                skills={"after_sale": result1["skills"]["after_sale"], "refund": result1["skills"]["refund"]},
                messages=[HumanMessage(content="退款 ORD-1001"), HumanMessage(content="商品坏了 199")],
            )
            result2 = await graph.ainvoke(state2)
            assert result2["skills"]["refund"]["reason"] == "商品坏了 199"
            assert "确认退款" in result2.get("flow", {}).get("response", "")

            # Turn 3: 确认 → 退款成功
            state3 = make_state(
                skills={"after_sale": result2["skills"]["after_sale"], "refund": result2["skills"]["refund"]},
                messages=[HumanMessage(content="退款 ORD-1001"), HumanMessage(content="商品坏了 199"), HumanMessage(content="确认")],
            )
            result3 = await graph.ainvoke(state3)
            assert result3["mcp"]["refund_success"] is True
            assert "退款成功" in result3.get("flow", {}).get("response", "")
```

- [ ] **Step 6: 更新 check_order_mcp 相关旧测试**

`TestMcpNodes` 中的 `test_check_order_mcp_*` 测试：
- `test_check_order_mcp_pending_delivery`：order_no 现从统一槽位读，state 需带 `after_sale.order_no`（原用 `skills.refund.order_no`）。
- `test_check_order_mcp_in_delivery`：断言文案改为「无法退款」（refund 场景）。
- `test_check_order_mcp_delivered`：同理。
- `test_check_order_mcp_missing_order_no`：无槽位时提示「未提供订单号」。

例如 `test_check_order_mcp_pending_delivery` 改为：

```python
    @pytest.mark.asyncio
    async def test_check_order_mcp_pending_delivery(self) -> None:
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "pending_delivery", "buyer_id": 7, "amount": "199.00", "message": "订单查询成功"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-PENDING-001"}, "refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "pending_delivery"
            assert result["mcp"]["order_buyer_id"] == 7
            assert "response" not in result.get("flow", {})
```

- [ ] **Step 7: 更新 graph 路由单元测试**

`TestGraphRoutingLogic` 中：
- `test_route_after_after_sale_*` 补 `cancel_order` 用例。
- 新增 `test_route_after_ensure_missing` / `test_route_after_ensure_present`。
- 新增 `test_route_after_confirm_confirmed_cancel` / `confirmed_refund` / `not_confirmed`。

```python
    def test_route_after_after_sale_cancel(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_after_sale
        state = make_state(skills={"after_sale": {"sub_intent": "cancel_order"}})
        assert _route_after_after_sale(state) == "cancel_order"

    def test_route_after_ensure_missing(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_ensure
        from langgraph.graph import END
        state = make_state(skills={"after_sale": {"sub_intent": "query_order"}})
        assert _route_after_ensure(state) == END

    def test_route_after_ensure_present_query(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_ensure
        state = make_state(skills={"after_sale": {"sub_intent": "query_order", "order_no": "ORD-1"}})
        assert _route_after_ensure(state) == "query_order"

    def test_route_after_confirm_cancel(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_confirm
        state = make_state(skills={"after_sale": {"sub_intent": "cancel_order", "confirmed": True}})
        assert _route_after_confirm(state) == "cancel_order_mcp"

    def test_route_after_confirm_refund(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_confirm
        state = make_state(skills={"after_sale": {"sub_intent": "refund", "confirmed": True}})
        assert _route_after_confirm(state) == "process_refund_mcp"

    def test_route_after_confirm_not_confirmed(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_confirm
        from langgraph.graph import END
        state = make_state(skills={"after_sale": {"sub_intent": "cancel_order"}})
        assert _route_after_confirm(state) == END
```

- [ ] **Step 8: 更新 test_has_all_nodes**

`expected` 集合补 `ensure_order_no` / `confirm_after_sale` / `cancel_order_mcp`。

- [ ] **Step 9: 运行测试**

Run: `cd backend && uv run pytest tests/test_ai_workflow.py -q`
Expected: PASS

- [ ] **Step 10: 提交**

```bash
git add backend/tests/test_ai_workflow.py
git commit -m "test: 售后增强节点与流程测试"
```

---

### Task 7: MCP 测试与回归

**Files:**
- Modify: `backend/tests/test_mcp_server.py`

- [ ] **Step 1: 验证现有 MCP 测试不受状态机收紧影响**

`test_update_order_status_legal`（pending_payment→pending_delivery）与 `illegal`（pending_payment→in_delivery）不受影响。运行：

Run: `cd backend && uv run pytest tests/test_mcp_server.py -q`
Expected: PASS

- [ ] **Step 2: 新增状态非法返回测试**

```python
@pytest.mark.anyio
async def test_update_order_status_in_delivery_rejected() -> None:
    db = SessionLocal()
    db.add(Order(order_no="ORD-MCP-003", buyer_id=1, amount="100.00", status="in_delivery"))
    db.commit()
    db.close()

    result = await call_tool("update_order_status", {"order_id": "ORD-MCP-003", "status": "delivered"})
    payload = json.loads(result[0].text)
    assert payload["success"] is False
```

- [ ] **Step 3: 运行确认通过**

Run: `cd backend && uv run pytest tests/test_mcp_server.py -q`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_mcp_server.py
git commit -m "test: MCP 状态机收紧回归"
```

---

### Task 8: 全量回归

**Files:**
- 全部改动文件

- [ ] **Step 1: 运行全量后端测试**

Run: `cd backend && uv run pytest tests/ -q`
Expected: 全部 PASS

- [ ] **Step 2: 还原 uv.lock**

Run: `cd /Users/ziyuan.li/Projects/Delevelop/Work/ec-main && git checkout backend/uv.lock`
说明：`uv run pytest` 会改动 `backend/uv.lock`（langfuse 遗留锁不一致），需还原。

- [ ] **Step 3: 前端类型检查**

Run: `cd apps/admin && npx tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 4: 检查 git 状态**

Run: `git status --short`
Expected: 仅预期文件被修改，无 `backend/uv.lock` 残留变更。

---

## 自审记录

**Spec 覆盖：**
- 槽位补充（ensure_order_no）→ Task 4 Step 1、Task 5、Task 6
- cancel_order 子意图 → Task 3、Task 4 Step 3、Task 5、Task 6 Step 3
- 退款确认 → Task 4 Step 2/6/7、Task 5 Step 3/4、Task 6 Step 4/5
- 售后 case 落库 → Task 2、Task 4 Step 3/7
- 状态口径统一 → Task 1、Task 4 Step 6、Task 7

**占位符扫描：** 无 TBD/TODO；所有代码步骤给出完整代码。

**类型一致性：** `after_sale.order_no` 统一槽位在所有节点一致；`mcp.order_buyer_id` 在 check_order_mcp 写入、process_refund_mcp/cancel_order_mcp 读取一致；`create_case` 签名在 Task 2 定义、Task 4 调用一致（注：`create_case(state, db=None, ...)` 中的 `state` 参数为占位，实际实现应直接用 `create_case(db, ...)`，由执行者按 Task 2 签名调用——见下方【执行注意】）。

## 执行注意

1. **create_case 调用修正**：Task 4 Step 3/7 中 `create_case(state, db=None, ...)` 写法有误。实际应使用 `SessionLocal()` 打开会话再调用 `create_case(db, ...)`，参照 nodes.py 中 `handoff_human` 的 `SessionLocal` 用法。正确写法：

```python
from app.db.session import SessionLocal
from app.domain.after_sale import create_case

# 在退款/取消失败分支成功后：
db = SessionLocal()
try:
    create_case(db, order_no=order_id, buyer_id=buyer_id, case_type="refund", amount=amount, reason=reason)
finally:
    db.close()
```

2. **多轮确认的状态持久化**：`after_sale.confirmed` 通过 `after_sale_info` 系统消息持久化（engine.py 已支持）。注意：确认成功后应清理 `confirmed`（下次进入新流程时子意图已确定，短路逻辑不受影响）。

3. **cancel_order 多轮确认的槽位持久化**：Turn 1 确认询问后，`after_sale.order_no` 已持久化；Turn 2 用户回复「确认」时 `ensure_order_no` 因槽位已有值直接放行。若 Turn 2 消息含新订单号但槽位已有值，`ensure_order_no` 不会覆盖——符合预期（确认中的订单不变）。

4. **`_classify_confirm` 鲁棒性**：对「确认退款」「好的，确认」等前导词匹配已覆盖；测试用「确认」单字即可。

5. **旧 `test_refund_collection_routing`**：该测试曾 mock `sub_intent_prompt` 返回 refund 且 skills.refund 已完整。现 `collect_refund_info` 不再收 order_no（改从槽位取），该测试需同步更新：state 需带 `after_sale.order_no`，否则 collect_refund_info 无 order_no。Task 6 已覆盖。
