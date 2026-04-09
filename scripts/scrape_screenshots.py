"""
Capture targeted screenshots of each WorldMonitor feature area
"""
import asyncio
import os
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def shot(page, path, full_page=False):
    await page.screenshot(path=f"{SCREENSHOT_DIR}/{path}", full_page=full_page)
    print(f"  ✅ {path}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            device_scale_factor=2,
        )
        page = await context.new_page()

        # ── 1. 主站首页（全局态势）──────────────────────────────────
        print("=== 1. 主站首页 ===")
        await page.goto("https://www.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        await shot(page, "01_world_homepage.png")

        # ── 2. 切换 3D 地球视图 ──────────────────────────────────────
        print("=== 2. 3D 地球 ===")
        try:
            btn_3d = await page.query_selector("button:has-text('3D')")
            if btn_3d:
                await btn_3d.click()
                await asyncio.sleep(5)
                await shot(page, "02_world_3d_globe.png")
        except Exception as e:
            print(f"  3D button: {e}")

        # ── 3. 图层面板展开 ──────────────────────────────────────────
        print("=== 3. 图层面板 ===")
        try:
            # click the layers toggle (▼ button near layers label)
            layer_btn = await page.query_selector("button:has-text('▼')")
            if layer_btn:
                await layer_btn.click()
                await asyncio.sleep(2)
                await shot(page, "03_world_layers_panel.png")
                await layer_btn.click()  # close
        except Exception as e:
            print(f"  Layer panel: {e}")

        # ── 4. 导航栏与顶部 UI ───────────────────────────────────────
        print("=== 4. 顶部导航栏 ===")
        # Crop top portion only - take screenshot and crop via clip
        await page.screenshot(
            path=f"{SCREENSHOT_DIR}/04_topnav.png",
            clip={"x": 0, "y": 0, "width": 1600, "height": 80}
        )
        print(f"  ✅ 04_topnav.png")

        # ── 5. CII 国家不稳定指数面板 ────────────────────────────────
        print("=== 5. CII 面板 ===")
        try:
            cii_panel = page.locator("text=国家不稳定性").first
            if await cii_panel.count() > 0:
                box = await cii_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/05_cii_panel.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 600}
                    )
                    print("  ✅ 05_cii_panel.png")
        except Exception as e:
            print(f"  CII panel: {e}")

        # ── 6. AI 洞察面板 ───────────────────────────────────────────
        print("=== 6. AI 洞察面板 ===")
        try:
            ai_panel = page.locator("text=AI洞察").first
            if await ai_panel.count() > 0:
                box = await ai_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/06_ai_insights_panel.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 500}
                    )
                    print("  ✅ 06_ai_insights_panel.png")
        except Exception as e:
            print(f"  AI insights: {e}")

        # ── 7. AI 战略态势面板 ───────────────────────────────────────
        print("=== 7. AI 战略态势 ===")
        try:
            strat_panel = page.locator("text=AI战略态势").first
            if await strat_panel.count() > 0:
                box = await strat_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/07_ai_strategic.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 400}
                    )
                    print("  ✅ 07_ai_strategic.png")
        except Exception as e:
            print(f"  Strategic: {e}")

        # ── 8. AI 预测面板 ───────────────────────────────────────────
        print("=== 8. AI 预测预报 ===")
        try:
            forecast_panel = page.locator("text=AI FORECASTS").first
            if await forecast_panel.count() > 0:
                box = await forecast_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/08_ai_forecasts.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 600}
                    )
                    print("  ✅ 08_ai_forecasts.png")
        except Exception as e:
            print(f"  Forecasts: {e}")

        # ── 9. 实时新闻面板 ──────────────────────────────────────────
        print("=== 9. 实时新闻面板 ===")
        try:
            news_panel = page.locator("text=实时新闻").first
            if await news_panel.count() > 0:
                box = await news_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/09_live_news.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 550}
                    )
                    print("  ✅ 09_live_news.png")
        except Exception as e:
            print(f"  Live news: {e}")

        # ── 10. 直播摄像头面板 ───────────────────────────────────────
        print("=== 10. 直播摄像头 ===")
        try:
            webcam_panel = page.locator("text=LIVE WEBCAMS").first
            if await webcam_panel.count() > 0:
                box = await webcam_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/10_live_webcams.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 400}
                    )
                    print("  ✅ 10_live_webcams.png")
        except Exception as e:
            print(f"  Webcams: {e}")

        # ── 11. 科技站 ───────────────────────────────────────────────
        print("=== 11. 科技站 ===")
        await page.goto("https://tech.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(9)
        await shot(page, "11_tech_homepage.png")

        # AI/ML panel
        try:
            ai_ml = page.locator("text=AI/ML").first
            if await ai_ml.count() > 0:
                box = await ai_ml.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/11b_tech_aiml_panel.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 500}
                    )
                    print("  ✅ 11b_tech_aiml_panel.png")
        except Exception as e:
            print(f"  AI/ML panel: {e}")

        # ── 12. 金融站 ───────────────────────────────────────────────
        print("=== 12. 金融站 ===")
        await page.goto("https://finance.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(9)
        await shot(page, "12_finance_homepage.png")

        # Markets panel
        try:
            markets_panel = page.locator("text=MARKETS").first
            if await markets_panel.count() > 0:
                box = await markets_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/12b_finance_markets.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 700}
                    )
                    print("  ✅ 12b_finance_markets.png")
        except Exception as e:
            print(f"  Markets: {e}")

        # ── 13. 大宗商品站 ───────────────────────────────────────────
        print("=== 13. 大宗商品站 ===")
        await page.goto("https://commodity.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(9)
        await shot(page, "13_commodity_homepage.png")

        # ── 14. 好消息站 ─────────────────────────────────────────────
        print("=== 14. 好消息站 ===")
        await page.goto("https://happy.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(9)
        await shot(page, "14_happy_homepage.png")

        # Good news feed panel
        try:
            good_panel = page.locator("text=Good News Feed").first
            if await good_panel.count() > 0:
                box = await good_panel.bounding_box()
                if box:
                    await page.screenshot(
                        path=f"{SCREENSHOT_DIR}/14b_good_news_feed.png",
                        clip={"x": max(0, box["x"]-10), "y": max(0, box["y"]-10),
                              "width": min(600, 1600-box["x"]), "height": 600}
                    )
                    print("  ✅ 14b_good_news_feed.png")
        except Exception as e:
            print(f"  Good news feed: {e}")

        # ── 15. Pro 页面 ─────────────────────────────────────────────
        print("=== 15. Pro 页面 ===")
        await page.goto("https://www.worldmonitor.app/pro", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(7)
        await shot(page, "15_pro_page.png")
        await shot(page, "15b_pro_page_full.png", full_page=True)

        # ── 16. 回到主站——展开 Cmd+K 搜索 ──────────────────────────
        print("=== 16. Cmd+K 搜索 ===")
        await page.goto("https://www.worldmonitor.app", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(8)
        try:
            search_btn = page.locator("button:has-text('搜索')").first
            if await search_btn.count() > 0:
                await search_btn.click()
                await asyncio.sleep(2)
                await shot(page, "16_cmdk_search.png")
                await page.keyboard.press("Escape")
        except Exception as e:
            print(f"  CmdK: {e}")

        # ── 17. 区域切换菜单 ─────────────────────────────────────────
        print("=== 17. 区域切换 ===")
        try:
            region_btn = page.locator("button:has-text('全球')").first
            if await region_btn.count() > 0:
                await region_btn.click()
                await asyncio.sleep(1)
                await shot(page, "17_region_switcher.png")
                await page.keyboard.press("Escape")
        except Exception as e:
            print(f"  Region: {e}")

        # ── 18. 设置面板 ─────────────────────────────────────────────
        print("=== 18. 设置面板 ===")
        try:
            settings_btn = page.locator("button:has-text('设置')").first
            if await settings_btn.count() > 0:
                await settings_btn.click()
                await asyncio.sleep(2)
                await shot(page, "18_settings_panel.png")
                await page.keyboard.press("Escape")
        except Exception as e:
            print(f"  Settings: {e}")

        # ── 19. DEFCON 弹窗 ──────────────────────────────────────────
        print("=== 19. DEFCON 弹窗 ===")
        try:
            defcon_btn = page.locator("button:has-text('DEFCON')").first
            if await defcon_btn.count() > 0:
                await defcon_btn.click()
                await asyncio.sleep(2)
                await shot(page, "19_defcon_popup.png")
                await page.keyboard.press("Escape")
        except Exception as e:
            print(f"  DEFCON: {e}")

        # ── 20. Docs 首页 ────────────────────────────────────────────
        print("=== 20. Docs ===")
        await page.goto("https://www.worldmonitor.app/docs", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        await shot(page, "20_docs_home.png")

        # ── 21. Blog 首页 ────────────────────────────────────────────
        print("=== 21. Blog ===")
        await page.goto("https://www.worldmonitor.app/blog/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        await shot(page, "21_blog_home.png")

        await browser.close()

    # List captured screenshots
    files = sorted(os.listdir(SCREENSHOT_DIR))
    print(f"\n✅ Captured {len(files)} screenshots:")
    for f in files:
        size = os.path.getsize(f"{SCREENSHOT_DIR}/{f}")
        print(f"  {f}  ({size//1024}KB)")

asyncio.run(main())
