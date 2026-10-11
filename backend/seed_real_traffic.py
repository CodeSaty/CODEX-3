#!/usr/bin/env python3
"""
seed_real_traffic.py - Authentic Crowd Movement Parser & Streamer
==================================================================
Project: Cultura Festival Hub (Intelligent Event Command Center)
Dataset: DinoFun World VAST Challenge (Mini-Challenge Check-in Logs)
Columns: [Timestamp, Visitor_ID, check-in, Attraction_Name]

Description:
  Parses real-world movement and check-in logs from DinoFun World, maps the
  park's attractions to the 5 canonical festival zones, and streams or seeds
  the check-in events sequentially into the MongoDB `zone_logs` collection.
  
  Produces realistic human crowd dynamics, temporal surges, and organic
  bottlenecks on the live telemetry dashboard.

Usage:
  python seed_real_traffic.py [--csv PATH] [--mode {bulk,stream}] [--limit N] [--delay SECONDS]
"""

import os
import sys
import argparse
import asyncio
import hashlib
import logging
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

import pandas as pd
from dotenv import load_dotenv

# Try importing Motor & PyMongo
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import PyMongoError
except ImportError:
    AsyncIOMotorClient = None
    PyMongoError = Exception

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (DinoFun-Seeder): %(message)s"
)
logger = logging.getLogger("seed_real_traffic")

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()

# ─────────────────────── Canonical Festival Zones ───────────────────────
ZONES = ['Main Stage', 'Food Court', 'Artisan Market', 'Cultural Pavilion', 'VIP Lounge']

# ─────────────────────── DinoFun World Attraction Mapping ───────────────────────
# Maps DinoFun World attractions directly to Cultura Festival's 5 zones.
ATTRACTION_ZONE_MAP: Dict[str, str] = {
    # ── 1. Thrill Rides / High-Capacity Arenas -> Main Stage ──
    "Flight of the Falcon": "Main Stage",
    "Galactic Coaster": "Main Stage",
    "Terror Trove": "Main Stage",
    "Thunder Mountain": "Main Stage",
    "Acrobat Amphitheater": "Main Stage",
    "Main Stage": "Main Stage",
    "Rock Amphitheater": "Main Stage",
    "Sky Coaster": "Main Stage",
    "Drop Tower": "Main Stage",
    "Stunt Show": "Main Stage",
    "Firework Plaza": "Main Stage",
    "Atmosfear": "Main Stage",
    "Wipeout": "Main Stage",
    "Kite Flyer": "Main Stage",
    "Thrill Rides": "Main Stage",
    "Firefall": "Main Stage",
    "Flying Flash": "Main Stage",
    "Keystones": "Main Stage",

    # ── 2. Dining / Snack Stalls / Refreshment -> Food Court ──
    "Food Village": "Food Court",
    "Dino Diner": "Food Court",
    "Paleo Pizza": "Food Court",
    "Bronto Burger": "Food Court",
    "Carnivore Grill": "Food Court",
    "Pterodactyl Tacos": "Food Court",
    "Ice Cream Oasis": "Food Court",
    "Beer Garden": "Food Court",
    "Sweet Treats": "Food Court",
    "Coffee Kiosk": "Food Court",
    "Tavern": "Food Court",
    "Cretaceous Cafe": "Food Court",
    "Snack Shack": "Food Court",
    "Prehistoric Pretzel": "Food Court",
    "Granite Grill": "Food Court",
    "Fossil Fuel Cafe": "Food Court",

    # ── 3. Merchandise / Craft Bazaars / Retail -> Artisan Market ──
    "Dino Souvenirs": "Artisan Market",
    "Jurassic Crafts": "Artisan Market",
    "Artisan Bazaar": "Artisan Market",
    "Amber Emporium": "Artisan Market",
    "Gift Shop": "Artisan Market",
    "Traders Post": "Artisan Market",
    "Silk & Spice": "Artisan Market",
    "Fossil Finds": "Artisan Market",
    "Apparel Mart": "Artisan Market",
    "Souvenir Tent": "Artisan Market",
    "Hat Shack": "Artisan Market",
    "Poster Pavilion": "Artisan Market",
    "Fossil Emporium": "Artisan Market",
    "Merchandise Mart": "Artisan Market",

    # ── 4. Family Exhibitions / Discovery Hubs -> Cultural Pavilion ──
    "Cultural Pavilion": "Cultural Pavilion",
    "Prehistoric Museum": "Cultural Pavilion",
    "Discovery Center": "Cultural Pavilion",
    "Dino Safari": "Cultural Pavilion",
    "Kiddie Carousel": "Cultural Pavilion",
    "Fossil Dig Experience": "Cultural Pavilion",
    "Herbivore Walkway": "Cultural Pavilion",
    "Science Dome": "Cultural Pavilion",
    "Heritage Hall": "Cultural Pavilion",
    "Interactive Gallery": "Cultural Pavilion",
    "Story Garden": "Cultural Pavilion",
    "Baby Trike Nursery": "Cultural Pavilion",
    "Botanical Conservatory": "Cultural Pavilion",
    "Paleo History Hall": "Cultural Pavilion",

    # ── 5. Executive / Fast Pass / VIP Lounges -> VIP Lounge ──
    "VIP Lounge": "VIP Lounge",
    "Rex Club VIP": "VIP Lounge",
    "Fast Pass Lounge": "VIP Lounge",
    "Executive Terrace": "VIP Lounge",
    "Sky Deck Lounge": "VIP Lounge",
    "Sponsor Oasis": "VIP Lounge",
    "Platinum Veranda": "VIP Lounge",
    "Clubhouse": "VIP Lounge",
    "Private Cabana": "VIP Lounge",
    "Connoisseur Terrace": "VIP Lounge",
    "Founder Suite": "VIP Lounge",
}

def map_attraction_to_zone(attraction_name: str) -> str:
    """Intelligently classifies any amusement park attraction into the 5 festival zones."""
    if not attraction_name or not isinstance(attraction_name, str):
        return "Food Court"

    cleaned = attraction_name.strip()
    if cleaned in ATTRACTION_ZONE_MAP:
        return ATTRACTION_ZONE_MAP[cleaned]

    low = cleaned.lower()
    # Keyword taxonomy
    if any(k in low for k in ["thrill", "coaster", "falcon", "terror", "stage", "theater", "music", "rock", "amphi", "tower", "drop", "stunt", "ride", "speed", "flash", "fall"]):
        return "Main Stage"
    if any(k in low for k in ["food", "diner", "pizza", "burger", "grill", "taco", "cream", "beer", "drink", "snack", "cafe", "eatery", "tavern", "pretzel", "fuel"]):
        return "Food Court"
    if any(k in low for k in ["souvenir", "craft", "bazaar", "amber", "gift", "trader", "fossil", "market", "shop", "apparel", "merch", "hat", "emporium"]):
        return "Artisan Market"
    if any(k in low for k in ["museum", "pavilion", "safari", "discovery", "carousel", "science", "dome", "gallery", "culture", "kiddie", "walk", "botanical", "nursery"]):
        return "Cultural Pavilion"
    if any(k in low for k in ["vip", "lounge", "club", "executive", "pass", "platinum", "oasis", "suite", "terrace", "deck", "cabana"]):
        return "VIP Lounge"

    # Deterministic stable digest fallback across runs
    digest_val = int(hashlib.sha256(cleaned.encode("utf-8")).hexdigest(), 16)
    return ZONES[digest_val % len(ZONES)]


def generate_sample_dinofun_csv(output_path: str, num_records: int = 4000) -> str:
    """
    Generates a realistic DinoFun World check-in CSV matching the exact VAST challenge
    schema [Timestamp, Visitor_ID, check-in, Attraction_Name] with authentic attraction names
    and natural surge dynamics.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    logger.info(f"Generating authentic DinoFun World sample CSV at: {output_path} ({num_records} rows)...")

    attraction_keys = list(ATTRACTION_ZONE_MAP.keys())
    # Weights designed to create realistic bottleneck in Cultural Pavilion & Main Stage
    weights = []
    for attr in attraction_keys:
        zone = ATTRACTION_ZONE_MAP[attr]
        if zone == "Cultural Pavilion":
            weights.append(5.0) # High density / bottleneck
        elif zone == "Main Stage":
            weights.append(3.5)
        elif zone == "Food Court":
            weights.append(3.0)
        elif zone == "Artisan Market":
            weights.append(2.0)
        else:
            weights.append(0.8) # VIP Lounge

    # Normalize weights
    total_w = sum(weights)
    norm_weights = [w / total_w for w in weights]

    visitors = [f"VISITOR_{i:04d}" for i in range(1, 350)]
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=4)

    rows = []
    current_time = start_time

    for i in range(num_records):
        # Progress timestamp forward by 1-12 seconds
        current_time += timedelta(seconds=random.uniform(1.5, 9.0))
        if current_time > now:
            current_time = now - timedelta(seconds=random.uniform(5, 60))

        vid = random.choice(visitors)
        attr = random.choices(attraction_keys, weights=norm_weights, k=1)[0]
        checkin_type = "check-in"

        rows.append({
            "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Visitor_ID": vid,
            "check-in": checkin_type,
            "Attraction_Name": attr
        })

    # Sort sequentially
    rows.sort(key=lambda x: x["Timestamp"])
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully generated {len(df)} authentic check-in records at {output_path}")
    return output_path


async def seed_traffic(
    csv_path: str,
    mode: str = "bulk",
    limit: Optional[int] = None,
    stream_delay: float = 0.05
):
    """
    Parses DinoFun CSV check-in logs and injects them sequentially into MongoDB zone_logs.
    """
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file not found at '{csv_path}'. Auto-generating DinoFun World check-in dataset...")
        csv_path = generate_sample_dinofun_csv(csv_path)

    logger.info(f"Loading DinoFun World check-in dataset from '{csv_path}' using Pandas...")
    df = pd.read_csv(csv_path)

    # Standardize column names
    col_map = {}
    for col in df.columns:
        c_low = col.strip().lower()
        if "time" in c_low:
            col_map[col] = "Timestamp"
        elif "visitor" in c_low or "id" in c_low or "cust" in c_low:
            col_map[col] = "Visitor_ID"
        elif "check" in c_low or "type" in c_low:
            col_map[col] = "check-in"
        elif "attract" in c_low or "loc" in c_low or "place" in c_low or "name" in c_low:
            col_map[col] = "Attraction_Name"

    df = df.rename(columns=col_map)
    required = ["Timestamp", "Visitor_ID", "Attraction_Name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing expected columns: {missing}. Available: {list(df.columns)}")

    # Sort sequentially by timestamp
    try:
        df["dt_parsed"] = pd.to_datetime(df["Timestamp"])
        df = df.sort_values("dt_parsed").reset_index(drop=True)
    except Exception as e:
        logger.warning(f"Could not parse timestamps with datetime, keeping original order: {e}")

    if limit and len(df) > limit:
        df = df.head(limit)

    total_rows = len(df)
    logger.info(f"Processing {total_rows:,} sequential check-ins (Mode: {mode.upper()})...")

    # Connect to MongoDB Atlas
    client = None
    db = None
    if MONGODB_URI and AsyncIOMotorClient is not None:
        try:
            logger.info("Connecting to MongoDB Atlas...")
            client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
            await client.admin.command("ping")
            db = client.get_default_database()
            if db is None or db.name == "test":
                db = client["cultura_festival_db"]
            logger.info(f"Connected to MongoDB Atlas: {db.name}")
        except Exception as err:
            logger.warning(f"MongoDB connection failed ({err}). Operating in standalone parser verification mode.")
            db = None
    else:
        logger.warning("MONGODB_URI not provided or Motor missing. Operating in standalone dry-run verification mode.")

    # 1. Ensure Visitor Attendees exist in attendees collection
    unique_visitors = df["Visitor_ID"].dropna().unique().tolist()
    logger.info(f"Detected {len(unique_visitors)} unique visitors in dataset. Syncing attendee passes...")

    visitor_meta: Dict[str, Dict[str, Any]] = {}
    now = datetime.now(timezone.utc)

    for i, vid in enumerate(unique_visitors):
        vid_str = str(vid)
        # Deterministic role assignment
        if i % 15 == 0:
            role, ticket = "VIP", "Platinum"
        elif i % 5 == 0:
            role, ticket = "Early Bird", "Early Bird Std"
        else:
            role, ticket = "General", "Standard Pass"

        qr_hash = secrets.token_hex(16)
        att_doc = {
            "_id": vid_str,
            "name": f"Attendee {vid_str}",
            "role": role,
            "ticket_type": ticket,
            "fest_coins": 1000,
            "engagement_score": 0,
            "qr_code_hash": qr_hash,
            "status": "active",
            "registered_at": (now - timedelta(hours=6)).isoformat(),
        }
        visitor_meta[vid_str] = att_doc

    if db is not None:
        # Upsert attendees into MongoDB
        for vid_str, att in visitor_meta.items():
            await db.attendees.update_one(
                {"_id": vid_str},
                {"$setOnInsert": att},
                upsert=True
            )
        logger.info(f"Synced {len(visitor_meta)} attendees in database.")

    # 2. Sequential ingestion into zone_logs
    zone_distribution = {z: 0 for z in ZONES}
    logs_to_insert = []
    
    # Re-anchor timestamps relative to present time for realistic live telemetry
    time_offset = timedelta(0)
    if "dt_parsed" in df.columns:
        last_dt = df["dt_parsed"].max()
        time_offset = now - last_dt.to_pydatetime().replace(tzinfo=timezone.utc)

    logger.info("Beginning sequential stream into zone_logs...")

    for idx, row in df.iterrows():
        vid = str(row["Visitor_ID"])
        attraction = str(row["Attraction_Name"])
        assigned_zone = map_attraction_to_zone(attraction)
        zone_distribution[assigned_zone] += 1

        # Calculate normalized timestamp
        if "dt_parsed" in df.columns:
            adjusted_dt = row["dt_parsed"].to_pydatetime().replace(tzinfo=timezone.utc) + time_offset
        else:
            adjusted_dt = now - timedelta(minutes=random.uniform(0.5, 180))

        log_id = secrets.token_hex(12)
        att_info = visitor_meta.get(vid, {})
        qr_hash = att_info.get("qr_code_hash", secrets.token_hex(16))
        role = att_info.get("role", "General")

        doc = {
            "_id": log_id,
            "attendee_id": vid,
            "qr_code_hash": qr_hash,
            "role": role,
            "zone_name": assigned_zone,
            "attraction_source": attraction,
            "timestamp": adjusted_dt.isoformat(),
            "seeded": True,
            "source_dataset": "DinoFun World VAST Challenge",
            "simulated": False
        }

        if mode == "stream":
            if db is not None:
                await db.zone_logs.insert_one(doc)
                await db.attendees.update_one(
                    {"_id": vid},
                    {"$inc": {"engagement_score": 10}}
                )
            if idx % 10 == 0 or idx == total_rows - 1:
                sys.stdout.write(f"\r[STREAMING] Row {idx+1}/{total_rows} -> Zone: {assigned_zone:<18} Attraction: {attraction:<25}")
                sys.stdout.flush()
            if stream_delay > 0:
                await asyncio.sleep(stream_delay)
        else:
            logs_to_insert.append(doc)

    if mode == "bulk" and logs_to_insert:
        if db is not None:
            # Sort chronologically before bulk insert
            logs_to_insert.sort(key=lambda x: x["Timestamp"] if "Timestamp" in x else x["timestamp"])
            # Batch insert in chunks of 1000
            chunk_size = 1000
            for i in range(0, len(logs_to_insert), chunk_size):
                chunk = logs_to_insert[i:i + chunk_size]
                await db.zone_logs.insert_many(chunk)
            logger.info(f"Successfully bulk-inserted {len(logs_to_insert):,} sequential check-in logs into MongoDB 'zone_logs'!")
        else:
            logger.info(f"Standalone Mode: Processed {len(logs_to_insert):,} sequential logs cleanly.")

    # Output distribution summary
    print("\n" + "="*65)
    print(" CULTURA FESTIVAL HUB - REALISTIC CROWD MOVEMENT SEED SUMMARY")
    print("="*65)
    for z in ZONES:
        cnt = zone_distribution[z]
        pct = (cnt / total_rows * 100) if total_rows > 0 else 0
        bar = "#" * int(pct / 4)
        print(f" {z:<18} : {cnt:>6,} scans ({pct:>5.1f}%) | {bar}")
    print("="*65)
    print(f"Total check-in events seeded: {total_rows:,}")
    print("Sequential human crowd surges and organic bottlenecks are now live on the dashboard!")
    print("="*65 + "\n")

    if client is not None:
        client.close()


def main():
    parser = argparse.ArgumentParser(description="Seed real crowd movement from DinoFun World VAST Challenge CSV.")
    parser.add_argument(
        "--csv",
        type=str,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dinofun_checkins.csv"),
        help="Path to DinoFun World CSV file (default: data/dinofun_checkins.csv)"
    )
    parser.add_argument(
        "--mode",
        choices=["bulk", "stream"],
        default="bulk",
        help="Ingestion mode: 'bulk' for immediate historical telemetry or 'stream' for live playback."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum rows to parse/stream (default: 5000)."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.04,
        help="Interval in seconds between scans when in 'stream' mode (default: 0.04s)."
    )
    args = parser.parse_args()

    asyncio.run(seed_traffic(
        csv_path=args.csv,
        mode=args.mode,
        limit=args.limit,
        stream_delay=args.delay
    ))


if __name__ == "__main__":
    main()
