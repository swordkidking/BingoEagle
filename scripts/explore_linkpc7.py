"""
Phase 7: Capture more specific screenshots
- AI assistant tabs (macOS screencapture)
- Click through apps to see each app
- Get full apps list from HTML
"""
import asyncio
import json
import base64
import os
import urllib.request
import websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots"

_id = 0
def next_id():
    global _id; _id += 1; return _id

async def send(ws, method, params=None, timeout=20):
    msg = {"id": next_id(), "method": method, "params": params or {}}
    await ws.send(json.dumps(msg))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        data = json.loads(raw)
        if data.get("id") == msg["id"]:
            return data.get("result", {})

async def screenshot(ws, filename):
    try:
        r = await send(ws, "Page.captureScreenshot", {"format": "png"})
        if "data" in r:
            path = f"{SCREENSHOT_DIR}/{filename}"
            with open(path, "wb") as f:
                f.write(base64.b64decode(r["data"]))
            size = os.path.getsize(path)
            print(f"  ✅ {filename} ({size//1024}KB)")
            return path
    except Exception as e:
        print(f"  ❌ {filename}: {e}")
    return None

async def js(ws, expr, timeout=20):
    try:
        r = await send(ws, "Runtime.evaluate", {
            "expression": expr, "returnByValue": True, "awaitPromise": True
        }, timeout=timeout)
        return r.get("result", {}).get("value")
    except:
        return None

async def click(ws, x, y):
    await send(ws, "Input.dispatchMouseEvent", {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
    await send(ws, "Input.dispatchMouseEvent", {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})

async def main():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())

    home = next((t for t in targets if t.get("type") == "page"), None)
    ai_target = next((t for t in targets if "12258" in t.get("url","")), None)

    # ── Part 1: Apps tab - get all apps via HTML inspection ──
    async with websockets.connect(home["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # Click 应用 tab
        await click(ws, 720, 21)
        await asyncio.sleep(3)
        await screenshot(ws, "apps_full.png")

        # Get full HTML of apps grid
        apps_html = await js(ws, """
            (() => {
                // Find apps container
                let maxArea = 0, best = null;
                for (const el of document.querySelectorAll('*')) {
                    const r = el.getBoundingClientRect();
                    if (r.x > 100 && r.width > 300 && r.height > 200) {
                        const area = r.width * r.height;
                        if (area > maxArea) { maxArea = area; best = el; }
                    }
                }
                return best ? best.innerHTML.substring(0, 8000) : 'not found';
            })()
        """)
        print(f"Apps HTML:\n{apps_html[:3000]}")

        # Get all app names visible
        all_apps = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('*')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length > 1 && t.length < 15
                        && el.children.length === 0
                        && r.x > 100 && r.x < 800
                        && r.y > 30 && r.y < 300
                        && r.width > 5 && r.height > 5) {
                        items.push({text: t, x: Math.round(r.x), y: Math.round(r.y)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"\nAll app names ({len(all_apps) if all_apps else 0}):")
        if all_apps:
            for a in all_apps:
                print(f"  [{a['x']},{a['y']}] {a['text']!r}")

        # Click "全部应用" button to see all apps
        full_apps_btn = await js(ws, """
            (() => {
                for (const el of document.querySelectorAll('*')) {
                    const t = el.textContent.trim();
                    if (t === '全部应用' || t === '所有应用') {
                        const r = el.getBoundingClientRect();
                        return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            })()
        """)
        if full_apps_btn:
            print(f"\nClicking 全部应用 @ ({full_apps_btn['x']},{full_apps_btn['y']})")
            await click(ws, full_apps_btn['x'], full_apps_btn['y'])
            await asyncio.sleep(2)
            await screenshot(ws, "apps_all.png")

            # Get all apps in full view
            all_apps2 = await js(ws, """
                (() => {
                    const items = [];
                    for (const el of document.querySelectorAll('*')) {
                        const r = el.getBoundingClientRect();
                        const t = el.textContent.trim();
                        if (t && t.length > 1 && t.length < 20
                            && el.children.length === 0
                            && r.width > 5 && r.height > 5
                            && r.x > 0) {
                            items.push({text: t, x: Math.round(r.x), y: Math.round(r.y)});
                        }
                    }
                    const seen = new Set();
                    return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
                })()
            """)
            print(f"\nAll apps in full view ({len(all_apps2) if all_apps2 else 0}):")
            if all_apps2:
                for a in all_apps2[:80]:
                    print(f"  [{a['x']},{a['y']}] {a['text']!r}")

            with open(f"{SCREENSHOT_DIR}/all_apps_full.json", "w", encoding="utf-8") as f:
                json.dump({"apps": all_apps2}, f, ensure_ascii=False, indent=2)

        # ── Part 2: Click through individual apps ──
        # Back to apps tab, click some specific apps
        await click(ws, 720, 21)  # apps tab
        await asyncio.sleep(2)

        # Try clicking specific known apps by position from the screenshot
        app_clicks = [
            ("请假与考勤", 55, 98),
            ("协作", 110, 68),
            ("项目协管", None, None),
        ]

        # Get apps by looking at all items in apps grid
        grid_items = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('*')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length > 1 && t.length < 12
                        && el.children.length === 0
                        && r.x > 100 && r.x < 800
                        && r.y > 35 && r.y < 280) {
                        items.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"\nGrid items for clicking ({len(grid_items) if grid_items else 0}):")
        if grid_items:
            for g in grid_items:
                print(f"  [{g['x']},{g['y']}] {g['text']!r}")

        # Click first app
        if grid_items and len(grid_items) > 0:
            for app in grid_items[:8]:
                print(f"\nClicking app: {app['text']}")
                await click(ws, app['x'], app['y'])
                await asyncio.sleep(3)
                safe = app['text'].replace('/','_').replace(' ','_')
                await screenshot(ws, f"app_open_{safe}.png")
                # Go back
                await click(ws, 720, 21)
                await asyncio.sleep(1.5)

    # ── Part 3: AI assistant - navigate all tabs ──
    if ai_target:
        print(f"\n{'='*60}")
        print("AI Assistant tabs navigation")
        async with websockets.connect(ai_target["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
            await send(ws, "Page.enable")
            await send(ws, "Runtime.enable")

            # Navigate to 配置 page
            await js(ws, "location.hash = '#/agentic/config'")
            await asyncio.sleep(2)
            config_text = await js(ws, "document.body.innerText.substring(0,4000)")
            print(f"\n配置 page:\n{config_text[:2000]}")

            # Navigate to 专家
            await js(ws, "location.hash = '#/agentic/expert'")
            await asyncio.sleep(2)
            expert_text = await js(ws, "document.body.innerText.substring(0,4000)")
            print(f"\n专家 page:\n{expert_text[:2000]}")

            # Navigate to 创作
            await js(ws, "location.hash = '#/agentic/create'")
            await asyncio.sleep(2)
            create_text = await js(ws, "document.body.innerText.substring(0,4000)")
            print(f"\n创作 page:\n{create_text[:2000]}")

            # Navigate to 会话
            await js(ws, "location.hash = '#/agentic/thread'")
            await asyncio.sleep(2)
            thread_text = await js(ws, "document.body.innerText.substring(0,4000)")
            print(f"\n会话 page:\n{thread_text[:2000]}")

            with open(f"{SCREENSHOT_DIR}/ai_all_content.json", "w", encoding="utf-8") as f:
                json.dump({
                    "config": config_text,
                    "expert": expert_text,
                    "create": create_text,
                    "thread": thread_text
                }, f, ensure_ascii=False, indent=2)

    print("\n✅ Done")

asyncio.run(main())
