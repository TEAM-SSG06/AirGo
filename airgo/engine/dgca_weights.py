"""
<<<<<<< HEAD
AirGo DGCA Airlines Lookup & Weights.
"""

INDIAN_AIRLINES = {
=======
DGCA (Directorate General of Civil Aviation) Sector Weights & Route Matrix
"""

from typing import Dict, List, Any

# Top domestic city pairs by passenger volume in India
DGCA_ROUTES: Dict[str, Dict[str, Any]] = {
    "DEL-BOM": {
        "origin": "DEL",
        "destination": "BOM",
        "name": "Delhi - Mumbai",
        "annual_pax_approx": 7200000,
        "traffic_weight": 0.165,
        "base_fare_baseline": 4850.0,
        "avg_flight_time_mins": 130,
    },
    "DEL-BLR": {
        "origin": "DEL",
        "destination": "BLR",
        "name": "Delhi - Bengaluru",
        "annual_pax_approx": 5100000,
        "traffic_weight": 0.125,
        "base_fare_baseline": 5400.0,
        "avg_flight_time_mins": 165,
    },
    "BOM-BLR": {
        "origin": "BOM",
        "destination": "BLR",
        "name": "Mumbai - Bengaluru",
        "annual_pax_approx": 3800000,
        "traffic_weight": 0.095,
        "base_fare_baseline": 3950.0,
        "avg_flight_time_mins": 100,
    },
    "DEL-CCU": {
        "origin": "DEL",
        "destination": "CCU",
        "name": "Delhi - Kolkata",
        "annual_pax_approx": 3400000,
        "traffic_weight": 0.085,
        "base_fare_baseline": 5100.0,
        "avg_flight_time_mins": 135,
    },
    "BLR-HYD": {
        "origin": "BLR",
        "destination": "HYD",
        "name": "Bengaluru - Hyderabad",
        "annual_pax_approx": 2900000,
        "traffic_weight": 0.075,
        "base_fare_baseline": 3100.0,
        "avg_flight_time_mins": 75,
    },
    "MAA-DEL": {
        "origin": "MAA",
        "destination": "DEL",
        "name": "Chennai - Delhi",
        "annual_pax_approx": 2800000,
        "traffic_weight": 0.070,
        "base_fare_baseline": 5350.0,
        "avg_flight_time_mins": 170,
    },
    "BOM-GOI": {
        "origin": "BOM",
        "destination": "GOI",
        "name": "Mumbai - Goa",
        "annual_pax_approx": 2600000,
        "traffic_weight": 0.065,
        "base_fare_baseline": 3300.0,
        "avg_flight_time_mins": 75,
    },
    "DEL-HYD": {
        "origin": "DEL",
        "destination": "HYD",
        "name": "Delhi - Hyderabad",
        "annual_pax_approx": 2500000,
        "traffic_weight": 0.065,
        "base_fare_baseline": 4700.0,
        "avg_flight_time_mins": 130,
    },
    "BOM-CCU": {
        "origin": "BOM",
        "destination": "CCU",
        "name": "Mumbai - Kolkata",
        "annual_pax_approx": 2300000,
        "traffic_weight": 0.060,
        "base_fare_baseline": 5600.0,
        "avg_flight_time_mins": 160,
    },
    "DEL-PNQ": {
        "origin": "DEL",
        "destination": "PNQ",
        "name": "Delhi - Pune",
        "annual_pax_approx": 2200000,
        "traffic_weight": 0.055,
        "base_fare_baseline": 4600.0,
        "avg_flight_time_mins": 125,
    },
    "DEL-GAU": {
        "origin": "DEL",
        "destination": "GAU",
        "name": "Delhi - Guwahati",
        "annual_pax_approx": 1900000,
        "traffic_weight": 0.045,
        "base_fare_baseline": 5800.0,
        "avg_flight_time_mins": 150,
    },
    "CCU-BLR": {
        "origin": "CCU",
        "destination": "BLR",
        "name": "Kolkata - Bengaluru",
        "annual_pax_approx": 1800000,
        "traffic_weight": 0.045,
        "base_fare_baseline": 5200.0,
        "avg_flight_time_mins": 155,
    },
    "MAA-BOM": {
        "origin": "MAA",
        "destination": "BOM",
        "name": "Chennai - Mumbai",
        "annual_pax_approx": 1900000,
        "traffic_weight": 0.050,
        "base_fare_baseline": 3800.0,
        "avg_flight_time_mins": 115,
    }
}

# Normalize weights so sum is 1.0
TOTAL_RAW_WEIGHT = sum(r["traffic_weight"] for r in DGCA_ROUTES.values())
for route in DGCA_ROUTES.values():
    route["traffic_weight"] = round(route["traffic_weight"] / TOTAL_RAW_WEIGHT, 4)

ADVANCE_WINDOWS: Dict[str, Dict[str, Any]] = {
    "T+1": {
        "days": 1,
        "description": "Next-Day Travel",
        "weight": 0.28,
        "target_lead_days": 1
    },
    "T+7": {
        "days": 7,
        "description": "1-Week Advance",
        "weight": 0.32,
        "target_lead_days": 7
    },
    "T+15": {
        "days": 15,
        "description": "2-Weeks Advance",
        "weight": 0.22,
        "target_lead_days": 15
    },
    "T+30": {
        "days": 30,
        "description": "1-Month Advance",
        "weight": 0.12,
        "target_lead_days": 30
    },
    "T+45": {
        "days": 45,
        "description": "45-Days Advance",
        "weight": 0.06,
        "target_lead_days": 45
    }
}

INDIAN_AIRLINES: Dict[str, str] = {
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
    "6E": "IndiGo",
    "AI": "Air India",
    "IX": "Air India Express",
    "SG": "SpiceJet",
    "QP": "Akasa Air",
<<<<<<< HEAD
    "UK": "Vistara",
    "IC": "Fly91",
    "S5": "Star Air",
    "9I": "Alliance Air"
=======
    "I5": "AIX Connect"
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
}
