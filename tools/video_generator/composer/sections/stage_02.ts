import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage02Config = {
  id: "stage_02",
  stageCode: "02",
  duration: 30,
  narration: "资料收集：多源数据汇聚，建立数据中台",
};

export function generateStage02HTML(data: any): string {
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("02")}
  <div style="margin-top: 40px; display: flex; justify-content: center; gap: 40px;">
    ${[
      { name: "空间数据", count: "110,289", unit: "建筑", color: colors.primary },
      { name: "POI 数据", count: "1,200", unit: "条记录", color: colors.eco },
      { name: "街景影像", count: "80", unit: "采样点", color: colors.gold },
      { name: "舆情数据", count: "207", unit: "条分析", color: colors.purple },
    ].map((d) => `
      <div class="data-node" style="background: ${colors.backgroundLight};
           border-radius: 16px; padding: 32px; text-align: center;
           border: 2px solid ${d.color}33; min-width: 200px; opacity: 0; transform: scale(0.9);">
        <div style="font-size: 48px; font-weight: bold; color: ${d.color};
                    font-family: 'JetBrains Mono', monospace; text-shadow: 0 0 20px ${d.color}44;">
          ${d.count}
        </div>
        <div style="font-size: 16px; color: ${colors.textSecondary}; margin-top: 8px;">${d.unit}</div>
        <div style="font-size: 20px; color: ${colors.text}; margin-top: 12px;
                    border-top: 1px solid ${d.color}33; padding-top: 12px;">${d.name}</div>
      </div>`).join("")}
  </div>
</div>
<script>
  anime({ targets: '.data-node', scale: [0.9, 1], opacity: [0, 1], duration: 800, easing: 'easeOutQuad', delay: anime.stagger(200, { start: 1500 }) });
</script>`;
}
