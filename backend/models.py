from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# 1. HACKATHON PS1 COMMAND CENTRE CORE MODELS
# ─────────────────────────────────────────────────────────────────────────────

class Event(BaseModel):
    id: Optional[str] = Field(None, alias="_id", description="Unique Event identifier")
    title: str = Field(..., description="Event Title", example="Hackingly AI Tech Summit 2026")
    format: str = Field("Hybrid", description="Event Format: In-person, Hybrid, or Virtual", example="Hybrid")
    target_scale: int = Field(2500, description="Target attendee capacity / scale", example=2500)
    start_date: str = Field(..., description="Event Start Date (ISO or string)", example="2026-11-15")
    venue: str = Field(..., description="Venue name or physical/virtual platform", example="Cyber Arena & Spatial Hub")
    objectives: str = Field(..., description="Primary objectives and goals of the event", example="Unite 2,500 builders, launch 50 AI sponsor challenges, and achieve 95% attendee engagement.")
    created_at: Optional[str] = Field(None, description="ISO timestamp when event plan was initialized")

    class Config:
        populate_by_name = True


class Task(BaseModel):
    id: Optional[str] = Field(None, alias="_id", description="Unique Task identifier")
    title: str = Field(..., description="Actionable task title", example="Finalize Title Sponsor Agreement with Cloud Provider")
    role: str = Field(..., description="Role department: Marketing, Partnerships, Operations, Programme, Leadership", example="Partnerships")
    status: str = Field("Pending", description="Task Status: Pending, In Progress, Resolved", example="In Progress")
    is_blocker: bool = Field(False, description="Flag indicating if this task is a critical blocker")
    deadline: str = Field(..., description="Deadline timestamp or formatted date", example="2026-10-25T18:00:00Z")
    description: Optional[str] = Field(None, description="Detailed actionable operational notes")
    resolved_at: Optional[str] = Field(None, description="ISO timestamp when task was resolved")

    class Config:
        populate_by_name = True


class RegistrationMetrics(BaseModel):
    target_registrations: int = Field(2500, description="Target total registrations", example=2500)
    current_registrations: int = Field(1620, description="Current confirmed registrations", example=1620)
    days_remaining: int = Field(14, description="Days remaining until the event", example=14)
    daily_velocity: float = Field(42.5, description="Current daily registration run rate / pace", example=42.5)
    required_daily_velocity: Optional[float] = Field(None, description="Required run rate to hit target registrations")
    velocity_ratio: Optional[float] = Field(None, description="Ratio of current velocity to required velocity")
    registration_risk: bool = Field(False, description="True if current daily velocity paces below 80% of target")
    reach_gap: Optional[int] = Field(0, description="Quantified registrations lag / deficit")


class SentimentPost(BaseModel):
    id: Optional[str] = Field(None, description="Unique post identifier")
    text: str = Field(..., description="Content of the social post or review")
    sentiment: str = Field("neutral", description="Sentiment rating: positive, negative, or neutral")
    source: str = Field("Twitter", description="Source channel: Twitter, Discord, or Feedback")
    timestamp: str = Field(..., description="Timestamp of post creation")
    author: Optional[str] = Field("@attendee", description="User handle or author name")


# ─────────────────────────────────────────────────────────────────────────────
# 2. API REQUEST & RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────

class GeneratePlanRequest(BaseModel):
    title: Optional[str] = Field("Hackingly AI Innovations Summit 2026", description="Event Title")
    format: Optional[str] = Field("Hybrid", description="In-person, Hybrid, or Virtual")
    target_scale: Optional[int] = Field(2500, description="Target attendee capacity")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    venue: Optional[str] = Field("Cyber Arena & Virtual Metaverse", description="Event Venue")
    objectives: Optional[str] = Field(None, description="Raw event brief or executive goals")


class GeneratePlanResponse(BaseModel):
    message: str
    event: Event
    tasks_generated: int
    tasks: List[Task]
    registration_metrics: RegistrationMetrics


class TaskResolveResponse(BaseModel):
    message: str
    task: Task
    registration_risk: bool
    community_friction_risk: bool
    recovery_action: Optional[str] = None


class MetricItem(BaseModel):
    label: str
    value: str
    alert: Optional[bool] = False


class QuickActionItem(BaseModel):
    label: str
    url: Optional[str] = None
    action: Optional[str] = None
    query: Optional[str] = None


class NLPQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question or command", example="What are the critical blockers in Partnerships?")


class NLPQueryResponse(BaseModel):
    query: str
    response: str
    answer: str
    category: str
    metrics: List[MetricItem] = []
    quick_actions: List[QuickActionItem] = []
    result_count: int = 0


class AdminStatsResponse(BaseModel):
    event: Optional[Dict[str, Any]] = None
    registration_metrics: Dict[str, Any]
    registration_risk: bool
    community_friction_risk: bool
    friction_category: Optional[str] = None
    recovery_action: Optional[str] = None
    recovery_action_title: Optional[str] = None
    recovery_action_type: Optional[str] = None
    sentiment_metrics: Dict[str, Any]
    tasks_by_role: Dict[str, List[Dict[str, Any]]]
    blocker_count: int
    total_tasks: int
    resolved_tasks: int
    system_status: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# 3. ATTENDEE & CASHLESS COMPATIBILITY MODELS (Retained for Full Integration)
# ─────────────────────────────────────────────────────────────────────────────

class AttendeeBase(BaseModel):
    name: str = Field(..., description="Full name of attendee", example="Aarav Sharma")
    role: str = Field("General", description="Ticket tier role (General, Early Bird, VIP, Organizer, Sponsor)")
    ticket_type: str = Field("Standard", description="Specific pass type")
    fest_coins: int = Field(1000, description="Current Fest Coin cashless balance")

class AttendeeCreate(AttendeeBase):
    initial_coins: Optional[int] = Field(None, description="Optional initial Fest Coins override")

class AttendeeResponse(AttendeeBase):
    id: str = Field(..., alias="_id", description="Unique attendee ID")
    engagement_score: int = Field(0, description="Cumulative engagement points")
    qr_code_hash: str = Field(..., description="Unique hexadecimal QR pass identifier")
    status: str = Field("active", description="Status: 'active' or 'terminated'")
    registered_at: str = Field(..., description="ISO registration timestamp")

    class Config:
        populate_by_name = True

class ScanRequest(BaseModel):
    qr_code_hash: str = Field(..., description="Attendee QR code hash")
    zone_name: str = Field(..., description="Target festival zone")

class RechargeRequest(BaseModel):
    attendee_id: Optional[str] = Field(None, description="Attendee ID")
    qr_code_hash: Optional[str] = Field(None, description="Attendee QR hash")
    inr_amount: int = Field(..., gt=0, description="Amount in Indian Rupees to top up")
    payment_method: Optional[str] = Field("UPI", description="Payment method: UPI, Card, NetBanking")

class IncidentCreate(BaseModel):
    type: str = Field(..., description="Medical, Security, or Logistics")
    zone_name: Optional[str] = Field("Main Stage", description="Festival zone")
    notes: Optional[str] = Field(None, description="Specific incident notes")

class HealthCheckResponse(BaseModel):
    status: str
    framework: str = "FastAPI (Python 3.11)"
    server: str = "Uvicorn ASGI"
    database_driver: str = "Motor (async MongoDB Atlas) with Resilient Fallback"
    database_status: str
    database_uri_configured: bool
    gemini_ai_copilot: str = "Google Gemini 2.5/3.8 Flash SDK Active"
    sentiment_analyzer: str = "Hugging Face 5-Minute Rolling Vibe Engine Active"
    version: str = "3.0.0"
