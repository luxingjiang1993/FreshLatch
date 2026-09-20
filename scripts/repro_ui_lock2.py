"""复现2:连点两次复验,或复验期间点击,观察左栏 handler 是否死亡。"""
import asyncio
from playwright.async_api import async_playwright

URL = "http://127.0.0.1:8000/"


async def click_and_report(page, tag):
    links = page.locator(".ev a")
    cnt = await links.count()
    if cnt >= 3:
        await links.nth(2).click()
        await page.wait_for_timeout(1200)
        try:
            t = await page.locator("#pane h3").inner_text()
        except Exception:
            t = "<无文档>"
        print(f"{tag}: 点证据链接 → 右栏标题={t.strip()[:40]!r}")
    await page.locator(".claim").nth(1).click()
    await page.wait_for_timeout(200)
    sel = await page.locator(".claim.sel").count()
    print(f"{tag}: 点卡片 → 高亮数={sel}")


async def run_once(page, tag):
    await page.locator("#btn-run").click()
    await page.wait_for_function("!document.getElementById('btn-run').disabled", timeout=300000)
    print(f"{tag}: 状态栏={(await page.locator('#status').inner_text()).strip()[:80]!r}")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(URL)
        await page.wait_for_selector(".claim", timeout=10000)

        await run_once(page, "[第1次复验]")
        await click_and_report(page, "[第1次复验后]")
        await run_once(page, "[第2次复验]")
        await click_and_report(page, "[第2次复验后]")

        # 复验进行中点击
        await page.locator("#btn-run").click()
        await page.wait_for_timeout(400)
        mid = await page.locator("#btn-run").is_disabled()
        print(f"[复验进行中] 按钮禁用={mid}")
        await click_and_report(page, "[复验进行中]")
        await page.wait_for_function("!document.getElementById('btn-run').disabled", timeout=300000)
        await click_and_report(page, "[第3次复验后]")

        print(f"[console 错误] {errors if errors else '无'}")
        await browser.close()


asyncio.run(main())
