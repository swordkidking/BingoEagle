"""
Phase 12: Smart app screenshot - watch for both new targets AND URL changes in existing webviews.
Apps can open via:
1. New CDP target (new browser window)
2. URL change in existing BingoERP webview (erp.bingosoft.net/...)
3. URL change in existing 项目管理 webview (projectcollaboration.bingosoft.net/...)
4. URL change in existing 邮箱 webview

Strategy: record URL of all existing webviews before click, then after click check:
- Any new target? Screenshot it.
- Any webview URL changed? Screenshot that webview.
- Neither? Screenshot the main window anyway (some apps are iframes in main).
"""
import asyncio
import json
import base64
import os
import urllib.request
import websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots/apps2"
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

async def js(ws, expr, timeout=15):
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

async def connect_and_screenshot(t, filename, wait=4):
    """Connect to a target and screenshot it"""
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url:
        print(f"  ⚠️ No webSocketDebuggerUrl for {t.get('title','')}")
        return None
    try:
        async with websockets.connect(ws_url, max_size=100*1024*1024) as ws2:
            await send(ws2, "Page.enable")
            await send(ws2, "Runtime.enable")
            await asyncio.sleep(wait)
            return await screenshot(ws2, filename)
    except Exception as e:
        print(f"  ❌ connect_and_screenshot: {e}")
    return None

async def get_target_url(t):
    """Get current URL from a webview target"""
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url:
        return t.get("url", "")
    try:
        async with websockets.connect(ws_url, max_size=100*1024*1024) as ws2:
            url = await js(ws2, "location.href", timeout=5)
            return url or t.get("url", "")
    except:
        return t.get("url", "")

async def get_target_content(t):
    """Get text content + nav from a webview target"""
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url:
        return None, None
    try:
        async with websockets.connect(ws_url, max_size=100*1024*1024) as ws2:
            text = await js(ws2, "document.body ? document.body.innerText.substring(0,3000) : ''")
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
            return text, nav
    except Exception as e:
        return None, None

async def click_nav_and_screenshot(t, safe_name, nav_items):
    """Click through nav items and screenshot"""
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url or not nav_items:
        return
    try:
        async with websockets.connect(ws_url, max_size=100*1024*1024) as ws2:
            await send(ws2, "Page.enable")
            await send(ws2, "Runtime.enable")
            left_nav = [n for n in nav_items if n.get('x', 999) < 250 and n.get('y', 0) > 40][:6]
            for i, item in enumerate(left_nav):
                await send(ws2, "Input.dispatchMouseEvent", {
                    "type":"mousePressed","x":item['x']+10,"y":item['y'],
                    "button":"left","clickCount":1
                })
                await send(ws2, "Input.dispatchMouseEvent", {
                    "type":"mouseReleased","x":item['x']+10,"y":item['y'],
                    "button":"left","clickCount":1
                })
                await asyncio.sleep(2.5)
                await screenshot(ws2, f"{safe_name}_{i+2:02d}_{item['text'][:15]}.png")
    except Exception as e:
        print(f"  ❌ nav screenshot: {e}")

async def explore_app(main_ws, app_name, x, y, initial_snapshot):
    """Click an app, detect where it opened, screenshot it"""
    safe = app_name.replace('/','_').replace(' ','_')
    print(f"\n{'='*50}")
    print(f"📱 {app_name}")

    # Record state before click
    before_targets = get_targets()
    before_ids = {t['id'] for t in before_targets}
    before_urls = {t['id']: t.get('url','') for t in before_targets}

    # Navigate to apps tab and click
    await click(main_ws, 720, 21)
    await asyncio.sleep(1.5)
    await press_esc(main_ws)
    await asyncio.sleep(0.5)
    await click(main_ws, x, y)

    # Wait and check what changed
    found_target = None
    found_type = None
    for attempt in range(20):  # up to 10 seconds
        await asyncio.sleep(0.5)
        after_targets = get_targets()

        # Check for new target
        new_targets = [t for t in after_targets if t['id'] not in before_ids
                      and t.get('type') in ('page', 'webview')]
        if new_targets:
            found_target = new_targets[-1]
            found_type = 'new'
            print(f"  New target [{found_target['type']}]: {found_target.get('title','')!r}")
            break

        # Check for URL change in existing webviews
        for t in after_targets:
            if t['id'] in before_urls and t.get('type') == 'webview':
                new_url = t.get('url', '')
                old_url = before_urls[t['id']]
                if new_url != old_url and 'fromAppDesktop=1' in new_url:
                    # URL changed - this webview now shows the app
                    found_target = t
                    found_type = 'url_change'
                    print(f"  URL changed in webview [{t.get('title','')!r}]: {new_url[:80]}")
                    break
        if found_target:
            break

    if not found_target:
        print(f"  ⚠️ No change detected, capturing BingoERP webview as fallback")
        # Find BingoERP webview
        after_targets = get_targets()
        erp = next((t for t in after_targets if 'BingoERP' in t.get('title','') or 'erp.bingosoft.net' in t.get('url','')), None)
        if erp:
            found_target = erp
            found_type = 'fallback_erp'

    if found_target:
        # Wait for content to load
        wait_time = 5 if found_type == 'new' else 3
        await asyncio.sleep(wait_time)

        # Screenshot
        await connect_and_screenshot(found_target, f"{safe}_01.png", wait=0)

        # Get content
        text, nav = await get_target_content(found_target)
        print(f"  Content: {text[:300] if text else '(empty)'}")

        # Click nav items
        if nav:
            await click_nav_and_screenshot(found_target, safe, nav)

        # Save content JSON
        with open(f"{SCREENSHOT_DIR}/{safe}_content.json", "w", encoding="utf-8") as f:
            json.dump({
                "app": app_name,
                "type": found_type,
                "url": found_target.get("url",""),
                "title": found_target.get("title",""),
                "text": text,
                "nav": nav
            }, f, ensure_ascii=False, indent=2)

    # Clean up new windows
    await asyncio.sleep(1)
    after = get_targets()
    for t in after:
        if t['id'] not in {tt['id'] for tt in initial_snapshot}:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}") as r:
                    print(f"  Closed: {t.get('title','')!r}")
            except:
                pass
    await asyncio.sleep(0.5)

async def main():
    initial_targets = get_targets()
    home = next((t for t in initial_targets if t.get("type") == "page" and 'home' in t.get('url','').lower()), None)

    print(f"Initial targets ({len(initial_targets)}):")
    for t in initial_targets:
        print(f"  [{t['type']}] {t.get('title','')!r} url={t.get('url','')[:60]}")

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
            try:
                await explore_app(ws, app_name, x, y, initial_targets)
            except Exception as e:
                print(f"  ❌ Error on {app_name}: {e}")

    print("\n✅ All apps done!")
    print(f"📁 Screenshots: {SCREENSHOT_DIR}")

asyncio.run(main())
