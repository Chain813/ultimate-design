# scripts/build_portable_env.py
import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
PYTHON_EMBED_DIR = DIST_DIR / "python_embed"

PYTHON_ZIP_URL = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

PORTABLE_REQUIREMENTS = [
    "streamlit==1.55.0",
    "pandas==2.3.3",
    "pydeck==0.9.1",
    "openpyxl==3.1.5",
    "requests==2.32.3",
    "plotly==6.6.0",
    "pillow==11.3.0",
    "numpy>=1.26.0",
    "jieba==0.42.1",
    "folium==0.20.0",
    "geopandas==1.1.3",
    "streamlit-folium==0.22.1",
    "python-dotenv==1.0.1",
    "PyYAML==6.0.2",
    "pywebview==6.2.1",
    "shapely>=2.0",
    "rasterio>=1.3",
    "fiona>=1.9",
    "pyproj>=3.6",
    "osmnx>=1.0",
    "beautifulsoup4==4.12.3",
    "mammoth==1.8.0",
    "python-docx==1.1.2",
    "lxml==5.3.0",
    "pdfminer.six==20240706",
    "pypdf==5.0.1",
    "pymupdf==1.24.11"
]

def main():
    print("=== Step 1: Creating target directories ===")
    DIST_DIR.mkdir(exist_ok=True)
    if PYTHON_EMBED_DIR.exists():
        print(f"Cleaning existing directory: {PYTHON_EMBED_DIR}")
        shutil.rmtree(PYTHON_EMBED_DIR)
    PYTHON_EMBED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download portable Python zip
    zip_path = DIST_DIR / "python-3.12.3-embed-amd64.zip"
    if not zip_path.exists():
        print(f"Downloading Python embed from {PYTHON_ZIP_URL}...")
        urllib.request.urlretrieve(PYTHON_ZIP_URL, zip_path)
    else:
        print("Using cached Python zip.")

    # 2. Extract portable Python zip
    print(f"Extracting Python embed to {PYTHON_EMBED_DIR}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(PYTHON_EMBED_DIR)

    # 3. Download get-pip.py
    get_pip_path = DIST_DIR / "get-pip.py"
    if not get_pip_path.exists():
        print(f"Downloading get-pip.py from {GET_PIP_URL}...")
        urllib.request.urlretrieve(GET_PIP_URL, get_pip_path)
    else:
        print("Using cached get-pip.py.")

    # 4. Modify python312._pth to enable 'import site'
    pth_file = PYTHON_EMBED_DIR / "python312._pth"
    if pth_file.exists():
        print("Modifying python312._pth to enable site-packages...")
        content = pth_file.read_text(encoding="utf-8")
        # Uncomment 'import site' if commented out
        new_content = []
        for line in content.splitlines():
            if "import site" in line:
                new_content.append("import site")
            else:
                new_content.append(line)
        # Add app directory root path to search paths
        new_content.append("..")
        pth_file.write_text("\n".join(new_content) + "\n", encoding="utf-8")

    # 5. Install pip inside the embed environment
    print("Installing pip inside embed environment...")
    python_exe = PYTHON_EMBED_DIR / "python.exe"
    subprocess.run([str(python_exe), str(get_pip_path)], check=True)

    # Pre-install setuptools and wheel to support source compiles of legacy packages
    print("Installing setuptools and wheel...")
    subprocess.run([str(python_exe), "-m", "pip", "install", "setuptools", "wheel"], check=True)

    # 6. Write temporary requirements file
    req_file_path = DIST_DIR / "portable_requirements.txt"
    req_file_path.write_text("\n".join(PORTABLE_REQUIREMENTS) + "\n", encoding="utf-8")

    # 7. Install requirements
    print("Installing application dependencies (this may take a few minutes)...")
    subprocess.run([
        str(python_exe), "-m", "pip", "install",
        "-r", str(req_file_path),
        "--prefer-binary",
        "--no-warn-script-location"
    ], check=True)

    # 8. Verify the installation
    print("=== Step 2: Verifying libraries ===")
    verify_code = (
        "import streamlit; "
        "import geopandas; "
        "import shapely; "
        "import pyproj; "
        "import folium; "
        "import openpyxl; "
        "print('SUCCESS: All portable dependencies verified!')"
    )
    res = subprocess.run([str(python_exe), "-c", verify_code], capture_output=True, text=True)
    print("Verification Stdout:", res.stdout)
    if res.returncode == 0:
        print("[SUCCESS] Portable python environment successfully built!")
    else:
        print("[ERROR] Verification failed!")
        print("Verification Stderr:", res.stderr)
        exit(1)

if __name__ == "__main__":
    main()
