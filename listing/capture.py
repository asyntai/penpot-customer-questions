"""Real captures of the plugin in a local Penpot, for the Penpot Hub listing.

Needs: the local Penpot on :9001, and `FIXTURE=demo-sessions.json python
test/serve.py --mock` on :4400 (a made-up outdoor shop, no real chats).
Headless, so nothing on the desktop moves.
"""
import asyncio, json, os, re
from playwright.async_api import async_playwright

BASE = 'http://localhost:9001'
HERE = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join(os.path.dirname(HERE), 'test')
RAW = os.path.join(HERE, 'raw')
RPC = """async ([name, params]) => {
  const r = await fetch('/api/rpc/command/' + name, {method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, body: JSON.stringify(params)});
  return {status: r.status, body: await r.text()};
}"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--host-resolver-rules=MAP localhost 127.0.0.1'])
        ctx = await browser.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=2,
                                        storage_state=os.path.join(TEST, '.penpot_state.json'))
        page = await ctx.new_page()
        await page.goto(BASE + '/#/dashboard/recent')
        await page.wait_for_timeout(3000)
        me = json.loads((await page.evaluate(RPC, ['get-profile', {}]))['body'])
        made = json.loads((await page.evaluate(RPC, ['create-file', {'projectId': me['defaultProjectId'], 'name': 'FAQ page research'}]))['body'])
        await page.goto(BASE + '/#/workspace?team-id=%s&file-id=%s&page-id=%s' % (me['defaultTeamId'], made['id'], made['data']['pages'][0]))
        await page.wait_for_timeout(8000)

        await page.keyboard.press('Control+Alt+P')
        await page.wait_for_timeout(1500)
        await page.get_by_role('button', name=re.compile('^open$', re.I)).first.click()
        await page.wait_for_timeout(2500)
        fr = [x for x in page.frames if '4400' in x.url][0]
        await page.screenshot(path=os.path.join(RAW, 'a_connect.png'))
        await fr.fill('#key', 'demo-key')
        await fr.click('#connect-btn')
        await fr.wait_for_selector('#main:not(.hidden)')
        await fr.select_option('#site', '101')
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(RAW, 'b_main.png'))
        await fr.click('#add-btn')
        await fr.wait_for_function("document.getElementById('main-msg').textContent.indexOf('on the canvas') !== -1", timeout=20000)
        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(RAW, 'c_added.png'))
        await page.mouse.click(1303, 70)
        await page.wait_for_timeout(800)
        await page.keyboard.press('Escape')
        await page.keyboard.press('Shift+1')
        await page.wait_for_timeout(2500)
        await page.screenshot(path=os.path.join(RAW, 'd_canvas.png'))
        # A close look at the first row: zoom in with the keyboard around the top left.
        for _ in range(3):
            await page.keyboard.press('Shift+0') if False else None
        await page.mouse.move(700, 300)
        for _ in range(4):
            await page.keyboard.down('Control'); await page.mouse.wheel(0, -300); await page.keyboard.up('Control')
            await page.wait_for_timeout(300)
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(RAW, 'e_close.png'))
        await browser.close()

asyncio.run(main())
