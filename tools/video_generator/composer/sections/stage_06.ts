import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage06Config = {
  id: "stage_06",
  stageCode: "06",
  duration: 35,
  skipIf: (data: any) => !data.stages?.["06"]?.data?.design_concept,
  narration: "目标定位：数字孪生·古今共振设计理念",
};

export function generateStage06HTML(data: any): string {
  const concept = data.stages?.["06"]?.data?.design_concept ?? "数字孪生·古今共振";
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("06")}
  <div style="margin-top: 60px; text-align: center;">
    <h2 id="concept" style="font-size: 56px; color: ${colors.gold};
        text-shadow: 0 0 30px ${colors.gold}44; transform: scale(0.9); opacity: 0;">
      「${concept}」
    </h2>
    <div style="display: flex; justify-content: center; gap: 40px; margin-top: 60px;">
      ${[
        { label: "精准感知", desc: "数据驱动的现状诊断" },
        { label: "古今共振", desc: "历史文脉与当代活力融合" },
        { label: "多元协商", desc: "居民/开发商/规划师共识" },
        { label: "渐进更新", desc: "微更新→系统更新的分期路径" },
      ].map((item) => `
        <div class="dimension" style="background: ${colors.backgroundLight};
             border-radius: 16px; padding: 32px; width: 200px;
             border-top: 4px solid ${colors.primary}; opacity: 0; transform: translateY(30px);">
          <div style="font-size: 24px; color: ${colors.primary}; font-weight: bold;">${item.label}</div>
          <div style="font-size: 16px; color: ${colors.textSecondary}; margin-top: 12px;">${item.desc}</div>
        </div>`).join("")}
    </div>
  </div>
</div>
<script>
  anime.timeline({ loop: false })
    .add({ targets: '#concept', scale: [0.9, 1], opacity: [0, 1], duration: 1000, easing: 'easeOutQuad', delay: 1500 })
    .add({ targets: '.dimension', translateY: ['30px', '0'], opacity: [0, 1], duration: 600, easing: 'easeOutQuad', delay: anime.stagger(200, { start: 2500 }) });
</script>`;
}
