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
