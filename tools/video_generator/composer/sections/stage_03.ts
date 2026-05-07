import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage03Config = {
  id: "stage_03",
  stageCode: "03",
  duration: 40,
  narration: "现场调研：实地踏勘，记录街道空间与环境问题",
};

export function generateStage03HTML(data: any): string {
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("03")}
  <div style="margin-top: 40px;">
    <h3 style="color: ${colors.primary}; font-size: 28px; margin-bottom: 24px;">调研点位分布与典型问题</h3>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
      ${[
        { type: "界面杂乱", icon: "🏚️", color: colors.warning },
        { type: "停车混乱", icon: "🅿️", color: colors.gold },
        { type: "消极空间", icon: "⬜", color: colors.textSecondary },
        { type: "设施老化", icon: "🔧", color: colors.primary },
        { type: "绿化不足", icon: "🌿", color: colors.eco },
        { type: "交通割裂", icon: "🚧", color: colors.error },
      ].map((item) => `
        <div class="survey-card" style="background: ${colors.backgroundLight};
             border-radius: 12px; padding: 24px; display: flex; align-items: center; gap: 16px;
             border-left: 4px solid ${item.color}; opacity: 0; transform: translateY(20px);">
          <span style="font-size: 36px;">${item.icon}</span>
          <span style="color: ${colors.text}; font-size: 20px;">${item.type}</span>
        </div>`).join("")}
    </div>
  </div>
</div>
<script>
  anime({ targets: '.survey-card', translateY: ['20px', '0'], opacity: [0, 1], duration: 600, easing: 'easeOutQuad', delay: anime.stagger(150, { start: 1500 }) });
</script>`;
}
