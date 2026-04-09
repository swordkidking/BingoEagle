# WM 功能架构说明书

> World Monitor（worldmonitor.app）  
> 文档版本：v1.1 | 撰写日期：2026-04-08  
> 数据来源：Playwright 全站爬取（主站 + 4 个子站 + Docs + Blog + Pro 页）+ 实时界面截图

---

## 目录

1. [产品概述](#1-产品概述)
2. [顶层架构：五大专题站](#2-顶层架构五大专题站)
3. [通用 UI 框架](#3-通用-ui-框架)
4. [地图引擎模块](#4-地图引擎模块)
5. [地图图层体系（49 层）](#5-地图图层体系49-层)
6. [情报面板体系](#6-情报面板体系)
7. [AI 智能分析引擎](#7-ai-智能分析引擎)
8. [军事追踪模块](#8-军事追踪模块)
9. [海事情报模块](#9-海事情报模块)
10. [基础设施级联分析](#10-基础设施级联分析)
11. [金融与市场模块](#11-金融与市场模块)
12. [数据源体系](#12-数据源体系)
13. [高级功能与工具](#13-高级功能与工具)
14. [产品版本与权限分级](#14-产品版本与权限分级)
15. [技术栈总览](#15-技术栈总览)
16. [面向用户群体](#16-面向用户群体)

---

## 1. 产品概述

**World Monitor** 是一个开源、实时的全球情报仪表盘（Global Intelligence Dashboard），由 Elie Habib（Anghami 前 CEO）创建，托管在 worldmonitor.app。

| 核心指标 | 数值 |
|---------|------|
| 独立访客 | 2M+/月 |
| 峰值日活 | 421K |
| 覆盖国家 | 190+ |
| 实时数据源 | 435+ |
| 互动地图图层 | 49 层 |
| 新闻来源 | 344 个精选 RSS |
| 语言支持 | 21 种（含阿拉伯语 RTL、中文、日韩等）|
| 当前版本 | v2.6.7 |

**核心定位**：将冲突追踪、军事活动、海事监控、金融市场、地缘政治分析、基础设施风险整合到**单一地图界面**，面向记者、安全分析师、投资者、研究人员。

**开源协议**：AGPL-3.0，GitHub：koala73/worldmonitor

---

## 2. 顶层架构：五大专题站

World Monitor 从同一套代码库派生出五个**独立域名的专题站**，每个站聚焦不同情报领域，共享同一套顶部导航互相切换：

| 图标 | 专题站 | 域名 | 核心主题 |
|-----|--------|------|---------|
| 🌍 | **世界（World）** | worldmonitor.app | 地缘政治 · 军事 · 冲突 · 全球态势 |
| 💻 | **科技（Tech）** | tech.worldmonitor.app | AI/科技产业 · 网络安全 · 太空 · 数据中心 |
| 📈 | **金融（Finance）** | finance.worldmonitor.app | 全球股市 · 央行 · 加密货币 · 宏观经济 |
| ⛏️ | **大宗商品（Commodity）** | commodity.worldmonitor.app | 能源 · 矿产 · 供应链 · 航运 |
| ☀️ | **好消息（Good News）** | happy.worldmonitor.app | 积极事件 · 人类善举 · 物种恢复 · 清洁能源 |

---

## 3. 通用 UI 框架

所有专题站共享同一套界面框架，下图为主站整体布局：

![世界站主界面](screenshots/01_world_homepage.png)

### 3.1 顶部导航栏

```
[五站切换 Tabs] | [DEFCON 警报] | [地图控件] | [⌘K 搜索] | [区域筛选 ▸] | [⚙ 设置] | [亮/暗模式] | [Pro] [Blog] [Docs] [Status] | [GitHub] [Discord] [X] | [下载应用]
```

![顶部导航栏](screenshots/04_topnav.png)

### 3.2 整体布局划分

| 区域 | 说明 |
|-----|------|
| 左侧图层面板 | 可折叠，控制所有地图图层开关 |
| 中央地图区 | 2D/3D 互动地图，支持缩放、拖拽 |
| 右侧面板栏 | 可滚动的情报面板组（总高约 8980px） |

### 3.3 区域视图切换（8 个预设）

| 视图 | 覆盖区域 |
|-----|---------|
| 全球 | 默认全球俯视 |
| 美洲 | 北美 + 南美 |
| 中东北非（MENA）| 中东 + 北非 |
| 欧洲 | 欧洲大陆 |
| 亚洲 | 亚洲全域 |
| 拉丁美洲 | 中南美洲 |
| 非洲 | 非洲大陆 |
| 大洋洲 | 澳新及太平洋 |

![区域切换与图层面板](screenshots/17_region_switcher.png)

### 3.4 时间轴筛选器

全部事件可按时间窗口过滤：**1h / 6h / 24h / 48h / 7d / 全部**

### 3.5 Cmd+K 全局搜索

模糊搜索 195 个国家、25+ 数据图层、150+ 命令，多语言支持，一秒内定位全球任意目标。

![Cmd+K 全局搜索](screenshots/16_cmdk_search.png)

### 3.6 设置面板

包含显示（主题/字体/地图底图）、面板管理、数据来源三个 Tab。

![设置面板](screenshots/18_settings_panel.png)

### 3.7 面板管理

- 拖拽排序（Drag-to-Reorder）
- 面板可见性开关
- 面板状态持久化（IndexedDB + LocalStorage）
- 支持��享链接（复制当前地图状态 URL）

---

## 4. 地图引擎模块

### 4.1 2D 平面地图

基于 deck.gl + MapLibre GL，WebGL 加速渲染，支持 GPU 聚类。

![2D 地图区域](screenshots/04_map_area_2d.png)

### 4.2 3D 地球（Globe）

基于 globe.gl + Three.js，光真实地球纹理，大气散射着色器，自动旋转，海洋反射贴图，星空背景。

![3D 地球视图](screenshots/02_world_3d_globe.png)

### 4.3 地图图层控制面板

左侧图层面板列出所有可切换的数据图层，支持时间轴和区域过滤。

![图层控制面板](screenshots/03_world_layers_open.png)

### 4.4 双模式对比

| 模式 | 技术栈 | 特性 |
|-----|--------|------|
| **3D 地球** | globe.gl + Three.js | 光真实地球纹理、大气散射、自动旋转、海洋反射、星空背景 |
| **2D 平面** | deck.gl + MapLibre GL | WebGL 加速、GPU 聚类、GeoJSON/Scatterplot/Path/Icon 多层 |

支持运行时一键切换，偏好存入 LocalStorage。

### 4.5 地图底图（可切换）

| 供应商 | 说明 |
|-------|------|
| OpenFreeMap | 免费，OpenStreetMap 数据，Dark/Positron 风格，默认 |
| CARTO | Dark Matter / Voyager GL 风格 |
| Protomaps（自建）| 自托管矢量瓦片 maps.worldmonitor.app |

---

## 5. 地图图层体系（49 层）

### 5.1 世界站（🌍）图层——安全 & 冲突类

| 图标 | 图层名 | 数据来源 |
|-----|--------|---------|
| 🎯 | 伊朗袭击 | 实时事件追踪 |
| 🎯 | 情报热点 | 综合多源 |
| ⚔ | 冲突区 | ACLED / UCDP |
| 🏛 | 军事基地 | 开放情报数据库 |
| ☢ | 核设施 | IAEA |
| ⚠ | 伽马辐照器 | 辐射监测 |
| ☢ | RADIATION WATCH | 实时辐射监测 |
| 🚀 | 航天发射场 | 公开数据 |

**基础设施类**

| 图标 | 图层名 |
|-----|--------|
| 🔌 | 海底电缆 |
| 🛢 | 管道 |
| 🖥 | AI 数据中心 |
| ⚓ | 战略水道 |
| 💰 | ��济中心 |
| 💎 | 关键矿产 |

**军事 & 运输类**

| 图标 | 图层名 |
|-----|--------|
| ✈ | 军事活动（ADS-B）|
| 🚢 | 船舶交通（AIS）|
| ⚓ | 贸易航线 |
| ✈ | 航班延误 |

**事件 & 社会类**

| 图标 | 图层名 |
|-----|--------|
| 📢 | 抗议活动（ACLED��|
| ⚔ | UCDP 事件 |
| 👥 | 流离失所流向 |

**环境 & 自然类**

| 图标 | 图层名 |
|-----|--------|
| 🌫 | 气候异常 |
| ⛈ | 天气预警（NOAA）|
| 🌋 | 自然事件（USGS）|
| 🔥 | 火灾（NASA FIRMS）|

**网络 & 信息类**

| 图标 | 图层名 |
|-----|--------|
| 📡 | 互联网中断（Cloudflare Radar）|
| 🛡 | 网络威胁 |
| 📡 | GPS 干扰（GPSJAM）|
| 🛰 | 轨道监视 |

**综合评估类**

| 图标 | 图层名 | 说明 |
|-----|--------|------|
| 🌎 | CII 不稳定度 | 国家不稳定指数热力图 |
| 📈 | 韧性指数 🔒 | Pro 功能 |
| 🚫 | 制裁 🔒 | Pro 功能 |
| 🌓 | 昼/夜图层 | 地球明暗界限 |
| 📷 | 实时摄像头 | 31 路直播 |
| 🦠 | 疾病爆发 | 传染病监控 |

### 5.2 科技站（💻）图层

| 图标 | 图层名 |
|-----|--------|
| 🚀 | 初创中心 |
| 🏢 | 科技公司总部 |
| ⚡ | 加速器 |
| ☁ | 云计算区域 |
| 🖥 | AI 数据中心 |
| 🔌 | 海底电缆 |
| 📡 | 互联网中断 |
| 🛡 | 网络威胁 |
| 📅 | 科技展会/活动 |
| 📈 | 韧性指数 🔒 |
| 🌋 | 自然事件 |
| 🔥 | 火灾 |
| 🌓 | 昼/夜 |

### 5.3 金融站（📈）图层

| 图标 | 图层名 |
|-----|--------|
| 🏛 | 证券交易所 |
| 💰 | 金融中心 |
| 🏦 | 央行 |
| 📦 | 大宗商品枢纽 |
| 🌐 | 海湾国家投资（GCC）|
| ⚓ | 贸易航线 |
| 🔌 | 海底电缆 |
| 🛢 | 管道 |
| 📡 | 互联网中断 |
| ⛈ | 天气预警 |
| 💰 | 经济中心 |
| ⚓ | 战略水道 |
| 📈 | 韧性指数 🔒 |
| 🌋 | 自然事件 |
| 🛡 | 网络威胁 |
| 🚫 | 制裁 🔒 |
| 🌓 | 昼/夜 |

### 5.4 大宗商品站（⛏️）图层

| 图标 | 图层名 |
|-----|--------|
| 🔭 | 矿山 |
| 🏭 | 加工厂 |
| ⛵ | 商品港口 |
| 📦 | 商品枢纽 |
| 💎 | 关键矿产 |
| 🛢 | 管道 |
| ⚓ | 战略水道 |
| ⚓ | 贸易航线 |
| 🚢 | 船舶交通 |
| 💰 | 经济中心 |
| 🔥 | 火灾 |
| 🌫 | 气候异常 |
| 📈 | 韧性指数 🔒 |
| 🌋 | 自然事件 |
| ⛈ | 天气预警 |
| 📡 | 互联网中断 |
| 🚫 | 制裁 🔒 |
| 🌓 | 昼/夜 |

### 5.5 好消息站（☀️）图层

| 图标 | 图层名 |
|-----|--------|
| 🌟 | 积极事件 |
| 💚 | 善举 |
| 😊 | 世界幸福指数 |
| 📈 | 韧性指数 🔒 |
| 🐾 | 物种恢复 |
| ⚡ | 清洁能源 |

---

## 6. 情报面板体系

右侧面板栏是 WM 的核心信息展示区，总内容高度约 8980px，可垂直滚动浏览全部面板。

### 6.1 实时新闻聚合

344 个精选 RSS 源，按专题站分类，每条新闻带来源标签、状态标签（ONGOING / ALERT / BREAKING）和时间戳。

![实时新闻面板](screenshots/09_live_news.png)

**主要直播新闻源**

| 专题站 | 核心来源 |
|--------|---------|
| 世界站 | BLOOMBERG / SKYNEWS / EURONEWS / DW / CNBC / CNN / FRANCE 24 / AL ARABIYA / AL JAZEERA |
| 科技站 | THE VERGE / ARS TECHNICA / TECHCRUNCH / ARXIV AI / WIRED / KREBS ON SECURITY |
| 金融站 | YAHOO FINANCE / SEEKING ALPHA / CNBC / BLOOMBERG |
| 大宗商品 | BLOOMBERG COMMODITIES / REUTERS COMMODITIES / KITCO / MINING.COM |
| 好消息 | GOOD NEWS NETWORK / OPTIMIST DAILY / POSITIVE.NEWS / REASONS TO BE CHEERFUL |

### 6.2 直播摄像头（Live Webcams）

27–31 路实时摄像头，按地区分组（全部 / 中东 / 欧洲 / 美洲 / 亚洲 / 太空）。

![直播摄像头面板](screenshots/10_live_webcams.png)

### 6.3 AI 洞察 + AI 战略态势

左列：AI 生成的实时情报摘要（WORLD BRIEF），标注事件���量与级别。  
右列：各战略区域（IRAN / TAIWAN / BALTIC / BLACK SEA / KOREA / SCS…）实时状态与军机数量。

![AI洞察与战略态势](screenshots/06_ai_insights_panel.png)

### 6.4 AI 预测预报（AI Forecasts）

结合 Polymarket 预测市场与 AI 地缘分析，按类别（Conflict / Market / Supply Chain / Political / Military / Cyber / Infra）给出事件概率预测。

![AI预测预报](screenshots/08_ai_forecasts.png)

### 6.5 国家不稳定性指数（CII）+ 战略风险概览

左列：24 个战略国家实时不稳定评分（0–100），显示分项（U=动乱 / C=冲突 / S=制裁 / I=信息）。  
右列：综合战略风险仪表盘（0–100），实时趋势。

![CII与战略风险](screenshots/05_cii_panel.png)

### 6.6 情报动态（Signal Intelligence）

按来源权威性分级的跨域情报流，标注 ALERT / CONFLICT / DIPLOMATIC / ECONOMIC 等标签，支持多语言显示。

### 6.7 国家不稳定性详细评分

CII 完整列表，包含每个国家的总分、趋势箭头和四维分项（U / C / S / I）。

![CII详细评分与战略风险](screenshots/panel_scroll_1200.png)

### 6.8 信号聚合器（Cross-Source Signal Aggregator）

跨源信号聚合，将军事航班、社会动乱等信号按优先级排列，标注 CRITICAL / HIGH / MEDIUM 等级。

![信号聚合器](screenshots/23_signal_aggregator.png)

### 6.9 升级监视器（Escalation Monitor）+ 经济战（Economic Warfare）

左列：按冲突组合（冲突 + 新闻升级 / 通讯中断 + 新闻升级）追踪各地区升级信号数量。  
右列：制裁活动追踪，显示各方制裁行为及信号数量。

![升级监视器与经济战](screenshots/25_escalation_economic.png)

### 6.10 武力态势（Force Posture）

监测全球各地军事飞行集群，按国家/地区统计活跃信号数量。

### 6.11 基础设施级联分析

350 节点依赖图谱，选择任意基础设施节点可查看级联影响范围与受影响国家。

![基础设施级联分析](screenshots/panel_scroll_1800.png)

### 6.12 灾难级联（Disaster Cascade）

多事件聚合检测：当地理区域内多类灾害事件同时发生时触发告警（目前示例：No active convergence detected）。

### 6.13 区域新闻流

按地区（世界 / 美国 / 欧洲 / 中东 / 亚太 / 拉丁美洲 / 非洲 / 政府 / 能源…）提供聚焦的实时新闻流。

![区域新闻流](screenshots/27_regional_news.png)

### 6.14 能源 & 资源 / 政府 / 预测市场

覆盖石油天然气、政策动态和 Polymarket 预测赔率的专题新闻流。

![能源政府预测](screenshots/28_energy_gov_prediction.png)

---

## 7. AI 智能分析引擎

### 7.1 AI 摘要四级调用链

```
用户请求
  │
  ▼
Tier 1: Ollama / LM Studio（本地，零云端）
  │ 超时/错误
  ▼
Tier 2: Groq（Llama 3.1 8B，温度 0.3）
  │ 超时/错误
  ▼
Tier 3: 用户自带 API Key（OpenAI / Anthropic Claude 等，BYOK）
  │ 超时/错误
  ▼
Tier 4: 浏览器端 ONNX Runtime（完全离线推理）
```

标题去重使用 **Jaccard 相似度 > 0.6** 过滤。

### 7.2 信号情报系统（12 种信号类型）

**新闻 & 来源信号**

| 信号 | 触发条件 | 含义 |
|-----|---------|------|
| ◉ 收敛 | 3+ 种来源 30 分钟内报同一故事 | 多独立渠道确认，可信度高 |
| △ 三角验证 | 电讯社 + 政府 + 情报源三角对齐 | "权威三角" |
| 🔥 速度峰值 | 6+ 来源/小时话题提及率翻倍 | 故事在生态快速扩散 |

**市场信号**

| 信号 | 触发条件 | 含义 |
|-----|---------|------|
| 🔮 预测领先 | 预测市场波动 5%+ 但新闻覆盖低 | 市场定价尚未反映的信息 |
| 📰 新闻领先市场 | 高新闻速度但无对应市场移动 | 突发新闻尚未反映到价格 |
| ✓ 市场移动已解释 | 市场移动 2%+ 有对应新闻 | 价格行为有可识别催化剂 |
| 📊 静默背离 | 市场移动 2%+ 无关联新闻 | 价格移动无新闻解释——需关注 |

### 7.3 地理收敛检测

维护实时 1°×1° 地理网格，同一网格 24 小时内出现 3+ 种事件类型（抗议/军机/海军/地震）→ 生成收敛警报。

```
convergence_score = min(100, event_types×25 + min(25, total_events×2))
```

| 类型数 | 分数区间 | 警报级别 |
|-------|---------|---------|
| 4 种 | 80–100 | Critical |
| 3 种 | 60–80 | High |
| 3 种（低数量）| 40–60 | Medium |

### 7.4 战略风险综合评分

| 组成 | 权重 |
|-----|------|
| 收敛检测 | 40% |
| CII 偏差 | 35% |
| 基础设施 | 25% |

![战略风险仪表盘](screenshots/22_strategic_risk.png)

### 7.5 浏览器端本地 ML

- 引擎：ONNX Runtime Web
- 功能：标题分类、情感分析、威胁分级、离线摘要
- Worker 隔离，无需服务器，作为 AI 摘要链 Tier 4 兜底

---

## 8. 军事追踪模块

### 8.1 世界站军事追踪概览

![世界站含军事图层](screenshots/03_world_layers_panel.png)

### 8.2 舰艇识别

- MMSI 分析：150+ 国家代码映射
- 已知舰艇数据库：50+ 命名舰艇（美国 11 艘航母、英法中俄主力舰艇等）
- 前缀推断：USS / HMS / HMCS / INS / JS / ROKS / TCG

### 8.3 军机追踪与浪涌检测

- 数据源：OpenSky（ADS-B）+ Wingbits 数据富化
- **10 个活跃冲突区**：伊朗、霍尔木兹、乌克兰、加沙、南黎巴嫩、红海、苏丹、缅甸、朝鲜 DMZ、巴巴基斯坦-阿富汗边境
- **4 个军事指挥热点**：印太、中央、欧洲、北极司令部

### 8.4 武力态势面板

实时追踪全球军事飞行集群，按国家排列，显示活跃信号数。

![武力态势面板](screenshots/26_force_posture.png)

---

## 9. 海事情报模块

### 9.1 金融站（含贸易航线图层）

![金融站含贸易航线](screenshots/12_finance_homepage.png)

### 9.2 13 个战略水道监控

| 水道 | 战略意义 |
|-----|---------|
| 霍尔木兹海峡 | 全球 20% 石油；伊朗控制 |
| 苏伊士运河 | 欧亚航运单点故障 |
| 马六甲海峡 | 亚太主要石油通道 |
| 曼德海峡 | 红海出口；胡塞活动 |
| 巴拿马运河 | 美洲东西向过境 |
| 台湾海峡 | 半导体供应链；解放军活动 |
| 好望角 | 超大型油轮苏伊士备用航线 |
| 直布罗陀海峡 | 大西洋-地中海门户；NATO 咽喉 |
| 博斯普鲁斯海峡 | 黑海出口；蒙特勒公约 |
| 朝鲜海峡 | 日韩贸易；东亚最繁忙 |
| 多佛尔海峡 | 世界最繁忙航运通道 |
| 刻赤海峡 | 俄控；乌克兰粮食出口受限 |
| 龙目海峡 | 超大型油轮马六甲替代 |

每个水道卡显示：实时过境数（油轮 vs 货船）、周环比变化、可展开 180 天时序图。

### 9.3 幽灵船检测（Dark Ship Detection）

AIS 信号中断 > 60 分钟 → 标记为可疑（制裁规避 / 军事活动 / 设备故障）。

---

## 10. 基础设施级联分析

### 10.1 面板概览

![基础设施级联面板](screenshots/24_infra_cascade.png)

### 10.2 依赖图谱（350 节点）

| 节点类型 | 数量 | 典型示例 |
|---------|------|---------|
| 海底电缆 | 86 | MAREA、FLAG Europe-Asia、SEA-ME-WE 6 |
| 管道 | 88 | 北溪、跨西伯利亚、Keystone |
| 港口 | 62 | 新加坡、鹿特丹、深圳 |
| 战略水道节点 | 9 | 苏伊士、霍尔木兹、马六甲等 |
| 国家（终端）| 105 | 代表各国受影响程度 |

### 10.3 级联计算

广度优先传播，最深 3 层：

```
impact = edge_strength × disruption_level × (1 - redundancy)
```

影响程度：Critical（>0.8）/ High（>0.5）/ Medium（>0.2）/ Low（≤0.2）

---

## 11. 金融与市场模块

### 11.1 金融站主界面

![金融站主界面](screenshots/12_finance_homepage.png)

### 11.2 市场面板

实时股票价格、涨跌幅，覆盖 25+ 主要标的和全球主要指数。

![市场监视列表](screenshots/12b_finance_markets.png)

### 11.3 免费功能

| 功能 | 内容 |
|-----|------|
| 股票监视列表 | AAPL / AMZN / NVDA / META / GOOGL / TSLA 等 25+ |
| 全球指数 | 道指 / 标普 / 纳指 / 罗素 2000 |
| 央行追踪 | 13 家央行利率决策 |
| 加密货币 | CoinGecko（BTC/ETH 等）+ 恐惧贪婪指数 |
| 预测市场 | Polymarket 赔率叠加 |
| 海湾国家 FDI | GCC 外商直接投资流向 |

### 11.4 Pro 高级功能

| 功能 | 说明 |
|-----|------|
| 高级股票分析 | 均线堆叠、趋势状态、MACD/RSI、成交量评分、AI 叠加 |
| 历史回测 | 策略回测，Redis 持久化 |
| 每日市场简报 | AI 生成，宏观 + 地缘 + 市场信号关联 |
| 股票搜索富化 | Premium Finance Search Layer |

---

## 12. 数据源体系

### 12.1 科技站主界面

![科技站主界面](screenshots/11_tech_homepage.png)

### 12.2 科技站 AI/ML 面板

![科技站AI/ML面板](screenshots/11b_tech_aiml_panel.png)

### 12.3 大宗商品站主界面

![大宗商品站主界面](screenshots/13_commodity_homepage.png)

### 12.4 大宗商品新闻面板

![大宗商品新闻面板](screenshots/13b_commodity_news.png)

### 12.5 情报数据源

| 类别 | 数据源 |
|-----|--------|
| 冲突数据 | ACLED、UCDP、GDELT |
| 军事航空 | OpenSky（ADS-B）、Wingbits |
| 海事 | AISStream（WebSocket）、IMF PortWatch、CorridorRisk |
| 太空/卫星 | NASA FIRMS（火点）、Copernicus（SAR，Enterprise）|
| 自然灾害 | USGS（地震）、GDACS（灾害预警）、NOAA（天气）|
| 核/辐射 | IAEA、Radiation Watch |
| 网络安全 | Cloudflare Radar、BGPStream、GPSJAM |
| 传染病 | WHO / CDC |

### 12.6 Telegram OSINT 频道（26 个，分三级）

| 级别 | 频道 |
|-----|------|
| Tier 1 | VahidOnline（伊朗政治）|
| Tier 2 | Abu Ali Express、Aurora Intel、BNO News、Clash Report、DeepState、Iran International、LiveUAMap、OSINTdefender 等 |
| Tier 3 | Bellingcat、CyberDetective、NEXTA、OSINT Industries、OsintOps News、The Spectator Index、War Monitor 等 |

架构：GramJS MTProto 客户端在 Railway 上运行，60 秒循环轮询，每频道 15 秒超时。

### 12.7 财经数据源

| 数据源 | 内容 |
|-------|------|
| Finnhub | 全球 92 家交易所实时行情、分析师目标价 |
| FRED | 宏观指标（GDP/CPI/利率）|
| CoinGecko | 加密货币价格、恐惧贪婪指数 |
| Polymarket | 预测市场赔率 |
| Oilprice / Rigzone | 原油价格 |

---

## 13. 高级功能与工具

### 13.1 DEFCON 综合警报

顶栏 DEFCON 徽章显示当前全球紧张级别（DEFCON 1–5 + 百分比）。

![DEFCON弹窗](screenshots/19_defcon_popup.png)

### 13.2 好消息站

专门收集全球正能量新闻，用 AI 过滤信息焦虑，提供"治愈系日报"。

![好消息站主界面](screenshots/14_happy_homepage.png)

![好消息信息流](screenshots/14b_good_news_feed.png)

**新闻分类 Tab**：全部 / 科学健康 / 自然野生 / 人类善举 / 创新科技 / 气候胜利 / 文化社区

**主要来源**：GOOD NEWS NETWORK / OPTIMIST DAILY / POSITIVE.NEWS / REASONS TO BE CHEERFUL / NATURE NEWS / SINGULARITY HUB / HUMAN PROGRESS

### 13.3 Docs 文档中心

完整的开发者和用户文档，覆盖：Getting Started / Features / Map Layers / AI Intelligence / CII / Maritime / Military / Finance / Data Sources / Developer Guide。

![Docs文档中心](screenshots/20_docs_home.png)

### 13.4 Blog

面向 OSINT 分析师、供应链专业人士、开发者的深度分析文章。

![Blog首页](screenshots/21_blog_home.png)

### 13.5 Pro 产品页

![Pro页面](screenshots/15_pro_page.png)

### 13.6 快照与数据导出

- 快照系统：IndexedDB 存储当前地图 + 面板状态，支持基线对比
- 导出格式：CSV 和 JSON
- 时间轴播放控制（⏪⏮◀ 实时 ▶⏭⏩）

### 13.7 多语言支持

21 种语言界面（含阿拉伯语 RTL、中文简繁、日语、韩语、泰语等），语言包懒加载（首屏速度提升 40%+）。

### 13.8 桌面客户端（Tauri）

支持 Windows / macOS / Linux，高性能 GPU 渲染，后台失去焦点时暂停 WebGL 渲染节省电量。

### 13.9 MCP 集成（Enterprise）

Model Context Protocol 支持，允许 Claude / GPT / 自定义 LLM 将 World Monitor 作为 Tool 调用，查询全部 22 服务、读取地图状态、触发分析任务。

---

## 14. 产品版本与权限分级

| 功能 | 免费版 | Pro | Enterprise |
|-----|--------|-----|-----------|
| 全功能仪表盘 | ✅ | ✅ | ✅ |
| 435+ 数据源 | ✅ | ✅ | ✅ |
| 49 层地图图层（基础）| ✅ | ✅ | ✅ |
| BYOK AI | ✅ | ✅ | ✅ |
| 21 种语言 | ✅ | ✅ | ✅ |
| 高级股票分析 + 回测 | ❌ | ✅ | ✅ |
| 地缘政治分析框架 | ❌ | ✅ | ✅ |
| 宏观经济分析 | ❌ | ✅ | ✅ |
| AI 晨报 & 闪报（Slack/TG/WA/Email）| ❌ | ✅ | ✅ |
| 央行 & 货币政策追踪 | ❌ | ✅ | ✅ |
| 22 服务 1 Key | ❌ | ✅ | ✅ |
| 全球风险评分 & 情景分析 | ❌ | ✅ | ✅ |
| 制裁/韧性 Premium 图层 | ❌ | ✅ | ✅ |
| 实时卫星 + SAR 影像 | ❌ | ❌ | ✅ |
| AI Agent（投资者人设）+ MCP | ❌ | ❌ | ✅ |
| 50,000+ 基础设施资产 | ❌ | ❌ | ✅ |
| 100+ 连接器（Splunk/Snowflake 等）| ❌ | ❌ | ✅ |
| REST API + Webhook + 批量导出 | ❌ | ❌ | ✅ |
| 团队工作区（SSO/MFA/RBAC）| ❌ | ❌ | ✅ |
| 白标 & 可嵌入面板 | ❌ | ❌ | ✅ |
| Android TV 应用 | ❌ | ❌ | ✅ |
| 云/本地/离线部署 | ❌ | ❌ | ✅ |
| 专属支持 & 托管部署 | ❌ | ❌ | ✅ |

---

## 15. 技术栈总览

| 层 | 技术 | 用途 |
|----|------|------|
| 语言 | TypeScript 5.x | 60+ 源文件全类型安全 |
| 构建 | Vite | 快速 HMR + 优化生产构建 |
| 3D 地图（桌面）| deck.gl + MapLibre GL | WebGL 加速大数据集渲染 |
| 3D 地球 | globe.gl + Three.js | 光真实 3D 地球 |
| 移动地图 | D3.js + TopoJSON | SVG 省电渲染 |
| 并发 | Web Workers | 主线程外聚类与关联分析 |
| AI/ML | ONNX Runtime Web | 浏览器内离线推理 |
| 网络 | WebSocket + REST | AIS 实时流 + HTTP 其他 API |
| 存储 | IndexedDB | 快照、基线（MB 级状态）|
| 偏好 | LocalStorage | 用户设置、面板顺序 |
| 后端部署 | Vercel Edge Functions | 60+ 无服务器代理，全球分发 |
| 中继 | Railway | 绕过云供应商 IP 封锁 |
| 图表 | TradingView lightweight-charts | 过境时序图 |
| API 协议 | Protocol Buffers（92 个 proto 文件）| 类型安全 API 契约 |
| 桌面 | Tauri | Windows / macOS / Linux |
| 认证 | Clerk | 用户身份验证 |
| 支付 | DodoPayments + Stripe | Pro/Enterprise 订阅 |
| 错误追踪 | Sentry | 生产错误监控 |

---

## 16. 面向用户群体

| 用户类型 | 核心需求 | 主要功能 |
|---------|---------|---------|
| **投资者 & 基金经理** | 股票 + 宏观 + 地缘风险关联 | 金融面板 + AI 晨报 + CII + 预测市场 |
| **能源 & 大宗商品交易员** | 航运通道 + 供应链中断 + 能源价格 | 海事图层 + 管道图层 + 大宗商品站 |
| **记者 & 媒体** | 快速追踪多区域事件 | 实时新闻 + 直播摄像头 + AI 洞察 |
| **安全分析师 & OSINT 研究员** | 多源情报融合 + 军事活动 | 军事图层 + CII + 信号情报 + Telegram 频道 |
| **学术研究员** | 冲突数据 + 经济数据 + 历史分析 | ACLED/UCDP/GDELT + FRED + 数据导出 |
| **应急响应团队** | 灾害定位 + 基础设施影响 | 地震/火灾图层 + 级联分析 + 基础设施依赖图 |
| **政府 & 机构** | 宏观政策 + 情报态势 | 全站 + Enterprise API + 团队工作区 |
| **普通用户** | 理解世界发生了什么 | 好消息站 + AI 摘要 + 多语言 |

---

*本说明书基于 2026-04-08 通过 Playwright 对 worldmonitor.app 及所有子站、Docs、Blog、Pro 页面的全面爬取与实时界面截图整理，反映 WM v2.6.7 的功能架构。*
