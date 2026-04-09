"""
Explore 品高聆客 via CDP - comprehensive feature discovery
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def shot(page, name):
    path = f"{SCREENSHOT_DIR}/{name}"
    await page.screenshot(path=path, full_page=False)
    print(f"  ✅ {name}")

async def get_structure(page):
    return await page.evaluate("""
        () => {
            const result = {nav: [], buttons: [], tabs: [], panels: [], text: ''};
            // Nav / sidebar
            for (const sel of ['nav a','nav li','.sidebar li','.sidebar a','.menu-item',
                                '[class*="menu"] li','[class*="nav"] li','aside li','aside a',
                                '.tab','[role="tab"]','[class*="tab"]']) {
                for (const el of document.querySelectorAll(sel)) {
                    const t = el.textContent.trim();
                    if (t && t.length < 40) result.nav.push(t);
                }
            }
            // Buttons
            for (const el of document.querySelectorAll('button,[role="button"],.btn')) {
                const t = el.textContent.trim();
                if (t && t.length < 40) result.buttons.push(t);
            }
            // Page text
            result.text = document.body.innerText.substring(0, 5000);
            // Deduplicate
            result.nav = [...new Set(result.nav)];
            result.buttons = [...new Set(result.buttons)];
            return result;
        }
    """)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        print(f"✅ Connected to 品高聆客")
        print(f"   Contexts: {len(browser.contexts)}")

        context = browser.contexts[0]
        pages = context.pages
        print(f"   Pages: {len(pages)}")
        for i, pg in enumerate(pages):
            t = await pg.title()
            print(f"   [{i}] {t!r}  {pg.url!r}")

        # Find the main window
        main_page = None
        for pg in pages:
            if pg.url and "devtools" not in pg.url and pg.url != "about:blank":
                main_page = pg
                break
        if not main_page:
            main_page = pages[0]

        await asyncio.sleep(3)
        title = await main_page.title()
        print(f"\n📱 Main window: {title!r}  {main_page.url!r}")

        # Initial screenshot
        await shot(main_page, "00_initial.png")

        # Get structure
        struct = await get_structure(main_page)
        print(f"\n📋 Nav items ({len(struct['nav'])}):")
        for item in struct['nav']:
            print(f"   • {item}")
        print(f"\n🔘 Buttons ({len(struct['buttons'])}):")
        for b in struct['buttons'][:30]:
            print(f"   • {b}")
        print(f"\n📄 Page text preview:\n{struct['text'][:2000]}")

        # Get all clickable elements with their positions
        elements = await main_page.evaluate("""
            () => {
                const items = [];
                const sels = ['a[href]','button','[role="button"]','[role="tab"]',
                               '[class*="nav"]','[class*="menu"]','[class*="tab"]',
                               'li[class]','[class*="item"]'];
                for (const sel of sels) {
                    for (const el of document.querySelectorAll(sel)) {
                        const r = el.getBoundingClientRect();
                        const t = el.textContent.trim();
                        if (t && t.length < 50 && r.width > 5 && r.height > 5) {
                            items.push({
                                tag: el.tagName, text: t,
                                x: Math.round(r.x), y: Math.round(r.y),
                                w: Math.round(r.width), h: Math.round(r.height),
                                cls: el.className.substring(0,60)
                            });
                        }
                    }
                }
                // Deduplicate by text
                const seen = new Set();
                return items.filter(i => {
                    if (seen.has(i.text)) return false;
                    seen.add(i.text);
                    return true;
                });
            }
        """)
        print(f"\n🎯 All clickable elements ({len(elements)}):")
        for el in elements:
            print(f"   [{el['x']},{el['y']}] {el['tag']} '{el['text']}'")

        # Save all data
        data = {
            "title": title,
            "url": main_page.url,
            "structure": struct,
            "elements": elements
        }
        with open(f"{SCREENSHOT_DIR}/app_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Data saved to app_data.json")

        # Try clicking through left sidebar items
        print("\n🖱️ Exploring sidebar navigation...")
        sidebar_items = [el for el in elements if el['x'] < 200 and el['y'] > 50]
        print(f"   Found {len(sidebar_items)} items in left sidebar area")
        for i, item in enumerate(sidebar_items[:15]):
            try:
                print(f"\n   Clicking: '{item['text']}' at ({item['x']},{item['y']})")
                await main_page.mouse.click(item['x'] + item['w']//2, item['y'] + item['h']//2)
                await asyncio.sleep(2)
                fname = f"nav_{i:02d}_{item['text'][:20].replace('/', '_').replace(' ', '_')}.png"
                await shot(main_page, fname)
            except Exception as e:
                print(f"   Error: {e}")

        await browser.close()
        print("\n✅ Exploration complete!")

asyncio.run(main())
