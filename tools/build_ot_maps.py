#!/usr/bin/env python3
"""
Build "Lands of the Old Testament" — a zoomable, tabbed parchment map hub
for the Old Testament Timeline. Four maps:
  1. The Journeys of Abraham   (route, Fertile Crescent)
  2. The Exodus                (route, Egypt-Sinai)
  3. The Divided Kingdom       (region, Canaan)
  4. The Exile & the Return    (routes, Fertile Crescent)

Fully owned + offline-first: public-domain Natural Earth (50m land, 10m
lakes, 10m river centerlines) projected to inline SVG per map, with routes
or regions overlaid from the site's OpenBible coordinates. Vector zoom/pan.

Inputs (/tmp): ne_land.geojson, ne_lakes.geojson, ne_rivers.geojson
Output: old-testament-timeline/bible-lands-maps.html
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "old-testament-timeline/bible-lands-maps.html")
NE_LAND = json.load(open("/tmp/ne_land.geojson"))["features"]
NE_LAKES = json.load(open("/tmp/ne_lakes.geojson"))["features"]
NE_RIVERS = json.load(open("/tmp/ne_rivers.geojson"))["features"]

loc = {r["name"].lower(): (r["lat"], r["lon"]) for r in json.load(open(os.path.join(ROOT, "maps/data/locations.json")))}
loc.update({
    "ur": (30.96, 46.10), "bethel": (31.93, 35.22), "beersheba": (31.25, 34.80), "babylon": (32.54, 44.42),
    "succoth-egypt": (30.55, 32.07), "mount sinai": (28.54, 33.97), "mount nebo": (31.77, 35.73),
    "jericho": (31.87, 35.44), "samaria": (32.28, 35.19), "jezreel": (32.56, 35.32), "rabbah": (31.95, 35.93),
    "dibon": (31.51, 35.78), "bethlehem": (31.70, 35.20), "riblah": (34.46, 36.55), "hazor": (33.02, 35.57),
    "carchemish": (36.83, 38.02), "egypt": (30.60, 31.30),
    "ai": (31.917, 35.262), "debir": (31.417, 34.99), "gilgal": (31.87, 35.50),
    "etham": (29.9, 33.2), "pi-hahiroth": (29.03, 34.67), "jebel al-lawz": (28.60, 35.30),
    "ezion-geber": (29.55, 34.97),
})
def C(n): return loc[n.lower()]

# ---------- geometry helpers ----------
def make_geo(bbox, rivers_named):
    lon0, lon1, lat0, lat1 = bbox
    cosl = math.cos(math.radians((lat0 + lat1) / 2))
    W = 1000.0
    scale = W / ((lon1 - lon0) * cosl)
    H = (lat1 - lat0) * scale
    def proj(lon, lat): return round((lon - lon0) * cosl * scale, 1), round((lat1 - lat) * scale, 1)

    def ring_path(ring, decim=0.5):
        pts, last = [], None
        for lon, lat in ring:
            x, y = proj(lon, lat)
            if last and abs(x - last[0]) < decim and abs(y - last[1]) < decim: continue
            pts.append((x, y)); last = (x, y)
        return ("M" + " ".join(f"{x},{y}" for x, y in pts) + "Z") if len(pts) >= 3 else None
    def hits(ring):
        xs = [c[0] for c in ring]; ys = [c[1] for c in ring]
        return not (max(xs) < lon0-2 or min(xs) > lon1+2 or max(ys) < lat0-2 or min(ys) > lat1+2)

    land = []
    for f in NE_LAND:
        g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            if not hits(poly[0]): continue
            for ring in poly:
                p = ring_path(ring);  land.append(p) if p else None
    lakes = []
    for f in NE_LAKES:
        if (f["properties"].get("name") or "") not in ("Sea of Galilee", "Dead Sea"): continue
        g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            p = ring_path(poly[0], 0.2);  lakes.append(p) if p else None
    rivers = []
    for f in NE_RIVERS:
        if (f["properties"].get("name") or "") not in rivers_named: continue
        g = f["geometry"]; lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for line in lines:
            pts, last = [], None
            for lon, lat in line:
                if not (lon0-1 <= lon <= lon1+1 and lat0-1 <= lat <= lat1+1): continue
                x, y = proj(lon, lat)
                if last and abs(x-last[0]) < 0.4 and abs(y-last[1]) < 0.4: continue
                pts.append((x, y)); last = (x, y)
            if len(pts) >= 2: rivers.append("M" + " ".join(f"{x},{y}" for x, y in pts))
    def grp(lst, cls):
        return '<g class="%s">%s</g>' % (cls, "".join('<path d="%s"/>' % p for p in lst))
    svg = grp(land, "land") + grp(lakes, "water") + grp(rivers, "river")
    return svg, proj, round(W), round(H)

def labels_svg(proj, items, cls):  # items: (text, lon, lat, rot)
    out = []
    for txt, lon, lat, rot in items:
        x, y = proj(lon, lat)
        lines = txt.split("\n")
        ts = "".join(f'<tspan x="{x}" dy="{0 if i==0 else 13}">{ln}</tspan>' for i, ln in enumerate(lines))
        out.append(f'<text class="{cls}" transform="rotate({rot} {x} {y})" x="{x}" y="{y}">{ts}</text>')
    return "".join(out)

def route_svg(proj, stops, color, ret=False):
    pts = " ".join(f"{proj(C(n)[1],C(n)[0])[0]},{proj(C(n)[1],C(n)[0])[1]}" for n,_ in stops)
    s = f'<polyline class="route" points="{pts}" stroke="{color}"/>'
    if ret:
        s += f'<polyline class="route ret" points="{pts}" stroke="{color}"/>'
    return s

def points_json(proj, items, numbered):  # items: (name, note) or (name, key, note)
    out = []
    for i, it in enumerate(items):
        if len(it) == 3: name, key, note = it
        else: name, note = it; key = 0
        lat, lon = C(name); x, y = proj(lon, lat)
        d = {"name": name, "x": x, "y": y, "note": note, "key": key}
        if numbered: d["n"] = i + 1
        out.append(d)
    return out

# ---------- map configs ----------
MAPS = []

# 1. Abraham
geo, P, W, H = make_geo((29, 48, 24, 38), {"Euphrates", "Tigris", "Nile"})
stops = [("Ur","Genesis 11:31"),("Haran","Genesis 12:4"),("Shechem","Genesis 12:6"),
         ("Bethel","Genesis 12:8"),("Egypt","Genesis 12:10"),("Hebron","Genesis 13:18"),("Beersheba","Genesis 21:33")]
overlay = (labels_svg(P, [("MESOPOTAMIA",43,35,0),("CANAAN",35.2,32.6,0),("EGYPT",31,29,0),
                          ("ARABIAN DESERT",40,28.5,0)], "region")
           + labels_svg(P, [("The Great Sea",33,33.5,0),("Euphrates",41.5,33.6,-32),
                            ("Tigris",43.6,34.2,-50),("Nile",31.3,28,-78),("Persian\nGulf",49,29.5,0),
                            ("Red Sea",35.2,26,-58)], "water-lbl")
           + route_svg(P, stops, "#9C6B1E"))
MAPS.append({"id":"abraham","label":"Abraham's Journey","blurb":"From Ur of the Chaldeans to Haran, into Canaan, down to Egypt in a famine, and back — the journey of faith God called Abram to make (Genesis 11–25).","desc":"God calls Abram out of <b>Ur of the Chaldeans</b>, and he travels with his household up the Fertile Crescent to Haran, then down into <b>Canaan</b> &mdash; the land God promises to give his offspring. A famine drives him to Egypt and back; at last he settles by the oaks of Mamre at Hebron. So begins the family through whom 'all the families of the earth shall be blessed.' Click a stop to follow the journey (Genesis 11–25).","W":W,"H":H,"geo":geo,"overlay":overlay,"points":points_json(P,stops,True)})

EXODUS_PANEL = """<details class="routes">
  <summary>Which route did the Exodus take? &mdash; the Gulf of Aqaba and the traditional view</summary>
  <div class="rbody">
    <p>Both views read the same events &mdash; out of Egypt at the Passover, a journey to the sea, the crossing on dry ground, the Law at Sinai, forty years in the wilderness, and at last the plains of Moab. They disagree on the <em>geography</em>: which sea was crossed, and where Mount Sinai stood. Much of it turns on what Scripture means by &ldquo;the Red Sea&rdquo; (Hebrew <em>Yam Suph</em>).</p>
    <p>The <strong>traditional</strong> Sinai-peninsula route is the majority view and has the longer history. The <strong>Gulf-of-Aqaba / Arabian-Sinai</strong> view is a serious minority case, built largely from the text. This map draws the Aqaba route; here are both, side by side.</p>
    <table class="rtab">
      <tr><th>The question</th><th>Traditional &mdash; Sinai Peninsula</th><th>Gulf of Aqaba &mdash; Sinai in Arabia</th></tr>
      <tr><td class="q">&ldquo;The Red Sea&rdquo; (<em>Yam Suph</em>)</td><td>a marshy &ldquo;Sea of Reeds&rdquo; near the Gulf of Suez or the Bitter Lakes</td><td>the Gulf of Aqaba &mdash; which Scripture itself calls the Red Sea: Ezion-geber lay &ldquo;on the shore of the Red Sea, in the land of Edom&rdquo; (1 Kings 9:26)</td></tr>
      <tr><td class="q">Where Mount Sinai stood</td><td>in the Sinai Peninsula (by tradition, Jebel Musa)</td><td>in Arabia (Jebel al-Lawz) &mdash; Paul writes &ldquo;Mount Sinai in Arabia&rdquo; (Galatians 4:25); Moses met God at the mountain while in Midian</td></tr>
      <tr><td class="q">The march before the sea</td><td>a shorter route to a nearby crossing</td><td>&ldquo;around by the way of the wilderness&rdquo; (Exodus 13:18), traveling day <em>and</em> night (13:21) &mdash; a long march, not a 20-mile step to the Gulf of Suez</td></tr>
      <tr><td class="q">The water they crossed</td><td>shallow reeds or marsh</td><td>&ldquo;the waters of the great deep&hellip; the depths of the sea&rdquo; (Isaiah 51:10), the water &ldquo;a wall to them on their right hand and on their left&rdquo; (Exodus 14:22)</td></tr>
    </table>
    <p><strong>Where the Aqaba view is strong:</strong> Scripture plainly calls the Gulf of Aqaba &ldquo;the Red Sea&rdquo; (1 Kings 9:26); a long wilderness march by day and night (Exodus 13:18, 21) fits crossing the peninsula far better than a short walk to Suez; and the &ldquo;great deep&rdquo; with walls of water (Isaiah 51:10; Exodus 14:22) reads like deep water, not a shallow marsh.</p>
    <p><strong>Where the traditional view is strong:</strong> <em>Yam Suph</em> can be rendered &ldquo;Sea of Reeds,&rdquo; which suits a reedy body near Suez; &ldquo;Arabia&rdquo; in Paul's day reached into the Sinai Peninsula, so Galatians 4:25 need not mean Saudi Arabia; the &ldquo;great deep&rdquo; can be poetic language; and it remains the view of most scholars, many of them evangelical.</p>
    <p class="ev">A word on the much-publicized &ldquo;coral-encrusted chariot wheels&rdquo; on the Aqaba seabed: those claims are contested and are not accepted even by many who hold the Aqaba view &mdash; so this case rests on the text, not on them. What Scripture makes certain is not <em>where</em> but <em>that</em> they crossed: on dry ground, the sea walled up on either side, by the hand of God (Exodus 14).</p>
  </div>
</details>"""

# 2. The Exodus (Gulf-of-Aqaba crossing; Mount Sinai in Arabia)
EXODUS_RELIEF = True   # shaded-relief terrain basemap prototype; set False to revert to flat parchment
geo, P, W, H = make_geo((30, 36.9, 27.0, 32.7), {"Nile"})
if EXODUS_RELIEF:
    geo = f'<image href="exodus-relief.jpg" x="0" y="0" width="{round(W)}" height="{round(H)}" preserveAspectRatio="none"/>'
stops = [("Rameses","Ex 12:37 — out of Egypt at the Passover"),
         ("Succoth-egypt","Ex 13:20 — the first encampment"),
         ("Etham","Ex 13:20 — on the edge of the wilderness"),
         ("Pi-hahiroth","Ex 14 — hemmed in against the sea, where Israel crossed and Pharaoh's army drowned"),
         ("Jebel al-Lawz","Ex 19 — Mount Sinai, where the Law was given (cf. Gal 4:25, 'Mount Sinai in Arabia')"),
         ("Ezion-geber","Num 33:35 — at the head of the gulf, on the way north"),
         ("Kadesh-barnea","Num 13 — the spies sent out; then forty years of wandering"),
         ("Mount Nebo","Deut 34 — Moses sees the land he may not enter")]
disp = {"Succoth-egypt":"Succoth","Jebel al-Lawz":"Mt. Sinai (Jebel al-Lawz)"}
# Route polyline with waypoints: from Kadesh the line bends around the SOUTH end
# of the Salt Sea and up its EASTERN side (through Edom/Moab) to Nebo, instead of
# a straight segment slicing across the Dead Sea. (C(name) -> (lat, lon).)
exo_route = [C("Rameses"), C("Succoth-egypt"), C("Etham"), C("Pi-hahiroth"),
             C("Jebel al-Lawz"), C("Ezion-geber"), C("Kadesh-barnea"),
             (30.85, 35.55), (31.35, 35.85), (31.70, 35.82), C("Mount Nebo")]
exo_poly = " ".join(f"{P(lo, la)[0]},{P(lo, la)[1]}" for la, lo in exo_route)
overlay = (labels_svg(P, [("EGYPT",31.3,30.6,0),("SINAI",33.6,29.5,0),("CANAAN",35.1,31.8,0),
                          ("MIDIAN",36.1,28.7,0),("ARABIA",36.4,27.5,0)], "region")
           + labels_svg(P, [("The Great Sea",33.2,32.3,0),("Nile",31.2,29.4,-80),
                            ("Red Sea",33.5,27.5,-40),("Gulf of\nSuez",32.7,28.6,-62),("Gulf of\nAqaba",34.9,29.4,-30)], "water-lbl")
           + f'<polyline class="route" points="{exo_poly}" stroke="#8B2A3A"/>')
pts = points_json(P, stops, True)
for p in pts: p["name"] = disp.get(p["name"], p["name"])
MAPS.append({"id":"exodus","label":"The Exodus","panel":EXODUS_PANEL,"blurb":"Out of Egypt, across the sea, to Mount Sinai and the Law — then forty years to the edge of the promised land. The crossing point is debated; this map follows the Gulf-of-Aqaba route.","desc":"At the Passover, Israel leaves Egypt and journeys to the sea &mdash; which God parts so they cross on dry ground while Pharaoh's army drowns behind them (Exodus 14), the great deliverance of the Old Testament. This map follows the view that the crossing was at the <b>Gulf of Aqaba</b> and that <b>Mount Sinai stood in Arabia</b> (Jebel al-Lawz &mdash; Paul calls it 'Mount Sinai in Arabia,' Galatians 4:25). From Sinai they go north to Kadesh, wander forty years, and reach the plains of Moab opposite Jericho. Scripture is certain that they crossed the sea; it does not fix the exact spot, and a traditional route instead places Sinai in the Sinai peninsula &mdash; careful readers hold both. Click any stop for its place in the story.","W":W,"H":H,"geo":geo,"overlay":overlay,"points":pts})

# 3. The Conquest (Canaan, three campaigns)
geo, P, W, H = make_geo((33.9, 36.9, 29.7, 33.6), {"Jordan"})
central = [("Gilgal", ""), ("Jericho", ""), ("Ai", ""), ("Gibeon", "")]
southern = [("Gibeon", ""), ("Lachish", ""), ("Debir", ""), ("Hebron", "")]
northern = [("Gibeon", ""), ("Hazor", "")]
cqcities = [("Gilgal", 0, "The camp by the Jordan; the twelve stones"),
            ("Jericho", 1, "The first city — its walls fell down"),
            ("Ai", 0, "Taken after Achan's sin"),
            ("Gibeon", 0, "The deceived ally; the sun stood still (Joshua 10)"),
            ("Lachish", 0, "Fell in the southern campaign"),
            ("Debir", 0, "The southern hill country"),
            ("Hebron", 0, "The southern hill country"),
            ("Hazor", 0, "Head of the northern kings — burned (Joshua 11)"),
            ("Shechem", 0, "The covenant renewed at Ebal & Gerizim"),
            ("Shiloh", 1, "The tabernacle set up; the land divided")]
overlay = (labels_svg(P, [("CANAAN", 34.9, 33.2, 0), ("PHILISTIA", 34.5, 31.45, 0),
                          ("AMMON", 36.05, 31.95, 0), ("MOAB", 35.75, 31.3, 0)], "region")
           + labels_svg(P, [("The Great Sea", 34.3, 32.5, -66), ("Sea of\nChinnereth", 35.75, 32.80, 0),
                            ("The Jordan", 35.40, 32.0, -74), ("The Salt Sea", 35.47, 31.45, -80)], "water-lbl")
           + route_svg(P, central, "#8B2A3A") + route_svg(P, southern, "#2B5C86") + route_svg(P, northern, "#2E6B43"))
MAPS.append({"id":"conquest","label":"The Conquest","blurb":"Israel crosses the Jordan and takes the land in three thrusts — a central campaign in red (Jericho, Ai, Gibeon), a southern campaign in blue (down to Hebron and Debir), and a northern campaign in green (Hazor) — then the land is divided among the tribes at Shiloh (Joshua 1–21).","desc":"Under Joshua, Israel crosses the Jordan on dry ground and takes the land in three campaigns &mdash; a <b>central</b> thrust (Jericho, then Ai, then the Gibeonite alliance), a <b>southern</b> sweep (Lachish, Debir, Hebron), and a <b>northern</b> strike (Hazor) &mdash; though much land still remained. The covenant is renewed at Shechem between Mounts Ebal and Gerizim, and at <b>Shiloh</b> the tabernacle is set up and the land divided among the twelve tribes (Joshua 1–21).","W":W,"H":H,"geo":geo,"overlay":overlay,"points":points_json(P,cqcities,False)})

# 4. Divided Kingdom (region)
geo, P, W, H = make_geo((33.9, 36.9, 29.7, 33.6), {"Jordan"})
bdy = [[(34.92,31.90),(35.18,31.86),(35.40,31.84),(35.55,31.83)]]  # Israel | Judah (approx)
bdy_svg = "".join('<polyline class="bdy" points="%s"/>' % " ".join(f"{P(lo,la)[0]},{P(lo,la)[1]}" for lo,la in line) for line in bdy)
cities = [("Dan",0,"Israel's northern shrine"),("Hazor",0,"A fortified city of the north"),
          ("Megiddo",0,"Guarding the Jezreel pass"),("Jezreel",0,"Ahab and Jezebel's city"),
          ("Samaria",1,"Capital of the northern kingdom, Israel"),("Shechem",0,"Where the kingdom divided"),
          ("Tirzah",0,"An early northern capital"),("Bethel",0,"Jeroboam's golden calf"),
          ("Jerusalem",1,"Capital of the southern kingdom, Judah"),("Bethlehem",0,"City of David"),
          ("Hebron",0,"David's first capital"),("Lachish",0,"A fortress of Judah"),
          ("Beersheba",0,"The southern bound — ‘Dan to Beersheba’"),
          ("Damascus",0,"Capital of Aram"),("Tyre",0,"Phoenician seaport"),
          ("Gaza",0,"A city of Philistia"),("Rabbah",0,"Capital of Ammon"),("Dibon",0,"A city of Moab")]
overlay = (labels_svg(P, [("ISRAEL",34.95,32.45,0),("JUDAH",34.98,31.45,0),("PHILISTIA",34.42,31.55,0),
                          ("AMMON",36.05,31.95,0),("MOAB",35.75,31.30,0),("EDOM",35.15,30.30,0),
                          ("ARAM",36.45,33.30,0),("PHOENICIA",35.30,33.45,0)], "region")
           + bdy_svg
           + labels_svg(P, [("The Great Sea",34.3,32.5,-66),("Sea of\nChinnereth",35.75,32.80,0),
                            ("The Jordan",35.40,32.0,-74),("The Salt Sea",35.47,31.45,-80)], "water-lbl"))
MAPS.append({"id":"kingdom","label":"The Divided Kingdom","blurb":"After Solomon the kingdom split — Israel in the north (capital Samaria) and Judah in the south (capital Jerusalem) — among the surrounding nations (1 Kings 12 onward).","desc":"After Solomon's death the kingdom tears in two: ten tribes form <b>Israel</b> in the north (its capital finally Samaria), while Judah and Benjamin remain in the south around <b>Jerusalem</b>. The two kingdoms stand among watchful neighbors &mdash; Aram, Phoenicia, Philistia, Ammon, Moab, Edom &mdash; through the long line of kings and prophets, until Israel falls to Assyria and, later, Judah to Babylon (1 Kings 12 onward).","W":W,"H":H,"geo":geo,"overlay":overlay,"points":points_json(P,cities,False)})

# 4. Exile & Return (Fertile Crescent, two routes)
geo, P, W, H = make_geo((29, 48, 24, 38), {"Euphrates", "Tigris", "Nile"})
judah = [("Jerusalem","2 Kings 25"),("Riblah","2 Kings 25:6"),("Carchemish","Jeremiah 46:2"),("Babylon","2 Kings 25:11")]
israel = [("Samaria","2 Kings 17:6"),("Carchemish",""),("Nineveh","2 Kings 17:6")]
overlay = (labels_svg(P, [("BABYLONIA",44.5,32,0),("ASSYRIA",43,35.5,0),("JUDAH",35.0,31.6,0),
                          ("ARABIAN DESERT",40,28.5,0)], "region")
           + labels_svg(P, [("The Great Sea",33,33.5,0),("Euphrates",41.5,33.6,-32),("Tigris",43.6,34.2,-50)], "water-lbl")
           + route_svg(P, judah, "#8B2A3A", ret=True)
           + route_svg(P, israel, "#2B5C86"))
pts = points_json(P, judah, True)
# add the two Israel-only stops (Samaria, Nineveh) as lettered points
for nm, note in [("Samaria","The north exiled to Assyria, 722 BC"),("Nineveh","Capital of Assyria")]:
    lat, lon = C(nm); x, y = P(lon, lat)
    pts.append({"name": nm, "x": x, "y": y, "note": note, "key": 0})
MAPS.append({"id":"exile","label":"The Exile & Return","blurb":"Judah carried to Babylon and, seventy years later, the remnant's return to rebuild Jerusalem (red, with the dashed return). The northern kingdom had earlier been swept to Assyria (blue). — 2 Kings 17, 25; Ezra.","desc":"Israel in the north is carried off to <b>Assyria</b> (722 BC); Judah, after Jerusalem's fall, is taken to <b>Babylon</b> (586 BC) &mdash; both deported along the Fertile Crescent, not straight across the desert. Seventy years later a remnant returns from Babylon to rebuild the temple and the city walls (the dashed line). 2 Kings 17 &amp; 25; Ezra; Nehemiah.","W":W,"H":H,"geo":geo,"overlay":overlay,"points":pts})

MAPS_JSON = json.dumps([{k: m[k] for k in ("id","label","blurb","desc","W","H","points")} for m in MAPS], ensure_ascii=False)
SECTIONS = "".join(
    f'<section class="mapsec" data-id="{m["id"]}" style="display:none">'
    f'<div class="blurb">{m["blurb"]}</div>'
    + m.get("panel", "") +
    f'<div class="mapbox"><svg viewBox="0 0 {m["W"]} {m["H"]}" preserveAspectRatio="xMidYMid meet">'
    f'{m["geo"]}{m["overlay"]}<g class="pts"></g></svg><div class="info"></div></div></section>'
    for m in MAPS)
TABS = "".join(f'<button class="tab" data-id="{m["id"]}">{m["label"]}</button>' for m in MAPS)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lands of the Old Testament — Maps | Noble Mind Study</title>
<link rel="canonical" href="https://noblemind.study/old-testament-timeline/bible-lands-maps.html">
<meta name="description" content="Zoomable parchment maps of the Old Testament world — Abraham's journey, the Exodus, the divided kingdom of Israel and Judah, and the exile and return.">
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
  .wrap { max-width:1000px; margin:0 auto; padding:16px 12px 50px; }
  .tabs { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:6px 0; }
  .tab { font-family:'IM Fell English',serif; font-size:14px; padding:7px 16px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); }
  .tab:hover { background:rgba(196,164,74,.12); }
  .tab.active { color:#fff; background:var(--sepia); border-color:var(--sepia); }
  .blurb { text-align:center; font-style:italic; color:var(--sepia); font-size:14px; max-width:760px; margin:10px auto 12px; }
  details.routes { max-width:900px; margin:4px auto 14px; background:rgba(255,252,245,.85); border:1px solid var(--land-line); border-left:4px solid #8B2A3A; border-radius:8px; padding:0 16px; }
  details.routes > summary { cursor:pointer; padding:12px 0; font-family:'IM Fell English',serif; font-size:15px; color:var(--sepia); }
  details.routes[open] > summary { border-bottom:1px solid var(--land-line); }
  details.routes .rbody { padding:11px 0 14px; font-size:13.5px; line-height:1.6; color:#3A2A12; }
  details.routes .rbody p { margin-bottom:9px; }
  details.routes .rbody em { color:var(--sepia); font-style:italic; }
  details.routes .ev { font-style:italic; color:var(--sepia-light); border-top:1px solid #E7DAC0; padding-top:9px; }
  table.rtab { width:100%; border-collapse:collapse; margin:11px 0; font-size:12.5px; }
  table.rtab th, table.rtab td { border:1px solid var(--land-line); padding:6px 9px; text-align:left; vertical-align:top; }
  table.rtab th { background:rgba(196,164,74,.18); font-family:'IM Fell English',serif; color:var(--sepia); font-weight:normal; }
  table.rtab td.q { color:var(--sepia); font-weight:600; }
  @media (max-width:560px){ table.rtab{font-size:11px;} table.rtab th,table.rtab td{padding:4px 5px;} }
  .toolbar { display:flex; gap:8px; justify-content:center; margin:6px 0 10px; }
  .toolbar button { font-family:'IM Fell English',serif; font-size:13px; padding:4px 12px; border-radius:999px; cursor:pointer; border:1.5px solid var(--sepia-light); background:transparent; color:var(--sepia); }
  .toolbar button:hover { background:rgba(196,164,74,.15); }
  .mapbox { position:relative; background:var(--sea); border:2px solid var(--land-line); border-radius:10px; overflow:hidden; box-shadow:0 3px 14px rgba(42,26,5,.12); touch-action:none; }
  svg { display:block; width:100%; height:auto; cursor:grab; }
  svg:active { cursor:grabbing; }
  .land { fill:var(--land); stroke:var(--land-line); stroke-width:0.8; stroke-linejoin:round; }
  .water { fill:var(--water); stroke:var(--water-line); stroke-width:0.6; }
  .river { fill:none; stroke:var(--water-line); stroke-width:1.6; stroke-linejoin:round; stroke-linecap:round; }
  .route { fill:none; stroke-width:3; stroke-linecap:round; stroke-linejoin:round; opacity:.9; }
  .route.ret { stroke-dasharray:2 8; opacity:.5; }
  .bdy { fill:none; stroke:var(--sepia-light); stroke-width:1; stroke-dasharray:5 5; opacity:.55; }
  .region { fill:var(--sepia); font-family:'IM Fell English',serif; font-size:15px; letter-spacing:2px; text-anchor:middle; opacity:.5; text-transform:uppercase; pointer-events:none; paint-order:stroke; stroke:var(--parchment); stroke-width:3px; stroke-linejoin:round; }
  .water-lbl { fill:#3f6168; font-family:'IM Fell English',serif; font-style:italic; font-size:12px; text-anchor:middle; opacity:.92; pointer-events:none; paint-order:stroke; stroke:var(--parchment); stroke-width:2.4px; stroke-linejoin:round; }
  .pt { cursor:pointer; }
  .pt circle.dot { fill:#fff; stroke-width:1.8; }
  .pt circle.numbg { opacity:.95; }
  .pt.key circle.dot { fill:var(--key); stroke:#fff; }
  .pt text.num { fill:#fff; font-family:'IM Fell English',serif; font-size:9px; text-anchor:middle; pointer-events:none; }
  .pt text.lbl { font-family:'Crimson Text',serif; font-size:11px; fill:var(--ink); paint-order:stroke; stroke:var(--parchment); stroke-width:2.6px; stroke-linejoin:round; pointer-events:none; }
  .pt.key text.lbl { font-weight:600; }
  .crossing { fill:#8B2A3A; font-family:'IM Fell English',serif; font-style:italic; font-size:11px; text-anchor:middle; pointer-events:none; }
  .info { position:absolute; left:10px; bottom:10px; width:300px; max-width:44%; max-height:64%; overflow:auto; background:rgba(255,252,245,.97); border:1.5px solid var(--gold); border-radius:8px; padding:11px 14px; font-size:13px; line-height:1.55; box-shadow:0 2px 10px rgba(42,26,5,.18); }
  .info h3 { font-family:'IM Fell English',serif; color:var(--sepia); font-size:16px; margin-bottom:3px; }
  .info .desc { color:#3A2A12; }
  .info .desc b { color:var(--sepia); font-weight:600; }
  .info .n { margin-top:2px; font-style:italic; color:#3A2A12; }
  .info .back { display:inline-block; margin-top:8px; font-size:12px; color:var(--sepia); cursor:pointer; border-bottom:1px dotted var(--sepia-light); }
  @media (max-width:560px) { .info { width:auto; right:10px; max-height:42%; } }
  .hint { text-align:center; font-size:12px; color:var(--sepia-light); font-style:italic; margin-top:10px; }
  footer { text-align:center; font-size:11.5px; color:#5A5A5A; font-style:italic; margin-top:18px; line-height:1.7; }
  footer a { color:inherit; }
</style>
</head>
<body>
<header>
  <a class="backlink" href="/old-testament-timeline/">&larr; Old Testament Timeline</a>
  <h1>Lands of the Old Testament</h1>
  <div class="sub">Abraham &middot; the Exodus &middot; the Conquest &middot; the Divided Kingdom &middot; the Exile &amp; Return</div>
</header>
<div class="wrap">
  <div class="tabs">%TABS%</div>
  <div class="toolbar"><button data-z="in">+ Zoom in</button><button data-z="out">&minus; Zoom out</button><button data-z="reset">Reset</button></div>
  %SECTIONS%
  <p class="hint">scroll or pinch to zoom &middot; drag to pan &middot; click a marked place. Regional borders are approximate.</p>
  <footer>
    <p>Basemap, waters &amp; rivers: Natural Earth (public domain). Places: OpenBible.info. References: NASB.</p>
    <p>Part of the <a href="/old-testament-timeline/">Old Testament Timeline</a> &middot; Noble Mind Study</p>
  </footer>
</div>
<script>
const MAPS = %MAPS_JSON%;
const byId = {};
MAPS.forEach(m => byId[m.id] = m);

function placeLabels(g, pts, FW, color) {
  const placed = [];
  const ov = b => placed.some(p => !(b.x2<p.x1||b.x1>p.x2||b.y2<p.y1||b.y1>p.y2));
  pts.forEach(s => {
    const w = s.name.length*5.4 + 4;
    const cands = [[10,3.5,'start'],[-10,3.5,'end'],[10,-9,'start'],[10,16,'start'],[-10,-9,'end'],[-10,16,'end']];
    let pk = null;
    for (const c of cands) { const dx=c[0],dy=c[1],anc=c[2];
      const bx1 = anc==='start'? s.x+dx : s.x+dx-w;
      const box = {x1:bx1,y1:s.y+dy-9,x2:bx1+w,y2:s.y+dy+2};
      if (box.x1<2||box.x2>FW-2) continue;
      if (!ov(box)) { pk=[dx,dy,anc,box]; break; } }
    if (!pk) { const dx=10,dy=3.5,bx1=s.x+dx; pk=[dx,dy,'start',{x1:bx1,y1:s.y+dy-9,x2:bx1+w,y2:s.y+dy+2}]; }
    placed.push(pk[3]);
    const el = document.createElementNS('http://www.w3.org/2000/svg','g');
    el.setAttribute('class','pt'+(s.key?' key':'')); el.setAttribute('transform',`translate(${s.x},${s.y})`);
    const num = (s.n!=null) ? `<circle class="numbg" r="7.5" fill="${color}"></circle><text class="num" y="3">${s.n}</text>`
                            : `<circle class="dot" r="3.4" stroke="${s.key?'#fff':'#6B4C1A'}"></circle>`;
    if (s.n!=null && !s.key) el.innerHTML = num + `<text class="lbl" x="${pk[0]}" y="${pk[1]}" text-anchor="${pk[2]}">${s.name}</text>`;
    else if (s.key) el.innerHTML = `<circle class="dot" r="4.5" stroke="#fff"></circle>` + (s.n!=null?`<text class="num" y="3">${s.n}</text>`:``) + `<text class="lbl" x="${pk[0]}" y="${pk[1]}" text-anchor="${pk[2]}">${s.name}</text>`;
    else el.innerHTML = num + `<text class="lbl" x="${pk[0]}" y="${pk[1]}" text-anchor="${pk[2]}">${s.name}</text>`;
    el.addEventListener('click', e => { e.stopPropagation(); showInfo(el.closest('.mapsec'), s); });
    g.appendChild(el);
  });
}
function setMapInfo(sec) {
  const m = byId[sec.dataset.id];
  sec.querySelector('.info').innerHTML = `<h3>${m.label}</h3><div class="desc">${m.desc || m.blurb}</div>`;
}
function showInfo(sec, s) {
  sec.querySelector('.info').innerHTML = `<h3>${(s.n!=null?s.n+'. ':'')}${s.name}</h3><div class="n">${s.note||''}</div><span class="back">&lsaquo; overview</span>`;
  sec.querySelector('.back').addEventListener('click', () => setMapInfo(sec));
}

// vector zoom/pan per svg
const vbState = new WeakMap();
function initZoom(svg, FW, FH) {
  const st = {x:0,y:0,w:FW,h:FH, FW, FH, MINW:FW/9}; vbState.set(svg, st);
  const apply = () => svg.setAttribute('viewBox',`${st.x} ${st.y} ${st.w} ${st.h}`);
  const clamp = () => { st.x=Math.max(0,Math.min(FW-st.w,st.x)); st.y=Math.max(0,Math.min(FH-st.h,st.y)); };
  const c2s = (cx,cy)=>{ const r=svg.getBoundingClientRect(); return {x:st.x+(cx-r.left)/r.width*st.w, y:st.y+(cy-r.top)/r.height*st.h}; };
  st.zoomAt = (px,py,f)=>{ let nw=Math.min(FW,Math.max(st.MINW,st.w*f)); const k=nw/st.w; st.w=nw; st.h*=k; st.x=px-(px-st.x)*k; st.y=py-(py-st.y)*k; clamp(); apply(); };
  st.reset = ()=>{ st.x=0;st.y=0;st.w=FW;st.h=FH; apply(); };
  svg.addEventListener('wheel', e=>{ e.preventDefault(); const p=c2s(e.clientX,e.clientY); st.zoomAt(p.x,p.y,e.deltaY<0?0.84:1/0.84); }, {passive:false});
  let drag=null, moved=false;
  svg.addEventListener('pointerdown', e=>{ drag={x:e.clientX,y:e.clientY}; moved=false; svg.setPointerCapture(e.pointerId); });
  svg.addEventListener('pointermove', e=>{ if(!drag)return; const r=svg.getBoundingClientRect();
    if(Math.abs(e.clientX-drag.x)+Math.abs(e.clientY-drag.y)>4) moved=true;
    st.x-=(e.clientX-drag.x)/r.width*st.w; st.y-=(e.clientY-drag.y)/r.height*st.h; drag={x:e.clientX,y:e.clientY}; clamp(); apply(); });
  svg.addEventListener('pointerup', ()=> drag=null);
  let pinch=null;
  svg.addEventListener('touchmove', e=>{ if(e.touches.length!==2)return; e.preventDefault();
    const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX, e.touches[0].clientY-e.touches[1].clientY);
    const mx=(e.touches[0].clientX+e.touches[1].clientX)/2, my=(e.touches[0].clientY+e.touches[1].clientY)/2;
    if(pinch){ const p=c2s(mx,my); st.zoomAt(p.x,p.y,pinch/d); } pinch=d; }, {passive:false});
  svg.addEventListener('touchend', ()=>pinch=null);
  svg.closest('.mapbox').addEventListener('click', ()=>{ if(!moved) setMapInfo(svg.closest('.mapsec')); });
}

// build each map's points + zoom
document.querySelectorAll('.mapsec').forEach(sec => {
  const m = byId[sec.dataset.id]; const svg = sec.querySelector('svg');
  const color = m.points.find(p=>p.n!=null) ? '#6B4C1A' : '#6B4C1A';
  placeLabels(sec.querySelector('.pts'), m.points, m.W, getComputedStyle(document.documentElement).getPropertyValue('--sepia')||'#6B4C1A');
  initZoom(svg, m.W, m.H);
  setMapInfo(sec);
});
// route stop numbers should match route colour — recolor numbg per map
const ROUTECOL = {abraham:'#9C6B1E', exodus:'#8B2A3A', exile:'#8B2A3A'};
document.querySelectorAll('.mapsec').forEach(sec=>{ const c=ROUTECOL[sec.dataset.id]; if(c) sec.querySelectorAll('.numbg').forEach(n=>n.setAttribute('fill',c)); });

// tabs
function show(id){
  document.querySelectorAll('.mapsec').forEach(s=> s.style.display = s.dataset.id===id?'block':'none');
  document.querySelectorAll('.tab').forEach(t=> t.classList.toggle('active', t.dataset.id===id));
}
document.querySelectorAll('.tab').forEach(t=> t.onclick=()=>show(t.dataset.id));
document.querySelectorAll('.toolbar button').forEach(b=> b.onclick=()=>{
  const sec=[...document.querySelectorAll('.mapsec')].find(s=>s.style.display!=='none'); if(!sec)return;
  const st=vbState.get(sec.querySelector('svg'));
  if(b.dataset.z==='in') st.zoomAt(st.x+st.w/2,st.y+st.h/2,0.7);
  else if(b.dataset.z==='out') st.zoomAt(st.x+st.w/2,st.y+st.h/2,1/0.7);
  else st.reset();
});
const want=(location.hash||'').replace('#',''); show(byId[want]?want:MAPS[0].id);
</script>
</body>
</html>
"""
html = (TEMPLATE.replace("%TABS%", TABS).replace("%SECTIONS%", SECTIONS).replace("%MAPS_JSON%", MAPS_JSON))
with open(OUT, "w") as f:
    f.write(html)
print(f"wrote {OUT}  ({len(MAPS)} maps)")
