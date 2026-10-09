import base64
from io import BytesIO

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


def generate_official_word_doc(title, text_content, aigc_history=None):
    """
    使用 python-docx 纯代码生成带红头的官方公文 Word 格式，
    支持插入 Markdown 转换来的纯文本和 AIGC 推演生成的 Base64 图像。
    """
    doc = docx.Document()

    # 1. 渲染大红头
    red_head = doc.add_paragraph()
    red_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rh_run = red_head.add_run("长春市历史文化街区微更新规划专项报告")
    rh_run.font.size = Pt(22)
    rh_run.font.name = '宋体'
    rh_run.font.color.rgb = RGBColor(255, 0, 0)

    # 红线分隔符
    red_line = doc.add_paragraph()
    red_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rl_run = red_line.add_run("★")
    rl_run.font.size = Pt(14)
    rl_run.font.color.rgb = RGBColor(255, 0, 0)

    # 2. 正文标题
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.space_before = Pt(20)
    title_p.space_after = Pt(20)
    t_run = title_p.add_run(title)
    t_run.font.size = Pt(18)
    t_run.font.bold = True

    # 3. 规划文本注入
    doc.add_heading("一、 微更新规划导则文本", level=1)

    # 文本与表格分段渲染处理
    lines = text_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # 检测 Markdown 表格块
        if line.startswith('|') and line.endswith('|'):
            tbl_rows = []
            while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                row_str = lines[i].strip()
                cleaned_cells = [c.strip() for c in row_str.strip('|').split('|')]
                # 跳过对齐分隔行如 | :--- | :--- |
                if not all(set(c).issubset({'-', ':', ' '}) for c in cleaned_cells):
                    tbl_rows.append(cleaned_cells)
                i += 1

            if tbl_rows:
                num_cols = max(len(r) for r in tbl_rows)
                try:
                    tbl = doc.add_table(rows=len(tbl_rows), cols=num_cols)
                    tbl.style = 'Table Grid'
                    for r_idx, row_data in enumerate(tbl_rows):
                        for c_idx in range(num_cols):
                            cell_val = row_data[c_idx] if c_idx < len(row_data) else ""
                            cell = tbl.cell(r_idx, c_idx)
                            cell.text = cell_val
                            if r_idx == 0:
                                for cp in cell.paragraphs:
                                    for cr in cp.runs:
                                        cr.font.bold = True
                except Exception:
                    # 容错降级
                    for r_data in tbl_rows:
                        doc.add_paragraph(" | ".join(r_data))
            continue

        if line.startswith('#'):
            # 处理加粗标题
            p = doc.add_paragraph()
            run = p.add_run(line.replace('#', '').strip())
            run.font.bold = True
            run.font.size = Pt(14)
            i += 1
        elif line.startswith('-') or line.startswith('*'):
            # 处理列表
            doc.add_paragraph(line.lstrip('-* ').strip(), style='List Bullet')
            i += 1
        else:
            # 普通段落，首行缩进
            p = doc.add_paragraph(line)
            p.paragraph_format.first_line_indent = Pt(28)
            i += 1

    # 4. AIGC 成果图集注入
    if aigc_history and len(aigc_history) > 0:
        doc.add_page_break()
        doc.add_heading("二、 重点地块 AIGC 视觉推演图集", level=1)

        for idx, img_data in enumerate(aigc_history):
            try:
                doc.add_heading(f"图景 {idx+1}: {img_data.get('plot', '未命名地块')}", level=2)
                p_desc = doc.add_paragraph()
                p_desc.add_run(f"采用策略：{img_data.get('strategy', '未定')}\n").font.bold = True
                p_desc.add_run(f"核心咒语记录：{img_data.get('prompt_excerpt', '')}")

                # 解码 Base64 并插入
                if 'thumb_b64' in img_data:
                    img_bytes = base64.b64decode(img_data['thumb_b64'])
                    img_io = BytesIO(img_bytes)

                    pic_p = doc.add_paragraph()
                    pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    pic_p.add_run().add_picture(img_io, width=Inches(5.0))
            except Exception as e:
                doc.add_paragraph(f"[图片渲染失败: {e}]")

    # 5. 结尾声明
    doc.add_page_break()
    end_p = doc.add_paragraph()
    end_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    end_p.add_run("本红头文件由 ultimateDESIGN 数字孪生平台自动排版生成。").font.color.rgb = RGBColor(128, 128, 128)

    # 存入缓存
    f = BytesIO()
    doc.save(f)
    f.seek(0)
    return f


def export_statutory_dxf_bundle(gdfs, output_zip_path):
    """
    导出法定规划 CAD DXF 图纸与 GeoJSON 打包 ZIP 压缩包。
    """
    from src.utils.vector_exporter import VectorExporter
    exporter = VectorExporter()
    return exporter.export_bundle(gdfs, output_zip_path)

