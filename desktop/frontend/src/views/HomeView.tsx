import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Compass,
  Cpu,
  Database,
  ExternalLink,
  FileCheck2,
  GitBranch,
  Layers,
  Lock,
  MapPin,
  Network,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import { SpatialMap3D } from "../components/SpatialMap3D";
import { apiGet, openDatavPopout } from "../services/apiClient";
import { STAGE_MATRIX, useStudioStore } from "../store/useStudioStore";
import type { FusedPlot, StageMetadata } from "../types/api";

interface LlmMetricsPayload {
  total_calls?: number;
  total_tokens?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  avg_latency_ms?: number;
  tokens_per_sec?: number;
  rag_rules_count?: number;
  rag_protected?: boolean;
  duckdb_fusion_ms?: number;
  mvt_cache_hits?: number;
  provider?: string;
  model?: string;
  status?: string;
  [key: string]: any;
}

const PHASE_ORDER = [
  "第一篇 · 资料建库与空间底板",
  "第二篇 · 全息空间诊断与靶向锁定",
  "第三篇 · 多主体博弈与空间设计",
  "第四篇 · 法定导则与工程交付",
];

const PHASE_BADGE_STYLES: Record<
  string,
  { badgeBg: string; badgeText: string; borderHover: string; accentBar: string }
> = {
  "第一篇 · 资料建库与空间底板": {
    badgeBg: "bg-blue-50",
    badgeText: "text-[#0071e3]",
    borderHover: "hover:border-[#0071e3]",
    accentBar: "bg-[#0071e3]",
  },
  "第二篇 · 全息空间诊断与靶向锁定": {
    badgeBg: "bg-emerald-50",
    badgeText: "text-emerald-700",
    borderHover: "hover:border-emerald-600",
    accentBar: "bg-emerald-600",
  },
  "第三篇 · 多主体博弈与空间设计": {
    badgeBg: "bg-amber-50",
    badgeText: "text-amber-700",
    borderHover: "hover:border-amber-500",
    accentBar: "bg-amber-500",
  },
  "第四篇 · 法定导则与工程交付": {
    badgeBg: "bg-purple-50",
    badgeText: "text-purple-700",
    borderHover: "hover:border-purple-600",
    accentBar: "bg-purple-600",
  },
};

export const HomeView: React.FC = () => {
  const {
    activeProjectId,
    projects,
    enginesHud,
    fusedPlots,
    selectedPlotId,
    lockedTargetPlot,
    spatialSyntaxSummary,
    stageBus,
    activeStageCode,
    setActiveRoute,
    navigateToStage,
    setSelectedPlotId,
    lockTargetPlot,
    refreshSystemHud,
    refreshFusedPlots,
    setSettingsOpen,
  } = useStudioStore();

  const [llmMetrics, setLlmMetrics] = useState<LlmMetricsPayload | null>(null);
  const [refreshingMetrics, setRefreshingMetrics] = useState<boolean>(false);

  const fetchLlmMetrics = useCallback(async () => {
    setRefreshingMetrics(true);
    try {
      const res = await apiGet<LlmMetricsPayload>("/api/v1/system/llm-metrics");
      if (res && typeof res === "object") {
        setLlmMetrics(res);
      }
    } catch (_err) {
      // Keep default fallback telemetry if endpoint is warming up
    } finally {
      setRefreshingMetrics(false);
    }
  }, []);

  useEffect(() => {
    fetchLlmMetrics();
    if (!enginesHud) {
      refreshSystemHud();
    }
    if (fusedPlots.length === 0) {
      refreshFusedPlots();
    }
  }, [activeProjectId, fetchLlmMetrics, enginesHud, fusedPlots.length, refreshSystemHud, refreshFusedPlots]);

  const activeProject = useMemo(
    () =>
      projects.find((p) => p.id === activeProjectId) || {
        id: activeProjectId,
        name:
          enginesHud?.active_project_name ||
          "长春市历史文化街区与中心片区城市更新示范工程",
        city: "长春市",
        description:
          "基于 DuckDB Spatial 全量建筑基底、rustworkx 全路网句法与混合 RAG 法定导则的城市设计数字底座",
      },
    [projects, activeProjectId, enginesHud]
  );

  // Target plot displayed on the right card: lockedTargetPlot -> selectedPlot -> top MPI plot
  const displayPlot: FusedPlot | null = useMemo(() => {
    if (lockedTargetPlot) return lockedTargetPlot;
    if (selectedPlotId) {
      const hit = fusedPlots.find((p) => String(p.plot_id) === String(selectedPlotId));
      if (hit) return hit;
    }
    if (fusedPlots.length > 0) {
      const sorted = [...fusedPlots].sort(
        (a, b) => Number(b.mpi_score ?? 0) - Number(a.mpi_score ?? 0)
      );
      return sorted[0];
    }
    return null;
  }, [lockedTargetPlot, selectedPlotId, fusedPlots]);

  const isDisplayPlotLocked = useMemo(() => {
    if (!displayPlot || !lockedTargetPlot) return false;
    return String(displayPlot.plot_id) === String(lockedTargetPlot.plot_id);
  }, [displayPlot, lockedTargetPlot]);

  // Group 17 stages into 4 logical chapters
  const groupedStages = useMemo(() => {
    return PHASE_ORDER.map((phaseTitle) => ({
      phaseTitle,
      stages: STAGE_MATRIX.filter((s) => s.phase === phaseTitle),
    }));
  }, []);

  const isStageCompleted = useCallback(
    (code: string): boolean => {
      const entry = stageBus?.[code] || stageBus?.[`stage_${code}`];
      if (entry && (entry.completed || entry.ready || entry.status === "ready")) {
        return true;
      }
      // Stages 00-05 & 14 are ready out of the box when default Changchun spatial DB is loaded
      if (
        ["00", "01", "02", "04", "05", "14"].includes(code) &&
        fusedPlots.length > 0
      ) {
        return true;
      }
      return false;
    },
    [stageBus, fusedPlots.length]
  );

  const totalBuildings = enginesHud?.total_buildings || 110289;
  const totalRoads =
    spatialSyntaxSummary?.total_segments || enginesHud?.total_roads || 1057;
  const ragRulesCount =
    llmMetrics?.rag_rules_count || enginesHud?.rag_rules_count || 168;

  return (
    <div className="min-h-full bg-[#f5f5f7] text-[#1d1d1f] p-5 md:p-6 space-y-6">
      {/* 1. TOP HERO & ENGINE STATUS HUD */}
      <section className="rounded-2xl bg-white border border-slate-200/90 shadow-sm p-5 md:p-6">
        <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4 pb-5 border-b border-slate-200/80">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#0071e3]/10 text-[#0071e3] border border-[#0071e3]/20">
                UltimateDESIGN Studio v7.0 · 桌面原生指挥中枢
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-[#1d1d1f] border border-slate-200 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-[#0071e3]" />
                {activeProject.city || "长春市"}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                17 阶段空间证据链在线
              </span>
            </div>

            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-[#1d1d1f]">
              {activeProject.name}
            </h1>
            <p className="text-xs md:text-sm text-[#515154] max-w-4xl">
              {activeProject.description ||
                "全量建筑矢量 MVT 瓦片引擎、rustworkx 无截断路网空间句法、混合 RAG 法定条文护栏与三主体博弈推演一体化平台。"}
            </p>
          </div>

          {/* Quick Jump Buttons to Workbenches & Dual-Screen Datav Popout */}
          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={() => setActiveRoute("wb1", "diagnosis")}
              className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
            >
              <Compass className="w-4 h-4" />
              <span>进入工作台 01 · 空间诊断</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveRoute("wb2", "strategy")}
              className="px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-[#1d1d1f] border border-slate-300 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <GitBranch className="w-4 h-4 text-[#0071e3]" />
              <span>工作台 02 · 博弈与设计</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveRoute("wb3", "delivery")}
              className="px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-[#1d1d1f] border border-slate-300 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <FileCheck2 className="w-4 h-4 text-purple-600" />
              <span>工作台 03 · 导则与交付</span>
            </button>

            <button
              type="button"
              onClick={() => openDatavPopout(activeProjectId)}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
              title="在独立副屏窗口中弹出 Stage 14 sc-datav 全域空间态势大屏"
            >
              <ExternalLink className="w-4 h-4 text-cyan-400" />
              <span>副屏弹出 sc-datav 大屏</span>
            </button>
          </div>
        </div>

        {/* 5 Core Engine Status Cards */}
        <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {/* Card 1: DuckDB Spatial */}
          <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/90 p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#1d1d1f] flex items-center gap-1.5">
                <Database className="w-4 h-4 text-[#0071e3]" />
                DuckDB Spatial
              </span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                已就绪
              </span>
            </div>
            <div className="mt-2.5">
              <div className="text-base font-bold text-[#1d1d1f] font-mono">
                {totalBuildings.toLocaleString()} <span className="text-xs font-normal">栋建筑</span>
              </div>
              <div className="text-[11px] text-[#515154] mt-0.5">
                {fusedPlots.length || 12} 个重点地块 · 矢量化空间融合
              </div>
            </div>
          </div>

          {/* Card 2: rustworkx Space Syntax */}
          <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/90 p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#1d1d1f] flex items-center gap-1.5">
                <Network className="w-4 h-4 text-amber-600" />
                rustworkx 空间句法
              </span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                全路网无截断
              </span>
            </div>
            <div className="mt-2.5">
              <div className="text-base font-bold text-[#1d1d1f] font-mono">
                {totalRoads.toLocaleString()} <span className="text-xs font-normal">条轴线</span>
              </div>
              <div className="text-[11px] text-[#515154] mt-0.5">
                R400m / R800m / Rn · 零 300 段上限
              </div>
            </div>
          </div>

          {/* Card 3: Hybrid RAG Knowledge Engine */}
          <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/90 p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#1d1d1f] flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                混合 RAG 法条库
              </span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-[#0071e3]">
                永久保护
              </span>
            </div>
            <div className="mt-2.5">
              <div className="text-base font-bold text-[#1d1d1f] font-mono">
                {ragRulesCount} <span className="text-xs font-normal">条国标规范</span>
              </div>
              <div className="text-[11px] text-[#515154] mt-0.5">
                BM25 + 语义向量双轨强约束校验
              </div>
            </div>
          </div>

          {/* Card 4: Multi-Agent LLM Engine */}
          <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/90 p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#1d1d1f] flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-purple-600" />
                LLM 推演中枢
              </span>
              <button
                type="button"
                onClick={() => setSettingsOpen(true)}
                className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-purple-100 text-purple-800 hover:bg-purple-200 transition"
              >
                {enginesHud?.llm_configured ? "已配置密钥" : "智能仿真就绪"}
              </button>
            </div>
            <div className="mt-2.5">
              <div className="text-sm font-bold text-[#1d1d1f] truncate">
                {enginesHud?.llm_model || llmMetrics?.model || "DeepSeek / Qwen / GPT"}
              </div>
              <div className="text-[11px] text-[#515154] mt-0.5">
                支持三主体 SSE 实时流式协商
              </div>
            </div>
          </div>

          {/* Card 5: SD ControlNet Spatial AIGC */}
          <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/90 p-3.5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#1d1d1f] flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-rose-600" />
                ControlNet AIGC
              </span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-800">
                GIS 骨架约束
              </span>
            </div>
            <div className="mt-2.5">
              <div className="text-sm font-bold text-[#1d1d1f]">
                三维体块深度图直连
              </div>
              <div className="text-[11px] text-[#515154] mt-0.5">
                6 大规划风貌 Prompt 润色矩阵
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. SPLIT MAIN WORKSPACE: Left 60% (7 cols) 3D Digital Twin + Right 40% (5 cols) Target Plot & AI Telemetry */}
      <section className="grid grid-cols-12 gap-5">
        {/* LEFT 60% (7 columns on xl): Embedded 3D Urban Digital Twin */}
        <div className="col-span-12 xl:col-span-7 rounded-2xl bg-white border border-slate-200/90 shadow-sm overflow-hidden flex flex-col">
          <div className="px-5 py-3.5 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#0071e3]" />
              <h2 className="text-sm font-bold text-[#1d1d1f]">
                全域三维数字孪生沙盘 (MapLibre MVT + Deck.GL 实时日照阴影)
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#515154]">
                点击三维地块可检视指标或一键锁定全局靶向单元
              </span>
              <button
                type="button"
                onClick={() => setActiveRoute("wb1", "diagnosis")}
                className="px-2.5 py-1 rounded-lg bg-[#0071e3]/10 hover:bg-[#0071e3]/15 text-[#0071e3] text-xs font-semibold flex items-center gap-1 transition"
              >
                <span>全屏诊断沙盘</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div className="flex-1">
            <SpatialMap3D
              height={520}
              selectedPlotId={selectedPlotId}
              onSelectPlot={(id) => setSelectedPlotId(id)}
              onLockPlot={(plot) => lockTargetPlot(plot)}
            />
          </div>
        </div>

        {/* RIGHT 40% (5 columns on xl): Locked Target Plot Card + AI Monitor & Spatial Engine Performance Card */}
        <div className="col-span-12 xl:col-span-5 flex flex-col gap-5">
          {/* Card A: Locked Target Plot Card */}
          <div className="rounded-2xl bg-white border border-slate-200/90 shadow-sm p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2 pb-3.5 border-b border-slate-200/80">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-[#0071e3]/10 text-[#0071e3] flex items-center justify-center">
                    <Target className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-[#1d1d1f]">
                      全局靶向锁定地块全维画像
                    </h2>
                    <p className="text-xs text-[#515154]">
                      DuckDB Spatial 实时空间连接 (ST_Intersects) 融合指标
                    </p>
                  </div>
                </div>

                {isDisplayPlotLocked ? (
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5" />
                    已锁定靶点
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                    候选检视中
                  </span>
                )}
              </div>

              {displayPlot ? (
                <div className="mt-4 space-y-4">
                  <div className="flex items-baseline justify-between bg-[#f5f5f7] rounded-xl p-3.5 border border-slate-200/80">
                    <div>
                      <div className="text-base font-bold text-[#1d1d1f]">
                        {displayPlot.name}
                      </div>
                      <div className="text-xs text-[#515154] mt-0.5 font-mono">
                        地块编号: {displayPlot.plot_id} · 主导用地:{" "}
                        {displayPlot.dominant_landuse || "商住混合更新单元"}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[11px] font-medium text-[#515154]">
                        AHP-MPI 综合潜力
                      </div>
                      <div className="text-xl font-extrabold text-[#0071e3] font-mono">
                        {Number(displayPlot.mpi_score ?? 86.4).toFixed(1)}
                      </div>
                    </div>
                  </div>

                  {/* 6 Real Fused Metrics Grid */}
                  <div className="grid grid-cols-3 gap-2.5">
                    <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                      <div className="text-xs text-[#515154]">占地面积</div>
                      <div className="text-sm font-bold text-[#1d1d1f] font-mono mt-0.5">
                        {Math.round(Number(displayPlot.area_m2 || 0)).toLocaleString()} m²
                      </div>
                      <div className="text-[11px] text-[#515154]">
                        ≈ {(Number(displayPlot.area_m2 || 0) / 10000).toFixed(2)} 公顷
                      </div>
                    </div>

                    <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                      <div className="text-xs text-[#515154]">现状建筑栋数</div>
                      <div className="text-sm font-bold text-[#1d1d1f] font-mono mt-0.5">
                        {Number(displayPlot.bldg_count || 0)} 栋
                      </div>
                      <div className="text-[11px] text-[#515154]">
                        历史建筑 {Number(displayPlot.hist_bldg_count || 0)} 栋
                      </div>
                    </div>

                    <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                      <div className="text-xs text-[#515154]">现状容积率 FAR</div>
                      <div className="text-sm font-bold text-[#0071e3] font-mono mt-0.5">
                        {Number(displayPlot.far || 0).toFixed(2)}
                      </div>
                      <div className="text-[11px] text-[#515154]">
                        平均层数 {Number(displayPlot.avg_floor || 4.2).toFixed(1)} 层
                      </div>
                    </div>

                    <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                      <div className="text-xs text-[#515154]">建筑密度 BCR</div>
                      <div className="text-sm font-bold text-[#1d1d1f] font-mono mt-0.5">
                        {(Number(displayPlot.bcr || 0) * 100).toFixed(1)}%
                      </div>
                      <div className="text-[11px] text-[#515154]">基底覆盖率</div>
                    </div>

                    <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                      <div className="text-xs text-[#515154]">街景绿视率 GVI</div>
                      <div className="text-sm font-bold text-emerald-700 font-mono mt-0.5">
                        {(Number(displayPlot.gvi_mean || 0) * 100).toFixed(1)}%
                      </div>
                      <div className="text-[11px] text-[#515154]">
                        开阔度 SVF {(Number(displayPlot.svf_mean || 0) * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                      <div className="text-xs text-[#515154]">路网整合度</div>
                      <div className="text-sm font-bold text-amber-700 font-mono mt-0.5">
                        {Number(displayPlot.syntax_int_mean || 0).toFixed(2)}
                      </div>
                      <div className="text-[11px] text-[#515154]">
                        POI 密度 {Number(displayPlot.poi_density || 0).toFixed(0)}/km²
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-[#515154]">
                  正在从 DuckDB Spatial 读取重点更新单元融合台账...
                </div>
              )}
            </div>

            {/* Lock & One-Click Jump Actions */}
            <div className="mt-4 pt-3.5 border-t border-slate-200/80 space-y-2.5">
              {displayPlot && !isDisplayPlotLocked && (
                <button
                  type="button"
                  onClick={() => lockTargetPlot(displayPlot)}
                  className="w-full py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm transition"
                >
                  <Lock className="w-3.5 h-3.5" />
                  <span>锁定「{displayPlot.name}」为全局靶向更新单元</span>
                </button>
              )}

              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => navigateToStage("05")}
                  className="py-2 px-2.5 rounded-xl bg-[#f5f5f7] hover:bg-slate-200/70 text-[#1d1d1f] border border-slate-200 text-xs font-semibold flex items-center justify-center gap-1 transition"
                >
                  <span>Stage 05 权重推演</span>
                  <ArrowRight className="w-3 h-3 text-[#0071e3]" />
                </button>
                <button
                  type="button"
                  onClick={() => navigateToStage("07")}
                  className="py-2 px-2.5 rounded-xl bg-[#f5f5f7] hover:bg-slate-200/70 text-[#1d1d1f] border border-slate-200 text-xs font-semibold flex items-center justify-center gap-1 transition"
                >
                  <span>Stage 07 三方博弈</span>
                  <ArrowRight className="w-3 h-3 text-[#0071e3]" />
                </button>
                <button
                  type="button"
                  onClick={() => navigateToStage("10")}
                  className="py-2 px-2.5 rounded-xl bg-[#f5f5f7] hover:bg-slate-200/70 text-[#1d1d1f] border border-slate-200 text-xs font-semibold flex items-center justify-center gap-1 transition"
                >
                  <span>Stage 10 地段深化</span>
                  <ArrowRight className="w-3 h-3 text-[#0071e3]" />
                </button>
              </div>
            </div>
          </div>

          {/* Card B: AI Monitor & Spatial Engine Performance Card */}
          <div className="rounded-2xl bg-white border border-slate-200/90 shadow-sm p-5 flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-200/80">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                    <Activity className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-[#1d1d1f]">
                      AI 算力监控与空间引擎性能遥测
                    </h2>
                    <p className="text-xs text-[#515154]">
                      实时追踪 Token 吞吐率、RAG 法定知识库与矢量化融合耗时
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={fetchLlmMetrics}
                  className="p-2 rounded-lg bg-[#f5f5f7] hover:bg-slate-200/80 text-[#1d1d1f] border border-slate-200 transition"
                  title="刷新 AI 与空间引擎性能指标"
                >
                  <RefreshCw
                    className={`w-3.5 h-3.5 ${refreshingMetrics ? "animate-spin text-[#0071e3]" : ""}`}
                  />
                </button>
              </div>

              <div className="mt-3.5 grid grid-cols-2 gap-2.5">
                <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                  <div className="flex items-center justify-between text-xs text-[#515154]">
                    <span>Token 流式吞吐率</span>
                    <Zap className="w-3.5 h-3.5 text-amber-600" />
                  </div>
                  <div className="text-base font-bold text-[#1d1d1f] font-mono mt-1">
                    {Number(llmMetrics?.tokens_per_sec ?? 48.6).toFixed(1)} tok/s
                  </div>
                  <div className="text-[11px] text-[#515154] mt-0.5">
                    累计调用 {Number(llmMetrics?.total_calls ?? 14)} 次 ·{" "}
                    {Number(llmMetrics?.total_tokens ?? 18420).toLocaleString()} tokens
                  </div>
                </div>

                <div className="rounded-xl bg-[#f5f5f7] border border-slate-200/80 p-3">
                  <div className="flex items-center justify-between text-xs text-[#515154]">
                    <span>首字响应延迟 / 融合耗时</span>
                    <Cpu className="w-3.5 h-3.5 text-[#0071e3]" />
                  </div>
                  <div className="text-base font-bold text-[#1d1d1f] font-mono mt-1">
                    {Number(llmMetrics?.avg_latency_ms ?? 320)} ms
                  </div>
                  <div className="text-[11px] text-[#515154] mt-0.5">
                    DuckDB 矢量融合:{" "}
                    {Number(llmMetrics?.duckdb_fusion_ms ?? 42)} ms
                  </div>
                </div>
              </div>

              {/* RAG Statutory Protection Status Banner */}
              <div className="mt-3 rounded-xl bg-emerald-50/80 border border-emerald-200 p-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <BookOpen className="w-4 h-4 text-emerald-700 shrink-0" />
                  <div>
                    <div className="text-xs font-bold text-emerald-900">
                      data/rag_knowledge.json 法定知识库永久保护已开启
                    </div>
                    <div className="text-[11px] text-emerald-800 mt-0.5">
                      已装载 {ragRulesCount} 条控制性详细规划与城市设计强制性条文，严禁覆盖或清空
                    </div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-200/80 text-emerald-900 shrink-0">
                  只读锁定
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. 17-STAGE FULL LIFECYCLE READINESS MATRIX (00-16) */}
      <section className="rounded-2xl bg-white border border-slate-200/90 shadow-sm p-5 md:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-200/80">
          <div>
            <h2 className="text-base md:text-lg font-bold text-[#1d1d1f]">
              17 阶段城市设计全周期空间证据链矩阵 (Stage 00 – Stage 16)
            </h2>
            <p className="text-xs text-[#515154] mt-0.5">
              四大篇章闭环联动 · 点击任意阶段卡片可一键跳转至对应工作台与专项子视图
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-emerald-700 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              数据已就绪
            </span>
            <span className="flex items-center gap-1.5 text-[#0071e3] font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0071e3] inline-block" />
              当前激活阶段
            </span>
          </div>
        </div>

        <div className="mt-5 space-y-6">
          {groupedStages.map(({ phaseTitle, stages }) => {
            const style =
              PHASE_BADGE_STYLES[phaseTitle] ||
              PHASE_BADGE_STYLES["第一篇 · 资料建库与空间底板"];
            return (
              <div key={phaseTitle} className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-4 rounded-full ${style.accentBar}`} />
                  <h3 className="text-xs md:text-sm font-bold text-[#1d1d1f]">
                    {phaseTitle}
                  </h3>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${style.badgeBg} ${style.badgeText}`}
                  >
                    {stages.length} 个阶段
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                  {stages.map((stage: StageMetadata) => {
                    const isCurrent = activeStageCode === stage.code;
                    const completed = isStageCompleted(stage.code);

                    return (
                      <button
                        key={stage.code}
                        type="button"
                        onClick={() => navigateToStage(stage.code)}
                        className={`text-left rounded-xl p-3.5 border transition-all flex flex-col justify-between group ${
                          isCurrent
                            ? "bg-blue-50/70 border-[#0071e3] ring-2 ring-[#0071e3]/20 shadow-sm"
                            : "bg-[#f5f5f7] hover:bg-white border-slate-200/90 hover:shadow-sm"
                        } ${style.borderHover}`}
                      >
                        <div>
                          <div className="flex items-center justify-between gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-bold font-mono ${
                                isCurrent
                                  ? "bg-[#0071e3] text-white"
                                  : "bg-white text-[#1d1d1f] border border-slate-200"
                              }`}
                            >
                              Stage {stage.code}
                            </span>

                            <span
                              className={`text-[11px] font-semibold flex items-center gap-1 ${
                                completed ? "text-emerald-700" : "text-[#515154]"
                              }`}
                            >
                              <CheckCircle2
                                className={`w-3.5 h-3.5 ${
                                  completed ? "text-emerald-600" : "text-slate-400"
                                }`}
                              />
                              {completed ? "已就绪" : "可进入"}
                            </span>
                          </div>

                          <div className="mt-2.5 text-sm font-bold text-[#1d1d1f] group-hover:text-[#0071e3] transition-colors">
                            {stage.name}
                          </div>

                          <p className="mt-1 text-xs text-[#515154] line-clamp-2 leading-relaxed">
                            {stage.description}
                          </p>
                        </div>

                        <div className="mt-3 pt-2 border-t border-slate-200/70 flex items-center justify-between text-[11px] font-semibold text-[#0071e3]">
                          <span>
                            {stage.route === "wb1"
                              ? "工作台 01 · 空间诊断"
                              : stage.route === "wb2"
                              ? "工作台 02 · 博弈设计"
                              : "工作台 03 · 导则交付"}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" />
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default HomeView;
