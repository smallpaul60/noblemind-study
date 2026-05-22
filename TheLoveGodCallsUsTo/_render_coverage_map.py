#!/usr/bin/env python3
"""Render Willis_Workbook_Coverage_Map.md to a letter-size PDF for sharing."""

from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

BOOK_DIR = Path(__file__).parent
MD_FILE = BOOK_DIR / "Willis_Workbook_Coverage_Map.md"
PDF_FILE = BOOK_DIR / "Willis_Workbook_Coverage_Map.pdf"

FONT_DIR = Path.home() / ".local" / "share" / "fonts"

md_text = MD_FILE.read_text(encoding="utf-8")
body_html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Willis Workbook Coverage Map &mdash; The Love God Calls Us To</title>
</head>
<body>
  <div class="content">
    {body_html}
  </div>
</body>
</html>
"""

css_text = f"""
@font-face {{
  font-family: "EB Garamond";
  src: url("file://{FONT_DIR}/EBGaramond.ttf");
  font-weight: 400;
  font-style: normal;
}}
@font-face {{
  font-family: "EB Garamond";
  src: url("file://{FONT_DIR}/EBGaramond-Italic.ttf");
  font-weight: 400;
  font-style: italic;
}}
@font-face {{
  font-family: "EB Garamond";
  src: url("file://{FONT_DIR}/EBGaramond-Bold.ttf");
  font-weight: 700;
  font-style: normal;
}}

@page {{
  size: letter;
  margin: 0.85in 0.85in 0.95in 0.85in;
  @bottom-center {{
    content: counter(page);
    font-family: "EB Garamond", serif;
    font-size: 9.5pt;
    color: #6b5a3e;
  }}
}}

html, body {{
  font-family: "EB Garamond", "Times New Roman", serif;
  font-size: 11pt;
  line-height: 1.45;
  color: #1f1610;
}}

.content {{
  max-width: 100%;
}}

h1 {{
  font-size: 22pt;
  font-weight: 700;
  color: #1f1610;
  margin: 0 0 0.05in 0;
  text-align: center;
  line-height: 1.15;
}}

h2 {{
  font-size: 14pt;
  font-weight: 400;
  font-style: italic;
  color: #8a6a32;
  text-align: center;
  margin: 0.02in 0 0.35in 0;
  letter-spacing: 0.01em;
}}

h3 {{
  font-size: 13pt;
  font-weight: 700;
  color: #1f1610;
  margin: 0.32in 0 0.10in 0;
  border-bottom: 1.5pt solid #c4a864;
  padding-bottom: 4pt;
}}

h4 {{
  font-size: 11.5pt;
  font-weight: 700;
  color: #5a4220;
  margin: 0.20in 0 0.08in 0;
}}

p {{
  margin: 0 0 0.10in 0;
  text-align: justify;
  hyphens: auto;
}}

hr {{
  border: none;
  border-top: 0.5pt solid #c4a864;
  margin: 0.25in 0;
}}

blockquote {{
  margin: 0.10in 0.25in;
  padding: 6pt 12pt;
  border-left: 2pt solid #c4a864;
  background-color: #faf4e8;
  font-style: italic;
  color: #3a2c18;
}}

blockquote p {{
  margin-bottom: 0;
}}

strong {{
  font-weight: 700;
  color: #1f1610;
}}

em {{
  font-style: italic;
}}

code {{
  font-family: "Courier New", monospace;
  font-size: 10pt;
  background-color: #f5edd9;
  padding: 1pt 3pt;
  border-radius: 2pt;
}}

table {{
  width: 100%;
  border-collapse: collapse;
  margin: 0.12in 0 0.18in 0;
  font-size: 10pt;
  page-break-inside: avoid;
}}

th {{
  background-color: #5a4220;
  color: #f5edd9;
  padding: 5pt 8pt;
  text-align: left;
  font-weight: 700;
  border: 0.5pt solid #5a4220;
}}

td {{
  padding: 5pt 8pt;
  border: 0.5pt solid #c4a864;
  vertical-align: top;
  background-color: #fdfaf3;
}}

tr:nth-child(even) td {{
  background-color: #f9f1de;
}}

/* Make Willis sub-Q first column compact */
table td:first-child {{
  white-space: nowrap;
}}
table:last-of-type td:first-child {{
  white-space: normal;
}}
"""

font_config = FontConfiguration()
HTML(string=html_template, base_url=str(BOOK_DIR)).write_pdf(
    target=str(PDF_FILE),
    stylesheets=[CSS(string=css_text, font_config=font_config)],
    font_config=font_config,
)

print(f"PDF saved to {PDF_FILE}")
