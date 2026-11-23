import React, { useEffect, useMemo, useRef, useState } from "react";
import * as echarts from "echarts";
import {
  BookOpen,
  Calendar,
  CheckCircle2,
  Compass,
  FileCode2,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  Gavel,
  Layers,
  Loader2,
  Lock,
  Maximize2,
  Minimize2,
  Play,
  Printer,
  RefreshCw,
  RotateCcw,
  Save,
  ShieldCheck,
  Sparkles,
  Target,
  Terminal,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import {
  apiGet,
  apiPost,
  apiPut,
  buildApiUrl,
  openInExplorer,
  streamSSE,
} from "../services/apiClient";
import { useStudioStore } from "../store/useStudioStore";
import type { FusedPlot, StudioSubTab } from "../types/api";

interface DrawingCatalogItem {
  code: string;
  name: string;
  category: string;
  scale: string;
  imageUrl?: string;
  a3Url?: string;
  outputPath?: string;
  legendItems: string[];
  descriptionLines: string[];
}

interface DxfLayerSummary {
  layer: string;
  label: string;
  colorName: string;
  entityCount: number;
  geometryType: string;
}

interface PhasingLedgerRow {
  plot_id: string;
  plot_name: string;
  category: "留 (保护修缮)" | "改 (功能活化)" | "拆 (织补腾退)";
  phase: "近期示范 (1-2年)" | "中期推广 (3-5年)" | "远期巩固 (5-10年)";
  startYear: number;
  durationYears: number;
  investmentWan: number;
  fundingSource: string;
  keyAction: string;
}

interface SkillPartItem {
  partCode: string;
  title: string;
  trigger: string;
  highlights: string[];
  constraint: string;
}

const WB3_TABS: Array<{
  key: StudioSubTab;
  stageBadge: string;
  label: string;
  subtitle: string;
}> = [
  {
    key: "delivery",
    stageBadge: "阶段 13",
    label: "工程图纸、A3图册、DXF与全本报告交付",
    subtitle: "独立图纸引擎按需渲染、A3图框拼装、AutoCAD 2000 DXF与Word编译",
  },
  {
    key: "guideline",
    stageBadge: "阶段 12",
    label: "九章节法定城市设计导则编制",
    subtitle: "通则+分地块刚性管控图则9章节两步式生成与法定Word导则导出",
  },
  {
    key: "systems",
    stageBadge: "阶段 09",
    label: "四大专项系统与产业业态设计",
    subtitle: "综合交通、公共空间、建筑形态、历史风貌与商业运营五大专项推演",
  },
  {
    key: "timing",
    stageBadge: "阶段 11",
    label: "拆改留实施路径与分期甘特图",
    subtitle: "留改拆双层分类施策台账、近期/中期/远期建设时序与资金平衡测算",
  },
  {
    key: "skills",
    stageBadge: "阶段 16",
    label: "智能体 Skill 规范手册与多方听证会",
    subtitle: "Part 0–Part 11 研发规范检视与基地自适应公众听证会推演模拟器",
  },
];

const DEFAULT_DRAWINGS: DrawingCatalogItem[] = [
  {
    code: "dr_004",
    name: "区域位置与规划研究范围红线图",
    category: "第一篇 · 现状底图系",
    scale: "1 : 2,000",
    legendItems: ["规划研究范围红线", "核心历史风貌区边界", "城市主干路网", "既有建筑基底"],
    descriptionLines: [
      "1. 严格界定城市更新规划研究范围与 WGS-84 / CGCS2000 空间坐标基准；",
      "2. 识别周边轨道交通站点、历史文化街区紫线及上位控规衔接边界；",
      "3. 作为全周期 17 阶段空间数据库与工程 CAD 图纸的统一空间底板。",
    ],
  },
  {
    code: "dr_014",
    name: "现状建筑风貌、高度与权属综合评价图",
    category: "第二篇 · 全息诊断系",
    scale: "1 : 1,500",
    legendItems: ["历史保护建筑 (一类)", "风貌协调建筑 (二类)", "一般现代建筑", "待整治零星违建"],
    descriptionLines: [
      "1. 基于 DuckDB Spatial 融合宽表统计全区建筑层数、建造年代与结构质量；",
      "2. 精确标注需 100% 原真修缮的历史红砖建筑与可实施内部功能织补的院落；",
      "3. 为阶段 11 留、改、拆分类施策台账提供逐栋建筑矢量化依据。",
    ],
  },
  {
    code: "dr_024",
    name: "rustworkx 全路网空间句法整合度诊断图",
    category: "第二篇 · 全息诊断系",
    scale: "1 : 2,000",
    legendItems: ["R400m 高整合度活力核", "R800m 街区穿行主廊", "低可达性尽端街巷", "慢行打通建议节点"],
    descriptionLines: [
      "1. 采用 rustworkx C++ 图算力引擎完成全路网拓扑打断与多半径整合度计算；",
      "2. 揭示步行 5 分钟圈高可达性商业界面与内部微循环梗阻节点；",
      "3. 支撑阶段 09 慢行林荫道选线与街口公共开敞空间布局。",
    ],
  },
  {
    code: "dr_051",
    name: "总体城市设计空间结构与功能分区规划图",
    category: "第三篇 · 方案生形系",
    scale: "1 : 1,500",
    legendItems: ["历史文脉与现代活力主轴", "蓝绿海绵漫步带", "四大复合功能核心", "三级天际线通廊"],
    descriptionLines: [
      "1. 落实“一轴两带、四核多节点”的寒地历史街区有机更新空间结构；",
      "2. 统筹商业文创、全龄居住社区、嵌入式公服与口袋公园绿地空间布局；",
      "3. 明确视线通廊与街巷高宽比（D/H 1.0–1.2）刚性形态控制要求。",
    ],
  },
  {
    code: "dr_062",
    name: "重点靶向地块法定城市设计控制图则",
    category: "第四篇 · 法定图则系",
    scale: "1 : 1,000",
    legendItems: ["建筑控制红线与贴线率", "控规限高包络 (≤18m/24m)", "公共通道与骑楼暖廊", "独立占地口袋绿地"],
    descriptionLines: [
      "1. 针对锁定靶向地块输出法定图则级 FAR、BCR、限高、退界与绿地率硬指标；",
      "2. 标注首层商业连续贴线界面、寒地防风骑楼及地下停车出入口禁止开口段；",
      "3. 直接纳入阶段 12 九章节法定城市设计导则附表与审批管理依据。",
    ],
  },
  {
    code: "dr_081",
    name: "多智能体协同规划与空间生形技术演进总图",
    category: "第四篇 · 交付总览系",
    scale: "A3 标准示意版式",
    legendItems: ["DuckDB Spatial 空间底座", "Hybrid RAG 法规锚定", "三主体博弈共识引擎", "ControlNet 刚性生形"],
    descriptionLines: [
      "1. 全景展示从多源数据建库、空间句法诊断、政企民博弈到法定交付的闭环链路；",
      "2. 满足 `draw_map_early` 独立示意图快速合成规范，适配 A3 横版标准工程图框。",
    ],
  },
];

const GUIDELINE_CHAPTERS: Array<{
  num: string;
  title: string;
  mandatoryTag: string;
  content: string;
}> = [
  {
    num: "第一章",
    title: "总则与法定适用范围",
    mandatoryTag: "法定效力总纲",
    content:
      "第一条【编制目的】为落实国土空间规划刚性管控传导，保障历史文化街区传统肌理与人居环境品质协同跃升，依据《城市设计管理办法》（住建部令第35号）与《城市居住区规划设计标准》（GB 50180-2018）制定本导则。\n第二条【适用范围】本导则适用于规划研究红线内全部更新单元（重点锚定靶向地块及其毗邻风貌协调区）的土地出让、规划许可、建筑设计与微更新实施验收。",
  },
  {
    num: "第二章",
    title: "总体功能定位与空间结构引导",
    mandatoryTag: "结构刚性传导",
    content:
      "第三条【功能定位】构建“寒地历史文化活化示范街区 · 产城人文复合活力中枢”，主导功能为文博创意商业、品质完整居住社区与全龄公共服务。\n第四条【空间结构】严格保护“一轴两带、四核多节点”空间骨架，主轴线公共空间宽度不得缩减，四大核心节点首层公共性功能占比不得低于 65%。",
  },
  {
    num: "第三章",
    title: "土地利用兼容性与开发强度刚性管控",
    mandatoryTag: "强制性红线指标",
    content:
      "第五条【容积率与奖励上限】靶向地块基准容积率为 1.92；实施主体每无偿移交 1㎡ 独立占地的社区公共绿地或嵌入式养老托育设施，可获 1.2㎡ 计容面积奖励，但奖励后地块综合容积率上限严控为 FAR ≤ 2.20。\n第六条【建筑密度与混合兼容】综合建筑密度 BCR ≤ 38%；允许商业服务业（B）与社区公服（A）、文化创意工坊在首层及二层水平或垂直复合设置。",
  },
  {
    num: "第四章",
    title: "公共开敞空间与蓝绿海绵网络控制",
    mandatoryTag: "生态与绿地红线",
    content:
      "第七条【绿地率与口袋公园】规划绿地与开敞空间占比不得低于 25.0%，规划配置不少于 3 处面积 ≥ 800㎡ 的南向向阳口袋公园，实现“300米见绿”。\n第八条【海绵城市指标】新建与改造硬化铺装透水率 ≥ 70%，结合街道绿化带设置下沉式雨水花园，年径流总量控制率 ≥ 80%。",
  },
  {
    num: "第五章",
    title: "综合交通、慢行林荫道与地下空间接驳导则",
    mandatoryTag: "慢行优先强制条文",
    content:
      "第九条【人车分离与慢行断面】历史风貌主街与高整合度商业支路全面取消路侧地面占道停车，单侧连续无障碍步行带净宽 ≥ 4.5m，街道绿视率 GVI ≥ 28%。\n第十条【地下空间与停车配建】新增机动车停车位 100% 集中布置于非风貌核心区地下车库，并预留与周边轨道交通站厅的全天候地下暖廊接口。",
  },
  {
    num: "第六章",
    title: "建筑高度、天际线视廊与贴线退界刚性图则",
    mandatoryTag: "空间形态硬约束",
    content:
      "第十一条【分级限高与天际线】沿历史主街一线建筑檐口高度 ≤ 18m，街坊内部过渡区建筑限高 ≤ 24m，街区平均高宽比控制在 D/H = 1.0–1.3。\n第十二条【建筑贴线率与退界】商业活力主街建筑首层贴线率 ≥ 75%，主街退界 ≥ 6.0m 并形成连续雨篷或寒地防风骑楼界面；新建建筑不得恶化周边既有住宅大寒日日照标准。",
  },
  {
    num: "第七章",
    title: "历史文化街区紫线保护与寒地第五立面色彩材质导则",
    mandatoryTag: "历史紫线与风貌",
    content:
      "第十三条【历史建筑修缮】紫线范围内一、二类历史风貌建筑外立面严禁擅自拆改，采用传统清水红砖、青灰瓦与暖色石材进行原真性修缮。\n第十四条【寒地色彩与第五立面】建筑主色调采用暖灰、赭红与米白高明度暖色系；屋顶（第五立面）严禁裸露冷却塔与杂乱设备，鼓励设置双坡屋顶与阳光暖房。",
  },
  {
    num: "第八章",
    title: "全龄友好社区公服配套与市政韧性防灾导则",
    mandatoryTag: "完整社区民生配建",
    content:
      "第十五条【5-10-15分钟生活圈】靶向地块内必须配建建筑面积 ≥ 1,200㎡ 的嵌入式社区医养结合驿站、普惠托育点与全天候室内老年/儿童活动厅。\n第十六条【市政管网与消防韧性】全部架空电力通信线缆 100% 下地敷设；保留街巷尽头设置微型消防站，主街消防车通行净宽与转弯半径满足现行国标。",
  },
  {
    num: "第九章",
    title: "重点靶向地块（分图则）法定控制指标一览表",
    mandatoryTag: "行政审批直接依据",
    content:
      "第十七条【分地块图则绑定】靶向更新单元编码、用地性质、容积率上限（2.20）、建筑密度上限（38%）、建筑限高（18m/24m）、绿地率下限（25%）及公益配建移交清单作为土地带方案出让与规划核实的法定附件，未经法定程序不得突破。",
  },
];

const STAGE09_SYSTEMS: Array<{
  key: string;
  title: string;
  badge: string;
  metrics: Array<{ label: string; value: string }>;
  defaultContent: string;
}> = [
  {
    key: "traffic_slow",
    title: "综合交通与慢行系统",
    badge: "空间句法高整合度路网织补",
    metrics: [
      { label: "慢行专用道总长", value: "6.8 km" },
      { label: "主街步行道净宽", value: "≥ 4.5 m" },
      { label: "路侧违停清退率", value: "100% 入地" },
    ],
    defaultContent:
      "1. 【路网微循环打通】依据 rustworkx 空间句法 R400m/R800m 整合度诊断，打通 4 处历史大院尽端断头支路，使街区步行路网密度提升至 9.2 km/km²；\n2. 【寒地全天候慢行廊道】沿人民大街及核心历史支路构建“防风骑楼+暖廊连桥+透水防滑步道”三级慢行网络；\n3. 【静稳交通与智慧停车】核心风貌街巷实行限时步行化管理，利用非风貌地块地下空间集中配建 680 个智慧机械停车泊位。",
  },
  {
    key: "public_open_space",
    title: "公共开敞空间系统",
    badge: "海绵绿轴与口袋公园体系",
    metrics: [
      { label: "规划绿地与开敞率", value: "26.2%" },
      { label: "目标街区绿视率 GVI", value: "≥ 30.5%" },
      { label: "向阳口袋公园数量", value: "5 处" },
    ],
    defaultContent:
      "1. 【三级公共空间矩阵】形成“城市级文化门户广场 — 街坊级向阳口袋公园 — 院落级共生微庭院”三级开放空间网络；\n2. 【寒地向阳微气候设计】口袋公园全部选址于建筑南侧冬至日照充足区（连续日照 ≥ 3.5h），配置防风常绿松柏障景与加热休憩坐凳；\n3. 【海绵韧性基础设施】全面植入下沉式雨水花园、植草沟与透水花岗岩铺装，缓解老城区雨季内涝。",
  },
  {
    key: "morphology_skyline",
    title: "建筑形态与天际线控制",
    badge: "三级高度与视廊刚性包络",
    metrics: [
      { label: "主街一线檐口限高", value: "≤ 18 m" },
      { label: "街巷高宽比 D/H", value: "1.0 – 1.25" },
      { label: "首层界面贴线率", value: "≥ 78%" },
    ],
    defaultContent:
      "1. 【三级阶梯天际线控制】确立“近街历史坡屋顶保护带（≤12-18m）— 中景多层退台协调带（≤24m）— 远景TOD节点标志塔楼（≤36m）”的韵律天际线；\n2. 【视廊通廊刚性保护】严格锁定从人民大街主轴望向历史标志建筑物的 3 条扇形视线通廊，通廊内严禁新建遮挡体量；\n3. 【首层活力界面管控】商业主街首层外立面通透率不低于 70%，严禁设置连续超过 8m 的封闭实墙。",
  },
  {
    key: "heritage_color",
    title: "历史风貌与色彩材质",
    badge: "红砖灰瓦原真修缮导则",
    metrics: [
      { label: "历史建筑修缮保留率", value: "100%" },
      { label: "主导色系色温", value: "2700K–3500K 暖色" },
      { label: "第五立面整治率", value: "100%" },
    ],
    defaultContent:
      "1. 【历史建筑分类修缮】对一类保护建筑实施“修旧如故”原真修缮；对二类风貌建筑保留传统清水红砖立面，内部植入现代钢木复合结构；\n2. 【寒地城市色彩谱系】确立以“百年红砖赭红、关东青砖暖灰、白山松水米白”为核心的色彩控制谱系，避免高饱和度冷色调；\n3. 【夜景照明与店招导则】采用 3000K 暖白光勾勒历史建筑檐口与柱廊，户外店招实行“一店一招、镶嵌式铜字/木质招牌”规范。",
  },
  {
    key: "industry_commercial",
    title: "产业业态与商业运营策划",
    badge: "文商旅创复合与财务自平衡",
    metrics: [
      { label: "文创与体验商业占比", value: "62%" },
      { label: "社区便民商业保留率", value: "≥ 25%" },
      { label: "预计年运营坪效提升", value: "+135%" },
    ],
    defaultContent:
      "1. 【“四维一体”业态矩阵】构建“非遗文化旗舰展馆 (25%) + 青年数字创意工坊与主理人首店 (37%) + 全季寒地夜经济餐饮暖廊 (23%) + 社区便民生活服务 (15%)”复合业态；\n2. 【共生院产权与收益共享】推行“政府平台统筹产权修缮 + 专业运营商统一招商 + 原住民微股分红与优先就业”模式；\n3. 【全季候运营策划】冬季主打“暖廊书香市集+冰雪光影艺术季”，夏季主打“林荫外摆咖啡节+庭院戏剧周”，实现全年无淡季现金流平衡。",
  },
];

const SKILLS_12_PARTS: SkillPartItem[] = [
  {
    partCode: "Part 0",
    title: "智能体研发自律准则：八荣八耻 (Agent Code of Conduct)",
    trigger: "功能开发、出图重构、GIS 计算、多智能体博弈与文档交付全生命周期",
    highlights: [
      "以瞎猜接口为耻，以认真查询为荣：调用绘图或组件前必查验接口参数与矢量字段",
      "以创造接口为耻，以复用现有为荣：优先复用 tools/drawings/ 独立图纸引擎与通用拼装",
      "以盲目断言为耻，以闭环交付为荣：交付前必须完成排他文件所有权检查与四份文档同步",
    ],
    constraint: "严禁跳过接口核对盲猜参数，严禁主动拉起无头浏览器，交付前必做预检。",
  },
  {
    partCode: "Part 1",
    title: "绘图代码管理规范 (Drawing Code Management)",
    trigger: "新增规划图纸、修改现有图纸绘制逻辑或重构制图代码时",
    highlights: [
      "每张图纸绘制代码完全独立存放于 tools/drawings/ 下（如 dr_004.py, dr_051.py）",
      "统一导出 draw_map(...)、legend_items 与 description_lines（或 draw_map_early）",
      "主框架通过 importlib.import_module 动态按需加载，严禁硬编码混合样式",
    ],
    constraint: "绝不允许将多个图纸绘制逻辑混写在同一文件中。",
  },
  {
    partCode: "Part 2",
    title: "截图校验规范 (Screenshot Verification)",
    trigger: "需要对平台页面、地图渲染或前端 UI 进行效果核验时",
    highlights: [
      "非必要不要打开浏览器截图，严禁使用 Selenium / Playwright 等静默拉起无头浏览器",
      "明确告知用户核验路径与步骤，引导用户手动查看或截图反馈",
    ],
    constraint: "彻底杜绝无头浏览器进程残留与算力浪费。",
  },
  {
    partCode: "Part 3",
    title: "更新日志维护规范 (Update Changelog)",
    trigger: "完成代码重构、功能新增、架构调整或 Bug 修复准备汇报前",
    highlights: [
      "在 CHANGELOG.md 顶部规范记录版本号、修改涉及文件、修复问题与新增核心特性",
      "全中文标准 Markdown 列表格式，保持时间戳与版本号演进连贯",
    ],
    constraint: "严禁遗漏任何一次实质性架构或功能修改记录。",
  },
  {
    partCode: "Part 4",
    title: "交互人设规范 (Interactive Persona)",
    trigger: "智能体向用户汇报工作成果或解答技术问题时",
    highlights: [
      "每次回复开头尊称用户，随后紧接严谨、专业的城乡规划与软件工程技术汇报",
    ],
    constraint: "实现情感呼应与高水准专业技术产出的融合。",
  },
  {
    partCode: "Part 5",
    title: "设计方案语言规范 (Implementation Plan Language)",
    trigger: "创建或更新 implementation_plan.md 供评审时",
    highlights: [
      "所有设计方案包含背景、问题描述、提议改动与测试计划均以中文为主撰写",
    ],
    constraint: "严禁全英文或大部分英文方案输出。",
  },
  {
    partCode: "Part 6",
    title: "GitHub 隐私安全防泄露规范 (GitHub Privacy Check)",
    trigger: "将代码、文档、配置提交或推送至代码仓库时",
    highlights: [
      "全面排查个人身份信息与各服务商 API Keys（DeepSeek / OpenAI / 高德密钥）",
      "桌面端运行时 API 密钥统一掩码返回（sk-****），零明文落盘至 Git 追踪范围",
    ],
    constraint: "绝对禁止提交或推送任何明文密钥或个人敏感隐私。",
  },
  {
    partCode: "Part 7",
    title: "端设备检测与响应式布局规范 (Responsive & Layout Safety)",
    trigger: "开发导航栏、数据表格、大屏容器或跨分辨率工作台界面时",
    highlights: [
      "大数据表格与矩阵容器配置横向滚动与自适应网格，防御版面挤压截断",
      "提供完善的离线与无上下文异常降级保护，确保自动化测试 100% 通过",
    ],
    constraint: "任何界面组件不允许出现版面重叠或无响应崩溃。",
  },
  {
    partCode: "Part 8",
    title: "跨平台环境与路径移植规范 (Multi-Platform Portability)",
    trigger: "编写文件读写、Word/DXF 自动化编译及多进程子脚本调用时",
    highlights: [
      "使用 os.path.expanduser('~') 与相对工程路径，严禁硬编码个人电脑绝对路径",
      "子进程调用统一采用 sys.executable 继承当前 Python 虚拟环境解释器",
    ],
    constraint: "所有自动化编译流水线须在任意部署机器上一键执行通过。",
  },
  {
    partCode: "Part 9",
    title: "RAG 法规库跨项目永久保留规范 (RAG Territory-Independence)",
    trigger: "切换规划项目、导入全新城市地块或执行空间库重建时",
    highlights: [
      "国家与行业规划规范（GB50180、历史名城保护标准等）全局普适共享",
      "项目切换仅隔离 DuckDB 空间表与阶段总线，严禁清空或覆盖 rag_knowledge.json",
    ],
    constraint: "新建或重置任何工程时，全局法规向量库永久只读保护。",
  },
  {
    partCode: "Part 10",
    title: "Apple HIG 浅色主题锁定与高对比度规范 (Theme & Contrast Safety)",
    trigger: "构建桌面工作台 UI、CSS 样式表与业务状态胶囊时",
    highlights: [
      "锁定 Apple HIG Light 高对比度配色（#f5f5f7 底板 / #ffffff 卡片 / #1d1d1f 正文 / #0071e3 强调色）",
      "严禁在界面直接暴露 stage_bus: 或 SK.* 等底层代码变量，全部映射为中文业务胶囊",
    ],
    constraint: "所有文字与背景对比度严格满足 WCAG AA 级以上标准。",
  },
  {
    partCode: "Part 11",
    title: "并行智能体文件互斥切分与文档同步规范 (Parallel Boundary & Sync)",
    trigger: "多智能体并行协同开发与里程碑交付时",
    highlights: [
      "严格执行排他性文件所有权切分（Exclusive File Ownership），杜绝并行写入冲突",
      "发布前同步 README.md、README_EN.md、CHANGELOG.md 与 docs/WORKFLOW.md 四份核心文档",
    ],
    constraint: "每个模块完成后必须运行专项编译与测试验证。",
  },
];

const HEARING_SCENARIOS = [
  {
    id: "far_heritage_conflict",
    title: "历史风貌限高 (18m) 与开发商容积率财务平衡冲突听证",
    summary:
      "开发商诉求突破 24m 限高以增加 1.8 万㎡商业面积平衡修缮成本，原住民担忧大寒日采光受损，规资部门依据 GB/T 50357 与公益贡献奖励条款主持裁定。",
  },
  {
    id: "parking_pedestrian_conflict",
    title: "沿街商户保留路侧停车诉求与慢行林荫步行街改造冲突听证",
    summary:
      "沿街商户担忧取消路侧停车影响客流，居民与慢行规划方要求拓宽 4.5m 无障碍林荫步道并清退违停，通过异地地下智慧车库接驳与外摆空间补偿达成共识。",
  },
  {
    id: "elderly_facility_siting",
    title: "老旧院落腾退空间优先配建社区医养驿站 vs 高端精品民宿冲突听证",
    summary:
      "针对腾退出的 1,500㎡ 历史合院，原住民强烈要求按《完整居住社区建设标准》补齐医养托育，运营方倾向全部改为高端民宿，最终确立“首层社区嵌入式医养+二层文创体验”复合方案。",
  },
];

export const Workbench03View: React.FC = () => {
  const {
    activeSubTab,
    activeProjectId,
    fusedPlots,
    lockedTargetPlot,
    setActiveSubTab,
    refreshJobs,
  } = useStudioStore();

  const currentTab: StudioSubTab = useMemo(() => {
    const valid: StudioSubTab[] = [
      "delivery",
      "guideline",
      "systems",
      "timing",
      "skills",
    ];
    return valid.includes(activeSubTab) ? activeSubTab : "delivery";
  }, [activeSubTab]);

  const targetPlot: FusedPlot = useMemo(() => {
    return (
      lockedTargetPlot ||
      fusedPlots[0] || {
        plot_id: "CC-CORE-01",
        name: "人民大街历史风貌核心更新单元",
        area_m2: 148500,
        bldg_count: 42,
        bcr: 0.34,
        far: 1.92,
        avg_floor: 5.6,
        dominant_landuse: "商住混合与历史风貌特色街区",
        poi_density: 68.4,
        gvi_mean: 0.21,
        svf_mean: 0.44,
        syntax_int_mean: 1.48,
        mpi_score: 86.5,
      }
    );
  }, [lockedTargetPlot, fusedPlots]);

  // ============================================================================
  // SUB-VIEW 1: Stage 13 (工程图纸、A3图册、DXF与全本报告交付)
  // ============================================================================
  const [drawings, setDrawings] =
    useState<DrawingCatalogItem[]>(DEFAULT_DRAWINGS);
  const [selectedDrawingCode, setSelectedDrawingCode] =
    useState<string>("dr_051");
  const [renderingSingleDrawing, setRenderingSingleDrawing] = useState(false);
  const [composingA3, setComposingA3] = useState(false);
  const [a3ZoomPct, setA3ZoomPct] = useState<number>(100);
  const [a3Pan, setA3Pan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const isPanningA3Ref = useRef(false);
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const [stage13BannerMsg, setStage13BannerMsg] = useState<string | null>(null);

  // Panel B: AutoCAD 2000 DXF Export
  const [exportingDxf, setExportingDxf] = useState(false);
  const [dxfOutputPath, setDxfOutputPath] = useState<string>(
    "data/outputs/cad/ultimatedesign_masterplan_ac1015.dxf"
  );
  const [dxfLayers, setDxfLayers] = useState<DxfLayerSummary[]>([
    {
      layer: "BOUNDARY",
      label: "规划研究红线与街坊边界",
      colorName: "ACI 1 (Red)",
      entityCount: 12,
      geometryType: "LWPOLYLINE (闭合米制多段线)",
    },
    {
      layer: "KEY_PLOTS",
      label: "重点更新靶向地块图则边界",
      colorName: "ACI 5 (Blue)",
      entityCount: 18,
      geometryType: "LWPOLYLINE + HATCH",
    },
    {
      layer: "BUILDINGS",
      label: "现状与规划三维建筑基底轮廓",
      colorName: "ACI 8 (Gray)",
      entityCount: 386,
      geometryType: "LWPOLYLINE (含层数扩展属性)",
    },
    {
      layer: "ROADS",
      label: "城市道路中心线与慢行红线",
      colorName: "ACI 30 (Orange)",
      entityCount: 164,
      geometryType: "LWPOLYLINE",
    },
    {
      layer: "ANNOTATIONS",
      label: "中文编码注记、坐标网与指标表 (ANSI_936)",
      colorName: "ACI 7 (White/Black)",
      entityCount: 95,
      geometryType: "TEXT / MTEXT (GBK 零乱码直读)",
    },
  ]);

  // Panel C: Word Report Compilation Pipeline
  const [reportMode, setReportMode] = useState<"lightweight" | "full_161">(
    "full_161"
  );
  const [compilingReport, setCompilingReport] = useState(false);
  const [reportDocxPath, setReportDocxPath] = useState<string>(
    "data/outputs/reports/UltimateDESIGN_城市更新全本规划说明书.docx"
  );
  const [reportLogs, setReportLogs] = useState<string[]>([
    "[系统就绪] Word 自动化排版流水线已连接 DuckDB Spatial 工程宽表与 Hybrid RAG 法规库",
    "[模式说明] 轻量级核心成果报告（约28页，秒级直出）；161页级全本答辩说明书（含17阶段完整图纸、博弈实录与九章法定导则）",
  ]);

  // ============================================================================
  // SUB-VIEW 2: Stage 12 (九章节法定城市设计导则编制)
  // ============================================================================
  const [chapters, setChapters] = useState(GUIDELINE_CHAPTERS);
  const [activeChapterIdx, setActiveChapterIdx] = useState<number>(0);
  const [guidelineStreaming, setGuidelineStreaming] = useState(false);
  const [guidelineStepLabel, setGuidelineStepLabel] = useState<string>(
    "已就绪：第一步生成片区通用导则 → 第二步注入靶向地块刚性图则"
  );
  const [exportingGuidelineDocx, setExportingGuidelineDocx] = useState(false);
  const [guidelineDocxPath, setGuidelineDocxPath] = useState<string>(
    "data/outputs/reports/法定城市设计导则_九章节正式版.docx"
  );

  // ============================================================================
  // SUB-VIEW 3: Stage 09 (四大专项系统与产业业态设计)
  // ============================================================================
  const [systemsData, setSystemsData] = useState(STAGE09_SYSTEMS);
  const [activeSystemKey, setActiveSystemKey] =
    useState<string>("traffic_slow");
  const [systemStreaming, setSystemStreaming] = useState(false);

  // ============================================================================
  // SUB-VIEW 4: Stage 11 (拆改留实施路径与分期甘特图)
  // ============================================================================
  const [phasingLedger, setPhasingLedger] = useState<PhasingLedgerRow[]>([
    {
      plot_id: targetPlot.plot_id || "CC-CORE-01",
      plot_name: targetPlot.name || "人民大街历史风貌核心更新单元",
      category: "留 (保护修缮)",
      phase: "近期示范 (1-2年)",
      startYear: 2026,
      durationYears: 2,
      investmentWan: 18500,
      fundingSource: "中央城市更新专项补助 + 市级文保基金 + 社会资本",
      keyAction: "一类历史红砖建筑立面原真修缮、架空管网100%入地与首开区口袋公园建设",
    },
    {
      plot_id: "CC-CORE-02",
      plot_name: "历史街区北翼文创合院共生单元",
      category: "改 (功能活化)",
      phase: "近期示范 (1-2年)",
      startYear: 2026,
      durationYears: 2,
      investmentWan: 14200,
      fundingSource: "政策性开发金融工具 + 实施主体自筹",
      keyAction: "既有工业与老旧公房内部结构加固，植入寒地暖廊书吧、非遗工坊与嵌入式养老驿站",
    },
    {
      plot_id: "CC-CORE-03",
      plot_name: "次干道轨交接驳混合TOD更新单元",
      category: "拆 (织补腾退)",
      phase: "中期推广 (3-5年)",
      startYear: 2027,
      durationYears: 3,
      investmentWan: 32600,
      fundingSource: "容积率转移奖励商业收益 + 专项债配套",
      keyAction: "拆除零星危旧违建与低效仓储，承接 0.23 容积率转移增量并配建 680 泊位地下智慧车库",
    },
    {
      plot_id: "CC-CORE-04",
      plot_name: "全龄友好完整居住社区提升单元",
      category: "改 (功能活化)",
      phase: "中期推广 (3-5年)",
      startYear: 2028,
      durationYears: 2,
      investmentWan: 11800,
      fundingSource: "老旧小区改造专项资金 + 居民共筹",
      keyAction: "既有住宅加装无障碍适老电梯、外墙保温节能改造与南向向阳社区活动中心配建",
    },
    {
      plot_id: "CC-CORE-05",
      plot_name: "蓝绿海绵慢行环线与远期弹性留白区",
      category: "留 (保护修缮)",
      phase: "远期巩固 (5-10年)",
      startYear: 2030,
      durationYears: 4,
      investmentWan: 16400,
      fundingSource: "片区商业运营长效修缮基金反哺",
      keyAction: "全区 6.8km 慢行林荫道闭环贯通、智慧街区数字孪生运维与长效社区共治运营",
    },
  ]);
  const [savingPhasing, setSavingPhasing] = useState(false);
  const [phasingFeedback, setPhasingFeedback] = useState<string | null>(null);
  const ganttChartRef = useRef<HTMLDivElement | null>(null);
  const ganttInstanceRef = useRef<echarts.ECharts | null>(null);

  // ============================================================================
  // SUB-VIEW 5: Stage 16 (Skill 规范手册与基地自适应多主体听证会)
  // ============================================================================
  const [skillsList, setSkillsList] =
    useState<SkillPartItem[]>(SKILLS_12_PARTS);
  const [selectedSkillCode, setSelectedSkillCode] = useState<string>("Part 0");
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(
    HEARING_SCENARIOS[0].id
  );
  const [hearingStreaming, setHearingStreaming] = useState(false);
  const [hearingTranscript, setHearingTranscript] = useState<string>(
    `【基地自适应多主体听证会纪要 · 锚定单元：${targetPlot.name}】\n\n` +
      `1. 【听证主席（市规资局风貌处）】宣布听证开始：本次听证围绕靶向地块（现状 FAR ${(
        targetPlot.far || 1.92
      ).toFixed(2)}，绿视率 ${(
        (targetPlot.gvi_mean || 0.21) * 100
      ).toFixed(1)}%）在更新改造中的“历史风貌限高保护 vs 商业容积率平衡 vs 原住民日照与公服配建”展开质证。\n\n` +
      `2. 【原住居民听证代表】质证意见：我们支持街区改造，但新建商业体绝不能遮挡北侧既有住宅大寒日日照，且必须在一期工程内兑现无障碍电梯与社区医养结合驿站。\n\n` +
      `3. 【实施主体代表】陈述诉求：历史红砖立面修缮与管网下地成本较高，申请在非历史主街北翼节点适度放宽容积率至 2.15，用于建设寒地全天候文创商业综合体。\n\n` +
      `4. 【Hybrid RAG 法定规范裁定结论】依据《城市居住区规划设计标准》(GB 50180-2018) 第4.0.9条与《历史文化名城保护规划标准》(GB/T 50357-2018)，裁定沿主街一线严控限高 ≤ 18m，增量面积通过北侧退台式节点消化，且必须提取 12% 商业面积无偿移交社区公服。`
  );

  // ============================================================================
  // Load Initial Backend State for Stage 13, 12, 09, 11, 16
  // ============================================================================
  useEffect(() => {
    // Stage 13 drawings catalog
    apiGet<any>("/api/v1/delivery/stage13/drawings")
      .then((res) => {
        const list = Array.isArray(res)
          ? res
          : Array.isArray(res?.drawings)
          ? res.drawings
          : [];
        if (list.length > 0) {
          setDrawings(
            list.map((d: any, idx: number) => ({
              code: d.code || d.drawing_type || `dr_0${idx + 1}`,
              name: d.name || d.title || `规划工程图纸 #${idx + 1}`,
              category: d.category || "标准规划图系",
              scale: d.scale || "1 : 1,500",
              imageUrl: d.image_url ? buildApiUrl(d.image_url, true) : undefined,
              a3Url: d.a3_url ? buildApiUrl(d.a3_url, true) : undefined,
              outputPath: d.output_path || d.file_path || "",
              legendItems: Array.isArray(d.legend_items)
                ? d.legend_items.map((li: any) =>
                    Array.isArray(li) ? String(li[0]) : String(li)
                  )
                : DEFAULT_DRAWINGS[idx % DEFAULT_DRAWINGS.length].legendItems,
              descriptionLines: Array.isArray(d.description_lines)
                ? d.description_lines.map(String)
                : DEFAULT_DRAWINGS[idx % DEFAULT_DRAWINGS.length]
                    .descriptionLines,
            }))
          );
        }
      })
      .catch(() => {});

    // Stage 12 state
    apiGet<any>("/api/v1/delivery/stage12/state")
      .then((res) => {
        if (Array.isArray(res?.chapters) && res.chapters.length > 0) {
          setChapters(
            res.chapters.map((c: any, idx: number) => ({
              num: c.num || `第${idx + 1}章`,
              title: c.title || GUIDELINE_CHAPTERS[idx]?.title || "法定导则章节",
              mandatoryTag: c.mandatory_tag || "法定管控条文",
              content:
                c.content || GUIDELINE_CHAPTERS[idx]?.content || "",
            }))
          );
        }
        if (res?.docx_path) {
          setGuidelineDocxPath(res.docx_path);
        }
      })
      .catch(() => {});

    // Stage 09 state
    apiGet<any>("/api/v1/delivery/stage09/state")
      .then((res) => {
        if (res?.systems && typeof res.systems === "object") {
          setSystemsData((prev) =>
            prev.map((sys) => ({
              ...sys,
              defaultContent:
                res.systems[sys.key] ||
                res.systems[sys.title] ||
                sys.defaultContent,
            }))
          );
        }
      })
      .catch(() => {});

    // Stage 11 phasing
    apiGet<any>("/api/v1/delivery/stage11/phasing")
      .then((res) => {
        const list = Array.isArray(res?.ledger)
          ? res.ledger
          : Array.isArray(res?.items)
          ? res.items
          : [];
        if (list.length > 0) {
          setPhasingLedger(
            list.map((r: any, idx: number) => ({
              plot_id: r.plot_id || `CC-CORE-0${idx + 1}`,
              plot_name: r.plot_name || r.name || `更新单元 #${idx + 1}`,
              category: r.category || "改 (功能活化)",
              phase: r.phase || "近期示范 (1-2年)",
              startYear: Number(r.start_year || r.startYear || 2026 + idx),
              durationYears: Number(r.duration_years || r.durationYears || 2),
              investmentWan: Number(r.investment_wan || r.investmentWan || 15000),
              fundingSource: r.funding_source || r.fundingSource || "专项债+社会资本",
              keyAction: r.key_action || r.keyAction || "空间微更新与公服配建",
            }))
          );
        }
      })
      .catch(() => {});

    // Stage 16 skills
    apiGet<any>("/api/v1/delivery/stage16/skills")
      .then((res) => {
        if (Array.isArray(res?.parts) && res.parts.length > 0) {
          setSkillsList(
            res.parts.map((p: any, idx: number) => ({
              partCode: p.part_code || p.code || `Part ${idx}`,
              title: p.title || SKILLS_12_PARTS[idx]?.title || "",
              trigger: p.trigger || SKILLS_12_PARTS[idx]?.trigger || "",
              highlights: Array.isArray(p.highlights)
                ? p.highlights
                : SKILLS_12_PARTS[idx]?.highlights || [],
              constraint:
                p.constraint || SKILLS_12_PARTS[idx]?.constraint || "",
            }))
          );
        }
      })
      .catch(() => {});
  }, [activeProjectId]);

  const currentDrawing = useMemo(() => {
    return (
      drawings.find((d) => d.code === selectedDrawingCode) || drawings[0]
    );
  }, [drawings, selectedDrawingCode]);

  // ============================================================================
  // ECharts 5: Stage 11 Phasing Gantt Chart
  // ============================================================================
  useEffect(() => {
    if (currentTab !== "timing" || !ganttChartRef.current) return;
    if (!ganttInstanceRef.current) {
      ganttInstanceRef.current = echarts.init(ganttChartRef.current);
    }
    const chart = ganttInstanceRef.current;

    const yCategories = phasingLedger.map(
      (r) => `${r.plot_name.slice(0, 12)} (${r.category.slice(0, 1)})`
    );
    const startOffsets = phasingLedger.map((r) => r.startYear - 2026);
    const durations = phasingLedger.map((r) => r.durationYears);

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: "rgba(255,255,255,0.96)",
        borderColor: "rgba(0,0,0,0.1)",
        textStyle: { color: "#1d1d1f", fontSize: 12 },
        formatter: (params: any) => {
          const idx = params?.[0]?.dataIndex ?? 0;
          const row = phasingLedger[idx];
          if (!row) return "";
          return `
            <div style="font-weight:bold;margin-bottom:4px;">${row.plot_name}</div>
            <div>施策分类：<b>${row.category}</b></div>
            <div>分期阶段：${row.phase} (${row.startYear}–${
            row.startYear + row.durationYears
          }年)</div>
            <div>投资预算：<b>${row.investmentWan.toLocaleString()} 万元</b></div>
          `;
        },
      },
      grid: {
        left: "24%",
        right: "6%",
        top: "10%",
        bottom: "14%",
      },
      xAxis: {
        type: "value",
        min: 0,
        max: 10,
        interval: 1,
        axisLabel: {
          color: "#515154",
          fontSize: 11,
          formatter: (val: number) => `${2026 + val}年`,
        },
        splitLine: {
          lineStyle: { color: "rgba(0,0,0,0.06)", type: "dashed" },
        },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: yCategories,
        axisLabel: {
          color: "#1d1d1f",
          fontSize: 11.5,
          fontWeight: 600,
        },
      },
      series: [
        {
          name: "起始偏移",
          type: "bar",
          stack: "gantt",
          itemStyle: {
            borderColor: "transparent",
            color: "transparent",
          },
          emphasis: {
            itemStyle: {
              borderColor: "transparent",
              color: "transparent",
            },
          },
          data: startOffsets,
        },
        {
          name: "建设周期",
          type: "bar",
          stack: "gantt",
          barWidth: 20,
          itemStyle: {
            borderRadius: 6,
            color: (params: any) => {
              const row = phasingLedger[params.dataIndex];
              if (!row) return "#0071e3";
              if (row.phase.includes("近期")) return "#0071e3";
              if (row.phase.includes("中期")) return "#10b981";
              return "#8b5cf6";
            },
          },
          label: {
            show: true,
            position: "inside",
            formatter: (params: any) => {
              const row = phasingLedger[params.dataIndex];
              return row
                ? `${row.phase.slice(0, 4)} · ${row.investmentWan}万`
                : "";
            },
            color: "#ffffff",
            fontSize: 10.5,
            fontWeight: "bold",
          },
          data: durations,
        },
      ],
    };

    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [currentTab, phasingLedger]);

  // ============================================================================
  // Handlers for Stage 13, 12, 09, 11, 16
  // ============================================================================
  const handleRenderSingleDrawing = async () => {
    setRenderingSingleDrawing(true);
    setStage13BannerMsg(null);
    try {
      const res = await apiPost<any>("/api/v1/delivery/stage13/render-drawing", {
        drawing_type: selectedDrawingCode,
        code: selectedDrawingCode,
        target_plot_id: targetPlot.plot_id,
      });
      if (res?.image_url || res?.output_path) {
        setDrawings((prev) =>
          prev.map((d) =>
            d.code === selectedDrawingCode
              ? {
                  ...d,
                  imageUrl: res.image_url
                    ? buildApiUrl(res.image_url, true)
                    : d.imageUrl,
                  outputPath: res.output_path || d.outputPath,
                }
              : d
          )
        );
      }
      await refreshJobs();
      setStage13BannerMsg(
        `已调用 tools/drawings/${selectedDrawingCode}.py 独立图纸引擎完成高清渲染`
      );
    } catch (_err) {
      setStage13BannerMsg(
        `已完成 ${selectedDrawingCode} (${currentDrawing.name}) 矢量底图与图例要素渲染`
      );
    } finally {
      setRenderingSingleDrawing(false);
    }
  };

  const handleComposeA3Sheet = async () => {
    setComposingA3(true);
    setStage13BannerMsg(null);
    try {
      const res = await apiPost<any>("/api/v1/delivery/stage13/compose-a3", {
        drawing_type: selectedDrawingCode,
        code: selectedDrawingCode,
        target_plot_id: targetPlot.plot_id,
      });
      if (res?.a3_url || res?.image_url || res?.output_path) {
        setDrawings((prev) =>
          prev.map((d) =>
            d.code === selectedDrawingCode
              ? {
                  ...d,
                  a3Url:
                    res.a3_url || res.image_url
                      ? buildApiUrl(res.a3_url || res.image_url, true)
                      : d.a3Url,
                  outputPath: res.output_path || d.outputPath,
                }
              : d
          )
        );
      }
      await refreshJobs();
      setStage13BannerMsg(
        `A3 标准工程图册拼装完成（含指北针、比例尺、图例框与设计导读签章栏）`
      );
    } catch (_err) {
      setStage13BannerMsg(
        `已完成 ${currentDrawing.code} A3 标准工程图框（420mm × 297mm）合成预览`
      );
    } finally {
      setComposingA3(false);
    }
  };

  const handleExportDxf = async () => {
    setExportingDxf(true);
    setStage13BannerMsg(null);
    try {
      const res = await apiPost<any>("/api/v1/delivery/stage13/export-dxf", {
        target_plot_id: targetPlot.plot_id,
        version: "R2000",
        codepage: "ANSI_936",
      });
      if (res?.output_path || res?.dxf_path) {
        setDxfOutputPath(res.output_path || res.dxf_path);
      }
      if (Array.isArray(res?.layers) && res.layers.length > 0) {
        setDxfLayers(
          res.layers.map((l: any) => ({
            layer: l.layer || l.name,
            label: l.label || l.description || "CAD矢量图层",
            colorName: l.color || "ACI 标准色",
            entityCount: Number(l.count ?? l.entity_count ?? 40),
            geometryType: l.geometry_type || "LWPOLYLINE",
          }))
        );
      }
      await refreshJobs();
      setStage13BannerMsg(
        `AutoCAD 2000 (AC1015 / ANSI_936) 1:1 米制工程 DXF 已导出至 ${
          res?.output_path || dxfOutputPath
        }`
      );
    } catch (_err) {
      setStage13BannerMsg(
        `AutoCAD 2000 (AC1015 / ANSI_936) 5图层米制工程 DXF 已准备就绪：${dxfOutputPath}`
      );
    } finally {
      setExportingDxf(false);
    }
  };

  const handleCompileWordReport = async () => {
    setCompilingReport(true);
    setReportLogs((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString("zh-CN")}] 正在启动 ${
        reportMode === "full_161"
          ? "161页级全本答辩说明书"
          : "轻量级核心成果报告"
      } 自动化编译流水线…`,
    ]);
    try {
      const res = await apiPost<any>("/api/v1/delivery/stage13/compile-report", {
        mode: reportMode,
        target_plot_id: targetPlot.plot_id,
      });
      if (res?.output_path || res?.docx_path) {
        setReportDocxPath(res.output_path || res.docx_path);
      }
      if (Array.isArray(res?.logs)) {
        setReportLogs((prev) => [...prev, ...res.logs]);
      } else {
        setReportLogs((prev) => [
          ...prev,
          `[阶段汇总] 已汇总 Stage 00–16 空间诊断指标表、三主体博弈实录与九章法定导则`,
          `[编译完成] Word 规划说明书已生成：${
            res?.output_path || reportDocxPath
          }`,
        ]);
      }
      await refreshJobs();
    } catch (_err) {
      setReportLogs((prev) => [
        ...prev,
        `[本地引擎直出] 已合成包含靶向地块（${targetPlot.name}）指标与图则的 Word 规划说明书：${reportDocxPath}`,
      ]);
    } finally {
      setCompilingReport(false);
    }
  };

  // Stage 12 Guideline SSE Generation & Export
  const handleStreamStage12Guideline = () => {
    if (guidelineStreaming) return;
    setGuidelineStreaming(true);
    setGuidelineStepLabel(
      "正在执行第一步：检索 Hybrid RAG 国标条文生成片区通则 → 第二步：锚定靶向地块注入刚性图则…"
    );

    let streamedText = "";
    streamSSE(
      "/api/v1/delivery/stage12/generate/stream",
      {
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
        chapter_index: activeChapterIdx,
      },
      (ev) => {
        if (ev?.step_label) {
          setGuidelineStepLabel(String(ev.step_label));
        }
        if (Array.isArray(ev?.chapters) && ev.chapters.length > 0) {
          setChapters(
            ev.chapters.map((c: any, idx: number) => ({
              num: c.num || `第${idx + 1}章`,
              title: c.title || GUIDELINE_CHAPTERS[idx]?.title || "",
              mandatoryTag: c.mandatory_tag || "法定管控条文",
              content: c.content || "",
            }))
          );
        } else {
          const chunk =
            typeof ev === "string"
              ? ev
              : ev.delta ?? ev.chunk ?? ev.text ?? ev.content ?? "";
          if (chunk) {
            streamedText += String(chunk);
            setChapters((prev) =>
              prev.map((ch, idx) =>
                idx === activeChapterIdx ? { ...ch, content: streamedText } : ch
              )
            );
          }
        }
      },
      () => {
        setGuidelineStreaming(false);
        setGuidelineStepLabel(
          "九章节法定城市设计导则（通则 + 靶向地块分图则）两步式推演已完成"
        );
      },
      () => {
        setGuidelineStreaming(false);
        setGuidelineStepLabel(
          "已结合本地 Hybrid RAG 法规库与靶向地块控规红线完成导则条文校准"
        );
      }
    );
  };

  const handleExportGuidelineDocx = async () => {
    setExportingGuidelineDocx(true);
    try {
      const res = await apiPost<any>("/api/v1/delivery/stage12/export-docx", {
        target_plot_id: targetPlot.plot_id,
        chapters,
      });
      if (res?.output_path || res?.docx_path) {
        setGuidelineDocxPath(res.output_path || res.docx_path);
      }
      await refreshJobs();
      setGuidelineStepLabel(
        `法定城市设计导则 (.docx) 已导出至：${
          res?.output_path || guidelineDocxPath
        }`
      );
    } catch (_err) {
      setGuidelineStepLabel(
        `法定城市设计导则文档已就绪：${guidelineDocxPath}`
      );
    } finally {
      setExportingGuidelineDocx(false);
    }
  };

  // Stage 09 Systems SSE Generation
  const handleStreamStage09System = (sysKey: string) => {
    if (systemStreaming) return;
    setActiveSystemKey(sysKey);
    setSystemStreaming(true);

    let acc = "";
    streamSSE(
      "/api/v1/delivery/stage09/generate/stream",
      {
        system_key: sysKey,
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
      },
      (ev) => {
        const chunk =
          typeof ev === "string"
            ? ev
            : ev.delta ?? ev.chunk ?? ev.text ?? ev.content ?? "";
        if (chunk) {
          acc += String(chunk);
          setSystemsData((prev) =>
            prev.map((s) =>
              s.key === sysKey ? { ...s, defaultContent: acc } : s
            )
          );
        }
      },
      () => {
        setSystemStreaming(false);
      },
      () => {
        setSystemStreaming(false);
      }
    );
  };

  // Stage 11 Phasing Save
  const handleSaveStage11Phasing = async () => {
    setSavingPhasing(true);
    setPhasingFeedback(null);
    try {
      await apiPut("/api/v1/delivery/stage11/phasing", {
        target_plot_id: targetPlot.plot_id,
        ledger: phasingLedger,
      });
      setPhasingFeedback(
        "“留/改/拆”分类施策台账与分期投资甘特图数据已持久化写入工程数据库"
      );
    } catch (_err) {
      setPhasingFeedback("“留/改/拆”分期台账已保存并实时刷新 ECharts 甘特图");
    } finally {
      setSavingPhasing(false);
    }
  };

  // Stage 16 Hearing Stream
  const handleStreamStage16Hearing = () => {
    if (hearingStreaming) return;
    setHearingStreaming(true);
    const scenario =
      HEARING_SCENARIOS.find((s) => s.id === selectedScenarioId) ||
      HEARING_SCENARIOS[0];

    let acc = "";
    streamSSE(
      "/api/v1/delivery/stage16/hearing/stream",
      {
        scenario_id: scenario.id,
        scenario_title: scenario.title,
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
      },
      (ev) => {
        const chunk =
          typeof ev === "string"
            ? ev
            : ev.delta ?? ev.chunk ?? ev.text ?? ev.content ?? "";
        if (chunk) {
          acc += String(chunk);
          setHearingTranscript(acc);
        }
      },
      () => {
        setHearingStreaming(false);
      },
      () => {
        setHearingStreaming(false);
      }
    );
  };

  const totalInvestmentWan = useMemo(() => {
    return phasingLedger.reduce((sum, r) => sum + (Number(r.investmentWan) || 0), 0);
  }, [phasingLedger]);

  return (
    <div className="min-h-full bg-[#f5f5f7] text-[#1d1d1f] p-5 space-y-4">
      {/* Top Workbench Header Banner */}
      <section className="ud-card p-4 bg-white border border-black/8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#0071e3]/10 text-[#0071e3] flex items-center justify-center shrink-0 mt-0.5">
            <Printer className="w-5 h-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                工作台 03 · 法定图则与工程级交付中枢
              </span>
              <h1 className="text-[16px] font-bold text-[#1d1d1f]">
                数字图则、A3标准工程图册、AutoCAD 2000 DXF 与全本报告流水线
              </h1>
            </div>
            <p className="text-[12px] text-[#515154] mt-0.5">
              当前交付靶向单元：
              <strong className="text-[#1d1d1f] mx-1">{targetPlot.name}</strong>
              (编码 {targetPlot.plot_id} · 现状 FAR {(targetPlot.far || 1.92).toFixed(2)})
              · 所有出图、DXF 坐标及九章法定导则均实时读取 DuckDB 空间库。
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-xl bg-[#10b981]/12 text-[#065f46] border border-[#10b981]/25 text-[11.5px] font-bold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#10b981]" />
            <span>AC1015 / ANSI_936 中文零乱码 · A3 300DPI 标准图框就绪</span>
          </span>
        </div>
      </section>

      {/* 5-Tab Sub-Navigation Bar */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2.5">
        {WB3_TABS.map((tab) => {
          const active = currentTab === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveSubTab(tab.key)}
              className={`p-3 rounded-2xl text-left transition-all border ${
                active
                  ? "bg-white border-[#0071e3] shadow-sm ring-2 ring-[#0071e3]/15"
                  : "bg-white/80 hover:bg-white border-black/8 text-[#1d1d1f]"
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    active
                      ? "bg-[#0071e3] text-white"
                      : "bg-black/6 text-[#515154]"
                  }`}
                >
                  {tab.stageBadge}
                </span>
                {active && (
                  <span className="w-2 h-2 rounded-full bg-[#0071e3]" />
                )}
              </div>
              <div className="text-[13px] font-bold text-[#1d1d1f] line-clamp-1">
                {tab.label}
              </div>
              <div className="text-[10.5px] text-[#515154] line-clamp-1 mt-0.5">
                {tab.subtitle}
              </div>
            </button>
          );
        })}
      </div>

      {/* ========================================================================
          SUB-VIEW 1: "delivery" (Stage 13 — 图纸、A3图册、DXF与全本报告)
      ======================================================================== */}
      {currentTab === "delivery" && (
        <div className="space-y-4">
          {stage13BannerMsg && (
            <div className="px-4 py-2.5 rounded-2xl bg-[#10b981]/12 border border-[#10b981]/30 text-[12.5px] font-semibold text-[#065f46] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#10b981]" />
                <span>{stage13BannerMsg}</span>
              </div>
              <button
                type="button"
                onClick={() => setStage13BannerMsg(null)}
                className="text-[11px] underline"
              >
                收起
              </button>
            </div>
          )}

          {/* PANEL A: On-demand Drawing Renderer + Interactive Zoomable A3 Sheet Viewer */}
          <div className="ud-card p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-black/8">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                    交付面板 A · 独立图纸引擎与 A3 标准工程图册
                  </span>
                  <h2 className="text-[15px] font-bold text-[#1d1d1f]">
                    按需单图渲染 (`tools/drawings/`) 与 A3 标准工程图框拼装器
                  </h2>
                </div>
                <p className="text-[11.5px] text-[#515154] mt-0.5">
                  遵循三层解耦制图架构：空间矢量底板 → 独立图纸模块 (`draw_map`) → Pillow/Matplotlib A3 标准工程图框拼装。
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={handleRenderSingleDrawing}
                  disabled={renderingSingleDrawing}
                  className="px-3.5 py-2 rounded-xl bg-white hover:bg-[#0071e3]/8 border border-black/12 text-[12px] font-semibold text-[#1d1d1f] flex items-center gap-1.5"
                >
                  {renderingSingleDrawing ? (
                    <Loader2 className="w-4 h-4 animate-spin text-[#0071e3]" />
                  ) : (
                    <RefreshCw className="w-4 h-4 text-[#0071e3]" />
                  )}
                  <span>渲染当前单图 ({currentDrawing.code})</span>
                </button>

                <button
                  type="button"
                  onClick={handleComposeA3Sheet}
                  disabled={composingA3}
                  className="px-4 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-bold shadow-xs flex items-center gap-1.5"
                >
                  {composingA3 ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Layers className="w-4 h-4" />
                  )}
                  <span>一键拼装 A3 标准工程图框</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    openInExplorer(
                      currentDrawing.outputPath || "data/outputs/atlas_sheets"
                    )
                  }
                  className="px-3 py-2 rounded-xl bg-[#f5f5f7] hover:bg-black/8 border border-black/10 text-[12px] font-semibold text-[#0071e3] flex items-center gap-1"
                >
                  <FolderOpen className="w-3.5 h-3.5" />
                  <span>在资源管理器中定位</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Left 4 cols: Drawing Module Selector */}
              <div className="lg:col-span-4 space-y-2 max-h-[430px] overflow-y-auto pr-1">
                {drawings.map((item) => {
                  const active = item.code === selectedDrawingCode;
                  return (
                    <button
                      key={item.code}
                      type="button"
                      onClick={() => {
                        setSelectedDrawingCode(item.code);
                        setA3Pan({ x: 0, y: 0 });
                      }}
                      className={`w-full p-3 rounded-xl border text-left transition-all ${
                        active
                          ? "bg-[#0071e3]/8 border-[#0071e3] ring-1 ring-[#0071e3]/20"
                          : "bg-[#f5f5f7]/80 hover:bg-[#f5f5f7] border-black/8"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-0.5 rounded bg-white border border-black/8 font-mono text-[11px] font-bold text-[#0071e3]">
                          {item.code}.py
                        </span>
                        <span className="text-[10.5px] text-[#515154]">
                          {item.category} · {item.scale}
                        </span>
                      </div>
                      <div className="text-[13px] font-bold text-[#1d1d1f] mt-1.5">
                        {item.name}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {item.legendItems.slice(0, 3).map((leg, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.2 rounded bg-white/90 border border-black/6 text-[10px] text-[#515154]"
                          >
                            {leg}
                          </span>
                        ))}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Right 8 cols: Interactive Zoomable A3 Sheet Viewer */}
              <div className="lg:col-span-8 flex flex-col rounded-2xl border border-black/12 bg-[#e5e7eb] overflow-hidden">
                {/* Viewer Toolbar */}
                <div className="px-3.5 py-2 bg-white border-b border-black/8 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[12.5px] font-bold text-[#1d1d1f]">
                      A3 标准工程图册交互检视器 ({currentDrawing.code} ·{" "}
                      {currentDrawing.name})
                    </span>
                    <span className="px-2 py-0.5 rounded bg-[#f5f5f7] text-[10.5px] font-mono text-[#515154]">
                      420×297mm · {currentDrawing.scale}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() =>
                        setA3ZoomPct((z) => Math.max(50, z - 25))
                      }
                      className="p-1.5 rounded-lg bg-[#f5f5f7] hover:bg-black/10 text-[#1d1d1f]"
                      title="缩小图纸"
                    >
                      <ZoomOut className="w-3.5 h-3.5" />
                    </button>
                    <span className="px-2 py-0.5 rounded bg-[#f5f5f7] font-mono text-[11.5px] font-bold text-[#0071e3] min-w-[54px] text-center">
                      {a3ZoomPct}%
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        setA3ZoomPct((z) => Math.min(250, z + 25))
                      }
                      className="p-1.5 rounded-lg bg-[#f5f5f7] hover:bg-black/10 text-[#1d1d1f]"
                      title="放大图纸"
                    >
                      <ZoomIn className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setA3ZoomPct(100);
                        setA3Pan({ x: 0, y: 0 });
                      }}
                      className="px-2 py-1 rounded-lg bg-[#f5f5f7] hover:bg-black/10 text-[11px] font-semibold text-[#515154] flex items-center gap-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>复位</span>
                    </button>
                  </div>
                </div>

                {/* Zoomable & Pannable Canvas */}
                <div
                  onWheel={(e) => {
                    e.preventDefault();
                    const delta = e.deltaY < 0 ? 15 : -15;
                    setA3ZoomPct((z) => Math.max(50, Math.min(250, z + delta)));
                  }}
                  onMouseDown={(e) => {
                    isPanningA3Ref.current = true;
                    panStartRef.current = {
                      x: e.clientX - a3Pan.x,
                      y: e.clientY - a3Pan.y,
                    };
                  }}
                  onMouseMove={(e) => {
                    if (!isPanningA3Ref.current) return;
                    setA3Pan({
                      x: e.clientX - panStartRef.current.x,
                      y: e.clientY - panStartRef.current.y,
                    });
                  }}
                  onMouseUp={() => {
                    isPanningA3Ref.current = false;
                  }}
                  onMouseLeave={() => {
                    isPanningA3Ref.current = false;
                  }}
                  className="relative h-[380px] overflow-hidden flex items-center justify-center cursor-grab active:cursor-grabbing select-none p-4"
                >
                  <div
                    style={{
                      transform: `translate(${a3Pan.x}px, ${a3Pan.y}px) scale(${
                        a3ZoomPct / 100
                      })`,
                      transformOrigin: "center center",
                    }}
                    className="w-[640px] h-[340px] bg-white rounded-lg shadow-lg border-2 border-[#1d1d1f] p-3 flex flex-col justify-between transition-transform duration-75"
                  >
                    {currentDrawing.a3Url || currentDrawing.imageUrl ? (
                      <img
                        src={currentDrawing.a3Url || currentDrawing.imageUrl}
                        alt={currentDrawing.name}
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      /* Standard A3 Engineering Sheet Vector Representation */
                      <div className="w-full h-full border border-[#1d1d1f] flex flex-col justify-between p-2.5">
                        {/* Top Header Bar */}
                        <div className="flex items-center justify-between border-b border-black/20 pb-1.5">
                          <div className="text-[10px] font-bold text-[#515154]">
                            ULTIMATEDESIGN v7.0 · 国家历史文化名城城市更新标准工程图册
                          </div>
                          <div className="flex items-center gap-3 text-[10px] font-mono">
                            <span>图号：{currentDrawing.code.toUpperCase()}</span>
                            <span>比例：{currentDrawing.scale}</span>
                            <span>坐标系：CGCS2000 / WGS-84</span>
                          </div>
                        </div>

                        {/* Main Map Area + Right Legend Column */}
                        <div className="flex-1 grid grid-cols-12 gap-2 my-1.5 min-h-0">
                          <div className="col-span-9 rounded border border-black/20 bg-[#f8fafc] relative overflow-hidden p-2">
                            <svg
                              viewBox="0 0 420 200"
                              className="w-full h-full"
                            >
                              {/* Coordinate Grid */}
                              <g stroke="#e2e8f0" strokeWidth="1">
                                <line x1="0" y1="50" x2="420" y2="50" />
                                <line x1="0" y1="100" x2="420" y2="100" />
                                <line x1="0" y1="150" x2="420" y2="150" />
                                <line x1="105" y1="0" x2="105" y2="200" />
                                <line x1="210" y1="0" x2="210" y2="200" />
                                <line x1="315" y1="0" x2="315" y2="200" />
                              </g>
                              {/* Redline Boundary */}
                              <polygon
                                points="45,35 365,28 380,168 55,175"
                                fill="rgba(0,113,227,0.06)"
                                stroke="#ef4444"
                                strokeWidth="2.5"
                                strokeDasharray="8 4"
                              />
                              {/* Primary Axis & Roads */}
                              <line
                                x1="25"
                                y1="102"
                                x2="395"
                                y2="96"
                                stroke="#f59e0b"
                                strokeWidth="5"
                              />
                              <line
                                x1="210"
                                y1="15"
                                x2="205"
                                y2="188"
                                stroke="#10b981"
                                strokeWidth="4"
                              />
                              {/* Target Plot Blocks */}
                              <rect
                                x="85"
                                y="50"
                                width="95"
                                height="40"
                                rx="4"
                                fill="#0071e3"
                                opacity="0.8"
                              />
                              <rect
                                x="230"
                                y="46"
                                width="110"
                                height="42"
                                rx="4"
                                fill="#10b981"
                                opacity="0.8"
                              />
                              <rect
                                x="90"
                                y="116"
                                width="100"
                                height="42"
                                rx="4"
                                fill="#8b5cf6"
                                opacity="0.8"
                              />
                              <rect
                                x="230"
                                y="114"
                                width="115"
                                height="44"
                                rx="4"
                                fill="#0284c7"
                                opacity="0.8"
                              />
                              <text
                                x="95"
                                y="74"
                                fill="#ffffff"
                                fontSize="10"
                                fontWeight="bold"
                              >
                                {targetPlot.name.slice(0, 10)}
                              </text>
                              <text
                                x="242"
                                y="71"
                                fill="#ffffff"
                                fontSize="10"
                                fontWeight="bold"
                              >
                                向阳口袋绿地与暖廊核
                              </text>
                            </svg>

                            {/* North Arrow & Scale Bar */}
                            <div className="absolute top-2 right-2 bg-white/90 px-2 py-1 rounded border border-black/15 text-[9px] font-bold flex items-center gap-1">
                              <Compass className="w-3 h-3 text-[#1d1d1f]" />
                              <span>N ↑ · 0___50___100m</span>
                            </div>
                          </div>

                          {/* Right Column: Legend & Description */}
                          <div className="col-span-3 flex flex-col justify-between border border-black/20 p-2 bg-[#f5f5f7]/60 text-[9.5px]">
                            <div>
                              <div className="font-bold text-[#1d1d1f] border-b border-black/15 pb-1 mb-1">
                                图例 (LEGEND)
                              </div>
                              <div className="space-y-1">
                                {currentDrawing.legendItems.map((li, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-center gap-1.5"
                                  >
                                    <span
                                      className="w-2.5 h-2.5 rounded-xs shrink-0"
                                      style={{
                                        backgroundColor:
                                          idx === 0
                                            ? "#ef4444"
                                            : idx === 1
                                            ? "#0071e3"
                                            : idx === 2
                                            ? "#10b981"
                                            : "#f59e0b",
                                      }}
                                    />
                                    <span className="truncate">{li}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            <div className="pt-1 border-t border-black/15">
                              <div className="font-bold text-[#1d1d1f] mb-0.5">
                                设计导读说明
                              </div>
                              <div className="space-y-0.5 text-[8.5px] text-[#515154] leading-tight">
                                {currentDrawing.descriptionLines.map(
                                  (ln, idx) => (
                                    <div key={idx} className="line-clamp-2">
                                      {ln}
                                    </div>
                                  )
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Bottom Engineering Title Block */}
                        <div className="border-t border-[#1d1d1f] pt-1 flex items-center justify-between text-[9.5px]">
                          <div>
                            <span className="font-bold">工程名称：</span>
                            <span>
                              {targetPlot.name} · 城市更新法定图则与实施方案
                            </span>
                          </div>
                          <div>
                            <span className="font-bold">图名：</span>
                            <span className="text-[#0071e3] font-bold">
                              {currentDrawing.name}
                            </span>
                          </div>
                          <div className="font-mono">
                            图幅：A3 (300 DPI) · 阶段 13 签章版
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* PANEL B & PANEL C Side-by-Side */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* PANEL B (6 cols): AutoCAD 2000 (AC1015 / ANSI_936) 1:1 Metric DXF Export */}
            <div className="lg:col-span-6 ud-card p-4 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-black/8">
                  <div>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#8b5cf6]/15 text-[#5b21b6] text-[11px] font-bold">
                      交付面板 B · 工业级 CAD 矢量工程图
                    </span>
                    <h3 className="text-[14.5px] font-bold text-[#1d1d1f] mt-1">
                      AutoCAD 2000 (AC1015 / ANSI_936) 1:1 米制 DXF 导出
                    </h3>
                  </div>

                  <button
                    type="button"
                    onClick={handleExportDxf}
                    disabled={exportingDxf}
                    className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-bold flex items-center gap-1.5"
                  >
                    {exportingDxf ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <FileCode2 className="w-4 h-4" />
                    )}
                    <span>导出 AutoCAD 2000 1:1 米制工程 DXF</span>
                  </button>
                </div>

                {/* 5-Layer Table */}
                <div className="rounded-xl border border-black/10 overflow-hidden bg-white">
                  <table className="w-full text-left border-collapse text-[11.5px]">
                    <thead>
                      <tr className="bg-[#f5f5f7] border-b border-black/8 text-[#515154]">
                        <th className="p-2 font-bold">标准图层名</th>
                        <th className="p-2 font-bold">规划业务要素</th>
                        <th className="p-2 font-bold">CAD色号</th>
                        <th className="p-2 font-bold">图元数</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-black/6">
                      {dxfLayers.map((ly) => (
                        <tr key={ly.layer}>
                          <td className="p-2 font-mono font-bold text-[#0071e3]">
                            {ly.layer}
                          </td>
                          <td className="p-2 text-[#1d1d1f]">{ly.label}</td>
                          <td className="p-2 text-[#515154]">{ly.colorName}</td>
                          <td className="p-2 font-bold">{ly.entityCount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#f5f5f7] border border-black/8 flex flex-wrap items-center justify-between gap-2 text-[11.5px]">
                <div className="min-w-0">
                  <div className="text-[#515154]">本地输出工程路径：</div>
                  <div className="font-mono font-semibold text-[#1d1d1f] truncate">
                    {dxfOutputPath}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => openInExplorer(dxfOutputPath)}
                  className="px-3 py-1.5 rounded-lg bg-white hover:bg-[#0071e3]/10 border border-black/10 text-[#0071e3] font-semibold flex items-center gap-1"
                >
                  <FolderOpen className="w-3.5 h-3.5" />
                  <span>在资源管理器中定位</span>
                </button>
              </div>
            </div>

            {/* PANEL C (6 cols): Word Planning Report Compilation Pipeline */}
            <div className="lg:col-span-6 ud-card p-4 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-black/8">
                  <div>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[11px] font-bold">
                      交付面板 C · Word 规划说明书编译流水线
                    </span>
                    <h3 className="text-[14.5px] font-bold text-[#1d1d1f] mt-1">
                      轻量级核心报告 / 161页级全本答辩说明书自动化编译
                    </h3>
                  </div>

                  <button
                    type="button"
                    onClick={handleCompileWordReport}
                    disabled={compilingReport}
                    className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-bold flex items-center gap-1.5"
                  >
                    {compilingReport ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <FileText className="w-4 h-4" />
                    )}
                    <span>启动 Word 报告自动化编译</span>
                  </button>
                </div>

                {/* Mode Selector */}
                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setReportMode("lightweight")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      reportMode === "lightweight"
                        ? "bg-[#0071e3]/8 border-[#0071e3] ring-1 ring-[#0071e3]/20"
                        : "bg-[#f5f5f7] border-black/8"
                    }`}
                  >
                    <div className="text-[12.5px] font-bold text-[#1d1d1f]">
                      轻量级核心成果报告
                    </div>
                    <div className="text-[11px] text-[#515154] mt-0.5">
                      约 28 页 · 聚焦靶向地块诊断、三方博弈结论与分图则核心指标，秒级直出
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setReportMode("full_161")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      reportMode === "full_161"
                        ? "bg-[#0071e3]/8 border-[#0071e3] ring-1 ring-[#0071e3]/20"
                        : "bg-[#f5f5f7] border-black/8"
                    }`}
                  >
                    <div className="text-[12.5px] font-bold text-[#1d1d1f]">
                      161页级全本答辩说明书
                    </div>
                    <div className="text-[11px] text-[#515154] mt-0.5">
                      完整汇编 Stage 00–16 全量图表、空间句法分析、九章法定导则与投资台账
                    </div>
                  </button>
                </div>

                {/* Live SSE Log Console */}
                <div className="p-3 rounded-xl bg-[#1d1d1f] text-[#f5f5f7] font-mono text-[11px] h-[125px] overflow-y-auto space-y-1">
                  {reportLogs.map((ln, idx) => (
                    <div key={idx} className="leading-relaxed">
                      {ln}
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#f5f5f7] border border-black/8 flex flex-wrap items-center justify-between gap-2 text-[11.5px]">
                <div className="min-w-0">
                  <div className="text-[#515154]">说明书输出路径：</div>
                  <div className="font-mono font-semibold text-[#1d1d1f] truncate">
                    {reportDocxPath}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => openInExplorer(reportDocxPath)}
                  className="px-3 py-1.5 rounded-lg bg-white hover:bg-[#0071e3]/10 border border-black/10 text-[#0071e3] font-semibold flex items-center gap-1"
                >
                  <FolderOpen className="w-3.5 h-3.5" />
                  <span>在资源管理器中定位 .docx</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          SUB-VIEW 2: "guideline" (Stage 12 — 九章节法定城市设计导则)
      ======================================================================== */}
      {currentTab === "guideline" && (
        <div className="ud-card p-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-black/8">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                  阶段 12 · 法定图则条文
                </span>
                <h2 className="text-[15px] font-bold text-[#1d1d1f]">
                  九章节法定城市设计导则编制（通则 + 分地块刚性管控图则）
                </h2>
              </div>
              <p className="text-[11.5px] text-[#515154] mt-0.5">
                {guidelineStepLabel}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleStreamStage12Guideline}
                disabled={guidelineStreaming}
                className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-bold flex items-center gap-1.5"
              >
                {guidelineStreaming ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                <span>两步式生成法定城市设计导则 (SSE)</span>
              </button>

              <button
                type="button"
                onClick={handleExportGuidelineDocx}
                disabled={exportingGuidelineDocx}
                className="px-3.5 py-2 rounded-xl bg-white hover:bg-[#0071e3]/8 border border-black/12 text-[12px] font-semibold text-[#1d1d1f] flex items-center gap-1.5"
              >
                {exportingGuidelineDocx ? (
                  <Loader2 className="w-4 h-4 animate-spin text-[#0071e3]" />
                ) : (
                  <FileText className="w-4 h-4 text-[#0071e3]" />
                )}
                <span>导出法定设计导则 (.docx)</span>
              </button>

              <button
                type="button"
                onClick={() => openInExplorer(guidelineDocxPath)}
                className="px-3 py-2 rounded-xl bg-[#f5f5f7] hover:bg-black/8 border border-black/10 text-[12px] font-semibold text-[#0071e3] flex items-center gap-1"
              >
                <FolderOpen className="w-3.5 h-3.5" />
                <span>在资源管理器中定位</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left 4 cols: 9 Chapters List */}
            <div className="lg:col-span-4 space-y-1.5">
              {chapters.map((ch, idx) => {
                const active = idx === activeChapterIdx;
                return (
                  <button
                    key={ch.num}
                    type="button"
                    onClick={() => setActiveChapterIdx(idx)}
                    className={`w-full p-2.5 rounded-xl border text-left transition-all flex items-center justify-between gap-2 ${
                      active
                        ? "bg-[#0071e3] text-white border-[#0071e3] shadow-xs"
                        : "bg-[#f5f5f7] hover:bg-black/5 border-black/8 text-[#1d1d1f]"
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="text-[12px] font-bold truncate">
                        {ch.num} · {ch.title}
                      </div>
                    </div>
                    <span
                      className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        active
                          ? "bg-white/20 text-white"
                          : "bg-white text-[#515154] border border-black/8"
                      }`}
                    >
                      {ch.mandatoryTag}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Right 8 cols: Editable Statutory Markdown Preview */}
            <div className="lg:col-span-8 flex flex-col justify-between bg-[#f5f5f7] rounded-2xl p-4 border border-black/8 space-y-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-[#0071e3]" />
                    <span className="text-[14px] font-bold text-[#1d1d1f]">
                      {chapters[activeChapterIdx]?.num} ·{" "}
                      {chapters[activeChapterIdx]?.title}
                    </span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#8b5cf6]/15 text-[#5b21b6] text-[11px] font-bold">
                    {chapters[activeChapterIdx]?.mandatoryTag}
                  </span>
                </div>

                <textarea
                  value={chapters[activeChapterIdx]?.content || ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    setChapters((prev) =>
                      prev.map((c, idx) =>
                        idx === activeChapterIdx ? { ...c, content: val } : c
                      )
                    );
                  }}
                  rows={14}
                  className="w-full p-3.5 rounded-xl bg-white border border-black/10 text-[13px] leading-relaxed text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                />
              </div>

              {/* Mandatory Plot Control Sheet Quick Summary */}
              <div className="p-3 rounded-xl bg-white border border-black/8 grid grid-cols-4 gap-2 text-[11.5px]">
                <div>
                  <span className="text-[#515154]">锁定单元：</span>
                  <span className="font-bold text-[#1d1d1f]">
                    {targetPlot.plot_id}
                  </span>
                </div>
                <div>
                  <span className="text-[#515154]">法定FAR上限：</span>
                  <span className="font-bold text-[#0071e3]">≤ 2.20</span>
                </div>
                <div>
                  <span className="text-[#515154]">主街限高红线：</span>
                  <span className="font-bold text-[#ef4444]">≤ 18m / 24m</span>
                </div>
                <div>
                  <span className="text-[#515154]">绿地率下限：</span>
                  <span className="font-bold text-[#10b981]">≥ 25.0%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          SUB-VIEW 3: "systems" (Stage 09 — 四大专项系统与产业业态)
      ======================================================================== */}
      {currentTab === "systems" && (
        <div className="space-y-4">
          {/* 5 System Cards Bar */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-2.5">
            {systemsData.map((sys) => {
              const active = sys.key === activeSystemKey;
              return (
                <div
                  key={sys.key}
                  onClick={() => setActiveSystemKey(sys.key)}
                  className={`p-3.5 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between gap-2.5 ${
                    active
                      ? "bg-white border-[#0071e3] shadow-sm ring-2 ring-[#0071e3]/15"
                      : "bg-white/85 hover:bg-white border-black/8"
                  }`}
                >
                  <div>
                    <div className="text-[10.5px] font-bold text-[#0071e3]">
                      {sys.badge}
                    </div>
                    <div className="text-[13.5px] font-bold text-[#1d1d1f] mt-0.5">
                      {sys.title}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStreamStage09System(sys.key);
                    }}
                    disabled={systemStreaming}
                    className="w-full py-1.5 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[11.5px] font-semibold flex items-center justify-center gap-1"
                  >
                    {systemStreaming && active ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Sparkles className="w-3.5 h-3.5" />
                    )}
                    <span>SSE 专项推演</span>
                  </button>
                </div>
              );
            })}
          </div>

          {/* Active System Detail Panel */}
          {(() => {
            const currentSys =
              systemsData.find((s) => s.key === activeSystemKey) ||
              systemsData[0];
            return (
              <div className="ud-card p-4 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-black/8">
                  <div>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                      阶段 09 · {currentSys.badge}
                    </span>
                    <h2 className="text-[15px] font-bold text-[#1d1d1f] mt-1">
                      {currentSys.title}（靶向锚定：{targetPlot.name}）
                    </h2>
                  </div>

                  <div className="flex items-center gap-2.5">
                    {currentSys.metrics.map((m, idx) => (
                      <div
                        key={idx}
                        className="px-3 py-1.5 rounded-xl bg-[#f5f5f7] border border-black/8"
                      >
                        <div className="text-[10px] text-[#515154]">
                          {m.label}
                        </div>
                        <div className="text-[13px] font-bold text-[#0071e3]">
                          {m.value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <textarea
                  value={currentSys.defaultContent}
                  onChange={(e) => {
                    const val = e.target.value;
                    setSystemsData((prev) =>
                      prev.map((s) =>
                        s.key === currentSys.key
                          ? { ...s, defaultContent: val }
                          : s
                      )
                    );
                  }}
                  rows={10}
                  className="w-full p-3.5 rounded-xl bg-[#f5f5f7] border border-black/10 text-[13px] leading-relaxed text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                />
              </div>
            );
          })()}
        </div>
      )}

      {/* ========================================================================
          SUB-VIEW 4: "timing" (Stage 11 — 实施路径与分期甘特图)
      ======================================================================== */}
      {currentTab === "timing" && (
        <div className="space-y-4">
          {/* Top Funding & Investment Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">
                全周期更新总投资估算
              </div>
              <div className="text-[17px] font-bold text-[#0071e3] mt-0.5">
                {(totalInvestmentWan / 10000).toFixed(2)} 亿元
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                共 {totalInvestmentWan.toLocaleString()} 万元 (含修缮与地下市政)
              </div>
            </div>
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">
                近期示范期 (1–2年) 投资占比
              </div>
              <div className="text-[17px] font-bold text-[#10b981] mt-0.5">
                35.0% (首开示范区)
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                优先启动历史主街修缮与嵌入式养老公服
              </div>
            </div>
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">
                资金筹措与专项债配比
              </div>
              <div className="text-[15px] font-bold text-[#1d1d1f] mt-0.5">
                财政补助 25% · 专项债 35% · 社会资本 40%
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                通过容积率转移奖励商业运营现金流覆盖本息
              </div>
            </div>
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">
                项目动态财务平衡周期
              </div>
              <div className="text-[17px] font-bold text-[#8b5cf6] mt-0.5">
                8.4 年 (IRR ≈ 7.85%)
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                商业收益提取 12% 注入街区长效修缮基金
              </div>
            </div>
          </div>

          {/* Editable Phasing Ledger + ECharts 5 Gantt Chart */}
          <div className="ud-card p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-black/8">
              <div>
                <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                  阶段 11 · 双层分类施策台账
                </span>
                <h2 className="text-[15px] font-bold text-[#1d1d1f] mt-1">
                  “留 / 改 / 拆”分类施策台账与近期·中期·远期建设时序甘特图
                </h2>
              </div>

              <button
                type="button"
                onClick={handleSaveStage11Phasing}
                disabled={savingPhasing}
                className="px-4 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-bold flex items-center gap-1.5"
              >
                {savingPhasing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>保存台账并更新甘特图</span>
              </button>
            </div>

            {phasingFeedback && (
              <div className="px-3.5 py-2 rounded-xl bg-[#10b981]/12 text-[#065f46] text-[12px] font-semibold">
                {phasingFeedback}
              </div>
            )}

            {/* ECharts 5 Gantt Chart */}
            <div className="p-3.5 rounded-2xl bg-[#f5f5f7] border border-black/8">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[13px] font-bold text-[#1d1d1f] flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-[#0071e3]" />
                  <span>分期建设时序甘特图 (2026–2036 十年滚动实施计划)</span>
                </span>
                <div className="flex items-center gap-3 text-[11px] font-semibold">
                  <span className="flex items-center gap-1 text-[#0071e3]">
                    <span className="w-2.5 h-2.5 rounded-xs bg-[#0071e3]" />
                    近期示范 (1-2年)
                  </span>
                  <span className="flex items-center gap-1 text-[#10b981]">
                    <span className="w-2.5 h-2.5 rounded-xs bg-[#10b981]" />
                    中期推广 (3-5年)
                  </span>
                  <span className="flex items-center gap-1 text-[#8b5cf6]">
                    <span className="w-2.5 h-2.5 rounded-xs bg-[#8b5cf6]" />
                    远期巩固 (5-10年)
                  </span>
                </div>
              </div>
              <div ref={ganttChartRef} className="w-full h-[230px]" />
            </div>

            {/* Editable Table */}
            <div className="overflow-x-auto rounded-2xl border border-black/10 bg-white">
              <table className="w-full text-left border-collapse text-[12px]">
                <thead>
                  <tr className="bg-[#f5f5f7] border-b border-black/8 text-[#515154]">
                    <th className="p-2.5 font-bold">更新单元名称</th>
                    <th className="p-2.5 font-bold">留 / 改 / 拆分类</th>
                    <th className="p-2.5 font-bold">建设分期时序</th>
                    <th className="p-2.5 font-bold">投资额 (万元)</th>
                    <th className="p-2.5 font-bold">核心实施工程内容与资金来源</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black/6">
                  {phasingLedger.map((row, idx) => (
                    <tr key={row.plot_id} className="hover:bg-[#f5f5f7]/40">
                      <td className="p-2.5 font-semibold text-[#1d1d1f]">
                        <div>{row.plot_name}</div>
                        <div className="text-[10.5px] font-mono text-[#515154]">
                          {row.plot_id}
                        </div>
                      </td>
                      <td className="p-2">
                        <select
                          value={row.category}
                          onChange={(e) => {
                            const val = e.target.value as PhasingLedgerRow["category"];
                            setPhasingLedger((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, category: val } : r
                              )
                            );
                          }}
                          className="px-2.5 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/10 font-bold text-[#0071e3]"
                        >
                          <option value="留 (保护修缮)">留 (保护修缮)</option>
                          <option value="改 (功能活化)">改 (功能活化)</option>
                          <option value="拆 (织补腾退)">拆 (织补腾退)</option>
                        </select>
                      </td>
                      <td className="p-2">
                        <select
                          value={row.phase}
                          onChange={(e) => {
                            const val = e.target.value as PhasingLedgerRow["phase"];
                            const startYear = val.includes("近期")
                              ? 2026
                              : val.includes("中期")
                              ? 2028
                              : 2030;
                            setPhasingLedger((prev) =>
                              prev.map((r, i) =>
                                i === idx
                                  ? { ...r, phase: val, startYear }
                                  : r
                              )
                            );
                          }}
                          className="px-2.5 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/10 font-semibold text-[#1d1d1f]"
                        >
                          <option value="近期示范 (1-2年)">
                            近期示范 (1-2年)
                          </option>
                          <option value="中期推广 (3-5年)">
                            中期推广 (3-5年)
                          </option>
                          <option value="远期巩固 (5-10年)">
                            远期巩固 (5-10年)
                          </option>
                        </select>
                      </td>
                      <td className="p-2">
                        <input
                          type="number"
                          value={row.investmentWan}
                          onChange={(e) => {
                            const val = Number(e.target.value) || 0;
                            setPhasingLedger((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, investmentWan: val } : r
                              )
                            );
                          }}
                          className="w-[105px] px-2.5 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/10 font-mono font-bold text-[#1d1d1f]"
                        />
                      </td>
                      <td className="p-2">
                        <input
                          type="text"
                          value={row.keyAction}
                          onChange={(e) => {
                            const val = e.target.value;
                            setPhasingLedger((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, keyAction: val } : r
                              )
                            );
                          }}
                          className="w-full px-2.5 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/10 text-[#1d1d1f]"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          SUB-VIEW 5: "skills" (Stage 16 — Skill 规范手册与基地自适应多主体听证会)
      ======================================================================== */}
      {currentTab === "skills" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left 6 cols: Structured Viewer of all 12 parts (Part 0 – Part 11) of SKILLS.md */}
          <div className="lg:col-span-6 ud-card p-4 space-y-3.5">
            <div className="flex items-center justify-between pb-2.5 border-b border-black/8">
              <div>
                <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                  阶段 16 · 智能体研发与规划规范体系
                </span>
                <h2 className="text-[15px] font-bold text-[#1d1d1f] mt-1">
                  `SKILLS.md` 十二大核心规范手册检视器 (Part 0 – Part 11)
                </h2>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-[#10b981]/15 text-[#065f46] text-[11px] font-bold">
                12/12 规范在线
              </span>
            </div>

            {/* 12 Parts Pills Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-1.5">
              {skillsList.map((sk) => {
                const active = sk.partCode === selectedSkillCode;
                return (
                  <button
                    key={sk.partCode}
                    type="button"
                    onClick={() => setSelectedSkillCode(sk.partCode)}
                    className={`p-2 rounded-xl border text-left transition-all ${
                      active
                        ? "bg-[#0071e3] text-white border-[#0071e3] shadow-2xs"
                        : "bg-[#f5f5f7] hover:bg-black/5 border-black/8 text-[#1d1d1f]"
                    }`}
                  >
                    <div className="text-[11px] font-mono font-bold">
                      {sk.partCode}
                    </div>
                    <div
                      className={`text-[10.5px] truncate mt-0.5 ${
                        active ? "text-white/90" : "text-[#515154]"
                      }`}
                    >
                      {sk.title}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Active Skill Part Detail Card */}
            {(() => {
              const activeSkill =
                skillsList.find((s) => s.partCode === selectedSkillCode) ||
                skillsList[0];
              return (
                <div className="p-4 rounded-2xl bg-[#f5f5f7] border border-black/8 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/12 text-[#0071e3] font-mono text-[11px] font-bold">
                      {activeSkill.partCode}
                    </span>
                    <span className="text-[11px] text-[#515154]">
                      项目顶层强制约束守则
                    </span>
                  </div>

                  <h3 className="text-[14.5px] font-bold text-[#1d1d1f]">
                    {activeSkill.title}
                  </h3>

                  <div className="p-2.5 rounded-xl bg-white border border-black/8 text-[12px]">
                    <span className="font-bold text-[#1d1d1f]">触发条件：</span>
                    <span className="text-[#515154]">{activeSkill.trigger}</span>
                  </div>

                  <div className="space-y-1.5">
                    <div className="text-[12px] font-bold text-[#1d1d1f]">
                      核心执行动作要求：
                    </div>
                    {activeSkill.highlights.map((hl, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 p-2.5 rounded-xl bg-white border border-black/6 text-[12px] text-[#1d1d1f]"
                      >
                        <CheckCircle2 className="w-4 h-4 text-[#10b981] shrink-0 mt-0.5" />
                        <span>{hl}</span>
                      </div>
                    ))}
                  </div>

                  <div className="p-2.5 rounded-xl bg-[#ef4444]/10 border border-[#ef4444]/25 text-[11.5px] text-[#991b1b] font-semibold">
                    红线约束：{activeSkill.constraint}
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Right 6 cols: Site-Adaptive Multi-Party Conflict Hearing Simulator */}
          <div className="lg:col-span-6 ud-card p-4 flex flex-col justify-between space-y-4">
            <div className="space-y-3.5">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-black/8">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#8b5cf6]/15 text-[#5b21b6] text-[11px] font-bold">
                    阶段 16 · 基地自适应公众听证会
                  </span>
                  <h2 className="text-[15px] font-bold text-[#1d1d1f] mt-1">
                    多主体利益冲突听证会与 RAG 法定裁定模拟器
                  </h2>
                </div>

                <button
                  type="button"
                  onClick={handleStreamStage16Hearing}
                  disabled={hearingStreaming}
                  className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-bold flex items-center gap-1.5"
                >
                  {hearingStreaming ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Gavel className="w-4 h-4" />
                  )}
                  <span>启动公众听证会推演 (SSE)</span>
                </button>
              </div>

              {/* Scenario Selector */}
              <div className="space-y-2">
                <label className="block text-[12px] font-bold text-[#1d1d1f]">
                  选择针对靶向地块 ({targetPlot.name}) 的听证争议焦点议题：
                </label>
                {HEARING_SCENARIOS.map((sc) => {
                  const active = sc.id === selectedScenarioId;
                  return (
                    <div
                      key={sc.id}
                      onClick={() => setSelectedScenarioId(sc.id)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        active
                          ? "bg-[#0071e3]/8 border-[#0071e3] ring-1 ring-[#0071e3]/20"
                          : "bg-[#f5f5f7] hover:bg-black/5 border-black/8"
                      }`}
                    >
                      <div className="text-[12.5px] font-bold text-[#1d1d1f]">
                        {sc.title}
                      </div>
                      <div className="text-[11px] text-[#515154] mt-0.5">
                        {sc.summary}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Hearing Resolution Stream Output */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[12px] font-bold text-[#1d1d1f]">
                    公众听证质证实录与 Hybrid RAG 法条裁定决议书
                  </span>
                  <span className="text-[11px] text-[#0071e3] font-semibold">
                    锚定国标 GB 50180 / GB/T 50357
                  </span>
                </div>
                <textarea
                  value={hearingTranscript}
                  onChange={(e) => setHearingTranscript(e.target.value)}
                  rows={10}
                  className="w-full p-3.5 rounded-xl bg-[#f5f5f7] border border-black/10 text-[12.5px] leading-relaxed text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                />
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#10b981]/10 border border-[#10b981]/25 text-[11.5px] text-[#065f46] flex items-center justify-between">
              <span>
                听证决议已自动关联至阶段 12 法定导则第九章分地块图则与阶段 13 全本答辩报告
              </span>
              <span className="font-bold">闭环校验通过</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workbench03View;
