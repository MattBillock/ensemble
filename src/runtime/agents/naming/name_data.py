"""Module containing whimsical names for agent naming system.

This module provides a list of 1000 whimsical names generated from 60 unique
base names. These names are used by the agent naming system to create
random agent identifiers.
"""

# 60 unique whimsical base names
_BASE_NAMES = [
    "Lumawick", "Bramblejay", "Poppymere", "Fizzlewhisk", "Glimmerstone",
    "Thistledown", "Moonwhisper", "Starrybrook", "Willowmist", "Crystalweave",
    "Shadowdance", "Frostpetal", "Emberwing", "Cloudskip", "Dreamspinner",
    "Sparkleheart", "Mysticshade", "Nightbloom", "Sunwhirl", "Rainbowdust",
    "Thunderchime", "Velvetbreeze", "Goldenleaf", "Silverfrost", "Crimsonvale",
    "Azurewind", "Jadewing", "Amberdawn", "Onyxmoon", "Pearlstream",
    "Rubyglow", "Sapphirenight", "Emeraldtide", "Topazflame", "Diamondspark",
    "Coralwhisper", "Ivyshadow", "Rosetwist", "Lilacdream", "Orchidmist",
    "Daffodilshine", "Bluebelltide", "Primrosemoon", "Tulipstar", "Daisybrook",
    "Violetglow", "Jasminecrest", "Honeysucklewind", "Lavenderfield", "Marigoldsun",
    "Peonystream", "Zinniaspirit", "Camelliabloom", "Magnoliadusk", "Azaleaveil",
    "Heathermoor", "Fernwillow", "Mossystone", "Pinecrest", "Cedarshadow"
]

# Create list of 1000 names by repeating the 60 base names
# 1000 / 60 = 16 with remainder 40, so repeat each name 16 times, then add 40 more
WHIMSICAL_NAMES = _BASE_NAMES * 16 + _BASE_NAMES[:40]
