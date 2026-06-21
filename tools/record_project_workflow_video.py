from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageStat
try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:
    class PlaywrightTimeoutError(Exception):
        pass
    sync_playwright = None


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(
    os.environ.get(
        "VIDEO_OUT_DIR",
        str(ROOT / "static" / "project_video" / "live_recording_optimized"),
    )
)
RAW_DIR = OUT_DIR / "raw"
PROBE_DIR = OUT_DIR / "probe_frames"
SEGMENT_DIR = OUT_DIR / "segments"
BASE_URL = os.environ.get("PROJECT_URL", "http://localhost:8501")
WIDTH = 1920
HEIGHT = 1080


SCENES = [
    {
        "code": "00",
        "title": "项目总览",
        "route": "/",
        "expected": "长春伪满皇宫周边街区微更新支持平台",
        "cue": "从研究对象、平台能力与全链路工作流建立整体认知",
        "seconds": 70,
    },
    {
        "code": "01",
        "title": "任务输入与数据准备",
        "route": "/数据准备与任务解读",
        "expected": "数据准备与任务解读",
        "cue": "任务书、边界、基础数据与质量检查进入统一工作底盘",
        "seconds": 24,
    },
    {
        "code": "02",
        "title": "资料收集与现场调研",
        "route": "/资料收集与现场调研",
        "expected": "资料收集与现场调研",
        "cue": "文本资料、空间资产、现场样本和固定图纸模板协同入库",
        "seconds": 20,
    },
    {
        "code": "03",
        "title": "现状分析与问题诊断",
        "route": "/现状分析与问题诊断?sub=3D现状全息底座",
        "expected": "3D 现状全息底座",
        "cue": "三维底座、MPI 潜力评价、雷达诊断与 AI 问题报告形成诊断闭环",
        "seconds": 64,
    },
    {
        "code": "04",
        "title": "目标定位",
        "route": "/目标定位",
        "expected": "目标定位",
        "cue": "将诊断结果转译为愿景、目标体系与设计原则",
        "seconds": 20,
    },
    {
        "code": "05",
        "title": "策略生成与协同决策",
        "route": "/设计策略?sub=⚖️ 多主体协同推演",
        "expected": "三轮动态博弈协商推演",
        "cue": "问题策略对应、案例对标、多主体协商和共识雷达共同校准方案方向",
        "seconds": 100,
    },
    {
        "code": "06",
        "title": "总体城市设计推演",
        "route": "/总体城市设计?sub=用地结构优化沙盘",
        "expected": "用地结构优化沙盘",
        "cue": "空间结构、用地沙盘与概念总平面推演进入方案生成阶段",
        "seconds": 30,
    },
    {
        "code": "07",
        "title": "专项系统校核",
        "route": "/专项系统设计",
        "expected": "专项系统设计",
        "cue": "交通、公共空间、建筑形态、景观遗产与产业系统叠合校验",
        "seconds": 22,
    },
    {
        "code": "08",
        "title": "重点地块深化",
        "route": "/重点地段深化?sub=控制性详细指标推演",
        "expected": "控制性详细指标推演",
        "cue": "五个地块从诊断、指标、人群画像到深化方案形成可比较样本",
        "seconds": 30,
    },
    {
        "code": "09",
        "title": "AIGC 设计推演",
        "route": "/AIGC设计推演?sub=概念总平面图生形",
        "expected": "AIGC 设计推演",
        "cue": "ControlNet、深度图、提示词和风貌参数共同约束生成式表达",
        "seconds": 35,
    },
    {
        "code": "10",
        "title": "实施路径",
        "route": "/实施路径",
        "expected": "实施路径",
        "cue": "更新模式、时序分期、留改拆与资金策略把方案落到执行层",
        "seconds": 15,
    },
    {
        "code": "11",
        "title": "城市设计导则",
        "route": "/城市设计导则",
        "expected": "城市设计导则",
        "cue": "管控指标、导则文本与合规检查把设计推演转化为规则输出",
        "seconds": 15,
    },
    {
        "code": "12",
        "title": "智能体与成果表达",
        "route": "/制图与设计智能体Skill手册",
        "expected": "AI制图与设计技能手册",
        "cue": "制图智能体沉淀规则，支撑图册、展板和后续汇报材料生产",
        "seconds": 15,
    },
    {
        "code": "13",
        "title": "成果快速收束",
        "route": "/成果表达?sub=图册自动组装",
        "expected": "图册自动组装",
        "cue": "Atlas 图册与 A1 展板作为工作流输出证明，不展开逐页讲解",
        "seconds": 20,
    },
]


def _route_url(route: str) -> str:
    if route == "/":
        return BASE_URL + "/"
    return BASE_URL + quote(route, safe="/?=&%")


def _selected_scenes() -> list[dict[str, str | int]]:
    scene_codes = os.environ.get("SCENE_CODES", "").strip()
    if scene_codes:
        requested = {code.strip() for code in scene_codes.split(",") if code.strip()}
        return [scene for scene in SCENES if str(scene["code"]) in requested]
    scene_limit = int(os.environ.get("SCENE_LIMIT", str(len(SCENES))))
    return SCENES[:scene_limit]


def _wait_for_page(page, expected: str) -> None:
    expected_json = json.dumps(expected, ensure_ascii=False)
    for attempt in range(3):
        try:
            page.wait_for_function(
                f"() => document.body && document.body.innerText.includes({expected_json})",
                timeout=45_000,
            )
            return
        except PlaywrightTimeoutError:
            if attempt == 2:
                print(f"WARNING: expected text not found: {expected}", flush=True)
                return
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(5_000)


def _wait_for_page_stable(page, expected: str) -> None:
    _wait_for_page(page, expected)
    try:
        page.wait_for_load_state("networkidle", timeout=12_000)
    except PlaywrightTimeoutError:
        pass
    try:
        page.wait_for_function(
            """
            () => {
              const hidden = (el) => {
                const style = getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0' ||
                       rect.width < 2 || rect.height < 2;
              };
              const blockers = Array.from(document.querySelectorAll(
                '[data-testid="stSkeleton"], [data-testid="stSpinner"], .stSpinner, .stAlert'
              )).filter((el) => !hidden(el));
              const text = document.body ? document.body.innerText.trim() : '';
              return blockers.length === 0 && text.length > 80;
            }
            """,
            timeout=18_000,
        )
    except PlaywrightTimeoutError:
        print("WARNING: page stability wait timed out; continuing with visible content", flush=True)
    try:
        page.wait_for_function(
            """
            () => new Promise((resolve) => {
              const maxScroll = () => {
                const candidates = [
                  document.scrollingElement,
                  document.documentElement,
                  document.body,
                  ...document.querySelectorAll('[data-testid="stMain"], section.main, main')
                ].filter(Boolean);
                return Math.max(...candidates.map((el) => Math.max(0, el.scrollHeight - el.clientHeight)));
              };
              let last = maxScroll();
              let stable = 0;
              const tick = () => {
                const next = maxScroll();
                stable = Math.abs(next - last) < 4 ? stable + 1 : 0;
                last = next;
                if (stable >= 6) resolve(true);
                else setTimeout(tick, 140);
              };
              tick();
            })
            """,
            timeout=8_000,
        )
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(900)


def _install_capture_css(page) -> None:
    page.add_style_tag(
        content="""
        [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="stToast"], .stDeployButton, #MainMenu, footer,
        #auto-scroller-hud, #tour-hud, .tour-hud, .auto-scroller-hud {
          display: none !important;
        }
        header[data-testid="stHeader"] {
          background: rgba(255,255,255,0.96) !important;
        }
        html {
          scroll-behavior: auto !important;
        }
        #recorder-cursor {
          position: fixed;
          z-index: 999999;
          left: 0;
          top: 0;
          width: 22px;
          height: 22px;
          border-radius: 999px;
          background: #0071e3;
          border: 3px solid rgba(255,255,255,0.95);
          box-shadow: 0 10px 30px rgba(0,0,0,0.24), 0 0 0 2px rgba(0,113,227,0.24);
          pointer-events: none;
          opacity: 0;
          transform: translate(1760px, 128px);
          transition: transform 360ms cubic-bezier(.2,.8,.2,1), opacity 160ms ease;
        }
        .recorder-click-ring {
          position: fixed;
          z-index: 999998;
          left: 0;
          top: 0;
          width: 48px;
          height: 48px;
          margin-left: -24px;
          margin-top: -24px;
          border-radius: 999px;
          border: 3px solid rgba(0,113,227,0.65);
          pointer-events: none;
          animation: recorderClick 640ms ease-out forwards;
        }
        @keyframes recorderClick {
          from { opacity: 0.9; transform: scale(0.35); }
          to { opacity: 0; transform: scale(1.55); }
        }
        """
    )


def _hide_engine_warning(page) -> None:
    page.evaluate(
        """
        () => {
          const keywords = ['Stable Diffusion', 'ollama run deepseek', 'SD WebUI'];
          Array.from(document.querySelectorAll('[data-testid="stElementContainer"]')).forEach((el) => {
            const text = el.innerText || '';
            const r = el.getBoundingClientRect();
            if (r.top < 560 && r.height < 360 && keywords.some((k) => text.includes(k))) {
              el.style.display = 'none';
            }
          });
        }
        """
    )


def _show_cursor(page, x: int = 1760, y: int = 128) -> None:
    page.evaluate(
        """
        ({x, y}) => {
          let cursor = document.getElementById('recorder-cursor');
          if (!cursor) {
            cursor = document.createElement('div');
            cursor.id = 'recorder-cursor';
            document.body.appendChild(cursor);
          }
          cursor.style.opacity = '1';
          cursor.style.transform = `translate(${x}px, ${y}px)`;
        }
        """,
        {"x": x, "y": y},
    )


def _move_cursor(page, x: int, y: int, steps: int = 18) -> None:
    page.evaluate(
        "({x, y}) => { const cursor = document.getElementById('recorder-cursor'); if (cursor) cursor.style.transform = `translate(${x}px, ${y}px)`; }",
        {"x": x, "y": y},
    )
    page.mouse.move(x, y, steps=steps)


def _click_at(page, x: int, y: int) -> None:
    _move_cursor(page, x, y, steps=16)
    page.wait_for_timeout(220)
    page.evaluate(
        """
        ({x, y}) => {
          const ring = document.createElement('div');
          ring.className = 'recorder-click-ring';
          ring.style.transform = `translate(${x}px, ${y}px)`;
          document.body.appendChild(ring);
          window.setTimeout(() => ring.remove(), 800);
        }
        """,
        {"x": x, "y": y},
    )
    page.mouse.click(x, y)
    page.wait_for_timeout(850)


def _move_cursor_visual(page, x: int, y: int, wait_ms: int = 350) -> None:
    page.evaluate(
        """
        ({x, y}) => {
          let cursor = document.getElementById('recorder-cursor');
          if (!cursor) {
            cursor = document.createElement('div');
            cursor.id = 'recorder-cursor';
            document.body.appendChild(cursor);
          }
          cursor.style.opacity = '1';
          cursor.style.transform = `translate(${x}px, ${y}px)`;
        }
        """,
        {"x": x, "y": y},
    )
    page.wait_for_timeout(wait_ms)


def _click_ring_visual(page, x: int, y: int, wait_ms: int = 450) -> None:
    _move_cursor_visual(page, x, y, wait_ms=120)
    page.evaluate(
        """
        ({x, y}) => {
          const ring = document.createElement('div');
          ring.className = 'recorder-click-ring';
          ring.style.transform = `translate(${x}px, ${y}px)`;
          document.body.appendChild(ring);
          window.setTimeout(() => ring.remove(), 800);
        }
        """,
        {"x": x, "y": y},
    )
    page.wait_for_timeout(wait_ms)


def _visible_text_target(page, terms: list[str], selector: str = "button, [role='button'], label, summary, [data-baseweb='select'], input, textarea, div") -> dict[str, int | str] | None:
    return page.evaluate(
        """
        ({terms, selector}) => {
          const viewportH = window.innerHeight || document.documentElement.clientHeight;
          const candidates = Array.from(document.querySelectorAll(selector));
          for (const el of candidates) {
            const r = el.getBoundingClientRect();
            const style = getComputedStyle(el);
            const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\\s+/g, ' ');
            if (!text) continue;
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
            if (r.width < 12 || r.height < 12 || r.bottom < 64 || r.top > viewportH - 58) continue;
            if (terms.some((term) => text.includes(term))) {
              return {
                text: text.slice(0, 120),
                x: Math.round(r.left + r.width / 2),
                y: Math.round(r.top + r.height / 2),
                w: Math.round(r.width),
                h: Math.round(r.height),
              };
            }
          }
          return null;
        }
        """,
        {"terms": terms, "selector": selector},
    )


def _click_text(page, terms: list[str], *, actual: bool = True, wait_ms: int = 1_100) -> bool:
    target = _visible_text_target(page, terms)
    if not target:
        return False
    x = int(target["x"])
    y = int(target["y"])
    if actual:
        _click_at(page, x, y)
    else:
        _move_cursor(page, x, y, steps=16)
        page.wait_for_timeout(220)
        page.evaluate(
            """
            ({x, y}) => {
              const ring = document.createElement('div');
              ring.className = 'recorder-click-ring';
              ring.style.transform = `translate(${x}px, ${y}px)`;
              document.body.appendChild(ring);
              window.setTimeout(() => ring.remove(), 800);
            }
            """,
            {"x": x, "y": y},
        )
        page.wait_for_timeout(wait_ms)
    return True


def _click_text_in_selector(
    page,
    terms: list[str],
    selector: str,
    *,
    actual: bool = True,
    wait_ms: int = 1_100,
) -> bool:
    target = _visible_text_target(page, terms, selector=selector)
    if not target:
        return False
    x = int(target["x"])
    y = int(target["y"])
    if actual:
        _click_at(page, x, y)
    else:
        _move_cursor(page, x, y, steps=16)
        page.wait_for_timeout(wait_ms)
    return True


def _scroll_root_script() -> str:
    return """
    () => {
      const candidates = [
        document.querySelector('[data-testid="stMain"]'),
        document.querySelector('section.main'),
        document.querySelector('main'),
        document.scrollingElement,
        document.documentElement,
        document.body
      ].filter(Boolean);
      let best = candidates[0];
      let bestRange = -1;
      for (const el of candidates) {
        const range = Math.max(0, el.scrollHeight - el.clientHeight);
        if (range > bestRange) {
          best = el;
          bestRange = range;
        }
      }
      return best;
    }
    """


def _scroll_to_top(page) -> None:
    page.evaluate(
        """
        (rootScript) => {
          const root = eval(rootScript)();
          window.scrollTo(0, 0);
          for (const el of [root, document.scrollingElement, document.documentElement, document.body]) {
            if (el) el.scrollTop = 0;
          }
        }
        """,
        _scroll_root_script(),
    )
    page.wait_for_timeout(700)


def _scroll_metrics(page) -> dict[str, int]:
    return page.evaluate(
        """
        (rootScript) => {
          const root = eval(rootScript)();
          const scrollTop = root === document.body || root === document.documentElement || root === document.scrollingElement
            ? Math.round(window.scrollY || root.scrollTop || 0)
            : Math.round(root.scrollTop);
          return {
            y: scrollTop,
            max: Math.round(Math.max(0, root.scrollHeight - root.clientHeight))
          };
        }
        """,
        _scroll_root_script(),
    )


def _smooth_scroll_to_fraction(page, fraction: float, duration_ms: int) -> None:
    fraction = max(0.0, min(1.0, fraction))
    metrics = _scroll_metrics(page)
    start = metrics["y"]
    target = int(metrics["max"] * fraction)
    if metrics["max"] <= 0 or abs(target - start) < 4:
        page.wait_for_timeout(min(max(duration_ms, 250), 1_000))
        return

    segments = max(2, min(10, int(duration_ms / 1_000)))
    segment_wait = max(120, int(duration_ms / segments))
    for step in range(1, segments + 1):
        t = step / segments
        eased = 2 * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 2) / 2
        y = int(start + (target - start) * eased)
        page.evaluate(
            """
            ({rootScript, y}) => {
              const root = eval(rootScript)();
              const isWindowRoot = root === document.body || root === document.documentElement || root === document.scrollingElement;
              if (isWindowRoot) {
                document.documentElement.style.scrollBehavior = 'smooth';
                document.body.style.scrollBehavior = 'smooth';
                window.scrollTo({top: y, behavior: 'smooth'});
              } else {
                root.style.scrollBehavior = 'smooth';
                root.scrollTo({top: y, behavior: 'smooth'});
              }
            }
            """,
            {"rootScript": _scroll_root_script(), "y": y},
        )
        page.wait_for_timeout(segment_wait)


def _smooth_scroll_to_bottom(page, duration_ms: int) -> None:
    _smooth_scroll_to_fraction(page, 1.0, duration_ms)
    page.wait_for_timeout(1_000)


def _jump_scroll_to_fraction(page, fraction: float, wait_ms: int = 900) -> None:
    fraction = max(0.0, min(1.0, fraction))
    page.evaluate(
        """
        ({rootScript, fraction}) => {
          const root = eval(rootScript)();
          const isWindowRoot = root === document.body || root === document.documentElement || root === document.scrollingElement;
          const y = Math.max(0, Math.min(root.scrollHeight - root.clientHeight, (root.scrollHeight - root.clientHeight) * fraction));
          if (isWindowRoot) window.scrollTo(0, y);
          else root.scrollTop = y;
        }
        """,
        {"rootScript": _scroll_root_script(), "fraction": fraction},
    )
    page.wait_for_timeout(wait_ms)


def _drag_first_slider(page, index: int = 0, delta: int = 120) -> bool:
    sliders = page.locator('[role="slider"], input[type="range"]')
    count = sliders.count()
    if count <= index:
        return False
    box = sliders.nth(index).bounding_box()
    if not box:
        return False
    x = int(box["x"] + box["width"] / 2)
    y = int(box["y"] + box["height"] / 2)
    _move_cursor(page, x, y, steps=14)
    page.wait_for_timeout(200)
    page.mouse.down()
    page.mouse.move(x + delta, y, steps=28)
    page.mouse.up()
    page.wait_for_timeout(1_000)
    return True


def _open_first_selectbox(page) -> bool:
    selectors = page.locator('[role="combobox"], div[data-baseweb="select"]')
    if selectors.count() == 0:
        return False
    box = selectors.first.bounding_box()
    if not box:
        return False
    x = int(box["x"] + min(box["width"] - 20, box["width"] * 0.75))
    y = int(box["y"] + box["height"] / 2)
    _click_at(page, x, y)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(280)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1_200)
    return True


def _drag_map_surface(page) -> bool:
    target_box = page.evaluate(
        """
        () => {
          const selectors = ['.mapboxgl-canvas', 'canvas', 'iframe', '[data-testid="stIFrame"]'];
          for (const selector of selectors) {
            for (const el of Array.from(document.querySelectorAll(selector))) {
              const r = el.getBoundingClientRect();
              const style = getComputedStyle(el);
              if (
                style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                Number(style.opacity || 1) !== 0 &&
                r.width > 240 &&
                r.height > 180 &&
                r.bottom > 80 &&
                r.top < window.innerHeight - 80
              ) {
                return {
                  x: Math.round(r.left),
                  y: Math.round(r.top),
                  width: Math.round(r.width),
                  height: Math.round(r.height)
                };
              }
            }
          }
          return null;
        }
        """
    )
    if target_box is None:
        target_box = {"x": 260, "y": 360, "width": 1240, "height": 520}

    x0 = int(target_box["x"] + target_box["width"] * 0.56)
    y0 = int(target_box["y"] + target_box["height"] * 0.54)
    x1 = int(target_box["x"] + target_box["width"] * 0.38)
    y1 = int(target_box["y"] + target_box["height"] * 0.42)
    x2 = int(target_box["x"] + target_box["width"] * 0.64)
    y2 = int(target_box["y"] + target_box["height"] * 0.62)
    _move_cursor(page, x0, y0, steps=8)
    page.mouse.down()
    page.mouse.move(x1, y1, steps=8)
    page.mouse.move(x2, y2, steps=8)
    page.mouse.up()
    page.wait_for_timeout(500)
    page.mouse.wheel(0, -320)
    page.wait_for_timeout(700)
    return True


def _animate_map_surface_visual(page) -> None:
    box = page.evaluate(
        """
        () => {
          const selectors = ['.mapboxgl-canvas', 'canvas', 'iframe', '[data-testid="stIFrame"]'];
          for (const selector of selectors) {
            for (const el of Array.from(document.querySelectorAll(selector))) {
              const r = el.getBoundingClientRect();
              const style = getComputedStyle(el);
              if (
                style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                Number(style.opacity || 1) !== 0 &&
                r.width > 240 &&
                r.height > 180 &&
                r.bottom > 80 &&
                r.top < window.innerHeight - 80
              ) {
                const target = el.closest('[data-testid="stIFrame"], .stDeckGlJsonChart, .element-container, [data-testid="stElementContainer"]') || el;
                target.dataset.recorderMapTarget = '1';
                target.style.transformOrigin = '50% 50%';
                target.style.willChange = 'transform';
                target.style.transition = 'transform 1800ms cubic-bezier(.2,.8,.2,1)';
                return {
                  x: Math.round(r.left),
                  y: Math.round(r.top),
                  width: Math.round(r.width),
                  height: Math.round(r.height)
                };
              }
            }
          }
          return null;
        }
        """
    )
    if not box:
        box = {"x": 260, "y": 280, "width": 1220, "height": 620}
    cx = int(box["x"] + box["width"] * 0.56)
    cy = int(box["y"] + box["height"] * 0.54)
    _move_cursor_visual(page, cx, cy, wait_ms=500)
    for transform, wait_ms in [
        ("translate(-18px, -10px) scale(1.035)", 2_100),
        ("translate(22px, 12px) scale(1.06)", 2_100),
        ("translate(0px, 0px) scale(1.02)", 2_100),
    ]:
        page.evaluate(
            """
            (transform) => {
              const target = document.querySelector('[data-recorder-map-target="1"]');
              if (target) target.style.transform = transform;
            }
            """,
            transform,
        )
        page.wait_for_timeout(wait_ms)


def _scroll_map_into_view(page) -> bool:
    _move_cursor(page, 1500, 760, steps=10)
    page.mouse.wheel(0, 650)
    page.wait_for_timeout(1_200)
    try:
        page.wait_for_selector("iframe, canvas, [data-testid='stIFrame']", timeout=6_000)
    except PlaywrightTimeoutError:
        return False

    positioned = page.evaluate(
        """
        () => {
          const el = document.querySelector('iframe, canvas, [data-testid="stIFrame"]');
          const main = document.querySelector('[data-testid="stMain"], section.main, main');
          if (!el || !main) return false;
          const r = el.getBoundingClientRect();
          main.scrollTo({top: Math.max(0, main.scrollTop + r.top - 230), behavior: 'smooth'});
          return true;
        }
        """
    )
    page.wait_for_timeout(1_800)
    if positioned:
        return True

    for _ in range(3):
        _wheel_down(page, amount=650, ticks=1)
    return True


def _safe_click_targets(page) -> list[dict[str, int | str]]:
    return page.evaluate(
        """
        () => {
          const unsafe = ['运行', '导出', '生成', '渲染', '下载', '上传', '删除', '清空', '发送', '一键', '选择文件'];
          const selector = 'button, [role="button"], summary, input[type="checkbox"], input[type="radio"]';
          const seen = new Set();
          return Array.from(document.querySelectorAll(selector)).filter((el) => {
            const r = el.getBoundingClientRect();
            const style = getComputedStyle(el);
            const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\\s+/g, ' ');
            if (!text) return false;
            if (unsafe.some((word) => text.includes(word))) return false;
            if (String(el.className).includes('apple-')) return false;
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
            if (r.width < 16 || r.height < 16 || r.bottom < 70 || r.top > window.innerHeight - 84) return false;
            const key = `${Math.round(r.left)}:${Math.round(r.top)}:${text}`;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
          }).slice(0, 8).map((el) => {
            const r = el.getBoundingClientRect();
            return {
              text: (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 80),
              x: Math.round(r.left + r.width / 2),
              y: Math.round(r.top + r.height / 2),
              w: Math.round(r.width),
              h: Math.round(r.height),
            };
          });
        }
        """
    )


def _click_visible_controls(page, limit: int = 2) -> int:
    clicked = 0
    for target in _safe_click_targets(page):
        if clicked >= limit:
            break
        x = int(target["x"])
        y = int(target["y"])
        _click_at(page, x, y)
        clicked += 1
    return clicked


def _wheel_down(page, amount: int = 680, ticks: int = 1) -> None:
    for _ in range(ticks):
        _move_cursor(page, 1540, 760, steps=14)
        page.mouse.wheel(0, amount)
        page.wait_for_timeout(850)


def _custom_scene_actions(page, scene: dict[str, str | int], seconds: int) -> bool:
    route = str(scene.get("route", ""))
    code = str(scene.get("code", ""))

    if code == "00":
        print("  scene 00 action: smooth homepage scroll", flush=True)
        _scroll_to_top(page)
        _show_cursor(page, 1660, 180)
        _move_cursor(page, 1660, 180, steps=28)
        page.wait_for_timeout(1_400)
        _smooth_scroll_to_bottom(page, max(18_000, (seconds - 8) * 1_000))
        _move_cursor(page, 1520, 760, steps=42)
        page.wait_for_timeout(2_000)
        return True

    if "3D现状全息底座" in route or code == "03":
        start = time.time()
        print("  scene 03 action: map layer cues and 3D drag", flush=True)
        _jump_scroll_to_fraction(page, 0.52, wait_ms=1_500)
        for x, y in [(1520, 270), (1520, 335), (1520, 400), (1520, 465)]:
            _click_ring_visual(page, x, y, wait_ms=420)
        print("  scene 03 action: map surface into view", flush=True)
        _jump_scroll_to_fraction(page, 0.58, wait_ms=1_200)
        print("  scene 03 action: visual map animation", flush=True)
        _animate_map_surface_visual(page)
        page.wait_for_timeout(2_500)
        remaining = seconds - int(time.time() - start) - 1
        if remaining > 0:
            page.wait_for_timeout(min(remaining, 6) * 1_000)
        return True

    if code == "05" or "设计策略" in route:
        start = time.time()
        print("  scene 05 action: multi-agent negotiation walkthrough", flush=True)
        _scroll_to_top(page)
        _show_cursor(page, 1660, 180)
        _move_cursor(page, 1380, 180, steps=28)
        page.wait_for_timeout(1_200)
        _click_text(page, ["DeepSeek 模型"], actual=False, wait_ms=900)
        _click_text(page, ["决策倾向"], actual=False, wait_ms=900)
        _click_text(page, ["启用政策合规校验"], actual=False, wait_ms=900)
        _click_text_in_selector(page, ["空间数据约束"], "summary, button, [role='button']", actual=True, wait_ms=1_000)
        _click_text_in_selector(page, ["政策合规校验", "RAG"], "summary, button, [role='button']", actual=True, wait_ms=1_200)
        _smooth_scroll_to_fraction(page, 0.38, 12_000)
        _click_text(page, ["传统卡片视角"], actual=True, wait_ms=1_100)
        _smooth_scroll_to_fraction(page, 0.70, 10_000)
        _click_text(page, ["交互式博弈沙盘"], actual=True, wait_ms=1_600)
        _smooth_scroll_to_bottom(page, 9_000)

        page.goto(_route_url("/设计策略?sub=📊 共识雷达"), wait_until="domcontentloaded")
        _install_capture_css(page)
        _wait_for_page_stable(page, "动态共识雷达")
        _scroll_to_top(page)
        _move_cursor(page, 1460, 260, steps=30)
        page.wait_for_timeout(1_200)
        _smooth_scroll_to_fraction(page, 0.62, 12_000)

        page.goto(_route_url("/设计策略?sub=📐 设计纲领提炼"), wait_until="domcontentloaded")
        _install_capture_css(page)
        _wait_for_page_stable(page, "设计纲领提炼")
        _scroll_to_top(page)
        _click_text(page, ["设计依据"], actual=False, wait_ms=900)
        _smooth_scroll_to_fraction(page, 0.58, 8_000)
        remaining = seconds - int(time.time() - start) - 1
        if remaining > 0:
            _smooth_scroll_to_bottom(page, min(remaining * 1_000, 12_000))
        return True

    if "总体城市设计" in route:
        _click_text(page, ["空间数据概览"], actual=True)
        _click_text(page, ["评估此方案的影响"], actual=False, wait_ms=1_200)
        _wheel_down(page, amount=520, ticks=1)
        for slider_index in range(3):
            _drag_first_slider(page, slider_index, delta=90 if slider_index % 2 == 0 else -70)
        return False

    if "重点地段深化" in route:
        _open_first_selectbox(page)
        _wheel_down(page, amount=620, ticks=1)
        _click_text(page, ["推演", "控规指标"], actual=False, wait_ms=1_100)
        _click_text(page, ["人群画像"], actual=False, wait_ms=900)
        return False

    if "AIGC设计推演" in route:
        _click_text(page, ["重点地块"], actual=True)
        _click_text(page, ["用地类型"], actual=True)
        _click_text(page, ["启用深度图约束"], actual=True)
        _drag_first_slider(page, 0, delta=110)
        _drag_first_slider(page, 1, delta=-80)
        _click_text(page, ["预览约束图", "深度图"], actual=True)
        _click_text(page, ["显示实时渲染"], actual=True)
        _wheel_down(page, amount=620, ticks=2)
        _click_text(page, ["AI 润色提示词"], actual=False, wait_ms=1_000)
        return False

    if "成果表达" in route:
        _open_first_selectbox(page)
        _wheel_down(page, amount=680, ticks=1)
        _click_text(page, ["AI 智能编写说明", "指标"], actual=False, wait_ms=1_000)
        _click_text(page, ["一键代码绘图", "组装图纸"], actual=False, wait_ms=1_000)
        return False

    return False


def _interact_scene(page, scene: dict[str, str | int]) -> None:
    seconds = int(scene["seconds"])
    max_scroll = _scroll_metrics(page)["max"]
    _show_cursor(page)
    page.wait_for_timeout(1_600)
    _move_cursor(page, 1260, 190, steps=26)
    page.wait_for_timeout(900)
    if _custom_scene_actions(page, scene, seconds):
        return
    _click_visible_controls(page, limit=1)
    if max_scroll < 220:
        _move_cursor(page, 1180, 680, steps=50)
        page.wait_for_timeout(max(1_000, (seconds - 5) * 1_000))
        return

    end_time = time.time() + max(8, seconds - 4)
    click_budget = 5
    while time.time() < end_time:
        if click_budget > 0:
            click_budget -= _click_visible_controls(page, limit=1)
        _wheel_down(page, amount=520, ticks=1)
        metrics = _scroll_metrics(page)
        y = metrics["y"]
        max_scroll = metrics["max"]
        if y >= max_scroll - 60:
            page.wait_for_timeout(900)
            break
    page.wait_for_timeout(1_200)


def _write_storyboard() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    elapsed = 0
    lines = [
        "# 项目工作流动态录屏分镜",
        "",
        "此分镜对应 `project_workflow_live.mp4`，用于后期配音。",
        "",
    ]
    scenes = _selected_scenes()
    for scene in scenes:
        start = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        elapsed += int(scene["seconds"])
        end = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        lines.append(f"- `{start}-{end}` {scene['code']} {scene['title']}：{scene['cue']}")
    (OUT_DIR / "workflow_video_storyboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _detect_content_start(video_path: Path, probe_dir: Path) -> float:
    """Find the first frame after the blank Streamlit loading state.

    The visible recorder cursor is injected only after the target page has
    loaded and engine warnings have been hidden. We trim until that cursor is
    visible, so route-change white screens and startup warnings do not remain in
    the final video.
    """
    if probe_dir.exists():
        shutil.rmtree(probe_dir)
    probe_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-t",
            "18",
            "-vf",
            "fps=2,scale=480:-1",
            str(probe_dir / "frame_%04d.png"),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    frames = sorted(probe_dir.glob("frame_*.png"))
    fallback_start = 0.0
    for idx, frame_path in enumerate(frames):
        with Image.open(frame_path).convert("RGB") as rgb_image:
            width, height = rgb_image.size
            cursor_crop = rgb_image.crop((int(width * 0.78), 55, width, int(height * 0.28)))
            cursor_small = cursor_crop.resize((220, 90))
            cursor_pixels = list(cursor_small.getdata())
            cursor_blue_ratio = sum(1 for r, g, b in cursor_pixels if b > 145 and 70 < g < 170 and r < 80) / len(cursor_pixels)
            cursor_present = cursor_blue_ratio > 0.0007

            gray = rgb_image.convert("L")
            stat = ImageStat.Stat(gray)
            mean = stat.mean[0]
            stddev = stat.stddev[0]
            small = gray.resize((160, 90))
            pixels = list(small.getdata())
            dark_ratio = sum(1 for value in pixels if value < 120) / len(pixels)
            non_white_ratio = sum(1 for value in pixels if value < 238) / len(pixels)

        if not fallback_start:
            looks_blank = mean > 235 and stddev < 11 and dark_ratio < 0.006
            has_page_content = stddev > 13 or dark_ratio > 0.012 or non_white_ratio > 0.10
            if has_page_content and not looks_blank:
                fallback_start = max(0.0, idx / 2 - 0.20)

        if cursor_present:
            return max(0.0, idx / 2 - 0.20)
    return fallback_start


def _trim_scene(raw_path: Path, segment_path: Path, scene_index: int) -> float:
    trim_start = _detect_content_start(raw_path, PROBE_DIR / f"scene_{scene_index:02d}")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{trim_start:.2f}",
            "-i",
            str(raw_path),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(segment_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return trim_start


def _concat_segments(segment_paths: list[Path], mp4_path: Path) -> None:
    concat_file = OUT_DIR / "concat_segments.txt"
    concat_file.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in segment_paths) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(mp4_path),
        ],
        check=True,
    )


def _retrim_existing_recordings() -> None:
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)
    if PROBE_DIR.exists():
        shutil.rmtree(PROBE_DIR)
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    for old_segment in SEGMENT_DIR.glob("*.mp4"):
        old_segment.unlink()
    segment_paths: list[Path] = []
    for index, raw_path in enumerate(sorted(RAW_DIR.glob("scene_*.webm")), start=1):
        scene_segment_path = SEGMENT_DIR / f"scene_{index:02d}.mp4"
        trim_start = _trim_scene(raw_path, scene_segment_path, index)
        print(f"RETRIM scene {index:02d}: {trim_start:.2f}s", flush=True)
        segment_paths.append(scene_segment_path)
    if not segment_paths:
        raise RuntimeError(f"No raw scene recordings found in {RAW_DIR}")
    _concat_segments(segment_paths, OUT_DIR / "project_workflow_live.mp4")


def _convert_to_mp4(webm_path: Path, mp4_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(webm_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(mp4_path),
        ],
        check=True,
    )


def _prewarm_project(browser) -> None:
    prewarm_ms = int(os.environ.get("PREWARM_MS", "30000"))
    if prewarm_ms <= 0:
        return
    print(f"Prewarming project for {prewarm_ms / 1000:.0f}s before recording...", flush=True)
    context = browser.new_context(
        viewport={"width": WIDTH, "height": HEIGHT},
        device_scale_factor=1,
    )
    page = context.new_page()
    page.set_default_timeout(90_000)
    page.goto(_route_url("/"), wait_until="domcontentloaded")
    _install_capture_css(page)
    _wait_for_page_stable(page, str(SCENES[0]["expected"]))
    _scroll_to_top(page)
    page.wait_for_timeout(prewarm_ms)
    context.close()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)
    _write_storyboard()

    if os.environ.get("RETRIM_ONLY") == "1":
        _retrim_existing_recordings()
        return

    mp4_path = OUT_DIR / "project_workflow_live.mp4"
    scenes = _selected_scenes()

    for path in [mp4_path]:
        if path.exists():
            path.unlink()
    for directory in [RAW_DIR, SEGMENT_DIR, PROBE_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        _prewarm_project(browser)
        total = len(scenes)
        segment_paths: list[Path] = []
        for index, scene in enumerate(scenes, start=1):
            print(f"SCENE {index}/{total}: {scene['title']}", flush=True)
            context = browser.new_context(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=1,
                record_video_dir=str(RAW_DIR),
                record_video_size={"width": WIDTH, "height": HEIGHT},
            )
            page = context.new_page()
            page.set_default_timeout(90_000)
            page.goto(_route_url(str(scene["route"])), wait_until="domcontentloaded")
            _install_capture_css(page)
            _wait_for_page_stable(page, str(scene["expected"]))
            _hide_engine_warning(page)
            _scroll_to_top(page)
            _interact_scene(page, scene)
            video = page.video
            context.close()
            raw_video_path = Path(video.path())
            scene_raw_path = RAW_DIR / f"scene_{index:02d}.webm"
            shutil.move(str(raw_video_path), str(scene_raw_path))
            scene_segment_path = SEGMENT_DIR / f"scene_{index:02d}.mp4"
            trim_start = _trim_scene(scene_raw_path, scene_segment_path, index)
            print(f"  trimmed {trim_start:.2f}s loading/blank lead-in", flush=True)
            segment_paths.append(scene_segment_path)

        browser.close()

    print("Concatenating trimmed scene recordings...", flush=True)
    _concat_segments(segment_paths, mp4_path)
    print(f"MP4: {mp4_path}", flush=True)


if __name__ == "__main__":
    start = time.time()
    main()
    print(f"Done in {time.time() - start:.1f}s", flush=True)
