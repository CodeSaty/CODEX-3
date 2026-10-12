"""
Unified data models for the End-to-End Intelligent Event Operating System.
Planning Mode (pre-event) + Live Mode (day-of telemetry) + shared AI models.
Pydantic v2 syntax throughout.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field

ROLES = ["Marketing", "Partnerships", "Operations", "Programme", "Leadership"]
ZONES = ["Main Stage", "Food Court", "Artisan Market", "Cultural Pavilion", "VIP Lounge"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. PLANNING MODELS
# ─────────────────────────────────────────────────────────────────────────────
class Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id")
    title: str = Field("Hackingly AI Tech Summit 2026")
    format: Literal["In-person", "Hybrid", "Virtual"] = "Hybrid"
    target_scale: int = Field(2500, ge=1)
    ticket_price: float = Field(799.0, ge=0, description="Ticket price in INR")
    total_budget: float = Field(2500000.0, ge=0, description="Total event budget in INR")
    start_date: Optional[str] = None
    venue: Optional[str] = "Cyber Arena & Metaverse Campus"
    objectives: Optional[str] = None
    created_at: Optional[str] = None


class Task(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id")
    title: str
    role: str = Field(..., description="Marketing | Partnerships | Operations | Programme | Leadership")
    status: Literal["Pending", "In Progress", "Resolved"] = "Pending"
    is_blocker: bool = False
    deadline: Optional[str] = None
    description: Optional[str] = None
    resolved_at: Optional[str] = None


class RegistrationMetrics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target: int = 2500
    current: int = 1620
    daily_velocity: float = 42.5
    days_remaining: int = 14
    required_daily_velocity: float = 0.0
    projected_final_headcount: int = 0
    projected_revenue_loss: float = 0.0
    budget_burn_risk: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# 2. LIVE MODELS
# ─────────────────────────────────────────────────────────────────────────────
class ZoneLog(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id")
    attendee_id: str
    zone_name: str
    timestamp: str


class Transaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: Optional[str] = Field(None, alias="_id")
    amount: int = Field(..., gt=0)
    category: str = "Food & Beverage"


class Incident(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id")
    type: Literal["Medical", "Security", "Logistics"] = "Medical"
    zone_name: str = "Main Stage"
    description: str = ""
    status: Literal["Active", "Resolved"] = "Active"


# ─────────────────────────────────────────────────────────────────────────────
# 3. SHARED / AI MODELS
# ─────────────────────────────────────────────────────────────────────────────
class SentimentPost(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    source: Optional[str] = "Twitter"
    author: Optional[str] = "@attendee"
    timestamp: Optional[str] = None


class ZoneStat(BaseModel):
    zone_name: str
    recent_scans: int
    total_scans: int
    capacity_pct: int
    capacity_warning: bool
    active_diversion: Optional[Dict[str, Any]] = None


class PlanningStats(BaseModel):
    event: Optional[Dict[str, Any]] = None
    registration: RegistrationMetrics
    tasks_by_role: Dict[str, List[Dict[str, Any]]]
    total_tasks: int
    resolved_tasks: int
    blocker_count: int


class LiveStats(BaseModel):
    zones: List[ZoneStat]
    capacity_warning: bool
    fest_coin_revenue: int
    transaction_volume: int
    total_inr_recharged: int
    recent_transactions: List[Dict[str, Any]] = []
    active_incidents: List[Dict[str, Any]] = []
    recent_scans: List[Dict[str, Any]] = []
    total_attendees: int = 0


class AdminStatsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    current_mode: Literal["planning", "live"] = "planning"
    planning_stats: PlanningStats
    live_stats: LiveStats
    sentiment_metrics: Dict[str, Any]
    social_feed: List[Dict[str, Any]] = []
    budget_burn_risk: bool = False
    capacity_warning: bool = False
    community_friction_risk: bool = False
    friction_category: Optional[str] = None
    recovery_action: Optional[str] = None
    recovery_action_title: Optional[str] = None
    system_status: Dict[str, Any] = {}


# ─────────────────────────────────────────────────────────────────────────────
# 4. REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────
class GeneratePlanRequest(BaseModel):
    title: str = "Hackingly AI Tech Summit 2026"
    format: Literal["In-person", "Hybrid", "Virtual"] = "Hybrid"
    target_scale: int = Field(2500, ge=1)
    ticket_price: float = Field(799.0, ge=0)
    total_budget: float = Field(2500000.0, ge=0)
    days_remaining: int = Field(14, ge=1)
    current_registrations: int = Field(1200, ge=0)
    daily_velocity: float = Field(40.0, ge=0)
    start_date: Optional[str] = None
    venue: Optional[str] = "Cyber Arena & Metaverse Campus"
    objectives: Optional[str] = None


class NLPQueryRequest(BaseModel):
    query: str
    current_mode: Literal["planning", "live"] = "planning"


class NLPQueryResponse(BaseModel):
    query: str
    answer: str
    response: str
    category: str
    current_mode: str
    result_count: int = 0
    metrics: List[Dict[str, Any]] = []


class ScanRequest(BaseModel):
    qr_code_hash: Optional[str] = None
    attendee_id: Optional[str] = None
    zone_name: str = "Main Stage"


class TransactionRequest(BaseModel):
    qr_code_hash: Optional[str] = None
    attendee_id: Optional[str] = None
    amount: int = Field(..., gt=0)
    category: str = "Food & Beverage"
    stall_name: Optional[str] = None
    zone_name: str = "Food Court"


class IncidentCreate(BaseModel):
    type: Literal["Medical", "Security", "Logistics"] = "Medical"
    zone_name: str = "Main Stage"
    description: Optional[str] = None
    notes: Optional[str] = None


class DiversionRequest(BaseModel):
    zone_name: str
    target_zone: str = "Food Court"
    message: Optional[str] = None


class AttendeeCreate(BaseModel):
    name: str
    role: str = "General"
    ticket_type: str = "Standard"
    initial_coins: Optional[int] = 1000


class RechargeRequest(BaseModel):
    attendee_id: Optional[str] = None
    qr_code_hash: Optional[str] = None
    inr_amount: int = Field(..., gt=0)
    payment_method: Optional[str] = "UPI"
    operator_mode: Optional[str] = "self_service"
    operator_name: Optional[str] = None
    notes: Optional[str] = ""
