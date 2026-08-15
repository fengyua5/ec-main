# 前端 API 调用规范

## 统一走 @ec/sdk

- 所有 API 调用一律通过 `packages/sdk` 的 `createApiClient` 创建 client,并调用 sdk 提供的一等函数。
- 函数签名以 `client: ApiClient` 为第一个参数。

```ts
// apps/web 或 apps/admin 中创建单例
const client = createApiClient({ baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000" });

// sdk 用法
const orders = await getOrders(client, { page, page_size });
```

  参考:`apps/web/app/(auth)/login/page.tsx`、`packages/sdk/src/client.ts`、`packages/sdk/src/orders.ts`

## 禁止

- ❌ 在页面/组件里裸 `fetch(BACKEND_URL...)` 直连后端。
- ❌ 在 app 业务代码中重复定义请求/响应类型(应加在 sdk 对应模块)。

## admin BFF 代理

- 需要隐藏后端 URL 或透传凭证时,在 `apps/admin/app/api/<域>/route.ts` 用 Next.js Route Handler 作为 BFF:转发浏览器的 `Cookie` 头、透传后端 status。

  参考:`apps/admin/app/api/auth/me/route.ts`
