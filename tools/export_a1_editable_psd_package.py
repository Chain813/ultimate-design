# -*- coding: utf-8 -*-
"""Export A1 exhibition boards as editable Photoshop source packages.

The Python PSD libraries available in this environment can write pixel layers,
but Photoshop editable text layers are best created through Photoshop's own JSX
scripting API. This script therefore creates:

1. A manifest and copied ASCII-named assets.
2. Background-only PNGs rendered from the existing HTML/CSS layout.
3. A Photoshop JSX script and one-click BAT/PowerShell launcher.
4. Optional raster-layer PSD fallbacks, where text is separate but rasterized.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image, ImageDraw, ImageFont
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer


ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = ROOT / "static" / "exhibition_boards"
HTML_PATH = BOARD_DIR / "index.html"
PACKAGE_DIR = BOARD_DIR / "psd_editable"
ASSET_DIR = PACKAGE_DIR / "assets"
OUTPUT_DIR = PACKAGE_DIR / "output"
MANIFEST_PATH = PACKAGE_DIR / "a1_editable_manifest.json"
JSX_PATH = PACKAGE_DIR / "generate_a1_psd.jsx"
BAT_PATH = PACKAGE_DIR / "generate_a1_psd.bat"
PS1_PATH = PACKAGE_DIR / "run_photoshop_jsx.ps1"
README_PATH = PACKAGE_DIR / "README.txt"

A1_WIDTH_MM = 594
A1_HEIGHT_MM = 841
TARGET_DPI = 150
BOARD_WIDTH_PX = round(A1_WIDTH_MM / 25.4 * TARGET_DPI)
BOARD_HEIGHT_PX = round(A1_HEIGHT_MM / 25.4 * TARGET_DPI)

TEXT_SELECTORS = ",".join(
    [
        ".board-title .project-label",
        ".board-title h1",
        ".board-title .subtitle",
        ".board-number",
        ".tech-ribbon b",
        ".tech-ribbon em",
        ".tech-proof-panel h2",
        ".tech-proof-panel > p",
        ".proof-card b",
        ".proof-card span",
        ".proof-metrics span",
        ".strategy-column h2",
        ".strategy-column > p",
        ".metric-strip span",
        ".parcel-name b",
        ".parcel-name h2",
        ".parcel-name p",
        "figcaption",
    ]
)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=max(8, size))
    return ImageFont.load_default()


def _safe_name(value: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return value[:80] or fallback


def _path_from_file_url(url: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "file":
        raise ValueError(f"Expected file URL, got {url}")
    path = unquote(parsed.path)
    if re.match(r"^/[A-Za-z]:/", path):
        path = path[1:]
    return Path(path)


def _rgb_to_hex(css_color: str) -> str:
    nums = [int(float(n)) for n in re.findall(r"[\d.]+", css_color)]
    if len(nums) >= 3:
        return f"#{nums[0]:02x}{nums[1]:02x}{nums[2]:02x}"
    return "#101827"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _copy_image_asset(src_url: str, board_index: int, image_index: int) -> str:
    source = _path_from_file_url(src_url)
    suffix = source.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
        suffix = ".png"
    name = f"board{board_index:02d}_img_{image_index:03d}{suffix}"
    target = ASSET_DIR / name
    if source.suffix.lower() == suffix:
        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)
    else:
        with Image.open(source) as image:
            image.convert("RGBA").save(target)
    return target.as_posix()


def _scaled_rect(rect: dict[str, float], scale: float) -> dict[str, int]:
    return {
        "x": round(rect["x"] * scale),
        "y": round(rect["y"] * scale),
        "w": round(rect["w"] * scale),
        "h": round(rect["h"] * scale),
    }


def _collect_layout() -> dict:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for old in ASSET_DIR.glob("*"):
        old.unlink()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": 2400, "height": 3350},
            device_scale_factor=BOARD_WIDTH_PX / 2246,
        )
        page.goto(HTML_PATH.as_uri())
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "() => Array.from(document.images).every((img) => img.complete && img.naturalWidth > 0)"
        )

        boards_raw = page.evaluate(
            """
            (textSelectors) => Array.from(document.querySelectorAll('.print-board')).map((board, boardIndex) => {
              const br = board.getBoundingClientRect();
              const rel = (r) => ({ x: r.left - br.left, y: r.top - br.top, w: r.width, h: r.height });
              const images = Array.from(board.querySelectorAll('figure img')).map((img, i) => {
                const figure = img.closest('figure') || img;
                const r = figure.getBoundingClientRect();
                const cs = getComputedStyle(img);
                return {
                  index: i + 1,
                  src: img.currentSrc || img.src,
                  alt: img.getAttribute('alt') || '',
                  fit: cs.objectFit || 'contain',
                  rect: rel(r)
                };
              });

              const seen = new Set();
              const texts = [];
              Array.from(board.querySelectorAll(textSelectors)).forEach((el) => {
                if (seen.has(el)) return;
                seen.add(el);
                const value = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
                if (!value) return;
                const r = el.getBoundingClientRect();
                if (r.width < 2 || r.height < 2) return;
                const cs = getComputedStyle(el);
                const fontSize = parseFloat(cs.fontSize) || 12;
                const lineHeight = parseFloat(cs.lineHeight) || fontSize * 1.25;
                texts.push({
                  index: texts.length + 1,
                  tag: el.tagName.toLowerCase(),
                  className: el.className || '',
                  text: value,
                  rect: rel(r),
                  fontSize,
                  lineHeight,
                  fontWeight: cs.fontWeight || '400',
                  color: cs.color || 'rgb(16,24,39)',
                  textAlign: cs.textAlign || 'left'
                });
              });
              return { index: boardIndex + 1, cssWidth: br.width, cssHeight: br.height, images, texts };
            })
            """,
            TEXT_SELECTORS,
        )

        page.add_style_tag(
            content="""
            .print-board * {
              color: transparent !important;
              text-shadow: none !important;
            }
            .print-board img,
            .print-board canvas,
            .print-board iframe,
            .print-board video {
              visibility: hidden !important;
            }
            """
        )

        boards_locator = page.locator(".print-board")
        boards: list[dict] = []
        for raw in boards_raw:
            board_index = int(raw["index"])
            bg_path = ASSET_DIR / f"board{board_index:02d}_layout_background.png"
            boards_locator.nth(board_index - 1).screenshot(path=bg_path)
            with Image.open(bg_path) as bg:
                width, height = bg.size
            scale = width / float(raw["cssWidth"])

            images = []
            for item in raw["images"]:
                local_file = _copy_image_asset(item["src"], board_index, int(item["index"]))
                images.append(
                    {
                        "name": _safe_name(item.get("alt") or f"image_{item['index']}", f"image_{item['index']}"),
                        "file": local_file,
                        "fit": item.get("fit", "contain"),
                        "rect": _scaled_rect(item["rect"], scale),
                    }
                )

            texts = []
            for item in raw["texts"]:
                rect = _scaled_rect(item["rect"], scale)
                if rect["w"] <= 1 or rect["h"] <= 1:
                    continue
                texts.append(
                    {
                        "name": _safe_name(item.get("text", "")[:24], f"text_{item['index']}"),
                        "text": item["text"],
                        "rect": rect,
                        "fontSize": max(8, round(float(item["fontSize"]) * scale, 1)),
                        "lineHeight": max(9, round(float(item["lineHeight"]) * scale, 1)),
                        "fontWeight": str(item.get("fontWeight", "400")),
                        "color": _rgb_to_hex(item.get("color", "")),
                        "align": item.get("textAlign", "left"),
                    }
                )

            boards.append(
                {
                    "index": board_index,
                    "name": f"A1_Board_{board_index:02d}",
                    "width": width,
                    "height": height,
                    "dpi": TARGET_DPI,
                    "background": bg_path.as_posix(),
                    "psd": (OUTPUT_DIR / f"A1_Board_{board_index:02d}_editable_text.psd").as_posix(),
                    "rasterPsd": (OUTPUT_DIR / f"A1_Board_{board_index:02d}_raster_layers.psd").as_posix(),
                    "images": images,
                    "texts": texts,
                }
            )

        browser.close()

    manifest = {
        "sourceHtml": HTML_PATH.as_posix(),
        "packageDir": PACKAGE_DIR.as_posix(),
        "outputDir": OUTPUT_DIR.as_posix(),
        "dpi": TARGET_DPI,
        "a1SizeMm": {"width": A1_WIDTH_MM, "height": A1_HEIGHT_MM},
        "boards": boards,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _fit_image(source: Image.Image, rect: dict[str, int], fit: str) -> Image.Image:
    source = source.convert("RGBA")
    rw, rh = max(1, rect["w"]), max(1, rect["h"])
    sw, sh = source.size
    scale = max(rw / sw, rh / sh) if fit == "cover" else min(rw / sw, rh / sh)
    nw, nh = max(1, round(sw * scale)), max(1, round(sh * scale))
    resized = source.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    canvas.alpha_composite(resized, ((rw - nw) // 2, (rh - nh) // 2))
    return canvas


def _text_to_image(item: dict) -> Image.Image:
    rect = item["rect"]
    w, h = max(1, rect["w"]), max(1, rect["h"])
    image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = _font(round(item["fontSize"]), int(item.get("fontWeight", "400")) >= 700)
    fill = (*_hex_to_rgb(item["color"]), 255)
    words = item["text"].split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= w or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    y = 0
    for line in lines[: max(1, math.floor(h / max(1, item["lineHeight"])) + 1)]:
        draw.text((0, y), line, font=font, fill=fill)
        y += item["lineHeight"]
    return image


def _write_raster_psd(manifest: dict) -> None:
    for board in manifest["boards"]:
        psd = PSDImage.new(mode="RGB", size=(board["width"], board["height"]), color=(255, 255, 255))
        background = Image.open(board["background"]).convert("RGBA")
        psd.append(PixelLayer.frompil(background, psd, "00_layout_background", top=0, left=0))

        for index, image_item in enumerate(board["images"], start=1):
            with Image.open(image_item["file"]) as source:
                fitted = _fit_image(source, image_item["rect"], image_item.get("fit", "contain"))
            rect = image_item["rect"]
            layer_name = f"01_image_{index:03d}_{image_item['name']}"
            psd.append(PixelLayer.frompil(fitted, psd, layer_name[:120], top=rect["y"], left=rect["x"]))

        for index, text_item in enumerate(board["texts"], start=1):
            rendered = _text_to_image(text_item)
            rect = text_item["rect"]
            layer_name = f"02_text_{index:03d}_{text_item['name']}"
            psd.append(PixelLayer.frompil(rendered, psd, layer_name[:120], top=rect["y"], left=rect["x"]))

        psd.save(board["rasterPsd"])


def _jsx_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _write_jsx(manifest: dict) -> None:
    manifest_js = json.dumps(manifest, ensure_ascii=False, indent=2).replace("\\", "/")
    jsx = f"""#target photoshop
app.displayDialogs = DialogModes.NO;

var MANIFEST = {manifest_js};

function solid(hex) {{
  var c = new SolidColor();
  hex = hex.replace('#', '');
  c.rgb.red = parseInt(hex.substr(0, 2), 16);
  c.rgb.green = parseInt(hex.substr(2, 2), 16);
  c.rgb.blue = parseInt(hex.substr(4, 2), 16);
  return c;
}}

function boundsPx(layer) {{
  var b = layer.bounds;
  return {{
    left: b[0].as('px'),
    top: b[1].as('px'),
    right: b[2].as('px'),
    bottom: b[3].as('px')
  }};
}}

function placeFile(path) {{
  var desc = new ActionDescriptor();
  desc.putPath(charIDToTypeID('null'), new File(path));
  executeAction(charIDToTypeID('Plc '), desc, DialogModes.NO);
  return app.activeDocument.activeLayer;
}}

function addRectMask(doc, r) {{
  try {{
    doc.selection.select([[r.x, r.y], [r.x + r.w, r.y], [r.x + r.w, r.y + r.h], [r.x, r.y + r.h]]);
    var desc = new ActionDescriptor();
    desc.putClass(charIDToTypeID('Nw  '), charIDToTypeID('Chnl'));
    var ref = new ActionReference();
    ref.putEnumerated(charIDToTypeID('Chnl'), charIDToTypeID('Chnl'), charIDToTypeID('Msk '));
    desc.putReference(charIDToTypeID('At  '), ref);
    desc.putEnumerated(charIDToTypeID('Usng'), charIDToTypeID('UsrM'), charIDToTypeID('RvlS'));
    executeAction(charIDToTypeID('Mk  '), desc, DialogModes.NO);
    doc.selection.deselect();
  }} catch (e) {{
    try {{ doc.selection.deselect(); }} catch (_) {{}}
  }}
}}

function fitLayer(layer, r, fitMode) {{
  var b = boundsPx(layer);
  var lw = Math.max(1, b.right - b.left);
  var lh = Math.max(1, b.bottom - b.top);
  var scale = fitMode === 'cover' ? Math.max(r.w / lw, r.h / lh) : Math.min(r.w / lw, r.h / lh);
  layer.resize(scale * 100, scale * 100, AnchorPosition.TOPLEFT);
  b = boundsPx(layer);
  lw = Math.max(1, b.right - b.left);
  lh = Math.max(1, b.bottom - b.top);
  layer.translate(r.x + (r.w - lw) / 2 - b.left, r.y + (r.h - lh) / 2 - b.top);
}}

function moveInto(layer, group) {{
  try {{ layer.move(group, ElementPlacement.INSIDE); }} catch (e) {{}}
}}

function addTextLayer(doc, group, item) {{
  var layer = doc.artLayers.add();
  layer.name = ('TXT_' + item.name).substr(0, 120);
  layer.kind = LayerKind.TEXT;
  var t = layer.textItem;
  t.kind = TextType.PARAGRAPHTEXT;
  t.contents = item.text;
  t.size = UnitValue(item.fontSize, 'px');
  t.width = UnitValue(item.rect.w, 'px');
  t.height = UnitValue(Math.max(item.rect.h, item.fontSize * 1.4), 'px');
  t.position = [UnitValue(item.rect.x, 'px'), UnitValue(item.rect.y + item.fontSize * 0.90, 'px')];
  t.color = solid(item.color);
  try {{
    t.font = parseInt(item.fontWeight, 10) >= 700 ? 'MicrosoftYaHei-Bold' : 'MicrosoftYaHei';
  }} catch (e) {{
    try {{ t.font = parseInt(item.fontWeight, 10) >= 700 ? 'SimHei' : 'MicrosoftYaHei'; }} catch (_) {{}}
  }}
  if (item.align === 'center') t.justification = Justification.CENTER;
  else if (item.align === 'right') t.justification = Justification.RIGHT;
  else t.justification = Justification.LEFT;
  moveInto(layer, group);
}}

function makeBoard(board) {{
  var doc = app.documents.add(
    UnitValue(board.width, 'px'),
    UnitValue(board.height, 'px'),
    board.dpi,
    board.name,
    NewDocumentMode.RGB,
    DocumentFill.WHITE
  );

  var backgroundGroup = doc.layerSets.add();
  backgroundGroup.name = '00_layout_background';
  var imageGroup = doc.layerSets.add();
  imageGroup.name = '01_replaceable_images';
  var textGroup = doc.layerSets.add();
  textGroup.name = '02_editable_text';

  var bg = placeFile(board.background);
  bg.name = 'layout_background';
  fitLayer(bg, {{x: 0, y: 0, w: board.width, h: board.height}}, 'cover');
  moveInto(bg, backgroundGroup);

  for (var i = 0; i < board.images.length; i++) {{
    var item = board.images[i];
    var layer = placeFile(item.file);
    layer.name = ('IMG_' + (i + 1) + '_' + item.name).substr(0, 120);
    fitLayer(layer, item.rect, item.fit);
    addRectMask(doc, item.rect);
    moveInto(layer, imageGroup);
  }}

  for (var j = 0; j < board.texts.length; j++) {{
    addTextLayer(doc, textGroup, board.texts[j]);
  }}

  var out = new File(board.psd);
  var opts = new PhotoshopSaveOptions();
  opts.layers = true;
  opts.embedColorProfile = true;
  doc.saveAs(out, opts, true, Extension.LOWERCASE);
  doc.close(SaveOptions.DONOTSAVECHANGES);
}}

for (var b = 0; b < MANIFEST.boards.length; b++) {{
  makeBoard(MANIFEST.boards[b]);
}}

$.writeln('A1 PSD generated: ' + MANIFEST.outputDir);
"""
    JSX_PATH.write_text(jsx, encoding="utf-8-sig")


def build_readme_text(board_count: int, output_dir: Path = OUTPUT_DIR) -> str:
    first_board = "A1_Board_01"
    last_board = f"A1_Board_{board_count:02d}"
    return f"""A1 PSD editable package

One-click editable PSD:
1. Double-click generate_a1_psd.bat.
2. Photoshop will create {board_count} A1 vertical PSD files in:
   {output_dir}

Output naming:
- {first_board}_editable_text.psd ... {last_board}_editable_text.psd
  Photoshop-generated version with editable text layers.
- {first_board}_raster_layers.psd ... {last_board}_raster_layers.psd
  Python fallback version. Layers are separate, but text is rasterized.

Canvas:
- A1 portrait, {A1_WIDTH_MM}mm x {A1_HEIGHT_MM}mm
- {TARGET_DPI} dpi
- About {BOARD_WIDTH_PX}px x {BOARD_HEIGHT_PX}px

Replacement workflow:
- In Photoshop, expand 01_replaceable_images and replace the relevant smart object/image layer.
- Text is under 02_editable_text in the Photoshop-generated PSD.
- Layout background is under 00_layout_background.
"""


def _write_launcher(manifest: dict) -> None:
    ps1 = rf"""$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Jsx = Join-Path $ScriptDir "generate_a1_psd.jsx"
Write-Host "Running Photoshop JSX:" $Jsx
try {{
  $app = New-Object -ComObject Photoshop.Application
  $app.Visible = $true
  $app.DoJavaScriptFile($Jsx)
  Write-Host "Done."
}} catch {{
  Write-Host "Photoshop COM failed:" $_.Exception.Message
  Write-Host "Fallback: opening the JSX file. If Photoshop does not run it automatically, use File > Scripts > Browse and select:"
  Write-Host $Jsx
  Invoke-Item $Jsx
}}
"""
    PS1_PATH.write_text(ps1, encoding="utf-8")

    bat = rf"""@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_photoshop_jsx.ps1"
pause
"""
    BAT_PATH.write_text(bat, encoding="gbk")

    README_PATH.write_text(build_readme_text(len(manifest["boards"])), encoding="utf-8")


def main() -> None:
    manifest = _collect_layout()
    _write_jsx(manifest)
    _write_launcher(manifest)
    if os.environ.get("WRITE_RASTER_PSD") == "1":
        _write_raster_psd(manifest)
    else:
        print("Skipped raster PSD fallback. Set WRITE_RASTER_PSD=1 to generate it.", flush=True)
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Photoshop JSX: {JSX_PATH}")
    print(f"One-click BAT: {BAT_PATH}")
    print(f"Output dir: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
