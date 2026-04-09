"""
Deep explore all 3 windows of 品高聆客:
1. home.html - main shell
2. projectcollaboration webview - 项目管理系统
3. AI agent webview - 智能体/AI助手
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
        r = await send(ws, "Page.captureScreenshot", {"format": "png", "quality": 90})
        if "data" in r:
            path = f"{SCREENSHOT_DIR}/{filename}"
            with open(path, "wb") as f:
                f.write(base64.b64decode(r["data"]))
            size = os.path.getsize(path)
            print(f"  ✅ {filename} ({size//1024}KB)")
            return path
    except Exception as e:
        print(f"  ❌ screenshot {filename}: {e}")
    return None

async def js(ws, expr, timeout=20):
    try:
        r = await send(ws, "Runtime.evaluate", {
            "expression": expr, "returnByValue": True, "awaitPromise": True
        }, timeout=timeout)
        return r.get("result", {}).get("value")
    except Exception as e:
        print(f"  JS error: {e}")
        return None

async def explore_window(target, prefix):
    ws_url = target["webSocketDebuggerUrl"]
    title = target.get("title", "")
    url = target.get("url", "")
    print(f"\n{'='*60}")
    print(f"🪟 Exploring: {title!r}")
    print(f"   URL: {url}")

    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # Screenshot
        await screenshot(ws, f"{prefix}_00_initial.png")

        # Full page text
        text = await js(ws, "document.body ? document.body.innerText.substring(0, 8000) : ''")
        print(f"\n📄 Text:\n{text}")

        # Get detailed UI structure
        struct = await js(ws, """
            (() => {
                const r = {nav:[], tabs:[], buttons:[], panels:[], inputs:[], headings:[], allItems:[]};

                // Headings
                for (const el of document.querySelectorAll('h1,h2,h3,h4,h5')) {
                    const t = el.textContent.trim();
                    if (t) r.headings.push({tag: el.tagName, text: t});
                }

                // Nav / tabs / sidebar
                for (const el of document.querySelectorAll(
                    'nav *,aside *,.sidebar *,[class*="sidebar"] *,[class*="nav"] *,.menu *,[class*="menu"] *,'+
                    '[role="tab"],[role="menuitem"],[role="navigation"] *'
                )) {
                    const t = el.textContent.trim();
                    if (t && t.length < 60 && el.children.length <= 1) {
                        r.nav.push(t);
                    }
                }

                // Buttons
                for (const el of document.querySelectorAll('button,[role="button"],.btn,[class*="btn"]')) {
                    const t = el.textContent.trim();
                    if (t && t.length < 60) r.buttons.push(t);
                }

                // Inputs
                for (const el of document.querySelectorAll('input,select,textarea')) {
                    r.inputs.push({type:el.type||el.tagName, placeholder:el.placeholder, id:el.id, name:el.name});
                }

                // All clickable items with positions
                for (const el of document.querySelectorAll(
                    'button,[role="button"],[role="tab"],a,li[class],[class*="item"],[class*="nav"],[class*="menu"]'
                )) {
                    const rect = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 80 && rect.width > 5 && rect.height > 5) {
                        r.allItems.push({
                            text: t, tag: el.tagName,
                            x: Math.round(rect.x + rect.width/2),
                            y: Math.round(rect.y + rect.height/2),
                            w: Math.round(rect.width), h: Math.round(rect.height),
                            cls: el.className.substring(0, 80)
                        });
                    }
                }

                // Deduplicate
                r.nav = [...new Set(r.nav)];
                r.buttons = [...new Set(r.buttons)];
                r.allItems = r.allItems.filter((v,i,a) => i === a.findIndex(x => x.text === v.text));
                return r;
            })()
        """)

        if struct:
            print(f"\n📋 Nav ({len(struct.get('nav',[]))}): {struct.get('nav',[][:30])}")
            print(f"🔘 Buttons ({len(struct.get('buttons',[]))}): {struct.get('buttons',[])[:30]}")
            print(f"📝 Headings: {struct.get('headings',[])[:20]}")
            print(f"✏️ Inputs: {struct.get('inputs',[])[:10]}")
            print(f"🎯 All clickable ({len(struct.get('allItems',[]))})")
            for item in struct.get('allItems', [])[:50]:
                print(f"   [{item['x']},{item['y']}] '{item['text'][:40]}' cls={item['cls'][:40]}")

        # Save
        with open(f"{SCREENSHOT_DIR}/{prefix}_structure.json", "w", encoding="utf-8") as f:
            json.dump({"title": title, "url": url, "text": text, "struct": struct}, f, ensure_ascii=False, indent=2)

        # Click through navigation items
        if struct and struct.get('allItems'):
            items = struct['allItems']
            # Focus on left-side items (sidebar/nav)
            left_items = [it for it in items if it.get('x', 999) < 300]
            top_items  = [it for it in items if it.get('y', 999) < 60]
            all_nav    = left_items + [it for it in top_items if it not in left_items]

            print(f"\n🖱️ Clicking {len(all_nav[:20])} nav items...")
            for i, item in enumerate(all_nav[:20]):
                try:
                    print(f"  [{i}] '{item['text'][:30]}' @ ({item['x']},{item['y']})")
                    await send(ws, "Input.dispatchMouseEvent", {
                        "type": "mousePressed", "x": item['x'], "y": item['y'],
                        "button": "left", "clickCount": 1
                    })
                    await send(ws, "Input.dispatchMouseEvent", {
                        "type": "mouseReleased", "x": item['x'], "y": item['y'],
                        "button": "left", "clickCount": 1
                    })
                    await asyncio.sleep(2.5)
                    safe_name = item['text'][:20].replace('/', '_').replace(' ', '_').replace('\n', '')
                    await screenshot(ws, f"{prefix}_{i+1:02d}_{safe_name}.png")
                except Exception as e:
                    print(f"  Error clicking: {e}")

async def main():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())

    print(f"Found {len(targets)} targets:")
    for i, t in enumerate(targets):
        print(f"  [{i}] {t.get('type')} | {t.get('title')!r} | {t.get('url','')[:80]}")

    # Explore each target
    for i, target in enumerate(targets):
        prefix = f"win{i}"
        await explore_window(target, prefix)

    print("\n✅ All windows explored!")
    print(f"📁 Screenshots: {SCREENSHOT_DIR}")

asyncio.run(main())
