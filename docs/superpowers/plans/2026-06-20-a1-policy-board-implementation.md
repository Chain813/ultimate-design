# A1 Policy Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fifth A1 exhibition board for policy and economic strategy, using Codex-side generated A3 policy bitmaps stored under `static/atlas/`, enhanced with Real-ESRGAN x4plus, and integrated into the existing A1 preview pipeline.

**Architecture:** Keep the existing HTML/CSS exhibition-board workflow. Add one focused content generation script for structured policy text, one focused Real-ESRGAN upscale script for generated A3 bitmaps, then add `board-05` to the existing static A1 HTML/CSS and make preview rendering count boards dynamically.

**Tech Stack:** Python, pytest, Pillow, Playwright, DeepSeek via `src.engines.llm_engine.call_llm_engine`, Codex image generation tool, local `realesrgan-ncnn-vulkan.exe`, HTML/CSS.

---

## File Structure

- Create: `tools/generate_policy_board_content.py`
  - Produces deterministic fallback policy content and optionally replaces it with DeepSeek-generated structured JSON.
  - Writes `static/atlas/policy_a3/policy_board_content.json`.

- Create: `tools/upscale_policy_a3_images.py`
  - Finds generated A3 PNGs under `static/atlas/policy_a3/generated/`.
  - Calls `tools/realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan.exe -n realesrgan-x4plus -s 4`.
  - Writes x4 outputs under `static/atlas/policy_a3/upscaled/`.

- Create: `tests/test_policy_board_content.py`
  - Unit-tests content normalization and fallback behavior without calling DeepSeek.

- Create: `tests/test_upscale_policy_a3_images.py`
  - Unit-tests Real-ESRGAN command construction and image selection without invoking GPU/Vulkan.

- Modify: `tests/test_exhibition_boards.py`
  - Update A1 count expectations from 4 to 5.
  - Add assertions for `board-05`, policy titles, and `../atlas/policy_a3/upscaled/` image references.

- Modify: `tools/render_exhibition_board_previews.py`
  - Replace hard-coded four-board output list with dynamic outputs based on `.print-board` count.

- Modify: `tools/export_a1_editable_psd_package.py`
  - Replace README text that says “4 A1 vertical PSD files” with dynamic board count language.

- Modify: `static/exhibition_boards/index.html`
  - Add `<section class="print-board board-05">`.
  - Reference the four upscaled A3 images from `../atlas/policy_a3/upscaled/`.

- Modify: `static/exhibition_boards/boards.css`
  - Add `board-05` layout styles: large left loop visual, right policy tool stack, bottom A3 strip.

- Create image assets during execution:
  - `static/atlas/policy_a3/generated/a3_policy_01_loop.png`
  - `static/atlas/policy_a3/generated/a3_policy_02_tools.png`
  - `static/atlas/policy_a3/generated/a3_policy_03_market.png`
  - `static/atlas/policy_a3/generated/a3_policy_04_residents.png`
  - `static/atlas/policy_a3/upscaled/a3_policy_01_loop_x4.png`
  - `static/atlas/policy_a3/upscaled/a3_policy_02_tools_x4.png`
  - `static/atlas/policy_a3/upscaled/a3_policy_03_market_x4.png`
  - `static/atlas/policy_a3/upscaled/a3_policy_04_residents_x4.png`

## Task 1: Policy Content Generator

**Files:**
- Create: `tools/generate_policy_board_content.py`
- Create: `tests/test_policy_board_content.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_policy_board_content.py` with:

```python
import json

from tools.generate_policy_board_content import (
    FALLBACK_POLICY_CONTENT,
    build_policy_prompt,
    normalize_policy_content,
    write_policy_content,
)


def test_build_policy_prompt_mentions_required_subjects():
    prompt = build_policy_prompt()

    assert "政府" in prompt
    assert "市场" in prompt
    assert "居民" in prompt
    assert "A3" in prompt


def test_normalize_policy_content_accepts_valid_payload():
    payload = {
        "title": "政经良性循环与实施政策策划",
        "subtitle": "政府定规则、市场做运营、居民得收益",
        "loop_nodes": [
            {"role": "政府", "title": "规则与财政引导", "body": "控规弹性与公共投入。"},
            {"role": "市场", "title": "投资与运营导入", "body": "业态更新与收益分成。"},
            {"role": "居民", "title": "参与与收益反馈", "body": "就业增收与社区基金。"},
        ],
        "policy_tools": [
            {"name": "财政奖补", "body": "首期公共空间改造补助。"},
            {"name": "租金分成", "body": "平台公司与运营方共享增量收益。"},
        ],
        "a3_sheets": [
            {"file": "a3_policy_01_loop", "title": "三方良性循环机制图", "caption": "三方权责与收益流向。", "prompt": "urban planning policy loop infographic"},
            {"file": "a3_policy_02_tools", "title": "政策工具矩阵图", "caption": "政策工具与主体矩阵。", "prompt": "policy tools matrix"},
            {"file": "a3_policy_03_market", "title": "市场运营与收益回流图", "caption": "运营收益回流。", "prompt": "market operation loop"},
            {"file": "a3_policy_04_residents", "title": "居民收益与治理反馈图", "caption": "居民收益反馈。", "prompt": "resident benefits governance loop"},
        ],
    }

    normalized = normalize_policy_content(payload)

    assert normalized["title"] == payload["title"]
    assert len(normalized["loop_nodes"]) == 3
    assert len(normalized["a3_sheets"]) == 4


def test_normalize_policy_content_falls_back_on_missing_keys():
    normalized = normalize_policy_content({"title": "incomplete"})

    assert normalized == FALLBACK_POLICY_CONTENT


def test_write_policy_content_writes_utf8_json(tmp_path):
    output = tmp_path / "policy_board_content.json"

    result = write_policy_content(output, llm_func=lambda *_args, **_kwargs: "not json")

    assert result == FALLBACK_POLICY_CONTENT
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["title"] == FALLBACK_POLICY_CONTENT["title"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest tests/test_policy_board_content.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.generate_policy_board_content'`.

- [ ] **Step 3: Implement `tools/generate_policy_board_content.py`**

Create the file with these public functions and constants:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "static" / "atlas" / "policy_a3" / "policy_board_content.json"

FALLBACK_POLICY_CONTENT: dict[str, Any] = {
    "title": "政经良性循环与实施政策策划",
    "subtitle": "以政府规则、市场运营、居民收益构建可持续更新闭环",
    "loop_nodes": [
        {
            "role": "政府",
            "title": "规则供给与财政引导",
            "body": "通过控规弹性、财政奖补、公共空间先导投入和绩效监管，降低社会资本进入门槛。",
        },
        {
            "role": "市场",
            "title": "投资导入与运营增值",
            "body": "以轻资产运营、业态导入、租金分成和品牌联营激活街区消费与长期现金流。",
        },
        {
            "role": "居民",
            "title": "民生改善与社区反馈",
            "body": "居民通过就业增收、服务改善、消费回流和社区基金共治获得直接收益并反馈治理。",
        },
    ],
    "policy_tools": [
        {"name": "财政奖补", "body": "首期公共空间、立面整治和基础设施补短板由政府资金撬动。"},
        {"name": "税费减免", "body": "对导入社区服务、文旅消费和小微商业的运营主体给予阶段性减免。"},
        {"name": "租金分成", "body": "平台公司、产权方和运营方按增量收益分成，避免一次性高租金挤出。"},
        {"name": "社区基金", "body": "从经营收益中提取固定比例进入社区基金，用于微更新和困难群体支持。"},
        {"name": "分期滚动", "body": "以示范节点带动后续地块，形成投入、运营、回收、再投入节奏。"},
        {"name": "绩效复盘", "body": "以客流、就业、租金稳定性、居民满意度和公共服务覆盖率作为复盘指标。"},
    ],
    "a3_sheets": [
        {
            "file": "a3_policy_01_loop",
            "title": "三方良性循环机制图",
            "caption": "政府、市场、居民三方权责与收益流向。",
            "prompt": "A3 urban planning competition infographic, government market residents virtuous cycle, policy flow arrows, clean white background, red teal orange navy palette, professional masterplan diagram, no small text",
        },
        {
            "file": "a3_policy_02_tools",
            "title": "政策工具矩阵图",
            "caption": "财政、税费、租金、运营、基金和绩效工具矩阵。",
            "prompt": "A3 urban policy tools matrix infographic, fiscal subsidy tax relief rent sharing PPP community fund performance review, clean grid, urban planning board style, no small text",
        },
        {
            "file": "a3_policy_03_market",
            "title": "市场运营与收益回流图",
            "caption": "业态导入、客流提升、经营收益和社区再投入链条。",
            "prompt": "A3 market operation revenue return infographic, urban renewal, business mix, footfall, rent revenue, reinvestment loop, professional planning diagram, no small text",
        },
        {
            "file": "a3_policy_04_residents",
            "title": "居民收益与治理反馈图",
            "caption": "就业、服务、空间品质、社区基金和协商治理反馈。",
            "prompt": "A3 resident benefits governance feedback infographic, jobs public service public space community fund participatory governance, urban renewal planning style, no small text",
        },
    ],
}


def build_policy_prompt() -> str:
    return (
        "请为长春伪满皇宫周边街区更新生成第五张A1展板的政策策划结构化JSON，"
        "重点关注政府、市场、居民三者之间的良性循环。必须包含title、subtitle、"
        "loop_nodes、policy_tools、a3_sheets。a3_sheets必须为4张A3小图纸，并为每张提供file、title、caption、prompt。"
    )


def _extract_json(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def normalize_policy_content(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return FALLBACK_POLICY_CONTENT
    required = {"title", "subtitle", "loop_nodes", "policy_tools", "a3_sheets"}
    if not required.issubset(payload):
        return FALLBACK_POLICY_CONTENT
    if len(payload.get("loop_nodes", [])) != 3 or len(payload.get("a3_sheets", [])) != 4:
        return FALLBACK_POLICY_CONTENT
    return payload


def write_policy_content(
    output_path: Path = OUTPUT_PATH,
    llm_func: Callable[..., str] | None = None,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] | None = None
    if llm_func is not None:
        text = llm_func(
            prompt=build_policy_prompt(),
            system_prompt="你是城市更新经济政策策划专家，只输出JSON。",
            model="deepseek-v4-pro",
        )
        payload = _extract_json(text)
    content = normalize_policy_content(payload)
    output_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    return content


def main() -> None:
    from src.engines.llm_engine import call_llm_engine

    content = write_policy_content(OUTPUT_PATH, llm_func=call_llm_engine)
    print(OUTPUT_PATH)
    print(content["title"])


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run content tests**

Run:

```powershell
pytest tests/test_policy_board_content.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate content JSON**

Run:

```powershell
python tools/generate_policy_board_content.py
```

Expected: `static/atlas/policy_a3/policy_board_content.json` exists. If DeepSeek is unavailable, it contains fallback content and the script still exits cleanly.

- [ ] **Step 6: Commit**

```powershell
git add tools/generate_policy_board_content.py tests/test_policy_board_content.py static/atlas/policy_a3/policy_board_content.json
git commit -m "feat: add A1 policy board content generator"
```

## Task 2: Real-ESRGAN Upscale Script

**Files:**
- Create: `tools/upscale_policy_a3_images.py`
- Create: `tests/test_upscale_policy_a3_images.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_upscale_policy_a3_images.py`:

```python
from pathlib import Path

from tools.upscale_policy_a3_images import (
    GENERATED_DIR,
    UPSCALED_DIR,
    build_output_path,
    build_realesrgan_command,
    iter_generated_images,
)


def test_build_output_path_adds_x4_suffix():
    source = GENERATED_DIR / "a3_policy_01_loop.png"

    assert build_output_path(source) == UPSCALED_DIR / "a3_policy_01_loop_x4.png"


def test_build_realesrgan_command_uses_x4plus_model():
    source = GENERATED_DIR / "a3_policy_01_loop.png"
    output = build_output_path(source)

    command = build_realesrgan_command(source, output)

    assert "-n" in command
    assert "realesrgan-x4plus" in command
    assert "-s" in command
    assert "4" in command
    assert str(source) in command
    assert str(output) in command


def test_iter_generated_images_finds_policy_pngs(tmp_path):
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "a3_policy_01_loop.png").write_bytes(b"png")
    (generated / "notes.txt").write_text("ignore", encoding="utf-8")

    found = list(iter_generated_images(generated))

    assert found == [generated / "a3_policy_01_loop.png"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest tests/test_upscale_policy_a3_images.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.upscale_policy_a3_images'`.

- [ ] **Step 3: Implement `tools/upscale_policy_a3_images.py`**

Create:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REALESRGAN_DIR = ROOT / "tools" / "realesrgan-ncnn-vulkan"
REALESRGAN_EXE = REALESRGAN_DIR / "realesrgan-ncnn-vulkan.exe"
GENERATED_DIR = ROOT / "static" / "atlas" / "policy_a3" / "generated"
UPSCALED_DIR = ROOT / "static" / "atlas" / "policy_a3" / "upscaled"
MODEL_NAME = "realesrgan-x4plus"


def iter_generated_images(generated_dir: Path = GENERATED_DIR) -> list[Path]:
    if not generated_dir.exists():
        return []
    return sorted(path for path in generated_dir.glob("a3_policy_*.png") if path.is_file())


def build_output_path(source: Path, upscaled_dir: Path = UPSCALED_DIR) -> Path:
    return upscaled_dir / f"{source.stem}_x4.png"


def build_realesrgan_command(source: Path, output: Path) -> list[str]:
    return [
        str(REALESRGAN_EXE),
        "-i",
        str(source),
        "-o",
        str(output),
        "-n",
        MODEL_NAME,
        "-s",
        "4",
        "-f",
        "png",
    ]


def upscale_image(source: Path) -> Path:
    if not REALESRGAN_EXE.exists():
        raise FileNotFoundError(f"Real-ESRGAN executable not found: {REALESRGAN_EXE}")
    output = build_output_path(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(build_realesrgan_command(source, output), cwd=REALESRGAN_DIR, check=True)
    return output


def upscale_all() -> list[Path]:
    outputs = []
    for source in iter_generated_images():
        outputs.append(upscale_image(source))
    return outputs


def main() -> None:
    outputs = upscale_all()
    if not outputs:
        raise SystemExit(f"No generated policy A3 images found in {GENERATED_DIR}")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run script tests**

Run:

```powershell
pytest tests/test_upscale_policy_a3_images.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add tools/upscale_policy_a3_images.py tests/test_upscale_policy_a3_images.py
git commit -m "feat: add policy A3 Real-ESRGAN upscaler"
```

## Task 3: Generate A3 Policy Bitmaps With Codex Image Generation

**Files:**
- Create image assets under `static/atlas/policy_a3/generated/`
- Create enhanced image assets under `static/atlas/policy_a3/upscaled/`

- [ ] **Step 1: Ensure directories exist**

Run:

```powershell
New-Item -ItemType Directory -Force -Path 'static\atlas\policy_a3\generated','static\atlas\policy_a3\upscaled'
```

Expected: both directories exist.

- [ ] **Step 2: Generate four A3 images using Codex image generation**

Use the image generation tool four times, one prompt per sheet. Save outputs with exact filenames:

```text
static/atlas/policy_a3/generated/a3_policy_01_loop.png
static/atlas/policy_a3/generated/a3_policy_02_tools.png
static/atlas/policy_a3/generated/a3_policy_03_market.png
static/atlas/policy_a3/generated/a3_policy_04_residents.png
```

Prompt template:

```text
A3 portrait urban planning competition board infographic, clean white and light gray background,
navy title band, red teal orange gold accent colors, professional policy diagram style,
large readable shapes, minimal tiny text, no illegible labels, no people portraits,
[SHEET-SPECIFIC-DESCRIPTION].
```

Sheet-specific descriptions:

```text
01 loop: government, market, residents virtuous cycle, three large nodes connected by circular arrows, central consensus hub, public investment, market operation, resident benefit feedback.
02 tools: policy tools matrix, rows for fiscal subsidy, tax reduction, rent sharing, light asset operation, community fund, performance review; columns for government, platform company, social capital, community, residents.
03 market: market operation and revenue return loop, business mix introduction, footfall growth, operating income, rent stabilization, community reinvestment, phased renewal timeline.
04 residents: resident benefit and governance feedback, jobs, public services, public space quality, community fund, participation council, satisfaction review loop.
```

- [ ] **Step 3: Inspect generated image dimensions**

Run:

```powershell
@'
from pathlib import Path
from PIL import Image
for path in sorted(Path('static/atlas/policy_a3/generated').glob('a3_policy_*.png')):
    with Image.open(path) as image:
        print(path.name, image.size)
'@ | python -
```

Expected: four PNGs exist and are non-empty.

- [ ] **Step 4: Run Real-ESRGAN x4plus**

Run:

```powershell
python tools/upscale_policy_a3_images.py
```

Expected: four `_x4.png` files exist under `static/atlas/policy_a3/upscaled/`.

- [ ] **Step 5: Commit generated and upscaled assets**

```powershell
git add static/atlas/policy_a3/generated static/atlas/policy_a3/upscaled
git commit -m "assets: add generated policy A3 sheets"
```

## Task 4: Exhibition Board Tests for Five Boards

**Files:**
- Modify: `tests/test_exhibition_boards.py`

- [ ] **Step 1: Update failing tests for fifth board**

Change `test_exhibition_board_html_defines_four_a1_portrait_boards` to:

```python
def test_exhibition_board_html_defines_five_a1_portrait_boards():
    html = (BOARD_DIR / "index.html").read_text(encoding="utf-8")

    assert html.count('class="print-board') == 5
    assert "鎶€鏈€昏緫涓庡钩鍙版灦鏋? in html
    assert "鎬讳綋瑙勫垝鍥惧唽鎴愭灉" in html
    assert "浜斾釜閲嶇偣鍦板潡娣卞寲" in html
    assert "涓撻」鍒嗘瀽涓庡疄鏂芥敮鎾? in html
    assert "政经良性循环与实施政策策划" in html
```

Add:

```python
def test_exhibition_board_05_uses_policy_a3_upscaled_atlas_sources():
    board_05 = _board_html("board-05")

    assert "政经良性循环与实施政策策划" in board_05
    assert board_05.count("../atlas/policy_a3/upscaled/") == 4
    for name in [
        "a3_policy_01_loop_x4.png",
        "a3_policy_02_tools_x4.png",
        "a3_policy_03_market_x4.png",
        "a3_policy_04_residents_x4.png",
    ]:
        assert f'../atlas/policy_a3/upscaled/{name}' in board_05
```

Update `test_exhibition_board_competition_layout_is_dense_and_structured`:

```python
assert html.count('class="print-board') == 5
assert html.count('class="board-number"') == 5
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest tests/test_exhibition_boards.py -q
```

Expected: FAIL because `board-05` does not exist yet.

- [ ] **Step 3: Do not commit yet**

Keep these failing tests staged only after implementation in Task 5.

## Task 5: Add Board 05 HTML/CSS

**Files:**
- Modify: `static/exhibition_boards/index.html`
- Modify: `static/exhibition_boards/boards.css`
- Modify: `tests/test_exhibition_boards.py`

- [ ] **Step 1: Add `board-05` HTML before `</main>`**

Insert a new section after `board-04`:

```html
    <section class="print-board board-05">
      <header class="board-title">
        <div>
          <p class="project-label">POLICY & ECONOMIC STRATEGY / IMPLEMENTATION LOOP</p>
          <h1>政经良性循环与实施政策策划</h1>
          <p class="subtitle">以政府规则供给、市场运营增值和居民收益反馈构建街区更新的长期自我造血机制。</p>
        </div>
        <span class="board-number">05</span>
      </header>

      <div class="policy-board-layout">
        <section class="policy-loop-hero" aria-label="政府市场居民良性循环">
          <div class="loop-center">
            <b>良性循环</b>
            <span>投入 · 运营 · 收益 · 共治</span>
          </div>
          <article class="loop-node loop-government">
            <b>政府</b>
            <h2>规则供给与财政引导</h2>
            <p>控规弹性、财政奖补、公共空间先导投入和绩效监管，降低社会资本进入门槛。</p>
          </article>
          <article class="loop-node loop-market">
            <b>市场</b>
            <h2>投资导入与运营增值</h2>
            <p>以轻资产运营、业态导入、租金分成和品牌联营激活街区消费与长期现金流。</p>
          </article>
          <article class="loop-node loop-residents">
            <b>居民</b>
            <h2>民生改善与社区反馈</h2>
            <p>居民通过就业增收、服务改善、消费回流和社区基金共治获得直接收益并反馈治理。</p>
          </article>
        </section>

        <aside class="policy-toolkit">
          <h2>经济政策工具箱</h2>
          <p>以公共投入撬动市场运营，以增量收益反哺社区服务，形成可持续更新资金池。</p>
          <div class="policy-tool-list">
            <div><b>财政奖补</b><span>首期公共空间、立面整治和基础设施补短板由政府资金撬动。</span></div>
            <div><b>税费减免</b><span>对社区服务、文旅消费和小微商业运营主体给予阶段性减免。</span></div>
            <div><b>租金分成</b><span>平台公司、产权方和运营方按增量收益分成，避免高租金挤出。</span></div>
            <div><b>社区基金</b><span>从经营收益中提取固定比例，用于微更新和困难群体支持。</span></div>
            <div><b>分期滚动</b><span>以示范节点带动后续地块，形成投入、运营、回收、再投入节奏。</span></div>
            <div><b>绩效复盘</b><span>以客流、就业、租金稳定性、居民满意度和服务覆盖率复盘。</span></div>
          </div>
        </aside>

        <section class="policy-a3-strip" aria-label="政策A3小图纸">
          <figure class="policy-a3-tile">
            <img src="../atlas/policy_a3/upscaled/a3_policy_01_loop_x4.png" alt="三方良性循环机制图">
            <figcaption>三方良性循环机制图</figcaption>
          </figure>
          <figure class="policy-a3-tile">
            <img src="../atlas/policy_a3/upscaled/a3_policy_02_tools_x4.png" alt="政策工具矩阵图">
            <figcaption>政策工具矩阵图</figcaption>
          </figure>
          <figure class="policy-a3-tile">
            <img src="../atlas/policy_a3/upscaled/a3_policy_03_market_x4.png" alt="市场运营与收益回流图">
            <figcaption>市场运营与收益回流图</figcaption>
          </figure>
          <figure class="policy-a3-tile">
            <img src="../atlas/policy_a3/upscaled/a3_policy_04_residents_x4.png" alt="居民收益与治理反馈图">
            <figcaption>居民收益与治理反馈图</figcaption>
          </figure>
        </section>
      </div>
    </section>
```

- [ ] **Step 2: Add `board-05` CSS**

Append before `@media print`:

```css
.policy-board-layout {
  height: 737mm;
  padding-top: 8mm;
  display: grid;
  grid-template-columns: 1.12fr 0.88fr;
  grid-template-rows: 475mm 252mm;
  gap: 6mm;
}

.policy-loop-hero {
  position: relative;
  grid-column: 1;
  grid-row: 1;
  min-height: 0;
  background: var(--panel);
  border: 0.45mm solid var(--line-strong);
  border-top: 3mm solid var(--red);
  overflow: hidden;
}

.policy-loop-hero::before {
  content: "";
  position: absolute;
  inset: 42mm;
  border: 8mm solid rgba(201, 154, 46, 0.88);
  border-radius: 50%;
}

.loop-center {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 95mm;
  height: 95mm;
  transform: translate(-50%, -50%);
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 3mm;
  color: #fff;
  background: var(--navy);
}

.loop-center b {
  font-size: 21pt;
  line-height: 1;
}

.loop-center span {
  font-size: 8.4pt;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.78);
}

.loop-node {
  position: absolute;
  width: 145mm;
  padding: 7mm;
  color: #fff;
  background: var(--navy);
}

.loop-node b {
  display: inline-grid;
  place-items: center;
  min-width: 22mm;
  height: 12mm;
  margin-bottom: 4mm;
  background: rgba(255, 255, 255, 0.18);
  font-size: 10pt;
}

.loop-node h2 {
  color: #fff;
  font-size: 15pt;
}

.loop-node p {
  margin-top: 3mm;
  color: rgba(255, 255, 255, 0.78);
  font-size: 8.2pt;
  line-height: 1.48;
}

.loop-government {
  left: 18mm;
  top: 24mm;
  border-left: 4mm solid var(--red);
}

.loop-market {
  right: 18mm;
  top: 180mm;
  border-left: 4mm solid var(--teal);
}

.loop-residents {
  left: 60mm;
  bottom: 28mm;
  border-left: 4mm solid var(--orange);
}

.policy-toolkit {
  grid-column: 2;
  grid-row: 1;
  padding: 8mm;
  background: var(--panel);
  border: 0.45mm solid var(--line-strong);
  border-top: 3mm solid var(--teal);
}

.policy-toolkit > p {
  margin-top: 4mm;
  color: var(--muted);
  font-size: 9pt;
  line-height: 1.5;
}

.policy-tool-list {
  margin-top: 7mm;
  display: grid;
  grid-template-rows: repeat(6, 1fr);
  gap: 4mm;
  height: 382mm;
}

.policy-tool-list div {
  padding: 5mm;
  background: #f7f9fa;
  border-left: 3mm solid var(--blue);
}

.policy-tool-list div:nth-child(2) {
  border-left-color: var(--teal);
}

.policy-tool-list div:nth-child(3) {
  border-left-color: var(--orange);
}

.policy-tool-list div:nth-child(4) {
  border-left-color: var(--gold);
}

.policy-tool-list div:nth-child(5) {
  border-left-color: var(--green);
}

.policy-tool-list div:nth-child(6) {
  border-left-color: var(--red);
}

.policy-tool-list b {
  display: block;
  margin-bottom: 2mm;
  font-size: 11.4pt;
}

.policy-tool-list span {
  display: block;
  color: var(--muted);
  font-size: 7.8pt;
  line-height: 1.35;
}

.policy-a3-strip {
  grid-column: 1 / 3;
  grid-row: 2;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4mm;
  min-height: 0;
}

.policy-a3-tile {
  background: var(--panel);
  border-top: 2.4mm solid var(--red);
}

.policy-a3-tile:nth-child(2) {
  border-top-color: var(--blue);
}

.policy-a3-tile:nth-child(3) {
  border-top-color: var(--teal);
}

.policy-a3-tile:nth-child(4) {
  border-top-color: var(--orange);
}

.policy-a3-tile figcaption {
  padding: 1.8mm 2.2mm;
  font-size: 6.8pt;
  line-height: 1.15;
}
```

- [ ] **Step 3: Run board tests**

Run:

```powershell
pytest tests/test_exhibition_boards.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add tests/test_exhibition_boards.py static/exhibition_boards/index.html static/exhibition_boards/boards.css
git commit -m "feat: add fifth A1 policy exhibition board"
```

## Task 6: Dynamic Preview Renderer and PSD README

**Files:**
- Modify: `tools/render_exhibition_board_previews.py`
- Modify: `tools/export_a1_editable_psd_package.py`

- [ ] **Step 1: Update preview renderer**

Replace `SINGLE_OUTPUTS` with:

```python
def build_single_outputs(count: int) -> list[Path]:
    return [BOARD_DIR / f"a1_board_{index:02d}_preview.png" for index in range(1, count + 1)]
```

Update `render_previews()`:

```python
        boards = page.locator(".print-board")
        count = boards.count()
        single_outputs = build_single_outputs(count)
        outputs = [*single_outputs, COMBINED_OUTPUT]
        for index, output in enumerate(single_outputs):
            boards.nth(index).screenshot(path=output)
```

Keep the final `return outputs`.

- [ ] **Step 2: Update README wording in PSD package script**

In `_write_launcher()`, compute dynamic count before `readme`:

```python
    board_count = len(json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("boards", [])) if MANIFEST_PATH.exists() else 5
```

Change README lines to:

```text
2. Photoshop will create {board_count} A1 vertical PSD files in:
```

and:

```text
- A1_Board_01_editable_text.psd ... A1_Board_{board_count:02d}_editable_text.psd
```

- [ ] **Step 3: Run focused tests**

Run:

```powershell
pytest tests/test_exhibition_boards.py::test_exhibition_board_competition_layout_is_dense_and_structured -q
```

Expected: PASS.

- [ ] **Step 4: Render previews**

Run:

```powershell
python tools/render_exhibition_board_previews.py
```

Expected output includes:

```text
static\exhibition_boards\a1_board_05_preview.png
static\exhibition_boards\a1_boards_competition_preview.png
```

- [ ] **Step 5: Commit**

```powershell
git add tools/render_exhibition_board_previews.py tools/export_a1_editable_psd_package.py static/exhibition_boards/a1_board_05_preview.png static/exhibition_boards/a1_boards_competition_preview.png
git commit -m "feat: render five A1 exhibition board previews"
```

## Task 7: Final Verification

**Files:**
- Read/verify generated previews and assets.

- [ ] **Step 1: Run unit tests**

Run:

```powershell
pytest tests/test_policy_board_content.py tests/test_upscale_policy_a3_images.py tests/test_exhibition_boards.py -q
```

Expected: PASS.

- [ ] **Step 2: Verify image files exist**

Run:

```powershell
@'
from pathlib import Path
required = [
    'static/atlas/policy_a3/generated/a3_policy_01_loop.png',
    'static/atlas/policy_a3/generated/a3_policy_02_tools.png',
    'static/atlas/policy_a3/generated/a3_policy_03_market.png',
    'static/atlas/policy_a3/generated/a3_policy_04_residents.png',
    'static/atlas/policy_a3/upscaled/a3_policy_01_loop_x4.png',
    'static/atlas/policy_a3/upscaled/a3_policy_02_tools_x4.png',
    'static/atlas/policy_a3/upscaled/a3_policy_03_market_x4.png',
    'static/atlas/policy_a3/upscaled/a3_policy_04_residents_x4.png',
    'static/exhibition_boards/a1_board_05_preview.png',
]
missing = [p for p in required if not Path(p).exists()]
print('missing=', missing)
raise SystemExit(1 if missing else 0)
'@ | python -
```

Expected: `missing= []`.

- [ ] **Step 3: Visual QA**

Open or inspect:

```text
static/exhibition_boards/a1_board_05_preview.png
```

Check:

- The main loop, policy toolkit, and A3 strip are visible.
- No A3 image is stretched beyond recognition.
- Captions and policy text do not overlap.
- The fifth board visually matches the first four boards' restrained competition-board style.

- [ ] **Step 4: Final commit if verification changed files**

Only if verification generated additional files:

```powershell
git status --short
git add static/atlas/policy_a3/generated static/atlas/policy_a3/upscaled static/exhibition_boards/a1_board_05_preview.png static/exhibition_boards/a1_boards_competition_preview.png
git commit -m "chore: update A1 policy board generated outputs"
```

## Self-Review

- Spec coverage:
  - Fifth A1 board: Task 5.
  - DeepSeek/fallback content: Task 1.
  - Codex-side image generation: Task 3.
  - Real-ESRGAN x4plus: Task 2 and Task 3.
  - `static/atlas` policy bitmap location: Task 3 and Task 5.
  - Dynamic 5-board preview export: Task 6.
  - PSD README count update: Task 6.
  - Verification: Task 7.

- Placeholder scan:
  - No marker strings or unspecified implementation steps remain.

- Type consistency:
  - Generated file stems match HTML references and upscaler output names.
  - Test names match file names and paths used by implementation tasks.
