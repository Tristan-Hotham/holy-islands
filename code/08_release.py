"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
{{DOI}}, {{DOI_URL}} and https://blog.tristanhotham.com/2026/10/31/holy-islands/ stay as placeholders for the publisher."""
import re, zipfile, json as _json, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_Holy_Islands"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{rnd(v):,}"
    if f == "pc": return f"{rnd(v)}%"
    if f == "f1": return f"{float(v):.1f}"
    raise ValueError(f)


# facts stated in words in the blog (alt text included)
G = R["periods"]["groups"]
assert rnd(G["atl"]["p1"]["pct"]) == 15 and rnd(G["all"]["p1"]["pct"]) == 4 and all(rnd(G["all"][k]["pct"]) == 1 for k in ("p3", "p4"))
assert all(2.5 <= G["med"][k]["pct"] <= 5.5 for k in ("p1", "p2", "p3", "p4")) and all(G["cont"][k]["pct"] < .5 for k in ("p3", "p4"))
rg = sorted([d for d in R["regions"] if d["n"] >= 20], key=lambda d: -d["pct"])
assert [(d["k"], rnd(d["pct"])) for d in rg[:5]] == [("wales", 13), ("scotland", 12), ("med", 8), ("ireland", 8), ("nordic", 7)], [(d["k"], d["pct"]) for d in rg[:5]]
assert {d["k"] for d in rg[5:]} == {"east", "iberia", "galicia", "england", "brittany", "france", "central"} and all(d["pct"] < 2 for d in rg[5:])
assert max(R["regions"], key=lambda d: d["lake"] / d["n"])["k"] == "ireland"
f = R["far"]["top"]
assert 1375 < f[4]["d"] < f[0]["d"] < 1660 and round(f[5]["d"]) == 666 and round(f[6]["d"]) == 444 and round(f[7]["d"]) == 249
assert all(235 < x["d"] < 245 for x in f[8:9]) and 1 < f[9]["lon"] < 5 and 38.5 < f[9]["lat"] < 40.2 and 1 < f[8]["lon"] < 5      # Cabrera and Menorca
assert [t["iso"] for t in R["coverage"]["top"][:6]] == ["DEU", "FRA", "ITA", "ESP", "GBR", "POL"] and rnd(R["coverage"]["deu_pct"]) == 24
dd = {d["k"]: d["dated_pct"] for d in R["regions"]}
assert rnd(dd["natl"]) == 67 and min(dd, key=dd.get) == "iberia" and dd["iberia"] < 25
dec = dict(R["dissolution"]["by_decade"])
assert 650 < dec[1530] < 750 and dec[1800] > 400 and sum(v for k, v in dec.items() if k < 1500) < 300
import csv
lp = [r for r in csv.DictReader(open(f"{DATA}/houses.csv", encoding="utf-8")) if r["label"] == "Lindisfarne Priory"][0]
assert 1536 <= int(lp["dissolved"]) <= 1541                                  # 'closed by Henry VIII'

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Holy islands: monks, hermits and the edge of the world",
        "slug": SLUG,
        "excerpt": f"Skellig Michael, Iona, Lindisfarne, Bardsey: I checked {R['coverage']['n']:,} monasteries, abbeys and hermitages across Europe against a detailed shoreline. Before 800, {R['compare']['all_pre800']['pct']:.1f}% of dated houses stood on islands; after 1100, about one in a hundred.",
        "seo_description": f"Island monasteries in Europe mapped: {R['islands']['n']} of {R['coverage']['n']:,} monastic houses in Wikidata stand on islands, most often the earliest ones.",
        "tags": ["monasteries", "islands", "early medieval", "Iona", "Skellig Michael", "history", "maps", "data visualisation", "Wikidata"],
        "header_alt": f"Title card reading 'Holy islands' in dark slate and rust red on pale paper, beside a map of Europe where grey dots mark {R['coverage']['n']:,} monastic houses and larger red, blue and green dots mark the {R['islands']['n']} on islands, clustered around western Ireland and Scotland and across the Aegean."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)


def link(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.link(src, dst)


link(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__" or fn in ("points.json",):   # page-only file, rebuilt by the code
                continue
            z.write(os.path.join(ROOT, d, fn), f"{SLUG}/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\emph{", "").replace("}", "").replace("\\&", "&").replace("$^2$", "²").replace("km$^2", "km²")
assert "\\" not in ab and "$" not in ab, ab
zmeta = {"title": "Holy Islands: Monks, Hermits and the Edge of the World. Island Monasteries in Wikidata, Mapped Through Time",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: {PAGE}. Data and code: {REPO}. Blog post: {{https://blog.tristanhotham.com/2026/10/31/holy-islands/}}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["monasticism", "islands", "early medieval", "Insular Christianity", "Dissolution of the Monasteries", "historical geography", "Wikidata", "GSHHG", "maps"],
         "license": "cc-by-4.0",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.soest.hawaii.edu/pwessel/gshhg/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "; zenodo files", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
