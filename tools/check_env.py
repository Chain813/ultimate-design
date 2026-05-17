import sys
import importlib.util
from pathlib import Path


PACKAGE_IMPORT_NAMES = {
    "beautifulsoup4": "bs4",
    "geopandas": "geopandas",
    "opencv-python": "cv2",
    "pdfminer.six": "pdfminer",
    "pillow": "PIL",
    "pymupdf": "fitz",
    "python-docx": "docx",
    "python-dotenv": "dotenv",
    "PyYAML": "yaml",
    "scikit-learn": "sklearn",
    "streamlit-folium": "streamlit_folium",
    "webdriver-manager": "webdriver_manager",
}

def check_package(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return False
    return True


def package_import_name(package_name: str) -> str:
    return PACKAGE_IMPORT_NAMES.get(package_name, package_name.replace("-", "_"))


def main():
    project_root = Path(__file__).resolve().parents[1]
    print("="*50)
    print("  --- Project Runtime Diagnostics")
    print("="*50)

    print("\n[1/3] Checking Python version...")
    print(f"Current version: {sys.version}")
    if sys.version_info < (3, 8):
        print("[!] Warning: Python 3.8 or higher is recommended.")
    else:
        print("[OK] Python version is compatible.")

    print("\n[2/3] Checking core dependencies...")
    requirements_path = project_root / "requirements.txt"
    missing = []
    if requirements_path.exists():
        with requirements_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                import re
                pkg = re.split(r'==|>=|<=|>|<|~=', line)[0].strip()
                import_name = package_import_name(pkg)

                if not check_package(import_name):
                    missing.append(pkg)

        if missing:
            print(f"[ERROR] Missing packages: {', '.join(missing)}")
            print(">>> Run: pip install -r requirements.txt")
        else:
            print("[OK] All core dependencies are installed.")
    else:
        print("[!] requirements.txt not found, skipping dependency check.")

    print("\n[3/3] Checking critical data files...")
    critical_files = [
        "app.py",
        "src/engines/engine_registry.py",
        "src/ui/app_shell.py",
        "src/workflow/city_design_workflow.py",
        "src/engines/social_media_crawler.py",
        "src/engines/urban_image_segmentation.py",
        "tools/run_deeplabv3.py",
        "pages/00_数据准备.py",
        "pages/01_任务解读.py",
        "pages/02_资料收集.py",
        "pages/03_现场调研.py",
        "pages/04_现状分析.py",
        "pages/05_问题诊断.py",
        "pages/06_目标定位.py",
        "pages/07_设计策略.py",
        "pages/08_总体城市设计.py",
        "pages/09_专项系统设计.py",
        "pages/10_重点地段深化.py",
        "pages/11_实施路径.py",
        "pages/12_城市设计导则.py",
        "pages/13_成果表达.py",
        "pages/14_视频生成.py",
        "src/utils/geo_transform.py",
    ]

    missing_files = []
    for f in critical_files:
        if not (project_root / f).exists():
            missing_files.append(f)

    if missing_files:
        print("[ERROR] Missing critical files:")
        for mf in missing_files:
            print(f"   - {mf}")
    else:
        print("[OK] All critical files are present.")

    print("\n" + "="*50)
    if not missing and not missing_files:
        print("SUCCESS: Everything looks good! System ready.")
    else:
        print("Warning: Issues found. Please resolve them before running the app.")
    print("="*50)
    return 0 if not missing and not missing_files else 1

if __name__ == "__main__":
    sys.exit(main())
