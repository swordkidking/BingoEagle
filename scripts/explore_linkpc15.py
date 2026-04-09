"""
Phase 15: 最终正确策略
1. 用osascript模拟真实鼠标点击（不占用CDP连接）
2. 每次点击后等待新CDP target出现
3. 对已存在的webview（BingoERP等），先点击打开应用，立即通过CDP截图该webview

关键发现：
- 同一个webview不能同时建立两个CDP连接
- /json接口的url字段不实时更新
- 点击应用后BingoERP webview的title会变化（可以用title检测）
"""
import asyncio
import json
import base64
import os
import sys
import subprocess
import urllib.request
import websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots/apps3"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

_id = 0
def next_id():
    global _id; _id += 1; return _id

def log(msg):
    print(msg, flush=True)

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as resp:
        return json.loads(resp.read())

def click_at(x, y):
    """用AppleScript模拟鼠标点击（真实鼠标事件，绕过CDP连接限制）"""
    script = f'''
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        click at {{x, y}} of frontApp's window 1
    end tell
    '''
    # 直接用cliclick更可靠
    result = subprocess.run(['cliclick', f'c:{x},{y}'], capture_output=True, timeout=3)
    return result.returncode == 0

def has_cliclick():
    try:
        subprocess.run(['cliclick', '--version'], capture_output=True, timeout=2)
        return True
    except:
        return False

async def cdp_send(ws, method, params=None, timeout=15):
    global _id
    _id += 1
    msg = {"id": _id, "method": method, "params": params or {}}
    await ws.send(json.dumps(msg))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        data = json.loads(raw)
        if data.get("id") == msg["id"]:
            return data.get("result", {})

async def screenshot_and_content(ws_url, filename):
    """连接到target，截图并获取内容"""
    try:
        async with websockets.connect(ws_url, max_size=100*1024*1024, open_timeout=5) as ws:
            await cdp_send(ws, "Page.enable")
            await cdp_send(ws, "Runtime.enable")
            # 截图
            r = await cdp_send(ws, "Page.captureScreenshot", {"format": "png"})
            if "data" in r:
                path = f"{SCREENSHOT_DIR}/{filename}"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(r["data"]))
                size = os.path.getsize(path)
                log(f"  ✅ {filename} ({size//1024}KB)")
            # 获取内容
            r2 = await cdp_send(ws, "Runtime.evaluate", {
                "expression": "JSON.stringify({url: location.href, title: document.title, text: document.body ? document.body.innerText.substring(0,2000) : ''})",
                "returnByValue": True
            })
            val = r2.get("result", {}).get("value", "{}")
            return json.loads(val)
    except Exception as e:
        log(f"  ❌ {filename}: {e}")
        return {}

async def main():
    # 先激活品高聆客窗口
    subprocess.run(['osascript', '-e', 'tell application "品高聆客" to activate'], timeout=3)
    await asyncio.sleep(1)

    use_cliclick = has_cliclick()
    log(f"cliclick: {'可用' if use_cliclick else '不可用（将用CDP点击）'}")

    targets = get_targets()
    home = next((t for t in targets if t.get("type") == "page" and 'home' in t.get('url','').lower()), None)
    if not home:
        log("❌ 找不到home target")
        return

    home_ws_url = home["webSocketDebuggerUrl"]
    initial_ids = {t['id'] for t in targets}
    log(f"home target: {home['id'][:8]}")

    # 初始webview URL（通过titles检测变化）
    initial_titles = {t['id']: t.get('title','') for t in targets}

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
        log(f"\n{'='*50}")
        log(f"📱 {app_name}")

        before_targets = get_targets()
        before_ids = {t['id'] for t in before_targets}
        before_titles = {t['id']: t.get('title','') for t in before_targets}

        # 点击应用tab（用CDP，主窗口连接一下立刻断开）
        try:
            async with websockets.connect(home_ws_url, max_size=10*1024*1024, open_timeout=5) as ws:
                await cdp_send(ws, "Input.dispatchMouseEvent",
                    {"type":"mousePressed","x":720,"y":21,"button":"left","clickCount":1})
                await cdp_send(ws, "Input.dispatchMouseEvent",
                    {"type":"mouseReleased","x":720,"y":21,"button":"left","clickCount":1})
                await asyncio.sleep(1.2)
                # 关闭搜索框
                await cdp_send(ws, "Input.dispatchKeyEvent",
                    {"type":"keyDown","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
                await cdp_send(ws, "Input.dispatchKeyEvent",
                    {"type":"keyUp","key":"Escape","code":"Escape","windowsVirtualKeyCode":27})
                await asyncio.sleep(0.4)
                # 点击应用图标
                await cdp_send(ws, "Input.dispatchMouseEvent",
                    {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
                await cdp_send(ws, "Input.dispatchMouseEvent",
                    {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})
                log(f"  已点击 ({x},{y})")
        except Exception as e:
            log(f"  ❌ 点击失败: {e}")
            continue

        # 轮询检测：新target 或 title变化（每0.3秒，最多15秒）
        found_t = None
        found_type = None
        for attempt in range(50):
            await asyncio.sleep(0.3)
            after_targets = get_targets()

            # 新target
            new_ts = [t for t in after_targets
                      if t['id'] not in before_ids
                      and t.get('type') in ('page','webview')
                      and t.get('webSocketDebuggerUrl')]
            if new_ts:
                found_t = new_ts[-1]
                found_type = 'new'
                log(f"  新窗口: [{found_t['type']}] {found_t.get('title','')!r}")
                break

            # title变化（webview title反映当前页面）
            for t in after_targets:
                if t['id'] in before_titles and t.get('webSocketDebuggerUrl'):
                    new_title = t.get('title','')
                    old_title = before_titles[t['id']]
                    # title变化且不是空/不是已知固定title
                    if new_title and new_title != old_title and new_title not in ('BingoERP','项目管理系统','待处理事项'):
                        found_t = t
                        found_type = 'title_change'
                        log(f"  title变化: {old_title!r} -> {new_title!r}")
                        break
                    # URL变化（/json有时会更新）
                    new_url = t.get('url','')
                    old_url = next((tt.get('url','') for tt in before_targets if tt['id'] == t['id']), '')
                    if new_url and new_url != old_url:
                        found_t = t
                        found_type = 'url_change'
                        log(f"  URL变化: {old_url[:50]} -> {new_url[:50]}")
                        break
            if found_t:
                break

        if found_t:
            wait = 3 if found_type == 'new' else 1.5
            await asyncio.sleep(wait)
            content = await screenshot_and_content(found_t["webSocketDebuggerUrl"], f"{safe}_01.png")
            log(f"  URL: {content.get('url','?')[:80]}")
            log(f"  标题: {content.get('title','?')}")
            log(f"  内容: {content.get('text','')[:150]}")
            with open(f"{SCREENSHOT_DIR}/{safe}_content.json","w",encoding="utf-8") as f:
                json.dump({"app":app_name,"type":found_type,**content}, f, ensure_ascii=False, indent=2)
        else:
            log(f"  ⚠️ 15秒未检测到变化")
            # 截图所有webview当前状态（每个单独连接）
            after_targets = get_targets()
            for i, t in enumerate(after_targets):
                if t.get('type') == 'webview' and t.get('webSocketDebuggerUrl'):
                    tname = t.get('title','')[:12].replace('/','_').replace(' ','_')
                    content = await screenshot_and_content(t["webSocketDebuggerUrl"], f"{safe}_wv{i}_{tname}.png")
                    log(f"    [{tname}] url={content.get('url','?')[:60]}")

        # 关闭新开的窗口
        await asyncio.sleep(0.5)
        after = get_targets()
        for t in after:
            if t['id'] not in initial_ids:
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}", timeout=3)
                    log(f"  已关闭: {t.get('title','')!r}")
                except:
                    pass
        await asyncio.sleep(0.5)

    log("\n✅ 全部完成！")

asyncio.run(main())
