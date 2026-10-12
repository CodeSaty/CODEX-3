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

# Load .env from project root or backend folder
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
load_dotenv()

from fastapi import FastAPI, Request, Response, HTTPException, Header, Depends, Query, Path, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from models import (
    Event, Task, RegistrationMetrics, SentimentPost,
    GeneratePlanRequest, GeneratePlanResponse, TaskResolveResponse,
    NLPQueryRequest, NLPQueryResponse, MetricItem, QuickActionItem,
    AdminStatsResponse, HealthCheckResponse,
    AttendeeCreate, AttendeeResponse, ScanRequest, RechargeRequest, IncidentCreate
)
from database import db_manager, generate_id, generate_qr_hash

# Try importing google-genai
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hackingly.ps1.command_centre")

# Admin Security Key
ADMIN_ACCESS_KEY = os.getenv("ADMIN_KEY", "").strip()

def verify_admin(x_admin_key: Optional[str] = Header(None, alias="x-admin-key")):
    if ADMIN_ACCESS_KEY and x_admin_key and x_admin_key.strip() != ADMIN_ACCESS_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized Access")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 1. LIVE ROLLING 5-MINUTE SENTIMENT & VIBE ENGINE (Hugging Face validation)
# ─────────────────────────────────────────────────────────────────────────────
class RollingSentimentEngine:
    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds  # 5-minute rolling window
        self.raw_posts: List[Dict[str, Any]] = []
        self.positive_pool: List[Dict[str, Any]] = []
        self.neutral_pool: List[Dict[str, Any]] = []
        self.negative_pool: List[Dict[str, Any]] = []
        self.rolling_stream: List[Dict[str, Any]] = []  # Posts in the current 5-min window
        self.cooldown_until: Optional[datetime] = None
        self.community_friction_risk: bool = False
        self.friction_category: Optional[str] = None
        self.sources = ["Twitter", "Discord", "Feedback"]
        self.load_dataset()

    def load_dataset(self):
        paths_to_check = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "huggingface_sentiment.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "huggingface_sentiment.json"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "huggingface_sentiment.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "huggingface_sentiment.json"),
        ]
        chosen_path = next((p for p in paths_to_check if os.path.exists(p)), None)
        if chosen_path:
            try:
                with open(chosen_path, "r", encoding="utf-8") as f:
                    self.raw_posts = json.load(f)
                self._partition_pools()
                logger.info(f"Loaded {len(self.raw_posts)} sentiment posts from {chosen_path}.")
                self._seed_initial_window()
                return
            except Exception as e:
                logger.warning(f"Error loading sentiment JSON ({e}). Falling back to internal templates.")

        # Synthetic fallback templates if file is missing
        templates = [
            ("The keynote presentation on autonomous multi-agent systems was breathtaking!", "positive"),
            ("Super fast badge check-in, walked right into the hackathon arena within 30 seconds.", "positive"),
            ("Discord mentors are answering questions super fast! Loving the developer support.", "positive"),
            ("Catering and snack tables are stacked with energy drinks. Great fuel for late-night hacking!", "positive"),
            ("Heading over to the sponsor demo tables to check out new API bounties.", "neutral"),
            ("Waiting for the 2:00 PM workshop on edge AI inference models.", "neutral"),
            ("WiFi latency in Section B is unbearable, SSH connection keeps dropping! Fix the router!", "negative"),
            ("Registration approval took 48 hours and my team pass is still missing in the portal!", "negative"),
            ("Massive confusion over track submission deadlines! Schedule needs immediate clarification on Discord.", "negative"),
            ("Power strips at table row 8 tripped the breaker, 20 laptop chargers just died!", "negative"),
        ]
        authors = ["@alex_dev", "@priya_coder", "@sam_builds", "@neha_hack", "@jason_ai", "@tanya_ops"]
        self.raw_posts = []
        for i in range(500):
            txt, lbl = random.choice(templates)
            self.raw_posts.append({
                "id": f"post_{10000 + i}",
                "text": txt,
                "label": lbl,
                "author": random.choice(authors),
                "source": random.choice(self.sources)
            })
        self._partition_pools()
        self._seed_initial_window()

    def _partition_pools(self):
        self.positive_pool = [p for p in self.raw_posts if str(p.get("label", "")).lower() == "positive"]
        self.neutral_pool = [p for p in self.raw_posts if str(p.get("label", "")).lower() == "neutral"]
        self.negative_pool = [p for p in self.raw_posts if str(p.get("label", "")).lower() == "negative"]

    def _seed_initial_window(self):
        now = datetime.now(timezone.utc)
        self.rolling_stream = []
        # Prepopulate with 20 balanced posts over the last 4 minutes
        for i in range(20):
            r = random.random()
            if r < 0.65: pool = self.positive_pool or self.raw_posts
            elif r < 0.85: pool = self.neutral_pool or self.raw_posts
            else: pool = self.negative_pool or self.raw_posts

            if not pool: continue
            base = random.choice(pool)
            post_time = now - timedelta(seconds=random.randint(10, self.window_seconds - 20))
            self.rolling_stream.append({
                "id": base.get("id", f"post_{random.randint(1000, 9999)}"),
                "text": base.get("text", "Event attendee update."),
                "sentiment": str(base.get("label", "neutral")).lower(),
                "source": base.get("source") or random.choice(self.sources),
                "author": base.get("author", f"@attendee_{random.randint(10, 99)}"),
                "timestamp": post_time.isoformat()
            })
        self._prune_and_evaluate(now)

    def sample_tick(self, count: int = 1):
        """Samples incoming posts into the rolling window."""
        now = datetime.now(timezone.utc)
        for _ in range(count):
            r = random.random()
            # If in cooldown, suppress negative frequency
            in_cooldown = self.cooldown_until and now < self.cooldown_until
            if in_cooldown:
                pool = self.positive_pool if r < 0.85 else (self.neutral_pool if r < 0.95 else self.negative_pool)
            else:
                pool = self.positive_pool if r < 0.60 else (self.neutral_pool if r < 0.80 else self.negative_pool)

            if not pool: pool = self.raw_posts
            base = random.choice(pool) if pool else {"text": "Great event!", "label": "positive"}
            self.rolling_stream.insert(0, {
                "id": f"post_{random.randint(100000, 999999)}",
                "text": base.get("text", ""),
                "sentiment": str(base.get("label", "neutral")).lower(),
                "source": base.get("source") or random.choice(self.sources),
                "author": base.get("author", f"@attendee_{random.randint(10, 99)}"),
                "timestamp": now.isoformat()
            })
        self._prune_and_evaluate(now)

    def inject_negative_spike(self, count: int = 8):
        """Admin trigger: Injects a burst of negative attendee feedback to test risk triage."""
        now = datetime.now(timezone.utc)
        friction_samples = [
            ("Discord general chat is completely blowing up: schedule shifted 4 hours with zero warning!", "Schedule Backlash"),
            ("Registration portal won't accept student credentials! 50 people stuck at entrance!", "Registration System Friction"),
            ("Security guards at Gate 2 confiscating hackathon hardware kits! Need organizer intervention ASAP!", "Venue & Rule Grievances"),
            ("Power blackout on Main Stage floor! Whole row of teams lost unsaved code!", "Operational Bottleneck"),
            ("Sponsor Discord channel is unmoderated, spammers flooding with phishing links!", "Community Friction"),
        ]
        for i in range(count):
            txt, cat = random.choice(friction_samples)
            self.rolling_stream.insert(0, {
                "id": f"spike_{random.randint(100000, 999999)}",
                "text": txt,
                "sentiment": "negative",
                "source": random.choice(["Discord", "Twitter", "Feedback"]),
                "author": f"@urgent_hacker_{i+1}",
                "timestamp": now.isoformat()
            })
        self.cooldown_until = None
        self._prune_and_evaluate(now)

    def resolve_alert(self, cooldown_seconds: int = 180):
        now = datetime.now(timezone.utc)
        self.cooldown_until = now + timedelta(seconds=cooldown_seconds)
        self.community_friction_risk = False
        self.friction_category = None
        # Add positive reassurance posts to rebalance window
        for _ in range(5):
            pos = random.choice(self.positive_pool) if self.positive_pool else {"text": "All clear!", "label": "positive"}
            self.rolling_stream.insert(0, {
                "id": f"relief_{random.randint(10000, 99999)}",
                "text": f"Resolved: {pos.get('text', 'Everything moving smoothly again!')}",
                "sentiment": "positive",
                "source": "Discord",
                "author": "@community_mod",
                "timestamp": now.isoformat()
            })
        self._prune_and_evaluate(now)

    def _prune_and_evaluate(self, now: datetime):
        cutoff = now - timedelta(seconds=self.window_seconds)
        valid = []
        for p in self.rolling_stream:
            try:
                t_str = p.get("timestamp", "")
                t = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                if t >= cutoff:
                    valid.append(p)
            except Exception:
                valid.append(p)
        self.rolling_stream = valid[:100]  # Cap at 100 recent posts

        total = len(self.rolling_stream)
        if total == 0:
            self.community_friction_risk = False
            self.friction_category = None
            return

        neg_count = sum(1 for p in self.rolling_stream if p.get("sentiment") == "negative")
        neg_pct = (neg_count / total) * 100.0

        in_cooldown = self.cooldown_until and now < self.cooldown_until
        if in_cooldown:
            self.community_friction_risk = False
            self.friction_category = None
        elif neg_pct >= 60.0 and total >= 5:
            self.community_friction_risk = True
            # Determine dominant friction category
            texts = " ".join([p.get("text", "") for p in self.rolling_stream if p.get("sentiment") == "negative"]).lower()
            if "schedule" in texts or "time" in texts or "delay" in texts or "shift" in texts:
                self.friction_category = "Schedule Backlash"
            elif "registration" in texts or "form" in texts or "portal" in texts or "credential" in texts or "ticket" in texts:
                self.friction_category = "Registration System Friction"
            elif "security" in texts or "rule" in texts or "gate" in texts or "confiscat" in texts or "guard" in texts:
                self.friction_category = "Venue & Rule Grievances"
            else:
                self.friction_category = "Operational Bottleneck"
        else:
            self.community_friction_risk = False
            self.friction_category = None

    def get_metrics(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        self._prune_and_evaluate(now)
        total = len(self.rolling_stream)
        pos = sum(1 for p in self.rolling_stream if p.get("sentiment") == "positive")
        neu = sum(1 for p in self.rolling_stream if p.get("sentiment") == "neutral")
        neg = sum(1 for p in self.rolling_stream if p.get("sentiment") == "negative")

        denom = max(1, total)
        return {
            "total_5m": total,
            "positive_count": pos,
            "neutral_count": neu,
            "negative_count": neg,
            "positive_pct": round((pos / denom) * 100.0, 1),
            "neutral_pct": round((neu / denom) * 100.0, 1),
            "negative_pct": round((neg / denom) * 100.0, 1),
            "community_friction_risk": self.community_friction_risk,
            "friction_category": self.friction_category,
            "is_cooldown": bool(self.cooldown_until and now < self.cooldown_until)
        }

sentiment_engine = RollingSentimentEngine(window_seconds=300)


# ─────────────────────────────────────────────────────────────────────────────
# 2. GOOGLE GEMINI NLP COPILOT & RECOVERY ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class GeminiOperationsCopilot:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self.cached_recovery: Optional[Dict[str, Any]] = None
        self.last_risk_signature: str = ""
        self.init_client()

    def init_client(self):
        if self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Google Gemini genai.Client successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client ({e}). Fallback active.")
                self.client = None
        else:
            self.client = None

    async def generate_event_plan(self, brief: str, title: str, format_type: str, scale: int, venue: str) -> List[Dict[str, Any]]:
        """Calls Gemini to parse event brief into 15 structured tasks (3 per role). Fallback if offline."""
        prompt = f"""You are the Google Gemini Operations Copilot for the Hackingly Intelligent Event Command Centre.
Parse the following event brief and output EXACTLY 15 actionable operational tasks evenly distributed across the 5 core roles:
- 3 tasks for 'Marketing'
- 3 tasks for 'Partnerships'
- 3 tasks for 'Operations'
- 3 tasks for 'Programme'
- 3 tasks for 'Leadership'

Event Title: {title}
Event Format: {format_type}
Target Scale: {scale} attendees
Venue: {venue}
Event Brief & Objectives:
{brief}

Requirements for each task:
1. 'title': Clear, actionable verb-first operational task title.
2. 'role': Must be exactly one of: 'Marketing', 'Partnerships', 'Operations', 'Programme', 'Leadership'.
3. 'status': Realistic status ('Pending', 'In Progress', or 'Resolved'). At least 2 tasks should be 'Resolved'.
4. 'is_blocker': Boolean. Mark 2 to 3 critical path tasks as true (e.g. key contract or safety permit), the rest false.
5. 'deadline': An ISO timestamp within 2 to 14 days from now.
6. 'description': Concise operational detail.

Respond ONLY with a valid JSON array of 15 objects matching:
[
  {{
    "title": "Task title",
    "role": "Marketing",
    "status": "In Progress",
    "is_blocker": false,
    "deadline": "2026-11-01T18:00:00Z",
    "description": "Details"
  }}, ...
]"""

        if self.client:
            try:
                # Call Gemini API
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if response and response.text:
                    cleaned = response.text.strip()
                    if cleaned.startswith("```"):
                        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
                        cleaned = re.sub(r"\n?```$", "", cleaned)
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, list) and len(parsed) >= 10:
                        # Normalize and ensure IDs and roles
                        normalized = []
                        roles = ["Marketing", "Partnerships", "Operations", "Programme", "Leadership"]
                        for i, item in enumerate(parsed[:15]):
                            role = item.get("role", roles[i % 5])
                            if role not in roles:
                                role = roles[i % 5]
                            normalized.append({
                                "_id": generate_id(),
                                "title": str(item.get("title", f"Execute {role} Milestone")),
                                "role": role,
                                "status": item.get("status", "In Progress" if i % 2 == 0 else "Pending"),
                                "is_blocker": bool(item.get("is_blocker", False)),
                                "deadline": str(item.get("deadline", (datetime.now(timezone.utc) + timedelta(days=i+2)).isoformat())),
                                "description": str(item.get("description", f"Operational execution step for {role}."))
                            })
                        logger.info(f"Successfully generated {len(normalized)} tasks via Gemini API.")
                        return normalized
            except Exception as e:
                logger.warning(f"Gemini API plan generation failed ({e}). Activating intelligent fallback.")

        # High-Fidelity Domain Fallback Generator (Ensures 15 structured tasks)
        now = datetime.now(timezone.utc)
        fallback_tasks = [
            # Marketing (3)
            {
                "_id": generate_id(),
                "title": f"Launch Omnichannel Campaign for {title}",
                "role": "Marketing",
                "status": "Resolved",
                "is_blocker": False,
                "deadline": (now + timedelta(days=2)).isoformat(),
                "description": f"Target student tech societies, Discord communities, and LinkedIn developers targeting {scale} attendees."
            },
            {
                "_id": generate_id(),
                "title": "Activate Discord Community Hackathon AMA",
                "role": "Marketing",
                "status": "In Progress",
                "is_blocker": False,
                "deadline": (now + timedelta(days=4)).isoformat(),
                "description": "Host live audio AMA on Discord answering hacker team formation, API keys, and logistics."
            },
            {
                "_id": generate_id(),
                "title": "Push 24-Hour Flash Referral Incentive",
                "role": "Marketing",
                "status": "Pending",
                "is_blocker": True,
                "deadline": (now + timedelta(days=5)).isoformat(),
                "description": "Release bonus Fest Coins and premium merch tier for attendees inviting 3+ team builders."
            },
            # Partnerships (3)
            {
                "_id": generate_id(),
                "title": "Finalize Cloud AI Title Sponsor Contract",
                "role": "Partnerships",
                "status": "In Progress",
                "is_blocker": True,
                "deadline": (now + timedelta(days=3)).isoformat(),
                "description": "Secure master sponsorship agreement for GPU compute credits and hackathon track awards."
            },
            {
                "_id": generate_id(),
                "title": "Coordinate Partner Booth Hardware Logistics",
                "role": "Partnerships",
                "status": "Pending",
                "is_blocker": False,
                "deadline": (now + timedelta(days=7)).isoformat(),
                "description": f"Confirm display monitors, power drops, and exhibition banners for {venue}."
            },
            {
                "_id": generate_id(),
                "title": "Sponsor Mentors & Judge Onboarding Call",
                "role": "Partnerships",
                "status": "Resolved",
                "is_blocker": False,
                "deadline": (now + timedelta(days=8)).isoformat(),
                "description": "Distribute evaluation rubric, scoring portals, and mentoring slot schedules."
            },
            # Operations (3)
            {
                "_id": generate_id(),
                "title": "Deploy Gigabit High-Density Venue WiFi",
                "role": "Operations",
                "status": "In Progress",
                "is_blocker": True,
                "deadline": (now + timedelta(days=6)).isoformat(),
                "description": f"Test failover multi-WAN connection and configure dedicated SSID for {scale} simultaneous devices."
            },
            {
                "_id": generate_id(),
                "title": "Setup Digital Badging & NFC Scanner Kiosks",
                "role": "Operations",
                "status": "In Progress",
                "is_blocker": False,
                "deadline": (now + timedelta(days=9)).isoformat(),
                "description": f"Stage 10 high-speed check-in terminals at {venue} to prevent gate bottlenecks."
            },
            {
                "_id": generate_id(),
                "title": "Catering & Midnight Energy Ration Allocation",
                "role": "Operations",
                "status": "Pending",
                "is_blocker": False,
                "deadline": (now + timedelta(days=10)).isoformat(),
                "description": "Confirm meal passes, dietary options, and 24-hour hydration stations across the arena."
            },
            # Programme (3)
            {
                "_id": generate_id(),
                "title": "Lock Opening Keynote & VIP Speaker Lineup",
                "role": "Programme",
                "status": "Resolved",
                "is_blocker": False,
                "deadline": (now + timedelta(days=3)).isoformat(),
                "description": "Reconfirm technical talk abstracts and AV deck specs with AI keynote leaders."
            },
            {
                "_id": generate_id(),
                "title": "Publish Hackathon Problem Statements & API Docs",
                "role": "Programme",
                "status": "In Progress",
                "is_blocker": False,
                "deadline": (now + timedelta(days=5)).isoformat(),
                "description": "Review problem tracks: Generative AI, Intelligent Event Command, and Edge Agents."
            },
            {
                "_id": generate_id(),
                "title": "Schedule Demo Day & Pitch Finalist Showcase",
                "role": "Programme",
                "status": "Pending",
                "is_blocker": False,
                "deadline": (now + timedelta(days=12)).isoformat(),
                "description": "Configure 3-minute hard stop timers and investor evaluation scoring boards."
            },
            # Leadership (3)
            {
                "_id": generate_id(),
                "title": "Approve Budget Allocations & Prize Pool Escrow",
                "role": "Leadership",
                "status": "Resolved",
                "is_blocker": False,
                "deadline": (now + timedelta(days=2)).isoformat(),
                "description": "Verify developer bounty disbursement pipeline and legal disclaimers."
            },
            {
                "_id": generate_id(),
                "title": "Establish Cross-Functional Emergency Response Matrix",
                "role": "Leadership",
                "status": "In Progress",
                "is_blocker": False,
                "deadline": (now + timedelta(days=4)).isoformat(),
                "description": "Designate leads for medical SOS, cyber security incident response, and crowd diversion."
            },
            {
                "_id": generate_id(),
                "title": "Sign Off Municipal Safety Clearance & Permits",
                "role": "Leadership",
                "status": "Pending",
                "is_blocker": False,
                "deadline": (now + timedelta(days=7)).isoformat(),
                "description": "Complete on-site fire department and local governance capacity audits."
            }
        ]
        return fallback_tasks

    async def execute_nlp_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Translates executive plain-English queries into synthesized insights using Gemini."""
        q_low = query.lower()
        event = context.get("event", {})
        tasks = context.get("tasks", [])
        reg_metrics = context.get("registration_metrics", {})
        sentiment_metrics = context.get("sentiment_metrics", {})
        reg_risk = context.get("registration_risk", False)
        fric_risk = context.get("community_friction_risk", False)

        # Categorize
        if any(w in q_low for w in ["blocker", "critical", "blocking", "blocked", "barrier"]):
            category = "blockers"
        elif any(w in q_low for w in ["velocity", "registration", "pacing", "reach", "pace", "attendee", "scale"]):
            category = "velocity"
        elif any(w in q_low for w in ["sentiment", "vibe", "mood", "discord", "twitter", "feedback", "friction", "social"]):
            category = "sentiment"
        elif any(w in q_low for w in ["partner", "sponsor", "contract"]):
            category = "partnerships"
        elif any(w in q_low for w in ["marketing", "campaign", "outreach"]):
            category = "marketing"
        elif any(w in q_low for w in ["operation", "wifi", "badge", "venue", "food"]):
            category = "operations"
        else:
            category = "executive"

        # Build fallback / deterministic summary first
        blockers = [t for t in tasks if t.get("is_blocker")]
        resolved = [t for t in tasks if t.get("status") == "Resolved"]
        pending = [t for t in tasks if t.get("status") != "Resolved"]

        target_reg = reg_metrics.get("target_registrations", 2500)
        curr_reg = reg_metrics.get("current_registrations", 1620)
        days_rem = reg_metrics.get("days_remaining", 14)
        daily_vel = reg_metrics.get("daily_velocity", 42.5)
        req_vel = reg_metrics.get("required_daily_velocity", 62.8)
        vel_pct = reg_metrics.get("velocity_ratio", 0.68) * 100.0

        metrics_pills: List[MetricItem] = [
            MetricItem(label="Total Tasks", value=f"{len(tasks)} (5 Roles)"),
            MetricItem(label="Critical Blockers", value=f"{len(blockers)} Active", alert=len(blockers) > 0),
            MetricItem(label="Reg Velocity", value=f"{daily_vel}/day ({vel_pct:.0f}% Pace)", alert=reg_risk),
            MetricItem(label="Community Mood", value=f"{sentiment_metrics.get('positive_pct', 70)}% Positive", alert=fric_risk)
        ]

        quick_actions: List[QuickActionItem] = []
        if blockers:
            quick_actions.append(QuickActionItem(label="Inspect Blockers", action="scroll_blockers"))
        if reg_risk:
            quick_actions.append(QuickActionItem(label="Trigger Velocity Boost", action="execute_recovery"))
        if fric_risk:
            quick_actions.append(QuickActionItem(label="Clear Friction Alert", action="clear_friction"))

        # Base default calculated answer
        if category == "blockers":
            if blockers:
                b_titles = "; ".join([f"**{b.get('title')}** ({b.get('role')})" for b in blockers])
                answer = f"Found **{len(blockers)} critical blocker(s)** in the command pipeline: {b_titles}. Resolving these unlocks downstream execution across {', '.join(set(b.get('role') for b in blockers))}."
            else:
                answer = "All clear! Zero critical blockers detected across Marketing, Partnerships, Operations, Programme, and Leadership."
        elif category == "velocity":
            risk_text = "⚠️ **Registration Risk ACTIVE**: Daily run rate is pacing below 80% of target." if reg_risk else "✅ **Velocity Nominal**: Pacing on schedule."
            answer = f"{risk_text} Current registrations stand at **{curr_reg:,} / {target_reg:,}** with {days_rem} days remaining. Pacing at **{daily_vel:.1f}/day** vs required **{req_vel:.1f}/day** ({vel_pct:.1f}% pace)."
        elif category == "sentiment":
            mood = "CRITICAL FRICTION" if fric_risk else "HEALTHY"
            answer = f"Rolling 5-minute sentiment is **{mood}**: {sentiment_metrics.get('positive_pct')}% Positive, {sentiment_metrics.get('neutral_pct')}% Neutral, and {sentiment_metrics.get('negative_pct')}% Negative across {sentiment_metrics.get('total_5m')} live posts. "
            if fric_risk:
                answer += f"🚨 **Friction Risk Detected**: Category: *{sentiment_metrics.get('friction_category')}*. Urgent community outreach recommended."
            else:
                answer += "Community buzz across Discord and Twitter is nominal with strong excitement."
        else:
            answer = f"Executive Command Summary for **{event.get('title', 'Event')}**: {len(resolved)}/{len(tasks)} tasks resolved. Active blockers: {len(blockers)}. Registration pacing at {vel_pct:.0f}% with audience sentiment at {sentiment_metrics.get('positive_pct')}% positive."

        # If Gemini client is available, refine and enhance the answer
        if self.client:
            try:
                gemini_prompt = f"""You are the Executive NLP Operations Copilot for the Hackingly Intelligent Event Command Centre.
The Event Director asked: "{query}"

Real-Time Telemetry Context:
- Event: {event.get('title', 'Summit')} ({event.get('format', 'Hybrid')} | Target: {target_reg} | Venue: {event.get('venue')})
- Tasks: {len(tasks)} total across 5 roles ({len(resolved)} resolved, {len(pending)} pending)
- Critical Blockers ({len(blockers)}): {[b.get('title') + ' (' + b.get('role') + ')' for b in blockers]}
- Registration Metrics: Current {curr_reg} / Target {target_reg} | Days left: {days_rem} | Pacing: {daily_vel}/day (Required: {req_vel}/day, {vel_pct:.1f}% pace) | Reg Risk: {reg_risk}
- Live Sentiment (Rolling 5m): {sentiment_metrics.get('positive_pct')}% Pos, {sentiment_metrics.get('negative_pct')}% Neg | Friction Risk: {fric_risk} (Category: {sentiment_metrics.get('friction_category')})
- Base Calculation: "{answer}"

Instructions:
Provide a crisp, authoritative executive briefing answering the director's query in 2 to 3 sentences formatted with bold highlights. Suggest the single most impactful immediate action."""

                res = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=gemini_prompt
                )
                if res and res.text:
                    answer = res.text.strip()
            except Exception as e:
                logger.debug(f"Gemini API copilot query fallback: {e}")

        return {
            "query": query,
            "response": answer,
            "answer": answer,
            "category": category,
            "metrics": metrics_pills,
            "quick_actions": quick_actions,
            "result_count": len(blockers) if category == "blockers" else len(tasks)
        }

    async def get_recovery_recommendation(self, reg_risk: bool, fric_risk: bool, fric_category: Optional[str], reg_gap: int) -> Dict[str, str]:
        """Synthesizes concrete recovery action using Gemini when risks are detected."""
        if not reg_risk and not fric_risk:
            return {
                "action": "All operational indicators within nominal thresholds. Maintain current campaign execution.",
                "title": "Nominal Pacing",
                "type": "nominal"
            }

        risk_sig = f"{reg_risk}_{fric_risk}_{fric_category}_{reg_gap}"
        if self.cached_recovery and self.last_risk_signature == risk_sig:
            return self.cached_recovery

        # Rule-based default
        if reg_risk and fric_risk:
            title = "Dual Risk: Velocity Lag & Community Friction"
            action = f"Friction drop ({fric_category}) compounding registration lag. Release Discord FAQ addressing rules immediately, and launch 24-hr referral bonus to recover {reg_gap} attendee pace deficit."
            action_type = "critical_dual"
        elif reg_risk:
            title = "Velocity Lag Recovery"
            action = f"Pacing lag detected ({reg_gap} registrations behind target). Launch 24-hr peer referral incentive offering 500 bonus Fest Coins and priority VIP hackathon workspace."
            action_type = "velocity_boost"
        else:
            title = f"Community Sentiment Recovery: {fric_category}"
            action = f"Negative feedback spiked above 60% due to {fric_category}. Deploy community manager response on Discord and publish transparent organizer clarification."
            action_type = "friction_mitigation"

        if self.client:
            try:
                rec_prompt = f"""You are the Google Gemini Event Risk Recovery Engine.
The event command centre has detected operational risk:
- Registration Risk: {reg_risk} (Lagging behind target by ~{reg_gap} registrations)
- Community Sentiment Risk: {fric_risk} (Category: {fric_category}, Negative sentiment > 60%)

Formulate a single concrete, decisive 1-sentence recovery action that the event director can trigger immediately with one click.
Also provide a 3-word action title."""

                res = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=rec_prompt
                )
                if res and res.text:
                    lines = [l.strip() for l in res.text.strip().split("\n") if l.strip()]
                    if len(lines) >= 1:
                        action = lines[0]
            except Exception as e:
                logger.debug(f"Gemini recovery recommendation fallback: {e}")

        result = {
            "action": action,
            "title": title,
            "type": action_type
        }
        self.cached_recovery = result
        self.last_risk_signature = risk_sig
        return result

copilot = GeminiOperationsCopilot()


# ─────────────────────────────────────────────────────────────────────────────
# 3. BACKGROUND SIMULATION RUNNERS
# ─────────────────────────────────────────────────────────────────────────────
async def social_stream_tick_loop():
    """Simulates realistic incoming social listening traffic every 3 seconds."""
    while True:
        try:
            await asyncio.sleep(3.0)
            sentiment_engine.sample_tick(count=1)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Error in social stream tick loop: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. FASTAPI APP LIFECYCLE & INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Hackingly Intelligent Event Command Centre...")
    await db_manager.connect()
    sentiment_engine.load_dataset()
    copilot.init_client()
    task = asyncio.create_task(social_stream_tick_loop())
    yield
    task.cancel()
    logger.info("Command Centre shutting down.")

app = FastAPI(
    title="Hackingly Intelligent Event Command Centre (PS1)",
    description="Full-stack Event Operations Command Centre powered by Google Gemini NLP Copilot, MongoDB Atlas, and Hugging Face Sentiment Analyzer.",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# 5. CORE API ENDPOINTS (PHASES 1 & 2)
# ─────────────────────────────────────────────────────────────────────────────

# PHASE 2.1: Intelligent Event Setup
@app.post("/api/generate_plan", response_model=GeneratePlanResponse, tags=["Event Setup"])
async def generate_plan_endpoint(payload: GeneratePlanRequest):
    """Parses event brief using Gemini API into 15 actionable tasks (3 per role) and initializes MongoDB Atlas."""
    title = payload.title or "Hackingly AI Innovations Summit 2026"
    format_type = payload.format or "Hybrid"
    target_scale = payload.target_scale or 2500
    venue = payload.venue or "Cyber Arena & Virtual Metaverse"
    objectives = payload.objectives or "Deliver autonomous event operations with Gemini NLP copilot, live sentiment triage, and zero registration friction."
    start_date = payload.start_date or (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d")

    # 1. Save Event
    event_dict = {
        "_id": generate_id(),
        "title": title,
        "format": format_type,
        "target_scale": target_scale,
        "start_date": start_date,
        "venue": venue,
        "objectives": objectives,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    saved_event = await db_manager.save_event(event_dict)

    # 2. Call Gemini Copilot to generate 15 tasks
    tasks = await copilot.generate_event_plan(
        brief=objectives,
        title=title,
        format_type=format_type,
        scale=target_scale,
        venue=venue
    )
    saved_tasks = await db_manager.save_tasks(tasks, clear_existing=True)

    # 3. Initialize RegistrationMetrics
    initial_current = int(target_scale * random.uniform(0.55, 0.70))
    days_left = 14
    daily_vel = round((initial_current / 16.0), 1)
    metrics_dict = {
        "target_registrations": target_scale,
        "current_registrations": initial_current,
        "days_remaining": days_left,
        "daily_velocity": daily_vel
    }
    saved_metrics = await db_manager.save_registration_metrics(metrics_dict)

    return {
        "message": f"Successfully initialized operating plan for '{title}' with 15 role-wise tasks!",
        "event": saved_event,
        "tasks_generated": len(saved_tasks),
        "tasks": saved_tasks,
        "registration_metrics": saved_metrics
    }


# PHASE 2.2: Executive NLP Copilot
@app.post("/api/admin/nlp_query", response_model=NLPQueryResponse, tags=["AI Command Assistant"])
async def executive_nlp_query_endpoint(payload: NLPQueryRequest):
    """Executes conversational plain-English queries against MongoDB state using Gemini."""
    event = await db_manager.get_active_event()
    tasks = await db_manager.get_tasks()
    reg_raw = await db_manager.get_registration_metrics()
    sent_metrics = sentiment_engine.get_metrics()

    # Compute velocity metrics
    target_reg = reg_raw.get("target_registrations", 2500)
    curr_reg = reg_raw.get("current_registrations", 1620)
    days_rem = max(1, reg_raw.get("days_remaining", 14))
    daily_vel = reg_raw.get("daily_velocity", 42.5)
    req_vel = round((target_reg - curr_reg) / days_rem, 1)
    vel_ratio = round(daily_vel / max(0.01, req_vel), 2)
    reg_risk = daily_vel < (0.8 * req_vel)

    reg_metrics = {
        **reg_raw,
        "required_daily_velocity": req_vel,
        "velocity_ratio": vel_ratio,
        "registration_risk": reg_risk,
        "reach_gap": max(0, int(round((0.8 * req_vel - daily_vel) * days_rem)))
    }

    context = {
        "event": event,
        "tasks": tasks,
        "registration_metrics": reg_metrics,
        "sentiment_metrics": sent_metrics,
        "registration_risk": reg_risk,
        "community_friction_risk": sent_metrics["community_friction_risk"]
    }

    result = await copilot.execute_nlp_query(payload.query, context)
    return result


# PHASE 2.3: Live Community Sentiment & Vibe Engine Endpoints
@app.get("/api/social/feed", tags=["Community Sentiment"])
async def get_social_feed_endpoint():
    """Returns rolling 5-minute social listening feed and real-time vibe metrics."""
    metrics = sentiment_engine.get_metrics()
    feed_items = sentiment_engine.rolling_stream[:30]
    return {
        "feed": feed_items,
        "metrics": metrics,
        "community_friction_risk": metrics["community_friction_risk"],
        "friction_category": metrics["friction_category"],
    }

@app.post("/api/social/simulate_spike", tags=["Community Sentiment"])
async def simulate_sentiment_spike_endpoint():
    """Simulates a sudden negative feedback surge to test automated friction triage."""
    sentiment_engine.inject_negative_spike(count=8)
    metrics = sentiment_engine.get_metrics()
    return {
        "message": "Simulated negative sentiment spike injected! Community Friction Alert is now ACTIVE.",
        "metrics": metrics
    }

@app.post("/api/social/clear_alert", tags=["Community Sentiment"])
async def clear_sentiment_alert_endpoint():
    """Resolves friction alert and establishes 3-minute operational cooldown."""
    sentiment_engine.resolve_alert(cooldown_seconds=180)
    metrics = sentiment_engine.get_metrics()
    return {
        "message": "Community Friction Alert cleared! Cooldown initiated.",
        "metrics": metrics
    }


# PHASE 2.4: Risk Calculation & Live Stats Engine (Polled every 3s)
@app.get("/api/admin/stats", tags=["Command Telemetry"])
async def get_admin_stats_endpoint():
    """Consolidated command telemetry polled every 3s by frontend."""
    event = await db_manager.get_active_event()
    tasks = await db_manager.get_tasks()
    reg_raw = await db_manager.get_registration_metrics()
    sent_metrics = sentiment_engine.get_metrics()

    # Calculate Registration Velocity
    target_reg = reg_raw.get("target_registrations", 2500)
    curr_reg = reg_raw.get("current_registrations", 1620)
    days_rem = max(1, reg_raw.get("days_remaining", 14))
    daily_vel = reg_raw.get("daily_velocity", 42.5)
    req_vel = round((target_reg - curr_reg) / days_rem, 1)
    vel_ratio = round(daily_vel / max(0.01, req_vel), 2)
    reg_risk = daily_vel < (0.8 * req_vel)
    reach_gap = max(0, int(round((0.8 * req_vel - daily_vel) * days_rem)))

    reg_metrics = {
        "target_registrations": target_reg,
        "current_registrations": curr_reg,
        "days_remaining": days_rem,
        "daily_velocity": daily_vel,
        "required_daily_velocity": req_vel,
        "velocity_ratio": vel_ratio,
        "registration_risk": reg_risk,
        "reach_gap": reach_gap
    }

    fric_risk = sent_metrics["community_friction_risk"]
    fric_cat = sent_metrics["friction_category"]

    # Generate Recovery Action via Gemini
    recovery = await copilot.get_recovery_recommendation(
        reg_risk=reg_risk,
        fric_risk=fric_risk,
        fric_category=fric_cat,
        reg_gap=reach_gap
    )

    # Group tasks by role
    roles = ["Marketing", "Partnerships", "Operations", "Programme", "Leadership"]
    tasks_by_role: Dict[str, List[Dict[str, Any]]] = {r: [] for r in roles}
    blocker_count = 0
    resolved_count = 0

    for t in tasks:
        r = t.get("role", "Operations")
        if r not in tasks_by_role:
            tasks_by_role[r] = []
        tasks_by_role[r].append(t)
        if t.get("is_blocker"):
            blocker_count += 1
        if t.get("status") == "Resolved":
            resolved_count += 1

    return {
        "event": event,
        "registration_metrics": reg_metrics,
        "registration_risk": reg_risk,
        "community_friction_risk": fric_risk,
        "friction_category": fric_cat,
        "recovery_action": recovery.get("action"),
        "recovery_action_title": recovery.get("title"),
        "recovery_action_type": recovery.get("type"),
        "sentiment_metrics": sent_metrics,
        "tasks_by_role": tasks_by_role,
        "blocker_count": blocker_count,
        "total_tasks": len(tasks),
        "resolved_tasks": resolved_count,
        "system_status": {
            "mongodb_atlas": db_manager.is_connected_to_atlas,
            "gemini_copilot": bool(copilot.client),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }


# PHASE 2.5: Task Resolution & One-Click Recovery Action
@app.patch("/api/tasks/{task_id}/resolve", response_model=TaskResolveResponse, tags=["Workflow Tasks"])
@app.post("/api/tasks/{task_id}/resolve", response_model=TaskResolveResponse, tags=["Workflow Tasks"])
async def resolve_task_endpoint(task_id: str):
    """Marks a task as Resolved, clearing blocker state and recalculating risks immediately."""
    updated = await db_manager.resolve_task(task_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")

    # If resolving a blocker task, boost registration velocity slightly
    if updated.get("role") in ["Marketing", "Partnerships"]:
        await db_manager.update_registration_progress(added_registrations=25, delta_velocity=2.5)

    stats = await get_admin_stats_endpoint()
    return {
        "message": f"Task '{updated.get('title')}' successfully marked as Resolved!",
        "task": updated,
        "registration_risk": stats["registration_risk"],
        "community_friction_risk": stats["community_friction_risk"],
        "recovery_action": stats["recovery_action"]
    }

@app.post("/api/admin/execute_recovery_action", tags=["Command Telemetry"])
async def execute_recovery_action_endpoint():
    """One-click resolution of the AI recommended recovery action from the Risk Banner."""
    sent_metrics = sentiment_engine.get_metrics()
    reg_raw = await db_manager.get_registration_metrics()

    # 1. Clear any friction alert
    if sent_metrics["community_friction_risk"]:
        sentiment_engine.resolve_alert(cooldown_seconds=180)

    # 2. Boost velocity to alleviate registration risk
    target = reg_raw.get("target_registrations", 2500)
    current = reg_raw.get("current_registrations", 1620)
    days = max(1, reg_raw.get("days_remaining", 14))
    needed_vel = round((target - current) / days, 1)

    # Set velocity comfortably at 85% of target to clear risk
    new_vel = round(needed_vel * 0.90, 1)
    await db_manager.update_registration_progress(added_registrations=80, delta_velocity=(new_vel - reg_raw.get("daily_velocity", 40.0)))

    # Also resolve any pending blocker in Marketing or Partnerships
    tasks = await db_manager.get_tasks()
    for t in tasks:
        if t.get("is_blocker") and t.get("role") in ["Marketing", "Partnerships"]:
            await db_manager.resolve_task(t.get("_id") or t.get("id"))
            break

    return {
        "message": "⚡ AI Recovery Action executed! Community friction cleared and registration referral boost activated (+80 attendees, daily velocity restored)."
    }


# System Health
@app.get("/api/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check_endpoint():
    db_summary = db_manager.get_status_summary()
    return {
        "status": "healthy",
        "database_status": db_summary["connection_message"],
        "database_uri_configured": db_summary["database_uri_configured"],
        "gemini_ai_copilot": "Google Gemini 2.5 Flash SDK Active" if copilot.client else "Autonomous AI Copilot Engine Active",
        "sentiment_analyzer": "Hugging Face 5-Minute Rolling Vibe Engine Active",
        "version": "3.0.0"
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. STATIC FRONTEND SERVING
# ─────────────────────────────────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(os.path.dirname(base_dir), "frontend")
if not os.path.exists(static_dir):
    static_dir = os.path.join(base_dir, "static")
if not os.path.exists(static_dir):
    static_dir = os.path.join(os.path.dirname(base_dir), "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"), headers=NO_CACHE_HEADERS)

@app.api_route("/admin.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_admin():
    return FileResponse(os.path.join(static_dir, "index.html"), headers=NO_CACHE_HEADERS)

@app.api_route("/{file_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_static_fallback(file_path: str):
    clean_path = file_path.strip("/")
    full_path = os.path.join(static_dir, clean_path)

    if os.path.isfile(full_path):
        return FileResponse(full_path, headers=NO_CACHE_HEADERS)

    # Check with .html appended (e.g. /workflows -> frontend/workflows.html)
    html_path = full_path + ".html"
    if os.path.isfile(html_path):
        return FileResponse(html_path, headers=NO_CACHE_HEADERS)

    return FileResponse(os.path.join(static_dir, "index.html"), headers=NO_CACHE_HEADERS)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    host = os.getenv("HOST", "127.0.0.1")
    reload_mode = os.getenv("RELOAD", "false").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host=host, port=port, reload=reload_mode)
