"""
Scrape WorldMonitor Blog posts and Docs in detail
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_page(page, url, name, wait=6):
    print(f"\n=== {name} ===")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(wait)
        text = await page.inner_text("body")
        print(text[:3000])
        return {"url": url, "text": text[:10000]}
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

        # Docs pages
        doc_pages = [
            ("https://www.worldmonitor.app/docs", "docs_home"),
            ("https://www.worldmonitor.app/docs/getting-started", "docs_getting_started"),
            ("https://www.worldmonitor.app/docs/platform-overview", "docs_platform"),
            ("https://www.worldmonitor.app/docs/features", "docs_features"),
            ("https://www.worldmonitor.app/docs/map-layers", "docs_map_layers"),
            ("https://www.worldmonitor.app/docs/ai-intelligence", "docs_ai"),
            ("https://www.worldmonitor.app/docs/country-instability-index", "docs_cii"),
            ("https://www.worldmonitor.app/docs/finance", "docs_finance"),
            ("https://www.worldmonitor.app/docs/data-sources", "docs_data_sources"),
        ]

        for url, name in doc_pages:
            results[name] = await scrape_page(page, url, name, wait=5)

        # Blog articles
        blog_pages = [
            ("https://www.worldmonitor.app/blog/", "blog_home"),
            ("https://www.worldmonitor.app/blog/supply-chain", "blog_supply_chain"),
            ("https://www.worldmonitor.app/blog/world-monitor-vs-traditional-tools", "blog_vs_tools"),
            ("https://www.worldmonitor.app/blog/developer-platform", "blog_dev_platform"),
        ]
        for url, name in blog_pages:
            results[name] = await scrape_page(page, url, name, wait=5)

        # Also try getting the docs sidebar / table of contents more deeply
        print("\n=== Docs full sidebar ===")
        try:
            await page.goto("https://www.worldmonitor.app/docs", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(6)
            # Get all links in sidebar
            links = await page.query_selector_all("nav a, aside a, [data-sidebar] a")
            for l in links[:60]:
                href = await l.get_attribute("href")
                t = await l.inner_text()
                if t.strip():
                    print(f"  {t.strip()} -> {href}")
        except Exception as e:
            print(f"Error: {e}")

        await browser.close()

        with open("/tmp/wm_docs_blog.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\n✅ Saved to /tmp/wm_docs_blog.json")

asyncio.run(main())
