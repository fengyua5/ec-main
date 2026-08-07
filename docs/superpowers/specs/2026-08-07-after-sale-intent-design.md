# 售后意图模块设计

日期：2026-08-07

## 背景

EC Main 的 AI 客服意图识别目前只有四个主意图：`faq` / `refund` / `human` / `greeting`。`refund` 意图走一条退款流程（收集订单号/原因/金额 → 查订单 → 退款）。需求：把 `refund` 意图升级为「售后」模块，让「查询订单」「修改订单」「退款」都识别为售后的意图，并在售后模块内通过二次子意图分类分别处理。

## 目标

- 主意图新增 `after_sale`（售后），移除 `refund`。
- 售后模块内用子意图分类器细分：`query_order`（查订单）/ `update_order`（改订单）/ `refund`（退款）。
- 三个子流程均真实调用 MCP 工具完成操作。

## 范围决策

- 主意图进入售后后，直接用当前用户消息做子意图分类，不再多问一轮。
- 修改订单流程：先收集订单号，再收集目标状态；改状态时后端已校验订单存在（相当于查详情后再改）。
- 保留现有退款链路 `collect_refund_info → check_order_mcp → process_refund_mcp`。
- 子意图一旦确定，多轮流程中不再漂移（`classify_intent` 与 `enter_after_sale` 均做短路判断）。

## 意图定义

### 主意图（prompts.py `INTENT_SYSTEM_PROMPT`）

类别：`faq` / `after_sale` / `human` / `greeting`

- `faq`：常见问题（退货政策、运费、发货时间等）
- `after_sale`：售后类诉求，包括查询订单、修改订单、退款/退货
- `human`：要求转接人工客服
- `greeting`：打招呼或问候

### 子意图（prompts.py 新增 `sub_intent_prompt`）

类别：`query_order` / `update_order` / `refund`

- `query_order`：查询订单状态或详情
- `update_order`：修改订单（如修改状态）
- `refund`：申请退款或退货

## 节点设计（nodes.py）

| 节点 | 职责 |
|---|---|
| `enter_after_sale` | 售后入口。若 `skills.after_sale.sub_intent` 未设置，用 `sub_intent_prompt` 对当前用户消息分类并写入 state；已设置则跳过分类，保持子意图不变 |
| `collect_order_no` | query_order 用：把用户消息当作订单号记录到 `skills.after_sale.query_order.order_no` |
| `query_order_mcp` | 调 MCP `check_order`，返回订单完整详情（订单号/买家/金额/状态/时间）给用户 |
| `collect_update_order_info` | update_order 用：先收集订单号，再询问目标状态；状态收集完整后进入 `update_order_mcp` |
| `update_order_mcp` | 调 MCP `update_order_status`（内部经 domain 校验订单存在与状态流转合法性） |

保留原有节点：`classify_intent`、`handle_greeting`、`retrieve_faq`、`answer_faq`、`collect_refund_info`、`process_refund`、`handoff_human`、`check_order_mcp`、`process_refund_mcp`。

### classify_intent 短路

新增逻辑：若 `skills.after_sale.sub_intent` 已设置（售后多轮流程进行中），直接返回主意图 `after_sale`，不调用主 LLM 分类。

## State 扩展（state.py / engine.py）

`skills` 增加 `after_sale` 结构：

```python
"after_sale": {
    "sub_intent": "query_order" | "update_order" | "refund" | None,
    "query_order": {"order_no": str},
    "update_order": {"order_no": str, "status": str},
}
```

engine.py 持久化逻辑从仅持久化 `refund_info`，扩展为同时持久化 `after_sale`（沿用 `msg_type` 系统消息模式，消息类型区分 `refund_info` 与 `after_sale_info`）。

## Graph 路由（graph.py）

```
classify_intent:
  greeting → handle_greeting
  faq → retrieve_faq
  after_sale → enter_after_sale
  human → handoff_human

enter_after_sale:
  query_order → collect_order_no → query_order_mcp → END
  update_order → collect_update_order_info → update_order_mcp → END
  refund → collect_refund_info → check_order_mcp → process_refund_mcp → END
```

## MCP 扩展

`server.py` 的 `check_order` 返回完整订单字段：`order_no` / `buyer_id` / `amount` / `status` / `created_at`（当前仅 status/amount）。`client.py` 的 `check_order` 对应解析返回。

## 测试

- `test_ai_workflow.py`：
  - `enter_after_sale` 子意图分类（query_order / update_order / refund）
  - 子意图已设置时跳过分类
  - query_order 全流程（收集订单号 → MCP 返回详情）
  - update_order 全流程（收集订单号 + 状态 → MCP 改状态）
  - refund 链路回归
  - `classify_intent` 售后进行中短路
- `test_mcp_server.py`：`check_order` 返回完整字段
- `test_ai_api_web.py`：SSE intent 事件仍正常
