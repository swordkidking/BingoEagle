"""
Capture remaining panels: CII (hidden initially), layers panel
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

        # ── CII: find it by JS evaluation ────────────────────────────
        print("=== Finding CII panel via JS ===")
        try:
            # Use JS to find element containing CII text and scroll to it
            result = await page.evaluate("""
                () => {
                    const all = document.querySelectorAll('*');
                    for (const el of all) {
                        if (el.childElementCount === 0 && el.textContent.includes('国家不稳定性')) {
                            el.scrollIntoView({block: 'center'});
                            const r = el.getBoundingClientRect();
                            return {x: r.x, y: r.y, w: r.width, h: r.height, text: el.textContent.trim().substring(0,50)};
                        }
                    }
                    // try English
                    for (const el of all) {
                        if (el.childElementCount === 0 && el.textContent.includes('Country Instability')) {
                            el.scrollIntoView({block: 'center'});
                            const r = el.getBoundingClientRect();
                            return {x: r.x, y: r.y, w: r.width, h: r.height, text: el.textContent.trim().substring(0,50)};
                        }
                    }
                    return null;
                }
            """)
            print(f"  CII element: {result}")
            if result and result["y"] > 0:
                await asyncio.sleep(1)
                await page.screenshot(
                    path=f"{SCREENSHOT_DIR}/05_cii_panel.png",
                    clip={
                        "x": max(0, result["x"] - 10),
                        "y": max(0, result["y"] - 10),
                        "width": min(700, 3200 - result["x"]),
                        "height": 650
                    }
                )
                print("  ✅ 05_cii_panel.png")
        except Exception as e:
            print(f"  CII JS error: {e}")

        # ── Layers panel: use JS click ────────────────────────────────
        print("\n=== Layers panel via JS click ===")
        try:
            # Find the layers toggle button and click via JS
            result = await page.evaluate("""
                () => {
                    // Find toggle buttons near 'LAYERS' or '图层' text
                    const buttons = document.querySelectorAll('button');
                    for (const b of buttons) {
                        if (b.textContent.includes('▼') || b.textContent.includes('图层') || b.textContent.includes('LAYERS')) {
                            b.scrollIntoView({block: 'center'});
                            const r = b.getBoundingClientRect();
                            return {x: r.x + r.width/2, y: r.y + r.height/2, text: b.textContent.trim().substring(0,30)};
                        }
                    }
                    return null;
                }
            """)
            print(f"  Layers button: {result}")

            # Now try clicking all ▼ buttons to find the right one
            buttons = await page.query_selector_all("button.toggle-collapse")
            print(f"  Found {len(buttons)} toggle-collapse buttons")
            for i, btn in enumerate(buttons[:3]):
                try:
                    parent = await btn.evaluate_handle("el => el.closest('.panel-wrapper, .panel-container, section, .panel')")
                    parent_text = await page.evaluate("el => el ? el.textContent.substring(0,80) : ''", parent)
                    print(f"    btn[{i}] parent text: {parent_text[:60]}")
                except:
                    pass
                try:
                    await page.evaluate("el => el.click()", btn)
                    await asyncio.sleep(1.5)
                except Exception as e2:
                    print(f"    click err: {e2}")

            await page.screenshot(path=f"{SCREENSHOT_DIR}/03_world_layers_panel_v2.png")
            print("  ✅ 03_world_layers_panel_v2.png")
        except Exception as e:
            print(f"  Layers error: {e}")

        # ── Also try to screenshot the full right panel area ──────────
        print("\n=== Full right panel area ===")
        try:
            # Get the right side panel container
            panel_x = await page.evaluate("""
                () => {
                    // Find rightmost fixed panel
                    const panels = document.querySelectorAll('.panel-wrapper, .side-panel, .right-panel, [class*="panel"]');
                    let rightmost = null;
                    let maxX = 0;
                    for (const p of panels) {
                        const r = p.getBoundingClientRect();
                        if (r.width > 100 && r.height > 200 && r.x > maxX) {
                            maxX = r.x;
                            rightmost = {x: r.x, y: r.y, w: r.width, h: r.height};
                        }
                    }
                    return rightmost;
                }
            """)
            print(f"  Panel area: {panel_x}")
            if panel_x and panel_x.get("x"):
                px = int(panel_x["x"])
                await page.screenshot(
                    path=f"{SCREENSHOT_DIR}/00_right_panel_overview.png",
                    clip={"x": px, "y": 60, "width": min(700, 3200 - px), "height": 840}
                )
                print("  ✅ 00_right_panel_overview.png")
        except Exception as e:
            print(f"  Right panel: {e}")

        await browser.close()

    files = sorted(os.listdir(SCREENSHOT_DIR))
    print(f"\n✅ Total: {len(files)} screenshots")
    for f in files:
        size = os.path.getsize(f"{SCREENSHOT_DIR}/{f}")
        print(f"  {f}  ({size//1024}KB)")

asyncio.run(main())
