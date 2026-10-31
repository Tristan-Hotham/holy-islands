"""Countries, study area and regions.
Keeps items in Europe (Natural Earth's Europe plus Cyprus and Turkey, west of 60 E, including Iceland, the Faroes
and Macaronesia). Country: Wikidata's country where it is one of these, else the Natural Earth country under (or
within 25 km of) the point. Region: from the country and the Natural Earth admin-1 unit nearest the point.
Output: WORK/eu.json, data/world.json (outlines for the page)."""
from collections import Counter
import numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely import set_precision
from pyproj import Transformer
from common import *

items = jload(f"{WORK}/items.json")
NE = jload(os.path.join(GEO, "ne_50m_admin_0_countries.geojson"))
A1 = jload(os.path.join(GEO, "ne_10m_admin_1_states_provinces.geojson"))
EUROPE = {f["properties"]["ADM0_A3"] for f in NE["features"] if f["properties"]["CONTINENT"] == "Europe"} | {"CYP", "TUR"}
ALIAS = {"XKS": "KOS", "ALA": "ALD"}
LAEA = Transformer.from_crs(4326, 3035, always_xy=True)


def proj(geom):
    import shapely
    return shapely.transform(geom, lambda a: np.column_stack(LAEA.transform(a[:, 0], a[:, 1])))


cg, ciso = [], []
for f in NE["features"]:
    p = f["properties"]
    if p["ADM0_A3"] in EUROPE or p["CONTINENT"] in ("Europe", "Asia", "Africa"):
        cg.append(shape(f["geometry"])); ciso.append(p["ADM0_A3"])
ctree = STRtree(cg)
a1g, a1p = [], []
for f in A1["features"]:
    p = f["properties"]
    if p["adm0_a3"] in ("GBR", "FRA", "ESP", "IRL", "IMN", "JEY", "GGY"):
        a1g.append(proj(shape(f["geometry"]).buffer(0))); a1p.append(p)
a1tree = STRtree(a1g)

BRITTANY = {"Finistère", "Côtes-d'Armor", "Morbihan", "Ille-et-Vilaine", "Loire-Atlantique"}   # historic Brittany
MED_FRA = {"Provence-Alpes-Côte-d'Azur", "Corse"}
MED_ESP = {"Islas Baleares", "Cataluña", "Valenciana", "Murcia"}
MED = {"ITA", "VAT", "SMR", "MLT", "GRC", "CYP", "TUR", "HRV", "SVN", "MNE", "ALB", "BIH", "MCO"}
NORD = {"NOR", "SWE", "DNK", "FIN", "EST", "LVA", "LTU", "ALD"}
CENT = {"DEU", "AUT", "CHE", "LIE", "LUX", "BEL", "NLD", "POL", "CZE", "SVK", "HUN"}
EAST = {"RUS", "UKR", "BLR", "MDA", "ROU", "BGR", "SRB", "MKD", "KOS"}
REGIONS = [("ireland", "Ireland"), ("scotland", "Scotland"), ("wales", "Wales"), ("england", "England, Man and the Channel Islands"),
           ("brittany", "Brittany"), ("france", "France (rest)"), ("galicia", "Galicia"), ("iberia", "Iberia (rest)"),
           ("natl", "Iceland and the Faroes"), ("nordic", "Scandinavia and the Baltic"), ("central", "Central Europe and the Low Countries"),
           ("med", "Mediterranean"), ("east", "Eastern Europe and the Balkans")]
ATLANTIC = ["ireland", "scotland", "wales", "brittany", "galicia"]


def region(iso, a1):
    if iso == "IRL":
        return "ireland"
    if iso == "GBR":
        g = a1["geonunit"] if a1 else "England"
        return {"Northern Ireland": "ireland", "Scotland": "scotland", "Wales": "wales"}.get(g, "england")
    if iso in ("IMN", "JEY", "GGY"):
        return "england"
    if iso == "FRA":
        if a1 and a1["name"] in BRITTANY:
            return "brittany"
        if a1 and a1["region"] in MED_FRA:
            return "med"
        return "france"
    if iso == "ESP":
        if a1 and a1["region"] == "Galicia":
            return "galicia"
        if a1 and a1["region"] in MED_ESP:
            return "med"
        return "iberia"
    if iso in ("PRT", "AND", "GIB"):
        return "iberia"
    if iso in ("ISL", "FRO"):
        return "natl"
    if iso in NORD:
        return "nordic"
    if iso in CENT:
        return "central"
    if iso in MED:
        return "med"
    if iso in EAST:
        return "east"
    return None


# classes that are not monastic houses (wayside shrines, lodgings, town houses of abbeys, an abbot's palace), and
# Buddhist monasteries (this study is about Christian monasticism): an item is dropped only if all its classes are here
EXCL = {"Q5792403", "Q48772482", "Q21584825", "Q107928374", "Q132291220", "Q10729920",
        "Q427287", "Q844619", "Q65156015", "Q54074585", "Q2567370"}
out, how = [], Counter()
for x in items:
    lon, lat = x["lon"], x["lat"]
    if x["t"] and all(t in EXCL for t in x["t"]):
        if BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]:
            how["excluded_class"] += 1
        continue
    if not (BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]):
        continue
    wd = [ALIAS.get(i, i) for i in x["iso"]]
    iso = next((i for i in wd if i in EUROPE), None)
    pt = Point(lon, lat)
    if iso is None:
        hit = [ciso[i] for i in ctree.query(pt, predicate="intersects")]
        if not hit:
            j = ctree.nearest(pt)
            hit = [ciso[j]] if cg[j].distance(pt) < 0.3 else []
        if hit and wd and hit[0] not in EUROPE:
            how["wd_outside"] += 1; continue
        if not hit or hit[0] not in EUROPE:
            how["outside"] += 1; continue
        iso = hit[0]; how["ne"] += 1
    else:
        how["wd"] += 1
        if iso == "GBR":     # Wikidata often gives the Crown Dependencies as the United Kingdom
            hit = [ciso[i] for i in ctree.query(pt.buffer(0.05), predicate="intersects") if ciso[i] in ("IMN", "JEY", "GGY")]
            if hit:
                iso = hit[0]; how["crown_dep"] += 1
    a1 = None
    if iso in ("GBR", "FRA", "ESP", "IRL", "IMN", "JEY", "GGY"):
        pp = Point(*LAEA.transform(lon, lat))
        j = a1tree.nearest(pp)
        a1 = a1p[j]
        if a1["adm0_a3"] != iso:      # nearest unit across a border: take the nearest unit of the right country
            cand = [k for k in a1tree.query(pp.buffer(60000)) if a1p[k]["adm0_a3"] == iso]
            if cand:
                a1 = a1p[min(cand, key=lambda k: a1g[k].distance(pp))]
    r = region(iso, a1)
    if r is None:
        how["noregion"] += 1; continue
    x["c"] = iso; x["r"] = r
    out.append(x)
print(len(out), how, Counter(x["r"] for x in out).most_common())
jsave(out, f"{WORK}/eu.json")
jsave(dict(how), f"{WORK}/geo_stats.json")
jsave({"regions": REGIONS, "atlantic": ATLANTIC}, f"{WORK}/regions.json")

# world outlines for the page (Europe and neighbours, simplified)
feats = []
for f in NE["features"]:
    p = f["properties"]
    g = shape(f["geometry"])
    mnx, mny, mxx, mxy = g.bounds
    if mxx < -35 or mnx > 65 or mxy < 25 or mny > 83:
        continue
    g = set_precision(g.simplify(0.02, preserve_topology=True), 0.001)
    feats.append({"type": "Feature", "properties": {"iso": p["ADM0_A3"], "name": p["NAME_EN"] if p.get("NAME_EN") else p["NAME"]},
                  "geometry": json.loads(json.dumps(g.__geo_interface__))})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
print("world.json", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")
