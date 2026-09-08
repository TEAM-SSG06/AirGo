"""
Central Scraper Registry & Unified Dispatcher for AirGo.
Provides a single-threaded async dispatch function to execute any supported scraper.
Zero threads, zero workers, purely standard async coroutine flow.
"""

from typing import List, Dict, Any, Optional

SUPPORTED_PLATFORMS = [
    "makemytrip",
    "easemytrip",
    "cleartrip"
]


async def run_scraper(
    platform: str,
    route: str = "BOM-DEL",
    horizons: Optional[List[int]] = None,
    headless: bool = True,
    deep_checkout: bool = False,
    runs_dir: str = "runs"
) -> List[Dict[str, Any]]:
    """
    Executes the specified scraper on the current single-threaded asyncio event loop.
    Returns the extracted list of flight quote dictionaries in-memory.
    """
    plat = platform.lower().strip()
    active_horizons = horizons or [7]

    parts = route.upper().split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid route format '{route}'. Expected format 'ORIGIN-DEST' (e.g. 'BOM-DEL').")
    origin, dest = parts[0].strip(), parts[1].strip()
    route_obj = [{"route": f"{origin}-{dest}", "origin": origin, "destination": dest}]

    if plat in ("makemytrip", "mmt"):
        from airgo.scrapers.makemytrip import MakeMyTripScraper
        scraper = MakeMyTripScraper(
            routes=route_obj,
            horizons=active_horizons,
            headless=headless,
            deep_checkout=deep_checkout,
            runs_dir=runs_dir
        )
        await scraper.harvest_all()
        return scraper.all_extracted_quotes

    elif plat in ("easemytrip", "emt"):
        from airgo.scrapers.easemytrip import EaseMyTripScraper
        scraper = EaseMyTripScraper(runs_dir=runs_dir)
        quotes = await scraper.run(
            routes=route_obj,
            horizons=active_horizons,
            deep_checkout=deep_checkout,
            visible=not headless
        )
        return quotes or []

    elif plat == "cleartrip":
        from airgo.scrapers.cleartrip.scraper import CleartripScraper
        scraper = CleartripScraper(
            route=f"{origin}-{dest}",
            horizons=active_horizons,
            headless=headless,
            runs_dir=runs_dir
        )
        return await scraper.run()

    else:
        raise ValueError(
            f"Unsupported platform '{platform}'. Supported platforms are: {', '.join(SUPPORTED_PLATFORMS)}"
        )
