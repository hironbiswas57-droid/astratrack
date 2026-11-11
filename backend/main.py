"""
AstraTrack AI - FastAPI Main Server
Provides REST endpoints for millennial sky computations, helio-phenology seasonal predictions,
comet/asteroid satellite trajectory tracking, multi-tier cache memory, Cosmos database,
HTML astronomical search engine parsing, and multi-agent AI dialogues with Novice Guidance.

API credentials are loaded from environment variables via backend/config.py.
See .env.example for required variables — copy it to .env and fill in your values.
"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import (
    get_cors_origins,
    get_server_settings,
    validate_required_keys,
    get_log_level,
)
from .astronomy.precession import get_north_celestial_pole, get_precession_circle_points, POLE_STARS, ZODIAC_AGES
from .astronomy.constellations import get_constellation_network
from .astronomy.seasons import predict_season_from_sky, sun_ecliptic_position
from .astronomy.trajectories import get_astral_tracking_telemetry, ASTRAL_BODIES, SATELLITE_FLEET
from .astronomy.stars import CATALOG_STARS
from .astronomy.open_data import get_gaia_match, get_confirmed_planets, get_nasa_images
from .agents.orchestrator import orchestrator
from .agents.nova_agent import NOVICE_TOURS
from .cache import search_cache, cosmos_cache, client_memory_cache
from .database import (
    get_or_create_client,
    update_client_profile,
    save_client_preference,
    get_client_preferences,
    add_client_bookmark,
    get_client_bookmarks,
    delete_client_bookmark,
    record_client_history,
    search_cosmos_catalog,
    get_cosmos_object_by_id,
    get_cosmos_categories,
    get_client_chat_memory
)
from .html_search import html_search_engine

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=getattr(logging, get_log_level(), logging.INFO))
logger = logging.getLogger(__name__)

# ── Startup Validation ────────────────────────────────────────────────────────
_missing = validate_required_keys()
if not _missing:
    logger.info("[AstraTrack Config] Required runtime configuration is available.")

# ── App Initialisation ────────────────────────────────────────────────────────
app = FastAPI(
    title="AstraTrack AI Sentinel API",
    description=(
        "Agentic celestial tracking, millennial constellation precession, "
        "authoritative cosmos databases, HTML search engine parsers, "
        "and novice guidance."
    ),
    version="1.1.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    year: float = 2026.0
    day_of_year: int = 80
    client_id: str = "default_client"


class ProfileUpdateRequest(BaseModel):
    client_id: str = "default_client"
    username: Optional[str] = None
    experience_level: Optional[str] = None  # novice | intermediate | expert
    novice_mode_active: Optional[bool] = None
    notes: Optional[str] = None


class BookmarkRequest(BaseModel):
    client_id: str = "default_client"
    object_id: str
    notes: str = ""


class HTMLSearchRequest(BaseModel):
    query: str
    search_web: bool = True
    max_results: int = 15


class URLParseRequest(BaseModel):
    url: str


# ══════════════════════════════════════════════════════════════════════════════
#  CORE ASTROPHYSICS & TELEMETRY ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health_check():
    """
    System health, memory metrics, and capability report.
    Credential values and provider-configuration status are never returned here.
    """
    settings = get_server_settings()
    return {
        "status": "online",
        "system": "AstraTrack AI Sentinel",
        "version": "1.1.0",
        "environment": settings["env"],
        "cache_metrics": {
            "search_cache": search_cache.get_stats(),
            "cosmos_cache": cosmos_cache.get_stats(),
            "client_memory_cache": client_memory_cache.get_stats()
        },
        "capabilities": [
            "millennial_precession_tracking",
            "proper_motion_kinematics",
            "stellar_distances_in_astronomical_units",
            "earth_centered_constellation_mapping",
            "helio_phenology_seasons",
            "orbital_keplerian_trajectories",
            "satellite_defense_monitoring",
            "multi_agent_orchestration",
            "five_stage_agent_workflow",
            "local_semantic_memory_embeddings",
            "novice_guided_tours",
            "authoritative_cosmos_database",
            "html_search_engine_parser",
            "persistent_client_memory"
        ],
    }


@app.get("/api/astronomy/sky")
def get_sky(year: float = Query(2026.0, description="Epoch year (-15000 to +15000)")):
    """Returns stars, constellations, precession pole, and circle for given epoch year."""
    network = get_constellation_network(year)
    pole_info = get_north_celestial_pole(year)
    precession_circle = get_precession_circle_points(samples=64)

    return {
        "year": year,
        "pole_telemetry": pole_info,
        "precession_circle": precession_circle,
        "pole_stars_catalog": POLE_STARS,
        "zodiac_ages": ZODIAC_AGES,
        "stars": network["stars"],
        "constellations": network["constellations"],
    }


@app.get("/api/astronomy/stars/{star_id}/research")
def research_star(star_id: str):
    """Join a catalog star to Gaia DR3, NASA confirmed planets, and NASA image assets."""
    star = next((item for item in CATALOG_STARS if item["id"].lower() == star_id.lower()), None)
    if not star:
        raise HTTPException(status_code=404, detail=f"Star '{star_id}' is not in the current sky catalog.")

    short_name = star["name"].split(" (")[0]
    cache_key = f"star_research_{star['id']}"
    cached = cosmos_cache.get(cache_key)
    if cached:
        return cached

    lookups = {
        "gaia": (get_gaia_match, (star["ra"], star["dec"])),
        "planets": (get_confirmed_planets, (short_name,)),
        "images": (get_nasa_images, (f"{short_name} star exoplanet", 3)),
    }
    responses: dict[str, Any] = {"gaia": None, "planets": [], "images": []}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(function, *args): key for key, (function, args) in lookups.items()}
        for future in as_completed(futures, timeout=10):
            key = futures[future]
            try:
                responses[key] = future.result()
            except Exception as exc:
                logger.info("%s lookup failed for %s: %s", key, star_id, exc)
    gaia = responses["gaia"]
    planets = responses["planets"]
    images = responses["images"]
    result = {
        "star": {"id": star["id"], "name": star["name"], "constellation": star["constellation"]},
        "gaia_dr3": gaia,
        "confirmed_planets": planets,
        "planet_catalog_status": "results" if planets else "no_confirmed_planets_returned",
        "nasa_images": images,
        "sources": {
            "gaia_dr3": "https://gea.esac.esa.int/archive/",
            "nasa_exoplanet_archive": "https://exoplanetarchive.ipac.caltech.edu/",
            "nasa_images": "https://images.nasa.gov/",
        },
        "image_note": "NASA archive images can include artist concepts or diagrams; the asset description identifies what each image represents. A catalog match is not proof that the planet itself was directly imaged.",
    }
    cosmos_cache.set(cache_key, result, ttl_sec=21600)
    return result


@app.get("/api/astronomy/seasons")
def get_seasons(
    year: float = Query(2026.0, description="Epoch year"),
    day_of_year: int = Query(80, ge=1, le=366, description="Day of year (1-366)"),
):
    """Returns helio-phenology calculations, stellar seasonal predictions, and solar telemetry."""
    return predict_season_from_sky(year=year, day_of_year=day_of_year)


@app.get("/api/astronomy/trajectories")
def get_trajectories(
    time_offset_yr: float = Query(0.0, description="Time offset in years from current moment"),
):
    """Returns real-time 3D positions, orbit lines, Earth distances, and satellite locks for comets and asteroids."""
    return get_astral_tracking_telemetry(time_offset_yr=time_offset_yr)


@app.post("/api/agent/chat")
def agent_chat(req: ChatRequest):
    """
    Executes collaborative multi-agent reasoning across Chronos, Demeter, Sentinel,
    and Nova (Novice Space Mentor) using persistent client conversational memory.
    """
    result = orchestrator.process_query(
        user_query=req.query,
        current_year=req.year,
        day_of_year=req.day_of_year,
        client_id=req.client_id
    )
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  COSMOS DATABASE ROUTES (Reliable Astronomical Catalogs)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/cosmos/catalog")
def get_cosmos_catalog(
    q: Optional[str] = Query(None, description="Search keyword or designation"),
    category: Optional[str] = Query(None, description="Category filter (galaxy, nebula, star, exoplanet, asteroid, black_hole)"),
    difficulty: Optional[str] = Query(None, description="Observing difficulty (naked_eye, binoculars, small_telescope, etc.)"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Query authoritative cosmic catalog with filters and full-text keyword matching."""
    cache_key = f"catalog_query_{q}_{category}_{difficulty}_{limit}_{offset}"
    cached = cosmos_cache.get(cache_key)
    if cached:
        return cached

    res = search_cosmos_catalog(query=q, category=category, difficulty=difficulty, limit=limit, offset=offset)
    cosmos_cache.set(cache_key, res, ttl_sec=3600)
    return res


@app.get("/api/cosmos/object/{object_id}")
def get_cosmos_object(object_id: str):
    """Retrieve verified scientific data and coordinates for a single cosmic body."""
    cache_key = f"object_{object_id.lower()}"
    cached = cosmos_cache.get(cache_key)
    if cached:
        return cached

    obj = get_cosmos_object_by_id(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"Cosmic object '{object_id}' not found in database.")

    cosmos_cache.set(cache_key, obj, ttl_sec=86400)
    return obj


@app.get("/api/cosmos/categories")
def get_categories():
    """Retrieve cosmic catalog categories and counts."""
    return {"categories": get_cosmos_categories()}


# ══════════════════════════════════════════════════════════════════════════════
#  HTML SEARCH ENGINE & PARSER ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/search/html")
def search_html(req: HTMLSearchRequest):
    """
    Search across authoritative Cosmos Database and parsed live HTML astronomical engines.
    Results are cleaned, stripped of HTML noise, and cached in memory.
    """
    return html_search_engine.search(
        query=req.query,
        search_web=req.search_web,
        max_results=req.max_results
    )


@app.get("/api/search/html")
def search_html_get(
    q: str = Query(..., description="Query to search"),
    web: bool = Query(True, description="Whether to include parsed HTML web results"),
    limit: int = Query(15, ge=1, le=50)
):
    """GET convenience endpoint for HTML cosmic search engine."""
    return html_search_engine.search(query=q, search_web=web, max_results=limit)


@app.post("/api/search/parse-url")
def parse_url_endpoint(req: URLParseRequest):
    """
    Parse an arbitrary HTML webpage URL to extract celestial entities,
    clean text snippets, meta tags, and astronomical outbound links.
    """
    return html_search_engine.parse_custom_url(req.url)


# ══════════════════════════════════════════════════════════════════════════════
#  CLIENT DATA & MEMORY ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/client/profile")
def get_profile(client_id: str = Query("default_client")):
    """Fetch client memory profile, preferences, and experience level."""
    client = get_or_create_client(client_id)
    prefs = get_client_preferences(client_id)
    return {
        "client": client,
        "preferences": prefs,
        "recent_chat": get_client_chat_memory(client_id, limit=5)
    }


@app.post("/api/client/profile")
def update_profile(req: ProfileUpdateRequest):
    """Update client profile settings (experience level, novice mode, notes)."""
    updated = update_client_profile(
        client_id=req.client_id,
        username=req.username,
        experience_level=req.experience_level,
        novice_mode_active=req.novice_mode_active,
        notes=req.notes
    )
    return {"status": "updated", "client": updated}


@app.get("/api/client/bookmarks")
def list_bookmarks(client_id: str = Query("default_client")):
    """List all cosmic objects bookmarked by the client."""
    return {"bookmarks": get_client_bookmarks(client_id)}


@app.post("/api/client/bookmarks")
def add_bookmark(req: BookmarkRequest):
    """Save an astronomical object to client's personal notebook."""
    res = add_client_bookmark(client_id=req.client_id, object_id=req.object_id, notes=req.notes)
    record_client_history(req.client_id, "bookmark_added", {"object_id": req.object_id})
    return res


@app.delete("/api/client/bookmarks/{object_id}")
def remove_bookmark(object_id: str, client_id: str = Query("default_client")):
    """Delete a saved bookmark from client memory."""
    success = delete_client_bookmark(client_id=client_id, object_id=object_id)
    return {"status": "deleted" if success else "not_found", "object_id": object_id}


# ══════════════════════════════════════════════════════════════════════════════
#  NOVICE GUIDED TOURS ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/tours")
def list_guided_tours():
    """Retrieve all available guided astronomical tours for beginners."""
    return {"tours": list(NOVICE_TOURS.values())}


@app.get("/api/tours/{tour_id}")
def get_tour_details(tour_id: str):
    """Retrieve full steps and UI directives for a specific guided tour."""
    tour = NOVICE_TOURS.get(tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail=f"Tour '{tour_id}' not found.")
    return tour


@app.get("/api/cache/stats")
def cache_statistics():
    """Return live memory cache metrics and hit/miss telemetry."""
    return {
        "search_cache": search_cache.get_stats(),
        "cosmos_cache": cosmos_cache.get_stats(),
        "client_memory_cache": client_memory_cache.get_stats()
    }


# ── Mount Frontend Static Directory ───────────────────────────────────────────
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
