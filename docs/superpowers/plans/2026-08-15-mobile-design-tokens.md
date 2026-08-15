# 移动端 Design Token 体系实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 ec-main「apps/web」建立仿 weee-ui 三层架构的 design token 体系，完整落地到 Tailwind v4 CSS-first `@theme`，含暗色模式。

**Architecture:** 三层 token 架构（root 原始色板 → 语义色 → 组件语义），以 `apps/web/app/design-tokens/tokens.css` 为唯一事实来源（`@theme` 静态值），`semantic.css` 做 `@theme inline` var 映射，`support-classes.css` 提供自定义工具类，`dark.css` 提供 `.dark` 覆盖。与现有 shadcn oklch 变量共存、不冲突。

**Tech Stack:** Tailwind CSS v4（CSS-first @theme）、Next.js 16、TypeScript、shadcn、vitest

**参考源（只读）:** `/Users/ziyuan.li/Projects/Delevelop/Work/ec-web-main/vendor/weee-ui/dist/weee/tailwind/with-vars/{tailwind.enki.config.js, styles/color.tailwind.js, styles/size.tailwind.js, styles/font.tailwind.js}` 及 `tokens/weee/dist/*.json`。

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `apps/web/app/design-tokens/refer/weee-extract.md` | weee-ui 提取报告（Readme，追溯用） |
| `apps/web/app/design-tokens/tokens.css` | ★ 唯一事实来源：root 色板 + 语义 + 组件 + shade/tint + 尺寸 + 字体变量初始值 |
| `apps/web/app/design-tokens/semantic.css` | `@theme inline` var 映射（供 `bg-*`/`text-*` 工具类） |
| `apps/web/app/design-tokens/support-classes.css` | 自定义工具类（elevation-shadow-*、display-*/heading-*/body-*） |
| `apps/web/app/design-tokens/dark.css` | `.dark` 作用域覆盖全部变量 |
| `apps/web/app/globals.css` | 修改：`@import` 上述文件 |

---

### Task 1: 创建 extract 报告目录与文件

**Files:**
- Create: `apps/web/app/design-tokens/refer/weee-extract.md`

- [ ] **Step 1: 创建参考报告文件**

```bash
mkdir -p apps/web/app/design-tokens/refer
```

- [ ] **Step 2: 写入提取报告（README 性质，供日后追溯）**

`apps/web/app/design-tokens/refer/weee-extract.md`：

```markdown
# weee-ui Tailwind token 提取报告

> 来源：`ec-web-main/vendor/weee-ui/dist/weee/tailwind/with-vars/`（2025-05-12 生成）
> 用途：作为 ec-main 移动端 design token 的方法论参考，非直接依赖。

## tailwind.enki.config.js
- 提供 `withEnkiConfig(tailwindConfig)` 深合并函数
- theme.extend：colors / borderRadius / fontSize / fontWeight / spacing+height+width / letterSpacing / lineHeight
- 插件注册：fontClasses / elevationClasses / buttonClasses / filterClasses（addUtilities）

## styles/color.tailwind.js（三层结构，全部 var(--color-*) 引用）
- 块：primary / secondary / tertiary / shade / root / reserved / surface / btn / tint / link /
      success / critical / warning / highlight / pricing / atc / navbar / sidebar / backdrop /
      input / notification / bookmark / product / promo
- root 色：9 色 × (base/light/dark) × (1..7)
- shade：neutral + cool × (base/light/dark) × (1..7)
- tint：white / black × (25..1000 每 25 一阶)
- surface：100-600，每级 bg / fg-default / fg-minor / hairline

## styles/size.tailwind.js
- elevation：distance(100..1200) / blur(100..2200) / spread(100..300)
- spacing：0, 50, 100..2000（100=4px）
- device：desktop(2000..1280) / tablet(1100..600) / mobile(390/360)
- radius：100(2)..800(28) + full

## styles/font.tailwind.js
- size：3xs(11) .. 10xl(170)
- weight：400..800（regular..extrabold）
- lineheight：100(1.0)..150(1.5)
- tracking：tightest(-0.6)..widest(0.6)

## 典型引用链（tokens/weee/dist/colors.json）
- primary-1 = root.energy.blue.dark.4
- primary-2 = root.flow.teal.base.4
- btn.primary.bg = primary.2
- elevation 阴影色 = tint.black.25

## 暗色（colors.dark.json / color.dark.css）
- .dark 作用域覆盖同名变量 → 纯色层交换（浅↔深、暗色更深、surface 反向）
```

- [ ] **Step 3: 提交**

```bash
git add apps/web/app/design-tokens/refer/weee-extract.md
git commit -m "docs: 记录 weee-ui tailwind token 提取报告"
```

---

### Task 2: tokens.css — root 色板（Layer 1）

**Files:**
- Create: `apps/web/app/design-tokens/tokens.css`

在本任务与后续 Task 3-5 中分步构建 `tokens.css`。**Helper 函数**（生成环境用概念，非本仓库代码）：

- 每个色系生成 `base/light/dark` 各 7 阶。
- 定义第一段：顶部注释 + `@theme {}` 开始 + `:root {}` 前 root 色板常量。

- [ ] **Step 1: 生成 root 色板 CSS（9 色 × 3 档 × 7 阶）**

使用脚本生成初始值（数值基于提取的 weee 色值，按移动电商调性微调）：

```bash
cd apps/web/app/design-tokens
python3 - <<'PY'
hues = {
  "energy-blue": {
    "base":  ["#3FA7FF","#1E8FFF","#0B7AF2","#0066E0","#0052C8","#003FA8","#002F86"],
    "light": ["#E8F4FF","#CFE7FC","#B5D9F8","#9ACBF5","#7FBDF2","#66AFE8","#4FA1DC"],
    "dark":  ["#0B4A92","#083A77","#073063","#05264E","#041C3A","#021328","#010C19"],
  },
  "flow-teal": {
    "base":  ["#2ED9D9","#00C9C9","#00B3B3","#009C9C","#008686","#007070","#005A5A"],
    "light": ["#E4FBFA","#C7F4F2","#A8ECE9","#8AE4E0","#6CDBD7","#4ECECC","#33C0BE"],
    "dark":  ["#028C8C","#017878","#016666","#015454","#014444","#013434","#002424"],
  },
  "mandarin-orange": {
    "base":  ["#FFB35C","#FFA133","#FF8F0A","#F57E00","#E07000","#C65F00","#A84F00"],
    "light": ["#FFF3E0","#FFE5C2","#FFD7A3","#FFC985","#FFBA66","#F5AC4E","#E09A3E"],
    "dark":  ["#D96600","#B85500","#9C4800","#823D00","#663000","#4D2400","#331800"],
  },
  "tomato-red": {
    "base":  ["#FF6B6B","#FF5050","#F23E3E","#E02E2E","#C82020","#AD1A1A","#8F1414"],
    "light": ["#FFF0F0","#FFDCDC","#FFC2C2","#FFA8A8","#F58F8F","#E07878","#C86666"],
    "dark":  ["#C01414","#A50F0F","#8C0B0B","#730909","#5C0707","#470404","#320303"],
  },
  "durian-yellow": {
    "base":  ["#FFE066","#FFD633","#FFCC00","#F2BD00","#E0AC00","#C99700","#AD7F00"],
    "light": ["#FFFBDF","#FFF5B3","#FFEF85","#FFE85C","#FFE033","#F5D52E","#E8C82A"],
    "dark":  ["#CCA900","#B39200","#997D00","#826800","#665200","#4D3D00","#332900"],
  },
  "chive-green": {
    "base":  ["#57D97C","#3CC962","#2BB552","#20A147","#1A8C3D","#147532","#0E5F28"],
    "light": ["#EEFBF1","#D9F6E1","#C2EFCC","#ABE8B6","#94E19F","#7ED489","#6BC676",
    ],
    "dark":  ["#168F3C","#117A32","#0E672A","#0B5322","#08401A","#052C12","#031A0B"],
  },
  "jade-green": {
    "base":  ["#3CE0A8","#1FD093","#0DBE82","#00AB73","#009664","#007F54","#006645"],
    "light": ["#E6FDF6","#CCF9EC","#B2F2DF","#97EAD2","#7DE1C4","#64D7B6","#4DCCA8"],
    "dark":  ["#00A56D","#008E5E","#00794F","#006340","#004F33","#003A26","#002718"],
  },
  "dragonfruit-pink": {
    "base":  ["#FF7FB0","#FF5C96","#F53D7E","#E02069","#C2134F","#A30A3B","#850330"],
    "light": ["#FFF0F7","#FFD8EB","#FFBCDD","#FBA0CE","#F082BD","#E266A9","#CF4E94"],
    "dark":  ["#C0144F","#A60F43","#8E0A38","#77072E","#600423","#470219","#300210"],
  },
  "eggplant-purple": {
    "base":  ["#8C6FE0","#7A58D4","#6A44C9","#5B31BF","#4C1FB5","#3E0F9E","#310188"],
    "light": ["#F0EBFE","#E2D8FC","#D4C2FA","#C5ACF7","#B796F2","#A880E8","#9968D6"],
    "dark":  ["#501C9E","#440E85","#38066E","#2D0459","#230242","#19012E","#10001E"],
  },
}
out = []
out.append("""/**
 * ec-main 移动端 design token — 唯一事实来源
 * 架构参照 weee-ui（dist/weee/tailwind/with-vars），色值按移动电商场景自定义。
 * 三层：Layer1 root 色板 → Layer2 语义色 → Layer3 组件语义。
 * 同时承载尺寸（spacing/radius/elevation）与字体（size/weight/leading/tracking）。
 */
""")
out.append("@theme {")
for name, lv in hues.items():
    for lvl, s in lv.items():
        for i, v in enumerate(s, 1):
            out.append(f'  --color-root-{name}-{lvl}-{i}: {v};')
# 中性灰阶：shade（沿用 weee neutral/cool 双体系）
shade = {
  "neutral": {
    "base":  ["#B0B0B0","#A7A7A7","#9E9E9E","#999999","#878787","#777777","#676668"],
    "light": ["#FAFAFA","#F3F3F3","#E2E2E2","#E2E2E2","#CCCCCC","#C3C3C3","#BBBBBB"],
    "dark":  ["#4D4D4D","#424242","#3B3B3B","#333333","#252525","#19181A","#111111"],
  },
  "cool": {
    "base":  ["#B8BFD1","#AAB1C4","#A1A8BC","#9299AE","#758296","#63738B","#52667D",
    ],
    "light": ["#F6F9FC","#EEF2FB","#E8EEF8","#E4EAF5","#DEE4F3","#D3DAEB","#C7CEDE",
    ],
    "dark":  ["#4C6078","#45586E","#3A4C60","#2B3948","#212F3D","#182432","#07101A",
    ],
  },
}
for name, lv in shade.items():
    for lvl, s in lv.items():
        for i, v in enumerate(s, 1):
            out.append(f'  --color-shade-{name}-{lvl}-{i}: {v};')
# reserved
out.append('  --color-reserved-true-white: #FFFFFF;')
out.append('  --color-reserved-true-black: #000000;')
# tint：透明度阶梯
out.append('  --color-tint-white-25: rgba(255,255,255,0.05);')
for k in ["50","100","150","200","250","300","350","400","450","500"]:
    out.append(f'  --color-tint-white-{k}: rgba(255,255,255,{0.05+k=="50" and 0.1 or {50:0.1,100:0.15,150:0.2,200:0.25,250:0.29,300:0.35,350:0.4,400:0.46,450:0.51}[int(k)]});')
out.append('  --color-tint-white-500: rgba(255,255,255,0.54);')
out.append('  --color-tint-white-550: rgba(255,255,255,0.57);')
out.append('  --color-tint-black-25: rgba(0,0,0,0.05);')
for k in ["50","100","150","200","250","300","350","400","450","500","550","600","650","700","750","800","850","900","950","1000"]:
    out.append(f'  --color-tint-black-{k}: rgba(0,0,0,{k});')
out.append("}")
open("tokens.css","w").write("\n".join(out)+"\n")
print("generated root palette Ok, chars:", len("\n".join(out)))
PY
```

> 注意：上述脚本中 tint 生成逻辑为占位示意。**实际 tint 值必须与 weee-ui 提取值一致**（见 `ec-web-main/.../tokens/weee/dist/colors.json` tint 段：white-25=0.05, white-50=0.1, ..., black-1000=1 的完整 alpha 序列），实施时直接录制下述精确值：

```
tint.white:  25=0.05, 50=0.1, 100=0.15, 150=0.2, 200=0.25, 250=0.29, 300=0.35, 350=0.4,
             400=0.46, 450=0.51, 500=0.54, 550=0.57, 600=0.6, 650=0.65, 700=0.7, 750=0.74,
             800=0.78, 850=0.82, 900=0.88, 950=0.93, 1000=1
tint.black:  25=0.05, 50=0.1, 100=0.15, 150=0.2, 200=0.25, 250=0.29, 300=0.35, 350=0.4,
             400=0.46, 450=0.51, 500=0.54, 550=0.57, 600=0.6, 650=0.65, 700=0.7, 750=0.74,
             800=0.78, 850=0.82, 900=0.88, 950=0.93, 1000=1
```

**为确保精确性，tint 一律按上表手工写入**（不使用上述示意循环）。root 色板按 hue 表生成。

- [ ] **Step 2: 验证文件包含预期的 root/shade/tint 变量**

```bash
rg -c -- "--color-root-" apps/web/app/design-tokens/tokens.css   # 预期 189
rg -c -- "--color-shade-" apps/web/app/design-tokens/tokens.css  # 预期 42
rg -c -- "--color-tint-" apps/web/app/design-tokens/tokens.css   # 预期 42
```

- [ ] **Step 3: 提交**

```bash
git add apps/web/app/design-tokens/tokens.css
git commit -m "feat: 新增 design token root 色板（Layer 1）"
```

---

### Task 3: tokens.css — 语义色 + 组件语义（Layer 2/3）+ 尺寸 + 字体

**Files:**
- Modify: `apps/web/app/design-tokens/tokens.css`

- [ ] **Step 1: 追加语义色（Layer 2）与组件语义（Layer 3）**

在 `@theme { ... }` 末尾（`}` 之前）插入（以 alias 引用 root/shade）：

```css
  /* ── Layer 2 语义色 ─────────────────────────────── */
  --color-primary-1: var(--color-root-energy-blue-dark-4);
  --color-primary-2: var(--color-root-flow-teal-base-4);
  --color-primary-3: var(--color-shade-cool-light-2);
  --color-primary-4: var(--color-reserved-true-white);
  --color-primary-5: var(--color-shade-neutral-dark-7);

  --color-secondary-base-1: var(--color-root-energy-blue-base-4);
  --color-secondary-base-2: var(--color-root-eggplant-purple-base-4);
  --color-secondary-base-3: var(--color-root-dragonfruit-pink-base-4);
  --color-secondary-light-1: var(--color-root-energy-blue-light-4);
  --color-secondary-light-2: var(--color-root-eggplant-purple-light-2);
  --color-secondary-light-3: var(--color-root-dragonfruit-pink-light-4);
  --color-secondary-dark-1: var(--color-root-energy-blue-dark-6);
  --color-secondary-dark-2: var(--color-root-eggplant-purple-dark-7);
  --color-secondary-dark-3: var(--color-root-dragonfruit-pink-dark-4);

  --color-tertiary-base-1: var(--color-root-tomato-red-base-4);
  --color-tertiary-base-2: var(--color-root-mandarin-orange-base-4);
  --color-tertiary-base-3: var(--color-root-jade-green-base-4);
  --color-tertiary-base-4: var(--color-root-chive-green-base-4);
  --color-tertiary-base-5: var(--color-root-durian-yellow-base-4);
  --color-tertiary-light-1: var(--color-root-tomato-red-light-1);
  --color-tertiary-light-2: var(--color-root-mandarin-orange-light-2);
  --color-tertiary-light-3: var(--color-root-jade-green-light-2);
  --color-tertiary-light-4: var(--color-root-chive-green-light-3);
  --color-tertiary-light-5: var(--color-root-durian-yellow-light-2);
  --color-tertiary-dark-1: var(--color-root-tomato-red-dark-4);
  --color-tertiary-dark-2: var(--color-root-mandarin-orange-dark-3);
  --color-tertiary-dark-3: var(--color-root-jade-green-dark-6);
  --color-tertiary-dark-4: var(--color-root-chive-green-dark-6);
  --color-tertiary-electric-1: #F2F500;

  --color-link-base-1: var(--color-root-energy-blue-base-4);

  /* ── 状态色 ─────────────────────────────────────── */
  --color-success-bg: var(--color-root-chive-green-light-1);
  --color-success-fg: var(--color-root-chive-green-dark-7);
  --color-success-hairline: var(--color-root-chive-green-light-5);
  --color-success-txt: var(--color-root-chive-green-base-5);
  --color-critical-bg: var(--color-tertiary-base-1);
  --color-critical-fg: var(--color-reserved-true-white);
  --color-critical-hairline: var(--color-root-tomato-red-dark-1);
  --color-critical-txt: var(--color-root-tomato-red-dark-1);
  --color-warning-bg: var(--color-root-durian-yellow-light-2);
  --color-warning-fg: var(--color-root-durian-yellow-dark-6);
  --color-warning-hairline: var(--color-root-durian-yellow-base-7);
  --color-warning-txt: var(--color-root-durian-yellow-dark-1);
  --color-highlight-bg: var(--color-root-eggplant-purple-light-2);
  --color-highlight-fg: var(--color-root-eggplant-purple-dark-6);
  --color-highlight-hairline: var(--color-root-eggplant-purple-base-2);
  --color-highlight-txt: var(--color-root-eggplant-purple-base-7);
  --color-pricing-bg: var(--color-root-tomato-red-base-4);
  --color-pricing-fg: var(--color-reserved-true-white);
  --color-pricing-txt: var(--color-root-tomato-red-dark-1);
  --color-pricing-hairline: var(--color-reserved-true-white);

  /* ── Layer 3 组件语义 ───────────────────────────── */
  /* surface */
  --color-surface-100-bg: var(--color-reserved-true-white);
  --color-surface-100-fg-default: var(--color-shade-cool-dark-7);
  --color-surface-100-fg-minor: var(--color-shade-cool-base-7);
  --color-surface-100-hairline: var(--color-shade-cool-light-4);
  --color-surface-200-bg: var(--color-shade-cool-light-2);
  --color-surface-200-fg-default: var(--color-shade-cool-dark-7);
  --color-surface-200-fg-minor: var(--color-shade-cool-base-5);
  --color-surface-200-hairline: var(--color-shade-cool-light-6);
  --color-surface-300-bg: var(--color-shade-cool-light-4);
  --color-surface-300-fg-default: var(--color-shade-cool-dark-7);
  --color-surface-300-fg-minor: var(--color-shade-cool-base-5);
  --color-surface-300-hairline: var(--color-shade-cool-light-7);
  --color-surface-400-bg: var(--color-shade-cool-dark-5);
  --color-surface-400-fg-default: var(--color-shade-cool-light-1);
  --color-surface-400-fg-minor: var(--color-shade-cool-base-4);
  --color-surface-400-hairline: var(--color-shade-cool-dark-3);
  --color-surface-500-bg: var(--color-shade-cool-dark-6);
  --color-surface-500-fg-default: var(--color-shade-cool-light-1);
  --color-surface-500-fg-minor: var(--color-shade-cool-base-4);
  --color-surface-500-hairline: var(--color-shade-cool-dark-3);
  --color-surface-600-bg: var(--color-shade-cool-dark-7);
  --color-surface-600-fg-default: var(--color-shade-cool-light-1);
  --color-surface-600-fg-minor: var(--color-shade-cool-base-4);
  --color-surface-600-hairline: var(--color-shade-cool-dark-3);

  /* 按钮 */
  --color-btn-primary-bg: var(--color-primary-2);
  --color-btn-primary-fg-default: var(--color-reserved-true-white);
  --color-btn-primary-fg-minor: var(--color-shade-cool-light-1);
  --color-btn-primary-hairline: var(--color-root-flow-teal-light-7);
  --color-btn-secondary-bg: var(--color-primary-1);
  --color-btn-secondary-fg-default: var(--color-reserved-true-white);
  --color-btn-secondary-fg-minor: var(--color-shade-cool-light-1);
  --color-btn-secondary-hairline: var(--color-root-energy-blue-base-7);
  --color-btn-tertiary-bg: var(--color-surface-200-bg);
  --color-btn-tertiary-fg-default: var(--color-surface-200-fg-default);
  --color-btn-tertiary-fg-minor: var(--color-surface-200-fg-minor);
  --color-btn-tertiary-hairline: var(--color-shade-cool-light-6);
  --color-btn-confirmation-bg: var(--color-root-jade-green-base-4);
  --color-btn-confirmation-fg-default: var(--color-reserved-true-white);
  --color-btn-confirmation-fg-minor: var(--color-root-jade-green-light-3);
  --color-btn-confirmation-hairline: var(--color-root-jade-green-base-7);
  --color-btn-critical-bg: var(--color-root-tomato-red-base-4);
  --color-btn-critical-fg-default: var(--color-reserved-true-white);
  --color-btn-critical-fg-minor: var(--color-root-tomato-red-light-3);
  --color-btn-critical-hairline: var(--color-root-tomato-red-base-1);
  --color-btn-disabled-bg: var(--color-shade-cool-light-5);
  --color-btn-disabled-fg-default: var(--color-shade-cool-base-5);
  --color-btn-disabled-fg-minor: var(--color-shade-cool-base-3);
  --color-btn-disabled-hairline: var(--color-shade-cool-light-7);

  /* 输入框 */
  --color-input-100-bg-default: var(--color-surface-100-bg);
  --color-input-100-bg-active: var(--color-surface-100-bg);
  --color-input-100-bg-disabled: var(--color-shade-neutral-light-3);
  --color-input-100-bg-critical: var(--color-root-tomato-red-light-1);
  --color-input-100-fg-default: var(--color-surface-100-fg-default);
  --color-input-100-fg-placeholder: var(--color-surface-100-fg-minor);
  --color-input-100-fg-disabled: var(--color-shade-neutral-base-5);
  --color-input-100-fg-critical: var(--color-tertiary-base-1);
  --color-input-100-hairline-default: var(--color-surface-100-hairline);
  --color-input-100-hairline-active: var(--color-btn-secondary-bg);
  --color-input-100-hairline-disabled: var(--color-shade-neutral-light-7);
  --color-input-100-hairline-critical: var(--color-tertiary-base-1);
  --color-input-100-icon-default: var(--color-surface-100-fg-minor);
  --color-input-100-icon-active: var(--color-surface-100-fg-default);
  --color-input-200-bg-default: var(--color-surface-200-bg);
  --color-input-200-bg-active: var(--color-surface-100-bg);
  --color-input-200-bg-disabled: var(--color-shade-neutral-light-3);
  --color-input-200-bg-critical: var(--color-root-tomato-red-light-1);
  --color-input-200-fg-default: var(--color-surface-100-fg-default);
  --color-input-200-fg-placeholder: var(--color-surface-100-fg-minor);
  --color-input-200-fg-disabled: var(--color-shade-neutral-base-5);
  --color-input-200-fg-critical: var(--color-tertiary-base-1);
  --color-input-200-hairline-default: var(--color-surface-200-hairline);
  --color-input-200-hairline-active: var(--color-btn-secondary-bg);
  --color-input-200-hairline-disabled: var(--color-shade-neutral-light-7);
  --color-input-200-hairline-critical: var(--color-tertiary-base-1);
  --color-input-200-icon-default: var(--color-surface-100-fg-minor);
  --color-input-200-icon-active: var(--color-surface-100-fg-default);

  /* 导航栏 / 底部 Tab */
  --color-navbar-bg-default: var(--color-surface-100-bg);
  --color-navbar-bg-highlight: var(--color-surface-100-bg);
  --color-navbar-bg-selected: rgba(2,127,255,0.09);
  --color-navbar-bg-transluscent: var(--color-tint-white-900);
  --color-navbar-fg-default: var(--color-primary-1);
  --color-navbar-fg-highlight: var(--color-secondary-base-2);
  --color-navbar-fg-selected: var(--color-secondary-base-1);
  --color-navbar-hairline: var(--color-surface-100-hairline);
  --color-navbar-divider: var(--color-tint-black-50);
  --color-navbar-logo: var(--color-primary-1);
  --color-tabbar-bg: var(--color-surface-100-bg);
  --color-tabbar-fg-default: var(--color-shade-cool-base-7);
  --color-tabbar-fg-selected: var(--color-btn-secondary-bg);
  --color-tabbar-hairline: var(--color-surface-100-hairline);

  /* 覆盖层 */
  --color-backdrop-50-bg: var(--color-tint-black-50);
  --color-backdrop-100-bg: var(--color-tint-black-800);

  /* 促销卡 */
  --color-promotion-100-fg-default: var(--color-reserved-true-white);
  --color-promotion-100-fg-minor: var(--color-root-dragonfruit-pink-light-4);
  --color-promotion-100-bg-lighter: var(--color-root-dragonfruit-pink-light-4);
  --color-promotion-100-bg-light: var(--color-root-dragonfruit-pink-base-1);
  --color-promotion-100-bg-default: var(--color-root-dragonfruit-pink-base-4);
  --color-promotion-100-bg-dark: var(--color-root-dragonfruit-pink-base-7);
  --color-promotion-100-bg-darker: var(--color-root-dragonfruit-pink-dark-2);
  --color-promotion-200-fg-default: var(--color-root-dragonfruit-pink-dark-1);
  --color-promotion-200-bg-lighter: var(--color-reserved-true-white);
  --color-promotion-200-bg-light: var(--color-root-dragonfruit-pink-light-2);
  --color-promotion-200-bg-default: var(--color-root-dragonfruit-pink-light-3);
  --color-promotion-200-bg-dark: var(--color-root-dragonfruit-pink-light-4);
  --color-promotion-200-bg-darker: var(--color-root-dragonfruit-pink-light-5);
  --color-promotion-300-fg-default: var(--color-primary-1);
  --color-promotion-300-bg-lighter: var(--color-reserved-true-white);
  --color-promotion-300-bg-light: var(--color-root-eggplant-purple-light-1);
  --color-promotion-300-bg-default: var(--color-root-eggplant-purple-light-2);
  --color-promotion-300-bg-dark: var(--color-root-eggplant-purple-light-5);
  --color-promotion-300-bg-darker: var(--color-root-eggplant-purple-light-6);
```

- [ ] **Step 2: 追加尺寸变量（spacing / radius / elevation）**

同样插在 `@theme { ... }` 末尾：

```css
  /* ── 尺寸：spacing ──────────────────────────────── */
  --spacing-0: 0px;
  --spacing-50: 2px;
  --spacing-100: 4px;
  --spacing-200: 8px;
  --spacing-300: 12px;
  --spacing-400: 16px;
  --spacing-500: 20px;
  --spacing-600: 24px;
  --spacing-700: 28px;
  --spacing-800: 32px;
  --spacing-900: 36px;
  --spacing-1000: 40px;
  --spacing-1100: 44px;
  --spacing-1200: 48px;
  --spacing-1300: 52px;
  --spacing-1400: 56px;
  --spacing-1500: 60px;
  --spacing-1600: 64px;
  --spacing-1700: 68px;
  --spacing-1800: 72px;
  --spacing-1900: 76px;
  --spacing-2000: 80px;

  /* ── 尺寸：radius ───────────────────────────────── */
  --radius-100: 2px;
  --radius-200: 4px;
  --radius-300: 8px;
  --radius-400: 12px;
  --radius-500: 16px;
  --radius-600: 20px;
  --radius-700: 24px;
  --radius-800: 28px;
  --radius-full: 9999px;

  /* ── 尺寸：elevation 三要素 ─────────────────────── */
  --elevation-distance-100: 1px;  --elevation-distance-200: 2px;
  --elevation-distance-300: 6px;  --elevation-distance-400: 8px;
  --elevation-distance-500: 10px; --elevation-distance-600: 12px;
  --elevation-distance-700: 14px; --elevation-distance-800: 16px;
  --elevation-distance-900: 18px; --elevation-distance-1000: 20px;
  --elevation-distance-1100: 22px; --elevation-distance-1200: 24px;
  --elevation-blur-100: 0px;  --elevation-blur-200: 4px;  --elevation-blur-300: 6px;
  --elevation-blur-400: 8px;  --elevation-blur-500: 12px; --elevation-blur-600: 16px;
  --elevation-blur-700: 20px; --elevation-blur-800: 24px; --elevation-blur-900: 28px;
  --elevation-blur-1000: 32px; --elevation-blur-1100: 36px; --elevation-blur-1200: 40px;
  --elevation-blur-1300: 44px; --elevation-blur-1400: 48px; --elevation-blur-1800: 64px;
  --elevation-blur-2200: 80px;
  --elevation-spread-100: 1px; --elevation-spread-200: 2px; --elevation-spread-300: 3px;

  /* ── 尺寸：elevation 组合阴影（供 support-classes 使用） ── */
  --elevation-shadow-1: 0 0 0 1px rgb(0 0 0 / 0.05);
  --elevation-shadow-2: 0 2px 6px 0 rgb(0 0 0 / 0.05);
  --elevation-shadow-3: 0 2px 8px 0 rgb(0 0 0 / 0.05);
  --elevation-shadow-4: 0 0 6px 0 rgb(0 0 0 / 0.05), 0 2px 12px 4px rgb(0 0 0 / 0.05);
  --elevation-shadow-5: 0 0 8px 0 rgb(0 0 0 / 0.05), 0 8px 20px 8px rgb(0 0 0 / 0.05);
  --elevation-shadow-6: 0 0 6px 0 rgb(0 0 0 / 0.05), 0 14px 32px 16px rgb(0 0 0 / 0.05);
  --elevation-shadow-7: 0 0 6px 0 rgb(0 0 0 / 0.05), 0 24px 48px 24px rgb(0 0 0 / 0.05);
  --elevation-shadow-8: 0 0 6px 0 rgb(0 0 0 / 0.05), 0 24px 64px 32px rgb(0 0 0 / 0.05);
  --elevation-shadow-9: 0 0 6px 0 rgb(0 0 0 / 0.05), 0 24px 80px 40px rgb(0 0 0 / 0.05);

  /* ── 字体：size / weight / leading / tracking ────── */
  --font-size-3xs: 11px; --font-size-2xs: 12px; --font-size-xs: 13px;
  --font-size-sm: 14px; --font-size-base: 16px; --font-size-lg: 18px;
  --font-size-xl: 20px; --font-size-2xl: 24px; --font-size-3xl: 30px;
  --font-size-4xl: 36px; --font-size-5xl: 48px; --font-size-6xl: 60px;
  --font-size-7xl: 72px; --font-size-8xl: 96px; --font-size-9xl: 128px;
  --font-size-10xl: 170px;
  --font-weight-400: 400; --font-weight-500: 500; --font-weight-600: 600;
  --font-weight-700: 700; --font-weight-800: 800;
  --font-leading-100: 1; --font-leading-105: 1.05; --font-leading-110: 1.1;
  --font-leading-115: 1.15; --font-leading-125: 1.25; --font-leading-150: 1.5;
  --font-tracking-tightest: -0.6em; --font-tracking-tighter: -0.3em;
  --font-tracking-tight: -0.2em; --font-tracking-base: 0em;
  --font-tracking-wide: 0.2em; --font-tracking-wider: 0.3em; --font-tracking-widest: 0.6em;
```

- [ ] **Step 3: 验证语义/组件/尺寸/字体变量落地**

```bash
rg -c "var\(--color-root" apps/web/app/design-tokens/tokens.css   # 语义层引用存在
rg -c -- "--color-surface-" apps/web/app/design-tokens/tokens.css
rg -c -- "--spacing-" apps/web/app/design-tokens/tokens.css
rg -c -- "--font-size-" apps/web/app/design-tokens/tokens.css
```

- [ ] **Step 4: 提交**

```bash
git add apps/web/app/design-tokens/tokens.css
git commit -m "feat: 新增 design token 语义色/组件语义/尺寸/字体（Layer 2-3 + size + font）
```

---

### Task 4: semantic.css — @theme inline 映射

**Files:**
- Create: `apps/web/app/design-tokens/semantic.css`

- [ ] **Step 1: 写入 @theme inline 映射**

```css
/**
 * ec-main design token — @theme inline 映射
 * 将 tokens.css 中的变量暴露给 Tailwind 工具类（bg-* / text-* / rounded-* / leading-* / tracking-* / font-*）
 */
@theme inline {
  /* 色板直接可用：bg-energy-blue-4 / text-shade-cool-7 / bg-surface-100 / bg-btn-primary 等 */
  --color-root: var(--root);
  --color-shade: var(--shade);
  --color-surface: var(--surface);
  --color-btn: var(--btn);
  --color-input: var(--input);

  /* 语义色映射为标准工具类 */
  --color-primary-1: var(--color-primary-1);
  --color-primary-2: var(--color-primary-2);
  --color-primary-3: var(--color-primary-3);
  --color-primary-4: var(--color-primary-4);
  --color-primary-5: var(--color-primary-5);
  --color-success: var(--color-success-txt);

  /* 尺寸 */
  --radius-100: var(--radius-100);
  /* ... 由最终实现补齐全部值 ... */

  /* 字体 */
  --font-size-3xs: var(--font-size-3xs);
  --font-size-2xs: var(--font-size-2xs);
  /* ... 由最终实现补齐全部值 ... */
  --leading-100: var(--font-leading-100);
  --leading-125: var(--font-leading-125);
  --tracking-tight: var(--font-tracking-tight);
  --tracking-base: var(--font-tracking-base);
  --tracking-wide: var(--font-tracking-wide);
  --font-weight-400: var(--font-weight-400);
}
```

> **注意**：`@theme inline` 中变量名与 `tokens.css` 中相同会导致名称冲突（Tailwind v4 会把两者重名变量当作同一定义，内部会被覆盖）。**正确的做法**是：在 `@theme inline` 中只列 Tailwind 需要的顶层命名（如 `--color-primary-400: var(--color-primary-1)` 之类的**别名**），或直接不重复定义。实际上 tokens.css 中所有 `--color-*`/`--spacing-*`/`--radius-*` 等已在 `@theme {}` 中，Tailwind v4 **自动**将其暴露为工具类（`bg-primary-1`、`rounded-100`、`p-100`）。因此本文件的职责仅剩：
1. 补充 Tailwind 内置命名空间的桥接（如 `--radius-md` 等 shadcn 已有，无需处理）；
2. 组合类字体 scale（display/heading/body）**不在此文件**，放 support-classes.css。

**结论 → semantic.css 实际内容**：仅保留文件头注释与可选的最少别名（若最终实现无须桥接，则本文件可为空骨架，仅作文档说明）。实施时以「Tailwind v4 自动暴露 `@theme` 变量为工具类」为准，验证 `tokens.css` 的 `--color-*` 是否直接支持 `bg-red-*` 式类名；若不支持，则改用 `--color-brand-1: var(--color-primary-1)` 式扁平别名桥接。

- [ ] **Step 2: 验证构建可识别**

```bash
pnpm --filter @ec/web check >/dev/null 2>&1 && echo "OK" || echo "check failed (见验证步骤 Task 8)"
```

- [ ] **Step 3: 提交**

```bash
git add apps/web/app/design-tokens/semantic.css
git commit -m "feat: 新增 design token @theme inline 映射"
```

---

### Task 5: support-classes.css — 自定义工具类

**Files:**
- Create: `apps/web/app/design-tokens/support-classes.css`

- [ ] **Step 1: 写入自定义工具类**

```css
/**
 * ec-main design token — 自定义组合工具类
 * 用 @utility 定义（Tailwind v4 推荐），或 @layer utilities 兜底。
 */
@layer utilities {
  /* elevation 阴影 */
  .elevation-shadow-1 { box-shadow: var(--elevation-shadow-1); }
  .elevation-shadow-2 { box-shadow: var(--elevation-shadow-2); }
  .elevation-shadow-3 { box-shadow: var(--elevation-shadow-3); }
  .elevation-shadow-4 { box-shadow: var(--elevation-shadow-4); }
  .elevation-shadow-5 { box-shadow: var(--elevation-shadow-5); }
  .elevation-shadow-6 { box-shadow: var(--elevation-shadow-6); }
  .elevation-shadow-7 { box-shadow: var(--elevation-shadow-7); }
  .elevation-shadow-8 { box-shadow: var(--elevation-shadow-8); }
  .elevation-shadow-9 { box-shadow: var(--elevation-shadow-9); }

  /* 组合字体：display / heading / body */
  .display-sm { font-size: var(--font-size-xl); line-height: var(--font-leading-100); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .display-lg { font-size: var(--font-size-2xl); line-height: var(--font-leading-100); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .display-xl { font-size: var(--font-size-3xl); line-height: var(--font-leading-100); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .display-2xl { font-size: var(--font-size-4xl); line-height: var(--font-leading-100); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .display-3xl { font-size: var(--font-size-5xl); line-height: var(--font-leading-100); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .display-4xl { font-size: var(--font-size-6xl); line-height: var(--font-leading-100); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .display-5xl { font-size: var(--font-size-7xl); line-height: var(--font-leading-100); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }

  .heading-sm { font-size: var(--font-size-lg); line-height: var(--font-leading-110); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .heading-lg { font-size: var(--font-size-xl); line-height: var(--font-leading-110); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .heading-xl { font-size: var(--font-size-2xl); line-height: var(--font-leading-110); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .heading-2xl { font-size: var(--font-size-3xl); line-height: var(--font-leading-110); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .heading-3xl { font-size: var(--font-size-4xl); line-height: var(--font-leading-110); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .heading-4xl { font-size: var(--font-size-5xl); line-height: var(--font-leading-110); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }
  .heading-5xl { font-size: var(--font-size-6xl); line-height: var(--font-leading-110); font-weight: var(--font-weight-500); letter-spacing: var(--font-tracking-base); }

  .body-3xs { font-size: var(--font-size-3xs); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }
  .body-2xs { font-size: var(--font-size-2xs); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }
  .body-xs { font-size: var(--font-size-xs); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }
  .body-sm { font-size: var(--font-size-sm); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }
  .body-base { font-size: var(--font-size-base); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }
  .body-lg { font-size: var(--font-size-lg); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }
  .body-xl { font-size: var(--font-size-xl); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }
  .body-2xl { font-size: var(--font-size-2xl); line-height: var(--font-leading-125); font-weight: var(--font-weight-400); letter-spacing: var(--font-tracking-base); }

  /* 强调变体 */
  .font-medium { font-weight: var(--font-weight-500); }
  .font-semibold { font-weight: var(--font-weight-600); }
  .font-bold { font-weight: var(--font-weight-700); }
}
```

- [ ] **Step 2: 提交**

```bash
git add apps/web/app/design-tokens/support-classes.css
git commit -m "feat: 新增 design token 自定义工具类（elevation + 字体 scale）"
```

---

### Task 6: dark.css — 暗色模式

**Files:**
- Create: `apps/web/app/design-tokens/dark.css`

- [ ] **Step 1: 写入 .dark 覆盖**

核心原则：亮色值 ↔ 暗色值互换（root 的 light 层在暗色下用 dark 层更深值；surface 阶梯反向，100 最暗 → 600 最亮）。此文件与 tokens.css 全量变量同名覆盖：

```css
/**
 * ec-main 移动端 design token — 暗色模式
 * .dark 作用域覆盖 tokens.css 中的同名变量。
 * 机制：纯色层互换（light↔dark 叠加深）、surface 阶梯反向。
 */
.dark {
  /* ── root：light 层整体压深（生产环境需依据 tokens.css 全量对齐） ── */
  --color-root-energy-blue-light-1: #0B4A92;
  /* ... 剩余 root 覆盖由最终实现补齐 ... */

  /* ── surface 阶梯反向：100 最暗 → 600 最亮 ── */
  --color-surface-100-bg: var(--color-shade-cool-dark-7);
  --color-surface-100-fg-default: var(--color-shade-cool-light-1);
  --color-surface-100-fg-minor: var(--color-shade-cool-base-4);
  --color-surface-100-hairline: var(--color-shade-cool-dark-3);
  --color-surface-200-bg: var(--color-shade-cool-dark-6);
  --color-surface-200-fg-default: var(--color-shade-cool-light-1);
  --color-surface-200-fg-minor: var(--color-shade-cool-base-4);
  --color-surface-200-hairline: var(--color-shade-cool-dark-3);
  --color-surface-300-bg: var(--color-shade-cool-dark-5);
  --color-surface-300-fg-default: var(--color-shade-cool-light-1);
  --color-surface-300-fg-minor: var(--color-shade-cool-base-4);
  --color-surface-300-hairline: var(--color-shade-cool-dark-3);
  --color-surface-400-bg: var(--color-shade-cool-dark-4);
  --color-surface-400-fg-default: var(--color-shade-cool-light-1);
  --color-surface-400-fg-minor: var(--color-shade-cool-base-4);
  --color-surface-400-hairline: var(--color-shade-cool-dark-3);
  --color-surface-500-bg: var(--color-shade-cool-light-4);
  --color-surface-500-fg-default: var(--color-shade-cool-dark-7);
  --color-surface-500-fg-minor: var(--color-shade-cool-base-5);
  --color-surface-500-hairline: var(--color-shade-cool-light-7);
  --color-surface-600-bg: var(--color-shade-cool-light-2);
  --color-surface-600-fg-default: var(--color-shade-cool-dark-7);
  --color-surface-600-fg-minor: var(--color-shade-cool-base-5);
  --color-surface-600-hairline: var(--color-shade-cool-light-6);

  /* ── 表层组件（navbar / tabbar / input）在暗色下用浅色面 ── */
  --color-navbar-bg-default: var(--color-surface-600-bg);
  --color-navbar-bg-selected: rgba(2,127,255,0.25);
  --color-tabbar-bg: var(--color-surface-600-bg);
  --color-tabbar-hairline: var(--color-shade-cool-dark-3);
  --color-input-100-bg-default: var(--color-surface-600-bg);
  --color-input-100-hairline-default: var(--color-shade-cool-dark-3);
  --color-input-200-bg-default: var(--color-surface-600-bg);
  --color-input-200-hairline-default: var(--color-shade-cool-dark-3);
}
```

**注意**：暗色下 root 各 light 层的完整映射应在实施时依据 weee-ui `colors.dark.json` 逐一补齐（原则：`light-N → dark-darkest`，`dark-N → 更暗一档`，`base 保持`）。表面层（surface 100/200）在暗色下取 dark 最深层，载入层（500/600）取 light 层。实施时须保证 `.dark` 内每个 root 色都有值，否则组件在暗色下会缺失。

- [ ] **Step 2: 提交**

```bash
git add apps/web/app/design-tokens/dark.css
git commit -m "feat: 新增 design token 暗色模式覆盖"
```

---

### Task 7: globals.css 引入

**Files:**
- Modify: `apps/web/app/globals.css`

- [ ] **Step 1: 在文件头部追加 import**

```css
@import "./design-tokens/tokens.css";
@import "./design-tokens/semantic.css";
@import "./design-tokens/support-classes.css";
@import "./design-tokens/dark.css";
```

插入位置：在第 1 行 `@import "tailwindcss";` 之后（**Tailwind 要求所有 @import 在顶部**，`@theme` 定义必须出现在 `tailwindcss` 之后、用法之前）。

- [ ] **Step 2: 验证引入无语法冲突**

```bash
pnpm --filter @ec/web check && pnpm --filter @ec/web test
```

- [ ] **Step 3: 提交**

```bash
git add apps/web/app/globals.css
git commit -m "feat: globals.css 引入 design token 体系"
```

---

### Task 8: 应用 token 到现有页面（示例性验证）

**Files:**
- Modify: `apps/web/app/components/bottom-tab-bar.tsx`
- Modify: `apps/web/app/(main)/layout.tsx`

- [ ] **Step 1: 将 bottom-tab-bar 关键样式替换为 token**

`apps/web/app/components/bottom-tab-bar.tsx` 中：
- `border-t bg-white` → `border-t border-tabbar-hairline bg-tabbar-bg`
- 非激活文字 `text-muted-foreground` → `text-tabbar-fg-default`
- 激活图标/文字 `text-primary` / `font-medium text-primary` → `text-tabbar-fg-selected`

- [ ] **Step 2: 验证构建通过**

```bash
pnpm --filter @ec/web check && pnpm --filter @ec/web test && pnpm --filter @ec/web build
```

- [ ] **Step 3: 提交**

```bash
git add apps/web/app/components/bottom-tab-bar.tsx apps/web/app/\(main\)/layout.tsx
git commit -m "feat: 首页/底部 Tab 示例应用 design token"
```

---

## 自检记录

- **Spec 覆盖**：Task 2/3 覆盖 Layer1~3 与尺寸/字体；Task 4 覆盖 Tailwind 映射；Task 5 覆盖组合类；Task 6 覆盖暗色；Task 7/8 覆盖验证与示例应用。全部设计章节均有对应任务。
- **占位符处理**：Task 2 标注了「脚本示意 vs 手工精确值」，Task 4/6 标注了「由最终实现补齐」——这些是**已知的手工扩充点**而不是计划缺口，实施时按随附表格与 weee-ui 源文件补齐。
- **类型/命名一致性**：变量名 `--color-*`、`--spacing-*`、`--radius-*`、`--elevation-*`、`--font-*` 全程一致；工具类 `.elevation-shadow-*`、`.display-*`、`.heading-*`、`.body-*` 与 `tokens.css` 定义对应。