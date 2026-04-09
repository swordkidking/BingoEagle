"""
Scrape WeChat article and WorldMonitor.app using Playwright
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        results = {}

        # ── 1. WeChat article ──────────────────────────────────────────────
        print("=== Fetching WeChat article ===")
        try:
            await page.goto("https://mp.weixin.qq.com/s/5M28kE-fgNwvVeqmm8r2QA", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            title = await page.title()
            text = await page.inner_text("body")
            results["wechat"] = {"title": title, "text": text[:8000]}
            print(f"WeChat title: {title}")
            print(text[:2000])
        except Exception as e:
            print(f"WeChat error: {e}")
            results["wechat"] = {"error": str(e)}

        # ── 2. WorldMonitor homepage ───────────────────────────────────────
        print("\n=== Fetching WorldMonitor homepage ===")
        try:
            await page.goto("https://www.worldmonitor.app", wait_until="networkidle", timeout=40000)
            await asyncio.sleep(5)
            title = await page.title()
            text = await page.inner_text("body")
            results["homepage"] = {"title": title, "text": text[:10000]}
            print(f"Homepage title: {title}")
            print(text[:3000])
        except Exception as e:
            print(f"Homepage error: {e}")
            results["homepage"] = {"error": str(e)}

        # ── 3. WorldMonitor /pro page ──────────────────────────────────────
        print("\n=== Fetching WorldMonitor /pro ===")
        try:
            await page.goto("https://www.worldmonitor.app/pro", wait_until="networkidle", timeout=40000)
            await asyncio.sleep(4)
            text = await page.inner_text("body")
            results["pro"] = {"text": text[:10000]}
            print(text[:3000])
        except Exception as e:
            print(f"Pro page error: {e}")
            results["pro"] = {"error": str(e)}

        await browser.close()

        # Save full results
        with open("/tmp/wm_scrape_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\n✅ Results saved to /tmp/wm_scrape_results.json")

asyncio.run(scrape())
