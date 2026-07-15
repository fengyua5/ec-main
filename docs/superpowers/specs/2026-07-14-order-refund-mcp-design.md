---
comet_change: order-refund-mcp
role: technical-design
canonical_spec: openspec
---

# 订单退款 MCP 服务设计文档

## 背景

AI 客服现有退单意图通过 `collect_refund_info` + `process_refund` 模拟处理，不涉及真实订单系统。需要将订单退款能力封装为 MCP（Model Context Protocol）服务，通过标准接口查询订单状态并执行条件退款。

## State 分层重构

将扁平的 `ConversationState` 重构为三层命名空间：

```python
class ConversationState(TypedDict):
    messages: list[HumanMessage | AIMessage]   # 全局对话历史
    flow: dict                                  # 工作流上下文
    skills: dict[str, Any]                     # 技能隔离区
    mcp: dict                                   # MCP 调用记录
```

### flow

```python
flow = {
    "intent": None | str,        # classify_intent 输出
    "confidence": float,
    "conversation_id": int | None,
    "response": "",              # 当前回复文本
}
```

### skills

```python
skills = {
    "refund": {
        "order_no": str,
        "reason": str,
        "amount": str,
    },
    "faq": {
        "context": list[dict],
    }
}
```

### mcp

```python
mcp = {
    "order_status": None | str,   # pending_delivery / in_delivery / not_found
    "refund_success": None | bool,
    "error": None | str,
}
```

## MCP 架构

### 通信模式

Python stdio 子进程模式。ChatEngine 初始化时启动 MCP Server 子进程，通过 stdin/stdout JSON-RPC 通信，进程级共享一个 Server 实例。

```
ChatEngine.__init__ → subprocess.Popen(mcp_server.py) → stdio 通信
ChatEngine.__del__  → process.terminate()
```

### MCP Server 工具

| 工具 | 参数 | 返回 | 逻辑 |
|------|------|------|------|
| `check_order` | `order_id: str` | `{status, amount, message}` | 查询 SQLite orders 表 |
| `process_refund` | `order_id, reason, amount` | `{success, message}` | 验证状态后标记退款 |

### Order 数据模型

SQLAlchemy `orders` 表：

```sql
order_no  VARCHAR PRIMARY KEY
buyer_id  INTEGER
amount    VARCHAR
status    VARCHAR  -- pending_delivery / in_delivery / delivered
created_at DATETIME
```

种子数据：`pending_delivery`、`in_delivery`、`delivered` 各一条。

## LangGraph 工作流集成

### 新增/修改节点

| 节点 | 类型 | 职责 |
|------|------|------|
| `collect_refund_info` | 修改 | 信息存入 `skills["refund"]`，填满后转 `check_order_mcp` |
| `check_order_mcp` | 新增 | 调 MCP `check_order`，根据 status 条件分支 |
| `process_refund_mcp` | 新增 | 调 MCP `process_refund` |
| `process_refund` | 保留 | MCP 不可用时降级路径 |

### 条件边

```python
{
    "proceed_refund": "process_refund_mcp",
    "reject": END,
    "not_found": END,
}
```

### 流程

```
classify_intent → "refund"
    → collect_refund_info（多轮，填 skills["refund"]）
        → check_order_mcp（调 MCP check_order）
            ├── pending_delivery → process_refund_mcp → "退款成功"
            ├── in_delivery      → "订单在配送中，无法退款"
            └── not_found        → "未找到该订单"
```

## 降级策略

`check_order_mcp` 节点中 MCP 调用失败或超时时，将 `mcp["error"]` 设为错误信息，`flow["intent"]` 回退到 `"human"`，转到 `process_refund` 降级节点。

## 测试策略

Mock MCP Client 层，全覆盖：

- 未配送订单 → 调用 `process_refund_mcp` → 退款成功
- 配送中订单 → 拒绝退款 → 回复 "订单在配送中"
- 订单不存在 → 回复提示
- MCP 异常 → 降级到 `process_refund` 模拟逻辑
