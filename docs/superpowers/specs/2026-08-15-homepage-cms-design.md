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

#### CMS 组件池

在 `apps/web/app/(main)/cms-components/` 目录下维护 CMS 组件池:

- `cms-banner.tsx` — 原 `HomeBanner`,组件名 `CmsBanner`
- `cms-product-grid.tsx` — 原 `HomeProductGrid`,组件名 `CmsProductGrid`
- `cms-announcement.tsx` — 原 `HomeAnnouncement`,组件名 `CmsAnnouncement`
- `cms-search-bar.tsx` — 原 `HomeSearchBar`,组件名 `CmsSearchBar`
- `index.ts` — 统一 re-export 所有 CMS 组件

组件 API 保持纯展示:接收 `items` 等数据 props,不含数据获取逻辑。

#### useCMS hook

在 `apps/web/app/(main)/hooks/use-cms.ts` 新增模块级 hook:

```typescript
function useCMS<T = unknown>(
  module: { is_static: boolean; data_source_url: string },
  initialData?: T,
): { data: T | null; loading: boolean; error: string | null }
```

行为矩阵:

| is_static | data_source_url | useCMS 行为 |
|-----------|----------------|-------------|
| `true` | `""` (空) | `{ data: null, loading: false, error: null }` — 无请求,组件直接渲染 |
| `true` | 非空 | `{ data: initialData, ... }` — 返回服务器预取数据,无额外请求 |
| `false` | 非空 | `useEffect` 中 `fetch(data_source_url)` → `{ data, loading, error }` 动态加载 |

遵循前端规范:`"use client"` + `useState` + `useEffect` + `useCallback`,命名 `loadData`。

#### 首页渲染流程

```
Server Component (page.tsx):
  getHomeModules(client) → modules[]
  对每个模块:
    is_static && data_source_url → 预取数据
    is_static && !data_source_url → 跳过
    !is_static → 跳过(客户端处理)
  → 传给 HomeModuleRenderer

HomeModuleRenderer:
  is_static → 直接渲染 CMS 组件(带数据或不带数据)
  !is_static → 渲染 <DynamicCmsModule> 客户端包装

DynamicCmsModule (client component):
  用 useCMS 从 data_source_url 获取数据
  加载中 → Loader2 spinner
  错误 → error message
  成功 → 渲染对应 CMS 组件
```

#### 目录结构

```
apps/web/app/(main)/
├── cms-components/          ← CMS 组件池
│   ├── cms-banner.tsx
│   ├── cms-product-grid.tsx
│   ├── cms-announcement.tsx
│   ├── cms-search-bar.tsx
│   └── index.ts
├── hooks/
│   └── use-cms.ts           ← 模块级 hook
├── components/
│   ├── home-module-renderer.tsx  ← 区分静态/动态渲染
│   └── dynamic-cms-module.tsx    ← 动态模块客户端包装
└── page.tsx                 ← 只预取模块列表 + 静态数据
```

### admin 管理页(`apps/admin/app/(main)/cms/`)

- `modules/page.tsx`、`banners/page.tsx`、`announcements/page.tsx`、`products/page.tsx`。
- 遵循现有模式:`loadXxx` + useCallback + 受控表单 + 独立 error/loading;复用 `components/ui/*`。
- sidebar 增加"首页配置"导航(指向 /cms/modules)。

## 测试

- 后端:`backend/tests/test_home_api.py`(web 公开)、`test_cms_api.py`(admin CRUD + 鉴权),沿用 `TestClient` + `_clean_db` 模式。
- 前端:`apps/web/__tests__/home/`:
  - `HomeModuleRenderer` 按 type 分发、静态/动态渲染路径
  - `useCMS` hook:静态无数据、静态有数据、动态加载、动态加载失败
  - CMS 组件:渲染/空数据
  - `vi.mock("@ec/sdk")` 或 `vi.spyOn(globalThis, "fetch")` 模拟请求
- admin 页面交互测试视复杂度,mock SDK 验证渲染。

## 种子数据

- `db/seed.py` 增加 `seed_cms(db)`:插入默认首页模块(banner / product_recommend / announcement)+ 若干 banner、公告、商品,幂等。
- `main.py` lifespan 调用。