/**
 * GSAP 图表生长动画组件
 */

export interface BarData {
  label: string;
  value: number;
  maxValue: number;
  color?: string;
}

export interface RadarData {
  axes: string[];
  values: number[];
  color?: string;
}

export function generateBarChartHTML(data: BarData[], title: string): string {
  const bars = data
    .map(
      (d, i) => `
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 12px;">
      <div style="width: 120px; text-align: right; color: #94a3b8; font-size: 16px;">${d.label}</div>
      <div style="flex: 1; height: 32px; background: rgba(255,255,255,0.05);
                  border-radius: 16px; overflow: hidden; position: relative;">
        <div class="bar-fill" id="bar-${i}"
             style="width: 0%; height: 100%; border-radius: 16px;
                    background: linear-gradient(90deg, ${d.color ?? "#00d4ff"}, ${d.color ?? "#00d4ff"}88);
                    box-shadow: 0 0 12px ${d.color ?? "#00d4ff"}44;"></div>
        <div style="position: absolute; right: 12px; top: 50%;
                    transform: translateY(-50%); color: white; font-size: 14px;
                    font-weight: bold;" id="val-${i}">0</div>
      </div>
    </div>`
    )
    .join("");

  return `
<div style="padding: 40px;">
  <h2 style="color: #00d4ff; font-size: 32px; margin-bottom: 32px;
             text-shadow: 0 0 20px rgba(0,212,255,0.3);">${title}</h2>
  ${bars}
</div>
<script>
  document.addEventListener('DOMContentLoaded', () => {
    ${data.map((d, i) => `
      setTimeout(() => {
        document.getElementById('bar-${i}').style.width = '${(d.value / d.maxValue) * 100}%';
        animateValue('val-${i}', 0, ${d.value}, 1500);
      }, ${i * 200});`).join("")}
  });
  function animateValue(id, start, end, duration) {
    const el = document.getElementById(id);
    const range = end - start;
    const startTime = performance.now();
    function update(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      el.textContent = Math.floor(start + range * progress);
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }
</script>`;
}

export function generateRadarChartHTML(data: RadarData, title: string): string {
  const size = 300;
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 40;
  const angleStep = (2 * Math.PI) / data.axes.length;

  const gridLines = [0.25, 0.5, 0.75, 1.0]
    .map(
      (r) => `<polygon points="${data.axes
        .map((_, i) => {
          const angle = i * angleStep - Math.PI / 2;
          return `${cx + Math.cos(angle) * radius * r},${cy + Math.sin(angle) * radius * r}`;
        })
        .join(" ")}" fill="none" stroke="rgba(0,212,255,0.1)" stroke-width="1" />`
    )
    .join("");

  const axisLines = data.axes
    .map((_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      return `<line x1="${cx}" y1="${cy}" x2="${cx + Math.cos(angle) * radius}"
                    y2="${cy + Math.sin(angle) * radius}" stroke="rgba(0,212,255,0.2)" stroke-width="1" />`;
    })
    .join("");

  const dataPolygon = data.axes
    .map((_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const r = data.values[i] * radius;
      return `${cx + Math.cos(angle) * r},${cy + Math.sin(angle) * r}`;
    })
    .join(" ");

  const labels = data.axes
    .map((label, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const lx = cx + Math.cos(angle) * (radius + 20);
      const ly = cy + Math.sin(angle) * (radius + 20);
      return `<text x="${lx}" y="${ly}" fill="#94a3b8" font-size="14"
                    text-anchor="middle" dominant-baseline="middle">${label}</text>`;
    })
    .join("");

  return `
<div style="display: flex; flex-direction: column; align-items: center; padding: 40px;">
  <h2 style="color: #00d4ff; font-size: 32px; margin-bottom: 24px;
             text-shadow: 0 0 20px rgba(0,212,255,0.3);">${title}</h2>
  <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    ${gridLines}${axisLines}
    <polygon class="radar-data" points="${dataPolygon}"
             fill="rgba(0,212,255,0.15)" stroke="#00d4ff" stroke-width="2"
             stroke-dasharray="1000" stroke-dashoffset="1000" />
    ${labels}
  </svg>
</div>
<script>
  anime({ targets: '.radar-data', strokeDashoffset: [1000, 0], duration: 2000, easing: 'easeInOutQuad' });
</script>`;
}
