# 前端数据获取规范

## 两种允许的模式

1. **静态 / 非交互页面**:使用 Server Component,直接 `await` SDK 调用。

```tsx
export default async function HomePage() {
  const health = await checkHealth(getClient());
  return <div>...{health}...</div>;
}
```

  参考:`apps/web/app/(main)/page.tsx`

2. **交互页面**:`"use client"` + `useEffect` + `useState` + `useCallback`,统一命名为 `loadXxx`。

```tsx
"use client";
const [data, setData] = useState<T>([]);
const [loading, setLoading] = useState(false);

const loadOrders = useCallback(async () => {
  setLoading(true);
  try {
    setData(await getOrders(getClient()));
  } finally {
    setLoading(false);
  }
}, []);

useEffect(() => { void loadOrders(); }, [loadOrders]);
```

  参考:`apps/admin/app/(main)/orders/page.tsx`

## 禁止

- ❌ 引入 SWR / React Query / @tanstack(项目不采用)。
- ❌ 在组件内裸写业务 fetch 逻辑。