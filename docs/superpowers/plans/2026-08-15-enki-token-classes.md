# ec-main enki Token 组合类体系实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 ec-main 移动端 design token 体系中落地 67 个 `enki-*` 组合类（含字体栈/中间变量/elevation/button filter），取值与 weee 线上产物（`static.weeecdn.net/.../main.cjk.b6b084eb.min.css`）像素级一致，且作为基础组件默认值时可被外部 Tailwind utilities **无需 `!`** 覆盖。

**Architecture:** 以 `@layer components` 普通 class 实现 enki-* 组合类（CSS cascade 中 utilities layer 优先级最高，天然可被外部覆盖），tokens.css 追加 enki 所需基础变量（font-family/lineheight/weight 别名 + elevation 中间值 + 中间变量），删除现有取值有偏差的无前缀 `display-*`/`heading-*`/`body-*`/`elevation-shadow-*` 类，全站字体栈切换为 enki CJK 栈。

**Tech Stack:** Tailwind v4 CSS-first（`@theme` + `@layer components`）、Next.js App Router、vitest、TypeScript。

**参考源（只读）：** `/tmp/enki-main.cjk.css`（CDN 产物抓取件，或线上重抓）。

---

## 文件结构

| 文件 | 操作 | 职责 |
|---|---|---|
| `apps/web/app/design-tokens/refer/enki-cdn.css` | 新建 | CDN 产物原件归档（只读审计） |
| `apps/web/app/design-tokens/tokens.css` | 修改 | 追加 enki 字体栈/别名/elevation 中间值/中间变量 |
| `apps/web/app/design-tokens/enki.css` | 新建 | 67 个 `enki-*` 组合类（`@layer components`） |
| `apps/web/app/design-tokens/support-classes.css` | 修改 | 删除无前缀 display/heading/body/elevation-shadow @utility |
| `apps/web/app/globals.css` | 修改 | import enki.css；body 字体栈切换 |
| `apps/web/app/(main)/page.tsx` | 修改 | `body-sm`/`heading-3xl`/`body-base` → `enki-*` |

---

### Task 1: 归档 CDN 产物

**Files:**
- Create: `apps/web/app/design-tokens/refer/enki-cdn.css`

- [ ] **Step 1: 抓取 CDN 产物并归档**

```bash
mkdir -p apps/web/app/design-tokens/refer
curl -sL "https://static.weeecdn.net/common/enki-styles/main.cjk.b6b084eb.min.css" -o apps/web/app/design-tokens/refer/enki-cdn.css
wc -c apps/web/app/design-tokens/refer/enki-cdn.css   # 预期约 48431 字节
```

- [ ] **Step 2: 确认抓取成功**

```bash
rg -c "enki-display-3xl" apps/web/app/design-tokens/refer/enki-cdn.css   # 预期 ≥ 1（类 + 中间变量引用）
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/app/design-tokens/refer/enki-cdn.css
git commit -m "docs: 归档 weee enki CDN 产物（只读审计）"
```

---

### Task 2: tokens.css 追加 enki 变量

**Files:**
- Modify: `apps/web/app/design-tokens/tokens.css`

> 全部追加在文件末尾 `@theme { ... }` 的最后一个 `}` 之前（当前第 596 行 `}` 前）。字体栈与 CDN 产物逐一字符串相同。

- [ ] **Step 1: 追加 enki 字体栈 + 别名变量**

在 `--font-tracking-widest` 行（当前 595 行）之后、末尾 `}` 之前插入：

```css
  /* ────────────── 字体栈（对齐 weee 线上 enki 产物） ────────────── */
  --font-family-number-main: SF Pro Text,SF Pro,Microsoft YaHei,PingFang SC,Roboto,Helvetica Neue,Helvetica,Arial,Apple SD Gothic Neo,Malgun Gothic,BlinkMacSystemFont,-apple-system,Segoe UI,Ubuntu,sans-serif;
  --font-family-cjk-display: SF Pro Text,SF Pro,Microsoft YaHei,PingFang SC,Roboto,Helvetica Neue,Helvetica,Arial,Apple SD Gothic Neo,Malgun Gothic,BlinkMacSystemFont,-apple-system,Segoe UI,Ubuntu,sans-serif;
  --font-family-cjk-heading: SF Pro Text,SF Pro,Microsoft YaHei,PingFang SC,Roboto,Helvetica Neue,Helvetica,Arial,Apple SD Gothic Neo,Malgun Gothic,BlinkMacSystemFont,-apple-system,Segoe UI,Ubuntu,sans-serif;
  --font-family-cjk-body: SF Pro Text,SF Pro,Microsoft YaHei,PingFang SC,Roboto,Helvetica Neue,Helvetica,Arial,Apple SD Gothic Neo,Malgun Gothic,BlinkMacSystemFont,-apple-system,Segoe UI,Ubuntu,sans-serif;
  --font-family-cjk-main: SF Pro Text,SF Pro,Microsoft YaHei,PingFang SC,Roboto,Helvetica Neue,Helvetica,Arial,Apple SD Gothic Neo,Malgun Gothic,BlinkMacSystemFont,-apple-system,Segoe UI,Ubuntu,sans-serif;

  /* ────────────── enki 行高别名（与 --font-leading-* 同值） ────────────── */
  --font-lineheight-100: 1;
  --font-lineheight-105: 1.05;
  --font-lineheight-110: 1.1;
  --font-lineheight-115: 1.15;
  --font-lineheight-125: 1.25;
  --font-lineheight-150: 1.5;

  /* ────────────── enki 字重别名（对齐 CDN 命名后缀） ────────────── */
  --font-weight-400-regular: 400;
  --font-weight-500-medium: 500;
  --font-weight-700-bold: 700;
```

- [ ] **Step 2: 字距单位 em → px（原位替换）**

将现有 589-595 行的 `--font-tracking-*` 从 `em` 改为 CDN 的 `px` 值：

```css
  --font-tracking-tightest: -0.60px;
  --font-tracking-tighter:  -0.30px;
  --font-tracking-tight:    -0.20px;
  --font-tracking-base:     0px;
  --font-tracking-wide:     0.20px;
  --font-tracking-wider:    0.30px;
  --font-tracking-widest:   0.60px;
```

- [ ] **Step 3: 追加 elevation 基础尺寸 + 组合值 + filter**

同样在末尾 `}` 之前接续：

```css
  /* ────────────── enki elevation 基础尺寸（对齐 CDN --size-elevation-*） ────────────── */
  --size-elevation-spread-100: 1px;
  --size-elevation-spread-200: 2px;
  --size-elevation-spread-300: 3px;
  --size-elevation-blur-100: 0px;
  --size-elevation-blur-200: 4px;
  --size-elevation-blur-300: 6px;
  --size-elevation-blur-400: 8px;
  --size-elevation-blur-500: 12px;
  --size-elevation-blur-600: 16px;
  --size-elevation-blur-700: 20px;
  --size-elevation-blur-800: 24px;
  --size-elevation-blur-900: 28px;
  --size-elevation-blur-1000: 32px;
  --size-elevation-blur-1100: 36px;
  --size-elevation-blur-1200: 40px;
  --size-elevation-blur-1300: 44px;
  --size-elevation-blur-1400: 48px;
  --size-elevation-blur-1800: 64px;
  --size-elevation-blur-2200: 80px;
  --size-elevation-distance-100: 1px;
  --size-elevation-distance-200: 2px;
  --size-elevation-distance-300: 6px;
  --size-elevation-distance-400: 8px;
  --size-elevation-distance-500: 10px;
  --size-elevation-distance-600: 12px;
  --size-elevation-distance-700: 14px;
  --size-elevation-distance-800: 16px;
  --size-elevation-distance-900: 18px;
  --size-elevation-distance-1000: 20px;
  --size-elevation-distance-1100: 22px;
  --size-elevation-distance-1200: 24px;

  /* ────────────── enki elevation 组合值（box-shadow 双层结构） ────────────── */
  --style-elevation-1: 0 0 0 var(--size-elevation-spread-100) var(--color-tint-black-25);
  --style-elevation-2: 0 var(--size-elevation-distance-200) var(--size-elevation-blur-300) 0 var(--color-tint-black-25);
  --style-elevation-3: 0 var(--size-elevation-distance-200) var(--size-elevation-blur-400) 0 var(--color-tint-black-25);
  --style-elevation-4: 0 0 var(--size-elevation-blur-300) 0 var(--color-tint-black-25),0 var(--size-elevation-distance-200) var(--size-elevation-blur-500) 0 var(--color-tint-black-25);
  --style-elevation-5: 0 0 var(--size-elevation-blur-400) 0 var(--color-tint-black-25),0 var(--size-elevation-distance-400) var(--size-elevation-blur-700) 0 var(--color-tint-black-25);
  --style-elevation-6: 0 0 var(--size-elevation-blur-300) 0 var(--color-tint-black-25),0 var(--size-elevation-distance-700) var(--size-elevation-blur-1000) 0 var(--color-tint-black-25);
  --style-elevation-7: 0 0 var(--size-elevation-blur-300) 0 var(--color-tint-black-25),0 var(--size-elevation-distance-1200) var(--size-elevation-blur-1400) 0 var(--color-tint-black-25);
  --style-elevation-8: 0 0 var(--size-elevation-blur-300) 0 var(--color-tint-black-25),0 var(--size-elevation-distance-1200) var(--size-elevation-blur-1800) 0 var(--color-tint-black-25);
  --style-elevation-9: 0 0 var(--size-elevation-blur-300) 0 var(--color-tint-black-25),0 var(--size-elevation-distance-1200) var(--size-elevation-blur-2200) 0 var(--color-tint-black-25);

  /* ────────────── enki button filter（hover/pressed） ────────────── */
  --style-filter-lighten-1-hover: brightness(105%) saturate(105%);
  --style-filter-lighten-1-pressed: brightness(108%) saturate(108%);
  --style-filter-darken-1-hover: brightness(95%) saturate(105%);
  --style-filter-darken-1-pressed: brightness(92%) saturate(108%);
```

- [ ] **Step 4: 追加 display/heading 中间变量**

在末尾 `}` 之前接续：

```css
  /* ────────────── enki 中间变量：display（7 字号 × size/family/weight/weightstrong/lineheight/tracking） ────────────── */
  --display-sm-size: var(--font-size-lg);
  --display-sm-family: var(--font-family-cjk-display);
  --display-sm-weight: var(--font-weight-500-medium);
  --display-sm-weightstrong: var(--font-weight-700-bold);
  --display-sm-lineheight: var(--font-lineheight-125);
  --display-sm-tracking: var(--font-tracking-widest);
  --display-lg-size: var(--font-size-xl);
  --display-lg-family: var(--font-family-cjk-display);
  --display-lg-weight: var(--font-weight-500-medium);
  --display-lg-weightstrong: var(--font-weight-700-bold);
  --display-lg-lineheight: var(--font-lineheight-125);
  --display-lg-tracking: var(--font-tracking-widest);
  --display-xl-size: var(--font-size-2xl);
  --display-xl-family: var(--font-family-cjk-display);
  --display-xl-weight: var(--font-weight-500-medium);
  --display-xl-weightstrong: var(--font-weight-700-bold);
  --display-xl-lineheight: var(--font-lineheight-125);
  --display-xl-tracking: var(--font-tracking-widest);
  --display-2xl-size: var(--font-size-3xl);
  --display-2xl-family: var(--font-family-cjk-display);
  --display-2xl-weight: var(--font-weight-500-medium);
  --display-2xl-weightstrong: var(--font-weight-700-bold);
  --display-2xl-lineheight: var(--font-lineheight-125);
  --display-2xl-tracking: var(--font-tracking-widest);
  --display-3xl-size: var(--font-size-4xl);
  --display-3xl-family: var(--font-family-cjk-display);
  --display-3xl-weight: var(--font-weight-500-medium);
  --display-3xl-weightstrong: var(--font-weight-700-bold);
  --display-3xl-lineheight: var(--font-lineheight-125);
  --display-3xl-tracking: var(--font-tracking-widest);
  --display-4xl-size: var(--font-size-5xl);
  --display-4xl-family: var(--font-family-cjk-display);
  --display-4xl-weight: var(--font-weight-500-medium);
  --display-4xl-weightstrong: var(--font-weight-700-bold);
  --display-4xl-lineheight: var(--font-lineheight-125);
  --display-4xl-tracking: var(--font-tracking-widest);
  --display-5xl-size: var(--font-size-6xl);
  --display-5xl-family: var(--font-family-cjk-display);
  --display-5xl-weight: var(--font-weight-500-medium);
  --display-5xl-weightstrong: var(--font-weight-700-bold);
  --display-5xl-lineheight: var(--font-lineheight-125);
  --display-5xl-tracking: var(--font-tracking-widest);
```

- [ ] **Step 5: 追加 heading 中间变量**

同样接续：

```css
  /* ────────────── enki 中间变量：heading ────────────── */
  --heading-sm-size: var(--font-size-lg);
  --heading-sm-family: var(--font-family-cjk-heading);
  --heading-sm-weight: var(--font-weight-500-medium);
  --heading-sm-weightstrong: var(--font-weight-700-bold);
  --heading-sm-lineheight: var(--font-lineheight-125);
  --heading-sm-tracking: var(--font-tracking-widest);
  --heading-lg-size: var(--font-size-xl);
  --heading-lg-family: var(--font-family-cjk-heading);
  --heading-lg-weight: var(--font-weight-500-medium);
  --heading-lg-weightstrong: var(--font-weight-700-bold);
  --heading-lg-lineheight: var(--font-lineheight-125);
  --heading-lg-tracking: var(--font-tracking-widest);
  --heading-xl-size: var(--font-size-2xl);
  --heading-xl-family: var(--font-family-cjk-heading);
  --heading-xl-weight: var(--font-weight-500-medium);
  --heading-xl-weightstrong: var(--font-weight-700-bold);
  --heading-xl-lineheight: var(--font-lineheight-125);
  --heading-xl-tracking: var(--font-tracking-widest);
  --heading-2xl-size: var(--font-size-3xl);
  --heading-2xl-family: var(--font-family-cjk-heading);
  --heading-2xl-weight: var(--font-weight-500-medium);
  --heading-2xl-weightstrong: var(--font-weight-700-bold);
  --heading-2xl-lineheight: var(--font-lineheight-125);
  --heading-2xl-tracking: var(--font-tracking-widest);
  --heading-3xl-size: var(--font-size-4xl);
  --heading-3xl-family: var(--font-family-cjk-heading);
  --heading-3xl-weight: var(--font-weight-500-medium);
  --heading-3xl-weightstrong: var(--font-weight-700-bold);
  --heading-3xl-lineheight: var(--font-lineheight-125);
  --heading-3xl-tracking: var(--font-tracking-widest);
  --heading-4xl-size: var(--font-size-5xl);
  --heading-4xl-family: var(--font-family-cjk-heading);
  --heading-4xl-weight: var(--font-weight-500-medium);
  --heading-4xl-weightstrong: var(--font-weight-700-bold);
  --heading-4xl-lineheight: var(--font-lineheight-125);
  --heading-4xl-tracking: var(--font-tracking-widest);
  --heading-5xl-size: var(--font-size-6xl);
  --heading-5xl-family: var(--font-family-cjk-heading);
  --heading-5xl-weight: var(--font-weight-500-medium);
  --heading-5xl-weightstrong: var(--font-weight-700-bold);
  --heading-5xl-lineheight: var(--font-lineheight-125);
  --heading-5xl-tracking: var(--font-tracking-widest);
```

- [ ] **Step 6: 追加 body 中间变量**

最后接续：

```css
  /* ────────────── enki 中间变量：body（8 字号，含 weightmedium） ────────────── */
  --body-2xl-size: var(--font-size-2xl);
  --body-2xl-family: var(--font-family-cjk-body);
  --body-2xl-weight: var(--font-weight-400-regular);
  --body-2xl-weightmedium: var(--font-weight-500-medium);
  --body-2xl-weightstrong: var(--font-weight-700-bold);
  --body-2xl-lineheight: var(--font-lineheight-125);
  --body-2xl-tracking: var(--font-tracking-widest);
  --body-xl-size: var(--font-size-xl);
  --body-xl-family: var(--font-family-cjk-body);
  --body-xl-weight: var(--font-weight-400-regular);
  --body-xl-weightmedium: var(--font-weight-500-medium);
  --body-xl-weightstrong: var(--font-weight-700-bold);
  --body-xl-lineheight: var(--font-lineheight-125);
  --body-xl-tracking: var(--font-tracking-widest);
  --body-lg-size: var(--font-size-lg);
  --body-lg-family: var(--font-family-cjk-body);
  --body-lg-weight: var(--font-weight-400-regular);
  --body-lg-weightmedium: var(--font-weight-500-medium);
  --body-lg-weightstrong: var(--font-weight-700-bold);
  --body-lg-lineheight: var(--font-lineheight-125);
  --body-lg-tracking: var(--font-tracking-widest);
  --body-base-size: var(--font-size-base);
  --body-base-family: var(--font-family-cjk-body);
  --body-base-weight: var(--font-weight-400-regular);
  --body-base-weightmedium: var(--font-weight-500-medium);
  --body-base-weightstrong: var(--font-weight-700-bold);
  --body-base-lineheight: var(--font-lineheight-125);
  --body-base-tracking: var(--font-tracking-widest);
  --body-sm-size: var(--font-size-sm);
  --body-sm-family: var(--font-family-cjk-body);
  --body-sm-weight: var(--font-weight-400-regular);
  --body-sm-weightmedium: var(--font-weight-500-medium);
  --body-sm-weightstrong: var(--font-weight-700-bold);
  --body-sm-lineheight: var(--font-lineheight-125);
  --body-sm-tracking: var(--font-tracking-widest);
  --body-xs-size: var(--font-size-xs);
  --body-xs-family: var(--font-family-cjk-body);
  --body-xs-weight: var(--font-weight-400-regular);
  --body-xs-weightmedium: var(--font-weight-500-medium);
  --body-xs-weightstrong: var(--font-weight-700-bold);
  --body-xs-lineheight: var(--font-lineheight-125);
  --body-xs-tracking: var(--font-tracking-widest);
  --body-2xs-size: var(--font-size-2xs);
  --body-2xs-family: var(--font-family-cjk-body);
  --body-2xs-weight: var(--font-weight-400-regular);
  --body-2xs-weightmedium: var(--font-weight-500-medium);
  --body-2xs-weightstrong: var(--font-weight-700-bold);
  --body-2xs-lineheight: var(--font-lineheight-125);
  --body-2xs-tracking: var(--font-tracking-widest);
  --body-3xs-size: var(--font-size-3xs);
  --body-3xs-family: var(--font-family-cjk-body);
  --body-3xs-weight: var(--font-weight-400-regular);
  --body-3xs-weightmedium: var(--font-weight-500-medium);
  --body-3xs-weightstrong: var(--font-weight-700-bold);
  --body-3xs-lineheight: var(--font-lineheight-125);
  --body-3xs-tracking: var(--font-tracking-widest);
```

- [ ] **Step 7: 验证变量数（精确断言）**

```bash
T=apps/web/app/design-tokens/tokens.css
rg -c -- "--font-family-(cjk|number)-" $T          # 预期 5
rg -c -- "--font-lineheight-" $T                    # 预期 6
rg -c -- "--font-weight-400-regular|--font-weight-500-medium|--font-weight-700-bold" $T   # 预期 3
rg -c -- "--size-elevation-" $T                     # 预期 32（blur 17 + distance 12 + spread 3）
rg -c -- "--style-elevation-|--style-filter-" $T    # 预期 13（elevation 9 + filter 4）
rg -c -- "--font-size-" $T                          # 预期 13（3xs..10xl，用于核对中间变量引用存在）
rg -c -- "--display-" $T                            # 预期 42（7 字号 × 6 中间变量）
rg -c -- "--heading-" $T                            # 预期 42
rg -c -- "--body-" $T                               # 预期 56（8 字号 × 7 中间变量）
```

- [ ] **Step 8: Commit**

```bash
git add apps/web/app/design-tokens/tokens.css
git commit -m "feat: tokens.css 追加 enki 字体栈/别名/elevation/中间变量"
```

---

### Task 3: 新建 enki.css 组合类

**Files:**
- Create: `apps/web/app/design-tokens/enki.css`

> 全部 67 个类包裹在 `@layer components` 内，属性集与 CDN 产物逐字一致。生成方式可参考 `/tmp` 的脚本模板，但本计划给出全部代码。

- [ ] **Step 1: 创建 enki.css（第 1 部分：display + heading）**

```css
/**
 * ec-main design token — enki 组合类（对齐 weee 线上产物）
 * 实现方式：@layer components 普通 class。
 * 依据 Tailwind v4 cascade：utilities layer 优先级最高，
 * 故外部叠加 text-sm/font-bold 等工具类可无需 ! 覆盖本层默认值。
 */
@layer components {
  /* ── display ── */
  .enki-display-sm {
    letter-spacing: var(--display-sm-tracking);
    font-size: var(--display-sm-size);
    font-family: var(--display-sm-family);
    line-height: var(--display-sm-lineheight);
    font-weight: var(--display-sm-weight);
  }
  .enki-display-sm-strong {
    letter-spacing: var(--display-sm-tracking);
    font-size: var(--display-sm-size);
    font-family: var(--display-sm-family);
    line-height: var(--display-sm-lineheight);
    font-weight: var(--display-sm-weightstrong);
  }
  .enki-display-lg {
    letter-spacing: var(--display-lg-tracking);
    font-size: var(--display-lg-size);
    font-family: var(--display-lg-family);
    line-height: var(--display-lg-lineheight);
    font-weight: var(--display-lg-weight);
  }
  .enki-display-lg-strong {
    letter-spacing: var(--display-lg-tracking);
    font-size: var(--display-lg-size);
    font-family: var(--display-lg-family);
    line-height: var(--display-lg-lineheight);
    font-weight: var(--display-lg-weightstrong);
  }
  .enki-display-xl {
    letter-spacing: var(--display-xl-tracking);
    font-size: var(--display-xl-size);
    font-family: var(--display-xl-family);
    line-height: var(--display-xl-lineheight);
    font-weight: var(--display-xl-weight);
  }
  .enki-display-xl-strong {
    letter-spacing: var(--display-xl-tracking);
    font-size: var(--display-xl-size);
    font-family: var(--display-xl-family);
    line-height: var(--display-xl-lineheight);
    font-weight: var(--display-xl-weightstrong);
  }
  .enki-display-2xl {
    letter-spacing: var(--display-2xl-tracking);
    font-size: var(--display-2xl-size);
    font-family: var(--display-2xl-family);
    line-height: var(--display-2xl-lineheight);
    font-weight: var(--display-2xl-weight);
  }
  .enki-display-2xl-strong {
    letter-spacing: var(--display-2xl-tracking);
    font-size: var(--display-2xl-size);
    font-family: var(--display-2xl-family);
    line-height: var(--display-2xl-lineheight);
    font-weight: var(--display-2xl-weightstrong);
  }
  .enki-display-3xl {
    letter-spacing: var(--display-3xl-tracking);
    font-size: var(--display-3xl-size);
    font-family: var(--display-3xl-family);
    line-height: var(--display-3xl-lineheight);
    font-weight: var(--display-3xl-weight);
  }
  .enki-display-3xl-strong {
    letter-spacing: var(--display-3xl-tracking);
    font-size: var(--display-3xl-size);
    font-family: var(--display-3xl-family);
    line-height: var(--display-3xl-lineheight);
    font-weight: var(--display-3xl-weightstrong);
  }
  .enki-display-4xl {
    letter-spacing: var(--display-4xl-tracking);
    font-size: var(--display-4xl-size);
    font-family: var(--display-4xl-family);
    line-height: var(--display-4xl-lineheight);
    font-weight: var(--display-4xl-weight);
  }
  .enki-display-4xl-strong {
    letter-spacing: var(--display-4xl-tracking);
    font-size: var(--display-4xl-size);
    font-family: var(--display-4xl-family);
    line-height: var(--display-4xl-lineheight);
    font-weight: var(--display-4xl-weightstrong);
  }
  .enki-display-5xl {
    letter-spacing: var(--display-5xl-tracking);
    font-size: var(--display-5xl-size);
    font-family: var(--display-5xl-family);
    line-height: var(--display-5xl-lineheight);
    font-weight: var(--display-5xl-weight);
  }
  .enki-display-5xl-strong {
    letter-spacing: var(--display-5xl-tracking);
    font-size: var(--display-5xl-size);
    font-family: var(--display-5xl-family);
    line-height: var(--display-5xl-lineheight);
    font-weight: var(--display-5xl-weightstrong);
  }

  /* ── heading ── */
  .enki-heading-sm {
    letter-spacing: var(--heading-sm-tracking);
    font-size: var(--heading-sm-size);
    font-family: var(--heading-sm-family);
    line-height: var(--heading-sm-lineheight);
    font-weight: var(--heading-sm-weight);
  }
  .enki-heading-sm-strong {
    letter-spacing: var(--heading-sm-tracking);
    font-size: var(--heading-sm-size);
    font-family: var(--heading-sm-family);
    line-height: var(--heading-sm-lineheight);
    font-weight: var(--heading-sm-weightstrong);
  }
  .enki-heading-lg {
    letter-spacing: var(--heading-lg-tracking);
    font-size: var(--heading-lg-size);
    font-family: var(--heading-lg-family);
    line-height: var(--heading-lg-lineheight);
    font-weight: var(--heading-lg-weight);
  }
  .enki-heading-lg-strong {
    letter-spacing: var(--heading-lg-tracking);
    font-size: var(--heading-lg-size);
    font-family: var(--heading-lg-family);
    line-height: var(--heading-lg-lineheight);
    font-weight: var(--heading-lg-weightstrong);
  }
  .enki-heading-xl {
    letter-spacing: var(--heading-xl-tracking);
    font-size: var(--heading-xl-size);
    font-family: var(--heading-xl-family);
    line-height: var(--heading-xl-lineheight);
    font-weight: var(--heading-xl-weight);
  }
  .enki-heading-xl-strong {
    letter-spacing: var(--heading-xl-tracking);
    font-size: var(--heading-xl-size);
    font-family: var(--heading-xl-family);
    line-height: var(--heading-xl-lineheight);
    font-weight: var(--heading-xl-weightstrong);
  }
  .enki-heading-2xl {
    letter-spacing: var(--heading-2xl-tracking);
    font-size: var(--heading-2xl-size);
    font-family: var(--heading-2xl-family);
    line-height: var(--heading-2xl-lineheight);
    font-weight: var(--heading-2xl-weight);
  }
  .enki-heading-2xl-strong {
    letter-spacing: var(--heading-2xl-tracking);
    font-size: var(--heading-2xl-size);
    font-family: var(--heading-2xl-family);
    line-height: var(--heading-2xl-lineheight);
    font-weight: var(--heading-2xl-weightstrong);
  }
  .enki-heading-3xl {
    letter-spacing: var(--heading-3xl-tracking);
    font-size: var(--heading-3xl-size);
    font-family: var(--heading-3xl-family);
    line-height: var(--heading-3xl-lineheight);
    font-weight: var(--heading-3xl-weight);
  }
  .enki-heading-3xl-strong {
    letter-spacing: var(--heading-3xl-tracking);
    font-size: var(--heading-3xl-size);
    font-family: var(--heading-3xl-family);
    line-height: var(--heading-3xl-lineheight);
    font-weight: var(--heading-3xl-weightstrong);
  }
  .enki-heading-4xl {
    letter-spacing: var(--heading-4xl-tracking);
    font-size: var(--heading-4xl-size);
    font-family: var(--heading-4xl-family);
    line-height: var(--heading-4xl-lineheight);
    font-weight: var(--heading-4xl-weight);
  }
  .enki-heading-4xl-strong {
    letter-spacing: var(--heading-4xl-tracking);
    font-size: var(--heading-4xl-size);
    font-family: var(--heading-4xl-family);
    line-height: var(--heading-4xl-lineheight);
    font-weight: var(--heading-4xl-weightstrong);
  }
  .enki-heading-5xl {
    letter-spacing: var(--heading-5xl-tracking);
    font-size: var(--heading-5xl-size);
    font-family: var(--heading-5xl-family);
    line-height: var(--heading-5xl-lineheight);
    font-weight: var(--heading-5xl-weight);
  }
  .enki-heading-5xl-strong {
    letter-spacing: var(--heading-5xl-tracking);
    font-size: var(--heading-5xl-size);
    font-family: var(--heading-5xl-family);
    line-height: var(--heading-5xl-lineheight);
    font-weight: var(--heading-5xl-weightstrong);
  }
```

- [ ] **Step 2: 追加 body 段（第 2 部分）**

接续该 `@layer components { ... }` 块内：

```css
  /* ── body ── */
  .enki-body-2xl {
    letter-spacing: var(--body-2xl-tracking);
    font-size: var(--body-2xl-size);
    font-family: var(--body-2xl-family);
    line-height: var(--body-2xl-lineheight);
    font-weight: var(--body-2xl-weight);
  }
  .enki-body-2xl-medium {
    letter-spacing: var(--body-2xl-tracking);
    font-size: var(--body-2xl-size);
    font-family: var(--body-2xl-family);
    line-height: var(--body-2xl-lineheight);
    font-weight: var(--body-2xl-weightmedium);
  }
  .enki-body-2xl-strong {
    letter-spacing: var(--body-2xl-tracking);
    font-size: var(--body-2xl-size);
    font-family: var(--body-2xl-family);
    line-height: var(--body-2xl-lineheight);
    font-weight: var(--body-2xl-weightstrong);
  }
  .enki-body-xl {
    letter-spacing: var(--body-xl-tracking);
    font-size: var(--body-xl-size);
    font-family: var(--body-xl-family);
    line-height: var(--body-xl-lineheight);
    font-weight: var(--body-xl-weight);
  }
  .enki-body-xl-medium {
    letter-spacing: var(--body-xl-tracking);
    font-size: var(--body-xl-size);
    font-family: var(--body-xl-family);
    line-height: var(--body-xl-lineheight);
    font-weight: var(--body-xl-weightmedium);
  }
  .enki-body-xl-strong {
    letter-spacing: var(--body-xl-tracking);
    font-size: var(--body-xl-size);
    font-family: var(--body-xl-family);
    line-height: var(--body-xl-lineheight);
    font-weight: var(--body-xl-weightstrong);
  }
  .enki-body-lg {
    letter-spacing: var(--body-lg-tracking);
    font-size: var(--body-lg-size);
    font-family: var(--body-lg-family);
    line-height: var(--body-lg-lineheight);
    font-weight: var(--body-lg-weight);
  }
  .enki-body-lg-medium {
    letter-spacing: var(--body-lg-tracking);
    font-size: var(--body-lg-size);
    font-family: var(--body-lg-family);
    line-height: var(--body-lg-lineheight);
    font-weight: var(--body-lg-weightmedium);
  }
  .enki-body-lg-strong {
    letter-spacing: var(--body-lg-tracking);
    font-size: var(--body-lg-size);
    font-family: var(--body-lg-family);
    line-height: var(--body-lg-lineheight);
    font-weight: var(--body-lg-weightstrong);
  }
  .enki-body-base {
    letter-spacing: var(--body-base-tracking);
    font-size: var(--body-base-size);
    font-family: var(--body-base-family);
    line-height: var(--body-base-lineheight);
    font-weight: var(--body-base-weight);
  }
  .enki-body-base-medium {
    letter-spacing: var(--body-base-tracking);
    font-size: var(--body-base-size);
    font-family: var(--body-base-family);
    line-height: var(--body-base-lineheight);
    font-weight: var(--body-base-weightmedium);
  }
  .enki-body-base-strong {
    letter-spacing: var(--body-base-tracking);
    font-size: var(--body-base-size);
    font-family: var(--body-base-family);
    line-height: var(--body-base-lineheight);
    font-weight: var(--body-base-weightstrong);
  }
  .enki-body-sm {
    letter-spacing: var(--body-sm-tracking);
    font-size: var(--body-sm-size);
    font-family: var(--body-sm-family);
    line-height: var(--body-sm-lineheight);
    font-weight: var(--body-sm-weight);
  }
  .enki-body-sm-medium {
    letter-spacing: var(--body-sm-tracking);
    font-size: var(--body-sm-size);
    font-family: var(--body-sm-family);
    line-height: var(--body-sm-lineheight);
    font-weight: var(--body-sm-weightmedium);
  }
  .enki-body-sm-strong {
    letter-spacing: var(--body-sm-tracking);
    font-size: var(--body-sm-size);
    font-family: var(--body-sm-family);
    line-height: var(--body-sm-lineheight);
    font-weight: var(--body-sm-weightstrong);
  }
  .enki-body-xs {
    letter-spacing: var(--body-xs-tracking);
    font-size: var(--body-xs-size);
    font-family: var(--body-xs-family);
    line-height: var(--body-xs-lineheight);
    font-weight: var(--body-xs-weight);
  }
  .enki-body-xs-medium {
    letter-spacing: var(--body-xs-tracking);
    font-size: var(--body-xs-size);
    font-family: var(--body-xs-family);
    line-height: var(--body-xs-lineheight);
    font-weight: var(--body-xs-weightmedium);
  }
  .enki-body-xs-strong {
    letter-spacing: var(--body-xs-tracking);
    font-size: var(--body-xs-size);
    font-family: var(--body-xs-family);
    line-height: var(--body-xs-lineheight);
    font-weight: var(--body-xs-weightstrong);
  }
  .enki-body-2xs {
    letter-spacing: var(--body-2xs-tracking);
    font-size: var(--body-2xs-size);
    font-family: var(--body-2xs-family);
    line-height: var(--body-2xs-lineheight);
    font-weight: var(--body-2xs-weight);
  }
  .enki-body-2xs-medium {
    letter-spacing: var(--body-2xs-tracking);
    font-size: var(--body-2xs-size);
    font-family: var(--body-2xs-family);
    line-height: var(--body-2xs-lineheight);
    font-weight: var(--body-2xs-weightmedium);
  }
  .enki-body-2xs-strong {
    letter-spacing: var(--body-2xs-tracking);
    font-size: var(--body-2xs-size);
    font-family: var(--body-2xs-family);
    line-height: var(--body-2xs-lineheight);
    font-weight: var(--body-2xs-weightstrong);
  }
  .enki-body-3xs {
    letter-spacing: var(--body-3xs-tracking);
    font-size: var(--body-3xs-size);
    font-family: var(--body-3xs-family);
    line-height: var(--body-3xs-lineheight);
    font-weight: var(--body-3xs-weight);
  }
  .enki-body-3xs-medium {
    letter-spacing: var(--body-3xs-tracking);
    font-size: var(--body-3xs-size);
    font-family: var(--body-3xs-family);
    line-height: var(--body-3xs-lineheight);
    font-weight: var(--body-3xs-weightmedium);
  }
  .enki-body-3xs-strong {
    letter-spacing: var(--body-3xs-tracking);
    font-size: var(--body-3xs-size);
    font-family: var(--body-3xs-family);
    line-height: var(--body-3xs-lineheight);
    font-weight: var(--body-3xs-weightstrong);
  }
```

- [ ] **Step 3: 追加 button + elevation 段（第 3 部分）并闭合**

接续：

```css
  /* ── button（cursor 与 CDN 对齐；disabled 无 hover/pressed） ── */
  .enki-button-primary {
    appearance: none;
    outline: 0;
    cursor: pointer;
    background-color: var(--color-btn-primary-bg);
    color: var(--color-btn-primary-fg-default);
  }
  @media (hover: hover) {
    .enki-button-primary:hover { filter: var(--style-filter-lighten-1-hover); }
  }
  .enki-button-primary:active { filter: var(--style-filter-lighten-1-pressed); }
  .enki-button-secondary {
    appearance: none;
    outline: 0;
    cursor: pointer;
    background-color: var(--color-btn-secondary-bg);
    color: var(--color-btn-secondary-fg-default);
  }
  @media (hover: hover) {
    .enki-button-secondary:hover { filter: var(--style-filter-lighten-1-hover); }
  }
  .enki-button-secondary:active { filter: var(--style-filter-lighten-1-pressed); }
  .enki-button-tertiary {
    appearance: none;
    outline: 0;
    cursor: pointer;
    background-color: var(--color-btn-tertiary-bg);
    color: var(--color-btn-tertiary-fg-default);
  }
  @media (hover: hover) {
    .enki-button-tertiary:hover { filter: var(--style-filter-darken-1-hover); }
  }
  .enki-button-tertiary:active { filter: var(--style-filter-darken-1-pressed); }
  .enki-button-confirmation {
    appearance: none;
    outline: 0;
    cursor: pointer;
    background-color: var(--color-btn-confirmation-bg);
    color: var(--color-btn-confirmation-fg-default);
  }
  @media (hover: hover) {
    .enki-button-confirmation:hover { filter: var(--style-filter-darken-1-hover); }
  }
  .enki-button-confirmation:active { filter: var(--style-filter-darken-1-pressed); }
  .enki-button-critical {
    appearance: none;
    outline: 0;
    cursor: pointer;
    background-color: var(--color-btn-critical-bg);
    color: var(--color-btn-critical-fg-default);
  }
  @media (hover: hover) {
    .enki-button-critical:hover { filter: var(--style-filter-darken-1-hover); }
  }
  .enki-button-critical:active { filter: var(--style-filter-darken-1-pressed); }
  .enki-button-disabled {
    appearance: none;
    outline: 0;
    cursor: not-allowed;
    background-color: var(--color-btn-disabled-bg);
    color: var(--color-btn-disabled-fg-default);
  }

  /* ── elevation ── */
  .enki-elevation-1 { box-shadow: var(--style-elevation-1); }
  .enki-elevation-2 { box-shadow: var(--style-elevation-2); }
  .enki-elevation-3 { box-shadow: var(--style-elevation-3); }
  .enki-elevation-4 { box-shadow: var(--style-elevation-4); }
  .enki-elevation-5 { box-shadow: var(--style-elevation-5); }
  .enki-elevation-6 { box-shadow: var(--style-elevation-6); }
  .enki-elevation-7 { box-shadow: var(--style-elevation-7); }
  .enki-elevation-8 { box-shadow: var(--style-elevation-8); }
  .enki-elevation-9 { box-shadow: var(--style-elevation-9); }
}
```

- [ ] **Step 4: 验证类数量**

```bash
rg -o "\.enki-[a-z0-9-]+" apps/web/app/design-tokens/enki.css | sort -u | wc -l   # 预期 67
rg -c "@layer components" apps/web/app/design-tokens/enki.css   # 预期 1
```

- [ ] **Step 5: Commit**

```bash
git add apps/web/app/design-tokens/enki.css
git commit -m "feat: 新增 67 个 enki 组合类（display/heading/body/button/elevation）"
```

---

### Task 4: 删除旧无前缀组合类

**Files:**
- Modify: `apps/web/app/design-tokens/support-classes.css`

> 删除全部 `@utility display-*`（36-77 行附近）、`@utility heading-*`（80-121 行附近）、`@utility body-*`（124-171 行附近）、`@utility elevation-shadow-*`（7-33 行附近），并把文件头注释改为说明已迁移。仅保留文件头注释 + 一句说明。

- [ ] **Step 1: 用脚本生成新旧文件内容**

```bash
cat apps/web/app/design-tokens/support-classes.css
# 确认行范围后，将文件整体替换为以下内容：
```

新文件内容：

```css
/**
 * ec-main design token — 自定义组合工具类（已迁移至 enki-* 体系）
 * 原 display-*/heading-*/body-*/elevation-shadow-* 无前缀组合类已迁移为
 * enki-*（见 enki.css），取值与 weee 线上产物对齐。
 * sizeof: enki.css 承担组合类职责后，本文件保留为空壳说明。
 */
```

- [ ] **Step 2: 验证无残留**

```bash
rg -n "display-3xl|heading-3xl|body-base|elevation-shadow" apps/web/app/design-tokens/support-classes.css
# 预期：无匹配
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/app/design-tokens/support-classes.css
git commit -m "refactor: 删除无前缀 display/heading/body/elevation 组合类（迁至 enki-*）"
```

---

### Task 5: globals.css 引入 enki.css + 切换字体栈

**Files:**
- Modify: `apps/web/app/globals.css`

- [ ] **Step 1: import enki.css**

在 `@import "./design-tokens/support-classes.css";` 行后新增：

```css
@import "./design-tokens/enki.css";
```

- [ ] **Step 2: 切换 body 字体栈**

将现有 `body { font-family: Arial, "Microsoft YaHei", sans-serif; }` 改为：

```css
body {
  margin: 0;
  font-family: var(--font-family-cjk-main);
}
```

- [ ] **Step 3: 验证**

```bash
rg -n "enki.css|font-family-cjk-main" apps/web/app/globals.css
# 预期：@import 与 body font-family 均命中
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/globals.css
git commit -m "feat: globals.css 引入 enki.css 并切换全站字体栈"
```

---

### Task 6: 迁移页面类名

**Files:**
- Modify: `apps/web/app/(main)/page.tsx`

- [ ] **Step 1: 无前缀类改为 enki-***

将三处类名替换：

| 原 | 新 |
|---|---|
| `body-sm` | `enki-body-sm` |
| `heading-3xl` | `enki-heading-3xl` |
| `body-base` | `enki-body-base` |

修改后文件关键部分：

```tsx
          <p className="enki-body-sm font-medium uppercase tracking-wide text-surface-100-fg-minor">
            EC Main
          </p>
          <h1 className="enki-heading-3xl">买家端商城底座</h1>
          <p className="enki-body-base text-surface-100-fg-minor">
```

- [ ] **Step 2: 验证无旧类残留**

```bash
rg -n "body-sm|heading-3xl|body-base|display-|elevation-shadow" "apps/web/app/(main)/page.tsx"
# 预期：无匹配（font-medium/tracking-wide 为 Tailwind 内置类，保留）
```

- [ ] **Step 3: Commit**

```bash
git add "apps/web/app/(main)/page.tsx"
git commit -m "feat: 首页改用 enki-* 组合类"
```

---

### Task 7: 全量验证

**Files:** 无（仅验证）

- [ ] **Step 1: 类型检查**

```bash
pnpm --filter @ec/web check
# 预期：tsc --noEmit 无错误
```

- [ ] **Step 2: 单元测试**

```bash
pnpm --filter @ec/web test
# 预期：4 test files、15 tests 全部通过
```

- [ ] **Step 3: 构建**

```bash
pnpm --filter @ec/web build
# 预期：Compiled successfully，无 CSS 警告
```

- [ ] **Step 4: 产物抽查（类与变量）**

```bash
CSS=$(find apps/web/.next/static/chunks -name "*.css" | head -1)
rg -o "\.enki-display-3xl\{[^}]*\}" "$CSS"        # 存在（components 层）
rg -o "\.enki-body-base-strong\{[^}]*\}" "$CSS"   # 存在
rg -o "\.enki-button-primary:hover[^{]*" "$CSS"   # 存在（hover filter）
rg -o "\.enki-elevation-5\{[^}]*\}" "$CSS"        # 存在
rg -o "\.display-3xl" "$CSS"                      # 预期无匹配（旧类已删）
rg -o -- "--font-family-cjk-main:[^;]*" "$CSS"    # 存在
rg -o -- "--style-elevation-5:[^;]*" "$CSS"       # 存在
```

- [ ] **Step 5: 覆盖行为验证（用户核心诉求）**

在产物中确认 `@layer components` 与 `@layer utilities` 的声明顺序，utilities 在 components 之后（保证 utilities 优先级更高）：

```bash
rg -n "@layer (theme, base, components, utilities|utilities|components)" "$CSS" | head
# 预期：存在 "@layer theme, base, components, utilities;" 声明
```

- [ ] **Step 6: 提交验证结果**

```bash
git add -A
git commit -m "test: enki token 全量验证（构建产物抽查）" || echo "无变更可提交"
```