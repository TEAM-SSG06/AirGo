"""
Database persistence adapter for Yatra normalized quotes.
Integrates directly with the existing PostgreSQL engine in airgo.db
and maps NormalizedFareQuote items to the fare_quotes partition schema.
"""

from datetime import datetime, time, timezone
import json
import logging
from typing import List, Optional
from sqlalchemy import text

from airgo.db import engine
from airgo.scrapers.yatra.models import NormalizedFareQuote

logger = logging.getLogger("AirGo.Yatra.DBAdapter")

# Mapping of common Indian carrier names to 2-character IATA codes
CARRIER_IATA_CODES = {
    "INDIGO": "6E",
    "AIR INDIA": "AI",
    "AIR INDIA EXPRESS": "IX",
    "AKASA AIR": "QP",
    "SPICEJET": "SG",
    "VISTARA": "UK",
}


def _resolve_airline_code(airline_name: str, flight_number: str) -> str:
    """Extracts or infers the 2-letter IATA airline code."""
    if flight_number and "-" in flight_number:
        prefix = flight_number.split("-")[0].strip().upper()
        if len(prefix) == 2:
            return prefix

    name_upper = airline_name.strip().upper()
    for carrier, code in CARRIER_IATA_CODES.items():
        if carrier in name_upper:
            return code

    return flight_number[:2].upper() if len(flight_number) >= 2 else "XX"


def _parse_time_str(time_str: str) -> time:
    """Parses 'HH:MM' string into a datetime.time object."""
    try:
        parts = time_str.strip().split(":")
        return time(hour=int(parts[0]), minute=int(parts[1]))
    except Exception:
        return time(0, 0)


def ensure_platform_registered() -> int:
    """Ensures Yatra is registered in dim_platforms and returns its platform_id."""
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT platform_id FROM dim_platforms WHERE platform_name = 'Yatra';")
            ).fetchone()
            if row:
                return int(row[0])

            # Insert Yatra
            insert_res = conn.execute(
                text("""
                    INSERT INTO dim_platforms (platform_name, platform_type, base_url, scrape_method, rate_limit_rpm)
                    VALUES ('Yatra', 'ota', 'https://www.yatra.com', 'playwright', 12)
                    RETURNING platform_id;
                """)
            )
            conn.commit()
            new_id = insert_res.fetchone()
            return int(new_id[0]) if new_id else 1
    except Exception as e:
        logger.warning(f"Could not verify Yatra in dim_platforms: {e}")
        return 1


def persist_fare_quotes_to_db(
    quotes: List[NormalizedFareQuote],
    run_id: int = 1,
    run_started_at: Optional[datetime] = None,
) -> int:
    """
    Persists normalized fare quotes to PostgreSQL fare_quotes table.
    Uses ON CONFLICT DO NOTHING to guarantee idempotent, non-destructive appends.
    Returns the number of quotes successfully inserted.
    """
    if not quotes:
        return 0

    platform_id = ensure_platform_registered()
    start_ts = run_started_at or datetime.now(timezone.utc)
    inserted_count = 0

    insert_sql = text("""
        INSERT INTO fare_quotes (
            run_id,
            run_started_at,
            airline_code,
            airline_name,
            flight_number,
            route_code,
            origin_iata,
            dest_iata,
            scheduled_dep_time,
            scheduled_arr_time,
            platform_id,
            platform_name,
            platform_type,
            scrape_timestamp,
            travel_date,
            advance_purchase_days,
            window_code,
            fare_class,
            base_fare,
            taxes,
            convenience_fee,
            total_fare,
            displayed_search_price,
            final_payable_price,
            verification_status,
            verification_timestamp,
            currency,
            availability_status,
            dedup_hash,
            raw_payload
        ) VALUES (
            :run_id,
            :run_started_at,
            :airline_code,
            :airline_name,
            :flight_number,
            :route_code,
            :origin_iata,
            :dest_iata,
            :scheduled_dep_time,
            :scheduled_arr_time,
            :platform_id,
            :platform_name,
            :platform_type,
            :scrape_timestamp,
            :travel_date,
            :advance_purchase_days,
            :window_code,
            :fare_class,
            :base_fare,
            :taxes,
            :convenience_fee,
            :total_fare,
            :displayed_search_price,
            :final_payable_price,
            :verification_status,
            :verification_timestamp,
            :currency,
            :availability_status,
            :dedup_hash,
            :raw_payload
        )
        ON CONFLICT (dedup_hash, scrape_timestamp) DO NOTHING;
    """)

    try:
        with engine.connect() as conn:
            for q in quotes:
                airline_code = _resolve_airline_code(q.airline, q.flight_number)
                dep_t = _parse_time_str(q.departure_time)
                arr_t = _parse_time_str(q.arrival_time) if q.arrival_time else None
                window_code = f"T+{q.advance_purchase_days}"

                raw_payload_json = json.dumps(q.model_dump(mode="json"), default=str)

                disp_price = float(q.displayed_search_price if q.displayed_search_price is not None else q.displayed_price)
                fin_price = float(q.final_payable_price) if q.final_payable_price is not None else None
                total_f = fin_price if fin_price is not None else disp_price
                v_status = q.verification_status.value if hasattr(q.verification_status, "value") else str(q.verification_status)

                conn.execute(
                    insert_sql,
                    {
                        "run_id": run_id,
                        "run_started_at": start_ts,
                        "airline_code": airline_code,
                        "airline_name": q.airline,
                        "flight_number": q.flight_number,
                        "route_code": q.route,
                        "origin_iata": q.origin,
                        "dest_iata": q.destination,
                        "scheduled_dep_time": dep_t,
                        "scheduled_arr_time": arr_t,
                        "platform_id": platform_id,
                        "platform_name": "Yatra",
                        "platform_type": "ota",
                        "scrape_timestamp": q.scraped_at,
                        "travel_date": q.travel_date,
                        "advance_purchase_days": q.advance_purchase_days,
                        "window_code": window_code,
                        "fare_class": q.fare_class or "ECONOMY",
                        "base_fare": float(q.base_fare),
                        "taxes": float(q.taxes),
                        "convenience_fee": float(q.convenience_fee),
                        "total_fare": total_f,
                        "displayed_search_price": disp_price,
                        "final_payable_price": fin_price,
                        "verification_status": v_status,
                        "verification_timestamp": q.verification_timestamp,
                        "currency": q.currency,
                        "availability_status": q.availability_status.value,
                        "dedup_hash": q.dedup_hash,
                        "raw_payload": raw_payload_json,
                    }
                )
                inserted_count += 1

            conn.commit()
            logger.info(f"Persisted {inserted_count} quotes to database.")
    except Exception as e:
        logger.warning(f"Database persistence skipped or partially failed (raw data preserved in /runs): {e}")

    return inserted_count
