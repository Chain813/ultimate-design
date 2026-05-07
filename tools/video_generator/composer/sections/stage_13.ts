import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";
import { generateHolographicMapHTML, defaultMapConfig } from "../components/holographic-map";
import { generateDataCountersHTML } from "../components/data-counter";

export const stage13Config = {
  id: "stage_13",
  stageCode: "13",
  duration: 60,
  narration: "成果表达：核心指标汇总与3D全息方案回顾",
};

export function generateStage13HTML(data: any): string {
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; font-family: ${fonts.body};">
  ${generateTransitionHTML("13")}
  <div style="position: absolute; top: 120px; left: ${layout.padding}px;
              right: ${layout.padding}px; height: 400px;">
    ${generateHolographicMapHTML({ ...defaultMapConfig, holdDuration: 15 })}
  </div>
  <div style="position: absolute; bottom: 80px; left: ${layout.padding}px; right: ${layout.padding}px;">
    ${generateDataCountersHTML([
      { label: "研究范围", value: 150, suffix: " 公顷", color: colors.primary },
      { label: "建筑总量", value: 110289, suffix: " 栋", color: colors.gold },
      { label: "重点地块", value: 5, suffix: " 个", color: colors.eco },
      { label: "图纸模板", value: 70, suffix: " 种", color: colors.purple },
    ])}
  </div>
  <div style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); text-align: center;">
    <div style="color: ${colors.textSecondary}; font-size: 18px;">感谢聆听 | Thank You</div>
  </div>
</div>`;
}
