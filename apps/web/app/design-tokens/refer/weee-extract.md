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
- `.dark` 作用域覆盖语义/组件变量（primary/secondary/tertiary/surface/btn/input/navbar 等）
- root 色板在暗色下基本保持不变；变化集中在 Layer2/3 映射反向
- surface 阶梯反向：100 最暗 → 600 最亮
- 组件态（input/bg-disabled、btn/disabled 等）改用更深/更浅档