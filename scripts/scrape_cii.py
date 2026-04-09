"""
Capture CII panel and missing panels by scrolling the right panel container
"""
import asyncio
import os
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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

        # Find the right-side scrollable panel container
        container_info = await page.evaluate("""
            () => {
                // Find the scrollable panels container on the right
                const candidates = [];
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    if (
                        rect.width > 200 && rect.height > 400 &&
                        rect.x > 400 &&
                        (style.overflowY === 'scroll' || style.overflowY === 'auto')
                    ) {
                        candidates.push({
                            tag: el.tagName,
                            cls: el.className.substring(0, 60),
                            x: rect.x, y: rect.y, w: rect.width, h: rect.height,
                            scrollH: el.scrollHeight,
                            id: el.id
                        });
                    }
                }
                return candidates;
            }
        """)
        print("Scrollable containers found:")
        for c in container_info:
            print(f"  {c}")

        # Now scroll the right panel and capture each section
        # Find container by id or class
        panel_sel = None
        for c in container_info:
            if c['scrollH'] > 1000:
                panel_sel = f"#{c['id']}" if c['id'] else f".{c['cls'].split()[0]}" if c['cls'] else None
                print(f"  Using container: {panel_sel}, scrollH={c['scrollH']}")
                break

        if not panel_sel:
            # fallback: scroll the whole page
            print("  Fallback: scrolling page body")

        # Helper: scroll to position and screenshot right panel area
        async def scroll_and_shot(scroll_y, filename, right_x=740):
            if panel_sel:
                try:
                    await page.evaluate(f"document.querySelector('{panel_sel}').scrollTop = {scroll_y}")
                except:
                    await page.evaluate(f"window.scrollTo(0, {scroll_y})")
            else:
                await page.evaluate(f"window.scrollTo(0, {scroll_y})")
            await asyncio.sleep(1.2)
            await page.screenshot(
                path=f"{SCREENSHOT_DIR}/{filename}",
                clip={"x": right_x, "y": 60, "width": min(900, 3200 - right_x), "height": 840}
            )
            print(f"  ✅ {filename} (scroll={scroll_y})")

        # Screenshot at different scroll positions
        await scroll_and_shot(0,    "panel_scroll_0.png")
        await scroll_and_shot(600,  "panel_scroll_600.png")
        await scroll_and_shot(1200, "panel_scroll_1200.png")
        await scroll_and_shot(1800, "panel_scroll_1800.png")
        await scroll_and_shot(2400, "panel_scroll_2400.png")
        await scroll_and_shot(3000, "panel_scroll_3000.png")

        # Also try scrolling inside known panel class names
        print("\n=== Trying panel-specific scroll ===")
        scroll_result = await page.evaluate("""
            () => {
                const selectors = [
                    '.panels-container', '#panels', '.right-panels',
                    '.panel-list', '[data-testid="panels"]', '.sidebar'
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        return {found: sel, scrollH: el.scrollHeight, clientH: el.clientHeight};
                    }
                }
                // try nth scrollable
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    const s = window.getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    if (r.x > 700 && r.width > 200 && el.scrollHeight > el.clientHeight + 100) {
                        el.scrollTop = 2000;
                        return {found: el.tagName + '.' + el.className.substring(0,30), scrollH: el.scrollHeight};
                    }
                }
                return null;
            }
        """)
        print(f"  Panel scroll result: {scroll_result}")
        await asyncio.sleep(1.5)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/panel_after_scroll.png",
                              clip={"x": 740, "y": 60, "width": 900, "height": 840})
        print("  ✅ panel_after_scroll.png")

        await browser.close()

asyncio.run(main())
