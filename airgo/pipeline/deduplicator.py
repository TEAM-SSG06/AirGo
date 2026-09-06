"""
AirGo Airfare Canonical Deduplication Engine.
Groups raw observations across platforms to form single canonical airfare products.
Calculates price spread (min, avg, max), identifies cheapest platform, and preserves multi-OTA auditability.
"""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from airgo.pipeline.models import RawObservationSchema, CanonicalFareSchema

logger = logging.getLogger("AirGo.Deduplicator")


class AirfareDeduplicator:
    """
    Deduplicates raw airfare observations across multiple platforms (OTAs and Airlines)
    into clean canonical airfare records.
    """

    def __init__(self, iqr_multiplier: float = 2.0, min_quotes_for_outlier: int = 4):
        self.iqr_multiplier = iqr_multiplier
        self.min_quotes_for_outlier = min_quotes_for_outlier

    def deduplicate(self, raw_quotes: List[RawObservationSchema]) -> List[CanonicalFareSchema]:
        """
        Groups raw quotes by:
        (origin, destination, travel_date, carrier, flight_number, departure_time, fare_class)
        and builds canonical records.
        """
        if not raw_quotes:
            logger.info("No raw quotes provided for deduplication.")
            return []

        # 1. Group raw quotes by canonical key
        groups: Dict[Tuple, List[RawObservationSchema]] = {}
        for q in raw_quotes:
            dep_time_clean = q.departure_time.strip() if q.departure_time else "00:00"
            key = (
                q.origin.upper(),
                q.destination.upper(),
                q.travel_date,
                q.carrier.strip(),
                q.flight_number.strip().upper(),
                dep_time_clean,
                q.fare_class or "Economy"
            )
            if key not in groups:
                groups[key] = []
            groups[key].append(q)

        canonical_records: List[CanonicalFareSchema] = []

        # 2. Build canonical records per group
        for key, group in groups.items():
            origin, dest, travel_date, carrier, flight_no, dep_time, fare_class = key
            
            # Sort group by total fare ASC
            group_sorted = sorted(group, key=lambda x: x.total_fare)
            cheapest_quote = group_sorted[0]
            
            fares = [x.total_fare for x in group_sorted]
            min_fare = min(fares)
            max_fare = max(fares)
            avg_fare = round(float(np.mean(fares)), 2)
            
            all_platforms = sorted(list(set(x.platform for x in group_sorted)))
            observed_platforms_str = ", ".join(all_platforms)
            
            base_f = cheapest_quote.base_fare if cheapest_quote.base_fare is not None else round(min_fare * 0.75, 2)
            taxes_f = cheapest_quote.taxes if cheapest_quote.taxes is not None else round(min_fare - base_f, 2)
            fees_f = cheapest_quote.fees if cheapest_quote.fees is not None else 0.0
            conv_fee = cheapest_quote.convenience_fee or 0.0

            canonical_id = f"{origin}-{dest}_{travel_date.isoformat()}_{carrier}_{flight_no}_{dep_time.replace(':', '')}_{fare_class}"
            
            canonical_records.append(CanonicalFareSchema(
                canonical_id=canonical_id,
                route=f"{origin}-{dest}",
                origin=origin,
                destination=dest,
                carrier=carrier,
                flight_number=flight_no,
                observation_date=cheapest_quote.observation_date,
                travel_date=travel_date,
                departure_time=dep_time,
                arrival_time=cheapest_quote.arrival_time,
                advance_purchase_days=cheapest_quote.advance_purchase_days,
                advance_purchase_window=cheapest_quote.advance_purchase_window,
                fare_class=fare_class,
                fare_family=cheapest_quote.fare_family or "Standard",
                stops=cheapest_quote.stops or 0,
                min_total_fare=min_fare,
                avg_total_fare=avg_fare,
                max_total_fare=max_fare,
                base_fare=base_f,
                taxes=taxes_f,
                fees=fees_f,
                convenience_fee=conv_fee,
                cheapest_platform=cheapest_quote.platform,
                platform_count=len(all_platforms),
                observed_platforms=observed_platforms_str
            ))

        # 3. Detect statistical outliers across route & advance window groups
        route_window_map: Dict[Tuple[str, str], List[CanonicalFareSchema]] = {}
        for c in canonical_records:
            rw_key = (c.route, c.advance_purchase_window)
            if rw_key not in route_window_map:
                route_window_map[rw_key] = []
            route_window_map[rw_key].append(c)

        for (route, window), items in route_window_map.items():
            if len(items) >= self.min_quotes_for_outlier:
                all_min_fares = [x.min_total_fare for x in items]
                q25, q75 = np.percentile(all_min_fares, [25, 75])
                iqr = q75 - q25
                lower_bound = max(800.0, q25 - (self.iqr_multiplier * iqr))
                upper_bound = q75 + (self.iqr_multiplier * iqr)

                for item in items:
                    if item.min_total_fare < lower_bound or item.min_total_fare > upper_bound:
                        # Mark outlier attribute if needed on Schema/DB level
                        pass

        logger.info(
            f"✅ [Deduplicator] Processed {len(raw_quotes)} raw observations into {len(canonical_records)} canonical airfare records."
        )
        return canonical_records
