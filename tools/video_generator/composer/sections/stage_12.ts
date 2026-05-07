import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage12Config = {
  id: "stage_12",
  stageCode: "12",
  duration: 30,
  narration: "城市设计导则：地块控制图则与街道断面设计",
};

export function generateStage12HTML(data: any): string {
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("12")}
  <div style="margin-top: 40px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;">
    ${[
      { title: "地块控制图则", desc: "容积率、建筑密度、绿地率、限高", icon: "📐" },
      { title: "街道设计导则", desc: "断面设计、界面控制、设施配置", icon: "🛤️" },
      { title: "公共空间导则", desc: "配置标准、设施指引、活动场景", icon: "🏛️" },
    ].map((item) => `
      <div class="guideline-card" style="background: ${colors.backgroundLight};
           border-radius: 16px; padding: 32px; text-align: center;
           border: 2px solid ${colors.primary}33; opacity: 0; transform: scale(0.95);">
        <div style="font-size: 48px; margin-bottom: 16px;">${item.icon}</div>
        <div style="font-size: 22px; color: ${colors.primary}; font-weight: bold;">${item.title}</div>
        <div style="font-size: 16px; color: ${colors.textSecondary}; margin-top: 12px;">${item.desc}</div>
      </div>`).join("")}
  </div>
</div>
<script>
  anime({ targets: '.guideline-card', scale: [0.95, 1], opacity: [0, 1], duration: 800, easing: 'easeOutQuad', delay: anime.stagger(200, { start: 1500 }) });
</script>`;
}
