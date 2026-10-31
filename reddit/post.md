## Title

[OC] Holy islands: before 800, 4.3% of Europe's dated monasteries stood on islands. After 1100, about 1%. Every monastery, abbey and hermitage in Wikidata, checked against a detailed shoreline

## Body

I took every monastery, abbey, priory, convent, friary, hermitage and clochán in Wikidata with coordinates in Europe (20,228 of them) and put each on the GSHHG full-resolution shoreline, which includes islets as small as Skellig Michael. Islands under 1,000 km² count as islands; Great Britain, Ireland and bigger islands count as mainland. 459 houses (2.3%) stand on islands: 414 at sea, 45 in lakes and rivers. Only 35% have a foundation date, but among those, 11 of 255 founded before 800 are on islands (Lérins, Cabrera, Bardsey, Caldey, Iona, Mont-Saint-Michel, Reichenau and others), against 1.1% for 1100 to 1299. On the Atlantic Celtic edge it is 3 of 28 before 1100, against 5 of 3,230 in France and Central Europe from 1100. The furthest out are the convents of the Azores (1,656 km); Skellig Michael is just 12 km offshore. Caveats: Wikidata is lopsided (Germany has 24% of the houses, Iceland and the Faroes 3), the early samples are small, and the Viking raids leave no trace in the dissolution dates. Interactive map with a century slider and an islands-only view: https://maps.tristanhotham.com/holy-islands/

## Source comment

Source: Wikidata (CC0), every item that is an instance of a subclass of monastery, abbey, priory, hermitage or clochán with coordinates, with inception (P571) and dissolution (P576) dates, via the QLever SPARQL engine. Islands from GSHHG full-resolution shorelines (Wessel and Smith, LGPL), with houses named after islands checked by hand; outlines from Natural Earth (public domain).

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/holy-islands/
Paper: https://doi.org/10.5281/zenodo.23844515
Blog post: https://blog.tristanhotham.com/2026/10/31/holy-islands/
Data and code: https://github.com/Tristan-Hotham/holy-islands
