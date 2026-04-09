"""
Phase 16: 每个应用独立子进程处理，彻底解决连接占用问题。
主进程：点击应用 -> 等待 -> 启动子进程截图 -> 等子进程完成 -> 下一个应用

对于在新窗口打开的应用：截图新CDP target
对于在已有webview打开的应用：截图该webview（通过title变化识别）
对于在home.html内渲染的应用：截图home.html的Page.captureScreenshot
"""
import asyncio, json, base64, os, sys, subprocess, urllib.request, time, websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots/apps3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(msg): print(msg, flush=True)

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as r:
        return json.loads(r.read())

# ─── 子进程截图函数 ───────────────────────────────────────────────
SCREENSHOT_SCRIPT = """
import asyncio, json, base64, sys, websockets

async def do(ws_url, out_path):
    async with websockets.connect(ws_url, max_size=100*1024*1024, open_timeout=8) as ws:
        _id = [0]
        async def send(method, params=None):
            _id[0] += 1
            msg = {"id": _id[0], "method": method, "params": params or {}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=15)
                d = json.loads(raw)
                if d.get("id") == _id[0]:
                    return d.get("result", {})
        await send("Page.enable")
        r = await send("Page.captureScreenshot", {"format": "png"})
        if "data" in r:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(r["data"]))
            print(f"OK:{out_path}", flush=True)
        r2 = await send("Runtime.evaluate", {
            "expression": "JSON.stringify({url:location.href,title:document.title,text:document.body?document.body.innerText.substring(0,2000):''})",
            "returnByValue": True
        })
        val = r2.get("result",{}).get("value","{}")
        print(f"CONTENT:{val}", flush=True)

asyncio.run(do(sys.argv[1], sys.argv[2]))
"""

def screenshot_in_subprocess(ws_url, out_path, timeout=20):
    """在子进程中截图，完全隔离连接"""
    result = subprocess.run(
        [sys.executable, '-c', SCREENSHOT_SCRIPT, ws_url, out_path],
        capture_output=True, text=True, timeout=timeout
    )
    content = {}
    for line in result.stdout.splitlines():
        if line.startswith("OK:"):
            log(f"  ✅ {os.path.basename(out_path)} ({os.path.getsize(out_path)//1024}KB)")
        elif line.startswith("CONTENT:"):
            try:
                content = json.loads(line[8:])
            except:
                pass
    if result.returncode != 0:
        log(f"  ❌ 子进程错误: {result.stderr[:100]}")
    return content

# ─── CDP点击（也用子进程，避免残留连接）────────────────────────────
CLICK_SCRIPT = """
import asyncio, json, sys, websockets

async def do(ws_url, actions):
    async with websockets.connect(ws_url, max_size=5*1024*1024, open_timeout=5) as ws:
        _id = [0]
        async def send(method, params=None):
            _id[0] += 1
            msg = {"id": _id[0], "method": method, "params": params or {}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=8)
                d = json.loads(raw)
                if d.get("id") == _id[0]:
                    return d.get("result", {})
        for act in actions:
            if act[0] == "click":
                _, x, y = act
                await send("Input.dispatchMouseEvent", {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
                await send("Input.dispatchMouseEvent", {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})
            elif act[0] == "esc":
                await send("Input.dispatchKeyEvent", {"type":"keyDown","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
                await send("Input.dispatchKeyEvent", {"type":"keyUp","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
            elif act[0] == "sleep":
                await asyncio.sleep(act[1])
        print("DONE", flush=True)

actions = json.loads(sys.argv[2])
asyncio.run(do(sys.argv[1], actions))
"""

def do_actions(ws_url, actions, timeout=15):
    result = subprocess.run(
        [sys.executable, '-c', CLICK_SCRIPT, ws_url, json.dumps(actions)],
        capture_output=True, text=True, timeout=timeout
    )
    return "DONE" in result.stdout

def main():
    subprocess.run(['osascript', '-e', 'tell application "品高聆客" to activate'], timeout=3)
    time.sleep(1)

    targets = get_targets()
    home = next((t for t in targets if t.get("type") == "page" and 'home' in t.get('url','').lower()), None)
    if not home:
        log("❌ 找不到home target"); return
    home_ws = home["webSocketDebuggerUrl"]
    initial_ids = {t['id'] for t in targets}
    log(f"home: {home['id'][:8]}, 初始targets: {len(targets)}")

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

        # 点击操作：应用tab -> ESC -> 应用图标
        ok = do_actions(home_ws, [
            ["click", 720, 21],
            ["sleep", 1.2],
            ["esc"],
            ["sleep", 0.4],
            ["click", ax, ay]
        ])
        if not ok:
            log(f"  ❌ 点击失败，跳过")
            continue
        log(f"  已点击 ({ax},{ay})")

        # 轮询检测（0.3秒×50次=15秒）
        found_ws = None
        found_type = None
        for attempt in range(50):
            time.sleep(0.3)
            after = get_targets()

            # 新target
            new_ts = [t for t in after if t['id'] not in before_ids
                      and t.get('type') in ('page','webview')
                      and t.get('webSocketDebuggerUrl')]
            if new_ts:
                found_ws = new_ts[-1]["webSocketDebuggerUrl"]
                found_type = f"新窗口:{new_ts[-1].get('title','')[:20]!r}"
                log(f"  检测到{found_type}")
                time.sleep(3)  # 等加载
                break

            # title或url变化
            for t in after:
                if t['id'] in before_info and t.get('webSocketDebuggerUrl'):
                    old_title, old_url = before_info[t['id']]
                    new_title = t.get('title','')
                    new_url = t.get('url','')
                    if (new_title and new_title != old_title) or (new_url and new_url != old_url):
                        found_ws = t["webSocketDebuggerUrl"]
                        found_type = f"变化:{old_title!r}->{new_title!r}"
                        log(f"  检测到{found_type}")
                        time.sleep(1.5)
                        break
            if found_ws:
                break

        if not found_ws:
            log(f"  ⚠️ 未检测到变化，截图主窗口")
            # 点击应用打开了home.html内的视图 -> 截图home.html
            time.sleep(1)
            out = f"{SCREENSHOT_DIR}/{safe}_01.png"
            content = screenshot_in_subprocess(home_ws, out)
            if content:
                log(f"  标题: {content.get('title','?')}")
                with open(f"{SCREENSHOT_DIR}/{safe}_content.json","w",encoding="utf-8") as f:
                    json.dump({"app":app_name,"type":"home_window",**content},f,ensure_ascii=False,indent=2)
        else:
            out = f"{SCREENSHOT_DIR}/{safe}_01.png"
            content = screenshot_in_subprocess(found_ws, out)
            log(f"  URL: {content.get('url','?')[:80]}")
            log(f"  内容: {content.get('text','')[:150]}")
            with open(f"{SCREENSHOT_DIR}/{safe}_content.json","w",encoding="utf-8") as f:
                json.dump({"app":app_name,"type":found_type,**content},f,ensure_ascii=False,indent=2)

        # 关闭新窗口
        time.sleep(0.5)
        after = get_targets()
        for t in after:
            if t['id'] not in initial_ids:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}", timeout=3)
                    log(f"  已关闭: {t.get('title','')!r}")
                except: pass
        time.sleep(0.5)

    log("\n✅ 全部完成！")
    log(f"📁 {SCREENSHOT_DIR}")

main()
