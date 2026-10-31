"""Island detection with GSHHG full-resolution shorelines.
For every item in the study area: is it on the mainland (a landmass of 1,000 km2 or more: the continents, Great
Britain, Ireland, Iceland, Sicily and other big islands), on a sea island under 1,000 km2, or on an island in a lake;
the area of its island; and its distance to the 'great lands' (continental Europe, Africa, Great Britain, Ireland).
A point that falls in the sea is put on the nearest land within 1.5 km; points further out are checked by name.
Output: WORK/eu_isl.json, WORK/islands.json (island polygons with monasteries, simplified, for the page)."""
from collections import Counter, defaultdict
import numpy as np
import shapely
from shapely.geometry import Polygon, Point
from shapely.strtree import STRtree
from pyproj import Transformer
from common import *

LAEA = Transformer.from_crs(4326, 3035, always_xy=True)
INV = Transformer.from_crs(3035, 4326, always_xy=True)
W, S, E, N = BBOX[0] - 3, BBOX[1] - 3, BBOX[2] + 3, BBOX[3]
polys = []      # (level, area_km2, id, geometry in EPSG:3035)
with open(os.path.join(COAST, "gshhsmeta_f.dat")) as meta, open(os.path.join(COAST, "gshhs_f.dat"), "rb") as dat:
    for line in meta:
        typ, area, npts, south, north, off, nb, pid = line.split()[:8]
        typ, area, npts, south, north, off, nb = int(typ), float(area), int(npts), float(south), float(north), int(off), int(nb)
        if north < S or south > N or typ > 3:
            continue
        dat.seek(off)
        b = np.frombuffer(dat.read(nb), dtype="<f4").astype("f8").reshape(npts, 2)
        lon = np.where(b[:, 0] > 180, b[:, 0] - 360, b[:, 0])
        if lon.max() < W or lon.min() > E:
            continue
        if pid.endswith("-W"):
            continue                   # the far-eastern sliver of Eurasia across the date line
        lon = np.clip(lon, -179.99, 179.99)
        x, y = LAEA.transform(lon, np.clip(b[:, 1], -89.9, 89.9))
        g = Polygon(np.column_stack([x, y]))
        if not g.is_valid:
            g = g.buffer(0)
        polys.append((typ, area if area > 0 else 1e8, pid, g))
print("polygons", Counter(p[0] for p in polys))
geoms = [p[3] for p in polys]
tree = STRtree(geoms)
lvl = np.array([p[0] for p in polys]); area = np.array([p[1] for p in polys])
land_idx = np.where(lvl == 1)[0]
land_tree = STRtree([geoms[i] for i in land_idx])
l3_idx = np.where(lvl == 3)[0]
l3_tree = STRtree([geoms[i] for i in l3_idx])


# landmarks to name the great lands
def poly_at(lon, lat):
    p = Point(*LAEA.transform(lon, lat))
    hit = [land_idx[k] for k in land_tree.query(p, predicate="within")]
    return hit[0] if hit else None


GREAT = {"eurasia": poly_at(10.0, 50.0), "africa": poly_at(5.0, 30.0), "gb": poly_at(-1.5, 52.5), "ireland": poly_at(-8.0, 53.3)}
assert all(v is not None for v in GREAT.values()), GREAT
GREAT_SET = set(GREAT.values())
for k, v in GREAT.items():
    print(k, round(area[v]))
great_union = shapely.union_all([geoms[i] for i in GREAT_SET])
great_bd = great_union.boundary
shapely.prepare(great_bd)

KEY = re.compile(r"(?i)\b(island|isle|islet|isles|islands|île|ile|ilha|isla|isola|eilean|ynys|insel|holy island)\b|\binis|\binish|\binch|insel\b|\bholm\b|\bøy\b|\bö\b|\bsaari\b")

from overrides import OVERRIDE
eu = jload(f"{WORK}/eu.json")
xs, ys = LAEA.transform([x["lon"] for x in eu], [x["lat"] for x in eu])
cls_count = Counter()
island_polys = defaultdict(list)
unresolved = []
for x, px, py in zip(eu, xs, ys):
    p = Point(px, py)
    x["kw"] = bool(KEY.search(x["l"] or ""))
    within = tree.query(p, predicate="within")
    levels = {int(lvl[i]): i for i in within}
    snapped = 0.0
    if 3 in levels:
        li = levels[3]; kind = "lake"
    elif 1 in levels and 2 in levels:
        # in a lake: an island in it within reach, else the shore
        k = l3_tree.query_nearest(p, max_distance=SNAP_KM * 1000, return_distance=True)
        if len(k[0]):
            li = l3_idx[k[0][0]]; kind = "lake"; snapped = float(k[1][0]) / 1000
        else:
            li = levels[1]; kind = "land"; snapped = float(geoms[levels[2]].exterior.distance(p)) / 1000
    elif 1 in levels:
        li = levels[1]; kind = "land"
    else:
        k = land_tree.query_nearest(p, return_distance=True)
        j, d = land_idx[k[0][0]], float(k[1][0]) / 1000
        if d <= SNAP_KM:
            li = j; kind = "land"; snapped = d
        else:
            li = j; kind = "sea"; snapped = d
    a = float(area[li])
    if kind == "lake":
        cls = "lake"
    elif kind == "land":
        cls = "mainland" if a >= ISLAND_KM2 else ("small" if a < SMALL_KM2 else "island")
    else:
        cls = "offshore"     # out at sea: an islet too small for the shoreline data, or a misplaced point
        unresolved.append((x["q"], x["l"], round(snapped, 1), x["c"]))
    how = "shoreline"
    if x["q"] in OVERRIDE:
        cls, why = OVERRIDE[x["q"]]; how = "hand"; x["why"] = why
    x["cls"] = cls; x["how"] = how
    known = how == "shoreline" and cls in ("small", "island", "lake")
    x["iarea"] = round(a, 3) if known else None
    x["snap"] = round(snapped, 2)
    x["pid"] = int(li) if known else None
    if cls in ("small", "island"):
        x["dmain"] = round(float(great_bd.distance(p)) / 1000, 1)
    elif cls == "lake":
        lk = [i for i in tree.query(p.buffer(SNAP_KM * 1000 + 10)) if lvl[i] == 2 and geoms[i].covers(geoms[li] if known else p.buffer(1))]
        x["dmain"] = round(float(geoms[lk[0]].exterior.distance(p)) / 1000, 1) if lk else None    # distance to the lake shore
    elif cls == "offshore":
        x["dmain"] = None
    elif li not in GREAT_SET:
        x["dmain"] = round(float(great_bd.distance(p)) / 1000, 1)     # on a big island (Iceland, Sicily...)
    else:
        x["dmain"] = 0.0
    x["bigisl"] = cls == "mainland" and li not in GREAT_SET
    if x["pid"] is not None:
        island_polys[li].append(x["q"])
    cls_count[cls] += 1
print(cls_count)
print("unresolved", len(unresolved))
for u in sorted(unresolved, key=lambda r: -r[2])[:60]:
    print(u)
jsave(eu, f"{WORK}/eu_isl.json")
jsave(unresolved, f"{WORK}/unresolved.json")

# island outlines with monasteries on them, simplified, in lon/lat, for the page and figures
isl = []
for li, qs in island_polys.items():
    g = geoms[li].simplify(25, preserve_topology=True)
    g = shapely.transform(g, lambda a: np.column_stack(INV.transform(a[:, 0], a[:, 1])))
    g = shapely.set_precision(g, 0.00001)
    isl.append({"id": int(li), "lvl": int(lvl[li]), "area": round(float(area[li]), 3), "n": len(qs), "geom": shapely.geometry.mapping(g)})
jsave(isl, f"{WORK}/islands.json")
print("islands with houses", len(isl))
