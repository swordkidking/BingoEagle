# Changelog

本文件记录 BingoEagle 项目的所有重要改动。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

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
