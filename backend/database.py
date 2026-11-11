"""
AstraTrack AI - Cosmos Database & Client Memory System
Provides persistent SQLite storage for:
1. Client Profiles, Preferences, Bookmarks, and Conversational Memory
2. Authoritative Cosmos Catalog seeded from NASA, SEDS Messier, SIMBAD, and JPL Small-Body Database
3. Persistent Cache Storage
"""

import os
import sqlite3
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Locate database in astratrack/data directory
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "astratrack.db"


def get_db_connection() -> sqlite3.Connection:
    """Create or return a thread-safe connection to the SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    """Initialize database tables and seed authoritative cosmic catalog if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    -- 1. Clients Table (User profiling & skill level)
    CREATE TABLE IF NOT EXISTS clients (
        client_id TEXT PRIMARY KEY,
        username TEXT NOT NULL DEFAULT 'Stargazer',
        experience_level TEXT NOT NULL DEFAULT 'novice', -- novice | intermediate | expert
        novice_mode_active INTEGER NOT NULL DEFAULT 1,
        notes TEXT DEFAULT '',
        created_at REAL NOT NULL,
        last_active REAL NOT NULL
    );

    -- 2. Client Preferences (Key-Value)
    CREATE TABLE IF NOT EXISTS client_preferences (
        client_id TEXT NOT NULL,
        pref_key TEXT NOT NULL,
        pref_value TEXT NOT NULL,
        updated_at REAL NOT NULL,
        PRIMARY KEY (client_id, pref_key),
        FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
    );

    -- 3. Client Bookmarks (Saved celestial objects)
    CREATE TABLE IF NOT EXISTS client_bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        object_id TEXT NOT NULL,
        object_name TEXT NOT NULL,
        category TEXT NOT NULL,
        notes TEXT DEFAULT '',
        saved_at REAL NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE,
        UNIQUE(client_id, object_id)
    );

    -- 4. Client Activity History (Actions & Tour Progress)
    CREATE TABLE IF NOT EXISTS client_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        action_type TEXT NOT NULL, -- view_epoch | inspect_target | complete_tour_step | search
        details_json TEXT NOT NULL DEFAULT '{}',
        timestamp REAL NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
    );

    -- 5. Client Chat Memory (Conversational context)
    CREATE TABLE IF NOT EXISTS client_chat_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        role TEXT NOT NULL, -- user | assistant
        message TEXT NOT NULL,
        agent_invoked TEXT DEFAULT 'AstraTrack',
        timestamp REAL NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
    );

    -- 6. Cosmos Catalog (Reliable astronomical resources)
    CREATE TABLE IF NOT EXISTS cosmos_catalog (
        id TEXT PRIMARY KEY,
        catalog_id TEXT NOT NULL,          -- e.g. M31, NGC 1976, Kepler-452b
        name TEXT NOT NULL,
        common_name TEXT NOT NULL,
        category TEXT NOT NULL,            -- galaxy | nebula | star_cluster | exoplanet | star | asteroid | black_hole
        subcategory TEXT NOT NULL DEFAULT '',
        ra_deg REAL,                       -- Right Ascension (0-360)
        dec_deg REAL,                      -- Declination (-90 to +90)
        dist_ly REAL,                      -- Distance in light years
        mag REAL,                          -- Apparent magnitude
        constellation TEXT NOT NULL,
        description TEXT NOT NULL,
        scientific_data_json TEXT NOT NULL DEFAULT '{}',
        source_reference TEXT NOT NULL,    -- NASA, SIMBAD, SEDS, JPL
        observation_difficulty TEXT NOT NULL, -- naked_eye | binoculars | small_telescope | large_telescope | space_probe
        tags TEXT NOT NULL DEFAULT ''
    );

    -- 7. Persistent Cache Store (Fallback for expired / memory evicted items)
    CREATE TABLE IF NOT EXISTS cache_store (
        cache_key TEXT PRIMARY KEY,
        value_json TEXT NOT NULL,
        namespace TEXT NOT NULL DEFAULT 'default',
        expires_at REAL NOT NULL,
        created_at REAL NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_cosmos_category ON cosmos_catalog(category);
    CREATE INDEX IF NOT EXISTS idx_cosmos_difficulty ON cosmos_catalog(observation_difficulty);
    CREATE INDEX IF NOT EXISTS idx_cosmos_constellation ON cosmos_catalog(constellation);
    CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_store(expires_at);
    """)

    conn.commit()

    # Check if cosmos_catalog needs seeding
    cursor.execute("SELECT COUNT(*) FROM cosmos_catalog")
    count = cursor.fetchone()[0]
    if count == 0:
        logger.info("Seeding authoritative Cosmos Catalog into database...")
        _seed_cosmos_catalog(conn)

    conn.close()


def _seed_cosmos_catalog(conn: sqlite3.Connection) -> None:
    """Populate database with verified records from reliable astronomical catalogs."""
    records = [
        # --- Deep Sky / Messier (SEDS / NASA / Hubble) ---
        (
            "m31", "M31 / NGC 224", "Andromeda Galaxy", "The Great Andromeda Spiral",
            "galaxy", "spiral", 10.68, 41.27, 2537000.0, 3.44, "Andromeda",
            "Nearest major spiral galaxy to the Milky Way, containing approximately one trillion stars. Bound on a mutual collision trajectory with the Milky Way in ~4.5 billion years.",
            json.dumps({"diameter_ly": 220000, "radial_velocity_kms": -301, "morphology": "SA(s)b", "satellite_galaxies": ["M32", "M110"]}),
            "NASA Extragalactic Database (NED) / SEDS", "naked_eye", "galaxy,spiral,messier,local_group,naked_eye"
        ),
        (
            "m42", "M42 / NGC 1976", "Orion Nebula", "The Great Orion Nebula",
            "nebula", "diffuse_emission", 83.82, -5.39, 1344.0, 4.0, "Orion",
            "Vast stellar nursery situated south of Orion's Belt. Illuminating young massive stars within the Trapezium cluster trigger glowing ionization fronts.",
            json.dumps({"diameter_ly": 24, "age_myr": 3, "embedded_stars": "Trapezium Cluster", "stellar_nursery": True}),
            "Hubble Space Telescope / SIMBAD", "naked_eye", "nebula,star_formation,orion,messier,winter"
        ),
        (
            "m45", "M45", "Pleiades", "The Seven Sisters",
            "star_cluster", "open_cluster", 56.75, 24.11, 444.0, 1.6, "Taurus",
            "Famous open star cluster dominated by luminous hot blue B-type stars. Revering cultural signpost historically indicating ancient harvest and sowing seasons.",
            json.dumps({"brightest_stars": ["Alcyone", "Electra", "Maia", "Merope", "Taygeta"], "age_myr": 100, "cluster_type": "Open"}),
            "Hipparcos / Gaia Catalog", "naked_eye", "cluster,pleiades,seven_sisters,taurus,messier,ancient_calendar"
        ),
        (
            "m1", "M1 / NGC 1952", "Crab Nebula", "Taurus Supernova Remnant",
            "nebula", "supernova_remnant", 83.63, 22.01, 6500.0, 8.4, "Taurus",
            "Gaseous remnant of the historic SN 1054 supernova recorded by Chinese, Japanese, and Arab astronomers in 1054 CE. Harbors a central 30-Hz pulsating neutron star (Crab Pulsar).",
            json.dumps({"pulsar_period_sec": 0.033, "expansion_speed_kms": 1500, "supernova_year": 1054}),
            "Chandra X-Ray / NASA SEDS", "binoculars", "nebula,supernova,pulsar,taurus,neutron_star"
        ),
        (
            "m13", "M13 / NGC 6205", "Great Hercules Cluster", "Hercules Globular",
            "star_cluster", "globular_cluster", 250.42, 36.46, 22200.0, 5.8, "Hercules",
            "One of the brightest and most densely packed globular clusters in the northern sky, containing several hundred thousand ancient stars dating back 11.6 billion years.",
            json.dumps({"star_count": 300000, "age_gyr": 11.65, "arecibo_message_target": True}),
            "SIMBAD / Gaia DR3", "binoculars", "cluster,globular,hercules,ancient,messier"
        ),
        (
            "m57", "M57 / NGC 6720", "Ring Nebula", "The Cosmic Smoke Ring",
            "nebula", "planetary_nebula", 283.40, 33.03, 2570.0, 8.8, "Lyra",
            "Iconic planetary nebula formed by a dying intermediate-mass star expelling its outer ionized envelopes into the void, leaving an ultra-dense central white dwarf.",
            json.dumps({"central_star_mag": 15.75, "expansion_age_yr": 7000, "central_star": "White Dwarf"}),
            "Hubble / JWST NIRCam", "small_telescope", "nebula,planetary,lyra,white_dwarf,messier"
        ),
        (
            "m87", "M87 / NGC 4486", "Virgo A", "Messier 87 Elliptical Supergiant",
            "galaxy", "elliptical", 187.71, 12.39, 53500000.0, 9.59, "Virgo",
            "Supergiant elliptical galaxy in the Virgo Cluster harboring the historic supermassive black hole Powehi (6.5 billion solar masses) imaged by the Event Horizon Telescope (EHT).",
            json.dumps({"black_hole_name": "M87*", "black_hole_mass_solar": 6.5e9, "relativistic_jet_ly": 5000}),
            "Event Horizon Telescope (EHT) / NASA NED", "small_telescope", "galaxy,black_hole,eht,relativistic_jet,virgo"
        ),

        # --- NASA Exoplanet Archive (Reliable Discovery Records) ---
        (
            "trappist1e", "TRAPPIST-1 e", "TRAPPIST-1 e", "Temperate Earth-Sized Rocky World",
            "exoplanet", "terrestrial", 346.62, -5.04, 39.46, 18.8, "Aquarius",
            "Earth-sized terrestrial exoplanet orbiting within the conservative habitable zone of the ultra-cool dwarf TRAPPIST-1. Prime target for JWST atmospheric transmission spectroscopy.",
            json.dumps({"radius_earth": 0.92, "mass_earth": 0.69, "orbital_period_days": 6.1, "equilibrium_temp_k": 251, "discovery_method": "Transit"}),
            "NASA Exoplanet Archive / Spitzer / JWST", "space_probe", "exoplanet,habitable_zone,trappist,earth_analog,aquarius"
        ),
        (
            "proxima_b", "Proxima Centauri b", "Proxima Centauri b", "Our Nearest Exoplanet Neighbor",
            "exoplanet", "terrestrial", 217.43, -62.68, 4.24, 11.13, "Centaurus",
            "Closest known exoplanet to the Solar System, orbiting in the habitable zone of the red dwarf Proxima Centauri at 4.24 light-years. Discovered via radial velocity Doppler shifts.",
            json.dumps({"minimum_mass_earth": 1.17, "orbital_period_days": 11.2, "distance_pc": 1.3, "discovery_method": "Radial Velocity"}),
            "ESO / NASA Exoplanet Archive", "space_probe", "exoplanet,nearest,proxima,centaurus,habitable"
        ),
        (
            "kepler452b", "Kepler-452 b", "Kepler-452 b", "Earth's Older Cousin",
            "exoplanet", "super_earth", 296.01, 44.28, 1785.0, 13.4, "Cygnus",
            "First near-Earth-size world discovered in the habitable zone of a Sun-like G2-type star by NASA's Kepler Mission. Year length is 385 Earth days.",
            json.dumps({"radius_earth": 1.56, "orbital_period_days": 384.8, "host_star_type": "G2V", "discovery_year": 2015}),
            "NASA Kepler Space Telescope Archive", "space_probe", "exoplanet,super_earth,kepler,habitable,cygnus"
        ),
        (
            "wasp12b", "WASP-12 b", "WASP-12 b", "Tidally Disrupted Hot Jupiter",
            "exoplanet", "hot_jupiter", 97.64, 29.67, 1410.0, 11.7, "Auriga",
            "Ultra-hot gas giant in an extremely tight 1.1-day orbit around its host star. Gravitational tidal forces deform the planet into an egg shape as its atmosphere is continuously stripped away.",
            json.dumps({"temp_kelvin": 2500, "orbital_period_days": 1.09, "mass_jupiter": 1.47, "albedo": 0.064}),
            "SuperWASP / Hubble Spectroscopy", "space_probe", "exoplanet,hot_jupiter,extreme,auriga"
        ),

        # --- Luminous Anchor Stars & Millennial Pole Stars ---
        (
            "polaris", "Alpha UMi / HIP 11767", "Polaris", "Current North Pole Star",
            "star", "supergiant_variable", 37.95, 89.26, 433.0, 1.98, "Ursa Minor",
            "Triple star system whose primary component is a classical Cepheid variable. Currently located less than 0.7° from the North Celestial Pole.",
            json.dumps({"spectral_type": "F7Ib", "proper_motion_ra_mas": 44.22, "proper_motion_dec_mas": -11.75, "cycle_role": "Present North Star"}),
            "Hipparcos / Gaia DR3", "naked_eye", "star,pole_star,polaris,navigation,ursa_minor"
        ),
        (
            "vega", "Alpha Lyr / HIP 91262", "Vega", "Harp Star & Future Pole Anchor",
            "star", "main_sequence", 279.23, 38.78, 25.04, 0.03, "Lyra",
            "Fifth brightest star in the night sky and the baseline 0-magnitude anchor for stellar photometry. Served as the Pole Star in 12,000 BCE and will return to polar guardianship in 13,700 CE.",
            json.dumps({"spectral_type": "A0V", "rapid_rotator_speed_kms": 236, "dust_disk": True, "precession_role": "Ancient/Future Pole Star"}),
            "SIMBAD / Gaia DR3", "naked_eye", "star,pole_star,vega,precession,lyra,summer_triangle"
        ),
        (
            "thuban", "Alpha Dra / HIP 68756", "Thuban", "Giza Pyramids Pole Star",
            "star", "giant", 211.10, 64.38, 303.0, 3.67, "Draco",
            "Ancient North Star when the Egyptian Pyramids of Giza were constructed around 2800 BCE. The ascending and descending shafts in the Great Pyramid were aligned toward Thuban.",
            json.dumps({"spectral_type": "A0III", "pyramid_alignment_year": -2800, "precession_role": "Egyptian Pole Star"}),
            "SIMBAD / Archaeoastronomy Records", "naked_eye", "star,thuban,draco,egypt,pyramid,pole_star"
        ),
        (
            "sirius", "Alpha CMa / HIP 32349", "Sirius", "The Dog Star",
            "star", "binary_system", 101.29, -16.72, 8.6, -1.46, "Canis Major",
            "Brightest individual star in Earth's night sky. Accompanied by Sirius B, the first white dwarf ever identified. Its heliacal dawn rising signaled the ancient Nile flood season.",
            json.dumps({"spectral_type": "A1V + DA2", "companion": "The Pup (Sirius B)", "heliacal_rising_significance": "Egyptian New Year / Nile Flood"}),
            "SIMBAD / Hipparcos", "naked_eye", "star,sirius,brightest,canis_major,ancient_calendar,nile"
        ),
        (
            "betelgeuse", "Alpha Ori / HIP 27989", "Betelgeuse", "Red Supergiant of Orion",
            "star", "red_supergiant", 88.79, 7.41, 642.5, 0.50, "Orion",
            "Enormous pulsating red supergiant near the end of its thermonuclear lifecycle. If placed at the center of our solar system, its surface would extend past the orbit of Jupiter.",
            json.dumps({"radius_solar": 764, "pulsation_period_days": 420, "supernova_imminent": "100,000 years"}),
            "ESO VLT / ALMA / Hubble", "naked_eye", "star,red_supergiant,betelgeuse,orion,supernova_candidate"
        ),

        # --- Extreme Cosmic Objects & Black Holes ---
        (
            "sgr_a_star", "Sagittarius A*", "Sagittarius A*", "Milky Way Supermassive Core",
            "black_hole", "supermassive", 266.42, -29.01, 26700.0, 99.0, "Sagittarius",
            "The supermassive black hole anchoring the center of our galaxy with 4.15 million solar masses. Direct shadow resolved by the Event Horizon Telescope collaboration in 2022.",
            json.dumps({"mass_solar": 4.15e6, "schwarzschild_radius_km": 1.2e7, "eht_imaging_year": 2022}),
            "Event Horizon Telescope / Keck / UCLA Galactic Center Group", "space_probe", "black_hole,supermassive,milky_way_center,sagittarius"
        ),
        (
            "cygnus_x1", "Cygnus X-1 / HDE 226868", "Cygnus X-1", "First Confirmed Stellar Black Hole",
            "black_hole", "stellar_mass", 299.59, 35.20, 7200.0, 8.9, "Cygnus",
            "Intense X-ray binary system containing a 21-solar-mass black hole accreting gas from a blue supergiant companion star. First generally accepted astrophysical black hole.",
            json.dumps({"black_hole_mass_solar": 21.2, "companion_type": "O9.7Iab", "spin_parameter": 0.95}),
            "Chandra X-Ray / NASA Goddard", "large_telescope", "black_hole,xray_binary,cygnus,stellar_mass"
        ),

        # --- Near-Earth Objects & Historic Comets (JPL Horizons) ---
        (
            "apophis", "99942 Apophis (2004 MN4)", "Apophis", "Potentially Hazardous Asteroid",
            "asteroid", "aten_asteroid", 320.0, -10.0, 0.00025, 19.7, "Various",
            "370-meter asteroid slated for a sensational close approach on April 13, 2029, passing within 31,600 km (0.08 LD) of Earth's surface — closer than geostationary communication satellites.",
            json.dumps({"diameter_m": 370, "close_approach_date": "2029-04-13", "clearance_km": 31600, "naked_eye_during_flyby": True}),
            "NASA JPL Center for NEO Studies (CNEOS)", "binoculars", "asteroid,apophis,neo,close_approach,planetary_defense"
        ),
        (
            "halley", "1P/Halley", "Halley's Comet", "The Great Periodic Comet",
            "asteroid", "periodic_comet", 150.0, 5.0, 35.0, 28.0, "Various",
            "The most famous periodic comet in human records, visible from Earth every 75–76 years. Its next perihelion return is projected for mid-2061.",
            json.dumps({"period_years": 75.3, "next_perihelion": "2061-07-28", "orbital_eccentricity": 0.967, "nucleus_dimensions_km": "15x8"}),
            "JPL Small-Body Database", "naked_eye", "comet,halley,periodic,ancient_records,meteor_shower"
        ),
        (
            "bennu", "101955 Bennu", "Bennu", "OSIRIS-REx Sampled Asteroid",
            "asteroid", "apollo_asteroid", 100.0, 15.0, 0.5, 20.0, "Various",
            "Carbonaceous B-type asteroid visited by NASA's OSIRIS-REx spacecraft, which collected pristine surface regolith samples and safely delivered them to Earth in September 2023.",
            json.dumps({"diameter_m": 490, "sample_mass_grams": 121.6, "mission": "OSIRIS-REx", "hydration_bearing": True}),
            "NASA OSIRIS-REx / JPL CNEOS", "space_probe", "asteroid,bennu,osiris_rex,sample_return,carbonaceous"
        )
    ]

    cursor = conn.cursor()
    cursor.executemany("""
    INSERT OR REPLACE INTO cosmos_catalog (
        id, catalog_id, name, common_name, category, subcategory,
        ra_deg, dec_deg, dist_ly, mag, constellation, description,
        scientific_data_json, source_reference, observation_difficulty, tags
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    conn.commit()
    logger.info(f"Seeded {len(records)} authoritative cosmos catalog entries.")


# ==============================================================================
#  CLIENT DATA MANAGEMENT (Memory & Preferences)
# ==============================================================================

def get_or_create_client(client_id: str, default_level: str = "novice") -> Dict[str, Any]:
    """Retrieve client profile or register a new one. Remembers experience level."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()

    cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("""
        INSERT INTO clients (client_id, username, experience_level, novice_mode_active, created_at, last_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (client_id, f"Observer-{client_id[:6]}", default_level, 1 if default_level == "novice" else 0, now, now))
        conn.commit()
        cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
        row = cursor.fetchone()
    else:
        # Update last active timestamp
        cursor.execute("UPDATE clients SET last_active = ? WHERE client_id = ?", (now, client_id))
        conn.commit()

    client_dict = dict(row)
    conn.close()
    return client_dict


def update_client_profile(client_id: str, username: Optional[str] = None,
                          experience_level: Optional[str] = None,
                          novice_mode_active: Optional[bool] = None,
                          notes: Optional[str] = None) -> Dict[str, Any]:
    """Update client profile settings and experience level memory."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()

    fields = ["last_active = ?"]
    params = [now]

    if username is not None:
        fields.append("username = ?")
        params.append(username)
    if experience_level is not None:
        fields.append("experience_level = ?")
        params.append(experience_level)
    if novice_mode_active is not None:
        fields.append("novice_mode_active = ?")
        params.append(1 if novice_mode_active else 0)
    if notes is not None:
        fields.append("notes = ?")
        params.append(notes)

    params.append(client_id)
    cursor.execute(f"UPDATE clients SET {', '.join(fields)} WHERE client_id = ?", params)
    conn.commit()

    cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def save_client_preference(client_id: str, key: str, value: Any) -> None:
    """Store arbitrary client preference (e.g. favorite_constellation, theme)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    val_str = json.dumps(value) if not isinstance(value, str) else value
    cursor.execute("""
    INSERT OR REPLACE INTO client_preferences (client_id, pref_key, pref_value, updated_at)
    VALUES (?, ?, ?, ?)
    """, (client_id, key, val_str, time.time()))
    conn.commit()
    conn.close()


def get_client_preferences(client_id: str) -> Dict[str, Any]:
    """Retrieve all stored preferences for a client."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pref_key, pref_value FROM client_preferences WHERE client_id = ?", (client_id,))
    prefs = {}
    for row in cursor.fetchall():
        try:
            prefs[row["pref_key"]] = json.loads(row["pref_value"])
        except Exception:
            prefs[row["pref_key"]] = row["pref_value"]
    conn.close()
    return prefs


def add_client_bookmark(client_id: str, object_id: str, notes: str = "") -> Dict[str, Any]:
    """Save a cosmic object into the client's notebook."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Look up object name and category from catalog
    cursor.execute("SELECT name, category FROM cosmos_catalog WHERE id = ?", (object_id,))
    item = cursor.fetchone()
    obj_name = item["name"] if item else object_id
    category = item["category"] if item else "custom"

    cursor.execute("""
    INSERT OR REPLACE INTO client_bookmarks (client_id, object_id, object_name, category, notes, saved_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (client_id, object_id, obj_name, category, notes, time.time()))
    conn.commit()
    conn.close()
    return {"status": "saved", "object_id": object_id, "object_name": obj_name}


def get_client_bookmarks(client_id: str) -> List[Dict[str, Any]]:
    """Retrieve all saved bookmarks for a client."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.*, c.description, c.constellation, c.mag, c.observation_difficulty
    FROM client_bookmarks b
    LEFT JOIN cosmos_catalog c ON b.object_id = c.id
    WHERE b.client_id = ?
    ORDER BY b.saved_at DESC
    """, (client_id,))
    bookmarks = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return bookmarks


def delete_client_bookmark(client_id: str, object_id: str) -> bool:
    """Remove a bookmark."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM client_bookmarks WHERE client_id = ? AND object_id = ?", (client_id, object_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected


def record_client_history(client_id: str, action_type: str, details: Dict[str, Any]) -> None:
    """Log client interaction (e.g. view epoch, search, tour step) into memory."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO client_history (client_id, action_type, details_json, timestamp)
    VALUES (?, ?, ?, ?)
    """, (client_id, action_type, json.dumps(details), time.time()))
    conn.commit()
    conn.close()


def save_chat_memory(client_id: str, role: str, message: str, agent_invoked: str = "AstraTrack") -> None:
    """Store conversational memory turn."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO client_chat_memory (client_id, role, message, agent_invoked, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (client_id, role, message, agent_invoked, time.time()))
    conn.commit()
    conn.close()


def get_client_chat_memory(client_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent conversational context to power agentic memory."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT role, message, agent_invoked, timestamp
    FROM client_chat_memory
    WHERE client_id = ?
    ORDER BY id DESC LIMIT ?
    """, (client_id, limit))
    rows = cursor.fetchall()
    conn.close()
    # Reverse so it's in chronological order
    return [dict(r) for r in reversed(rows)]


# ==============================================================================
#  COSMOS CATALOG QUERIES
# ==============================================================================

def search_cosmos_catalog(query: Optional[str] = None,
                          category: Optional[str] = None,
                          difficulty: Optional[str] = None,
                          limit: int = 25,
                          offset: int = 0) -> Dict[str, Any]:
    """
    Search and filter the authoritative cosmos catalog.
    Supports keywords, categories, and observation difficulties.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if query and query.strip():
        q_wildcard = f"%{query.strip().lower()}%"
        conditions.append("""(
            LOWER(name) LIKE ? OR
            LOWER(catalog_id) LIKE ? OR
            LOWER(common_name) LIKE ? OR
            LOWER(constellation) LIKE ? OR
            LOWER(description) LIKE ? OR
            LOWER(tags) LIKE ?
        )""")
        params.extend([q_wildcard] * 6)

    if category and category.lower() != "all":
        conditions.append("LOWER(category) = ?")
        params.append(category.lower())

    if difficulty and difficulty.lower() != "all":
        conditions.append("LOWER(observation_difficulty) = ?")
        params.append(difficulty.lower())

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Total count
    count_sql = f"SELECT COUNT(*) FROM cosmos_catalog {where_clause}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]

    # Data rows
    data_sql = f"""
    SELECT id, catalog_id, name, common_name, category, subcategory,
           ra_deg, dec_deg, dist_ly, mag, constellation, description,
           source_reference, observation_difficulty, tags, scientific_data_json
    FROM cosmos_catalog
    {where_clause}
    ORDER BY CASE WHEN mag IS NOT NULL THEN mag ELSE 99 END ASC
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(data_sql, params)

    results = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["scientific_data"] = json.loads(d.pop("scientific_data_json", "{}"))
        except Exception:
            d["scientific_data"] = {}
        results.append(d)

    conn.close()
    return {
        "total": total,
        "count": len(results),
        "limit": limit,
        "offset": offset,
        "results": results
    }


def get_cosmos_object_by_id(object_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full telemetry and scientific records for a single cosmic object."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cosmos_catalog WHERE id = ? OR LOWER(catalog_id) = ?", (object_id, object_id.lower()))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    try:
        d["scientific_data"] = json.loads(d.pop("scientific_data_json", "{}"))
    except Exception:
        d["scientific_data"] = {}
    return d


def get_cosmos_categories() -> List[Dict[str, Any]]:
    """Return distinct categories with item counts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM cosmos_catalog
    GROUP BY category
    ORDER BY count DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# Initialize database automatically when imported
init_db()
