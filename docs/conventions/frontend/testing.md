# 前端测试规范

## 框架

- Vitest + Testing Library(jsdom),配置见 `apps/web/vitest.config.ts` / `apps/admin/vitest.config.ts`。

## 要求

- 组件、hooks、Next.js API route handler 都要补测试。
- 测试文件放 `apps/<app>/__tests__/`,按被测模块镜像目录结构。

## 常用 mock 手法

- 路由:`vi.mock("next/navigation")`。
- SDK:`vi.mock("@ec/sdk")`。
- 后端请求:`vi.spyOn(globalThis, "fetch")`。
- 浏览器 API:`vi.stubGlobal`(如 Worker)。

  参考:`apps/web/__tests__/bottom-tab-bar.test.tsx`、`apps/web/__tests__/ai/use-sse-chat.test.ts`、`apps/admin/__tests__/api/auth/login.test.ts`