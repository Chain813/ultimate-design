/**
 * 数字计数器动画组件
 */

export interface CounterData {
  label: string;
  value: number;
  suffix?: string;
  prefix?: string;
  color?: string;
}

export function generateDataCountersHTML(counters: CounterData[]): string {
  const counterHTML = counters
    .map(
      (c, i) => `
    <div style="text-align: center;">
      <div class="counter-value" id="counter-${i}"
           style="font-size: 72px; font-weight: bold; font-family: 'JetBrains Mono', monospace;
                  color: ${c.color ?? "#00d4ff"};
                  text-shadow: 0 0 30px ${c.color ?? "#00d4ff"}44;">
        ${c.prefix ?? ""}0${c.suffix ?? ""}
      </div>
      <div style="font-size: 20px; color: #94a3b8; margin-top: 8px;">${c.label}</div>
    </div>`
    )
    .join("");

  return `
<div style="display: flex; justify-content: space-around; align-items: center;
            width: 100%; height: 100%; padding: 80px;">${counterHTML}</div>
<script>
  document.addEventListener('DOMContentLoaded', () => {
    ${counters.map((c, i) => `
      animateCounter('counter-${i}', 0, ${c.value}, 2500, '${c.prefix ?? ""}', '${c.suffix ?? ""}');`).join("")}
  });
  function animateCounter(id, start, end, duration, prefix, suffix) {
    const el = document.getElementById(id);
    const range = end - start;
    const startTime = performance.now();
    function update(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + range * eased);
      el.textContent = prefix + current.toLocaleString() + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }
</script>`;
}
