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
