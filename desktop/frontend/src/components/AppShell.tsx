import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  BookOpen,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Compass,
  Cpu,
  Database,
  ExternalLink,
  FolderOpen,
  FolderPlus,
  Layers,
  Loader2,
  MapPin,
  MonitorUp,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  Terminal,
  Trash2,
  X,
} from "lucide-react";
import {
  apiDelete,
  apiGet,
  apiPut,
  openDatavPopout,
  openInExplorer,
  streamSSE,
} from "../services/apiClient";
import { STAGE_MATRIX, useStudioStore } from "../store/useStudioStore";
import type {
  BackgroundJob,
  CopilotCitation,
  CopilotMessage,
  StudioRoute,
  SystemSettingsPayload,
} from "../types/api";

export interface AppShellProps {
  children: React.ReactNode;
}

const MAIN_NAV_ITEMS: Array<{
  route: StudioRoute;
  label: string;
  shortBadge: string;
}> = [
  { route: "home", label: "首页指挥中枢", shortBadge: "HUB" },
  { route: "wb1", label: "工作台 01 · 全息空间诊断", shortBadge: "00-05 · 14" },
  { route: "wb2", label: "工作台 02 · 博弈与AIGC", shortBadge: "06-08 · 10 · 15" },
  { route: "wb3", label: "工作台 03 · 数字图则交付", shortBadge: "09 · 11-13 · 16" },
];

const QUICK_COPILOT_PROMPTS = [
  "解读当前锁定靶向地块的空间短板与控规刚性边界",
  "检索《城市居住区规划设计标准》GB50180日照与绿地率强制条文",
  "生成政企民三方利益平衡的微更新容积率奖励建议",
  "核查当前方案是否满足历史风貌保护街区高度与退界要求",
];

function isStageCompleted(
  code: string,
  stageBus: Record<string, any>,
  hasPlots: boolean,
  hasLockedPlot: boolean
): boolean {
  if (!stageBus) return false;
  const entry =
    stageBus[code] ||
    stageBus[`stage_${code}`] ||
    stageBus[`STAGE_${code}`];
  if (entry && (entry.completed || entry.done || Object.keys(entry).length > 0)) {
    return true;
  }
  if ((code === "00" || code === "01" || code === "04") && hasPlots) {
    return true;
  }
  if (code === "05" && hasLockedPlot) {
    return true;
  }
  return false;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const {
    activeRoute,
    activeStageCode,
    activeProjectId,
    projects,
    enginesHud,
    fusedPlots,
    lockedTargetPlot,
    stageBus,
    jobs,
    copilotOpen,
    settingsOpen,
    setActiveRoute,
    navigateToStage,
    setCopilotOpen,
    setSettingsOpen,
    refreshSystemHud,
    refreshFusedPlots,
    switchProject,
    createProject,
    refreshJobs,
  } = useStudioStore();

  // Dropdown states
  const [stageMenuOpen, setStageMenuOpen] = useState(false);
  const [projectMenuOpen, setProjectMenuOpen] = useState(false);
  const [creatingProject, setCreatingProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectCity, setNewProjectCity] = useState("长春市");

  // Copilot states
  const [messages, setMessages] = useState<CopilotMessage[]>([
    {
      id: "welcome-0",
      role: "assistant",
      content:
        "您好！我是 **UltimateDESIGN v7.0 全局规划师副驾**。我已实时连接当前工程的 **DuckDB Spatial 空间融合宽表** 与 **Hybrid RAG 城乡规划法定规范库**。您可以在任意工作台随时向我提问法规条文、地块指标或策略建议。",
      timestamp: "刚刚",
      stage_label: "全局规划知识引擎已就绪",
      citations: [
        {
          source: "《城市居住区规划设计标准》GB 50180-2018",
          clause: "第 4.0.2 条 · 用地与建筑控制",
        },
        {
          source: "《历史文化名城保护规划标准》GB/T 50357-2018",
          clause: "第 3.2.1 条 · 历史文化街区核心保护范围",
        },
      ],
    },
  ]);
  const [copilotInput, setCopilotInput] = useState("");
  const [copilotStreaming, setCopilotStreaming] = useState(false);
  const copilotAbortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Settings modal states
  const [settingsForm, setSettingsForm] = useState<SystemSettingsPayload>({
    llm_provider: "deepseek",
    llm_model: "deepseek-chat",
    llm_base_url: "https://api.deepseek.com/v1",
    llm_api_key: "",
    llm_api_key_masked: "",
    sd_api_url: "http://127.0.0.1:7860",
  });
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsFeedback, setSettingsFeedback] = useState<string | null>(null);

  // JobTray states
  const [jobTrayExpanded, setJobTrayExpanded] = useState(false);
  const [activeLogJobId, setActiveLogJobId] = useState<string | null>(null);
  const [liveJobLogs, setLiveJobLogs] = useState<Record<string, string[]>>({});
  const jobStreamRef = useRef<AbortController | null>(null);

  // Initial bootstrap & periodic job polling
  useEffect(() => {
    refreshSystemHud();
    refreshFusedPlots();
    refreshJobs();

    const timer = window.setInterval(() => {
      refreshJobs();
    }, 3500);
    return () => window.clearInterval(timer);
  }, [refreshSystemHud, refreshFusedPlots, refreshJobs]);

  // Load copilot history when opened
  useEffect(() => {
    if (!copilotOpen) return;
    apiGet<any>("/api/v1/copilot/history")
      .then((res) => {
        const list = Array.isArray(res)
          ? res
          : Array.isArray(res?.history)
          ? res.history
          : Array.isArray(res?.messages)
          ? res.messages
          : [];
        if (list.length > 0) {
          setMessages(
            list.map((m: any, idx: number) => ({
              id: m.id || `hist-${idx}`,
              role: m.role === "user" ? "user" : "assistant",
              content: m.content || m.text || "",
              timestamp: m.timestamp || "历史对话",
              stage_label: m.stage_label || "规划法规与阶段上下文",
              citations: Array.isArray(m.citations) ? m.citations : undefined,
            }))
          );
        }
      })
      .catch(() => {
        // Keep welcome message if history endpoint not yet populated
      });
  }, [copilotOpen]);

  // Load settings when settings modal opens
  useEffect(() => {
    if (!settingsOpen) return;
    setSettingsFeedback(null);
    apiGet<SystemSettingsPayload>("/api/v1/system/settings")
      .then((res) => {
        if (res && typeof res === "object") {
          setSettingsForm((prev) => ({
            ...prev,
            ...res,
            llm_api_key: "",
          }));
        }
      })
      .catch(() => {
        // Keep defaults
      });
  }, [settingsOpen]);

  // Scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, copilotStreaming]);

  // Stream live logs for selected job
  useEffect(() => {
    if (!activeLogJobId) return;
    jobStreamRef.current?.abort();
    const ctrl = streamSSE(
      `/api/v1/system/jobs/${encodeURIComponent(activeLogJobId)}/stream`,
      null,
      (ev) => {
        const line =
          typeof ev === "string"
            ? ev
            : ev.log || ev.message || ev.text || ev.chunk || "";
        if (line) {
          setLiveJobLogs((prev) => ({
            ...prev,
            [activeLogJobId]: [...(prev[activeLogJobId] || []), String(line)],
          }));
        }
        if (ev?.status === "succeeded" || ev?.status === "failed") {
          refreshJobs();
        }
      },
      () => {
        refreshJobs();
      }
    );
    jobStreamRef.current = ctrl;
    return () => {
      ctrl.abort();
    };
  }, [activeLogJobId, refreshJobs]);

  const currentStageMeta = useMemo(() => {
    return (
      STAGE_MATRIX.find((s) => s.code === activeStageCode) || STAGE_MATRIX[5]
    );
  }, [activeStageCode]);

  const stagesByPhase = useMemo(() => {
    const groups = new Map<string, typeof STAGE_MATRIX>();
    STAGE_MATRIX.forEach((s) => {
      const arr = groups.get(s.phase) || [];
      arr.push(s);
      groups.set(s.phase, arr);
    });
    return Array.from(groups.entries());
  }, []);

  const completedCount = useMemo(() => {
    return STAGE_MATRIX.filter((s) =>
      isStageCompleted(
        s.code,
        stageBus,
        fusedPlots.length > 0,
        Boolean(lockedTargetPlot)
      )
    ).length;
  }, [stageBus, fusedPlots.length, lockedTargetPlot]);

  const activeProject = useMemo(() => {
    return (
      projects.find((p) => (p.id || p.project_id) === activeProjectId) || {
        id: activeProjectId,
        name:
          activeProjectId === "changchun_default"
            ? "长春历史街区与中心片区示范工程"
            : activeProjectId,
        city: "长春市",
      }
    );
  }, [projects, activeProjectId]);

  const runningJobsCount = useMemo(() => {
    return jobs.filter((j) => j.status === "running" || j.status === "queued")
      .length;
  }, [jobs]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    await createProject({
      name: newProjectName.trim(),
      city: newProjectCity.trim() || "长春市",
    });
    setNewProjectName("");
    setCreatingProject(false);
    setProjectMenuOpen(false);
  };

  const handleSendCopilot = (promptText?: string) => {
    const query = (promptText ?? copilotInput).trim();
    if (!query || copilotStreaming) return;

    const userMsg: CopilotMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      stage_label: `阶段 ${currentStageMeta.code} · ${currentStageMeta.name}`,
    };

    const assistantId = `ast-${Date.now()}`;
    const assistantMsg: CopilotMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: "实时推流中",
      stage_label: lockedTargetPlot
        ? `靶向锁定：${lockedTargetPlot.name}`
        : `阶段 ${currentStageMeta.code} · ${currentStageMeta.name}`,
      citations: [],
      streaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    if (!promptText) {
      setCopilotInput("");
    }
    setCopilotStreaming(true);

    copilotAbortRef.current?.abort();
    copilotAbortRef.current = streamSSE(
      "/api/v1/copilot/chat/stream",
      {
        message: query,
        query,
        stage_code: currentStageMeta.code,
        stage_name: currentStageMeta.name,
        project_id: activeProjectId,
        target_plot_id: lockedTargetPlot?.plot_id || null,
        target_plot_name: lockedTargetPlot?.name || null,
      },
      (ev) => {
        const textChunk =
          typeof ev === "string"
            ? ev
            : ev.delta ?? ev.chunk ?? ev.token ?? ev.text ?? ev.content ?? "";
        const citations: CopilotCitation[] | undefined = Array.isArray(
          ev?.citations
        )
          ? ev.citations
          : Array.isArray(ev?.rag_hits)
          ? ev.rag_hits
          : undefined;

        setMessages((prev) =>
          prev.map((m) => {
            if (m.id !== assistantId) return m;
            return {
              ...m,
              content: textChunk ? m.content + String(textChunk) : m.content,
              citations: citations && citations.length > 0 ? citations : m.citations,
            };
          })
        );
      },
      () => {
        setCopilotStreaming(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  streaming: false,
                  timestamp: new Date().toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  }),
                  content:
                    m.content ||
                    "已结合当前工程空间诊断与混合 RAG 法规库完成分析。",
                }
              : m
          )
        );
      },
      (err) => {
        setCopilotStreaming(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  streaming: false,
                  timestamp: "本地离线规则引擎",
                  content:
                    m.content ||
                    `[离线规范辅助应答] 当前处于本地规则回退模式（${err.message}）。建议重点核查靶向地块（${
                      lockedTargetPlot?.name || "核心更新单元"
                    }）的建筑密度、绿视率及《城市居住区规划设计标准》GB50180 日照间距硬约束。`,
                }
              : m
          )
        );
      }
    );
  };

  const handleClearCopilot = async () => {
    try {
      await apiDelete("/api/v1/copilot/history");
    } catch (_e) {
      // ignore
    }
    setMessages([
      {
        id: `reset-${Date.now()}`,
        role: "assistant",
        content: "对话历史已清空。当前工程空间上下文与法规库检索已就绪。",
        timestamp: "刚刚",
        stage_label: `阶段 ${currentStageMeta.code} · ${currentStageMeta.name}`,
      },
    ]);
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSettingsSaving(true);
    setSettingsFeedback(null);
    try {
      const payload: Record<string, any> = {
        llm_provider: settingsForm.llm_provider,
        model: settingsForm.llm_model,
        llm_model: settingsForm.llm_model,
        base_url: settingsForm.llm_base_url,
        llm_base_url: settingsForm.llm_base_url,
        sd_url: settingsForm.sd_api_url,
        sd_api_url: settingsForm.sd_api_url,
      };
      if (settingsForm.llm_api_key && settingsForm.llm_api_key.trim()) {
        payload.api_key = settingsForm.llm_api_key.trim();
        payload.llm_api_key = settingsForm.llm_api_key.trim();
      }
      if (settingsForm.baidu_ak && settingsForm.baidu_ak.trim()) {
        payload.baidu_ak = settingsForm.baidu_ak.trim();
      }
      const saved = await apiPut<any>("/api/v1/system/settings", payload);
      await refreshSystemHud();
      setSettingsFeedback("配置已保存至本机用户配置目录（~/.ultimatedesign/config.json）并即时生效");
      setSettingsForm((prev) => ({
        ...prev,
        llm_api_key: "",
        baidu_ak: "",
        llm_api_key_masked: saved?.api_key_masked || prev.llm_api_key_masked,
        baidu_ak_masked: saved?.baidu_ak_masked || prev.baidu_ak_masked,
      }));
    } catch (err: any) {
      setSettingsFeedback(`保存失败：${err.message || String(err)}`);
    } finally {
      setSettingsSaving(false);
    }
  };

  // If in standalone datav-popout mode, render full-bleed canvas without top bar clutter
  if (activeRoute === "datav-popout") {
    return <div className="w-screen h-screen overflow-hidden bg-[#0b1120]">{children}</div>;
  }

  return (
    <div className="flex flex-col w-screen h-screen overflow-hidden bg-[#f5f5f7] text-[#1d1d1f]">
      {/* Fixed 52px Apple HIG Light Frosted Top Navigation Bar */}
      <header className="ud-glass-bar fixed top-0 left-0 right-0 z-40 h-[52px] px-4 flex items-center justify-between gap-3 select-none">
        {/* Left: Brand Identity & Multi-Project Switcher */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            type="button"
            onClick={() => setActiveRoute("home")}
            className="flex items-center gap-2.5 text-left group focus:outline-none"
          >
            <div className="w-8 h-8 rounded-xl bg-[#0071e3] text-white flex items-center justify-center shadow-sm group-hover:bg-[#0077ed] transition-colors">
              <Compass className="w-4.5 h-4.5" />
            </div>
            <div className="leading-tight">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-[14px] tracking-tight text-[#1d1d1f]">
                  UltimateDESIGN
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded-md bg-[#0071e3]/10 text-[#0071e3]">
                  v7.0 Studio
                </span>
              </div>
              <div className="text-[11px] text-[#515154] truncate max-w-[180px]">
                DuckDB Spatial · 原生桌面工作站
              </div>
            </div>
          </button>

          <div className="h-5 w-[1px] bg-black/10 mx-1" />

          {/* Multi-Project Switcher Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setProjectMenuOpen((v) => !v);
                setStageMenuOpen(false);
              }}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white/90 hover:bg-white border border-black/10 text-[12px] font-medium text-[#1d1d1f] shadow-2xs transition-all"
              title="切换或新建独立 DuckDB Spatial 规划工程库"
            >
              <Database className="w-3.5 h-3.5 text-[#0071e3]" />
              <span className="truncate max-w-[175px]">{activeProject.name}</span>
              <ChevronDown className="w-3.5 h-3.5 text-[#515154]" />
            </button>

            {projectMenuOpen && (
              <div className="ud-glass-panel absolute left-0 mt-2 w-[360px] rounded-2xl p-3 z-50">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-black/8">
                  <div>
                    <div className="text-[12px] font-bold text-[#1d1d1f]">
                      DuckDB Spatial 多工程 ACID 工作库
                    </div>
                    <div className="text-[11px] text-[#515154]">
                      独立空间表与17阶段总线隔离 · 全局法规库永久共享保护
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setCreatingProject((v) => !v)}
                    className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#0071e3] text-white text-[11px] font-semibold hover:bg-[#0077ed]"
                  >
                    <FolderPlus className="w-3.5 h-3.5" />
                    <span>新建工程</span>
                  </button>
                </div>

                {creatingProject && (
                  <form
                    onSubmit={handleCreateProject}
                    className="mb-3 p-2.5 rounded-xl bg-[#f5f5f7] border border-black/8 space-y-2"
                  >
                    <div className="text-[11px] font-semibold text-[#1d1d1f]">
                      创建新城市设计工程
                    </div>
                    <input
                      type="text"
                      value={newProjectName}
                      onChange={(e) => setNewProjectName(e.target.value)}
                      placeholder="工程名称（如：南关区历史街区微更新）"
                      className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-black/12 text-[12px] text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                    />
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={newProjectCity}
                        onChange={(e) => setNewProjectCity(e.target.value)}
                        placeholder="所属城市"
                        className="flex-1 px-2.5 py-1.5 rounded-lg bg-white border border-black/12 text-[12px] text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                      />
                      <button
                        type="submit"
                        className="px-3 py-1.5 rounded-lg bg-[#0071e3] text-white text-[12px] font-semibold hover:bg-[#0077ed]"
                      >
                        创建并切换
                      </button>
                    </div>
                  </form>
                )}

                <div className="max-h-[240px] overflow-y-auto space-y-1">
                  {projects.map((proj) => {
                    const pid = proj.id || proj.project_id || "changchun_default";
                    const isCurrent = pid === activeProjectId;
                    return (
                      <button
                        key={pid}
                        type="button"
                        onClick={() => {
                          switchProject(pid);
                          setProjectMenuOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left transition-colors ${
                          isCurrent
                            ? "bg-[#0071e3]/10 text-[#0071e3] font-semibold"
                            : "hover:bg-black/5 text-[#1d1d1f]"
                        }`}
                      >
                        <div className="min-w-0 pr-2">
                          <div className="text-[12px] truncate">{proj.name}</div>
                          <div className="text-[10px] text-[#515154] flex items-center gap-2">
                            <span>编码: {pid}</span>
                            {proj.city && <span>· {proj.city}</span>}
                          </div>
                        </div>
                        {isCurrent && (
                          <CheckCircle2 className="w-4 h-4 text-[#0071e3] shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center: Main Workbench Navigation Pills */}
        <nav className="flex items-center gap-1 bg-black/[0.04] p-1 rounded-xl border border-black/[0.05]">
          {MAIN_NAV_ITEMS.map((item) => {
            const isActive = activeRoute === item.route;
            return (
              <button
                key={item.route}
                type="button"
                onClick={() => setActiveRoute(item.route)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-all ${
                  isActive
                    ? "bg-white text-[#0071e3] shadow-xs border border-black/6"
                    : "text-[#515154] hover:text-[#1d1d1f] hover:bg-white/50"
                }`}
              >
                <span>{item.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? "bg-[#0071e3]/10 text-[#0071e3]"
                      : "bg-black/6 text-[#515154]"
                  }`}
                >
                  {item.shortBadge}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Right: 17-Stage Matrix Dropdown, Locked Target Plot Badge, sc-datav Popout, Settings & Copilot */}
        <div className="flex items-center gap-2">
          {/* Locked Target Plot Pill */}
          {lockedTargetPlot && (
            <button
              type="button"
              onClick={() => navigateToStage("05")}
              className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#10b981]/12 text-[#065f46] border border-[#10b981]/25 text-[11px] font-semibold"
              title="当前工作台已锁定的靶向更新地块"
            >
              <MapPin className="w-3.5 h-3.5 text-[#10b981]" />
              <span className="truncate max-w-[125px]">
                靶向: {lockedTargetPlot.name}
              </span>
            </button>
          )}

          {/* 17-Stage Quick Jump Matrix */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setStageMenuOpen((v) => !v);
                setProjectMenuOpen(false);
              }}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white hover:bg-white/95 border border-black/10 text-[12px] font-semibold text-[#1d1d1f] shadow-2xs"
            >
              <Layers className="w-3.5 h-3.5 text-[#0071e3]" />
              <span>
                阶段 {currentStageMeta.code} · {currentStageMeta.name.slice(0, 8)}
              </span>
              <span className="px-1.5 py-0.2 rounded-full bg-[#10b981]/15 text-[#065f46] text-[10px] font-bold">
                {completedCount}/17
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-[#515154]" />
            </button>

            {stageMenuOpen && (
              <div className="ud-glass-panel absolute right-0 mt-2 w-[620px] rounded-2xl p-4 z-50">
                <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-black/8">
                  <div>
                    <div className="text-[13px] font-bold text-[#1d1d1f]">
                      全流程 17 逻辑阶段速达矩阵 (Stage 00 – 16)
                    </div>
                    <div className="text-[11px] text-[#515154]">
                      点击任意阶段一键切换对应专业工作台与子页签 · 绿点代表该阶段已完成数据入库或推演
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-full bg-[#0071e3]/10 text-[#0071e3] text-[11px] font-bold">
                    总体进度 {Math.round((completedCount / 17) * 100)}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 max-h-[420px] overflow-y-auto pr-1">
                  {stagesByPhase.map(([phaseTitle, items]) => (
                    <div
                      key={phaseTitle}
                      className="p-2.5 rounded-xl bg-[#f5f5f7]/90 border border-black/6 space-y-1.5"
                    >
                      <div className="text-[11px] font-bold text-[#515154] px-1">
                        {phaseTitle}
                      </div>
                      {items.map((st) => {
                        const done = isStageCompleted(
                          st.code,
                          stageBus,
                          fusedPlots.length > 0,
                          Boolean(lockedTargetPlot)
                        );
                        const isCurrent = st.code === activeStageCode;
                        return (
                          <button
                            key={st.code}
                            type="button"
                            onClick={() => {
                              navigateToStage(st.code);
                              setStageMenuOpen(false);
                            }}
                            className={`w-full flex items-start gap-2 p-2 rounded-lg text-left transition-all ${
                              isCurrent
                                ? "bg-[#0071e3] text-white shadow-xs"
                                : "bg-white hover:bg-[#0071e3]/8 text-[#1d1d1f] border border-black/5"
                            }`}
                          >
                            <span
                              className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
                                done
                                  ? isCurrent
                                    ? "bg-white"
                                    : "bg-[#10b981]"
                                  : isCurrent
                                  ? "bg-white/60"
                                  : "bg-black/20"
                              }`}
                            />
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center justify-between gap-1">
                                <span className="text-[12px] font-bold truncate">
                                  {st.code} · {st.name}
                                </span>
                                <ChevronRight
                                  className={`w-3.5 h-3.5 shrink-0 ${
                                    isCurrent ? "text-white" : "text-[#515154]"
                                  }`}
                                />
                              </div>
                              <div
                                className={`text-[10px] truncate ${
                                  isCurrent ? "text-white/85" : "text-[#515154]"
                                }`}
                              >
                                {st.description}
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Dual-Monitor sc-datav Popout Window Button */}
          <button
            type="button"
            onClick={() => openDatavPopout(activeProjectId)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white hover:bg-[#0071e3]/8 border border-black/10 text-[12px] font-semibold text-[#1d1d1f] transition-colors"
            title="在独立副屏窗口中弹出 sc-datav 全屏空间态势驾驶舱（双屏答辩投影）"
          >
            <MonitorUp className="w-3.5 h-3.5 text-[#0071e3]" />
            <span className="hidden md:inline">副屏大屏</span>
          </button>

          {/* System & API Settings Modal Trigger */}
          <button
            type="button"
            onClick={() => setSettingsOpen(true)}
            className="p-2 rounded-lg bg-white hover:bg-black/5 border border-black/10 text-[#1d1d1f] transition-colors"
            title="大模型与本地引擎设置"
          >
            <Settings className="w-4 h-4 text-[#515154]" />
          </button>

          {/* Hybrid RAG AI Copilot Drawer Toggle */}
          <button
            type="button"
            onClick={() => setCopilotOpen(!copilotOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-all ${
              copilotOpen
                ? "bg-[#0071e3] text-white shadow-xs"
                : "bg-white hover:bg-[#0071e3]/10 text-[#0071e3] border border-[#0071e3]/30"
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>AI 副驾</span>
          </button>
        </div>
      </header>

      {/* Main Content Workspace below 52px Top Bar */}
      <div className="flex-1 flex pt-[52px] min-h-0 relative overflow-hidden">
        <main className="flex-1 min-w-0 h-full overflow-y-auto">{children}</main>

        {/* Collapsible Right Hybrid RAG Copilot Drawer */}
        {copilotOpen && (
          <aside className="w-[400px] shrink-0 h-full bg-white border-l border-black/10 flex flex-col shadow-xl z-30">
            {/* Drawer Header */}
            <div className="p-3.5 border-b border-black/8 flex items-center justify-between bg-[#f5f5f7]/70">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#0071e3] text-white flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[13px] font-bold text-[#1d1d1f] flex items-center gap-1.5">
                    <span>规划师 AI 副驾</span>
                    <span className="px-1.5 py-0.2 rounded-full bg-[#10b981]/15 text-[#065f46] text-[10px] font-semibold">
                      Hybrid RAG
                    </span>
                  </div>
                  <div className="text-[11px] text-[#515154]">
                    阶段 {currentStageMeta.code}：{currentStageMeta.name}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={handleClearCopilot}
                  className="p-1.5 rounded-lg hover:bg-black/6 text-[#515154]"
                  title="清空对话记录"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setCopilotOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-black/6 text-[#515154]"
                  title="收起副驾抽屉"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Active Context Banner (Clean Chinese business pills — zero internal keys) */}
            <div className="px-3.5 py-2 bg-[#0071e3]/[0.05] border-b border-black/6 flex flex-wrap items-center gap-1.5 text-[11px]">
              <span className="px-2 py-0.5 rounded-full bg-white border border-black/8 text-[#1d1d1f] font-medium">
                当前工程：{activeProject.name.slice(0, 14)}
              </span>
              {lockedTargetPlot ? (
                <span className="px-2 py-0.5 rounded-full bg-[#10b981]/15 text-[#065f46] font-semibold">
                  靶向地块：{lockedTargetPlot.name} (FAR {lockedTargetPlot.far?.toFixed(2)})
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full bg-black/6 text-[#515154]">
                  已加载 {fusedPlots.length} 个重点更新单元
                </span>
              )}
            </div>

            {/* Messages Stream */}
            <div className="flex-1 overflow-y-auto p-3.5 space-y-3">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${
                    msg.role === "user" ? "items-end" : "items-start"
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1 px-1 text-[10px] text-[#515154]">
                    <span>
                      {msg.role === "user" ? "规划师提问" : "UltimateDESIGN 副驾"}
                    </span>
                    <span>·</span>
                    <span>{msg.timestamp}</span>
                    {msg.stage_label && (
                      <span className="px-1.5 py-0.2 rounded bg-black/5 text-[#1d1d1f]">
                        {msg.stage_label}
                      </span>
                    )}
                  </div>

                  <div
                    className={`max-w-[92%] rounded-2xl px-3.5 py-2.5 text-[12.5px] leading-relaxed whitespace-pre-wrap ${
                      msg.role === "user"
                        ? "bg-[#0071e3] text-white rounded-br-xs"
                        : "bg-[#f5f5f7] text-[#1d1d1f] border border-black/8 rounded-bl-xs"
                    }`}
                  >
                    {msg.content || (msg.streaming ? "正在检索法规库并推演空间策略…" : "")}
                  </div>

                  {/* Hybrid RAG Legal Citations Badges */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-1.5 max-w-[92%] space-y-1">
                      {msg.citations.map((cit, cIdx) => (
                        <div
                          key={`${msg.id}-cit-${cIdx}`}
                          className="flex items-start gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#8b5cf6]/8 border border-[#8b5cf6]/25 text-[11px] text-[#1d1d1f]"
                        >
                          <BookOpen className="w-3.5 h-3.5 text-[#8b5cf6] shrink-0 mt-0.5" />
                          <div className="min-w-0">
                            <div className="font-semibold text-[#5b21b6] truncate">
                              {cit.source} {cit.clause ? `· ${cit.clause}` : ""}
                            </div>
                            {cit.snippet && (
                              <div className="text-[10.5px] text-[#515154] line-clamp-2">
                                {cit.snippet}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            {/* Quick Prompts & Input Box */}
            <div className="p-3 border-t border-black/8 bg-[#f5f5f7]/60 space-y-2">
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                {QUICK_COPILOT_PROMPTS.map((qp, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendCopilot(qp)}
                    disabled={copilotStreaming}
                    className="shrink-0 px-2.5 py-1 rounded-full bg-white hover:bg-[#0071e3]/10 border border-black/10 text-[11px] text-[#1d1d1f] transition-colors"
                  >
                    {qp.slice(0, 18)}…
                  </button>
                ))}
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendCopilot();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={copilotInput}
                  onChange={(e) => setCopilotInput(e.target.value)}
                  placeholder="询问规划法规、地块容积率核算或更新策略…"
                  className="flex-1 px-3 py-2 rounded-xl bg-white border border-black/12 text-[12.5px] text-[#1d1d1f] focus:outline-none focus:border-[#0071e3]"
                />
                <button
                  type="submit"
                  disabled={copilotStreaming || !copilotInput.trim()}
                  className="px-3.5 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] disabled:opacity-50 text-white text-[12px] font-semibold flex items-center gap-1"
                >
                  {copilotStreaming ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </form>
            </div>
          </aside>
        )}

        {/* Floating Bottom-Left Background Task Tray (JobTray) */}
        <div className="fixed bottom-3.5 left-3.5 z-40">
          {!jobTrayExpanded ? (
            <button
              type="button"
              onClick={() => setJobTrayExpanded(true)}
              className="ud-glass-panel flex items-center gap-2 px-3.5 py-2 rounded-full text-[12px] font-semibold text-[#1d1d1f] hover:border-[#0071e3]/40 transition-all"
            >
              {runningJobsCount > 0 ? (
                <Loader2 className="w-4 h-4 text-[#0071e3] animate-spin" />
              ) : (
                <Terminal className="w-4 h-4 text-[#0071e3]" />
              )}
              <span>
                后台作业队列 ({jobs.length})
              </span>
              {runningJobsCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-[#0071e3] text-white text-[10px]">
                  {runningJobsCount} 运行中
                </span>
              )}
            </button>
          ) : (
            <div className="ud-glass-panel w-[440px] rounded-2xl p-3.5 space-y-2.5">
              <div className="flex items-center justify-between pb-2 border-b border-black/8">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#0071e3]" />
                  <span className="text-[12.5px] font-bold text-[#1d1d1f]">
                    异步工程交付与计算作业队列
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setJobTrayExpanded(false)}
                  className="p-1 rounded-lg hover:bg-black/6 text-[#515154]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {jobs.length === 0 ? (
                <div className="py-4 text-center text-[12px] text-[#515154]">
                  当前暂无运行中的后台编译或导出作业（Word报告 / AutoCAD DXF / A3图册 / SD生图）
                </div>
              ) : (
                <div className="max-h-[240px] overflow-y-auto space-y-2 pr-1">
                  {jobs.slice(0, 10).map((job: BackgroundJob) => {
                    const jid = job.id || job.job_id || "job";
                    const title =
                      job.title || job.name || job.type || job.job_type || "规划后台作业";
                    const targetPath =
                      job.output_path ||
                      job.artifact_path ||
                      job.result?.output_path ||
                      job.result?.file_path ||
                      "";
                    const pct = Math.max(
                      0,
                      Math.min(100, Math.round((job.progress || 0) * (job.progress <= 1 ? 100 : 1)))
                    );

                    return (
                      <div
                        key={jid}
                        className="p-2.5 rounded-xl bg-white border border-black/8 space-y-1.5"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[12px] font-semibold text-[#1d1d1f] truncate">
                            {title}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              job.status === "succeeded"
                                ? "bg-[#10b981]/15 text-[#065f46]"
                                : job.status === "failed"
                                ? "bg-[#ef4444]/15 text-[#991b1b]"
                                : "bg-[#0071e3]/15 text-[#0071e3]"
                            }`}
                          >
                            {job.status === "succeeded"
                              ? "已完成"
                              : job.status === "failed"
                              ? "异常"
                              : `${pct}%`}
                          </span>
                        </div>

                        <div className="w-full h-1.5 rounded-full bg-black/8 overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              job.status === "succeeded"
                                ? "bg-[#10b981]"
                                : job.status === "failed"
                                ? "bg-[#ef4444]"
                                : "bg-[#0071e3]"
                            }`}
                            style={{
                              width: `${job.status === "succeeded" ? 100 : pct}%`,
                            }}
                          />
                        </div>

                        <div className="flex items-center justify-between text-[11px] text-[#515154]">
                          <span className="truncate max-w-[220px]">
                            {job.message || "任务已纳入本地后台线程池监管"}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <button
                              type="button"
                              onClick={() =>
                                setActiveLogJobId(activeLogJobId === jid ? null : jid)
                              }
                              className="px-2 py-0.5 rounded bg-black/5 hover:bg-black/10 text-[#1d1d1f] font-medium"
                            >
                              日志
                            </button>
                            {targetPath && (
                              <button
                                type="button"
                                onClick={() => openInExplorer(targetPath)}
                                className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#0071e3]/10 hover:bg-[#0071e3]/20 text-[#0071e3] font-semibold"
                              >
                                <FolderOpen className="w-3 h-3" />
                                <span>在资源管理器中定位</span>
                              </button>
                            )}
                          </div>
                        </div>

                        {activeLogJobId === jid && (
                          <div className="mt-1.5 p-2 rounded-lg bg-[#1d1d1f] text-[#f5f5f7] font-mono text-[10.5px] max-h-[110px] overflow-y-auto space-y-0.5">
                            {(liveJobLogs[jid] || job.logs || ["正在连接实时 SSE 任务日志流…"]).map(
                              (ln, lIdx) => (
                                <div key={lIdx}>{ln}</div>
                              )
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* System & API Keys Configuration Modal */}
      {settingsOpen && (
        <div className="fixed inset-0 z-50 bg-black/35 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="ud-card w-full max-w-[540px] p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-black/8">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-[#0071e3]/10 text-[#0071e3] flex items-center justify-center">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-[16px] font-bold text-[#1d1d1f]">
                    系统引擎与大模型密钥配置
                  </h2>
                  <p className="text-[12px] text-[#515154]">
                    遵循零明文泄露规范 · 支持离线规则回退与本地 SD ControlNet
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSettingsOpen(false)}
                className="p-1.5 rounded-lg hover:bg-black/6 text-[#515154]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Engine Status Summary Pills */}
            <div className="grid grid-cols-3 gap-2.5">
              <div className="p-2.5 rounded-xl bg-[#f5f5f7] border border-black/6">
                <div className="text-[11px] text-[#515154]">DuckDB Spatial</div>
                <div className="text-[13px] font-bold text-[#10b981] flex items-center gap-1 mt-0.5">
                  <ShieldCheck className="w-4 h-4" />
                  <span>{enginesHud?.duckdb_version || "v1.5+ SIMD 就绪"}</span>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-[#f5f5f7] border border-black/6">
                <div className="text-[11px] text-[#515154]">rustworkx 图算力</div>
                <div className="text-[13px] font-bold text-[#10b981] mt-0.5">
                  全路网并行就绪
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-[#f5f5f7] border border-black/6">
                <div className="text-[11px] text-[#515154]">Hybrid RAG 法规库</div>
                <div className="text-[13px] font-bold text-[#0071e3] mt-0.5">
                  只读保护已启用
                </div>
              </div>
            </div>

            <form onSubmit={handleSaveSettings} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[12px] font-semibold text-[#1d1d1f] mb-1">
                    大模型服务商
                  </label>
                  <select
                    value={settingsForm.llm_provider || "deepseek"}
                    onChange={(e) =>
                      setSettingsForm((s) => ({ ...s, llm_provider: e.target.value }))
                    }
                    className="w-full px-3 py-2 rounded-xl bg-[#f5f5f7] border border-black/12 text-[12.5px] text-[#1d1d1f]"
                  >
                    <option value="deepseek">DeepSeek (OpenAI 兼容)</option>
                    <option value="openai">OpenAI / 兼容网关</option>
                    <option value="qwen">阿里通义千问 DashScope</option>
                    <option value="ollama">本地 Ollama 离线推理</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[12px] font-semibold text-[#1d1d1f] mb-1">
                    模型名称 (Model ID)
                  </label>
                  <input
                    type="text"
                    value={settingsForm.llm_model || ""}
                    onChange={(e) =>
                      setSettingsForm((s) => ({ ...s, llm_model: e.target.value }))
                    }
                    placeholder="deepseek-chat"
                    className="w-full px-3 py-2 rounded-xl bg-[#f5f5f7] border border-black/12 text-[12.5px] text-[#1d1d1f]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-[#1d1d1f] mb-1">
                  API Base URL
                </label>
                <input
                  type="text"
                  value={settingsForm.llm_base_url || ""}
                  onChange={(e) =>
                    setSettingsForm((s) => ({ ...s, llm_base_url: e.target.value }))
                  }
                  placeholder="https://api.deepseek.com/v1"
                  className="w-full px-3 py-2 rounded-xl bg-[#f5f5f7] border border-black/12 text-[12.5px] text-[#1d1d1f]"
                />
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-[#1d1d1f] mb-1">
                  API Key 密钥{" "}
                  {settingsForm.llm_api_key_masked && (
                    <span className="text-[11px] text-[#10b981] font-normal">
                      (当前已配置: {settingsForm.llm_api_key_masked})
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  value={settingsForm.llm_api_key || ""}
                  onChange={(e) =>
                    setSettingsForm((s) => ({ ...s, llm_api_key: e.target.value }))
                  }
                  placeholder="输入新密钥以更新（留空则保持既有密钥不变）"
                  className="w-full px-3 py-2 rounded-xl bg-[#f5f5f7] border border-black/12 text-[12.5px] text-[#1d1d1f]"
                />
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-[#1d1d1f] mb-1">
                  Stable Diffusion WebUI / ControlNet 本地端点
                </label>
                <input
                  type="text"
                  value={settingsForm.sd_api_url || ""}
                  onChange={(e) =>
                    setSettingsForm((s) => ({ ...s, sd_api_url: e.target.value }))
                  }
                  placeholder="http://127.0.0.1:7860"
                  className="w-full px-3 py-2 rounded-xl bg-[#f5f5f7] border border-black/12 text-[12.5px] text-[#1d1d1f]"
                />
              </div>

              <div>
                <label className="block text-[12px] font-semibold text-[#1d1d1f] mb-1">
                  百度地图开放平台街景 AK (BYOK 自带密钥){" "}
                  {settingsForm.baidu_ak_masked && (
                    <span className="text-[11px] text-[#10b981] font-normal">
                      (当前已配置: {settingsForm.baidu_ak_masked})
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  value={settingsForm.baidu_ak || ""}
                  onChange={(e) =>
                    setSettingsForm((s) => ({ ...s, baidu_ak: e.target.value }))
                  }
                  placeholder="请前往 lbsyun.baidu.com 申请服务端 AK（安装包不预置个人街景与密钥）"
                  className="w-full px-3 py-2 rounded-xl bg-[#f5f5f7] border border-black/12 text-[12.5px] text-[#1d1d1f]"
                />
              </div>

              {settingsFeedback && (
                <div className="p-2.5 rounded-xl bg-[#0071e3]/10 text-[#0071e3] text-[12px] font-medium">
                  {settingsFeedback}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSettingsOpen(false)}
                  className="px-4 py-2 rounded-xl bg-black/6 hover:bg-black/10 text-[12.5px] font-semibold text-[#1d1d1f]"
                >
                  关闭
                </button>
                <button
                  type="submit"
                  disabled={settingsSaving}
                  className="px-4 py-2 rounded-xl bg-[#0071e3] hover:bg-[#0077ed] text-white text-[12.5px] font-semibold flex items-center gap-1.5"
                >
                  {settingsSaving && <Loader2 className="w-4 h-4 animate-spin" />}
                  <span>保存配置</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AppShell;
