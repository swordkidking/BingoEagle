"""
Phase 8: Close search box first, then properly screenshot apps and individual app openings
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

async def main():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())
    home = next((t for t in targets if t.get("type") == "page"), None)

    async with websockets.connect(home["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # Close search box with Escape
        await press_esc(ws)
        await asyncio.sleep(1)

        # Click somewhere neutral to close search
        await click(ws, 900, 500)
        await asyncio.sleep(1)
        await press_esc(ws)
        await asyncio.sleep(1)

        # Go to 应用 tab
        await click(ws, 720, 21)
        await asyncio.sleep(2)
        await press_esc(ws)
        await asyncio.sleep(0.5)

        # Screenshot clean apps tab
        await screenshot(ws, "apps_clean.png")

        # Now click individual apps - use positions from first screenshot
        # Apps visible: 请假与考勤(47,177), 协作(168,177), Excel(265,177), 系统管理(354,177)
        # 品高CRM(453,177), 邮箱(568,177), 招聘系统(654,177), 会议系统(754,177), 工单系统(854,177)
        # Row 2: 报销与请款(47,293), 项目工作(154,293), 运营看板(254,293), 品高合同系统(340,293)
        # 项目协管(454,293), 超域协作(554,293), 薪酬系统(654,293), 请示(768,293), CRM(867,293)
        # Row 3: 工作量填报(47,409), 工作量查询(147,409), 规章制度(254,409), 绩效系统(354,409)
        # 应用工场(454,409), 公章申请(554,409), 办事指南(654,409), 全域BI小助理(741,409), 签到管理(854,409)
        # Row 4: 汇报(68,525)

        apps_to_click = [
            ("请假与考勤", 47, 135),
            ("协作", 168, 135),
            ("Excel", 265, 135),
            ("系统管理", 354, 135),
            ("品高CRM", 453, 135),
            ("邮箱", 568, 135),
            ("招聘系统", 654, 135),
            ("会议系统", 754, 135),
            ("工单系统", 854, 135),
            ("报销与请款", 47, 251),
            ("项目工作", 154, 251),
            ("运营看板", 254, 251),
            ("品高合同系统", 340, 251),
            ("项目协管", 454, 251),
            ("超域协作", 554, 251),
            ("薪酬系统", 654, 251),
            ("请示", 768, 251),
            ("工作量填报", 47, 367),
            ("工作量查询", 147, 367),
            ("规章制度", 254, 367),
            ("绩效系统", 354, 367),
            ("应用工场", 454, 367),
            ("公章申请", 554, 367),
            ("办事指南", 654, 367),
            ("全域BI", 741, 367),
            ("签到管理", 854, 367),
            ("汇报", 68, 483),
        ]

        for name, x, y in apps_to_click:
            print(f"\nOpening: {name} @ ({x},{y})")
            await click(ws, x, y)
            await asyncio.sleep(3)
            await screenshot(ws, f"appview_{name}.png")

            # Check what opened - get page title and text
            title = await js(ws, "document.title")
            body = await js(ws, "document.body.innerText.substring(0,500)")
            print(f"  Title: {title}")
            print(f"  Body: {body[:200] if body else ''}")

            # Go back to apps tab
            await click(ws, 720, 21)
            await asyncio.sleep(1.5)
            await press_esc(ws)
            await asyncio.sleep(0.5)

        print("\n✅ Done")

asyncio.run(main())
