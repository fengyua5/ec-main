# 售后增强设计（槽位补充 / 取消订单 / 退款确认 / 售后 Case 落库）

日期：2026-08-07

## 背景

现有售后模块（`after_sale`）已支持 `query_order` / `update_order` / `refund` 三个子意图，其中退款链路为 `collect_refund_info → check_order_mcp → process_refund_mcp`。本次增强：

1. 进入售后后，若用户消息未含明确订单号，应主动询问（槽位补充），而非直接当订单号使用。
2. 新增「取消订单」子意图 `cancel_order`，先查订单状态，`in_delivery` 起（含 `delivered`）不可取消。
3. 退款时需先向用户确认，确认通过后才执行退款并创建售后 case。
4. 售后 case 落库持久化（新表 `after_sale_cases`）。

## 目标

- 统一「订单号槽位」收集：四类子流程（query_order / cancel_order / update_order / refund）共用。
- 新增 `cancel_order` 子意图及独立流程，含状态校验。
- refund 增加确认环节，确认后才退款 + 创建 case。
- 取消与退款的状态校验口径统一为 `in_delivery` 起禁。
- 售后 case 落库，支持后续查询。

## 范围决策

- 确认环节用「通用 confirm 节点 + 规则判定」，不调用 LLM。
- 订单号槽位用正则 `ORD-\S+` 匹配；未命中则主动询问。
- 售后 case 用新表落库，由 AI 节点经领域服务直接写入（与 MCP server 一致的 SessionLocal 模式）。
- 保留 `update_order` 子意图，与 `cancel_order` 并存。
- 退款/取消的状态校验由后端 domain 层（`VALID_TRANSITIONS`）与 AI 层（check_order_mcp 状态判断）双重保证，口径一致。

## 子意图定义

`SUB_INTENT_SYSTEM_PROMPT` 增补 `cancel_order`：

类别：`query_order` / `cancel_order` / `update_order` / `refund`

- `query_order`：查询订单状态或详情
- `cancel_order`：取消订单（要求订单未发货）
- `update_order`：修改订单（如修改状态）
- `refund`：申请退款或退货

## State 扩展

`skills.after_sale` 增加统一订单号槽位与确认标志：

```python
"after_sale": {
    "sub_intent": "query_order" | "cancel_order" | "update_order" | "refund" | None,
    "order_no": str,                    # 统一订单号槽位
    "confirmed": bool,                  # confirm 节点判定结果
    "query_order": {"order_no": str},
    "cancel_order": {"order_no": str},
    "update_order": {"order_no": str, "status": str},
    "refund": {"order_no": str, "reason": str, "amount": str, "confirmed": bool},
}
```

说明：`after_sale.order_no` 为统一槽位；`cancel_order` / `query_order` 直接读取该槽位；`refund` / `update_order` 也可读取，各自仍需收集补充信息。

## 节点设计

| 节点 | 职责 |
|---|---|
| `ensure_order_no` | 统一订单号槽位。从当前用户消息正则匹配 `ORD-\S+`，命中写入 `after_sale.order_no` 并继续；未命中返回「请提供订单号（格式 ORD-xxx）：」并停在 END |
| `confirm_after_sale` | 通用确认节点。展示待确认信息（订单号/金额/操作类型），用规则判定用户确认：`是/确认/好的/可以` → yes；`否/不/取消/别` → no；其他 → 重新询问 |
| `check_order_mcp` | 复用于 cancel_order 与 refund：查询订单状态；`in_delivery` / `delivered` 返回拒绝文案，其余返回通过 |
| `cancel_order_mcp` | 调 MCP `update_order_status`(→`cancelled`)；失败透传 message |
| `process_refund_mcp` | 调 MCP `process_refund`；成功后调用领域服务 `create_case` 落库 |

保留原节点：`enter_after_sale`、`collect_order_no`、`query_order_mcp`、`collect_update_order_info`、`update_order_mcp`、`collect_refund_info`、`handoff_human` 等。

> `collect_order_no`（query_order 用）改为读取统一槽位 `after_sale.order_no`，不再把消息当订单号。

### 订单号槽位补充

`ensure_order_no` 逻辑：

```python
match = re.search(r"ORD-\S+", last_msg)
if match:
    after_sale["order_no"] = match.group(0)
    return {"skills": {"after_sale": after_sale}}
return {"flow": {"response": "请提供订单号（格式 ORD-xxx）："}, "skills": {"after_sale": after_sale}}
```

### confirm 规则判定

```python
YES = {"是", "确认", "好的", "可以", "确定", "嗯", "对"}
NO = {"否", "不", "取消", "别", "算了", "不要"}
```

用户消息去掉标点后首词/整体在 YES → yes，在 NO → no，否则返回「请确认您的选择（是/否）」并停在 END。

### 状态校验口径

`VALID_TRANSITIONS` 调整：

```python
VALID_TRANSITIONS = {
    "pending_payment": {"pending_delivery", "cancelled"},
    "pending_delivery": {"in_delivery", "cancelled", "refunded"},
    "in_delivery": set(),      # 原 {"delivered"}，调整为不再允许任何流转
    "delivered": set(),
    "cancelled": set(),
    "refunded": set(),
}
```

AI 层 `check_order_mcp` 同步：`in_delivery` / `delivered` 返回拒绝文案（取消：已发货/配送中无法取消；退款：订单已发货/签收无法退款）。

## Graph 路由

```
classify_intent:
  greeting → handle_greeting
  faq → retrieve_faq
  after_sale → enter_after_sale
  human → handoff_human

enter_after_sale (子意图路由):
  query_order   → ensure_order_no → collect_order_no → query_order_mcp → END
  cancel_order  → ensure_order_no → check_order_mcp → confirm_after_sale → cancel_order_mcp → END
  update_order  → ensure_order_no → collect_update_order_info → update_order_mcp → END
  refund        → ensure_order_no → collect_refund_info → check_order_mcp
                 → confirm_after_sale → process_refund_mcp(+create_case) → END
```

其中 cancel/refund 的 `check_order_mcp` 若状态非法（in_delivery/delivered）直接返回拒绝文案并 END；合法才进入 confirm。

## 售后 Case 落库

### 模型（app/models/after_sale_case.py）

```python
class AfterSaleCase(Base):
    __tablename__ = "after_sale_cases"

    id: int (PK, autoincrement)
    order_no: str
    buyer_id: int
    case_type: str        # refund | cancel | update
    amount: str | None
    reason: str | None
    status: str           # processed
    created_at: datetime
```

### 领域服务（app/domain/after_sale/__init__.py）

- `create_case(db, *, order_no, buyer_id, case_type, amount=None, reason=None) -> AfterSaleCase`
- 支持 `list_cases_by_buyer(db, buyer_id)`（预留，供后续客服查询）。

### 写入路径

`process_refund_mcp` 退款成功后调用 `create_case`（case_type=`refund`）；`cancel_order_mcp` 取消成功后同样调用 `create_case`（case_type=`cancel`）。buyer_id 从 `check_order` 返回的订单信息中获取（已有 `check_order` 完整字段含 `buyer_id`）。update_order 暂不创建 case。

## MCP 扩展

- `check_order` 已返回完整订单字段（order_no / buyer_id / amount / status / created_at），供确认环节展示 buyer_id。
- `process_refund` / `update_order_status` 维持现状，内部经 domain 层校验状态流转。

## 测试

- `test_ai_workflow.py`：
  - `ensure_order_no`：命中订单号 / 未命中询问 / 重新输入后命中
  - `confirm_after_sale`：yes / no / 其他需重问
  - `cancel_order` 全流程：可取消 / 配送中拒绝 / 确认后取消
  - `refund` 确认流程：确认后退款 + 创建 case / 反悔不退款
  - 统一槽位在 query_order / update_order 上的复用
  - `classify_intent` 售后短路回归
- `test_after_sale_case.py`（新）：`create_case` 落库、字段完整、按 buyer 查询
- `test_order_api.py` / 现有 domain 测试：`VALID_TRANSITIONS` 调整后 `in_delivery` 不再允许流转的回归
- `test_mcp_server.py`：cancel / refund 状态非法返回失败文案回归

## 风险与注意

- `VALID_TRANSITIONS` 变更可能影响现有管理端「修改订单状态」接口与测试，需同步回归。
- `ensure_order_no` 统一槽位改变现有退款/查询对「消息即订单号」的假设，相关旧测试需更新。
- 售后 case 为新增表，需 `Base.metadata.create_all` 建表（现有测试在 fixture 中已统一建表）。
