#!/usr/bin/env python3
"""
Build the owned, offline Bible-lands location explorer -> maps/index.html.

Single source of truth: maps/data/locations.json (OpenBible, 1309 places),
embedded. Basemap projected from public-domain Natural Earth (50m land, 10m
lakes, 10m rivers). Features (parity with the old Leaflet system, but owned
+ offline): search; type filter; a Journeys dropdown (Paul's journeys, the
voyage to Rome, the Seven Churches, Jesus' ministry, the Exodus) that draws
the route and highlights its stops; auto place-labels that fill in as you
zoom (importance-ranked, collision-avoided); named seas/regions; a fixed
legend + place-info panel; vector zoom/pan. No tiles, works fully offline.

Inputs (/tmp): ne_land.geojson, ne_lakes.geojson, ne_rivers.geojson
Output: maps/index.html
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "maps/index.html")
LON0, LON1, LAT0, LAT1 = 10.0, 50.0, 22.0, 43.5
COSL = math.cos(math.radians((LAT0 + LAT1) / 2))
W = 1400.0
SCALE = W / ((LON1 - LON0) * COSL)
H = (LAT1 - LAT0) * SCALE
def proj(lon, lat): return round((lon - LON0) * COSL * SCALE, 1), round((LAT1 - lat) * SCALE, 1)

def ring(r, dc=0.6):
    pts, last = [], None
    for lon, lat in r:
        x, y = proj(lon, lat)
        if last and abs(x - last[0]) < dc and abs(y - last[1]) < dc: continue
        pts.append((x, y)); last = (x, y)
    return ("M" + " ".join(f"{x},{y}" for x, y in pts) + "Z") if len(pts) >= 3 else None
def hits(r):
    xs = [c[0] for c in r]; ys = [c[1] for c in r]
    return not (max(xs) < LON0-2 or min(xs) > LON1+2 or max(ys) < LAT0-2 or min(ys) > LAT1+2)

land = []
for f in json.load(open("/tmp/ne_land.geojson"))["features"]:
    g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        if not hits(poly[0]): continue
        for r in poly:
            p = ring(r);  land.append(p) if p else None
lakes = []
for f in json.load(open("/tmp/ne_lakes.geojson"))["features"]:
    g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        if not hits(poly[0]): continue
        p = ring(poly[0], 0.3);  lakes.append(p) if p else None
rivers = []
for f in json.load(open("/tmp/ne_rivers.geojson"))["features"]:
    if (f["properties"].get("name") or "") not in ("Nile", "Tigris", "Euphrates", "Jordan"): continue
    g = f["geometry"]; lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
    for line in lines:
        pts, last = [], None
        for lon, lat in line:
            if not (LON0-1 <= lon <= LON1+1 and LAT0-1 <= lat <= LAT1+1): continue
            x, y = proj(lon, lat)
            if last and abs(x-last[0]) < 0.5 and abs(y-last[1]) < 0.5: continue
            pts.append((x, y)); last = (x, y)
        if len(pts) >= 2: rivers.append("M" + " ".join(f"{x},{y}" for x, y in pts))

GEO = ('<g class="land">%s</g><g class="water">%s</g><g class="river">%s</g>' %
       ("".join('<path d="%s"/>' % p for p in land),
        "".join('<path d="%s"/>' % p for p in lakes),
        "".join('<path d="%s"/>' % p for p in rivers)))
# shaded-relief basemap: the image replaces the flat land+water vector fill;
# the named rivers stay drawn on top of it.
RELIEF = "relief-world.jpg"
if os.path.exists(os.path.join(os.path.dirname(OUT), RELIEF)):
    GEO = ('<image href="%s" x="0" y="0" width="%d" height="%d" preserveAspectRatio="none"/>' % (RELIEF, round(W), round(H))
           + '<g class="river">%s</g>' % "".join('<path d="%s"/>' % p for p in rivers))

def lblsvg(items, cls):
    out = []
    for txt, lon, lat, rot in items:
        x, y = proj(lon, lat)
        ts = "".join(f'<tspan x="{x}" dy="{0 if i==0 else 13}">{ln}</tspan>' for i, ln in enumerate(txt.split("\n")))
        out.append(f'<text class="{cls}" transform="rotate({rot} {x} {y})" x="{x}" y="{y}">{ts}</text>')
    return "".join(out)

REGIONS = [("EGYPT",31,27.5,0),("ARABIA",43,26,0),("CANAAN",35.2,32,0),("PHOENICIA",35.5,34,0),
           ("SYRIA",37.5,35,0),("ARAM",38.5,34,0),("ASSYRIA",43,36,0),("BABYLONIA",44.5,31.5,0),
           ("MESOPOTAMIA",41,34.5,0),("PERSIA",49,32,0),("MEDIA",47,35.5,0),("ASIA MINOR",33,39,0),
           ("GALATIA",33.5,39.7,0),("CILICIA",34.5,37,0),("CAPPADOCIA",36,38.7,0),("PHRYGIA",30.5,38.5,0),
           ("LYDIA",28,38.4,0),("GREECE",22.3,39,0),("MACEDONIA",22.5,41,0),("ACHAIA",22.2,38,0),
           ("ITALY",13.5,42,0),("CYPRUS",33,34.95,0),("CRETE",25,34.85,0),("LIBYA",18,30,0),("CUSH",33,22.5,0)]
WATERS = [("The Great Sea",19,34,-8),("Red Sea",37,24.5,-52),("Persian\nGulf",49.5,28.5,0),
          ("Black Sea",34,43,0),("Caspian\nSea",50,40,0),("Nile",31.2,27,-80),
          ("Euphrates",42,34,-30),("Tigris",44,34.5,-46),("The Jordan",35.62,32.15,0),
          ("Sea of Galilee",35.85,32.82,0),("Salt Sea",35.7,31.5,0)]
REGION_SVG = lblsvg(REGIONS, "region")
WATER_SVG = lblsvg(WATERS, "water-lbl")

def category(t):
    if t in ("river","spring","water","sea","lake","well","waters"): return "water"
    if t in ("mountain","hill","mountain range","peak"): return "mountain"
    if t == "region": return "region"
    if t == "settlement": return "settlement"
    return "other"

raw = json.load(open(os.path.join(ROOT, "maps/data/locations.json")))
byname = {r["name"].lower(): r for r in raw}
places = []
for r in raw:
    x, y = proj(r["lon"], r["lat"])
    places.append({"n": r["name"], "x": x, "y": y, "t": r.get("type",""),
                   "c": category(r.get("type","")), "v": r.get("verses", [])[:8],
                   "s": r.get("url_slug",""), "w": len(r.get("verses", []))})
idx_of = {r["name"].lower(): i for i, r in enumerate(raw)}
PLACES_JSON = json.dumps(places, ensure_ascii=False, separators=(",", ":"))

# ---- journeys (resolve stop coords from locations.json + overrides) ----
OVR = {"antioch (syria)": (36.20,36.16), "pisidian antioch": (38.31,31.19), "mount sinai": (28.54,33.97),
       "mount nebo": (31.77,35.73), "succoth": (30.55,32.07), "bethlehem": (31.705,35.203),
       "bethany": (31.771,35.276), "jericho": (31.87,35.44), "bethsaida": (32.91,35.63),
       "pergamum": (39.13,27.18), "smyrna": (38.42,27.14), "thyatira": (38.92,27.84),
       "sardis": (38.49,28.04), "philadelphia": (38.35,28.52), "laodicea": (37.84,29.11),
       "rameses": (30.80,31.83), "marah": (29.35,32.94), "elim": (29.25,32.92), "rephidim": (28.62,33.88),
       "kadesh-barnea": (30.65,34.42), "fair havens": (34.93,24.80), "malta": (35.93,14.41)}
def coord(name):
    k = name.lower()
    if k in OVR: return OVR[k]
    r = byname.get(k)
    return (r["lat"], r["lon"]) if r else None

JDEF = [
  ("paul1", "Paul's 1st Journey", True, ["Antioch (Syria)","Salamis","Paphos","Perga","Pisidian Antioch","Iconium","Lystra","Derbe"]),
  ("paul2", "Paul's 2nd Journey", True, ["Antioch (Syria)","Derbe","Lystra","Troas","Neapolis","Philippi","Thessalonica","Berea","Athens","Corinth","Ephesus","Caesarea"]),
  ("paul3", "Paul's 3rd Journey", True, ["Antioch (Syria)","Ephesus","Philippi","Corinth","Troas","Miletus","Tyre","Caesarea","Jerusalem"]),
  ("rome", "The Voyage to Rome", True, ["Caesarea","Sidon","Myra","Fair Havens","Malta","Syracuse","Rhegium","Puteoli","Rome"]),
  ("seven", "The Seven Churches (Rev 2–3)", True, ["Ephesus","Smyrna","Pergamum","Thyatira","Sardis","Philadelphia","Laodicea"]),
  ("jesus", "Jesus' Ministry", False, ["Nazareth","Bethlehem","Jerusalem","Capernaum","Cana","Bethsaida","Jericho","Bethany","Nain","Caesarea Philippi"]),
  ("exodus", "The Exodus", True, ["Rameses","Succoth","Marah","Elim","Rephidim","Mount Sinai","Kadesh-barnea","Mount Nebo"]),
]
journeys = []
for jid, label, route, stops in JDEF:
    pts = []
    for nm in stops:
        c = coord(nm)
        if not c:
            print(f"  (journey {jid}: missing {nm})"); continue
        x, y = proj(c[1], c[0])
        pts.append({"n": nm.replace(" (Syria)",""), "x": x, "y": y})
    journeys.append({"id": jid, "label": label, "route": route, "stops": pts})
JOURNEYS_JSON = json.dumps(journeys, ensure_ascii=False, separators=(",", ":"))
VB = f"0 0 {round(W)} {round(H)}"
NPLACES = len(places)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bible Lands — Map &amp; Place Finder | Noble Mind Study</title>
<link rel="canonical" href="https://noblemind.study/maps/">
<meta name="description" content="An interactive, offline map of the biblical world — search any of 1,300+ places named in Scripture, trace the missionary journeys and the Exodus, and read the verses that mention each place. Fully owned, no third-party tiles.">
<style>
  @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
  :root {{ --parchment:#F5EDD6; --sea:#D8E0DC; --land:#E5D4A8; --land-line:#C9B485; --water:#AFC4C9; --water-line:#7FA0A6;
          --ink:#2A1A05; --sepia:#6B4C1A; --sepia-light:#A07840; --gold:#C4A44A;
          --c-settlement:#9C6B1E; --c-water:#2B5C86; --c-mountain:#8B2A3A; --c-region:#2E6B43; --c-other:#7A6A4A; --j:#8B2A3A; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Crimson Text',Georgia,serif; background:var(--parchment); color:var(--ink); }}
  header {{ text-align:center; padding:24px 20px 10px; border-bottom:3px double var(--gold); position:relative; }}
  .backlink {{ position:absolute; left:18px; top:14px; font-size:13px; color:var(--sepia); text-decoration:none; border:1px solid rgba(107,76,26,.3); border-radius:4px; padding:4px 10px; background:rgba(245,237,214,.6); }}
  .backlink:hover {{ background:rgba(196,164,74,.2); }}
  h1 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:clamp(22px,3.2vw,36px); }}
  .sub {{ font-family:'IM Fell English',serif; font-style:italic; color:var(--sepia-light); font-size:14px; margin-top:5px; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:12px 12px 50px; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:center; margin:10px 0; }}
  .search {{ position:relative; }}
  .search input {{ font-family:'Crimson Text',serif; font-size:15px; padding:7px 14px; width:230px; border:1.5px solid var(--sepia-light); border-radius:999px; background:rgba(255,252,245,.8); color:var(--ink); }}
  .results {{ position:absolute; left:0; right:0; top:40px; z-index:30; background:#FFFBF2; border:1.5px solid var(--gold); border-radius:8px; max-height:260px; overflow:auto; display:none; box-shadow:0 4px 14px rgba(42,26,5,.2); }}
  .results.show {{ display:block; }}
  .results div {{ padding:6px 12px; cursor:pointer; font-size:14px; border-bottom:1px solid #EEE3CC; }}
  .results div:hover {{ background:rgba(196,164,74,.18); }}
  .results .ty {{ color:var(--sepia-light); font-style:italic; font-size:12px; }}
  select.jsel {{ font-family:'IM Fell English',serif; font-size:13.5px; padding:6px 12px; border-radius:999px; border:1.5px solid var(--sepia-light); background:rgba(255,252,245,.8); color:var(--sepia); cursor:pointer; }}
  .filters {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .fpill {{ font-family:'IM Fell English',serif; font-size:12.5px; padding:5px 12px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); }}
  .fpill.active {{ color:#fff; background:var(--sepia); border-color:var(--sepia); }}
  .fpill[data-c="settlement"].active {{ background:var(--c-settlement); border-color:var(--c-settlement); }}
  .fpill[data-c="water"].active {{ background:var(--c-water); border-color:var(--c-water); }}
  .fpill[data-c="mountain"].active {{ background:var(--c-mountain); border-color:var(--c-mountain); }}
  .fpill[data-c="region"].active {{ background:var(--c-region); border-color:var(--c-region); }}
  .toolbar button {{ font-family:'IM Fell English',serif; font-size:13px; padding:5px 12px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); }}
  .toolbar button:hover {{ background:rgba(196,164,74,.15); }}
  .mapbox {{ position:relative; background:var(--sea); border:2px solid var(--land-line); border-radius:10px; overflow:hidden; box-shadow:0 3px 14px rgba(42,26,5,.12); touch-action:none; }}
  svg {{ display:block; width:100%; height:auto; cursor:grab; }}
  svg:active {{ cursor:grabbing; }}
  .land {{ fill:var(--land); stroke:var(--land-line); stroke-width:0.7; stroke-linejoin:round; }}
  .water {{ fill:var(--water); stroke:var(--water-line); stroke-width:0.5; }}
  .river {{ fill:none; stroke:var(--water-line); stroke-width:1.3; stroke-linejoin:round; stroke-linecap:round; }}
  .region {{ fill:var(--sepia); font-family:'IM Fell English',serif; font-size:13px; letter-spacing:1.5px; text-anchor:middle; opacity:.34; text-transform:uppercase; pointer-events:none; }}
  .water-lbl {{ fill:#5a7a80; font-family:'IM Fell English',serif; font-style:italic; font-size:12px; text-anchor:middle; opacity:.85; pointer-events:none; }}
  #dots circle {{ r:var(--dr,3px); stroke:#FFF8E8; stroke-width:0.4px; cursor:pointer; }}
  .settlement {{ fill:var(--c-settlement); }} .water-d {{ fill:var(--c-water); }}
  .mountain {{ fill:var(--c-mountain); }} .region-d {{ fill:var(--c-region); }} .other {{ fill:var(--c-other); }}
  circle.hide {{ display:none; }}
  circle.jstop {{ r:var(--dr2,5px) !important; stroke:#fff; stroke-width:1.2px; }}
  .route {{ fill:none; stroke:var(--j); stroke-width:var(--rw,2.2px); stroke-linecap:round; stroke-linejoin:round; opacity:.9; }}
  .sel {{ fill:none; stroke:var(--gold); stroke-width:var(--rw,2.5px); }}
  /* HTML label overlay */
  .labels {{ position:absolute; inset:0; pointer-events:none; overflow:hidden; }}
  .maplabel {{ position:absolute; font-family:'Crimson Text',serif; font-size:11.5px; color:var(--ink); white-space:nowrap;
               paint-order:stroke; text-shadow:0 0 2px var(--parchment),0 0 2px var(--parchment),0 0 3px var(--parchment); transform:translateY(-50%); }}
  .maplabel.j {{ font-weight:600; color:var(--j); font-size:12px; }}
  .maplabel.key {{ font-weight:600; }}
  /* legend + place info panel */
  .panel {{ position:absolute; left:10px; bottom:10px; width:240px; background:rgba(255,252,245,.96); border:1.5px solid var(--gold); border-radius:8px; padding:9px 12px; font-size:12.5px; box-shadow:0 2px 10px rgba(42,26,5,.18); z-index:10; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:4px 12px; padding-bottom:7px; margin-bottom:7px; border-bottom:1px solid #E7DAC0; }}
  .legend span {{ display:inline-flex; align-items:center; gap:5px; font-size:12px; color:var(--sepia); }}
  .legend i {{ width:9px; height:9px; border-radius:50%; display:inline-block; }}
  .legend .settlement {{ background:var(--c-settlement); }} .legend .water-d {{ background:var(--c-water); }}
  .legend .mountain {{ background:var(--c-mountain); }} .legend .region-d {{ background:var(--c-region); }}
  .pinfo h3 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:15px; }}
  .pinfo .ty {{ font-style:italic; color:var(--sepia-light); font-size:11.5px; margin-bottom:4px; }}
  .pinfo .vs {{ font-size:12px; line-height:1.5; }}
  .pinfo .vs b {{ color:var(--sepia); }}
  .pinfo .hint {{ font-style:italic; color:var(--sepia-light); }}
  .pinfo .ob {{ display:inline-block; margin-top:6px; font-size:11.5px; color:var(--sepia); }}
  footer {{ text-align:center; font-size:11.5px; color:#5A5A5A; font-style:italic; margin-top:14px; line-height:1.7; }}
  footer a {{ color:inherit; }}
  @media (max-width:560px) {{ .panel {{ width:190px; font-size:11.5px; }} }}
</style>
</head>
<body>
<header>
  <a class="backlink" href="/index.html">&larr; Noble Mind Study</a>
  <h1>Bible Lands</h1>
  <div class="sub">A map of the world of Scripture &mdash; {NPLACES:,} named places &amp; the great journeys</div>
</header>
<div class="wrap">
  <div class="controls">
    <div class="search">
      <input id="q" type="text" placeholder="Search a place… (e.g. Capernaum)" autocomplete="off">
      <div class="results" id="results"></div>
    </div>
    <select class="jsel" id="jsel"><option value="">Journeys &amp; routes…</option></select>
    <div class="filters" id="filters">
      <button class="fpill active" data-c="all">All</button>
      <button class="fpill" data-c="settlement">Cities</button>
      <button class="fpill" data-c="region">Regions</button>
      <button class="fpill" data-c="water">Waters</button>
      <button class="fpill" data-c="mountain">Mountains</button>
    </div>
    <div class="toolbar"><button id="zin">+</button><button id="zout">&minus;</button><button id="zreset">Reset</button></div>
  </div>
  <div class="mapbox">
    <svg id="map" viewBox="{VB}" preserveAspectRatio="xMidYMid meet">
      {GEO}
      <g class="regions">{REGION_SVG}</g>
      <g class="waters">{WATER_SVG}</g>
      <g id="route"></g>
      <g id="dots" style="--dr:3px;--dr2:5px"></g>
      <g id="sel"></g>
    </svg>
    <div class="labels" id="labels"></div>
    <div class="panel">
      <div class="legend">
        <span><i class="settlement"></i>Cities</span><span><i class="region-d"></i>Regions</span>
        <span><i class="water-d"></i>Waters</span><span><i class="mountain"></i>Mountains</span>
      </div>
      <div class="pinfo" id="pinfo"><span class="hint">Search, pick a journey, or click any place. Names fill in as you zoom.</span></div>
    </div>
  </div>
  <footer>
    <p>Basemap, waters &amp; rivers: Natural Earth (public domain). {NPLACES:,} places: OpenBible.info (CC BY 4.0).</p>
    <p>Part of <a href="/index.html">Noble Mind Study</a> &middot; works fully offline</p>
  </footer>
</div>
<script>
const PLACES = {PLACES_JSON};
const JOURNEYS = {JOURNEYS_JSON};
const FULLW = {round(W)}, FULLH = {round(H)};
const svg = document.getElementById('map'), dotsG = document.getElementById('dots'),
      selG = document.getElementById('sel'), routeG = document.getElementById('route'),
      labels = document.getElementById('labels'), results = document.getElementById('results'),
      q = document.getElementById('q'), pinfo = document.getElementById('pinfo'), jsel = document.getElementById('jsel');
const CLS = {{settlement:'settlement', water:'water-d', mountain:'mountain', region:'region-d', other:'other'}};
let filter = 'all', activeJourney = null;
const jstop = new Set();           // indices that are current journey stops
const order = PLACES.map((p,i)=>i).sort((a,b)=> PLACES[b].w - PLACES[a].w);  // importance: verse count

// dots
PLACES.forEach((p,i) => {{
  const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
  c.setAttribute('class', CLS[p.c]); c.setAttribute('cx',p.x); c.setAttribute('cy',p.y); c.dataset.i = i;
  c.addEventListener('click', e => {{ e.stopPropagation(); select(i, false); }});
  dotsG.appendChild(c);
}});
const dotEls = dotsG.childNodes;

function applyFilter() {{
  dotEls.forEach(c => {{ const p = PLACES[c.dataset.i];
    c.classList.toggle('hide', !(filter==='all' || p.c===filter || jstop.has(+c.dataset.i))); }});
  updateLabels();
}}

// ----- labels: HTML overlay, importance-ranked, collision-avoided, zoom-aware -----
function collides(b, arr) {{ return arr.some(p => !(b.x2<p.x1||b.x1>p.x2||b.y2<p.y1||b.y1>p.y2)); }}
function updateLabels() {{
  labels.innerHTML = '';
  const rect = svg.getBoundingClientRect(); if (!rect.width) return;
  const sx = rect.width/vb.w, sy = rect.height/vb.h;
  const placed = []; let n = 0;
  const cand = [...jstop].concat(order);   // journey stops first, then by importance
  for (const i of cand) {{
    if (n > 110) break;
    const p = PLACES[i];
    const isJ = jstop.has(i);
    if (!isJ && filter!=='all' && p.c!==filter) continue;
    const px = (p.x - vb.x)*sx, py = (p.y - vb.y)*sy;
    if (px < -4 || px > rect.width+4 || py < 0 || py > rect.height) continue;
    const w = p.n.length*6.2 + 8, box = {{x1:px+6, y1:py-7, x2:px+6+w, y2:py+7}};
    if (collides(box, placed)) continue;
    placed.push(box);
    const d = document.createElement('div');
    d.className = 'maplabel' + (isJ?' j':'') + (p.w>=12?' key':'');
    d.textContent = p.n; d.style.left = (px+7)+'px'; d.style.top = py+'px';
    labels.appendChild(d); n++;
  }}
}}

function select(i, fly) {{
  const p = PLACES[i];
  selG.innerHTML = `<circle class="sel" cx="${{p.x}}" cy="${{p.y}}" r="${{7*vb.w/FULLW}}"></circle>`;
  const vs = p.v && p.v.length ? `<div class="vs"><b>Mentioned:</b> ${{p.v.join(' · ')}}</div>` : `<div class="vs hint">No verse references listed.</div>`;
  const ob = p.s ? `<a class="ob" href="https://www.openbible.info/geo/${{p.s}}" target="_blank" rel="noopener">More at OpenBible.info →</a>` : '';
  pinfo.innerHTML = `<h3>${{p.n}}</h3><div class="ty">${{p.t||'place'}}</div>${{vs}}${{ob}}`;
  if (fly || p.x<vb.x || p.x>vb.x+vb.w || p.y<vb.y || p.y>vb.y+vb.h) {{
    vb.w = Math.min(FULLW, FULLW/3.2); vb.h = vb.w*FULLH/FULLW; vb.x = p.x-vb.w/2; vb.y = p.y-vb.h/2; clamp(); ap();
  }}
}}

// ----- journeys -----
JOURNEYS.forEach(j => {{ const o=document.createElement('option'); o.value=j.id; o.textContent=j.label; jsel.appendChild(o); }});
function clearJourney() {{ jstop.clear(); routeG.innerHTML=''; dotEls.forEach(c=>c.classList.remove('jstop')); }}
function showJourney(id) {{
  clearJourney();
  const j = JOURNEYS.find(x=>x.id===id); if(!j) {{ applyFilter(); return; }}
  if (j.route && j.stops.length>1) {{
    const pl = document.createElementNS('http://www.w3.org/2000/svg','polyline');
    pl.setAttribute('class','route'); pl.setAttribute('points', j.stops.map(s=>`${{s.x}},${{s.y}}`).join(' '));
    routeG.appendChild(pl);
  }}
  // mark stops (match by name) so they highlight + always label
  j.stops.forEach(s => {{ const i = PLACES.findIndex(p=>p.n===s.n); if(i>=0){{ jstop.add(i); }} }});
  dotEls.forEach(c => c.classList.toggle('jstop', jstop.has(+c.dataset.i)));
  // fit to journey bounds
  const xs=j.stops.map(s=>s.x), ys=j.stops.map(s=>s.y);
  const pad=40, minx=Math.min(...xs)-pad, maxx=Math.max(...xs)+pad, miny=Math.min(...ys)-pad, maxy=Math.max(...ys)+pad;
  let w=Math.max(maxx-minx,(maxy-miny)*FULLW/FULLH); w=Math.min(FULLW,Math.max(FULLW/22,w));
  vb.w=w; vb.h=w*FULLH/FULLW; vb.x=(minx+maxx)/2-w/2; vb.y=(miny+maxy)/2-vb.h/2; clamp(); ap();
  pinfo.innerHTML = `<h3>${{j.label}}</h3><div class="ty">${{j.stops.length}} stops</div><div class="vs hint">Click a stop for its verses.</div>`;
}}
jsel.addEventListener('change', () => {{ activeJourney = jsel.value; showJourney(activeJourney); }});

// ----- search -----
function runSearch() {{
  const s = q.value.trim().toLowerCase();
  if (s.length < 2) {{ results.classList.remove('show'); return; }}
  const m = order.filter(i => PLACES[i].n.toLowerCase().includes(s)).slice(0,12);
  results.innerHTML = m.map(i => `<div data-i="${{i}}">${{PLACES[i].n}} <span class="ty">${{PLACES[i].t}}</span></div>`).join('') || '<div class="ty" style="padding:6px 12px">No match</div>';
  results.classList.add('show');
  results.querySelectorAll('div[data-i]').forEach(d => d.addEventListener('click', () => {{
    select(+d.dataset.i, true); results.classList.remove('show'); q.value = PLACES[+d.dataset.i].n; }}));
}}
q.addEventListener('input', runSearch); q.addEventListener('focus', runSearch);
document.addEventListener('click', e => {{ if (!e.target.closest('.search')) results.classList.remove('show'); }});
document.querySelectorAll('.fpill').forEach(b => b.onclick = () => {{
  filter = b.dataset.c; document.querySelectorAll('.fpill').forEach(x=>x.classList.toggle('active', x===b)); applyFilter(); }});

// ----- zoom / pan -----
let vb = {{x:0,y:0,w:FULLW,h:FULLH}}; const MINW = FULLW/24;
let lblTimer=null;
function setDr(){{ const sc=vb.w/FULLW; dotsG.style.setProperty('--dr',(3*sc)+'px'); dotsG.style.setProperty('--dr2',(5*sc)+'px'); document.documentElement.style.setProperty('--rw',(2.4*sc)+'px'); }}
function ap(){{ svg.setAttribute('viewBox',`${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`); setDr(); clearTimeout(lblTimer); lblTimer=setTimeout(updateLabels,90); }}
function clamp(){{ vb.x=Math.max(0,Math.min(FULLW-vb.w,vb.x)); vb.y=Math.max(0,Math.min(FULLH-vb.h,vb.y)); }}
function c2s(cx,cy){{ const r=svg.getBoundingClientRect(); return {{x:vb.x+(cx-r.left)/r.width*vb.w, y:vb.y+(cy-r.top)/r.height*vb.h}}; }}
function zoomAt(px,py,f){{ let nw=Math.min(FULLW,Math.max(MINW,vb.w*f)); const k=nw/vb.w; vb.w=nw; vb.h*=k; vb.x=px-(px-vb.x)*k; vb.y=py-(py-vb.y)*k; clamp(); ap(); }}
svg.addEventListener('wheel',e=>{{ e.preventDefault(); const p=c2s(e.clientX,e.clientY); zoomAt(p.x,p.y,e.deltaY<0?0.82:1/0.82); }},{{passive:false}});
let drag=null, moved=false;
svg.addEventListener('pointerdown',e=>{{ drag={{x:e.clientX,y:e.clientY,pid:e.pointerId}}; moved=false; }});
svg.addEventListener('pointermove',e=>{{ if(!drag)return; const r=svg.getBoundingClientRect(); if(Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>4&&!moved){{ moved=true; try{{svg.setPointerCapture(drag.pid);}}catch(_){{}} }} if(!moved)return; vb.x-=(e.clientX-drag.x)/r.width*vb.w; vb.y-=(e.clientY-drag.y)/r.height*vb.h; drag={{x:e.clientX,y:e.clientY,pid:drag.pid}}; clamp(); ap(); }});
svg.addEventListener('pointerup',()=>drag=null);
let pinch=null;
svg.addEventListener('touchmove',e=>{{ if(e.touches.length!==2)return; e.preventDefault(); const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY); const mx=(e.touches[0].clientX+e.touches[1].clientX)/2,my=(e.touches[0].clientY+e.touches[1].clientY)/2; if(pinch){{const p=c2s(mx,my); zoomAt(p.x,p.y,pinch/d);}} pinch=d; }},{{passive:false}});
svg.addEventListener('touchend',()=>pinch=null);
document.getElementById('zin').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,0.65);
document.getElementById('zout').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,1/0.65);
document.getElementById('zreset').onclick=()=>{{ vb={{x:0,y:0,w:FULLW,h:FULLH}}; jsel.value=''; clearJourney(); selG.innerHTML=''; pinfo.innerHTML='<span class="hint">Search, pick a journey, or click any place. Names fill in as you zoom.</span>'; ap(); applyFilter(); }};
svg.addEventListener('click',()=>{{ if(!moved){{ selG.innerHTML=''; }} }});
window.addEventListener('resize',()=>{{ clearTimeout(lblTimer); lblTimer=setTimeout(updateLabels,120); }});
setDr(); applyFilter(); updateLabels();
</script>
</body>
</html>
"""
with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT}  ({len(land)} land, {len(lakes)} lakes, {len(rivers)} rivers, {NPLACES} places, {len(journeys)} journeys)")
