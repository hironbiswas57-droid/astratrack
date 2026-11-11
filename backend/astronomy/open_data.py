"""Read-only lookups against public stellar, exoplanet, and image archives."""

import logging
import re
from typing import Any

import requests

logger = logging.getLogger(__name__)

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
EXOPLANET_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
NASA_IMAGES = "https://images-api.nasa.gov/search"
USER_AGENT = "AstraTrack/1.2 (public astronomy catalog lookup)"


def _get_json(url: str, params: dict[str, Any], timeout: float = 8.0) -> Any:
    response = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    data = payload.get("data", [])
    metadata = payload.get("metadata", [])
    if data and metadata and isinstance(data[0], list):
        names = [column.get("name") for column in metadata]
        return [dict(zip(names, row)) for row in data]
    if data and isinstance(data[0], dict):
        return data
    return []


def get_gaia_match(ra_deg: float, dec_deg: float) -> dict[str, Any] | None:
    """Return the nearest Gaia DR3 source within 2 arcminutes of the catalog coordinate."""
    ra = float(ra_deg) % 360.0
    dec = max(-90.0, min(90.0, float(dec_deg)))
    query = (
        "SELECT TOP 1 source_id,designation,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag "
        "FROM gaiadr3.gaia_source "
        f"WHERE DISTANCE(POINT('ICRS',ra,dec),POINT('ICRS',{ra:.7f},{dec:.7f})) < 0.0333333333 "
        f"ORDER BY DISTANCE(POINT('ICRS',ra,dec),POINT('ICRS',{ra:.7f},{dec:.7f}))"
    )
    try:
        rows = _rows(_get_json(GAIA_TAP, {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json", "QUERY": query}))
    except (requests.RequestException, ValueError) as exc:
        logger.info("Gaia DR3 lookup unavailable: %s", exc)
        return None
    if not rows:
        return None
    row = rows[0]
    return {
        "source_id": row.get("source_id"),
        "designation": row.get("designation"),
        "ra_deg": row.get("ra"),
        "dec_deg": row.get("dec"),
        "parallax_mas": row.get("parallax"),
        "proper_motion_ra_mas_yr": row.get("pmra"),
        "proper_motion_dec_mas_yr": row.get("pmdec"),
        "g_magnitude": row.get("phot_g_mean_mag"),
        "reference_epoch": 2016.0,
        "source_url": "https://gea.esac.esa.int/archive/",
    }


def get_confirmed_planets(host_name: str) -> list[dict[str, Any]]:
    """Look up confirmed planets for a catalog star through NASA Exoplanet Archive TAP."""
    safe_host = re.sub(r"[^A-Za-z0-9 +.-]", "", host_name).strip()[:80]
    if not safe_host:
        return []
    escaped_host = safe_host.replace("'", "''").lower()
    query = (
        "SELECT pl_name,hostname,discoverymethod,disc_year,pl_orbper,pl_rade,pl_bmasse,"
        "pl_eqt,pl_orbsmax,disc_facility FROM pscomppars "
        f"WHERE lower(hostname)=lower('{escaped_host}') ORDER BY pl_name"
    )
    try:
        rows = _rows(_get_json(EXOPLANET_TAP, {"query": query, "format": "json"}))
    except (requests.RequestException, ValueError) as exc:
        logger.info("NASA Exoplanet Archive lookup unavailable: %s", exc)
        return []
    fields = {
        "pl_name": "name", "hostname": "host", "discoverymethod": "discovery_method",
        "disc_year": "discovery_year", "pl_orbper": "orbital_period_days",
        "pl_rade": "radius_earth", "pl_bmasse": "mass_earth",
        "pl_eqt": "equilibrium_temperature_k", "disc_facility": "discovery_facility",
        "pl_orbsmax": "semi_major_axis_au",
    }
    return [{target: row.get(source) for source, target in fields.items()} for row in rows]


def get_nasa_images(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """Find image-library assets; NASA image descriptions retain their media caveats."""
    try:
        payload = _get_json(NASA_IMAGES, {"q": query, "media_type": "image", "page_size": limit})
    except (requests.RequestException, ValueError) as exc:
        logger.info("NASA Image and Video Library lookup unavailable: %s", exc)
        return []
    items = payload.get("collection", {}).get("items", []) if isinstance(payload, dict) else []
    results = []
    for item in items[:limit]:
        data = (item.get("data") or [{}])[0]
        preview = next((link.get("href") for link in item.get("links", []) if link.get("rel") == "preview"), None)
        results.append({
            "title": data.get("title"),
            "description": data.get("description", ""),
            "date_created": data.get("date_created"),
            "nasa_id": data.get("nasa_id"),
            "center": data.get("center"),
            "preview_url": preview,
            "page_url": f"https://images.nasa.gov/details/{data.get('nasa_id')}" if data.get("nasa_id") else "https://images.nasa.gov/",
            "media_type": "NASA Image and Video Library image asset",
        })
    return results
