"""Parse the QLever TSV of monasteries, abbeys, priories, hermitages and clochans into one record per Wikidata item.
Output: WORK/items.json (all items with coordinates, worldwide) and WORK/parse_stats.json."""
from collections import Counter, defaultdict
from common import *

rows = tsv(os.path.join(RAW, "monasteries.tsv"))
n_rows = len(rows)
ISO = {r["c"]: r["iso"] for r in tsv(os.path.join(ARCH, "arch_countries.tsv")) if r.get("iso")}
CNAME = {r["c"]: r["label"] for r in tsv(os.path.join(ARCH, "arch_countries.tsv"))}
TL = {r["type"]: r["label"] for r in tsv(os.path.join(ARCH, "arch_typelabels.tsv")) if r.get("label")}
for r in tsv(os.path.join(RAW, "dl", "2a0b4d88993ad1bf63f402fc4d1bf5e9.txt")):
    TL[r["c"]] = r["l"]
TL["Q1175763"] = "clochán"          # beehive hut (class named in the query; English label not in the label file)

it = defaultdict(lambda: {"l": "", "pt": None, "inc": set(), "dis": set(), "c": [], "t": [], "sl": 0})
for r in rows:
    x = it[r["m"]]
    if r["l"] and not x["l"]:
        x["l"] = r["l"]
    m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", r["coord"])
    if m and x["pt"] is None:
        x["pt"] = (float(m.group(1)), float(m.group(2)))
    if r["inc"]:
        x["inc"].add(r["inc"])
    if r["dis"]:
        x["dis"].add(r["dis"])
    if r["country"] and r["country"] not in x["c"]:
        x["c"].append(r["country"])
    if r["type"] and r["type"] not in x["t"]:
        x["t"].append(r["type"])
    x["sl"] = max(x["sl"], int(r["sl"] or 0))

# Round-century dates. Wikidata keeps a date of century precision as a full date: '12th century' is stored either as
# 1101-01-01 or as 1100-01-01 (the first or the last year of the century). The excess of 1 January dates on years
# ending in 00 and 01 shows how common this is.
md_by_mod = Counter()
for x in it.values():
    for v in x["inc"]:
        d = date_of(v)
        if d and d[1] == "01-01":
            md_by_mod[d[0] % 100] += 1
typical = sorted(md_by_mod[k] for k in range(2, 100) if k not in (50,))[48]   # median of the other endings


def year_used(v):
    """Year read for analysis, and whether it is a century-precision value."""
    d = date_of(v)
    if not d:
        return None, False
    y, md = d
    if md == "01-01" and y % 100 == 0 and y > 0:
        return y - 50, True          # last year of a century: read as the middle of the century it ends
    if md == "01-01" and y % 100 == 1 and y > 0:
        return y + 49, True          # first year of a century: read as the middle of the century it begins
    return y, False


items = []
bad_inc = 0
for q, x in it.items():
    if not x["pt"]:
        continue
    incs = []
    for v in x["inc"]:
        y, rc = year_used(v)
        if y is None:
            bad_inc += 1
            continue
        incs.append((y, rc, date_of(v)[0]))
    incs.sort()
    dis = sorted(date_of(v)[0] for v in x["dis"] if date_of(v))
    iso = [ISO[c] for c in x["c"] if c in ISO]
    items.append({"q": q, "l": x["l"], "lon": round(x["pt"][0], 5), "lat": round(x["pt"][1], 5),
                  "y": incs[0][0] if incs else None, "yr": incs[0][2] if incs else None, "rc": incs[0][1] if incs else False,
                  "dis": [d for d in dis if d <= 2026], "iso": iso, "cn": [CNAME.get(c, c) for c in x["c"]],
                  "t": x["t"], "sl": x["sl"]})
items.sort(key=lambda r: int(r["q"][1:]))
jsave(items, f"{WORK}/items.json")
jsave({"types": TL}, f"{WORK}/typelabels.json")
st = {"n_rows": n_rows, "n_items": len(it), "n_with_point": len(items), "md_by_mod": {str(k): md_by_mod[k] for k in (0, 1, 2, 50, 99)},
      "typical_md": typical, "bad_inc": bad_inc}
jsave(st, f"{WORK}/parse_stats.json", indent=1)
print(st)
