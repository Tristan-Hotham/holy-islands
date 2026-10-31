# Holy islands

Monks, hermits and the edge of the world: which of Europe's monasteries, abbeys, priories, convents, friaries and hermitages stand on islands, when they were founded, how far they lie from the mainland and when they were dissolved. Every such house in Wikidata with coordinates in Europe (20,228) was placed on the GSHHG full-resolution shoreline.

Interactive page: https://maps.tristanhotham.com/holy-islands/
Paper: https://doi.org/10.5281/zenodo.23844515
Blog post: https://blog.tristanhotham.com/2026/10/31/holy-islands/

## Headline results

- 459 of 20,228 houses (2.3%) stand on islands under 1,000 km²: 414 at sea (107 on small islands under 25 km²) and 45 in lakes and rivers. Great Britain, Ireland and bigger islands count as mainland; counting them as islands gives 4.4%.
- Early foundations went to sea: 11 of 255 houses dated before 800 (4.3%) are on islands, against 1.1% for 1100 to 1299 and 1.2% after 1300. On the Atlantic Celtic edge (Ireland, Scotland, Wales, Brittany, Galicia), 3 of 28 houses dated before 1100 (10.7%, 95% interval 3.7 to 27.2%), against 5 of 3,230 (0.2%) founded in France and Central Europe from 1100.
- By region (all houses): Wales 13.0%, Scotland 12.4%, the Mediterranean 7.7% (304 houses, the most of any region, mostly on Greek and Turkish islands), Ireland 7.5%; France and Central Europe 0.3%.
- Furthest from the mainland: the convents of the Azores, up to 1,656 km out; Skellig Michael is 12.3 km offshore and Iona 38.1 km.
- Dissolution: 2,944 houses have a date; 614 fall in England and Wales in 1536 to 1541, 245 in France in 1789 to 1795 and 492 in the German lands in 1802 to 1811. Only 18 are dated 793 to 1066, none on islands.
- Coverage: only 35% of houses have a foundation date; Germany has 24% of all houses and Iceland and the Faroes 3. This is a map of what Wikidata records.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; page data embedded, `data/points.json` and `data/islands.geojson` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/houses.csv` | All 20,228 houses: Wikidata ID, label, point, country, region, kind, classes, raw inception year, round-century flag, year used, period, dissolution year, ruin flag, setting, how it was classified, island area, distance to the mainland, big-island flag, island word in label, sitelinks (2.9 MB). |
| `data/island_houses.csv` | The 459 island houses, with notes for the hand-checked ones. |
| `data/period_region.csv` | Houses and island houses by region and period, with 95% intervals. |
| `data/century.csv` | Dated houses and island houses by century of foundation. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/islands.geojson` | Outlines of the 178 islands with a house, simplified from GSHHG (LGPL-3.0). |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data, Natural Earth outlines and place names. |
| `code/` | Scripts, run in order (below), the page, paper and blog templates, `overrides.py` (the hand-checked island decisions) and `qa.js`. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Houses: every Wikidata item that is an instance of a subclass of monastery (Q44613), abbey (Q160742), priory (Q2750108), hermitage (Q513550) or clochán (Q1175763) with coordinates; kept in Europe (with Iceland, the Faroes, Macaronesia, Cyprus and Turkey, west of 60 E); 136 wayside shrines, lodgings, town houses and Buddhist monasteries dropped.
- Islands: points placed on GSHHG full-resolution land, lake and lake-island polygons; points in the sea within 1.5 km put on that land. Island = land under 1,000 km². 18 houses moved onto islands missing from the shoreline after a hand check of every house named after an island (`code/overrides.py`).
- Distance: to the nearest coast of continental Europe, Africa, Great Britain or Ireland (lake islands: to the lake shore), in EPSG:3035.
- Dates: Wikidata inception; years ending 01 or 00 on 1 January are century-precision values, read as the middle of the century (28% of dates). The other reading is tested in the paper. Intervals are Wilson 95%.
- Caveats: very uneven coverage by country; early sites often classed as churches or archaeological sites; refoundation dates; present-day shorelines; inland islands probably undercounted.

## How to rerun

Needs Python 3 with numpy, shapely (2.x), pyproj, matplotlib and fontTools, xelatex (TeX Gyre Pagella, Inter), pdftotext, and node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`, or set `HOLY_RAW`, `HOLY_ARCH`, `HOLY_GEO`): the Wikidata TSV from QLever (retrieved in 2026), Natural Earth files, and the GSHHG full-resolution files `gshhs_f.dat` and `gshhsmeta_f.dat` from the `basemap-data-hires` Python package (`pip install basemap-data-hires`, then copy them from `mpl_toolkits/basemap_data/`). Intermediate files go to `/dev/shm/holy/work` (`HOLYTMP`).

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

Hotham, T. (2026) Holy islands: monks, hermits and the edge of the world. Island monasteries in Wikidata, mapped through time. Zenodo. https://doi.org/10.5281/zenodo.23844515

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
