"""
AstraTrack AI - Orbital Mechanics, Astral Trajectory & Satellite Sentinel Engine
Propagates Keplerian orbits for Comets and Asteroids (NEOs/PHAs), calculates close approaches
to Earth, and simulates tracking telemetry and optical/infrared sensor cones from satellite fleets.
"""

import math
from typing import Dict, List, Any, Tuple

# Physical constants
AU_TO_KM = 149597870.7  # 1 AU in km
EARTH_MOON_DIST_KM = 384400.0  # 1 Lunar Distance (LD) in km
EARTH_ORBIT_RADIUS_AU = 1.0

# 1. Tracked Astral Bodies (Comets, Potentially Hazardous Asteroids, Interstellar Interlopers)
ASTRAL_BODIES = [
    {
        "id": "apophis",
        "name": "99942 Apophis",
        "type": "Potentially Hazardous Asteroid (Aten)",
        "diameter_m": 370,
        "a": 0.9224,      # semi-major axis (AU)
        "e": 0.1912,      # eccentricity
        "i": 3.331,       # inclination (deg)
        "node": 204.05,   # longitude of ascending node (deg)
        "peri": 126.40,   # argument of perihelion (deg)
        "period_yr": 0.886,
        "color": "#ff4d4d",
        "hazard_level": "CRITICAL WATCH (Close Approach April 13, 2029 at 0.08 LD)",
        "composition": "Silicate / Stony (S-type)",
        "tracking_notes": "Monitored continuously by NEOWISE and planetary radar. In April 2029, will pass 31,600 km above Earth, inside geosynchronous satellite orbits."
    },
    {
        "id": "bennu",
        "name": "101955 Bennu",
        "type": "Near-Earth Asteroid (Apollo / Carbonaceous)",
        "diameter_m": 490,
        "a": 1.1264,
        "e": 0.2037,
        "i": 6.035,
        "node": 2.06,
        "peri": 66.22,
        "period_yr": 1.195,
        "color": "#00ffcc",
        "hazard_level": "MONITORED (Sample returned by OSIRIS-REx)",
        "composition": "Carbonaceous / Organic-rich (B-type)",
        "tracking_notes": "Sample return mission confirmed water-bearing minerals and primordial amino acid precursors. High-precision orbit tracking to year 2300."
    },
    {
        "id": "halley",
        "name": "1P/Halley",
        "type": "Periodic Comet (Halley-type)",
        "diameter_m": 11000,
        "a": 17.834,
        "e": 0.9671,
        "i": 162.26,  # Retrograde orbit
        "node": 58.42,
        "peri": 111.33,
        "period_yr": 75.32,
        "color": "#70a1ff",
        "hazard_level": "BENIGN (Next perihelion 2061)",
        "composition": "Volatile Ices (H2O, CO, CO2) & Dark Carbonaceous Dust",
        "tracking_notes": "The most celebrated comet in recorded human history. Produces the Orionid and Eta Aquariid meteor showers. Observed across millennia from 240 BCE to present."
    },
    {
        "id": "neowise_comet",
        "name": "C/2020 F3 (NEOWISE)",
        "type": "Long-Period Comet",
        "diameter_m": 5000,
        "a": 360.0,
        "e": 0.9992,
        "i": 128.94,
        "node": 61.01,
        "peri": 37.27,
        "period_yr": 6800.0,
        "color": "#a8ff78",
        "hazard_level": "OUTBOUND (Orbital period ~6,800 years)",
        "composition": "Pristine Oort Cloud Clathrates & Sodium Tail",
        "tracking_notes": "Discovered by NASA's NEOWISE infrared space telescope in March 2020. Dazzled Northern skies during July 2020 before swinging outward for seven millennia."
    },
    {
        "id": "oumuamua",
        "name": "1I/'Oumuamua",
        "type": "Interstellar Interloper",
        "diameter_m": 200,
        "a": -1.27,      # Hyperbolic orbit
        "e": 1.20,
        "i": 122.68,
        "node": 24.60,
        "peri": 241.70,
        "period_yr": 999999,
        "color": "#ffa502",
        "hazard_level": "INTERSTELLAR ESCAPE (Departing Solar System at 26 km/s)",
        "composition": "Hydrogen ice / Solid Nitrogen mantle with anomalous non-gravitational acceleration",
        "tracking_notes": "First confirmed interstellar object to visit the Solar System. Tracked departing toward constellation Pegasus by deep space tracking networks."
    },
    {
        "id": "eros",
        "name": "433 Eros",
        "type": "Near-Earth Asteroid (Amor)",
        "diameter_m": 16840,
        "a": 1.4583,
        "e": 0.2227,
        "i": 10.828,
        "node": 304.32,
        "peri": 178.82,
        "period_yr": 1.76,
        "color": "#e056fd",
        "hazard_level": "LOW RISK (First asteroid orbited and landed on by NEAR Shoemaker)",
        "composition": "Silicate / Stony-Iron (S-type)",
        "tracking_notes": "Second-largest Near-Earth asteroid known. Its elongated shape and rotation period are tracked by planetary defense observatories."
    }
]

# 2. Tracking Satellites & Space Observatories
SATELLITE_FLEET = [
    {
        "id": "neowise_sat",
        "name": "NEOWISE Space Telescope",
        "agency": "NASA / JPL",
        "orbit_type": "Sun-Synchronous Low Earth Orbit (525 km altitude)",
        "instrument": "Wide-field Cryogenic/Thermal Infrared Camera (3.4 & 4.6 micron)",
        "mission_focus": "Near-Earth Object Detection & Albedo Thermal Sizing",
        "color": "#00d2d3",
        "sensor_fov_deg": 47.0,
        "active_status": "SENTINEL ACTIVE",
        "detection_count": "Over 3,000 NEOs and 200 Comets cataloged"
    },
    {
        "id": "jwst",
        "name": "James Webb Space Telescope (JWST)",
        "agency": "NASA / ESA / CSA",
        "orbit_type": "Sun-Earth L2 Lagrange Halo Orbit (1.5 million km outward)",
        "instrument": "NIRCam & MIRI Deep Infrared Spectrographs",
        "mission_focus": "Volatile Cometary Outgassing Spectroscopy & Interstellar Body Chemical Profiling",
        "color": "#f368e0",
        "sensor_fov_deg": 18.0,
        "active_status": "FLAGSHIP ACTIVE",
        "detection_count": "Spectral signatures of CO2, water vapor, and organic tholins in comets"
    },
    {
        "id": "soho",
        "name": "SOHO (Solar & Heliospheric Observatory)",
        "agency": "ESA / NASA",
        "orbit_type": "Sun-Earth L1 Lagrange Halo Orbit (1.5 million km sunward)",
        "instrument": "LASCO C2/C3 Coronagraphs",
        "mission_focus": "Sungrazing Comet Discovery & Solar Coronal Mass Ejection Monitoring",
        "color": "#ff9f43",
        "sensor_fov_deg": 32.0,
        "active_status": "SENTINEL ACTIVE",
        "detection_count": "Over 5,000 Sungrazing Comets discovered to date"
    },
    {
        "id": "dart_sentinel",
        "name": "Planetary Defense Sentinel (DART/Hera Network)",
        "agency": "NASA / ESA",
        "orbit_type": "Heliocentric Intercept & Deep Space Planetary Defense Orbit",
        "instrument": "DRACO High-Resolution Optical Reconnaissance & Lidar Navigation",
        "mission_focus": "Kinetic Impactor Orbital Deflection & Asteroid Morphological Characterization",
        "color": "#54a0ff",
        "sensor_fov_deg": 25.0,
        "active_status": "SENTINEL ACTIVE",
        "detection_count": "Demonstrated 33-minute orbital period reduction on Dimorphos"
    }
]


def solve_kepler(m: float, e: float) -> float:
    """
    Solves Kepler's equation M = E - e * sin(E) for eccentric anomaly E using Newton-Raphson.
    """
    # Initial guess
    e_val = m if e < 0.8 else math.pi
    for _ in range(12):
        delta = e_val - e * math.sin(e_val) - m
        if abs(delta) < 1e-7:
            break
        e_val -= delta / (1.0 - e * math.cos(e_val))
    return e_val


def compute_keplerian_position(body: Dict[str, Any], time_offset_yr: float) -> Dict[str, Any]:
    """
    Computes 3D heliocentric coordinates (in AU) and velocity (in km/s)
    for a given celestial body at time_offset_yr from its perihelion.
    """
    a = body["a"]
    e = body["e"]
    i_rad = math.radians(body["i"])
    node_rad = math.radians(body["node"])
    peri_rad = math.radians(body["peri"])

    # For hyperbolic interstellar visitors like 'Oumuamua
    if e >= 1.0:
        # Hyperbolic trajectory approximation
        v_inf = 26.0  # km/s
        r_au = math.sqrt(1.0 + (v_inf * time_offset_yr * 0.21) ** 2)
        true_anom = math.radians(min(140.0, max(-140.0, time_offset_yr * 45.0)))
    else:
        # Elliptic Keplerian orbit
        period = body["period_yr"]
        mean_motion = (2.0 * math.pi) / period
        mean_anomaly = (mean_motion * time_offset_yr) % (2.0 * math.pi)

        eccentric_anomaly = solve_kepler(mean_anomaly, e)

        # True anomaly and radius
        cos_nu = (math.cos(eccentric_anomaly) - e) / (1.0 - e * math.cos(eccentric_anomaly))
        sin_nu = (math.sqrt(1.0 - e * e) * math.sin(eccentric_anomaly)) / (1.0 - e * math.cos(eccentric_anomaly))
        true_anom = math.atan2(sin_nu, cos_nu)

        r_au = a * (1.0 - e * math.cos(eccentric_anomaly))

    # Position in orbital plane
    x_orb = r_au * math.cos(true_anom)
    y_orb = r_au * math.sin(true_anom)

    # Transform to 3D heliocentric ecliptic coordinates
    # Rotate by argument of perihelion (peri), inclination (i), and node
    p_x = math.cos(node_rad) * math.cos(peri_rad) - math.sin(node_rad) * math.sin(peri_rad) * math.cos(i_rad)
    p_y = math.sin(node_rad) * math.cos(peri_rad) + math.cos(node_rad) * math.sin(peri_rad) * math.cos(i_rad)
    p_z = math.sin(peri_rad) * math.sin(i_rad)

    q_x = -math.cos(node_rad) * math.sin(peri_rad) - math.sin(node_rad) * math.cos(peri_rad) * math.cos(i_rad)
    q_y = -math.sin(node_rad) * math.sin(peri_rad) + math.cos(node_rad) * math.cos(peri_rad) * math.cos(i_rad)
    q_z = math.cos(peri_rad) * math.sin(i_rad)

    x = x_orb * p_x + y_orb * q_x
    y = x_orb * p_y + y_orb * q_y
    z = x_orb * p_z + y_orb * q_z

    # Approximate orbital velocity in km/s via vis-viva equation: v = sqrt(GM * (2/r - 1/a))
    # GM_sun = 1.327e11 km^3/s^2, 1 AU = 1.496e8 km -> sqrt(GM/AU) ~ 29.78 km/s
    if a > 0:
        speed_kms = 29.78 * math.sqrt(max(0.01, (2.0 / r_au) - (1.0 / a)))
    else:
        speed_kms = 26.0

    return {
        "x": round(x, 4),
        "y": round(y, 4),
        "z": round(z, 4),
        "distance_sun_au": round(r_au, 4),
        "speed_kms": round(speed_kms, 2)
    }


def compute_earth_position(time_offset_yr: float) -> Dict[str, float]:
    """Computes Earth's approximate heliocentric position at time_offset_yr."""
    theta = 2.0 * math.pi * (time_offset_yr % 1.0)
    return {
        "x": round(math.cos(theta), 4),
        "y": round(math.sin(theta), 4),
        "z": 0.0
    }


def generate_orbit_path(body: Dict[str, Any], samples: int = 60) -> List[Dict[str, float]]:
    """Generates 3D points outlining an object's full orbit for visual canvas trails."""
    points = []
    period = min(100.0, body["period_yr"]) if body["period_yr"] < 99999 else 20.0
    step = period / samples
    for i in range(samples + 1):
        t = (i * step) - (period / 2.0)
        pos = compute_keplerian_position(body, t)
        points.append({"x": pos["x"], "y": pos["y"], "z": pos["z"]})
    return points


def get_astral_tracking_telemetry(time_offset_yr: float = 0.0) -> Dict[str, Any]:
    """
    Computes real-time 3D positions, Earth distances (AU & Lunar Distances),
    and active tracking satellite linkages for all comets and asteroids.
    """
    earth_pos = compute_earth_position(time_offset_yr)

    tracked_results = []
    for body in ASTRAL_BODIES:
        pos = compute_keplerian_position(body, time_offset_yr)
        # Distance to Earth
        dx = pos["x"] - earth_pos["x"]
        dy = pos["y"] - earth_pos["y"]
        dz = pos["z"] - earth_pos["z"]
        dist_earth_au = math.sqrt(dx * dx + dy * dy + dz * dz)
        dist_earth_km = dist_earth_au * AU_TO_KM
        dist_earth_ld = dist_earth_km / EARTH_MOON_DIST_KM

        # Satellite lock status: Which satellites have target within active sensor range?
        assigned_satellites = []
        for sat in SATELLITE_FLEET:
            # Check optical/infrared tracking relevance
            if "NEOWISE" in sat["name"] and (dist_earth_au < 1.8 or "Apophis" in body["name"] or "NEOWISE" in body["name"]):
                assigned_satellites.append({"sat_id": sat["id"], "name": sat["name"], "mode": "Thermal IR Detection", "signal_snr_db": 28.4})
            elif "JWST" in sat["name"] and ("Halley" in body["name"] or "Bennu" in body["name"] or "Oumuamua" in body["name"]):
                assigned_satellites.append({"sat_id": sat["id"], "name": sat["name"], "mode": "Deep NIR Spectrograph", "signal_snr_db": 34.1})
            elif "SOHO" in sat["name"] and pos["distance_sun_au"] < 1.2:
                assigned_satellites.append({"sat_id": sat["id"], "name": sat["name"], "mode": "LASCO Coronagraph Watch", "signal_snr_db": 31.0})
            elif "DART" in sat["name"] and dist_earth_ld < 50.0:
                assigned_satellites.append({"sat_id": sat["id"], "name": sat["name"], "mode": "DRACO Optical Ranging", "signal_snr_db": 42.6})

        tracked_results.append({
            "id": body["id"],
            "name": body["name"],
            "type": body["type"],
            "diameter_m": body["diameter_m"],
            "color": body["color"],
            "hazard_level": body["hazard_level"],
            "composition": body["composition"],
            "tracking_notes": body["tracking_notes"],
            "position": pos,
            "orbit_path": generate_orbit_path(body, samples=40),
            "distance_earth_au": round(dist_earth_au, 4),
            "distance_earth_km": round(dist_earth_km, 0),
            "distance_earth_ld": round(dist_earth_ld, 2),
            "is_close_approach": dist_earth_ld < 20.0,
            "tracking_satellites": assigned_satellites
        })

    # Sort by closest approach to Earth
    tracked_results.sort(key=lambda b: b["distance_earth_au"])

    return {
        "time_offset_yr": time_offset_yr,
        "earth_position": earth_pos,
        "satellite_fleet": SATELLITE_FLEET,
        "tracked_bodies": tracked_results,
        "active_sentinel_count": len(SATELLITE_FLEET),
        "total_targets_monitored": len(ASTRAL_BODIES)
    }
