"""
Phase 11: Click app → detect new CDP target → screenshot the new target
Apps open in new browser windows which become new CDP targets
"""
import asyncio
import json
import base64
import os
import urllib.request
import websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots/apps"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        return json.loads(resp.read())

async def screenshot_new_target(existing_ids, app_name, wait_secs=8):
    """Wait for a new CDP target to appear, then screenshot it"""
    safe = app_name.replace('/','_').replace(' ','_')

    for attempt in range(wait_secs * 2):
        await asyncio.sleep(0.5)
        targets = get_targets()
        new_targets = [t for t in targets if t['id'] not in existing_ids]
        if new_targets:
            # Use the newest target
            new_t = new_targets[-1]
            print(f"  New target: [{new_t['type']}] {new_t.get('title','')!r} {new_t.get('url','')[:60]}")
            try:
                async with websockets.connect(new_t["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws2:
                    await send(ws2, "Page.enable")
                    await send(ws2, "Runtime.enable")
                    # Wait for page to load
                    await asyncio.sleep(5)
                    await screenshot(ws2, f"{safe}_01.png")
                    # Get content
                    text = await js(ws2, "document.body ? document.body.innerText.substring(0,3000) : ''")
                    print(f"  Content: {text[:400] if text else '(empty)'}")

                    # Get nav structure
                    nav = await js(ws2, """
                        (() => {
                            const items = [];
                            for (const el of document.querySelectorAll('*')) {
                                const r = el.getBoundingClientRect();
                                const t = el.textContent.trim();
                                if (t && t.length < 30 && el.children.length === 0
                                    && r.width > 5 && r.height > 5) {
                                    items.push({text: t, x: Math.round(r.x), y: Math.round(r.y)});
                                }
                            }
                            const seen = new Set();
                            return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
                        })()
                    """)

                    # Click through left nav items
                    left_nav = [n for n in (nav or []) if n['x'] < 250 and n['y'] > 40]
                    print(f"  Left nav: {[n['text'] for n in left_nav[:10]]}")

                    for i, item in enumerate(left_nav[:8]):
                        await click(ws2, item['x'] + 10, item['y'])
                        await asyncio.sleep(3)
                        await screenshot(ws2, f"{safe}_{i+2:02d}_{item['text'][:15]}.png")

                    with open(f"{SCREENSHOT_DIR}/{safe}_content.json", "w", encoding="utf-8") as f:
                        json.dump({"app": app_name, "url": new_t.get("url",""), "text": text, "nav": nav}, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"  ❌ Error connecting to new target: {e}")
            return new_t['id']
    print(f"  ⚠️ No new target appeared for {app_name}")
    return None

async def close_extra_targets(keep_ids):
    """Close any extra targets not in keep_ids"""
    targets = get_targets()
    for t in targets:
        if t['id'] not in keep_ids and t.get('type') in ('page', 'webview'):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}") as r:
                    pass
            except:
                pass

async def main():
    # Get initial targets
    initial_targets = get_targets()
    initial_ids = {t['id'] for t in initial_targets}
    home = next((t for t in initial_targets if t.get("type") == "page"), None)

    print(f"Initial targets: {len(initial_targets)}")
    for t in initial_targets:
        print(f"  [{t['type']}] {t.get('title','')!r}")

    # App list with positions
    apps = [
        ("请假与考勤",  47, 135),
        ("协作",        147, 135),
        ("Excel",       247, 135),
        ("系统管理",    347, 135),
        ("品高CRM",     447, 135),
        ("邮箱",        547, 135),
        ("招聘系统",    647, 135),
        ("会议系统",    747, 135),
        ("工单系统",    847, 135),
        ("报销与请款",  47, 251),
        ("项目工作",    147, 251),
        ("运营看板",    247, 251),
        ("品高合同系统", 347, 251),
        ("项目协管",    447, 251),
        ("超域协作",    547, 251),
        ("薪酬系统",    647, 251),
        ("请示",        747, 251),
        ("CRM",         847, 251),
        ("工作量填报",  47, 367),
        ("工作量查询",  147, 367),
        ("规章制度",    247, 367),
        ("绩效系统",    347, 367),
        ("应用工场",    447, 367),
        ("公章申请",    547, 367),
        ("办事指南",    647, 367),
        ("全域BI小助理", 747, 367),
        ("签到管理",    847, 367),
        ("汇报",        47, 483),
    ]

    async with websockets.connect(home["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        for app_name, x, y in apps:
            print(f"\n{'='*50}")
            print(f"📱 {app_name}")

            # Record current targets
            before_targets = get_targets()
            before_ids = {t['id'] for t in before_targets}

            # Go to apps tab
            await click(ws, 720, 21)
            await asyncio.sleep(1.5)
            await press_esc(ws)
            await asyncio.sleep(0.5)

            # Click the app
            await click(ws, x, y)

            # Wait for and screenshot new target
            new_id = await screenshot_new_target(before_ids, app_name, wait_secs=12)

            # Close extra windows to keep things clean
            await asyncio.sleep(1)
            current_targets = get_targets()
            for t in current_targets:
                if t['id'] not in initial_ids:
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}") as r:
                            print(f"  Closed: {t.get('title','')!r}")
                    except:
                        pass
            await asyncio.sleep(1)

    print("\n✅ All apps done!")

asyncio.run(main())
