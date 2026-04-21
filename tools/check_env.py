import os
import sys
import importlib.util
from pathlib import Path

def check_package(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return False
    return True

def main():
    project_root = Path(__file__).resolve().parents[1]
    print("="*50)
    print("  --- Project Runtime Diagnostics")
    print("="*50)
    
    print(f"\n[1/3] Checking Python version...")
    print(f"Current version: {sys.version}")
    if sys.version_info < (3, 8):
        print("[!] Warning: Python 3.8 or higher is recommended.")
    else:
        print("[OK] Python version is compatible.")

    print(f"\n[2/3] Checking core dependencies...")
    requirements_path = project_root / "requirements.txt"
    missing = []
    if requirements_path.exists():
        with requirements_path.open("r", encoding="utf-8") as f:
            for line in f:
                pkg = line.split("==")[0].strip()
                if not pkg or pkg.startswith("#"):
                    continue
                import_name = pkg.replace("-", "_")
                if pkg == "beautifulsoup4":
                    import_name = "bs4"
                if pkg == "opencv-python":
                    import_name = "cv2"
                if pkg == "pillow":
                    import_name = "PIL"
                if pkg == "scikit-learn":
                    import_name = "sklearn"
                if pkg == "webdriver-manager":
                    import_name = "webdriver_manager"
                if pkg == "python-docx":
                    import_name = "docx"
                if pkg == "pdfminer.six":
                    import_name = "pdfminer"
                if pkg == "pymupdf":
                    import_name = "fitz"
                if pkg == "python-dotenv":
                    import_name = "dotenv"
                if pkg == "streamlit-folium":
                    import_name = "streamlit_folium"
                
                if not check_package(import_name):
                    missing.append(pkg)
        
        if missing:
            print(f"[ERROR] Missing packages: {', '.join(missing)}")
            print(">>> Run: pip install -r requirements.txt")
        else:
            print("[OK] All core dependencies are installed.")
    else:
        print("[!] requirements.txt not found, skipping dependency check.")

    print(f"\n[3/3] Checking critical data files...")
    critical_files = [
        "app.py",
        "src/engines/core_engine.py",
        "src/ui/ui_components.py",
        "src/engines/spider_engine.py",
        "src/engines/cv_semantic_engine.py",
        "tools/run_deeplabv3.py",
        "pages/1_数据底座与规划策略.py",
        "pages/2_数字孪生与全息诊断.py",
        "pages/3_AIGC设计推演.py",
        "pages/4_LLM博弈决策.py",
        "src/utils/geo_transform.py",
    ]
    
    missing_files = []
    for f in critical_files:
        if not (project_root / f).exists():
            missing_files.append(f)
            
    if missing_files:
        print(f"[ERROR] Missing critical files:")
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

if __name__ == "__main__":
    main()
