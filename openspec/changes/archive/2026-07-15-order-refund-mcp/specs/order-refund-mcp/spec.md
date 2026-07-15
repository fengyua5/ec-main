## ADDED Requirements

### Requirement: MCP Server 注册 check_order 工具
MCP Server SHALL 注册 `check_order` 工具，接收订单号查询订单状态。

#### Scenario: 查询存在的订单
- **WHEN** 客户端调用 `check_order` 传入存在的 `order_id`
- **THEN** 返回订单信息，包含 `status`、`amount`、`message`

#### Scenario: 查询不存在的订单
- **WHEN** 客户端调用 `check_order` 传入不存在的 `order_id`
- **THEN** 返回 `status: "not_found"`，`message` 提示订单不存在

### Requirement: MCP Server 注册 process_refund 工具
MCP Server SHALL 注册 `process_refund` 工具，处理订单退款。

#### Scenario: 退款成功
- **WHEN** 客户端调用 `process_refund` 传入可退款的 `order_id`、`reason`、`amount`
- **THEN** 返回 `success: true`，`message` 提示退款已处理

#### Scenario: 退款失败（订单不可退款）
- **WHEN** 客户端调用 `process_refund` 传入配送中的 `order_id`
- **THEN** 返回 `success: false`，`message` 提示订单正在配送中无法退款

### Requirement: Order 数据模型
系统 SHALL 提供 `Order` SQLAlchemy 模型，包含 `order_no`、`buyer_id`、`amount`、`status`、`created_at` 字段。`status` SHALL 支持 `pending_delivery`、`in_delivery`、`delivered`。

#### Scenario: 订单表初始化
- **WHEN** 数据库初始化时
- **THEN** `orders` 表自动创建，包含种子演示数据

#### Scenario: 订单状态枚举
- **WHEN** 创建订单时未指定状态
- **THEN** 默认状态为 `pending_delivery`

### Requirement: LangGraph 集成 check_order
LangGraph 工作流 SHALL 在退单意图路径中，多轮收集信息完成后调用 MCP `check_order` 检查订单状态。

#### Scenario: 订单未配送走退款
- **WHEN** `check_order` 返回 `status: "pending_delivery"`
- **THEN** 自动调用 MCP `process_refund` 处理退款，回复退款成功消息

#### Scenario: 订单配送中拒绝退款
- **WHEN** `check_order` 返回 `status: "in_delivery"`
- **THEN** 放弃退款流程，回复用户"您的订单正在配送中，暂时无法退款"

#### Scenario: 订单不存在
- **WHEN** `check_order` 返回 `status: "not_found"`
- **THEN** 回复用户提示订单号有误或订单不存在

### Requirement: 降级路径
当 MCP Server 不可用时，系统 SHALL 回退到原有的 process_refund 模拟逻辑。

#### Scenario: MCP 不可用时降级
- **WHEN** MCP Server 启动失败或调用超时
- **THEN** 使用原有的 `process_refund` 节点处理退单
