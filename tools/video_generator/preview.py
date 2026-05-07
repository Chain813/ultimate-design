"""快速预览：生成 30 秒低分辨率预览"""

import subprocess
import sys
from pathlib import Path


def main():
    print("=== 快速预览模式 ===")
    print("生成 30 秒预览...")

    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "generate_video.py"), "low"],
        capture_output=False,
    )

    if result.returncode == 0:
        print("\n预览就绪：tools/video_generator/output/preview.mp4")
    else:
        print("\n预览生成失败。")
        sys.exit(1)


if __name__ == "__main__":
    main()
