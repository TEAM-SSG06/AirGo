"""
AirGo CLI Runner for EaseMyTrip Multi-Carrier Full-Day Flight Harvesting across DGCA Routes.
Usage:
    python scripts/run_easemytrip_harvest.py --top-n 1 --horizons 0,1,7,15,30,45
"""

import os
import sys
import asyncio
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from airgo.harvester.easemytrip_harvester import run_easemytrip_harvest


def main():
    parser = argparse.ArgumentParser(description="AirGo EaseMyTrip Full-Day Route Harvester")
    parser.add_argument("--top-n", type=int, default=1, help="Number of top DGCA routes to audit (default: 1)")
    parser.add_argument("--horizons", type=str, default="0,1,7,15,30,45", help="Comma-separated advance horizons in days (default: 0,1,7,15,30,45)")
    parser.add_argument("--csv", type=str, default="data/processed/dgca_top100_route_basket.csv", help="Path to DGCA route basket CSV")

    args = parser.parse_args()
    horizons_list = [int(h.strip()) for h in args.horizons.split(",") if h.strip().isdigit()]
    csv_full_path = os.path.join(ROOT_DIR, args.csv) if not os.path.isabs(args.csv) else args.csv

    asyncio.run(
        run_easemytrip_harvest(
            csv_path=csv_full_path,
            top_n=args.top_n,
            horizons=horizons_list
        )
    )


if __name__ == "__main__":
    main()
