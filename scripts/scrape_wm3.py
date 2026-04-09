"""
Scrape WorldMonitor sub-sites: tech, finance, commodity, happy
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_subsite(page, url, name, wait=8):
    print(f"\n=== {name}: {url} ===")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(wait)
        title = await page.title()
        text = await page.inner_text("body")
        await page.screenshot(path=f"/tmp/wm_{name}.png", full_page=False)

        # get nav/tab items
        buttons = await page.query_selector_all("nav a, nav button, [role='tab'], header a, header button")
        btn_texts = []
        for b in buttons[:40]:
            t = await b.inner_text()
            if t.strip():
                btn_texts.append(t.strip())

        print(f"Title: {title}")
        print(f"Nav/buttons: {btn_texts}")
        print("Body preview:")
        print(text[:4000])
        return {"title": title, "text": text[:12000], "nav": btn_texts}
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

async def scrape_blog_docs(page):
    results = {}
    # Blog
    print("\n=== Blog ===")
    try:
        await page.goto("https://www.worldmonitor.app/blog/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        text = await page.inner_text("body")
        links = await page.query_selector_all("a[href]")
        blog_links = []
        for l in links[:30]:
            href = await l.get_attribute("href")
            t = await l.inner_text()
            if href and t.strip():
                blog_links.append({"href": href, "text": t.strip()[:80]})
        results["blog"] = {"text": text[:8000], "links": blog_links}
        print(text[:3000])
    except Exception as e:
        results["blog"] = {"error": str(e)}

    # Docs
    print("\n=== Docs ===")
    try:
        await page.goto("https://www.worldmonitor.app/docs", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        text = await page.inner_text("body")
        results["docs"] = {"text": text[:8000]}
        print(text[:3000])
    except Exception as e:
        results["docs"] = {"error": str(e)}

    return results

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        results = {}

        # Sub-sites
        results["tech"] = await scrape_subsite(page, "https://tech.worldmonitor.app", "tech")
        results["finance"] = await scrape_subsite(page, "https://finance.worldmonitor.app", "finance")
        results["commodity"] = await scrape_subsite(page, "https://commodity.worldmonitor.app", "commodity")
        results["happy"] = await scrape_subsite(page, "https://happy.worldmonitor.app", "happy")

        # Blog and Docs
        bd = await scrape_blog_docs(page)
        results.update(bd)

        # Pro page again with longer wait
        print("\n=== Pro page ===")
        try:
            await page.goto("https://www.worldmonitor.app/pro", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(8)
            text = await page.inner_text("body")
            await page.screenshot(path="/tmp/wm_pro.png", full_page=True)
            results["pro"] = {"text": text[:15000]}
            print(text[:5000])
        except Exception as e:
            results["pro"] = {"error": str(e)}

        await browser.close()

        with open("/tmp/wm_subsites.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\n�� Saved to /tmp/wm_subsites.json")

asyncio.run(main())
