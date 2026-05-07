import { colors, fonts, layout } from "../styles/theme";

export const openingConfig = {
  id: "opening",
  duration: 15,
  narration: "数字孪生·古今共振——AI赋能下的伪满皇宫周边街区更新规划设计",
};

export function generateOpeningHTML(data: any): string {
  const project = data.project ?? {};
  return `
<div style="width: ${layout.width}px; height: ${layout.height}px;
            background: ${colors.background}; display: flex;
            flex-direction: column; align-items: center; justify-content: center;
            position: relative; overflow: hidden;">
  <div style="position: absolute; top: 50%; left: 50%;
              width: 600px; height: 600px; border-radius: 50%;
              background: radial-gradient(circle, ${colors.primaryDim}, transparent 70%);
              transform: translate(-50%, -50%);"></div>
  <div style="position: absolute; inset: 0;
              background: repeating-linear-gradient(0deg, transparent, transparent 99px, ${colors.primary}08 100px),
              repeating-linear-gradient(90deg, transparent, transparent 99px, ${colors.primary}08 100px);"></div>
  <h1 id="title" style="font-size: 80px; font-weight: bold; color: ${colors.text};
      font-family: ${fonts.title}; z-index: 1; text-shadow: 0 0 40px ${colors.primary}44;
      transform: scale(0.8); opacity: 0;">
    ${project.name ?? "数字孪生·古今共振"}
  </h1>
  <p id="subtitle" style="font-size: 36px; color: ${colors.textSecondary};
     font-family: ${fonts.body}; margin-top: 24px; z-index: 1;
     transform: translateY(20px); opacity: 0;">
    ${project.subtitle ?? "AI赋能下的伪满皇宫周边街区更新规划设计"}
  </p>
  <div id="divider" style="width: 0; height: 2px; background: ${colors.primary};
       margin: 32px 0; z-index: 1;"></div>
  <p id="info" style="font-size: 24px; color: ${colors.textSecondary};
     font-family: ${fonts.body}; z-index: 1; transform: translateY(20px); opacity: 0;">
    ${project.location ?? "中国吉林省长春市宽城区"} | ${project.area ?? "约150公顷"}
  </p>
</div>
<script>
  anime.timeline({ loop: false })
    .add({ targets: '#title', scale: [0.8, 1], opacity: [0, 1], duration: 1200, easing: 'easeOutQuad' })
    .add({ targets: '#subtitle', translateY: [20, 0], opacity: [0, 1], duration: 800, easing: 'easeOutQuad' }, '-=600')
    .add({ targets: '#divider', width: [0, 300], duration: 600, easing: 'easeInOutQuad' }, '-=400')
    .add({ targets: '#info', translateY: [20, 0], opacity: [0, 1], duration: 600, easing: 'easeOutQuad' }, '-=300');
</script>`;
}
