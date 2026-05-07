/** UltimateDESIGN 视频主题常量 */

export const colors = {
  background: "#0a0f1a",
  backgroundLight: "#111827",
  primary: "#00d4ff",
  primaryDim: "rgba(0, 212, 255, 0.3)",
  text: "#ffffff",
  textSecondary: "#94a3b8",
  gold: "#ffd700",
  warning: "#ff6b35",
  eco: "#4ecdc4",
  purple: "#a855f7",
  success: "#34d399",
  error: "#ef4444",
} as const;

export const fonts = {
  title: '"Noto Sans SC", "Source Han Sans SC", sans-serif',
  body: '"Noto Sans SC", sans-serif',
  mono: '"JetBrains Mono", "Fira Code", monospace',
} as const;

export const animation = {
  easeIn: "power2.out",
  easeOut: "power2.in",
  easeInOut: "power2.inOut",
  durationIn: 0.8,
  durationOut: 0.5,
  durationTransition: 1.2,
  stagger: 0.15,
} as const;

export const layout = {
  width: 1920,
  height: 1080,
  padding: 80,
  titleSize: 64,
  subtitleSize: 36,
  bodySize: 24,
  captionSize: 18,
} as const;

export const stageNames: Record<string, string> = {
  "01": "任务解读",
  "02": "资料收集",
  "03": "现场调研",
  "04": "现状分析",
  "05": "问题诊断",
  "06": "目标定位",
  "07": "设计策略",
  "08": "总体城市设计",
  "09": "专项系统设计",
  "10": "重点地段深化",
  "11": "实施路径",
  "12": "城市设计导则",
  "13": "成果表达",
};
