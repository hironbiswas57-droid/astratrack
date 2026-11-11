# AstraTrack AI

AstraTrack is a local astronomy explorer for deep-time sky changes, stellar seasonal markers, and modeled comet and asteroid trajectories. The FastAPI backend provides astronomy data and coordinates three specialist agents: Chronos (precession and stellar motion), Demeter (seasonal predictions), and Sentinel (orbital tracking). The served frontend visualizes those results in a planetarium and orbital view.

The computations are educational models, not authoritative ephemerides or operational planetary-defense alerts. Agent responses are rule-based by default; optional Gemini or OpenAI credentials enable LLM-generated synthesis.

## Features

- Explore pole-star changes, precession, proper motion, and constellation geometry across historical and future epochs.
- Switch between the angular celestial dome and an Earth-centered 3D stellar map with true distances returned in AU.
- Inspect solar-season calculations and stellar seasonal predictions.
- View modeled trajectories, Earth distances, and associated satellite coverage for the included bodies.
- Ask astronomy questions through the multi-agent orchestrator and receive structured analysis and suggested follow-ups.
- Use a JSON API or the browser interface.

## Requirements

- Python 3.10 or newer.
- Dependencies listed in `requirements.txt`.
- An optional Gemini or OpenAI API key for LLM enrichment. Without one, the agents return their built-in rule-based analysis. In production mode, startup validation specifically requires `GEMINI_API_KEY`.

## Setup and Run

From the project directory in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` to configure keys and server settings. Keep real credentials in `.env`; it is excluded from version control. For local development, API keys may be left empty.

Set up the environment and open the command center:

```powershell
commands\setup.bat
commands\astratrack.bat
```

The server uses HTTPS by default and generates a localhost leaf certificate, its private key, and a separate local CA certificate under `certs/`. The CA private key is generated in memory and is not saved. The local CA has been installed into this Windows user's trust store so Chrome/Edge can validate localhost HTTPS. The command center can trust a regenerated CA or remove AstraTrack roots later. Trust only the CA generated in this workspace. Firefox profiles may need their own certificate trust setting. For HTTP, choose it in the command center or run `python run_server.py --http`.

Open `https://localhost:8000` (or `https://127.0.0.1:8000`; both are in the certificate SAN). FastAPI's interactive API documentation is available at `/docs`.

Optional launcher arguments (also accepted by `commands\start_https.bat`):

```powershell
python run_server.py --host 127.0.0.1 --port 8000
python run_server.py --http --host 127.0.0.1 --port 8000
```

The defaults can also be set with `ASTRATRACK_HOST` and `ASTRATRACK_PORT`. TLS certificate and key paths can be set with `SSL_CERT_PATH` and `SSL_KEY_PATH`.

### Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `ASTRATRACK_HOST` | Bind address | `127.0.0.1` |
| `ASTRATRACK_PORT` | Listening port | `8000` |
| `ASTRATRACK_ENV` | Runtime mode; production startup requires Gemini credentials | `development` |
| `GEMINI_API_KEY` | Gemini LLM enrichment | Unset |
| `GEMINI_MODEL` | Gemini synthesis model | `gemini-3.8-flash` |
| `OPENAI_API_KEY` | OpenAI fallback when Gemini is not configured | Unset |
| `NASA_API_KEY` | NASA API credential setting; falls back to `DEMO_KEY` | `DEMO_KEY` |
| `JPL_HORIZONS_BASE_URL` | JPL Horizons API URL setting | `https://ssd.jpl.nasa.gov/api/horizons.api` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins, or `*` | `*` |
| `SSL_CERT_PATH` / `SSL_KEY_PATH` | TLS leaf certificate and private key paths | `certs/cert.pem` / `certs/key.pem` |
| `LOG_LEVEL` | Python logging level | `INFO` |

The default wildcard CORS setting is intended for local development. Restrict allowed origins before exposing the service beyond localhost. The health endpoint reports service status and capabilities without disclosing credentials or whether provider keys are configured.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Service status, cache metrics, and capability list; no credential metadata |
| `GET` | `/api/astronomy/sky?year=2026` | Constellations, stars, true stellar distances and position vectors in AU, pole telemetry, precession circle, and zodiac ages |
| `GET` | `/api/astronomy/seasons?year=2026&day_of_year=80` | Seasonal forecast, solar telemetry, and stellar predictions |
| `GET` | `/api/astronomy/trajectories?time_offset_yr=0` | Modeled tracked-body positions, orbit paths, distances, and satellite links |
| `POST` | `/api/agent/chat` | Multi-agent response; JSON body: `{"query":"...","year":2026,"day_of_year":80}` |

Chat responses include a five-stage audit trail: plan specialist work, retrieve relevant saved turns with offline local embeddings, run bounded astronomy tools, synthesize with the configured model when available, then report whether the response used provider synthesis or a deterministic fallback. “Level 5” here names this five-stage workflow; it is not a claim of human-level general intelligence. Chat remains available without provider credentials through deterministic specialist responses.

## Project Layout

```text
astratrack/
├── backend/
│   ├── agents/orchestrator.py       # Chronos, Demeter, Sentinel, and optional LLM synthesis
│   ├── astronomy/
│   │   ├── constellations.py        # Constellation network and geometry
│   │   ├── precession.py            # Pole position and precession calculations
│   │   ├── seasons.py               # Solar position and seasonal predictions
│   │   ├── stars.py                 # Star catalog and proper-motion propagation
│   │   └── trajectories.py          # Modeled body trajectories and satellite coverage
│   ├── tests/test_astronomy.py      # Astronomy and agent tests
│   ├── config.py                    # Environment and credential access
│   └── main.py                      # FastAPI routes and frontend mounting
├── frontend/
│   ├── css/style.css                # Served application styles
│   ├── js/
│   │   ├── app.js                   # API communication and interface state
│   │   ├── orbital_view.js          # Orbital visualization
│   │   └── planetarium.js           # Celestial visualization
│   └── index.html                   # Served application entry point
├── Dockerfile                       # Container deployment
├── render.yaml                      # Render web service configuration
├── commands/                        # Windows setup, launch, trust, removal, and test commands
├── run_server.py                    # Uvicorn launcher with HTTPS by default
├── requirements.txt
└── .env.example                     # Safe environment-variable template
```

`backend/main.py` serves `frontend/` at `/`. The retired root-level mockup and its assets were removed so there is one maintained web application. The interface includes the live in-app catalog/search, chat, epoch timeline, celestial dome, and trajectory view. Public resource links point to NASA Open APIs and JPL Horizons; HTML search currently consumes Wikimedia OpenSearch. Trajectory figures remain educational local models.

In `/api/astronomy/sky`, each catalog star includes exact `distance_au` and `position_au` fields (using 1 light year = 63,241.077 AU). The celestial dome uses a unit sphere to preserve familiar constellation shapes. The optional 3D stellar map places stars around Earth using a logarithmic radial display scale so the large stellar distances fit on screen; exact distances remain available in hover details and API responses. The AU shells communicate scale, while constellation line lengths are illustrative.

Conversation recall uses deterministic local hashed n-gram embeddings over saved messages. It does not download an embedding model or send chat history to an embedding provider. Run `commands\astratrack.bat` to set up, launch, manage local HTTPS trust, or run tests; each action is also available as a separate command file. Local HTTPS uses three runtime files: the CA certificate to trust, the server certificate, and its private key. No duplicate CA certificate or on-disk CA signing key is needed.

The local launcher generates `certs/local_ca.crt`, `certs/cert.pem`, and `certs/key.pem`. Containers terminate TLS at the hosting platform and run the app over HTTP internally.

### Container deployment

Build and run locally:

```powershell
docker build -t astratrack .
docker run --rm -p 8000:8000 -e GEMINI_API_KEY=your_key -e CORS_ALLOWED_ORIGINS=http://localhost:8000 astratrack
```

The included `render.yaml` configures a Render Docker web service at `https://astratrack.onrender.com`. Render terminates HTTPS with a publicly trusted certificate at the edge; the container runs HTTP behind that TLS proxy. Set `GEMINI_API_KEY` in the hosting service environment; production startup requires it. Keep API credentials out of the image and repository. Update `CORS_ALLOWED_ORIGINS` if the public hostname changes. Local SQLite databases are excluded from source control and container builds because they can contain user profiles and chat history. The app creates and seeds a fresh catalog database on first startup; attach persistent storage or move to a managed database if user bookmarks and chat memory must survive container replacement.

Google's Gemini model identifiers change over time; `GEMINI_MODEL` is configurable. The default is `gemini-3.8-flash`, listed as a stable model in the [official Gemini API model catalog](https://ai.google.dev/gemini-api/docs/models).

## Tests

Run the focused automated suite with:

```powershell
commands\run_tests.bat
```

The suite covers precession epochs, star propagation, constellation data, seasonal calculations, trajectory telemetry, and agent routing.
