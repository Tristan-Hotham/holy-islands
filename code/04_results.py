"""All analysis: island shares by period, century and region, the furthest island houses, dissolutions, coverage
and sensitivity checks. Writes data/results.json (every number quoted anywhere), data/houses.csv, data/period_region.csv,
data/century.csv, data/island_houses.csv, data/points.json and data/site.json (page data)."""
import csv, math, statistics
from collections import Counter, defaultdict
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

eu = jload(f"{WORK}/eu_isl.json")
TL = jload(f"{WORK}/typelabels.json")["types"]
RG = jload(f"{WORK}/regions.json")
REG = RG["regions"]; RN = dict(REG); ATL = set(RG["atlantic"])
PS = jload(f"{WORK}/parse_stats.json"); GS = jload(f"{WORK}/geo_stats.json")
from overrides import OVERRIDE

ISL = ("small", "island", "lake")
isl = lambda x: x["cls"] in ISL
sea = lambda x: x["cls"] in ("small", "island")
pc = lambda a, b: 100 * a / b if b else None
r1 = lambda v: None if v is None else round(v, 1)


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * max(0, c - h), 1), round(100 * min(1, c + h), 1)


# ---------- kinds of house and flags from the Wikidata classes ----------
def kind(x):
    ls = [TL.get(t, "").lower() for t in x["t"]]
    if any("hermitage" in l or "clochán" in l or "skete" in l for l in ls):
        return "hermitage"
    if any("abbey" in l or "abby" in l for l in ls):
        return "abbey"
    if any("priory" in l or "provosty" in l for l in ls):
        return "priory"
    if any("friary" in l or "mendicant" in l for l in ls):
        return "friary"
    if any("convent" in l or "nunnery" in l for l in ls):
        return "convent"
    return "monastery"


KINDS = [("monastery", "Monastery"), ("abbey", "Abbey"), ("priory", "Priory"), ("convent", "Convent or nunnery"),
         ("friary", "Friary"), ("hermitage", "Hermitage")]
future = 0
for x in eu:
    if x["y"] is not None and x["y"] > 2026:      # a few inception dates lie in the future: treated as missing
        x["y"] = x["yr"] = None; x["rc"] = False; future += 1
    x["k"] = kind(x)
    ls = [TL.get(t, "").lower() for t in x["t"]]
    x["ruin"] = any(w in l for l in ls for w in ("ruin", "former", "destroyed", "secularized"))
    x["d"] = x["dis"][0] if x["dis"] else None
    x["p"] = period_of(x["y"])
    x["cent"] = None if x["y"] is None else max(300, math.floor(x["y"] / 100) * 100)
N = len(eu)
dated = [x for x in eu if x["y"] is not None]
assert all(x["y"] <= 2026 for x in dated)

R = {"meta": {"retrieved": RETRIEVED, "page": PAGE, "repo": REPO, "n_rows": PS["n_rows"], "n_items_world": PS["n_items"],
              "small_km2": SMALL_KM2, "island_km2": ISLAND_KM2, "snap_km": SNAP_KM, "excluded_class": GS["excluded_class"], "future_dates": future}}

# ---------- coverage ----------
NE = jload(os.path.join(GEO, "ne_50m_admin_0_countries.geojson"))
POP = {f["properties"]["ADM0_A3"]: f["properties"]["POP_EST"] for f in NE["features"]}
CNAME = {f["properties"]["ADM0_A3"]: f["properties"]["NAME_EN"] or f["properties"]["NAME"] for f in NE["features"]}
CNAME.update({"GBR": "United Kingdom", "CZE": "Czechia", "MKD": "North Macedonia", "BIH": "Bosnia and Herzegovina"})
cc = Counter(x["c"] for x in eu)
top = [{"iso": c, "name": CNAME.get(c, c), "n": n, "pct": r1(pc(n, N)), "per_m": r1(n / POP[c] * 1e6) if POP.get(c) else None}
       for c, n in cc.most_common()]
big = [t for t in top if POP.get(t["iso"], 0) >= 2e6 and t["per_m"] is not None]
R["coverage"] = {
    "n": N, "dated_n": len(dated), "dated_pct": pc(len(dated), N),
    "rc_n": sum(x["rc"] for x in dated), "rc_pct": pc(sum(x["rc"] for x in dated), len(dated)),
    "label_pct": pc(sum(1 for x in eu if x["l"]), N), "sl0_pct": pc(sum(1 for x in eu if x["sl"] == 0), N),
    "n_countries": len(cc), "top": top[:15],
    "deu_pct": pc(cc["DEU"], N), "irl_n": sum(1 for x in eu if x["r"] == "ireland"),
    "per_m_top": sorted(big, key=lambda t: -t["per_m"])[:5], "per_m_low": sorted(big, key=lambda t: t["per_m"])[:5],
    "deu_per_m": next(t["per_m"] for t in top if t["iso"] == "DEU"), "irl_per_m": next(t["per_m"] for t in top if t["iso"] == "IRL"),
    "gbr_per_m": next(t["per_m"] for t in top if t["iso"] == "GBR"),
    "natl_n": sum(1 for x in eu if x["r"] == "natl"),
    "pre800_n": sum(1 for x in dated if x["y"] < 800), "pre1100_n": sum(1 for x in dated if x["y"] < 1100),
}

# ---------- islands overall ----------
cls = Counter(x["cls"] for x in eu)
kw = [x for x in eu if x["kw"]]
nisl = sum(isl(x) for x in eu)
R["islands"] = {
    "n": nisl, "pct": pc(nisl, N), "sea_n": cls["small"] + cls["island"], "sea_pct": pc(cls["small"] + cls["island"], N),
    "small_n": cls["small"], "small_pct": pc(cls["small"], N), "mid_n": cls["island"], "lake_n": cls["lake"],
    "offshore_n": cls["offshore"], "bigisl_n": sum(x["bigisl"] for x in eu),
    "any_pct": pc(nisl + sum(x["bigisl"] for x in eu), N),
    "n_override": len(OVERRIDE), "override_lake": sum(1 for v in OVERRIDE.values() if v[0] == "lake"),
    "kw_n": len(kw), "kw_isl": sum(isl(x) for x in kw), "kw_isl_pct": pc(sum(isl(x) for x in kw), len(kw)),
    "isl_kw_pct": pc(sum(1 for x in eu if isl(x) and x["kw"]), nisl),
    "n_polys": len({x["pid"] for x in eu if x.get("pid") is not None}),
    "shoreline_isl": sum(1 for x in eu if isl(x) and x["how"] == "shoreline"),
}
# islands with most houses (named after their best-documented house)
byp = defaultdict(list)
for x in eu:
    if x.get("pid") is not None:
        byp[x["pid"]].append(x)
R["islands"]["busiest"] = [{"n": len(v), "area": v[0]["iarea"], "best": max(v, key=lambda x: x["sl"])["l"], "c": v[0]["c"], "r": v[0]["r"]}
                           for v in sorted(byp.values(), key=lambda v: -len(v))[:10]]


# ---------- by period, group and region ----------
def share(rows):
    n = len(rows); k = sum(isl(x) for x in rows); lo, hi = wilson(k, n)
    return {"n": n, "isl": k, "sea": sum(sea(x) for x in rows), "pct": r1(pc(k, n)), "lo": lo, "hi": hi}


GROUPS = [("all", "All Europe", lambda x: True), ("atl", "Atlantic Celtic edge", lambda x: x["r"] in ATL),
          ("cont", "Continental (France and Central Europe)", lambda x: x["r"] in ("france", "central")),
          ("med", "Mediterranean", lambda x: x["r"] == "med"), ("nordic", "Scandinavia and the Baltic", lambda x: x["r"] == "nordic"),
          ("east", "Eastern Europe and the Balkans", lambda x: x["r"] == "east")]
per = {}
for g, gl, f in GROUPS:
    rows = [x for x in eu if f(x)]
    per[g] = {"name": gl, "all": share(rows), "undated": share([x for x in rows if x["y"] is None])}
    for k, lab, a, b in PERIODS:
        per[g][k] = share([x for x in rows if x["p"] == k])
    per[g]["pre1100"] = share([x for x in rows if x["y"] is not None and x["y"] < 1100])
    per[g]["post1100"] = share([x for x in rows if x["y"] is not None and x["y"] >= 1100])
R["periods"] = {"labels": [[k, lab] for k, lab, a, b in PERIODS], "groups": per}
regs = []
for k, nm in REG:
    rows = [x for x in eu if x["r"] == k]
    d = {"k": k, "name": nm, **share(rows), "dated": sum(1 for x in rows if x["y"] is not None)}
    d["dated_pct"] = r1(pc(d["dated"], d["n"]))
    d["lake"] = sum(1 for x in rows if x["cls"] == "lake"); d["small"] = sum(1 for x in rows if x["cls"] == "small")
    for pk, lab, a, b in PERIODS:
        s = share([x for x in rows if x["p"] == pk]); d[pk] = s
    d["pre1100"] = share([x for x in rows if x["y"] is not None and x["y"] < 1100])
    regs.append(d)
R["regions"] = regs
RR = {d["k"]: d for d in regs}

# early Atlantic against later Continental
ea = per["atl"]["pre1100"]; lc = per["cont"]["post1100"]
R["compare"] = {"early_atl": ea, "late_cont": lc, "ratio": round(ea["pct"] / lc["pct"]) if lc["pct"] else None,
                "atl_pre800": per["atl"]["p1"], "all_pre800": per["all"]["p1"], "all_p3": per["all"]["p3"], "all_p4": per["all"]["p4"],
                "atl_all": per["atl"]["all"], "cont_all": per["cont"]["all"], "med_all": per["med"]["all"]}
R["compare"]["early_atl_names"] = sorted([(x["y"], x["l"]) for x in eu if x["r"] in ATL and x["y"] is not None and x["y"] < 1100 and isl(x)])
R["compare"]["pre800_isl_names"] = sorted([(x["y"], x["l"], x["c"]) for x in eu if x["p"] == "p1" and isl(x)])

# ---------- by century ----------
cent = []
for c in range(300, 2000, 100):
    rows = [x for x in dated if x["cent"] == c]
    s = share(rows); s["c"] = c
    s["atl"] = share([x for x in rows if x["r"] in ATL]); s["rest"] = share([x for x in rows if x["r"] not in ATL])
    cent.append(s)
R["century"] = cent

# ---------- furthest from the mainland ----------
far = sorted([x for x in eu if sea(x) and x["dmain"] is not None], key=lambda x: -x["dmain"])
fmt_far = lambda x: {"q": x["q"], "name": x["l"] or "(no English name)", "c": x["c"], "cname": CNAME.get(x["c"], x["c"]), "d": x["dmain"], "y": x["y"], "yr": x["yr"],
                     "area": x["iarea"], "lon": x["lon"], "lat": x["lat"], "r": x["r"]}
seen, farl = set(), []
for x in far:           # one house per island in the table
    key = x.get("pid") or x["q"]
    if key in seen:
        continue
    seen.add(key); farl.append(fmt_far(x))
early = [x for x in far if x["y"] is not None and x["y"] < 1300]
atl_far = [x for x in far if x["r"] in ATL | {"england", "natl", "nordic", "brittany"}]
R["far"] = {"top": farl[:12], "early": [fmt_far(x) for x in early[:8]], "atl": [fmt_far(x) for x in atl_far[:10]],
            "macaronesia_n": sum(1 for x in eu if x["lon"] < -12 and x["lat"] < 40 and sea(x)),
            "over100_n": sum(1 for x in far if x["dmain"] > 100), "median_sea": statistics.median(x["dmain"] for x in far),
            "skellig": next(fmt_far(x) for x in far if "Skellig" in x["l"]),
            "iona": next(fmt_far(x) for x in far if x["l"] == "Iona Abbey")}
bigs = sorted([x for x in eu if x["bigisl"]], key=lambda x: -x["dmain"])
R["far"]["big_top"] = [fmt_far(x) for x in bigs[:6]]
R["far"]["isl_n"] = sum(1 for x in eu if x["c"] == "ISL")
lakes = sorted([x for x in eu if x["cls"] == "lake" and x["dmain"] is not None], key=lambda x: -x["dmain"])
R["far"]["lake_top"] = [fmt_far(x) for x in lakes[:5]]

# ---------- dissolutions ----------
dd = [x for x in eu if x["d"] is not None]
yc = Counter(x["d"] for x in dd)


def wave(a, b, f=lambda x: True):
    return sum(1 for x in dd if a <= x["d"] <= b and f(x))


ew = lambda x: x["r"] in ("england", "wales")
waves = {"dissolution_ew": wave(1536, 1541, ew), "dissolution_ew_all": sum(1 for x in dd if ew(x)),
         "reform_scot": wave(1559, 1600, lambda x: x["r"] == "scotland"), "scot_all": sum(1 for x in dd if x["r"] == "scotland"),
         "ireland_1536_1600": wave(1536, 1600, lambda x: x["r"] == "ireland"), "ireland_all": sum(1 for x in dd if x["r"] == "ireland"),
         "france_rev": wave(1789, 1795, lambda x: x["c"] == "FRA"), "france_all": sum(1 for x in dd if x["c"] == "FRA"),
         "german_1802_1811": wave(1802, 1811, lambda x: x["c"] in ("DEU", "AUT", "CHE", "BEL", "LUX", "NLD")),
         "josephine_1780_1790": wave(1780, 1790, lambda x: x["c"] in ("AUT", "CZE", "HUN", "SVK", "BEL", "ITA", "SVN", "HRV")),
         "spain_1835_1837": wave(1835, 1837, lambda x: x["c"] == "ESP"), "portugal_1834": wave(1834, 1834, lambda x: x["c"] == "PRT"),
         "reformation_1520_1599": wave(1520, 1599), "rev_1780_1815": wave(1780, 1815),
         "viking": wave(793, 1066, lambda x: x["r"] in ATL | {"england", "france", "nordic"}),
         "viking_all": wave(793, 1066)}
viking_list = sorted([(x["d"], x["l"], x["cls"], x["c"]) for x in dd if 793 <= x["d"] <= 1066])
isl_d = [x for x in eu if isl(x)]; main_d = [x for x in eu if x["cls"] == "mainland"]
R["dissolution"] = {
    "n": len(dd), "pct": pc(len(dd), N), "top_years": [[y, n] for y, n in yc.most_common(12)],
    "by_decade": sorted(Counter(x["d"] // 10 * 10 for x in dd if 500 <= x["d"] <= 1999).items()),
    "waves": waves, "ew_pct": pc(waves["dissolution_ew"], waves["dissolution_ew_all"]),
    "france_rev_pct": pc(waves["france_rev"], waves["france_all"]),
    "reform_rev_pct": pc(waves["reformation_1520_1599"] + waves["rev_1780_1815"], len(dd)),
    "viking_list": viking_list,
    "isl_pct": pc(sum(1 for x in isl_d if x["d"] is not None), len(isl_d)),
    "main_pct": pc(sum(1 for x in main_d if x["d"] is not None), len(main_d)),
    "isl_ruin_pct": pc(sum(1 for x in isl_d if x["ruin"] or x["d"] is not None), len(isl_d)),
    "main_ruin_pct": pc(sum(1 for x in main_d if x["ruin"] or x["d"] is not None), len(main_d)),
    "ruin_n": sum(1 for x in eu if x["ruin"]), "ended_n": sum(1 for x in eu if x["ruin"] or x["d"] is not None),
    "isl_med_dis": statistics.median([x["d"] for x in isl_d if x["d"] is not None]),
    "main_med_dis": statistics.median([x["d"] for x in main_d if x["d"] is not None]),
}
R["dissolution"]["ended_pct"] = pc(R["dissolution"]["ended_n"], N)
# atlantic island houses: dated dissolution or ruin, early foundations
atl_isl = [x for x in eu if x["r"] in ATL | {"england"} and isl(x)]
R["dissolution"]["atl_isl_n"] = len(atl_isl)
R["dissolution"]["atl_isl_ended"] = sum(1 for x in atl_isl if x["ruin"] or x["d"] is not None)

# ---------- kinds ----------
kc = Counter(x["k"] for x in eu); ki = Counter(x["k"] for x in eu if isl(x))
R["kinds"] = [{"k": k, "name": nm, "n": kc[k], "isl": ki[k], "pct": r1(pc(ki[k], kc[k]))} for k, nm in KINDS]
R["kinds_by"] = {k: {"n": kc[k], "isl": ki[k], "pct": pc(ki[k], kc[k])} for k, nm in KINDS}

# ---------- sensitivity ----------
def alt_year(x):
    """The other reading of a year ending in 00: the middle of the century it begins (1100 as the 12th century)."""
    if not x["rc"] or x["yr"] % 100 != 0:
        return x["y"]
    return x["yr"] + 50


sens = {}
for k, lab, a, b in PERIODS:
    rows = [x for x in eu if x["y"] is not None and a <= alt_year(x) <= b]
    sens[k] = share(rows)
sens["atl_pre1100"] = share([x for x in eu if x["r"] in ATL and x["y"] is not None and alt_year(x) < 1100])
sens["cont_post1100"] = share([x for x in eu if x["r"] in ("france", "central") and x["y"] is not None and alt_year(x) >= 1100])
nr = [x for x in dated if not x["rc"]]
for k, lab, a, b in PERIODS:
    sens["exact_" + k] = share([x for x in nr if x["p"] == k])
sens["small_only_p1"] = r1(pc(sum(1 for x in eu if x["p"] == "p1" and x["cls"] == "small"), sum(1 for x in eu if x["p"] == "p1")))
sens["small_only_p4"] = r1(pc(sum(1 for x in eu if x["p"] == "p4" and x["cls"] == "small"), sum(1 for x in eu if x["p"] == "p4")))
sens["any_p1"] = r1(pc(sum(1 for x in eu if x["p"] == "p1" and (isl(x) or x["bigisl"])), sum(1 for x in eu if x["p"] == "p1")))
sens["any_p4"] = r1(pc(sum(1 for x in eu if x["p"] == "p4" and (isl(x) or x["bigisl"])), sum(1 for x in eu if x["p"] == "p4")))
sens["no_override_n"] = R["islands"]["shoreline_isl"]
R["sens"] = sens

# ---------- famous island houses (for cards) ----------
best = sorted([x for x in eu if isl(x)], key=lambda x: -x["sl"])
R["best"] = [{"q": x["q"], "name": x["l"], "c": x["c"], "cname": CNAME.get(x["c"], x["c"]), "y": x["y"], "yr": x["yr"], "sl": x["sl"],
              "cls": x["cls"], "d": x["dmain"], "area": x["iarea"], "r": x["r"]} for x in best[:12]]
R["median_sl"] = statistics.median(x["sl"] for x in eu)
R["best_mainland_median_sl"] = statistics.median(x["sl"] for x in eu if x["cls"] == "mainland")
R["best_island_median_sl"] = statistics.median(x["sl"] for x in eu if isl(x))

lp = next(x for x in eu if x["l"] == "Lindisfarne Priory"); ba = next(x for x in eu if x["l"] == "Bardsey Abbey")
R["compare"]["cont_lake"] = sum(1 for x in eu if x["r"] in ("france", "central") and x["cls"] == "lake")
medi = [x for x in eu if x["r"] == "med" and isl(x)]
R["compare"]["med_grc_tur_pct"] = pc(sum(1 for x in medi if x["c"] in ("GRC", "TUR")), len(medi))
R["compare"]["isl_grc_tur_pct"] = pc(sum(1 for x in eu if isl(x) and x["c"] in ("GRC", "TUR")), nisl)
ng = [x for x in eu if isl(x) and x["c"] not in ("GRC", "TUR")]
R["dissolution"]["isl_nongt_pct"] = pc(sum(1 for x in ng if x["d"] is not None), len(ng))
R["lindis"] = {"y": lp["yr"], "bardsey_d": ba["d"]}
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- data files ----------
CL = {"mainland": "Mainland", "small": "Small sea island (under 25 km2)", "island": "Sea island (25 to 1,000 km2)",
      "lake": "Island in a lake or river", "offshore": "At sea, not placed"}
with open(f"{DATA}/houses.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["wikidata", "label", "lon", "lat", "country", "region", "kind", "classes", "inception_raw_year", "round_century",
                "year_used", "period", "dissolved", "former_or_ruin_class", "setting", "setting_how", "island_area_km2",
                "km_to_mainland", "big_island", "label_names_island", "sitelinks"])
    for x in eu:
        w.writerow([x["q"], dash(x["l"]), x["lon"], x["lat"], x["c"], RN[x["r"]], x["k"], "|".join(x["t"]), x["yr"], int(x["rc"]), x["y"],
                    dict((k, l) for k, l, a, b in PERIODS).get(x["p"], ""), x["d"], int(x["ruin"]), CL[x["cls"]], x["how"],
                    x["iarea"], x["dmain"], int(x["bigisl"]), int(x["kw"]), x["sl"]])
with open(f"{DATA}/period_region.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["region", "period", "houses", "on_islands", "pct", "ci_low", "ci_high"])
    for d in regs:
        for k, lab, a, b in PERIODS:
            s = d[k]; w.writerow([d["name"], lab, s["n"], s["isl"], s["pct"], s["lo"], s["hi"]])
        s = d; w.writerow([d["name"], "All, dated or not", s["n"], s["isl"], s["pct"], s["lo"], s["hi"]])
with open(f"{DATA}/century.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["century", "dated_houses", "on_islands", "pct", "atlantic_houses", "atlantic_on_islands", "rest_houses", "rest_on_islands"])
    for s in cent:
        w.writerow([s["c"], s["n"], s["isl"], s["pct"], s["atl"]["n"], s["atl"]["isl"], s["rest"]["n"], s["rest"]["isl"]])
with open(f"{DATA}/island_houses.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["wikidata", "label", "country", "region", "setting", "island_area_km2", "km_to_mainland_or_lake_shore", "year_used", "dissolved", "how", "note"])
    for x in sorted([x for x in eu if isl(x)], key=lambda x: -(x["dmain"] or 0)):
        w.writerow([x["q"], dash(x["l"]), x["c"], RN[x["r"]], CL[x["cls"]], x["iarea"], x["dmain"], x["y"], x["d"], x["how"], x.get("why", "")])

# ---------- page data ----------
CI = sorted(cc); RI = [k for k, nm in REG]; KI = [k for k, nm in KINDS]; CLS = ["mainland", "small", "island", "lake", "offshore"]
P = {"x": [], "y": [], "cl": [], "yr": [], "rc": [], "d": [], "r": [], "c": [], "k": [], "sl": [], "q": [], "dm": [], "a": [], "ru": [], "n": [], "big": []}
for x in sorted(eu, key=lambda x: (isl(x), x["sl"])):     # islands last so they draw on top
    P["x"].append(round(x["lon"] * 1e4)); P["y"].append(round(x["lat"] * 1e4)); P["cl"].append(CLS.index(x["cls"]))
    P["yr"].append(x["y"]); P["rc"].append(int(x["rc"])); P["d"].append(x["d"]); P["r"].append(RI.index(x["r"]))
    P["c"].append(CI.index(x["c"])); P["k"].append(KI.index(x["k"])); P["sl"].append(x["sl"]); P["q"].append(int(x["q"][1:]))
    P["dm"].append(x["dmain"]); P["a"].append(x["iarea"]); P["ru"].append(int(x["ruin"])); P["n"].append(dash(x["l"])); P["big"].append(int(x["bigisl"]))
jsave(P, f"{DATA}/points.json")
import shapely
from shapely.geometry import shape as _shape, mapping as _mapping
feats = []
for d in jload(f"{WORK}/islands.json"):
    g = shapely.set_precision(_shape(d["geom"]), 0.0001)
    feats.append({"type": "Feature", "properties": {"area": d["area"], "n": d["n"], "lake": int(d["lvl"] == 3)}, "geometry": _mapping(g)})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/islands.geojson")
clab = []
for f in NE["features"]:
    p = f["properties"]
    if p["ADM0_A3"] in cc or (p["CONTINENT"] == "Europe"):
        clab.append([p["ADM0_A3"], CNAME.get(p["ADM0_A3"], p["NAME"]), round(p["LABEL_X"], 3), round(p["LABEL_Y"], 3), p["POP_EST"]])
PP = jload(os.path.join(GEO, "ne_10m_populated_places_simple.geojson"))
cities = []
for f in PP["features"]:
    p = f["properties"]; lon, lat = f["geometry"]["coordinates"][:2]
    if BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3] and p["pop_max"] >= 20000:
        cities.append({"name": p["name"], "lat": round(lat, 4), "lon": round(lon, 4), "pop": p["pop_max"], "iso": p["adm0_a3"], "cap": int(p["adm0cap"] == 1)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
SITE = {"clab": clab, "countries": [[c, CNAME.get(c, c)] for c in CI], "regions": REG, "kinds": KINDS, "cls": CLS,
        "types": {t: TL.get(t, "") for t in {t for x in eu for t in x["t"]}}}
jsave(SITE, f"{DATA}/site.json")
print("points.json", os.path.getsize(f"{DATA}/points.json") // 1024, "KB")
print(json.dumps({k: R[k] for k in ("islands", "compare")}, ensure_ascii=False)[:3000])
