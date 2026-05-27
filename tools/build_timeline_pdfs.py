#!/usr/bin/env python3
"""Build PDF versions of the Apostle Paul timeline spokes.

Reads each spoke's HTML, extracts the JS data arrays (events, PHASES,
comparisons, commentaries) via Node, renders to static print-ready
HTML with the same parchment aesthetic as the on-screen version,
then runs WeasyPrint to produce a PDF.

Outputs seven PDFs into apostle-paul/:
  Paul_Life_Timeline.pdf
  Paul_Corinth_Timeline.pdf
  Paul_Ephesus_Timeline.pdf
  Paul_Roman_Years_Timeline.pdf
  Paul_Jerusalem_Visits_Timeline.pdf
  Paul_Antioch_Timeline.pdf
  Paul_Conversion_Timeline.pdf
"""
import html as html_lib
import json
import subprocess
import sys
from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
APOSTLE_DIR = ROOT / "apostle-paul"  # legacy default; per-spoke `dir` field overrides


def spoke_dir(spoke):
    """Resolve a spoke's working directory (defaults to apostle-paul/)."""
    return ROOT / spoke.get("dir", "apostle-paul")

# Parchment palette (same as the HTML spokes)
PARCHMENT = "#F5EDD6"
INK = "#2A1A05"
SEPIA = "#6B4C1A"
SEPIA_LIGHT = "#A07840"
GOLD = "#C4A44A"
GRAY = "#5A5A5A"


SPOKES = [
    {
        "kind": "life",
        "source": "index.html",
        "output": "Paul_Life_Timeline.pdf",
        "title": "The Life of the Apostle Paul",
        "subtitle": "A Comprehensive Chronological Timeline",
        "date_range": "c. AD 5 – c. AD 67",
    },
    {
        "kind": "chronological",
        "source": "corinth.html",
        "output": "Paul_Corinth_Timeline.pdf",
        "title": "Paul & the Corinthian Church",
        "subtitle": "A Comprehensive Chronological Timeline",
        "date_range": "c. AD 49 – AD 58",
    },
    {
        "kind": "chronological",
        "source": "ephesus.html",
        "output": "Paul_Ephesus_Timeline.pdf",
        "title": "Paul & the Ephesian Church",
        "subtitle": "A Comprehensive Chronological Timeline",
        "date_range": "c. AD 52 – c. AD 95",
    },
    {
        "kind": "chronological",
        "source": "roman-years.html",
        "output": "Paul_Roman_Years_Timeline.pdf",
        "title": "Paul’s Roman Years",
        "subtitle": "The Voyage, the House Arrest, the Pastoral Period, and the Martyrdom",
        "date_range": "c. AD 59 – c. AD 67",
    },
    {
        "kind": "chronological",
        "source": "jerusalem-visits.html",
        "output": "Paul_Jerusalem_Visits_Timeline.pdf",
        "title": "Paul’s Five Visits to Jerusalem",
        "subtitle": "From Fugitive to Courier to Defender of the Gospel to Prisoner",
        "date_range": "c. AD 37 – c. AD 57",
    },
    {
        "kind": "chronological",
        "source": "antioch.html",
        "output": "Paul_Antioch_Timeline.pdf",
        "title": "Paul & the Church at Antioch",
        "subtitle": "The Sending Church — From Hellenist Refugees to the Apostolic Sending Base",
        "date_range": "c. AD 33 – c. AD 52",
    },
    {
        "kind": "conversion",
        "source": "conversion.html",
        "output": "Paul_Conversion_Timeline.pdf",
        "title": "Paul’s Conversion in Three Tellings",
        "subtitle": "Acts 9 · Acts 22 · Acts 26 — Side by Side",
        "date_range": "",
    },
    {
        "kind": "ot",
        "dir": "old-testament-timeline",
        "source": "index.html",
        "output": "Old_Testament_Timeline.pdf",
        "title": "The Old Testament Timeline",
        "subtitle": "From Creation to Malachi — The Unfolding of God’s Plan",
        "date_range": "c. 4000 BC – c. 400 BC",
    },
]


def extract_js_array(html_path: Path, var_name: str):
    """Use Node to evaluate a JS array literal in the page and return as Python data.

    Also picks up any `const DEEPDIVE_* = { ... };` declarations so the events
    array can reference them by name without ReferenceError.
    """
    script = """
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const varName = process.argv[2];

// Pre-define DEEPDIVE_* and BOOK_* constants so references inside the events array resolve.
const constPattern = /const ((?:DEEPDIVE|BOOK)_[A-Z_]+) = (\\{[^}]*\\});/g;
let preamble = '';
let m1;
while ((m1 = constPattern.exec(html)) !== null) {
  preamble += 'const ' + m1[1] + ' = ' + m1[2] + ';\\n';
}

const pattern = new RegExp('const ' + varName + ' = (\\\\[[\\\\s\\\\S]*?\\\\n\\\\]);');
const m = html.match(pattern);
if (!m) { process.stdout.write('null'); process.exit(0); }
const data = eval(preamble + m[1]);
process.stdout.write(JSON.stringify(data));
"""
    result = subprocess.run(
        ["node", "-e", script, str(html_path), var_name],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Node failed extracting {var_name} from {html_path}: {result.stderr}")
    return json.loads(result.stdout)


def extract_types(html_path: Path) -> dict:
    """Extract the TYPES dictionary (typename -> {color, bg})."""
    script = """
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const m = html.match(/const TYPES = (\\{[\\s\\S]*?\\n\\});/);
if (!m) { process.stdout.write('{}'); process.exit(0); }
const data = eval('(' + m[1] + ')');
process.stdout.write(JSON.stringify(data));
"""
    result = subprocess.run(
        ["node", "-e", script, str(html_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Node failed extracting TYPES from {html_path}: {result.stderr}")
    return json.loads(result.stdout)


# ============================================================
# Static HTML rendering
# ============================================================

PRINT_CSS = f"""
@page {{
  size: letter;
  margin: 0.75in 0.7in 0.75in 0.7in;
  background: {PARCHMENT};
  @bottom-center {{
    content: "Page " counter(page) " of " counter(pages);
    color: {SEPIA};
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 9pt;
    font-style: italic;
  }}
}}
@page :first {{
  @bottom-center {{ content: ""; }}
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: 'EB Garamond', Georgia, serif;
  color: {INK};
  font-size: 10.5pt;
  line-height: 1.55;
  margin: 0;
  padding: 0;
  background: {PARCHMENT};
}}
.title-page {{
  page-break-after: always;
  text-align: center;
  padding-top: 2.5in;
  position: relative;
  min-height: 9in; /* fill the page so .source absolute-positions to the bottom */
}}
.title-page h1 {{
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 32pt;
  color: {SEPIA};
  margin: 0 0 18pt 0;
  font-weight: normal;
  letter-spacing: 0.5pt;
  line-height: 1.15;
}}
.title-page h2 {{
  font-family: Georgia, serif;
  font-style: italic;
  font-size: 16pt;
  color: {SEPIA_LIGHT};
  margin: 0 0 30pt 0;
  font-weight: normal;
  line-height: 1.3;
  padding: 0 0.5in;
}}
.title-page .date-range {{
  font-family: Georgia, serif;
  font-style: italic;
  font-size: 13pt;
  color: {INK};
  margin-top: 18pt;
}}
.title-page .rule {{
  width: 2in;
  height: 1pt;
  background: {GOLD};
  margin: 30pt auto;
}}
.title-page .note {{
  font-style: italic;
  font-size: 10pt;
  color: {GRAY};
  max-width: 5in;
  margin: 1in auto 0 auto;
  line-height: 1.55;
}}
.title-page .source {{
  text-align: center;
  font-size: 9pt;
  color: {GRAY};
  font-style: italic;
  margin: 18pt auto 0 auto;
}}
.phase {{
  text-align: center;
  margin: 24pt 0 12pt 0;
  page-break-after: avoid;
}}
.phase-label {{
  display: inline-block;
  background: {SEPIA};
  color: {PARCHMENT};
  font-family: Georgia, serif;
  font-size: 11pt;
  padding: 5pt 14pt;
  border-radius: 3pt;
  letter-spacing: 0.3pt;
}}
.event, .comparison {{
  border-left: 3pt solid;
  background: rgba(255,255,255,0.5);
  padding: 9pt 12pt;
  margin: 0 0 12pt 0;
  border-radius: 2pt;
  page-break-inside: avoid;
}}
.event-date {{
  font-family: Georgia, serif;
  font-style: italic;
  font-size: 9.5pt;
  color: {SEPIA_LIGHT};
  margin-bottom: 2pt;
}}
.event-type {{
  display: inline-block;
  font-size: 8pt;
  font-weight: bold;
  padding: 1pt 7pt;
  border-radius: 8pt;
  color: white;
  margin-bottom: 4pt;
  letter-spacing: 0.3pt;
}}
.event-title {{
  font-size: 11.5pt;
  font-weight: bold;
  color: {INK};
  margin: 2pt 0 4pt 0;
  line-height: 1.3;
}}
.event-ref {{
  font-family: Georgia, serif;
  font-style: italic;
  font-size: 9.5pt;
  color: {SEPIA};
  margin-bottom: 5pt;
}}
.event-detail {{
  font-size: 10pt;
  line-height: 1.55;
  color: #2a2a2a;
  margin-top: 5pt;
}}
.event-detail p {{ margin: 0 0 5pt 0; }}
.event-secondary {{
  margin-top: 6pt;
  padding: 6pt 9pt;
  background: rgba(196,164,74,0.10);
  border-left: 2pt solid {GOLD};
  font-size: 9pt;
  color: {GRAY};
  font-style: italic;
  border-radius: 0 2pt 2pt 0;
}}
.deep-dive-note {{
  margin-top: 6pt;
  font-size: 9pt;
  color: {SEPIA};
  font-style: italic;
}}
/* Conversion-spoke specific */
.intro-card {{
  background: white;
  border-left: 3pt solid {GOLD};
  padding: 12pt 14pt;
  margin-bottom: 14pt;
  page-break-inside: avoid;
}}
.intro-card h3 {{
  font-family: Georgia, serif;
  color: {SEPIA};
  font-size: 14pt;
  margin: 0 0 8pt 0;
}}
.intro-card p {{ margin: 0 0 6pt 0; font-size: 10pt; line-height: 1.55; }}
.intro-card p:last-child {{ margin-bottom: 0; }}
.feature-title {{
  font-family: Georgia, serif;
  color: {SEPIA};
  font-size: 13pt;
  font-weight: bold;
  margin-bottom: 8pt;
  padding-bottom: 3pt;
  border-bottom: 0.5pt solid rgba(107, 76, 26, 0.25);
}}
.telling {{
  margin-bottom: 6pt;
  padding: 6pt 10pt;
  background: rgba(245, 237, 214, 0.5);
  border-left: 2.5pt solid;
  border-radius: 0 2pt 2pt 0;
}}
.telling-acts9  {{ border-left-color: #8B2020; }}
.telling-acts22 {{ border-left-color: #1A3A6B; }}
.telling-acts26 {{ border-left-color: #2A5C2A; }}
.telling-label {{
  display: inline-block;
  font-size: 8pt;
  font-weight: bold;
  color: white;
  padding: 1pt 6pt;
  border-radius: 7pt;
  margin-right: 6pt;
}}
.telling-acts9  .telling-label {{ background: #8B2020; }}
.telling-acts22 .telling-label {{ background: #1A3A6B; }}
.telling-acts26 .telling-label {{ background: #2A5C2A; }}
.telling-body {{ font-size: 9.5pt; line-height: 1.5; color: #2a2a2a; margin-top: 3pt; }}
.telling-body em {{ font-style: italic; color: {INK}; }}
.telling-ref {{ font-size: 8.5pt; color: {SEPIA}; font-style: italic; }}
.telling-absent {{ font-style: italic; color: {SEPIA_LIGHT}; }}
.feature-note {{
  margin-top: 6pt;
  padding: 6pt 9pt;
  background: rgba(196,164,74,0.12);
  border-left: 2pt solid {GOLD};
  font-size: 9pt;
  color: {GRAY};
  font-style: italic;
  border-radius: 0 2pt 2pt 0;
}}
.feature-note strong {{ color: {SEPIA}; font-style: normal; }}
.section-heading {{
  font-family: Georgia, serif;
  color: {SEPIA};
  font-size: 18pt;
  text-align: center;
  margin: 24pt 0 12pt 0;
  page-break-before: always;
  page-break-after: avoid;
}}
.commentary-card {{
  border-left: 3pt solid #4A1A6B;
  background: rgba(255,255,255,0.6);
  padding: 10pt 14pt;
  margin-bottom: 12pt;
  page-break-inside: avoid;
}}
.commentary-card h4 {{
  font-family: Georgia, serif;
  color: #4A1A6B;
  font-size: 13pt;
  margin: 0 0 6pt 0;
}}
.commentary-card p {{ margin: 0 0 6pt 0; font-size: 10pt; line-height: 1.55; }}
.commentary-card blockquote {{
  margin: 6pt 0 6pt 12pt;
  padding-left: 9pt;
  border-left: 1.5pt solid {GOLD};
  color: {INK};
  font-style: italic;
  font-size: 9.5pt;
}}
footer.print-footer {{
  margin-top: 18pt;
  padding-top: 8pt;
  border-top: 0.5pt solid rgba(107, 76, 26, 0.3);
  font-size: 8.5pt;
  color: {GRAY};
  font-style: italic;
  text-align: center;
  line-height: 1.5;
  page-break-inside: avoid;
}}
footer.print-footer p {{ margin: 2pt 0; }}
"""


def title_page(spoke):
    note = ""
    if spoke["kind"] == "life":
        note = ("This timeline draws together every event Scripture records of Paul's life, "
                "from his birth at Tarsus to the martyrdom under Nero. Events marked with a "
                "secondary reference rest on dates from Roman or Jewish sources outside the "
                "biblical text.")
    elif spoke["kind"] == "chronological":
        note = ("This is a focused timeline. For the broader chronology of Paul's life, "
                "consult the parent timeline (Paul_Life_Timeline.pdf).")
    elif spoke["kind"] == "conversion":
        note = ("The three accounts in Acts of Paul's conversion are not three independent "
                "witnesses; they are the same event narrated for three different audiences. "
                "This document lays them side by side feature-by-feature, with commentary on "
                "the apparent contradictions.")
    elif spoke["kind"] == "ot":
        note = ("One hundred fifteen events across thirteen phases. Structural framework drawn "
                "from Bob Waldron's teaching. Hebrew Masoretic chronology with the Exodus at "
                "1446 BC; pre-patriarchal dates use the broader Ussher-style framework.")

    site_path = spoke.get("dir", "apostle-paul") + "/"
    return f"""<div class="title-page">
  <h1>{spoke['title']}</h1>
  <h2>{spoke['subtitle']}</h2>
  {f'<div class="date-range">{spoke["date_range"]}</div>' if spoke['date_range'] else ''}
  <div class="rule"></div>
  <div class="source">Primary Source: Holy Scripture &nbsp;&middot;&nbsp; noblemind.study/{site_path}</div>
  <div class="note">{note}</div>
</div>"""


def render_event(event, types_map):
    """Render a single event card to HTML."""
    type_name = event.get("type", "")
    type_color = types_map.get(type_name, {}).get("color") or SEPIA

    parts = [f'<div class="event" style="border-left-color:{type_color};">']
    if event.get("date"):
        parts.append(f'<div class="event-date">{html_lib.escape(event["date"])}</div>')
    if type_name:
        parts.append(
            f'<span class="event-type" style="background:{type_color};">'
            f'{html_lib.escape(type_name)}</span>'
        )
    if event.get("title"):
        parts.append(f'<div class="event-title">{event["title"]}</div>')
    if event.get("ref"):
        parts.append(f'<div class="event-ref">&#128214; {event["ref"]}</div>')
    if event.get("detail"):
        parts.append(f'<div class="event-detail"><p>{event["detail"]}</p></div>')
    if event.get("secondary"):
        parts.append(f'<div class="event-secondary">{event["secondary"]}</div>')
    # Accept either deepDive (single) or deepDives (array)
    deep_dives = event.get("deepDives") or (
        [event["deepDive"]] if event.get("deepDive") else []
    )
    for dd in deep_dives:
        if dd and dd.get("label"):
            parts.append(
                f'<div class="deep-dive-note">&rarr; {html_lib.escape(dd["label"])}</div>'
            )
    if event.get("bookLink") and event["bookLink"].get("label"):
        parts.append(
            f'<div class="deep-dive-note">&rarr; {html_lib.escape(event["bookLink"]["label"])}</div>'
        )
    parts.append('</div>')
    return "\n".join(parts)


def render_chronological(spoke):
    source = spoke_dir(spoke) / spoke["source"]
    events = extract_js_array(source, "events")
    phases = extract_js_array(source, "PHASES") or []
    # Some pages name it PHASE_LABELS instead (Life timeline)
    phase_labels = extract_js_array(source, "PHASE_LABELS") or []
    phase_of = None  # only Life timeline uses PHASE_OF mapping
    if not phases and phase_labels:
        # Life timeline uses PHASE_OF (event type -> phase index)
        phase_of_raw = subprocess.run(
            ["node", "-e",
             "const fs=require('fs');"
             f"const h=fs.readFileSync('{source}','utf8');"
             "const m=h.match(/const PHASE_OF = (\\{[\\s\\S]*?\\n\\});/);"
             "if(!m){process.stdout.write('null');process.exit(0);}"
             "process.stdout.write(JSON.stringify(eval('('+m[1]+')')));"
            ], capture_output=True, text=True
        )
        if phase_of_raw.returncode == 0 and phase_of_raw.stdout.strip() != "null":
            phase_of = json.loads(phase_of_raw.stdout)

    types_map = extract_types(source)

    body_parts = [title_page(spoke)]

    if phase_of is not None and phase_labels:
        # Life-timeline style: phases driven by event-type membership
        last_phase = None
        for ev in events:
            phase_idx = phase_of.get(ev.get("type"))
            if phase_idx is not None and phase_idx != last_phase:
                body_parts.append(
                    f'<div class="phase"><span class="phase-label">{html_lib.escape(phase_labels[phase_idx])}</span></div>'
                )
                last_phase = phase_idx
            body_parts.append(render_event(ev, types_map))
    elif phases:
        # Spoke-style: phases have explicit `before` index
        # Index events; insert phase header before each `before` index
        phases_by_before = {p["before"]: p["label"] for p in phases}
        for i, ev in enumerate(events):
            if i in phases_by_before:
                body_parts.append(
                    f'<div class="phase"><span class="phase-label">{html_lib.escape(phases_by_before[i])}</span></div>'
                )
            body_parts.append(render_event(ev, types_map))
    else:
        for ev in events:
            body_parts.append(render_event(ev, types_map))

    site_url = f"https://noblemind.study/{spoke.get('dir', 'apostle-paul')}/"
    body_parts.append(
        '<footer class="print-footer">'
        '<p>Compiled from the Holy Bible &middot; '
        f'<a href="{site_url}" style="color:inherit;">{site_url[8:]}</a></p>'
        '<p>Generated automatically &mdash; this document mirrors the interactive timeline online.</p>'
        '</footer>'
    )

    return wrap_html(spoke["title"], "".join(body_parts))


def render_conversion(spoke):
    source = spoke_dir(spoke) / spoke["source"]
    comparisons = extract_js_array(source, "comparisons")
    commentaries = extract_js_array(source, "commentaries")

    body_parts = [title_page(spoke)]

    # Intro card (echo of the on-screen intro)
    body_parts.append(
        '<div class="intro-card">'
        '<h3>Why three tellings?</h3>'
        '<p>Luke records Paul&rsquo;s conversion three times in Acts, and Paul mentions it briefly in his own letters. The three accounts in Acts are not three independent witnesses; they are the same event narrated for three different audiences:</p>'
        '<p><strong style="color:#8B2020;">Acts 9:1&ndash;19</strong> &mdash; Luke&rsquo;s third-person narrative for Theophilus. Comprehensive, with full detail about Ananias and the recovery from blindness.</p>'
        '<p><strong style="color:#1A3A6B;">Acts 22:1&ndash;21</strong> &mdash; Paul&rsquo;s own defense to the Jerusalem temple-mob from the Antonia stairs. Hebrew language, Jewish bona fides emphasized.</p>'
        '<p><strong style="color:#2A5C2A;">Acts 26:1&ndash;23</strong> &mdash; Paul&rsquo;s defense to King Herod Agrippa II, Festus, and the leading men of Caesarea. The commission Christ delivered directly is emphasized; the Ananias episode is omitted as irrelevant to the kingly audience.</p>'
        '</div>'
    )

    # Comparison cards
    for cmp_ in comparisons:
        parts = [f'<div class="comparison">']
        parts.append(f'<div class="feature-title">{html_lib.escape(cmp_["feature"])}</div>')
        for key, label in [("acts9", "Acts 9"), ("acts22", "Acts 22"), ("acts26", "Acts 26")]:
            entry = cmp_.get(key, {})
            ref = entry.get("ref") or ""
            body = entry.get("body") or ""
            ref_html = f'<span class="telling-ref">{html_lib.escape(ref)}</span>' if ref else ""
            parts.append(
                f'<div class="telling telling-{key}">'
                f'<span class="telling-label">{label}</span>{ref_html}'
                f'<div class="telling-body">{body}</div>'
                f'</div>'
            )
        if cmp_.get("note"):
            parts.append(f'<div class="feature-note">{cmp_["note"]}</div>')
        parts.append('</div>')
        body_parts.append("\n".join(parts))

    # Commentary section
    if commentaries:
        body_parts.append('<div class="section-heading">Commentary</div>')
        for c in commentaries:
            body_parts.append(
                f'<div class="commentary-card">'
                f'<h4>{html_lib.escape(c["title"])}</h4>'
                f'{c["body"]}'
                f'</div>'
            )

    body_parts.append(
        '<footer class="print-footer">'
        '<p>Compiled from the Holy Bible &middot; '
        '<a href="https://noblemind.study/apostle-paul/conversion.html" style="color:inherit;">noblemind.study/apostle-paul/conversion.html</a></p>'
        '<p>Generated automatically &mdash; this document mirrors the interactive comparison online.</p>'
        '</footer>'
    )

    return wrap_html(spoke["title"], "".join(body_parts))


def wrap_html(title, body):
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{html_lib.escape(title)}</title>
  <style>{PRINT_CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def main():
    print(f"Building timeline PDFs\n")
    for spoke in SPOKES:
        sd = spoke_dir(spoke)
        source = sd / spoke["source"]
        output = sd / spoke["output"]
        if not source.exists():
            print(f"  SKIP   {spoke['output']:<42} (source {spoke['source']} not found)")
            continue
        print(f"  build  {spoke['output']:<42} <- {sd.name}/{spoke['source']}")
        if spoke["kind"] == "conversion":
            html = render_conversion(spoke)
        else:
            html = render_chronological(spoke)
        HTML(string=html, base_url=str(sd)).write_pdf(str(output))
        size_kb = output.stat().st_size / 1024
        print(f"         {size_kb:>7.1f} KB")
    print("\nDone.")


if __name__ == "__main__":
    main()
