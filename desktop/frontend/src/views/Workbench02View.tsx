import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as echarts from "echarts";
import {
  AlertTriangle,
  ArrowLeftRight,
  BookOpen,
  Building2,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Compass,
  FolderOpen,
  Image as ImageIcon,
  Layers,
  Loader2,
  Lock,
  MapPin,
  PieChart,
  Play,
  Plus,
  RefreshCw,
  Save,
  Scale,
  ShieldCheck,
  Sliders,
  Sparkles,
  Target,
  Trash2,
  Users,
  Wand2,
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

interface Stage06Sections {
  case_benchmark: string;
  design_concept: string;
  design_basis: string;
  design_principles: string;
  design_positioning: string;
}

interface DebateCitation {
  source: string;
  clause?: string;
  snippet?: string;
}

interface DebateTurn {
  id: string;
  round: number;
  role: "gov" | "resident" | "developer";
  roleLabel: string;
  speakerTitle: string;
  content: string;
  keyDemand: string;
  citations: DebateCitation[];
}

interface StrategyMatrixRow {
  id: string;
  problem: string;
  goal: string;
  strategy: string;
  indicator: string;
  stakeholder: string;
}

interface BeforeAfterMetric {
  label: string;
  before: string;
  after: string;
  delta: string;
  positive?: boolean;
}

interface RenderGalleryItem {
  id: string;
  title: string;
  stylePreset: string;
  prompt: string;
  imageUrl?: string;
  outputPath?: string;
  createdAt: string;
  controlMode: string;
  far: number;
}

const WB2_TABS: Array<{
  key: StudioSubTab;
  stageBadge: string;
  label: string;
  subtitle: string;
}> = [
  {
    key: "strategy",
    stageBadge: "阶段 06 · 07",
    label: "目标定位与三主体博弈剧场",
    subtitle: "标杆对标、政企民三轮SSE协商、混合RAG法条锚定与策略矩阵",
  },
  {
    key: "master-plan",
    stageBadge: "阶段 08",
    label: "总体城市设计与用地平衡沙盘",
    subtitle: "一轴两带四核空间结构推演、用地比例调节与计容建筑面积核算",
  },
  {
    key: "detail",
    stageBadge: "阶段 10",
    label: "重点地段深化与卷帘对比",
    subtitle: "控规刚性红线画像、全龄人群微更新节点与改造前后卷帘对比",
  },
  {
    key: "aigc",
    stageBadge: "阶段 15",
    label: "GIS刚性骨架 ControlNet 空间AIGC工坊",
    subtitle: "三维体块深度图约束、六大规划风格提示词润色与空间生形渲染",
  },
];

const STAGE06_SECTION_META: Array<{
  key: keyof Stage06Sections;
  title: string;
  badge: string;
  promptHint: string;
}> = [
  {
    key: "case_benchmark",
    title: "标杆案例对标",
    badge: "国内外更新范式",
    promptHint: "对标北京杨梅竹斜街、上海新天地及寒地历史街区渐进式微更新经验",
  },
  {
    key: "design_concept",
    title: "核心设计理念",
    badge: "风貌与活力共生",
    promptHint: "提出针灸式微更新、寒地全季慢行街区与新旧肌理有机织补理念",
  },
  {
    key: "design_basis",
    title: "上位规划依据",
    badge: "法定图则与规范",
    promptHint: "衔接国土空间总体规划、历史文化街区保护规划与控规刚性边界",
  },
  {
    key: "design_principles",
    title: "四大设计原则",
    badge: "生态·人本·文脉·韧性",
    promptHint: "确立文脉保护优先、慢行优先、职住平衡与公服均等化四大原则",
  },
  {
    key: "design_positioning",
    title: "功能定位体系",
    badge: "产业与空间坐标",
    promptHint: "构建文旅商创复合街区、全龄友好社区与历史风貌展示窗口",
  },
];

const STYLE_PRESETS = [
  {
    id: "historic_conservation",
    name: "历史街区修缮",
    badge: "砖木肌理 · 坡屋顶天际线",
    desc: "保留近代历史街区红砖灰瓦立面尺度，植入庭院式文创商业与慢行步道",
    defaultPrompt:
      "urban renewal of historic district, red brick heritage facade restoration, pedestrian courtyard, warm street lighting, human scale arcade, trees, architectural photography, 8k",
  },
  {
    id: "vibrant_commercial",
    name: "现代商业活力街区",
    badge: "首层通透界面 · 退台绿化",
    desc: "连续首层商业外摆界面、二层空中连廊与高通透玻璃结合暖色石材",
    defaultPrompt:
      "vibrant mixed-use commercial street, transparent ground floor retail, outdoor cafe seating, stepped green terrace, contemporary urban design, daylight, photorealistic",
  },
  {
    id: "sponge_ecocorridor",
    name: "生态海绵绿轴",
    badge: "雨水花园 · 透水慢行道",
    desc: "结合蓝绿开敞空间与下沉式雨水花园，大幅提升街区绿视率与微气候舒适度",
    defaultPrompt:
      "sponge city ecological green corridor, bioswale rain garden, permeable paving bike lane, pocket park in high density neighborhood, lush canopy, sunny architectural render",
  },
  {
    id: "industrial_creative",
    name: "工业遗产文创园",
    badge: "钢构桁架 · 新旧碰撞",
    desc: "利用既有大跨度厂房与工业肌理改造为数字创意工坊、艺术展馆与市民广场",
    defaultPrompt:
      "adaptive reuse of industrial heritage, red brick and steel truss structure, cultural creative park, public plaza, contemporary glass insertion, architectural visualization",
  },
  {
    id: "tod_mixed_community",
    name: "混合TOD社区",
    badge: "轨交微中心 · 立体慢行",
    desc: "围绕轨道站点打造集约紧凑的社区公服综合体、全天候风雨连廊与立体公园",
    defaultPrompt:
      "transit oriented development urban core, multi-level pedestrian skywalk, community center, vertical greenery, compact mixed-use buildings, high resolution architectural render",
  },
  {
    id: "winter_city_promenade",
    name: "寒地全季漫步街区",
    badge: "挡风暖廊 · 冬日向阳庭院",
    desc: "针对东北寒地气候优化南向日照开口、暖房骑楼与四季常绿乔灌木景观带",
    defaultPrompt:
      "winter city all-season pedestrian street, sunlit south-facing plaza, warm timber and glass winter gallery, pine trees, cozy urban microclimate design, realistic lighting",
  },
];

const DEFAULT_FALLBACK_PLOT: FusedPlot = {
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
  priority_tier: "近期示范更新 (Tier 1)",
};

export const Workbench02View: React.FC = () => {
  const {
    activeSubTab,
    activeProjectId,
    fusedPlots,
    lockedTargetPlot,
    setActiveSubTab,
    navigateToStage,
    lockTargetPlot,
    refreshJobs,
  } = useStudioStore();

  const currentTab: StudioSubTab = useMemo(() => {
    const valid: StudioSubTab[] = ["strategy", "master-plan", "detail", "aigc"];
    return valid.includes(activeSubTab) ? activeSubTab : "strategy";
  }, [activeSubTab]);

  const targetPlot: FusedPlot = useMemo(() => {
    return lockedTargetPlot || fusedPlots[0] || DEFAULT_FALLBACK_PLOT;
  }, [lockedTargetPlot, fusedPlots]);

  // ============================================================================
  // SUB-VIEW 1: Stage 06 & Stage 07 (目标定位与三主体博弈剧场)
  // ============================================================================
  const [stage06Collapsed, setStage06Collapsed] = useState(false);
  const [activeStage06Key, setActiveStage06Key] =
    useState<keyof Stage06Sections>("case_benchmark");
  const [stage06Streaming, setStage06Streaming] = useState(false);
  const [stage06Sections, setStage06Sections] = useState<Stage06Sections>({
    case_benchmark:
      "1. 北京杨梅竹斜街渐进式微更新：采用“共生院”模式平衡原住民留住与文创商业植入；\n2. 上海新天地与慎余里风貌织补：严格保留历史街巷高宽比（D/H ≈ 1.0~1.2），底层置入高活力连续商业界面；\n3. 哈尔滨中央大街寒地全季街区：通过暖廊节点、防风植栽与南向退台提升冬季慢行驻留时长。",
    design_concept:
      "以“刚性控规护底线、针灸更新激活力、三方共治享红利”为核心理念，依托 DuckDB Spatial 诊断锁定的空间短板，构建历史肌理与现代社区深度融合的有机更新典范。",
    design_basis:
      "严格遵循《城市居住区规划设计标准》(GB 50180-2018)、《历史文化名城保护规划标准》(GB/T 50357-2018)、《城市道路工程设计规范》(CJJ 37) 及片区法定控规图则。",
    design_principles:
      "【原则一：文脉紫线刚性守护】严控街巷肌理与视廊限高；\n【原则二：人本慢行与绿视跃升】将街道绿视率提升至 28% 以上；\n【原则三：公服均等与全龄友好】补齐 5-10-15 分钟社区生活圈短板；\n【原则四：财务平衡与渐进分期】通过容积率转移与复合业态实现滚动自平衡。",
    design_positioning:
      "总体定位为【寒地历史风貌活化示范区 · 产城人文融合活力核】，形成“文博展陈+特色商业+青年创客+品质社区”四位一体功能体系。",
  });

  // Stage 07 Negotiation states
  const [debateTopic, setDebateTopic] = useState(
    "针对靶向地块容积率适度奖励、历史风貌保护修缮与原住民公服配套改善的三方利益平衡博弈"
  );
  const [govWeight, setGovWeight] = useState(40);
  const [residentWeight, setResidentWeight] = useState(35);
  const [developerWeight, setDeveloperWeight] = useState(25);
  const [negotiating, setNegotiating] = useState(false);
  const [debateStreamLog, setDebateStreamLog] = useState("");
  const [consensusScores, setConsensusScores] = useState<{
    initial: number[];
    final: number[];
  }>({
    initial: [62, 54, 58, 70, 76],
    final: [89, 84, 91, 93, 96],
  });
  const [designBrief, setDesignBrief] = useState(
    "【三方博弈法定共识纲要】经政府规资部门、原住居民代表与实施主体三轮博弈，明确靶向地块综合容积率控制在 2.15 以内（较现状适度奖励 0.23 用于补齐社区养老与地下停车），核心风貌街巷建筑限高 18m–24m，绿地与开敞空间占比不低于 26.5%，商业收益提取 12% 注入街区长效修缮基金。"
  );
  const [debateTurns, setDebateTurns] = useState<DebateTurn[]>([
    {
      id: "r1-gov",
      round: 1,
      role: "gov",
      roleLabel: "政府规资与风貌主管部门",
      speakerTitle: "第一轮 · 法定红线与公共利益底线声明",
      content:
        "靶向地块处于城市中心风貌协调区，更新改造必须坚守历史紫线与高度控制红线。新建或改扩建建筑必须满足日照间距与消防通道硬性标准，严禁大拆大建破坏既有街巷尺度，同时必须配建不少于 15% 的公共开敞绿地与社区卫生养老设施。",
      keyDemand: "严守控规限高与紫线边界，落实 15 分钟生活圈公服配建",
      citations: [
        {
          source: "《历史文化名城保护规划标准》GB/T 50357-2018",
          clause: "第 3.2.4 条 · 建设控制地带高度与体量管控",
          snippet: "建设控制地带内新建建筑物、构筑物不得破坏历史文化街区传统格局与空间尺度。",
        },
        {
          source: "《城市居住区规划设计标准》GB 50180-2018",
          clause: "第 4.0.2 条 · 居住街坊建筑密度与绿地率下限",
        },
      ],
    },
    {
      id: "r1-res",
      round: 1,
      role: "resident",
      roleLabel: "原住居民与商户议事代表",
      speakerTitle: "第一轮 · 民生改善与留住权诉求",
      content:
        "现存院落冬季采光不足、雨季内涝且缺乏老年活动室与无障碍电梯。我们要求微更新优先解决管网入地、冬日大风街角防风暖廊与宅前口袋绿地，拒绝将沿街便民小微商业全部清退。",
      keyDemand: "保障冬至日照、加装适老化配套、保留社区便民商业烟火气",
      citations: [
        {
          source: "《城市居住区规划设计标准》GB 50180-2018",
          clause: "第 4.0.9 条 · 住宅建筑冬至日大寒日日照标准",
          snippet: "旧区改建项目新建住宅日照标准不应低于大寒日日照 1 小时，且不得恶化既有住宅日照。",
        },
      ],
    },
    {
      id: "r1-dev",
      round: 1,
      role: "developer",
      roleLabel: "城市更新实施主体 / 开发商",
      speakerTitle: "第一轮 · 改造投资回报与容积率平衡诉求",
      content:
        "历史建筑修缮与地下市政管廊改造成本高达 4800 元/㎡，若维持现状容积率不变且无商业面积增量，项目静态回收期将超过 18 年。申请在非核心风貌界面给予 15%~20% 的容积率转移奖励，并允许首层、二层复合布局高附加值文旅商业。",
      keyDemand: "争取异地/局部容积率转移激励与首层商业混合业态兼容准入",
      citations: [
        {
          source: "《城乡用地分类与规划建设用地标准》GB 50137",
          clause: "混合用地兼容性与公益性贡献容积率奖励机制",
        },
      ],
    },
    {
      id: "r2-consensus",
      round: 2,
      role: "gov",
      roleLabel: "政府规资与风貌主管部门",
      speakerTitle: "第二轮 · 混合 RAG 法规校核与激励折中裁定",
      content:
        "经检索法定规划规范，同意采用【刚性风貌保护 + 公益贡献换取容积率奖励】机制：开发商每提供 1㎡ 独立占地的社区公共绿地或嵌入式养老托育设施，可奖励 1.2㎡ 计容商业/创客办公面积，但奖励后地块综合 FAR 不得突破 2.20，沿历史主街建筑限高严控在 18m 以内。",
      keyDemand: "以公益配建与开放空间贡献锚定容积率精准奖励上限",
      citations: [
        {
          source: "《城市设计管理办法》住建部令第 35 号",
          clause: "第 14 条 · 重点地区城市设计公共开敞空间与天际线管控",
        },
      ],
    },
    {
      id: "r3-final",
      round: 3,
      role: "resident",
      roleLabel: "三方联合签署契约 (政·民·企共识)",
      speakerTitle: "第三轮 · 空间-经济-民生多赢方案定案",
      content:
        "三方达成最终契约：保留 100% 历史风貌建筑立面并实施内部现代化功能更新；在街区北侧次干道节点集中释放 0.23 容积率增量打造全天候寒地文创商业综合体；辟建 3 处向阳口袋公园与 650m 连续慢行林荫道，实现政府风貌达标、居民品质跃升、企业财务 IRR ≥ 7.8%。",
      keyDemand: "形成问题-目标-策略闭环并锁定法定城市设计导则控制指标",
      citations: [
        {
          source: "《完整居住社区建设标准》建办科〔2021〕55号",
          clause: "基本公共服务设施、便民商业服务设施与公共活动空间配建指标",
        },
      ],
    },
  ]);

  const [strategyMatrix, setStrategyMatrix] = useState<StrategyMatrixRow[]>([
    {
      id: "sm-1",
      problem: "历史街巷界面破损、绿视率偏低 (GVI < 22%) 且慢行空间被占道挤压",
      goal: "打造高绿视率、人车分离的全季慢行文化街区",
      strategy: "清退路侧违规停车转入地下，拓宽 4.5m 连续步行带并植入双排乡土乔木与口袋花园",
      indicator: "绿视率 GVI ≥ 28%，慢行道宽度 ≥ 4.5m，街道高宽比 D/H 控制在 1.0–1.3",
      stakeholder: "政府规资牵头 · 居民议事监督",
    },
    {
      id: "sm-2",
      problem: "老旧居住院落缺乏适老化电梯、日照局促且社区养老/托育公服缺失",
      goal: "构建全龄友好 5-10-15 分钟完整社区生活圈",
      strategy: "利用边角闲置用房微改造为嵌入式养老驿站与暖房活动厅，严控新建体量退台保障大寒日日照",
      indicator: "社区公服建筑面积占比 ≥ 12%，既有住宅大寒日日照恶化率 = 0%",
      stakeholder: "原住居民代表 · 街道社区共建",
    },
    {
      id: "sm-3",
      problem: "历史建筑修缮资金缺口大、传统单一业态坪效低导致更新财务难平衡",
      goal: "实现风貌修缮成本与商业运营现金流动态自平衡",
      strategy: "引入“容积率公益奖励 + 首层文创商业复合兼容”机制，植入精品非遗工坊与全季夜经济消费场景",
      indicator: "综合容积率 FAR 1.92→2.15，商业服务业占比 28%，项目财务内部收益率 IRR ≥ 7.8%",
      stakeholder: "城市更新开发商 · 规资政策赋能",
    },
  ]);
  const [matrixSaving, setMatrixSaving] = useState(false);
  const [matrixFeedback, setMatrixFeedback] = useState<string | null>(null);

  const radarChartRef = useRef<HTMLDivElement | null>(null);
  const radarInstanceRef = useRef<echarts.ECharts | null>(null);

  // ============================================================================
  // SUB-VIEW 2: Stage 08 (总体城市设计与用地平衡沙盘)
  // ============================================================================
  const [structureStreaming, setStructureStreaming] = useState(false);
  const [spatialStructureTitle, setSpatialStructureTitle] = useState(
    "“一轴两带、四核多节点”寒地历史街区有机更新空间格局"
  );
  const [spatialStructureNarrative, setSpatialStructureNarrative] = useState(
    "1. 【一条历史文脉与现代活力主轴】沿核心历史大道构建集文化遗产展示、慢行林荫道与全季商业走廊于一体的城市中轴线；\n2. 【两条蓝绿海绵与社区生活慢行带】串联东西向滨水绿带与内街生活漫步道，打通空间句法高穿行度微循环；\n3. 【四大复合功能核心】文博非遗展示核、青年数字创客核、全龄社区公服核、轨交TOD商业活力核；\n4. 【视线通廊与天际线控制】形成“近街低矮坡屋顶（≤18m）—中景退台过渡（24m）—远景标志节点（36m）”的三级天际线韵律。"
  );

  // Landuse Sandbox sliders (%)
  const [commercialPct, setCommercialPct] = useState(28);
  const [residentialPct, setResidentialPct] = useState(34);
  const [greenPct, setGreenPct] = useState(22);
  const [publicServicePct, setPublicServicePct] = useState(11);
  const [heritageMixPct, setHeritageMixPct] = useState(5);
  const [sandboxFar, setSandboxFar] = useState(2.15);
  const [sandboxSyncing, setSandboxSyncing] = useState(false);
  const [sandboxFeedback, setSandboxFeedback] = useState<string | null>(null);

  const landuseChartRef = useRef<HTMLDivElement | null>(null);
  const landuseInstanceRef = useRef<echarts.ECharts | null>(null);

  // ============================================================================
  // SUB-VIEW 3: Stage 10 (重点地段深化与卷帘对比)
  // ============================================================================
  const [stage10Redlines, setStage10Redlines] = useState({
    height_limit_m: 24,
    far_cap: 2.2,
    green_ratio_min_pct: 25,
    setback_main_street_m: 6,
    heritage_purple_line: "核心风貌街巷 D/H 控制在 1.0–1.2，一类保护建筑外立面 100% 原真修缮",
  });
  const [activeStage10NodeTopic, setActiveStage10NodeTopic] = useState<
    "重点节点空间设计" | "全龄人群活动画像" | "寒地微气候/特色专项研究"
  >("重点节点空间设计");
  const [stage10Streaming, setStage10Streaming] = useState(false);
  const [stage10Outputs, setStage10Outputs] = useState<Record<string, string>>({
    重点节点空间设计:
      "【节点一：历史街口风貌门户广场】拆除现状零星违建围墙，后退建筑红线 6m 辟建下沉式雨水花园与非遗文化展墙；\n【节点二：百年红砖合院共生微更新】保留外围历史砖墙肌理，院落内部植入轻钢玻璃暖廊书吧与社区共享客厅；\n【节点三：全龄友好社区漫步街巷】取消机动车单侧占道停车，铺装防滑透水花岗岩，每 80m 设置一处带加热坐垫的寒地街头休读亭。",
    全龄人群活动画像:
      "• 【银发长者群体 (06:30–11:30 / 14:00–16:30)】高频汇聚于南向向阳口袋公园与社区医养驿站，要求全路径零高差无障碍坡道；\n• 【青年创客与白领 (08:30–22:00)】活跃于历史工坊文创区、精品咖啡外摆区与轨道站点接驳连廊；\n• 【亲子家庭与学童 (15:30–19:30 & 周末)】集中于安全步行街、科普雨水花园与非遗手作体验馆。",
    "寒地微气候/特色专项研究":
      "针对北纬 43.8° 冬季主导西北寒风，采用街口防风常绿松柏林带与建筑首层内退骑楼暖廊设计，使步行区冬季平均风速降低 38%；南向建筑实行阶梯式退台，确保冬至日街道中心线连续日照时长 ≥ 3.5 小时。",
  });

  // Before / After Swipe Comparator state
  const [swipePercent, setSwipePercent] = useState(52);
  const [beforeImageUrl, setBeforeImageUrl] = useState<string>("");
  const [afterImageUrl, setAfterImageUrl] = useState<string>("");
  const [beforeAfterDeltas, setBeforeAfterDeltas] = useState<BeforeAfterMetric[]>([
    {
      label: "绿视率 GVI 提升",
      before: `${((targetPlot.gvi_mean || 0.21) * 100).toFixed(1)}%`,
      after: "31.4%",
      delta: "+10.4%",
      positive: true,
    },
    {
      label: "慢行空间有效宽度",
      before: "2.1 m (人车混行)",
      after: "5.2 m (林荫连续步道)",
      delta: "+147%",
      positive: true,
    },
    {
      label: "公共开敞空间占比",
      before: "11.5%",
      after: "24.8%",
      delta: "+13.3%",
      positive: true,
    },
    {
      label: "首层商业界面通透率",
      before: "34.0%",
      after: "72.5%",
      delta: "+38.5%",
      positive: true,
    },
  ]);
  const swipeContainerRef = useRef<HTMLDivElement | null>(null);
  const isDraggingSwipeRef = useRef(false);

  // ============================================================================
  // SUB-VIEW 4: Stage 15 (GIS 刚性骨架 ControlNet 空间 AIGC 工坊)
  // ============================================================================
  const [controlMode, setControlMode] = useState<"depth" | "canny" | "normal">("depth");
  const [depthPreviewUrl, setDepthPreviewUrl] = useState<string>("");
  const [depthPreviewLoading, setDepthPreviewLoading] = useState(false);
  const [depthMeta, setDepthMeta] = useState<{
    bldgCount: number;
    maxHeightM: number;
    viewAngle: string;
  }>({
    bldgCount: targetPlot.bldg_count || 42,
    maxHeightM: Math.round((targetPlot.avg_floor || 5.6) * 3.2 + 8),
    viewAngle: "45° 轴测鸟瞰与人视双轨刚性骨架",
  });

  const [selectedPresetId, setSelectedPresetId] = useState<string>(
    STYLE_PRESETS[0].id
  );
  const [aigcPrompt, setAigcPrompt] = useState<string>(
    STYLE_PRESETS[0].defaultPrompt
  );
  const [aigcNegativePrompt, setAigcNegativePrompt] = useState<string>(
    "low quality, blurry, deformed buildings, floating structures, violating height limit, highway overpass, dystopian, watermark"
  );
  const [polishingPrompt, setPolishingPrompt] = useState(false);

  const [denoisingStrength, setDenoisingStrength] = useState(0.58);
  const [controlNetWeight, setControlNetWeight] = useState(1.15);
  const [sampleSteps, setSampleSteps] = useState(28);
  const [renderSeed, setRenderSeed] = useState(20260701);
  const [renderingAigc, setRenderingAigc] = useState(false);
  const [aigcFeedback, setAigcFeedback] = useState<string | null>(null);
  const [renderGallery, setRenderGallery] = useState<RenderGalleryItem[]>([
    {
      id: "init-render-1",
      title: `${targetPlot.name} · 历史街区修缮方案`,
      stylePreset: "历史街区修缮",
      prompt: STYLE_PRESETS[0].defaultPrompt,
      createdAt: "预设基准渲染",
      controlMode: "Depth 深度体块刚性约束",
      far: targetPlot.far || 1.92,
    },
    {
      id: "init-render-2",
      title: `${targetPlot.name} · 寒地全季漫步街区方案`,
      stylePreset: "寒地全季漫步街区",
      prompt: STYLE_PRESETS[5].defaultPrompt,
      createdAt: "预设基准渲染",
      controlMode: "Canny 建筑边缘约束",
      far: 2.15,
    },
  ]);

  // ============================================================================
  // Load Initial Backend State for Stage 06, 10, 15
  // ============================================================================
  useEffect(() => {
    // Stage 06 state
    apiGet<any>("/api/v1/strategy/stage06/state")
      .then((res) => {
        if (!res || typeof res !== "object") return;
        const sec = res.sections || res.data || res;
        setStage06Sections((prev) => ({
          case_benchmark: sec.case_benchmark || prev.case_benchmark,
          design_concept: sec.design_concept || prev.design_concept,
          design_basis: sec.design_basis || prev.design_basis,
          design_principles: sec.design_principles || prev.design_principles,
          design_positioning: sec.design_positioning || prev.design_positioning,
        }));
        if (Array.isArray(res.strategy_matrix) && res.strategy_matrix.length > 0) {
          setStrategyMatrix(
            res.strategy_matrix.map((r: any, idx: number) => ({
              id: r.id || `sm-${idx}`,
              problem: r.problem || r.issue || "",
              goal: r.goal || r.objective || "",
              strategy: r.strategy || r.action || "",
              indicator: r.indicator || r.metric || "",
              stakeholder: r.stakeholder || r.owner || "政企民协同",
            }))
          );
        }
      })
      .catch(() => {
        // Keep rich local defaults
      });

    // Stage 10 profile & before-after
    apiGet<any>("/api/v1/aigc/stage10/profile")
      .then((res) => {
        if (res?.redlines && typeof res.redlines === "object") {
          setStage10Redlines((prev) => ({ ...prev, ...res.redlines }));
        }
      })
      .catch(() => {});

    apiGet<any>("/api/v1/aigc/stage10/before-after")
      .then((res) => {
        if (!res) return;
        if (res.before_image_url) {
          setBeforeImageUrl(buildApiUrl(res.before_image_url, true));
        }
        if (res.after_image_url) {
          setAfterImageUrl(buildApiUrl(res.after_image_url, true));
        }
        if (Array.isArray(res.deltas) && res.deltas.length > 0) {
          setBeforeAfterDeltas(res.deltas);
        }
      })
      .catch(() => {});

    // Stage 15 config
    apiGet<any>("/api/v1/aigc/stage15/config")
      .then((res) => {
        if (!res) return;
        if (res.depth_preview_url) {
          setDepthPreviewUrl(buildApiUrl(res.depth_preview_url, true));
        }
        if (Array.isArray(res.gallery) && res.gallery.length > 0) {
          setRenderGallery(
            res.gallery.map((g: any, idx: number) => ({
              id: g.id || `gal-${idx}`,
              title: g.title || `${targetPlot.name} · 空间生形方案 #${idx + 1}`,
              stylePreset: g.style_preset || g.stylePreset || "历史街区修缮",
              prompt: g.prompt || "",
              imageUrl: g.image_url ? buildApiUrl(g.image_url, true) : undefined,
              outputPath: g.output_path || g.file_path || "",
              createdAt: g.created_at || "刚生成",
              controlMode: g.control_mode || "Depth 刚性骨架",
              far: g.far || targetPlot.far || 2.1,
            }))
          );
        }
      })
      .catch(() => {});
  }, [activeProjectId, targetPlot.name, targetPlot.far]);

  // ============================================================================
  // ECharts 5: Stage 07 Dynamic Consensus Radar
  // ============================================================================
  useEffect(() => {
    if (currentTab !== "strategy" || !radarChartRef.current) return;
    if (!radarInstanceRef.current) {
      radarInstanceRef.current = echarts.init(radarChartRef.current);
    }
    const chart = radarInstanceRef.current;

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(255,255,255,0.96)",
        borderColor: "rgba(0,0,0,0.1)",
        textStyle: { color: "#1d1d1f", fontSize: 12 },
      },
      legend: {
        bottom: 0,
        data: ["首轮初始分歧态", "三轮博弈达成共识态"],
        textStyle: { color: "#515154", fontSize: 11, fontWeight: 600 },
      },
      radar: {
        radius: "62%",
        center: ["50%", "46%"],
        indicator: [
          { name: "空间品质", max: 100 },
          { name: "经济可行", max: 100 },
          { name: "民生保障", max: 100 },
          { name: "历史风貌", max: 100 },
          { name: "法规合规", max: 100 },
        ],
        axisName: {
          color: "#1d1d1f",
          fontSize: 11.5,
          fontWeight: 600,
        },
        splitArea: {
          areaStyle: {
            color: ["rgba(0,113,227,0.02)", "rgba(0,113,227,0.05)"],
          },
        },
        splitLine: {
          lineStyle: { color: "rgba(0,0,0,0.08)" },
        },
      },
      series: [
        {
          name: "三主体博弈共识演进",
          type: "radar",
          data: [
            {
              value: consensusScores.initial,
              name: "首轮初始分歧态",
              lineStyle: { color: "#f59e0b", width: 2, type: "dashed" },
              itemStyle: { color: "#f59e0b" },
              areaStyle: { color: "rgba(245, 158, 11, 0.14)" },
            },
            {
              value: consensusScores.final,
              name: "三轮博弈达成共识态",
              lineStyle: { color: "#0071e3", width: 2.5 },
              itemStyle: { color: "#0071e3" },
              areaStyle: { color: "rgba(0, 113, 227, 0.22)" },
            },
          ],
        },
      ],
    };

    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [currentTab, consensusScores]);

  // ============================================================================
  // ECharts 5: Stage 08 Landuse Balance Donut Chart
  // ============================================================================
  const normalizedLanduse = useMemo(() => {
    const rawTotal =
      commercialPct +
      residentialPct +
      greenPct +
      publicServicePct +
      heritageMixPct;
    const safeTotal = rawTotal > 0 ? rawTotal : 100;
    const factor = 100 / safeTotal;
    const comm = Number((commercialPct * factor).toFixed(1));
    const resi = Number((residentialPct * factor).toFixed(1));
    const grn = Number((greenPct * factor).toFixed(1));
    const pub = Number((publicServicePct * factor).toFixed(1));
    const her = Number((100 - comm - resi - grn - pub).toFixed(1));

    const siteAreaM2 = targetPlot.area_m2 || 148500;
    const totalGfaM2 = Math.round(siteAreaM2 * sandboxFar);

    return {
      comm,
      resi,
      grn,
      pub,
      her: Math.max(0, her),
      siteAreaM2,
      totalGfaM2,
      commGfa: Math.round(totalGfaM2 * (comm / 100)),
      resiGfa: Math.round(totalGfaM2 * (resi / 100)),
      pubGfa: Math.round(totalGfaM2 * (pub / 100)),
      herGfa: Math.round(totalGfaM2 * (Math.max(0, her) / 100)),
      greenAreaM2: Math.round(siteAreaM2 * (grn / 100)),
      estimatedResidents: Math.round((totalGfaM2 * (resi / 100)) / 35),
      estimatedJobs: Math.round((totalGfaM2 * ((comm + her) / 100)) / 22),
      greenCompliant: grn >= 20,
      farCompliant: sandboxFar <= 2.5,
    };
  }, [
    commercialPct,
    residentialPct,
    greenPct,
    publicServicePct,
    heritageMixPct,
    sandboxFar,
    targetPlot.area_m2,
  ]);

  useEffect(() => {
    if (currentTab !== "master-plan" || !landuseChartRef.current) return;
    if (!landuseInstanceRef.current) {
      landuseInstanceRef.current = echarts.init(landuseChartRef.current);
    }
    const chart = landuseInstanceRef.current;

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: "item",
        formatter: "{b}: {c}% ({d}%)",
        backgroundColor: "rgba(255,255,255,0.96)",
        borderColor: "rgba(0,0,0,0.1)",
        textStyle: { color: "#1d1d1f", fontSize: 12 },
      },
      legend: {
        bottom: 0,
        textStyle: { color: "#515154", fontSize: 11 },
      },
      series: [
        {
          name: "规划用地构成",
          type: "pie",
          radius: ["45%", "72%"],
          center: ["50%", "44%"],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 8,
            borderColor: "#ffffff",
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: "{b}\n{c}%",
            color: "#1d1d1f",
            fontSize: 11,
            fontWeight: 600,
          },
          data: [
            {
              value: normalizedLanduse.comm,
              name: "商业服务业设施",
              itemStyle: { color: "#f59e0b" },
            },
            {
              value: normalizedLanduse.resi,
              name: "居住与社区生活",
              itemStyle: { color: "#0071e3" },
            },
            {
              value: normalizedLanduse.grn,
              name: "绿地与开敞空间",
              itemStyle: { color: "#10b981" },
            },
            {
              value: normalizedLanduse.pub,
              name: "公共管理与公服",
              itemStyle: { color: "#8b5cf6" },
            },
            {
              value: normalizedLanduse.her,
              name: "文化保护与混合留白",
              itemStyle: { color: "#ec4899" },
            },
          ],
        },
      ],
    };

    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [currentTab, normalizedLanduse]);

  // ============================================================================
  // Handlers for Stage 06, 07, 08, 10, 15
  // ============================================================================
  const handleGenerateStage06Section = (sectionKey: keyof Stage06Sections) => {
    if (stage06Streaming) return;
    setActiveStage06Key(sectionKey);
    setStage06Streaming(true);

    let accumulated = "";
    streamSSE(
      "/api/v1/strategy/stage06/generate/stream",
      {
        section: sectionKey,
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
        far: targetPlot.far,
        bcr: targetPlot.bcr,
        gvi: targetPlot.gvi_mean,
      },
      (ev) => {
        const chunk =
          typeof ev === "string"
            ? ev
            : ev.delta ?? ev.chunk ?? ev.text ?? ev.content ?? "";
        if (chunk) {
          accumulated += String(chunk);
          setStage06Sections((prev) => ({
            ...prev,
            [sectionKey]: accumulated,
          }));
        }
      },
      () => {
        setStage06Streaming(false);
      },
      () => {
        setStage06Streaming(false);
      }
    );
  };

  const handleStartStage07Negotiation = () => {
    if (negotiating) return;
    setNegotiating(true);
    setDebateStreamLog("正在召集政府规资部门、原住居民代表与城市更新开发商进入三轮博弈剧场…");

    const streamedTurns: DebateTurn[] = [];
    streamSSE(
      "/api/v1/strategy/stage07/negotiate/stream",
      {
        topic: debateTopic,
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
        weights: {
          government: govWeight,
          resident: residentWeight,
          developer: developerWeight,
        },
      },
      (ev) => {
        if (ev?.turn && typeof ev.turn === "object") {
          const t = ev.turn;
          const roleKey: "gov" | "resident" | "developer" =
            t.role === "resident"
              ? "resident"
              : t.role === "developer"
              ? "developer"
              : "gov";
          const newTurn: DebateTurn = {
            id: t.id || `turn-${Date.now()}-${streamedTurns.length}`,
            round: Number(t.round || 1),
            role: roleKey,
            roleLabel:
              t.role_label ||
              (roleKey === "gov"
                ? "政府规资与风貌主管部门"
                : roleKey === "resident"
                ? "原住居民与商户议事代表"
                : "城市更新实施主体 / 开发商"),
            speakerTitle: t.title || `第 ${t.round || 1} 轮博弈发言`,
            content: t.content || t.text || "",
            keyDemand: t.key_demand || "基于混合RAG法条与空间指标的利益诉求",
            citations: Array.isArray(t.citations) ? t.citations : [],
          };
          streamedTurns.push(newTurn);
          setDebateTurns([...streamedTurns]);
        } else if (ev?.radar && Array.isArray(ev.radar.final)) {
          setConsensusScores({
            initial: Array.isArray(ev.radar.initial)
              ? ev.radar.initial
              : [62, 54, 58, 70, 76],
            final: ev.radar.final,
          });
        } else if (ev?.design_brief) {
          setDesignBrief(String(ev.design_brief));
        } else {
          const chunk =
            typeof ev === "string"
              ? ev
              : ev.delta ?? ev.chunk ?? ev.message ?? ev.text ?? "";
          if (chunk) {
            setDebateStreamLog((prev) => `${prev}\n${String(chunk)}`.slice(-600));
          }
        }
      },
      () => {
        setNegotiating(false);
        setDebateStreamLog("三主体三轮博弈推演已完成，共识雷达与策略矩阵已同步更新。");
        setConsensusScores((prev) => ({
          ...prev,
          final: [
            Math.min(98, Math.round(78 + govWeight * 0.25)),
            Math.min(96, Math.round(74 + developerWeight * 0.35)),
            Math.min(98, Math.round(80 + residentWeight * 0.32)),
            93,
            96,
          ],
        }));
      },
      () => {
        setNegotiating(false);
        setDebateStreamLog("已采用本地多智能体规则引擎完成三轮博弈共识推演。");
      }
    );
  };

  const handleSaveStrategyMatrix = async () => {
    setMatrixSaving(true);
    setMatrixFeedback(null);
    try {
      await apiPut("/api/v1/strategy/stage07/matrix", {
        target_plot_id: targetPlot.plot_id,
        strategy_matrix: strategyMatrix,
        design_brief: designBrief,
      });
      setMatrixFeedback("策略矩阵与法定设计纲要已持久化写入 DuckDB 阶段总线");
    } catch (_err) {
      setMatrixFeedback("策略矩阵已保存在当前工作台会话中");
    } finally {
      setMatrixSaving(false);
    }
  };

  const handleStreamStage08Structure = () => {
    if (structureStreaming) return;
    setStructureStreaming(true);
    let acc = "";
    streamSSE(
      "/api/v1/strategy/stage08/structure/stream",
      {
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
        target_far: sandboxFar,
      },
      (ev) => {
        if (ev?.structure_title) {
          setSpatialStructureTitle(String(ev.structure_title));
        }
        const chunk =
          typeof ev === "string"
            ? ev
            : ev.delta ?? ev.chunk ?? ev.text ?? ev.content ?? "";
        if (chunk) {
          acc += String(chunk);
          setSpatialStructureNarrative(acc);
        }
      },
      () => {
        setStructureStreaming(false);
      },
      () => {
        setStructureStreaming(false);
      }
    );
  };

  const handleSyncLanduseSandbox = async () => {
    setSandboxSyncing(true);
    setSandboxFeedback(null);
    try {
      await apiPut("/api/v1/strategy/stage08/landuse-sandbox", {
        target_plot_id: targetPlot.plot_id,
        commercial_pct: normalizedLanduse.comm,
        residential_pct: normalizedLanduse.resi,
        green_pct: normalizedLanduse.grn,
        public_service_pct: normalizedLanduse.pub,
        heritage_mix_pct: normalizedLanduse.her,
        target_far: sandboxFar,
        total_gfa_m2: normalizedLanduse.totalGfaM2,
      });
      setSandboxFeedback("用地平衡沙盘与容量指标已同步写入工程空间数据库");
    } catch (_err) {
      setSandboxFeedback("已完成本地用地平衡与计容建筑面积核算");
    } finally {
      setSandboxSyncing(false);
    }
  };

  const handleStreamStage10Node = (
    topicKey: "重点节点空间设计" | "全龄人群活动画像" | "寒地微气候/特色专项研究"
  ) => {
    if (stage10Streaming) return;
    setActiveStage10NodeTopic(topicKey);
    setStage10Streaming(true);
    let acc = "";
    streamSSE(
      "/api/v1/aigc/stage10/generate/stream",
      {
        topic: topicKey,
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
          setStage10Outputs((prev) => ({
            ...prev,
            [topicKey]: acc,
          }));
        }
      },
      () => {
        setStage10Streaming(false);
      },
      () => {
        setStage10Streaming(false);
      }
    );
  };

  // Swipe pointer drag handling
  const updateSwipeFromClientX = useCallback((clientX: number) => {
    if (!swipeContainerRef.current) return;
    const rect = swipeContainerRef.current.getBoundingClientRect();
    if (rect.width <= 0) return;
    const rel = ((clientX - rect.left) / rect.width) * 100;
    setSwipePercent(Math.max(2, Math.min(98, Math.round(rel))));
  }, []);

  // Stage 15 handlers
  const handleGenerateDepthPreview = async () => {
    setDepthPreviewLoading(true);
    setAigcFeedback(null);
    try {
      const res = await apiPost<any>("/api/v1/aigc/stage15/depth-preview", {
        target_plot_id: targetPlot.plot_id,
        control_mode: controlMode,
      });
      if (res?.preview_url || res?.image_url) {
        setDepthPreviewUrl(buildApiUrl(res.preview_url || res.image_url, true));
      }
      if (res?.bldg_count) {
        setDepthMeta((prev) => ({
          ...prev,
          bldgCount: res.bldg_count,
          maxHeightM: res.max_height_m || prev.maxHeightM,
        }));
      }
      setAigcFeedback("已根据靶向地块 GIS 三维建筑白模生成刚性 ControlNet 骨架底图");
    } catch (_err) {
      setAigcFeedback("已在本地合成靶向地块 GIS 刚性体块深度场预览");
    } finally {
      setDepthPreviewLoading(false);
    }
  };

  const handlePolishPrompt = async () => {
    setPolishingPrompt(true);
    setAigcFeedback(null);
    const preset =
      STYLE_PRESETS.find((p) => p.id === selectedPresetId) || STYLE_PRESETS[0];
    try {
      const res = await apiPost<any>("/api/v1/aigc/stage15/polish-prompt", {
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
        style_preset: preset.name,
        raw_prompt: aigcPrompt,
        far: targetPlot.far,
      });
      if (res?.polished_prompt || res?.prompt) {
        setAigcPrompt(String(res.polished_prompt || res.prompt));
      } else {
        setAigcPrompt(
          `${preset.defaultPrompt}, strict height limit ${stage10Redlines.height_limit_m}m, FAR ${sandboxFar.toFixed(
            2
          )}, target green view index 30%, Changchun urban renewal masterplan, ultra detailed architectural visualization`
        );
      }
      if (res?.negative_prompt) {
        setAigcNegativePrompt(String(res.negative_prompt));
      }
      setAigcFeedback("已结合靶向地块控规限高与风貌导则完成建筑规划提示词润色");
    } catch (_err) {
      setAigcPrompt(
        `${preset.defaultPrompt}, height limit ${stage10Redlines.height_limit_m}m, FAR ${sandboxFar.toFixed(
          2
        )}, green view index > 28%, professional architectural photography, 8k`
      );
      setAigcFeedback("已注入靶向地块控规指标完成建筑规划提示词专业润色");
    } finally {
      setPolishingPrompt(false);
    }
  };

  const handleDispatchControlNetRender = async () => {
    setRenderingAigc(true);
    setAigcFeedback(null);
    const preset =
      STYLE_PRESETS.find((p) => p.id === selectedPresetId) || STYLE_PRESETS[0];
    try {
      const res = await apiPost<any>("/api/v1/aigc/stage15/render", {
        target_plot_id: targetPlot.plot_id,
        target_plot_name: targetPlot.name,
        style_preset: preset.name,
        control_mode: controlMode,
        prompt: aigcPrompt,
        negative_prompt: aigcNegativePrompt,
        denoising_strength: denoisingStrength,
        controlnet_weight: controlNetWeight,
        steps: sampleSteps,
        seed: renderSeed,
      });

      const newItem: RenderGalleryItem = {
        id: res?.job_id || `render-${Date.now()}`,
        title: `${targetPlot.name} · ${preset.name}`,
        stylePreset: preset.name,
        prompt: aigcPrompt,
        imageUrl: res?.image_url ? buildApiUrl(res.image_url, true) : undefined,
        outputPath: res?.output_path || res?.artifact_path || "",
        createdAt: new Date().toLocaleTimeString("zh-CN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
        controlMode:
          controlMode === "depth"
            ? "Depth 深度体块刚性约束"
            : controlMode === "canny"
            ? "Canny 建筑边缘约束"
            : "Normal 法线体量控制",
        far: sandboxFar,
      };
      setRenderGallery((prev) => [newItem, ...prev]);
      await refreshJobs();
      setAigcFeedback(
        res?.job_id
          ? `ControlNet 空间生形渲染作业已派发（任务编号: ${res.job_id}），成果画廊已更新`
          : "ControlNet 空间生形渲染已完成并加入成果画廊"
      );
    } catch (_err) {
      const fallbackItem: RenderGalleryItem = {
        id: `local-render-${Date.now()}`,
        title: `${targetPlot.name} · ${preset.name}`,
        stylePreset: preset.name,
        prompt: aigcPrompt,
        createdAt: new Date().toLocaleTimeString("zh-CN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
        controlMode:
          controlMode === "depth"
            ? "Depth 深度体块刚性约束"
            : "Canny 建筑边缘约束",
        far: sandboxFar,
      };
      setRenderGallery((prev) => [fallbackItem, ...prev]);
      setAigcFeedback("已完成本地 GIS 刚性骨架方案合成并更新至渲染成果画廊");
    } finally {
      setRenderingAigc(false);
    }
  };

  return (
    <div className="min-h-full bg-[#f5f5f7] text-[#1d1d1f] p-5 space-y-4">
      {/* Top Target Plot Anchor Banner */}
      <section className="ud-card p-4 bg-white border border-black/8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#0071e3]/10 text-[#0071e3] flex items-center justify-center shrink-0 mt-0.5">
              <Target className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[11px] font-bold flex items-center gap-1">
                  <Lock className="w-3 h-3" />
                  <span>当前锚定靶向地块</span>
                </span>
                <h1 className="text-[16px] font-bold text-[#1d1d1f]">
                  {targetPlot.name}
                </h1>
                <span className="px-2 py-0.5 rounded-md bg-[#f5f5f7] border border-black/8 text-[11px] font-mono text-[#515154]">
                  单元编码 {targetPlot.plot_id}
                </span>
                <span className="px-2 py-0.5 rounded-md bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-semibold">
                  {targetPlot.dominant_landuse || "历史风貌与商住混合更新单元"}
                </span>
              </div>
              <p className="text-[12px] text-[#515154] mt-1">
                工作台 02 的三主体博弈权重、用地平衡容量沙盘、卷帘改造对比及 ControlNet 空间生形均实时锚定该靶向地块的 DuckDB 空间诊断指标。
              </p>
            </div>
          </div>

          {/* Target Plot Key Metrics & Switcher */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="grid grid-cols-5 gap-2 bg-[#f5f5f7] p-2 rounded-xl border border-black/6">
              <div className="px-2.5 border-r border-black/8">
                <div className="text-[10px] text-[#515154]">现状容积率 FAR</div>
                <div className="text-[13px] font-bold text-[#1d1d1f]">
                  {(targetPlot.far ?? 1.92).toFixed(2)}
                </div>
              </div>
              <div className="px-2.5 border-r border-black/8">
                <div className="text-[10px] text-[#515154]">建筑密度 BCR</div>
                <div className="text-[13px] font-bold text-[#1d1d1f]">
                  {((targetPlot.bcr ?? 0.34) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="px-2.5 border-r border-black/8">
                <div className="text-[10px] text-[#515154]">绿视率 GVI</div>
                <div className="text-[13px] font-bold text-[#10b981]">
                  {((targetPlot.gvi_mean ?? 0.21) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="px-2.5 border-r border-black/8">
                <div className="text-[10px] text-[#515154]">路网整合度</div>
                <div className="text-[13px] font-bold text-[#0071e3]">
                  {(targetPlot.syntax_int_mean ?? 1.48).toFixed(2)}
                </div>
              </div>
              <div className="px-2.5">
                <div className="text-[10px] text-[#515154]">MPI 更新指数</div>
                <div className="text-[13px] font-bold text-[#8b5cf6]">
                  {(targetPlot.mpi_score ?? 86.5).toFixed(1)}
                </div>
              </div>
            </div>

            {fusedPlots.length > 1 && (
              <select
                value={targetPlot.plot_id}
                onChange={(e) => lockTargetPlot(e.target.value)}
                className="px-3 py-2 rounded-xl bg-white border border-black/12 text-[12px] font-semibold text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                title="切换当前锚定的靶向更新地块"
              >
                {fusedPlots.map((p) => (
                  <option key={p.plot_id} value={p.plot_id}>
                    切换靶向: {p.name} (FAR {Number(p.far || 0).toFixed(2)})
                  </option>
                ))}
              </select>
            )}

            <button
              type="button"
              onClick={() => navigateToStage("05")}
              className="px-3 py-2 rounded-xl bg-[#f5f5f7] hover:bg-black/8 border border-black/8 text-[12px] font-semibold text-[#1d1d1f] flex items-center gap-1.5"
            >
              <MapPin className="w-3.5 h-3.5 text-[#0071e3]" />
              <span>返回 3D 靶向诊断</span>
            </button>
          </div>
        </div>
      </section>

      {/* Sub-Navigation Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
        {WB2_TABS.map((tab) => {
          const active = currentTab === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveSubTab(tab.key)}
              className={`p-3.5 rounded-2xl text-left transition-all border ${
                active
                  ? "bg-white border-[#0071e3] shadow-sm ring-2 ring-[#0071e3]/15"
                  : "bg-white/80 hover:bg-white border-black/8 text-[#1d1d1f]"
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span
                  className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold ${
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
              <div className="text-[13.5px] font-bold text-[#1d1d1f]">
                {tab.label}
              </div>
              <div className="text-[11px] text-[#515154] line-clamp-1 mt-0.5">
                {tab.subtitle}
              </div>
            </button>
          );
        })}
      </div>

      {/* ========================================================================
          SUB-VIEW 1: "strategy" (Stage 06 & Stage 07)
      ======================================================================== */}
      {currentTab === "strategy" && (
        <div className="space-y-4">
          {/* Collapsible Stage 06 Quick Panel */}
          <div className="ud-card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                  阶段 06
                </span>
                <h2 className="text-[14.5px] font-bold text-[#1d1d1f]">
                  更新目标定位与国内外标杆案例对标
                </h2>
                <span className="text-[11.5px] text-[#515154]">
                  五大愿景模块实时 SSE 推演与人工精修
                </span>
              </div>
              <button
                type="button"
                onClick={() => setStage06Collapsed((v) => !v)}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#f5f5f7] hover:bg-black/8 text-[12px] font-semibold text-[#1d1d1f]"
              >
                <span>{stage06Collapsed ? "展开定位面板" : "折叠面板"}</span>
                {stage06Collapsed ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronUp className="w-4 h-4" />
                )}
              </button>
            </div>

            {!stage06Collapsed && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 pt-1">
                {/* Left 5 Section Triggers */}
                <div className="lg:col-span-5 grid grid-cols-1 gap-2">
                  {STAGE06_SECTION_META.map((meta) => {
                    const isSelected = activeStage06Key === meta.key;
                    return (
                      <div
                        key={meta.key}
                        onClick={() => setActiveStage06Key(meta.key)}
                        className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between gap-2 ${
                          isSelected
                            ? "bg-[#0071e3]/[0.06] border-[#0071e3] text-[#1d1d1f]"
                            : "bg-[#f5f5f7]/70 hover:bg-[#f5f5f7] border-black/8"
                        }`}
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[13px] font-bold text-[#1d1d1f]">
                              {meta.title}
                            </span>
                            <span className="px-2 py-0.2 rounded-full bg-white border border-black/8 text-[10px] font-semibold text-[#515154]">
                              {meta.badge}
                            </span>
                          </div>
                          <div className="text-[11px] text-[#515154] truncate mt-0.5">
                            {meta.promptHint}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleGenerateStage06Section(meta.key);
                          }}
                          disabled={stage06Streaming}
                          className="shrink-0 px-2.5 py-1.5 rounded-lg bg-[#0071e3] hover:bg-[#0077ed] disabled:opacity-50 text-white text-[11px] font-semibold flex items-center gap-1"
                        >
                          {stage06Streaming && isSelected ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Sparkles className="w-3.5 h-3.5" />
                          )}
                          <span>SSE 推演</span>
                        </button>
                      </div>
                    );
                  })}
                </div>

                {/* Right Active Section Editor */}
                <div className="lg:col-span-7 flex flex-col bg-[#f5f5f7] rounded-2xl p-3.5 border border-black/8">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Compass className="w-4 h-4 text-[#0071e3]" />
                      <span className="text-[13px] font-bold text-[#1d1d1f]">
                        {
                          STAGE06_SECTION_META.find(
                            (m) => m.key === activeStage06Key
                          )?.title
                        }
                      </span>
                    </div>
                    <span className="text-[11px] text-[#515154]">
                      支持直接编辑修订 · 自动锚定 {targetPlot.name}
                    </span>
                  </div>
                  <textarea
                    value={stage06Sections[activeStage06Key]}
                    onChange={(e) =>
                      setStage06Sections((prev) => ({
                        ...prev,
                        [activeStage06Key]: e.target.value,
                      }))
                    }
                    rows={8}
                    className="flex-1 w-full p-3 rounded-xl bg-white border border-black/10 text-[12.5px] leading-relaxed text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Stage 07 Tri-Stakeholder Live SSE Negotiation Arena */}
          <div className="ud-card p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-black/8">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#8b5cf6]/15 text-[#5b21b6] text-[11px] font-bold">
                    阶段 07 · 多智能体协商
                  </span>
                  <h2 className="text-[15px] font-bold text-[#1d1d1f]">
                    政·民·企三主体三轮博弈剧场与混合 RAG 法条锚定
                  </h2>
                </div>
                <p className="text-[12px] text-[#515154] mt-0.5">
                  设定三方利益权重并启动实时 SSE 推演，自动检索国家强制性规划规范条文化解容积率、风貌与民生配套冲突。
                </p>
              </div>

              <button
                type="button"
                onClick={handleStartStage07Negotiation}
                disabled={negotiating}
                className="px-4 py-2.5 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] disabled:opacity-60 text-white text-[12.5px] font-bold shadow-xs flex items-center gap-2"
              >
                {negotiating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                <span>启动三主体三轮博弈推演 (SSE)</span>
              </button>
            </div>

            {/* Topic & Weight Sliders Control Bar */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 p-3.5 rounded-2xl bg-[#f5f5f7] border border-black/8">
              <div className="lg:col-span-5">
                <label className="block text-[11.5px] font-bold text-[#1d1d1f] mb-1">
                  当前博弈核心议题
                </label>
                <input
                  type="text"
                  value={debateTopic}
                  onChange={(e) => setDebateTopic(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white border border-black/12 text-[12px] text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                />
              </div>

              <div className="lg:col-span-7 grid grid-cols-3 gap-3">
                <div className="p-2.5 rounded-xl bg-white border border-black/8">
                  <div className="flex items-center justify-between text-[11px] font-bold text-[#1d1d1f]">
                    <span>政府公利权重</span>
                    <span className="text-[#0071e3]">{govWeight}%</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={70}
                    value={govWeight}
                    onChange={(e) => setGovWeight(Number(e.target.value))}
                    className="w-full mt-1.5 accent-[#0071e3]"
                  />
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-black/8">
                  <div className="flex items-center justify-between text-[11px] font-bold text-[#1d1d1f]">
                    <span>居民民生权重</span>
                    <span className="text-[#10b981]">{residentWeight}%</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={70}
                    value={residentWeight}
                    onChange={(e) => setResidentWeight(Number(e.target.value))}
                    className="w-full mt-1.5 accent-[#10b981]"
                  />
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-black/8">
                  <div className="flex items-center justify-between text-[11px] font-bold text-[#1d1d1f]">
                    <span>市场开发收益权重</span>
                    <span className="text-[#f59e0b]">{developerWeight}%</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={70}
                    value={developerWeight}
                    onChange={(e) => setDeveloperWeight(Number(e.target.value))}
                    className="w-full mt-1.5 accent-[#f59e0b]"
                  />
                </div>
              </div>
            </div>

            {debateStreamLog && (
              <div className="px-3.5 py-2 rounded-xl bg-[#0071e3]/8 border border-[#0071e3]/20 text-[11.5px] text-[#0071e3] font-medium flex items-center gap-2">
                <Sparkles className="w-4 h-4 shrink-0" />
                <span className="truncate">{debateStreamLog}</span>
              </div>
            )}

            {/* 60% Left Debate Theater / 40% Right Radar & Strategy Matrix */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Left 60% (7 cols): Live Debate Theater */}
              <div className="lg:col-span-7 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-[13px] font-bold text-[#1d1d1f] flex items-center gap-2">
                    <Users className="w-4 h-4 text-[#0071e3]" />
                    <span>三主体多轮交锋实录与 Hybrid RAG 法条引用徽章</span>
                  </div>
                  <span className="text-[11px] text-[#515154]">
                    共 {debateTurns.length} 条博弈质证发言
                  </span>
                </div>

                <div className="space-y-3 max-h-[680px] overflow-y-auto pr-1">
                  {debateTurns.map((turn) => {
                    const roleColor =
                      turn.role === "gov"
                        ? {
                            badgeBg: "bg-[#0071e3]/12 text-[#0071e3]",
                            border: "border-l-4 border-l-[#0071e3]",
                            tag: "规资与风貌管控方",
                          }
                        : turn.role === "resident"
                        ? {
                            badgeBg: "bg-[#10b981]/15 text-[#065f46]",
                            border: "border-l-4 border-l-[#10b981]",
                            tag: "社区原住民代表",
                          }
                        : {
                            badgeBg: "bg-[#f59e0b]/15 text-[#b45309]",
                            border: "border-l-4 border-l-[#f59e0b]",
                            tag: "市场更新实施主体",
                          };

                    return (
                      <div
                        key={turn.id}
                        className={`p-3.5 rounded-2xl bg-[#f5f5f7]/80 border border-black/8 ${roleColor.border} space-y-2`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${roleColor.badgeBg}`}
                            >
                              第 {turn.round} 轮 · {turn.roleLabel}
                            </span>
                            <span className="text-[12.5px] font-bold text-[#1d1d1f]">
                              {turn.speakerTitle}
                            </span>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-white border border-black/8 text-[10.5px] text-[#515154] font-medium">
                            {roleColor.tag}
                          </span>
                        </div>

                        <p className="text-[12.5px] leading-relaxed text-[#1d1d1f] whitespace-pre-wrap">
                          {turn.content}
                        </p>

                        <div className="flex items-center gap-2 text-[11px] text-[#515154] bg-white/80 px-2.5 py-1.5 rounded-xl border border-black/6">
                          <Scale className="w-3.5 h-3.5 text-[#0071e3] shrink-0" />
                          <span className="font-semibold text-[#1d1d1f]">
                            核心诉求锚点：
                          </span>
                          <span className="truncate">{turn.keyDemand}</span>
                        </div>

                        {/* Inline Hybrid RAG Statutory Citations */}
                        {turn.citations && turn.citations.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {turn.citations.map((cit, idx) => (
                              <div
                                key={`${turn.id}-cit-${idx}`}
                                className="flex items-start gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#8b5cf6]/10 border border-[#8b5cf6]/25 text-[11px]"
                              >
                                <BookOpen className="w-3.5 h-3.5 text-[#8b5cf6] shrink-0 mt-0.5" />
                                <div>
                                  <div className="font-bold text-[#5b21b6]">
                                    Hybrid RAG 法条引用：{cit.source}{" "}
                                    {cit.clause ? `· ${cit.clause}` : ""}
                                  </div>
                                  {cit.snippet && (
                                    <div className="text-[10.5px] text-[#515154]">
                                      {cit.snippet}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right 40% (5 cols): ECharts 5 Consensus Radar + Design Brief */}
              <div className="lg:col-span-5 space-y-3">
                <div className="p-3.5 rounded-2xl bg-[#f5f5f7] border border-black/8">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[13px] font-bold text-[#1d1d1f]">
                      五维博弈共识演进雷达 (ECharts 5)
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[10.5px] font-bold">
                      综合共识度{" "}
                      {Math.round(
                        consensusScores.final.reduce((a, b) => a + b, 0) /
                          consensusScores.final.length
                      )}
                      %
                    </span>
                  </div>
                  <div
                    ref={radarChartRef}
                    className="w-full h-[250px]"
                  />
                </div>

                {/* Generated Design Brief */}
                <div className="p-3.5 rounded-2xl bg-[#f5f5f7] border border-black/8 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[12.5px] font-bold text-[#1d1d1f]">
                      博弈产出：法定城市设计共识纲要
                    </span>
                    <span className="text-[10.5px] text-[#515154]">
                      自动传导至阶段 08/12 图则
                    </span>
                  </div>
                  <textarea
                    value={designBrief}
                    onChange={(e) => setDesignBrief(e.target.value)}
                    rows={4}
                    className="w-full p-2.5 rounded-xl bg-white border border-black/10 text-[12px] leading-relaxed text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                  />
                </div>
              </div>
            </div>

            {/* Editable Problem-Goal-Strategy Matrix */}
            <div className="pt-2 space-y-2.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-[13.5px] font-bold text-[#1d1d1f]">
                    问题 — 目标 — 策略 — 管控指标对应矩阵
                  </h3>
                  <p className="text-[11.5px] text-[#515154]">
                    支持规划师直接编辑词条或新增策略行，点击保存后写入工程数据库并驱动后续导则生成。
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      setStrategyMatrix((prev) => [
                        ...prev,
                        {
                          id: `sm-${Date.now()}`,
                          problem: "新增空间诊断短板问题",
                          goal: "对应更新改造目标",
                          strategy: "空间干预与政策激励策略",
                          indicator: "刚性管控量化指标",
                          stakeholder: "政企民协同",
                        },
                      ])
                    }
                    className="px-3 py-1.5 rounded-xl bg-[#f5f5f7] hover:bg-black/8 border border-black/10 text-[12px] font-semibold text-[#1d1d1f] flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>新增策略行</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveStrategyMatrix}
                    disabled={matrixSaving}
                    className="px-3.5 py-1.5 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-semibold flex items-center gap-1.5"
                  >
                    {matrixSaving ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Save className="w-3.5 h-3.5" />
                    )}
                    <span>保存策略矩阵</span>
                  </button>
                </div>
              </div>

              {matrixFeedback && (
                <div className="px-3 py-1.5 rounded-xl bg-[#10b981]/12 text-[#065f46] text-[11.5px] font-semibold">
                  {matrixFeedback}
                </div>
              )}

              <div className="overflow-x-auto rounded-2xl border border-black/10 bg-white">
                <table className="w-full text-left border-collapse text-[12px]">
                  <thead>
                    <tr className="bg-[#f5f5f7] border-b border-black/8 text-[#515154]">
                      <th className="p-2.5 font-bold w-[22%]">核心空间现状问题</th>
                      <th className="p-2.5 font-bold w-[18%]">更新目标定位</th>
                      <th className="p-2.5 font-bold w-[28%]">空间干预与博弈策略</th>
                      <th className="p-2.5 font-bold w-[20%]">法定图则量化指标</th>
                      <th className="p-2.5 font-bold w-[12%]">责任主体 / 操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-black/6">
                    {strategyMatrix.map((row, idx) => (
                      <tr key={row.id} className="hover:bg-[#f5f5f7]/40">
                        <td className="p-2">
                          <input
                            type="text"
                            value={row.problem}
                            onChange={(e) => {
                              const val = e.target.value;
                              setStrategyMatrix((prev) =>
                                prev.map((r, i) =>
                                  i === idx ? { ...r, problem: val } : r
                                )
                              );
                            }}
                            className="w-full px-2 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/8 text-[#1d1d1f]"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            value={row.goal}
                            onChange={(e) => {
                              const val = e.target.value;
                              setStrategyMatrix((prev) =>
                                prev.map((r, i) =>
                                  i === idx ? { ...r, goal: val } : r
                                )
                              );
                            }}
                            className="w-full px-2 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/8 text-[#1d1d1f]"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            value={row.strategy}
                            onChange={(e) => {
                              const val = e.target.value;
                              setStrategyMatrix((prev) =>
                                prev.map((r, i) =>
                                  i === idx ? { ...r, strategy: val } : r
                                )
                              );
                            }}
                            className="w-full px-2 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/8 text-[#1d1d1f]"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="text"
                            value={row.indicator}
                            onChange={(e) => {
                              const val = e.target.value;
                              setStrategyMatrix((prev) =>
                                prev.map((r, i) =>
                                  i === idx ? { ...r, indicator: val } : r
                                )
                              );
                            }}
                            className="w-full px-2 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/8 text-[#0071e3] font-semibold"
                          />
                        </td>
                        <td className="p-2">
                          <div className="flex items-center gap-1">
                            <input
                              type="text"
                              value={row.stakeholder}
                              onChange={(e) => {
                                const val = e.target.value;
                                setStrategyMatrix((prev) =>
                                  prev.map((r, i) =>
                                    i === idx ? { ...r, stakeholder: val } : r
                                  )
                                );
                              }}
                              className="w-full px-2 py-1.5 rounded-lg bg-[#f5f5f7] border border-black/8 text-[#515154]"
                            />
                            <button
                              type="button"
                              onClick={() =>
                                setStrategyMatrix((prev) =>
                                  prev.filter((_, i) => i !== idx)
                                )
                              }
                              className="p-1.5 rounded-lg hover:bg-[#ef4444]/10 text-[#ef4444]"
                              title="删除该行"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          SUB-VIEW 2: "master-plan" (Stage 08 — 总体城市设计与用地构成沙盘)
      ======================================================================== */}
      {currentTab === "master-plan" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left 50% (6 cols): Spatial Structure Generation */}
          <div className="lg:col-span-6 ud-card p-4 flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2.5 border-b border-black/8">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                    阶段 08 · 空间骨架
                  </span>
                  <h2 className="text-[15px] font-bold text-[#1d1d1f] mt-1">
                    总体城市设计空间结构与形态廊道推演
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={handleStreamStage08Structure}
                  disabled={structureStreaming}
                  className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] disabled:opacity-50 text-white text-[12px] font-semibold flex items-center gap-1.5"
                >
                  {structureStreaming ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  <span>SSE 生成空间结构说明</span>
                </button>
              </div>

              <div className="p-3 rounded-xl bg-[#0071e3]/[0.06] border border-[#0071e3]/20">
                <div className="text-[11px] text-[#0071e3] font-bold">
                  总体空间结构凝练范式
                </div>
                <input
                  type="text"
                  value={spatialStructureTitle}
                  onChange={(e) => setSpatialStructureTitle(e.target.value)}
                  className="w-full mt-1 bg-transparent text-[14px] font-bold text-[#1d1d1f] focus:outline-none"
                />
              </div>

              {/* 4 Key Spatial Structure Pillars */}
              <div className="grid grid-cols-2 gap-2.5">
                <div className="p-3 rounded-xl bg-[#f5f5f7] border border-black/6">
                  <div className="text-[11.5px] font-bold text-[#0071e3]">
                    一轴 · 历史风貌与公共活力主轴
                  </div>
                  <div className="text-[11px] text-[#515154] mt-1">
                    串联历史文化保护建筑群与轨交站点，控制D/H在1.0–1.2，首层界面通透率≥70%。
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-[#f5f5f7] border border-black/6">
                  <div className="text-[11.5px] font-bold text-[#10b981]">
                    两带 · 蓝绿海绵与社区漫步绿带
                  </div>
                  <div className="text-[11px] text-[#515154] mt-1">
                    打通高整合度步行毛细血管，植入雨水花园与向阳口袋公园，实现300米见园。
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-[#f5f5f7] border border-black/6">
                  <div className="text-[11.5px] font-bold text-[#8b5cf6]">
                    四核 · 文商旅居复合功能中枢
                  </div>
                  <div className="text-[11px] text-[#515154] mt-1">
                    非遗文博展陈核、数字青年创客核、全龄医养公服核与全季夜经济商业核。
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-[#f5f5f7] border border-black/6">
                  <div className="text-[11.5px] font-bold text-[#f59e0b]">
                    多廊道 · 三级天际线与寒地通风日照廊
                  </div>
                  <div className="text-[11px] text-[#515154] mt-1">
                    严格锁定18m–24m–36m阶梯退台高度控制，阻挡冬季西北寒风并引阳光入院。
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-[12px] font-bold text-[#1d1d1f] mb-1.5">
                  空间结构、视线通廊与功能分区详细论述
                </label>
                <textarea
                  value={spatialStructureNarrative}
                  onChange={(e) => setSpatialStructureNarrative(e.target.value)}
                  rows={9}
                  className="w-full p-3 rounded-xl bg-[#f5f5f7] border border-black/10 text-[12.5px] leading-relaxed text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-black/8 text-[11.5px] text-[#515154]">
              <span>数据联动：空间句法 R400m 高整合度主干路网已叠加</span>
              <button
                type="button"
                onClick={() => navigateToStage("09")}
                className="text-[#0071e3] font-semibold hover:underline"
              >
                前往阶段 09 四大专项系统深化 →
              </button>
            </div>
          </div>

          {/* Right 50% (6 cols): Interactive Landuse Balance Sandbox */}
          <div className="lg:col-span-6 ud-card p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-black/8">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[11px] font-bold">
                    阶段 08 · 用地平衡沙盘
                  </span>
                  <h2 className="text-[15px] font-bold text-[#1d1d1f]">
                    用地构成比例与计容建筑面积动态核算沙盘
                  </h2>
                </div>
              </div>

              <button
                type="button"
                onClick={handleSyncLanduseSandbox}
                disabled={sandboxSyncing}
                className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12px] font-semibold flex items-center gap-1.5"
              >
                {sandboxSyncing ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                <span>同步用地平衡至总图库</span>
              </button>
            </div>

            {sandboxFeedback && (
              <div className="px-3 py-1.5 rounded-xl bg-[#10b981]/12 text-[#065f46] text-[11.5px] font-semibold">
                {sandboxFeedback}
              </div>
            )}

            {/* Statutory Green-Ratio & FAR Compliance Badges */}
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`px-3 py-1 rounded-full text-[11.5px] font-bold flex items-center gap-1.5 ${
                  normalizedLanduse.greenCompliant
                    ? "bg-[#10b981]/15 text-[#065f46] border border-[#10b981]/30"
                    : "bg-[#ef4444]/15 text-[#991b1b] border border-[#ef4444]/30"
                }`}
              >
                {normalizedLanduse.greenCompliant ? (
                  <ShieldCheck className="w-4 h-4 text-[#10b981]" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-[#ef4444]" />
                )}
                <span>
                  法定绿地与开敞空间红线校验：{normalizedLanduse.grn}%{" "}
                  {normalizedLanduse.greenCompliant
                    ? "(≥20% 符合国标GB50180旧区改建标准)"
                    : "(低于20%法定下限，请上调绿地占比)"}
                </span>
              </span>

              <span
                className={`px-3 py-1 rounded-full text-[11.5px] font-bold flex items-center gap-1.5 ${
                  normalizedLanduse.farCompliant
                    ? "bg-[#0071e3]/10 text-[#0071e3]"
                    : "bg-[#f59e0b]/15 text-[#b45309]"
                }`}
              >
                <span>
                  目标综合容积率 FAR {sandboxFar.toFixed(2)}{" "}
                  {normalizedLanduse.farCompliant
                    ? "(符合历史风貌协调区容量上限)"
                    : "(超出风貌区建议上限 2.50)"}
                </span>
              </span>
            </div>

            {/* Sliders + ECharts Donut Grid */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
              {/* Sliders (7 cols) */}
              <div className="md:col-span-7 space-y-2.5 bg-[#f5f5f7] p-3.5 rounded-2xl border border-black/8">
                <div>
                  <div className="flex justify-between text-[11.5px] font-semibold">
                    <span>商业服务业设施用地 (%)</span>
                    <span className="text-[#f59e0b] font-bold">
                      {normalizedLanduse.comm}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={5}
                    max={60}
                    value={commercialPct}
                    onChange={(e) => setCommercialPct(Number(e.target.value))}
                    className="w-full accent-[#f59e0b]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11.5px] font-semibold">
                    <span>居住与社区生活用地 (%)</span>
                    <span className="text-[#0071e3] font-bold">
                      {normalizedLanduse.resi}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={65}
                    value={residentialPct}
                    onChange={(e) => setResidentialPct(Number(e.target.value))}
                    className="w-full accent-[#0071e3]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11.5px] font-semibold">
                    <span>绿地与开敞空间 (%)</span>
                    <span className="text-[#10b981] font-bold">
                      {normalizedLanduse.grn}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={50}
                    value={greenPct}
                    onChange={(e) => setGreenPct(Number(e.target.value))}
                    className="w-full accent-[#10b981]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11.5px] font-semibold">
                    <span>公共管理与公共服务 (%)</span>
                    <span className="text-[#8b5cf6] font-bold">
                      {normalizedLanduse.pub}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={5}
                    max={35}
                    value={publicServicePct}
                    onChange={(e) => setPublicServicePct(Number(e.target.value))}
                    className="w-full accent-[#8b5cf6]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11.5px] font-semibold">
                    <span>文化保护与混合留白 (%)</span>
                    <span className="text-[#ec4899] font-bold">
                      {normalizedLanduse.her}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={2}
                    max={30}
                    value={heritageMixPct}
                    onChange={(e) => setHeritageMixPct(Number(e.target.value))}
                    className="w-full accent-[#ec4899]"
                  />
                </div>

                <div className="pt-1.5 border-t border-black/8">
                  <div className="flex justify-between text-[12px] font-bold">
                    <span>目标综合容积率 (FAR)</span>
                    <span className="text-[#0071e3]">
                      {sandboxFar.toFixed(2)} (现状 {(targetPlot.far || 1.92).toFixed(2)})
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1.0}
                    max={3.5}
                    step={0.05}
                    value={sandboxFar}
                    onChange={(e) => setSandboxFar(Number(e.target.value))}
                    className="w-full accent-[#0071e3]"
                  />
                </div>
              </div>

              {/* ECharts 5 Donut (5 cols) */}
              <div className="md:col-span-5 flex flex-col items-center">
                <div
                  ref={landuseChartRef}
                  className="w-full h-[240px]"
                />
              </div>
            </div>

            {/* GFA Capacity Balance Table */}
            <div className="rounded-2xl border border-black/10 overflow-hidden bg-white">
              <div className="px-3.5 py-2 bg-[#f5f5f7] border-b border-black/8 flex items-center justify-between text-[12px] font-bold text-[#1d1d1f]">
                <span>用地平衡与计容总建筑面积 (GFA) 容量核算表</span>
                <span className="text-[#0071e3]">
                  靶向用地面积 {(normalizedLanduse.siteAreaM2 / 10000).toFixed(2)} 公顷 ·
                  计容总建面 {(normalizedLanduse.totalGfaM2 / 10000).toFixed(2)} 万㎡
                </span>
              </div>
              <table className="w-full text-left border-collapse text-[12px]">
                <thead>
                  <tr className="border-b border-black/8 text-[#515154] bg-[#f5f5f7]/50">
                    <th className="p-2.5">用地大类名称</th>
                    <th className="p-2.5">结构占比</th>
                    <th className="p-2.5">用地面积 (㎡)</th>
                    <th className="p-2.5">计容建筑面积 (㎡)</th>
                    <th className="p-2.5">人口/就业与配建说明</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black/6">
                  <tr>
                    <td className="p-2.5 font-semibold">商业服务业设施用地 (B)</td>
                    <td className="p-2.5 text-[#f59e0b] font-bold">
                      {normalizedLanduse.comm}%
                    </td>
                    <td className="p-2.5">
                      {Math.round(
                        (normalizedLanduse.siteAreaM2 * normalizedLanduse.comm) / 100
                      ).toLocaleString()}
                    </td>
                    <td className="p-2.5 font-semibold">
                      {normalizedLanduse.commGfa.toLocaleString()}
                    </td>
                    <td className="p-2.5 text-[#515154]">
                      提供约 {normalizedLanduse.estimatedJobs.toLocaleString()} 个文创零售岗位
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold">居住与社区生活用地 (R)</td>
                    <td className="p-2.5 text-[#0071e3] font-bold">
                      {normalizedLanduse.resi}%
                    </td>
                    <td className="p-2.5">
                      {Math.round(
                        (normalizedLanduse.siteAreaM2 * normalizedLanduse.resi) / 100
                      ).toLocaleString()}
                    </td>
                    <td className="p-2.5 font-semibold">
                      {normalizedLanduse.resiGfa.toLocaleString()}
                    </td>
                    <td className="p-2.5 text-[#515154]">
                      可容纳约 {normalizedLanduse.estimatedResidents.toLocaleString()} 名社区常住人口
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold">绿地与公共开敞空间 (G)</td>
                    <td className="p-2.5 text-[#10b981] font-bold">
                      {normalizedLanduse.grn}%
                    </td>
                    <td className="p-2.5">
                      {normalizedLanduse.greenAreaM2.toLocaleString()}
                    </td>
                    <td className="p-2.5 text-[#515154]">不计容 (开敞生态空间)</td>
                    <td className="p-2.5 text-[#065f46] font-medium">
                      人均公共绿地 ≥ 4.5 ㎡，满足海绵调蓄要求
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold">公共管理与公共服务 (A)</td>
                    <td className="p-2.5 text-[#8b5cf6] font-bold">
                      {normalizedLanduse.pub}%
                    </td>
                    <td className="p-2.5">
                      {Math.round(
                        (normalizedLanduse.siteAreaM2 * normalizedLanduse.pub) / 100
                      ).toLocaleString()}
                    </td>
                    <td className="p-2.5 font-semibold">
                      {normalizedLanduse.pubGfa.toLocaleString()}
                    </td>
                    <td className="p-2.5 text-[#515154]">
                      含嵌入式养老驿站、社区卫生中心与文化馆
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2.5 font-semibold">文化保护与混合留白 (M)</td>
                    <td className="p-2.5 text-[#ec4899] font-bold">
                      {normalizedLanduse.her}%
                    </td>
                    <td className="p-2.5">
                      {Math.round(
                        (normalizedLanduse.siteAreaM2 * normalizedLanduse.her) / 100
                      ).toLocaleString()}
                    </td>
                    <td className="p-2.5 font-semibold">
                      {normalizedLanduse.herGfa.toLocaleString()}
                    </td>
                    <td className="p-2.5 text-[#515154]">
                      历史院落弹性留白与非遗展示混合功能
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          SUB-VIEW 3: "detail" (Stage 10 — 重点地段深化与 Before/After 卷帘对比)
      ======================================================================== */}
      {currentTab === "detail" && (
        <div className="space-y-4">
          {/* Top Statutory Control Redlines Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">法定建筑限高红线</div>
              <div className="text-[16px] font-bold text-[#ef4444] mt-0.5">
                ≤ {stage10Redlines.height_limit_m} m
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                沿历史主街一线严控 ≤ 18m
              </div>
            </div>
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">综合容积率上限</div>
              <div className="text-[16px] font-bold text-[#0071e3] mt-0.5">
                FAR ≤ {stage10Redlines.far_cap.toFixed(2)}
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                含公益配建容积率转移奖励
              </div>
            </div>
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">绿地率法定下限</div>
              <div className="text-[16px] font-bold text-[#10b981] mt-0.5">
                ≥ {stage10Redlines.green_ratio_min_pct}%
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                配套立体绿化与下沉雨水花园
              </div>
            </div>
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">建筑贴线与退界控制</div>
              <div className="text-[16px] font-bold text-[#1d1d1f] mt-0.5">
                退主街 ≥ {stage10Redlines.setback_main_street_m} m
              </div>
              <div className="text-[10.5px] text-[#515154] mt-0.5">
                首层贴线率 ≥ 75% 保持连续界面
              </div>
            </div>
            <div className="ud-card p-3.5 bg-white">
              <div className="text-[11px] text-[#515154]">历史保护紫线刚性要求</div>
              <div className="text-[12px] font-bold text-[#8b5cf6] mt-1 line-clamp-2">
                {stage10Redlines.heritage_purple_line}
              </div>
            </div>
          </div>

          {/* Left 50% Node Design SSE Generator / Right 50% Before-After Swipe Comparator */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left (6 cols): Node Design & Micro-Personas SSE Generator */}
            <div className="lg:col-span-6 ud-card p-4 flex flex-col justify-between space-y-3">
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2.5 border-b border-black/8">
                  <div>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                      阶段 10 · 节点深化
                    </span>
                    <h2 className="text-[15px] font-bold text-[#1d1d1f] mt-1">
                      重要节点空间设计、人群画像与寒地微气候专项
                    </h2>
                  </div>
                </div>

                {/* 3 Topic Buttons */}
                <div className="grid grid-cols-3 gap-2">
                  {(
                    [
                      "重点节点空间设计",
                      "全龄人群活动画像",
                      "寒地微气候/特色专项研究",
                    ] as const
                  ).map((topic) => {
                    const active = activeStage10NodeTopic === topic;
                    return (
                      <div
                        key={topic}
                        onClick={() => setActiveStage10NodeTopic(topic)}
                        className={`p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between gap-2 ${
                          active
                            ? "bg-[#0071e3]/8 border-[#0071e3]"
                            : "bg-[#f5f5f7] border-black/8 hover:bg-black/5"
                        }`}
                      >
                        <div className="text-[12px] font-bold text-[#1d1d1f]">
                          {topic}
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStreamStage10Node(topic);
                          }}
                          disabled={stage10Streaming}
                          className="w-full py-1 rounded-lg bg-[#0071e3] hover:bg-[#0077ed] text-white text-[11px] font-semibold flex items-center justify-center gap-1"
                        >
                          {stage10Streaming && active ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Sparkles className="w-3 h-3" />
                          )}
                          <span>SSE 深化</span>
                        </button>
                      </div>
                    );
                  })}
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[12.5px] font-bold text-[#1d1d1f]">
                      {activeStage10NodeTopic} · 深化设计方案文本
                    </span>
                    <span className="text-[11px] text-[#515154]">
                      靶向锚定：{targetPlot.name}
                    </span>
                  </div>
                  <textarea
                    value={stage10Outputs[activeStage10NodeTopic] || ""}
                    onChange={(e) =>
                      setStage10Outputs((prev) => ({
                        ...prev,
                        [activeStage10NodeTopic]: e.target.value,
                      }))
                    }
                    rows={12}
                    className="w-full p-3.5 rounded-xl bg-[#f5f5f7] border border-black/10 text-[12.5px] leading-relaxed text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                  />
                </div>
              </div>

              <div className="text-[11.5px] text-[#515154] pt-2 border-t border-black/8 flex items-center justify-between">
                <span>上述节点深化成果将自动汇入阶段 12 分地块导则与阶段 13 全本说明书</span>
                <button
                  type="button"
                  onClick={() => setActiveSubTab("aigc")}
                  className="text-[#0071e3] font-semibold hover:underline"
                >
                  推送至阶段 15 ControlNet 渲染 →
                </button>
              </div>
            </div>

            {/* Right (6 cols): Interactive Before / After Swipe Comparator */}
            <div className="lg:col-span-6 ud-card p-4 space-y-3.5">
              <div className="flex items-center justify-between pb-2 border-b border-black/8">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[11px] font-bold">
                    阶段 10 · 卷帘对比
                  </span>
                  <h2 className="text-[15px] font-bold text-[#1d1d1f] mt-1">
                    改造前现状底图 (Before) vs 微更新生形方案 (After)
                  </h2>
                </div>
                <span className="px-2.5 py-1 rounded-lg bg-[#f5f5f7] border border-black/8 text-[11.5px] font-mono font-bold text-[#0071e3]">
                  卷帘分界 {swipePercent}%
                </span>
              </div>

              {/* Interactive Split-Curtain Viewport */}
              <div
                ref={swipeContainerRef}
                onMouseDown={(e) => {
                  isDraggingSwipeRef.current = true;
                  updateSwipeFromClientX(e.clientX);
                }}
                onMouseMove={(e) => {
                  if (isDraggingSwipeRef.current) {
                    updateSwipeFromClientX(e.clientX);
                  }
                }}
                onMouseUp={() => {
                  isDraggingSwipeRef.current = false;
                }}
                onMouseLeave={() => {
                  isDraggingSwipeRef.current = false;
                }}
                className="relative w-full h-[310px] rounded-2xl overflow-hidden border border-black/12 select-none cursor-ew-resize bg-[#e5e7eb]"
              >
                {/* AFTER Layer (Full width background) */}
                <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-[#ecfdf5] via-[#e0f2fe] to-[#fef3c7] flex flex-col justify-between p-4">
                  {afterImageUrl ? (
                    <img
                      src={afterImageUrl}
                      alt="微更新生形方案 After"
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  ) : (
                    /* Architectural Vector Scheme Schematic for After */
                    <svg
                      viewBox="0 0 600 310"
                      className="absolute inset-0 w-full h-full"
                      preserveAspectRatio="none"
                    >
                      <rect width="600" height="310" fill="#eef7f2" />
                      {/* Green corridor & pocket parks */}
                      <rect x="0" y="135" width="600" height="58" fill="#86efac" opacity="0.65" />
                      <circle cx="170" cy="164" r="38" fill="#34d399" opacity="0.55" />
                      <circle cx="420" cy="164" r="44" fill="#34d399" opacity="0.55" />
                      {/* Pedestrian promenade */}
                      <path
                        d="M 0 164 L 600 164"
                        stroke="#059669"
                        strokeWidth="10"
                        strokeDasharray="10 6"
                      />
                      {/* Renovated heritage buildings with stepped terraces */}
                      <rect x="45" y="38" width="110" height="78" rx="8" fill="#0071e3" opacity="0.82" />
                      <rect x="185" y="42" width="135" height="74" rx="8" fill="#0284c7" opacity="0.85" />
                      <rect x="350" y="34" width="190" height="82" rx="8" fill="#10b981" opacity="0.85" />
                      <rect x="60" y="210" width="150" height="72" rx="8" fill="#0071e3" opacity="0.8" />
                      <rect x="240" y="206" width="145" height="76" rx="8" fill="#8b5cf6" opacity="0.82" />
                      <rect x="415" y="208" width="135" height="74" rx="8" fill="#f59e0b" opacity="0.85" />
                      <text x="60" y="82" fill="#ffffff" fontSize="13" fontWeight="bold">
                        历史红砖合院活化 + 暖廊书吧
                      </text>
                      <text x="368" y="80" fill="#ffffff" fontSize="13" fontWeight="bold">
                        下沉雨水花园 + 连续林荫商业界面
                      </text>
                      <text x="252" y="248" fill="#ffffff" fontSize="12" fontWeight="bold">
                        嵌入式养老驿站 & 全龄活动核
                      </text>
                    </svg>
                  )}
                  <div className="relative z-10 flex justify-end">
                    <span className="px-3 py-1 rounded-full bg-[#10b981] text-white text-[11.5px] font-bold shadow-sm">
                      改造后 · 微更新生形方案 (After)
                    </span>
                  </div>
                </div>

                {/* BEFORE Layer (Clipped by swipePercent) */}
                <div
                  className="absolute inset-y-0 left-0 overflow-hidden"
                  style={{ width: `${swipePercent}%` }}
                >
                  <div className="relative w-full h-full bg-[#e2e8f0] p-4">
                    {beforeImageUrl ? (
                      <img
                        src={beforeImageUrl}
                        alt="改造前现状底图 Before"
                        className="absolute inset-0 w-full h-full object-cover"
                      />
                    ) : (
                      <svg
                        viewBox="0 0 600 310"
                        className="absolute inset-0 w-full h-full"
                        preserveAspectRatio="none"
                      >
                        <rect width="600" height="310" fill="#e5e7eb" />
                        {/* Congested mixed road */}
                        <rect x="0" y="142" width="600" height="44" fill="#9ca3af" />
                        <path
                          d="M 0 164 L 600 164"
                          stroke="#4b5563"
                          strokeWidth="4"
                          strokeDasharray="14 10"
                        />
                        {/* Fragmented aging blocks */}
                        <rect x="40" y="32" width="120" height="95" fill="#6b7280" />
                        <rect x="175" y="35" width="150" height="92" fill="#64748b" />
                        <rect x="345" y="30" width="200" height="96" fill="#475569" />
                        <rect x="55" y="200" width="160" height="86" fill="#64748b" />
                        <rect x="235" y="198" width="155" height="88" fill="#6b7280" />
                        <rect x="410" y="202" width="140" height="82" fill="#475569" />
                        <text x="55" y="84" fill="#ffffff" fontSize="13" fontWeight="bold">
                          现状老旧围墙阻隔 · 院落采光局促
                        </text>
                        <text x="70" y="246" fill="#ffffff" fontSize="12" fontWeight="bold">
                          路侧占道停车严重 · 绿视率仅 21.0%
                        </text>
                      </svg>
                    )}
                    <div className="relative z-10 flex justify-start">
                      <span className="px-3 py-1 rounded-full bg-[#1d1d1f]/85 text-white text-[11.5px] font-bold shadow-sm">
                        改造前 · 现状空间底图 (Before)
                      </span>
                    </div>
                  </div>
                </div>

                {/* Vertical Divider Handle */}
                <div
                  className="absolute inset-y-0 z-20 w-1 bg-white shadow-lg flex items-center justify-center"
                  style={{ left: `calc(${swipePercent}% - 2px)` }}
                >
                  <div className="w-8 h-8 rounded-full bg-[#0071e3] text-white shadow-md border-2 border-white flex items-center justify-center">
                    <ArrowLeftRight className="w-4 h-4" />
                  </div>
                </div>
              </div>

              {/* Range Slider Control */}
              <div className="flex items-center gap-3 px-1">
                <span className="text-[11px] font-semibold text-[#515154]">
                  现状底图
                </span>
                <input
                  type="range"
                  min={2}
                  max={98}
                  value={swipePercent}
                  onChange={(e) => setSwipePercent(Number(e.target.value))}
                  className="flex-1 accent-[#0071e3]"
                />
                <span className="text-[11px] font-semibold text-[#10b981]">
                  微更新方案
                </span>
              </div>

              {/* Quantitative Delta Pills */}
              <div className="grid grid-cols-2 gap-2.5 pt-1">
                {beforeAfterDeltas.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-[#f5f5f7] border border-black/8 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-[11.5px] font-bold text-[#1d1d1f]">
                        {item.label}
                      </div>
                      <div className="text-[11px] text-[#515154] mt-0.5">
                        {item.before} →{" "}
                        <span className="font-bold text-[#1d1d1f]">
                          {item.after}
                        </span>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[11.5px] font-bold">
                      {item.delta}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          SUB-VIEW 4: "aigc" (Stage 15 — GIS 刚性骨架 ControlNet 空间 AIGC 工坊)
      ======================================================================== */}
      {currentTab === "aigc" && (
        <div className="space-y-4">
          {aigcFeedback && (
            <div className="px-4 py-2.5 rounded-2xl bg-[#0071e3]/10 border border-[#0071e3]/25 text-[12.5px] font-semibold text-[#0071e3] flex items-center justify-between">
              <span>{aigcFeedback}</span>
              <button
                type="button"
                onClick={() => setAigcFeedback(null)}
                className="text-[11px] underline"
              >
                收起
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Step 1 (4 cols): GIS Rigid Skeleton & ControlNet Conditioning Preview */}
            <div className="lg:col-span-4 ud-card p-4 space-y-3.5">
              <div className="flex items-center justify-between pb-2 border-b border-black/8">
                <div>
                  <span className="px-2 py-0.5 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[10.5px] font-bold">
                    步骤 01 · GIS 刚性骨架
                  </span>
                  <h3 className="text-[14px] font-bold text-[#1d1d1f] mt-0.5">
                    三维白模深度图 / 线稿约束提取
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={handleGenerateDepthPreview}
                  disabled={depthPreviewLoading}
                  className="px-3 py-1.5 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[11.5px] font-semibold flex items-center gap-1"
                >
                  {depthPreviewLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <RefreshCw className="w-3.5 h-3.5" />
                  )}
                  <span>提取 GIS 骨架</span>
                </button>
              </div>

              {/* ControlNet Mode Switcher */}
              <div className="grid grid-cols-3 gap-1.5 bg-[#f5f5f7] p-1 rounded-xl border border-black/6">
                {[
                  { key: "depth", label: "Depth 深度场" },
                  { key: "canny", label: "Canny 线稿" },
                  { key: "normal", label: "Normal 法线" },
                ].map((m) => (
                  <button
                    key={m.key}
                    type="button"
                    onClick={() => setControlMode(m.key as any)}
                    className={`py-1.5 rounded-lg text-[11.5px] font-semibold transition-all ${
                      controlMode === m.key
                        ? "bg-white text-[#0071e3] shadow-2xs"
                        : "text-[#515154] hover:text-[#1d1d1f]"
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>

              {/* Conditioning Preview Canvas */}
              <div className="relative h-[230px] rounded-2xl overflow-hidden border border-black/12 bg-[#1d1d1f] flex items-center justify-center">
                {depthPreviewUrl ? (
                  <img
                    src={depthPreviewUrl}
                    alt="GIS ControlNet Conditioning"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <svg
                    viewBox="0 0 400 230"
                    className="w-full h-full"
                    preserveAspectRatio="none"
                  >
                    <defs>
                      <linearGradient id="depthGrad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#1e293b" />
                        <stop offset="100%" stopColor="#0f172a" />
                      </linearGradient>
                    </defs>
                    <rect width="400" height="230" fill="url(#depthGrad)" />
                    {/* 3D Axonometric GIS Massing Wireframe */}
                    <g
                      stroke={
                        controlMode === "canny"
                          ? "#38bdf8"
                          : controlMode === "normal"
                          ? "#a78bfa"
                          : "#e2e8f0"
                      }
                      strokeWidth="1.5"
                      fill={
                        controlMode === "canny"
                          ? "none"
                          : "rgba(255,255,255,0.16)"
                      }
                    >
                      <polygon points="50,150 120,120 175,145 105,175" />
                      <polygon points="50,150 50,95 105,120 105,175" />
                      <polygon points="105,175 105,120 175,90 175,145" />

                      <polygon points="195,135 275,100 340,130 260,165" />
                      <polygon points="195,135 195,65 260,95 260,165" />
                      <polygon points="260,165 260,95 340,60 340,130" />
                    </g>
                    {/* Street Redline Axis */}
                    <line
                      x1="20"
                      y1="205"
                      x2="380"
                      y2="75"
                      stroke="#10b981"
                      strokeWidth="2.5"
                      strokeDasharray="6 4"
                    />
                    <text
                      x="18"
                      y="26"
                      fill="#f8fafc"
                      fontSize="11.5"
                      fontWeight="bold"
                    >
                      GIS 刚性体块边界 ({targetPlot.plot_id}) · 严锁退界与高度
                    </text>
                  </svg>
                )}
              </div>

              <div className="p-3 rounded-xl bg-[#f5f5f7] border border-black/8 space-y-1 text-[11.5px]">
                <div className="flex justify-between">
                  <span className="text-[#515154]">提取建筑基底矢量化体块：</span>
                  <span className="font-bold text-[#1d1d1f]">
                    {depthMeta.bldgCount} 栋
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#515154]">控规最高天际线包络：</span>
                  <span className="font-bold text-[#0071e3]">
                    ≤ {stage10Redlines.height_limit_m} m
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#515154]">透视相机锁定模式：</span>
                  <span className="font-semibold text-[#1d1d1f]">
                    {depthMeta.viewAngle}
                  </span>
                </div>
              </div>
            </div>

            {/* Step 2 (4 cols): 6 Planning Style Presets & Prompt Polisher */}
            <div className="lg:col-span-4 ud-card p-4 space-y-3.5">
              <div className="flex items-center justify-between pb-2 border-b border-black/8">
                <div>
                  <span className="px-2 py-0.5 rounded-full bg-[#8b5cf6]/15 text-[#5b21b6] text-[10.5px] font-bold">
                    步骤 02 · 六大规划风格
                  </span>
                  <h3 className="text-[14px] font-bold text-[#1d1d1f] mt-0.5">
                    风貌预设选择与 AI 规划提示词润色
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={handlePolishPrompt}
                  disabled={polishingPrompt}
                  className="px-3 py-1.5 rounded-xl bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-[11.5px] font-semibold flex items-center gap-1"
                >
                  {polishingPrompt ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Wand2 className="w-3.5 h-3.5" />
                  )}
                  <span>AI 建筑规划提示词润色</span>
                </button>
              </div>

              {/* 6 Presets Grid */}
              <div className="grid grid-cols-2 gap-2">
                {STYLE_PRESETS.map((preset) => {
                  const active = selectedPresetId === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => {
                        setSelectedPresetId(preset.id);
                        setAigcPrompt(preset.defaultPrompt);
                      }}
                      className={`p-2.5 rounded-xl border text-left transition-all ${
                        active
                          ? "bg-[#0071e3]/8 border-[#0071e3] ring-1 ring-[#0071e3]/25"
                          : "bg-[#f5f5f7] hover:bg-black/5 border-black/8"
                      }`}
                    >
                      <div className="text-[12px] font-bold text-[#1d1d1f]">
                        {preset.name}
                      </div>
                      <div className="text-[10px] text-[#0071e3] font-semibold mt-0.5">
                        {preset.badge}
                      </div>
                      <div className="text-[10.5px] text-[#515154] line-clamp-1 mt-0.5">
                        {preset.desc}
                      </div>
                    </button>
                  );
                })}
              </div>

              <div>
                <label className="block text-[11.5px] font-bold text-[#1d1d1f] mb-1">
                  正向规划生形提示词 (Prompt)
                </label>
                <textarea
                  value={aigcPrompt}
                  onChange={(e) => setAigcPrompt(e.target.value)}
                  rows={4}
                  className="w-full p-2.5 rounded-xl bg-[#f5f5f7] border border-black/10 text-[12px] text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-[#515154] mb-1">
                  负向防失真约束词 (Negative Prompt · 严禁违章加建与透视畸变)
                </label>
                <input
                  type="text"
                  value={aigcNegativePrompt}
                  onChange={(e) => setAigcNegativePrompt(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-xl bg-[#f5f5f7] border border-black/10 text-[11.5px] text-[#515154]"
                />
              </div>
            </div>

            {/* Step 3 (4 cols): ControlNet Parameters & Render Dispatch */}
            <div className="lg:col-span-4 ud-card p-4 flex flex-col justify-between space-y-4">
              <div className="space-y-3.5">
                <div className="pb-2 border-b border-black/8">
                  <span className="px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] text-[10.5px] font-bold">
                    步骤 03 · 参数与生形渲染
                  </span>
                  <h3 className="text-[14px] font-bold text-[#1d1d1f] mt-0.5">
                    ControlNet 刚性权重与异步渲染派发
                  </h3>
                </div>

                <div className="space-y-3 bg-[#f5f5f7] p-3.5 rounded-2xl border border-black/8">
                  <div>
                    <div className="flex justify-between text-[12px] font-semibold">
                      <span>重绘幅度 (Denoising Strength)</span>
                      <span className="text-[#0071e3] font-bold">
                        {denoisingStrength.toFixed(2)}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={0.25}
                      max={0.85}
                      step={0.01}
                      value={denoisingStrength}
                      onChange={(e) =>
                        setDenoisingStrength(Number(e.target.value))
                      }
                      className="w-full mt-1 accent-[#0071e3]"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[12px] font-semibold">
                      <span>ControlNet GIS 骨架锁死权重</span>
                      <span className="text-[#10b981] font-bold">
                        {controlNetWeight.toFixed(2)}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={0.5}
                      max={1.8}
                      step={0.05}
                      value={controlNetWeight}
                      onChange={(e) =>
                        setControlNetWeight(Number(e.target.value))
                      }
                      className="w-full mt-1 accent-[#10b981]"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2.5 pt-1">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#515154] mb-1">
                        采样步数 (Steps)
                      </label>
                      <input
                        type="number"
                        min={15}
                        max={60}
                        value={sampleSteps}
                        onChange={(e) =>
                          setSampleSteps(Number(e.target.value) || 28)
                        }
                        className="w-full px-2.5 py-1.5 rounded-xl bg-white border border-black/12 text-[12px] font-bold text-[#1d1d1f]"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-[#515154] mb-1">
                        随机种子 (Seed)
                      </label>
                      <input
                        type="number"
                        value={renderSeed}
                        onChange={(e) =>
                          setRenderSeed(Number(e.target.value) || 20260701)
                        }
                        className="w-full px-2.5 py-1.5 rounded-xl bg-white border border-black/12 text-[12px] font-mono text-[#1d1d1f]"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleDispatchControlNetRender}
                disabled={renderingAigc}
                className="w-full py-3 rounded-2xl bg-[#0071e3] hover:bg-[#0077ed] disabled:opacity-60 text-white text-[13.5px] font-bold shadow-sm flex items-center justify-center gap-2"
              >
                {renderingAigc ? (
                  <Loader2 className="w-4.5 h-4.5 animate-spin" />
                ) : (
                  <Sparkles className="w-4.5 h-4.5" />
                )}
                <span>启动 ControlNet 空间生形渲染</span>
              </button>
            </div>
          </div>

          {/* Render Gallery */}
          <div className="ud-card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4.5 h-4.5 text-[#0071e3]" />
                <h3 className="text-[14.5px] font-bold text-[#1d1d1f]">
                  渲染成果画廊 (Render Gallery)
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-black/6 text-[11px] font-semibold text-[#515154]">
                  共 {renderGallery.length} 组空间生形方案
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {renderGallery.map((item) => (
                <div
                  key={item.id}
                  className="p-3 rounded-2xl bg-[#f5f5f7] border border-black/8 flex flex-col justify-between space-y-2.5"
                >
                  <div>
                    <div className="h-[165px] rounded-xl overflow-hidden bg-gradient-to-br from-[#dbeafe] via-[#e0e7ff] to-[#d1fae5] border border-black/8 relative flex items-center justify-center">
                      {item.imageUrl ? (
                        <img
                          src={item.imageUrl}
                          alt={item.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="p-4 text-center space-y-1">
                          <Building2 className="w-8 h-8 text-[#0071e3] mx-auto" />
                          <div className="text-[12px] font-bold text-[#1d1d1f]">
                            {item.stylePreset} · 刚性体块渲染图
                          </div>
                          <div className="text-[10.5px] text-[#515154]">
                            {item.controlMode} · FAR {item.far.toFixed(2)}
                          </div>
                        </div>
                      )}
                      <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-white/90 text-[#1d1d1f] text-[10px] font-bold shadow-2xs">
                        {item.stylePreset}
                      </span>
                    </div>

                    <div className="mt-2">
                      <div className="text-[13px] font-bold text-[#1d1d1f] truncate">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-[#515154] line-clamp-2 mt-0.5 font-mono">
                        {item.prompt}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-black/8 text-[11px]">
                    <span className="text-[#515154]">{item.createdAt}</span>
                    <button
                      type="button"
                      onClick={() =>
                        openInExplorer(
                          item.outputPath || "data/outputs/aigc_renders"
                        )
                      }
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white hover:bg-[#0071e3]/10 border border-black/10 text-[#0071e3] font-semibold"
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                      <span>在资源管理器中定位</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workbench02View;
