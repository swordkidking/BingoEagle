"""
Phase 13: 关键改进 - 点击应用后立即（不等待）截图BingoERP webview
同时也检测新窗口。

发现：大多数应用都在BingoERP webview里打开，但脚本等太久导致页面已经跳走。
解决：检测到URL变化后立即截图，不sleep。
"""
import asyncio
import json
import base64
import os
import urllib.request
import websockets

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots/apps3"
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

async def screenshot_ws(ws, filename):
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

async def js(ws, expr, timeout=10):
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

# 找到可截图的webview targets（有webSocketDebuggerUrl的）
def get_screenshottable_targets():
    targets = get_targets()
    return [t for t in targets if t.get('webSocketDebuggerUrl') and t.get('type') in ('page','webview')]

async def main():
    initial_targets = get_targets()
    initial_ids = {t['id'] for t in initial_targets}
    home = next((t for t in initial_targets if t.get("type") == "page" and 'home' in t.get('url','').lower()), None)

    # 找到BingoERP webview
    erp_target = next((t for t in initial_targets if 'erp.bingosoft.net' in t.get('url','')), None)
    # 找到项目管理 webview
    proj_target = next((t for t in initial_targets if 'projectcollaboration' in t.get('url','')), None)

    print(f"主窗口: {home.get('title')}")
    print(f"BingoERP: {erp_target.get('url','')[:60] if erp_target else 'None'}")
    print(f"项目管理: {proj_target.get('url','')[:60] if proj_target else 'None'}")

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

    async with websockets.connect(home["webSocketDebuggerUrl"], max_size=100*1024*1024) as main_ws:
        await send(main_ws, "Page.enable")
        await send(main_ws, "Runtime.enable")

        # 同时保持BingoERP的连接
        erp_ws_conn = None

        for app_name, x, y in apps:
            safe = app_name.replace('/','_').replace(' ','_')
            print(f"\n{'='*50}")
            print(f"📱 {app_name}")

            # 记录当前状态
            before_targets = get_targets()
            before_ids = {t['id'] for t in before_targets}
            before_erp_url = erp_target.get('url','') if erp_target else ''

            # 先刷新erp_target的当前URL（从CDP获取）
            if erp_target:
                try:
                    async with websockets.connect(erp_target["webSocketDebuggerUrl"], max_size=50*1024*1024) as ews:
                        cur_url = await js(ews, "location.href", timeout=5)
                        before_erp_url = cur_url or before_erp_url
                except:
                    pass

            # 点击应用tab，关闭搜索框，点击应用
            await click(main_ws, 720, 21)
            await asyncio.sleep(1.5)
            await press_esc(main_ws)
            await asyncio.sleep(0.5)
            await click(main_ws, x, y)

            # 快速轮询检测变化（每0.3秒，最多15秒）
            found = None
            found_type = None
            for attempt in range(50):
                await asyncio.sleep(0.3)
                after_targets = get_targets()

                # 检查新target
                new_page_targets = [t for t in after_targets
                                   if t['id'] not in before_ids
                                   and t.get('type') in ('page','webview')
                                   and t.get('webSocketDebuggerUrl')]
                if new_page_targets:
                    found = new_page_targets[-1]
                    found_type = 'new_target'
                    print(f"  新窗口: [{found['type']}] {found.get('title','')!r}")
                    break

                # 检查BingoERP URL变化
                if erp_target:
                    cur_erp = next((t for t in after_targets if t['id'] == erp_target['id']), None)
                    if cur_erp:
                        new_url = cur_erp.get('url','')
                        if new_url != before_erp_url and new_url and 'BingoERP/Home/Index' not in new_url:
                            found = cur_erp
                            found_type = 'erp_url_change'
                            print(f"  BingoERP URL变化: {new_url[:80]}")
                            break

                # 检查项目管理 URL变化
                if proj_target:
                    cur_proj = next((t for t in after_targets if t['id'] == proj_target['id']), None)
                    if cur_proj:
                        new_url = cur_proj.get('url','')
                        if new_url != proj_target.get('url','') and new_url:
                            found = cur_proj
                            found_type = 'proj_url_change'
                            print(f"  项目管理 URL变化: {new_url[:80]}")
                            break

            if not found:
                # fallback：截图当前所有changed webviews
                print(f"  ⚠️ 未检测到变化，截图所有webview")
                after_targets = get_targets()
                for t in after_targets:
                    if t.get('type') == 'webview' and t.get('webSocketDebuggerUrl'):
                        tname = t.get('title','unknown')[:20]
                        try:
                            async with websockets.connect(t["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws2:
                                await send(ws2, "Page.enable")
                                cur_url = await js(ws2, "location.href", timeout=5)
                                print(f"    webview URL: {cur_url[:80] if cur_url else '?'}")
                                await screenshot_ws(ws2, f"{safe}_fallback_{tname}.png")
                        except Exception as e:
                            print(f"    ❌ {e}")
                continue

            # 立即截图（不等待）
            if found_type == 'new_target':
                await asyncio.sleep(4)  # 新窗口需要等加载
                try:
                    async with websockets.connect(found["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws2:
                        await send(ws2, "Page.enable")
                        await send(ws2, "Runtime.enable")
                        await screenshot_ws(ws2, f"{safe}_01.png")
                        text = await js(ws2, "document.body ? document.body.innerText.substring(0,2000) : ''")
                        print(f"  内容: {text[:200] if text else '(空)'}")
                        with open(f"{SCREENSHOT_DIR}/{safe}_content.json","w",encoding="utf-8") as f:
                            json.dump({"app":app_name,"type":found_type,"url":found.get("url",""),"text":text},f,ensure_ascii=False,indent=2)
                except Exception as e:
                    print(f"  ❌ {e}")
            else:
                # BingoERP/项目管理 URL变化 - 立即截图
                await asyncio.sleep(1.5)  # 短暂等待渲染
                try:
                    async with websockets.connect(found["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws2:
                        await send(ws2, "Page.enable")
                        await send(ws2, "Runtime.enable")
                        await screenshot_ws(ws2, f"{safe}_01.png")
                        text = await js(ws2, "document.body ? document.body.innerText.substring(0,2000) : ''")
                        cur_url = await js(ws2, "location.href", timeout=5)
                        print(f"  URL: {cur_url[:80] if cur_url else '?'}")
                        print(f"  内容: {text[:200] if text else '(空)'}")
                        with open(f"{SCREENSHOT_DIR}/{safe}_content.json","w",encoding="utf-8") as f:
                            json.dump({"app":app_name,"type":found_type,"url":cur_url or found.get("url",""),"text":text},f,ensure_ascii=False,indent=2)
                except Exception as e:
                    print(f"  ❌ {e}")

            # 关闭新开的窗口
            await asyncio.sleep(0.5)
            after = get_targets()
            for t in after:
                if t['id'] not in initial_ids:
                    try:
                        urllib.request.urlopen(f"http://127.0.0.1:9222/json/close/{t['id']}")
                        print(f"  关闭: {t.get('title','')!r}")
                    except:
                        pass
            await asyncio.sleep(0.5)

    print("\n✅ 全部完成！")
    print(f"📁 截图目录: {SCREENSHOT_DIR}")

asyncio.run(main())
