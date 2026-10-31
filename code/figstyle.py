"""House style for static figures: fonts (static Fraunces instances cut from the variable font in /home/claude/ref/fonts,
written to WORK), the sea-and-stone palette, and Natural Earth outlines in the LAEA Europe projection (EPSG:3035)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold"), (600, "Semi")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#5E6A70", "axes.labelcolor": "#1D2A31",
                     "xtick.color": "#5E6A70", "ytick.color": "#5E6A70"})
# paper, ink, muted, land, rule, sea
BG, FG, MUT, LAND, RULE, SEA = "#F5F2EA", "#1D2A31", "#5E6A70", "#E3DDCF", "#DCD5C6", "#EEF1EE"
CLS_C = {"small": "#B8462E", "island": "#1F5E7A", "lake": "#4F8A3C", "mainland": "#A39B8C", "offshore": "#A39B8C"}
CLS_N = {"small": "Small sea island (under 25 km²)", "island": "Sea island (25 to 1,000 km²)", "lake": "Island in a lake or river",
         "mainland": "Mainland (incl. Great Britain, Ireland and islands over 1,000 km²)", "offshore": "At sea, not placed"}
HOT, COOL, GOLD = "#B8462E", "#1F5E7A", "#C49A3A"
GRP_C = {"all": FG, "atl": HOT, "cont": "#8C8574", "med": COOL, "nordic": "#6E5A8A", "east": GOLD}
LAEA = Transformer.from_crs(4326, 3035, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


def shapes(clip):
    out = []
    for f in W["features"]:
        for ring in rings(f["geometry"]):
            lo, la = ring[:, 0], ring[:, 1]
            if lo.max() < clip[0] or lo.min() > clip[2] or la.max() < clip[1] or la.min() > clip[3]:
                continue
            x, y = LAEA.transform(ring[:, 0], ring[:, 1])
            out.append((f["properties"]["iso"], np.column_stack([x, y])))
    return out


EUR = shapes((-35, 25, 65, 83))


def draw_land(ax, shp=None, fc=LAND, ec="#FFFFFF", lw=.35, z=1):
    for iso, p in (shp or EUR):
        ax.add_patch(MPoly(p, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))


def frame(ax, ext):
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def ext_ll(w, s, e, n):
    """Extent in EPSG:3035 covering a lon/lat box."""
    xs, ys = LAEA.transform([w, e, w, e, (w + e) / 2, (w + e) / 2], [s, s, n, n, s, n])
    return min(xs), max(xs), min(ys), max(ys)


EUR_EXT = (1.0e6, 6.9e6, 0.85e6, 5.6e6)
ATL_EXT = ext_ll(-11.5, 41.5, 1.5, 59.5)


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def load_points():
    P = jload(f"{DATA}/points.json")
    S = jload(f"{DATA}/site.json")
    n = len(P["x"])
    lon = np.array(P["x"]) / 1e4; lat = np.array(P["y"]) / 1e4
    x, y = LAEA.transform(lon, lat)
    cls = np.array([S["cls"][c] for c in P["cl"]])
    return P, S, x, y, cls
