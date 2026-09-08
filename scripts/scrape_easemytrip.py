"""
CLI Runner for EaseMyTrip Scraper.
Usage:
    python scripts/scrape_easemytrip.py --top-n 1 --horizons 1,7,15 --visible
    python scripts/scrape_easemytrip.py --routes BOM-DEL --horizons 7 --deep-checkout
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from airgo.scrapers.easemytrip.scraper import main

if __name__ == "__main__":
    main()
