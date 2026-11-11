"""
AstraTrack AI - Cosmic HTML Search Engine & Parser
Parses live HTML astronomical search engines, portals, and web resources.
Extracts structured celestial metadata, cleans noisy HTML, identifies astronomical entities,
and caches results into the multi-tier memory system.
"""

import re
import urllib.parse
import urllib.request
import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from .cache import search_cache
from .database import search_cosmos_catalog

logger = logging.getLogger(__name__)

# User-Agent for polite astronomical research requests
USER_AGENT = "AstraTrackAI-Observatory/1.0 (Cyber-Astronomical Educational Sentinel; +https://astratrack.ai)"


class CosmicHTMLParser:
    """
    Robust HTML parser specifically tuned for astronomical search results,
    scientific articles, and celestial catalogs.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """Strip redundant whitespace, line breaks, and escape codes."""
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def parse_document(cls, html_content: str, source_url: str = "") -> Dict[str, Any]:
        """
        Parses raw HTML and extracts semantic metadata: title, description,
        cleaned headings, paragraphs, outbound links, and identified celestial entities.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles, forms, and navigation junk
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
            tag.decompose()

        # 1. Title Extraction
        title = ""
        if soup.title and soup.title.string:
            title = cls.clean_text(soup.title.string)
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = cls.clean_text(h1.get_text())
        if not title:
            title = "Astronomical Resource Document"

        # 2. Meta Description / OpenGraph
        meta_desc = ""
        desc_tag = (
            soup.find("meta", attrs={"name": "description"}) or
            soup.find("meta", attrs={"property": "og:description"}) or
            soup.find("meta", attrs={"name": "twitter:description"})
        )
        if desc_tag and desc_tag.get("content"):
            meta_desc = cls.clean_text(desc_tag["content"])

        # 3. Main Text Extraction (Paragraphs & Headings)
        paragraphs = []
        for p in soup.find_all(["p", "h2", "h3", "li"]):
            text = cls.clean_text(p.get_text())
            if len(text) > 25 and not text.startswith("Cookie") and "privacy policy" not in text.lower():
                paragraphs.append(text)
            if len(paragraphs) >= 15:
                break

        full_body = " ".join(paragraphs)

        # Fallback description if meta is empty
        if not meta_desc and paragraphs:
            meta_desc = paragraphs[0][:280] + ("..." if len(paragraphs[0]) > 280 else "")

        # 4. Outbound Astronomical Links
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            anchor_text = cls.clean_text(a.get_text())
            if anchor_text and len(anchor_text) > 3 and not href.startswith("#") and not href.startswith("javascript:"):
                full_link = urllib.parse.urljoin(source_url, href)
                links.append({"text": anchor_text[:60], "url": full_link})
            if len(links) >= 8:
                break

        # 5. Semantic Celestial Entity Recognition
        detected_entities = cls.extract_celestial_entities(full_body or meta_desc)

        return {
            "title": title,
            "description": meta_desc,
            "source_url": source_url,
            "detected_entities": detected_entities,
            "snippet": (meta_desc or full_body[:320]),
            "links": links
        }

    @staticmethod
    def extract_celestial_entities(text: str) -> List[str]:
        """Detect celestial objects, constellations, and space missions mentioned in text."""
        known_keywords = [
            "Polaris", "Vega", "Sirius", "Betelgeuse", "Rigel", "Thuban", "Alkaid", "Dubhe",
            "Ursa Major", "Ursa Minor", "Orion", "Taurus", "Cassiopeia", "Pleiades", "Andromeda",
            "Apophis", "Halley", "Bennu", "NEOWISE", "JWST", "Hubble", "Chandra",
            "TRAPPIST-1", "Proxima Centauri", "Kepler", "Precession", "Equinox",
            "Black Hole", "Supernova", "Neutron Star", "Sagittarius A*", "Exoplanet"
        ]
        found = set()
        text_lower = text.lower()
        for kw in known_keywords:
            if kw.lower() in text_lower:
                found.add(kw)
        return sorted(list(found))


class CosmicHTMLSearchEngine:
    """
    Search engine that aggregates searches across:
    1. Curated Local Cosmos Database
    2. Wikipedia Astronomical Portal (HTML search engine parsed via BeautifulSoup)
    3. NASA / Astrophysics Open Web Endpoints
    """

    def __init__(self):
        self.parser = CosmicHTMLParser()

    def search(self, query: str, search_web: bool = True, max_results: int = 15) -> Dict[str, Any]:
        """
        Execute search across Cosmos Database and parsed HTML web search engines.
        Results are cached in memory for high-speed repeated retrieval.
        """
        query = query.strip()
        if not query:
            return {"query": "", "total_results": 0, "results": []}

        cache_key = f"cosmic_search_{query.lower()}_{search_web}_{max_results}"
        cached = search_cache.get(cache_key)
        if cached is not None:
            logger.debug("Serving search results from memory cache for query: %s", query)
            cached["from_cache"] = True
            return cached

        combined_results = []

        # ── Step 1: Query Curated Authoritative Cosmos Catalog (Database) ──────
        db_results = search_cosmos_catalog(query=query, limit=10)
        for item in db_results.get("results", []):
            combined_results.append({
                "type": "cosmos_catalog",
                "title": f"{item['name']} ({item['catalog_id']})",
                "subtitle": f"{item['category'].upper()} • {item['constellation']}",
                "description": item["description"],
                "source": item["source_reference"],
                "difficulty": item["observation_difficulty"],
                "url": f"/api/cosmos/object/{item['id']}",
                "coordinates": {"ra_deg": item["ra_deg"], "dec_deg": item["dec_deg"]},
                "tags": item["tags"].split(",") if item.get("tags") else [],
                "scientific_data": item.get("scientific_data", {}),
                "action": {
                    "label": "Inspect Object",
                    "target_id": item["id"],
                    "view_mode": "orbital" if item["category"] in ["asteroid", "comet"] else "planetarium"
                }
            })

        # ── Step 2: Query & Parse HTML Search Engines if Web Search is Active ──
        if search_web and len(combined_results) < max_results:
            web_hits = self._query_and_parse_wiki_astronomy(query)
            combined_results.extend(web_hits)

        # Formulate response
        response = {
            "query": query,
            "total_results": len(combined_results),
            "results": combined_results[:max_results],
            "from_cache": False
        }

        # Cache results for 30 minutes
        search_cache.set(cache_key, response, ttl_sec=1800)
        return response

    def _query_and_parse_wiki_astronomy(self, query: str) -> List[Dict[str, Any]]:
        """
        Queries Wikipedia Astronomy API, fetches the live HTML summary,
        and parses it using CosmicHTMLParser into rich astronomical search cards.
        """
        web_hits = []
        try:
            # Query Wikipedia Opensearch API (free, open, highly reliable for astronomy)
            encoded_q = urllib.parse.quote(query)
            api_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_q}&limit=5&namespace=0&format=json"

            req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=5.0) as res:
                import json
                data = json.loads(res.read().decode("utf-8"))

            titles = data[1] if len(data) > 1 else []
            descriptions = data[2] if len(data) > 2 else []
            urls = data[3] if len(data) > 3 else []

            for title, desc, url in zip(titles, descriptions, urls):
                # Filter for astronomy-related results
                entities = CosmicHTMLParser.extract_celestial_entities(f"{title} {desc}")
                is_astro = bool(entities) or any(w in (title + desc).lower() for w in [
                    "star", "planet", "galaxy", "orbit", "astronomy", "celestial",
                    "nebula", "constellation", "space", "equinox", "comet", "telescope"
                ])

                if is_astro and desc:
                    web_hits.append({
                        "type": "parsed_html_engine",
                        "title": title,
                        "subtitle": "Wikipedia Astronomy Archive (HTML Parsed)",
                        "description": desc,
                        "source": "Wikipedia Astronomy & Astrophysics Portal",
                        "difficulty": "general_knowledge",
                        "url": url,
                        "detected_entities": entities,
                        "action": {
                            "label": "Read Source Archive",
                            "external_url": url
                        }
                    })
        except Exception as exc:
            logger.warning("HTML Search Engine fetch encountered: %s", exc)

        return web_hits

    def parse_custom_url(self, url: str) -> Dict[str, Any]:
        """
        Directly fetches and parses an HTML page from a provided URL,
        returning structured celestial entities, title, text, and metadata.
        """
        cache_key = f"parsed_url_{url}"
        cached = search_cache.get(cache_key)
        if cached:
            return cached

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=8.0) as res:
                html = res.read().decode("utf-8", errors="replace")

            parsed = self.parser.parse_document(html, source_url=url)
            search_cache.set(cache_key, parsed, ttl_sec=3600)
            return parsed
        except Exception as exc:
            logger.error("Failed to parse URL %s: %s", url, exc)
            return {"error": str(exc), "source_url": url}


# Singleton search engine instance
html_search_engine = CosmicHTMLSearchEngine()
