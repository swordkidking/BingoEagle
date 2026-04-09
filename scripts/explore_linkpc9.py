"""
Phase 9: Explore the dropdown menu next to 应用 tab
Modules: 通讯录, 云盘, 动态, 日程, 协作
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

async def press_esc(ws):
    await send(ws, "Input.dispatchKeyEvent", {"type":"keyDown","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
    await send(ws, "Input.dispatchKeyEvent", {"type":"keyUp","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})

async def get_page_info(ws):
    text = await js(ws, "document.body.innerText.substring(0,5000)")
    all_items = await js(ws, """
        (() => {
            const items = [];
            for (const el of document.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                const t = el.textContent.trim();
                if (t && t.length < 40 && el.children.length === 0
                    && r.width > 5 && r.height > 5) {
                    items.push({text: t, x: Math.round(r.x), y: Math.round(r.y),
                                cls: el.className.substring(0,50), tag: el.tagName});
                }
            }
            const seen = new Set();
            return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
        })()
    """)
    return text, all_items

async def main():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())
    home = next((t for t in targets if t.get("type") == "page"), None)

    async with websockets.connect(home["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # First: find the dropdown arrow next to 应用
        # From the screenshot: arrow is at ~760,21 area
        # Let's find it precisely
        nav_items = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('*')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (r.y > 0 && r.y < 50 && r.x > 600 && r.width > 0 && r.width < 100) {
                        items.push({text: t.substring(0,30), x: Math.round(r.x),
                                    y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                                    tag: el.tagName, cls: el.className.substring(0,60)});
                    }
                }
                return items;
            })()
        """)
        print("Top nav items (x>600):")
        for n in (nav_items or []):
            print(f"  [{n['x']},{n['y']}] w={n['w']} h={n['h']} tag={n['tag']} cls={n['cls'][:40]} text={n['text']!r}")

        # Click the dropdown arrow (应用 ▾) - it's the trigger next to 应用 tab
        # From screenshot it appears to be around x=760, y=21
        print("\n--- Clicking dropdown arrow next to 应用 ---")
        await click(ws, 760, 21)
        await asyncio.sleep(1.5)
        await screenshot(ws, "dropdown_menu.png")

        # Get menu items
        menu_items = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('*')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 20 && el.children.length === 0
                        && r.x > 600 && r.x < 900
                        && r.y > 30 && r.y < 300
                        && r.width > 10 && r.height > 10) {
                        items.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2),
                                    cls: el.className.substring(0,50)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"\nDropdown menu items ({len(menu_items) if menu_items else 0}):")
        for m in (menu_items or []):
            print(f"  [{m['x']},{m['y']}] {m['text']!r}")

        # Now explore each module
        modules = ["通讯录", "云盘", "动态", "日程", "协作"]

        for mod_name in modules:
            print(f"\n{'='*60}")
            print(f"🔍 Exploring: {mod_name}")

            # Re-open dropdown
            await click(ws, 760, 21)
            await asyncio.sleep(1.5)

            # Find and click the module
            target = await js(ws, f"""
                (() => {{
                    for (const el of document.querySelectorAll('*')) {{
                        const t = el.textContent.trim();
                        if (t === '{mod_name}') {{
                            const r = el.getBoundingClientRect();
                            if (r.width > 0 && r.height > 0)
                                return {{x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)}};
                        }}
                    }}
                    return null;
                }})()
            """)

            if target:
                print(f"  Found at ({target['x']},{target['y']})")
                await click(ws, target['x'], target['y'])
            else:
                print(f"  ⚠️ Not found in dropdown, trying direct click")
                # Try clicking by known positions from screenshot
                known_pos = {"通讯录": (745, 75), "云盘": (745, 105),
                             "动态": (745, 135), "日程": (745, 165), "协作": (745, 195)}
                pos = known_pos.get(mod_name, (745, 100))
                await click(ws, pos[0], pos[1])

            await asyncio.sleep(3)
            await screenshot(ws, f"module_{mod_name}_01.png")

            # Get page content
            text, all_items = await get_page_info(ws)
            print(f"\n  Page text:\n{text[:1000]}")
            print(f"\n  UI items ({len(all_items) if all_items else 0}):")
            for item in (all_items or [])[:40]:
                print(f"    [{item['x']},{item['y']}] {item['text']!r} cls={item['cls'][:30]}")

            # Save structure
            with open(f"{SCREENSHOT_DIR}/module_{mod_name}_structure.json", "w", encoding="utf-8") as f:
                json.dump({"text": text, "items": all_items}, f, ensure_ascii=False, indent=2)

            # Explore sub-navigation
            if all_items:
                # Left-side nav items (sidebar)
                left_items = [it for it in all_items if it['x'] < 300 and it['y'] > 40]
                print(f"\n  Left sidebar items: {len(left_items)}")
                for item in left_items[:20]:
                    print(f"    [{item['x']},{item['y']}] {item['text']!r}")

                # Click through sub-nav items
                for i, item in enumerate(left_items[:8]):
                    print(f"\n  Clicking sub-nav: {item['text']!r}")
                    await click(ws, item['x'] + 10, item['y'] + 10)
                    await asyncio.sleep(2.5)
                    safe = item['text'].replace('/','_').replace(' ','_')
                    await screenshot(ws, f"module_{mod_name}_{i+2:02d}_{safe}.png")

            # Also scroll down to see more content
            await js(ws, "window.scrollTo(0, 500)")
            await asyncio.sleep(1)
            await screenshot(ws, f"module_{mod_name}_scrolled.png")
            await js(ws, "window.scrollTo(0, 0)")

        print("\n✅ All modules explored!")

asyncio.run(main())
