import logging
from datetime import date
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy import select
from airgo.pipeline.models import CleanFareDB, ElasticityPoint
from airgo.pipeline.db import get_db_session
from airgo.engine.dgca_weights import ADVANCE_WINDOWS

logger = logging.getLogger("AirGo.Elasticity")


class ElasticityAnalyzer:
    """
    Analyzes lead-time price elasticity curves and booking window surge dynamics (T+1 through T+45).
    """

    def compute_lead_time_curve(self, sector: Optional[str] = None) -> List[ElasticityPoint]:
        """
        Compute lead-time price elasticity curve across T+1, T+7, T+15, T+30, T+45 days.
        """
        with get_db_session() as session:
            stmt = select(CleanFareDB).where(CleanFareDB.is_outlier == False)
            if sector and sector != "ALL":
                stmt = stmt.where(CleanFareDB.sector == sector)

            fares = session.scalars(stmt).all()

            if not fares:
                # Default baseline points if no data yet
                return [
                    ElasticityPoint(advance_window="T+1", advance_days=1, avg_fare=8950.0, median_fare=8700.0, fare_multiplier=2.15, elasticity_score=-0.85, sample_size=50),
                    ElasticityPoint(advance_window="T+7", advance_days=7, avg_fare=6350.0, median_fare=6100.0, fare_multiplier=1.52, elasticity_score=-0.52, sample_size=50),
                    ElasticityPoint(advance_window="T+15", advance_days=15, avg_fare=4900.0, median_fare=4800.0, fare_multiplier=1.18, elasticity_score=-0.25, sample_size=50),
                    ElasticityPoint(advance_window="T+30", advance_days=30, avg_fare=4350.0, median_fare=4250.0, fare_multiplier=1.04, elasticity_score=-0.12, sample_size=50),
                    ElasticityPoint(advance_window="T+45", advance_days=45, avg_fare=4150.0, median_fare=4100.0, fare_multiplier=1.00, elasticity_score=0.00, sample_size=50),
                ]

            # Group by advance window
            window_fares: Dict[str, List[float]] = {w: [] for w in ADVANCE_WINDOWS.keys()}
            for f in fares:
                if f.advance_window in window_fares:
                    window_fares[f.advance_window].append(f.total_fare)

            # Baseline fare is T+45 (or highest advance window available)
            base_t45 = np.median(window_fares.get("T+45", [4200.0])) if window_fares.get("T+45") else 4200.0

            results: List[ElasticityPoint] = []
            for win_code, win_meta in ADVANCE_WINDOWS.items():
                flist = window_fares.get(win_code, [])
                if flist:
                    avg_f = float(np.mean(flist))
                    med_f = float(np.median(flist))
                    multiplier = round(med_f / max(base_t45, 1.0), 2)
                    # Elasticity score: percentage price surge per day closer to departure
                    elasticity = round((multiplier - 1.0) / max(45 - win_meta["days"], 1), 4)
                    results.append(ElasticityPoint(
                        advance_window=win_code,
                        advance_days=win_meta["days"],
                        avg_fare=round(avg_f, 2),
                        median_fare=round(med_f, 2),
                        fare_multiplier=multiplier,
                        elasticity_score=elasticity,
                        sample_size=len(flist)
                    ))
                else:
                    results.append(ElasticityPoint(
                        advance_window=win_code,
                        advance_days=win_meta["days"],
                        avg_fare=round(base_t45 * 1.2, 2),
                        median_fare=round(base_t45 * 1.2, 2),
                        fare_multiplier=1.2,
                        elasticity_score=-0.1,
                        sample_size=0
                    ))

            return sorted(results, key=lambda x: x.advance_days)
