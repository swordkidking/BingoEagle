"""
Deep explore 品高聆客 - click all nav items and capture screenshots
Focus on the main home.html window which we can screenshot
Also try to navigate into all sections
"""
import asyncio
import json
import base64
import os
import urllib.request
import websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

_id = 0
def next_id():
    global _id; _id += 1; return _id

async def send(ws, method, params=None, timeout=15):
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

async def js(ws, expr, timeout=15):
    try:
        r = await send(ws, "Runtime.evaluate", {
            "expression": expr, "returnByValue": True, "awaitPromise": True
        }, timeout=timeout)
        return r.get("result", {}).get("value")
    except Exception as e:
        return None

async def click(ws, x, y):
    await send(ws, "Input.dispatchMouseEvent", {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
    await send(ws, "Input.dispatchMouseEvent", {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})

async def main():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())

    # Main home.html target
    home = next(t for t in targets if t.get("type") == "page")
    ws_url = home["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # ── 0. Initial state ──────────────────────────────────────
        await screenshot(ws, "01_home_initial.png")

        # ── 1. Click 消息 tab ─────────────────────────────────────
        print("\n[消息 tab]")
        await click(ws, 33, 23)
        await asyncio.sleep(2)
        await screenshot(ws, "02_messages_tab.png")

        # ── 2. Click different message filters ───────────────────
        filters = [
            ("全部",    75, 100),
            ("@我",    100, 155),
            ("未读",   100, 195),
            ("智能体",  100, 230),
            ("单聊",   100, 265),
            ("群组",   100, 305),
            ("工作",   100, 345),
            ("服务",   100, 385),
        ]
        for name, x, y in filters:
            print(f"\n  [{name}]")
            await click(ws, x, y)
            await asyncio.sleep(1.5)
            await screenshot(ws, f"03_msg_{name}.png")

        # ── 3. Click 应用 tab ─────────────────────────────────────
        print("\n[应用 tab]")
        await click(ws, 100, 23)  # 应用 tab
        await asyncio.sleep(2)
        await screenshot(ws, "04_apps_tab.png")

        # Get apps text
        text = await js(ws, "document.body.innerText.substring(0,3000)")
        print(f"Apps text:\n{text}")

        # Get app items
        apps = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('*')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 40 && el.children.length === 0 &&
                        r.width > 10 && r.height > 10 && r.x > 130) {
                        items.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"\nApp items ({len(apps)}):")
        for a in apps[:40]:
            print(f"  [{a['x']},{a['y']}] {a['text']}")

        # Click some apps
        if apps:
            for i, app in enumerate(apps[:15]):
                if any(kw in app['text'] for kw in ['会议','邮件','邮箱','日历','文档','云盘','待办','任务','审批','工作流','考勤','打卡']):
                    print(f"\n  Clicking app: {app['text']}")
                    await click(ws, app['x'], app['y'])
                    await asyncio.sleep(2.5)
                    await screenshot(ws, f"05_app_{app['text'][:10]}.png")
                    await click(ws, 33, 23)  # back to main
                    await asyncio.sleep(1)

        # ── 4. Try right-click context menus, settings etc ───────
        # Look for settings/profile icon top-right
        print("\n[Settings / Profile]")
        await click(ws, 680, 23)  # right side of nav
        await asyncio.sleep(1.5)
        await screenshot(ws, "06_profile_menu.png")
        await js(ws, "document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape'}))")

        # Search
        print("\n[Search]")
        search_btn = await js(ws, """
            (() => {
                for (const el of document.querySelectorAll('[class*="search"],button')) {
                    const r = el.getBoundingClientRect();
                    if (r.x > 300 && r.width > 10) return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
                }
                return {x: 600, y: 23};
            })()
        """)
        await click(ws, search_btn['x'], search_btn['y'])
        await asyncio.sleep(1.5)
        await screenshot(ws, "07_search.png")

        # ── 5. Explore message conversation ──────────────────────
        print("\n[Opening a conversation]")
        await click(ws, 33, 23)  # 消息 tab
        await asyncio.sleep(1)
        # Click first real conversation item
        conv = await js(ws, """
            (() => {
                for (const el of document.querySelectorAll('[class*="session"],[class*="chat"],[class*="conv"],[class*="item"]')) {
                    const r = el.getBoundingClientRect();
                    if (r.x > 5 && r.x < 250 && r.y > 60 && r.width > 50) {
                        return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            })()
        """)
        if conv:
            print(f"  Opening conversation at ({conv['x']},{conv['y']})")
            await click(ws, conv['x'], conv['y'])
            await asyncio.sleep(3)
            await screenshot(ws, "08_chat_window.png")
            # Get chat text
            chat_text = await js(ws, "document.body.innerText.substring(0,3000)")
            print(f"Chat text:\n{chat_text[:1000]}")

        # ── 6. Explore all section titles in full page ────────────
        print("\n[Full structure dump]")
        all_items = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('*')) {
                    const t = el.textContent.trim();
                    const r = el.getBoundingClientRect();
                    if (t && t.length > 0 && t.length < 60 && el.children.length === 0
                        && r.width > 5 && r.height > 5) {
                        items.push({text: t, x:Math.round(r.x), y:Math.round(r.y), cls: el.className.substring(0,50)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"All unique UI text items ({len(all_items)}):")
        for item in all_items:
            print(f"  [{item['x']},{item['y']}] {item['text']!r}")

        # Save
        with open(f"{SCREENSHOT_DIR}/full_structure.json","w",encoding="utf-8") as f:
            json.dump({"apps": apps, "all_items": all_items}, f, ensure_ascii=False, indent=2)

    print("\n✅ Done")

asyncio.run(main())
