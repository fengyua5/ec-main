# 自建 CMS 首页改造设计

日期:2026-08-15
状态:待实施

## 目标

将 `apps/web/app/(main)/page.tsx`(静态底座页)改造为 CMS 配置驱动的首页:admin 端可配置首页模块(动态模块 + 排序 + 启停),每类模块的数据源指向内部接口 URL,web 首页按配置渲染。

## 范围

自建完整 CMS,覆盖三端:
- backend:新增 4 张表 + 公开读取接口 + admin CRUD 接口
- admin:首页配置管理页(模块/商品/banner/公告)
- web:首页按配置渲染

## 数据模型(4 张新表)

| 表 | 字段 | 说明 |
|---|---|---|
| `products` | id, title, image_url, price(分, int), status(active/inactive), sort_order, created_at | 推荐位数据源 |
| `home_modules` | id, module_type(banner/product_recommend/announcement), title, data_source_url, sort_order, is_enabled, created_at, updated_at | 动态模块配置 |
| `banner_items` | id, image_url, link_url, sort_order, is_enabled, created_at | banner 内容 |
| `announcements` | id, content, is_enabled, created_at | 公告内容 |

时间统一 `DateTime(timezone=True)`、`created_at` 用 `server_default=func.now()`。

## API

### web 公开(无需登录)

- `GET /api/v1/web/home/modules` → `{ modules: [{id, module_type, title, data_source_url, sort_order}] }`(仅 is_enabled,按 sort_order)
- `GET /api/v1/web/home/banner` → `{ items: [{id, image_url, link_url}] }`
- `GET /api/v1/web/home/announcement` → `{ items: [{id, content}] }`
- `GET /api/v1/web/products?status=active` → `{ items: [{id, title, image_url, price}], total }`

### admin CRUD(需登录,`get_current_user`)

- `/api/v1/admin/cms/modules`:list / create / update / delete / move(上下移交换 sort_order)
- `/api/v1/admin/cms/banners`:list / create / update / delete
- `/api/v1/admin/cms/announcements`:list / create / update / delete
- `/api/v1/admin/cms/products`:list / create / update / delete

分层遵循后端规范:路由薄,业务在 `domain/cms/<域>/`,schema 放 `domain/cms/<域>/schemas.py`,`model_config={"from_attributes": True}`。

## 前端

### SDK(`packages/sdk/src/`)

- 新增 `home.ts`(web 公开读取)+ `cms.ts`(admin CRUD),`index.ts` re-export。
- 类型:HomeModule、BannerItem、Announcement、Product、CmsModuleInput、ProductInput 等。

### web 首页(`apps/web/app/(main)/page.tsx`)

- async Server Component:并行 `Promise.all` 拉 `getHomeModules` + 各模块数据源;按 `module_type` 渲染组件。
- 新增组件就近内聚于 `app/(main)/components/`:`HomeBanner`、`HomeProductGrid`、`HomeAnnouncement`、`HomeModuleRenderer`。
- 接口失败/无模块时优雅降级,保留现有 try/catch 风格。

### admin 管理页(`apps/admin/app/(main)/cms/`)

- `modules/page.tsx`、`banners/page.tsx`、`announcements/page.tsx`、`products/page.tsx`。
- 遵循现有模式:`loadXxx` + useCallback + 受控表单 + 独立 error/loading;复用 `components/ui/*`。
- sidebar 增加"首页配置"导航(指向 /cms/modules)。

## 测试

- 后端:`backend/tests/test_home_api.py`(web 公开)、`test_cms_api.py`(admin CRUD + 鉴权),沿用 `TestClient` + `_clean_db` 模式。
- 前端:`apps/web/__tests__/home/`(HomeModuleRenderer 按 type 分发、组件渲染,`vi.mock("@ec/sdk")`)。
- admin 页面交互测试视复杂度,mock SDK 验证渲染。

## 种子数据

- `db/seed.py` 增加 `seed_cms(db)`:插入默认首页模块(banner / product_recommend / announcement)+ 若干 banner、公告、商品,幂等。
- `main.py` lifespan 调用。