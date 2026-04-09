"""
Get more docs detail pages
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_page(page, url, name, wait=5):
    print(f"\n=== {name} ===")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(wait)
        text = await page.inner_text("body")
        print(text[:4000])
        return {"url": url, "text": text[:12000]}
    except Exception as e:
        print(f"Error: {e}")
        return {"url": url, "error": str(e)}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        results = {}

        pages = [
            ("https://www.worldmonitor.app/docs/features-interface", "features_interface"),
            ("https://www.worldmonitor.app/docs/signal-intelligence", "signal_intel"),
            ("https://www.worldmonitor.app/docs/geographic-convergence", "geo_convergence"),
            ("https://www.worldmonitor.app/docs/strategic-risk", "strategic_risk"),
            ("https://www.worldmonitor.app/docs/map-engine", "map_engine"),
            ("https://www.worldmonitor.app/docs/military-tracking", "military_tracking"),
            ("https://www.worldmonitor.app/docs/maritime-intelligence", "maritime"),
            ("https://www.worldmonitor.app/docs/natural-disaster-tracking", "disasters"),
            ("https://www.worldmonitor.app/docs/infrastructure-cascade", "infra_cascade"),
            ("https://www.worldmonitor.app/docs/finance-market-data", "finance_data"),
            ("https://www.worldmonitor.app/docs/premium-finance", "premium_finance"),
            ("https://www.worldmonitor.app/docs/desktop-application", "desktop_app"),
            ("https://www.worldmonitor.app/docs/data-sources", "data_sources"),
            ("https://www.worldmonitor.app/docs/design-philosophy", "design_philosophy"),
            ("https://www.worldmonitor.app/docs/hotspots-navigation", "hotspots"),
            ("https://www.worldmonitor.app/docs/orbital-surveillance", "orbital"),
            ("https://www.worldmonitor.app/docs/webcam-layer", "webcam"),
        ]

        for url, name in pages:
            results[name] = await scrape_page(page, url, name, wait=4)

        await browser.close()

        with open("/tmp/wm_docs2.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\n✅ Saved to /tmp/wm_docs2.json")

asyncio.run(main())
