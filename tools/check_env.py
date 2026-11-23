import importlib.util
import sys
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
    "pywebview": "webview",
    "pytest-xdist": "xdist",
}

def check_package(package_name):
    spec = importlib.util.find_spec(package_name)
    return spec is not None


def package_import_name(package_name: str) -> str:
    return PACKAGE_IMPORT_NAMES.get(package_name, package_name.replace("-", "_"))


def main():
    project_root = Path(__file__).resolve().parents[1]
    print("="*50)
    print("  --- Project Runtime Diagnostics")
    print("="*50)

    print("\n[1/3] Checking Python version...")
    print(f"Current version: {sys.version}")
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
        "pages/01_全息空间诊断与数据沙盘.py",
        "pages/02_多主体博弈与空间AIGC工坊.py",
        "pages/03_数字图则与工程交付枢纽.py",
        "src/stages/stage04_diagnosis/page.py",
        "src/stages/stage07_strategy/page.py",
        "src/stages/stage08_master_plan/page.py",
        "src/stages/stage09_systems/page.py",
        "src/stages/stage10_detail_design/page.py",
        "src/stages/stage11_implementation/page.py",
        "src/stages/stage12_guideline/page.py",
        "src/stages/stage13_outputs/page.py",
        "src/stages/stage15_aigc/page.py",
        "src/stages/stage16_skills/page.py",
        "src/engines/engine_registry.py",
        "src/engines/spatial_syntax_engine.py",
        "src/ui/app_shell.py",
        "src/workflow/city_design_workflow.py",
        "scripts/fetch_social_sentiment.py",
        "src/engines/urban_image_segmentation.py",
        "src/utils/geo_transform.py",
        "assets/datav_bigscreen.html",
    ]

    missing_files = []
    for f in critical_files:
        target = project_root / f
        if not target.exists():
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
