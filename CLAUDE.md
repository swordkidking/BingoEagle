# BingoEagle - AI驱动的企业全域智能经营仪表盘

## 项目概述

BingoEagle（鹰眼）是一个企业级经营监控仪表盘产品，参考 WorldMonitor 的 UI 框架，面向 B2B 软件企业的经营管理场景。

## 目录结构规范

```
BingoEagle/
├── CLAUDE.md                          # 本文件 - 项目规范与开发约定
├── .gitignore
├── prototype/                         # 交互原型（HTML/CSS/JS 单文件原型）
│   └── enterprise-monitor.html        # 主仪表盘原型
├── src/                               # 正式源码（未来开发阶段使用）
│   ├── components/                    # UI 组件
│   ├── layouts/                       # 布局模板
│   ├── data/                          # 数据层 / mock 数据
│   ├── styles/                        # 样式文件
│   └── utils/                         # 工具函数
├── scripts/                           # 工具脚本（爬虫、数据采集、构建等）
│   ├── scrape_*.py                    # 网站截图/数据采集脚本
│   └── explore_*.py                   # 功能探索/逆向脚本
├── docs/                              # 文档
│   ├── specs/                         # 需求说明书、功能架构文档
│   ├── reference/                     # 参考资料（竞品截图等）
│   │   ├── worldmonitor/              # WorldMonitor 参考截图
│   │   └── linkpc/                    # 品高聆客参考截图
│   └── assets/                        # 文档引用的图片资源
└── .claude/                           # Claude Code 配置（自动管理）
```

## 开发规则

### 目录与文件规则

1. **不在项目根目录放业务文件。** 根目录只允许：CLAUDE.md、.gitignore、配置文件（package.json 等）。
2. **脚本统一放 `scripts/`。** 任何 .py/.sh/.js 工具脚本必须放入 scripts/ 目录，禁止散落在根目录。
3. **原型放 `prototype/`。** HTML 单文件原型放在 prototype/ 下，正式组件化代码放 src/。
4. **文档放 `docs/`。** 需求文档 → docs/specs/，参考素材 → docs/reference/，文档用图 → docs/assets/。
5. **参考资料按来源分子目录。** 如 docs/reference/worldmonitor/、docs/reference/linkpc/。
6. **新目录必须有明确用途。** 禁止创建空目录占位（src/ 下的子目录在实际使用时再创建）。

### 命名规则

1. **目录名：** 全小写英文，用连字符分隔（如 `world-monitor`），不用中文目录名。
2. **代码文件：** 全小写英文，连字符分隔（如 `enterprise-monitor.html`）。
3. **文档文件：** 允许中文文件名（需求说明书等），但路径中不能有空格。
4. **脚本文件：** 小写英文 + 下划线（如 `scrape_wm.py`），功能相近的脚本应合并或用版本后缀。
5. **禁止数字后缀堆叠。** 如 `scrape_wm.py` 到 `scrape_wm5.py` 这种模式应避免，应使用有意义的命名区分或合并为一个可配置的脚本。

### 原型开发规则

1. **参考 WorldMonitor 的布局框架：** 左右两栏结构，地图在左上方约 60% 宽 × 42vh 高，右栏堆叠数据面板。
2. **单文件 HTML 原型中：** CSS 在 `<style>` 中，JS 在 `<script>` 中，不外链文件。
3. **写大文件时每 200 行写一次磁盘，避免上下文过长丢失工作。**
4. **每次写文件后用 `wc -l` 确认行数，用 `node -e` 验证 JS 语法。**

### Git 规范

1. 提交信息用中文，格式：`<类型>: <描述>`，如 `feat: 完成仪表盘原型首页布局`。
2. 类型：feat（功能）、fix（修复）、refactor（重构）、docs（文档）、chore（杂项）。
3. .gitignore 必须排除：.DS_Store、node_modules/、*.pyc、__pycache__/。

## 技术栈

- **原型阶段：** 纯 HTML + CSS + JavaScript 单文件
- **正式开发：** 待定（预计 Vue/React + TypeScript）
- **工具脚本：** Python 3
