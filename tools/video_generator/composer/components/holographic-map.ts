/**
 * 3D 全息分层地图组件
 * 使用相同旋转视角逐层叠加展示不同数据层
 */

export interface MapLayer {
  name: string;
  color: string;
  dataUrl?: string;
  opacity?: number;
}

export interface HolographicMapConfig {
  layers: MapLayer[];
  layerDuration: number;
  holdDuration: number;
  cameraAngle: number;
  rotationSpeed: number;
}

export const defaultMapConfig: HolographicMapConfig = {
  layers: [
    { name: "建筑基底", color: "#475569", opacity: 0.8 },
    { name: "用地现状", color: "#ef4444", opacity: 0.6 },
    { name: "POI 热力", color: "#f59e0b", opacity: 0.5 },
    { name: "道路交通", color: "#ffffff", opacity: 0.7 },
    { name: "建筑高度", color: "#3b82f6", opacity: 0.6 },
    { name: "更新潜力", color: "#a855f7", opacity: 0.5 },
  ],
  layerDuration: 4,
  holdDuration: 10,
  cameraAngle: 45,
  rotationSpeed: 5,
};

export function generateHolographicMapHTML(config: HolographicMapConfig): string {
  const layerHTML = config.layers
    .map(
      (layer, i) => `
    <div class="map-layer" id="layer-${i}"
         style="opacity: 0; background-color: ${layer.color};
                position: absolute; inset: 0; border-radius: 12px;">
      <div class="layer-label"
           style="position: absolute; top: 20px; left: 20px;
                  color: white; font-size: 18px; font-weight: bold;
                  background: rgba(0,0,0,0.6); padding: 8px 16px;
                  border-radius: 8px; border-left: 3px solid ${layer.color};">
        ${layer.name}
      </div>
    </div>`
    )
    .join("\n");

  const layerAnimations = config.layers
    .map(
      (_, i) => `
    { targets: '#layer-${i}', opacity: [0, ${config.layers[i].opacity ?? 0.6}],
      duration: 800, delay: ${i * config.layerDuration * 1000},
      easing: 'easeOutQuad' }`
    )
    .join(",\n");

  return `
<div style="width: 100%; height: 100%; position: relative;
            background: #0a0f1a; overflow: hidden;">
  <div id="grid-bg" style="position: absolute; inset: 0;
       background: repeating-linear-gradient(
         0deg, transparent, transparent 49px,
         rgba(0,212,255,0.05) 50px),
       repeating-linear-gradient(
         90deg, transparent, transparent 49px,
         rgba(0,212,255,0.05) 50px);
       transform: perspective(800px) rotateX(${config.cameraAngle}deg);
       transform-origin: center center;">
  </div>
  <div style="position: absolute; inset: 80px;
              transform: perspective(800px) rotateX(${config.cameraAngle}deg);
              transform-origin: center center;">
    ${layerHTML}
  </div>
  <div style="position: absolute; bottom: 40px; left: 50%;
              transform: translateX(-50%);
              color: #00d4ff; font-size: 28px; font-weight: bold;
              text-shadow: 0 0 20px rgba(0,212,255,0.5);">
    3D 全息数据底座
  </div>
</div>
<script>
  anime.timeline({ loop: false })
    .add({ targets: '#grid-bg', rotateX: [50, 45], duration: 1000, easing: 'easeOutQuad' })
    .add([${layerAnimations}], '-=500');
</script>`;
}
