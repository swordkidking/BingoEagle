"""
Connect to 品高聆客 Electron app via remote debugging and explore all features
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
    return path

async def main():
    async with async_playwright() as p:
        # Connect to the running Electron app via CDP
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        print(f"Connected! Contexts: {len(browser.contexts)}")

        # Get all pages/windows
        context = browser.contexts[0]
        pages = context.pages
        print(f"Pages found: {len(pages)}")
        for i, pg in enumerate(pages):
            print(f"  [{i}] title={await pg.title()!r}  url={pg.url!r}")

        # Use the first meaningful page
        page = None
        for pg in pages:
            url = pg.url
            title = await pg.title()
            if url and url != "about:blank" and "devtools" not in url.lower():
                page = pg
                print(f"\nUsing page: {title!r} @ {url}")
                break

        if not page:
            page = pages[0]
            print(f"Fallback to pages[0]: {page.url}")

        await asyncio.sleep(2)

        # ── Screenshot current state ───────────────────────────────
        await shot(page, "00_initial.png")

        # ── Get full page text and structure ──────────────────────
        title = await page.title()
        url = page.url
        body_text = await page.inner_text("body")
        print(f"\nTitle: {title}")
        print(f"URL: {url}")
        print(f"Body text (first 3000):\n{body_text[:3000]}")

        # ── Get all navigation items ──────────────────────────────
        nav_items = await page.evaluate("""
            () => {
                const results = [];
                // sidebar nav items
                const sels = [
                    'nav a', 'nav li', '.sidebar a', '.menu a', '.nav-item',
                    '[class*="menu"] li', '[class*="nav"] li', '[class*="sidebar"] li',
                    'aside a', 'aside li', '.left-panel a', '.left-panel li'
                ];
                for (const sel of sels) {
                    for (const el of document.querySelectorAll(sel)) {
                        const text = el.textContent.trim();
                        if (text && text.length < 30) {
                            results.push({sel, text, tag: el.tagName});
                        }
                    }
                }
                // deduplicate
                const seen = new Set();
                return results.filter(r => {
                    if (seen.has(r.text)) return false;
                    seen.add(r.text);
                    return true;
                });
            }
        """)
        print(f"\nNavigation items found ({len(nav_items)}):")
        for item in nav_items:
            print(f"  {item['text']}")

        # ── Get all buttons ───────────────────────────────────────
        buttons = await page.evaluate("""
            () => {
                const btns = [];
                for (const el of document.querySelectorAll('button, [role="button"], .btn')) {
                    const text = el.textContent.trim();
                    if (text && text.length < 40) btns.push(text);
                }
                const seen = new Set();
                return btns.filter(t => { if(seen.has(t)) return false; seen.add(t); return true; });
            }
        """)
        print(f"\nButtons ({len(buttons)}):")
        for b in buttons[:40]:
            print(f"  {b}")

        # Save all collected data
        with open(f"{SCREENSHOT_DIR}/page_data.json", "w", encoding="utf-8") as f:
            json.dump({
                "title": title, "url": url,
                "body_text": body_text[:10000],
                "nav_items": nav_items,
                "buttons": buttons
            }, f, ensure_ascii=False, indent=2)

        await browser.close()
        print("\n✅ Done. Screenshots saved to", SCREENSHOT_DIR)

asyncio.run(main())
