"""视频生成器：收集数据并调用 HyperFrames 渲染"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSER_DIR = Path(__file__).resolve().parent / "composer"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def run_render(quality: str = "high"):
    """调用 HyperFrames 渲染"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if quality == "low":
        cmd = ["npx", "hyperframes", "render", "--quality", "draft", "-o", "../output/preview.mp4"]
    else:
        cmd = ["npx", "hyperframes", "render", "-o", "../output/final.mp4"]

    print(f"渲染 {quality} 质量视频...")
    result = subprocess.run(cmd, cwd=COMPOSER_DIR, capture_output=True, text=True)

    if result.returncode == 0:
        output_file = "preview.mp4" if quality == "low" else "final.mp4"
        print(f"视频渲染成功：{OUTPUT_DIR / output_file}")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    else:
        print(f"渲染失败：{result.stderr}")
        sys.exit(1)


def main():
    quality = sys.argv[1] if len(sys.argv) > 1 else "high"
    print("=== UltimateDESIGN 视频生成器 ===")
    print(f"质量：{quality}")
    run_render(quality)
    print("\n完成！")


if __name__ == "__main__":
    main()
