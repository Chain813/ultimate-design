import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage09Config = {
  id: "stage_09",
  stageCode: "09",
  duration: 45,
  narration: "专项系统设计：道路交通、慢行系统、公共空间、绿地景观",
};

export function generateStage09HTML(data: any): string {
  const systems = [
    { name: "道路交通", icon: "🛣️", color: colors.textSecondary },
    { name: "慢行系统", icon: "🚶", color: colors.eco },
    { name: "公共空间", icon: "🏛️", color: colors.gold },
    { name: "绿地景观", icon: "🌳", color: colors.success },
  ];
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("09")}
  <div style="margin-top: 40px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 32px;">
    ${systems.map((sys) => `
      <div class="system-card" style="background: ${colors.backgroundLight};
           border-radius: 16px; padding: 32px; border-top: 4px solid ${sys.color};
           opacity: 0; transform: scale(0.95);">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
          <span style="font-size: 40px;">${sys.icon}</span>
          <span style="font-size: 24px; color: ${sys.color}; font-weight: bold;">${sys.name}</span>
        </div>
        <div style="height: 200px; background: rgba(0,0,0,0.2); border-radius: 8px;
                    display: flex; align-items: center; justify-content: center;">
          <span style="color: ${colors.textSecondary};">${sys.name}规划图</span>
        </div>
      </div>`).join("")}
  </div>
</div>
<script>
  anime({ targets: '.system-card', scale: [0.95, 1], opacity: [0, 1], duration: 800, easing: 'easeOutQuad', delay: anime.stagger(200, { start: 1500 }) });
</script>`;
}
