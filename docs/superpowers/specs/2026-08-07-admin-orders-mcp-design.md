# Admin 订单管理模块 + 订单接口 + MCP 设计

日期：2026-08-07

## 背景

EC Main 电商 MVP 平台已有 `Order` 模型（`order_no`/`buyer_id`/`amount`/`status`/`created_at`）和种子数据，但 Admin 后台的「订单管理」入口（侧边栏指向 `/orders`）尚无页面，后端也没有订单查询/改状态接口。同时已有一个 MCP server（含 `check_order`、`process_refund` 两个工具），需要扩展出通用的「修改订单状态」能力，让 agent 能操作订单状态。

## 目标

- Admin 后台新增订单管理模块：查看订单列表、查看订单详情、查看并修改订单状态。
- 后端新增订单接口：列表（分页+筛选）、详情、修改状态（状态机校验）。
- MCP 扩展 `update_order_status` 工具：agent 可按状态机修改订单状态。

## 范围决策

- 保持现有精简 `Order` 模型，不扩展字段。
- 采用完整状态机 + 流转校验，非法流转拒绝。
- 前端采用「列表页 + 独立详情页（`/orders/[order_no]`）」形态。
- 列表接口支持分页 + 状态筛选 + 订单号关键字搜索。

## 订单状态机

六个状态：

| 状态 | 含义 |
|---|---|
| `pending_payment` | 待付款 |
| `pending_delivery` | 待发货 |
| `in_delivery` | 配送中 |
| `delivered` | 已送达 |
| `cancelled` | 已取消 |
| `refunded` | 已退款 |

合法流转（其余跳转一律拒绝）：

- `pending_payment → pending_delivery / cancelled`
- `pending_delivery → in_delivery / cancelled / refunded`
- `in_delivery → delivered`
- `delivered`、`cancelled`、`refunded` 为终态，不可再流转

## 后端接口

路由挂在 `/api/v1/admin`：

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 订单列表 | GET | `/orders` | `page`（默认 1）、`page_size`（默认 20，上限 100）、`status`（可选，按状态筛选）、`keyword`（可选，订单号模糊匹配） |
| 订单详情 | GET | `/orders/{order_no}` | 不存在返回 404 |
| 修改状态 | PATCH | `/orders/{order_no}/status` | body `{ "status": "..." }`；非法状态值或非法流转返回 400；不存在返回 404 |

### 文件

- `backend/app/domain/orders/__init__.py`：状态机定义（`ORDER_STATUSES`、`VALID_TRANSITIONS`、`get_next_statuses`）、服务函数（`list_orders`、`get_order`、`update_order_status`）
- `backend/app/domain/orders/schemas.py`：`OrderResponse`、`OrderListResponse`、`OrderStatusUpdate`、`OrderStatusUpdateResponse`
- `backend/app/api/admin/orders.py`：三个路由，复用 `get_db` 依赖
- `backend/app/main.py`：注册 `admin_orders_router`

## MCP 扩展

- `backend/app/mcp/server.py`：
  - 新增工具 `update_order_status`，参数 `order_id`、`status`，走 domain 状态机校验
  - `process_refund` 重构为复用 domain 状态机（`pending_delivery → refunded`）
- `backend/app/mcp/client.py`：新增 `update_order_status` 方法

## SDK（`packages/sdk/src`）

- 新增 `orders.ts`：`getOrders`（带 `page`/`page_size`/`status`/`keyword` 参数）、`getOrder`、`updateOrderStatus`
- `index.ts` 导出类型 `Order`、`OrderListResponse`

## Admin 前端

- `apps/admin/app/(main)/orders/page.tsx`：列表页
  - 状态筛选下拉 + 订单号关键字搜索 + 分页控件
  - 表格：订单号、买家 ID、金额、状态徽章、创建时间、操作（查看详情）
- `apps/admin/app/(main)/orders/[order_no]/page.tsx`：详情页
  - 订单全部字段展示
  - 状态徽章 + 修改状态下拉（仅展示合法目标状态）

复用现有 `createApiClient` + `@ec/sdk` 模式；侧边栏 `/orders` 链接已存在无需修改。

## 测试

- `backend/tests/test_order_domain.py`：状态机合法/非法流转、`get_next_statuses`、终态不可流转
- `backend/tests/test_order_api.py`：列表分页/筛选/关键字、详情、改状态成功/非法流转 400/订单不存在 404
- `backend/tests/test_mcp_server.py`：扩展 `update_order_status` 用例
- SDK/前端改动较小，跟随现有 vitest 模式（如需要）
