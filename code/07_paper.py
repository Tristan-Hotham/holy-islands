"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/Hotham_Holy_Islands.pdf and .tex (figures f_*.png sit beside them)."""
import re, subprocess, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # runs the shared fact checks
R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Holy_Islands"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
KEEP = {"DOI"}

# facts stated in words only in the paper
b = R["islands"]["busiest"]
assert [round(x["area"]) for x in b[:6]] == [291, 205, 855, 604, 439, 390]       # Imbros, Paros, Chios, Corfu, Naxos, Andros in GSHHG
assert b[6]["best"] == "Valaam Monastery" and b[7]["best"] == "Abbey of Reichenau"
assert R["far"]["early"][1]["name"] == "Hozoviotissa monastery"
k = R["kinds_by"]
assert k["monastery"]["pct"] > max(k[x]["pct"] for x in ("abbey", "priory", "convent", "hermitage"))
rg = {d["k"]: d for d in R["regions"]}
assert all(rg[x]["dated_pct"] < 33.4 for x in ("france", "galicia", "iberia")) and all(45 < rg[x]["dated_pct"] < 56 for x in ("ireland", "scotland", "wales"))
assert [R["regions"][i]["k"] for i in (4, 6)] == ["brittany", "galicia"] and R["median_sl"] == 1
assert R["far"]["lake_top"][0]["name"].startswith("Saint Vladimir Skete")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{rnd(v):,}"
    if f == "pc": return f"{rnd(v)}\\%"
    if f == "f1": return f"{float(v):.1f}"
    return tex(str(v))


cv, isl = R["coverage"], R["islands"]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sources, what was kept and licences.}\\label{tab:sources}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.0cm}>{\\raggedright\\arraybackslash}p{7.4cm}r>{\\raggedright\\arraybackslash}p{2.0cm}}\\toprule Source & Kept & Records & Licence\\\\\\midrule\n"
      f"Wikidata & Monastic houses with coordinates, worldwide & {R['meta']['n_items_world']:,} & CC0\\\\\n"
      f"Wikidata & Houses in the study area (Europe) & {cv['n']:,} & CC0\\\\\n"
      f"Wikidata & of which with a foundation date (P571) & {cv['dated_n']:,} & CC0\\\\\n"
      f"Wikidata & of which with a dissolution date (P576) & {R['dissolution']['n']:,} & CC0\\\\\n"
      f"GSHHG & Full-resolution land, lake and lake-island polygons & {isl['n_polys']} with houses & LGPL-3.0\\\\\n"
      "Natural Earth & Countries, provinces, populated places & & Public domain\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
L = R["periods"]["labels"]
rows = ""
for d in R["regions"]:
    cells = " & ".join(f"{d[k]['isl']}/{d[k]['n']:,}" if d[k]["n"] else "" for k, l in L)
    rows += f"{tex(d['name'])} & {cells} & {d['isl']}/{d['n']:,} & {d['pct']:.1f}\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Houses on islands / houses, by region and period of foundation; the last two columns include undated houses.}\\label{tab:reg}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{4.4cm}rrrrrr}\\toprule Region & " + " & ".join(tex(l) for k, l in L) + " & All & \\%\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_SOURCES}}", TS).replace("{{TABLE_REG}}", TR)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP
assert "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
