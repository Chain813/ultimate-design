/**
 * 阶段转场效果：编号滑入 + 标题淡入
 */

import { colors, animation, stageNames } from "../styles/theme";

export function generateTransitionHTML(stageCode: string): string {
  const name = stageNames[stageCode] ?? stageCode;

  return `
<div style="width: 100%; height: 100%; display: flex;
            align-items: center; justify-content: center;
            background: ${colors.background}; position: relative;">
  <div style="position: absolute; top: 50%; left: 0; right: 0;
              height: 2px; background: linear-gradient(
                90deg, transparent, ${colors.primary}, transparent);
              transform: translateY(-50%);"></div>
  <div id="stage-num"
       style="font-size: 120px; font-weight: bold; color: ${colors.primary};
              font-family: 'JetBrains Mono', monospace;
              text-shadow: 0 0 40px ${colors.primary}66;
              transform: translateX(-100px); opacity: 0;">
    ${stageCode}
  </div>
  <div id="stage-name"
       style="font-size: 48px; color: ${colors.text};
              margin-left: 32px; transform: translateY(20px); opacity: 0;">
    ${name}
  </div>
</div>
<script>
  anime.timeline({ loop: false })
    .add({ targets: '#stage-num', translateX: ['-100px', '0px'], opacity: [0, 1], duration: 800, easing: '${animation.easeIn}' })
    .add({ targets: '#stage-name', translateY: ['20px', '0px'], opacity: [0, 1], duration: 600, easing: '${animation.easeIn}' }, '-=400');
</script>`;
}
