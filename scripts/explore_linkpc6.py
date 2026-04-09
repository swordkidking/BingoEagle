"""
Deep explore 品高聆客 - Phase 6
Goals:
1. Explore 应用 tab - find all apps/modules
2. Explore AI assistant webview (localhost:12258) - 配置/会话/专家/创作
3. Explore 项目管理 webview - 待办/待阅/已办 + more
4. Use macOS screencapture for webview windows
5. Capture more screenshots of all features
"""
import asyncio
import json
import base64
import os
import subprocess
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
    except Exception as e:
        return None

async def click(ws, x, y):
    await send(ws, "Input.dispatchMouseEvent", {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
    await send(ws, "Input.dispatchMouseEvent", {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})

def mac_screenshot(filename, delay=0.5):
    """Use macOS screencapture to capture the entire screen"""
    path = f"{SCREENSHOT_DIR}/{filename}"
    subprocess.run(["screencapture", "-x", path], check=True)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    print(f"  📸 macOS screencapture: {filename} ({size//1024}KB)")
    return path

async def explore_apps_tab(ws):
    """Fully explore the 应用 tab - find all apps"""
    print("\n" + "="*60)
    print("🔍 Exploring 应用 Tab")

    # Click 应用 tab
    await click(ws, 100, 23)
    await asyncio.sleep(3)
    await screenshot(ws, "apps_01_initial.png")

    # Get all apps with positions
    apps = await js(ws, """
        (() => {
            const items = [];
            // Try various selectors for app grid items
            const sels = [
                '[class*="app"]', '[class*="App"]',
                '[class*="grid"]', '[class*="icon"]',
                '[class*="launch"]', '[class*="module"]',
                '.app-item', '.app-icon', '.app-list li',
                '[class*="entry"]', '[class*="portal"]'
            ];
            for (const sel of sels) {
                for (const el of document.querySelectorAll(sel)) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 30 && r.width > 20 && r.height > 20 && r.x > 100) {
                        items.push({
                            text: t,
                            x: Math.round(r.x + r.width/2),
                            y: Math.round(r.y + r.height/2),
                            w: Math.round(r.width), h: Math.round(r.height),
                            cls: el.className.substring(0,60)
                        });
                    }
                }
            }
            const seen = new Set();
            return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
        })()
    """)

    print(f"App items found: {len(apps) if apps else 0}")
    if apps:
        for a in apps:
            print(f"  [{a['x']},{a['y']}] {a['text']!r} cls={a['cls'][:40]}")

    # Also get all text in apps area (x > 100)
    all_text = await js(ws, """
        (() => {
            const items = [];
            for (const el of document.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                const t = el.textContent.trim();
                if (t && t.length < 40 && el.children.length === 0
                    && r.width > 5 && r.height > 5 && r.x > 100) {
                    items.push({text: t, x: Math.round(r.x), y: Math.round(r.y)});
                }
            }
            const seen = new Set();
            return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
        })()
    """)
    print(f"\nAll text in apps area ({len(all_text) if all_text else 0}):")
    if all_text:
        for t in all_text[:60]:
            print(f"  [{t['x']},{t['y']}] {t['text']!r}")

    # Get full page HTML structure
    html_snippet = await js(ws, """
        (() => {
            // Find the apps container
            const containers = document.querySelectorAll('[class*="app"],[class*="grid"],[class*="launch"]');
            let result = '';
            for (const c of containers) {
                if (c.getBoundingClientRect().width > 200) {
                    result += c.outerHTML.substring(0, 2000) + '\\n---\\n';
                }
            }
            return result.substring(0, 5000);
        })()
    """)
    print(f"\nHTML snippets:\n{html_snippet}")

    # Save app data
    with open(f"{SCREENSHOT_DIR}/apps_structure.json", "w", encoding="utf-8") as f:
        json.dump({"apps": apps, "all_text": all_text}, f, ensure_ascii=False, indent=2)

    # Try scrolling in apps area to find more
    await js(ws, """
        (() => {
            // Find scrollable container in apps area
            for (const el of document.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                if (r.x > 100 && el.scrollHeight > el.clientHeight + 50) {
                    el.scrollTop = 500;
                    return {found: true, cls: el.className, scroll: el.scrollHeight};
                }
            }
            return {found: false};
        })()
    """)
    await asyncio.sleep(1)
    await screenshot(ws, "apps_02_scrolled.png")

    # Scroll back
    await js(ws, """
        for (const el of document.querySelectorAll('*')) {
            if (el.getBoundingClientRect().x > 100 && el.scrollHeight > el.clientHeight + 50)
                el.scrollTop = 0;
        }
    """)

    return apps, all_text


async def explore_main_nav(ws):
    """Explore all main navigation areas in the shell"""
    print("\n" + "="*60)
    print("🔍 Exploring Main Navigation")

    # Get left nav structure
    nav_items = await js(ws, """
        (() => {
            const items = [];
            for (const el of document.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                const t = el.textContent.trim();
                if (t && t.length < 30 && el.children.length === 0
                    && r.x >= 0 && r.x < 130 && r.width > 5 && r.height > 5) {
                    items.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), cls: el.className.substring(0,50)});
                }
            }
            const seen = new Set();
            return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
        })()
    """)
    print(f"Left nav items: {len(nav_items) if nav_items else 0}")
    if nav_items:
        for n in nav_items:
            print(f"  [{n['x']},{n['y']}] {n['text']!r}")

    return nav_items


async def explore_ai_assistant():
    """Explore AI assistant webview via CDP"""
    print("\n" + "="*60)
    print("🤖 Exploring AI Assistant (localhost:12258)")

    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())

    ai_target = None
    for t in targets:
        if "12258" in t.get("url", "") or "agent" in t.get("url", ""):
            ai_target = t
            break

    if not ai_target:
        print("  ❌ AI assistant target not found")
        return

    print(f"  URL: {ai_target['url'][:80]}")

    async with websockets.connect(ai_target["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # Try screenshot
        await screenshot(ws, "ai_01_initial.png")

        # Get full text
        text = await js(ws, "document.body ? document.body.innerText.substring(0,5000) : ''")
        print(f"\nAI text:\n{text}")

        # Get nav items with positions
        nav = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('button,[role="button"],[class*="menu"],[class*="nav"]')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 40 && r.width > 5 && r.height > 5) {
                        items.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), cls: el.className.substring(0,50)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"\nAI nav ({len(nav) if nav else 0}):")
        if nav:
            for n in nav:
                print(f"  [{n['x']},{n['y']}] {n['text']!r} cls={n['cls'][:30]}")

        # Click through AI nav tabs
        ai_tabs = ["配置", "会话", "专家", "创作"]
        for tab_name in ai_tabs:
            if nav:
                target = next((n for n in nav if n['text'] == tab_name), None)
                if target:
                    print(f"\n  Clicking {tab_name}...")
                    await click(ws, target['x'], target['y'])
                    await asyncio.sleep(2.5)
                    await screenshot(ws, f"ai_{tab_name}.png")

                    # Get content
                    content = await js(ws, "document.body.innerText.substring(0,3000)")
                    print(f"  {tab_name} content:\n{content[:500]}")

        # Go back to 新建会话
        if nav:
            new_chat = next((n for n in nav if n['text'] == "新建会话"), None)
            if new_chat:
                await click(ws, new_chat['x'], new_chat['y'])
                await asyncio.sleep(1.5)
                await screenshot(ws, "ai_new_chat.png")

        # Get guide cards detail
        guides = await js(ws, """
            (() => {
                const cards = [];
                for (const el of document.querySelectorAll('[class*="guide"]')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && r.width > 50) cards.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                }
                return cards;
            })()
        """)
        print(f"\nGuide cards: {guides}")


async def explore_project_mgmt():
    """Explore project management webview"""
    print("\n" + "="*60)
    print("📋 Exploring Project Management Webview")

    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())

    proj_target = None
    for t in targets:
        if "bingosoft.net" in t.get("url", "") or "projectcollaboration" in t.get("url", ""):
            proj_target = t
            break

    if not proj_target:
        print("  ❌ Project management target not found")
        return

    print(f"  URL: {proj_target['url'][:80]}")

    async with websockets.connect(proj_target["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # Try screenshot (may fail for webview)
        await screenshot(ws, "proj_01_initial.png")

        # Get structure
        text = await js(ws, "document.body ? document.body.innerText.substring(0,5000) : ''")
        print(f"\nProject text:\n{text}")

        # Get nav
        nav = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('*')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 40 && el.children.length === 0
                        && r.width > 10 && r.height > 10 && r.x < 400) {
                        items.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), cls: el.className.substring(0,50)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"\nProject nav ({len(nav) if nav else 0}):")
        if nav:
            for n in nav:
                print(f"  [{n['x']},{n['y']}] {n['text']!r}")

        # Click 消息 tab in project view (top nav)
        if nav:
            msg_tab = next((n for n in nav if n['text'] == '消息'), None)
            if msg_tab:
                print(f"\n  Clicking 消息 tab...")
                await click(ws, msg_tab['x'], msg_tab['y'])
                await asyncio.sleep(2)
                await screenshot(ws, "proj_02_messages.png")
                content = await js(ws, "document.body.innerText.substring(0,2000)")
                print(f"  消息 content:\n{content[:300]}")

            # Click 待阅
            daiYue = next((n for n in nav if '待阅' in n['text']), None)
            if daiYue:
                print(f"\n  Clicking 待阅...")
                await click(ws, daiYue['x'], daiYue['y'])
                await asyncio.sleep(2)
                await screenshot(ws, "proj_03_daiYue.png")

            # Click 已办
            yiBan = next((n for n in nav if '已办' in n['text']), None)
            if yiBan:
                print(f"\n  Clicking 已办...")
                await click(ws, yiBan['x'], yiBan['y'])
                await asyncio.sleep(2)
                await screenshot(ws, "proj_04_yiBan.png")

        # Try to explore more features in project management
        all_btns = await js(ws, """
            (() => {
                const items = [];
                for (const el of document.querySelectorAll('button,[role="button"],a[href]')) {
                    const r = el.getBoundingClientRect();
                    const t = el.textContent.trim();
                    if (t && t.length < 40 && r.width > 5 && r.height > 5) {
                        items.push({text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                    }
                }
                const seen = new Set();
                return items.filter(i => {if(seen.has(i.text)) return false; seen.add(i.text); return true;});
            })()
        """)
        print(f"\nAll buttons ({len(all_btns) if all_btns else 0}):")
        if all_btns:
            for b in all_btns[:30]:
                print(f"  [{b['x']},{b['y']}] {b['text']!r}")


async def explore_more_main(ws):
    """Explore more features in main shell - profile, search, settings"""
    print("\n" + "="*60)
    print("⚙️ Exploring Profile / Settings / Search")

    # Right-click on profile/avatar area
    # First get all items in top-right area
    top_right = await js(ws, """
        (() => {
            const items = [];
            for (const el of document.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                const t = el.textContent.trim();
                if (r.x > 500 && r.y < 60 && r.width > 5 && r.height > 5) {
                    items.push({text: t.substring(0,30), x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), w: Math.round(r.width), h: Math.round(r.height), tag: el.tagName, cls: el.className.substring(0,50)});
                }
            }
            const seen = new Set();
            return items.filter(i => {if(seen.has(i.text+''+i.x+''+i.y)) return false; seen.add(i.text+''+i.x+''+i.y); return true;});
        })()
    """)
    print(f"Top-right items ({len(top_right) if top_right else 0}):")
    if top_right:
        for t in top_right[:20]:
            print(f"  [{t['x']},{t['y']}] {t['text']!r} tag={t['tag']} cls={t['cls'][:30]}")

    # Click each top-right item
    if top_right:
        for item in top_right[:10]:
            if item['x'] > 600:  # far right items
                print(f"\n  Clicking top-right: {item['text']!r} @ ({item['x']},{item['y']})")
                await click(ws, item['x'], item['y'])
                await asyncio.sleep(1.5)
                safe = item['text'][:15].replace('/','_').replace(' ','_').replace('\n','')
                await screenshot(ws, f"topright_{item['x']}_{safe}.png")
                # Close any popup
                await js(ws, "document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}))")
                await asyncio.sleep(0.5)


async def explore_message_conversation(ws):
    """Explore a message conversation in detail"""
    print("\n" + "="*60)
    print("💬 Exploring Message Conversations in Detail")

    # Go to 消息 tab
    await click(ws, 33, 23)
    await asyncio.sleep(1.5)

    # Get all conversation items
    convs = await js(ws, """
        (() => {
            const items = [];
            for (const el of document.querySelectorAll('[class*="session"],[class*="chat"],[class*="conv"],[class*="item"],[class*="list"] > *')) {
                const r = el.getBoundingClientRect();
                const t = el.textContent.trim();
                if (t && t.length > 2 && t.length < 100 && r.x > 5 && r.x < 250 && r.y > 50 && r.width > 50 && r.height > 20) {
                    items.push({text: t.substring(0,50), x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), cls: el.className.substring(0,50)});
                }
            }
            const seen = new Set();
            return items.filter(i => {if(seen.has(i.y)) return false; seen.add(i.y); return true;});
        })()
    """)
    print(f"Conversations ({len(convs) if convs else 0}):")
    if convs:
        for c in convs[:15]:
            print(f"  [{c['x']},{c['y']}] {c['text']!r}")

    # Click first few conversations and capture
    if convs:
        for i, conv in enumerate(convs[:5]):
            print(f"\n  Opening conversation {i}: {conv['text']!r}")
            await click(ws, conv['x'], conv['y'])
            await asyncio.sleep(2.5)
            safe = conv['text'][:15].replace('/','_').replace(' ','_').replace('\n','')
            await screenshot(ws, f"chat_{i:02d}_{safe}.png")

            # Get message input area and features
            chat_features = await js(ws, """
                (() => {
                    const items = [];
                    // Input area
                    for (const el of document.querySelectorAll('textarea,input[type="text"],[contenteditable]')) {
                        const r = el.getBoundingClientRect();
                        if (r.width > 100) items.push({type: 'input', placeholder: el.placeholder || el.getAttribute('data-placeholder') || '', x: Math.round(r.x), y: Math.round(r.y)});
                    }
                    // Toolbar buttons in chat area
                    for (const el of document.querySelectorAll('[class*="toolbar"] *,[class*="input-area"] *,[class*="chat-footer"] *')) {
                        const r = el.getBoundingClientRect();
                        const t = el.textContent.trim();
                        if (t && t.length < 30 && r.y > 400) items.push({type: 'button', text: t, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                    }
                    return items;
                })()
            """)
            print(f"  Chat features: {chat_features}")

    # Also try right-clicking a conversation
    if convs and len(convs) > 0:
        c = convs[0]
        await send(ws, "Input.dispatchMouseEvent", {"type":"mousePressed","x":c['x'],"y":c['y'],"button":"right","clickCount":1})
        await send(ws, "Input.dispatchMouseEvent", {"type":"mouseReleased","x":c['x'],"y":c['y'],"button":"right","clickCount":1})
        await asyncio.sleep(1.5)
        await screenshot(ws, "chat_context_menu.png")
        await js(ws, "document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}))")


async def main():
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
        targets = json.loads(resp.read())

    print(f"Found {len(targets)} targets:")
    for i, t in enumerate(targets):
        print(f"  [{i}] {t.get('type')} | {t.get('title')!r} | {t.get('url','')[:80]}")

    # Get main shell target
    home = next((t for t in targets if t.get("type") == "page"), None)
    if not home:
        print("No page target found!")
        return

    ws_url = home["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url, max_size=100*1024*1024) as ws:
        await send(ws, "Page.enable")
        await send(ws, "Runtime.enable")

        # 1. Explore main nav
        nav_items = await explore_main_nav(ws)

        # 2. Explore apps tab fully
        apps, all_text = await explore_apps_tab(ws)

        # 3. Explore top-right area (profile/settings)
        await explore_more_main(ws)

        # 4. Explore message conversations
        await explore_message_conversation(ws)

    # 5. Explore AI assistant (separate connection)
    await explore_ai_assistant()

    # 6. Explore project management (separate connection)
    await explore_project_mgmt()

    print("\n✅ Done! All features explored.")
    print(f"📁 Screenshots: {SCREENSHOT_DIR}")

asyncio.run(main())
