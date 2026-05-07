import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";
import { generateBarChartHTML, generateRadarChartHTML } from "../components/chart-animation";

export const stage05Config = {
  id: "stage_05",
  stageCode: "05",
  duration: 50,
  narration: "问题诊断：MPI更新潜力排行与地块诊断雷达",
};

export function generateStage05HTML(data: any): string {
  const mpiData = data.stages?.["05"]?.data?.mpi_ranking ?? [
    { label: "站城门户", value: 85, maxValue: 100 },
    { label: "工业遗产", value: 72, maxValue: 100 },
    { label: "老旧社区", value: 68, maxValue: 100 },
    { label: "历史风貌", value: 65, maxValue: 100 },
    { label: "文旅活力", value: 58, maxValue: 100 },
  ];
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("05")}
  <div style="margin-top: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px;">
    <div>${generateBarChartHTML(mpiData, "MPI 更新潜力排行")}</div>
    <div>${generateRadarChartHTML({ axes: ["空间潜力", "设施密度", "绿视率", "天空开敞度", "环境整洁度"], values: [0.7, 0.5, 0.3, 0.6, 0.4], color: colors.primary }, "地块诊断雷达")}</div>
  </div>
</div>`;
}
