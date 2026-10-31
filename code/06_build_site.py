"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; results, page data, outlines and place names are embedded; data/points.json and data/islands.geojson
are loaded by the page. Facts stated in words are checked here (and reused by the blog, paper and collage).
{{DOI}} and https://blog.tristanhotham.com/2026/10/31/holy-islands/ stay as placeholders for the publisher. The full-screen snippet is pasted before </body>."""
import re
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
KEEP = {"DOI", "BLOG_URL", "DOI_URL"}


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


def fill(tpl):
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(m.group(1)), m.group(3)), tpl)


def check():
    """Facts stated in words on the page, blog, paper and collage."""
    c, G = R["compare"], R["periods"]["groups"]["all"]
    pre = {n for y, n, iso in c["pre800_isl_names"]}
    assert pre == {"", "Abbaye Saint-Honorat de Lérins", "Bardsey Abbey", "Caldey Priory", "Priory of Douglas", "abbaye de l'Île Barbe", "Iona Abbey",
                   "Kloster Herrenchiemsee", "Mont-Saint-Michel Abbey", "Abbey of Reichenau", "Frauenchiemsee convent"}, pre
    cab = [r for r in c["pre800_isl_names"] if r[1] == ""][0]
    assert cab[2] == "ESP"           # the unlabelled one is the early monastery on Cabrera (2.95 E, 39.15 N)
    assert len(c["pre800_isl_names"]) == c["all_pre800"]["isl"]
    assert 0.5 <= G["p3"]["pct"] < 1.5 and 0.5 <= G["p4"]["pct"] < 1.5          # 'about 1%'
    assert G["p1"]["pct"] > 3 * G["p3"]["pct"]
    assert c["early_atl"]["pct"] > 20 * c["late_cont"]["pct"]                  # 'far more often'
    assert [n for y, n in c["early_atl_names"]] == ["Bardsey Abbey", "Caldey Priory", "Iona Abbey"]
    rg = {d["k"]: d for d in R["regions"]}
    assert [R["regions"][i]["k"] for i in (0, 1, 2, 11)] == ["ireland", "scotland", "wales", "med"]
    big = sorted([d for d in R["regions"] if d["n"] >= 20], key=lambda d: -d["pct"])
    assert [d["k"] for d in big[:4]] == ["wales", "scotland", "med", "ireland"], [d["k"] for d in big[:5]]
    assert max(R["regions"], key=lambda d: d["isl"])["k"] == "med"
    assert R["compare"]["cont_all"]["n"] > R["coverage"]["n"] / 2                # 'over half the houses'
    f = R["far"]
    assert f["top"][0]["name"] == "Convent of Carmo" and f["top"][0]["lon"] < -24                       # Horta, Azores
    assert all(x["lon"] < -24 for x in f["top"][:5]) and -17.5 < f["top"][5]["lon"] < -16 and f["top"][6]["lon"] < -13 and f["top"][7]["c"] == "MLT"
    assert f["big_top"][0]["name"] == "Þingeyraklaustur" and f["big_top"][0]["y"] == 1133
    assert f["atl"][0]["name"] == "Cille Bharra" and 11.5 < f["skellig"]["d"] < 12.5
    assert [b["name"] for b in R["best"][:7]] == ["Nea Moni of Chios", "Solovetsky Monastery", "Monastery of Saint John the Theologian", "Valaam Monastery",
                                                  "Abbey of Reichenau", "Iona Abbey", "Mont-Saint-Michel Abbey"]
    assert f["skellig"]["y"] is None
    cv = R["coverage"]
    assert cv["per_m_top"][0]["iso"] == "MKD" and {x["iso"] for x in cv["per_m_low"]} == {"FIN", "TUR", "HUN", "UKR", "NOR"}
    assert all(x["per_m"] < rnd(cv["per_m_low"][4]["per_m"]) for x in cv["per_m_low"])
    assert 30 < cv["dated_pct"] < 37                                          # 'a third'
    d = R["dissolution"]
    assert not any(cls != "mainland" for y, n, cls, iso in d["viking_list"])    # 'none on an island'
    assert d["isl_pct"] < d["main_pct"] and d["isl_nongt_pct"] < d["main_pct"]
    s = R["sens"]
    assert abs(s["atl_pre1100"]["pct"] - c["early_atl"]["pct"]) < .05 and all(abs(s[k]["pct"] - G[k]["pct"]) < .5 for k in ("p1", "p2", "p3", "p4"))
    lake_names = {r["l"] for r in jload(f"{WORK}/eu_isl.json") if r["cls"] == "lake"}
    for nm in ("Valaam Monastery", "Inishcaltra Early Medieval Ecclesiastical Site", "Inchcleraun Early Medieval Ecclesiastical Site",
               "Inchagoill Early Medieval Ecclesiastical Site", "Dominican monastery on Margaret Island", "Abbey of Reichenau", "Kloster Herrenchiemsee"):
        assert nm in lake_names, nm


check()


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl)
    left = set(re.findall(r"\{\{([^}]+)\}\}", html))
    assert left <= KEEP, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    Rp = {k: R[k] for k in ("coverage", "islands", "periods", "regions", "compare", "century", "far", "dissolution", "best", "meta")}
    Rp["dissolution"] = {k: v for k, v in Rp["dissolution"].items() if k != "viking_list"}
    Rp["compare"] = {k: v for k, v in Rp["compare"].items() if not k.endswith("_names")}
    html = html.replace("/*RESULTS*/", J(Rp)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J(jload(f"{DATA}/cities.json")))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
