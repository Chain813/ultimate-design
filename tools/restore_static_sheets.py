import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS_DIR = ROOT / "static" / "atlas"
BACKUP_DIR = ROOT / "static" / "atlas_backup"

sys.path.append(str(ROOT))
from scripts.rename_atlas_sheets import MAPPING_RULES

PROGRAMMATIC_CODES = {
    # Cover & TOC
    "DR-001", "DR-002",
    # Chapter 1
    "DR-003", "DR-004", "DR-005", "DR-006", "DR-007", "DR-008", "DR-009",
    # Chapter 2
    "DR-010", "DR-011", "DR-012", "DR-013", "DR-014", "DR-015", "DR-016", "DR-017", "DR-018", "DR-019", "DR-020", "DR-021", "DR-022", "DR-023", "DR-024",
    # Chapter 3
    "DR-025", "DR-026", "DR-027", "DR-028", "DR-029", "DR-030", "DR-031", "DR-032", "DR-033", "DR-034",
    # Chapter 4
    "DR-035", "DR-036", "DR-037", "DR-038", "DR-039", "DR-040", "DR-041", "DR-042", "DR-043", "DR-044", "DR-045", "DR-046", "DR-047", "DR-050", "DR-051", "DR-052", "DR-053", "DR-054", "DR-055", "DR-056", "DR-057",
    # Chapter 5
    "DR-058", "DR-059", "DR-060",
    # Key Parcels Analysis drawings (5 analysis sheets per parcel)
    # 老水产市场 (DR-062 ~ DR-066)
    "DR-062", "DR-063", "DR-064", "DR-065", "DR-066",
    # 食品调料市场 (DR-083 ~ DR-087)
    "DR-083", "DR-084", "DR-085", "DR-086", "DR-087",
    # 市一中北侧 (DR-103 ~ DR-107)
    "DR-103", "DR-104", "DR-105", "DR-106", "DR-107",
    # 清禾集贸市场 (DR-122 ~ DR-126)
    "DR-122", "DR-123", "DR-124", "DR-125", "DR-126",
    # 中国石油 (DR-140 ~ DR-144)
    "DR-140", "DR-141", "DR-142", "DR-143", "DR-144",
    # 改造前后对比图
    "DR-075", "DR-095", "DR-114", "DR-132", "DR-150",
    # Chapter 6 (Technical appendix)
    "DR-155", "DR-156", "DR-157", "DR-158"
}

def get_code_from_filename(filename):
    parts = filename.split('_')
    if parts:
        return parts[0]
    return ""

def restore_static_files():
    print(f"Scanning all files in {BACKUP_DIR}...")
    backup_files = []
    for root_dir, _dirs, files in os.walk(str(BACKUP_DIR)):
        for f in files:
            if f.lower().endswith(".png"):
                full_path = Path(root_dir) / f
                backup_files.append(full_path)
                
    print(f"Found {len(backup_files)} backup files.")
    
    restored_count = 0
    # Map rules to match files
    for old_pattern, new_name in MAPPING_RULES:
        code = get_code_from_filename(new_name)
        if code in PROGRAMMATIC_CODES:
            # Skip restoring files that are programmatically generated
            continue
            
        dst_path = ATLAS_DIR / new_name
        
        # Search in backup files
        matched_file = None
        for fpath in backup_files:
            rel_to_backup = fpath.relative_to(BACKUP_DIR).as_posix()
            if old_pattern in rel_to_backup:
                matched_file = fpath
                break
                
        if matched_file:
            print(f"Restoring static drawing: {new_name} from {matched_file.name}")
            os.makedirs(str(dst_path.parent), exist_ok=True)
            shutil.copy2(str(matched_file), str(dst_path))
            restored_count += 1
        else:
            print(f"Warning: backup pattern '{old_pattern}' not found in backup dir for {new_name}")
            
    print(f"Successfully restored {restored_count} static/AIGC files to {ATLAS_DIR}.")

if __name__ == "__main__":
    restore_static_files()
