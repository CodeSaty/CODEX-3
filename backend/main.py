import os
import sys
import re
import json
import random
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load .env from project root or backend folder
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv()

from fastapi import FastAPI, Request, Response, HTTPException, Header, Depends, Query, Path, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from models import (
    AttendeeCreate, AttendeeResponse, AttendeeRegisterResult,
    TerminateQrRequest, ReinstateQrRequest,
    ScanRequest, ScanResponse,
    TransactionRequest, TransactionResponse,
    RechargeRequest, RechargeResponse, RechargesListResponse,
    IncidentCreate, IncidentResponse,
    DiversionCreate, DiversionResponse, ThrottleRequest,
    NLPQueryRequest, NLPQueryResponse, MetricItem, QuickActionItem,
    AdminStatsResponse, AttendeeHistoryResponse, HealthCheckResponse
)
from database import db_manager, ZONES, ROLES, BOTTLENECK_THRESHOLD, SCAN_ENGAGEMENT_POINTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cultura.server")

# Admin Security Key
ADMIN_ACCESS_KEY = os.getenv("ADMIN_KEY", "").strip()

def verify_admin(x_admin_key: Optional[str] = Header(None, alias="x-admin-key")):
    if not ADMIN_ACCESS_KEY or not x_admin_key or x_admin_key.strip() != ADMIN_ACCESS_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized Access")
    return True

# Background crowd simulation task
async def crowd_simulation_loop():
    logger.info("Starting background festival crowd movement simulation loop (4s interval)...")
    while True:
        try:
            await asyncio.sleep(4.0)
            att_list = await db_manager.list_attendees(limit=250)
            if att_list:
                num_scans = random.randint(1, 2)
                for _ in range(num_scans):
                    att = random.choice(att_list)
                    if att.get('status') == 'terminated':
                        continue
                    zone = random.choice(ZONES)
                    
                    # Check active diversions
                    active_div = next(
                        (d for d in db_manager.mem_diversions if d.get('active') and d.get('zone_name') == zone),
                        None
                    )
                    if active_div and random.random() < 0.65:
                        zone = active_div.get('target_zone', 'Food Court')

                    await db_manager.log_zone_scan(att, zone)
        except asyncio.CancelledError:
            logger.info("Crowd simulation background task cancelled.")
            break
        except Exception as e:
            logger.warning(f"Error in simulation loop: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB Atlas (or in-memory fallback) and seed
    await db_manager.connect()
    sim_task = asyncio.create_task(crowd_simulation_loop())
    yield
    # Shutdown
    sim_task.cancel()
    try:
        await sim_task
    except asyncio.CancelledError:
        pass
    if db_manager.client:
        db_manager.client.close()

# Initialize FastAPI app
app = FastAPI(
    title="Cultura Festival Hub API",
    description="Live festival crowd-management telemetry, pass checkpoint verification, and cashless Fest Coin economy powered by Python, FastAPI, Pydantic, and MongoDB Atlas (Motor).",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No-Cache Middleware for fresh development updates
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ─────────────────────── System & Health Endpoints ───────────────────────
@app.get("/api/health", response_model=HealthCheckResponse, tags=["Health"])
async def get_health():
    status_info = db_manager.get_status_summary()
    return {
        "status": "healthy",
        "framework": "FastAPI (Python 3.11)",
        "server": "Uvicorn ASGI",
        "validation": "Pydantic v2",
        "database_driver": "Motor (async MongoDB Atlas) with Resilient Fallback",
        "database_status": status_info["connection_message"],
        "database_uri_configured": status_info["database_uri_configured"],
        "active_connections": 1,
        "version": "2.0.0"
    }

# ─────────────────────── Canonical Zones ───────────────────────
@app.get("/zones", tags=["Zones"])
async def get_zones():
    return {"zones": ZONES}

# ─────────────────────── Attendee Registration & Lookup ───────────────────────
@app.post("/register_attendee", status_code=status.HTTP_201_CREATED, tags=["Attendees"])
async def register_attendee(payload: AttendeeCreate):
    attendee = await db_manager.create_attendee(
        name=payload.name,
        role=payload.role,
        ticket_type=payload.ticket_type,
        initial_coins=payload.initial_coins or 0
    )
    return {
        "message": "Attendee registered successfully",
        "qr_code_hash": attendee["qr_code_hash"],
        "attendee": attendee
    }

@app.get("/attendee/{qr_code_hash}", tags=["Attendees"])
async def get_attendee_by_qr(qr_code_hash: str = Path(..., description="16-byte QR pass hash")):
    attendee = await db_manager.get_attendee_by_qr(qr_code_hash)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return attendee

@app.get("/api/attendees/search", tags=["Attendees"])
async def search_attendees(q: Optional[str] = Query("", description="Query string for name, role, ticket, or ID")):
    results = await db_manager.list_attendees(query=q or "", limit=50)
    return {"attendees": results}

@app.get("/api/attendee/{attendee_id}/history", response_model=AttendeeHistoryResponse, tags=["Attendees"])
async def get_attendee_history(attendee_id: str):
    history = await db_manager.get_attendee_history(attendee_id)
    if not history:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return history

# ─────────────────────── Gate Checkpoint Scanning ───────────────────────
@app.post("/scan", status_code=status.HTTP_201_CREATED, tags=["Field Scanning"])
async def scan_checkpoint(payload: ScanRequest):
    if payload.zone_name not in ZONES:
        raise HTTPException(status_code=400, detail="Invalid scan payload or zone")

    attendee = await db_manager.get_attendee_by_qr(payload.qr_code_hash)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")

    # Security enforcement: Reject terminated passes
    if attendee.get("status") == "terminated":
        return JSONResponse(
            status_code=403,
            content={
                "detail": f"SECURITY ALERT: QR Pass is REVOKED/TERMINATED ({attendee.get('termination_reason') or 'Access Revoked by Administration'})",
                "terminated": True,
                "attendee": {
                    "id": attendee["_id"],
                    "name": attendee["name"],
                    "role": attendee["role"],
                    "ticket_type": attendee["ticket_type"],
                    "status": attendee["status"],
                    "terminated_at": attendee.get("terminated_at"),
                    "termination_reason": attendee.get("termination_reason"),
                }
            }
        )

    log_entry = await db_manager.log_zone_scan(attendee, payload.zone_name)
    updated_attendee = await db_manager.get_attendee_by_id(attendee["_id"])

    return {
        "message": f"Scan logged at {payload.zone_name}!",
        "attendee": updated_attendee or attendee,
        "zone_log": log_entry
    }

# ─────────────────────── Fest Coin Cashless Transactions ───────────────────────
@app.post("/transaction", status_code=status.HTTP_201_CREATED, tags=["Fest Coins"])
async def process_transaction(payload: TransactionRequest):
    attendee = await db_manager.get_attendee_by_qr(payload.qr_code_hash)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee QR code not registered")

    if attendee.get("status") == "terminated":
        return JSONResponse(
            status_code=403,
            content={
                "detail": f"SECURITY ALERT: Payment Denied! QR Pass is REVOKED/TERMINATED ({attendee.get('termination_reason') or 'Pass Revoked'})",
                "terminated": True,
                "attendee": {
                    "id": attendee["_id"],
                    "name": attendee["name"],
                    "role": attendee["role"],
                    "status": attendee["status"],
                    "terminated_at": attendee.get("terminated_at"),
                    "termination_reason": attendee.get("termination_reason"),
                }
            }
        )

    current_balance = attendee.get("fest_coins", 0)
    if current_balance < payload.amount:
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Insufficient Fest Coins. Current balance: {current_balance} coins, Required: {payload.amount} coins",
                "current_balance": current_balance
            }
        )

    tx = await db_manager.create_transaction(
        attendee=attendee,
        amount=payload.amount,
        stall_name=payload.stall_name or "Vendor Stall",
        zone_name=payload.zone_name or "Food Court"
    )
    updated_attendee = await db_manager.get_attendee_by_id(attendee["_id"])

    return {
        "message": f"Successfully deducted {payload.amount} Fest Coins for {payload.stall_name or 'Vendor Stall'}",
        "transaction": tx,
        "attendee": {
            "name": updated_attendee["name"] if updated_attendee else attendee["name"],
            "fest_coins": updated_attendee["fest_coins"] if updated_attendee else current_balance - payload.amount
        }
    }

# ─────────────────────── Rupee-to-Coin Cashless Top-up ───────────────────────
@app.post("/api/recharge", status_code=status.HTTP_201_CREATED, tags=["Recharges"])
async def recharge_wallet(payload: RechargeRequest):
    attendee = None
    if payload.attendee_id:
        attendee = await db_manager.get_attendee_by_id(payload.attendee_id)
    elif payload.qr_code_hash:
        attendee = await db_manager.get_attendee_by_qr(payload.qr_code_hash)

    if not attendee:
        raise HTTPException(
            status_code=404,
            detail="Attendee not found. Please verify attendee name or scan QR pass."
        )

    if attendee.get("status") == "terminated":
        return JSONResponse(
            status_code=403,
            content={
                "detail": f"SECURITY ALERT: Recharge Rejected! QR Pass is REVOKED/TERMINATED ({attendee.get('termination_reason') or 'Administrative Hold'}). Please reinstate pass first.",
                "terminated": True,
                "attendee": {
                    "id": attendee["_id"],
                    "name": attendee["name"],
                    "role": attendee["role"],
                    "status": attendee["status"],
                    "terminated_at": attendee.get("terminated_at"),
                    "termination_reason": attendee.get("termination_reason"),
                }
            }
        )

    recharge_entry = await db_manager.create_recharge(
        attendee=attendee,
        inr_amount=payload.inr_amount,
        payment_method=payload.payment_method or "UPI",
        operator_mode=payload.operator_mode or "self_service",
        operator_name=payload.operator_name,
        notes=payload.notes or ""
    )

    updated_attendee = await db_manager.get_attendee_by_id(attendee["_id"])

    return {
        "message": f"Payment of ₹{payload.inr_amount:,} successful! Added {payload.inr_amount:,} Fest Coins (1:1 conversion).",
        "recharge": recharge_entry,
        "attendee": {
            "_id": updated_attendee["_id"] if updated_attendee else attendee["_id"],
            "name": updated_attendee["name"] if updated_attendee else attendee["name"],
            "role": updated_attendee["role"] if updated_attendee else attendee["role"],
            "ticket_type": updated_attendee["ticket_type"] if updated_attendee else attendee["ticket_type"],
            "fest_coins": updated_attendee["fest_coins"] if updated_attendee else attendee.get("fest_coins", 0) + payload.inr_amount,
            "status": updated_attendee["status"] if updated_attendee else attendee["status"],
            "qr_code_hash": updated_attendee["qr_code_hash"] if updated_attendee else attendee["qr_code_hash"],
        }
    }

@app.get("/api/recharges", tags=["Recharges"])
async def list_recharges():
    recharges_list, summary = await db_manager.get_recharges_summary(limit=100)
    return {
        "recharges": recharges_list,
        "summary": summary
    }

# ─────────────────────── Emergency Incidents (God's Eye) ───────────────────────
@app.post("/api/incident", status_code=status.HTTP_201_CREATED, tags=["Incidents"])
async def report_incident(payload: IncidentCreate):
    valid_types = ["Medical", "Security", "Logistics"]
    if payload.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid incident type. Must be Medical, Security, or Logistics."
        )

    incident = await db_manager.create_incident(
        incident_type=payload.type,
        zone_name=payload.zone_name or "Main Stage",
        notes=payload.notes or ""
    )
    return {
        "message": f"🚨 Emergency {payload.type} incident logged at {incident['zone_name']}!",
        "incident": incident
    }

@app.patch("/api/incident/{incident_id}/resolve", tags=["Incidents"])
@app.post("/api/incident/{incident_id}/resolve", tags=["Incidents"])
async def resolve_incident_endpoint(incident_id: str, is_admin: bool = Depends(verify_admin)):
    resolved = await db_manager.resolve_incident(incident_id)
    if not resolved:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {
        "message": f"{resolved['type']} incident resolved successfully",
        "incident": resolved
    }

# ─────────────────────── Crowd Crush Prevention & Active Diversions ───────────────────────
@app.post("/api/admin/trigger_diversion", status_code=status.HTTP_201_CREATED, tags=["Crowd Control"])
async def trigger_diversion_endpoint(payload: DiversionCreate, is_admin: bool = Depends(verify_admin)):
    if payload.zone_name not in ZONES:
        raise HTTPException(status_code=400, detail="Invalid zone name for diversion")

    diversion, relieved_count = await db_manager.trigger_diversion(
        zone_name=payload.zone_name,
        target_zone=payload.target_zone or "Food Court",
        message=payload.message or ""
    )
    return {
        "message": f"Diversion activated for {payload.zone_name}! {relieved_count} attendees re-routed to {diversion['target_zone']}.",
        "diversion": diversion
    }

@app.post("/api/admin/clear_diversion/{diversion_id}", tags=["Crowd Control"])
async def clear_diversion_endpoint(diversion_id: str, is_admin: bool = Depends(verify_admin)):
    success = await db_manager.clear_diversion(diversion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Diversion not found")
    return {"message": "Diversion marked inactive"}

@app.post("/api/admin/throttle_zone", tags=["Crowd Control"])
async def throttle_zone_endpoint(payload: ThrottleRequest, is_admin: bool = Depends(verify_admin)):
    if payload.zone_name not in ZONES:
        raise HTTPException(status_code=400, detail="Invalid zone")

    other_zones = [z for z in ZONES if z != payload.zone_name]
    target = payload.target_zone if payload.target_zone and payload.target_zone in ZONES else random.choice(other_zones)
    relieved = await db_manager.reroute_recent_scans(payload.zone_name, target, limit=payload.count or 150)

    if relieved == 0:
        return {"message": f"No active attendees found in {payload.zone_name}."}
    return {"message": f"SUCCESS! Diverted {relieved} attendees from {payload.zone_name} to {target}."}

# ─────────────────────── Simulation Endpoints ───────────────────────
@app.post("/api/admin/simulate_surge", tags=["Simulation"])
async def simulate_surge_endpoint(is_admin: bool = Depends(verify_admin)):
    count = await db_manager.simulate_surge()
    return {"message": f"Surge simulated! {count} attendees rushed the Cultural Pavilion."}

@app.post("/api/admin/revert_simulation", tags=["Simulation"])
async def revert_simulation_endpoint(is_admin: bool = Depends(verify_admin)):
    reverted = await db_manager.revert_simulation()
    return {"message": f"Simulation stopped. Reverted {reverted} simulated scans."}

# ─────────────────────── Admin Pass Management & Directory ───────────────────────
@app.get("/api/admin/stats", tags=["Admin Operations"])
async def get_admin_stats_endpoint(is_admin: bool = Depends(verify_admin)):
    return await db_manager.get_admin_stats()

@app.get("/api/admin/attendees", tags=["Admin Operations"])
async def list_admin_attendees(is_admin: bool = Depends(verify_admin)):
    attendees = await db_manager.list_attendees(limit=500)
    return {"attendees": attendees}

@app.delete("/api/admin/delete_attendee/{attendee_id}", tags=["Admin Operations"])
async def delete_attendee_endpoint(attendee_id: str, is_admin: bool = Depends(verify_admin)):
    existing = await db_manager.get_attendee_by_id(attendee_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Attendee not found")
    await db_manager.delete_attendee(attendee_id)
    return {"message": "Attendee deleted permanently."}

async def _terminate_qr_logic(attendee_id: str, reason: Optional[str]):
    attendee = await db_manager.get_attendee_by_id(attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")

    revocation_reason = (reason and reason.strip()) or "Administrative revocation"
    updated = await db_manager.update_attendee(
        attendee_id,
        {
            "status": "terminated",
            "terminated_at": datetime.now(timezone.utc).isoformat(),
            "termination_reason": revocation_reason,
        }
    )
    return {
        "message": f"QR Pass for {attendee['name']} has been terminated.",
        "attendee": updated
    }

@app.post("/api/admin/attendee/{attendee_id}/terminate_qr", tags=["Pass Security"])
async def admin_terminate_qr(attendee_id: str, payload: Optional[TerminateQrRequest] = None, is_admin: bool = Depends(verify_admin)):
    return await _terminate_qr_logic(attendee_id, payload.reason if payload else None)

@app.post("/attendee/{attendee_id}/terminate_qr", tags=["Pass Security"])
async def public_terminate_qr(attendee_id: str, payload: Optional[TerminateQrRequest] = None):
    return await _terminate_qr_logic(attendee_id, payload.reason if payload else None)

async def _reinstate_qr_logic(attendee_id: str, regenerate: bool):
    attendee = await db_manager.get_attendee_by_id(attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")

    updates: Dict[str, Any] = {
        "status": "active",
        "terminated_at": None,
        "termination_reason": None,
    }
    if regenerate:
        import secrets
        updates["qr_code_hash"] = secrets.token_hex(16)

    updated = await db_manager.update_attendee(attendee_id, updates)
    msg = f"New QR Pass generated and activated for {attendee['name']}." if regenerate else f"QR Pass for {attendee['name']} has been reinstated."
    return {
        "message": msg,
        "attendee": updated
    }

@app.post("/api/admin/attendee/{attendee_id}/reinstate_qr", tags=["Pass Security"])
async def admin_reinstate_qr(attendee_id: str, payload: Optional[ReinstateQrRequest] = None, is_admin: bool = Depends(verify_admin)):
    return await _reinstate_qr_logic(attendee_id, payload.regenerate if payload else False)

@app.post("/attendee/{attendee_id}/reinstate_qr", tags=["Pass Security"])
async def public_reinstate_qr(attendee_id: str, payload: Optional[ReinstateQrRequest] = None):
    return await _reinstate_qr_logic(attendee_id, payload.regenerate if payload else False)

# ─────────────────────── NLP Assistant & Intelligence ───────────────────────
@app.post("/api/admin/nlp_query", tags=["AI Command Assistant"])
async def nlp_query_endpoint(request_body: Dict[str, Any], is_admin: bool = Depends(verify_admin)):
    original_query = str(request_body.get("query", "")).strip()
    query = original_query.lower()

    stats = await db_manager.get_admin_stats()
    all_att = await db_manager.list_attendees(limit=500)

    # Zone counts
    zone_counts = {z["zone_name"]: z["total_scans"] for z in stats["zones"]}
    bottlenecks = [z["zone_name"] for z in stats["zones"] if z["recent_scans"] >= BOTTLENECK_THRESHOLD]

    total_attendees = len(all_att)
    active_count = sum(1 for a in all_att if a.get("status") == "active")
    terminated_count = total_attendees - active_count
    total_coins = sum(a.get("fest_coins", 0) for a in all_att)
    role_counts = {}
    for a in all_att:
        r = a.get("role", "General")
        role_counts[r] = role_counts.get(r, 0) + 1

    fin = stats.get("financials", {})
    total_inr_collected = fin.get("total_inr_recharged", 0)
    recharge_volume = fin.get("recharge_volume", 0)
    active_incidents = stats.get("active_incidents", [])

    is_crowd = bool(re.search(r"crowd|bottleneck|congest|traffic|capacity|dens|packed|fullest|busy|divert", query))
    is_coin = bool(re.search(r"coin|recharge|inr|rupee|wallet|cash|money|top-up|balance|revenue|minted", query))
    is_pass = bool(re.search(r"pass|attendee|guest|ticket|revok|terminat|status|register|vip", query)) and not is_crowd
    is_incident = bool(re.search(r"incident|sos|alert|emergency|medical|security|logistics|hazard", query))

    category = "general"
    answer = ""
    metrics: List[Dict[str, Any]] = []
    quick_actions: List[Dict[str, Any]] = []
    result_count = 0

    if is_crowd:
        category = "crowd"
        if bottlenecks:
            b_str = ", ".join([f"{b} ({zone_counts.get(b, 0)} scans)" for b in bottlenecks])
            answer = f"⚠️ Alert: {len(bottlenecks)} festival zone(s) currently at or above bottleneck threshold (≥150 scans): {b_str}. Crowd diversion is recommended."
        else:
            top_zone = max(zone_counts.items(), key=lambda x: x[1]) if zone_counts else ("Main Stage", 0)
            answer = f"Flow is steady across all festival zones. No critical bottlenecks detected. The highest density is currently at {top_zone[0]} with {top_zone[1]} recorded scans."

        metrics = [
            {"label": z, "value": f"{zone_counts.get(z, 0)} scans", "alert": zone_counts.get(z, 0) >= BOTTLENECK_THRESHOLD}
            for z in ZONES
        ]
        quick_actions = [
            {"label": "View Live Telemetry", "url": "/"},
            {"label": "Trigger Crowd Diversion", "action": "diversion"}
        ]
        result_count = len(bottlenecks)

    elif is_coin:
        category = "financial"
        answer = f"Cashless Economy Status: Total Fest Coins in attendee circulation: 🪙 {total_coins:,}. Total INR collected via top-ups: ₹{total_inr_collected:,} across {recharge_volume} transactions (Standard rate: 1 INR = 1 Fest Coin)."
        metrics = [
            {"label": "Coins in Circulation", "value": f"🪙 {total_coins:,}"},
            {"label": "Total INR Collected", "value": f"₹{total_inr_collected:,}"},
            {"label": "Top-up Transactions", "value": str(recharge_volume)},
            {"label": "Rate", "value": "1 ₹ = 1 🪙"}
        ]
        quick_actions = [
            {"label": "Open Coin Top-up Hub", "url": "/recharge.html"},
            {"label": "View Guest Balances", "url": "/attendees.html"}
        ]
        result_count = total_coins

    elif is_incident:
        category = "security"
        if active_incidents:
            answer = f"Active Security Alerts: {len(active_incidents)} pending incident(s) require dispatcher triage. Latest incident in {active_incidents[0].get('zone_name', 'Festival Grounds')}."
        else:
            answer = "All clear. Zero unresolved SOS incidents. Emergency responders and security dispatchers are standing by across all 5 zones."
        metrics = [
            {"label": "Active Incidents", "value": str(len(active_incidents)), "alert": len(active_incidents) > 0},
            {"label": "Total Logged", "value": str(len(active_incidents))},
            {"label": "Diversions Active", "value": str(len(stats.get("active_diversions", [])))}
        ]
        quick_actions = [
            {"label": "Open Incident Radar", "url": "/"},
            {"label": "Scanner Station SOS", "url": "/scanner.html"}
        ]
        result_count = len(active_incidents)

    elif is_pass:
        category = "attendees"
        vip_count = role_counts.get("VIP", 0)
        answer = f"Attendee Directory: {total_attendees} total registered attendees. {active_count} passes active, {terminated_count} passes revoked/terminated. VIP passes: {vip_count}."
        metrics = [
            {"label": "Total Registered", "value": str(total_attendees)},
            {"label": "Active Passes", "value": str(active_count)},
            {"label": "Revoked Passes", "value": str(terminated_count)},
            {"label": "VIP Passholders", "value": str(vip_count)}
        ]
        quick_actions = [
            {"label": "Open Guest Directory", "url": "/attendees.html"},
            {"label": "Field Scanner Hub", "url": "/scanner.html"}
        ]
        result_count = total_attendees

    else:
        # Default query telemetry
        answer = f"Festival Telemetry Status: {total_attendees} registered attendees with {active_count} active passes. Current system balance: 🪙 {total_coins:,} Fest Coins."
        metrics = [
            {"label": "Registered Guests", "value": str(total_attendees)},
            {"label": "Active Zones", "value": str(len(ZONES))},
            {"label": "Cashless Balance", "value": f"🪙 {total_coins:,}"}
        ]
        quick_actions = [
            {"label": "Command Center", "url": "/"},
            {"label": "Live Analytics", "url": "/analytics.html"}
        ]
        result_count = total_attendees

    # Optional Google GenAI enhancement if GEMINI_API_KEY is available
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and len(gemini_key) > 10:
        try:
            from google import genai
            client = genai.Client()
            prompt = f"""You are the Cultura Festival AI Command Assistant.
The festival administrator asked: "{original_query}".
Telemetry Snapshot:
- Zones: {json.dumps(zone_counts)}
- Bottlenecks: {json.dumps(bottlenecks)}
- Total Attendees: {total_attendees} ({active_count} active passes, {terminated_count} revoked)
- Total Fest Coins in Circulation: {total_coins}
- Total INR Cashless Collected: ₹{total_inr_collected}
- Active SOS Incidents: {len(active_incidents)}
Base calculated response: "{answer}"

Provide a concise, direct, professional response in 1-2 clear sentences. Include specific numbers where relevant."""
            
            ai_res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if ai_res and ai_res.text:
                answer = ai_res.text.strip()
        except Exception as ai_err:
            logger.debug(f"Gemini API enhancement fallback: {ai_err}")

    return {
        "query": original_query,
        "response": answer,
        "answer": answer,
        "category": category,
        "metrics": metrics,
        "quick_actions": quick_actions,
        "result_count": result_count,
    }

# Database test config
@app.post("/api/admin/config", tags=["Admin Operations"])
async def config_test_endpoint(is_admin: bool = Depends(verify_admin)):
    status_info = db_manager.get_status_summary()
    return {"message": f"Database operational. {status_info['connection_message']}"}

# ─────────────────────── Static Frontend Serving ───────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
# Check sibling ../frontend directory or local static directory
static_dir = os.path.join(os.path.dirname(base_dir), "frontend")
if not os.path.exists(static_dir):
    static_dir = os.path.join(base_dir, "static")

# Mount /static static directory
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.api_route("/admin.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_admin():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.api_route("/scanner.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_scanner():
    return FileResponse(os.path.join(static_dir, "scanner.html"))

@app.api_route("/analytics.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_analytics():
    return FileResponse(os.path.join(static_dir, "analytics.html"))

@app.api_route("/attendees.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_attendees():
    return FileResponse(os.path.join(static_dir, "attendees.html"))

@app.api_route("/recharge.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_recharge():
    return FileResponse(os.path.join(static_dir, "recharge.html"))

@app.api_route("/payment.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_payment():
    return FileResponse(os.path.join(static_dir, "recharge.html"))

@app.api_route("/settings.html", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_settings():
    return FileResponse(os.path.join(static_dir, "settings.html"))

# Catch-all for other static files (css, js, assets) or fallback to index.html
@app.api_route("/{file_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_static_fallback(file_path: str):
    full_path = os.path.join(static_dir, file_path)
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    # Default fallback to index.html for SPA routing
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=port, reload=False)
