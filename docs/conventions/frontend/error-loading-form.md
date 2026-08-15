# 前端错误 / loading / 表单规范

## 错误处理

- 页面本地 `useState<string | null>` 存错误,`catch` 里 `setError(...)`,渲染 `<p className="text-sm text-destructive">`。
- 复杂场景可用 `{ type: "success" | "error", message }` 对象。

## loading

- 独立 `useState` boolean,`loadXxx` 开头 `setLoading(true)`,`.finally` 里 `setLoading(false)`。
- 渲染用 `Loader2 className="animate-spin"`。
- 行级操作(删除等)用独立 state(如 `deletingId`),不与整页 loading 混用。

## 表单

- 受控 `useState` + `onSubmit` `preventDefault`,不引入表单库。
- 基础校验交给原生 `required`,业务校验手写。

  参考:`apps/web/app/(auth)/login/page.tsx`、`apps/web/app/(main)/account/page.tsx`、`apps/admin/app/(main)/faq/components/upload-form.tsx`