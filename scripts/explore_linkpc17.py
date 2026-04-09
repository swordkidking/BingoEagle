"""
Phase 17: 最简策略 - 点击后固定等2秒立即截图
对于在新窗口打开的：截图新窗口
对于在home.html内SPA渲染的：截图home.html（等2秒页面渲染完）
对于在webview渲染的：截图对应webview
"""
import time, json, base64, os, sys, subprocess, urllib.request

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots/apps3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(msg): print(msg, flush=True)

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as r:
        return json.loads(r.read())

CLICK_AND_SCREENSHOT = """
import asyncio, json, base64, sys, websockets, time

async def main():
    home_ws = sys.argv[1]
    ax, ay = int(sys.argv[2]), int(sys.argv[3])
    out_path = sys.argv[4]
    wait = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0

    async with websockets.connect(home_ws, max_size=100*1024*1024, open_timeout=8) as ws:
        _id = [0]
        async def send(m, p=None):
            _id[0] += 1
            msg = {"id": _id[0], "method": m, "params": p or {}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                d = json.loads(raw)
                if d.get("id") == _id[0]:
                    return d.get("result", {})

        # 点击应用tab
        await send("Input.dispatchMouseEvent", {"type":"mousePressed","x":720,"y":21,"button":"left","clickCount":1})
        await send("Input.dispatchMouseEvent", {"type":"mouseReleased","x":720,"y":21,"button":"left","clickCount":1})
        await asyncio.sleep(1.2)
        # ESC关闭搜索
        await send("Input.dispatchKeyEvent", {"type":"keyDown","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
        await send("Input.dispatchKeyEvent", {"type":"keyUp","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
        await asyncio.sleep(0.4)
        # 点击应用
        await send("Input.dispatchMouseEvent", {"type":"mousePressed","x":ax,"y":ay,"button":"left","clickCount":1})
        await send("Input.dispatchMouseEvent", {"type":"mouseReleased","x":ax,"y":ay,"button":"left","clickCount":1})
        print("CLICKED", flush=True)
        # 等待渲染
        await asyncio.sleep(wait)
        # 截图
        r = await send("Page.captureScreenshot", {"format":"png"})
        if "data" in r:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(r["data"]))
            print(f"OK:{out_path}", flush=True)
        # 获取内容
        r2 = await send("Runtime.evaluate", {
            "expression": "JSON.stringify({url:location.href,title:document.title,text:document.body?document.body.innerText.substring(0,1500):''})",
            "returnByValue": True
        })
        val = r2.get("result",{}).get("value","{}")
        print(f"CONTENT:{val}", flush=True)

asyncio.run(main())
"""

def click_and_screenshot_home(home_ws, ax, ay, out_path, wait=2.0):
    result = subprocess.run(
        [sys.executable, '-c', CLICK_AND_SCREENSHOT, home_ws, str(ax), str(ay), out_path, str(wait)],
        capture_output=True, text=True, timeout=30
    )
    content = {}
    for line in result.stdout.splitlines():
        if line.startswith("OK:"):
            size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
            log(f"  ✅ {os.path.basename(out_path)} ({size//1024}KB)")
        elif line.startswith("CONTENT:"):
            try: content = json.loads(line[8:])
            except: pass
    if result.returncode != 0:
        log(f"  ❌ {result.stderr[:200]}")
    return content

SCREENSHOT_ONLY = """
import asyncio, json, base64, sys, websockets

async def main():
    ws_url, out_path = sys.argv[1], sys.argv[2]
    wait = float(sys.argv[3]) if len(sys.argv) > 3 else 0
    async with websockets.connect(ws_url, max_size=100*1024*1024, open_timeout=8) as ws:
        _id = [0]
        async def send(m, p=None):
            _id[0] += 1
            msg = {"id": _id[0], "method": m, "params": p or {}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                d = json.loads(raw)
                if d.get("id") == _id[0]:
                    return d.get("result", {})
        if wait > 0:
            import asyncio as a2; await a2.sleep(wait)
        r = await send("Page.captureScreenshot", {"format":"png"})
        if "data" in r:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(r["data"]))
            print(f"OK:{out_path}", flush=True)
        r2 = await send("Runtime.evaluate", {
            "expression": "JSON.stringify({url:location.href,title:document.title,text:document.body?document.body.innerText.substring(0,1500):''})",
            "returnByValue": True
        })
        val = r2.get("result",{}).get("value","{}")
        print(f"CONTENT:{val}", flush=True)
asyncio.run(main())
"""

def screenshot_target(ws_url, out_path, wait=0):
    result = subprocess.run(
        [sys.executable, '-c', SCREENSHOT_ONLY, ws_url, out_path, str(wait)],
        capture_output=True, text=True, timeout=25
    )
    content = {}
    for line in result.stdout.splitlines():
        if line.startswith("OK:"):
            size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
            log(f"  ✅ {os.path.basename(out_path)} ({size//1024}KB)")
        elif line.startswith("CONTENT:"):
            try: content = json.loads(line[8:])
            except: pass
    if result.returncode != 0:
        log(f"  ❌ {result.stderr[:200]}")
    return content

def main():
    subprocess.run(['osascript', '-e', 'tell application "品高聆客" to activate'], timeout=3)
    time.sleep(1)

    targets = get_targets()
    home = next((t for t in targets if t.get("type") == "page" and 'home' in t.get('url','').lower()), None)
    if not home:
        log("❌ 找不到home"); return
    home_ws = home["webSocketDebuggerUrl"]
    initial_ids = {t['id'] for t in targets}
    log(f"home: {home['id'][:8]}, targets: {len(targets)}")

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

    for app_name, ax, ay in apps:
        safe = app_name.replace('/','_').replace(' ','_')
        log(f"\n{'='*50}")
        log(f"📱 {app_name}")

        before = get_targets()
        before_ids = {t['id'] for t in before}
        before_info = {t['id']: (t.get('title',''), t.get('url','')) for t in before}

        # 方案A：检测新窗口（同时点击+等待）
        # 先点击
        CLICK_ONLY = """
import asyncio, json, sys, websockets
async def main():
    ws_url = sys.argv[1]
    ax, ay = int(sys.argv[2]), int(sys.argv[3])
    async with websockets.connect(ws_url, max_size=5*1024*1024, open_timeout=5) as ws:
        _id=[0]
        async def send(m,p=None):
            _id[0]+=1; msg={"id":_id[0],"method":m,"params":p or {}}
            await ws.send(json.dumps(msg))
            while True:
                raw=await asyncio.wait_for(ws.recv(),timeout=8)
                d=json.loads(raw)
                if d.get("id")==_id[0]: return d.get("result",{})
        await send("Input.dispatchMouseEvent",{"type":"mousePressed","x":720,"y":21,"button":"left","clickCount":1})
        await send("Input.dispatchMouseEvent",{"type":"mouseReleased","x":720,"y":21,"button":"left","clickCount":1})
        await asyncio.sleep(1.2)
        await send("Input.dispatchKeyEvent",{"type":"keyDown","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
        await send("Input.dispatchKeyEvent",{"type":"keyUp","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
        await asyncio.sleep(0.4)
        await send("Input.dispatchMouseEvent",{"type":"mousePressed","x":ax,"y":ay,"button":"left","clickCount":1})
        await send("Input.dispatchMouseEvent",{"type":"mouseReleased","x":ax,"y":ay,"button":"left","clickCount":1})
        print("DONE",flush=True)
asyncio.run(main())
"""
        result = subprocess.run(
            [sys.executable, '-c', CLICK_ONLY, home_ws, str(ax), str(ay)],
            capture_output=True, text=True, timeout=15
        )
        if "DONE" not in result.stdout:
            log(f"  ❌ 点击失败: {result.stderr[:100]}")
            continue
        log(f"  已点击 ({ax},{ay})")

        # 等待检测新target（最多5秒）
        found_new = None
        for _ in range(17):
            time.sleep(0.3)
            after = get_targets()
            new_ts = [t for t in after if t['id'] not in before_ids
                      and t.get('type') in ('page','webview')
                      and t.get('webSocketDebuggerUrl')]
            if new_ts:
                found_new = new_ts[-1]
                log(f"  新窗口: {found_new.get('title','')!r}")
                break
            # title/url变化
            changed = None
            for t in after:
                if t['id'] in before_info and t.get('webSocketDebuggerUrl'):
                    old_t, old_u = before_info[t['id']]
                    if t.get('title','') != old_t or t.get('url','') != old_u:
                        changed = t
                        log(f"  变化: {old_t!r} -> {t.get('title','')!r}")
                        break
            if changed:
                found_new = changed
                break

        out = f"{SCREENSHOT_DIR}/{safe}_01.png"
        if found_new:
            # 截图新窗口/变化的webview
            time.sleep(2.5 if found_new.get('type') == 'page' else 1.5)
            content = screenshot_target(found_new["webSocketDebuggerUrl"], out)
        else:
            # 截图home.html（SPA内渲染）
            log(f"  截图主窗口（SPA渲染）")
            time.sleep(1.5)
            content = screenshot_target(home_ws, out)

        log(f"  标题: {content.get('title','?')!r}")
        log(f"  内容: {content.get('text','')[:120]}")
        with open(f"{SCREENSHOT_DIR}/{safe}_content.json","w",encoding="utf-8") as f:
            json.dump({"app":app_name,"type":"new" if found_new else "spa",
                       **content}, f, ensure_ascii=False, indent=2)

        # 关闭新窗口
        time.sleep(0.5)
        for t in get_targets():
            if t['id'] not in initial_ids:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}", timeout=3)
                    log(f"  已关闭: {t.get('title','')!r}")
                except: pass
        time.sleep(0.5)

    log("\n✅ 全部完成！")

main()
