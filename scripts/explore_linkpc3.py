"""
Use raw CDP WebSocket to explore 品高聆客
Playwright connect_over_cdp fails for Electron 21 (Chrome 106)
So we use websockets + CDP directly for screenshots and DOM inspection
"""
import asyncio
import json
import base64
import os
import websockets
import urllib.request

SCREENSHOT_DIR = "/Users/mac/Documents/ClaudeWork/BingoEagle/需求/linkpc_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ── CDP helpers ──────────────────────────────────────────────────────────
_id = 0
def next_id():
    global _id; _id += 1; return _id

async def send(ws, method, params=None):
    msg = {"id": next_id(), "method": method, "params": params or {}}
    await ws.send(json.dumps(msg))
    # Read until we get the response for this id
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=15)
        data = json.loads(raw)
        if data.get("id") == msg["id"]:
            return data.get("result", {})

async def screenshot(ws, filename):
    r = await send(ws, "Page.captureScreenshot", {"format": "png"})
    if "data" in r:
        path = f"{SCREENSHOT_DIR}/{filename}"
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        print(f"  ✅ {filename}")
        return path
    print(f"  ❌ screenshot failed: {r}")
    return None

async def eval_js(ws, expr):
    r = await send(ws, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    return r.get("result", {}).get("value")

async def main():
    # Get all pages/targets
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())
    print(f"Targets ({len(targets)}):")
    for t in targets:
        print(f"  type={t.get('type')} title={t.get('title')!r} url={t.get('url')!r}")

    # Find the main page target
    main_target = None
    for t in targets:
        if t.get("type") == "page" and "devtools" not in t.get("url",""):
            main_target = t
            break
    if not main_target:
        main_target = targets[0]

    ws_url = main_target["webSocketDebuggerUrl"]
    print(f"\nConnecting to: {ws_url}")

    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # Enable necessary domains
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")
        await send(ws, "DOM.enable")

        # Get page info
        title = await eval_js(ws, "document.title")
        url   = await eval_js(ws, "location.href")
        print(f"\n📱 Page: {title!r}  {url!r}")

        # Initial screenshot
        await screenshot(ws, "00_initial.png")

        # Get page text
        body_text = await eval_js(ws, "document.body.innerText.substring(0, 5000)")
        print(f"\n📄 Page text:\n{body_text}")

        # Detailed structure analysis
        structure = await eval_js(ws, """
            (() => {
                const result = {
                    title: document.title,
                    url: location.href,
                    nav: [],
                    buttons: [],
                    inputs: [],
                    images: [],
                    allText: []
                };

                // Navigation/sidebar items
                const navSels = ['nav','aside','.sidebar','.left-panel','[class*="sidebar"]',
                                 '[class*="nav"]','[class*="menu"]','[class*="left"]'];
                for (const sel of navSels) {
                    const container = document.querySelector(sel);
                    if (container) {
                        for (const el of container.querySelectorAll('*')) {
                            const t = el.textContent.trim();
                            if (t && t.length < 50 && el.children.length === 0) {
                                result.nav.push(t);
                            }
                        }
                    }
                }

                // All buttons
                for (const el of document.querySelectorAll('button,[role="button"],[role="tab"],.btn')) {
                    const t = el.textContent.trim();
                    if (t && t.length < 60) result.buttons.push(t);
                }

                // Inputs
                for (const el of document.querySelectorAll('input,textarea,select')) {
                    result.inputs.push({
                        type: el.type || el.tagName.toLowerCase(),
                        placeholder: el.placeholder,
                        name: el.name,
                        id: el.id
                    });
                }

                // All visible text nodes (headings, labels)
                for (const el of document.querySelectorAll('h1,h2,h3,h4,label,span[class],div[class],p')) {
                    const t = el.textContent.trim();
                    if (t && t.length < 100 && el.children.length <= 1) {
                        result.allText.push({tag: el.tagName, text: t, cls: el.className.substring(0,50)});
                    }
                }

                // Deduplicate
                result.nav = [...new Set(result.nav)];
                result.buttons = [...new Set(result.buttons)];
                result.allText = result.allText.filter((v,i,a) =>
                    i === a.findIndex(t => t.text === v.text));

                return result;
            })()
        """)

        print(f"\n📋 Nav items ({len(structure.get('nav',[]))}):")
        for item in structure.get('nav', []):
            print(f"   • {item}")

        print(f"\n🔘 Buttons ({len(structure.get('buttons',[]))}):")
        for b in structure.get('buttons', [])[:40]:
            print(f"   • {b}")

        print(f"\n✏️ Inputs ({len(structure.get('inputs',[]))}):")
        for inp in structure.get('inputs', []):
            print(f"   • {inp}")

        print(f"\n📝 All text labels ({len(structure.get('allText',[]))}):")
        for item in structure.get('allText', [])[:60]:
            print(f"   [{item['tag']}] {item['text']}")

        # Get all clickable elements with positions
        clickables = await eval_js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll(
                    'button,[role="button"],[role="tab"],a,li[class],[class*="item"],[class*="nav"],[class*="menu"]'
                )) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 60 && r.width > 5 && r.height > 5 && r.x >= 0) {
                        items.push({
                            text: t, tag: el.tagName,
                            x: Math.round(r.x + r.width/2),
                            y: Math.round(r.y + r.height/2),
                            w: Math.round(r.width), h: Math.round(r.height),
                            cls: el.className.substring(0,60)
                        });
                    }
                }
                const seen = new Set();
                return items.filter(i => {
                    if (seen.has(i.text)) return false;
                    seen.add(i.text); return true;
                });
            })()
        """)

        print(f"\n🎯 Clickable elements ({len(clickables)}):")
        for el in clickables:
            print(f"   [{el['x']},{el['y']}] {el['tag']} '{el['text']}' cls={el['cls'][:30]}")

        # Save data
        with open(f"{SCREENSHOT_DIR}/app_structure.json", "w", encoding="utf-8") as f:
            json.dump({
                "structure": structure,
                "clickables": clickables,
                "body_text": body_text
            }, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved to app_structure.json")

        # Now click through sidebar items
        print("\n🖱️ Clicking through navigation items...")
        left_items = [el for el in clickables if el.get('x', 999) < 250]
        print(f"   Left sidebar items: {len(left_items)}")

        for i, item in enumerate(left_items[:20]):
            try:
                print(f"\n   [{i}] Clicking '{item['text']}' at ({item['x']},{item['y']})")
                await send(ws, "Input.dispatchMouseEvent", {
                    "type": "mousePressed", "x": item['x'], "y": item['y'],
                    "button": "left", "clickCount": 1
                })
                await send(ws, "Input.dispatchMouseEvent", {
                    "type": "mouseReleased", "x": item['x'], "y": item['y'],
                    "button": "left", "clickCount": 1
                })
                await asyncio.sleep(2)
                fname = f"nav_{i:02d}_{item['text'][:20].replace('/', '_').replace(' ', '_')}.png"
                await screenshot(ws, fname)
            except Exception as e:
                print(f"   Error: {e}")

    print("\n✅ Done!")

asyncio.run(main())
