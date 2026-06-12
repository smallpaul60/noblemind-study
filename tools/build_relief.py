#!/usr/bin/env python3
"""
Generate a parchment-toned shaded-relief basemap PNG for a map region, from
the open Terrarium elevation tiles (AWS open data). Output is a hillshaded,
parchment-coloured terrain image reprojected to the map's equirectangular
frame, to sit under the routes/labels of a Bible-lands map.

Owned/offline once built (the PNG is committed). Run only when (re)generating
a relief — it needs network to fetch the elevation tiles.

  python3 tools/build_relief.py
"""
import io, math, os, urllib.request
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 NobleMindRelief/1.0"
TILE = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

# parchment palette (matches the maps)
LAND = np.array([229, 212, 168], float)   # #E5D4A8
LAND_HI = np.array([196, 168, 120], float) # higher ground, browner
WATER = np.array([175, 196, 201], float)   # #AFC4C9
WATER_DEEP = np.array([130, 160, 170], float)


def fetch_tile(z, x, y):
    url = TILE.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"), float)


def merc_y(lat):
    lr = math.radians(lat)
    return (1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2


def build_relief(bbox, zoom, out_path, out_w=1500):
    lon0, lon1, lat0, lat1 = bbox
    n = 2 ** zoom
    tx0 = int((lon0 + 180) / 360 * n); tx1 = int((lon1 + 180) / 360 * n)
    ty0 = int(merc_y(lat1) * n); ty1 = int(merc_y(lat0) * n)
    print(f"  tiles x {tx0}..{tx1}, y {ty0}..{ty1} (z{zoom}) = {(tx1-tx0+1)*(ty1-ty0+1)} tiles")

    # mosaic of decoded elevation (Web Mercator)
    cols, rows = tx1 - tx0 + 1, ty1 - ty0 + 1
    mosaic = np.zeros((rows * 256, cols * 256), float)
    for j, ty in enumerate(range(ty0, ty1 + 1)):
        for i, tx in enumerate(range(tx0, tx1 + 1)):
            rgb = fetch_tile(zoom, tx, ty)
            elev = rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256 - 32768
            mosaic[j*256:(j+1)*256, i*256:(i+1)*256] = elev
    # mosaic geographic span
    m_lon0 = tx0 / n * 360 - 180; m_lon1 = (tx1 + 1) / n * 360 - 180
    m_my0 = ty0 / n; m_my1 = (ty1 + 1) / n      # mercator-y fraction at top/bottom

    # resample to equirectangular (linear in lon, linear in lat)
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
    hs = (math.sin(alt) * np.cos(slope) + math.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    hs = np.clip(hs, 0, 1)

    img = np.zeros((out_h, out_w, 3), float)
    land = elev > 0
    # land: parchment tan -> browner with elevation, modulated by hillshade
    hyp = np.clip(elev / 1400.0, 0, 1)[..., None]
    base = LAND * (1 - hyp) + LAND_HI * hyp
    shade = np.clip(0.55 + 0.7 * (hs - 0.5), 0.35, 1.12)[..., None]
    land_rgb = np.clip(base * shade, 0, 255)
    # water: shallow -> deep by depth
    depth = np.clip(-elev / 1200.0, 0, 1)[..., None]
    water_rgb = WATER * (1 - depth) + WATER_DEEP * depth
    img[land] = land_rgb[land]
    img[~land] = water_rgb[~land]

    Image.fromarray(img.astype(np.uint8)).save(out_path, quality=84, optimize=True)
    sz = os.path.getsize(out_path) / 1e3
    print(f"  wrote {os.path.relpath(out_path, ROOT)} ({out_w}x{out_h}, {sz:.0f} KB)")
    return out_w, out_h


if __name__ == "__main__":
    # The Exodus map frame (must match make_geo bbox in build_ot_maps.py)
    build_relief((30, 36.9, 27, 32.7), 8,
                 os.path.join(ROOT, "old-testament-timeline", "exodus-relief.jpg"))
