import pytest
import os
import sys
import io
import json
import asyncio
from datetime import datetime, date, timedelta
from patchright.async_api import async_playwright
from airgo.utils.run_manager import create_run_directory, save_run_artifact

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

PROFILE_DIR = os.path.join(os.getcwd(), "runs", "patchright_chrome_profile")

@pytest.mark.anyio
async def test_best_practice_cleartrip():
    # Create isolated timestamped audit folder per RULE 4
    run_dir = create_run_directory("patchright_cleartrip")
    print(f"📁 Created timestamped run folder: {run_dir}")

    os.makedirs(PROFILE_DIR, exist_ok=True)
    tomorrow = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")
    url = f"https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date={tomorrow}&from=BOM&to=DEL&intl=n&page=loaded"

    print(f"Launching Patchright with Best Practice config...")
    print(f"Profile: {PROFILE_DIR}")

    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                channel="msedge",
                headless=False,
                no_viewport=True
            )
            print("Launched with Microsoft Edge channel.")
        except Exception as e:
            print(f"Edge launch note: {e}, falling back to patched Chromium...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                headless=False,
                no_viewport=True
            )

        page = context.pages[0] if context.pages else await context.new_page()

        async def on_response(res):
            if "itinerary/create" in res.url:
                try:
                    body = await res.text()
                    print(f"\n[PATCHRIGHT ITINERARY CREATE RESPONSE {res.status}]:")
                    print(body[:400])
                    save_run_artifact(run_dir, "itinerary_response.json", {"url": res.url, "status": res.status, "body": body[:2000]})
                except Exception as e:
                    print(f"Error reading response: {e}")

        page.on("response", on_response)

        print(f"1. Navigating to Cleartrip Search: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_selector("button:has-text('Book')", timeout=25000)
        await page.wait_for_timeout(3000)

        # Save search results artifacts
        search_png = os.path.join(run_dir, "search_results.png")
        search_html = os.path.join(run_dir, "search_results.html")
        await page.screenshot(path=search_png, full_page=False)
        with open(search_html, "w", encoding="utf-8") as f:
            f.write(await page.content())
        print(f"📸 Search page saved: {search_png}")

        # 1. Click Book
        print("2. Clicking Book...")
        book_btn = page.locator("button:has-text('Book')").first
        await book_btn.click()
        await page.wait_for_timeout(2000)

        # 2. Select fare
        select_btn = page.locator("button:has-text('Select')").first
        if await select_btn.is_visible():
            print("Clicking Select fare button...")
            await select_btn.click()
            await page.wait_for_timeout(1500)

        # 3. Click Continue
        cont_btn = page.locator("button:has-text('Continue')").first
        if await cont_btn.is_visible():
            print("Clicking Continue button...")
            await cont_btn.click()

        await page.wait_for_timeout(8000)

        print(f"\nTotal Open Tabs: {len(context.pages)}")
        review_page = context.pages[-1]
        print(f"Active Tab URL: {review_page.url}")

        # Save checkout review artifacts
        review_png = os.path.join(run_dir, "checkout_review.png")
        review_html = os.path.join(run_dir, "checkout_review.html")
        await review_page.screenshot(path=review_png, full_page=True)
        with open(review_html, "w", encoding="utf-8") as f:
            f.write(await review_page.content())
        print(f"📸 Checkout Review saved: {review_png}")

        # Extract breakdown
        breakdown = await review_page.evaluate(r"""() => {
            const text = document.body.innerText;
            let baseFare = 0.0, taxes = 0.0, grandTotal = 0.0;
            const baseMatch = text.match(/Base\s*Fare[^\d]*([\d,]+)/i);
            if (baseMatch) baseFare = parseFloat(baseMatch[1].replace(/,/g, '')) || 0.0;
            const taxMatch = text.match(/Taxes[^\d]*([\d,]+)/i);
            if (taxMatch) taxes = parseFloat(taxMatch[1].replace(/,/g, '')) || 0.0;
            const totalMatch = text.match(/Total\s*Price[^\d]*([\d,]+)/i);
            if (totalMatch) grandTotal = parseFloat(totalMatch[1].replace(/,/g, '')) || 0.0;
            return { baseFare, taxes, grandTotal: grandTotal || (baseFare + taxes) };
        }""")

        summary_data = {
            "source": "Cleartrip",
            "audit_timestamp": datetime.utcnow().isoformat() + "Z",
            "url": review_page.url,
            "breakdown": breakdown,
            "artifacts": {
                "search_results_png": "search_results.png",
                "search_results_html": "search_results.html",
                "checkout_review_png": "checkout_review.png",
                "checkout_review_html": "checkout_review.html"
            }
        }
        save_run_artifact(run_dir, "run_summary.json", summary_data)
        print(f"✅ Audit run completed! Summary saved to: {os.path.join(run_dir, 'run_summary.json')}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(test_best_practice_cleartrip())
