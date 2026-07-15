import logging

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from app.db.session import SessionLocal
from app.models.order import Order

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
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "check_order":
        order_id = arguments.get("order_id", "")
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.order_no == order_id).first()
            if not order:
                return [types.TextContent(type="text", text='{"status": "not_found", "message": "订单不存在"}')]

            return [types.TextContent(
                type="text",
                text=f'{{"status": "{order.status}", "amount": "{order.amount}", "message": "订单查询成功"}}',
            )]
        finally:
            db.close()

    elif name == "process_refund":
        order_id = arguments.get("order_id", "")
        reason = arguments.get("reason", "")
        amount = arguments.get("amount", "")

        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.order_no == order_id).first()
            if not order:
                return [types.TextContent(type="text", text='{"success": false, "message": "订单不存在"}')]

            if order.status != "pending_delivery":
                return [types.TextContent(
                    type="text",
                    text=f'{{"success": false, "message": "订单当前状态为 {order.status}，无法退款"}}',
                )]

            order.status = "refunded"
            db.commit()
            return [types.TextContent(
                type="text",
                text=f'{{"success": true, "message": "退款成功，金额 {amount}"}}',
            )]
        finally:
            db.close()

    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
