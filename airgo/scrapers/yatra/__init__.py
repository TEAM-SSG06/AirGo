"""
Yatra Airfare Scraper Module (Phase 1 Foundation).
Exposes configuration, route registries, advance purchase date generators,
normalized fare models, price utilities, and centralized browser manager.
"""

from airgo.scrapers.yatra.config import (
    DEFAULT_YATRA_CONFIG,
    YatraScraperConfig,
)
from airgo.scrapers.yatra.routes import (
    INITIAL_ROUTES,
    RouteDefinition,
    RouteRegistry,
    ROUTE_REGISTRY,
    get_route,
    list_routes,
    validate_route,
)
from airgo.scrapers.yatra.dates import (
    STANDARD_HORIZONS,
    SearchWindow,
    generate_search_windows,
    get_travel_date,
    get_window_for_days,
)
from airgo.scrapers.yatra.normalizer import (
    normalize_price,
    normalize_price_float,
)
from airgo.scrapers.yatra.models import (
    DataStatus,
    AvailabilityStatus,
    AntiBotEventType,
    AntiBotEvent,
    NormalizedFareQuote,
)
from airgo.scrapers.yatra.browser import (
    PlaywrightBrowserManager,
    BROWSER_MANAGER,
)
from airgo.scrapers.yatra.selectors import YatraSelectors
from airgo.scrapers.yatra.parser import YatraParser
from airgo.scrapers.yatra.run_manager import YatraRunManager
from airgo.scrapers.yatra.db_adapter import persist_fare_quotes_to_db, ensure_platform_registered
from airgo.scrapers.yatra.checkout import YatraCheckoutVerifier
from airgo.scrapers.yatra.scraper import YatraScraper, run_yatra_harvest

__all__ = [
    # Configuration
    "DEFAULT_YATRA_CONFIG",
    "YatraScraperConfig",
    # Routes
    "INITIAL_ROUTES",
    "RouteDefinition",
    "RouteRegistry",
    "ROUTE_REGISTRY",
    "get_route",
    "list_routes",
    "validate_route",
    # Dates & Horizons
    "STANDARD_HORIZONS",
    "SearchWindow",
    "generate_search_windows",
    "get_travel_date",
    "get_window_for_days",
    # Normalizer
    "normalize_price",
    "normalize_price_float",
    # Data Models & Statuses
    "DataStatus",
    "AvailabilityStatus",
    "AntiBotEventType",
    "AntiBotEvent",
    "NormalizedFareQuote",
    # Browser
    "PlaywrightBrowserManager",
    "BROWSER_MANAGER",
    # Phase 2 Components
    "YatraSelectors",
    "YatraParser",
    "YatraRunManager",
    "persist_fare_quotes_to_db",
    "ensure_platform_registered",
    "YatraScraper",
    "run_yatra_harvest",
    # Phase 3 Components
    "YatraCheckoutVerifier",
]
