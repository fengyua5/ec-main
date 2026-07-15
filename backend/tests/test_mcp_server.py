import json
import pytest
from app.mcp.server import app, list_tools, call_tool


@pytest.mark.anyio
async def test_list_tools() -> None:
    tools = await list_tools()
    names = [t.name for t in tools]
    assert "check_order" in names
    assert "process_refund" in names
