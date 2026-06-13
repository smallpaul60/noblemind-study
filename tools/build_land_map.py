#!/usr/bin/env python3
"""
Build "The Land of Israel in the Days of Jesus" — a zoomable parchment
reference map for the Life of Christ timeline.

Fully owned + offline-first: public-domain Natural Earth geometry (50m land,
10m lakes, 10m river centerlines) projected to an inline SVG, with the
first-century regions (approximate boundaries), the named waters, and the
key Gospel landmarks. Vector zoom/pan (viewBox) — crisp at any zoom, no
tiles, works offline.

Inputs (public domain, fetched to /tmp):
  /tmp/ne_land.geojson    (ne_50m_land)
  /tmp/ne_lakes.geojson   (ne_10m_lakes)
  /tmp/ne_rivers.geojson  (ne_10m_rivers_lake_centerlines)
Output: the-life-of-christ/land-of-israel.html
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOC = os.path.join(ROOT, "maps/data/locations.json")
OUT = os.path.join(ROOT, "the-life-of-christ/land-of-israel.html")

LON0, LON1 = 33.8, 36.5
LAT0, LAT1 = 30.9, 33.7
LAT_MID = math.radians((LAT0 + LAT1) / 2)
COSL = math.cos(LAT_MID)
W = 900.0
SCALE = W / ((LON1 - LON0) * COSL)
H = (LAT1 - LAT0) * SCALE

def proj(lon, lat):
    return round((lon - LON0) * COSL * SCALE, 1), round((LAT1 - lat) * SCALE, 1)

def inbox(lon, lat, pad=0.4):
    return LON0 - pad <= lon <= LON1 + pad and LAT0 - pad <= lat <= LAT1 + pad

# ---- city coordinates ----
loc = {r["name"].lower(): (r["lat"], r["lon"]) for r in json.load(open(LOC))}
loc.update({
    "bethlehem": (31.705, 35.203), "bethany": (31.771, 35.276), "jericho": (31.870, 35.444),
    "bethsaida": (32.910, 35.630), "sebaste": (32.280, 35.190), "pella": (32.456, 35.617),
})
def C(name):
    return loc[name.lower()]

# ---- land (50m), clipped ----
def ring_path(ring, decim=0.5):
    pts, last = [], None
    for lon, lat in ring:
        x, y = proj(lon, lat)
        if last and abs(x - last[0]) < decim and abs(y - last[1]) < decim:
            continue
        pts.append((x, y)); last = (x, y)
    return ("M" + " ".join(f"{x},{y}" for x, y in pts) + "Z") if len(pts) >= 3 else None

def feature_hits(coords):
    flat = coords
    while isinstance(flat[0][0], (list, tuple)):
        flat = [p for r in flat for p in r] if isinstance(flat[0][0][0], (list, tuple)) else flat[0]
        break
    xs = [c[0] for c in flat]; ys = [c[1] for c in flat]
    return not (max(xs) < LON0 - 1 or min(xs) > LON1 + 1 or max(ys) < LAT0 - 1 or min(ys) > LAT1 + 1)

land_paths = []
for feat in json.load(open("/tmp/ne_land.geojson"))["features"]:
    g = feat["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        if not feature_hits(poly[0]):
            continue
        for ring in poly:
            p = ring_path(ring)
            if p:
                land_paths.append(p)
LAND = "".join(f'<path d="{p}"/>' for p in land_paths)

# ---- lakes (10m): Sea of Galilee + Dead Sea ----
lake_paths = []
for feat in json.load(open("/tmp/ne_lakes.geojson"))["features"]:
    nm = (feat["properties"].get("name") or "")
    if nm not in ("Sea of Galilee", "Dead Sea"):
        continue
    g = feat["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        p = ring_path(poly[0], decim=0.2)
        if p:
            lake_paths.append(p)
LAKES = "".join(f'<path d="{p}"/>' for p in lake_paths)
# shaded-relief basemap: the image replaces the flat land+water vector fill;
# the river/boundary/label layers stay drawn on top of it.
RELIEF = "relief-land.jpg"
if os.path.exists(os.path.join(os.path.dirname(OUT), RELIEF)):
    LAND = '<image href="%s" x="0" y="0" width="%d" height="%d" preserveAspectRatio="none"/>' % (RELIEF, round(W), round(H))
    LAKES = ""

# ---- Jordan river (10m centerlines), clipped ----
river_paths = []
for feat in json.load(open("/tmp/ne_rivers.geojson"))["features"]:
    if (feat["properties"].get("name") or "").lower() != "jordan":
        continue
    g = feat["geometry"]
    lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
    for line in lines:
        pts, last = [], None
        for lon, lat in line:
            if not inbox(lon, lat, 0.2):
                continue
            x, y = proj(lon, lat)
            if last and abs(x - last[0]) < 0.3 and abs(y - last[1]) < 0.3:
                continue
            pts.append((x, y)); last = (x, y)
        if len(pts) >= 2:
            river_paths.append("M" + " ".join(f"{x},{y}" for x, y in pts))
RIVERS = "".join(f'<path d="{p}"/>' for p in river_paths)

# ---- regions: label position (lon,lat) ----
REGIONS = [
    ("GALILEE", 35.30, 32.83), ("SAMARIA", 35.22, 32.30), ("JUDEA", 35.08, 31.70),
    ("IDUMEA", 34.95, 31.10), ("PEREA", 35.78, 31.80), ("DECAPOLIS", 35.95, 32.55),
    ("PHOENICIA", 35.30, 33.45), ("TETRARCHY OF PHILIP", 35.95, 33.30),
]
def reg_svg():
    out = []
    for name, lon, lat in REGIONS:
        x, y = proj(lon, lat)
        out.append(f'<text class="region" x="{x}" y="{y}">{name}</text>')
    return "".join(out)
REGION_LABELS = reg_svg()

# approximate region boundaries (dashed) — lon/lat polylines
BOUNDS = [
    [(34.95, 32.60), (35.22, 32.55), (35.45, 32.52), (35.58, 32.50)],   # Galilee | Samaria (Jezreel)
    [(34.92, 31.97), (35.15, 31.93), (35.35, 31.89), (35.52, 31.87)],   # Samaria | Judea
    [(34.85, 31.32), (35.12, 31.31), (35.38, 31.31)],                   # Judea | Idumea
]
def bounds_svg():
    out = []
    for line in BOUNDS:
        pts = " ".join(f"{proj(lo,la)[0]},{proj(lo,la)[1]}" for lo, la in line)
        out.append(f'<polyline class="bdy-casing" points="{pts}"/><polyline class="bdy" points="{pts}"/>')
    return "".join(out)
BOUNDARIES = bounds_svg()

# ---- water labels (lon, lat, text, rotation) ----
WATER_LABELS = [
    ("The Great Sea", 34.25, 32.45, -68, 16), ("Sea of\nGalilee", 35.72, 32.79, 0),
    ("The Jordan", 35.54, 32.05, -74), ("The Salt Sea", 35.47, 31.45, -80),
]
def water_lbl_svg():
    out = []
    for it in WATER_LABELS:
        txt, lon, lat, rot = it[:4]; size = it[4] if len(it) > 4 else None
        x, y = proj(lon, lat)
        lines = txt.split("\n")
        tspans = "".join(f'<tspan x="{x}" dy="{0 if i==0 else 13}">{ln}</tspan>' for i, ln in enumerate(lines))
        fs = f' font-size="{size}"' if size else ""
        out.append(f'<text class="water-lbl"{fs} transform="rotate({rot} {x} {y})" x="{x}" y="{y}">{tspans}</text>')
    return "".join(out)
WATER_LABELS_SVG = water_lbl_svg()

# ---- cities: name, key?, note ----
CITIES = [
    ("Caesarea Philippi", 0, "Peter's confession: ‘You are the Christ’"),
    ("Tyre", 0, "The Canaanite woman's daughter healed"),
    ("Sidon", 0, "On the border of His travels north"),
    ("Bethsaida", 0, "Home of Peter, Andrew, and Philip"),
    ("Capernaum", 1, "His own base in Galilee"),
    ("Cana", 0, "Water turned to wine — the first sign"),
    ("Tiberias", 0, "Herod Antipas's new lakeside capital"),
    ("Nazareth", 1, "Where Jesus grew up"),
    ("Nain", 0, "The widow's son raised"),
    ("Gadara", 0, "The Decapolis — the man called Legion"),
    ("Pella", 0, "A city of the Decapolis"),
    ("Caesarea", 0, "The Roman capital of Judea; Cornelius"),
    ("Sebaste", 0, "Herod's rebuilt Samaria; Philip preached here"),
    ("Sychar", 0, "The woman at the well, at Jacob's well"),
    ("Joppa", 0, "Peter's vision; Dorcas raised"),
    ("Jericho", 1, "Zacchaeus; blind Bartimaeus"),
    ("Bethany", 1, "Mary, Martha, and Lazarus"),
    ("Jerusalem", 1, "The cross, the empty tomb, and Pentecost"),
    ("Bethlehem", 1, "Where He was born"),
    ("Hebron", 0, "Burial place of the patriarchs"),
]
out_cities = []
for name, key, note in CITIES:
    lat, lon = C(name)
    x, y = proj(lon, lat)
    out_cities.append({"name": name, "x": x, "y": y, "key": key, "note": note})
CITIES_JSON = json.dumps(out_cities, ensure_ascii=False)
VB = f"0 0 {round(W)} {round(H)}"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Land of Israel in the Days of Jesus | The Life of Christ</title>
<link rel="canonical" href="https://noblemind.study/the-life-of-christ/land-of-israel.html">
<meta name="description" content="A zoomable map of the land of Israel in the time of Jesus — the regions of Galilee, Samaria, Judea and Perea under Roman rule, the named waters, and the towns of the Gospels.">
<style>
  @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
  :root { --parchment:#F5EDD6; --sea:#D8E0DC; --land:#E5D4A8; --land-line:#C9B485; --water:#AFC4C9; --water-line:#7FA0A6;
          --ink:#2A1A05; --sepia:#6B4C1A; --sepia-light:#A07840; --gold:#C4A44A; --key:#8B2A3A; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:'Crimson Text',Georgia,serif; background:var(--parchment); color:var(--ink); }
  header { text-align:center; padding:30px 20px 14px; border-bottom:3px double var(--gold); position:relative; }
  .backlink { position:absolute; left:18px; top:14px; font-size:13px; color:var(--sepia); text-decoration:none; border:1px solid rgba(107,76,26,.3); border-radius:4px; padding:4px 10px; background:rgba(245,237,214,.6); }
  .backlink:hover { background:rgba(196,164,74,.2); }
  h1 { font-family:'IM Fell English',serif; color:var(--sepia); font-size:clamp(22px,3.2vw,38px); }
  .sub { font-family:'IM Fell English',serif; font-style:italic; color:var(--sepia-light); font-size:14.5px; margin-top:6px; }
  .wrap { max-width:760px; margin:0 auto; padding:14px 12px 50px; }
  .toolbar { display:flex; gap:8px; justify-content:center; align-items:center; flex-wrap:wrap; margin:10px 0; font-size:13px; color:var(--sepia); }
  .toolbar button { font-family:'IM Fell English',serif; font-size:13px; padding:5px 13px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); }
  .toolbar button:hover { background:rgba(196,164,74,.15); }
  .toolbar .tip { font-style:italic; color:var(--sepia-light); font-size:12px; }
  .mapbox { position:relative; background:var(--sea); border:2px solid var(--land-line); border-radius:10px; overflow:hidden; box-shadow:0 3px 14px rgba(42,26,5,.12); touch-action:none; }
  svg { display:block; width:100%; height:auto; cursor:grab; }
  svg:active { cursor:grabbing; }
  .land { fill:var(--land); stroke:var(--land-line); stroke-width:0.8; stroke-linejoin:round; }
  .water { fill:var(--water); stroke:var(--water-line); stroke-width:0.6; }
  .river { fill:none; stroke:var(--water-line); stroke-width:1.8; stroke-linejoin:round; stroke-linecap:round; }
  .bdy-casing { fill:none; stroke:#F5EDD6; stroke-width:3.6; stroke-dasharray:7 5; opacity:.55; stroke-linecap:round; }
  .bdy { fill:none; stroke:#1a1a1a; stroke-width:1.8; stroke-dasharray:7 5; opacity:.9; stroke-linecap:round; }
  .region { fill:var(--sepia); font-family:'IM Fell English',serif; font-size:15px; letter-spacing:2px; text-anchor:middle; opacity:.42; text-transform:uppercase; pointer-events:none; }
  .water-lbl { fill:#5a7a80; font-family:'IM Fell English',serif; font-style:italic; font-size:12px; text-anchor:middle; opacity:.85; pointer-events:none; }
  .city { cursor:pointer; }
  .city circle { fill:#fff; stroke:var(--sepia); stroke-width:1.6; }
  .city.key circle { fill:var(--key); stroke:#fff; stroke-width:1.4; r:4.5; }
  .city text { font-family:'Crimson Text',serif; font-size:10px; fill:var(--ink); paint-order:stroke; stroke:var(--parchment); stroke-width:2.6px; stroke-linejoin:round; pointer-events:none; }
  .city.key text { font-weight:600; }
  .info { position:absolute; left:10px; bottom:10px; max-width:290px; background:rgba(255,252,245,.97); border:1.5px solid var(--gold); border-radius:8px; padding:9px 12px; font-size:13px; box-shadow:0 2px 10px rgba(42,26,5,.18); display:none; }
  .info.show { display:block; }
  .info h3 { font-family:'IM Fell English',serif; color:var(--sepia); font-size:15px; }
  .info .n { margin-top:2px; font-style:italic; color:#3A2A12; }
  .note { font-size:12.5px; color:var(--sepia-light); font-style:italic; text-align:center; margin-top:12px; line-height:1.6; }
  footer { text-align:center; font-size:11.5px; color:#5A5A5A; font-style:italic; margin-top:18px; line-height:1.7; }
  footer a { color:inherit; }
</style>
</head>
<body>
<header>
  <a class="backlink" href="/the-life-of-christ/">&larr; The Life of Christ</a>
  <h1>The Land of Israel in the Days of Jesus</h1>
  <div class="sub">Galilee, Samaria, Judea &amp; Perea &mdash; under Roman rule</div>
</header>
<div class="wrap">
  <div class="toolbar">
    <button id="zin">+ Zoom in</button><button id="zout">&minus; Zoom out</button><button id="reset">Reset</button>
    <span class="tip">scroll or pinch to zoom &middot; drag to pan &middot; click a town</span>
  </div>
  <div class="mapbox">
    <svg id="map" viewBox="%VB%" preserveAspectRatio="xMidYMid meet">
      <g class="land">%LAND%</g>
      <g class="water">%LAKES%</g>
      <g class="river">%RIVERS%</g>
      <g class="boundaries">%BOUNDARIES%</g>
      <g class="region-labels">%REGION_LABELS%</g>
      <g class="water-labels">%WATER_LABELS%</g>
      <g id="cities"></g>
    </svg>
    <div class="info" id="info"></div>
  </div>
  <p class="note">Regional boundaries are approximate &mdash; the borders of Galilee, Samaria, Judea, Perea, the Decapolis and Idumea were never sharply fixed, and shifted under the Herods and Rome. The dashed lines mark the rough divisions as best we know them.</p>
  <footer>
    <p>Basemap &amp; waters: Natural Earth (public domain). Towns: OpenBible.info. Significance from the Gospels (NASB).</p>
    <p>Part of <a href="/the-life-of-christ/">The Life of Christ</a> &middot; Noble Mind Study</p>
  </footer>
</div>
<script>
const CITIES = %CITIES_JSON%;
const FULLW = %FULLW%, FULLH = %FULLH%;
const svg = document.getElementById('map'), citiesG = document.getElementById('cities'), info = document.getElementById('info');
// ---- cities ----
CITIES.forEach(c => {
  const g = document.createElementNS('http://www.w3.org/2000/svg','g');
  g.setAttribute('class','city'+(c.key?' key':'')); g.setAttribute('transform',`translate(${c.x},${c.y})`);
  const right = c.x < FULLW-90;
  g.innerHTML = `<circle r="${c.key?4.5:3.2}"></circle>`+
    `<text x="${right?7:-7}" y="3.2" text-anchor="${right?'start':'end'}">${c.name}</text>`;
  g.addEventListener('click', e => { e.stopPropagation(); if (moved) return;
    info.innerHTML = `<h3>${c.name}</h3><div class="n">${c.note}</div>`; info.classList.add('show'); });
  citiesG.appendChild(g);
});
// ---- vector zoom / pan (viewBox) ----
let vb = {x:0,y:0,w:FULLW,h:FULLH}; const FULL = {...vb}; const MINW = FULLW/8;
function apply(){ svg.setAttribute('viewBox', `${vb.x} ${vb.y} ${vb.w} ${vb.h}`); }
function clampPan(){ vb.x = Math.max(FULL.x, Math.min(FULL.x+FULL.w-vb.w, vb.x)); vb.y = Math.max(FULL.y, Math.min(FULL.y+FULL.h-vb.h, vb.y)); }
function c2s(cx,cy){ const r = svg.getBoundingClientRect(); return { x: vb.x + (cx-r.left)/r.width*vb.w, y: vb.y + (cy-r.top)/r.height*vb.h }; }
function zoomAt(px,py,f){ let nw = Math.min(FULL.w, Math.max(MINW, vb.w*f)); const k = nw/vb.w; vb.w = nw; vb.h *= k; vb.x = px-(px-vb.x)*k; vb.y = py-(py-vb.y)*k; clampPan(); apply(); }
svg.addEventListener('wheel', e => { e.preventDefault(); const p = c2s(e.clientX,e.clientY); zoomAt(p.x,p.y, e.deltaY<0?0.84:1/0.84); }, {passive:false});
let drag = null, moved = false;
svg.addEventListener('pointerdown', e => { drag = {x:e.clientX,y:e.clientY,pid:e.pointerId}; moved = false; });
svg.addEventListener('pointermove', e => { if(!drag) return; const r = svg.getBoundingClientRect();
  if (Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y) > 4 && !moved) { moved = true; try{svg.setPointerCapture(drag.pid);}catch(_){} }
  if (!moved) return;
  vb.x -= (e.clientX-drag.x)/r.width*vb.w; vb.y -= (e.clientY-drag.y)/r.height*vb.h; drag = {x:e.clientX,y:e.clientY,pid:drag.pid}; clampPan(); apply(); });
svg.addEventListener('pointerup', () => { drag = null; });
// pinch
let pinch = null;
svg.addEventListener('touchmove', e => { if (e.touches.length !== 2) return; e.preventDefault();
  const dx = e.touches[0].clientX-e.touches[1].clientX, dy = e.touches[0].clientY-e.touches[1].clientY;
  const d = Math.hypot(dx,dy), mx = (e.touches[0].clientX+e.touches[1].clientX)/2, my = (e.touches[0].clientY+e.touches[1].clientY)/2;
  if (pinch){ const p = c2s(mx,my); zoomAt(p.x,p.y, pinch/d); } pinch = d; }, {passive:false});
svg.addEventListener('touchend', () => pinch = null);
document.getElementById('zin').onclick = () => zoomAt(vb.x+vb.w/2, vb.y+vb.h/2, 0.7);
document.getElementById('zout').onclick = () => zoomAt(vb.x+vb.w/2, vb.y+vb.h/2, 1/0.7);
document.getElementById('reset').onclick = () => { vb = {...FULL}; apply(); info.classList.remove('show'); };
document.querySelector('.mapbox').addEventListener('click', () => { if(!moved) info.classList.remove('show'); });
</script>
</body>
</html>
"""

html = (TEMPLATE
        .replace("%VB%", VB).replace("%LAND%", LAND).replace("%LAKES%", LAKES)
        .replace("%RIVERS%", RIVERS).replace("%BOUNDARIES%", BOUNDARIES)
        .replace("%REGION_LABELS%", REGION_LABELS).replace("%WATER_LABELS%", WATER_LABELS_SVG)
        .replace("%CITIES_JSON%", CITIES_JSON)
        .replace("%FULLW%", str(round(W))).replace("%FULLH%", str(round(H))))

with open(OUT, "w") as f:
    f.write(html)
print(f"wrote {OUT}  ({len(land_paths)} land, {len(lake_paths)} lakes, {len(river_paths)} river segs, "
      f"{len(out_cities)} cities, {round(W)}x{round(H)})")
