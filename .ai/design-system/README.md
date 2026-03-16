# Design System — 设计规范体系

> 本目录包含项目的完整设计规范。AI 在生成任何前端页面时会自动读取并遵循这些规范，确保全项目视觉统一。

## 目录结构

```
.ai/design-system/
  ├── tokens.json          # Design Tokens — 颜色、间距、字号、圆角、阴影的精确数值
  ├── brand.md             # 品牌视觉规范 — 风格定位、色彩原则、设计禁区
  ├── components.md        # 组件设计规范 — 按钮、表格、表单、卡片等使用规范
  ├── pages.md             # 页面模板规范 — 5 种标准页面的布局结构
  └── references/          # 参考截图 — 设计稿截图供 AI 参考风格
      └── README.md        # 放图指南
```

## 怎么用

### 有设计师的团队

1. **在 Figma 出设计稿** — 完成关键页面设计
2. **导出 Design Tokens** — 用 [Figma Tokens](https://www.figma.com/community/plugin/843461159747178978) 插件导出 JSON，替换 `tokens.json`；或手动填写
3. **截关键页面图** — 导出 4-6 张关键页面截图（1440px 宽，PNG），放入 `references/` 目录
4. **写品牌描述** — 根据设计语言更新 `brand.md` 中的风格定位和设计原则
5. **AI 自动遵循** — 之后所有 AI 生成的页面都会参考这些规范

### 没有设计师

**直接用就行。** 内置的默认 tokens + brand + pages 模板已经是一套完整的**企业级中台风格**（基于 Ant Design 蓝色企业风），小白不做任何修改也能产出风格统一、符合规范的页面。

## 文件说明

| 文件 | AI 怎么用 | 谁来维护 |
|------|----------|---------|
| `tokens.json` | 写代码时引用精确的颜色值、间距值、字号 | 设计师导出 / 开发者手填 |
| `brand.md` | 理解风格约束（"不要渐变"、"主色只用于焦点元素"） | 设计师 / 产品经理 |
| `components.md` | 选择组件时遵循规范（按钮类型、表格列宽、表单布局） | 设计师 / 前端负责人 |
| `pages.md` | 生成新页面时遵循标准模板布局 | 设计师 / 前端负责人 |
| `references/*.png` | 看图理解整体风格和布局比例 | 设计师 |

## 定制化

### 换颜色主题

修改 `tokens.json` 中的 `color.brand.primary` 等值，AI 后续生成的代码会自动使用新颜色。

### 换页面风格

修改 `pages.md` 中的布局模板描述，或替换 `references/` 中的截图。

### 添加新页面类型

在 `pages.md` 中追加新的模板定义即可。

## 与 Rules 的关系

本目录的设计规范通过以下 rules 文件联动生效：

- `.ai/rules/08-styling.md` — 引用本目录的 tokens 和 brand 规范
- `.ai/rules/17-antd.md` — Ant Design 组件使用规范（与 `components.md` 配合）
- `.ai/rules/18-pro-components.md` — ProTable/ProForm 模式（与 `pages.md` 配合）

AI 在写前端代码时会同时读取 rules + design-system，确保代码层面和设计层面的双重规范约束。
