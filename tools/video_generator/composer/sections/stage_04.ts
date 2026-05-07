import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";
import { generateHolographicMapHTML, defaultMapConfig } from "../components/holographic-map";

export const stage04Config = {
  id: "stage_04",
  stageCode: "04",
  duration: 50,
  narration: "现状分析：3D全息数据底座，多层叠加展示空间现状",
};

export function generateStage04HTML(data: any): string {
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; font-family: ${fonts.body};">
  ${generateTransitionHTML("04")}
  <div style="position: absolute; top: 120px; left: ${layout.padding}px;
              right: ${layout.padding}px; bottom: ${layout.padding}px;">
    ${generateHolographicMapHTML(defaultMapConfig)}
  </div>
</div>`;
}
