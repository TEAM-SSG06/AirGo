"""
EaseMyTrip Harvester Configuration & Utilities.
Provides city mappings, search URL generation, and DGCA route basket loading.
"""

import os
import csv
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

CITY_NAMES: Dict[str, str] = {
    "DEL": "Delhi", "BOM": "Mumbai", "BLR": "Bengaluru", "HYD": "Hyderabad",
    "CCU": "Kolkata", "MAA": "Chennai", "GOI": "Goa", "GOX": "Goa",
    "PNQ": "Pune", "AMD": "Ahmedabad", "COK": "Kochi", "GAU": "Guwahati",
    "LKO": "Lucknow", "PAT": "Patna", "JAI": "Jaipur", "SXR": "Srinagar",
    "BBI": "Bhubaneswar", "IXC": "Chandigarh", "IXR": "Ranchi", "VTZ": "Visakhapatnam",
    "TRV": "Thiruvananthapuram", "VNS": "Varanasi", "IDR": "Indore", "NAG": "Nagpur",
    "ATQ": "Amritsar", "IXB": "Bagdogra", "BDQ": "Vadodara", "UDR": "Udaipur"
}

DEFAULT_HORIZONS = [1, 7, 15, 30, 45]


def build_search_url(origin: str, dest: str, date_dmy: str) -> str:
    """
    Builds the pipe-delimited search URL with full city-country descriptors
    required by EaseMyTrip's Angular search engine.
    Example: srch=DEL-Delhi-India|BOM-Mumbai-India|15/09/2026
    """
    orig_city = CITY_NAMES.get(origin, origin)
    dest_city = CITY_NAMES.get(dest, dest)
    return (
        f"https://flight.easemytrip.com/FlightList/Index?"
        f"srch={origin}-{orig_city}-India|{dest}-{dest_city}-India|{date_dmy}"
        f"&px=1-0-0&cbn=0&ar=undefined&isDM=true&IsDoubleSeat=false&C=IN"
    )


def load_route_basket(csv_path: str, top_n: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Loads top domestic routes from the DGCA route basket CSV.
    Falls back to Tier-1 trunk routes (BOM-DEL, BLR-DEL) if CSV is unavailable.
    """
    routes: List[Dict[str, Any]] = []

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pair = row.get("route", "").strip().upper()
                if "-" in pair:
                    origin, dest = pair.split("-", 1)
                    routes.append({
                        "rank": int(row.get("rank", len(routes) + 1)),
                        "route": pair,
                        "origin": origin.strip(),
                        "destination": dest.strip(),
                        "city1": row.get("city1", CITY_NAMES.get(origin.strip(), origin.strip())),
                        "city2": row.get("city2", CITY_NAMES.get(dest.strip(), dest.strip())),
                        "tier": row.get("tier", "Tier 1")
                    })
    else:
        # Fallback trunk routes
        routes = [
            {"rank": 1, "route": "BOM-DEL", "origin": "BOM", "destination": "DEL", "city1": "Mumbai", "city2": "Delhi", "tier": "Tier 1"},
            {"rank": 2, "route": "BLR-DEL", "origin": "BLR", "destination": "DEL", "city1": "Bengaluru", "city2": "Delhi", "tier": "Tier 1"},
            {"rank": 3, "route": "BLR-BOM", "origin": "BLR", "destination": "BOM", "city1": "Bengaluru", "city2": "Mumbai", "tier": "Tier 1"}
        ]

    if top_n and top_n > 0:
        routes = routes[:top_n]

    return routes


def calculate_horizon_dates(horizons: List[int]) -> List[Dict[str, Any]]:
    """
    Calculates target departure dates for specified advance horizons (T+X days).
    """
    today = date.today()
    results = []
    for h in horizons:
        dept_date = today + timedelta(days=h)
        results.append({
            "horizon_days": h,
            "horizon_label": f"T+{h}",
            "date_obj": dept_date,
            "date_dmy": dept_date.strftime("%d/%m/%Y"),
            "date_iso": dept_date.isoformat()
        })
    return results
