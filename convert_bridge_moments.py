#!/usr/bin/env python3
"""
convert_bridge_moments.py — Extract content from Bridge Moments .docx files
and generate interactive HTML pages for the NobleMind Study Tool.

Reads raw Word XML to capture paragraph borders, table shading, and formatting
that python-docx misses.

Usage: python3 convert_bridge_moments.py
"""

import zipfile
import xml.etree.ElementTree as ET
import os
import re
import json
import html as html_module

DOCX_DIR = os.path.expanduser('~/Documents/BRIDGE MOMENTS')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BridgeMoments')

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Chapter metadata — titles, part assignments, epigraph scriptures
CHAPTERS = [
    {"num": 1,  "title": "The Weight of Words", "part": 1, "part_title": "The Foundation: Why Words Matter", "subtitle": ""},
    {"num": 2,  "title": "The Kairos Principle", "part": 1, "part_title": "The Foundation: Why Words Matter", "subtitle": ""},
    {"num": 3,  "title": "Love, Not Agenda", "part": 1, "part_title": "The Foundation: Why Words Matter", "subtitle": ""},
    {"num": 4,  "title": "\u201cGive Me a Drink\u201d", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "The Woman at the Well \u2022 John 4:1\u201342"},
    {"num": 5,  "title": "\u201cYou Must Be Born Again\u201d", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "Nicodemus \u2022 John 3:1\u201321"},
    {"num": 6,  "title": "\u201cI Must Stay at Your House\u201d", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "Zacchaeus \u2022 Luke 19:1\u201310"},
    {"num": 7,  "title": "Jesus Felt a Love for Him", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "The Rich Young Ruler \u2022 Mark 10:17\u201327"},
    {"num": 8,  "title": "\u201cNeither Do I Condemn You\u201d", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "The Woman Caught in Adultery \u2022 John 8:1\u201311"},
    {"num": 9,  "title": "Were Not Our Hearts Burning?", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "The Road to Emmaus \u2022 Luke 24:13\u201335"},
    {"num": 10, "title": "\u201cFollow Me\u201d", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "The Calling of the First Disciples \u2022 John 1:35\u201351"},
    {"num": 11, "title": "\u201cDo You See This Woman?\u201d", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "Simon\u2019s House \u2022 Luke 7:36\u201350"},
    {"num": 12, "title": "\u201cDo You Love Me?\u201d", "part": 2, "part_title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "subtitle": "Peter\u2019s Restoration \u2022 John 21:1\u201319"},
    {"num": 13, "title": "\u201cDo You Understand What You Are Reading?\u201d", "part": 3, "part_title": "The Pattern Continued: Bridge Moments in Acts", "subtitle": "Philip & the Ethiopian \u2022 Acts 8:26\u201340"},
    {"num": 14, "title": "\u201cMen of Athens\u201d", "part": 3, "part_title": "The Pattern Continued: Bridge Moments in Acts", "subtitle": "Paul on Mars Hill \u2022 Acts 17:16\u201334"},
    {"num": 15, "title": "\u201cWhat Must I Do to Be Saved?\u201d", "part": 3, "part_title": "The Pattern Continued: Bridge Moments in Acts", "subtitle": "The Philippian Jailer \u2022 Acts 16:16\u201334"},
    {"num": 16, "title": "Learning to Listen", "part": 4, "part_title": "The Practice: Living with Bridge Moment Eyes", "subtitle": "Hearing What People Are Really Saying \u2022 James 1:19"},
    {"num": 17, "title": "From Natural to Spiritual", "part": 4, "part_title": "The Practice: Living with Bridge Moment Eyes", "subtitle": "Building the Bridge \u2022 1 Peter 3:15"},
    {"num": 18, "title": "Seasoned with Salt", "part": 4, "part_title": "The Practice: Living with Bridge Moment Eyes", "subtitle": "Speaking Truth with Grace \u2022 Colossians 4:6"},
    {"num": 19, "title": "When They Walk Away", "part": 4, "part_title": "The Practice: Living with Bridge Moment Eyes", "subtitle": "Handling Rejection with Grace \u2022 1 Corinthians 3:6\u20137"},
    {"num": 20, "title": "The Heart Behind the Words", "part": 4, "part_title": "The Practice: Living with Bridge Moment Eyes", "subtitle": "Love as the Only Foundation \u2022 1 Corinthians 13:1\u20133"},
]

DOCX_FILES = {
    1:  "Bridge_Moments_Chapter_01_The_Weight_of_Words.docx",
    2:  "Bridge_Moments_Chapter_02_The_Kairos_Principle.docx",
    3:  "Bridge_Moments_Chapter_03_Love_Not_Agenda.docx",
    4:  "Bridge_Moments_Chapter_04_Give_Me_A_Drink.docx",
    5:  "Bridge_Moments_Chapter_05_You_Must_Be_Born_Again.docx",
    6:  "Bridge_Moments_Chapter_06_I_Must_Stay_At_Your_House.docx",
    7:  "Bridge_Moments_Chapter_07_Jesus_Felt_A_Love_For_Him.docx",
    8:  "Bridge_Moments_Chapter_08_Neither_Do_I_Condemn_You.docx",
    9:  "Bridge_Moments_Chapter_09_Were_Not_Our_Hearts_Burning.docx",
    10: "Bridge_Moments_Chapter_10_Follow_Me.docx",
    11: "Bridge_Moments_Chapter_11_Do_You_See_This_Woman.docx",
    12: "Bridge_Moments_Chapter_12_Do_You_Love_Me.docx",
    13: "Bridge_Moments_Chapter_13_Do_You_Understand_What_You_Are_Reading.docx",
    14: "Bridge_Moments_Chapter_14_Men_of_Athens.docx",
    15: "Bridge_Moments_Chapter_15_What_Must_I_Do_To_Be_Saved.docx",
    16: "Bridge_Moments_Chapter_16_Learning_to_Listen.docx",
    17: "Bridge_Moments_Chapter_17_From_Natural_to_Spiritual.docx",
    18: "Bridge_Moments_Chapter_18_Seasoned_with_Salt.docx",
    19: "Bridge_Moments_Chapter_19_When_They_Walk_Away.docx",
    20: "Bridge_Moments_Chapter_20_The_Heart_Behind_the_Words.docx",
}

APPENDIX_FILES = {
    'a': "Bridge_Moments_Appendix_A_Quick_Reference_Chart.docx",
    'b': "Bridge_Moments_Appendix_B_Scripture_Index.docx",
    'c': "Bridge_Moments_Appendix_C_Small_Group_Exercises.docx",
}

# ─── XML PARSING HELPERS ─────────────────────────────────────────────

def get_w(elem, attr):
    """Get a w: namespaced attribute value."""
    return elem.get(f'{{{NS["w"]}}}{attr}', '')

def get_para_text(para):
    """Extract all text from a paragraph, preserving line breaks."""
    parts = []
    for child in para:
        tag = child.tag.split('}')[-1]
        if tag == 'r':
            for rc in child:
                rtag = rc.tag.split('}')[-1]
                if rtag == 't':
                    parts.append(rc.text or '')
                elif rtag == 'br':
                    parts.append('\n')
        elif tag == 'hyperlink':
            for r in child.findall('.//w:t', NS):
                parts.append(r.text or '')
    return ''.join(parts).strip()

def get_para_runs(para):
    """Extract runs with formatting info from a paragraph."""
    runs = []
    for child in para:
        tag = child.tag.split('}')[-1]
        if tag == 'r':
            rPr = child.find('w:rPr', NS)
            bold = False
            italic = False
            color = ''
            sz = ''
            if rPr is not None:
                bold = rPr.find('w:b', NS) is not None
                italic = rPr.find('w:i', NS) is not None
                c = rPr.find('w:color', NS)
                if c is not None: color = get_w(c, 'val')
                s = rPr.find('w:sz', NS)
                if s is not None: sz = get_w(s, 'val')

            text_parts = []
            has_break = False
            for rc in child:
                rtag = rc.tag.split('}')[-1]
                if rtag == 't':
                    text_parts.append(rc.text or '')
                elif rtag == 'br':
                    has_break = True
                    text_parts.append('\n')

            text = ''.join(text_parts)
            if text:
                runs.append({
                    'text': text,
                    'bold': bold,
                    'italic': italic,
                    'color': color,
                    'size': sz,
                })
        elif tag == 'hyperlink':
            for r in child.findall('.//w:t', NS):
                runs.append({'text': r.text or '', 'bold': False, 'italic': False, 'color': '', 'size': ''})
    return runs

def get_para_border_color(para):
    """Get the dominant paragraph border color."""
    pPr = para.find('w:pPr', NS)
    if pPr is None:
        return ''
    pBdr = pPr.find('w:pBdr', NS)
    if pBdr is None:
        return ''
    for side in pBdr:
        c = get_w(side, 'color')
        if c and c != 'auto':
            return c.upper()
    return ''

def get_para_style(para):
    """Get paragraph style name."""
    pPr = para.find('w:pPr', NS)
    if pPr is None:
        return ''
    pStyle = pPr.find('w:pStyle', NS)
    if pStyle is not None:
        return get_w(pStyle, 'val')
    return ''

def get_para_alignment(para):
    """Get paragraph alignment."""
    pPr = para.find('w:pPr', NS)
    if pPr is None:
        return ''
    jc = pPr.find('w:jc', NS)
    if jc is not None:
        return get_w(jc, 'val')
    return ''

def get_table_shading(tbl):
    """Get all shading fill colors from a table."""
    fills = set()
    for shd in tbl.findall('.//w:shd', NS):
        fill = get_w(shd, 'fill')
        if fill and fill != 'auto':
            fills.add(fill.upper())
    return fills

def get_table_text(tbl):
    """Get all text from a table, separated by row."""
    rows = []
    for tr in tbl.findall('.//w:tr', NS):
        cells = []
        for tc in tr.findall('.//w:tc', NS):
            cell_texts = []
            for p in tc.findall('.//w:p', NS):
                t = get_para_text(p)
                if t:
                    cell_texts.append(t)
            cells.append('\n'.join(cell_texts))
        rows.append(cells)
    return rows

def get_table_runs(tbl):
    """Get all runs from all paragraphs in a table."""
    all_runs = []
    for p in tbl.findall('.//w:p', NS):
        runs = get_para_runs(p)
        text = ''.join(r['text'] for r in runs).strip()
        if text:
            all_runs.append({'paragraph_runs': runs, 'text': text})
    return all_runs

def classify_table(tbl):
    """Classify a table as principle, bridge, exercise, study_questions, or data."""
    fills = get_table_shading(tbl)
    text_sample = ''
    for t in tbl.findall('.//w:t', NS):
        text_sample += (t.text or '') + ' '
        if len(text_sample) > 300:
            break
    text_sample = text_sample.strip()

    if 'Study & Discussion Questions' in text_sample or 'Study and Discussion Questions' in text_sample:
        return 'study_questions'

    if 'F0F4F8' in fills:
        return 'principle'
    if 'F0F5F0' in fills:
        return 'bridge'
    if 'FDF8F0' in fills:
        return 'exercise'

    # Check border colors in table paragraphs
    for p in tbl.findall('.//w:p', NS):
        bc = get_para_border_color(p)
        if bc == '2B4C7E':
            return 'principle'
        if bc == '5B8C5A':
            return 'bridge'
        if bc == '8B4513':
            return 'exercise'

    return 'data'

# ─── CONTENT EXTRACTION ──────────────────────────────────────────────

def extract_chapter(docx_path, ch_num):
    """Extract structured content from a chapter .docx file."""
    z = zipfile.ZipFile(docx_path)
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    body = root.find('.//w:body', NS)

    elements = []
    epigraph = None
    chapter_purpose = None

    for elem in body:
        tag = elem.tag.split('}')[-1]

        if tag == 'p':
            text = get_para_text(elem)
            if not text:
                continue

            style = get_para_style(elem)
            border_color = get_para_border_color(elem)
            alignment = get_para_alignment(elem)
            runs = get_para_runs(elem)

            # Detect first run properties
            first_bold = runs[0]['bold'] if runs else False
            first_italic = runs[0]['italic'] if runs else False
            first_color = runs[0]['color'].upper() if runs else ''
            first_size = runs[0]['size'] if runs else ''

            # Skip decorative dividers
            if text.startswith('───') or text.startswith('---'):
                elements.append({'type': 'divider'})
                continue

            # Part header (e.g., "PART ONE")
            if text.startswith('PART ') and alignment == 'center' and first_size == '20':
                elements.append({'type': 'part_label', 'text': text})
                continue

            # Part subtitle (italic, blue, centered)
            if first_color == '2B4C7E' and first_italic and alignment == 'center' and first_size == '26':
                elements.append({'type': 'part_subtitle', 'text': text})
                continue

            # Chapter label (e.g., "Chapter One")
            if text.startswith('Chapter ') and alignment == 'center' and first_size == '22' and first_color == '4A4A4A':
                continue  # We generate this from metadata

            # Chapter title (large, bold, blue)
            if first_bold and first_color == '2B4C7E' and first_size == '36' and alignment == 'center':
                continue  # We generate this from metadata

            # Heading 2 sections
            if style == 'Heading2' or (first_bold and first_color == '5B8C5A' and first_size == '28'):
                elements.append({'type': 'h2', 'text': text})
                continue

            # Sub-section headers (bold, brown, sz 24)
            if first_bold and first_color == '8B4513' and first_size == '24':
                elements.append({'type': 'h3', 'text': text})
                continue

            # Epigraph scripture (green border, italic)
            if border_color == '5B8C5A' and first_italic:
                if epigraph is None:
                    epigraph = text
                    elements.append({'type': 'scripture', 'text': text})
                else:
                    elements.append({'type': 'scripture', 'text': text})
                continue

            # Chapter purpose (brown border, italic)
            if border_color == '8B4513' and first_italic and chapter_purpose is None:
                chapter_purpose = text
                elements.append({'type': 'chapter_purpose', 'text': text})
                continue

            # Key Scriptures Referenced header
            if first_bold and first_color == '8B4513' and 'Key Scriptures' in text:
                elements.append({'type': 'key_scriptures_header', 'text': text})
                continue

            # Key Scriptures list (bold+italic, gray, follows the header)
            if first_bold and first_italic and first_color == '4A4A4A' and '•' in text:
                elements.append({'type': 'key_scriptures', 'text': text})
                continue

            # Regular body paragraph
            html_text = runs_to_html(runs, strip_body_emphasis=True)
            elements.append({'type': 'paragraph', 'text': text, 'html': html_text})

        elif tag == 'tbl':
            tbl_type = classify_table(elem)

            if tbl_type == 'study_questions':
                questions = extract_study_questions(elem)
                elements.append({'type': 'study_questions', 'questions': questions})
            elif tbl_type in ('principle', 'bridge', 'exercise'):
                box_html = extract_box_content(elem)
                elements.append({'type': f'{tbl_type}_box', 'html': box_html})
            else:
                # Data table
                rows = get_table_text(elem)
                elements.append({'type': 'table', 'rows': rows})

    return {
        'elements': elements,
        'epigraph': epigraph,
        'chapter_purpose': chapter_purpose,
    }

def runs_to_html(runs, strip_body_emphasis=False):
    """Convert a list of runs to HTML with formatting.

    If strip_body_emphasis is True and ALL runs are bold+italic,
    the formatting is treated as a document-wide style artifact
    and stripped (the whole paragraph was styled, not emphasized).
    """
    # Check if we should strip: all runs must be bold+italic
    if strip_body_emphasis and runs and all(r['bold'] and r['italic'] for r in runs):
        parts = []
        for r in runs:
            text = html_module.escape(r['text'])
            text = text.replace('\n', '<br>')
            parts.append(text)
        return ''.join(parts)

    parts = []
    for r in runs:
        text = html_module.escape(r['text'])
        text = text.replace('\n', '<br>')

        if r['bold'] and r['italic']:
            text = f'<strong><em>{text}</em></strong>'
        elif r['bold']:
            text = f'<strong>{text}</strong>'
        elif r['italic']:
            text = f'<em>{text}</em>'

        parts.append(text)
    return ''.join(parts)

def extract_study_questions(tbl):
    """Extract study questions from a study questions table."""
    questions = []
    for p in tbl.findall('.//w:p', NS):
        text = get_para_text(p)
        if not text:
            continue
        # Skip the header text
        if 'Study & Discussion' in text or 'Study and Discussion' in text:
            continue
        # Try to parse numbered questions (e.g., "1. question text")
        m = re.match(r'^(\d+)\.\s*(.*)', text, re.DOTALL)
        if m:
            questions.append(m.group(2).strip())
        else:
            # Non-numbered paragraph — treat as a question if it's long enough
            # (skip very short items that might be sub-labels)
            if len(text) > 30:
                questions.append(text)
            elif questions:
                # Short text appended to previous question
                questions[-1] += ' ' + text
    return questions

def extract_box_content(tbl):
    """Extract content from a callout box table as HTML."""
    paras = []
    for p in tbl.findall('.//w:p', NS):
        runs = get_para_runs(p)
        text = ''.join(r['text'] for r in runs).strip()
        if not text:
            continue
        html_text = runs_to_html(runs)
        paras.append(f'<p>{html_text}</p>')
    return '\n'.join(paras)

# ─── APPENDIX EXTRACTION ─────────────────────────────────────────────

def extract_appendix_a(docx_path):
    """Extract Appendix A: Quick Reference Chart."""
    z = zipfile.ZipFile(docx_path)
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    body = root.find('.//w:body', NS)

    elements = []
    for elem in body:
        tag = elem.tag.split('}')[-1]
        if tag == 'p':
            text = get_para_text(elem)
            if not text or text.startswith('───'):
                continue
            runs = get_para_runs(elem)
            first_size = runs[0]['size'] if runs else ''
            first_bold = runs[0]['bold'] if runs else False
            first_color = runs[0]['color'].upper() if runs else ''

            if first_size == '36' or first_size == '32':
                elements.append({'type': 'title', 'text': text})
            elif first_size == '26' or first_size == '24':
                elements.append({'type': 'subtitle', 'text': text})
            else:
                elements.append({'type': 'paragraph', 'html': runs_to_html(runs)})
        elif tag == 'tbl':
            rows = get_table_text(elem)
            elements.append({'type': 'table', 'rows': rows})
    return elements

def extract_appendix_b(docx_path):
    """Extract Appendix B: Scripture Index."""
    z = zipfile.ZipFile(docx_path)
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    body = root.find('.//w:body', NS)

    elements = []
    for elem in body:
        tag = elem.tag.split('}')[-1]
        if tag == 'p':
            text = get_para_text(elem)
            if not text or text.startswith('───'):
                continue
            runs = get_para_runs(elem)
            first_size = runs[0]['size'] if runs else ''
            first_bold = runs[0]['bold'] if runs else False
            first_color = runs[0]['color'].upper() if runs else ''
            style = get_para_style(elem)

            if first_size == '36' or first_size == '32':
                elements.append({'type': 'title', 'text': text})
            elif style == 'Heading2' or (first_bold and first_color == '5B8C5A' and first_size == '28'):
                elements.append({'type': 'h2', 'text': text})
            elif first_bold and (first_color == '2B4C7E' or first_color == '8B4513') and first_size in ('24', '26'):
                elements.append({'type': 'h3', 'text': text})
            elif first_size == '26':
                elements.append({'type': 'subtitle', 'text': text})
            else:
                elements.append({'type': 'paragraph', 'html': runs_to_html(runs)})
    return elements

def extract_appendix_c(docx_path):
    """Extract Appendix C: Small Group Exercises."""
    z = zipfile.ZipFile(docx_path)
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    body = root.find('.//w:body', NS)

    elements = []
    for elem in body:
        tag = elem.tag.split('}')[-1]
        if tag == 'p':
            text = get_para_text(elem)
            if not text or text.startswith('───'):
                continue
            runs = get_para_runs(elem)
            first_size = runs[0]['size'] if runs else ''
            first_bold = runs[0]['bold'] if runs else False
            first_color = runs[0]['color'].upper() if runs else ''
            style = get_para_style(elem)

            if first_size == '36' or first_size == '32':
                elements.append({'type': 'title', 'text': text})
            elif style == 'Heading2' or (first_bold and first_size == '28'):
                elements.append({'type': 'h2', 'text': text})
            elif first_bold and first_size in ('24', '26'):
                elements.append({'type': 'h3', 'text': text})
            elif first_size == '26':
                elements.append({'type': 'subtitle', 'text': text})
            else:
                elements.append({'type': 'paragraph', 'html': runs_to_html(runs)})
        elif tag == 'tbl':
            tbl_type = classify_table(elem)
            if tbl_type in ('principle', 'bridge', 'exercise'):
                box_html = extract_box_content(elem)
                elements.append({'type': f'{tbl_type}_box', 'html': box_html})
            else:
                rows = get_table_text(elem)
                elements.append({'type': 'table', 'rows': rows})
    return elements

# ─── HTML GENERATION ──────────────────────────────────────────────────

def get_chapter_css():
    """Return the complete CSS for chapter pages."""
    return '''    :root {
      --bg-dark: #0d0d0d;
      --bg-panel: #1a1a1a;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f5f5f5;
      --text-secondary: #a0a0a0;
      --text-muted: #888;
      --border-color: #2a2a2a;
      --accent: #06FFA5;
      --accent-soft: rgba(6, 255, 165, 0.12);
      --accent-glow: rgba(6, 255, 165, 0.4);
      --accent-secondary: #5ee5ff;
      --accent-secondary-glow: rgba(94, 229, 255, 0.3);
      --box-principle: #4A90D9;
      --box-principle-bg: rgba(74, 144, 217, 0.08);
      --box-bridge: #06FFA5;
      --box-bridge-bg: rgba(6, 255, 165, 0.06);
      --box-exercise: #D4A574;
      --box-exercise-bg: rgba(212, 165, 116, 0.08);
      --glass-blur: blur(12px);
      --radius-card: 22px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Georgia, serif;
      background: var(--bg-dark);
      color: var(--text-primary);
      font-size: 1.1rem;
      line-height: 1.85;
      min-height: 100vh;
      padding: 30px 20px;
    }
    body::before {
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: 0;
      background:
        radial-gradient(circle at top, rgba(6,255,165,0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba(94,229,255,0.04), transparent 50%);
      pointer-events: none;
    }
    .glass-page-wrapper {
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba(6,255,165,0.45), transparent 50%),
        radial-gradient(circle at top right, rgba(94,229,255,0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba(6,255,165,0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba(94,229,255,0.15),
        0 0 80px rgba(6,255,165,0.2);
      max-width: 860px;
      width: 100%;
      margin: 0 auto;
    }
    .glass-page-inner {
      background: var(--bg-inner);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card);
      padding: 3rem 2.5rem;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }
    .glass-page-inner::before {
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 150px;
      background: radial-gradient(ellipse at top, rgba(6,255,165,0.04), transparent 70%);
      pointer-events: none;
    }
    .glass-tab {
      position: absolute;
      bottom: -12px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      border-radius: 999px;
      background: radial-gradient(circle at top, rgba(6,255,165,0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba(6,255,165,0.4);
    }

    /* Three Names Banner */
    .three-names-banner {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      margin-bottom: 24px;
      background: rgba(6,255,165,0.05);
      border: 1px solid rgba(6,255,165,0.15);
      border-radius: 10px;
      font-size: 0.85rem;
      color: var(--text-secondary);
      cursor: pointer;
      transition: all 0.3s;
      position: relative;
      z-index: 1;
      flex-wrap: wrap;
    }
    .three-names-banner:hover {
      border-color: var(--accent);
      background: rgba(6,255,165,0.08);
    }
    .three-names-banner .label {
      color: var(--accent);
      font-weight: 600;
      white-space: nowrap;
    }
    .three-names-banner .name-tag {
      padding: 3px 10px;
      background: rgba(6,255,165,0.1);
      border: 1px solid rgba(6,255,165,0.25);
      border-radius: 6px;
      color: var(--text-primary);
      font-size: 0.85rem;
    }
    .three-names-banner .name-tag.empty {
      color: var(--text-muted);
      font-style: italic;
    }
    .three-names-edit {
      display: none;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      width: 100%;
      margin-top: 8px;
    }
    .three-names-edit input {
      flex: 1;
      min-width: 100px;
      padding: 6px 10px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(6,255,165,0.3);
      border-radius: 6px;
      color: var(--text-primary);
      font-size: 0.85rem;
    }
    .three-names-edit input:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 8px var(--accent-glow);
    }
    .three-names-edit button {
      padding: 6px 14px;
      background: var(--accent);
      color: #0d0d0d;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.8rem;
    }

    /* Three Names Revisit (Chapter 20) */
    .three-names-revisit {
      margin-bottom: 32px;
      padding: 28px 24px;
      background: rgba(6,255,165,0.06);
      border: 2px solid rgba(6,255,165,0.3);
      border-radius: 16px;
      text-align: center;
      position: relative;
      z-index: 1;
    }
    .three-names-revisit h2 {
      color: var(--accent);
      font-size: 1.4rem;
      margin-bottom: 8px;
      text-shadow: 0 0 15px var(--accent-glow);
    }
    .three-names-revisit .revisit-prompt {
      color: var(--text-secondary);
      font-style: italic;
      font-size: 0.95rem;
      margin-bottom: 20px;
      line-height: 1.7;
    }
    .three-names-revisit .revisit-names {
      display: flex;
      justify-content: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .three-names-revisit .revisit-name {
      padding: 12px 24px;
      background: rgba(6,255,165,0.1);
      border: 1px solid rgba(6,255,165,0.35);
      border-radius: 10px;
      color: var(--accent);
      font-size: 1.3rem;
      font-weight: 600;
      min-width: 120px;
      text-shadow: 0 0 10px var(--accent-glow);
    }
    .three-names-revisit .revisit-name.empty {
      color: var(--text-muted);
      font-style: italic;
      font-weight: 400;
      font-size: 1rem;
    }

    /* Navigation */
    .nav-controls {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
      padding: 14px 18px;
      background: rgba(6,255,165,0.04);
      border-radius: 12px;
      border: 1px solid rgba(6,255,165,0.12);
      position: relative;
      z-index: 1;
    }
    .nav-controls a, .nav-controls select {
      color: var(--text-primary);
      text-decoration: none;
      padding: 8px 14px;
      border-radius: 8px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(6,255,165,0.25);
      font-size: 0.85rem;
      transition: all 0.3s;
    }
    .nav-controls a:hover, .nav-controls select:hover {
      border-color: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }
    .nav-controls select {
      cursor: pointer;
      min-width: 180px;
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2306FFA5' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      padding-right: 30px;
    }
    .nav-controls select option {
      background: var(--bg-dark);
      color: var(--text-primary);
    }
    .home-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--accent-secondary);
      font-size: 0.85rem;
    }
    .home-link svg { width: 14px; height: 14px; fill: currentColor; }

    /* Header */
    header {
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba(6,255,165,0.2);
      position: relative;
      z-index: 1;
    }
    .part-label {
      font-size: 0.85rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 3px;
      margin-bottom: 4px;
    }
    .part-title {
      font-size: 0.95rem;
      color: var(--accent-secondary);
      font-style: italic;
      margin-bottom: 14px;
    }
    h1 {
      font-size: 2.2rem;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      margin-bottom: 6px;
      font-weight: 600;
    }
    .chapter-num {
      font-size: 1.05rem;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }
    .chapter-subtitle {
      font-size: 0.95rem;
      color: var(--text-muted);
      font-style: italic;
      margin-top: 6px;
    }

    /* Epigraph */
    .epigraph {
      margin-bottom: 28px;
      padding: 22px;
      background: rgba(6,255,165,0.04);
      border-radius: 14px;
      text-align: center;
      border: 1px solid rgba(6,255,165,0.15);
      position: relative;
      z-index: 1;
    }
    .epigraph blockquote {
      font-style: italic;
      font-size: 1.15rem;
      color: var(--text-primary);
      line-height: 1.8;
      margin-bottom: 0;
      border: none;
      padding: 0;
      background: transparent;
    }
    .epigraph cite {
      display: block;
      margin-top: 8px;
      color: var(--accent);
      font-style: normal;
      font-weight: 500;
    }

    /* Chapter purpose */
    .chapter-purpose {
      padding: 16px 20px;
      margin-bottom: 28px;
      background: var(--box-exercise-bg);
      border-left: 3px solid var(--box-exercise);
      border-radius: 0 10px 10px 0;
      font-style: italic;
      color: var(--text-secondary);
      position: relative;
      z-index: 1;
    }

    /* Body content */
    .content { position: relative; z-index: 1; }
    .content h2 {
      color: var(--accent);
      font-size: 1.45rem;
      margin: 32px 0 16px;
      padding-bottom: 8px;
      border-bottom: 2px solid rgba(6,255,165,0.2);
    }
    .content h3 {
      color: var(--box-exercise);
      font-size: 1.2rem;
      margin: 24px 0 12px;
    }
    .content p {
      margin-bottom: 16px;
      color: var(--text-secondary);
      text-align: justify;
    }

    /* Scripture blockquotes */
    blockquote.scripture {
      margin: 20px 0;
      padding: 16px 20px;
      background: rgba(6,255,165,0.04);
      border-left: 3px solid var(--accent);
      border-radius: 0 10px 10px 0;
      font-style: italic;
    }
    blockquote.scripture p { margin-bottom: 0; color: var(--text-primary); }
    blockquote.scripture cite {
      display: block;
      margin-top: 6px;
      color: var(--accent);
      font-style: normal;
      font-weight: 500;
      font-size: 0.9rem;
    }

    /* Callout boxes */
    .principle-box, .bridge-box, .exercise-box {
      margin: 24px 0;
      padding: 20px 22px;
      border-radius: 12px;
      position: relative;
    }
    .principle-box {
      background: var(--box-principle-bg);
      border: 1px solid rgba(74,144,217,0.25);
      border-left: 4px solid var(--box-principle);
    }
    .principle-box p { color: var(--text-primary); }
    .bridge-box {
      background: var(--box-bridge-bg);
      border: 1px solid rgba(6,255,165,0.2);
      border-left: 4px solid var(--box-bridge);
    }
    .bridge-box p { color: var(--text-primary); }
    .exercise-box {
      background: var(--box-exercise-bg);
      border: 1px solid rgba(212,165,116,0.25);
      border-left: 4px solid var(--box-exercise);
    }
    .exercise-box p { color: var(--text-primary); }

    /* Data tables */
    .data-table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 0.9rem;
    }
    .data-table th, .data-table td {
      padding: 10px 14px;
      border: 1px solid rgba(6,255,165,0.15);
      text-align: left;
      vertical-align: top;
    }
    .data-table th {
      background: rgba(6,255,165,0.1);
      font-weight: 600;
      color: var(--accent);
    }
    .data-table tr:nth-child(even) td {
      background: rgba(6,255,165,0.03);
    }

    /* Study Questions */
    .study-questions-section {
      margin-top: 40px;
      border-top: 2px solid rgba(74,144,217,0.3);
      padding-top: 24px;
    }
    .study-questions-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      padding: 14px 18px;
      background: rgba(74,144,217,0.08);
      border: 1px solid rgba(74,144,217,0.2);
      border-radius: 12px;
      transition: all 0.3s;
      user-select: none;
    }
    .study-questions-header:hover {
      border-color: var(--box-principle);
      background: rgba(74,144,217,0.12);
    }
    .study-questions-header h2 {
      color: var(--box-principle);
      font-size: 1.3rem;
      margin: 0;
      border: none;
      padding: 0;
    }
    .study-questions-header .arrow {
      color: var(--box-principle);
      font-size: 1.3rem;
      transition: transform 0.3s;
    }
    .study-questions-header.expanded .arrow {
      transform: rotate(180deg);
    }
    .study-questions-body {
      display: none;
      padding-top: 20px;
    }
    .study-questions-body.expanded {
      display: block;
    }
    .study-question {
      margin-bottom: 24px;
      padding: 16px;
      background: rgba(74,144,217,0.04);
      border-radius: 10px;
      border: 1px solid rgba(74,144,217,0.1);
    }
    .study-question .q-num {
      color: var(--box-principle);
      font-weight: 700;
      margin-right: 8px;
    }
    .study-question .q-text {
      color: var(--text-primary);
      line-height: 1.7;
    }
    .study-question textarea {
      width: 100%;
      margin-top: 12px;
      padding: 10px 12px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(74,144,217,0.2);
      border-radius: 8px;
      color: var(--text-primary);
      font-family: inherit;
      font-size: 1rem;
      line-height: 1.6;
      resize: vertical;
      min-height: 60px;
      transition: border-color 0.3s;
    }
    .study-question textarea:focus {
      outline: none;
      border-color: var(--box-principle);
      box-shadow: 0 0 8px rgba(74,144,217,0.3);
    }
    .study-question textarea::placeholder {
      color: var(--text-muted);
    }

    /* Key Scriptures */
    .key-scriptures {
      margin: 20px 0;
      padding: 16px 20px;
      background: rgba(212,165,116,0.06);
      border: 1px solid rgba(212,165,116,0.2);
      border-radius: 10px;
    }
    .key-scriptures h3 {
      color: var(--box-exercise);
      margin-bottom: 8px;
    }
    .key-scriptures p {
      color: var(--text-secondary);
      font-size: 0.9rem;
    }

    /* Divider */
    .divider {
      text-align: center;
      margin: 28px 0;
      color: var(--text-muted);
      opacity: 0.4;
    }

    /* Mark Complete */
    .mark-complete {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin: 30px 0 10px;
      padding: 12px;
      background: rgba(6,255,165,0.06);
      border: 1px solid rgba(6,255,165,0.2);
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.3s;
      user-select: none;
    }
    .mark-complete:hover {
      border-color: var(--accent);
      background: rgba(6,255,165,0.1);
    }
    .mark-complete.completed {
      background: rgba(6,255,165,0.12);
      border-color: var(--accent);
    }
    .mark-complete .check {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: 2px solid var(--accent);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      color: transparent;
      transition: all 0.3s;
    }
    .mark-complete.completed .check {
      background: var(--accent);
      color: #0d0d0d;
    }
    .mark-complete span:last-child {
      color: var(--accent);
      font-weight: 600;
      font-size: 0.9rem;
    }

    /* Footer */
    footer {
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba(6,255,165,0.15);
      text-align: center;
      position: relative;
      z-index: 1;
    }
    .footer-nav {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
    }
    .footer-nav a {
      color: var(--accent-secondary);
      text-decoration: none;
      padding: 10px 20px;
      border-radius: 8px;
      background: rgba(94,229,255,0.08);
      border: 1px solid rgba(94,229,255,0.25);
      transition: all 0.3s;
      font-size: 0.9rem;
    }
    .footer-nav a:hover {
      background: rgba(94,229,255,0.15);
      box-shadow: 0 0 10px var(--accent-secondary-glow);
    }
    .footer-nav a.disabled {
      opacity: 0.35;
      pointer-events: none;
    }
    .copyright {
      color: var(--text-muted);
      font-size: 0.78rem;
      margin-top: 12px;
    }

    /* Print styles */
    @media print {
      body { background: white; color: #333; padding: 0; font-size: 11pt; line-height: 1.5; }
      body::before { display: none; }
      .glass-page-wrapper { box-shadow: none; background: none; padding: 0; max-width: 100%; }
      .glass-page-inner { background: white; padding: 0.5in; border-radius: 0; border: none; }
      .glass-page-inner::before { display: none; }
      .glass-tab, .nav-controls, .footer-nav, .three-names-banner, .mark-complete { display: none; }
      header { border-bottom: 2px solid #333; }
      h1 { color: #2B4C7E; text-shadow: none; font-size: 18pt; }
      .content h2 { color: #2B4C7E; border-bottom-color: #2B4C7E; }
      .content h3 { color: #8B4513; }
      .content p { color: #333; }
      .principle-box { background: #f0f4f8; border-color: #4A90D9; }
      .bridge-box { background: #f0f5f0; border-color: #2a8a2a; }
      .exercise-box { background: #fdf8f0; border-color: #8B4513; }
      blockquote.scripture { background: #f9f9f9; border-left-color: #2a8a2a; }
      .study-questions-body { display: block !important; }
      .study-question textarea { display: none; }
      .copyright { color: #999; }
      a { color: #333; text-decoration: none; }
    }

    /* Mobile */
    @media (max-width: 600px) {
      body { padding: 15px 10px; }
      .glass-page-inner { padding: 1.5rem 1.2rem; }
      h1 { font-size: 1.5rem; }
      .nav-controls { flex-direction: column; }
      .nav-controls select { width: 100%; }
      .footer-nav { flex-direction: column; gap: 10px; }
      .footer-nav a { text-align: center; }
      .three-names-banner { flex-direction: column; align-items: flex-start; }
    }'''

def get_chapter_js(ch_num):
    """Return the JavaScript for a chapter page."""
    return f'''
    // Three Names
    const NAMES_KEY = 'bridgeMoments_threeNames';
    const PROGRESS_KEY = 'bridgeMoments_progress';
    const CH_NUM = {ch_num};

    function loadNames() {{
      try {{ return JSON.parse(localStorage.getItem(NAMES_KEY)) || {{name1:'',name2:'',name3:''}}; }}
      catch {{ return {{name1:'',name2:'',name3:''}}; }}
    }}

    function saveNames(names) {{
      localStorage.setItem(NAMES_KEY, JSON.stringify(names));
    }}

    function renderNamesBanner() {{
      const names = loadNames();
      const display = document.getElementById('names-display');
      const edit = document.getElementById('names-edit');
      if (!display) return;

      display.innerHTML = '';
      ['name1','name2','name3'].forEach(k => {{
        const span = document.createElement('span');
        span.className = 'name-tag' + (names[k] ? '' : ' empty');
        span.textContent = names[k] || 'Name ' + k.slice(-1);
        display.appendChild(span);
      }});
    }}

    function toggleNamesEdit() {{
      const edit = document.getElementById('names-edit');
      const names = loadNames();
      if (edit.style.display === 'flex') {{
        edit.style.display = 'none';
      }} else {{
        edit.style.display = 'flex';
        document.getElementById('name1-input').value = names.name1;
        document.getElementById('name2-input').value = names.name2;
        document.getElementById('name3-input').value = names.name3;
        document.getElementById('name1-input').focus();
      }}
    }}

    function saveNamesFromInputs() {{
      const names = {{
        name1: document.getElementById('name1-input').value.trim(),
        name2: document.getElementById('name2-input').value.trim(),
        name3: document.getElementById('name3-input').value.trim()
      }};
      saveNames(names);
      renderNamesBanner();
      document.getElementById('names-edit').style.display = 'none';
    }}

    // Progress
    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch {{ return {{}}; }}
    }}

    function markVisited() {{
      const p = loadProgress();
      if (!p['ch' + CH_NUM]) p['ch' + CH_NUM] = 'visited';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
    }}

    function toggleComplete() {{
      const p = loadProgress();
      const key = 'ch' + CH_NUM;
      p[key] = p[key] === 'complete' ? 'visited' : 'complete';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
      updateCompleteBtn();
    }}

    function updateCompleteBtn() {{
      const p = loadProgress();
      const btn = document.getElementById('mark-complete');
      if (!btn) return;
      const done = p['ch' + CH_NUM] === 'complete';
      btn.className = 'mark-complete' + (done ? ' completed' : '');
      btn.querySelector('.check').textContent = done ? '\\u2713' : '';
      btn.querySelector('span:last-child').textContent = done ? 'Chapter Complete' : 'Mark Chapter Complete';
    }}

    // Study Questions
    function toggleQuestions() {{
      const header = document.querySelector('.study-questions-header');
      const body = document.querySelector('.study-questions-body');
      if (!header || !body) return;
      header.classList.toggle('expanded');
      body.classList.toggle('expanded');
    }}

    function loadNote(qNum) {{
      const key = 'bridgeMoments_notes_ch' + CH_NUM + '_q' + qNum;
      return localStorage.getItem(key) || '';
    }}

    function saveNote(qNum, value) {{
      const key = 'bridgeMoments_notes_ch' + CH_NUM + '_q' + qNum;
      localStorage.setItem(key, value);
    }}

    function initNotes() {{
      document.querySelectorAll('.study-question textarea').forEach(ta => {{
        const qNum = ta.dataset.question;
        ta.value = loadNote(qNum);
        ta.addEventListener('input', function() {{
          saveNote(qNum, this.value);
        }});
      }});
    }}

    // Chapter navigation
    function goToChapter(val) {{
      if (val) window.location.href = val;
    }}

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {{
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
      if (e.key === 'ArrowLeft') {{
        const prev = document.querySelector('.footer-nav a:first-child');
        if (prev && !prev.classList.contains('disabled')) prev.click();
      }} else if (e.key === 'ArrowRight') {{
        const next = document.querySelector('.footer-nav a:last-child');
        if (next && !next.classList.contains('disabled')) next.click();
      }}
    }});

    // Three Names Revisit (Chapter 20)
    function renderRevisitNames() {{
      const container = document.getElementById('revisit-names');
      if (!container) return;
      const names = loadNames();
      container.innerHTML = '';
      ['name1','name2','name3'].forEach(k => {{
        const div = document.createElement('div');
        div.className = 'revisit-name' + (names[k] ? '' : ' empty');
        div.textContent = names[k] || 'Not yet named';
        container.appendChild(div);
      }});
    }}

    // Init
    document.addEventListener('DOMContentLoaded', function() {{
      renderNamesBanner();
      renderRevisitNames();
      markVisited();
      updateCompleteBtn();
      initNotes();
    }});'''

def get_chapter_selector(current_num):
    """Generate the chapter selector dropdown HTML."""
    options = ['<option value="">Jump to Chapter...</option>']
    for ch in CHAPTERS:
        n = ch['num']
        sel = ' selected' if n == current_num else ''
        val = f'chapter-{n:02d}.html'
        options.append(f'<option value="{val}"{sel}>Ch {n}: {html_module.escape(ch["title"])}</option>')
    options.append('<option value="appendix-a.html">Appendix A: Quick Reference</option>')
    options.append('<option value="appendix-b.html">Appendix B: Scripture Index</option>')
    options.append('<option value="appendix-c.html">Appendix C: Small Group Exercises</option>')
    return '\n            '.join(options)

def generate_chapter_html(ch_meta, content):
    """Generate a complete chapter HTML page."""
    ch_num = ch_meta['num']
    title = ch_meta['title']
    part = ch_meta['part']
    part_title = ch_meta['part_title']
    subtitle = ch_meta.get('subtitle', '')

    prev_link = f'chapter-{ch_num-1:02d}.html' if ch_num > 1 else '#'
    next_link = f'chapter-{ch_num+1:02d}.html' if ch_num < 20 else 'appendix-a.html'
    prev_disabled = ' class="disabled"' if ch_num == 1 else ''

    prev_text = f'&larr; Chapter {ch_num-1}' if ch_num > 1 else '&larr; Previous'
    next_text = f'Chapter {ch_num+1} &rarr;' if ch_num < 20 else 'Appendix A &rarr;'

    # Build body content HTML
    body_html = build_body_html(content)

    # Build epigraph
    epigraph_html = ''
    if content.get('epigraph'):
        ep = content['epigraph']
        # Split scripture text and reference (skip empty lines)
        lines = [l.strip() for l in ep.split('\n')]
        quote_text = lines[0] if lines else ep
        ref_text = next((l for l in lines[1:] if l), '')
        epigraph_html = f'''
      <section class="epigraph">
        <blockquote>{html_module.escape(quote_text)}</blockquote>
        {f'<cite>{html_module.escape(ref_text)}</cite>' if ref_text else ''}
      </section>'''

    # Build chapter purpose
    purpose_html = ''
    if content.get('chapter_purpose'):
        purpose_html = f'''
      <div class="chapter-purpose">{html_module.escape(content["chapter_purpose"])}</div>'''

    # Chapter 20 special: Three Names Revisited
    revisit_html = ''
    if ch_num == 20:
        revisit_html = '''
      <section class="three-names-revisit">
        <h2>Your Three Names &mdash; Revisited</h2>
        <p class="revisit-prompt">You wrote these names at the beginning of this journey. They have traveled with you through every chapter, every principle, every bridge moment. As you read this final chapter, hold them close.</p>
        <div class="revisit-names" id="revisit-names"></div>
      </section>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chapter {ch_num}: {html_module.escape(title)} | Bridge Moments</title>
  <style>
{get_chapter_css()}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <div class="three-names-banner" onclick="toggleNamesEdit()">
        <span class="label">Your Three Names:</span>
        <span id="names-display"></span>
        <div id="names-edit" class="three-names-edit" onclick="event.stopPropagation()">
          <input type="text" id="name1-input" placeholder="First name">
          <input type="text" id="name2-input" placeholder="Second name">
          <input type="text" id="name3-input" placeholder="Third name">
          <button onclick="saveNamesFromInputs()">Save</button>
        </div>
      </div>

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          Bridge Moments
        </a>
        <select id="chapter-select" onchange="goToChapter(this.value)">
            {get_chapter_selector(ch_num)}
        </select>
        <a href="../Noble_Mind_Study_Tool_v2.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          Noble Mind Study
        </a>
      </nav>

      <header>
        <p class="part-label">Part {part}</p>
        <p class="part-title">{html_module.escape(part_title)}</p>
        <p class="chapter-num">Chapter {ch_num}</p>
        <h1>{html_module.escape(title)}</h1>
        {f'<p class="chapter-subtitle">{html_module.escape(subtitle)}</p>' if subtitle else ''}
      </header>
{epigraph_html}
{purpose_html}
{revisit_html}

      <div class="content">
{body_html}
      </div>

      <div id="mark-complete" class="mark-complete" onclick="toggleComplete()">
        <span class="check"></span>
        <span>Mark Chapter Complete</span>
      </div>

      <footer>
        <div class="footer-nav">
          <a href="{prev_link}"{prev_disabled}>{prev_text}</a>
          <a href="{next_link}">{next_text}</a>
        </div>
        <p class="copyright">Bridge Moments: Making the Most of Every Opportunity &copy; Paul Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>

  <script>{get_chapter_js(ch_num)}
  </script>
</body>
</html>'''

def build_body_html(content):
    """Build the main body HTML from extracted elements."""
    parts = []
    skip_initial = True  # Skip part labels, subtitles, first epigraph/purpose that are handled in header
    epigraph_seen = False
    purpose_seen = False
    in_key_scriptures = False

    for elem in content['elements']:
        etype = elem['type']

        # Skip elements that are rendered in the header section
        if etype in ('part_label', 'part_subtitle'):
            continue

        if etype == 'scripture' and not epigraph_seen:
            epigraph_seen = True
            continue

        if etype == 'chapter_purpose' and not purpose_seen:
            purpose_seen = True
            continue

        if etype == 'divider':
            parts.append('        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>')
            continue

        if etype == 'h2':
            parts.append(f'        <h2>{html_module.escape(elem["text"])}</h2>')
            continue

        if etype == 'h3':
            parts.append(f'        <h3>{html_module.escape(elem["text"])}</h3>')
            continue

        if etype == 'scripture':
            lines = [l.strip() for l in elem['text'].split('\n')]
            quote = lines[0] if lines else elem['text']
            ref = next((l for l in lines[1:] if l), '')
            parts.append(f'        <blockquote class="scripture"><p>{html_module.escape(quote)}</p>')
            if ref:
                parts.append(f'          <cite>{html_module.escape(ref)}</cite>')
            parts.append('        </blockquote>')
            continue

        if etype == 'paragraph':
            html_text = elem.get('html', html_module.escape(elem['text']))
            parts.append(f'        <p>{html_text}</p>')
            continue

        if etype == 'principle_box':
            parts.append(f'        <div class="principle-box">\n{elem["html"]}\n        </div>')
            continue

        if etype == 'bridge_box':
            parts.append(f'        <div class="bridge-box">\n{elem["html"]}\n        </div>')
            continue

        if etype == 'exercise_box':
            parts.append(f'        <div class="exercise-box">\n{elem["html"]}\n        </div>')
            continue

        if etype == 'key_scriptures_header':
            in_key_scriptures = True
            parts.append(f'        <div class="key-scriptures">')
            parts.append(f'          <h3>{html_module.escape(elem["text"])}</h3>')
            continue

        if etype == 'key_scriptures':
            parts.append(f'          <p>{html_module.escape(elem["text"])}</p>')
            if in_key_scriptures:
                parts.append(f'        </div>')
                in_key_scriptures = False
            continue

        if etype == 'table':
            rows = elem['rows']
            if not rows:
                continue
            parts.append('        <table class="data-table">')
            for i, row in enumerate(rows):
                parts.append('          <tr>')
                cell_tag = 'th' if i == 0 else 'td'
                for cell in row:
                    parts.append(f'            <{cell_tag}>{html_module.escape(cell)}</{cell_tag}>')
                parts.append('          </tr>')
            parts.append('        </table>')
            continue

        if etype == 'study_questions':
            questions = elem['questions']
            if not questions:
                continue
            parts.append('        <section class="study-questions-section">')
            parts.append('          <div class="study-questions-header" onclick="toggleQuestions()">')
            parts.append('            <h2>Study &amp; Discussion Questions</h2>')
            parts.append('            <span class="arrow">&#x25BC;</span>')
            parts.append('          </div>')
            parts.append('          <div class="study-questions-body">')
            for i, q in enumerate(questions, 1):
                parts.append(f'            <div class="study-question">')
                parts.append(f'              <span class="q-num">{i}.</span>')
                parts.append(f'              <span class="q-text">{html_module.escape(q)}</span>')
                parts.append(f'              <textarea data-question="{i}" placeholder="Your notes..." rows="3"></textarea>')
                parts.append(f'            </div>')
            parts.append('          </div>')
            parts.append('        </section>')
            continue

    # Close key-scriptures if still open
    if in_key_scriptures:
        parts.append('        </div>')

    return '\n'.join(parts)

# ─── INDEX PAGE ───────────────────────────────────────────────────────

def generate_index_html():
    """Generate the BridgeMoments/index.html hub page."""
    # Build part sections
    parts_html = []
    current_part = 0

    part_info = {
        1: {"title": "The Foundation: Why Words Matter", "chapters": "Chapters 1\u20133"},
        2: {"title": "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "chapters": "Chapters 4\u201312"},
        3: {"title": "The Pattern Continued: Bridge Moments in Acts", "chapters": "Chapters 13\u201315"},
        4: {"title": "The Practice: Living with Bridge Moment Eyes", "chapters": "Chapters 16\u201320"},
    }

    for ch in CHAPTERS:
        if ch['part'] != current_part:
            if current_part != 0:
                parts_html.append('        </div>\n      </section>')
            current_part = ch['part']
            pi = part_info[current_part]
            parts_html.append(f'''
      <section class="part-section">
        <div class="part-header">
          <h2>Part {current_part}: {pi["title"]}</h2>
          <span class="chapters">({pi["chapters"]})</span>
        </div>
        <div class="lesson-grid">''')

        n = ch['num']
        subtitle_html = f'\n            <div class="lesson-ref">{html_module.escape(ch["subtitle"])}</div>' if ch.get("subtitle") else ''
        parts_html.append(f'''          <a href="chapter-{n:02d}.html" class="lesson-card" data-ch="{n}">
            <span class="lesson-num">Chapter {n}</span>
            <div class="lesson-title">{html_module.escape(ch["title"])}</div>{subtitle_html}
            <span class="progress-dot" id="dot-{n}"></span>
          </a>''')

    parts_html.append('        </div>\n      </section>')

    parts_content = '\n'.join(parts_html)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bridge Moments: Making the Most of Every Opportunity</title>
  <style>
    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f5f5f5;
      --text-secondary: #a0a0a0;
      --text-muted: #888;
      --accent: #06FFA5;
      --accent-glow: rgba(6,255,165,0.4);
      --accent-soft: rgba(6,255,165,0.12);
      --accent-secondary: #5ee5ff;
      --accent-secondary-glow: rgba(94,229,255,0.3);
      --glass-blur: blur(12px);
      --radius-card: 22px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Georgia, serif;
      background: var(--bg-dark);
      color: var(--text-primary);
      font-size: 1.1rem;
      line-height: 1.8;
      min-height: 100vh;
      padding: 30px 20px;
    }}
    body::before {{
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: 0;
      background:
        radial-gradient(circle at top, rgba(6,255,165,0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba(94,229,255,0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba(6,255,165,0.45), transparent 50%),
        radial-gradient(circle at top right, rgba(94,229,255,0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba(6,255,165,0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba(94,229,255,0.15),
        0 0 80px rgba(6,255,165,0.2);
      max-width: 1000px;
      width: 100%;
      margin: 0 auto;
    }}
    .glass-page-inner {{
      background: var(--bg-inner);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card);
      padding: 45px 40px;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }}
    .glass-page-inner::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 150px;
      background: radial-gradient(ellipse at top, rgba(6,255,165,0.04), transparent 70%);
      pointer-events: none;
    }}
    .glass-tab {{
      position: absolute;
      bottom: -12px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      border-radius: 999px;
      background: radial-gradient(circle at top, rgba(6,255,165,0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba(6,255,165,0.4);
    }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba(6,255,165,0.2);
      position: relative;
      z-index: 1;
    }}
    h1 {{
      font-size: 2.3rem;
      color: var(--accent);
      text-shadow: 0 0 25px var(--accent-glow);
      margin-bottom: 8px;
    }}
    .subtitle {{
      font-size: 1.1rem;
      color: var(--text-secondary);
      font-style: italic;
      margin-bottom: 8px;
    }}
    .stats {{
      margin-top: 12px;
      color: var(--text-secondary);
      font-size: 0.9rem;
    }}
    .stats span {{
      color: var(--accent);
      font-weight: 600;
    }}
    .return-link {{
      display: inline-block;
      margin-top: 18px;
      padding: 10px 20px;
      background: rgba(94,229,255,0.08);
      border: 1px solid rgba(94,229,255,0.25);
      border-radius: 8px;
      color: var(--accent-secondary);
      text-decoration: none;
      font-size: 0.9rem;
      transition: all 0.3s ease;
    }}
    .return-link:hover {{
      background: rgba(94,229,255,0.15);
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
    }}

    /* Progress bar */
    .progress-bar {{
      margin: 20px 0;
      padding: 14px 18px;
      background: rgba(6,255,165,0.04);
      border: 1px solid rgba(6,255,165,0.12);
      border-radius: 12px;
      position: relative;
      z-index: 1;
    }}
    .progress-bar .label {{
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }}
    .progress-bar .label span {{ color: var(--accent); font-weight: 600; }}
    .progress-track {{
      height: 8px;
      background: rgba(0,0,0,0.3);
      border-radius: 4px;
      overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
      border-radius: 4px;
      transition: width 0.5s ease;
    }}

    /* Three Names Card */
    .three-names-card {{
      margin: 24px 0;
      padding: 24px;
      background: rgba(6,255,165,0.05);
      border: 1px solid rgba(6,255,165,0.2);
      border-radius: 14px;
      position: relative;
      z-index: 1;
    }}
    .three-names-card h2 {{
      color: var(--accent);
      font-size: 1.2rem;
      margin-bottom: 6px;
    }}
    .three-names-card .desc {{
      color: var(--text-secondary);
      font-size: 0.9rem;
      margin-bottom: 16px;
      font-style: italic;
    }}
    .names-inputs {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .names-inputs input {{
      flex: 1;
      min-width: 140px;
      padding: 10px 14px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(6,255,165,0.25);
      border-radius: 8px;
      color: var(--text-primary);
      font-size: 0.95rem;
      transition: all 0.3s;
    }}
    .names-inputs input:focus {{
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }}
    .names-inputs input::placeholder {{ color: var(--text-muted); }}

    /* Key verse */
    .key-verse {{
      margin: 24px 0;
      padding: 22px;
      background: rgba(6,255,165,0.04);
      border-radius: 14px;
      text-align: center;
      border: 1px solid rgba(6,255,165,0.15);
      position: relative;
      z-index: 1;
    }}
    .key-verse blockquote {{
      font-style: italic;
      font-size: 1.05rem;
      color: var(--text-primary);
      line-height: 1.8;
      margin-bottom: 10px;
    }}
    .key-verse cite {{
      color: var(--accent);
      font-style: normal;
      font-weight: 500;
    }}

    /* TOC Parts */
    .part-section {{
      margin-bottom: 32px;
      position: relative;
      z-index: 1;
    }}
    .part-header {{
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 14px;
    }}
    .part-header h2 {{
      font-size: 1.3rem;
      color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
    }}
    .part-header .chapters {{
      color: var(--text-secondary);
      font-size: 0.9rem;
    }}
    .lesson-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
    }}
    .lesson-card {{
      display: block;
      position: relative;
      padding: 14px 18px;
      background: rgba(0,0,0,0.2);
      border-radius: 10px;
      border: 1px solid rgba(6,255,165,0.12);
      text-decoration: none;
      transition: all 0.3s;
    }}
    .lesson-card:hover {{
      border-color: var(--accent);
      box-shadow: 0 0 15px var(--accent-glow);
      transform: translateY(-2px);
    }}
    .lesson-num {{
      color: var(--accent);
      font-weight: 700;
      font-size: 0.85rem;
    }}
    .lesson-title {{
      color: var(--text-primary);
      font-size: 0.95rem;
      margin: 4px 0;
    }}
    .lesson-ref {{
      color: var(--text-muted);
      font-size: 0.8rem;
      font-style: italic;
      margin-top: 2px;
    }}
    .progress-dot {{
      position: absolute;
      top: 12px;
      right: 14px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 2px solid rgba(6,255,165,0.3);
      transition: all 0.3s;
    }}
    .progress-dot.visited {{
      border-color: var(--accent);
      background: rgba(6,255,165,0.3);
    }}
    .progress-dot.complete {{
      border-color: var(--accent);
      background: var(--accent);
    }}

    /* Appendix section */
    .appendix-section {{
      margin-top: 16px;
    }}
    .appendix-section h2 {{
      font-size: 1.2rem;
      color: var(--accent-secondary);
      margin-bottom: 14px;
    }}

    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba(6,255,165,0.15);
      text-align: center;
      position: relative;
      z-index: 1;
    }}
    .copyright {{
      color: var(--text-muted);
      font-size: 0.78rem;
    }}

    @media print {{
      body {{ background: white; color: #333; }}
      body::before {{ display: none; }}
      .glass-page-wrapper {{ box-shadow: none; background: none; }}
      .glass-page-inner {{ background: white; border: none; }}
      .glass-page-inner::before {{ display: none; }}
      .glass-tab, .return-link, .progress-bar {{ display: none; }}
      h1 {{ color: #2B4C7E; text-shadow: none; }}
      .part-header h2 {{ color: #2B4C7E; text-shadow: none; }}
      .lesson-card {{ border: 1px solid #ddd; }}
      .lesson-num {{ color: #2B4C7E; }}
      .lesson-title {{ color: #333; }}
    }}
    @media (max-width: 600px) {{
      body {{ padding: 15px 10px; }}
      .glass-page-inner {{ padding: 25px 20px; }}
      h1 {{ font-size: 1.7rem; }}
      .lesson-grid {{ grid-template-columns: 1fr; }}
      .names-inputs {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">
      <header>
        <h1>Bridge Moments</h1>
        <p class="subtitle">Making the Most of Every Opportunity</p>
        <p class="stats">
          <span>20</span> Chapters &bull; <span>4</span> Parts &bull; <span>3</span> Appendices
        </p>
        <a href="../Noble_Mind_Study_Tool_v2.html" class="return-link">&larr; Return to Noble Mind Study</a>
      </header>

      <section class="key-verse">
        <blockquote>
          &ldquo;Walk in wisdom toward outsiders, making the most of the opportunity. Let your speech always be with grace, as though seasoned with salt, so that you will know how you should respond to each person.&rdquo;
        </blockquote>
        <cite>&mdash; Colossians 4:5&ndash;6 (NASB)</cite>
      </section>

      <section class="three-names-card">
        <h2>Your Three Names</h2>
        <p class="desc">In Chapter 1, you will be asked to write three names &mdash; people in your life who need a bridge moment. These names will travel with you through all 20 chapters.</p>
        <div class="names-inputs">
          <input type="text" id="name1" placeholder="First name" oninput="saveIndexNames()">
          <input type="text" id="name2" placeholder="Second name" oninput="saveIndexNames()">
          <input type="text" id="name3" placeholder="Third name" oninput="saveIndexNames()">
        </div>
      </section>

      <div class="progress-bar">
        <div class="label">
          <span>Study Progress</span>
          <span id="progress-text">0 / 20 chapters</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
      </div>

{parts_content}

      <section class="appendix-section part-section">
        <div class="part-header">
          <h2>Appendices</h2>
        </div>
        <div class="lesson-grid">
          <a href="appendix-a.html" class="lesson-card">
            <span class="lesson-num">Appendix A</span>
            <div class="lesson-title">Quick Reference Chart</div>
          </a>
          <a href="appendix-b.html" class="lesson-card">
            <span class="lesson-num">Appendix B</span>
            <div class="lesson-title">Scripture Index</div>
          </a>
          <a href="appendix-c.html" class="lesson-card">
            <span class="lesson-num">Appendix C</span>
            <div class="lesson-title">Small Group Exercises</div>
          </a>
        </div>
      </section>

      <footer>
        <p class="copyright">Bridge Moments: Making the Most of Every Opportunity &copy; Paul Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>

  <script>
    const NAMES_KEY = 'bridgeMoments_threeNames';
    const PROGRESS_KEY = 'bridgeMoments_progress';

    function loadNames() {{
      try {{ return JSON.parse(localStorage.getItem(NAMES_KEY)) || {{name1:'',name2:'',name3:''}}; }}
      catch {{ return {{name1:'',name2:'',name3:''}}; }}
    }}

    function saveIndexNames() {{
      const names = {{
        name1: document.getElementById('name1').value.trim(),
        name2: document.getElementById('name2').value.trim(),
        name3: document.getElementById('name3').value.trim()
      }};
      localStorage.setItem(NAMES_KEY, JSON.stringify(names));
    }}

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch {{ return {{}}; }}
    }}

    function updateProgressUI() {{
      const p = loadProgress();
      let complete = 0;
      for (let i = 1; i <= 20; i++) {{
        const dot = document.getElementById('dot-' + i);
        if (!dot) continue;
        const status = p['ch' + i];
        if (status === 'complete') {{
          dot.className = 'progress-dot complete';
          complete++;
        }} else if (status === 'visited') {{
          dot.className = 'progress-dot visited';
        }}
      }}
      document.getElementById('progress-text').textContent = complete + ' / 20 chapters';
      document.getElementById('progress-fill').style.width = (complete / 20 * 100) + '%';
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      const names = loadNames();
      document.getElementById('name1').value = names.name1;
      document.getElementById('name2').value = names.name2;
      document.getElementById('name3').value = names.name3;
      updateProgressUI();
    }});
  </script>
</body>
</html>'''

# ─── APPENDIX HTML GENERATION ────────────────────────────────────────

def generate_appendix_html(letter, title, subtitle, elements):
    """Generate an appendix HTML page."""
    prev_links = {'a': ('chapter-20.html', 'Chapter 20'), 'b': ('appendix-a.html', 'Appendix A'), 'c': ('appendix-b.html', 'Appendix B')}
    next_links = {'a': ('appendix-b.html', 'Appendix B'), 'b': ('appendix-c.html', 'Appendix C'), 'c': ('#', None)}

    prev_href, prev_text = prev_links[letter]
    next_href, next_text = next_links[letter]
    next_disabled = ' class="disabled"' if next_text is None else ''

    body_parts = []
    for elem in elements:
        if elem['type'] == 'title':
            continue  # Rendered in header
        elif elem['type'] == 'subtitle':
            continue
        elif elem['type'] == 'h2':
            body_parts.append(f'        <h2>{html_module.escape(elem["text"])}</h2>')
        elif elem['type'] == 'h3':
            body_parts.append(f'        <h3>{html_module.escape(elem["text"])}</h3>')
        elif elem['type'] == 'paragraph':
            body_parts.append(f'        <p>{elem["html"]}</p>')
        elif elem['type'] == 'table':
            rows = elem['rows']
            if not rows:
                continue
            body_parts.append('        <table class="data-table">')
            for i, row in enumerate(rows):
                body_parts.append('          <tr>')
                cell_tag = 'th' if i == 0 else 'td'
                for cell in row:
                    body_parts.append(f'            <{cell_tag}>{html_module.escape(cell)}</{cell_tag}>')
                body_parts.append('          </tr>')
            body_parts.append('        </table>')
        elif elem['type'] in ('principle_box', 'bridge_box', 'exercise_box'):
            css_class = elem['type'].replace('_box', '-box')
            body_parts.append(f'        <div class="{css_class}">\n{elem["html"]}\n        </div>')

    body_html = '\n'.join(body_parts)

    ch_selector = '<option value="">Jump to Chapter...</option>'
    for ch in CHAPTERS:
        n = ch['num']
        ch_selector += f'\n            <option value="chapter-{n:02d}.html">Ch {n}: {html_module.escape(ch["title"])}</option>'
    sel_a = ' selected' if letter == 'a' else ''
    sel_b = ' selected' if letter == 'b' else ''
    sel_c = ' selected' if letter == 'c' else ''
    ch_selector += f'\n            <option value="appendix-a.html"{sel_a}>Appendix A: Quick Reference</option>'
    ch_selector += f'\n            <option value="appendix-b.html"{sel_b}>Appendix B: Scripture Index</option>'
    ch_selector += f'\n            <option value="appendix-c.html"{sel_c}>Appendix C: Small Group Exercises</option>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Appendix {letter.upper()}: {html_module.escape(title)} | Bridge Moments</title>
  <style>
{get_chapter_css()}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          Bridge Moments
        </a>
        <select onchange="if(this.value)window.location.href=this.value">
            {ch_selector}
        </select>
        <a href="../Noble_Mind_Study_Tool_v2.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          Noble Mind Study
        </a>
      </nav>

      <header>
        <p class="part-label">Appendix {letter.upper()}</p>
        <h1>{html_module.escape(title)}</h1>
        {f'<p class="subtitle">{html_module.escape(subtitle)}</p>' if subtitle else ''}
      </header>

      <div class="content">
{body_html}
      </div>

      <footer>
        <div class="footer-nav">
          <a href="{prev_href}">&larr; {html_module.escape(prev_text)}</a>
          <a href="{next_href}"{next_disabled}>{html_module.escape(next_text or "")}{" &rarr;" if next_text else ""}</a>
        </div>
        <p class="copyright">Bridge Moments: Making the Most of Every Opportunity &copy; Paul Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
</body>
</html>'''

# ─── MAIN ─────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate index
    print("Generating index.html...")
    index_html = generate_index_html()
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print("  -> index.html written")

    # Generate chapter pages
    for ch_meta in CHAPTERS:
        ch_num = ch_meta['num']
        docx_file = DOCX_FILES[ch_num]
        docx_path = os.path.join(DOCX_DIR, docx_file)

        if not os.path.exists(docx_path):
            print(f"  WARNING: {docx_file} not found, skipping")
            continue

        print(f"Processing Chapter {ch_num}: {ch_meta['title']}...")
        content = extract_chapter(docx_path, ch_num)

        # Count elements for verification
        q_count = sum(len(e['questions']) for e in content['elements'] if e['type'] == 'study_questions')
        box_count = sum(1 for e in content['elements'] if e['type'].endswith('_box'))
        para_count = sum(1 for e in content['elements'] if e['type'] == 'paragraph')

        html = generate_chapter_html(ch_meta, content)

        # Docx errata: Ch 12 says "Stephen" and "Philip" but should be "Philip" and "Paul"
        if ch_num == 12:
            html = html.replace(
                'a man named Stephen, a man named Philip',
                'a man named Philip, a man named Paul',
            )

        filename = f'chapter-{ch_num:02d}.html'
        with open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  -> {filename}: {para_count} paragraphs, {box_count} callout boxes, {q_count} study questions")

    # Generate appendix pages
    appendix_configs = {
        'a': {"title": "Quick Reference Chart", "subtitle": "15 Bridge Moment Encounters at a Glance", "extract": extract_appendix_a},
        'b': {"title": "Scripture Index", "subtitle": "", "extract": extract_appendix_b},
        'c': {"title": "Small Group Exercises", "subtitle": "Role-Play Scenarios & Group Activities", "extract": extract_appendix_c},
    }

    for letter, config in appendix_configs.items():
        docx_file = APPENDIX_FILES[letter]
        docx_path = os.path.join(DOCX_DIR, docx_file)

        if not os.path.exists(docx_path):
            print(f"  WARNING: {docx_file} not found, skipping")
            continue

        print(f"Processing Appendix {letter.upper()}: {config['title']}...")
        elements = config['extract'](docx_path)
        html = generate_appendix_html(letter, config['title'], config['subtitle'], elements)
        filename = f'appendix-{letter}.html'
        with open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  -> {filename}: {len(elements)} elements")

    print(f"\nDone! {20 + 3 + 1} files generated in {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
