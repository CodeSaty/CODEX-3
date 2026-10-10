# Cultura Festival Hub - Intelligent Event Command Center

Live festival crowd-management telemetry dashboard, cashless Fest Coin economy, pass checkpoint verification, and emergency incident dispatch.

## Tech Stack

* **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
* **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
* **Data Validation & Schemas**: [Pydantic v2](https://docs.pydantic.dev/)
* **Database & Driver**: [MongoDB Atlas](https://www.mongodb.com/atlas) via official [Motor](https://motor.readthedocs.io/) asynchronous driver (`motor.motor_asyncio.AsyncIOMotorClient`)
* **Resilience**: Zero-downtime high-throughput in-memory reactive fallback if `MONGODB_URI` is omitted
* **Interactive API Playground**: Native Swagger UI at `/docs` and ReDoc at `/redoc`

---

## Quickstart

1. **Install Python dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Configure Environment Variables (Optional):**
   Copy `.env.example` to `.env`:
   ```bash
   # MongoDB Atlas cluster connection string
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/cultura_festival_db?retryWrites=true&w=majority

   # Admin security key
   ADMIN_KEY=TEST-KEY

   # Server port
   PORT=3000
   ```
   *Note: If `MONGODB_URI` is not set or network is offline, the system automatically uses its in-memory datastore with pre-seeded festival data.*

3. **Start the Application:**
   ```bash
   python backend/main.py
   # or
   npm run dev
   ```

4. **Access the Hub:**
   * **Dashboard**: `http://localhost:3000/`
   * **Field Scanner**: `http://localhost:3000/scanner.html`
   * **Cashless Recharge & Wallet**: `http://localhost:3000/recharge.html`
   * **Guest Directory**: `http://localhost:3000/attendees.html`
   * **Live Telemetry & Analytics**: `http://localhost:3000/analytics.html`
   * **Interactive Swagger UI**: `http://localhost:3000/docs`
   * **API Health Check**: `http://localhost:3000/api/health`
