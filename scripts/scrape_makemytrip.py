"""
CLI Runner for MakeMyTrip Scraper.
Usage:
    python scripts/scrape_makemytrip.py --top-n 1 --horizons 1 7 15 --visible
    python scripts/scrape_makemytrip.py --horizons 7 --deep-checkout
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from airgo.scrapers.makemytrip.scraper import main

if __name__ == "__main__":
    main()
