"""Shared paths and helpers for the holy-islands project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw2/monasteries.tsv
      Wikidata via QLever (CC0): every item that is an instance of a subclass of monastery (Q44613), hermitage (Q513550),
      abbey (Q160742), priory (Q2750108) or clochan (Q1175763) and has coordinates. Columns ?m ?l ?coord ?inc ?dis
      ?country ?type ?rel ?sl; one row per combination of values, so items repeat.
  /home/claude/newdata/raw2/dl/2a0b4d88993ad1bf63f402fc4d1bf5e9.txt   English labels of the four root classes
  /home/claude/newdata/raw/arch/arch_countries.tsv     Wikidata country items with English label and ISO 3166-1 alpha-3
  /home/claude/newdata/raw/arch/arch_typelabels.tsv    English labels of Wikidata classes (used for monastery types)
  /home/claude/newdata/raw2/coast/gshhs_f.dat, gshhsmeta_f.dat
      GSHHG full-resolution shorelines (Wessel and Smith; LGPL-3.0), as packaged in the basemap-data-hires 2.0.0
      Python package (pip), copied here. Binary little-endian float32 lon/lat pairs; the meta file lists, per polygon:
      level (1 land, 2 lake, 3 island in lake, 4 pond in island), area km2, points, south, north, byte offset, bytes, id.
  /home/claude/newdata/raw/geo/ne_10m_admin_1_states_provinces.geojson   Natural Earth (public domain), for regions
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson          Natural Earth, outlines and country fallback
  /home/claude/newdata/raw/geo/ne_10m_populated_places_simple.geojson    Natural Earth, place names for the page
All Wikidata files were retrieved through QLever in 2026.
"""
import json, gzip, math, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("HOLY_RAW", "/home/claude/newdata/raw2")
ARCH = os.environ.get("HOLY_ARCH", "/home/claude/newdata/raw/arch")
GEO = os.environ.get("HOLY_GEO", "/home/claude/newdata/raw/geo")
COAST = os.path.join(RAW, "coast")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("HOLYTMP", "/dev/shm/holy"), "work")   # intermediates live in memory, not in the repo
FONTS = os.environ.get("HOLY_FONTS", "/home/claude/ref/fonts")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "holy-islands"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "{{DOI}}"             # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/holy-islands/"       # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
WD = "http://www.wikidata.org/entity/"

# Study area: Europe in the wide sense, with Iceland, the Faroes, Macaronesia and Cyprus, west of the Urals.
BBOX = (-32.0, 27.0, 60.0, 82.0)
SMALL_KM2 = 25        # 'small island': the holy-island archetype (Iona 9 km2, Lindisfarne 4, Bardsey 2, Skellig Michael under 1)
ISLAND_KM2 = 1000     # islands under this are 'islands'; larger land (continents, Great Britain, Ireland, Iceland, Sicily...) is 'mainland'
SNAP_KM = 1.5         # a point in the sea within this distance of land is put on that land
PERIODS = [("p1", "Before 800", -9999, 799), ("p2", "800 to 1099", 800, 1099), ("p3", "1100 to 1299", 1100, 1299),
           ("p4", "1300 and later", 1300, 9999)]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from Wikidata (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def val(v):
    """Plain value from a QLever TSV cell: entity IRI to QID, literal to text, blank node to ''."""
    v = v.strip()
    if v.startswith("<" + WD):
        return v[len(WD) + 1:-1]
    if v.startswith("<http://www.wikidata.org/.well-known/genid/"):
        return ""
    if v.startswith("<") and v.endswith(">"):
        return v[1:-1]
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^<[^>]+>)?$', v, re.S)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\").replace("\\t", " ").replace("\\n", " ")
    return v


def tsv(path):
    out = []
    with open(path, encoding="utf-8") as f:
        head = [h.lstrip("?") for h in f.readline().rstrip("\n").split("\t")]
        for ln in f:
            parts = ln.rstrip("\n").split("\t")
            parts += [""] * (len(head) - len(parts))
            out.append({h: val(x) for h, x in zip(head, parts)})
    return out


def date_of(v):
    """(year, month-day) from an xsd:dateTime string (BCE negative); None if unparseable."""
    m = re.match(r"^(-?)(\d{1,6})-(\d\d-\d\d)T", v or "")
    if not m:
        return None
    y = int(m.group(2))
    return (-y if m.group(1) else y), m.group(3)


def rnd(v):
    """Round half up (so 32.5 shows as 33 everywhere, as in the page's JavaScript)."""
    return int(math.floor(float(v) + 0.5))


def haversine(lon1, lat1, lon2, lat2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def period_of(y):
    if y is None:
        return None
    for k, lab, a, b in PERIODS:
        if a <= y <= b:
            return k
    return None


def century_label(c):
    return f"{c}s" if c >= 0 else f"{-c}s BCE"
