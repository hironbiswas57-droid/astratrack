"""
Automated unit tests for AstraTrack AI astronomical engines and multi-agent brain.
"""

import pytest
from backend.astronomy.precession import (
    get_north_celestial_pole,
    precess_coordinates,
    get_precession_circle_points
)
from backend.astronomy.stars import propagate_star, get_all_propagated_stars, CATALOG_STARS
from backend.astronomy.constellations import get_constellation_network
from backend.astronomy.seasons import predict_season_from_sky, sun_ecliptic_position
from backend.astronomy.trajectories import (
    get_astral_tracking_telemetry,
    compute_keplerian_position,
    ASTRAL_BODIES
)
from backend.agents.orchestrator import orchestrator


def test_north_celestial_pole_epochs():
    # Present epoch (~2026 CE): Polaris should be the closest pole star
    pole_2026 = get_north_celestial_pole(2026.0)
    assert pole_2026["closest_pole_star"] is not None
    assert "Polaris" in pole_2026["closest_pole_star"]["name"]
    assert pole_2026["closest_pole_star"]["separation_degrees"] < 2.0

    # Ancient Egypt epoch (~-2800 BCE): Thuban should be the closest pole star
    pole_egypt = get_north_celestial_pole(-2800.0)
    assert pole_egypt["closest_pole_star"] is not None
    assert "Thuban" in pole_egypt["closest_pole_star"]["name"]

    # Distant future (~13,700 CE): Vega should be the closest pole star
    pole_vega = get_north_celestial_pole(13700.0)
    assert pole_vega["closest_pole_star"] is not None
    assert "Vega" in pole_vega["closest_pole_star"]["name"]


def test_precession_circle():
    circle = get_precession_circle_points(samples=32)
    assert len(circle) == 32
    for pt in circle:
        assert 0 <= pt["ra"] <= 360
        assert 0 <= pt["dec"] <= 90


def test_proper_motion_propagation():
    # Test Barnard's star (fastest proper motion)
    barnard = next(s for s in CATALOG_STARS if s["id"] == "barnard")
    propagated_future = propagate_star(barnard, 12000.0)
    assert propagated_future["drift_arcsec"] > 50000.0
    assert propagated_future["proper_motion_visible"] is True

    # Test all stars propagate correctly
    all_stars = get_all_propagated_stars(5000.0)
    assert len(all_stars) == len(CATALOG_STARS)
    for s in all_stars:
        assert "cartesian" in s
        assert "color" in s


def test_constellation_network():
    network = get_constellation_network(2026.0)
    assert len(network["constellations"]) > 0
    uma = next(c for c in network["constellations"] if c["id"] == "UMa")
    assert len(uma["segments"]) == 7  # 7 Big Dipper stick figure segments


def test_seasons_and_helio_phenology():
    # Day 80 (Spring Equinox)
    sun = sun_ecliptic_position(80, 2026.0)
    assert sun["season"] == "Spring"

    # Day 172 (Summer Solstice)
    sun_summer = sun_ecliptic_position(172, 2026.0)
    assert sun_summer["season"] == "Summer"

    # Season prediction
    pred = predict_season_from_sky(2026.0, day_of_year=80)
    assert "solar_telemetry" in pred
    assert len(pred["stellar_predictions"]) > 0


def test_orbital_trajectories_and_satellites():
    telemetry = get_astral_tracking_telemetry(0.0)
    assert telemetry["total_targets_monitored"] >= 5
    assert telemetry["active_sentinel_count"] >= 3

    # Check Apophis
    apophis = next(b for b in telemetry["tracked_bodies"] if b["id"] == "apophis")
    assert apophis["distance_earth_au"] > 0
    assert apophis["distance_earth_km"] > 0
    assert len(apophis["orbit_path"]) > 10


def test_multi_agent_orchestrator():
    # Query about millennial constellation drift
    res_time = orchestrator.process_query("How will the Big Dipper change in year 10000 CE?", current_year=2026.0)
    assert "Chronos" in res_time["agents_invoked"]
    assert len(res_time["agent_thoughts"]) > 0

    # Query about seasons and Sirius
    res_season = orchestrator.process_query("How does the rising of Sirius predict seasons?", current_year=2026.0)
    assert "Demeter" in res_season["agents_invoked"]

    # Query about satellites tracking asteroids
    res_sat = orchestrator.process_query("How are satellites tracking asteroid Apophis?", current_year=2026.0)
    assert "Sentinel" in res_sat["agents_invoked"]
