/**
 * Before/After 擦除对比组件
 */

export interface BeforeAfterConfig {
  beforeImageUrl: string;
  afterImageUrl: string;
  title: string;
  metrics?: Array<{ label: string; before: string; after: string }>;
}

export function generateBeforeAfterHTML(config: BeforeAfterConfig): string {
  const metricsHTML = (config.metrics ?? [])
    .map(
      (m) => `
    <div style="display: flex; justify-content: space-between; align-items: center;
                padding: 8px 16px; background: rgba(0,0,0,0.4); border-radius: 8px;
                border-left: 3px solid #00d4ff;">
      <span style="color: #94a3b8; font-size: 16px;">${m.label}</span>
      <div style="display: flex; gap: 12px; align-items: center;">
        <span style="color: #ef4444; font-size: 18px;">${m.before}</span>
        <span style="color: #00d4ff; font-size: 14px;">→</span>
        <span style="color: #34d399; font-size: 18px; font-weight: bold;">${m.after}</span>
      </div>
    </div>`
    )
    .join("");

  return `
<div style="width: 100%; height: 100%; position: relative; background: #0a0f1a;">
  <div style="position: absolute; top: 40px; left: 50%; transform: translateX(-50%);
              color: #00d4ff; font-size: 36px; font-weight: bold;
              text-shadow: 0 0 20px rgba(0,212,255,0.5); z-index: 10;">${config.title}</div>
  <div id="comparison" style="position: absolute; top: 100px; left: 80px;
       right: 80px; bottom: 180px; border-radius: 16px; overflow: hidden;
       border: 2px solid rgba(0,212,255,0.3);">
    <div style="position: absolute; inset: 0;
                background: url('${config.afterImageUrl}') center/cover;"></div>
    <div id="before-clip" style="position: absolute; inset: 0;
         background: url('${config.beforeImageUrl}') center/cover;
         clip-path: inset(0 50% 0 0);"></div>
    <div id="wipe-line" style="position: absolute; top: 0; bottom: 0;
         width: 4px; background: #00d4ff; left: 50%;
         box-shadow: 0 0 20px rgba(0,212,255,0.8); transform: translateX(-50%);">
      <div style="position: absolute; top: 50%; left: 50%;
                  transform: translate(-50%, -50%);
                  width: 40px; height: 40px; border-radius: 50%;
                  background: #00d4ff; display: flex;
                  align-items: center; justify-content: center;
                  box-shadow: 0 0 20px rgba(0,212,255,0.8);">
        <span style="color: #0a0f1a; font-size: 18px;">⇔</span>
      </div>
    </div>
    <div style="position: absolute; bottom: 16px; left: 16px;
                background: rgba(0,0,0,0.7); padding: 8px 16px;
                border-radius: 8px; color: #ef4444; font-weight: bold;">Before</div>
    <div style="position: absolute; bottom: 16px; right: 16px;
                background: rgba(0,0,0,0.7); padding: 8px 16px;
                border-radius: 8px; color: #34d399; font-weight: bold;">After</div>
  </div>
  <div style="position: absolute; bottom: 40px; left: 80px; right: 80px;
              display: flex; gap: 16px; justify-content: center;">${metricsHTML}</div>
</div>
<script>
  anime({ targets: '#before-clip', clipPath: ['inset(0 100% 0 0)', 'inset(0 50% 0 0)'], duration: 2000, easing: 'easeInOutQuad', delay: 500 });
  anime({ targets: '#wipe-line', left: ['100%', '50%'], duration: 2000, easing: 'easeInOutQuad', delay: 500 });
</script>`;
}
