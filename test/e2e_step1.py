"""Log in to the local Penpot and look around. Headless, local instance only."""
import asyncio, os, sys
from playwright.async_api import async_playwright

BASE = 'http://localhost:9001'
SHOTS = os.path.join(os.path.dirname(__file__), 'shots')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--host-resolver-rules=MAP localhost 127.0.0.1'])
        ctx = await browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = await ctx.new_page()
        page.on('console', lambda m: print('[console]', m.type, m.text[:200]))
        await page.goto(BASE + '/#/auth/login')
        await page.wait_for_timeout(4000)
        await page.screenshot(path=os.path.join(SHOTS, '01_login.png'))
        await page.fill('input[name="email"], #email', 'tester@example.test')
        await page.fill('input[name="password"], #password', 'LocalOnly-12345')
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(6000)
        await page.screenshot(path=os.path.join(SHOTS, '02_dashboard.png'))
        print('URL', page.url)
        await ctx.storage_state(path=os.path.join(os.path.dirname(__file__), '.penpot_state.json'))
        await browser.close()

asyncio.run(main())
