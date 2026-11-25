"""Chuyển docs/KICH_BAN_THUYET_TRINH.md sang docs/KICH_BAN_THUYET_TRINH.docx.

Hỗ trợ đúng các cú pháp Markdown mà kịch bản dùng: tiêu đề #/##/###, đoạn văn, trích dẫn (> lời thoại),
danh sách -, 1., danh sách lồng, bảng |...|, khối lệnh ``` và định dạng **đậm**, *nghiêng*, `mã`.
Chạy: python docs/build_kich_ban_docx.py
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SRC = Path(__file__).with_name("KICH_BAN_THUYET_TRINH.md")
OUT = SRC.with_suffix(".docx")
FONT, CODE_FONT = "Times New Roman", "Consolas"
BLUE, GREY = RGBColor(0x00, 0x52, 0x9C), RGBColor(0x55, 0x55, 0x55)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(2.5), Cm(2), Cm(2), Cm(2)


def set_font(style_or_run, name=FONT, size=None):
    f = style_or_run.font
    f.name = name
    rpr = style_or_run.element.get_or_add_rPr()
    rf = rpr.get_or_add_rFonts()
    for k in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):  # theme fonts would override the name
        rf.attrib.pop(qn(f"w:{k}"), None)
    for k in ("ascii", "hAnsi", "eastAsia", "cs"):
        rf.set(qn(f"w:{k}"), name)
    if size:
        f.size = Pt(size)


normal = doc.styles["Normal"]
set_font(normal, size=13)
normal.paragraph_format.space_after = Pt(4)
normal.paragraph_format.line_spacing = 1.15
for name, size in (("Title", 20), ("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 13)):
    st = doc.styles[name]
    set_font(st, size=size)
    st.font.bold = True
    st.font.color.rgb = BLUE
    st.paragraph_format.space_before = Pt(12 if name != "Heading 3" else 8)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.keep_with_next = True

INLINE = re.compile(r"(\*\*(.+?)\*\*|`([^`]+)`|\*([^*]+)\*)")


def add_inline(par, text, bold=False, italic=False, color=None):
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            r = par.add_run(text[pos:m.start()]); r.bold = bold or None; r.italic = italic or None
            if color: r.font.color.rgb = color
        if m.group(2) is not None:
            add_inline(par, m.group(2), bold=True, italic=italic, color=color)
        elif m.group(3) is not None:
            r = par.add_run(m.group(3)); set_font(r, CODE_FONT, 11); r.bold = bold or None
        else:
            add_inline(par, m.group(4), bold=bold, italic=True, color=color)
        pos = m.end()
    if pos < len(text):
        r = par.add_run(text[pos:]); r.bold = bold or None; r.italic = italic or None
        if color: r.font.color.rgb = color


def shade(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def left_border(par, color="0070C0"):
    ppr = par._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr"); left = OxmlElement("w:left")
    for k, v in (("val", "single"), ("sz", "18"), ("space", "8"), ("color", color)):
        left.set(qn(f"w:{k}"), v)
    bdr.append(left); ppr.append(bdr)


def add_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    ncol = max(len(r) for r in cells)
    t = doc.add_table(rows=len(cells), cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, r in enumerate(cells):
        for j in range(ncol):
            cell = t.cell(i, j)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            add_inline(p, r[j] if j < len(r) else "", bold=(i == 0))
            for run in p.runs:
                run.font.size = Pt(12)
            if i == 0:
                shade(cell, "DCE6F2")
    hdr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); hdr.append(th)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_code(lines, indent):
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6 + indent)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(line); set_font(r, CODE_FONT, 10)
        ppr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "F2F2F2")
        ppr.append(shd)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


lines = SRC.read_text(encoding="utf-8").splitlines()
i, first_h1 = 0, True
while i < len(lines):
    line = lines[i]
    s = line.strip()
    if not s or s == "---":
        i += 1
        continue
    if s.startswith("```"):
        indent = (len(line) - len(line.lstrip())) / 3 * 0.6
        j = i + 1
        while not lines[j].strip().startswith("```"):
            j += 1
        add_code([l.strip() for l in lines[i + 1:j]], indent)
        i = j + 1
        continue
    if s.startswith("|"):
        j = i
        while j < len(lines) and lines[j].strip().startswith("|"):
            j += 1
        add_table(lines[i:j])
        i = j
        continue
    m = re.match(r"^(#{1,3}) (.+)$", s)
    if m:
        level = len(m.group(1))
        if level == 1 and first_h1:
            p = doc.add_paragraph(style="Title"); add_inline(p, m.group(2)); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            first_h1 = False
        else:
            p = doc.add_paragraph(style=f"Heading {level}")
            # Mỗi phần lớn (Phân vai, Lời thoại, Demo, Câu hỏi) bắt đầu ở trang mới.
            if level == 2 and m.group(2) != "Phân vai":
                p.paragraph_format.page_break_before = True
            add_inline(p, m.group(2))
        i += 1
        continue
    if s.startswith(">"):
        # Lời thoại: gom các dòng > liên tiếp; dòng "> " trống tách đoạn.
        block = []
        while i < len(lines) and lines[i].strip().startswith(">"):
            block.append(lines[i].strip()[1:].strip()); i += 1
        paras, cur = [], []
        for b in block:
            if b: cur.append(b)
            elif cur: paras.append(" ".join(cur)); cur = []
        if cur: paras.append(" ".join(cur))
        for text in paras:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_after = Pt(6)
            left_border(p)
            add_inline(p, text)
        continue
    m = re.match(r"^(\s*)([-*]|\d+\.) (.+)$", line)
    if m:
        depth = len(m.group(1)) // 2
        if m.group(2)[0].isdigit():
            # Numbers are written as text so each list restarts at its own first number.
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.9 + 0.6 * depth)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            p.paragraph_format.space_after = Pt(2)
            add_inline(p, m.group(2) + " " + m.group(3))
        else:
            p = doc.add_paragraph(style="List Bullet" + (" 2" if depth else ""))
            p.paragraph_format.space_after = Pt(2)
            add_inline(p, m.group(3))
        i += 1
        continue
    # Đoạn văn thường; dòng chỉ có thao tác in nghiêng thì in màu xám.
    p = doc.add_paragraph()
    italic_only = re.fullmatch(r"\*[^*].*\*", s) is not None
    add_inline(p, s, color=GREY if italic_only else None)
    i += 1

# Số trang ở chân trang.
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
for kind, text in (("begin", None), ("instr", " PAGE "), ("end", None)):
    r = footer.add_run()
    if kind == "instr":
        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = text; r._r.append(it)
    else:
        fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), kind); r._r.append(fc)

doc.save(OUT)
print(OUT)
