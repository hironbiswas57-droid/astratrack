"""
AstraTrack AI - Stellar Catalog & Proper Motion Engine
Calculates true positions of stars factoring in both individual proper motion
vectors over millennia and axial precession of the coordinate frame.
"""

import math
from typing import Dict, List, Any
from .precession import precess_coordinates, J2000_EPOCH

# Star spectral colors for realistic rendering
SPECTRAL_COLORS = {
    "O": "#9bb0ff",
    "B": "#bbccff",
    "A": "#f8f9ff",
    "F": "#ffffed",
    "G": "#fff4e8",
    "K": "#ffd2a1",
    "M": "#ff9a66"
}

# Key stars with Hipparcos/Gaia catalog astrometric values
# pm_ra: proper motion in RA * cos(dec) [mas/yr]
# pm_dec: proper motion in Dec [mas/yr]
# distance_ly: distance in light years
CATALOG_STARS = [
    # Ursa Major (Big Dipper) - Demonstrates striking proper motion deformation across millennia
    {"id": "dubhe", "name": "Dubhe (Alpha UMa)", "constellation": "UMa", "ra": 165.93, "dec": 61.75, "mag": 1.79, "spect": "K", "pm_ra": -136.4, "pm_dec": -35.2, "dist_ly": 123},
    {"id": "merak", "name": "Merak (Beta UMa)", "constellation": "UMa", "ra": 165.46, "dec": 56.38, "mag": 2.37, "spect": "A", "pm_ra": 81.3, "pm_dec": 33.3, "dist_ly": 79.7},
    {"id": "phecda", "name": "Phecda (Gamma UMa)", "constellation": "UMa", "ra": 178.46, "dec": 53.69, "mag": 2.44, "spect": "A", "pm_ra": 107.7, "pm_dec": 11.6, "dist_ly": 83.2},
    {"id": "megrez", "name": "Megrez (Delta UMa)", "constellation": "UMa", "ra": 183.86, "dec": 57.03, "mag": 3.31, "spect": "A", "pm_ra": 103.6, "pm_dec": 8.6, "dist_ly": 80.5},
    {"id": "alioth", "name": "Alioth (Epsilon UMa)", "constellation": "UMa", "ra": 193.51, "dec": 55.96, "mag": 1.77, "spect": "A", "pm_ra": 111.7, "pm_dec": -8.9, "dist_ly": 82.6},
    {"id": "mizar", "name": "Mizar (Zeta UMa)", "constellation": "UMa", "ra": 200.98, "dec": 54.92, "mag": 2.23, "spect": "A", "pm_ra": 120.2, "pm_dec": -20.2, "dist_ly": 82.9},
    {"id": "alkaid", "name": "Alkaid (Eta UMa)", "constellation": "UMa", "ra": 206.88, "dec": 49.31, "mag": 1.86, "spect": "B", "pm_ra": -121.2, "pm_dec": -15.6, "dist_ly": 103.9},

    # Orion & Neighbors (Winter Hexagon markers)
    {"id": "betelgeuse", "name": "Betelgeuse (Alpha Ori)", "constellation": "Ori", "ra": 88.79, "dec": 7.41, "mag": 0.50, "spect": "M", "pm_ra": 27.3, "pm_dec": 10.9, "dist_ly": 548},
    {"id": "rigel", "name": "Rigel (Beta Ori)", "constellation": "Ori", "ra": 78.63, "dec": -8.20, "mag": 0.13, "spect": "B", "pm_ra": 1.8, "pm_dec": -0.5, "dist_ly": 860},
    {"id": "bellatrix", "name": "Bellatrix (Gamma Ori)", "constellation": "Ori", "ra": 81.28, "dec": 6.35, "mag": 1.64, "spect": "B", "pm_ra": -8.8, "pm_dec": -13.3, "dist_ly": 250},
    {"id": "saiph", "name": "Saiph (Kappa Ori)", "constellation": "Ori", "ra": 86.94, "dec": -9.67, "mag": 2.09, "spect": "B", "pm_ra": 1.5, "pm_dec": -1.3, "dist_ly": 650},
    {"id": "alnitak", "name": "Alnitak (Zeta Ori)", "constellation": "Ori", "ra": 85.19, "dec": -1.94, "mag": 1.77, "spect": "O", "pm_ra": 3.2, "pm_dec": 1.7, "dist_ly": 1260},
    {"id": "alnilam", "name": "Alnilam (Epsilon Ori)", "constellation": "Ori", "ra": 84.05, "dec": -1.20, "mag": 1.69, "spect": "B", "pm_ra": 1.5, "pm_dec": -0.8, "dist_ly": 2000},
    {"id": "mintaka", "name": "Mintaka (Delta Ori)", "constellation": "Ori", "ra": 83.00, "dec": -0.30, "mag": 2.23, "spect": "O", "pm_ra": 0.6, "pm_dec": 0.6, "dist_ly": 1200},

    # Seasonal Indicators & Brightest Beacons
    {"id": "sirius", "name": "Sirius (Alpha CMa)", "constellation": "CMa", "ra": 101.29, "dec": -16.72, "mag": -1.46, "spect": "A", "pm_ra": -546.0, "pm_dec": -1223.1, "dist_ly": 8.6},
    {"id": "procyon", "name": "Procyon (Alpha CMi)", "constellation": "CMi", "ra": 114.83, "dec": 5.22, "mag": 0.38, "spect": "F", "pm_ra": -716.6, "pm_dec": -1034.6, "dist_ly": 11.46},
    {"id": "canopus", "name": "Canopus (Alpha Car)", "constellation": "Car", "ra": 95.99, "dec": -52.70, "mag": -0.74, "spect": "F", "pm_ra": 19.9, "pm_dec": 23.7, "dist_ly": 310},
    {"id": "arcturus", "name": "Arcturus (Alpha Boo)", "constellation": "Boo", "ra": 213.92, "dec": 19.18, "mag": -0.05, "spect": "K", "pm_ra": -1093.4, "pm_dec": -1999.4, "dist_ly": 36.7},
    {"id": "vega", "name": "Vega (Alpha Lyr)", "constellation": "Lyr", "ra": 279.23, "dec": 38.78, "mag": 0.03, "spect": "A", "pm_ra": 200.9, "pm_dec": 286.2, "dist_ly": 25.04},
    {"id": "capella", "name": "Capella (Alpha Aur)", "constellation": "Aur", "ra": 79.17, "dec": 45.99, "mag": 0.08, "spect": "G", "pm_ra": 75.5, "pm_dec": -427.1, "dist_ly": 42.9},
    {"id": "spica", "name": "Spica (Alpha Vir)", "constellation": "Vir", "ra": 201.30, "dec": -11.16, "mag": 0.97, "spect": "B", "pm_ra": -42.4, "pm_dec": -31.7, "dist_ly": 250},
    {"id": "antares", "name": "Antares (Alpha Sco)", "constellation": "Sco", "ra": 247.35, "dec": -26.43, "mag": 0.96, "spect": "M", "pm_ra": -10.2, "pm_dec": -23.2, "dist_ly": 550},
    {"id": "aldebaran", "name": "Aldebaran (Alpha Tau)", "constellation": "Tau", "ra": 68.98, "dec": 16.51, "mag": 0.85, "spect": "K", "pm_ra": 62.8, "pm_dec": -189.4, "dist_ly": 65.3},
    {"id": "pollux", "name": "Pollux (Beta Gem)", "constellation": "Gem", "ra": 116.17, "dec": 28.03, "mag": 1.14, "spect": "K", "pm_ra": -625.7, "pm_dec": -45.9, "dist_ly": 33.78},
    {"id": "castor", "name": "Castor (Alpha Gem)", "constellation": "Gem", "ra": 113.65, "dec": 31.89, "mag": 1.58, "spect": "A", "pm_ra": -206.3, "pm_dec": -148.2, "dist_ly": 51.6},
    {"id": "deneb", "name": "Deneb (Alpha Cyg)", "constellation": "Cyg", "ra": 310.36, "dec": 45.28, "mag": 1.25, "spect": "A", "pm_ra": 1.6, "pm_dec": 2.0, "dist_ly": 2615},
    {"id": "altair", "name": "Altair (Alpha Aql)", "constellation": "Aql", "ra": 297.70, "dec": 8.87, "mag": 0.77, "spect": "A", "pm_ra": 536.8, "pm_dec": 385.5, "dist_ly": 16.73},
    {"id": "fomalhaut", "name": "Fomalhaut (Alpha PsA)", "constellation": "PsA", "ra": 344.41, "dec": -29.62, "mag": 1.16, "spect": "A", "pm_ra": 329.2, "pm_dec": -164.2, "dist_ly": 25.13},
    {"id": "regulus", "name": "Regulus (Alpha Leo)", "constellation": "Leo", "ra": 152.09, "dec": 11.97, "mag": 1.35, "spect": "B", "pm_ra": -249.4, "pm_dec": 4.9, "dist_ly": 79.3},
    {"id": "achernar", "name": "Achernar (Alpha Eri)", "constellation": "Eri", "ra": 24.43, "dec": -57.24, "mag": 0.46, "spect": "B", "pm_ra": 88.0, "pm_dec": -40.1, "dist_ly": 139},
    {"id": "polaris", "name": "Polaris (Alpha UMi)", "constellation": "UMi", "ra": 37.95, "dec": 89.26, "mag": 1.98, "spect": "F", "pm_ra": 44.2, "pm_dec": -11.7, "dist_ly": 433},
    {"id": "thuban", "name": "Thuban (Alpha Dra)", "constellation": "Dra", "ra": 211.09, "dec": 64.38, "mag": 3.67, "spect": "A", "pm_ra": -58.1, "pm_dec": 19.3, "dist_ly": 303},
    {"id": "alcyone", "name": "Alcyone (Pleiades Central)", "constellation": "Tau", "ra": 56.87, "dec": 24.11, "mag": 2.87, "spect": "B", "pm_ra": 19.3, "pm_dec": -43.7, "dist_ly": 440},
    {"id": "barnard", "name": "Barnard's Star (Fastest Proper Motion)", "constellation": "Oph", "ra": 269.45, "dec": 4.69, "mag": 9.54, "spect": "M", "pm_ra": -798.6, "pm_dec": 10337.8, "dist_ly": 5.96}
]


def propagate_star(star: Dict[str, Any], target_year: float) -> Dict[str, Any]:
    """
    Propagates a star's position from J2000 to target_year, applying:
    1. Proper motion vector (mas/year translated into degrees)
    2. General precession of equinoxes
    """
    dt_years = target_year - J2000_EPOCH

    # Proper motion shift in degrees
    # pm_ra is given in mas/year for RA * cos(Dec).
    # d_ra_deg = (pm_ra / cos(dec)) * dt / (3600 * 1000)
    dec_rad = math.radians(star["dec"])
    cos_dec = max(0.01, math.cos(dec_rad))
    delta_ra_deg = (star["pm_ra"] / cos_dec) * dt_years / 3600000.0
    delta_dec_deg = star["pm_dec"] * dt_years / 3600000.0

    # Intermediate position in J2000 frame after proper motion
    ra_pm = (star["ra"] + delta_ra_deg) % 360.0
    dec_pm = max(-89.9, min(89.9, star["dec"] + delta_dec_deg))

    # Apply precession from J2000 to target_year
    ra_epoch, dec_epoch = precess_coordinates(ra_pm, dec_pm, J2000_EPOCH, target_year)

    # 3D Cartesian coordinates on celestial unit sphere for easy 3D rendering
    ra_r = math.radians(ra_epoch)
    dec_r = math.radians(dec_epoch)
    x = math.cos(dec_r) * math.cos(ra_r)
    y = math.cos(dec_r) * math.sin(ra_r)
    z = math.sin(dec_r)

    # Proper motion drift indicator in arcseconds
    total_pm_drift_arcsec = math.hypot(delta_ra_deg * math.cos(dec_rad), delta_dec_deg) * 3600.0

    return {
        "id": star["id"],
        "name": star["name"],
        "constellation": star["constellation"],
        "mag": star["mag"],
        "spect": star["spect"],
        "color": SPECTRAL_COLORS.get(star["spect"], "#ffffff"),
        "dist_ly": star["dist_ly"],
        # 1 light year = 63,241.077 AU. Keep the true scale in the API;
        # renderers may compress it for legibility, but must disclose that.
        "distance_au": round(star["dist_ly"] * 63241.077, 2),
        "position_au": {
            "x": round(x * star["dist_ly"] * 63241.077, 2),
            "y": round(y * star["dist_ly"] * 63241.077, 2),
            "z": round(z * star["dist_ly"] * 63241.077, 2),
        },
        "ra": round(ra_epoch, 3),
        "dec": round(dec_epoch, 3),
        "ra_j2000_pm": round(ra_pm, 3),
        "dec_j2000_pm": round(dec_pm, 3),
        "cartesian": {"x": round(x, 4), "y": round(y, 4), "z": round(z, 4)},
        "drift_arcsec": round(total_pm_drift_arcsec, 2),
        "proper_motion_visible": total_pm_drift_arcsec > 60.0  # Noticeable drift > 1 arcmin
    }


def get_all_propagated_stars(target_year: float) -> List[Dict[str, Any]]:
    """Returns all catalog stars propagated to target_year."""
    return [propagate_star(s, target_year) for s in CATALOG_STARS]
