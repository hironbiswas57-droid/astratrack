"""
Automated unit & integration tests for AstraTrack AI Cosmos Database,
HTML Search Engine & Parser, Multi-tier Cache Memory, and Nova Novice Guide Agent.
"""

import time
import pytest
from fastapi.testclient import TestClient

from backend.cache import MemoryCache, search_cache, cosmos_cache
from backend.database import (
    get_or_create_client,
    update_client_profile,
    save_client_preference,
    get_client_preferences,
    add_client_bookmark,
    get_client_bookmarks,
    delete_client_bookmark,
    record_client_history,
    save_chat_memory,
    get_client_chat_memory,
    search_cosmos_catalog,
    get_cosmos_object_by_id,
    get_cosmos_categories
)
from backend.html_search import CosmicHTMLParser, CosmicHTMLSearchEngine
from backend.agents.nova_agent import nova_agent, NOVICE_TOURS
from backend.agents.orchestrator import orchestrator
from backend.main import app

client = TestClient(app)


# ==============================================================================
#  1. CACHE MEMORY TESTS
# ==============================================================================
def test_memory_cache_lru_and_ttl():
    cache = MemoryCache(max_size=3, default_ttl_sec=2)

    # Basic set and get
    cache.set("a", 100)
    cache.set("b", 200)
    assert cache.get("a") == 100
    assert cache.get("b") == 200

    # LRU eviction
    cache.set("c", 300)
    cache.set("d", 400) # Should evict least recently used (which is 'a' if 'b' was accessed)
    assert cache.get("d") == 400
    assert len(cache._cache) <= 3

    # Stats
    stats = cache.get_stats()
    assert stats["hits"] > 0
    assert stats["size"] <= 3

    # TTL expiration
    cache.set("quick", "vanish", ttl_sec=0.05)
    time.sleep(0.08)
    assert cache.get("quick") is None


# ==============================================================================
#  2. COSMOS DATABASE TESTS
# ==============================================================================
def test_cosmos_catalog_seeding_and_search():
    # Test categories
    categories = get_cosmos_categories()
    assert len(categories) >= 5
    cat_names = [c["category"] for c in categories]
    assert "galaxy" in cat_names
    assert "nebula" in cat_names
    assert "exoplanet" in cat_names
    assert "asteroid" in cat_names

    # Test keyword search
    andromeda_search = search_cosmos_catalog(query="Andromeda")
    assert andromeda_search["total"] >= 1
    top_hit = andromeda_search["results"][0]
    assert "Andromeda" in top_hit["name"] or "M31" in top_hit["catalog_id"]

    # Test category filter
    exoplanet_search = search_cosmos_catalog(category="exoplanet")
    assert exoplanet_search["total"] >= 2
    for r in exoplanet_search["results"]:
        assert r["category"] == "exoplanet"

    # Test single object retrieval
    m42 = get_cosmos_object_by_id("m42")
    assert m42 is not None
    assert "Orion" in m42["name"]
    assert m42["observation_difficulty"] == "naked_eye"


# ==============================================================================
#  3. CLIENT MEMORY & PREFERENCES TESTS
# ==============================================================================
def test_client_memory_and_bookmarks():
    test_client_id = f"test_observer_{int(time.time())}"

    # Create client
    c = get_or_create_client(test_client_id, default_level="novice")
    assert c["client_id"] == test_client_id
    assert c["experience_level"] == "novice"

    # Update profile
    updated = update_client_profile(test_client_id, username="AstroExplorer", experience_level="expert", novice_mode_active=False)
    assert updated["username"] == "AstroExplorer"
    assert updated["experience_level"] == "expert"

    # Preferences
    save_client_preference(test_client_id, "favorite_constellation", "Orion")
    prefs = get_client_preferences(test_client_id)
    assert prefs.get("favorite_constellation") == "Orion"

    # Bookmarks
    add_client_bookmark(test_client_id, "m31", notes="Target for next binoculars session")
    bookmarks = get_client_bookmarks(test_client_id)
    assert len(bookmarks) == 1
    assert bookmarks[0]["object_id"] == "m31"

    # Delete bookmark
    delete_client_bookmark(test_client_id, "m31")
    bookmarks_after = get_client_bookmarks(test_client_id)
    assert len(bookmarks_after) == 0

    # Chat memory
    save_chat_memory(test_client_id, "user", "What is Polaris?")
    save_chat_memory(test_client_id, "assistant", "Polaris is our current North Pole star.")
    mem = get_client_chat_memory(test_client_id, limit=5)
    assert len(mem) == 2
    assert mem[0]["message"] == "What is Polaris?"


# ==============================================================================
#  4. HTML SEARCH ENGINE & PARSER TESTS
# ==============================================================================
def test_cosmic_html_parser():
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Discovery of Water Vapor on Exoplanet Proxima Centauri b</title>
        <meta name="description" content="Spectroscopic observations from JWST suggest prebiotic molecules in Orion and Centaurus.">
      </head>
      <body>
        <h1>Exoplanet Exploration Mission</h1>
        <p>Astronomers observed Ursa Major and detected asteroid Apophis passing Earth.</p>
        <a href="https://nasa.gov/missions/jwst">JWST Mission Details</a>
      </body>
    </html>
    """
    parsed = CosmicHTMLParser.parse_document(sample_html, source_url="https://astronomy.example.org")
    assert "Water Vapor" in parsed["title"]
    assert "JWST" in parsed["description"]
    assert len(parsed["links"]) >= 1
    # Check detected celestial entities
    entities = parsed["detected_entities"]
    assert "JWST" in entities or "Apophis" in entities or "Ursa Major" in entities


def test_cosmic_search_engine_aggregation():
    engine = CosmicHTMLSearchEngine()
    results = engine.search(query="Apophis", search_web=False)
    assert results["total_results"] >= 1
    top = results["results"][0]
    assert "Apophis" in top["title"]
    assert top["type"] == "cosmos_catalog"


# ==============================================================================
#  5. NOVA NOVICE GUIDE AGENT TESTS
# ==============================================================================
def test_nova_novice_guidance():
    assert nova_agent.is_novice_query("I am a beginner and need a tour", "novice") is True
    assert "tour_nav_101" in NOVICE_TOURS
    assert "tour_defense_101" in NOVICE_TOURS

    res = nova_agent.analyze("Teach me how to find the North Star", 2026.0, client_id="test_client_novice")
    assert res["agent"] == "Nova"
    assert "insights" in res
    assert len(res["insights"]) >= 3
    assert any("top" in ins.lower() or "spinning" in ins.lower() or "clock" in ins.lower() for ins in res["insights"])


def test_orchestrator_novice_routing():
    res = orchestrator.process_query("I'm a complete novice, help me get started", 2026.0, client_id="test_client_novice")
    assert "Nova" in res["agents_invoked"]
    assert any(act["action"] in ["suggest_tour", "set_client_level"] for act in res["ui_actions"])


# ==============================================================================
#  6. REST API ENDPOINTS INTEGRATION
# ==============================================================================
def test_api_cosmos_and_search_endpoints():
    # Catalog
    r_cat = client.get("/api/cosmos/catalog?limit=5")
    assert r_cat.status_code == 200
    assert r_cat.json()["count"] > 0

    # Single Object
    r_obj = client.get("/api/cosmos/object/m31")
    assert r_obj.status_code == 200
    assert r_obj.json()["id"] == "m31"

    # HTML Search
    r_search = client.post("/api/search/html", json={"query": "Andromeda", "search_web": False})
    assert r_search.status_code == 200
    assert r_search.json()["total_results"] >= 1

    # Guided Tours
    r_tours = client.get("/api/tours")
    assert r_tours.status_code == 200
    assert len(r_tours.json()["tours"]) >= 3

    # Client Profile & Memory
    r_prof = client.get("/api/client/profile?client_id=test_api_client")
    assert r_prof.status_code == 200
    assert "client" in r_prof.json()

    # Agent Chat
    r_chat = client.post("/api/agent/chat", json={
        "query": "What is the Big Dipper?",
        "year": 2026.0,
        "day_of_year": 80,
        "client_id": "test_api_client"
    })
    assert r_chat.status_code == 200
    assert "response" in r_chat.json()
