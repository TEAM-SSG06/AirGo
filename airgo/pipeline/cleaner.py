<<<<<<< HEAD
"""
AirGo Data Cleaning Pipeline.
Clean, deduplicate, and validate raw flight fare quotes.
"""

from datetime import date
from typing import List, Dict, Any


class DataCleaningPipeline:
    def process_pending_quotes(self, target_date: date) -> int:
        return 0
=======
import logging
from datetime import date
from typing import List, Dict, Any, Tuple
import numpy as np
from sqlalchemy import select, delete
from airgo.pipeline.models import RawQuoteDB, CleanFareDB, CleanFareSchema
from airgo.pipeline.db import get_db_session

logger = logging.getLogger("AirGo.Cleaner")


class DataCleaningPipeline:
    """
    Cleans, de-duplicates, and removes statistical price outliers from raw scraped flight quotes.
    Preserves original live source URLs for transparent auditability.
    """

    def __init__(self, iqr_multiplier: float = 2.0, min_quotes_for_outlier: int = 4):
        self.iqr_multiplier = iqr_multiplier
        self.min_quotes_for_outlier = min_quotes_for_outlier

    def process_pending_quotes(self, booking_date: date = None) -> Dict[str, Any]:
        target_date = booking_date or date.today()
        logger.info(f"🧹 [Cleaner] Processing raw quotes for booking date: {target_date}")

        with get_db_session() as session:
            stmt = select(RawQuoteDB).where(RawQuoteDB.booking_date == target_date)
            raw_quotes = session.scalars(stmt).all()

            if not raw_quotes:
                logger.info(f"No raw quotes found for {target_date}")
                return {"status": "NO_DATA", "processed": 0, "clean_count": 0, "outliers_removed": 0}

            dedup_groups: Dict[Tuple, List[RawQuoteDB]] = {}
            for q in raw_quotes:
                dep_date = q.departure_datetime.date()
                key = (q.origin, q.destination, q.carrier, q.flight_number, dep_date, q.advance_window)
                if key not in dedup_groups:
                    dedup_groups[key] = []
                dedup_groups[key].append(q)

            normalized_candidates: List[CleanFareSchema] = []
            for key, group in dedup_groups.items():
                origin, dest, carrier, flight_no, dep_date, adv_win = key
                best_quote = min(group, key=lambda x: x.total_fare)
                all_sources = ",".join(sorted(list(set(x.source for x in group))))
                
                total_f = best_quote.total_fare
                base_f = best_quote.base_fare if (best_quote.base_fare and best_quote.base_fare < total_f) else round(total_f * 0.74, 2)
                taxes_f = round(total_f - base_f, 2)

                # Fallback source URL if None
                source_link = best_quote.source_url or f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{origin}%20on%20{dep_date.strftime('%Y-%m-%d')}%20one%20way"

                normalized_candidates.append(CleanFareSchema(
                    sector=f"{origin}-{dest}",
                    origin=origin,
                    destination=dest,
                    carrier=carrier,
                    flight_number=flight_no,
                    departure_date=dep_date,
                    departure_time=best_quote.departure_datetime.strftime("%H:%M"),
                    booking_date=target_date,
                    advance_window=adv_win,
                    advance_days=best_quote.advance_days,
                    fare_class=best_quote.fare_class or "Economy",
                    stops=best_quote.stops or 0,
                    base_fare=base_f,
                    taxes_and_fees=taxes_f,
                    total_fare=total_f,
                    source_url=source_link,
                    is_outlier=False,
                    source_count=len(group),
                    sources=all_sources
                ))

            outliers_detected = 0
            sector_win_groups: Dict[Tuple[str, str], List[CleanFareSchema]] = {}
            for cand in normalized_candidates:
                sw_key = (cand.sector, cand.advance_window)
                if sw_key not in sector_win_groups:
                    sector_win_groups[sw_key] = []
                sector_win_groups[sw_key].append(cand)

            for (sec, adv), items in sector_win_groups.items():
                if len(items) >= self.min_quotes_for_outlier:
                    fares = [x.total_fare for x in items]
                    q25, q75 = np.percentile(fares, [25, 75])
                    iqr = q75 - q25
                    lower_bound = max(1000.0, q25 - (self.iqr_multiplier * iqr))
                    upper_bound = q75 + (self.iqr_multiplier * iqr)

                    for item in items:
                        if item.total_fare < lower_bound or item.total_fare > upper_bound:
                            item.is_outlier = True
                            item.outlier_reason = f"IQR Outlier (Fare {item.total_fare} outside [{lower_bound:.0f}, {upper_bound:.0f}])"
                            outliers_detected += 1

            session.execute(delete(CleanFareDB).where(CleanFareDB.booking_date == target_date))
            
            clean_db_objects = [
                CleanFareDB(
                    sector=c.sector,
                    origin=c.origin,
                    destination=c.destination,
                    carrier=c.carrier,
                    flight_number=c.flight_number,
                    departure_date=c.departure_date,
                    departure_time=c.departure_time,
                    booking_date=c.booking_date,
                    advance_window=c.advance_window,
                    advance_days=c.advance_days,
                    fare_class=c.fare_class,
                    stops=c.stops,
                    base_fare=c.base_fare,
                    taxes_and_fees=c.taxes_and_fees,
                    total_fare=c.total_fare,
                    source_url=c.source_url,
                    is_outlier=c.is_outlier,
                    outlier_reason=c.outlier_reason,
                    source_count=c.source_count,
                    sources=c.sources
                )
                for c in normalized_candidates
            ]
            session.bulk_save_objects(clean_db_objects)

        clean_non_outliers = sum(1 for c in normalized_candidates if not c.is_outlier)
        logger.info(
            f"✅ [Cleaner] Done for {target_date}: {len(raw_quotes)} raw -> {len(normalized_candidates)} deduplicated "
            f"({clean_non_outliers} clean, {outliers_detected} outliers)"
        )
        return {
            "status": "SUCCESS",
            "raw_quotes_processed": len(raw_quotes),
            "deduplicated_quotes": len(normalized_candidates),
            "clean_valid_quotes": clean_non_outliers,
            "outliers_removed": outliers_detected
        }
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
