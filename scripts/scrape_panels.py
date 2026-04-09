"""
Precise panel captures: CII, Strategic Risk, Infra Cascade, Signal Aggregator,
Escalation Monitor, Economic Warfare, Force Posture, Disaster Cascade,
Real-time feeds by region
"""
import asyncio
import os
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/screenshots"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            device_scale_factor=2,
        )
        page = await context.new_page()
        await page.goto("https://www.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(12)

        PANELS_SEL = "#panelsGrid"
        RIGHT_X = 966   # panels start at x=966 (device pixel x / dpr = 966)

        async def scroll_snap(scroll_y, filename, crop_y=0, crop_h=840):
            await page.evaluate(f"document.querySelector('{PANELS_SEL}').scrollTop = {scroll_y}")
            await asyncio.sleep(1.0)
            await page.screenshot(
                path=f"{SCREENSHOT_DIR}/{filename}",
                clip={"x": RIGHT_X, "y": 79 + crop_y, "width": 634, "height": crop_h}
            )
            print(f"  ✅ {filename}")

        # ── CII panel  (scroll ~900 to center it) ─────────────────────
        await scroll_snap(880,  "05_cii_panel.png",        crop_y=0, crop_h=560)

        # ── Strategic Risk panel ──────────────────────────────────────
        await scroll_snap(880,  "22_strategic_risk.png",   crop_y=360, crop_h=400)

        # ── Signal Aggregator ─────────────────────────────────────────
        await scroll_snap(1500, "23_signal_aggregator.png",crop_y=0,   crop_h=220)

        # ── Infra Cascade ─────────────────────────────────────────────
        await scroll_snap(1700, "24_infra_cascade.png",    crop_y=200, crop_h=380)

        # ── Escalation Monitor + Economic Warfare ─────────────────────
        await scroll_snap(2300, "25_escalation_economic.png", crop_y=0, crop_h=560)

        # ── Force Posture ─────────────────────────────────────────────
        await scroll_snap(1700, "26_force_posture.png",    crop_y=370, crop_h=400)

        # ── Regional news feeds ───────────────────────────────────────
        await scroll_snap(2450, "27_regional_news.png",    crop_y=100, crop_h=760)

        # ── Energy & resources + Gov + Predictions ────────────────────
        await scroll_snap(2900, "28_energy_gov_prediction.png", crop_y=0, crop_h=760)

        # ── Layers panel open (click ▼ on the map layers toggle) ─────
        await page.evaluate(f"document.querySelector('{PANELS_SEL}').scrollTop = 0")
        await asyncio.sleep(0.8)
        # Click layers toggle via JS dispatch
        toggled = await page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button.toggle-collapse');
                if (btns[0]) { btns[0].dispatchEvent(new MouseEvent('click', {bubbles: true})); return true; }
                return false;
            }
        """)
        print(f"  Layers toggle clicked: {toggled}")
        await asyncio.sleep(1.5)
        await page.screenshot(
            path=f"{SCREENSHOT_DIR}/03_world_layers_open.png",
            clip={"x": 0, "y": 79, "width": 966, "height": 820}
        )
        print("  ✅ 03_world_layers_open.png")

        # ── Map area only (2D flat map) ───────────────────────────────
        await page.evaluate(f"document.querySelector('{PANELS_SEL}').scrollTop = 0")
        await asyncio.sleep(0.5)
        await page.screenshot(
            path=f"{SCREENSHOT_DIR}/04_map_area_2d.png",
            clip={"x": 0, "y": 79, "width": 966, "height": 820}
        )
        print("  ✅ 04_map_area_2d.png")

        # ── Cmd+K (already captured but re-do with centered dialog) ──
        search_btn = page.locator("button:has-text('搜索')").first
        await search_btn.click()
        await asyncio.sleep(1.5)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/16_cmdk_search.png")
        print("  ✅ 16_cmdk_search.png")
        await page.keyboard.press("Escape")

        # ── Settings - tabs ──────────────────────────────────────────
        # Already captured, also capture Panels tab and Sources tab
        settings_btn = page.locator("button:has-text('⚙')").first
        if await settings_btn.count() == 0:
            settings_btn = page.locator("nav").locator("button").filter(has_text="设置").first
        try:
            await settings_btn.click()
            await asyncio.sleep(1.5)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/18a_settings_display.png")
            print("  ✅ 18a_settings_display.png")
            # Click Panels tab
            panels_tab = page.locator("text=面板").first
            if await panels_tab.count() > 0:
                await panels_tab.click()
                await asyncio.sleep(1)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/18b_settings_panels.png")
                print("  ✅ 18b_settings_panels.png")
            # Click Sources tab
            sources_tab = page.locator("text=来源").first
            if await sources_tab.count() > 0:
                await sources_tab.click()
                await asyncio.sleep(1)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/18c_settings_sources.png")
                print("  ✅ 18c_settings_sources.png")
            await page.keyboard.press("Escape")
        except Exception as e:
            print(f"  Settings tabs: {e}")

        await browser.close()
    print("\n✅ Done")

asyncio.run(main())
