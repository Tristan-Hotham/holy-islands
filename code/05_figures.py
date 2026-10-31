"""Figures for the paper (release/paper/f_*.png) and blog (release/blog/b_*.png), and the social card (header.png)."""
import shutil
from collections import Counter
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
P, S, X, Y, CLS = load_points()
PAP = os.path.join(ROOT, "release", "paper"); BLG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLG, exist_ok=True)
fmt = lambda v: f"{rnd(v):,}"


def both(fig, name, blog=True):
    save(fig, f"{PAP}/f_{name}.png")
    if blog:
        shutil.copy(f"{PAP}/f_{name}.png", f"{BLG}/b_{name}.png")


def scatter_houses(ax, sel=None, smain=1.2, sisl=9, alpha_main=.45):
    m = CLS == "mainland" if sel is None else (CLS == "mainland") & sel
    ax.scatter(X[m], Y[m], s=smain, c=CLS_C["mainland"], lw=0, alpha=alpha_main, zorder=3, rasterized=True)
    for k in ("island", "lake", "small"):
        m = CLS == k if sel is None else (CLS == k) & sel
        ax.scatter(X[m], Y[m], s=sisl, c=CLS_C[k], lw=.4, edgecolors="#FFFFFF", zorder=5)


def legend_cls(ax, loc="lower left", fs=9.5, anchor=None):
    hs = [Line2D([], [], marker="o", ls="", mfc=CLS_C[k], mec="#FFFFFF" if k != "mainland" else CLS_C[k], ms=7 if k != "mainland" else 4, label=CLS_N[k])
          for k in ("small", "island", "lake", "mainland")]
    lg = ax.legend(handles=hs, loc=loc, bbox_to_anchor=anchor, frameon=True, fontsize=fs, framealpha=.92, facecolor=BG, edgecolor=RULE, borderpad=.8)
    for t in lg.get_texts():
        t.set_color(FG)


# ---------- 1. Europe map ----------
fig = plt.figure(figsize=(11, 9.2), facecolor=BG); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
draw_land(ax); scatter_houses(ax); frame(ax, EUR_EXT); legend_cls(ax, anchor=(.01, .01))
ax.text(.015, .975, f"{fmt(R['coverage']['n'])} monastic houses in Wikidata", transform=ax.transAxes, fontproperties=DISPB, fontsize=19, color=FG, va="top")
ax.text(.015, .935, f"{fmt(R['islands']['n'])} ({R['islands']['pct']:.1f}%) stand on islands under 1,000 km²", transform=ax.transAxes, family=MONO, fontsize=11, color=MUT, va="top")
both(fig, "map_europe")

# ---------- 2. Atlantic edge map ----------
ATLX = ext_ll(-11.0, 42.0, 2.5, 59.3)
fig = plt.figure(figsize=(8.6, 8.6 * (ATLX[3] - ATLX[2]) / (ATLX[1] - ATLX[0])), facecolor=BG); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG)
draw_land(ax); scatter_houses(ax, smain=3, sisl=34, alpha_main=.55); frame(ax, ATLX)
lab = {"Q198409": ("Iona", 1, 1), "Q105159796": ("Skellig Michael", 1, -1), "Q13125318": ("Bardsey", -1, 0), "Q13130875": ("Caldey", -1, -1),
       "Q651388": ("Mont-Saint-Michel", 1, -1)}
P_q = {f"Q{q}": i for i, q in enumerate(P["q"])}
for q, (nm, dx, dy) in lab.items():
    i = P_q.get(q)
    if i is None:
        continue
    ax.annotate(nm, (X[i], Y[i]), xytext=(X[i] + dx * 1.2e5, Y[i] + dy * .9e5), fontsize=10.5, family=MONO, color=FG, ha="left" if dx > 0 else "right",
                va="center", arrowprops=dict(arrowstyle="-", color=MUT, lw=.7), zorder=8)
# Lindisfarne (one of several items): label the priory
for q, nm, dx, dy in (("Q1361498", "Lindisfarne", 1, .3),):
    i = next((P_q[k] for k in P_q if P["n"][P_q[k]] == "Lindisfarne Priory"), None)
    if i is not None:
        ax.annotate(nm, (X[i], Y[i]), xytext=(X[i] + 1.2e5, Y[i] + .4e5), fontsize=10.5, family=MONO, color=FG, va="center",
                    arrowprops=dict(arrowstyle="-", color=MUT, lw=.7), zorder=8)
ax.text(.03, .975, "The Atlantic edge", transform=ax.transAxes, fontproperties=DISPB, fontsize=20, color=FG, va="top")
legend_cls(ax, loc="lower right", fs=9)
both(fig, "map_atlantic")

# ---------- 3. Periods by group ----------
G = R["periods"]["groups"]; L = R["periods"]["labels"]
grps = [("all", "All Europe"), ("atl", "Atlantic Celtic edge"), ("cont", "France and Central Europe"), ("med", "Mediterranean")]
fig, ax = plt.subplots(figsize=(10, 5.6), facecolor=BG); ax.set_facecolor(BG)
for j, (g, nm) in enumerate(grps):
    xs = np.arange(len(L)) + (j - 1.5) * .17
    for i, (k, lab) in enumerate(L):
        s = G[g][k]
        if not s["n"]:
            continue
        ax.plot([xs[i], xs[i]], [s["lo"], s["hi"]], color=GRP_C[g], lw=1.6, alpha=.45, solid_capstyle="round")
        ax.scatter(xs[i], s["pct"], s=26 + 3.4 * np.sqrt(s["n"]), color=GRP_C[g], zorder=4, edgecolors="#FFFFFF", lw=.7)
        if g == "atl" or (g == "all"):
            ax.text(xs[i], s["hi"] + .9 if g == "atl" else s["pct"] - 1.6, f"{s['isl']}/{fmt(s['n'])}", fontsize=8.2, color=GRP_C[g], ha="center", va="bottom" if g == "atl" else "top")
    ax.scatter([], [], s=60, color=GRP_C[g], label=nm)
ax.set_xticks(range(len(L))); ax.set_xticklabels([l for k, l in L]); ax.set_ylabel("Share founded on islands (%)")
ax.set_ylim(-2.5, 42); ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
ax.set_xlabel("Date of foundation in Wikidata"); lg = ax.legend(frameon=False, fontsize=10, loc="upper right")
ax.set_title("Share of dated monastic houses on islands, by date of foundation", loc="left", fontproperties=DISPB, fontsize=15, color=FG, pad=12)
fig.text(.01, .01, "Dots sized by the number of dated houses; lines are 95% intervals (Wilson). Labels: houses on islands / dated houses.", fontsize=8.5, color=MUT)
fig.tight_layout(rect=(0, .03, 1, 1)); both(fig, "periods")

# ---------- 4. Regions ----------
rg = sorted([d for d in R["regions"] if d["n"] >= 20], key=lambda d: d["pct"])
fig, ax = plt.subplots(figsize=(10, 6.2), facecolor=BG); ax.set_facecolor(BG)
atl = set(["ireland", "scotland", "wales", "brittany", "galicia"])
for i, d in enumerate(rg):
    sea_pct = 100 * (d["isl"] - d["lake"]) / d["n"]; lake_pct = 100 * d["lake"] / d["n"]
    ax.barh(i, sea_pct, color=HOT if d["k"] in atl else COOL, height=.62)
    ax.barh(i, lake_pct, left=sea_pct, color=CLS_C["lake"], height=.62)
    ax.text(d["pct"] + .25, i, f"{d['pct']:.1f}%  ({d['isl']} of {fmt(d['n'])})", va="center", fontsize=9.5, color=FG)
ax.set_yticks(range(len(rg))); ax.set_yticklabels([d["name"] for d in rg], fontsize=10)
ax.set_xlim(0, max(d["pct"] for d in rg) * 1.45); ax.spines[["top", "right"]].set_visible(False); ax.set_xlabel("Share of monastic houses on islands (%), dated or not")
ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
hs = [plt.Rectangle((0, 0), 1, 1, color=HOT), plt.Rectangle((0, 0), 1, 1, color=COOL), plt.Rectangle((0, 0), 1, 1, color=CLS_C["lake"])]
ax.legend(hs, ["Sea islands, Atlantic Celtic edge", "Sea islands, elsewhere", "Islands in lakes and rivers"], frameon=False, fontsize=9.5, loc="lower right")
ax.set_title("Island share by region", loc="left", fontproperties=DISPB, fontsize=15, color=FG, pad=10)
fig.tight_layout(); both(fig, "regions")

# ---------- 5. Century ----------
C = [c for c in R["century"] if c["c"] >= 400]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.4), facecolor=BG, sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
for a in (a1, a2):
    a.set_facecolor(BG); a.spines[["top", "right"]].set_visible(False)
xs = [c["c"] for c in C]
a1.fill_between(xs, [c["lo"] for c in C], [c["hi"] for c in C], color=COOL, alpha=.14, lw=0)
a1.plot(xs, [c["pct"] for c in C], color=COOL, lw=2.2, marker="o", ms=5)
a1.set_ylabel("On islands (%)"); a1.grid(axis="y", color=RULE, lw=.8); a1.set_ylim(0, None)
a1.set_title("Island share by century of foundation, all Europe", loc="left", fontproperties=DISPB, fontsize=15, color=FG, pad=10)
a2.bar(xs, [c["n"] for c in C], width=70, color="#A39B8C"); a2.set_ylabel("Dated houses")
a2.set_xticks(xs); a2.set_xticklabels([f"{c}s" for c in xs], rotation=0, fontsize=8.5)
fig.text(.01, .01, "Shaded band: 95% interval. Round-century dates read as the middle of the century.", fontsize=8.5, color=MUT)
fig.tight_layout(rect=(0, .03, 1, 1)); both(fig, "century")

# ---------- 6. Furthest ----------
F = R["far"]["top"][:10]
extra = [R["far"]["skellig"], R["far"]["iona"]]
rows = F + extra
fig, ax = plt.subplots(figsize=(10, 6.2), facecolor=BG); ax.set_facecolor(BG)
for i, f in enumerate(rows[::-1]):
    c = HOT if f["r"] in atl else COOL
    ax.plot([0, f["d"]], [i, i], color=c, lw=2, alpha=.6); ax.scatter(f["d"], i, s=50, color=c, zorder=3)
    ax.text(f["d"] + 25, i, f"{f['d']:,.0f} km", va="center", fontsize=9.5, color=FG)
ax.set_yticks(range(len(rows))); short = lambda t: (lambda u: u[:1].upper() + u[1:])(t.split(" (")[0] if len(t) > 38 else t)
ax.set_yticklabels([f"{short(f['name'])[:40]}, {f['cname']}" for f in rows[::-1]], fontsize=9.5)
ax.axhline(1.5, color=MUT, lw=.6, ls=":")
ax.set_xlabel("km to continental Europe, Africa, Great Britain or Ireland"); ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(0, max(f["d"] for f in rows) * 1.12); ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
ax.set_title("Furthest from the mainland", loc="left", fontproperties=DISPB, fontsize=15, color=FG, pad=10)
fig.tight_layout(); both(fig, "far")

# ---------- 7. Dissolutions ----------
D = R["dissolution"]["by_decade"]
fig, ax = plt.subplots(figsize=(10, 4.8), facecolor=BG); ax.set_facecolor(BG)
ax.bar([d for d, n in D], [n for d, n in D], width=9, color=COOL)
ax.set_xlim(750, 2000); ax.spines[["top", "right"]].set_visible(False); ax.set_ylabel("Houses dissolved or abandoned, per decade")
ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
W_ = R["dissolution"]["waves"]
notes = [(1532, 715, 1110, 640, f"Reformation: {fmt(W_['dissolution_ew'])} in\nEngland and Wales,\n1536 to 1541"),
         (1805, 446, 1640, 690, f"Secularisation:\n{fmt(W_['german_1802_1811'])} in the German\nlands, 1802 to 1811"),
         (1795, 307, 1620, 540, f"French Revolution:\n{fmt(W_['france_rev'])} in France,\n1789 to 1795"),
         (930, 4, 830, 230, f"The Viking age, 793 to 1066:\n{W_['viking_all']} in all, none on islands")]
for x, y, tx, ty, t in notes:
    ax.annotate(t, (x, y), xytext=(tx, ty), fontsize=9, color=FG, ha="left", va="top", linespacing=1.35,
                arrowprops=dict(arrowstyle="-", color=MUT, lw=.7, shrinkA=2, shrinkB=2))
ax.set_ylim(0, 780)
ax.set_title("When monastic houses were dissolved or abandoned, by decade", loc="left", fontproperties=DISPB, fontsize=15, color=FG, pad=10)
fig.text(.01, .01, f"{fmt(R['dissolution']['n'])} of {fmt(R['coverage']['n'])} houses have a Wikidata date of dissolution or abandonment (P576).", fontsize=8.5, color=MUT)
fig.tight_layout(rect=(0, .03, 1, 1)); both(fig, "dissolution")

# ---------- 8. Coverage ----------
T = R["coverage"]["top"][:15]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5.6), facecolor=BG, gridspec_kw={"width_ratios": [1.15, 1]})
for a in (a1, a2):
    a.set_facecolor(BG); a.spines[["top", "right"]].set_visible(False); a.grid(axis="x", color=RULE, lw=.8); a.set_axisbelow(True)
a1.barh(range(len(T))[::-1], [t["n"] for t in T], color="#7B8790")
for i, t in enumerate(T):
    a1.text(t["n"] + 60, len(T) - 1 - i, f"{t['pct']:.1f}%", va="center", fontsize=8.8)
a1.set_yticks(range(len(T))[::-1]); a1.set_yticklabels([t["name"] for t in T], fontsize=9.5); a1.set_xlabel("Monastic houses in Wikidata")
a1.set_xlim(0, T[0]["n"] * 1.18)
a1.set_title("Houses by country", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
reg = sorted(R["regions"], key=lambda d: d["dated_pct"])
a2.barh(range(len(reg)), [d["dated_pct"] for d in reg], color=GOLD)
for i, d in enumerate(reg):
    a2.text(d["dated_pct"] + 1, i, f"{d['dated_pct']:.0f}% of {fmt(d['n'])}", va="center", fontsize=8.8)
a2.set_yticks(range(len(reg))); a2.set_yticklabels([d["name"].replace(" and the Low Countries", "").replace(", Man and the Channel Islands", ", Man, Channel Is.") for d in reg], fontsize=9)
a2.set_xlim(0, 100); a2.set_xlabel("Share with a foundation date (%)")
a2.set_title("How many are dated", loc="left", fontproperties=DISPB, fontsize=13, color=FG)
fig.tight_layout(); both(fig, "coverage")

# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.40, -.02, .62, 1.04]); ax.set_facecolor(BG)
draw_land(ax); scatter_houses(ax, smain=.5, sisl=16, alpha_main=.5); frame(ax, ext_ll(-14, 34, 33, 66))
fig.text(.045, .80, "Holy", fontproperties=DISP, fontsize=82, color=FG, va="center")
fig.text(.045, .62, "islands", fontproperties=DISP, fontsize=82, color=HOT, va="center")
fig.text(.047, .44, f"{fmt(R['coverage']['n'])} monasteries, abbeys and\nhermitages in Europe; {fmt(R['islands']['n'])} on islands.\nWhere, when and how far out to sea.",
         fontproperties=SERP, fontsize=17, color=FG, va="top", linespacing=1.6)
kax = fig.add_axes([0, 0, 1, 1]); kax.set_xlim(0, 1); kax.set_ylim(0, 1); kax.axis("off"); kax.patch.set_alpha(0)
for j, k in enumerate(("small", "island", "lake")):
    kax.scatter(.053 + j * .135, .145, s=90, color=CLS_C[k])
    fig.text(.066 + j * .135, .145, {"small": "small island", "island": "sea island", "lake": "lake island"}[k], color=CLS_C[k], family=MONO, fontsize=11.5, va="center")
fig.text(.047, .055, f"maps.tristanhotham.com/{SLUG}", family=MONO, fontsize=12, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
print("figures ok")
