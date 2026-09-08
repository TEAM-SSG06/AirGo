"""
Centralized Playwright browser lifecycle manager.
Controls headless vs. headed modes for visual debugging, initializes
isolated browser contexts, and ensures deterministic resource cleanup.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Optional
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    ViewportSize,
)

from airgo.scrapers.yatra.config import DEFAULT_YATRA_CONFIG

logger = logging.getLogger("AirGo.Yatra.Browser")

# Default desktop viewport and client emulation attributes
DEFAULT_VIEWPORT: ViewportSize = {"width": 1920, "height": 1080}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
DEFAULT_LOCALE = "en-IN"
DEFAULT_TIMEZONE = "Asia/Kolkata"

DEFAULT_CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--window-size=1920,1080",
]


class PlaywrightBrowserManager:
    """
    Centralized controller for browser lifecycles and page contexts.
    Guarantees that browser instances are properly recycled and closed.
    """

    def __init__(
        self,
        headless: Optional[bool] = None,
        timeout_ms: Optional[int] = None,
        slow_mo_ms: Optional[int] = None,
    ):
        self.headless = headless if headless is not None else DEFAULT_YATRA_CONFIG.headless
        self.timeout_ms = timeout_ms or DEFAULT_YATRA_CONFIG.browser_timeout_ms
        self.slow_mo_ms = slow_mo_ms

    @asynccontextmanager
    async def launch_browser(
        self,
        headless: Optional[bool] = None,
        slow_mo_ms: Optional[int] = None,
    ) -> AsyncGenerator[Browser, None]:
        """Launches a centralized Chromium browser instance."""
        use_headless = headless if headless is not None else self.headless
        active_slow_mo = (
            0 if use_headless else (slow_mo_ms if slow_mo_ms is not None else (self.slow_mo_ms or DEFAULT_YATRA_CONFIG.slow_mo_ms))
        )
        mode_label = "⚡ Headless Mode (Invisible Background)" if use_headless else f"🖥️ Headed Visible Mode (Chromium GUI Window, slow_mo={active_slow_mo}ms)"
        logger.info(f"Launching Playwright Chromium: {mode_label}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=use_headless,
                slow_mo=active_slow_mo,
                args=DEFAULT_CHROMIUM_ARGS,
            )
            try:
                yield browser
            finally:
                logger.info("Closing Playwright Chromium browser")
                await browser.close()

    @asynccontextmanager
    async def new_context(
        self,
        browser: Browser,
        user_agent: Optional[str] = None,
        viewport: Optional[ViewportSize] = None
    ) -> AsyncGenerator[BrowserContext, None]:
        """Creates an isolated browser context with realistic fingerprinting."""
        context = await browser.new_context(
            viewport=viewport or DEFAULT_VIEWPORT,
            user_agent=user_agent or DEFAULT_USER_AGENT,
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
        )
        context.set_default_timeout(self.timeout_ms)
        try:
            yield context
        finally:
            await context.close()

    @asynccontextmanager
    async def new_page(
        self,
        headless: Optional[bool] = None,
        slow_mo_ms: Optional[int] = None,
        user_agent: Optional[str] = None
    ) -> AsyncGenerator[Page, None]:
        """Convenience context manager launching a fresh browser, context, and page."""
        async with self.launch_browser(headless=headless, slow_mo_ms=slow_mo_ms) as browser:
            async with self.new_context(browser, user_agent=user_agent) as context:
                page = await context.new_page()
                try:
                    yield page
                finally:
                    await page.close()


# Default global manager instance
BROWSER_MANAGER = PlaywrightBrowserManager()
