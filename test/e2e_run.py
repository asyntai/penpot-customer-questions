"""End to end in a real Penpot (local instance, headless browser).

Installs the plugin from http://localhost:4400/manifest.json, runs it, connects
with the mock key, adds the questions, then reads the canvas back through the
Penpot RPC API.
"""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright

BASE = 'http://localhost:9001'
MANIFEST = os.environ.get('MANIFEST', 'http://localhost:4400/manifest.json')
KEY = os.environ.get('TEST_KEY', 'demo-key')
HERE = os.path.dirname(__file__)
SHOTS = os.path.join(HERE, 'shots')
THEME = os.environ.get('THEME', '')

RPC = """async ([name, params]) => {
  const r = await fetch('/api/rpc/command/' + name, {
    method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
    body: JSON.stringify(params)});
  return {status: r.status, body: await r.text()};
}"""

async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOTS, name))
    print('shot', name)

async def plugin_frame(page):
    for _ in range(40):
        for fr in page.frames:
            if '4400' in fr.url or 'asyntai' in fr.url.lower():
                return fr
        await page.wait_for_timeout(500)
    raise RuntimeError('plugin frame not found: ' + ', '.join(f.url for f in page.frames))

async def main():
    f = json.load(open(os.path.join(HERE, '.penpot_file.json')))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--host-resolver-rules=MAP localhost 127.0.0.1'])
        ctx = await browser.new_context(viewport={'width': 1600, 'height': 1000},
                                        storage_state=os.path.join(HERE, '.penpot_state.json'))
        page = await ctx.new_page()
        errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
        await page.goto(BASE + '/#/workspace?team-id=%s&file-id=%s&page-id=%s' % (f['team'], f['file'], f['page']))
        await page.wait_for_timeout(7000)

        await page.keyboard.press('Control+Alt+P')
        await page.wait_for_timeout(1500)
        url_box = page.get_by_placeholder('Write a plugin URL')
        already = await page.get_by_text('Customer Questions by Asyntai').count()
        print('already installed:', bool(already))
        if not already and await url_box.count():
            await url_box.fill(MANIFEST)
            await page.get_by_role('button', name=re.compile('^install$', re.I)).first.click()
            await page.wait_for_timeout(2500)
            await shot(page, '05_after_install.png')
            allow = page.get_by_role('button', name=re.compile('^allow$', re.I))
            if await allow.count():
                await shot(page, '06_permissions.png')
                await allow.first.click()
                await page.wait_for_timeout(1500)
        await shot(page, '07_installed_list.png')
        opener = page.get_by_role('button', name=re.compile('^open$', re.I))
        await opener.first.click()
        await page.wait_for_timeout(3000)
        await shot(page, '08_panel_open.png')

        frame = await plugin_frame(page)
        print('plugin frame', frame.url)
        await frame.fill('#key', KEY)
        await frame.click('#connect-btn')
        await frame.wait_for_selector('#main:not(.hidden)', timeout=15000)
        await shot(page, '09_connected.png')
        await frame.select_option('#count', '10')
        await frame.click('#add-btn')
        await frame.wait_for_function("document.getElementById('main-msg').textContent.indexOf('on the canvas') !== -1 || document.getElementById('main-msg').className.indexOf('error') !== -1", timeout=20000)
        msg = await frame.inner_text('#main-msg')
        print('panel says:', msg)
        await page.wait_for_timeout(2500)
        await shot(page, '10_after_add.png')
        await page.mouse.click(1303, 70)
        await page.wait_for_timeout(800)
        await page.keyboard.press('Shift+1')
        await page.wait_for_timeout(2500)
        await shot(page, '11_canvas.png')
        dump = await page.evaluate(RPC, ['get-file', {'id': f['file']}])
        open(os.path.join(HERE, '.penpot_dump.json'), 'w', encoding='utf-8').write(dump['body'])
        print('get-file', dump['status'], len(dump['body']))
        print('errors:', [e for e in errors if 'favicon' not in e][:15])
        await browser.close()

asyncio.run(main())
