# Comet Design Handoff

- Change: order-refund-mcp
- Phase: design
- Mode: compact
- Context hash: 70aebdcbd77f56a2afa5e133e376d74d3338b739698c86f02a1dabb23b2b8c2d

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/order-refund-mcp/proposal.md

- Source: openspec/changes/order-refund-mcp/proposal.md
- Lines: 1-29
- SHA256: dadc83ba9f2129d8a7fe6fc0aa8048c37c35631915157843f31ee18863ee8db7

```md
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
```

## openspec/changes/order-refund-mcp/design.md

- Source: openspec/changes/order-refund-mcp/design.md
- Lines: 1-59
- SHA256: ace46c10fda6f1c389aa56539345e1493baea4833f0bf133ae7076a1176c482a

```md
## Context

AI 客服已实现 LangGraph 工作流，包含退单意图的 collect_refund_info（多轮收集订单号/原因/金额）和 process_refund（模拟成功）。需要引入 MCP（Model Context Protocol）标准化接口对接订单服务，使 LLM 可通过 LangGraph 节点调用 MCP 工具完成订单状态检查和条件退款。

## Goals / Non-Goals

**Goals:**
- 搭建 MCP Server（Python stdio 模式），注册 `check_order` 和 `process_refund` 工具
- 在 LangGraph 工作流中通过 MCP Client 调用 `check_order` 判断可退款性
- 未配送订单自动调用 `process_refund`；配送中订单拒绝并回复原因
- 新增 `Order` 模型（SQLite），含种子数据用于演示

**Non-Goals:**
- 不涉及真实支付网关或外部订单系统对接
- 不改动现有 classify_intent、FAQ、人工客服节点
- 不做前端或 SDK 改动

## Decisions

| 决策 | 方案 | 原因 |
|------|------|------|
| MCP 通信模式 | stdio 子进程 | 标准 MCP 模式，无需 HTTP 服务端口，适合单进程部署 |
| MCP SDK | `mcp`（Python） | Anthropic 官方 SDK，协议实现完整 |
| MCP Server 位置 | `backend/app/mcp/server.py` | 贴合现有项目结构，复用 SQLAlchemy 和配置 |
| 订单模型 | SQLAlchemy `orders` 表 | 复用现有 SQLite，`status` 字段含 `pending_delivery` / `in_delivery` / `delivered` |
| 集成方式 | LangGraph 节点直接调用 MCP Client | process_message 流程中同步调用，避免异步复杂性 |
| 退单流程 | 保留原 collect_refund_info 多轮收集 → 新增 check_order → 分支：退款/拒绝 | 最小改动原则，复用已验证的多轮交互 |

## Architecture

```
LangGraph Workflow
    │
    ├── classify_intent → "refund"
    │       │
    │       ▼
    ├── collect_refund_info（多轮收集 order_no/reason/amount）
    │       │  ← 信息收集完毕
    │       ▼
    ├── [NEW] check_order_mcp
    │       │
    │       ├── 订单未配送 ──→ [NEW] process_refund_mcp ──→ 退款成功
    │       │
    │       └── 订单配送中 ──→ 回复"订单在配送中，无法退款"
    │
    ├── process_refund（保留原模拟路径作为降级备选）

MCP Server (stdio subprocess)
    │
    ├── check_order(order_id: str) → {status, amount, message}
    │
    └── process_refund(order_id: str, reason: str) → {success, message}
```

## Risks / Trade-offs

- MCP Server 启动开销：每次子进程启动有毫秒级延迟 → 可接受，退单非高频操作
- stdio 模式下 MCP Server 无法处理并发请求 → 退单流程串行，无并发需求
- 订单数据为内存演示数据 → 设计上已隔离，后续可替换为真实订单服务
```

## openspec/changes/order-refund-mcp/tasks.md

- Source: openspec/changes/order-refund-mcp/tasks.md
- Lines: 1-33
- SHA256: 2b5a5f2c0234fd0c1d8eaf24e410fc3c167b346541823d0e057b4f4d81488a27

```md
## 1. Order 数据模型

- [ ] 1.1 创建 `backend/app/models/order.py`，定义 `Order` 模型（order_no, buyer_id, amount, status, created_at）
- [ ] 1.2 在 `backend/app/models/__init__.py` 导出 Order
- [ ] 1.3 添加种子数据脚本：创建 `pending_delivery`、`in_delivery`、`delivered` 三种状态订单各一条

## 2. MCP Server

- [ ] 2.1 安装 `mcp` Python SDK 依赖
- [ ] 2.2 创建 `backend/app/mcp/server.py`，实现 stdio MCP Server
- [ ] 2.3 注册 `check_order` 工具：查询 SQLite 订单状态
- [ ] 2.4 注册 `process_refund` 工具：验证订单状态后处理退款

## 3. MCP Client 集成

- [ ] 3.1 创建 `backend/app/mcp/client.py`，封装 stdio 子进程启动和工具调用
- [ ] 3.2 实现 `check_order(order_id)` 方法
- [ ] 3.3 实现 `process_refund(order_id, reason, amount)` 方法

## 4. LangGraph 工作流集成

- [ ] 4.1 修改 `collect_refund_info`：信息收集完毕后不再直接返回，而是转交 `check_order_mcp` 节点
- [ ] 4.2 新增 `check_order_mcp` 节点：调用 MCP `check_order`，根据状态分支到退款/拒绝/降级
- [ ] 4.3 新增 `process_refund_mcp` 节点：调用 MCP `process_refund`，返回结果
- [ ] 4.4 更新 `graph.py`：注册新节点，添加条件边路由
- [ ] 4.5 保留原有 `process_refund` 节点作为 MCP 不可用时的降级路径

## 5. 验证

- [ ] 5.1 编写 MCP Server 单元测试（测试工具注册和返回格式）
- [ ] 5.2 编写 MCP Client 集成测试（测试子进程启动和工具调用）
- [ ] 5.3 编写工作流集成测试（覆盖未配送→退款、配送中→拒绝、订单不存在等场景）
- [ ] 5.4 全量运行 pytest 确保 0 failure
```

## openspec/changes/order-refund-mcp/specs/order-refund-mcp/spec.md

- Source: openspec/changes/order-refund-mcp/specs/order-refund-mcp/spec.md
- Lines: 1-56
- SHA256: 403a6f3e4759ac5eb74cae662a405e9cd2ca124bb640b907cf9d9b4140bd3f7d

```md
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
```

