"""README.md, LICENSE and reddit/post.md, numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
c, i, cv, d, f = R["compare"], R["islands"], R["coverage"], R["dissolution"], R["far"]
size = lambda fn: f"{os.path.getsize(os.path.join(DATA, fn)) / 1e6:.1f} MB"
readme = f"""# Holy islands

Monks, hermits and the edge of the world: which of Europe's monasteries, abbeys, priories, convents, friaries and hermitages stand on islands, when they were founded, how far they lie from the mainland and when they were dissolved. Every such house in Wikidata with coordinates in Europe ({cv['n']:,}) was placed on the GSHHG full-resolution shoreline.

Interactive page: {PAGE}
Paper: https://doi.org/{{{{DOI}}}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/holy-islands/}}

## Headline results

- {i['n']} of {cv['n']:,} houses ({i['pct']:.1f}%) stand on islands under 1,000 km²: {i['sea_n']} at sea ({i['small_n']} on small islands under 25 km²) and {i['lake_n']} in lakes and rivers. Great Britain, Ireland and bigger islands count as mainland; counting them as islands gives {i['any_pct']:.1f}%.
- Early foundations went to sea: {c['all_pre800']['isl']} of {c['all_pre800']['n']} houses dated before 800 ({c['all_pre800']['pct']:.1f}%) are on islands, against {c['all_p3']['pct']:.1f}% for 1100 to 1299 and {c['all_p4']['pct']:.1f}% after 1300. On the Atlantic Celtic edge (Ireland, Scotland, Wales, Brittany, Galicia), {c['early_atl']['isl']} of {c['early_atl']['n']} houses dated before 1100 ({c['early_atl']['pct']:.1f}%, 95% interval {c['early_atl']['lo']} to {c['early_atl']['hi']}%), against {c['late_cont']['isl']} of {c['late_cont']['n']:,} ({c['late_cont']['pct']:.1f}%) founded in France and Central Europe from 1100.
- By region (all houses): Wales {R['regions'][2]['pct']:.1f}%, Scotland {R['regions'][1]['pct']:.1f}%, the Mediterranean {R['regions'][11]['pct']:.1f}% ({R['regions'][11]['isl']} houses, the most of any region, mostly on Greek and Turkish islands), Ireland {R['regions'][0]['pct']:.1f}%; France and Central Europe {c['cont_all']['pct']:.1f}%.
- Furthest from the mainland: the convents of the Azores, up to {f['top'][0]['d']:,.0f} km out; Skellig Michael is {f['skellig']['d']:.1f} km offshore and Iona {f['iona']['d']:.1f} km.
- Dissolution: {d['n']:,} houses have a date; {d['waves']['dissolution_ew']} fall in England and Wales in 1536 to 1541, {d['waves']['france_rev']} in France in 1789 to 1795 and {d['waves']['german_1802_1811']} in the German lands in 1802 to 1811. Only {d['waves']['viking_all']} are dated 793 to 1066, none on islands.
- Coverage: only {cv['dated_pct']:.0f}% of houses have a foundation date; Germany has {cv['deu_pct']:.0f}% of all houses and Iceland and the Faroes {cv['natl_n']}. This is a map of what Wikidata records.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; page data embedded, `data/points.json` and `data/islands.geojson` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/houses.csv` | All {cv['n']:,} houses: Wikidata ID, label, point, country, region, kind, classes, raw inception year, round-century flag, year used, period, dissolution year, ruin flag, setting, how it was classified, island area, distance to the mainland, big-island flag, island word in label, sitelinks ({size('houses.csv')}). |
| `data/island_houses.csv` | The {i['n']} island houses, with notes for the hand-checked ones. |
| `data/period_region.csv` | Houses and island houses by region and period, with 95% intervals. |
| `data/century.csv` | Dated houses and island houses by century of foundation. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/islands.geojson` | Outlines of the {i['n_polys']} islands with a house, simplified from GSHHG (LGPL-3.0). |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data, Natural Earth outlines and place names. |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, `overrides.py` (the hand-checked island decisions) and `qa.js`. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Houses: every Wikidata item that is an instance of a subclass of monastery (Q44613), abbey (Q160742), priory (Q2750108), hermitage (Q513550) or clochán (Q1175763) with coordinates; kept in Europe (with Iceland, the Faroes, Macaronesia, Cyprus and Turkey, west of 60 E); {R['meta']['excluded_class']} wayside shrines, lodgings, town houses and Buddhist monasteries dropped.
- Islands: points placed on GSHHG full-resolution land, lake and lake-island polygons; points in the sea within {R['meta']['snap_km']} km put on that land. Island = land under 1,000 km². {i['n_override']} houses moved onto islands missing from the shoreline after a hand check of every house named after an island (`code/overrides.py`).
- Distance: to the nearest coast of continental Europe, Africa, Great Britain or Ireland (lake islands: to the lake shore), in EPSG:3035.
- Dates: Wikidata inception; years ending 01 or 00 on 1 January are century-precision values, read as the middle of the century ({cv['rc_pct']:.0f}% of dates). The other reading is tested in the paper. Intervals are Wilson 95%.
- Caveats: very uneven coverage by country; early sites often classed as churches or archaeological sites; refoundation dates; present-day shorelines; inland islands probably undercounted.

## How to rerun

Needs Python 3 with numpy, shapely (2.x), pyproj, matplotlib and fontTools, xelatex (TeX Gyre Pagella, Inter), pdftotext, and node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`, or set `HOLY_RAW`, `HOLY_ARCH`, `HOLY_GEO`): the Wikidata TSV from QLever (retrieved in {RETRIEVED}), Natural Earth files, and the GSHHG full-resolution files `gshhs_f.dat` and `gshhsmeta_f.dat` from the `basemap-data-hires` Python package (`pip install basemap-data-hires`, then copy them from `mpl_toolkits/basemap_data/`). Intermediate files go to `/dev/shm/holy/work` (`HOLYTMP`).

```
python3 code/01_parse.py        # one record per Wikidata item, dates
python3 code/02_geo.py          # study area, countries, regions, outlines
python3 code/03_islands.py      # island classification against GSHHG (a few minutes)
python3 code/04_results.py      # all analysis, results.json, data files, page data
python3 code/05_figures.py      # header, paper and blog figures
python3 code/06_build_site.py   # index.html (and the fact checks)
python3 code/07_paper.py        # paper PDF
python3 code/09_readme.py       # README, LICENSE, reddit/post.md
python3 code/08_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
```

## Sources and licences

- Wikidata (https://www.wikidata.org/), via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- GSHHG, Global Self-consistent, Hierarchical, High-resolution Geography database (Wessel and Smith), full resolution. LGPL-3.0. The island outlines in `data/islands.geojson` are derived from it and carry the same licence.
- Natural Earth countries, provinces and populated places (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Holy islands: monks, hermits and the edge of the world. Island monasteries in Wikidata, mapped through time. Zenodo. https://doi.org/{{{{DOI}}}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
post = f"""## Title

[OC] Holy islands: before 800, {c['all_pre800']['pct']:.1f}% of Europe's dated monasteries stood on islands. After 1100, about 1%. Every monastery, abbey and hermitage in Wikidata, checked against a detailed shoreline

## Body

I took every monastery, abbey, priory, convent, friary, hermitage and clochán in Wikidata with coordinates in Europe ({cv['n']:,} of them) and put each on the GSHHG full-resolution shoreline, which includes islets as small as Skellig Michael. Islands under 1,000 km² count as islands; Great Britain, Ireland and bigger islands count as mainland. {i['n']} houses ({i['pct']:.1f}%) stand on islands: {i['sea_n']} at sea, {i['lake_n']} in lakes and rivers. Only {cv['dated_pct']:.0f}% have a foundation date, but among those, {c['all_pre800']['isl']} of {c['all_pre800']['n']} founded before 800 are on islands (Lérins, Cabrera, Bardsey, Caldey, Iona, Mont-Saint-Michel, Reichenau and others), against {c['all_p3']['pct']:.1f}% for 1100 to 1299. On the Atlantic Celtic edge it is {c['early_atl']['isl']} of {c['early_atl']['n']} before 1100, against {c['late_cont']['isl']} of {c['late_cont']['n']:,} in France and Central Europe from 1100. The furthest out are the convents of the Azores ({f['top'][0]['d']:,.0f} km); Skellig Michael is just {f['skellig']['d']:.0f} km offshore. Caveats: Wikidata is lopsided (Germany has {cv['deu_pct']:.0f}% of the houses, Iceland and the Faroes {cv['natl_n']}), the early samples are small, and the Viking raids leave no trace in the dissolution dates. Interactive map with a century slider and an islands-only view: {PAGE}

## Source comment

Source: Wikidata (CC0), every item that is an instance of a subclass of monastery, abbey, priory, hermitage or clochán with coordinates, with inception (P571) and dissolution (P576) dates, via the QLever SPARQL engine. Islands from GSHHG full-resolution shorelines (Wessel and Smith, LGPL), with houses named after islands checked by hand; outlines from Natural Earth (public domain).

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{{{{DOI}}}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/holy-islands/}}
Data and code: {REPO}
"""
for txt in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in txt.replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog, the figures and the derived data files in
data/ are released under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/), except data/islands.geojson,
which is derived from GSHHG and released under LGPL-3.0 like its source. The
underlying Wikidata content is CC0. Natural Earth data are public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(readme.split()), "words")
