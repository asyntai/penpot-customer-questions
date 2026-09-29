"""Make a fresh Penpot file through the RPC API and open it. Local instance only."""
import asyncio, json, os
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

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--host-resolver-rules=MAP localhost 127.0.0.1'])
        ctx = await browser.new_context(viewport={'width': 1600, 'height': 1000},
                                        storage_state=os.path.join(HERE, '.penpot_state.json'))
        page = await ctx.new_page()
        await page.goto(BASE + '/#/dashboard/recent')
        await page.wait_for_timeout(3000)
        prof = await page.evaluate(RPC, ['get-profile', {}])
        me = json.loads(prof['body'])
        await page.evaluate(RPC, ['update-profile-props', {'props': {'onboardingViewed': True, 'v2InfoShown': True, 'releaseNotesViewed': '9.9.9'}}])
        made = await page.evaluate(RPC, ['create-file', {'projectId': me['defaultProjectId'], 'name': 'Asyntai plugin test'}])
        f = json.loads(made['body'])
        page_id = f['data']['pages'][0]
        print('file', f['id'], 'page', page_id)
        open(os.path.join(HERE, '.penpot_file.json'), 'w').write(json.dumps({'team': me['defaultTeamId'], 'file': f['id'], 'page': page_id}))
        await page.goto(BASE + '/#/workspace?team-id=%s&file-id=%s&page-id=%s' % (me['defaultTeamId'], f['id'], page_id))
        await page.wait_for_timeout(8000)
        await page.screenshot(path=os.path.join(SHOTS, '03_workspace.png'))
        await page.keyboard.press('Control+Alt+P')
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SHOTS, '04_plugin_manager.png'))
        await browser.close()

asyncio.run(main())
