# Keen Slider 组件封装与 Banner 替换 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 封装 Keen Slider 组件到 `@ec/ui`，并替换 web 首页 banner 使用该组件

**Architecture:** 在 `packages/ui` 中创建通用 `Slider` 组件（wrapper around `useKeenSlider`），通过泛型 `T` + `renderSlide` 解耦业务数据。`CmsBanner` 保留在 web 中，改用 `Slider` 组件渲染。同时将 `@ec/ui` 接入 web 和 admin 两个 app。

**Tech Stack:** React 19, Next.js 16, Keen Slider, pnpm workspace, Tailwind CSS 4

---

### Task 1: 基础设施 — 添加依赖和配置

**Files:**
- Modify: `packages/ui/package.json`
- Modify: `apps/web/package.json`
- Modify: `apps/admin/package.json`
- Modify: `apps/web/next.config.ts`
- Modify: `apps/admin/next.config.ts`

- [ ] **Step 1: 在 `packages/ui/package.json` 中添加 `keen-slider` 依赖**

```json
{
  "dependencies": {
    "clsx": "^2.1.1",
    "keen-slider": "^6.8.6",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  }
}
```

- [ ] **Step 2: 在 `apps/web/package.json` 中添加 `@ec/ui` 依赖**

在 `dependencies` 中添加一行：
```json
"@ec/ui": "workspace:*",
```

- [ ] **Step 3: 在 `apps/admin/package.json` 中添加 `@ec/ui` 依赖**

在 `dependencies` 中添加一行：
```json
"@ec/ui": "workspace:*",
```

- [ ] **Step 4: 在 `apps/web/next.config.ts` 的 `transpilePackages` 中添加 `@ec/ui`**

```ts
const nextConfig: NextConfig = {
  transpilePackages: ["@ec/sdk", "@ec/ui"]
};
```

- [ ] **Step 5: 在 `apps/admin/next.config.ts` 的 `transpilePackages` 中添加 `@ec/ui`**

```ts
const nextConfig: NextConfig = {
  transpilePackages: ["@ec/sdk", "@ec/ui"],
  // ...existing rewrites
};
```

- [ ] **Step 6: 安装依赖**

```bash
pnpm install
```

---

### Task 2: 创建 Slider 组件

**Files:**
- Create: `packages/ui/src/slider.tsx`
- Modify: `packages/ui/src/index.ts`

- [ ] **Step 1: 创建 `packages/ui/src/slider.tsx`**

```tsx
"use client";

import { useKeenSlider } from "keen-slider/react";
import "keen-slider/keen-slider.min.css";
import type { KeenSliderOptions } from "keen-slider";
import { useState, useCallback, useEffect, useRef } from "react";
import { clsx } from "clsx";

export type SliderProps<T> = {
  items: T[];
  renderSlide: (item: T, index: number) => React.ReactNode;
  options?: KeenSliderOptions;
  autoPlay?: boolean | { interval: number };
  showDots?: boolean;
  showArrows?: boolean;
  className?: string;
  slideClassName?: string;
};

export function Slider<T>({
  items,
  renderSlide,
  options = {},
  autoPlay,
  showDots = false,
  showArrows = false,
  className,
  slideClassName,
}: SliderProps<T>) {
  const interval = typeof autoPlay === "object" ? autoPlay.interval : 4000;
  const [current, setCurrent] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const [sliderRef, instanceRef] = useKeenSlider<HTMLDivElement>({
    ...options,
    slideChanged(slider) {
      setCurrent(slider.track.details.rel);
      options.slideChanged?.(slider);
    },
  });

  const stopAutoPlay = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = undefined;
    }
  }, []);

  const startAutoPlay = useCallback(() => {
    stopAutoPlay();
    if (items.length <= 1) return;
    timerRef.current = setInterval(() => {
      instanceRef.current?.next();
    }, interval);
  }, [items.length, interval, instanceRef, stopAutoPlay]);

  useEffect(() => {
    if (!autoPlay) return;
    startAutoPlay();
    return stopAutoPlay;
  }, [autoPlay, startAutoPlay, stopAutoPlay]);

  if (items.length === 0) return null;

  return (
    <div className={clsx("relative", className)}>
      <div ref={sliderRef} className="keen-slider">
        {items.map((item, index) => (
          <div key={index} className={clsx("keen-slider__slide", slideClassName)}>
            {renderSlide(item, index)}
          </div>
        ))}
      </div>

      {showArrows && items.length > 1 && (
        <>
          <button
            onClick={() => instanceRef.current?.prev()}
            className="absolute left-2 top-1/2 z-10 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 text-zinc-800 shadow hover:bg-white"
            aria-label="previous slide"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <button
            onClick={() => instanceRef.current?.next()}
            className="absolute right-2 top-1/2 z-10 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-white/80 text-zinc-800 shadow hover:bg-white"
            aria-label="next slide"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </>
      )}

      {showDots && items.length > 1 && (
        <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1.5">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => instanceRef.current?.moveToIdx(index)}
              className={clsx(
                "size-2 rounded-full transition-colors",
                index === current ? "bg-white" : "bg-white/50",
              )}
              aria-label={`slide-${index}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 更新 `packages/ui/src/index.ts` 导出 Slider**

```ts
export { Button } from "./button";
export type { ButtonProps } from "./button";
export { Slider } from "./slider";
export type { SliderProps } from "./slider";
```

---

### Task 3: 更新 CmsBanner 使用 Slider 组件

**Files:**
- Modify: `apps/web/app/(main)/cms-components/cms-banner.tsx`

- [ ] **Step 1: 重写 `cms-banner.tsx` 使用 Slider 组件**

```tsx
"use client";

import type { BannerItem } from "@ec/sdk";
import { Slider } from "@ec/ui";

type Props = { items: BannerItem[] };

export function CmsBanner({ items }: Props) {
  return (
    <Slider
      items={items}
      options={{ loop: true }}
      autoPlay
      showDots
      className="mx-3 mt-3 overflow-hidden rounded-2xl"
      renderSlide={(item) => {
        const img = (
          <img
            src={item.image_url}
            alt={item.description || "banner"}
            className="h-48 w-full object-cover"
          />
        );
        return item.link_url ? (
          <a href={item.link_url}>{img}</a>
        ) : (
          img
        );
      }}
    />
  );
}
```

---

### Task 4: 更新测试

**Files:**
- Modify: `apps/web/__tests__/home/cms-banner.test.tsx`

- [ ] **Step 1: 重写测试文件，适配新的 Slider 组件**

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
    expect(screen.getByAltText("banner")).toBeInTheDocument();
    expect(screen.getAllByAltText("banner")).toHaveLength(2);
  });

  it("renders link when link_url is present", () => {
    render(
      <CmsBanner
        items={[{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "/target" }]}
      />,
    );
    const link = screen.getByAltText("banner").closest("a");
    expect(link).toHaveAttribute("href", "/target");
  });

  it("renders dot indicators for multiple items", () => {
    render(
      <CmsBanner
        items={[
          { id: 1, image_url: "https://example.com/b1.jpg", description: "", link_url: "" },
          { id: 2, image_url: "https://example.com/b2.jpg", description: "", link_url: "" },
        ]}
      />,
    );
    const dots = screen.getAllByRole("button");
    expect(dots.length).toBeGreaterThanOrEqual(2);
  });

  it("does not render dots for single item", () => {
    render(
      <CmsBanner
        items={[{ id: 1, image_url: "https://example.com/b.jpg", description: "", link_url: "" }]}
      />,
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试验证**

```bash
pnpm --filter @ec/web test
```

Expected: Tests pass.

---

### Task 5: 类型检查验证

- [ ] **Step 1: 运行类型检查**

```bash
pnpm --filter @ec/ui check
pnpm --filter @ec/web check
pnpm --filter @ec/admin check
```

Expected: No type errors.