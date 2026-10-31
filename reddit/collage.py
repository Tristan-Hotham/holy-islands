"""r/dataisbeautiful collage for holy-islands: 2400 x 3000 px, light background.
Numbers from data/results.json; points from data/points.json."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
P, S, X, Y, CLS = load_points()
PAPER = "#F7F4EE"; LANDC = "#E6E0D3"
fmt = lambda v: f"{rnd(v):,}"
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=PAPER)
fig.text(.045, .977, "Holy islands", fontproperties=DISP, fontsize=62, color=FG, va="top")
fig.text(.045, .912, f"Where Europe's monasteries went to sea. {fmt(R['islands']['n'])} of {fmt(R['coverage']['n'])} monasteries, abbeys, priories\n"
         "and hermitages in Wikidata stand on islands under 1,000 km² (Great Britain, Ireland and bigger\nislands count as mainland).",
         fontproperties=SERP, fontsize=15.5, color=FG, va="top", linespacing=1.45)

# ---- map ----
EXT = (1.05e6, 6.75e6, 1.25e6, 5.35e6)
ax = fig.add_axes([.01, .37, .98, .455]); ax.set_facecolor(PAPER)
draw_land(ax, fc=LANDC, ec=PAPER, lw=.3)
m = CLS == "mainland"
ax.scatter(X[m], Y[m], s=.6, c="#9C9485", lw=0, alpha=.5, zorder=3, rasterized=True)
for k in ("island", "lake", "small"):
    mm = CLS == k
    ax.scatter(X[mm], Y[mm], s=16, c=CLS_C[k], lw=.5, edgecolors=PAPER, zorder=5)
frame(ax, EXT)
q = {f"Q{v}": i for i, v in enumerate(P["q"])}
idx_name = {n: i for i, n in enumerate(P["n"])}


def lab(i, text, dx, dy, ha):
    """Label on open sea, with a short leader to the house."""
    ax.annotate(text, (X[i], Y[i]), xytext=(X[i] + dx, Y[i] + dy), fontsize=9.6, family=MONO, color=FG, ha=ha, va="center", zorder=9,
                arrowprops=dict(arrowstyle="-", color=MUT, lw=.6, shrinkA=1, shrinkB=3), linespacing=1.3)


sk = R["far"]["skellig"]; io = R["far"]["iona"]; az = R["far"]["top"][0]
lab(q[sk["q"]], f"Skellig Michael\n{sk['d']:.0f} km offshore", -3.6e5, -1.2e5, "right")
lab(q[io["q"]], "Iona, 563", -3.4e5, 1.4e5, "right")
lab(idx_name["Lindisfarne Priory"], "Lindisfarne", 2.6e5, .9e5, "left")
lab(q["Q334008"], "Lérins,\n5th century", -1.2e5, -2.6e5, "right")
lab(q["Q651388"], "Mont-Saint-Michel", -3.2e5, -.5e5, "right")
lab(q["Q1982506"], "Patmos", 2.0e5, -2.4e5, "left")
lab(q["Q1140434"], "Solovetsky,\nWhite Sea", -1.25e6, -.1e5, "right")
lab(q[az["q"]], f"Azores convents,\nup to {fmt(az['d'])} km out", 1.0e5, -4.2e5, "left")

# ---- legend with full names, on plain paper ----
hs = [Line2D([], [], marker="o", ls="", mfc=CLS_C[k], mec=PAPER, ms=9, label=CLS_N[k]) for k in ("small", "island", "lake")]
hs.append(Line2D([], [], marker="o", ls="", mfc="#9C9485", mec="#9C9485", ms=4, label="Mainland: continental Europe, Great Britain, Ireland and islands over 1,000 km²"))
prop = SERP.copy(); prop.set_size(12.5)
fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(.04, .365), ncol=2, frameon=False, prop=prop, handletextpad=.4, columnspacing=1.6, labelspacing=.55)

# ---- chart: share on islands by period ----
G = R["periods"]["groups"]; L = R["periods"]["labels"]
cx = fig.add_axes([.07, .115, .44, .135]); cx.set_facecolor(PAPER)
vals = [G["all"][k]["pct"] for k, l in L]
cx.bar(range(4), vals, color=[HOT, COOL, COOL, COOL], width=.62)
for i, (k, l) in enumerate(L):
    s = G["all"][k]
    cx.text(i, s["pct"] + max(vals) * .05, f"{s['pct']:.1f}%", ha="center", va="bottom", fontsize=11, color=FG, fontproperties=DISPB)
    cx.text(i, -.55, f"{s['isl']} of {fmt(s['n'])}", ha="center", fontsize=8.5, color=MUT, family=MONO)
cx.set_xticks(range(4)); cx.set_xticklabels([l for k, l in L], fontsize=9.5); cx.tick_params(axis="x", length=0, pad=16)
cx.set_yticks([]); cx.set_ylim(0, max(vals) * 1.3); [cx.spines[s].set_visible(False) for s in ("top", "right", "left")]
fig.text(.07, .272, "Share of dated houses on islands, by date of foundation", fontproperties=SERB, fontsize=12.5, color=FG)

# ---- big numbers ----
c = R["compare"]
nums = [(f"{c['early_atl']['pct']:.0f}%", HOT, f"of houses on the Atlantic\nCeltic edge dated before 1100\nare on islands ({c['early_atl']['isl']} of {c['early_atl']['n']})"),
        (f"{c['late_cont']['pct']:.1f}%", COOL, f"of houses founded in France\nand Central Europe from 1100\n({c['late_cont']['isl']} of {fmt(c['late_cont']['n'])})"),
        (f"{R['regions'][11]['isl']}", CLS_C["island"], "island houses around the\nMediterranean, most on\nGreek and Turkish islands")]
for i, (big, col, small) in enumerate(nums):
    y = .28 - i * .07
    fig.text(.585, y, big, fontproperties=DISP, fontsize=34, color=col, va="top")
    fig.text(.75, y - .004, small, family=MONO, fontsize=10, color=FG, va="top", linespacing=1.35)

fig.text(.045, .016, f"Source: Wikidata (CC0) via QLever, retrieved in {RETRIEVED}: monasteries, abbeys, priories, hermitages and clocháns with coordinates.\n"
         f"Islands from GSHHG full-resolution shorelines (LGPL); outlines Natural Earth. Only {R['coverage']['dated_pct']:.0f}% of houses have a foundation date;\n"
         "round-century dates read as mid-century. Analysis and chart: Tristan Hotham, Python and matplotlib  ·  maps.tristanhotham.com/holy-islands",
         family=MONO, fontsize=9, color=MUT, linespacing=1.55, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "holy_islands.png")
fig.savefig(out, facecolor=PAPER, dpi=200)
print("ok", out)
