# 可选 callout 样式

初始化不安装 CSS。用户需要视觉定制时，可在自己的 vault 创建 `.obsidian/snippets/vault-colors.css` 并在 Obsidian 中启用。

```css
.callout[data-callout='contradiction'] {
  --callout-color: 209, 105, 105;
  --callout-icon: lucide-alert-triangle;
}
.callout[data-callout='gap'] {
  --callout-color: 230, 170, 70;
  --callout-icon: lucide-search;
}
.callout[data-callout='key-insight'] {
  --callout-color: 80, 160, 210;
  --callout-icon: lucide-lightbulb;
}
.callout[data-callout='stale'] {
  --callout-color: 160, 150, 120;
  --callout-icon: lucide-clock;
}
```

无此文件时可使用标准类型：contradiction → warning，gap → question，key-insight → tip，stale → warning。不要为配色创建新的 entity/concept 内容层，也不要覆盖用户已有主题。
