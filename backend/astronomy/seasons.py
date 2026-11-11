"""
AstraTrack AI - Helio-Phenology & Stellar Seasonal Predictor Engine
Calculates how positions of stars and constellations predict incoming and outgoing seasons,
heliacal risings/settings, solstices, equinoxes, and agrarian/climatic cycles across millennia.
"""

import math
from typing import Dict, List, Any
from .precession import obliquity_of_ecliptic, precess_coordinates, J2000_EPOCH
from .stars import propagate_star, CATALOG_STARS

# Historical & Agrarian Seasonal Rules across cultures
SEASONAL_PROVERBS_AND_RULES = [
    {
        "star_id": "sirius",
        "phenomenon": "Heliacal Rising (Early Dawn)",
        "modern_window": "Late July - Early August",
        "culture": "Ancient Egyptian & Greco-Roman",
        "prediction": "Incoming Midsummer Heat & River Floods (The Nile Inundation / Dog Days)",
        "scientific_basis": "Sirius emerges from the Sun's glare just before dawn at azimuth ~100°. In ancient Egypt (~3000 BCE), this coincided exactly with the summer solstice and the monsoon-fed rise of the Nile."
    },
    {
        "star_id": "alcyone",
        "phenomenon": "Heliacal Rising (Late Spring)",
        "modern_window": "Late May - Early June",
        "culture": "Greco-Roman (Hesiod's Works & Days)",
        "prediction": "Incoming Summer & Grain Harvest; Safe Mediterranean Maritime Voyage",
        "scientific_basis": "Hesiod instructed: 'When the Pleiades daughters of Atlas rise, begin your harvest'. Their reappearance before sunrise marked the end of spring storms and the onset of dry summer."
    },
    {
        "star_id": "alcyone",
        "phenomenon": "Cosmical Setting (Dawn Setting)",
        "modern_window": "Early November",
        "culture": "Classical Mediterranean & Celtic (Samhain)",
        "prediction": "Incoming Winter Cold, Rain & End of Sailing Season; Winter Ploughing",
        "scientific_basis": "When the Pleiades set as the Sun rises, it signaled the arrival of winter frost, autumn leaves falling, and winter cereal planting."
    },
    {
        "star_id": "betelgeuse",
        "phenomenon": "Acronychal Rising (Dusk Rising)",
        "modern_window": "Late November - Early December",
        "culture": "Norse, Germanic & Mesopotamian",
        "prediction": "Incoming Frost, Ice, Long Nights & Deep Winter Solstice",
        "scientific_basis": "Orion's prominent belt and red shoulder rising in the East as twilight fades signals that the winter constellation will dominate the sky all night long."
    },
    {
        "star_id": "arcturus",
        "phenomenon": "Acronychal Rising (Twilight Rising)",
        "modern_window": "Late February - Early March",
        "culture": "Classical Greek & Persian",
        "prediction": "Outgoing Winter Frost; Incoming Spring Thaw & Vine Pruning",
        "scientific_basis": "Hesiod noted: 'Sixty days after the winter solstice, Arcturus leaves the ocean stream and rises at dusk; then prune your vines before the swallow arrives'."
    },
    {
        "star_id": "vega",
        "phenomenon": "Midnight Culmination (High Zenith)",
        "modern_window": "Mid July",
        "culture": "East Asian (Qixi / Tanabata Festival)",
        "prediction": "Peak Midsummer; Onset of Late Summer Monsoon / Rain Season",
        "scientific_basis": "The Summer Triangle (Vega, Altair, Deneb) overhead at midnight marks the solar zenith of the year and midsummer temperature crest."
    },
    {
        "star_id": "antares",
        "phenomenon": "Evening Culmination in the South",
        "modern_window": "July - August",
        "culture": "Ancient Chinese (Fire Star / Da Huo) & Polynesian",
        "prediction": "Peak Scorching Summer; Preparing for Autumn Harvest Transition",
        "scientific_basis": "The fiery red heart of the Scorpion culminates in the southern sky during the hottest months; its descent in September heralded the arrival of crisp autumn winds."
    }
]


def sun_ecliptic_position(day_of_year: int, year: float) -> Dict[str, Any]:
    """
    Computes the Sun's approximate equatorial coordinates (RA, Dec) and ecliptic longitude
    for a given day of the year (1-365) and target year, accounting for orbital eccentricity
    and axial tilt.
    """
    # Mean anomaly of the Sun
    m = math.radians((357.5291 + 0.98560028 * day_of_year) % 360.0)
    # Equation of center
    c = math.radians(1.9148 * math.sin(m) + 0.02 * math.sin(2.0 * m))
    # Ecliptic longitude of the Sun at J2000
    lam = math.radians((280.4665 + 0.98564736 * day_of_year) % 360.0) + c

    # Obliquity of the ecliptic for target year
    eps = obliquity_of_ecliptic(year)

    # Equatorial coordinates at current epoch
    sin_dec = math.sin(eps) * math.sin(lam)
    dec_rad = math.asin(sin_dec)

    sin_ra = math.cos(eps) * math.sin(lam)
    cos_ra = math.cos(lam)
    ra_rad = math.atan2(sin_ra, cos_ra)
    if ra_rad < 0:
        ra_rad += 2.0 * math.pi

    ra_deg = math.degrees(ra_rad)
    dec_deg = math.degrees(dec_dec_safe := max(-1.0, min(1.0, sin_dec)))
    lam_deg = math.degrees(lam) % 360.0

    # Determine astronomical season (Northern Hemisphere conventions)
    # Vernal equinox ~0° ecliptic, Summer solstice ~90°, Autumnal equinox ~180°, Winter solstice ~270°
    if 350.0 <= lam_deg or lam_deg < 80.0:
        season_name = "Spring"
        season_icon = "🌱"
        season_stage = "Vernal Ingress / Awakening Earth"
        next_season = "Summer"
    elif 80.0 <= lam_deg < 170.0:
        season_name = "Summer"
        season_icon = "☀️"
        season_stage = "Estival Climax / Ripening Sun"
        next_season = "Autumn"
    elif 170.0 <= lam_deg < 260.0:
        season_name = "Autumn"
        season_icon = "🍂"
        season_stage = "Autumnal Equinox / Harvest Dispersion"
        next_season = "Winter"
    else:
        season_name = "Winter"
        season_icon = "❄️"
        season_stage = "Hibernal Silence / Solstice Rebirth"
        next_season = "Spring"

    return {
        "day_of_year": day_of_year,
        "sun_ra": round(ra_deg, 2),
        "sun_dec": round(math.degrees(dec_rad), 2),
        "ecliptic_longitude": round(lam_deg, 2),
        "season": season_name,
        "season_icon": season_icon,
        "season_stage": season_stage,
        "next_season": next_season
    }


def predict_season_from_sky(year: float, day_of_year: int = 80, observer_lat: float = 30.0) -> Dict[str, Any]:
    """
    Analyzes star positions at target_year and day_of_year to produce predictive
    seasonal intelligence, active heliacal/acronychal alignments, and upcoming climate cues.
    """
    sun_info = sun_ecliptic_position(day_of_year, year)
    sun_ra = sun_info["sun_ra"]
    sun_dec = sun_info["sun_dec"]

    # Analyze key seasonal indicator stars
    active_predictions = []

    for rule in SEASONAL_PROVERBS_AND_RULES:
        # Find the star in catalog and propagate it
        matching_star = next((s for s in CATALOG_STARS if s["id"] == rule["star_id"]), None)
        if not matching_star:
            continue

        star_state = propagate_star(matching_star, year)
        # Angular elongation from the Sun
        # RA difference in degrees
        dra = (star_state["ra"] - sun_ra) % 360.0

        # Determine visibility status relative to the Sun:
        # If star is ~15° to 45° west of Sun (dra between 315° and 345°), it rises just before the Sun = Heliacal Rising!
        # If star is ~180° opposite Sun (dra between 165° and 195°), it culminates around midnight = Midnight Culmination!
        # If star is ~15° to 45° east of Sun (dra between 15° and 45°), it sets just after the Sun in twilight = Heliacal Setting!
        # If star is rising in the East as Sun sets in the West (dra between 160° and 200°), = Acronychal Rising!
        is_heliacal_rising = 310.0 <= dra <= 350.0
        is_midnight_culmination = 160.0 <= dra <= 200.0
        is_acronychal_rising = 165.0 <= dra <= 205.0

        status = "Inactive"
        relevance_score = 0
        if is_heliacal_rising:
            status = "ACTIVE: Heliacal Dawn Rising"
            relevance_score = 95
        elif is_acronychal_rising:
            status = "ACTIVE: Dusk Acronychal Rising"
            relevance_score = 90
        elif is_midnight_culmination:
            status = "ACTIVE: Midnight Meridian Culmination"
            relevance_score = 85

        active_predictions.append({
            "star_name": star_state["name"],
            "star_id": star_state["id"],
            "phenomenon": rule["phenomenon"],
            "culture": rule["culture"],
            "prediction": rule["prediction"],
            "scientific_basis": rule["scientific_basis"],
            "status": status,
            "relevance_score": relevance_score,
            "elongation_degrees": round(dra, 1),
            "star_ra": star_state["ra"],
            "star_dec": star_state["dec"]
        })

    # Sort predictions by active relevance
    active_predictions.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Seasonal transition index: calculates days remaining until the next astronomical solstice/equinox
    lam = sun_info["ecliptic_longitude"]
    # Distance to next quadrant (0°, 90°, 180°, 270°)
    next_quadrant = (math.floor(lam / 90.0) + 1) * 90.0
    deg_to_transition = (next_quadrant - lam) % 360.0
    days_to_transition = round(deg_to_transition / 0.9856)

    return {
        "year": year,
        "day_of_year": day_of_year,
        "solar_telemetry": sun_info,
        "current_season": sun_info["season"],
        "season_stage": sun_info["season_stage"],
        "days_until_next_transition": days_to_transition,
        "next_season": sun_info["next_season"],
        "stellar_predictions": active_predictions,
        "summary": f"At epoch {int(year)}, day {day_of_year}, the Sun is in {sun_info['season']} ({sun_info['season_stage']}). Stellar positions herald an incoming shift towards {sun_info['next_season']} in approximately {days_to_transition} days."
    }
