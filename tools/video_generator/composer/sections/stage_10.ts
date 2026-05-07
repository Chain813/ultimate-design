import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";
import { generateBeforeAfterHTML } from "../components/before-after";

export const stage10Config = {
  id: "stage_10",
  stageCode: "10",
  duration: 50,
  narration: "重点地段深化：5个重点地块的AIGC效果图与Before/After对比",
};

export function generateStage10HTML(data: any): string {
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; font-family: ${fonts.body};">
  ${generateTransitionHTML("10")}
  <div style="position: absolute; top: 120px; left: ${layout.padding}px;
              right: ${layout.padding}px; bottom: ${layout.padding}px;">
    ${generateBeforeAfterHTML({
      beforeImageUrl: data.stages?.["10"]?.images?.before ?? "",
      afterImageUrl: data.stages?.["10"]?.images?.after ?? "",
      title: "改造前后对比",
      metrics: [
        { label: "绿视率 GVI", before: "12%", after: "35%" },
        { label: "公共空间", before: "2.3ha", after: "8.7ha" },
        { label: "环境品质", before: "C级", after: "A级" },
      ],
    })}
  </div>
</div>`;
}
