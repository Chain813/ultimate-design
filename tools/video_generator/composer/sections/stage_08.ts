import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage08Config = {
  id: "stage_08",
  stageCode: "08",
  duration: 50,
  narration: "总体城市设计：总平面图与空间结构推演",
};

export function generateStage08HTML(data: any): string {
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("08")}
  <div style="margin-top: 40px; display: grid; grid-template-columns: 2fr 1fr; gap: 40px;">
    <div style="border-radius: 16px; overflow: hidden; border: 2px solid ${colors.primary}33;">
      <div style="background: ${colors.backgroundLight}; height: 500px;
                  display: flex; align-items: center; justify-content: center;">
        <span style="color: ${colors.textSecondary}; font-size: 20px;">总平面图 / 鸟瞰效果图</span>
      </div>
    </div>
    <div>
      <h3 style="color: ${colors.primary}; font-size: 24px; margin-bottom: 24px;">空间结构</h3>
      ${[
        { label: "一核", desc: "伪满皇宫文化核心", color: colors.gold },
        { label: "两轴", desc: "站城活力轴 + 工业遗产轴", color: colors.primary },
        { label: "多片", desc: "文旅/创意/社区/站前", color: colors.eco },
        { label: "多节点", desc: "门户/文化/社区/生态", color: colors.purple },
      ].map((item) => `
        <div class="structure-item" style="background: ${colors.backgroundLight};
             border-radius: 8px; padding: 16px; margin-bottom: 12px;
             border-left: 4px solid ${item.color}; opacity: 0; transform: translateX(20px);">
          <span style="color: ${item.color}; font-weight: bold; font-size: 20px;">${item.label}</span>
          <span style="color: ${colors.textSecondary}; margin-left: 12px;">${item.desc}</span>
        </div>`).join("")}
    </div>
  </div>
</div>
<script>
  anime({ targets: '.structure-item', translateX: ['20px', '0'], opacity: [0, 1], duration: 600, easing: 'easeOutQuad', delay: anime.stagger(200, { start: 2000 }) });
</script>`;
}
