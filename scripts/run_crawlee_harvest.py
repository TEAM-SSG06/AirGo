"""
AirGo CLI Runner for Crawlee-Driven Multi-Carrier Flight Harvesting.
Usage:
    python scripts/run_crawlee_harvest.py --platform cleartrip --top-n 1 --horizons 1 --flights-per-route 3
    python scripts/run_crawlee_harvest.py --platform easemytrip --top-n 2 --horizons 1,7 --flights-per-route 3
"""

import os
import sys
import asyncio
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from airgo.harvester.crawlee_harvester import CrawleeFlightHarvester


def main():
    parser = argparse.ArgumentParser(description="AirGo Crawlee Multi-Carrier Route Harvester")
    parser.add_argument("--platform", type=str, choices=["cleartrip", "easemytrip"], default="cleartrip", help="Target platform (default: cleartrip)")
    parser.add_argument("--top-n", type=int, default=1, help="Number of top DGCA routes to audit (default: 1)")
    parser.add_argument("--horizons", type=str, default="1", help="Comma-separated advance horizons in days (e.g. 1,7,15)")
    parser.add_argument("--flights-per-route", type=int, default=3, help="Number of flights per route-horizon with carrier diversity (default: 3)")
    parser.add_argument("--concurrency", type=int, default=1, help="Maximum concurrent browser pages (default: 1)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless (default: True)")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run browser in visible mode")
    parser.add_argument("--csv", type=str, default="data/processed/dgca_top100_route_basket.csv", help="Path to DGCA route basket CSV")

    args = parser.parse_args()
    horizons_list = [int(h.strip()) for h in args.horizons.split(",") if h.strip().isdigit()]
    csv_full_path = os.path.join(ROOT_DIR, args.csv) if not os.path.isabs(args.csv) else args.csv

    harvester = CrawleeFlightHarvester(
        platform=args.platform,
        flights_per_route=args.flights_per_route,
        max_concurrency=args.concurrency,
        headless=args.headless
    )

    asyncio.run(
        harvester.run(
            csv_path=csv_full_path,
            top_n=args.top_n,
            horizons=horizons_list
        )
    )


if __name__ == "__main__":
    main()
