# Admin 用户管理模块设计

日期：2026-08-07

## 背景

EC Main 的 web 端注册用户（角色 `buyer`）与 admin 用户（角色 `admin`）同存于 `users` 表。Admin 后台侧边栏已有「用户管理」入口（指向 `/users`），但页面与后端接口均不存在，无法查看和管理 web 端注册的用户。

## 目标

- Admin 后台新增用户管理模块：列表（分页 + 关键字搜索）、启用/禁用账号。
- 后端新增用户接口：列表、详情、启用/禁用。
- 被禁用的账号无法再登录（web 与 admin 登录均拦截）。

## 范围决策

- 用户列表范围：展示所有用户（buyer + admin），带角色标签；禁用操作仅对业务合理（admin 自己的账号不可禁用）。
- 前端交互：列表页 + 行内启用/禁用开关，不单独做详情页。
- 登录影响：禁用仅阻断新登录，已登录的 token 会话不受影响。
- `is_active` 字段迁移：启动时自动 ALTER TABLE 添加列（幂等），不引入 Alembic。

## 数据模型

`backend/app/models/user.py` 新增字段：

```python
is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
```

### 启动迁移

在应用 lifespan 中，`create_all` 之后执行幂等的列添加：

```sql
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1 NOT NULL
```

先查询 `PRAGMA table_info(users)` 判断 `is_active` 是否存在，已存在则跳过。

## 后端接口

路由挂在 `/api/v1/admin`：

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 用户列表 | GET | `/users` | `page`（默认 1）、`page_size`（默认 20，上限 100）、`keyword`（可选，邮箱/用户名模糊匹配）、`status`（可选，`active` / `inactive`） |
| 用户详情 | GET | `/users/{user_id}` | 不存在返回 404 |
| 启用/禁用 | PATCH | `/users/{user_id}/active` | body `{ "is_active": true/false }`；禁止禁用 admin 自己（当前登录用户）返回 400 |

### 文件

- `backend/app/domain/users/__init__.py`：`list_users`、`get_user`、`set_user_active`
- `backend/app/domain/users/schemas.py`：`UserListResponse`、`UserStatusUpdate`
- `backend/app/api/admin/users.py`：三个路由
- `backend/app/main.py`：注册 `admin_users_router`；lifespan 中执行 `ensure_is_active_column`

## 登录拦截

`backend/app/domain/auth/__init__.py` 的 `authenticate_user` 增加校验：

```python
if not user.is_active:
    raise HTTPException(status_code=403, detail="账号已被禁用")
```

web 与 admin 登录均复用该函数，一处生效。

## SDK（`packages/sdk/src`）

- 新增 `users.ts`：`getUsers`（`page`/`page_size`/`keyword`/`status`）、`getUser`、`setUserActive`
- `index.ts` 导出类型 `AdminUser`、`UserListResponse`

## Admin 前端

`apps/admin/app/(main)/users/page.tsx` — 列表页：
- 关键字搜索框 + 状态筛选下拉 + 分页控件
- 表格列：ID、用户名、邮箱、角色标签、状态徽章（正常/已禁用）、注册时间、操作（禁用/启用按钮）
- 角色标签区分：admin 显示「管理员」，buyer 显示「买家」
- 当前登录用户（admin 自己）禁用按钮置灰

复用现有 `createApiClient` + `@ec/sdk` 模式；侧边栏 `/users` 链接已存在无需修改。

## 测试

- `backend/tests/test_user_domain.py`：列表分页/搜索、`set_user_active`、禁止禁用 admin 自己
- `backend/tests/test_user_api.py`：列表/详情/改状态/404/禁用自己 400
- `backend/tests/test_auth.py` 扩展：禁用后登录返回 403
- `backend/tests/test_user_model.py`：`is_active` 默认值
