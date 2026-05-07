import { colors, fonts, layout } from "../styles/theme";
import { generateTransitionHTML } from "../components/transition";

export const stage01Config = {
  id: "stage_01",
  stageCode: "01",
  duration: 30,
  narration: "任务解读：梳理任务书红线限制，建立初始认知框架",
};

export function generateStage01HTML(data: any): string {
  const stageData = data.stages?.["01"]?.data ?? {};
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; padding: ${layout.padding}px; font-family: ${fonts.body};">
  ${generateTransitionHTML("01")}
  <div style="margin-top: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px;">
    <div>
      <h3 style="color: ${colors.primary}; font-size: 28px; margin-bottom: 24px;">任务书要点</h3>
      <div class="task-card" style="background: ${colors.backgroundLight};
           border-radius: 12px; padding: 24px; border-left: 4px solid ${colors.primary};
           opacity: 0; transform: translateX(-20px);">
        <p style="color: ${colors.text}; font-size: 20px; line-height: 1.8;">
          ${stageData.summary ?? "研究范围由长春大街、长白路、东九条、亚泰快速路围合，总用地面积约150公顷。核心任务：街区微更新与城市设计。"}
        </p>
      </div>
    </div>
    <div>
      <h3 style="color: ${colors.gold}; font-size: 28px; margin-bottom: 24px;">红线限制</h3>
      ${(stageData.constraints ?? ["容积率 ≤ 1.4", "建筑限高 ≤ 24m", "保护伪满皇宫核心保护区", "维持铁路安全退距"])
        .map((c: string) => `
        <div class="constraint" style="background: ${colors.backgroundLight};
             border-radius: 8px; padding: 16px; margin-bottom: 12px;
             border-left: 4px solid ${colors.gold}; opacity: 0; transform: translateX(20px);">
          <span style="color: ${colors.text}; font-size: 18px;">${c}</span>
        </div>`).join("")}
    </div>
  </div>
</div>
<script>
  anime.timeline({ loop: false })
    .add({ targets: '.task-card', translateX: ['-20px', '0'], opacity: [0, 1], duration: 800, easing: 'easeOutQuad', delay: 1500 })
    .add({ targets: '.constraint', translateX: ['20px', '0'], opacity: [0, 1], duration: 600, easing: 'easeOutQuad', delay: anime.stagger(150, { start: 2000 }) });
</script>`;
}
