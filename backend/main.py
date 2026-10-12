"""
End-to-End Intelligent Event Operating System (PS1 + Live Telemetry)
FastAPI + MongoDB Atlas (motor, via database.db_manager) + Google Gemini + HF sentiment.

Dual-phase "God Mode" backend:
  - Planning Mode: task boards, registration pacing, revenue-loss / budget-burn triage
  - Live Mode:     zone crowd telemetry, Fest Coin economy, SOS incidents
"""
import os
import sys
import re
import json
import random
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

_BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_BASE), ".env"))
load_dotenv(os.path.join(_BASE, ".env"))
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from models import (
    ROLES, ZONES,
    Event, Task, RegistrationMetrics, SentimentPost,
    ZoneStat, PlanningStats, LiveStats, AdminStatsResponse,
    GeneratePlanRequest, NLPQueryRequest, NLPQueryResponse,
    ScanRequest, TransactionRequest, IncidentCreate, DiversionRequest,
    AttendeeCreate, RechargeRequest,
)
from database import db_manager, generate_id, BOTTLENECK_THRESHOLD

try:
    from google import genai
except ImportError:
    genai = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("event_os")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
CAPACITY_THRESHOLD = BOTTLENECK_THRESHOLD  # 150 scans / rolling 10 min
BUDGET_LOSS_RATIO = 0.20
FRICTION_NEG_PCT = 60.0
DEFAULT_TICKET_PRICE = 799.0
DEFAULT_BUDGET = 2500000.0

STATE: Dict[str, Any] = {"current_mode": "planning"}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def strip_json_fence(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned


def clean_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in doc.items():
        out[k] = str(v) if k == "_id" else v
    out["id"] = str(doc.get("id") or doc.get("_id", ""))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 1. HUGGING FACE ROLLING 5-MINUTE VIBE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class VibeEngine:
    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self.pools: Dict[str, List[Dict[str, Any]]] = {"positive": [], "neutral": [], "negative": []}
        self.stream: List[Dict[str, Any]] = []
        self.cooldown_until: Optional[datetime] = None
        self.sources = ["Twitter", "Discord", "Feedback"]
        self._load()

    def _load(self):
        candidates = [
            os.path.join(_BASE, "data", "huggingface_sentiment.json"),
            os.path.join(os.path.dirname(_BASE), "data", "huggingface_sentiment.json"),
            os.path.join(_BASE, "huggingface_sentiment.json"),
            os.path.join(os.path.dirname(_BASE), "huggingface_sentiment.json"),
        ]
        raw: List[Dict[str, Any]] = []
        path = next((p for p in candidates if os.path.exists(p)), None)
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                logger.info(f"Loaded {len(raw)} Hugging Face sentiment posts from {path}.")
            except Exception as e:
                logger.warning(f"Failed to load sentiment dataset ({e}); using templates.")
        if not raw:
            templates = [
                ("Keynote on multi-agent systems was breathtaking!", "positive"),
                ("Check-in took 30 seconds. Super smooth!", "positive"),
                ("Discord mentors are answering super fast.", "positive"),
                ("Heading to the sponsor demo tables.", "neutral"),
                ("Waiting for the 2 PM edge AI workshop.", "neutral"),
                ("WiFi in Section B keeps dropping my SSH session!", "negative"),
                ("Food court queue is 40 minutes long, unacceptable.", "negative"),
                ("Schedule changed with zero warning on Discord!", "negative"),
            ]
            authors = ["@alex_dev", "@priya_codes", "@sam_builds", "@neha_hacks", "@jason_ai"]
            for i in range(300):
                t, l = random.choice(templates)
                raw.append({"id": f"tpl_{i}", "text": t, "label": l, "author": random.choice(authors)})
        for p in raw:
            lbl = str(p.get("label", p.get("sentiment", "neutral"))).lower()
            if lbl in self.pools:
                self.pools[lbl].append(p)
        now = now_utc()
        for _ in range(20):
            self._push(self._pick(0.65, 0.85), now - timedelta(seconds=random.randint(10, self.window_seconds - 20)))

    def _pick(self, pos_cut: float, neu_cut: float) -> Dict[str, Any]:
        r = random.random()
        key = "positive" if r < pos_cut else ("neutral" if r < neu_cut else "negative")
        pool = self.pools[key] or self.pools["positive"] or [{"text": "Great event!", "label": "positive"}]
        base = random.choice(pool)
        return {"text": base.get("text", ""), "sentiment": key, "author": base.get("author") or f"@attendee_{random.randint(10, 99)}"}

    def _push(self, post: Dict[str, Any], ts: Optional[datetime] = None):
        self.stream.insert(0, {
            "id": f"post_{random.randint(100000, 999999)}",
            "text": post["text"],
            "sentiment": post["sentiment"],
            "author": post.get("author", "@attendee"),
            "source": post.get("source") or random.choice(self.sources),
            "timestamp": (ts or now_utc()).isoformat(),
        })

    def _prune(self):
        cutoff = (now_utc() - timedelta(seconds=self.window_seconds)).isoformat()
        self.stream = [p for p in self.stream if p["timestamp"] >= cutoff][:120]
        self.stream.sort(key=lambda p: p["timestamp"], reverse=True)

    def sample_tick(self):
        in_cooldown = self.cooldown_until and now_utc() < self.cooldown_until
        self._push(self._pick(0.85, 0.95) if in_cooldown else self._pick(0.60, 0.80))
        self._prune()

    def inject_spike(self, count: int = 14):
        samples = [
            "Discord is blowing up: schedule shifted 4 hours with no warning!",
            "Registration portal rejecting student credentials, 50 people stuck at the gate!",
            "Security at Gate 2 is confiscating hardware kits!",
            "Power blackout on Main Stage floor, teams lost unsaved code!",
            "Food court queue is insane, nobody is managing the line!",
        ]
        for i in range(count):
            self._push({"text": random.choice(samples), "sentiment": "negative", "author": f"@urgent_hacker_{i + 1}", "source": "Discord"})
        self.cooldown_until = None
        self._prune()

    def clear(self, cooldown_seconds: int = 180):
        self.cooldown_until = now_utc() + timedelta(seconds=cooldown_seconds)
        self.stream = [p for p in self.stream if p["sentiment"] != "negative"]
        for _ in range(6):
            self._push({"text": "Resolved: organisers fixed it fast, great comms!", "sentiment": "positive", "author": "@community_mod", "source": "Discord"})
        self._prune()

    def metrics(self) -> Dict[str, Any]:
        self._prune()
        total = len(self.stream)
        pos = sum(1 for p in self.stream if p["sentiment"] == "positive")
        neu = sum(1 for p in self.stream if p["sentiment"] == "neutral")
        neg = sum(1 for p in self.stream if p["sentiment"] == "negative")
        d = max(1, total)
        neg_pct = round(neg / d * 100.0, 1)
        in_cooldown = bool(self.cooldown_until and now_utc() < self.cooldown_until)
        risk = (not in_cooldown) and total >= 5 and neg_pct > FRICTION_NEG_PCT
        category = None
        if risk:
            blob = " ".join(p["text"].lower() for p in self.stream if p["sentiment"] == "negative")
            if any(k in blob for k in ("schedule", "shift", "delay")):
                category = "Schedule Backlash"
            elif any(k in blob for k in ("registration", "portal", "credential")):
                category = "Registration Friction"
            elif any(k in blob for k in ("queue", "line", "food")):
                category = "Queue & Crowd Friction"
            else:
                category = "Operational Bottleneck"
        return {
            "total_5m": total,
            "positive_count": pos, "neutral_count": neu, "negative_count": neg,
            "positive_pct": round(pos / d * 100.0, 1),
            "neutral_pct": round(neu / d * 100.0, 1),
            "negative_pct": neg_pct,
            "community_friction_risk": risk,
            "friction_category": category,
            "is_cooldown": in_cooldown,
        }

    def feed(self, limit: int = 25) -> List[Dict[str, Any]]:
        return [SentimentPost(**{k: p[k] for k in ("text", "sentiment", "source", "author", "timestamp")}).model_dump() for p in self.stream[:limit]]


vibe = VibeEngine()


# ─────────────────────────────────────────────────────────────────────────────
# 2. GEMINI COPILOT (plan generation, NLP → aggregation, triage)
# ─────────────────────────────────────────────────────────────────────────────
class GeminiCopilot:
    def __init__(self):
        self.client = None
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if key and genai is not None:
            try:
                self.client = genai.Client(api_key=key)
                logger.info("Gemini client initialised.")
            except Exception as e:
                logger.warning(f"Gemini init failed ({e}); deterministic fallbacks active.")
        self._recovery_sig = ""
        self._recovery: Optional[Dict[str, str]] = None

    async def _generate(self, prompt: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(self.client.models.generate_content, model=GEMINI_MODEL, contents=prompt),
                timeout=20,
            )
            return (resp.text or "").strip() if resp else None
        except Exception as e:
            logger.warning(f"Gemini call failed: {e}")
            return None

    # ── Plan generation ──
    async def generate_plan(self, req: GeneratePlanRequest) -> List[Dict[str, Any]]:
        prompt = f"""You are the Operations Copilot of an Intelligent Event Operating System.
Parse the event brief and output EXACTLY 15 actionable tasks, 3 for each role:
Marketing, Partnerships, Operations, Programme, Leadership.

Event: {req.title} | Format: {req.format} | Scale: {req.target_scale} attendees
Ticket price: INR {req.ticket_price} | Total budget: INR {req.total_budget} | Venue: {req.venue}
Brief: {req.objectives or 'Deliver a world-class event with zero operational friction.'}

Each task: "title" (verb-first), "role" (one of the 5), "status" ("Pending"|"In Progress"|"Resolved"),
"is_blocker" (true for 2-3 critical-path tasks), "deadline" (ISO date within 14 days), "description" (one sentence).
Respond ONLY with a JSON array of 15 objects."""
        text = await self._generate(prompt)
        if text:
            try:
                parsed = json.loads(strip_json_fence(text))
                if isinstance(parsed, list) and len(parsed) >= 10:
                    out = []
                    for i, item in enumerate(parsed[:15]):
                        role = item.get("role") if item.get("role") in ROLES else ROLES[i % 5]
                        status = item.get("status") if item.get("status") in ("Pending", "In Progress", "Resolved") else "Pending"
                        task = Task(
                            title=str(item.get("title", f"Execute {role} milestone")),
                            role=role, status=status,
                            is_blocker=bool(item.get("is_blocker", False)) and status != "Resolved",
                            deadline=str(item.get("deadline") or (now_utc() + timedelta(days=i + 2)).isoformat()),
                            description=str(item.get("description", "")),
                        ).model_dump(exclude={"id"})
                        task["_id"] = generate_id()
                        out.append(task)
                    return out
            except Exception as e:
                logger.warning(f"Plan JSON parse failed ({e}); fallback plan used.")
        return self._fallback_plan(req)

    def _fallback_plan(self, req: GeneratePlanRequest) -> List[Dict[str, Any]]:
        blueprint = {
            "Marketing": [
                (f"Launch omnichannel campaign for {req.title}", "Resolved", False),
                ("Activate Discord community AMA series", "In Progress", False),
                ("Push 48-hour referral incentive to lift registration velocity", "Pending", True),
            ],
            "Partnerships": [
                ("Finalise title sponsor contract", "In Progress", True),
                ("Coordinate partner booth hardware logistics", "Pending", False),
                ("Onboard sponsor mentors and judges", "Resolved", False),
            ],
            "Operations": [
                (f"Deploy high-density WiFi for {req.target_scale} devices", "In Progress", True),
                ("Stage NFC check-in kiosks at all gates", "In Progress", False),
                ("Lock catering and hydration allocation", "Pending", False),
            ],
            "Programme": [
                ("Confirm keynote and VIP speaker lineup", "Resolved", False),
                ("Publish problem statements and API docs", "In Progress", False),
                ("Schedule demo day finalist showcase", "Pending", False),
            ],
            "Leadership": [
                ("Approve budget allocation and prize escrow", "Resolved", False),
                ("Establish emergency response matrix", "In Progress", False),
                ("Sign off municipal safety permits", "Pending", False),
            ],
        }
        tasks, i = [], 0
        for role, items in blueprint.items():
            for title, status, blocker in items:
                i += 1
                t = Task(title=title, role=role, status=status, is_blocker=blocker,
                         deadline=(now_utc() + timedelta(days=i)).isoformat(),
                         description=f"{role} deliverable for {req.title} ({req.format}, {req.target_scale} attendees).").model_dump(exclude={"id"})
                t["_id"] = generate_id()
                tasks.append(t)
        return tasks

    # ── NLP → aggregation intent ──
    async def classify_intent(self, query: str, mode: str) -> Dict[str, Any]:
        intents_planning = ["task_blockers", "tasks_by_role", "registration_pacing", "budget_risk", "sentiment"]
        intents_live = ["zone_bottlenecks", "zone_traffic", "fest_coin_revenue", "active_incidents", "sentiment"]
        allowed = intents_planning if mode == "planning" else intents_live
        prompt = f"""You translate plain-English event-ops questions into database aggregation intents.
CURRENT MODE: {mode.upper()} ({'pre-event planning: tasks, blockers, registrations, budget' if mode == 'planning' else 'day-of live ops: zone crowd bottlenecks, Fest Coin revenue, SOS incidents'}).
Allowed intents for this mode: {allowed}
Optional filters: "role" (one of {ROLES}) and "zone" (one of {ZONES}).
Question: "{query}"
Respond ONLY with JSON: {{"intent": "...", "role": null, "zone": null}}"""
        text = await self._generate(prompt)
        if text:
            try:
                data = json.loads(strip_json_fence(text))
                if data.get("intent") in allowed:
                    return data
            except Exception:
                pass
        q = query.lower()
        role = next((r for r in ROLES if r.lower() in q or (r == "Operations" and "ops" in q)), None)
        zone = next((z for z in ZONES if z.lower() in q), None)
        if any(k in q for k in ("sentiment", "vibe", "social", "community")):
            intent = "sentiment"
        elif mode == "planning":
            if "block" in q or "risk" in q and "budget" not in q:
                intent = "task_blockers"
            elif any(k in q for k in ("budget", "revenue", "loss", "burn", "money")):
                intent = "budget_risk"
            elif any(k in q for k in ("registration", "velocity", "signup", "headcount", "pace")):
                intent = "registration_pacing"
            else:
                intent = "tasks_by_role" if role else "task_blockers"
        else:
            if any(k in q for k in ("incident", "sos", "medical", "security", "emergency")):
                intent = "active_incidents"
            elif any(k in q for k in ("revenue", "coin", "sales", "transaction", "money")):
                intent = "fest_coin_revenue"
            elif any(k in q for k in ("bottleneck", "crowd", "capacity", "congest", "divert")):
                intent = "zone_bottlenecks"
            else:
                intent = "zone_traffic"
        return {"intent": intent, "role": role, "zone": zone}

    async def narrate(self, query: str, mode: str, intent: str, data: Any, fallback: str) -> str:
        prompt = f"""You are the Event OS Copilot in {mode.upper()} mode. Answer the organiser's question concisely
(max 90 words, bullet points allowed) using ONLY this aggregated data. Be decisive and actionable.
Question: {query}
Intent: {intent}
Data: {json.dumps(data, default=str)[:3500]}"""
        text = await self._generate(prompt)
        return text or fallback

    # ── Triage: single recovery action ──
    async def recovery_action(self, signals: Dict[str, Any]) -> Optional[Dict[str, str]]:
        active = {k: v for k, v in signals.items() if v.get("active")}
        if not active:
            self._recovery_sig, self._recovery = "", None
            return None
        sig = "|".join(sorted(f"{k}:{v.get('key', '')}" for k, v in active.items()))
        if sig == self._recovery_sig and self._recovery:
            return self._recovery
        prompt = f"""You are the triage brain of an event operating system. Risks are active:
{json.dumps(active, default=str)}
Produce ONE context-aware recovery action that addresses the highest-impact risk first.
Respond ONLY with JSON: {{"title": "<=6 words", "action": "<=45 words, concrete, includes numbers"}}"""
        text = await self._generate(prompt)
        result = None
        if text:
            try:
                parsed = json.loads(strip_json_fence(text))
                if parsed.get("action"):
                    result = {"title": str(parsed.get("title", "Recovery Action")), "action": str(parsed["action"])}
            except Exception:
                result = None
        if not result:
            result = self._fallback_recovery(active)
        self._recovery_sig, self._recovery = sig, result
        return result

    @staticmethod
    def _fallback_recovery(active: Dict[str, Any]) -> Dict[str, str]:
        if "capacity" in active:
            z = active["capacity"]
            return {"title": f"Divert Crowd From {z['zone']}",
                    "action": f"{z['zone']} hit {z['volume']} scans in 10 min (limit {CAPACITY_THRESHOLD}). Push a 50% Fest Coin discount at {z['target']} and redeploy 4 marshals to reroute inflow."}
        if "budget" in active:
            b = active["budget"]
            return {"title": "Launch Registration Recovery Sprint",
                    "action": f"Projected revenue loss INR {b['loss']:,.0f} exceeds 20% of budget. Trigger a 48h referral bonus (+500 Fest Coins), 15% group discount, and reallocate 10% marketing spend to paid student channels."}
        f = active.get("friction", {})
        return {"title": "Deploy Community Response",
                "action": f"Negative sentiment at {f.get('neg_pct', 0)}% ({f.get('category', 'friction')}). Post an official status update on Discord within 10 minutes and assign 2 moderators to reply to every open complaint."}


copilot = GeminiCopilot()


# ─────────────────────────────────────────────────────────────────────────────
# 3. TELEMETRY MATH
# ─────────────────────────────────────────────────────────────────────────────
async def compute_planning() -> Dict[str, Any]:
    event = await db_manager.get_active_event() or {}
    event = clean_doc(event) if event else {}
    ticket_price = float(event.get("ticket_price") or DEFAULT_TICKET_PRICE)
    total_budget = float(event.get("total_budget") or DEFAULT_BUDGET)

    m = await db_manager.get_registration_metrics()
    target = int(m.get("target_registrations", event.get("target_scale", 2500)))
    current = int(m.get("current_registrations", 0))
    velocity = float(m.get("daily_velocity", 0.0))
    days = max(1, int(m.get("days_remaining", 14)))

    projected = int(round(current + velocity * days))
    shortfall = max(0, target - projected)
    loss = round(shortfall * ticket_price, 2)
    required = round(max(0, target - current) / days, 1)
    burn_risk = loss > BUDGET_LOSS_RATIO * total_budget

    reg = RegistrationMetrics(
        target=target, current=current, daily_velocity=velocity, days_remaining=days,
        required_daily_velocity=required, projected_final_headcount=projected,
        projected_revenue_loss=loss, budget_burn_risk=burn_risk,
    )

    tasks = [clean_doc(t) for t in await db_manager.get_tasks()]
    by_role = {r: [t for t in tasks if t.get("role") == r] for r in ROLES}
    planning = PlanningStats(
        event={**event, "ticket_price": ticket_price, "total_budget": total_budget} if event else None,
        registration=reg,
        tasks_by_role=by_role,
        total_tasks=len(tasks),
        resolved_tasks=sum(1 for t in tasks if t.get("status") == "Resolved"),
        blocker_count=sum(1 for t in tasks if t.get("is_blocker") and t.get("status") != "Resolved"),
    )
    return {"model": planning, "total_budget": total_budget, "ticket_price": ticket_price}


async def compute_live() -> Dict[str, Any]:
    raw = await db_manager.get_admin_stats()
    zones = []
    for z in raw.get("zones", []):
        recent = int(z.get("recent_scans", 0))
        zones.append(ZoneStat(
            zone_name=z["zone_name"], recent_scans=recent, total_scans=int(z.get("total_scans", 0)),
            capacity_pct=min(100, round(recent / CAPACITY_THRESHOLD * 100)),
            capacity_warning=recent > CAPACITY_THRESHOLD,
            active_diversion=z.get("active_diversion"),
        ))
    fin = raw.get("financials", {})
    live = LiveStats(
        zones=zones,
        capacity_warning=any(z.capacity_warning for z in zones),
        fest_coin_revenue=int(fin.get("total_revenue", 0)),
        transaction_volume=int(fin.get("transaction_volume", 0)),
        total_inr_recharged=int(fin.get("total_inr_recharged", 0)),
        recent_transactions=fin.get("recent_transactions", []),
        active_incidents=raw.get("active_incidents", []),
        recent_scans=raw.get("recent_logs", []),
        total_attendees=int(raw.get("total_attendees", 0)),
    )
    return {"model": live, "raw": raw}


# ─────────────────────────────────────────────────────────────────────────────
# 4. APP SETUP
# ─────────────────────────────────────────────────────────────────────────────
async def vibe_ticker():
    while True:
        try:
            vibe.sample_tick()
        except Exception as e:
            logger.warning(f"Vibe tick error: {e}")
        await asyncio.sleep(4)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_manager.connect()
    task = asyncio.create_task(vibe_ticker())
    logger.info("Event OS online.")
    yield
    task.cancel()


app = FastAPI(title="Intelligent Event Operating System", version="4.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─────────────────────────────────────────────────────────────────────────────
# 5. PLANNING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/generate_plan")
async def generate_plan(req: GeneratePlanRequest):
    event = Event(
        title=req.title, format=req.format, target_scale=req.target_scale,
        ticket_price=req.ticket_price, total_budget=req.total_budget,
        start_date=req.start_date or (now_utc() + timedelta(days=req.days_remaining)).strftime("%Y-%m-%d"),
        venue=req.venue, objectives=req.objectives, created_at=now_utc().isoformat(),
    ).model_dump(exclude={"id"})
    saved_event = await db_manager.save_event(event)

    tasks = await copilot.generate_plan(req)
    saved_tasks = await db_manager.save_tasks(tasks, clear_existing=True)

    await db_manager.save_registration_metrics({
        "target_registrations": req.target_scale,
        "current_registrations": min(req.current_registrations, req.target_scale),
        "days_remaining": req.days_remaining,
        "daily_velocity": req.daily_velocity,
    })
    planning = (await compute_planning())["model"]
    return {
        "message": f"Generated {len(saved_tasks)} cross-functional tasks for {req.title}.",
        "event": clean_doc(saved_event),
        "tasks_generated": len(saved_tasks),
        "tasks": [clean_doc(t) for t in saved_tasks],
        "registration_metrics": planning.registration.model_dump(),
        "ai_source": "gemini" if copilot.client else "fallback",
    }


@app.patch("/api/tasks/{task_id}/resolve")
async def resolve_task(task_id: str):
    task = await db_manager.resolve_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db_manager.update_registration_progress(added_registrations=12, delta_velocity=1.5)
    return {"message": "Task resolved", "task": clean_doc(task)}


@app.post("/api/admin/simulate_velocity_drop")
async def simulate_velocity_drop():
    m = await db_manager.get_registration_metrics()
    m["daily_velocity"] = round(max(0.0, float(m.get("daily_velocity", 40)) * 0.35), 1)
    await db_manager.save_registration_metrics(m)
    return {"message": "Registration velocity dropped 65% for triage testing.", "daily_velocity": m["daily_velocity"]}


@app.post("/api/admin/execute_recovery_action")
async def execute_recovery_action():
    m = await db_manager.update_registration_progress(added_registrations=80, delta_velocity=25.0)
    vibe.clear()
    return {"message": "Recovery executed: +80 registrations, velocity boosted, community alert cleared.", "registration_metrics": m}


# ─────────────────────────────────────────────────────────────────────────────
# 6. LIVE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
async def resolve_attendee(qr: Optional[str], attendee_id: Optional[str]) -> Dict[str, Any]:
    att = None
    if qr:
        att = await db_manager.get_attendee_by_qr(qr.strip())
    if not att and attendee_id:
        att = await db_manager.get_attendee_by_id(attendee_id.strip())
    if not att:
        raise HTTPException(status_code=404, detail="Attendee not found")
    if att.get("status") == "terminated":
        raise HTTPException(status_code=403, detail="QR pass terminated")
    return att


@app.post("/scan")
async def scan(req: ScanRequest):
    if req.zone_name not in ZONES:
        raise HTTPException(status_code=400, detail=f"Unknown zone. Valid: {ZONES}")
    att = await resolve_attendee(req.qr_code_hash, req.attendee_id)
    log = await db_manager.log_zone_scan(att, req.zone_name)
    return {"message": f"{att.get('name')} checked into {req.zone_name}", "log": clean_doc(log)}


@app.post("/api/transaction")
@app.post("/transaction")
async def transaction(req: TransactionRequest):
    att = await resolve_attendee(req.qr_code_hash, req.attendee_id)
    if int(att.get("fest_coins", 0)) < req.amount:
        raise HTTPException(status_code=402, detail="Insufficient Fest Coins")
    tx = await db_manager.create_transaction(att, req.amount, req.stall_name or req.category, req.zone_name)
    tx["category"] = req.category
    return {"message": "Payment successful", "transaction": clean_doc(tx), "new_balance": int(att.get("fest_coins", 0)) - req.amount}


@app.post("/api/incident")
async def create_incident(req: IncidentCreate):
    inc = await db_manager.create_incident(req.type, req.zone_name, req.description or req.notes or "")
    return {"message": "SOS dispatched", "incident": clean_doc(inc)}


@app.patch("/api/incident/{incident_id}/resolve")
@app.post("/api/incident/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    inc = await db_manager.resolve_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Incident resolved", "incident": clean_doc(inc)}


@app.post("/api/admin/divert")
async def divert(req: DiversionRequest):
    div, relieved = await db_manager.trigger_diversion(req.zone_name, req.target_zone, req.message or "")
    return {"message": f"Diverted {relieved} attendees from {req.zone_name} to {div['target_zone']}.", "diversion": clean_doc(div), "relieved": relieved}


@app.post("/api/admin/simulate_surge")
async def simulate_surge():
    n = await db_manager.simulate_surge()
    return {"message": f"Injected {n} scans into Cultural Pavilion."}


@app.post("/api/admin/revert_surge")
async def revert_surge():
    n = await db_manager.revert_simulation()
    return {"message": f"Reverted {n} simulated scans."}


@app.post("/register_attendee")
@app.post("/api/admin/attendees")
async def register_attendee(req: AttendeeCreate):
    att = await db_manager.create_attendee(req.name, req.role, req.ticket_type, req.initial_coins or 0)
    return {"message": "Attendee registered", "attendee": clean_doc(att)}


@app.get("/api/attendees/search")
@app.get("/api/admin/attendees")
async def list_attendees(q: str = Query("", alias="q"), limit: int = 250):
    return {"attendees": [clean_doc(a) for a in await db_manager.list_attendees(q, limit)]}


@app.get("/api/attendee/{attendee_id}/history")
async def attendee_history(attendee_id: str):
    h = await db_manager.get_attendee_history(attendee_id)
    if not h:
        raise HTTPException(status_code=404, detail="Attendee not found")
    h["attendee"] = clean_doc(h["attendee"])
    for k in ("recharges", "transactions", "scans"):
        h[k] = [clean_doc(x) for x in h[k]]
    return h


@app.post("/api/admin/attendee/{attendee_id}/terminate_qr")
async def terminate_qr(attendee_id: str):
    att = await db_manager.update_attendee(attendee_id, {"status": "terminated", "terminated_at": now_utc().isoformat()})
    if not att:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return {"message": "QR terminated", "attendee": clean_doc(att)}


@app.post("/api/admin/attendee/{attendee_id}/reinstate_qr")
async def reinstate_qr(attendee_id: str):
    att = await db_manager.update_attendee(attendee_id, {"status": "active", "terminated_at": None})
    if not att:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return {"message": "QR reinstated", "attendee": clean_doc(att)}


@app.delete("/api/admin/delete_attendee/{attendee_id}")
@app.post("/api/admin/delete_attendee/{attendee_id}")
async def delete_attendee(attendee_id: str):
    await db_manager.delete_attendee(attendee_id)
    return {"message": "Attendee deleted"}


@app.post("/api/recharge")
async def recharge(req: RechargeRequest):
    att = await resolve_attendee(req.qr_code_hash, req.attendee_id)
    r = await db_manager.create_recharge(att, req.inr_amount, req.payment_method or "UPI",
                                         req.operator_mode or "self_service", req.operator_name, req.notes or "")
    return {"message": "Recharge successful", "recharge": clean_doc(r), "new_balance": int(att.get("fest_coins", 0)) + req.inr_amount}


@app.get("/api/recharges")
async def recharges(limit: int = 100):
    items, summary = await db_manager.get_recharges_summary(limit)
    return {"recharges": [clean_doc(r) for r in items], "summary": summary}


# ─────────────────────────────────────────────────────────────────────────────
# 7. SHARED: SOCIAL, MODE, NLP, MASTER TELEMETRY
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/social/feed")
async def social_feed(limit: int = 40):
    return {"feed": vibe.feed(limit), "metrics": vibe.metrics()}


@app.post("/api/social/simulate_spike")
async def simulate_spike():
    vibe.inject_spike()
    return {"message": "Negative sentiment spike injected.", "metrics": vibe.metrics()}


@app.post("/api/social/clear_alert")
async def clear_alert():
    vibe.clear()
    return {"message": "Community friction alert cleared.", "metrics": vibe.metrics()}


@app.post("/api/admin/mode")
async def set_mode(payload: Dict[str, str]):
    mode = (payload.get("mode") or "").lower()
    if mode not in ("planning", "live"):
        raise HTTPException(status_code=400, detail="mode must be 'planning' or 'live'")
    STATE["current_mode"] = mode
    return {"current_mode": mode}


@app.post("/api/admin/nlp_query", response_model=NLPQueryResponse)
async def nlp_query(req: NLPQueryRequest):
    mode = req.current_mode or STATE["current_mode"]
    plan = await copilot.classify_intent(req.query, mode)
    intent, role, zone = plan.get("intent"), plan.get("role"), plan.get("zone")
    data: Any = {}
    fallback = ""
    count = 0
    metrics: List[Dict[str, Any]] = []

    if intent in ("task_blockers", "tasks_by_role", "registration_pacing", "budget_risk"):
        p = (await compute_planning())["model"]
        tasks = [t for ts in p.tasks_by_role.values() for t in ts]
        if intent == "task_blockers":
            rows = [t for t in tasks if t.get("is_blocker") and t.get("status") != "Resolved" and (not role or t.get("role") == role)]
            data = [{"title": t["title"], "role": t["role"], "status": t["status"]} for t in rows]
            count = len(rows)
            fallback = (f"{count} open blocker(s){' in ' + role if role else ''}:\n" + "\n".join(f"- [{t['role']}] {t['title']} ({t['status']})" for t in rows)) if rows else "No open blockers. Critical path is clear."
        elif intent == "tasks_by_role":
            rows = [t for t in tasks if not role or t.get("role") == role]
            data = [{"title": t["title"], "role": t["role"], "status": t["status"], "is_blocker": t.get("is_blocker")} for t in rows]
            count = len(rows)
            done = sum(1 for t in rows if t["status"] == "Resolved")
            fallback = f"{role or 'All roles'}: {done}/{count} tasks resolved.\n" + "\n".join(f"- {t['title']} ({t['status']})" for t in rows[:8])
        else:
            r = p.registration
            data = r.model_dump()
            count = 1
            fallback = (f"Registrations {r.current}/{r.target} at {r.daily_velocity}/day (need {r.required_daily_velocity}/day). "
                        f"Projected final headcount {r.projected_final_headcount}. Projected revenue loss INR {r.projected_revenue_loss:,.0f}. "
                        f"Budget burn risk: {'YES' if r.budget_burn_risk else 'no'}.")
            metrics = [{"label": "Projected Headcount", "value": str(r.projected_final_headcount)},
                       {"label": "Revenue Loss", "value": f"INR {r.projected_revenue_loss:,.0f}", "alert": r.budget_burn_risk}]
    elif intent in ("zone_bottlenecks", "zone_traffic", "fest_coin_revenue", "active_incidents"):
        l = (await compute_live())["model"]
        if intent in ("zone_bottlenecks", "zone_traffic"):
            rows = [z for z in l.zones if (not zone or z.zone_name == zone) and (intent == "zone_traffic" or z.capacity_warning)]
            data = [z.model_dump(exclude={"active_diversion"}) for z in rows]
            count = len(rows)
            if intent == "zone_bottlenecks":
                fallback = ("Bottlenecks (>150 scans / 10 min):\n" + "\n".join(f"- {z.zone_name}: {z.recent_scans} scans ({z.capacity_pct}%)" for z in rows)) if rows else "No zone bottlenecks. All zones under 150 scans / 10 min."
            else:
                fallback = "Rolling 10-min traffic:\n" + "\n".join(f"- {z.zone_name}: {z.recent_scans} scans{' ⚠' if z.capacity_warning else ''}" for z in rows)
        elif intent == "fest_coin_revenue":
            data = {"fest_coin_revenue": l.fest_coin_revenue, "transactions": l.transaction_volume, "inr_recharged": l.total_inr_recharged}
            count = l.transaction_volume
            fallback = f"Fest Coin revenue: {l.fest_coin_revenue:,} coins across {l.transaction_volume} transactions. INR recharged: ₹{l.total_inr_recharged:,}."
        else:
            rows = [i for i in l.active_incidents if not zone or i.get("zone_name") == zone]
            data = rows
            count = len(rows)
            fallback = (f"{count} active SOS incident(s):\n" + "\n".join(f"- {i.get('type')} @ {i.get('zone_name')}: {i.get('notes')}" for i in rows)) if rows else "No active SOS incidents."
    else:
        s = vibe.metrics()
        data = s
        count = s["total_5m"]
        fallback = f"Community vibe (5 min): {s['positive_pct']}% positive, {s['negative_pct']}% negative across {s['total_5m']} posts. Friction risk: {'YES — ' + str(s['friction_category']) if s['community_friction_risk'] else 'no'}."

    answer = await copilot.narrate(req.query, mode, intent, data, fallback)
    return NLPQueryResponse(query=req.query, answer=answer, response=answer, category=intent,
                            current_mode=mode, result_count=count, metrics=metrics)


@app.get("/api/admin/stats")
async def admin_stats(mode: Optional[str] = Query(None)):
    if mode in ("planning", "live"):
        STATE["current_mode"] = mode
    current_mode = STATE["current_mode"]

    planning_pack, live_pack = await asyncio.gather(compute_planning(), compute_live())
    planning: PlanningStats = planning_pack["model"]
    live: LiveStats = live_pack["model"]
    sentiment = vibe.metrics()
    reg = planning.registration

    hottest = max(live.zones, key=lambda z: z.recent_scans) if live.zones else None
    coolest = min(live.zones, key=lambda z: z.recent_scans) if live.zones else None
    signals = {
        "budget": {"active": reg.budget_burn_risk, "key": int(reg.projected_revenue_loss // 50000),
                   "loss": reg.projected_revenue_loss, "budget": planning_pack["total_budget"],
                   "current": reg.current, "target": reg.target, "velocity": reg.daily_velocity,
                   "required_velocity": reg.required_daily_velocity},
        "capacity": {"active": live.capacity_warning, "key": hottest.zone_name if hottest else "",
                     "zone": hottest.zone_name if hottest else "", "volume": hottest.recent_scans if hottest else 0,
                     "target": coolest.zone_name if coolest else "Food Court"},
        "friction": {"active": sentiment["community_friction_risk"], "key": sentiment["friction_category"] or "",
                     "neg_pct": sentiment["negative_pct"], "category": sentiment["friction_category"]},
    }
    recovery = await copilot.recovery_action(signals)

    payload = AdminStatsResponse(
        current_mode=current_mode,
        planning_stats=planning,
        live_stats=live,
        sentiment_metrics=sentiment,
        social_feed=vibe.feed(20),
        budget_burn_risk=reg.budget_burn_risk,
        capacity_warning=live.capacity_warning,
        community_friction_risk=sentiment["community_friction_risk"],
        friction_category=sentiment["friction_category"],
        recovery_action=recovery["action"] if recovery else None,
        recovery_action_title=recovery["title"] if recovery else None,
        system_status={**db_manager.get_status_summary(), "gemini": bool(copilot.client), "server_time": now_utc().isoformat()},
    ).model_dump()

    # Backward-compatible flat fields for secondary pages (workflows/analytics/copilot/sentiment)
    payload.update({
        "event": planning.event,
        "tasks_by_role": planning.tasks_by_role,
        "total_tasks": planning.total_tasks,
        "resolved_tasks": planning.resolved_tasks,
        "blocker_count": planning.blocker_count,
        "registration_risk": reg.daily_velocity < 0.8 * max(0.1, reg.required_daily_velocity),
        "registration_metrics": {
            "target_registrations": reg.target,
            "current_registrations": reg.current,
            "days_remaining": reg.days_remaining,
            "daily_velocity": reg.daily_velocity,
            "required_daily_velocity": reg.required_daily_velocity,
            "velocity_ratio": round(reg.daily_velocity / max(0.1, reg.required_daily_velocity), 2),
            "reach_gap": max(0, reg.target - reg.projected_final_headcount),
            "projected_final_headcount": reg.projected_final_headcount,
            "projected_revenue_loss": reg.projected_revenue_loss,
        },
        "zones": live_pack["raw"].get("zones", []),
        "recent_logs": live.recent_scans,
        "financials": live_pack["raw"].get("financials", {}),
        "active_incidents": live.active_incidents,
        "friction_alert": sentiment["community_friction_risk"],
    })
    return payload


@app.get("/api/health")
async def health():
    return {"status": "ok", "database": db_manager.get_status_summary(), "gemini": bool(copilot.client),
            "mode": STATE["current_mode"], "version": "4.0.0"}


# ─────────────────────────────────────────────────────────────────────────────
# 8. STATIC FRONTEND
# ─────────────────────────────────────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(_BASE), "frontend")
if not os.path.exists(static_dir):
    static_dir = os.path.join(_BASE, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"), headers=NO_CACHE)


@app.api_route("/{file_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_static(file_path: str):
    if file_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    full = os.path.normpath(os.path.join(static_dir, file_path.strip("/")))
    if not full.startswith(os.path.normpath(static_dir)):
        raise HTTPException(status_code=403, detail="Forbidden")
    if os.path.isfile(full):
        return FileResponse(full, headers=NO_CACHE)
    if os.path.isfile(full + ".html"):
        return FileResponse(full + ".html", headers=NO_CACHE)
    return FileResponse(os.path.join(static_dir, "index.html"), headers=NO_CACHE)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 3000)),
                reload=os.getenv("RELOAD", "false").lower() in ("true", "1", "yes"))
