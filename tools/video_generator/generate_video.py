"""视频生成器：收集项目数据并调用 HyperFrames 合成器"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSER_DIR = Path(__file__).resolve().parent / "composer"
DATA_DIR = COMPOSER_DIR / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def collect_project_data() -> dict:
    """从项目文件收集数据"""
    data = {
        "project": {
            "name": "数字孪生·古今共振",
            "subtitle": "AI赋能下的伪满皇宫周边街区更新规划设计",
            "location": "中国吉林省长春市宽城区",
            "area": "约150公顷",
        },
        "stages": {},
        "narrator_marks": [],
    }

    # 从导出的 JSON 加载阶段数据
    stage_data_dir = DATA_DIR / "stages"
    if stage_data_dir.exists():
        for json_file in sorted(stage_data_dir.glob("stage_*.json")):
            stage_code = json_file.stem.replace("stage_", "")
            try:
                stage_data = json.loads(json_file.read_text(encoding="utf-8"))
                data["stages"][stage_code] = stage_data
            except Exception as e:
                print(f"警告：无法加载 {json_file}: {e}")

    # 从 VersionStore 收集图片
    output_drawings = ROOT / "output" / "drawings"
    if output_drawings.exists():
        for drawing_dir in output_drawings.iterdir():
            if drawing_dir.is_dir():
                latest_png = sorted(drawing_dir.glob("v*.png"))
                if latest_png:
                    dest = DATA_DIR / "images" / f"{drawing_dir.name}.png"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(latest_png[-1], dest)

    return data


def export_data(data: dict):
    """导出项目数据到合成器数据目录"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / "project_data.json"
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"数据已导出到 {output_path}")


def run_composer(quality: str = "high"):
    """调用 HyperFrames 合成器"""
    if not (COMPOSER_DIR / "node_modules").exists():
        print("安装 Node.js 依赖...")
        subprocess.run(["npm", "install"], cwd=COMPOSER_DIR, check=True)

    output_file = OUTPUT_DIR / "final.mp4" if quality == "high" else OUTPUT_DIR / "preview.mp4"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"渲染 {quality} 质量视频...")
    result = subprocess.run(
        ["npx", "hyperframes", "render", "index.ts", "--output", str(output_file)],
        cwd=COMPOSER_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"视频渲染成功：{output_file}")
    else:
        print(f"渲染失败：{result.stderr}")
        sys.exit(1)


def main():
    quality = sys.argv[1] if len(sys.argv) > 1 else "high"
    print("=== UltimateDESIGN 视频生成器 ===")
    print(f"质量：{quality}")

    print("\n[1/3] 收集项目数据...")
    data = collect_project_data()

    print("[2/3] 导出数据...")
    export_data(data)

    print("[3/3] 渲染视频...")
    run_composer(quality)

    print("\n完成！")


if __name__ == "__main__":
    main()
