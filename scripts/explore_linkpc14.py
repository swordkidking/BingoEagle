"""
Phase 14: 最终版 - 检测所有webview的URL变化，快速截图
关键改进：
1. 记录所有webview的初始URL
2. 点击后0.3秒轮询，检测任何webview的URL变化
3. 同时检测新target
4. fallback时截图所有webview当前状态
5. 不持久持有任何WebSocket连接（每次短暂连接）
"""
import asyncio
import json
import base64
import os
import sys
import urllib.request
import websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots/apps3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

_id = 0
def next_id():
    global _id; _id += 1; return _id

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as resp:
        return json.loads(resp.read())

async def cdp(ws_url, method, params=None, timeout=10):
    async with websockets.connect(ws_url, max_size=50*1024*1024, open_timeout=5) as ws:
        msg = {"id": 1, "method": method, "params": params or {}}
        await ws.send(json.dumps(msg))
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            data = json.loads(raw)
            if data.get("id") == 1:
                return data.get("result", {})

async def screenshot_target(t, filename):
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url:
        print(f"  ⚠️ 无webSocketDebuggerUrl")
        return False
    try:
        async with websockets.connect(ws_url, max_size=100*1024*1024, open_timeout=5) as ws:
            msg = {"id": 1, "method": "Page.captureScreenshot", "params": {"format": "png"}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                data = json.loads(raw)
                if data.get("id") == 1:
                    r = data.get("result", {})
                    if "data" in r:
                        path = f"{SCREENSHOT_DIR}/{filename}"
                        with open(path, "wb") as f:
                            f.write(base64.b64decode(r["data"]))
                        size = os.path.getsize(path)
                        print(f"  ✅ {filename} ({size//1024}KB)")
                        return True
                    break
    except Exception as e:
        print(f"  ❌ screenshot {filename}: {e}")
    return False

async def get_url(t):
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url:
        return t.get("url", "")
    try:
        async with websockets.connect(ws_url, max_size=5*1024*1024, open_timeout=3) as ws:
            msg = {"id": 1, "method": "Runtime.evaluate",
                   "params": {"expression": "location.href", "returnByValue": True}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(raw)
                if data.get("id") == 1:
                    return data.get("result", {}).get("result", {}).get("value", t.get("url",""))
    except:
        return t.get("url", "")

async def get_text(t):
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url:
        return ""
    try:
        async with websockets.connect(ws_url, max_size=50*1024*1024, open_timeout=5) as ws:
            msg = {"id": 1, "method": "Runtime.evaluate",
                   "params": {"expression": "document.body ? document.body.innerText.substring(0,2000) : ''",
                               "returnByValue": True}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(raw)
                if data.get("id") == 1:
                    return data.get("result", {}).get("result", {}).get("value", "")
    except:
        return ""

async def do_click(home_ws_url, x, y):
    """在home窗口发送鼠标点击事件"""
    try:
        async with websockets.connect(home_ws_url, max_size=10*1024*1024, open_timeout=5) as ws:
            for event_type in ["mousePressed", "mouseReleased"]:
                msg = {"id": next_id(), "method": "Input.dispatchMouseEvent",
                       "params": {"type": event_type, "x": x, "y": y,
                                  "button": "left", "clickCount": 1}}
                await ws.send(json.dumps(msg))
                await asyncio.wait_for(ws.recv(), timeout=5)
        return True
    except Exception as e:
        print(f"  ⚠️ click失败: {e}")
        return False

async def do_key(home_ws_url, key, code, vk):
    try:
        async with websockets.connect(home_ws_url, max_size=10*1024*1024, open_timeout=5) as ws:
            for event_type in ["keyDown", "keyUp"]:
                msg = {"id": next_id(), "method": "Input.dispatchKeyEvent",
                       "params": {"type": event_type, "key": key, "code": code,
                                  "windowsVirtualKeyCode": vk}}
                await ws.send(json.dumps(msg))
                await asyncio.wait_for(ws.recv(), timeout=5)
        return True
    except:
        return False

async def main():
    sys.stdout.reconfigure(line_buffering=True)

    targets = get_targets()
    home = next((t for t in targets if t.get("type") == "page" and 'home' in t.get('url','').lower()), None)
    if not home:
        print("❌ 找不到home.html target")
        return

    home_ws = home["webSocketDebuggerUrl"]
    initial_ids = {t['id'] for t in targets}

    # 记录所有webview的初始URL
    webviews = [t for t in targets if t.get('type') == 'webview' and t.get('webSocketDebuggerUrl')]
    print(f"初始webview数量: {len(webviews)}")
    initial_urls = {}
    for t in webviews:
        url = await get_url(t)
        initial_urls[t['id']] = url
        print(f"  [{t['id'][:8]}] {t.get('title','')[:30]!r} => {url[:70]}")

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

    for app_name, x, y in apps:
        safe = app_name.replace('/','_').replace(' ','_')
        print(f"\n{'='*50}", flush=True)
        print(f"📱 {app_name}", flush=True)

        before_targets = get_targets()
        before_ids = {t['id'] for t in before_targets}
        # 记录点击前所有webview的URL（从CDP实时获取）
        before_urls = {}
        cur_webviews = [t for t in before_targets if t.get('type') == 'webview' and t.get('webSocketDebuggerUrl')]
        for t in cur_webviews:
            url = await get_url(t)
            before_urls[t['id']] = url

        # 点击应用tab
        await do_click(home_ws, 720, 21)
        await asyncio.sleep(1.2)
        # 关闭搜索框
        await do_key(home_ws, "Escape", "Escape", 27)
        await asyncio.sleep(0.4)
        # 点击应用图标
        await do_click(home_ws, x, y)
        print(f"  已点击 ({x},{y})", flush=True)

        # 快速轮询检测变化（每0.3秒，最多15秒=50次）
        found_target = None
        found_type = None
        for attempt in range(50):
            await asyncio.sleep(0.3)
            after_targets = get_targets()

            # 1. 检测新target
            new_ts = [t for t in after_targets
                      if t['id'] not in before_ids
                      and t.get('type') in ('page', 'webview')
                      and t.get('webSocketDebuggerUrl')]
            if new_ts:
                found_target = new_ts[-1]
                found_type = 'new'
                print(f"  检测到新窗口: {found_target.get('title','')!r}", flush=True)
                break

            # 2. 检测任意webview URL变化
            cur_wvs = [t for t in after_targets if t.get('type') == 'webview' and t.get('webSocketDebuggerUrl')]
            for t in cur_wvs:
                if t['id'] not in before_urls:
                    continue
                new_url = t.get('url', '')
                old_url = before_urls[t['id']]
                # URL变化且不是回到主页
                if new_url and new_url != old_url:
                    found_target = t
                    found_type = 'url_change'
                    print(f"  URL变化 [{t.get('title','')[:20]!r}]: {old_url[:50]} -> {new_url[:50]}", flush=True)
                    break
            if found_target:
                break

        if found_target:
            wait = 3 if found_type == 'new' else 1.5
            await asyncio.sleep(wait)
            await screenshot_target(found_target, f"{safe}_01.png")
            text = await get_text(found_target)
            final_url = await get_url(found_target)
            print(f"  最终URL: {final_url[:80]}", flush=True)
            print(f"  内容前200字: {text[:200] if text else '(空)'}", flush=True)
            with open(f"{SCREENSHOT_DIR}/{safe}_content.json", "w", encoding="utf-8") as f:
                json.dump({"app": app_name, "type": found_type,
                           "url": final_url, "text": text}, f, ensure_ascii=False, indent=2)
        else:
            print(f"  ⚠️ 未检测到变化，截图所有webview当前状态", flush=True)
            after_targets = get_targets()
            for t in after_targets:
                if t.get('type') == 'webview' and t.get('webSocketDebuggerUrl'):
                    cur_url = await get_url(t)
                    tname = t.get('title','')[:15].replace('/','_').replace(' ','_')
                    print(f"    webview {tname!r}: {cur_url[:70]}", flush=True)
                    await screenshot_target(t, f"{safe}_fb_{tname}.png")

        # 关闭新开的窗口
        await asyncio.sleep(0.5)
        after = get_targets()
        for t in after:
            if t['id'] not in initial_ids:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}", timeout=3)
                    print(f"  已关闭: {t.get('title','')!r}", flush=True)
                except:
                    pass
        await asyncio.sleep(0.5)

    print("\n✅ 全部完成！", flush=True)

asyncio.run(main())
