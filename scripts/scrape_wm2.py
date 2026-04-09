"""
Scrape WorldMonitor.app using Playwright - deep exploration
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible for debugging
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        results = {}

        # ── 1. WorldMonitor homepage ───────────────────────────────────────
        print("=== Fetching WorldMonitor homepage ===")
        try:
            await page.goto("https://www.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(10)  # wait for React to render
            title = await page.title()
            text = await page.inner_text("body")

            # Also get all clickable nav items
            nav_items = await page.query_selector_all("nav a, nav button, [role='navigation'] a, [role='navigation'] button")
            nav_texts = []
            for item in nav_items:
                t = await item.inner_text()
                if t.strip():
                    nav_texts.append(t.strip())

            # Get all button/tab labels
            buttons = await page.query_selector_all("button, [role='tab'], [role='menuitem']")
            btn_texts = []
            for btn in buttons[:60]:
                t = await btn.inner_text()
                if t.strip():
                    btn_texts.append(t.strip())

            # Screenshot
            await page.screenshot(path="/tmp/wm_homepage.png", full_page=False)

            results["homepage"] = {
                "title": title,
                "text": text[:15000],
                "nav_items": nav_texts,
                "buttons": btn_texts
            }
            print(f"Title: {title}")
            print(f"Nav: {nav_texts}")
            print(f"Buttons: {btn_texts[:30]}")
            print("Text preview:")
            print(text[:5000])
        except Exception as e:
            print(f"Homepage error: {e}")
            results["homepage"] = {"error": str(e)}

        # ── 2. Pro page ───────────────────────────────────────────────────
        print("\n=== Fetching /pro ===")
        try:
            await page.goto("https://www.worldmonitor.app/pro", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(6)
            text = await page.inner_text("body")
            await page.screenshot(path="/tmp/wm_pro.png", full_page=True)
            results["pro"] = {"text": text[:15000]}
            print(text[:5000])
        except Exception as e:
            print(f"Pro error: {e}")
            results["pro"] = {"error": str(e)}

        # ── 3. Click through sidebar/menu items ───────────────────────────
        print("\n=== Exploring sidebar navigation ===")
        try:
            await page.goto("https://www.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(8)

            # Get all sidebar/panel links
            links = await page.query_selector_all("a[href], button")
            link_info = []
            for link in links[:80]:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if text.strip():
                    link_info.append({"href": href, "text": text.strip()})

            results["all_links"] = link_info
            print("All links/buttons found:")
            for l in link_info:
                print(f"  {l['text'][:50]} -> {l['href']}")

        except Exception as e:
            print(f"Links exploration error: {e}")

        await browser.close()

        with open("/tmp/wm_deep_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\n✅ Saved to /tmp/wm_deep_results.json")

asyncio.run(scrape())
