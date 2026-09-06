"""
AirGo Daily Airfare Aggregation Engine.
Computes analytics-ready daily market aggregates by route, observation_date, advance_purchase_window, carrier, and platform.
Used directly by Airfare Price Index (APIx) and market load factor modules.
"""

import logging
from typing import List, Dict, Tuple, Any
import numpy as np
from airgo.pipeline.models import RawObservationSchema, DailyAirfareAggregateSchema

logger = logging.getLogger("AirGo.Aggregator")


class AirfareAggregator:
    """
    Calculates summary market metrics for daily airfare observations.
    """

    def compute_daily_aggregates(self, raw_quotes: List[RawObservationSchema]) -> List[DailyAirfareAggregateSchema]:
        if not raw_quotes:
            logger.info("No raw quotes to aggregate.")
            return []

        # 1. Group quotes by (route, observation_date, advance_purchase_window, carrier, platform)
        groups: Dict[Tuple[str, Any, str, str, str], List[RawObservationSchema]] = {}

        def add_to_group(key, item):
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        for q in raw_quotes:
            obs_date = q.observation_date
            route = q.route
            window = q.advance_purchase_window
            carrier = q.carrier
            platform = q.platform

            # Specific carrier & platform group
            add_to_group((route, obs_date, window, carrier, platform), q)
            # Route-Window level overall group
            add_to_group((route, obs_date, window, "ALL", "ALL"), q)
            # Route-Window-Carrier level group
            add_to_group((route, obs_date, window, carrier, "ALL"), q)

        aggregates: List[DailyAirfareAggregateSchema] = []

        for key, items in groups.items():
            route, obs_date, window, carrier, platform = key
            
            fares = [x.total_fare for x in items]
            base_fares = [x.base_fare for x in items if x.base_fare is not None]
            taxes = [x.taxes for x in items if x.taxes is not None]
            fees = [x.fees for x in items if x.fees is not None]

            avg_fare = round(float(np.mean(fares)), 2)
            med_fare = round(float(np.median(fares)), 2)
            min_fare = round(float(np.min(fares)), 2)
            max_fare = round(float(np.max(fares)), 2)

            avg_base = round(float(np.mean(base_fares)), 2) if base_fares else round(avg_fare * 0.75, 2)
            avg_tax = round(float(np.mean(taxes)), 2) if taxes else round(avg_fare - avg_base, 2)
            avg_fee = round(float(np.mean(fees)), 2) if fees else 0.0

            unique_flights_count = len(set(x.flight_number for x in items))
            agg_key = f"{route}_{obs_date.isoformat()}_{window}_{carrier}_{platform}"

            aggregates.append(DailyAirfareAggregateSchema(
                aggregate_key=agg_key,
                route=route,
                observation_date=obs_date,
                advance_purchase_window=window,
                carrier=carrier,
                platform=platform,
                observation_count=len(items),
                unique_flights=unique_flights_count,
                average_fare=avg_fare,
                median_fare=med_fare,
                min_fare=min_fare,
                max_fare=max_fare,
                average_base_fare=avg_base,
                average_taxes=avg_tax,
                average_fees=avg_fee
            ))

        logger.info(f"✅ [Aggregator] Generated {len(aggregates)} daily aggregate records.")
        return aggregates
