# Changelog

本文件记录 BingoEagle 项目的所有重要改动。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

## [0.1.1] - 2026-04-10

### Changed
- **架构调整：五站 → 四站**：移除独立的「外部」Tab，外部信息整合到经营/交付/财务/人力四个维度中
  - 经营站：新增资本市场、竞争情报面板
  - 交付站：新增供应商生态面板
  - 财务站：新增资本市场、宏观经济面板
  - 人力站：新增人才市场面板
- 需求说明书升级至 v1.1，同步四站架构变更，新增 P13-P16 面板规格
- 需求说明书中 ~10 个 ASCII 架构图/流程图改用 Mermaid 重绘，浅色配色适配文档风格

### Added
- 新增 4 个面板：资本市场（panelCapitalMarket）、宏观经济（panelMacroEcon）、人才市场（panelTalentMarket）、供应商生态（panelVendorEcosystem）
- 资本市场面板支持 5 个二级钻取页面：总览、股价详情、分析师详情、股东详情、同业对比
- 每个二级页面包含「AI 交叉验证」模块（内部运营数据 vs 外部市场信号）

## [0.1.0] - 2026-04-09

### Added
- 项目目录结构初始化，建立标准工程目录：prototype/、scripts/、docs/、src/
- 创建 CLAUDE.md 项目规范（目录约定、命名规则、开发规范、Git 规范）
- 创建 .gitignore
- 完成仪表盘主原型 prototype/enterprise-monitor.html（参考 WorldMonitor 布局框架）
  - 左右两栏结构：左栏 60%（地图 + 下方面板）、右栏 40%（堆叠数据面板）
  - 左侧图标导航栏（维度切换、图层控制、快速导航）
  - 地图面板：中国全境轮廓 + 城市气泡（按 CHI 健康度着色）
  - AI 经营态势 BRIEF、AI 预测预报、外部情报流、收入脉搏、商机漏斗
  - EHI 企业健康指数（含仪表盘圆环 + 客户/项目/部门三个 Tab）
  - 客户风险雷达、项目交付态势、人力脉搏、竞争情报、政策监控、依赖链分析
  - 5 个维度视图切换（经营/交付/财务/人力/外部），左侧栏和顶部 Tab 联动
  - AI 对话助手（FAB 按钮 + 聊天面板）
  - 全局搜索（⌘K）
- 将 27 个 Python 工具脚本（scrape_*.py、explore_*.py）从根目录整理至 scripts/
- 将 4 份需求/架构文档整理至 docs/specs/
- 将参考截图整理至 docs/reference/worldmonitor/（45 张）和 docs/reference/linkpc/（583 张）
- 创建 CHANGELOG.md（本文件）
