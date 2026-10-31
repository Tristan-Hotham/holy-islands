"""Hand-checked corrections to the shoreline classification.

The GSHHG shorelines miss many small islands in lakes and rivers, and a few sea islets. Every item whose English label
names an island (Island, Isle, Inis, Inish, Inch, Ynys, Eilean, Ile, Insel and so on) and that the shorelines put on
the mainland was checked by hand against its name and position; so were the points that fell in the open sea.
Classes: 'small' sea island under 25 km2, 'lake' island in a lake or river.
Items whose names merely contain a place name with 'isle' in it (L'Isle, L'Ile-Bouchard), or that stood on islands
in marsh or lake that are now joined to the land, are left on the mainland: this study classifies by present-day
geography, as the shoreline data do.
"""
OVERRIDE = {
    "Q908451": ("lake", "Margaret Island, an island in the Danube at Budapest"),
    "Q1000452": ("lake", "Margaret Island, an island in the Danube at Budapest"),
    "Q1912023": ("lake", "Inchmahome, an island in the Lake of Menteith"),
    "Q7595460": ("lake", "St Serf's Inch, an island in Loch Leven"),
    "Q16892680": ("lake", "Inishmacsaint, an island in Lower Lough Erne"),
    "Q19324488": ("lake", "Ile Barbe, an island in the Saone at Lyon"),
    "Q28232520": ("lake", "Inchmacnerin (Church Island), an island in Lough Key"),
    "Q30161235": ("lake", "Inis Cealtra (Holy Island), an island in Lough Derg"),
    "Q30247115": ("small", "Church Island, an islet in Valentia Harbour"),
    "Q30247116": ("lake", "Church Island, an islet in Lough Currane"),
    "Q30247341": ("lake", "Inchagoill, an island in Lough Corrib"),
    "Q31101291": ("lake", "Inchcleraun, an island in Lough Ree"),
    "Q116486099": ("lake", "Inchbofin, an island in Lough Ree"),
    "Q122311042": ("lake", "the island in Lake Pamvotida at Ioannina"),
    "Q131523709": ("lake", "an island in a lake in Anatolia, named as an island in its label"),
    "Q131523730": ("lake", "an island in Lake Bafa, named as an island in its label"),
    "Q135599089": ("lake", "Trinity Island, an island in Lough Oughter"),
    "Q4334862": ("small", "Kiy Island in the White Sea, an islet missing from the shoreline data"),
}
