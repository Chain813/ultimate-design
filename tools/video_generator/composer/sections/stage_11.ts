import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage11Config = {
  id: "stage_11",
  stageCode: "11",
  duration: 30,
  narration: "实施路径：近期微更新、中期功能置换、远期整体提升",
};

export function generateStage11HTML(data: any): string {
  const phases = [
    { name: "近期", period: "1-3年", color: colors.success, items: ["环境整治", "口袋公园", "街道微更新"] },
    { name: "中期", period: "3-5年", color: colors.primary, items: ["功能置换", "工业遗产活化", "商业导入"] },
    { name: "远期", period: "5-10年", color: colors.purple, items: ["片区整体更新", "文旅品牌", "智慧系统"] },
  ];
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("11")}
  <div style="margin-top: 60px; display: flex; gap: 32px; justify-content: center;">
    ${phases.map((phase) => `
      <div class="phase-card" style="background: ${colors.backgroundLight};
           border-radius: 16px; padding: 32px; width: 300px;
           border-top: 4px solid ${phase.color}; opacity: 0; transform: translateY(30px);">
        <div style="font-size: 28px; color: ${phase.color}; font-weight: bold;">${phase.name}</div>
        <div style="font-size: 18px; color: ${colors.textSecondary}; margin: 8px 0 16px;">${phase.period}</div>
        ${phase.items.map((item) => `<div style="color: ${colors.text}; font-size: 16px; margin: 8px 0;">• ${item}</div>`).join("")}
      </div>`).join("")}
  </div>
</div>
<script>
  anime({ targets: '.phase-card', translateY: ['30px', '0'], opacity: [0, 1], duration: 800, easing: 'easeOutQuad', delay: anime.stagger(300, { start: 1500 }) });
</script>`;
}
