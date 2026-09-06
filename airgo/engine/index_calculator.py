<<<<<<< HEAD
"""
AirGo DGCA Route Index Calculator.
"""

from datetime import date
from typing import Dict, Any


class IndexCalculator:
    def compute_daily_index(self, target_date: date) -> Dict[str, Any]:
        return {"date": str(target_date), "index_score": 100.0}
=======
import logging
import math
from datetime import date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sqlalchemy import select, delete, desc
from airgo.pipeline.models import CleanFareDB, APIxIndexDB
from airgo.pipeline.db import get_db_session
from airgo.engine.dgca_weights import DGCA_ROUTES, ADVANCE_WINDOWS

logger = logging.getLogger("AirGo.IndexCalculator")


class IndexCalculator:
    """
    Computes the Real-Time Airfare Price Index (APIx) at Daily, Weekly, and Monthly frequencies.
    Applies official DGCA city-pair traffic weights and advance-purchase booking distributions.
    """

    def compute_daily_index(self, calculation_date: date = None) -> Dict[str, Any]:
        """
        Compute daily APIx for all sectors and overall national index for a specific date.
        """
        target_date = calculation_date or date.today()
        logger.info(f"📊 [IndexCalculator] Computing APIx Index for date: {target_date}")

        with get_db_session() as session:
            # 1. Fetch all clean non-outlier quotes for target_date
            stmt = select(CleanFareDB).where(
                CleanFareDB.booking_date == target_date,
                CleanFareDB.is_outlier == False
            )
            fares = session.scalars(stmt).all()

            if not fares:
                logger.warning(f"No clean fare quotes available for {target_date} to compute index.")
                return {"status": "NO_DATA", "date": str(target_date)}

            # 2. Group by Sector -> Advance Window
            # Structure: sector -> window -> list of total_fares
            sector_window_fares: Dict[str, Dict[str, List[float]]] = {}
            for f in fares:
                sec = f.sector
                win = f.advance_window
                if sec not in sector_window_fares:
                    sector_window_fares[sec] = {}
                if win not in sector_window_fares[sec]:
                    sector_window_fares[sec][win] = []
                sector_window_fares[sec][win].append(f.total_fare)

            # 3. Compute Elementary Route-Level Indices
            sector_indices: Dict[str, Dict[str, Any]] = {}
            national_laspeyres_sum = 0.0
            national_jevons_log_sum = 0.0
            national_total_weight = 0.0
            national_all_fares: List[float] = []

            for sec_code, win_map in sector_window_fares.items():
                route_meta = DGCA_ROUTES.get(sec_code, DGCA_ROUTES.get(f"{sec_code.split('-')[1]}-{sec_code.split('-')[0]}"))
                route_weight = route_meta["traffic_weight"] if route_meta else 0.05
                base_fare_p0 = route_meta["base_fare_baseline"] if route_meta else 4800.0

                # Weighted average fare across advance windows for this sector
                sector_window_weighted_fare = 0.0
                sector_window_weight_sum = 0.0
                sec_fares_all = []

                for win_code, fare_list in win_map.items():
                    win_weight = ADVANCE_WINDOWS.get(win_code, {}).get("weight", 0.2)
                    # Elementary Jevons (geometric mean) of quotes in this window
                    log_fares = [math.log(x) for x in fare_list if x > 0]
                    geom_mean = math.exp(sum(log_fares) / len(log_fares)) if log_fares else np.mean(fare_list)

                    sector_window_weighted_fare += (geom_mean * win_weight)
                    sector_window_weight_sum += win_weight
                    sec_fares_all.extend(fare_list)
                    national_all_fares.extend(fare_list)

                # Normalized sector price
                avg_sec_p1 = sector_window_weighted_fare / max(sector_window_weight_sum, 0.001)
                
                # Sector price relative to baseline P0 (Base 100.0)
                sec_index_laspeyres = (avg_sec_p1 / base_fare_p0) * 100.0
                sec_index_jevons = math.exp(math.log(avg_sec_p1 / base_fare_p0)) * 100.0

                sector_indices[sec_code] = {
                    "sector": sec_code,
                    "index_value": round(sec_index_laspeyres, 2),
                    "laspeyres": round(sec_index_laspeyres, 2),
                    "jevons": round(sec_index_jevons, 2),
                    "avg_fare": round(float(np.mean(sec_fares_all)), 2),
                    "median_fare": round(float(np.median(sec_fares_all)), 2),
                    "min_fare": round(float(np.min(sec_fares_all)), 2),
                    "max_fare": round(float(np.max(sec_fares_all)), 2),
                    "quote_count": len(sec_fares_all),
                    "weight": route_weight
                }

                national_laspeyres_sum += (sec_index_laspeyres * route_weight)
                national_jevons_log_sum += (route_weight * math.log(max(sec_index_jevons, 1.0)))
                national_total_weight += route_weight

            # 4. National APIx Composite Index
            national_laspeyres = national_laspeyres_sum / max(national_total_weight, 0.001)
            national_jevons = math.exp(national_jevons_log_sum / max(national_total_weight, 0.001))
            national_fisher = math.sqrt(national_laspeyres * national_jevons)
            national_composite_index = round(national_laspeyres, 2)

            # 5. Fetch previous day's index to calculate DoD change %
            prev_date = target_date - timedelta(days=1)
            prev_stmt = select(APIxIndexDB).where(
                APIxIndexDB.index_date == prev_date,
                APIxIndexDB.sector == "ALL",
                APIxIndexDB.frequency == "daily"
            )
            prev_index_record = session.scalars(prev_stmt).first()
            dod_change = None
            if prev_index_record and prev_index_record.index_value > 0:
                dod_change = round(((national_composite_index - prev_index_record.index_value) / prev_index_record.index_value) * 100.0, 2)

            # 6. Fetch 30 days prior index to calculate MoM change %
            prev_month_date = target_date - timedelta(days=30)
            mom_stmt = select(APIxIndexDB).where(
                APIxIndexDB.index_date == prev_month_date,
                APIxIndexDB.sector == "ALL",
                APIxIndexDB.frequency == "daily"
            )
            mom_record = session.scalars(mom_stmt).first()
            mom_change = None
            if mom_record and mom_record.index_value > 0:
                mom_change = round(((national_composite_index - mom_record.index_value) / mom_record.index_value) * 100.0, 2)

            # 7. Persist to apix_indices table
            session.execute(delete(APIxIndexDB).where(
                APIxIndexDB.index_date == target_date,
                APIxIndexDB.frequency == "daily"
            ))

            # National Record
            nat_obj = APIxIndexDB(
                index_date=target_date,
                frequency="daily",
                sector="ALL",
                advance_window="ALL",
                index_value=national_composite_index,
                laspeyres_value=round(national_laspeyres, 2),
                jevons_value=round(national_jevons, 2),
                fisher_value=round(national_fisher, 2),
                avg_fare=round(float(np.mean(national_all_fares)), 2),
                median_fare=round(float(np.median(national_all_fares)), 2),
                min_fare=round(float(np.min(national_all_fares)), 2),
                max_fare=round(float(np.max(national_all_fares)), 2),
                quote_count=len(national_all_fares),
                dod_change_pct=dod_change,
                mom_change_pct=mom_change
            )
            session.add(nat_obj)

            # Sector Records
            for sec_k, sec_data in sector_indices.items():
                sec_obj = APIxIndexDB(
                    index_date=target_date,
                    frequency="daily",
                    sector=sec_k,
                    advance_window="ALL",
                    index_value=sec_data["index_value"],
                    laspeyres_value=sec_data["laspeyres"],
                    jevons_value=sec_data["jevons"],
                    fisher_value=sec_data["index_value"],
                    avg_fare=sec_data["avg_fare"],
                    median_fare=sec_data["median_fare"],
                    min_fare=sec_data["min_fare"],
                    max_fare=sec_data["max_fare"],
                    quote_count=sec_data["quote_count"],
                    dod_change_pct=0.0
                )
                session.add(sec_obj)

        logger.info(
            f"✅ [IndexCalculator] Daily APIx for {target_date}: {national_composite_index} "
            f"(DoD: {dod_change if dod_change is not None else 0.0}%, Quotes: {len(national_all_fares)})"
        )
        return {
            "date": str(target_date),
            "national_apix": national_composite_index,
            "laspeyres": round(national_laspeyres, 2),
            "jevons": round(national_jevons, 2),
            "fisher": round(national_fisher, 2),
            "dod_change_pct": dod_change,
            "mom_change_pct": mom_change,
            "total_quotes": len(national_all_fares),
            "sector_count": len(sector_indices)
        }
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
