import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";
import { generateRadarChartHTML } from "../components/chart-animation";

export const stage07Config = {
  id: "stage_07",
  stageCode: "07",
  duration: 50,
  skipIf: (data: any) => !data.stages?.["07"]?.data?.negotiation_result,
  narration: "设计策略：三主体博弈与多主体共识",
};

export function generateStage07HTML(data: any): string {
  const negotiations = data.stages?.["07"]?.data?.negotiation ?? [
    { role: "居民代表老王", color: colors.eco, quote: "我们只想保留老街坊的味道，别全拆了。" },
    { role: "开发商赵总", color: colors.warning, quote: "容积率至少要1.4，不然算不过来账。" },
    { role: "规划师李工", color: colors.primary, quote: "我建议分区施策，历史区保护、新区适度开发。" },
  ];
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("07")}
  <div style="margin-top: 40px;">
    <h3 style="color: ${colors.primary}; font-size: 28px; margin-bottom: 32px;">三主体博弈推演</h3>
    <div style="display: flex; gap: 24px; margin-bottom: 40px;">
      ${negotiations.map((n: any) => `
        <div class="negotiation-card" style="flex: 1; background: ${colors.backgroundLight};
             border-radius: 16px; padding: 24px; border-top: 4px solid ${n.color};
             opacity: 0; transform: translateY(20px);">
          <div style="font-size: 18px; color: ${n.color}; font-weight: bold; margin-bottom: 12px;">${n.role}</div>
          <div style="font-size: 16px; color: ${colors.text}; line-height: 1.6; font-style: italic;">"${n.quote}"</div>
        </div>`).join("")}
    </div>
    ${generateRadarChartHTML({ axes: ["居民满意度", "开发商接受度", "规划合理性", "文化保护", "经济可行性"], values: [0.75, 0.6, 0.85, 0.8, 0.65], color: colors.success }, "多主体共识度雷达")}
  </div>
</div>
<script>
  anime({ targets: '.negotiation-card', translateY: ['20px', '0'], opacity: [0, 1], duration: 600, easing: 'easeOutQuad', delay: anime.stagger(300, { start: 1500 }) });
</script>`;
}
