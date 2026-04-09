"""
Fix: capture panels that are off-screen by scrolling into view
Also capture settings, region, webcam, markets, AI/ML panels
"""
import asyncio
import os
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def shot_element(page, selector_text, filename, extra_height=0, search_tag="text"):
    """Scroll element into view and screenshot its bounding box"""
    try:
        if search_tag == "text":
            el = page.locator(f"text={selector_text}").first
        else:
            el = page.locator(selector_text).first

        count = await el.count()
        if count == 0:
            print(f"  ❌ not found: {selector_text}")
            return False

        await el.scroll_into_view_if_needed()
        await asyncio.sleep(0.8)

        box = await el.bounding_box()
        if not box:
            print(f"  ❌ no bbox: {selector_text}")
            return False

        # Expand the clip area to capture the whole panel below the header
        clip_x = max(0, box["x"] - 10)
        clip_y = max(0, box["y"] - 10)
        clip_w = min(700, 3200 - clip_x)  # device_scale_factor=2 → effective 3200px
        clip_h = min(700 + extra_height, 1800 - clip_y)

        await page.screenshot(
            path=f"{SCREENSHOT_DIR}/{filename}",
            clip={"x": clip_x, "y": clip_y, "width": clip_w, "height": clip_h}
        )
        print(f"  ✅ {filename}  (bbox y={box['y']:.0f})")
        return True
    except Exception as e:
        print(f"  ❌ {selector_text}: {e}")
        return False

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            device_scale_factor=2,
        )
        page = await context.new_page()

        # ── Load main site ────────────────────────────────────────────
        print("=== Loading worldmonitor.app ===")
        await page.goto("https://www.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(12)

        # Full page scroll screenshot
        await page.screenshot(path=f"{SCREENSHOT_DIR}/01_world_homepage.png", full_page=False)
        print("  ✅ 01_world_homepage.png (re-shot)")

        # ── CII panel ────────────────────────────────────────────────
        print("\n=== CII panel ===")
        await shot_element(page, "国家不稳定性", "05_cii_panel.png", extra_height=500)

        # ── AI Insights ──────────────────────────────────────────────
        print("\n=== AI Insights panel ===")
        await shot_element(page, "AI洞察", "06_ai_insights_panel.png", extra_height=400)

        # ── AI Strategic ─────────────────────────────────────────────
        print("\n=== AI Strategic panel ===")
        await shot_element(page, "AI战略态势", "07_ai_strategic.png", extra_height=350)

        # ── AI Forecasts ─────────────────────────────────────────────
        print("\n=== AI Forecasts panel ===")
        await shot_element(page, "AI FORECASTS", "08_ai_forecasts.png", extra_height=550)

        # ── Live Webcams ─────────────────────────────────────────────
        print("\n=== Live Webcams panel ===")
        await shot_element(page, "LIVE WEBCAMS", "10_live_webcams.png", extra_height=350)

        # ── Live News ────────────────────────────────────────────────
        print("\n=== Live News panel ===")
        await shot_element(page, "实时新闻", "09_live_news.png", extra_height=500)

        # ── Map layers panel (open it) ────────────────────────────────
        print("\n=== Map layers (open toggle) ===")
        try:
            # The ▼ button is next to the layers icon - try clicking the layers section header
            layer_toggle = page.locator("button:has-text('▼')").first
            await layer_toggle.scroll_into_view_if_needed()
            await layer_toggle.click()
            await asyncio.sleep(2)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/03_world_layers_panel.png", full_page=False)
            print("  ✅ 03_world_layers_panel.png")
            await layer_toggle.click()
        except Exception as e:
            print(f"  Layers: {e}")

        # ── Region switcher ─────────────────────────────────────────
        print("\n=== Region switcher ===")
        try:
            # Find the visible region button in the top nav
            region_btn = page.locator("#regionDropdownBtn, button[data-region], .region-selector").first
            cnt = await region_btn.count()
            if cnt == 0:
                # try finding button that contains region labels
                region_btn = page.locator("nav button:has-text('全球'), header button:has-text('全球')").first
                cnt = await region_btn.count()
            if cnt > 0:
                await region_btn.click()
                await asyncio.sleep(1.5)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/17_region_switcher.png")
                print("  ✅ 17_region_switcher.png")
                await page.keyboard.press("Escape")
            else:
                # Just screenshot the region buttons area
                region_area = page.locator("text=美洲").first
                await region_area.scroll_into_view_if_needed()
                box = await region_area.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/17_region_switcher.png",
                        clip={"x": 0, "y": max(0, box["y"]-10), "width": 3200, "height": 80}
                    )
                    print("  ✅ 17_region_switcher.png (region bar)")
        except Exception as e:
            print(f"  Region: {e}")

        # ── Settings panel ─────────────────────────────────────────
        print("\n=== Settings panel ===")
        try:
            settings_btn = page.locator("nav button:has-text('设置'), button[aria-label*='设置'], button:has-text('⚙')").first
            cnt = await settings_btn.count()
            if cnt == 0:
                settings_btn = page.locator("button").filter(has_text="⚙").first
                cnt = await settings_btn.count()
            if cnt > 0:
                await settings_btn.click()
                await asyncio.sleep(2)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/18_settings_panel.png")
                print("  ✅ 18_settings_panel.png")
                await page.keyboard.press("Escape")
            else:
                print("  ❌ settings button not found")
        except Exception as e:
            print(f"  Settings: {e}")

        # ── Finance station ─────────────────────────────────────────
        print("\n=== Finance station ===")
        await page.goto("https://finance.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/12_finance_homepage.png")
        print("  ✅ 12_finance_homepage.png")

        # Markets panel (scroll into view)
        await shot_element(page, "MARKETS", "12b_finance_markets.png", extra_height=650)

        # ── Tech station - AI/ML panel ──────────────────────────────
        print("\n=== Tech station + AI/ML ===")
        await page.goto("https://tech.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/11_tech_homepage.png")
        print("  ✅ 11_tech_homepage.png")

        await shot_element(page, "AI/ML", "11b_tech_aiml_panel.png", extra_height=500)
        await shot_element(page, "TECHNOLOGY", "11c_tech_news_panel.png", extra_height=500)

        # ── Commodity - commodity news ──────────────────────────────
        print("\n=== Commodity news panel ===")
        await page.goto("https://commodity.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/13_commodity_homepage.png")
        print("  ✅ 13_commodity_homepage.png")
        await shot_element(page, "COMMODITY NEWS", "13b_commodity_news.png", extra_height=500)

        # ── World 3D globe ─────────────────────────────────────────
        print("\n=== World 3D globe ===")
        await page.goto("https://www.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        try:
            btn_3d = page.locator("button:has-text('3D')").first
            await btn_3d.click()
            await asyncio.sleep(6)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/02_world_3d_globe.png")
            print("  ✅ 02_world_3d_globe.png")
        except Exception as e:
            print(f"  3D globe: {e}")

        await browser.close()

    # Summary
    files = sorted(os.listdir(SCREENSHOT_DIR))
    print(f"\n✅ Total screenshots: {len(files)}")
    for f in files:
        size = os.path.getsize(f"{SCREENSHOT_DIR}/{f}")
        print(f"  {f}  ({size//1024}KB)")

asyncio.run(main())
