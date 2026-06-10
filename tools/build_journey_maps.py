#!/usr/bin/env python3
"""
Build the interactive parchment journey maps for The Church Christ Built.

Fully owned + offline-first: projects public-domain Natural Earth 50m land
polygons to an inline SVG parchment basemap, overlays each missionary
journey's route (ordered stops from maps/data/locations.json), and emits a
self-contained HTML page with a journey selector and clickable stops.

No external tiles, no runtime dependencies. Run:
    python3 tools/build_journey_maps.py
Input:  /tmp/ne_land.geojson (Natural Earth ne_50m_land, public domain)
Output: the-church-christ-built/journey-maps.html
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NE = "/tmp/ne_land.geojson"
LOC = os.path.join(ROOT, "maps/data/locations.json")
OUT = os.path.join(ROOT, "the-church-christ-built/journey-maps.html")

# Region viewport (lon/lat) covering all four journeys
LON0, LON1 = 11.0, 37.8
LAT0, LAT1 = 29.3, 43.0
LAT_MID = math.radians((LAT0 + LAT1) / 2)
COSL = math.cos(LAT_MID)
SCALE = 1000.0 / ((LON1 - LON0) * COSL)   # px per adjusted-degree -> ~1000 wide
W = (LON1 - LON0) * COSL * SCALE
H = (LAT1 - LAT0) * SCALE

def proj(lon, lat):
    x = (lon - LON0) * COSL * SCALE
    y = (LAT1 - lat) * SCALE
    return round(x, 1), round(y, 1)

# ---- Coordinates: from locations.json + a couple of hand-added stops ----
loc = {r["name"].lower(): (r["lat"], r["lon"]) for r in json.load(open(LOC))}
loc["antioch (syria)"] = (36.20, 36.16)     # Antioch on the Orontes (home base)
loc["pisidian antioch"] = (38.31, 31.19)    # Antioch of Pisidia
loc["seleucia"] = (36.12, 35.93)
loc["alexandria"] = (31.20, 29.92)          # Egypt — home port of the grain ship

def C(name):
    k = name.lower()
    if k not in loc:
        raise SystemExit(f"missing coord for {name!r}")
    return loc[k]

# ---- The journeys: ordered stops {name, ref, note}, and a return-to flag ----
JOURNEYS = [
    {
        "id": "first", "label": "First Journey", "ref": "Acts 13–14", "color": "#9C6B1E",
        "blurb": "From Antioch in Syria, with Barnabas — across Cyprus and into the highlands of Asia Minor, and back.",
        "returns_to": "Antioch (Syria)",
        "stops": [
            ("Antioch (Syria)", "Acts 13:1–3", "Sent out by the Spirit"),
            ("Salamis", "Acts 13:5", "Preaching in the synagogues of Cyprus"),
            ("Paphos", "Acts 13:6–12", "Sergius Paulus believes; Elymas struck blind"),
            ("Perga", "Acts 13:13", "John Mark turns back"),
            ("Pisidian Antioch", "Acts 13:14–50", "The synagogue sermon; turning to the Gentiles"),
            ("Iconium", "Acts 14:1–6", "Many believe; a plot drives them out"),
            ("Lystra", "Acts 14:8–20", "The lame man healed; Paul stoned"),
            ("Derbe", "Acts 14:20–21", "Many disciples made; then they retrace their steps"),
        ],
    },
    {
        "id": "second", "label": "Second Journey", "ref": "Acts 15:36–18:22", "color": "#2B5C86",
        "blurb": "With Silas and Timothy — the Macedonian call carries the gospel into Europe: Philippi, Athens, Corinth.",
        "returns_to": "Antioch (Syria)",
        "stops": [
            ("Antioch (Syria)", "Acts 15:36", "A new start, with Silas"),
            ("Derbe", "Acts 16:1", "Revisiting the churches"),
            ("Lystra", "Acts 16:1–3", "Timothy joins"),
            ("Pisidian Antioch", "Acts 16:6", "Through Phrygia and Galatia"),
            ("Troas", "Acts 16:8–10", "The vision of the man of Macedonia"),
            ("Neapolis", "Acts 16:11", "The gospel lands in Europe"),
            ("Philippi", "Acts 16:12–40", "Lydia and the jailer"),
            ("Thessalonica", "Acts 17:1–9", "‘These who have upset the world’"),
            ("Berea", "Acts 17:10–14", "Examining the Scriptures daily"),
            ("Athens", "Acts 17:16–34", "The Areopagus"),
            ("Corinth", "Acts 18:1–17", "Eighteen months; Gallio"),
            ("Ephesus", "Acts 18:19–21", "A brief first visit"),
            ("Caesarea", "Acts 18:22", "Landing on the way home"),
        ],
    },
    {
        "id": "third", "label": "Third Journey", "ref": "Acts 18:23–21:16", "color": "#2E6B43",
        "blurb": "Two years at Ephesus, then back through Macedonia and Greece, and on toward Jerusalem.",
        "returns_to": None,
        "stops": [
            ("Antioch (Syria)", "Acts 18:23", "Strengthening the disciples"),
            ("Pisidian Antioch", "Acts 18:23", "Through Galatia and Phrygia"),
            ("Ephesus", "Acts 19:1–41", "Two years; the riot of the silversmiths"),
            ("Philippi", "Acts 20:1–2", "Through Macedonia"),
            ("Corinth", "Acts 20:2–3", "Three months in Greece"),
            ("Troas", "Acts 20:6–12", "Eutychus raised on the first day of the week"),
            ("Assos", "Acts 20:13–14", "Paul goes by land"),
            ("Miletus", "Acts 20:15–38", "Farewell to the Ephesian elders"),
            ("Tyre", "Acts 21:3–6", "Seven days with the disciples"),
            ("Ptolemais", "Acts 21:7", "A day with the brethren"),
            ("Caesarea", "Acts 21:8–14", "‘The Lord’s will be done’"),
            ("Jerusalem", "Acts 21:15–17", "The journey’s end"),
        ],
    },
    {
        "id": "rome", "label": "The Voyage to Rome", "ref": "Acts 27–28", "color": "#8B2A3A",
        "blurb": "A prisoner bound for Caesar — storm, shipwreck at Malta, and at last the capital of the world.",
        "returns_to": None,
        "stops": [
            ("Caesarea", "Acts 27:1–2", "Sailing for Italy under guard"),
            ("Sidon", "Acts 27:3", "Friends allowed to care for him"),
            ("Myra", "Acts 27:5–6", "Transferred to an Alexandrian ship"),
            ("Cnidus", "Acts 27:7", "The wind against them"),
            ("Fair Havens", "Acts 27:8–13", "‘Men, I perceive this voyage will be with disaster’"),
            ("Malta", "Acts 27:39–28:10", "Shipwrecked; all 276 saved; the viper"),
            ("Syracuse", "Acts 28:12", "Three days"),
            ("Rhegium", "Acts 28:13", "A day"),
            ("Puteoli", "Acts 28:13–14", "Brethren; seven days"),
            ("Rome", "Acts 28:14–31", "Preaching the kingdom — unhindered"),
        ],
    },
]

# ---- Land basemap: project NE polygons within the viewport ----
def ring_to_path(ring):
    pts, last = [], None
    for lon, lat in ring:
        x, y = proj(lon, lat)
        if last is not None and abs(x - last[0]) < 0.6 and abs(y - last[1]) < 0.6:
            continue  # decimate sub-pixel points
        pts.append((x, y)); last = (x, y)
    if len(pts) < 3:
        return None
    return "M" + " ".join(f"{x},{y}" for x, y in pts) + "Z"

def bbox_hits(coords):
    xs = [c[0] for c in coords]; ys = [c[1] for c in coords]
    return not (max(xs) < LON0 - 2 or min(xs) > LON1 + 2 or max(ys) < LAT0 - 2 or min(ys) > LAT1 + 2)

land_paths = []
for feat in json.load(open(NE))["features"]:
    geom = feat["geometry"]; polys = []
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polys = geom["coordinates"]
    for poly in polys:
        outer = poly[0]
        if not bbox_hits(outer):
            continue
        for ring in poly:  # outer + holes (holes rare at this scale; drawn as same fill is fine)
            p = ring_to_path(ring)
            if p:
                land_paths.append(p)

LAND = "".join(f'<path d="{p}"/>' for p in land_paths)

# ---- Nile river (SE context) ----
RIVERS = ""
try:
    for feat in json.load(open("/tmp/ne_rivers.geojson"))["features"]:
        if (feat["properties"].get("name") or "").lower() != "nile":
            continue
        g = feat["geometry"]; lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for line in lines:
            pts, last = [], None
            for lon, lat in line:
                if not (LON0 - 1 <= lon <= LON1 + 1 and LAT0 - 1 <= lat <= LAT1 + 1):
                    continue
                x, y = proj(lon, lat)
                if last and abs(x - last[0]) < 0.4 and abs(y - last[1]) < 0.4:
                    continue
                pts.append((x, y)); last = (x, y)
            if len(pts) >= 2:
                RIVERS += '<path d="M%s"/>' % " ".join(f"{x},{y}" for x, y in pts)
except FileNotFoundError:
    pass

# ---- region + sea labels, context cities (static layers) ----
def lblsvg(items, cls):
    out = []
    for it in items:
        txt, lon, lat = it[0], it[1], it[2]; rot = it[3] if len(it) > 3 else 0
        x, y = proj(lon, lat)
        ts = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else 12}">{ln}</tspan>' for i, ln in enumerate(txt.split("\n")))
        out.append(f'<text class="{cls}" transform="rotate({rot} {x} {y})" x="{x}" y="{y}">{ts}</text>')
    return "".join(out)

REGIONS = [
    ("ITALY", 14.6, 41.4), ("SICILY", 14.3, 37.4), ("MACEDONIA", 22.3, 41.2), ("ACHAIA", 22.2, 38.2),
    ("THRACE", 26.4, 41.6), ("ASIA", 27.7, 38.9), ("BITHYNIA", 30.7, 40.8), ("GALATIA", 33.3, 39.5),
    ("CAPPADOCIA", 35.6, 38.8), ("PISIDIA", 30.9, 37.7), ("PAMPHYLIA", 31.1, 36.85), ("CILICIA", 34.4, 37.15),
    ("SYRIA", 37.1, 35.0), ("CYPRUS", 33.2, 34.95), ("CRETE", 24.9, 34.85), ("JUDEA", 35.25, 31.4), ("EGYPT", 30.5, 30.2),
]
WATERS = [
    ("The Great Sea", 18.5, 33.6, -10), ("Aegean\nSea", 24.8, 38.3, 0), ("Adriatic\nSea", 16.6, 41.0, -58),
    ("Black Sea", 32.5, 42.4, 0), ("Nile", 30.9, 29.6, -80),
]
CONTEXT = [("Tarsus", "Paul's home city (Acts 9:11; 21:39)"),
           ("Alexandria", "Home port of the grain ship that carried Paul toward Rome (Acts 27:6)")]
def ctxsvg():
    out = []
    for name, note in CONTEXT:
        lat, lon = C(name); x, y = proj(lon, lat)
        right = x < W - 90
        out.append(f'<g class="context" data-name="{name}" data-note="{note}">'
                   f'<circle cx="{x}" cy="{y}" r="2.6"/>'
                   f'<text x="{x + (7 if right else -7)}" y="{y + 3}" text-anchor="{"start" if right else "end"}">{name}</text></g>')
    return "".join(out)
REGION_SVG = lblsvg(REGIONS, "region")
WATER_SVG = lblsvg(WATERS, "water-lbl")
CONTEXT_SVG = ctxsvg()

# ---- Project journeys ----
out_journeys = []
for j in JOURNEYS:
    stops = []
    for name, ref, note in j["stops"]:
        lat, lon = C(name)
        x, y = proj(lon, lat)
        stops.append({"name": name.replace(" (Syria)", ""), "x": x, "y": y, "ref": ref, "note": note})
    ret = None
    if j["returns_to"]:
        lat, lon = C(j["returns_to"])
        ret = list(proj(lon, lat))
    out_journeys.append({"id": j["id"], "label": j["label"], "ref": j["ref"],
                         "color": j["color"], "blurb": j["blurb"], "stops": stops, "ret": ret})

JJSON = json.dumps(out_journeys, ensure_ascii=False)
VB = f"0 0 {round(W)} {round(H)}"

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Missionary Journeys — Map | The Church Christ Built</title>
<link rel="canonical" href="https://noblemind.study/the-church-christ-built/journey-maps.html">
<meta name="description" content="Interactive parchment maps of Paul's missionary journeys and the voyage to Rome, from the book of Acts — every stop a click away, with its Scripture reference.">
<style>
  @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
  :root {{ --parchment:#F5EDD6; --sea:#EFE6CB; --land:#E1CFA4; --land-line:#C9B485; --ink:#2A1A05; --sepia:#6B4C1A; --sepia-light:#A07840; --gold:#C4A44A; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Crimson Text',Georgia,serif; background:var(--parchment); color:var(--ink); }}
  header {{ text-align:center; padding:34px 20px 18px; border-bottom:3px double var(--gold); position:relative; }}
  .backlink {{ position:absolute; left:18px; top:14px; font-size:13px; color:var(--sepia); text-decoration:none; border:1px solid rgba(107,76,26,.3); border-radius:4px; padding:4px 10px; background:rgba(245,237,214,.6); }}
  .backlink:hover {{ background:rgba(196,164,74,.2); }}
  h1 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:clamp(24px,3.4vw,40px); }}
  .sub {{ font-family:'IM Fell English',serif; font-style:italic; color:var(--sepia-light); font-size:15px; margin-top:6px; }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:18px 14px 60px; }}
  .tabs {{ display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:14px 0 6px; }}
  .tab {{ font-family:'IM Fell English',serif; font-size:14px; padding:7px 16px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); transition:all .16s; }}
  .tab:hover {{ background:rgba(196,164,74,.12); }}
  .tab.active {{ color:#fff; }}
  .blurb {{ text-align:center; font-style:italic; color:var(--sepia); font-size:14px; max-width:720px; margin:8px auto 12px; min-height:2.6em; }}
  .mapbox {{ position:relative; background:var(--sea); border:2px solid var(--land-line); border-radius:10px; overflow:hidden; box-shadow:0 3px 14px rgba(42,26,5,.12); touch-action:none; }}
  svg {{ display:block; width:100%; height:auto; cursor:grab; }}
  svg:active {{ cursor:grabbing; }}
  .toolbar {{ display:flex; gap:8px; justify-content:center; margin:2px 0 8px; }}
  .toolbar button {{ font-family:'IM Fell English',serif; font-size:13px; padding:4px 12px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); }}
  .toolbar button:hover {{ background:rgba(196,164,74,.15); }}
  .land {{ fill:var(--land); stroke:var(--land-line); stroke-width:0.8; stroke-linejoin:round; }}
  .river {{ fill:none; stroke:#9FB9BF; stroke-width:1.4; stroke-linejoin:round; stroke-linecap:round; }}
  .region {{ fill:var(--sepia); font-family:'IM Fell English',serif; font-size:14px; letter-spacing:2px; text-anchor:middle; opacity:.36; text-transform:uppercase; pointer-events:none; }}
  .water-lbl {{ fill:#6E8A90; font-family:'IM Fell English',serif; font-style:italic; font-size:12px; text-anchor:middle; opacity:.8; pointer-events:none; }}
  .context {{ cursor:pointer; }}
  .context circle {{ fill:#fff; stroke:var(--sepia-light); stroke-width:1.4; }}
  .context text {{ font-family:'Crimson Text',serif; font-size:10px; fill:var(--sepia); font-style:italic; paint-order:stroke; stroke:var(--parchment); stroke-width:2.4px; stroke-linejoin:round; pointer-events:none; }}
  .route {{ fill:none; stroke-width:3; stroke-linecap:round; stroke-linejoin:round; opacity:.92; }}
  .route.ret {{ stroke-dasharray:2 7; opacity:.6; }}
  .stop {{ cursor:pointer; }}
  .stop circle.dot {{ fill:#fff; stroke-width:2.5; transition:r .12s; }}
  .stop:hover circle.dot {{ r:8; }}
  .stop circle.num-bg {{ opacity:.95; }}
  .stop text.num {{ fill:#fff; font-family:'IM Fell English',serif; font-size:9px; text-anchor:middle; pointer-events:none; }}
  .stop text.lbl {{ font-family:'Crimson Text',serif; font-size:11px; fill:var(--ink); paint-order:stroke; stroke:var(--parchment); stroke-width:3px; stroke-linejoin:round; pointer-events:none; }}
  .info {{ position:absolute; left:12px; bottom:12px; max-width:300px; background:rgba(255,252,245,.96); border:1.5px solid var(--gold); border-radius:8px; padding:10px 13px; font-size:13px; box-shadow:0 2px 10px rgba(42,26,5,.18); display:none; }}
  .info.show {{ display:block; }}
  .info h3 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:16px; margin-bottom:2px; }}
  .info .r {{ font-family:'IM Fell English',serif; color:var(--sepia-light); font-size:12px; }}
  .info .n {{ margin-top:4px; font-style:italic; color:#3A2A12; }}
  .hint {{ text-align:center; font-size:12.5px; color:var(--sepia-light); font-style:italic; margin-top:10px; }}
  footer {{ text-align:center; font-size:11.5px; color:#5A5A5A; font-style:italic; margin-top:22px; line-height:1.7; }}
  footer a {{ color:inherit; }}
</style>
</head>
<body>
<header>
  <a class="backlink" href="/the-church-christ-built/">&larr; The Church Christ Built</a>
  <h1>The Missionary Journeys</h1>
  <div class="sub">Paul's journeys &amp; the voyage to Rome &mdash; from the Acts of the Apostles</div>
</header>
<div class="wrap">
  <div class="tabs" id="tabs"></div>
  <div class="blurb" id="blurb"></div>
  <div class="toolbar"><button id="zin">+ Zoom in</button><button id="zout">&minus; Zoom out</button><button id="zreset">Reset</button></div>
  <div class="mapbox">
    <svg id="map" viewBox="{VB}" preserveAspectRatio="xMidYMid meet">
      <g class="land">{LAND}</g>
      <g class="river">{RIVERS}</g>
      <g class="regions">{REGION_SVG}</g>
      <g class="waters">{WATER_SVG}</g>
      <g class="contexts">{CONTEXT_SVG}</g>
      <g id="routes"></g>
      <g id="stops"></g>
    </svg>
    <div class="info" id="info"></div>
  </div>
  <div class="hint">Click a numbered stop to see its place in the story. The dashed line marks the return.</div>
  <footer>
    <p>Basemap: Natural Earth (public domain). Places: OpenBible.info. Routes from the Acts of the Apostles (NASB).</p>
    <p>Part of <a href="/the-church-christ-built/">The Church Christ Built</a> &middot; Noble Mind Study</p>
  </footer>
</div>
<script>
const JOURNEYS = {JJSON};
const tabs = document.getElementById('tabs'), routesG = document.getElementById('routes'),
      stopsG = document.getElementById('stops'), info = document.getElementById('info'),
      blurb = document.getElementById('blurb');
let active = 0;

function draw(i) {{
  active = i;
  const j = JOURNEYS[i];
  document.querySelectorAll('.tab').forEach((t,k)=>{{ t.classList.toggle('active',k===i); if(k===i) t.style.background=j.color, t.style.borderColor=j.color; else t.style.background='', t.style.borderColor=''; }});
  blurb.textContent = j.blurb;
  info.classList.remove('show');
  if (typeof resetVB === 'function') resetVB();
  routesG.innerHTML = ''; stopsG.innerHTML = '';
  // route polyline
  const pts = j.stops.map(s=>`${{s.x}},${{s.y}}`).join(' ');
  const path = document.createElementNS('http://www.w3.org/2000/svg','polyline');
  path.setAttribute('points', pts); path.setAttribute('class','route'); path.setAttribute('stroke', j.color);
  routesG.appendChild(path);
  const len = path.getTotalLength ? path.getTotalLength() : 0;
  if (len) {{ path.style.strokeDasharray = len; path.style.strokeDashoffset = len; path.getBoundingClientRect(); path.style.transition='stroke-dashoffset 1.1s ease'; path.style.strokeDashoffset = 0; }}
  // return leg (dashed)
  if (j.ret) {{
    const last = j.stops[j.stops.length-1];
    const r = document.createElementNS('http://www.w3.org/2000/svg','polyline');
    r.setAttribute('points', `${{last.x}},${{last.y}} ${{j.ret[0]}},${{j.ret[1]}}`);
    r.setAttribute('class','route ret'); r.setAttribute('stroke', j.color); routesG.appendChild(r);
  }}
  // stops — greedy label placement so names never overlap or appear swapped
  const placed = [];
  const FW = {round(W)};
  const ov = (b)=> placed.some(p=> !(b.x2<p.x1||b.x1>p.x2||b.y2<p.y1||b.y1>p.y2));
  j.stops.forEach((s,k)=>{{
    const w = s.name.length*5.4 + 4;
    const cands = [[11,3.5,'start'],[-11,3.5,'end'],[11,-9,'start'],[11,16,'start'],[-11,-9,'end'],[-11,16,'end']];
    let pick = null;
    for (const c of cands) {{
      const dx=c[0], dy=c[1], anc=c[2];
      const bx1 = anc==='start' ? s.x+dx : s.x+dx-w;
      const box = {{x1:bx1, y1:s.y+dy-9, x2:bx1+w, y2:s.y+dy+2}};
      if (box.x1<2 || box.x2>FW-2) continue;
      if (!ov(box)) {{ pick=[dx,dy,anc,box]; break; }}
    }}
    if (!pick) {{ const dx=cands[0][0],dy=cands[0][1],bx1=s.x+dx; pick=[dx,dy,'start',{{x1:bx1,y1:s.y+dy-9,x2:bx1+w,y2:s.y+dy+2}}]; }}
    placed.push(pick[3]);
    const g = document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class','stop'); g.setAttribute('transform',`translate(${{s.x}},${{s.y}})`);
    g.innerHTML =
      `<circle class="dot" r="6" stroke="${{j.color}}"></circle>`+
      `<circle class="num-bg" r="7.5" fill="${{j.color}}"></circle>`+
      `<text class="num" y="3">${{k+1}}</text>`+
      `<text class="lbl" x="${{pick[0]}}" y="${{pick[1]}}" text-anchor="${{pick[2]}}">${{s.name}}</text>`;
    g.addEventListener('click',(e)=>{{ e.stopPropagation(); showInfo(s,k+1,j); }});
    stopsG.appendChild(g);
  }});
}}
function showInfo(s,n,j) {{
  info.innerHTML = `<h3>${{n}}. ${{s.name}}</h3><div class="r">${{s.ref}}</div><div class="n">${{s.note}}</div>`;
  info.style.borderColor = j.color; info.classList.add('show');
}}
JOURNEYS.forEach((j,i)=>{{ const b=document.createElement('button'); b.className='tab'; b.textContent=j.label; b.title=j.ref; b.onclick=()=>draw(i); tabs.appendChild(b); }});

// ---- vector zoom / pan ----
const svgEl = document.getElementById('map');
const FULLW = {round(W)}, FULLH = {round(H)};
let vb = {{x:0,y:0,w:FULLW,h:FULLH}}; const MINW = FULLW/7;
function applyVB(){{ svgEl.setAttribute('viewBox',`${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`); }}
function clampVB(){{ vb.x=Math.max(0,Math.min(FULLW-vb.w,vb.x)); vb.y=Math.max(0,Math.min(FULLH-vb.h,vb.y)); }}
function c2s(cx,cy){{ const r=svgEl.getBoundingClientRect(); return {{x:vb.x+(cx-r.left)/r.width*vb.w, y:vb.y+(cy-r.top)/r.height*vb.h}}; }}
function zoomAt(px,py,f){{ let nw=Math.min(FULLW,Math.max(MINW,vb.w*f)); const k=nw/vb.w; vb.w=nw; vb.h*=k; vb.x=px-(px-vb.x)*k; vb.y=py-(py-vb.y)*k; clampVB(); applyVB(); }}
function resetVB(){{ vb={{x:0,y:0,w:FULLW,h:FULLH}}; applyVB(); }}
svgEl.addEventListener('wheel',e=>{{ e.preventDefault(); const p=c2s(e.clientX,e.clientY); zoomAt(p.x,p.y,e.deltaY<0?0.84:1/0.84); }},{{passive:false}});
let mdrag=null, mmoved=false;
svgEl.addEventListener('pointerdown',e=>{{ mdrag={{x:e.clientX,y:e.clientY}}; mmoved=false; svgEl.setPointerCapture(e.pointerId); }});
svgEl.addEventListener('pointermove',e=>{{ if(!mdrag)return; const r=svgEl.getBoundingClientRect(); if(Math.abs(e.clientX-mdrag.x)+Math.abs(e.clientY-mdrag.y)>4) mmoved=true; vb.x-=(e.clientX-mdrag.x)/r.width*vb.w; vb.y-=(e.clientY-mdrag.y)/r.height*vb.h; mdrag={{x:e.clientX,y:e.clientY}}; clampVB(); applyVB(); }});
svgEl.addEventListener('pointerup',()=>mdrag=null);
let mpinch=null;
svgEl.addEventListener('touchmove',e=>{{ if(e.touches.length!==2)return; e.preventDefault(); const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY); const mx=(e.touches[0].clientX+e.touches[1].clientX)/2,my=(e.touches[0].clientY+e.touches[1].clientY)/2; if(mpinch){{const p=c2s(mx,my); zoomAt(p.x,p.y,mpinch/d);}} mpinch=d; }},{{passive:false}});
svgEl.addEventListener('touchend',()=>mpinch=null);
document.getElementById('zin').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,0.7);
document.getElementById('zout').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,1/0.7);
document.getElementById('zreset').onclick=resetVB;
document.querySelectorAll('.context').forEach(g=>g.addEventListener('click',e=>{{ if(mmoved)return; e.stopPropagation(); info.innerHTML=`<h3>${{g.dataset.name}}</h3><div class="n">${{g.dataset.note}}</div>`; info.style.borderColor='var(--gold)'; info.classList.add('show'); }}));

document.querySelector('.mapbox').addEventListener('click', ()=>{{ if(!mmoved) info.classList.remove('show'); }});
// deep link via #id
const want = (location.hash||'').replace('#','');
const start = Math.max(0, JOURNEYS.findIndex(j=>j.id===want));
draw(start<0?0:start);
</script>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT}  ({len(land_paths)} land paths, {sum(len(j['stops']) for j in out_journeys)} stops, {round(W)}x{round(H)})")
