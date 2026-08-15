# 首页 CMS 组件池 + useCMS Hook 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将首页 CMS 组件抽取到 `cms-components/` 组件池，新增 `useCMS` hook 处理动态模块客户端数据加载。

**Architecture:** Server Component 只获取模块列表 + 静态数据，动态模块由客户端 `DynamicCmsModule` 包装组件通过 `useCMS` hook 按需 fetch。

**Tech Stack:** Next.js App Router, TypeScript, @ec/sdk, Vitest + Testing Library

---

### Task 1: 创建 CMS 组件池

**文件变更:**
- Create: `apps/web/app/(main)/cms-components/cms-banner.tsx`
- Create: `apps/web/app/(main)/cms-components/cms-product-grid.tsx`
- Create: `apps/web/app/(main)/cms-components/cms-announcement.tsx`
- Create: `apps/web/app/(main)/cms-components/cms-search-bar.tsx`
- Create: `apps/web/app/(main)/cms-components/index.ts`
- Delete: `apps/web/app/(main)/components/home-banner.tsx`
- Delete: `apps/web/app/(main)/components/home-product-grid.tsx`
- Delete: `apps/web/app/(main)/components/home-announcement.tsx`
- Delete: `apps/web/app/(main)/components/home-search-bar.tsx`

- [ ] **Step 1: 创建 `cms-banner.tsx`**

```tsx
import type { BannerItem } from "@ec/sdk";

type Props = { items: BannerItem[] };

export function CmsBanner({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="overflow-hidden rounded-2xl">
      {items.map((item, index) => {
        const inner = (
          <img
            src={item.image_url}
            alt={`banner-${index}`}
            className="h-48 w-full object-cover"
          />
        );
        return item.link_url ? (
          <a key={item.id} href={item.link_url}>
            {inner}
          </a>
        ) : (
          <div key={item.id}>{inner}</div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: 创建 `cms-product-grid.tsx`**

```tsx
import type { Product } from "@ec/sdk";

type Props = { items: Product[] };

export function formatPrice(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`;
}

export function CmsProductGrid({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((product) => (
        <div
          key={product.id}
          className="overflow-hidden rounded-xl border bg-surface-100-bg"
        >
          <img
            src={product.image_url}
            alt={product.title}
            className="h-32 w-full object-cover"
          />
          <div className="p-3">
            <p className="truncate text-sm text-surface-100-fg-default">{product.title}</p>
            <p className="mt-1 text-base font-medium text-text-accent">{formatPrice(product.price)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: 创建 `cms-announcement.tsx`**

```tsx
import type { Announcement } from "@ec/sdk";

type Props = { items: Announcement[] };

export function CmsAnnouncement({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <p
          key={item.id}
          className="rounded-lg bg-surface-100-bg px-4 py-2 text-sm text-surface-100-fg-minor"
        >
          {item.content}
        </p>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: 创建 `cms-search-bar.tsx`**

```tsx
export function CmsSearchBar() {
  return (
    <div className="relative">
      <input
        type="text"
        placeholder="搜索商品…"
        className="w-full rounded-xl border bg-surface-100-bg px-4 py-3 pl-10 text-sm text-surface-100-fg-default outline-none placeholder:text-surface-100-fg-minor"
      />
      <svg
        className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-surface-100-fg-minor"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
        />
      </svg>
    </div>
  );
}
```

- [ ] **Step 5: 创建 `index.ts`**

```ts
export { CmsBanner } from "./cms-banner";
export { CmsProductGrid, formatPrice } from "./cms-product-grid";
export { CmsAnnouncement } from "./cms-announcement";
export { CmsSearchBar } from "./cms-search-bar";
```

- [ ] **Step 6: 删除旧文件**

```bash
rm apps/web/app/\(main\)/components/home-banner.tsx
rm apps/web/app/\(main\)/components/home-product-grid.tsx
rm apps/web/app/\(main\)/components/home-announcement.tsx
rm apps/web/app/\(main\)/components/home-search-bar.tsx
```

---

### Task 2: 编写 `useCMS` hook

**文件:**
- Create: `apps/web/app/(main)/hooks/use-cms.ts`

- [ ] **Step 1: 创建 `use-cms.ts`**

```ts
"use client";

import { useState, useEffect, useCallback } from "react";
import { createApiClient } from "@ec/sdk/client";

const client = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
});

export function useCMS<T = unknown>(
  module: { is_static: boolean; data_source_url: string },
  initialData?: T,
) {
  const [data, setData] = useState<T | null>(initialData ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (module.is_static || !module.data_source_url) return;
    setLoading(true);
    setError(null);
    try {
      const result = await client.request<T>(module.data_source_url);
      setData(result);
    } catch {
      setError("数据加载失败");
    } finally {
      setLoading(false);
    }
  }, [module.is_static, module.data_source_url]);

  useEffect(() => {
    if (!module.is_static && module.data_source_url) {
      void loadData();
    }
  }, [loadData, module.is_static, module.data_source_url]);

  return { data, loading, error };
}
```

---

### Task 3: 创建 `DynamicCmsModule` 客户端包装组件

**文件:**
- Create: `apps/web/app/(main)/components/dynamic-cms-module.tsx`

- [ ] **Step 1: 创建 `dynamic-cms-module.tsx`**

```tsx
"use client";

import type { HomeModule } from "@ec/sdk";
import { Loader2 } from "lucide-react";
import { useCMS } from "../hooks/use-cms";
import { CmsBanner } from "../cms-components/cms-banner";
import { CmsProductGrid } from "../cms-components/cms-product-grid";
import { CmsAnnouncement } from "../cms-components/cms-announcement";
import { CmsSearchBar } from "../cms-components/cms-search-bar";

type Props = { module: HomeModule };

export function DynamicCmsModule({ module }: Props) {
  const { data, loading, error } = useCMS(module);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8" data-testid="dynamic-cms-loading">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  switch (module.module_type) {
    case "banner":
      return <CmsBanner items={(data as { items: import("@ec/sdk").BannerItem[] } | null)?.items ?? []} />;
    case "product_recommend":
      return <CmsProductGrid items={(data as { items: import("@ec/sdk").Product[] } | null)?.items ?? []} />;
    case "announcement":
      return <CmsAnnouncement items={(data as { items: import("@ec/sdk").Announcement[] } | null)?.items ?? []} />;
    case "search_bar":
      return <CmsSearchBar />;
    default:
      return null;
  }
}
```

---

### Task 4: 更新 `HomeModuleRenderer` 支持静态/动态分流

**文件:**
- Modify: `apps/web/app/(main)/components/home-module-renderer.tsx`

- [ ] **Step 1: 重写 `home-module-renderer.tsx`**

```tsx
import type { HomeModule, BannerItem, Product, Announcement } from "@ec/sdk";
import { CmsBanner } from "../cms-components/cms-banner";
import { CmsProductGrid } from "../cms-components/cms-product-grid";
import { CmsAnnouncement } from "../cms-components/cms-announcement";
import { CmsSearchBar } from "../cms-components/cms-search-bar";
import { DynamicCmsModule } from "./dynamic-cms-module";

export type ModulePayloads = {
  banner: BannerItem[];
  product_recommend: Product[];
  announcement: Announcement[];
};

type Props = {
  modules: HomeModule[];
  staticData: Partial<ModulePayloads>;
};

export function HomeModuleRenderer({ modules, staticData }: Props) {
  return (
    <div className="space-y-8">
      {modules.map((module) => {
        if (module.is_static) {
          switch (module.module_type) {
            case "banner":
              return <CmsBanner key={module.id} items={staticData.banner ?? []} />;
            case "product_recommend":
              return <CmsProductGrid key={module.id} items={staticData.product_recommend ?? []} />;
            case "announcement":
              return <CmsAnnouncement key={module.id} items={staticData.announcement ?? []} />;
            case "search_bar":
              return <CmsSearchBar key={module.id} />;
            default:
              return null;
          }
        }
        return <DynamicCmsModule key={module.id} module={module} />;
      })}
    </div>
  );
}
```

---

### Task 5: 更新首页 `page.tsx` — 只预取模块列表 + 静态数据

**文件:**
- Modify: `apps/web/app/(main)/page.tsx`

- [ ] **Step 1: 重写 `page.tsx`**

```tsx
import { createApiClient, getHomeModules, getHomeBanner, getHomeAnnouncements, getPublicProducts, type HomeModule } from "@ec/sdk";
import { HomeModuleRenderer, type ModulePayloads } from "./components/home-module-renderer";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function loadHomeData(): Promise<{ modules: HomeModule[]; staticData: Partial<ModulePayloads> } | null> {
  try {
    const client = createApiClient({ baseUrl: apiBaseUrl });
    const { modules } = await getHomeModules(client);

    const staticData: Partial<ModulePayloads> = {};
    const types = new Set(modules.filter((m) => m.is_static && m.data_source_url).map((m) => m.module_type));

    const promises: Promise<void>[] = [];
    if (types.has("banner")) {
      promises.push(
        getHomeBanner(client).then((res) => { staticData.banner = res.items; }),
      );
    }
    if (types.has("product_recommend")) {
      promises.push(
        getPublicProducts(client, { status: "active" }).then((res) => { staticData.product_recommend = res.items; }),
      );
    }
    if (types.has("announcement")) {
      promises.push(
        getHomeAnnouncements(client).then((res) => { staticData.announcement = res.items; }),
      );
    }

    await Promise.all(promises);
    return { modules, staticData };
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const result = await loadHomeData();

  return (
    <div className="min-h-screen bg-surface-200-bg text-surface-100-fg-default">
      <main className="mx-auto flex max-w-5xl flex-col gap-8">
        {result ? (
          <HomeModuleRenderer modules={result.modules} staticData={result.staticData} />
        ) : (
          <p className="enki-body-base text-surface-100-fg-minor">
            首页模块加载失败，请先到 Admin 后台配置首页内容。
          </p>
        )}
      </main>
    </div>
  );
}
```

---

### Task 6: 更新测试

**文件:**
- Modify: `apps/web/__tests__/home/home-module-renderer.test.tsx`
- Modify: `apps/web/__tests__/home/home-product-grid.test.tsx`
- Create: `apps/web/__tests__/home/use-cms.test.ts`
- Create: `apps/web/__tests__/home/cms-banner.test.tsx`
- Create: `apps/web/__tests__/home/cms-announcement.test.tsx`
- Create: `apps/web/__tests__/home/cms-search-bar.test.tsx`

- [ ] **Step 1: 更新 `home-module-renderer.test.tsx`**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { HomeModuleRenderer, type ModulePayloads } from "@/app/(main)/components/home-module-renderer";
import type { HomeModule } from "@ec/sdk";

afterEach(cleanup);

const staticData: Partial<ModulePayloads> = {
  banner: [{ id: 1, image_url: "https://example.com/banner.jpg", description: "", link_url: "/p" }],
  product_recommend: [{ id: 1, title: "商品1", image_url: "", price: 9900 }],
  announcement: [{ id: 1, content: "公告1" }],
};

describe("HomeModuleRenderer", () => {
  it("renders static banner module", () => {
    const modules: HomeModule[] = [
      { id: 1, module_type: "banner", title: "轮播", description: "", data_source_url: "/api/v1/web/home/banner", is_static: true, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={staticData} />);
    expect(screen.getByAltText("banner-0")).toBeInTheDocument();
  });

  it("renders static product grid module", () => {
    const modules: HomeModule[] = [
      { id: 2, module_type: "product_recommend", title: "商品推荐", description: "", data_source_url: "/api/v1/web/home/products", is_static: true, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={staticData} />);
    expect(screen.getByText("商品1")).toBeInTheDocument();
  });

  it("renders static announcement module", () => {
    const modules: HomeModule[] = [
      { id: 3, module_type: "announcement", title: "公告", description: "", data_source_url: "/api/v1/web/home/announcement", is_static: true, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={staticData} />);
    expect(screen.getByText("公告1")).toBeInTheDocument();
  });

  it("renders search bar module (static, no data_source_url)", () => {
    const modules: HomeModule[] = [
      { id: 5, module_type: "search_bar", title: "搜索", description: "", data_source_url: "", is_static: true, sort_order: 0 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={{}} />);
    expect(screen.getByPlaceholderText("搜索商品…")).toBeInTheDocument();
  });

  it("renders dynamic module wrapper for non-static module", () => {
    const modules: HomeModule[] = [
      { id: 6, module_type: "banner", title: "动态轮播", description: "", data_source_url: "/api/v1/web/home/banner", is_static: false, sort_order: 1 },
    ];
    render(<HomeModuleRenderer modules={modules} staticData={{}} />);
    // DynamicCmsModule shows loading spinner initially
    expect(screen.getByTestId("dynamic-cms-loading")).toBeInTheDocument();
  });

  it("renders nothing for unknown module type", () => {
    const unknownModule = {
      id: 4,
      module_type: "unknown",
      title: "未知模块",
      description: "",
      data_source_url: "",
      is_static: false,
      sort_order: 4,
    } as unknown as HomeModule;
    const { container } = render(<HomeModuleRenderer modules={[unknownModule]} staticData={{}} />);
    expect(container.querySelectorAll("*").length).toBe(1);
  });
});
```

- [ ] **Step 2: 更新 `home-product-grid.test.tsx` — 改引用路径**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsProductGrid, formatPrice } from "@/app/(main)/cms-components/cms-product-grid";

afterEach(cleanup);

describe("formatPrice", () => {
  it("formats cents into yuan with two decimals", () => {
    expect(formatPrice(9900)).toBe("¥99.00");
    expect(formatPrice(12900)).toBe("¥129.00");
  });
});

describe("CmsProductGrid", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<CmsProductGrid items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders product titles and prices", () => {
    render(
      <CmsProductGrid
        items={[
          { id: 1, title: "商品1", image_url: "", price: 9900 },
          { id: 2, title: "商品2", image_url: "", price: 12900 },
        ]}
      />,
    );
    expect(screen.getByText("商品1")).toBeInTheDocument();
    expect(screen.getByText("¥99.00")).toBeInTheDocument();
    expect(screen.getByText("商品2")).toBeInTheDocument();
    expect(screen.getByText("¥129.00")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: 创建 `cms-banner.test.tsx`**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsBanner } from "@/app/(main)/cms-components/cms-banner";

afterEach(cleanup);

describe("CmsBanner", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<CmsBanner items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders banner images", () => {
    render(
      <CmsBanner
        items={[
          { id: 1, image_url: "https://example.com/b1.jpg", description: "", link_url: "" },
          { id: 2, image_url: "https://example.com/b2.jpg", description: "", link_url: "/p/2" },
        ]}
      />,
    );
    expect(screen.getByAltText("banner-0")).toBeInTheDocument();
    expect(screen.getByAltText("banner-1")).toBeInTheDocument();
  });

  it("renders link when link_url is present", () => {
    render(
      <CmsBanner
        items={[{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "/target" }]}
      />,
    );
    const link = screen.getByAltText("banner-0").closest("a");
    expect(link).toHaveAttribute("href", "/target");
  });
});
```

- [ ] **Step 4: 创建 `cms-announcement.test.tsx`**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsAnnouncement } from "@/app/(main)/cms-components/cms-announcement";

afterEach(cleanup);

describe("CmsAnnouncement", () => {
  it("renders nothing when empty", () => {
    const { container } = render(<CmsAnnouncement items={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders announcement content", () => {
    render(
      <CmsAnnouncement
        items={[
          { id: 1, content: "公告1" },
          { id: 2, content: "公告2" },
        ]}
      />,
    );
    expect(screen.getByText("公告1")).toBeInTheDocument();
    expect(screen.getByText("公告2")).toBeInTheDocument();
  });
});
```

- [ ] **Step 5: 创建 `cms-search-bar.test.tsx`**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect } from "vitest";
import { CmsSearchBar } from "@/app/(main)/cms-components/cms-search-bar";

afterEach(cleanup);

describe("CmsSearchBar", () => {
  it("renders search input", () => {
    render(<CmsSearchBar />);
    expect(screen.getByPlaceholderText("搜索商品…")).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: 创建 `use-cms.test.ts`**

```ts
import { renderHook, waitFor, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { useCMS } from "@/app/(main)/hooks/use-cms";

afterEach(cleanup);

const staticModule = { is_static: true, data_source_url: "" };
const staticModuleWithUrl = { is_static: true, data_source_url: "/api/v1/web/home/banner" };
const dynamicModule = { is_static: false, data_source_url: "/api/v1/web/home/banner" };

describe("useCMS", () => {
  it("returns null data immediately for static module without data_source_url", () => {
    const { result } = renderHook(() => useCMS(staticModule));
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("returns initialData for static module with data_source_url", () => {
    const initialData = { items: [{ id: 1, image_url: "", description: "", link_url: "" }] };
    const { result } = renderHook(() => useCMS(staticModuleWithUrl, initialData));
    expect(result.current.data).toEqual(initialData);
    expect(result.current.loading).toBe(false);
  });

  it("fetches data for dynamic module", async () => {
    const mockData = { items: [{ id: 1, image_url: "", description: "", link_url: "" }] };
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response);

    const { result } = renderHook(() => useCMS(dynamicModule));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    fetchSpy.mockRestore();
  });

  it("sets error on fetch failure for dynamic module", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useCMS(dynamicModule));

    await waitFor(() => {
      expect(result.current.error).toBe("数据加载失败");
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    fetchSpy.mockRestore();
  });
});
```

- [ ] **Step 7: 创建 `dynamic-cms-module.test.tsx`**

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { DynamicCmsModule } from "@/app/(main)/components/dynamic-cms-module";
import type { HomeModule } from "@ec/sdk";

afterEach(cleanup);

const dynamicBanner: HomeModule = {
  id: 1, module_type: "banner", title: "动态轮播", description: "",
  data_source_url: "/api/v1/web/home/banner", is_static: false, sort_order: 1,
};

describe("DynamicCmsModule", () => {
  it("shows loading spinner initially", () => {
    render(<DynamicCmsModule module={dynamicBanner} />);
    expect(screen.getByTestId("dynamic-cms-loading")).toBeInTheDocument();
  });

  it("renders banner after data loads", async () => {
    const mockData = { items: [{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "" }] };
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response);

    render(<DynamicCmsModule module={dynamicBanner} />);

    await screen.findByAltText("banner-0");
    expect(screen.getByAltText("banner-0")).toBeInTheDocument();

    vi.restoreAllMocks();
  });

  it("shows error on fetch failure", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("fail"));

    render(<DynamicCmsModule module={dynamicBanner} />);

    await screen.findByText("数据加载失败");
    expect(screen.getByText("数据加载失败")).toBeInTheDocument();

    vi.restoreAllMocks();
  });
});
```

---

### Task 6: 验证

- [ ] **Step 1: 运行测试**

Run: `cd apps/web && npx vitest run --reporter verbose`
Expected: All tests pass