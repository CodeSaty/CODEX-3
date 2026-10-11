# Cultura Festival Hub (Codex 2.0) — Technical Architecture & Operational Documentation

**Cultura Festival Hub** is an asynchronous, high-throughput event operations platform for real-time crowd telemetry, bottleneck mitigation, cashless festival commerce, and incident triage.

---

## Table of Contents

1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Repository Structure](#2-repository-structure)
3. [Dataset Ingestion & Simulation Pipeline](#3-dataset-ingestion--simulation-pipeline)
4. [Data Models & MongoDB Collections](#4-data-models--mongodb-collections)
5. [Core Operational Engines](#5-core-operational-engines)
6. [REST API Specification](#6-rest-api-specification)
7. [Frontend Interfaces](#7-frontend-interfaces)
8. [Installation, Configuration & Execution](#8-installation-configuration--execution)
9. [Storage Resilience (In-Memory Fallback)](#9-storage-resilience-in-memory-fallback)
10. [Troubleshooting](#10-troubleshooting)
11. [Contributing & License](#11-contributing--license)

---

## 1. System Overview & Architecture

The platform runs on a dual-tier stack:

- A **FastAPI (Python)** backend that serves database-backed API endpoints and real-time streaming workers.
- A modular **glassmorphic web console**, plus an alternate **Node.js/Bun** static and proxy server (`backend/server.js`).

It ingests badge checkpoint scans and transactions, recalculates zone densities over rolling time windows, flags bottlenecks before physical congestion causes safety incidents, and coordinates crowd redistribution through operational diversions.

### 1.1 Tech Stack

| Layer | Technology |
| --- | --- |
| Backend framework | FastAPI (Python 3.11) |
| ASGI server | Uvicorn |
| Validation | Pydantic v2 |
| Database | MongoDB Atlas via Motor (`AsyncIOMotorClient`) |
| Fallback storage | In-memory reactive datastore with pre-seeded data |
| AI copilot | Google Gemini API |
| Weather | Open-Meteo REST API |
| Alternate server | Node.js v18+ or Bun v1.0+ |
| API docs | Swagger UI (`/docs`), ReDoc (`/redoc`) |

### 1.2 Architecture Diagram

```
                         [ INGESTION TIER ]
 Field Scanner (Staff UI)     DinoFun World Replay      Kaggle Retail Stream
     [scanner.html]          [seed_real_traffic.py]    [seed_real_traffic.py]
            │                         │                         │
            ▼                         ▼                         ▼
     POST /scan (Check-in)    POST /scan (Bulk)         POST /api/transaction
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                          [ FASTAPI BACKEND ENGINE ]
                             (backend/main.py)
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
 Bottleneck Engine            Fest Coin Engine            Incident Dispatch
(Rolling 10m Scans)        (Balance & Turnover)          (Medical/Security)
        └─────────────────────────────┼─────────────────────────────┘
                                      ▼
                          [ ASYNC STORAGE LAYER ]
                           (backend/database.py)
                            MongoDB Atlas (Motor)
          ├── zone_logs    ├── attendees    ├── transactions
          └── incidents    └── sentiment_logs
                                      ▼
                         [ OPERATIONS DASHBOARD ]
                    (frontend/index.html, analytics.html)
        ├── 3-second telemetry polling   (GET  /api/admin/stats)
        ├── Dynamic load redistribution  (POST /api/admin/trigger_diversion)
        ├── Natural-language copilot     (POST /api/admin/nlp_query)
        └── Live vibe / social friction monitoring (Hugging Face dataset)
```

---

## 2. Repository Structure

```
codex-2.0/
├── backend/
│   ├── data/
│   │   ├── dinofun_checkins.csv            # VAST Challenge crowd trajectory records
│   │   ├── huggingface_sentiment.json      # Labeled social sentiment records
│   │   └── kaggle_retail_transactions.csv  # Retail transaction events for Fest Coin
│   ├── database.py                         # Motor async client & collection references
│   ├── main.py                             # FastAPI routing, aggregation pipelines, NLP
│   ├── models.py                           # Pydantic schemas for data validation
│   ├── requirements.txt                    # Python dependencies
│   ├── seed_real_traffic.py                # Multi-dataset ingestion and replay runner
│   ├── server.js                           # Node.js/Bun alternate static and proxy server
│   └── static/
│       └── index.html                      # Packaged root dashboard bundle
├── frontend/
│   ├── admin.html                          # Operations command & simulation console
│   ├── analytics.html                      # Telemetry graphs, capacity bars, guest flow
│   ├── attendees.html                      # Attendee credentials & pass lookup
│   ├── index.html                          # Primary glassmorphic operations console
│   ├── nlp-assistant.js                    # LLM copilot UI drawer & query dispatch
│   ├── recharge.html                       # Fest Coin cashless wallet interface
│   ├── scanner.html                        # Field gate checkpoint & incident dispatcher
│   ├── settings.html                       # System thresholds & telemetry preferences
│   ├── structure-flow.js                   # Navigation & panel interaction routing
│   ├── theme.css                           # High-contrast glassmorphic styling
│   └── theme.js                            # Theme switching & canvas visual hooks
├── data/                                   # Root mirror of simulation data assets
│   ├── huggingface_sentiment.json
│   └── kaggle_retail_transactions.csv
├── static/
│   └── index.html                          # Static distribution asset
├── bun.lock                                # Bun dependency lockfile
├── package.json                            # Node.js/Bun project definitions
├── package-lock.json                       # NPM resolution lockfile
├── metadata.json                           # Workspace runtime metadata
└── seed_real_traffic.py                    # Root execution symlink for the simulator
```

---

## 3. Dataset Ingestion & Simulation Pipeline

The platform replays three public datasets to generate realistic festival activity instead of purely random synthetic numbers.

### 3.1 Crowd Movement (`backend/data/dinofun_checkins.csv`)

- **Source:** VAST Challenge 2015 DinoFun World trajectory dataset.
- **Strategy:** `seed_real_traffic.py` parses check-in rows containing visitor identifiers, timestamps, and venue locations.
- **Zone translation map:**

| Source venue type | Festival zone |
| --- | --- |
| Thrill & Pavilion attractions | Main Stage, Cultural Pavilion |
| Concession stalls & dining stands | Food Court |
| Craft exhibits & merchandise stands | Artisan Market |
| Restricted zones | VIP Lounge |

- **Value:** Recreates group clustering, staggered arrival bursts, and realistic bottlenecks during headline performances.

### 3.2 Cashless Commerce Replay (`backend/data/kaggle_retail_transactions.csv`)

- **Source:** Retail customer transaction records.
- **Fields:** Transaction ID, Customer ID, Timestamp, Category, Amount.
- **Processing:** The streamer iterates through customer expenditures, deducts the amounts as Fest Coins from the matching attendee record, and appends ledger entries to the `transactions` collection.
- **Value:** Produces realistic spending spikes around intermissions and meal hours, validating turnover metrics on the command console.

### 3.3 Sentiment & Friction Monitoring (`backend/data/huggingface_sentiment.json`)

- **Source:** Pre-labeled social sentiment dataset (positive, negative, neutral).
- **Processing:** Background workers continuously sample posts modeling commentary on sound levels, lines, hydration, and heat.
- **Threshold logic:** When the rolling ratio of negative to positive posts exceeds **60%** over a **5-minute** window, the backend sets `friction_alert: true`, turning the social listening ticker red on `index.html`.

---

## 4. Data Models & MongoDB Collections

Defined in `backend/models.py` with Pydantic, enforcing typing across async Motor operations. Collections: `attendees`, `zone_logs`, `transactions`, `incidents`, `sentiment_logs`.

### 4.1 Attendee

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Attendee(BaseModel):
    id: str = Field(..., alias="_id", description="Unique badge QR / NFC token")
    name: str
    role: str = "General"        # "General", "VIP", "Performer", "Organizer"
    ticket_type: str = "Regular"
    fest_coins: int = Field(default=1000, description="Available cashless token balance")
    engagement_score: int = Field(default=0, description="Gamification & visit weight")
    registered_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
```

### 4.2 Zone Log

```python
class ZoneLog(BaseModel):
    attendee_id: str
    zone_name: str   # "Main Stage", "Food Court", "Artisan Market", "Cultural Pavilion", "VIP Lounge"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    simulated: bool = False
    metadata: Optional[dict] = Field(default_factory=dict)
```

### 4.3 Incident

```python
class Incident(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    incident_type: str           # "Medical", "Security", "Logistics"
    zone_name: str
    description: str
    severity: str = "High"       # "Low", "Medium", "High", "Critical"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "Active"       # "Active", "In Progress", "Resolved"
    resolved_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
```

### 4.4 Transaction

```python
class Transaction(BaseModel):
    transaction_id: str
    attendee_id: str
    amount: int
    category: str    # "Food Stall", "Merchandise", "Beverages"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

> **Pydantic v2 note:** `class Config` and `datetime.utcnow()` still work but are deprecated. Prefer `model_config = ConfigDict(populate_by_name=True)` and `datetime.now(timezone.utc)`.

---

## 5. Core Operational Engines

### 5.1 Automated Bottleneck Detection & Alerting

Implemented in `backend/main.py`; zone health is recalculated on each telemetry poll.

- **Sliding window:** check-in logs from the preceding 10 minutes (`t >= now - 600 s`).
- **Bottleneck condition:** a zone gets `capacity_warning: true` when **either** is met:
  1. Net check-ins in the 10-minute window exceed **150 scans**, or
  2. Estimated zone occupancy reaches or exceeds **90%** of designated capacity.
- **Console behavior:** the zone card switches to a red warning state and shows the **DIVERT** button to authorized operators.

### 5.2 Active Crowd Diversion Protocol

- **Trigger:** `POST /api/admin/trigger_diversion` with `source_zone` and `target_zone`.
- **Actions:**
  - Writes an active diversion rule to the database.
  - Dispatches perk notifications (for example discounted items or free Fest Coins) to attendees in the overloaded zone, encouraging movement toward under-capacity zones such as the Artisan Market.
  - Updates staff assignments on field scanners (`frontend/scanner.html`) to manage incoming foot traffic.

### 5.3 Natural-Language Operations Copilot (Gemini API)

- **Wiring:** `frontend/nlp-assistant.js` → `POST /api/admin/nlp_query` in `backend/main.py`.
- **Function:** operators type conversational questions into the top command bar.
- **Example translations:**

| Operator question | What the backend does |
| --- | --- |
| "How many VIPs are in the VIP Lounge right now?" | Aggregation matching `role: "VIP"` against the latest VIP Lounge check-ins |
| "Identify all zones exceeding 80% capacity." | Analyzes recent scan velocity and capacity thresholds, returns overloaded zones |
| "List unresolved medical emergencies." | Queries incidents where `incident_type: "Medical"` and `status: "Active"` |

- **Output:** operational summaries and metric breakdowns shown in the floating assistant drawer.

### 5.4 Live Weather Telemetry

- **Provider:** Open-Meteo REST API (keyless, no auth, CORS-permissive).
- **Endpoint:** `https://api.open-meteo.com/v1/forecast?latitude=29.39&longitude=76.97&current_weather=true`
- **Behavior:** ambient temperature and weather codes update directly on the console, with no backend proxy.

---

## 6. REST API Specification

Interactive documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc). A health check is available at `/api/health`.

### 6.1 Check-in Scan — `POST /scan`

Request:

```json
{
  "attendee_id": "VIP-9021",
  "zone_name": "Main Stage",
  "timestamp": "2026-10-12T14:30:00Z"
}
```

Response `200 OK`:

```json
{
  "status": "success",
  "message": "Check-in logged",
  "zone": "Main Stage",
  "attendee_role": "VIP"
}
```

### 6.2 Admin Telemetry Poll — `GET /api/admin/stats`

Polled every **3000 ms** from `frontend/index.html`.

Response `200 OK`:

```json
{
  "total_attendees": 4812,
  "arrival_rate_3s": 184,
  "crowd_alerts_count": 1,
  "fest_coin_revenue": 9910,
  "weather": { "temperature": 28.4, "condition": "Clear" },
  "zones": {
    "Main Stage": {
      "current_occupancy": 1240,
      "capacity_percentage": 78,
      "capacity_warning": false,
      "recent_scans_10m": 92
    },
    "Cultural Pavilion": {
      "current_occupancy": 1390,
      "capacity_percentage": 96,
      "capacity_warning": true,
      "recent_scans_10m": 168
    }
  },
  "active_incidents": [
    {
      "id": "670982bc4f1a23",
      "type": "Logistics",
      "zone": "Food Court",
      "description": "Stall 4 power fluctuation",
      "timestamp": "2026-10-12T14:28:10Z"
    }
  ],
  "social_friction_alert": false
}
```

### 6.3 NLP Operations Copilot — `POST /api/admin/nlp_query`

Request:

```json
{ "query": "Show crowd distribution across all food dining areas" }
```

Response `200 OK`:

```json
{
  "query": "Show crowd distribution across all food dining areas",
  "answer": "Food Court is currently at 78% capacity with 1,048 attendees. 96 new scans were logged in the past 10 minutes.",
  "structured_data": { "zone": "Food Court", "occupancy": 1048, "percentage": 78 }
}
```

### 6.4 Cashless Transaction — `POST /api/transaction`

Request:

```json
{ "attendee_id": "ATT-3021", "amount": 150, "category": "Food Stall" }
```

Response `200 OK`:

```json
{ "status": "completed", "transaction_id": "TX-994812", "remaining_balance": 850 }
```

### 6.5 Crowd Diversion — `POST /api/admin/trigger_diversion`

Parameters: `source_zone`, `target_zone` (see [section 5.2](#52-active-crowd-diversion-protocol)).

### 6.6 Simulation Teardown — `POST /api/admin/revert_simulation`

Runs `delete_many({"simulated": True})` on `zone_logs`, resets synthetic incident logs, and clears active diversions.

### 6.7 Endpoint Summary

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/scan` | Log an attendee check-in |
| `GET` | `/api/admin/stats` | Aggregated telemetry for the dashboard |
| `POST` | `/api/admin/nlp_query` | Natural-language operations query |
| `POST` | `/api/admin/trigger_diversion` | Redirect crowd between zones |
| `POST` | `/api/admin/revert_simulation` | Remove simulated data |
| `POST` | `/api/transaction` | Record a Fest Coin purchase |
| `GET` | `/api/health` | Health check |
| `GET` | `/docs`, `/redoc` | Interactive API documentation |

---

## 7. Frontend Interfaces

Seven modular glassmorphic pages:

| Page | File | Audience | Key functionality |
| --- | --- | --- | --- |
| Command Center | `frontend/index.html` | Command operators | Live capacity gauges, 3s arrival rates, bottleneck warnings, diversion dispatcher, weather widget |
| Analytics Console | `frontend/analytics.html` | Logistics coordinators | Capacity bar charts, guest movement timelines, real-time export triggers |
| Field Scanner | `frontend/scanner.html` | Gate & security staff | Single-tap badge scanner, live pass verifier, one-click SOS dispatcher (Medical, Security, Logistics) |
| Pass & Attendees | `frontend/attendees.html` | Accreditation team | Searchable guest registry, roles (VIP, General, Organizer), access badges |
| Recharge Portal | `frontend/recharge.html` | Finance & top-up booths | Fest Coin balance check, wallet top-ups, receipt audit trail |
| Admin Controls | `frontend/admin.html` | System administrators | Dataset replay controls, simulated rush triggers, database purge buttons |
| System Settings | `frontend/settings.html` | Tech operations | Bottleneck scan-count thresholds, polling interval tuning, network status |

---

## 8. Installation, Configuration & Execution

### 8.1 Prerequisites

- Python 3.11+
- Node.js v18+ or Bun v1.0+
- MongoDB Atlas instance or local MongoDB 7.0+ *(optional, see [section 9](#9-storage-resilience-in-memory-fallback))*
- Google AI Studio Gemini API key *(required for the NLP copilot)*

### 8.2 Environment Configuration

Create a `.env` file in the project root (or copy `.env.example`):

```env
# Database
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/cultura?retryWrites=true&w=majority
DB_NAME=cultura_festival

# AI Studio
GEMINI_API_KEY=your_gemini_api_key_here

# Server
PORT=8000
HOST=0.0.0.0
SIMULATION_SPEED=1.0
```

| Variable | Description |
| --- | --- |
| `MONGO_URI` | MongoDB connection string. If unset, the in-memory datastore is used. |
| `DB_NAME` | Database name |
| `GEMINI_API_KEY` | Key for the NLP copilot |
| `PORT`, `HOST` | Server bind settings |
| `SIMULATION_SPEED` | Replay speed multiplier for the simulator |

Never commit `.env` to version control.

### 8.3 Backend Setup & Startup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 8.4 Simulation Data Seeding

In a second terminal:

```bash
python backend/seed_real_traffic.py
```

The runner parses `dinofun_checkins.csv`, streams Fest Coin deductions from `kaggle_retail_transactions.csv`, and publishes sentiment posts from `huggingface_sentiment.json`.

### 8.5 Accessing the Interfaces

| Interface | URL |
| --- | --- |
| Admin Command Center | http://localhost:8000/ or http://localhost:8000/frontend/index.html |
| Staff Checkpoint Scanner | http://localhost:8000/frontend/scanner.html |
| Analytics | http://localhost:8000/frontend/analytics.html |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/api/health |

---

## 9. Storage Resilience (In-Memory Fallback)

If the MongoDB URI is not set, or the network is offline, the system automatically switches to a high-throughput in-memory datastore pre-seeded with sample festival data, so the application always starts.

| | MongoDB Atlas | In-memory |
| --- | --- | --- |
| Persistence | Yes | No (lost on restart) |
| Setup | Connection string | None |
| Best for | Staging, production | Local development, demos, offline use |

---

## 10. Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| Data disappears after restart | Running in in-memory mode. Set a valid MongoDB URI. |
| Port already in use | Stop the other process or start Uvicorn with a different `--port`. |
| `ModuleNotFoundError` | Activate the virtual environment and re-run `pip install -r backend/requirements.txt`. |
| MongoDB connection fails | Check the URI, the Atlas IP allow-list, and URL-encode special characters in the password. |
| NLP copilot returns errors | Confirm `GEMINI_API_KEY` is set and valid. |
| Dashboard shows no live data | Run `python backend/seed_real_traffic.py` to start the replay. |
| Swagger UI won't load | Check that the server is running by visiting `/api/health`. |

---

## 11. Contributing & License

1. Fork the repository and create a feature branch.
2. Make changes with clear commit messages.
3. Verify the app starts and the key endpoints respond at `/docs`.
4. Open a pull request describing what changed and why.

**License:** add a `LICENSE` file and state it here.
