#!/usr/bin/env python3
"""
Build the owned, offline Bible-lands location explorer -> maps/index.html
(replacing the old remote-tile Leaflet viewer).

Single source of truth: reads maps/data/locations.json (OpenBible, 1309
places) and embeds a minimal projected copy. Basemap projected from
public-domain Natural Earth (50m land, 10m lakes, 10m rivers). Search,
type filter, clickable markers with their Bible verses, vector zoom/pan.
No tiles, no third-party basemap, works fully offline.

Inputs (/tmp): ne_land.geojson, ne_lakes.geojson, ne_rivers.geojson
Output: maps/index.html
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "maps/index.html")
# Biblical-world viewport: Italy/Rome -> Persia/Susa, Egypt -> Black Sea
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
    nm = (f["properties"].get("name") or "")
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
          ("Euphrates",42,34,-30),("Tigris",44,34.5,-46),("The\nJordan",35.6,32,0)]
REGION_SVG = lblsvg(REGIONS, "region")
WATER_SVG = lblsvg(WATERS, "water-lbl")

# ---- places (single source of truth: locations.json) ----
def category(t):
    if t in ("river","spring","water","sea","lake","well","waters"): return "water"
    if t in ("mountain","hill","mountain range","peak"): return "mountain"
    if t == "region": return "region"
    if t == "settlement": return "settlement"
    return "other"

places = []
for r in json.load(open(os.path.join(ROOT, "maps/data/locations.json"))):
    x, y = proj(r["lon"], r["lat"])
    places.append({"n": r["name"], "x": x, "y": y, "t": r.get("type",""),
                   "c": category(r.get("type","")), "v": r.get("verses", [])[:8], "s": r.get("url_slug","")})
PLACES_JSON = json.dumps(places, ensure_ascii=False, separators=(",", ":"))
VB = f"0 0 {round(W)} {round(H)}"
NPLACES = len(places)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bible Lands — Map &amp; Place Finder | Noble Mind Study</title>
<link rel="canonical" href="https://noblemind.study/maps/">
<meta name="description" content="An interactive, offline map of the biblical world — search any of 1,300+ places named in Scripture, see where it is, and read the verses that mention it. Fully owned, no third-party tiles.">
<style>
  @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
  :root {{ --parchment:#F5EDD6; --sea:#D8E0DC; --land:#E5D4A8; --land-line:#C9B485; --water:#AFC4C9; --water-line:#7FA0A6;
          --ink:#2A1A05; --sepia:#6B4C1A; --sepia-light:#A07840; --gold:#C4A44A;
          --c-settlement:#9C6B1E; --c-water:#2B5C86; --c-mountain:#8B2A3A; --c-region:#2E6B43; --c-other:#7A6A4A; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Crimson Text',Georgia,serif; background:var(--parchment); color:var(--ink); }}
  header {{ text-align:center; padding:26px 20px 12px; border-bottom:3px double var(--gold); position:relative; }}
  .backlink {{ position:absolute; left:18px; top:14px; font-size:13px; color:var(--sepia); text-decoration:none; border:1px solid rgba(107,76,26,.3); border-radius:4px; padding:4px 10px; background:rgba(245,237,214,.6); }}
  .backlink:hover {{ background:rgba(196,164,74,.2); }}
  h1 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:clamp(22px,3.2vw,36px); }}
  .sub {{ font-family:'IM Fell English',serif; font-style:italic; color:var(--sepia-light); font-size:14px; margin-top:5px; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:14px 12px 50px; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:center; margin:10px 0; }}
  .search {{ position:relative; }}
  .search input {{ font-family:'Crimson Text',serif; font-size:15px; padding:7px 14px; width:260px; border:1.5px solid var(--sepia-light); border-radius:999px; background:rgba(255,252,245,.8); color:var(--ink); }}
  .results {{ position:absolute; left:0; right:0; top:40px; z-index:20; background:#FFFBF2; border:1.5px solid var(--gold); border-radius:8px; max-height:260px; overflow:auto; display:none; box-shadow:0 4px 14px rgba(42,26,5,.2); }}
  .results.show {{ display:block; }}
  .results div {{ padding:6px 12px; cursor:pointer; font-size:14px; border-bottom:1px solid #EEE3CC; }}
  .results div:hover {{ background:rgba(196,164,74,.18); }}
  .results .ty {{ color:var(--sepia-light); font-style:italic; font-size:12px; }}
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
  .water-lbl {{ fill:#5a7a80; font-family:'IM Fell English',serif; font-style:italic; font-size:12px; text-anchor:middle; opacity:.82; pointer-events:none; }}
  .dot {{ stroke:#FFF8E8; stroke-width:0.5; cursor:pointer; }}
  .dot.settlement {{ fill:var(--c-settlement); }} .dot.water {{ fill:var(--c-water); }}
  .dot.mountain {{ fill:var(--c-mountain); }} .dot.region {{ fill:var(--c-region); }} .dot.other {{ fill:var(--c-other); }}
  .dot.hide {{ display:none; }}
  .sel {{ fill:none; stroke:var(--gold); stroke-width:2.5; }}
  .lbl {{ font-family:'Crimson Text',serif; font-size:11px; fill:var(--ink); paint-order:stroke; stroke:var(--parchment); stroke-width:2.6px; stroke-linejoin:round; pointer-events:none; }}
  .info {{ position:absolute; left:10px; bottom:10px; max-width:300px; background:rgba(255,252,245,.97); border:1.5px solid var(--gold); border-radius:8px; padding:10px 13px; font-size:13px; box-shadow:0 2px 10px rgba(42,26,5,.18); display:none; }}
  .info.show {{ display:block; }}
  .info h3 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:16px; }}
  .info .ty {{ font-style:italic; color:var(--sepia-light); font-size:12px; margin-bottom:5px; }}
  .info .vs {{ font-size:12.5px; line-height:1.5; }}
  .info .vs b {{ color:var(--sepia); font-weight:600; }}
  .info .ob {{ display:inline-block; margin-top:7px; font-size:12px; color:var(--sepia); }}
  .count {{ text-align:center; font-size:12px; color:var(--sepia-light); font-style:italic; margin-top:9px; }}
  footer {{ text-align:center; font-size:11.5px; color:#5A5A5A; font-style:italic; margin-top:16px; line-height:1.7; }}
  footer a {{ color:inherit; }}
</style>
</head>
<body>
<header>
  <a class="backlink" href="/index.html">&larr; Noble Mind Study</a>
  <h1>Bible Lands</h1>
  <div class="sub">A map of the world of Scripture &mdash; search any of {NPLACES:,} named places</div>
</header>
<div class="wrap">
  <div class="controls">
    <div class="search">
      <input id="q" type="text" placeholder="Search a place… (e.g. Capernaum)" autocomplete="off">
      <div class="results" id="results"></div>
    </div>
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
      <g id="dots"></g>
      <g id="sel"></g>
    </svg>
    <div class="info" id="info"></div>
  </div>
  <p class="count" id="count"></p>
  <footer>
    <p>Basemap, waters &amp; rivers: Natural Earth (public domain). {NPLACES:,} places: OpenBible.info (CC BY 4.0). Verse references: NASB book order.</p>
    <p>Part of <a href="/index.html">Noble Mind Study</a> &middot; works fully offline</p>
  </footer>
</div>
<script>
const PLACES = {PLACES_JSON};
const FULLW = {round(W)}, FULLH = {round(H)};
const svg = document.getElementById('map'), dotsG = document.getElementById('dots'),
      selG = document.getElementById('sel'), info = document.getElementById('info'),
      results = document.getElementById('results'), q = document.getElementById('q'), countEl = document.getElementById('count');
let filter = 'all';

// render dots
PLACES.forEach((p, i) => {{
  const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
  c.setAttribute('class','dot '+p.c); c.setAttribute('cx',p.x); c.setAttribute('cy',p.y); c.setAttribute('r','2.4');
  c.dataset.i = i;
  c.addEventListener('click', e => {{ e.stopPropagation(); select(i); }});
  dotsG.appendChild(c);
}});
function applyFilter() {{
  let n = 0;
  dotsG.childNodes.forEach(c => {{ const p = PLACES[c.dataset.i];
    const show = (filter === 'all' || p.c === filter); c.classList.toggle('hide', !show); if (show) n++; }});
  countEl.textContent = (filter === 'all' ? PLACES.length : n) + ' places shown';
}}
function select(i) {{
  const p = PLACES[i];
  selG.innerHTML = `<circle class="sel" cx="${{p.x}}" cy="${{p.y}}" r="6"></circle>`+
    `<text class="lbl" x="${{p.x+9}}" y="${{p.y+4}}">${{p.n}}</text>`;
  const vs = p.v && p.v.length ? `<div class="vs"><b>Mentioned:</b> ${{p.v.join(' · ')}}</div>` : `<div class="vs" style="opacity:.7">No verse references listed.</div>`;
  const ob = p.s ? `<a class="ob" href="https://www.openbible.info/geo/${{p.s}}" target="_blank" rel="noopener">More at OpenBible.info →</a>` : '';
  info.innerHTML = `<h3>${{p.n}}</h3><div class="ty">${{p.t||'place'}}</div>${{vs}}${{ob}}`;
  info.classList.add('show');
  // ensure visible: center if far outside current view
  if (p.x < vb.x || p.x > vb.x+vb.w || p.y < vb.y || p.y > vb.y+vb.h) {{
    vb.w = Math.min(FULLW, FULLW/3); vb.h = vb.w*FULLH/FULLW; vb.x = p.x-vb.w/2; vb.y = p.y-vb.h/2; clamp(); ap();
  }}
}}
// search
function runSearch() {{
  const s = q.value.trim().toLowerCase();
  if (s.length < 2) {{ results.classList.remove('show'); return; }}
  const m = PLACES.map((p,i)=>({{p,i}})).filter(o => o.p.n.toLowerCase().includes(s)).slice(0, 12);
  results.innerHTML = m.map(o => `<div data-i="${{o.i}}">${{o.p.n}} <span class="ty">${{o.p.t}}</span></div>`).join('') || '<div style="opacity:.6">No match</div>';
  results.classList.toggle('show', true);
  results.querySelectorAll('div[data-i]').forEach(d => d.addEventListener('click', () => {{
    select(+d.dataset.i); results.classList.remove('show'); q.value = PLACES[+d.dataset.i].n; }}));
}}
q.addEventListener('input', runSearch);
q.addEventListener('focus', runSearch);
document.addEventListener('click', e => {{ if (!e.target.closest('.search')) results.classList.remove('show'); }});
document.querySelectorAll('.fpill').forEach(b => b.onclick = () => {{
  filter = b.dataset.c; document.querySelectorAll('.fpill').forEach(x=>x.classList.toggle('active', x===b)); applyFilter(); }});

// vector zoom/pan
let vb = {{x:0,y:0,w:FULLW,h:FULLH}}; const MINW = FULLW/22;
function ap(){{ svg.setAttribute('viewBox',`${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`); }}
function clamp(){{ vb.x=Math.max(0,Math.min(FULLW-vb.w,vb.x)); vb.y=Math.max(0,Math.min(FULLH-vb.h,vb.y)); }}
function c2s(cx,cy){{ const r=svg.getBoundingClientRect(); return {{x:vb.x+(cx-r.left)/r.width*vb.w, y:vb.y+(cy-r.top)/r.height*vb.h}}; }}
function zoomAt(px,py,f){{ let nw=Math.min(FULLW,Math.max(MINW,vb.w*f)); const k=nw/vb.w; vb.w=nw; vb.h*=k; vb.x=px-(px-vb.x)*k; vb.y=py-(py-vb.y)*k; clamp(); ap(); }}
svg.addEventListener('wheel',e=>{{ e.preventDefault(); const p=c2s(e.clientX,e.clientY); zoomAt(p.x,p.y,e.deltaY<0?0.82:1/0.82); }},{{passive:false}});
let drag=null, moved=false;
svg.addEventListener('pointerdown',e=>{{ drag={{x:e.clientX,y:e.clientY}}; moved=false; svg.setPointerCapture(e.pointerId); }});
svg.addEventListener('pointermove',e=>{{ if(!drag)return; const r=svg.getBoundingClientRect(); if(Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>4) moved=true; vb.x-=(e.clientX-drag.x)/r.width*vb.w; vb.y-=(e.clientY-drag.y)/r.height*vb.h; drag={{x:e.clientX,y:e.clientY}}; clamp(); ap(); }});
svg.addEventListener('pointerup',()=>drag=null);
let pinch=null;
svg.addEventListener('touchmove',e=>{{ if(e.touches.length!==2)return; e.preventDefault(); const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY); const mx=(e.touches[0].clientX+e.touches[1].clientX)/2,my=(e.touches[0].clientY+e.touches[1].clientY)/2; if(pinch){{const p=c2s(mx,my); zoomAt(p.x,p.y,pinch/d);}} pinch=d; }},{{passive:false}});
svg.addEventListener('touchend',()=>pinch=null);
document.getElementById('zin').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,0.65);
document.getElementById('zout').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,1/0.65);
document.getElementById('zreset').onclick=()=>{{ vb={{x:0,y:0,w:FULLW,h:FULLH}}; ap(); info.classList.remove('show'); selG.innerHTML=''; }};
document.querySelector('.mapbox').addEventListener('click',()=>{{ if(!moved){{ info.classList.remove('show'); selG.innerHTML=''; }} }});
applyFilter();
</script>
</body>
</html>
"""
with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT}  ({len(land)} land, {len(lakes)} lakes, {len(rivers)} rivers, {NPLACES} places, {round(W)}x{round(H)})")
