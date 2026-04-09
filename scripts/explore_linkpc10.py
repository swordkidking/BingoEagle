"""
Phase 10: Open each app one by one, wait for load, screenshot
Apps from the desktop screenshot:
Row 1: 请假与考勤, 协作, Excel, 系统管理, 品高CRM, 邮箱, 招聘系统, 会议系统, 工单系统
Row 2: 报销与请款, 项目工作, 运营看板, 品高合同系统, 项目协管, 超域协作, 薪酬系统, 请示, CRM
Row 3: 工作量填报, 工作量查询, 规章制度, 绩效系统, 应用工场, 公章申请, 办事指南, 全域BI小助理, 签到管理
Row 4: 汇报
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

async def wait_for_load(ws, max_wait=8):
    """Wait until page stops changing (loading indicator gone)"""
    for i in range(max_wait):
        await asyncio.sleep(1)
        loading = await js(ws, """
            (() => {
                // Check for loading indicators
                const loadingTexts = ['努力加载中', '加载中', 'loading', 'Loading'];
                for (const el of document.querySelectorAll('*')) {
                    const t = el.textContent.trim();
                    if (loadingTexts.some(lt => t === lt)) return true;
                }
                return false;
            })()
        """)
        if not loading:
            break
    await asyncio.sleep(1)  # extra buffer

async def get_app_content(ws):
    """Get page text and structure after app loads"""
    text = await js(ws, "document.body ? document.body.innerText.substring(0, 3000) : ''")
    # Get nav items
    nav = await js(ws, """
        (() => {
            const items = [];
            for (const el of document.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                const t = el.textContent.trim();
                if (t && t.length < 30 && el.children.length === 0
                    && r.x < 300 && r.y > 30 && r.width > 5 && r.height > 5) {
                    items.push({text: t, x: Math.round(r.x), y: Math.round(r.y)});
                }
            }
            const seen = new Set();
            return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
        })()
    """)
    return text, nav

async def open_app_and_screenshot(ws, app_name, app_x, app_y):
    """Go to apps tab, click app, wait for load, screenshot"""
    print(f"\n{'='*50}")
    print(f"📱 Opening: {app_name}")

    # Go to 应用 tab
    await click(ws, 720, 21)
    await asyncio.sleep(1.5)
    await press_esc(ws)
    await asyncio.sleep(0.5)

    # Click the app icon
    await click(ws, app_x, app_y)
    await asyncio.sleep(1)

    # Wait for loading to complete
    await wait_for_load(ws, max_wait=10)

    # Screenshot
    safe = app_name.replace('/','_').replace(' ','_')
    await screenshot(ws, f"{safe}_01.png")

    # Get content
    text, nav = await get_app_content(ws)
    print(f"  Text: {text[:300]}")
    print(f"  Nav ({len(nav) if nav else 0}): {[n['text'] for n in (nav or [])[:15]]}")

    # Save content
    with open(f"{SCREENSHOT_DIR}/{safe}_content.json", "w", encoding="utf-8") as f:
        json.dump({"app": app_name, "text": text, "nav": nav}, f, ensure_ascii=False, indent=2)

    # Click through sub-navigation (left sidebar)
    if nav and len(nav) > 1:
        for i, item in enumerate(nav[:6]):
            print(f"  Sub-nav: {item['text']}")
            await click(ws, item['x'] + 10, item['y'])
            await asyncio.sleep(2.5)
            await wait_for_load(ws, max_wait=5)
            await screenshot(ws, f"{safe}_{i+2:02d}_{item['text'][:15]}.png")

async def main():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())
    home = next((t for t in targets if t.get("type") == "page"), None)

    async with websockets.connect(home["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # App positions from the desktop (full-screen layout)
        # Row 1 (y≈135): 请假与考勤, 协作, Excel, 系统管理, 品高CRM, 邮箱, 招聘系统, 会议系统, 工单系统
        # Row 2 (y≈251): 报销与请款, 项目工作, 运营看板, 品高合同系统, 项目协管, 超域协作, 薪酬系统, 请示, CRM
        # Row 3 (y≈367): 工作量填报, 工作量查询, 规章制度, 绩效系统, 应用工场, 公章申请, 办事指南, 全域BI小助理, 签到管理
        # Row 4 (y≈483): 汇报

        apps = [
            # Row 1
            ("请假与考勤",  47, 135),
            ("协作",        147, 135),
            ("Excel",       247, 135),
            ("系统管理",    347, 135),
            ("品高CRM",     447, 135),
            ("邮箱",        547, 135),
            ("招聘系统",    647, 135),
            ("会议系统",    747, 135),
            ("工单系统",    847, 135),
            # Row 2
            ("报销与请款",  47, 251),
            ("项目工作",    147, 251),
            ("运营看板",    247, 251),
            ("品高合同系统", 347, 251),
            ("项目协管",    447, 251),
            ("超域协作",    547, 251),
            ("薪酬系统",    647, 251),
            ("请示",        747, 251),
            ("CRM",         847, 251),
            # Row 3
            ("工作量填报",  47, 367),
            ("工作量查询",  147, 367),
            ("规章制度",    247, 367),
            ("绩效系统",    347, 367),
            ("应用工场",    447, 367),
            ("公章申请",    547, 367),
            ("办事指南",    647, 367),
            ("全域BI小助理", 747, 367),
            ("签到管理",    847, 367),
            # Row 4
            ("汇报",        47, 483),
        ]

        for app_name, x, y in apps:
            try:
                await open_app_and_screenshot(ws, app_name, x, y)
            except Exception as e:
                print(f"  ❌ Error on {app_name}: {e}")

        print("\n✅ All apps explored!")
        print(f"📁 Screenshots: {SCREENSHOT_DIR}")

asyncio.run(main())
