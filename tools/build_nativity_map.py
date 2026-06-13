#!/usr/bin/env python3
"""
Build "The Nativity & the Flight to Egypt" — a zoomable parchment route map
for the Life of Christ timeline. Nazareth -> Bethlehem (the census/birth) ->
Egypt (the flight from Herod) -> back to Nazareth, with Jerusalem (the
presentation) marked.

Fully owned + offline-first: public-domain Natural Earth (50m land, 10m
lakes, 10m rivers) projected to inline SVG; vector zoom/pan.

Inputs (/tmp): ne_land.geojson, ne_lakes.geojson, ne_rivers.geojson
Output: the-life-of-christ/nativity-route.html
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "the-life-of-christ/nativity-route.html")
LON0, LON1, LAT0, LAT1 = 29.5, 36.3, 29.4, 33.3
COSL = math.cos(math.radians((LAT0 + LAT1) / 2))
W = 1000.0
SCALE = W / ((LON1 - LON0) * COSL)
H = (LAT1 - LAT0) * SCALE
def proj(lon, lat): return round((lon - LON0) * COSL * SCALE, 1), round((LAT1 - lat) * SCALE, 1)

loc = {r["name"].lower(): (r["lat"], r["lon"]) for r in json.load(open(os.path.join(ROOT, "maps/data/locations.json")))}
loc.update({"bethlehem": (31.705, 35.203), "egypt": (30.55, 31.30), "gaza": (31.504, 34.464)})
def C(n): return loc[n.lower()]

def ring(r, dc=0.5):
    pts, last = [], None
    for lon, lat in r:
        x, y = proj(lon, lat)
        if last and abs(x - last[0]) < dc and abs(y - last[1]) < dc: continue
        pts.append((x, y)); last = (x, y)
    return ("M" + " ".join(f"{x},{y}" for x, y in pts) + "Z") if len(pts) >= 3 else None
def hits(r):
    xs = [c[0] for c in r]; ys = [c[1] for c in r]
    return not (max(xs) < LON0-1 or min(xs) > LON1+1 or max(ys) < LAT0-1 or min(ys) > LAT1+1)

land = []
for f in json.load(open("/tmp/ne_land.geojson"))["features"]:
    g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        if not hits(poly[0]): continue
        for r in poly:
            p = ring(r);  land.append(p) if p else None
lakes = []
for f in json.load(open("/tmp/ne_lakes.geojson"))["features"]:
    if (f["properties"].get("name") or "") not in ("Sea of Galilee", "Dead Sea"): continue
    g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        p = ring(poly[0], 0.2);  lakes.append(p) if p else None
rivers = []
for f in json.load(open("/tmp/ne_rivers.geojson"))["features"]:
    if (f["properties"].get("name") or "") not in ("Nile", "Jordan"): continue
    g = f["geometry"]; lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
    for line in lines:
        pts, last = [], None
        for lon, lat in line:
            if not (LON0-1 <= lon <= LON1+1 and LAT0-1 <= lat <= LAT1+1): continue
            x, y = proj(lon, lat)
            if last and abs(x-last[0]) < 0.4 and abs(y-last[1]) < 0.4: continue
            pts.append((x, y)); last = (x, y)
        if len(pts) >= 2: rivers.append("M" + " ".join(f"{x},{y}" for x, y in pts))

GEO = ('<g class="land">%s</g><g class="water">%s</g><g class="river">%s</g>' %
       ("".join('<path d="%s"/>' % p for p in land),
        "".join('<path d="%s"/>' % p for p in lakes),
        "".join('<path d="%s"/>' % p for p in rivers)))
# shaded-relief basemap: the image replaces the flat land+water vector fill;
# the named rivers stay drawn on top of it.
RELIEF = "relief-nativity.jpg"
if os.path.exists(os.path.join(os.path.dirname(OUT), RELIEF)):
    GEO = ('<image href="%s" x="0" y="0" width="%d" height="%d" preserveAspectRatio="none"/>' % (RELIEF, round(W), round(H))
           + '<g class="river">%s</g>' % "".join('<path d="%s"/>' % p for p in rivers))

def lblsvg(items, cls):
    out = []
    for it in items:
        txt, lon, lat, rot = it[:4]; size = it[4] if len(it) > 4 else None
        x, y = proj(lon, lat)
        ts = "".join(f'<tspan x="{x}" dy="{0 if i==0 else 12}">{ln}</tspan>' for i, ln in enumerate(txt.split("\n")))
        fs = f' font-size="{size}"' if size else ""
        out.append(f'<text class="{cls}"{fs} transform="rotate({rot} {x} {y})" x="{x}" y="{y}">{ts}</text>')
    return "".join(out)

REGIONS = [("GALILEE", 35.35, 32.78, 0), ("SAMARIA", 35.25, 32.25, 0), ("JUDEA", 35.05, 31.62, 0),
           ("IDUMEA", 34.95, 31.05, 0), ("PHILISTIA", 34.4, 31.5, 0), ("EGYPT", 31.3, 30.55, 0)]
WATERS = [("The Great Sea", 33.3, 32.4, -18, 16), ("The Jordan", 35.55, 32.05, -76),
          ("The Salt Sea", 35.42, 31.42, -82), ("Nile", 31.15, 30.0, -78)]
REGION_SVG = lblsvg(REGIONS, "region")
WATER_SVG = lblsvg(WATERS, "water-lbl")

ROUTE = [("Nazareth", "Luke 1:26–38", "Mary's home; Gabriel announces the birth"),
         ("Bethlehem", "Luke 2:1–7", "The census of Caesar Augustus; Jesus is born"),
         ("Egypt", "Matthew 2:13–15", "The flight from Herod — ‘Out of Egypt I called My Son’")]
RET_NOTE = "Matthew 2:19–23 — the return to Nazareth: ‘He shall be called a Nazarene.’"
CONTEXT = [("Jerusalem", "The presentation in the temple, forty days after the birth (Luke 2:22–38)"),
           ("Gaza", "On the coastal road the family would have taken toward Egypt")]

def pj(name): lat, lon = C(name); return proj(lon, lat)
route_pts = [{"name": n, "x": pj(n)[0], "y": pj(n)[1], "ref": r, "note": note, "n": i+1} for i, (n, r, note) in enumerate(ROUTE)]
naz = pj("Nazareth")
ctx_pts = [{"name": n, "x": pj(n)[0], "y": pj(n)[1], "note": note} for n, note in CONTEXT]
ROUTE_JSON = json.dumps(route_pts, ensure_ascii=False)
CTX_JSON = json.dumps(ctx_pts, ensure_ascii=False)
RETLINE = '%d,%d %d,%d' % (route_pts[-1]["x"], route_pts[-1]["y"], naz[0], naz[1])
ROUTELINE = " ".join(f'{p["x"]},{p["y"]}' for p in route_pts)
VB = f"0 0 {round(W)} {round(H)}"

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Nativity &amp; the Flight to Egypt | The Life of Christ</title>
<link rel="canonical" href="https://noblemind.study/the-life-of-christ/nativity-route.html">
<meta name="description" content="A zoomable map of the nativity journeys — Nazareth to Bethlehem for the census and the birth, the flight to Egypt from Herod, and the return to Nazareth.">
<style>
  @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
  :root {{ --parchment:#F5EDD6; --sea:#D8E0DC; --land:#E5D4A8; --land-line:#C9B485; --water:#AFC4C9; --water-line:#7FA0A6;
          --ink:#2A1A05; --sepia:#6B4C1A; --sepia-light:#A07840; --gold:#C4A44A; --route:#8B2A3A; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Crimson Text',Georgia,serif; background:var(--parchment); color:var(--ink); }}
  header {{ text-align:center; padding:30px 20px 14px; border-bottom:3px double var(--gold); position:relative; }}
  .backlink {{ position:absolute; left:18px; top:14px; font-size:13px; color:var(--sepia); text-decoration:none; border:1px solid rgba(107,76,26,.3); border-radius:4px; padding:4px 10px; background:rgba(245,237,214,.6); }}
  .backlink:hover {{ background:rgba(196,164,74,.2); }}
  h1 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:clamp(22px,3.2vw,38px); }}
  .sub {{ font-family:'IM Fell English',serif; font-style:italic; color:var(--sepia-light); font-size:14.5px; margin-top:6px; }}
  .wrap {{ max-width:1000px; margin:0 auto; padding:16px 12px 50px; }}
  .blurb {{ text-align:center; font-style:italic; color:var(--sepia); font-size:14px; max-width:760px; margin:10px auto 12px; }}
  .toolbar {{ display:flex; gap:8px; justify-content:center; margin:6px 0 10px; }}
  .toolbar button {{ font-family:'IM Fell English',serif; font-size:13px; padding:4px 12px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); }}
  .toolbar button:hover {{ background:rgba(196,164,74,.15); }}
  .mapbox {{ position:relative; background:var(--sea); border:2px solid var(--land-line); border-radius:10px; overflow:hidden; box-shadow:0 3px 14px rgba(42,26,5,.12); touch-action:none; }}
  svg {{ display:block; width:100%; height:auto; cursor:grab; }}
  svg:active {{ cursor:grabbing; }}
  .land {{ fill:var(--land); stroke:var(--land-line); stroke-width:0.8; stroke-linejoin:round; }}
  .water {{ fill:var(--water); stroke:var(--water-line); stroke-width:0.6; }}
  .river {{ fill:none; stroke:var(--water-line); stroke-width:1.6; stroke-linejoin:round; stroke-linecap:round; }}
  .route {{ fill:none; stroke:var(--route); stroke-width:3; stroke-linecap:round; stroke-linejoin:round; opacity:.92; }}
  .route.ret {{ stroke-dasharray:2 8; opacity:.55; }}
  .bdy-casing {{ fill:none; stroke:#F5EDD6; stroke-width:3.6; stroke-dasharray:7 5; opacity:.55; stroke-linecap:round; }}
  .bdy {{ fill:none; stroke:#1a1a1a; stroke-width:1.8; stroke-dasharray:7 5; opacity:.9; stroke-linecap:round; }}
  .region {{ fill:var(--sepia); font-family:'IM Fell English',serif; font-size:14px; letter-spacing:2px; text-anchor:middle; opacity:.4; text-transform:uppercase; pointer-events:none; }}
  .water-lbl {{ fill:#5a7a80; font-family:'IM Fell English',serif; font-style:italic; font-size:12px; text-anchor:middle; opacity:.85; pointer-events:none; }}
  .pt {{ cursor:pointer; }}
  .pt circle.dot {{ fill:#fff; stroke:var(--sepia); stroke-width:1.6; }}
  .pt circle.numbg {{ fill:var(--route); }}
  .pt text.num {{ fill:#fff; font-family:'IM Fell English',serif; font-size:9px; text-anchor:middle; pointer-events:none; }}
  .pt text.lbl {{ font-family:'Crimson Text',serif; font-size:11px; fill:var(--ink); paint-order:stroke; stroke:var(--parchment); stroke-width:2.6px; stroke-linejoin:round; pointer-events:none; }}
  .pt.num text.lbl {{ font-weight:600; }}
  .info {{ position:absolute; left:10px; bottom:10px; max-width:290px; background:rgba(255,252,245,.97); border:1.5px solid var(--gold); border-radius:8px; padding:9px 12px; font-size:13px; box-shadow:0 2px 10px rgba(42,26,5,.18); display:none; }}
  .info.show {{ display:block; }}
  .info h3 {{ font-family:'IM Fell English',serif; color:var(--sepia); font-size:15px; }}
  .info .r {{ font-family:'IM Fell English',serif; color:var(--sepia-light); font-size:12px; }}
  .info .n {{ margin-top:2px; font-style:italic; color:#3A2A12; }}
  .hint {{ text-align:center; font-size:12px; color:var(--sepia-light); font-style:italic; margin-top:10px; }}
  footer {{ text-align:center; font-size:11.5px; color:#5A5A5A; font-style:italic; margin-top:18px; line-height:1.7; }}
  footer a {{ color:inherit; }}
</style>
</head>
<body>
<header>
  <a class="backlink" href="/the-life-of-christ/">&larr; The Life of Christ</a>
  <h1>The Nativity &amp; the Flight to Egypt</h1>
  <div class="sub">Nazareth &middot; Bethlehem &middot; Egypt &middot; and home again</div>
</header>
<div class="wrap">
  <div class="blurb">From Nazareth to Bethlehem for the census and the birth, then the flight to Egypt to escape Herod, and at last the return home to Nazareth (the dashed line). Jerusalem marks the presentation in the temple.</div>
  <div class="toolbar"><button id="zin">+ Zoom in</button><button id="zout">&minus; Zoom out</button><button id="zreset">Reset</button></div>
  <div class="mapbox">
    <svg id="map" viewBox="{VB}" preserveAspectRatio="xMidYMid meet">
      {GEO}
      <g class="regions">{REGION_SVG}</g>
      <g class="waters">{WATER_SVG}</g>
      <polyline class="route" points="{ROUTELINE}"></polyline>
      <polyline class="route ret" points="{RETLINE}"></polyline>
      <g id="pts"></g>
    </svg>
    <div class="info" id="info"></div>
  </div>
  <p class="hint">scroll or pinch to zoom &middot; drag to pan &middot; click a place. The dashed line is the return to Nazareth.</p>
  <footer>
    <p>Basemap, waters &amp; rivers: Natural Earth (public domain). Places: OpenBible.info. References: NASB.</p>
    <p>Part of <a href="/the-life-of-christ/">The Life of Christ</a> &middot; Noble Mind Study</p>
  </footer>
</div>
<script>
const ROUTE = {ROUTE_JSON}, CTX = {CTX_JSON};
const RETNOTE = {json.dumps(RET_NOTE)};
const FULLW = {round(W)}, FULLH = {round(H)};
const svg = document.getElementById('map'), ptsG = document.getElementById('pts'), info = document.getElementById('info');
const placed = [];
const ov = b => placed.some(p => !(b.x2<p.x1||b.x1>p.x2||b.y2<p.y1||b.y1>p.y2));
function place(s, numbered) {{
  const w = s.name.length*5.4 + 4;
  const cands = [[10,3.5,'start'],[-10,3.5,'end'],[10,-9,'start'],[10,16,'start'],[-10,-9,'end'],[-10,16,'end']];
  let pk = null;
  for (const c of cands) {{ const bx1 = c[2]==='start'? s.x+c[0] : s.x+c[0]-w;
    const box = {{x1:bx1,y1:s.y+c[1]-9,x2:bx1+w,y2:s.y+c[1]+2}};
    if (box.x1<2||box.x2>FULLW-2) continue;
    if (!ov(box)) {{ pk=[c[0],c[1],c[2],box]; break; }} }}
  if (!pk) {{ const bx1=s.x+10; pk=[10,3.5,'start',{{x1:bx1,y1:s.y-5.5,x2:bx1+w,y2:s.y+5.5}}]; }}
  placed.push(pk[3]);
  const g = document.createElementNS('http://www.w3.org/2000/svg','g');
  g.setAttribute('class','pt'+(numbered?' num':'')); g.setAttribute('transform',`translate(${{s.x}},${{s.y}})`);
  g.innerHTML = (numbered ? `<circle class="numbg" r="7.5"></circle><text class="num" y="3">${{s.n}}</text>`
                          : `<circle class="dot" r="3.2"></circle>`)
              + `<text class="lbl" x="${{pk[0]}}" y="${{pk[1]}}" text-anchor="${{pk[2]}}">${{s.name}}</text>`;
  g.addEventListener('click', e => {{ e.stopPropagation();
    info.innerHTML = `<h3>${{(s.n!=null?s.n+'. ':'')}}${{s.name}}</h3>`+(s.ref?`<div class="r">${{s.ref}}</div>`:``)+`<div class="n">${{s.note}}</div>`;
    info.classList.add('show'); }});
  ptsG.appendChild(g);
}}
ROUTE.forEach(s => place(s, true));
CTX.forEach(s => place(s, false));

// vector zoom/pan
let vb = {{x:0,y:0,w:FULLW,h:FULLH}}; const MINW = FULLW/8;
const ap = () => svg.setAttribute('viewBox',`${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`);
const cl = () => {{ vb.x=Math.max(0,Math.min(FULLW-vb.w,vb.x)); vb.y=Math.max(0,Math.min(FULLH-vb.h,vb.y)); }};
const c2s = (cx,cy)=>{{ const r=svg.getBoundingClientRect(); return {{x:vb.x+(cx-r.left)/r.width*vb.w, y:vb.y+(cy-r.top)/r.height*vb.h}}; }};
const zoomAt = (px,py,f)=>{{ let nw=Math.min(FULLW,Math.max(MINW,vb.w*f)); const k=nw/vb.w; vb.w=nw; vb.h*=k; vb.x=px-(px-vb.x)*k; vb.y=py-(py-vb.y)*k; cl(); ap(); }};
svg.addEventListener('wheel',e=>{{ e.preventDefault(); const p=c2s(e.clientX,e.clientY); zoomAt(p.x,p.y,e.deltaY<0?0.84:1/0.84); }},{{passive:false}});
let drag=null, moved=false;
svg.addEventListener('pointerdown',e=>{{ drag={{x:e.clientX,y:e.clientY,pid:e.pointerId}}; moved=false; }});
svg.addEventListener('pointermove',e=>{{ if(!drag)return; const r=svg.getBoundingClientRect(); if(Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>4&&!moved){{ moved=true; try{{svg.setPointerCapture(drag.pid);}}catch(_){{}} }} if(!moved)return; vb.x-=(e.clientX-drag.x)/r.width*vb.w; vb.y-=(e.clientY-drag.y)/r.height*vb.h; drag={{x:e.clientX,y:e.clientY,pid:drag.pid}}; cl(); ap(); }});
svg.addEventListener('pointerup',()=>drag=null);
let pinch=null;
svg.addEventListener('touchmove',e=>{{ if(e.touches.length!==2)return; e.preventDefault(); const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY); const mx=(e.touches[0].clientX+e.touches[1].clientX)/2,my=(e.touches[0].clientY+e.touches[1].clientY)/2; if(pinch){{const p=c2s(mx,my); zoomAt(p.x,p.y,pinch/d);}} pinch=d; }},{{passive:false}});
svg.addEventListener('touchend',()=>pinch=null);
document.getElementById('zin').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,0.7);
document.getElementById('zout').onclick=()=>zoomAt(vb.x+vb.w/2,vb.y+vb.h/2,1/0.7);
document.getElementById('zreset').onclick=()=>{{ vb={{x:0,y:0,w:FULLW,h:FULLH}}; ap(); info.classList.remove('show'); }};
document.querySelector('.mapbox').addEventListener('click',()=>{{ if(!moved) info.classList.remove('show'); }});
</script>
</body>
</html>
"""
with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT}  ({len(land)} land, {len(lakes)} lakes, {len(rivers)} rivers, {len(route_pts)} stops, {round(W)}x{round(H)})")
