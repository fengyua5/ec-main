## Why

现有 AI 客服工作流中的退单处理（collect_refund_info + process_refund）是纯逻辑模拟，无法对接真实订单系统。需要将订单退款能力封装为标准 MCP（Model Context Protocol）服务，通过 LangGraph 节点调用 MCP 工具实现订单状态检查和条件退款，为未来对接真实订单系统提供标准化接口。

## What Changes

- 新增 `Order` SQLAlchemy 模型（SQLite），含订单号、买家、金额、状态字段，初始化种子数据
- 新增 MCP Server（Python stdio 模式），注册 `check_order` 和 `process_refund` 两个工具
- 新增 `order_refund` MCP Client 模块，在 LangGraph 工作流中调用 MCP Server
- 修改 `collect_refund_info` 节点：多轮收集完成后调用 MCP `check_order` 判断订单状态
- 新增 `mcp_refund` 节点：订单未配送时调用 `process_refund` 处理退款
- 如果订单处于配送状态，拒绝退款并回复"订单在配送中"
- 修改 `process_refund` 节点作为备选降级路径

## Capabilities

### New Capabilities
- `order-refund-mcp`: MCP Server + LangGraph 集成，提供标准化的订单退款工具链

### Modified Capabilities

（无）

## Impact

- 新增依赖：`mcp` Python SDK
- 新增文件：`backend/app/models/order.py`、`backend/app/mcp/server.py`、`backend/app/mcp/client.py`
- 修改文件：`backend/app/domain/ai/workflow/nodes.py`（新增/修改退单相关节点）
- 数据：SQLite 新增 `orders` 表，包含种子数据
