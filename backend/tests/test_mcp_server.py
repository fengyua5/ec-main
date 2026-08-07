import json
import pytest
from app.mcp.server import app, list_tools, call_tool
from app.models.user import Base
from app.models.order import Order
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.mark.anyio
async def test_list_tools() -> None:
    tools = await list_tools()
    names = [t.name for t in tools]
    assert "check_order" in names
    assert "process_refund" in names
    assert "update_order_status" in names


@pytest.mark.anyio
async def test_update_order_status_legal() -> None:
    db = SessionLocal()
    db.add(Order(order_no="ORD-MCP-001", buyer_id=1, amount="100.00", status="pending_payment"))
    db.commit()
    db.close()

    result = await call_tool("update_order_status", {"order_id": "ORD-MCP-001", "status": "pending_delivery"})
    payload = json.loads(result[0].text)
    assert payload["success"] is True
    assert payload["status"] == "pending_delivery"


@pytest.mark.anyio
async def test_update_order_status_illegal() -> None:
    db = SessionLocal()
    db.add(Order(order_no="ORD-MCP-002", buyer_id=1, amount="100.00", status="pending_payment"))
    db.commit()
    db.close()

    result = await call_tool("update_order_status", {"order_id": "ORD-MCP-002", "status": "in_delivery"})
    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "不允许" in payload["message"]


@pytest.mark.anyio
async def test_update_order_status_not_found() -> None:
    result = await call_tool("update_order_status", {"order_id": "ORD-NOPE", "status": "pending_delivery"})
    payload = json.loads(result[0].text)
    assert payload["success"] is False
    assert "不存在" in payload["message"]
