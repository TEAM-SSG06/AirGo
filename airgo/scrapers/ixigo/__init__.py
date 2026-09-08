"""Ixigo-only Playwright scraper."""

__all__ = ["IxigoScraper", "select_least_five", "price_mismatch"]


def __getattr__(name: str):
	if name in __all__:
		from .scraper import IxigoScraper, price_mismatch, select_least_five
		return {"IxigoScraper": IxigoScraper, "select_least_five": select_least_five,
				"price_mismatch": price_mismatch}[name]
	raise AttributeError(name)
