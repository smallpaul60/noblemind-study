#!/usr/bin/env python3
"""
Generate parchment-toned shaded-relief basemaps for the Bible-lands maps, from
the open Terrarium elevation tiles (AWS open data). Each output is a
hillshaded, parchment-coloured terrain image reprojected to a map's
equirectangular frame, to sit under the routes/labels of a map.

Owned/offline once built (the JPEGs are committed). Run only when
(re)generating a relief — it needs network to fetch the elevation tiles and,
once, the Natural Earth land/lake outlines.

  python3 tools/build_relief.py              # build every region
  python3 tools/build_relief.py exodus land  # build only the named regions

Water is decided region-agnostically: the OCEAN is the below-sea-level area
that lies OUTSIDE the Natural Earth land polygons (so the below-sea-level
Jordan Rift, which sits inside the land mass, is never flooded as sea), and
the named ancient inland lakes (Dead Sea, Sea of Galilee, ...) are drawn to
their true outline. No per-region tuning.
"""
import io, json, math, os, sys, urllib.request
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 NobleMindRelief/1.0"
TILE = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

# parchment palette (matches the maps)
LAND = np.array([229, 212, 168], float)    # #E5D4A8
LAND_HI = np.array([196, 168, 120], float)  # higher ground, browner
WATER = np.array([175, 196, 201], float)    # #AFC4C9
WATER_DEEP = np.array([130, 160, 170], float)

# real ancient inland waters drawn from their outline (NOT modern reservoirs)
ANCIENT_LAKES = {"Dead Sea", "Sea of Galilee", "Lake Tiberias", "Caspian Sea",
                 "Lake Urmia", "Lake Van", "Lake Hula"}

# region -> (bbox lon0,lon1,lat0,lat1 ; tile zoom ; output width ; out path)
# bboxes MUST match the make_geo / proj frame in the matching generator.
REGIONS = {
    "exodus":       ((30.0, 36.9, 27.0, 32.7), 8, 1500, "old-testament-timeline/exodus-relief.jpg"),
    "mesopotamia":  ((29.0, 48.0, 24.0, 38.0), 7, 2000, "old-testament-timeline/relief-mesopotamia.jpg"),
    "canaan":       ((33.9, 36.9, 29.7, 33.6), 9, 1300, "old-testament-timeline/relief-canaan.jpg"),
    "mediterranean":((11.0, 37.8, 29.3, 43.0), 7, 2000, "the-church-christ-built/relief-mediterranean.jpg"),
    "land":         ((33.8, 36.5, 30.9, 33.7), 9, 1100, "the-life-of-christ/relief-land.jpg"),
    "nativity":     ((29.5, 36.3, 29.4, 33.3), 8, 1300, "the-life-of-christ/relief-nativity.jpg"),
    "world":        ((10.0, 50.0, 22.0, 43.5), 6, 2000, "maps/relief-world.jpg"),
}

NE = {  # local cache -> source
    "land":  ("/tmp/ne_10m_land.geojson",
              "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson"),
    "lakes": ("/tmp/ne_lakes.geojson",
              "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_lakes.geojson"),
}


def fetch_tile(z, x, y):
    req = urllib.request.Request(TILE.format(z=z, x=x, y=y), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"), float)


def ne_features(key):
    path, url = NE[key]
    if not os.path.exists(path):
        print(f"  fetching {os.path.basename(path)} ...")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
            f.write(r.read())
    return json.load(open(path))["features"]


def merc_y(lat):
    lr = math.radians(lat)
    return (1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2


def _ring_px(ring, bbox, w, h):
    lon0, lon1, lat0, lat1 = bbox
    return [((lon - lon0) / (lon1 - lon0) * w, (lat1 - lat) / (lat1 - lat0) * h) for lon, lat in ring]


def _ring_hits(ring, bbox):
    lon0, lon1, lat0, lat1 = bbox
    xs = [c[0] for c in ring]; ys = [c[1] for c in ring]
    return not (max(xs) < lon0 - 1 or min(xs) > lon1 + 1 or max(ys) < lat0 - 1 or min(ys) > lat1 + 1)


def rasterize_land(bbox, w, h):
    """True where Natural Earth says LAND (exterior rings filled, holes ignored
    so inland lakes count as land). Its complement is the open ocean."""
    mask = Image.new("1", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for feat in ne_features("land"):
        g = feat["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            if not _ring_hits(poly[0], bbox):
                continue
            pts = _ring_px(poly[0], bbox, w, h)
            if len(pts) >= 3:
                d.polygon(pts, fill=1)
    return np.asarray(mask, bool)


def rasterize_lakes(bbox, w, h):
    mask = Image.new("1", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for feat in ne_features("lakes"):
        if (feat["properties"].get("name") or "") not in ANCIENT_LAKES:
            continue
        g = feat["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            pts = _ring_px(poly[0], bbox, w, h)
            if len(pts) >= 3:
                d.polygon(pts, fill=1)
    return np.asarray(mask, bool)


def build_relief(bbox, zoom, out_path, out_w=1500):
    lon0, lon1, lat0, lat1 = bbox
    n = 2 ** zoom
    tx0 = int((lon0 + 180) / 360 * n); tx1 = int((lon1 + 180) / 360 * n)
    ty0 = int(merc_y(lat1) * n); ty1 = int(merc_y(lat0) * n)
    print(f"  tiles x {tx0}..{tx1}, y {ty0}..{ty1} (z{zoom}) = {(tx1-tx0+1)*(ty1-ty0+1)} tiles")

    cols, rows = tx1 - tx0 + 1, ty1 - ty0 + 1
    mosaic = np.zeros((rows * 256, cols * 256), float)
    for j, ty in enumerate(range(ty0, ty1 + 1)):
        for i, tx in enumerate(range(tx0, tx1 + 1)):
            rgb = fetch_tile(zoom, tx, ty)
            elev = rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256 - 32768
            mosaic[j*256:(j+1)*256, i*256:(i+1)*256] = elev
    m_lon0 = tx0 / n * 360 - 180; m_lon1 = (tx1 + 1) / n * 360 - 180
    m_my0 = ty0 / n; m_my1 = (ty1 + 1) / n

    out_h = int(out_w * (lat1 - lat0) / ((lon1 - lon0) * math.cos(math.radians((lat0+lat1)/2))))
    lons = lon0 + (lon1 - lon0) * (np.arange(out_w) + 0.5) / out_w
    lats = lat1 - (lat1 - lat0) * (np.arange(out_h) + 0.5) / out_h
    sx = ((lons - m_lon0) / (m_lon1 - m_lon0) * mosaic.shape[1]).astype(int)
    my = np.array([merc_y(la) for la in lats])
    sy = ((my - m_my0) / (m_my1 - m_my0) * mosaic.shape[0]).astype(int)
    sx = np.clip(sx, 0, mosaic.shape[1]-1); sy = np.clip(sy, 0, mosaic.shape[0]-1)
    elev = mosaic[np.ix_(sy, sx)]

    # hillshade
    deg_per_px = (lon1 - lon0) / out_w
    m_per_px = deg_per_px * 111320 * math.cos(math.radians((lat0+lat1)/2))
    gy, gx = np.gradient(elev, m_per_px)
    zf = 3.0
    slope = np.arctan(zf * np.hypot(gx, gy))
    aspect = np.arctan2(gy, -gx)
    az, alt = math.radians(315), math.radians(45)
    hs = math.sin(alt) * np.cos(slope) + math.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0, 1)

    # ----- water = real OCEAN (below sea level AND outside the land polygons,
    # so the Jordan Rift / Dead Sea basin stays land) + ancient inland lakes. -----
    land_poly = rasterize_land(bbox, out_w, out_h)
    sea = elev <= 0
    lbl, _ = ndi.label(sea)
    ocean_lbls = set(np.unique(lbl[~land_poly])) - {0}
    ocean = np.isin(lbl, list(ocean_lbls))
    water = ocean | rasterize_lakes(bbox, out_w, out_h)

    img = np.zeros((out_h, out_w, 3), float)
    hyp = np.clip(elev / 1400.0, 0, 1)[..., None]
    base = LAND * (1 - hyp) + LAND_HI * hyp
    shade = np.clip(0.55 + 0.7 * (hs - 0.5), 0.35, 1.12)[..., None]
    land_rgb = np.clip(base * shade, 0, 255)
    depth = np.clip(-elev / 1500.0, 0, 1)[..., None]
    water_rgb = WATER * (1 - depth) + WATER_DEEP * depth
    img[~water] = land_rgb[~water]
    img[water] = water_rgb[water]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(img.astype(np.uint8)).save(out_path, quality=84, optimize=True)
    print(f"  wrote {os.path.relpath(out_path, ROOT)} ({out_w}x{out_h}, {os.path.getsize(out_path)/1e3:.0f} KB)")


if __name__ == "__main__":
    want = sys.argv[1:] or list(REGIONS)
    for name in want:
        if name not in REGIONS:
            print(f"  ! unknown region '{name}' (have: {', '.join(REGIONS)})"); continue
        bbox, zoom, out_w, rel = REGIONS[name]
        print(f"[{name}]")
        build_relief(bbox, zoom, os.path.join(ROOT, rel), out_w)
