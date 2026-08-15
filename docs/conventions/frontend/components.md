# 前端 UI 组件规范

## 使用各 app 自带的 shadcn 副本

- 组件放在 `apps/web/components/ui/` 或 `apps/admin/components/ui/`(项目不共享 `@ec/ui`,已废弃)。
- 写法:`@base-ui/react` 无头原语 + `cva()` 声明 variants + `cn()`(twMerge + clsx)合并类名,导出组件与 `xxxVariants`。

  参考:`apps/web/components/ui/button.tsx`

## 组织方式

- 特定页面/功能的组件、hooks、workers 按功能就近内聚在路由目录下(如 `app/(main)/ai/components/`、`app/(main)/ai/hooks/`)。
- 跨页面共享的组件放 `app/components/`(如 `bottom-tab-bar.tsx`)。

## 禁止

- ❌ 新建组件时手写 clsx 拼接大段类名(应走 cva)。
- ❌ 把不需要的组件放到全局 `components/ui/`(就近内聚优先)。