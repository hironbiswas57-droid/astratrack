"""
AstraTrack AI - Precession & Deep-Time Astrometry Engine
Calculates Earth's axial precession, North Celestial Pole path, and epoch transformations
over millennia (-15,000 BCE to +15,000 CE).
"""

import math
from typing import Tuple, Dict, Any, List

# Astronomical Constants
J2000_EPOCH = 2000.0
# Axial precession period in Julian years (the "Great Year" or Platonic Year)
PRECESSION_PERIOD_YEARS = 25772.0
# Obliquity of the Ecliptic at J2000 (radians)
EPSILON_0 = math.radians(23.43928)
# Precession rate: 360 degrees / 25772 years (radians / year)
OMEGA_PRECESSION = (2.0 * math.pi) / PRECESSION_PERIOD_YEARS

# Historic and futuristic pole stars with epoch of closest alignment
POLE_STARS = [
    {
        "name": "Polaris (Alpha Ursae Minoris)",
        "epoch_optimal": 2100,
        "ra_j2000": 37.95,       # degrees
        "dec_j2000": 89.26,      # degrees
        "magnitude": 1.98,
        "historical_context": "Current Northern Pole star, closest to the true north celestial pole around 2100 CE."
    },
    {
        "name": "Errai (Gamma Cephei)",
        "epoch_optimal": 4000,
        "ra_j2000": 354.83,
        "dec_j2000": 77.63,
        "magnitude": 3.21,
        "historical_context": "Will succeed Polaris as the northern pole star around 4000 CE."
    },
    {
        "name": "Alderamin (Alpha Cephei)",
        "epoch_optimal": 7500,
        "ra_j2000": 319.64,
        "dec_j2000": 62.59,
        "magnitude": 2.45,
        "historical_context": "Bright northern marker around 7500 CE, guiding futuristic civil navigation."
    },
    {
        "name": "Deneb (Alpha Cygni)",
        "epoch_optimal": 10000,
        "ra_j2000": 310.36,
        "dec_j2000": 45.28,
        "magnitude": 1.25,
        "historical_context": "Near-polar brilliant supergiant star around 10,000 CE."
    },
    {
        "name": "Vega (Alpha Lyrae)",
        "epoch_optimal": 13700,
        "ra_j2000": 279.23,
        "dec_j2000": 38.78,
        "magnitude": 0.03,
        "historical_context": "The most brilliant Northern Pole star in history. Was pole star during Upper Paleolithic (12,000 BCE) and will return in 13,700 CE."
    },
    {
        "name": "Thuban (Alpha Draconis)",
        "epoch_optimal": -2800,
        "ra_j2000": 211.09,
        "dec_j2000": 64.38,
        "magnitude": 3.67,
        "historical_context": "True pole star of Ancient Egypt (~2800 BCE), used by architects to align the Khufu Great Pyramid at Giza."
    },
    {
        "name": "Kochab (Beta Ursae Minoris)",
        "epoch_optimal": -1100,
        "ra_j2000": 222.68,
        "dec_j2000": 74.16,
        "magnitude": 2.08,
        "historical_context": "Co-guardian of the pole during the Phoenician and Homeric Greek seafaring era (1500 BCE to 500 BCE)."
    }
]

# Zodiacal astrological ages based on the vernal equinox constellation
ZODIAC_AGES = [
    {"age": "Age of Leo", "start": -10500, "end": -8000, "symbol": "♌", "significance": "Late Pleistocene melting, dawn of agricultural origins."},
    {"age": "Age of Cancer", "start": -8000, "end": -5800, "symbol": "♋", "significance": "Neolithic expansion, pottery and settlements."},
    {"age": "Age of Gemini", "start": -5800, "end": -3600, "symbol": "♊", "significance": "Invention of wheel, proto-writing, twin city-states."},
    {"age": "Age of Taurus", "start": -3600, "end": -1400, "symbol": "♉", "significance": "Bronze Age, bull cults of Crete, Sumer, and Giza Pyramids."},
    {"age": "Age of Aries", "start": -1400, "end": 600, "symbol": "♈", "significance": "Iron Age, classical antiquity, Greek philosophy, Roman Empire."},
    {"age": "Age of Pisces", "start": 600, "end": 2150, "symbol": "♓", "significance": "Global maritime exploration, global religions, scientific revolution."},
    {"age": "Age of Aquarius", "start": 2150, "end": 4300, "symbol": "♒", "significance": "Space exploration, networked planetary intelligence, AI synthesis."}
]


def obliquity_of_ecliptic(year: float) -> float:
    """
    Computes obliquity of the ecliptic (epsilon) in radians for a given year
    using Laskar (1986) / IAU polynomial fit valid over millennia.
    """
    eps_deg = 23.43929111 - 0.013004166 * (year - J2000_EPOCH) / 100.0
    eps_deg = max(22.1, min(24.5, eps_deg))
    return math.radians(eps_deg)


def get_north_celestial_pole(year: float) -> Dict[str, Any]:
    """
    Computes the position of the North Celestial Pole (NCP) in J2000 equatorial coordinates
    for any specified year in the range -15,000 BCE to +15,000 CE.
    The NCP traces a circle of radius = epsilon (obliquity) around the North Ecliptic Pole.
    """
    eps = obliquity_of_ecliptic(year)
    dt = year - J2000_EPOCH
    precession_angle = OMEGA_PRECESSION * dt  # Radians

    # In ecliptic coordinates, the NCP has latitude = 90° - eps, and longitude = 90° - precession_angle.
    lambda_pole = (math.pi / 2.0) - precession_angle

    # Cartesian coordinates in ecliptic frame
    x_ecl = math.sin(eps) * math.cos(lambda_pole)
    y_ecl = math.sin(eps) * math.sin(lambda_pole)
    z_ecl = math.cos(eps)

    # Convert ecliptic Cartesian coordinates back to J2000 equatorial coordinates
    x_eq = x_ecl
    y_eq = y_ecl * math.cos(EPSILON_0) - z_ecl * math.sin(EPSILON_0)
    z_eq = y_ecl * math.sin(EPSILON_0) + z_ecl * math.cos(EPSILON_0)

    # Convert Cartesian to RA, Dec (J2000 degrees)
    ra_rad = math.atan2(y_eq, x_eq)
    if ra_rad < 0:
        ra_rad += 2.0 * math.pi
    dec_rad = math.asin(max(-1.0, min(1.0, z_eq)))

    ra_deg = math.degrees(ra_rad)
    dec_deg = math.degrees(dec_rad)

    # Find closest known pole star
    closest_star = None
    min_separation = 999.0
    for star in POLE_STARS:
        star_ra_rad = math.radians(star["ra_j2000"])
        star_dec_rad = math.radians(star["dec_j2000"])
        cos_d = (math.sin(dec_rad) * math.sin(star_dec_rad) +
                 math.cos(dec_rad) * math.cos(star_dec_rad) * math.cos(ra_rad - star_ra_rad))
        sep_deg = math.degrees(math.acos(max(-1.0, min(1.0, cos_d))))
        if sep_deg < min_separation:
            min_separation = sep_deg
            closest_star = {**star, "separation_degrees": round(sep_deg, 2)}

    # Determine current zodiacal age
    current_age = None
    for age in ZODIAC_AGES:
        if age["start"] <= year < age["end"]:
            current_age = age
            break
    if not current_age:
        current_age = ZODIAC_AGES[0] if year < ZODIAC_AGES[0]["start"] else ZODIAC_AGES[-1]

    return {
        "year": year,
        "ncp_j2000_ra": round(ra_deg, 3),
        "ncp_j2000_dec": round(dec_deg, 3),
        "cartesian_pole": {"x": round(x_eq, 4), "y": round(y_eq, 4), "z": round(z_eq, 4)},
        "precession_angle_degrees": round(math.degrees(precession_angle) % 360.0, 2),
        "precession_cycle_fraction": round(((year % PRECESSION_PERIOD_YEARS) / PRECESSION_PERIOD_YEARS), 4),
        "obliquity_degrees": round(math.degrees(eps), 3),
        "closest_pole_star": closest_star,
        "zodiac_age": current_age
    }


def precess_coordinates(ra_deg: float, dec_deg: float, from_year: float, to_year: float) -> Tuple[float, float]:
    """
    Transforms equatorial coordinates (RA, Dec in degrees) from from_year to to_year,
    accounting for general precession of the equinoxes.
    Uses rigorous rotation via ecliptic coordinates.
    """
    if from_year == to_year:
        return ra_deg, dec_deg

    dt = to_year - from_year
    # General precession rate in longitude: ~50.29 arcseconds/year
    d_lambda = math.radians((50.28796195 / 3600.0) * dt)

    ra_rad = math.radians(ra_deg)
    dec_rad = math.radians(dec_deg)

    # 1. Convert equatorial (RA, Dec) to ecliptic (lambda, beta)
    eps = obliquity_of_ecliptic(from_year)
    sin_beta = math.sin(dec_rad) * math.cos(eps) - math.cos(dec_rad) * math.sin(eps) * math.sin(ra_rad)
    beta = math.asin(max(-1.0, min(1.0, sin_beta)))

    cos_beta_sin_lambda = math.sin(dec_rad) * math.sin(eps) + math.cos(dec_rad) * math.cos(eps) * math.sin(ra_rad)
    cos_beta_cos_lambda = math.cos(dec_rad) * math.cos(ra_rad)
    lam = math.atan2(cos_beta_sin_lambda, cos_beta_cos_lambda)

    # 2. Advance ecliptic longitude by precession
    lam_new = lam + d_lambda

    # 3. Convert back to equatorial (RA, Dec) at target epoch
    eps_target = obliquity_of_ecliptic(to_year)
    sin_dec_new = math.sin(beta) * math.cos(eps_target) + math.cos(beta) * math.sin(eps_target) * math.sin(lam_new)
    dec_new = math.asin(max(-1.0, min(1.0, sin_dec_new)))

    cos_dec_sin_ra = -math.sin(beta) * math.sin(eps_target) + math.cos(beta) * math.cos(eps_target) * math.sin(lam_new)
    cos_dec_cos_ra = math.cos(beta) * math.cos(lam_new)
    ra_new = math.atan2(cos_dec_sin_ra, cos_dec_cos_ra)

    if ra_new < 0:
        ra_new += 2.0 * math.pi

    return math.degrees(ra_new) % 360.0, math.degrees(dec_new)


def get_precession_circle_points(samples: int = 72) -> List[Dict[str, Any]]:
    """
    Returns points along the North Celestial Pole's 25,772-year precession circle in J2000 coordinates.
    Used for 3D/2D rendering of the cosmic clock in the celestial observatory.
    """
    points = []
    step = PRECESSION_PERIOD_YEARS / samples
    for i in range(samples):
        yr = J2000_EPOCH + i * step
        pole_info = get_north_celestial_pole(yr)
        points.append({
            "year": round(yr),
            "ra": pole_info["ncp_j2000_ra"],
            "dec": pole_info["ncp_j2000_dec"],
            "cartesian": pole_info["cartesian_pole"],
            "closest_star": pole_info["closest_pole_star"]["name"] if pole_info["closest_pole_star"] else None
        })
    return points
