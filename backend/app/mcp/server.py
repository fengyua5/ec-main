import logging

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from app.db.session import SessionLocal
from app.domain.orders import get_order, update_order_status

logger = logging.getLogger(__name__)

app = Server("order-refund")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="check_order",
            description="查询订单状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号"},
                },
                "required": ["order_id"],
            },
        ),
        types.Tool(
            name="process_refund",
            description="处理订单退款",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号"},
                    "reason": {"type": "string", "description": "退款原因"},
                    "amount": {"type": "string", "description": "退款金额"},
                },
                "required": ["order_id", "reason", "amount"],
            },
        ),
        types.Tool(
            name="update_order_status",
            description="修改订单状态，仅允许合法流转",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号"},
                    "status": {"type": "string", "description": "目标状态"},
                },
                "required": ["order_id", "status"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "check_order":
        order_id = arguments.get("order_id", "")
        db = SessionLocal()
        try:
            order = get_order(db, order_id)
            return [types.TextContent(
                type="text",
                text=f'{{"status": "{order.status}", "amount": "{order.amount}", "message": "订单查询成功"}}',
            )]
        except Exception:
            return [types.TextContent(type="text", text='{"status": "not_found", "message": "订单不存在"}')]
        finally:
            db.close()

    elif name == "process_refund":
        order_id = arguments.get("order_id", "")
        amount = arguments.get("amount", "")

        db = SessionLocal()
        try:
            order = update_order_status(db, order_id, "refunded")
            return [types.TextContent(
                type="text",
                text=f'{{"success": true, "message": "退款成功，金额 {amount}"}}',
            )]
        except Exception as exc:
            return [types.TextContent(
                type="text",
                text=f'{{"success": false, "message": "{exc.detail if hasattr(exc, "detail") else str(exc)}"}}',
            )]
        finally:
            db.close()

    elif name == "update_order_status":
        order_id = arguments.get("order_id", "")
        target = arguments.get("status", "")

        db = SessionLocal()
        try:
            order = update_order_status(db, order_id, target)
            return [types.TextContent(
                type="text",
                text=f'{{"success": true, "order_no": "{order.order_no}", "status": "{order.status}", "message": "订单状态修改成功"}}',
            )]
        except Exception as exc:
            return [types.TextContent(
                type="text",
                text=f'{{"success": false, "message": "{exc.detail if hasattr(exc, "detail") else str(exc)}"}}',
            )]
        finally:
            db.close()

    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
