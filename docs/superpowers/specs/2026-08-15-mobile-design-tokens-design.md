# ec-main 移动端 Design Token 体系设计文档

> 日期：2026-08-15
> 状态：设计已获批准，转入实施

## 一、背景与目标

ec-main 的移动端 Web（`apps/web`，Next.js + Tailwind v4）目前仅使用 shadcn 默认中性色主题（`globals.css` 中的 oklch 变量），缺乏品牌化的设计 token 体系。为支撑移动电商界面的一致性与后续暗色模式，需要建立一套仿 weee-ui 方法论的三层 design token。

**参考来源**：`ec-web-main/vendor/weee-ui/dist/weee/tailwind/` 下的 `tailwind.enki.config.js`、`styles/color.tailwind.js`、`styles/size.tailwind.js`、`styles/font.tailwind.js` 及 `tokens/weee/dist/*.json`。weee-ui 的完整提取报告见下文「附录」章节。

**设计目标**：
1. 三层架构：root 原始色板 → 语义色 → 组件语义
2. 完整落地到 Tailwind v4 CSS-first 的 `@theme`
3. 内建暗色模式（`.dark` 作用域）
4. 命名沿袭 weee-ui 体系，色值为电商场景自定义
5. 与现有 shadcn token 共存，逐步迁移而非一次性替换

## 二、总体架构

### 2.1 三层 token 架构

```
Layer 1  root 色板       → 9 色 × (base/light/dark) × 1-7 阶  = 原始不可复用的纯色
Layer 2  语义色         → primary / secondary / tertiary / success / critical / warning / highlight / pricing / link（别名引用 Layer1）
Layer 3  组件语义       → surface / btn / input / navbar / tabbar / backdrop / promotion（引用 Layer1+Layer2）
```

尺寸/字体独立成轴：`size`（spacing/radius/elevation）与 `font`（size/weight/lineheight/tracking）不参与三层引用，直接落值。

### 2.2 文件组织

```
apps/web/app/design-tokens/
  refer/weee-extract.md      # weee-ui 提取报告（只读追溯）
  tokens.css                 # ★ 唯一事实来源：全部变量的初始值（含 root 色板、语义层、组件层、shade/tint、尺寸）
  semantic.css               # 语义层 + 组件层（@theme inline var 映射，供 bg-*/text-* 等工具类）
  support-classes.css        # 自定义组合工具类（elevation-shadow-*、display-*/heading-*/body-*）
  dark.css                   # .dark 作用域全覆盖变量
apps/web/app/globals.css     # 修改：引入上述文件
```

### 2.3 与现有 shadcn 体系的关系

- **不删除**现有 `--color-primary`、`--background` 等 oklch 变量，避免破坏已有组件。
- 新增 token 统一使用 weee 命名空间变量（`--color-root-*`、`--color-surface-*`、`--color-btn-*` 等）。
- 将部分通用语义（如 `--color-primary-*`）逐步与现有 shadcn `--primary` 对齐，属后续迁移任务，不在本范围。

## 三、颜色体系

### 3.1 Layer 1 — root 原始色板

9 大色系，每色系 `base`（基准）/ `light`（提亮）/ `dark`（压暗）各 7 阶（1 最浅/弱，7 最深/强）：

| 色系 | 变量前缀 | 色相方向 | 移动电商用途 |
|---|---|---|---|
| energy（蓝） | `--color-root-energy-blue-*` | 品牌主蓝 | 主品牌色、链接 |
| flow（青） | `--color-root-flow-teal-*` | 青绿 | 主色辅助、促销氛围 |
| mandarin（蜜柑橙） | `--color-root-mandarin-orange-*` | 鲜明橙 | 价格、促销、加购强调 |
| tomato（番茄红） | `--color-root-tomato-red-*` | 正红 | 危险、强 CTA、价格强调 |
| durian（榴莲黄） | `--color-root-durian-yellow-*` | 亮黄 | 优惠标签、高亮 |
| chive（韭菜绿） | `--color-root-chive-green-*` | 绿 | 成功/确认 |
| jade（翡翠绿） | `--color-root-jade-green-*` | 青绿 | 健康/品质氛围 |
| dragonfruit（火龙果粉） | `--color-root-dragonfruit-pink-*` | 粉紫 | 女性向、温馨 |
| eggplant（茄子紫） | `--color-root-eggplant-purple-*` | 紫 | 会员/VIP 氛围 |

命名格式：`--color-root-{name}-{hue}-{base|light|dark}-{1..7}`

### 3.2 Layer 2 — 语义色

通过 CSS `var()` 别名引用 Layer 1：

- `--color-primary-{1..5}`：主品牌语义（1 主色、2 辅助、3 浅衬、4 白、5 深）
- `--color-secondary-{base|light|dark}-{1..3}`
- `--color-tertiary-{base|light|dark}-{1..5}` + `tertiary-electric`
- `--color-success-{bg|fg|hairline|txt}`、`--color-critical-*`、`--color-warning-*`、`--color-highlight-*`、`--color-pricing-*`
- `--color-link-base-1`

### 3.3 Layer 3 — 组件语义

- `--color-surface-{100..600}`：每个含 `bg` / `fg-default` / `fg-minor` / `hairline`
- `--color-btn-{primary|secondary|tertiary|confirmation|critical|disabled}`：每个含 `bg` / `fg-default` / `fg-minor` / `hairline` / `behavior`
- `--color-input-{100|200}`：含 `bg` / `fg` / `hairline` / `icon` 的 default/active/disabled/critical 态
- `--color-navbar-*`：bg / fg / hairline / divider / logo
- `--color-tabbar-*`：bg / fg / selected / hairline（**新增，替代 weee 的 sidebar**）
- `--color-backdrop-{50|100}`：覆盖层
- `--color-promotion-{100|200|300}`：促销卡
- `--color-tint-{white|black}-{25..1000}`：透明度阶梯（每 25 一阶）
- `--color-shade-{neutral|cool}-{base|light|dark}-{1..7}`：双向灰阶

### 3.4 暗色模式

`.dark` 作用域覆盖 Layer 1+2+3 全量变量为暗色值。机制与 weee-ui `colors.dark.json` / `color.dark.css` 一致：
- light 层的暗色值 ≈ 原 dark 层
- dark 层的暗色值 ≈ 更深一档或原 light
- surface 阶梯反向（100 最暗 → 600 最亮）

## 四、尺寸系统

| 类别 | 变量 | 取值 |
|---|---|---|
| spacing | `--spacing-{0,50,100..2000}` | 步进 100=4px，50=2px；最长 80px |
| radius | `--radius-{100..800}` + `--radius-full` | 2/4/8/12/16/20/24/28/9999px |
| elevation distance | `--elevation-distance-*` | 1..24px |
| elevation blur | `--elevation-blur-*` | 0..80px |
| elevation spread | `--elevation-spread-*` | 1..3px |
| elevation shadow | `--elevation-shadow-{1..9}` | 多影组合，阴影色 `tint-black-25` |

`elevation-shadow-*` 作为自定义工具类（`.elevation-shadow-3`）由 support-classes 提供 shadow。

## 五、字体系统

weee-ui 已提取（三套完整 scale）：

- **字号**：`--font-size-{3xs,2xs,xs,sm,base,lg,xl,2xl...10xl}`，11px → 170px（共 18 级）
- **行高**：`--font-leading-{100,105,110,115,125,150}`（数值 = 倍数 ×1.00..1.50）
- **字重**：`--font-weight-{400,500,600,700,800}`
- **字距**：`--font-tracking-{tightest,tighter,tight,base,wide,wider,widest}`（-0.60..0.60em）

### 组合字体 scale（自定义工具类）

- `display-{sm,lg,xl,2xl,3xl,4xl,5xl}`：促销大标题（use heading 池）
- `heading-{sm,lg,xl,2xl,3xl,4xl,5xl}`：页面/区块标题（medium 默认 + strong 变体）
- `body-{3xs,2xs,xs,sm,base,lg,xl,2xl}`：正文（regular 默认 + strong/medium 变体）

Tailwind 映射：`@theme inline` 把 `font-size/leading/tracking/weight` 映射到 `text-xs/leading-*.` 等标准工具类。

## 六、暗色模式机制

1. `tokens.css` 中 `:root`（亮色）定义全量变量。
2. `dark.css` 中 `.dark` 覆盖同名变量为暗色值。
3. `globals.css` 保留现有 `@custom-variant dark`。
4. 现有 shadcn 组件（`bg-background` 等）不受影响，仍由 oklch 变量驱动。

## 七、验证策略

- `pnpm --filter @ec/web check`（tsc）
- `pnpm --filter @ec/web test`（vitest 现有测试，防回归）
- `pnpm --filter @ec/web build`（确认 Tailwind v4 编译通过）
- 目视：登录页、首页、(main) 布局应用新 token 类名

## 八、范围说明（非目标）

- 不迁移现有 shadcn 组件的颜色到新 token（后续任务）
- 不做 Style Dictionary / JSON 源 → 多平台编译（本任务仅 Tailwind v4 @theme 单平台落地）
- 不涉及 Android/iOS 原生产物

## 附录：weee-ui 提取摘要

参考文件（`ec-web-main/vendor/weee-ui/`）：
- `dist/weee/tailwind/with-vars/tailwind.enki.config.js`：`withEnkiConfig()` 深合并，theme.extend.colors/radius/fontSize/spacing+height+width/letterSpacing/lineHeight；插件注册 font/button/elevation/filter 工具类
- `dist/weee/tailwind/with-vars/styles/color.tailwind.js`：颜色三层结构（primary/secondary/tertiary/shade/root/reserved/surface/btn/tint/link/success/critical/warning/highlight/pricing/atc/navbar/sidebar/backdrop/input/notification/bookmark/product/promo），全部 `var(--color-*)` 引用
- `dist/weee/tailwind/with-vars/styles/size.tailwind.js`：elevation(distance/blur/spread)、spacing(0-2000)、device(desktop/tablet/mobile)、radius(100-800+full)
- `dist/weee/tailwind/with-vars/styles/font.tailwind.js`：size(3xs-10xl)/weight(400-800)/lineheight(100-150)/tracking(7 档)
- `tokens/weee/dist/colors.json`：值引用关系（如 `primary-1 = root.energy.blue.dark.4`）
- `tokens/weee/dist/typography.core.json`：字号 11..170px、字重 Regular..ExtraBold、行高 1..1.5、字距 ±0.6
- `tokens/weee/dist/elevation.json`：elevation 1..9 组合阴影
- `dist/weee/tailwind/with-vars/css/main.latin.css`：字体族（display=Random Grotesque 系、main=Poppins，CJK 兜底 Microsoft YaHei/PingFang SC）
- `dist/weee/tailwind/with-vars/css/color.dark.css`：暗色变量覆盖机制