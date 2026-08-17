# 前端目录结构规范

## 核心规则

### 组件就近内聚

特定功能的组件、hooks、workers 放在路由目录下，不放全局：

```
apps/web/app/(main)/ai/
├── page.tsx
├── components/      # 页面级组件，只被本页用
├── hooks/           # 页面级 hooks
└── workers/         # Web Workers
```

### 全局共享组件

只有真正跨页面复用的才放 `app/components/`：

```
apps/web/app/components/
└── bottom-tab-bar.tsx    # 全局底部导航
```

### UI 组件

shadcn 组件统一放 `components/ui/`，各 app 自带副本：

```
apps/web/components/ui/button.tsx
```

---

## 页面分组约定

| 分组 | 用途 |
|------|------|
| `(auth)` | 登录、注册等认证页面 |
| `(main)` | 主应用页面（需要登录） |

---

## 禁止事项

- ❌ 在 `app/(main)/ai/` 里创建 `app/components/ai-chat.tsx`（应内聚在路由目录）
- ❌ 在 `app/components/` 放只被一个页面使用的组件
- ❌ 新建目录时不使用 `(group)/feature/` 命名

> 完整目录树参考：`apps/web/app/` 和 `apps/admin/app/`
