import { create } from "zustand";
import { apiGet, apiPost } from "../services/apiClient";
import type {
  BackgroundJob,
  EngineStatusHud,
  FusedPlot,
  GeoJsonFeatureCollection,
  MpiResult,
  ProjectInfo,
  SpatialSyntaxSummary,
  StageMetadata,
  StudioRoute,
  StudioSubTab,
} from "../types/api";

export const STAGE_MATRIX: StageMetadata[] = [
  {
    code: "00",
    name: "基地双轨接入与红线建库",
    phase: "第一篇 · 资料建库与空间底板",
    route: "wb1",
    subTab: "assets",
    description: "原生矢量/SHP/DXF拖入直读、OSM在线抓取与示范工程恢复",
  },
  {
    code: "01",
    name: "16大类规划资料资产盘点",
    phase: "第一篇 · 资料建库与空间底板",
    route: "wb1",
    subTab: "assets",
    description: "控规、地形、建筑、路网、POI、街景等16大类资料完备度核验",
  },
  {
    code: "02",
    name: "全局WGS-84空间拓扑质检",
    phase: "第一篇 · 资料建库与空间底板",
    route: "wb1",
    subTab: "assets",
    description: "坐标系一致性、自相交几何修复与属性字段完整性自动化体检",
  },
  {
    code: "03",
    name: "多源文档MarkItDown语义萃取",
    phase: "第一篇 · 资料建库与空间底板",
    route: "wb1",
    subTab: "assets",
    description: "上位规划文本、调研纪要与政策文件结构化语义抽取入库",
  },
  {
    code: "04",
    name: "全路网空间句法与多维体检",
    phase: "第二篇 · 全息空间诊断与靶向锁定",
    route: "wb1",
    subTab: "diagnosis",
    description: "rustworkx全路网多半径整合度/穿行度计算与文化/产业/人口专项诊断",
  },
  {
    code: "05",
    name: "AHP-MPI评估与靶向地块锁定",
    phase: "第二篇 · 全息空间诊断与靶向锁定",
    route: "wb1",
    subTab: "diagnosis",
    description: "DuckDB多源指标融合、AHP权重实时推演、3D联动雷达与靶向地块锁定",
  },
  {
    code: "06",
    name: "更新目标定位与标杆案例对标",
    phase: "第三篇 · 多主体博弈与空间设计",
    route: "wb2",
    subTab: "strategy",
    description: "靶向片区总体愿景定位、国内外更新标杆案例对标与核心策略推导",
  },
  {
    code: "07",
    name: "三主体三轮博弈与策略矩阵",
    phase: "第三篇 · 多主体博弈与空间设计",
    route: "wb2",
    subTab: "strategy",
    description: "政府/居民/开发商三轮SSE协商、混合RAG法条锚定与问题-目标-策略矩阵",
  },
  {
    code: "08",
    name: "总体空间结构与用地平衡沙盘",
    phase: "第三篇 · 多主体博弈与空间设计",
    route: "wb2",
    subTab: "master-plan",
    description: "轴线/节点/风貌分区结构生成与商业/居住/绿地/公服用地比例实时核算",
  },
  {
    code: "09",
    name: "四大专项系统与产业业态策划",
    phase: "第三篇 · 多主体博弈与空间设计",
    route: "wb3",
    subTab: "systems",
    description: "综合交通、公共空间、建筑形态、风貌景观四大系统与产业业态植入",
  },
  {
    code: "10",
    name: "重点地段深化与改造前后对比",
    phase: "第三篇 · 多主体博弈与空间设计",
    route: "wb2",
    subTab: "detail",
    description: "锁定地块控规红线画像、人群微更新场景与Before/After卷帘对比",
  },
  {
    code: "11",
    name: "拆改留分期实施与时序甘特图",
    phase: "第四篇 · 法定导则与工程交付",
    route: "wb3",
    subTab: "timing",
    description: "留改拆分类施策台账、近期/中期/远期建设时序与资金平衡甘特图",
  },
  {
    code: "12",
    name: "九章节法定城市设计导则编制",
    phase: "第四篇 · 法定导则与工程交付",
    route: "wb3",
    subTab: "guideline",
    description: "通则+分地块刚性管控图则9章节两步式生成与法定Word导则导出",
  },
  {
    code: "13",
    name: "A3标准图册、DXF与全本报告",
    phase: "第四篇 · 法定导则与工程交付",
    route: "wb3",
    subTab: "delivery",
    description: "专业规划图纸渲染、A3图册拼装、AutoCAD 2000 DXF与全本Word报告编译",
  },
  {
    code: "14",
    name: "sc-datav全域空间态势大屏",
    phase: "第二篇 · 全息空间诊断与靶向锁定",
    route: "wb1",
    subTab: "datav",
    description: "全量真实融合指标数字大屏、3D天际线沙盘与独立副屏答辩投影",
  },
  {
    code: "15",
    name: "GIS刚性骨架ControlNet空间AIGC",
    phase: "第三篇 · 多主体博弈与空间设计",
    route: "wb2",
    subTab: "aigc",
    description: "GIS三维体块深度图约束、六大规划风格润色与SD ControlNet建筑渲染",
  },
  {
    code: "16",
    name: "Skill规范手册与多主体听证会",
    phase: "第四篇 · 法定导则与工程交付",
    route: "wb3",
    subTab: "skills",
    description: "智能体专业规划规范检视、A3规范速览图合成与公众听证会推演模拟",
  },
];

const ROUTE_DEFAULT_SUBTAB: Record<StudioRoute, StudioSubTab> = {
  home: "diagnosis",
  wb1: "diagnosis",
  wb2: "strategy",
  wb3: "delivery",
  "datav-popout": "datav",
};

export interface StudioStoreState {
  activeRoute: StudioRoute;
  activeSubTab: StudioSubTab;
  activeStageCode: string;
  activeProjectId: string;
  projects: ProjectInfo[];
  enginesHud: EngineStatusHud | null;
  fusedPlots: FusedPlot[];
  fusedPlotsGeojson: GeoJsonFeatureCollection | null;
  boundaryGeojson: GeoJsonFeatureCollection | null;
  selectedPlotId: string | null;
  lockedTargetPlot: FusedPlot | null;
  mpiResult: MpiResult | null;
  spatialSyntaxSummary: SpatialSyntaxSummary | null;
  stageBus: Record<string, any>;
  jobs: BackgroundJob[];
  copilotOpen: boolean;
  settingsOpen: boolean;
  loading: boolean;

  setActiveRoute: (route: StudioRoute, subTab?: StudioSubTab) => void;
  setActiveSubTab: (subTab: StudioSubTab) => void;
  navigateToStage: (stageCode: string) => void;
  setSelectedPlotId: (plotId: string | null) => void;
  setMpiResult: (result: MpiResult | null) => void;
  setSpatialSyntaxSummary: (summary: SpatialSyntaxSummary | null) => void;
  setCopilotOpen: (open: boolean) => void;
  setSettingsOpen: (open: boolean) => void;
  refreshSystemHud: () => Promise<void>;
  refreshFusedPlots: () => Promise<void>;
  switchProject: (projectId: string) => Promise<void>;
  createProject: (payload: {
    id?: string;
    name: string;
    city?: string;
    description?: string;
  }) => Promise<void>;
  lockTargetPlot: (plotOrId: FusedPlot | string) => Promise<void>;
  refreshJobs: () => Promise<void>;
}

export const useStudioStore = create<StudioStoreState>((set, get) => ({
  activeRoute: "home",
  activeSubTab: "diagnosis",
  activeStageCode: "05",
  activeProjectId: "changchun_default",
  projects: [
    {
      id: "changchun_default",
      name: "长春市历史文化街区与中心片区城市更新示范工程",
      city: "长春市",
      is_default: true,
    },
  ],
  enginesHud: null,
  fusedPlots: [],
  fusedPlotsGeojson: null,
  boundaryGeojson: null,
  selectedPlotId: null,
  lockedTargetPlot: null,
  mpiResult: null,
  spatialSyntaxSummary: null,
  stageBus: {},
  jobs: [],
  copilotOpen: false,
  settingsOpen: false,
  loading: false,

  setActiveRoute: (route, subTab) => {
    const resolvedSubTab = subTab || ROUTE_DEFAULT_SUBTAB[route] || get().activeSubTab;
    const matchingStage = STAGE_MATRIX.find(
      (s) => s.route === route && s.subTab === resolvedSubTab
    );
    set({
      activeRoute: route,
      activeSubTab: resolvedSubTab,
      ...(matchingStage ? { activeStageCode: matchingStage.code } : {}),
    });
  },

  setActiveSubTab: (subTab) => {
    const currentRoute = get().activeRoute;
    const matchingStage = STAGE_MATRIX.find(
      (s) => s.route === currentRoute && s.subTab === subTab
    );
    set({
      activeSubTab: subTab,
      ...(matchingStage ? { activeStageCode: matchingStage.code } : {}),
    });
  },

  navigateToStage: (stageCode) => {
    const normalized = stageCode.replace(/^stage[_-]?/i, "").padStart(2, "0");
    const target = STAGE_MATRIX.find((s) => s.code === normalized);
    if (!target) {
      return;
    }
    set({
      activeRoute: target.route,
      activeSubTab: target.subTab,
      activeStageCode: target.code,
    });
  },

  setSelectedPlotId: (plotId) => {
    set({ selectedPlotId: plotId });
  },

  setMpiResult: (result) => {
    set((state) => {
      if (!result || !Array.isArray(result.ranking)) {
        return { mpiResult: result };
      }
      const scoreById = new Map<string, { score?: number; tier?: string; rank?: number }>();
      result.ranking.forEach((item, idx) => {
        if (item?.plot_id) {
          scoreById.set(String(item.plot_id), {
            score: item.mpi_score,
            tier: item.priority_tier,
            rank: item.rank ?? idx + 1,
          });
        }
      });

      const updatedPlots = state.fusedPlots.map((p) => {
        const hit = scoreById.get(String(p.plot_id));
        if (!hit) return p;
        return {
          ...p,
          mpi_score: hit.score ?? p.mpi_score,
          priority_tier: hit.tier ?? p.priority_tier,
          rank: hit.rank ?? p.rank,
        };
      });

      return {
        mpiResult: result,
        fusedPlots: updatedPlots,
      };
    });
  },

  setSpatialSyntaxSummary: (summary) => {
    set({ spatialSyntaxSummary: summary });
  },

  setCopilotOpen: (open) => {
    set({ copilotOpen: open });
  },

  setSettingsOpen: (open) => {
    set({ settingsOpen: open });
  },

  refreshSystemHud: async () => {
    try {
      const [enginesRes, projectsRes] = await Promise.allSettled([
        apiGet<any>("/api/v1/system/engines"),
        apiGet<any>("/api/v1/system/projects"),
      ]);

      const updates: Partial<StudioStoreState> = {};

      if (enginesRes.status === "fulfilled" && enginesRes.value) {
        const hud = enginesRes.value as EngineStatusHud;
        updates.enginesHud = hud;
        if (hud.active_project_id) {
          updates.activeProjectId = hud.active_project_id;
        }
        if (hud.stage_bus && typeof hud.stage_bus === "object") {
          updates.stageBus = hud.stage_bus;
        }
      }

      if (projectsRes.status === "fulfilled" && projectsRes.value) {
        const pData = projectsRes.value;
        const list: ProjectInfo[] = Array.isArray(pData)
          ? pData
          : Array.isArray(pData.projects)
          ? pData.projects
          : [];
        if (list.length > 0) {
          updates.projects = list.map((item) => ({
            ...item,
            id: item.id || item.project_id || "changchun_default",
          }));
        }
        if (pData.active_project_id) {
          updates.activeProjectId = pData.active_project_id;
        }
        if (pData.stage_bus && typeof pData.stage_bus === "object") {
          updates.stageBus = { ...(updates.stageBus || {}), ...pData.stage_bus };
        }
      }

      set(updates);
    } catch (_err) {
      // Keep existing state if backend is still warming up
    }
  },

  refreshFusedPlots: async () => {
    set({ loading: true });
    try {
      const [plotsRes, syntaxRes] = await Promise.allSettled([
        apiGet<any>("/api/v1/diagnosis/fused-plots"),
        apiGet<any>("/api/v1/diagnosis/spatial-syntax/summary"),
      ]);

      const updates: Partial<StudioStoreState> = { loading: false };

      if (plotsRes.status === "fulfilled" && plotsRes.value) {
        const payload = plotsRes.value;
        const plots: FusedPlot[] = Array.isArray(payload.plots)
          ? payload.plots
          : Array.isArray(payload.items)
          ? payload.items
          : Array.isArray(payload)
          ? payload
          : [];

        updates.fusedPlots = plots;

        if (payload.geojson && payload.geojson.type === "FeatureCollection") {
          updates.fusedPlotsGeojson = payload.geojson;
        } else if (payload.plots_geojson && payload.plots_geojson.type === "FeatureCollection") {
          updates.fusedPlotsGeojson = payload.plots_geojson;
        }

        if (payload.boundary_geojson && payload.boundary_geojson.type === "FeatureCollection") {
          updates.boundaryGeojson = payload.boundary_geojson;
        }

        if (payload.target_plot && typeof payload.target_plot === "object") {
          updates.lockedTargetPlot = payload.target_plot;
        } else if (payload.locked_plot_id) {
          const found = plots.find(
            (p) => String(p.plot_id) === String(payload.locked_plot_id)
          );
          if (found) updates.lockedTargetPlot = found;
        }

        const currentSelected = get().selectedPlotId;
        if (!currentSelected && plots.length > 0) {
          updates.selectedPlotId =
            updates.lockedTargetPlot?.plot_id || plots[0].plot_id;
        }

        if (payload.stage_bus && typeof payload.stage_bus === "object") {
          updates.stageBus = { ...get().stageBus, ...payload.stage_bus };
        }
      }

      if (syntaxRes.status === "fulfilled" && syntaxRes.value) {
        updates.spatialSyntaxSummary = syntaxRes.value;
      }

      set(updates);
    } catch (_err) {
      set({ loading: false });
    }
  },

  switchProject: async (projectId) => {
    if (!projectId) return;
    set({ loading: true });
    try {
      await apiPost("/api/v1/system/projects", {
        action: "switch",
        project_id: projectId,
        id: projectId,
      });
      set({
        activeProjectId: projectId,
        selectedPlotId: null,
        lockedTargetPlot: null,
      });
      await Promise.all([get().refreshSystemHud(), get().refreshFusedPlots()]);
    } catch (_err) {
      set({ activeProjectId: projectId, loading: false });
    }
  },

  createProject: async (payload) => {
    set({ loading: true });
    try {
      const res = await apiPost<any>("/api/v1/system/projects", {
        action: "create",
        ...payload,
      });
      const newId =
        res?.active_project_id || res?.project?.id || res?.project_id || payload.id;
      if (newId) {
        set({ activeProjectId: newId });
      }
      await Promise.all([get().refreshSystemHud(), get().refreshFusedPlots()]);
    } finally {
      set({ loading: false });
    }
  },

  lockTargetPlot: async (plotOrId) => {
    const state = get();
    const plotObj: FusedPlot | undefined =
      typeof plotOrId === "string"
        ? state.fusedPlots.find((p) => String(p.plot_id) === String(plotOrId))
        : plotOrId;

    const plotId =
      typeof plotOrId === "string" ? plotOrId : plotOrId?.plot_id || "";
    if (!plotId) return;

    try {
      const res = await apiPost<any>("/api/v1/diagnosis/target-plot", {
        plot_id: plotId,
        plot: plotObj || { plot_id: plotId },
      });
      const locked = res?.target_plot || plotObj || {
        plot_id: plotId,
        name: plotId,
        area_m2: 0,
        bldg_count: 0,
        bcr: 0,
        far: 0,
        avg_floor: 0,
        poi_density: 0,
        gvi_mean: 0,
        svf_mean: 0,
        syntax_int_mean: 0,
      };
      set({
        lockedTargetPlot: locked,
        selectedPlotId: plotId,
        stageBus: {
          ...state.stageBus,
          "05": { completed: true, target_plot_id: plotId, target_plot_name: locked.name },
          target_plot: locked,
        },
      });
    } catch (_err) {
      if (plotObj) {
        set({
          lockedTargetPlot: plotObj,
          selectedPlotId: plotId,
        });
      }
    }
  },

  refreshJobs: async () => {
    try {
      const res = await apiGet<any>("/api/v1/system/jobs");
      const list: BackgroundJob[] = Array.isArray(res)
        ? res
        : Array.isArray(res?.jobs)
        ? res.jobs
        : [];
      set({ jobs: list });
    } catch (_err) {
      // ignore polling error
    }
  },
}));
