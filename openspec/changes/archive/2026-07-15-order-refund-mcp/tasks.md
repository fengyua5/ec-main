## 1. Order 数据模型

- [x] 1.1 创建 `backend/app/models/order.py`，定义 `Order` 模型（order_no, buyer_id, amount, status, created_at）
- [x] 1.2 在 `backend/app/models/__init__.py` 导出 Order
- [x] 1.3 添加种子数据脚本：创建 `pending_delivery`、`in_delivery`、`delivered` 三种状态订单各一条

## 2. MCP Server

- [x] 2.1 安装 `mcp` Python SDK 依赖
- [x] 2.2 创建 `backend/app/mcp/server.py`，实现 stdio MCP Server
- [x] 2.3 注册 `check_order` 工具：查询 SQLite 订单状态
- [x] 2.4 注册 `process_refund` 工具：验证订单状态后处理退款

## 3. MCP Client 集成

- [x] 3.1 创建 `backend/app/mcp/client.py`，封装 stdio 子进程启动和工具调用
- [x] 3.2 实现 `check_order(order_id)` 方法
- [x] 3.3 实现 `process_refund(order_id, reason, amount)` 方法

## 4. LangGraph 工作流集成

- [x] 4.1 修改 `collect_refund_info`：信息收集完毕后不再直接返回，而是转交 `check_order_mcp` 节点
- [x] 4.2 新增 `check_order_mcp` 节点：调用 MCP `check_order`，根据状态分支到退款/拒绝/降级
- [x] 4.3 新增 `process_refund_mcp` 节点：调用 MCP `process_refund`，返回结果
- [x] 4.4 更新 `graph.py`：注册新节点，添加条件边路由
- [x] 4.5 保留原有 `process_refund` 节点作为 MCP 不可用时的降级路径

## 5. 验证

- [x] 5.1 编写 MCP Server 单元测试（测试工具注册和返回格式）
- [x] 5.2 编写 MCP Client 集成测试（测试子进程启动和工具调用）
- [x] 5.3 编写工作流集成测试（覆盖未配送→退款、配送中→拒绝、订单不存在等场景）
- [x] 5.4 全量运行 pytest 确保 0 failure
