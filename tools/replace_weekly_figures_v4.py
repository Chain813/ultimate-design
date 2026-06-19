# -*- coding: utf-8 -*-
import os
import shutil
import sys
import win32com.client
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

USER_HOME = os.path.expanduser("~")
DOC_PATH = os.path.join(USER_HOME, "Desktop", "陈礼冲 毕设", "毕业设计周志(开题之后).doc")
BACKUP_PATH = os.path.join(USER_HOME, "Desktop", "陈礼冲 毕设", "毕业设计周志(开题之后)_backup.doc")
ATLAS_DIR = r"e:\AI-based-project\urban-platform\static\atlas"

# We group shapes by week. For each week, we delete all shapes and insert the two images side-by-side
# at the insertion point of the first shape.
WEEKS_DATA = {
    1: {
        "shapes": [3, 4, 5, 6],
        "images": ["DR-010_数据来源与遥感现状图.png", "DR-014_建筑风貌识别图.png"]
    },
    2: {
        "shapes": [7, 8, 9],
        "images": ["DR-005_研究范围图.png", "DR-006_原始数据清单.png"]
    },
    3: {
        "shapes": [10, 11, 12],
        "images": ["DR-016_街区景观品质分析图.png", "DR-021_人群需求与老龄化分布图.png"]
    },
    4: {
        "shapes": [13, 14, 15],
        "images": ["DR-022_空间句法可达性分析图.png", "DR-024_MPI更新潜力评估图.png"]
    },
    5: {
        "shapes": [16, 17, 18],
        "images": ["DR-035_更新模式分区图.png", "DR-036_空间结构规划图.png"]
    },
    6: {
        "shapes": [19, 20, 21],
        "images": ["DR-043_道路交通系统规划图.png", "DR-044_慢行系统规划图.png"]
    },
    7: {
        "shapes": [22, 23, 24],
        "images": ["DR-026_平台核心代码清单.png", "DR-032_设计原则与理念图.png"]
    },
    8: {
        "shapes": [25, 26, 27],
        "images": ["DR-061_老水产市场_地块导引.png", "DR-067_老水产市场-改造总平面图.png"]
    },
    9: {
        "shapes": [28, 29, 30],
        "images": ["DR-088_食品调料市场-改造总平面图.png", "DR-127_清禾集贸市场-改造总平面图.png"]
    },
    10: {
        "shapes": [31, 32, 33],
        "images": ["DR-057_公众参与与博弈协商成果图.png", "DR-056_投资估算与经济测算图.png"]
    },
    11: {
        "shapes": [34, 35, 36],
        "images": ["DR-155_图册章节结构导图.png", "DR-156_数据处理管线导图.png"]
    },
    12: {
        "shapes": [37, 38, 39],
        "images": ["DR-077_老水产市场-控制性指标表.png", "DR-134_清禾集贸市场-控制性指标表.png"]
    },
    13: {
        "shapes": [40, 41, 42],
        "images": ["DR-158_城乡规划知识体系导图.png", "DR-039_用地规划指标表.png"]
    },
    14: {
        "shapes": [43, 44, 45],
        "images": ["DR-001_规划设计图册封面.png", "DR-002_图册目录.png"]
    }
}

TARGET_WIDTH = 210.0 # pt width to ensure side-by-side placement on the same row

def restore_backup():
    print(f"Restoring original document from backup: {BACKUP_PATH}")
    if os.path.exists(DOC_PATH):
        os.remove(DOC_PATH)
    shutil.copy2(BACKUP_PATH, DOC_PATH)
    print("Restore completed.")

def process_figures():
    if not os.path.exists(DOC_PATH):
        print("Error: Document does not exist.")
        return False

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    
    doc = None
    replaced_count = 0
    deleted_count = 0
    try:
        doc = word.Documents.Open(os.path.abspath(DOC_PATH))
        total_shapes = doc.InlineShapes.Count
        print(f"Document opened. Total InlineShapes: {total_shapes}")
        
        # Iterate backwards from Week 14 down to Week 1
        for week_idx in sorted(WEEKS_DATA.keys(), reverse=True):
            week = WEEKS_DATA[week_idx]
            shapes = week["shapes"]
            images = week["images"]
            
            # Check if indices exceed total shapes
            if shapes[0] > total_shapes:
                print(f"Warning: Week {week_idx} shape index {shapes[0]} exceeds total shapes ({total_shapes}). Skipping.")
                continue
                
            print(f"\nProcessing Week {week_idx}...")
            
            # Get range of the first shape in this week BEFORE deletion
            ish_first = doc.InlineShapes(shapes[0])
            rng = ish_first.Range
            
            # Delete all the shapes of this week in reverse order
            for s_idx in sorted(shapes, reverse=True):
                if s_idx <= doc.InlineShapes.Count:
                    print(f"  Deleting Shape {s_idx}...")
                    doc.InlineShapes(s_idx).Delete()
                    deleted_count += 1
                    
            # Now insert the two images side-by-side at the original range
            # Insert Image 1
            img1_name = images[0]
            img1_path = os.path.join(ATLAS_DIR, img1_name)
            with Image.open(img1_path) as im:
                im_w, im_h = im.size
            ar1 = im_w / im_h
            
            print(f"  Inserting Image 1: {img1_name}...")
            new_ish1 = doc.InlineShapes.AddPicture(
                FileName=os.path.abspath(img1_path),
                LinkToFile=False,
                SaveWithDocument=True,
                Range=rng
            )
            new_ish1.Width = TARGET_WIDTH
            new_ish1.Height = TARGET_WIDTH / ar1
            replaced_count += 1
            
            # Collapse range to the end of Image 1
            rng.Collapse(Direction=0) # 0 = wdCollapseEnd
            
            # Insert spaces separator
            rng.Text = "     "
            rng.Collapse(Direction=0)
            
            # Insert Image 2
            img2_name = images[1]
            img2_path = os.path.join(ATLAS_DIR, img2_name)
            with Image.open(img2_path) as im:
                im_w, im_h = im.size
            ar2 = im_w / im_h
            
            print(f"  Inserting Image 2: {img2_name}...")
            new_ish2 = doc.InlineShapes.AddPicture(
                FileName=os.path.abspath(img2_path),
                LinkToFile=False,
                SaveWithDocument=True,
                Range=rng
            )
            new_ish2.Width = TARGET_WIDTH
            new_ish2.Height = TARGET_WIDTH / ar2
            replaced_count += 1
            
        # Clean up empty paragraphs
        print("\nCleaning up empty paragraphs...")
        cleanup_count = 0
        for p_idx in range(doc.Paragraphs.Count, 30, -1):
            try:
                p = doc.Paragraphs(p_idx)
                text = p.Range.Text.strip()
                if not text and p.Range.InlineShapes.Count == 0:
                    p.Range.Delete()
                    cleanup_count += 1
            except Exception:
                pass
        print(f"Cleaned up {cleanup_count} empty paragraphs.")
        
        doc.Save()
        print(f"\nDocument saved successfully. Replaced/inserted {replaced_count} figures. Deleted {deleted_count} placeholders.")
        return True
    except Exception as e:
        print(f"Error occurred during replacement: {e}")
        return False
    finally:
        if doc:
            doc.Close(SaveChanges=True)
        word.Quit()

def main():
    restore_backup()
    success = process_figures()
    if success:
        print("All weekly log modifications finished successfully (exactly 2 side-by-side figures per week).")
    else:
        print("Modification task failed.")

if __name__ == "__main__":
    main()
