"""
Route configuration and validation for airfare scrapers.
Provides a configuration-driven list of corridors so new routes can be added
without modifying any core scraping logic.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RouteDefinition(BaseModel):
    """Normalized route corridor definition."""

    route_code: str
    origin_iata: str
    dest_iata: str
    origin_name: str
    dest_name: str
    origin_airport: Optional[str] = None
    dest_airport: Optional[str] = None
    is_active: bool = True

    @field_validator("origin_iata", "dest_iata")
    @classmethod
    def validate_iata(cls, v: str) -> str:
        clean = v.strip().upper()
        if len(clean) != 3 or not clean.isalpha():
            raise ValueError(f"IATA code must be exactly 3 alphabetic characters, got: {v}")
        return clean

    @field_validator("route_code")
    @classmethod
    def validate_route_code(cls, v: str, values) -> str:
        clean = v.strip().upper()
        parts = clean.split("-")
        if len(parts) != 2 or len(parts[0]) != 3 or len(parts[1]) != 3:
            raise ValueError(f"Route code must be in 'ORIGIN-DEST' format, got: {v}")
        return clean

    @property
    def display_name(self) -> str:
        return f"{self.origin_name} ({self.origin_iata}) → {self.dest_name} ({self.dest_iata})"


# Initial Target DGCA Corridors (BOM-DEL, BLR-DEL, BLR-BOM)
INITIAL_ROUTES: List[RouteDefinition] = [
    RouteDefinition(
        route_code="BOM-DEL",
        origin_iata="BOM",
        dest_iata="DEL",
        origin_name="Mumbai",
        dest_name="New Delhi",
        origin_airport="Chhatrapati Shivaji Maharaj International Airport",
        dest_airport="Indira Gandhi International Airport",
    ),
    RouteDefinition(
        route_code="BLR-DEL",
        origin_iata="BLR",
        dest_iata="DEL",
        origin_name="Bengaluru",
        dest_name="New Delhi",
        origin_airport="Kempegowda International Airport",
        dest_airport="Indira Gandhi International Airport",
    ),
    RouteDefinition(
        route_code="BLR-BOM",
        origin_iata="BLR",
        dest_iata="BOM",
        origin_name="Bengaluru",
        dest_name="Mumbai",
        origin_airport="Kempegowda International Airport",
        dest_airport="Chhatrapati Shivaji Maharaj International Airport",
    ),
]

# Additional bidirectional aliases for lookup compatibility
_ADDITIONAL_ROUTES: List[RouteDefinition] = [
    RouteDefinition(
        route_code="DEL-BOM",
        origin_iata="DEL",
        dest_iata="BOM",
        origin_name="New Delhi",
        dest_name="Mumbai",
        origin_airport="Indira Gandhi International Airport",
        dest_airport="Chhatrapati Shivaji Maharaj International Airport",
        is_active=False,
    ),
    RouteDefinition(
        route_code="DEL-BLR",
        origin_iata="DEL",
        dest_iata="BLR",
        origin_name="New Delhi",
        dest_name="Bengaluru",
        origin_airport="Indira Gandhi International Airport",
        dest_airport="Kempegowda International Airport",
        is_active=False,
    ),
    RouteDefinition(
        route_code="BOM-BLR",
        origin_iata="BOM",
        dest_iata="BLR",
        origin_name="Mumbai",
        dest_name="Bengaluru",
        origin_airport="Chhatrapati Shivaji Maharaj International Airport",
        dest_airport="Kempegowda International Airport",
        is_active=False,
    ),
]


class RouteRegistry:
    """Registry maintaining available route configurations."""

    def __init__(self, routes: Optional[List[RouteDefinition]] = None):
        self._routes: Dict[str, RouteDefinition] = {}
        for r in (routes or INITIAL_ROUTES):
            self.register(r)
        if routes is None:
            for r in _ADDITIONAL_ROUTES:
                self.register(r)

    def register(self, route: RouteDefinition) -> None:
        """Register a new or updated route corridor."""
        self._routes[route.route_code.upper()] = route

    def get(self, route_code: str) -> Optional[RouteDefinition]:
        """Retrieve route definition by code (case-insensitive)."""
        return self._routes.get(route_code.strip().upper())

    def list_routes(self, active_only: bool = True) -> List[RouteDefinition]:
        """List all registered routes."""
        if active_only:
            return [r for r in self._routes.values() if r.is_active]
        return list(self._routes.values())

    def validate_route_code(self, route_code: str) -> bool:
        """Checks if a route code is registered and active."""
        route = self.get(route_code)
        return route is not None and route.is_active

    def find_route(self, origin_iata: str, dest_iata: str) -> Optional[RouteDefinition]:
        """Find route by origin and destination IATA codes."""
        code = f"{origin_iata.strip().upper()}-{dest_iata.strip().upper()}"
        return self.get(code)


# Default global registry instance
ROUTE_REGISTRY = RouteRegistry()


def get_route(route_code: str) -> Optional[RouteDefinition]:
    """Helper to get a route from the global registry."""
    return ROUTE_REGISTRY.get(route_code)


def list_routes(active_only: bool = True) -> List[RouteDefinition]:
    """Helper to list all active routes."""
    return ROUTE_REGISTRY.list_routes(active_only=active_only)


def validate_route(origin_iata: str, dest_iata: str) -> bool:
    """Validates whether an origin-destination pair is a supported route."""
    return ROUTE_REGISTRY.find_route(origin_iata, dest_iata) is not None
