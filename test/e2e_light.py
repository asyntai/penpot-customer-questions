"""The panel in Penpot's light theme. Local instance only."""
import asyncio, json, os, re
from playwright.async_api import async_playwright

BASE = 'http://localhost:9001'
HERE = os.path.dirname(__file__)
RPC = """async ([name, params]) => {
  const r = await fetch('/api/rpc/command/' + name, {method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json', 'Accept': 'application/json'}, body: JSON.stringify(params)});
  return {status: r.status, body: await r.text()};
}"""

async def main():
    f = json.load(open(os.path.join(HERE, '.penpot_file.json')))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--host-resolver-rules=MAP localhost 127.0.0.1'])
        ctx = await browser.new_context(viewport={'width': 1600, 'height': 1000},
                                        storage_state=os.path.join(HERE, '.penpot_state.json'))
        page = await ctx.new_page()
        await page.goto(BASE + '/#/dashboard/recent')
        await page.wait_for_timeout(3000)
        me = json.loads((await page.evaluate(RPC, ['get-profile', {}]))['body'])
        r = await page.evaluate(RPC, ['update-profile', {'fullname': me['fullname'], 'lang': me.get('lang') or '', 'theme': 'light'}])
        print('update-profile', r['status'])
        await page.goto(BASE + '/#/workspace?team-id=%s&file-id=%s&page-id=%s' % (f['team'], f['file'], f['page']))
        await page.wait_for_timeout(7000)
        await page.keyboard.press('Control+Alt+P')
        await page.wait_for_timeout(1500)
        await page.get_by_role('button', name=re.compile('^open$', re.I)).first.click()
        await page.wait_for_timeout(3000)
        fr = [x for x in page.frames if '4400' in x.url][0]
        print('frame url', fr.url)
        print('panel theme', await fr.evaluate("document.documentElement.getAttribute('data-theme')"))
        print('body bg', await fr.evaluate("getComputedStyle(document.body).backgroundColor"))
        await page.screenshot(path=os.path.join(HERE, 'shots', '15_light.png'))
        await page.evaluate(RPC, ['update-profile', {'fullname': me['fullname'], 'lang': me.get('lang') or '', 'theme': 'dark'}])
        await browser.close()

asyncio.run(main())
