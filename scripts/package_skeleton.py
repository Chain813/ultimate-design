"""
ultimateDESIGN 代码骨架自动打包工具。
本脚本读取项目中的 .gitignore 配置，自动提取纯净的代码结构，
剔除大体积 GIS 矢量数据、本地运行缓存、虚拟环境及敏感凭据，
最终生成用于 GitHub 上传或分发的 ZIP 压缩包。
"""

import fnmatch
import os
import zipfile
from pathlib import Path

# 定义默认忽略的目录和文件（即便 .gitignore 未包含也强制忽略）
FORCE_IGNORE_PATTERNS = [
    ".git",
    ".git/*",
    ".github",
    ".github/*",
    ".idea",
    ".idea/*",
    ".venv",
    ".venv/*",
    "venv",
    "venv/*",
    "__pycache__",
    "**/__pycache__/*",
    ".pytest_cache",
    ".pytest_cache/*",
    ".ruff_cache",
    ".ruff_cache/*",
    ".claude",
    ".claude/*",
    ".gemini",
    ".gemini/*",
    "logs",
    "logs/*",
    "output",
    "output/*",
    "scratch",
    "scratch/*",
    ".env",
    ".env.local",
    ".runtime-packages",
    ".runtime-packages/*",
    ".superpowers",
    ".superpowers/*",
    "*.zip",
    "*.rar",
    "*.tar.gz",
    "*.docx",
    "*.pptx",
    "*.pdf",
]

# 单个文件体积上限（单位：字节），默认 10MB
# 超过该体积的文件将被过滤，并生成一个同名的占位符说明文件，防止打包过重
FILE_SIZE_LIMIT_BYTES = 10 * 1024 * 1024  # 10MB

def load_gitignore_rules(root_dir: Path) -> list:
    """读取并解析根目录下的 .gitignore 文件规则"""
    rules = list(FORCE_IGNORE_PATTERNS)
    gitignore_path = root_dir / ".gitignore"
    
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 忽略空行和注释
                    if line and not line.startswith("#"):
                        # 标准化规则路径格式
                        rules.append(line)
        except Exception as e:
            print(f"[警告] 读取 .gitignore 失败: {e}，将使用内置默认忽略规则。")
            
    # 去重
    return sorted(list(set(rules)))

def should_ignore(rel_path_str: str, rules: list) -> bool:
    """判断文件/目录是否符合忽略规则（高度优化版）"""
    # 统一 Windows 路径分隔符为 /
    rel_path_str = rel_path_str.replace("\\", "/")
    parts = rel_path_str.split("/")
    
    # 1. 快速检查组件中是否包含已知的被忽略目录
    ignored_dirs = {
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache", 
        ".ruff_cache", ".claude", ".gemini", "logs", "output", 
        "scratch", ".runtime-packages", ".superpowers", ".idea", ".codegraph",
        "exhibition_boards", "extracted_images", "extracted_pptx_images", "project_video", "附件"
    }
    for p in parts:
        if p in ignored_dirs:
            return True
            
    # 2. 检查特定后缀
    ignored_exts = {".zip", ".rar", ".tar.gz", ".docx", ".pptx", ".pdf"}
    file_name = parts[-1]
    for ext in ignored_exts:
        if file_name.endswith(ext):
            return True
            
    # 3. 检查特定文件名
    ignored_names = {".env", ".env.local"}
    if file_name in ignored_names:
        return True
        
    # 4. 对 .gitignore 中加载的其他自定义规则进行 fnmatch 匹配
    for rule in rules:
        clean_rule = rule.strip("/")
        # 如果是上述已知规则，跳过（前面已处理过）
        if clean_rule in ignored_dirs or any(clean_rule.endswith(ext) for ext in ignored_exts) or clean_rule in ignored_names:
            continue
            
        if fnmatch.fnmatch(rel_path_str, clean_rule) or \
           fnmatch.fnmatch(rel_path_str, f"*/{clean_rule}") or \
           fnmatch.fnmatch(rel_path_str, f"{clean_rule}/*") or \
           any(fnmatch.fnmatch(p, clean_rule) for p in parts):
            return True
            
    return False

def package_project(root_path: Path, output_zip: Path):
    """打包项目骨架"""
    rules = load_gitignore_rules(root_path)
    print(f"[*] 已载入 {len(rules)} 条忽略匹配规则。")
    print(f"[*] 开始扫描项目目录: {root_path}")
    
    added_count = 0
    ignored_count = 0
    placeholder_count = 0
    
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(root_path):
            # 将绝对路径转为相对于项目根目录的相对路径
            rel_root = Path(root).relative_to(root_path)
            
            # 过滤并剪枝忽略的子目录，防止深入搜索（如 .venv）
            pruned_dirs = []
            for d in dirs:
                rel_dir_path = rel_root / d
                if should_ignore(str(rel_dir_path), rules):
                    ignored_count += 1
                else:
                    pruned_dirs.append(d)
            dirs[:] = pruned_dirs # 剪枝修改
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                rel_path_str = str(rel_path)
                
                # 跳过输出压缩包自身
                if output_zip.name == rel_path.name:
                    continue
                    
                # 判断文件本身是否需要忽略
                if should_ignore(rel_path_str, rules):
                    ignored_count += 1
                    continue
                    
                # 检查文件体积
                try:
                    file_size = file_path.stat().st_size
                    if file_size > FILE_SIZE_LIMIT_BYTES:
                        # 写入大文件占位说明，而不打包实际数据
                        placeholder_name = f"{rel_path_str}.placeholder.txt"
                        placeholder_content = (
                            f"Placeholder File\n"
                            f"================\n"
                            f"源文件: {rel_path_str}\n"
                            f"实际体积: {file_size / (1024 * 1024):.2f} MB\n"
                            f"状态说明: 因体积超过系统限制（10MB）或为本地 GIS 矢量大资产，已自动过滤打包。\n"
                            f"获取方法: 请从小组成员或指定数据源获取原始文件并放至对应目录下。\n"
                        )
                        zip_file.writestr(placeholder_name, placeholder_content)
                        placeholder_count += 1
                        print(f"[提示] 大文件已替换为占位符: {rel_path_str} ({file_size / (1024 * 1024):.2f} MB)")
                        continue
                except Exception as e:
                    print(f"[警告] 无法读取文件状态 {rel_path_str}: {e}")
                    
                # 将文件写入 ZIP 压缩包
                try:
                    zip_file.write(file_path, arcname=rel_path_str)
                    added_count += 1
                except Exception as e:
                    print(f"[错误] 写入 ZIP 失败 {rel_path_str}: {e}")
                    
    print("\n" + "=" * 50)
    print("打包任务圆满完成！")
    print(f"输出路径: {output_zip.absolute()}")
    print(f"成功归档文件: {added_count} 个")
    print(f"已生成大文件占位符: {placeholder_count} 个")
    print(f"依据规则排除文件: {ignored_count} 处")
    print("=" * 50)

if __name__ == "__main__":
    # 动态定位项目根目录 (scripts/package_skeleton.py 的父目录)
    project_root = Path(__file__).resolve().parent.parent
    output_archive = project_root / "ultimate_design_skeleton.zip"
    
    # 确保输出归档此前不存在，或将其清理
    if output_archive.exists():
        try:
            output_archive.unlink()
        except Exception as e:
            print(f"[错误] 清理旧归档失败: {e}")
            
    package_project(project_root, output_archive)
