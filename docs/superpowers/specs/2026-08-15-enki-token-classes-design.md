# ec-main enki Token 组合类体系设计文档

> 日期：2026-08-15
> 状态：设计已获批准，转入实施

## 一、背景与目标

在 ec-main 移动端 design token 体系（见 `2026-08-15-mobile-design-tokens-design.md`）基础之上，对接 weee 线上真正的 enki 产物：`https://static.weeecdn.net/common/enki-styles/main.cjk.b6b084eb.min.css`。

该文件是 weee 移动端线上使用的构建产物，暴露了 **67 个 `enki-*` 组合类**（`.enki-display-3xl`、`.enki-heading-sm`、`.enki-body-base-strong`、`.enki-button-primary`、`.enki-elevation-5` 等）。我们现有体系的 `display-*`/`heading-*`/`body-*` 组合类命名与取值都与此产物有偏差（无 `enki-` 前缀、字号映射、行高、字距、字重、font-family、elevation 取值均不同）。

**目标**：新增一层「enki compatibility」——67 个 `enki-*` 组合类，类名、结构、取值与线上产物像素级一致；同时统一全站字体栈。

**设计目标**：
1. 全量 67 个 enki 组合类，命名/取值与 CDN 产物完全对齐
2. 引入 enki 字体栈（`--font-family-cjk-*`）并全站统一
3. 删除现有取值有偏差的无前缀组合类，避免同语义两套取值
4. 保持与现有 token 体系的共生：`@utility` 语法 + `@theme` 变量引用

## 二、参考来源

**主来源**：`https://static.weeecdn.net/common/enki-styles/main.cjk.b6b084eb.min.css`（2026-08-15 抓取）。

该文件仅为 enki 的轻量子集（约 48KB），包含：
- `:root` 基础变量：`--font-size-*`、`--font-weight-400-regular/500-medium/700-bold`、`--font-lineheight-100..150`、`--font-tracking-*`、`--font-family-cjk-*`、`--font-family-number-main`、`--size-radius-*`、`--size-elevation-blur/distance/spread-*`、`--size-spacing-*`
- 中间变量：`--display-*`、`--heading-*`、`--body-*`（每个字号五件套：size/family/weight/weightstrong/weightmedium/lineheight/tracking）、`--style-elevation-1..9`、`--style-filter-lighten-1-hover/pressed`、`--style-filter-darken-1-hover/pressed`
- 组合类：67 个 `.enki-*`

## 三、总体架构

### 3.1 文件组织

```
apps/web/app/design-tokens/
  refer/enki-cdn.css          # 新增：CDN 产物原件归档（只读，供审计，不 import）
  tokens.css                  # 修改：补充 font-family/lineheight 别名/elevation 中间值变量
  enki.css                    # 新增：67 个 enki-* 组合类（@utility）
  support-classes.css         # 修改：删除被 enki-* 取代的无前缀组合类
apps/web/app/globals.css      # 修改：引入 enki.css、切换全站字体栈
```

### 3.2 组合类清单（67 个）

| 分类 | 变体 | 数量 |
|---|---|---|
| `enki-display-*` | sm / lg / xl / 2xl / 3xl / 4xl / 5xl × (默认 + `-strong`) | 14 |
| `enki-heading-*` | sm / lg / xl / 2xl / 3xl / 4xl / 5xl × (默认 + `-strong`) | 14 |
| `enki-body-*` | 3xs / 2xs / xs / sm / base / lg / xl / 2xl × (默认 + `-medium` + `-strong`) | 24 |
| `enki-button-*` | primary / secondary / tertiary / confirmation / critical / disabled | 6 |
| `enki-elevation-*` | 1..9 | 9 |
| **合计** | | **67** |

### 3.3 与现有体系的关系

- **删除**现有 `support-classes.css` 中的无前缀 `display-*` / `heading-*` / `body-*` / `elevation-shadow-*` @utility（取值有偏差，被 enki-* 取代）。
- **不删除**现有 token 变量（`--font-size-*`、`--font-weight-*`、`--font-leading-*` 等），enki 值在 tokens.css 中以追加方式补齐。
- enki 组合类沿用 `@utility` 语法（Tailwind 按需生成、tree-shake 友好）；产出 CSS 的目标属性值完全对齐 CDN 产物。

## 四、变量补充（tokens.css）

### 4.1 字体栈（5 个）

```css
--font-family-cjk-display: SF Pro Text, SF Pro, Microsoft YaHei, PingFang SC, ...;
--font-family-cjk-heading: 同上;
--font-family-cjk-body: 同上;
--font-family-cjk-main: 同上;
--font-family-number-main: 同上;
```

> 五个变量均为同一字体栈，语义上分别服务 display/heading/body/main 与数字。与 CDN 产物逐一对应。

### 4.2 行高别名（6 个）

```css
--font-lineheight-100: 1;
--font-lineheight-105: 1.05;
--font-lineheight-110: 1.1;
--font-lineheight-115: 1.15;
--font-lineheight-125: 1.25;
--font-lineheight-150: 1.5;
```

> 与现有 `--font-leading-*` 同值。enki 产物用 `lineheight` 命名空间，故以别名共存，不迁移现有变量名。

### 4.3 字重别名（3 个）

```css
--font-weight-400-regular: 400;
--font-weight-500-medium: 500;
--font-weight-700-bold: 700;
```

> 对齐 CDN 产物的 `--font-weight-*` 命名后缀。

### 4.4 elevation 基础尺寸（22 个）

```css
--size-elevation-blur-100..2200: 0px..80px;      /* 17 个，非等差，见 CDN */
--size-elevation-distance-100..1200: 1px..24px;  /* 12 个，非等差 */
--size-elevation-spread-100..300: 1px..3px;      /* 3 个 */
```

> 命名空间为 `size`（非 Tailwind `--spacing-*` 命名空间），避免干扰间距体系。

### 4.5 elevation 组合值（9 个）

`--style-elevation-1..9` 完全按 CDN 产物的双层 box-shadow 结构（`0 0 blur 0 tint, 0 distance blur 0 tint` 或单层），引用 `--size-elevation-*` 与 `--color-tint-black-25`（已存在于 tokens.css，值 `rgba(0,0,0,0.05)` 与 CDN 一致）。

### 4.6 filter 值（4 个）

```css
--style-filter-lighten-1-hover:  brightness(105%) saturate(105%);
--style-filter-lighten-1-pressed: brightness(108%) saturate(108%);
--style-filter-darken-1-hover:   brightness(95%)  saturate(105%);
--style-filter-darken-1-pressed: brightness(92%)  saturate(108%);
```

## 五、组合类实现（enki.css）

每个组合类以 `@utility` 实现，属性集与 CDN 产物逐字对齐：

```css
/* 示例：CDN 产物（.enki-display-3xl） */
@utility enki-display-3xl {
  letter-spacing: var(--display-3xl-tracking);
  font-size: var(--display-3xl-size);
  font-family: var(--display-3xl-family);
  font-weight: var(--display-3xl-weight);
  line-height: var(--display-3xl-lineheight);
}
@utility enki-display-3xl-strong {
  letter-spacing: var(--display-3xl-tracking);
  font-size: var(--display-3xl-size);
  font-family: var(--display-3xl-family);
  line-height: var(--display-3xl-lineheight);
  font-weight: var(--display-3xl-weightstrong);
}
```

- **display/heading**：`weight` → 500-medium；`strong` → 700-bold；`lineheight` → 125；`tracking` → widest；family → 对应 cjk。
- **body**：`weight` → 400-regular；`medium` → 500-medium；`strong` → 700-bold；`lineheight` → 125；`tracking` → widest；family → cjk-body。
- **button**（6 个）：对齐 CDN 的 `appearance:none; outline:0; cursor:pointer;` + `background-color`/`color` 引用 `--color-btn-*-bg/fg-default`（现已存在于 tokens.css 且命名一致），并带 `:hover`/`:active` filter：
  ```css
  @media (hover: hover) {
    .enki-button-primary:hover { filter: var(--style-filter-lighten-1-hover); }
  }
  ```
  > 因 `@utility` 内无法直接表达该媒体查询换用 Pseudo，采用 CDN 同款的非 @utility 兜底写法（见下）。
- **elevation**（9 个）：`box-shadow: var(--style-elevation-N)`。

### 5.1 button hover 的实现取舍

Tailwind `@utility` 支持 `&:hover`，但 CDN 产物使用 `@media (hover:hover)`，两者语义等价但产物结构不同。为使产物对齐 CDN，button 的 `:hover`/`:active` 过滤器将以普通 CSS 写法追加在 `enki.css` 内（非 `@utility`，因不受按需生成影响，仍直接生效）。

## 六、字体栈全站切换

- `globals.css` 中 `body` 默认字体由 `Arial, "Microsoft YaHei", sans-serif` 切换为 `var(--font-family-cjk-main)`。
- 不引入外部字体文件，纯字体栈声明。

## 七、影响与迁移

| 文件 | 变更 |
|---|---|
| `apps/web/app/(main)/page.tsx` | `heading-3xl` → `enki-heading-3xl`；`body-base` → `enki-body-base` |
| `apps/web/app/components/bottom-tab-bar.tsx` | 无变更（仅用 font-medium + tabbar 色，不受影响） |
| `apps/web/__tests__` | 无断言受字号类影响，不新增测试（组合类为纯 CSS） |
| 现有使用无前缀 `display-*`/`heading-*`/`body-*`/`elevation-shadow-*` 的页面 | 全量扫描改为 `enki-*`（当前仅 `page.tsx`） |

## 八、验证

1. `tsc --noEmit` 通过
2. vitest 全量通过
3. `next build` 无 CSS 警告
4. 产物抽查：`.enki-display-3xl`、`.enki-body-base-strong`、`.enki-button-primary:hover`、`.enki-elevation-5` 已生成；`.display-3xl`（无前缀）不再生成
5. 变量抽查：`--font-family-cjk-main`、`--font-lineheight-125`、`--style-elevation-5`、`--style-filter-lighten-1-hover` 存在于产物