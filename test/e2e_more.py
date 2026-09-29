"""Second pass in the real (local) Penpot, on the file e2e_run.py filled.

Checks: the stored key connects on its own, a second block lands under the
first, a wrong key shows the API error, "Use another API key" forgets the key,
and the website and period filters reach the API.
"""
import asyncio, json, os, re, urllib.request
from playwright.async_api import async_playwright

BASE = 'http://localhost:9001'
HERE = os.path.dirname(__file__)
SHOTS = os.path.join(HERE, 'shots')
RPC = """async ([name, params]) => {
  const r = await fetch('/api/rpc/command/' + name, {
    method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
    body: JSON.stringify(params)});
  return {status: r.status, body: await r.text()};
}"""

passed = failed = 0
def check(name, ok, detail=''):
    global passed, failed
    if ok:
        passed += 1; print('  ok   ' + name)
    else:
        failed += 1; print('  FAIL ' + name + ('  ' + detail if detail else ''))

async def open_plugin(page):
    await page.keyboard.press('Control+Alt+P')
    await page.wait_for_timeout(1500)
    await page.get_by_role('button', name=re.compile('^open$', re.I)).first.click()
    for _ in range(40):
        for fr in page.frames:
            if '4400' in fr.url:
                await fr.wait_for_load_state()
                return fr
        await page.wait_for_timeout(250)
    raise RuntimeError('no plugin frame')

async def close_plugin(page):
    await page.mouse.click(1303, 70)
    await page.wait_for_timeout(800)

def calls():
    return json.load(urllib.request.urlopen('http://localhost:4400/__calls'))['calls']

async def main():
    f = json.load(open(os.path.join(HERE, '.penpot_file.json')))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--host-resolver-rules=MAP localhost 127.0.0.1'])
        ctx = await browser.new_context(viewport={'width': 1600, 'height': 1000},
                                        storage_state=os.path.join(HERE, '.penpot_state.json'))
        page = await ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto(BASE + '/#/workspace?team-id=%s&file-id=%s&page-id=%s' % (f['team'], f['file'], f['page']))
        await page.wait_for_timeout(7000)

        # 1. A saved key connects on its own after the plugin closes and after
        # the whole page reloads. Each headless run starts with empty browser
        # storage, so the key is saved first in this same browser.
        fr = await open_plugin(page)
        await page.wait_for_timeout(1500)
        if 'hidden' not in (await fr.get_attribute('#connect', 'class') or ''):
            await fr.fill('#key', 'demo-key')
            await fr.click('#connect-btn')
            await fr.wait_for_selector('#main:not(.hidden)', timeout=10000)
        await close_plugin(page)
        await page.reload()
        await page.wait_for_timeout(7000)
        stored = await page.evaluate("Object.keys(localStorage).filter(k => k.indexOf('asyntai') !== -1)")
        print('   localStorage keys holding the key:', stored)
        check('key is stored under a plugin-scoped name', len(stored) >= 1, str(stored))
        fr = await open_plugin(page)
        try:
            await fr.wait_for_selector('#main:not(.hidden)', timeout=10000)
            check('stored key reconnects without typing', True)
        except Exception as e:
            check('stored key reconnects without typing', False, str(e)[:120])
        check('connect view is hidden', 'hidden' in (await fr.get_attribute('#connect', 'class') or ''))
        check('dark theme reached the panel', (await fr.evaluate("document.documentElement.getAttribute('data-theme')")) == 'dark')

        # 2. Website and period filters reach the API.
        before = len(calls())
        await fr.select_option('#site', '102')
        await fr.select_option('#range', '7')
        await fr.select_option('#count', '25')
        await fr.click('#add-btn')
        await fr.wait_for_function("document.getElementById('main-msg').textContent.indexOf('on the canvas') !== -1", timeout=20000)
        msg = await fr.inner_text('#main-msg')
        check('second run reports its count', re.match(r'^\d+ questions are on the canvas\.$', msg) is not None, msg)
        new = calls()[before:]
        sess = [c for c in new if c.startswith('/api/v1/sessions/')]
        check('sessions call carries website_id=102', any('website_id=102' in c for c in sess), str(sess))
        check('sessions call carries a since date', any(re.search(r'since=\d{4}-\d{2}-\d{2}', c) for c in sess), str(sess))
        await page.wait_for_timeout(1500)
        await page.screenshot(path=os.path.join(SHOTS, '12_second_run.png'))

        # 3. "Use another API key" forgets the key; a wrong key shows the error.
        await fr.click('#forget-btn')
        await page.wait_for_timeout(500)
        check('forget shows the connect view', 'hidden' not in (await fr.get_attribute('#connect', 'class') or ''))
        await fr.fill('#key', 'bad-key')
        await fr.click('#connect-btn')
        await fr.wait_for_function("document.getElementById('connect-msg').className.indexOf('error') !== -1", timeout=10000)
        err = await fr.inner_text('#connect-msg')
        check('wrong key shows the API error', 'Invalid API key' in err, err)
        await page.screenshot(path=os.path.join(SHOTS, '13_wrong_key.png'))
        await close_plugin(page)

        # 4. After forget + close + reopen, nothing connects on its own.
        fr = await open_plugin(page)
        await page.wait_for_timeout(2500)
        check('forgotten key stays forgotten after reopen', 'hidden' not in (await fr.get_attribute('#connect', 'class') or ''))
        check('key field is empty after reopen', (await fr.input_value('#key')) == '')
        # Leave it connected for the next run.
        await fr.fill('#key', 'demo-key')
        await fr.press('#key', 'Enter')
        await fr.wait_for_selector('#main:not(.hidden)', timeout=10000)
        check('Enter key connects', True)
        await close_plugin(page)

        # 5. The two blocks do not overlap.
        dump = json.loads((await page.evaluate(RPC, ['get-file', {'id': f['file']}]))['body'])
        objs = list(dump['data']['pagesIndex'].values())[0]['objects']
        blocks = [o for o in objs.values() if o['type'] == 'frame' and o.get('name', '').startswith('Visitor questions')]
        blocks.sort(key=lambda o: o['y'])
        check('two blocks on the page', len(blocks) == 2, str(len(blocks)))
        if len(blocks) == 2:
            a, b = blocks
            check('second block starts 200 under the first', abs(b['y'] - (a['y'] + a['height'] + 200)) < 1, '%s %s %s' % (a['y'], a['height'], b['y']))
            check('second block title names the period', b['name'] == 'Visitor questions, last 7 days', b['name'])
        check('no page errors', not errors, str(errors[:3]))
        await page.keyboard.press('Shift+1')
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SHOTS, '14_two_blocks.png'))
        await browser.close()
    print('\n%d passed, %d failed' % (passed, failed))

asyncio.run(main())
