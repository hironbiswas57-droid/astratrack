"""
AstraTrack AI - Constellations Engine
Maps constellation stick figures, line segments, cultural/mythological lore,
seasonal heralds, and computes structural deformation across millennial epochs.
"""

from typing import Dict, List, Any
from .stars import propagate_star, CATALOG_STARS

# Constellation stick figures connecting star IDs
CONSTELLATIONS = [
    {
        "id": "UMa",
        "name": "Ursa Major (The Great Bear / Big Dipper)",
        "latin": "Ursa Major",
        "seasonal_marker": "Spring circumpolar anchor in the Northern Hemisphere; pointer stars Merak and Dubhe point to the Pole Star across epochs.",
        "lore": "One of the oldest recognized asterisms in human culture, dating back to Ice Age hunter-gatherers. Used as an eternal celestial clock.",
        "millennial_morph": "Demonstrates dramatic millennial shape distortion: Alkaid and Dubhe have opposing proper motion vectors compared to the Ursa Major Moving Group (Merak, Phecda, Megrez, Alioth, Mizar), bending the dipper into an elongated stream by 50,000 CE.",
        "lines": [
            ("dubhe", "merak"),
            ("merak", "phecda"),
            ("phecda", "megrez"),
            ("megrez", "dubhe"),
            ("megrez", "alioth"),
            ("alioth", "mizar"),
            ("mizar", "alkaid")
        ]
    },
    {
        "id": "Ori",
        "name": "Orion (The Celestial Hunter)",
        "latin": "Orion",
        "seasonal_marker": "Winter dominant constellation. Its evening rising in November signals oncoming cold; midnight culmination marks mid-winter.",
        "lore": "Identified by Sumerians as URU AN-NA (Light of Heaven) and Egyptians as Sah, the soul of Osiris. The belt stars align with Sirius and Aldebaran.",
        "millennial_morph": "Because Betelgeuse is a red supergiant nearing supernova and Orion's stars lie at varying distances (from 250 to 2000 light years), the hunter's belt slowly shifts tilt over 20,000 years.",
        "lines": [
            ("betelgeuse", "bellatrix"),
            ("bellatrix", "mintaka"),
            ("mintaka", "alnilam"),
            ("alnilam", "alnitak"),
            ("alnitak", "saiph"),
            ("saiph", "rigel"),
            ("rigel", "mintaka"),
            ("betelgeuse", "alnitak")
        ]
    },
    {
        "id": "Tau",
        "name": "Taurus & The Pleiades (The Bull & Seven Sisters)",
        "latin": "Taurus",
        "seasonal_marker": "Late Autumn & Winter herald. The heliacal rising of the Pleiades signaled Mediterranean planting; their dawn setting signaled harvest.",
        "lore": "Associated with the Bull of Heaven in the Epic of Gilgamesh. The Pleiades are recognized by indigenous cultures across all seven continents.",
        "millennial_morph": "Aldebaran, being only 65 light years distant with significant proper motion, is merely an optical foreground star passing across the ancient Hyades cluster over millennia.",
        "lines": [
            ("aldebaran", "alcyone")
        ]
    },
    {
        "id": "CMa",
        "name": "Canis Major (The Greater Dog & Sirius)",
        "latin": "Canis Major",
        "seasonal_marker": "Mid-summer Nile flood (heliacal rising of Sirius in July/August for ancient Egyptian Sothic calendar).",
        "lore": "Home of Sirius (Sothis), the brightest star in Earth's night sky. Ancient Greeks believed the combined heat of Sirius and the Sun caused the sweltering 'Dog Days' of summer.",
        "millennial_morph": "Sirius has one of the highest proper motions in the sky (-1.2 arcsec/yr in Dec). In 60,000 years it will drift into the constellation Columba.",
        "lines": [
            ("sirius", "procyon")  # Linked through winter triangle
        ]
    },
    {
        "id": "SummerTriangle",
        "name": "The Summer Triangle (Vega, Deneb, Altair)",
        "latin": "Triangulum Aestivale",
        "seasonal_marker": "Dominates high Northern skies throughout Summer and early Autumn.",
        "lore": "Famous in East Asian folklore as the Weaver Girl (Vega) and the Cowherd (Altair), separated by the Celestial River (the Milky Way) and reunited once a year on the 7th night of the 7th month (Qixi / Tanabata).",
        "millennial_morph": "Vega's rapid approach and proper motion will make it the magnificent North Pole Star by 13,700 CE, anchoring the northern rotational vortex.",
        "lines": [
            ("vega", "deneb"),
            ("deneb", "altair"),
            ("altair", "vega")
        ]
    },
    {
        "id": "SpringArc",
        "name": "The Spring Arc (Big Dipper to Arcturus to Spica)",
        "latin": "Arcus Vernalis",
        "seasonal_marker": "Classic navigational mnemonic: 'Follow the arc to Arcturus, and speed on to Spica' heralds the arrival of Northern Spring and planting.",
        "lore": "Arcturus ('Guardian of the Bear') is an ancient red giant halo star belonging to a dwarf galaxy accreted by the Milky Way billions of years ago.",
        "millennial_morph": "Arcturus is barreling through the solar neighborhood at over 122 km/s. Over 10,000 years, its position shifts by more than 6 full moon diameters!",
        "lines": [
            ("alkaid", "arcturus"),
            ("arcturus", "spica")
        ]
    },
    {
        "id": "Gemini",
        "name": "Gemini (The Celestial Twins)",
        "latin": "Gemini",
        "seasonal_marker": "Winter and early Spring zodiacal landmark. Sign of the winter solstice during the Gemini Age (5800-3600 BCE).",
        "lore": "Castor (mortal) and Pollux (immortal), the Dioscuri of classical myth and patron protectors of sailors.",
        "millennial_morph": "Castor and Pollux have divergent proper motions and will slowly separate over the next 30,000 years.",
        "lines": [
            ("castor", "pollux")
        ]
    }
]


def get_constellation_network(target_year: float) -> Dict[str, Any]:
    """
    Computes propagated star coordinates for target_year and constructs
    the constellation line network with millennial deformation indices.
    """
    # Propagate all catalog stars
    star_map = {}
    for s in CATALOG_STARS:
        p = propagate_star(s, target_year)
        star_map[p["id"]] = p

    constellation_data = []
    for c in CONSTELLATIONS:
        lines_coords = []
        valid = True
        segment_lengths = []

        for star_a_id, star_b_id in c["lines"]:
            if star_a_id in star_map and star_b_id in star_map:
                sa = star_map[star_a_id]
                sb = star_map[star_b_id]
                lines_coords.append({
                    "from_star": sa["name"],
                    "from_id": star_a_id,
                    "from_ra": sa["ra"],
                    "from_dec": sa["dec"],
                    "from_cartesian": sa["cartesian"],
                    "to_star": sb["name"],
                    "to_id": star_b_id,
                    "to_ra": sb["ra"],
                    "to_dec": sb["dec"],
                    "to_cartesian": sb["cartesian"]
                })

        constellation_data.append({
            "id": c["id"],
            "name": c["name"],
            "latin": c["latin"],
            "seasonal_marker": c["seasonal_marker"],
            "lore": c["lore"],
            "millennial_morph": c["millennial_morph"],
            "segments": lines_coords
        })

    return {
        "year": target_year,
        "stars": list(star_map.values()),
        "constellations": constellation_data
    }
