"""复现:复验后左栏点击失灵、右栏被锁定。"""
import asyncio
from playwright.async_api import async_playwright

URL = "http://127.0.0.1:8000/"


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        await page.goto(URL)
        await page.wait_for_selector(".claim", timeout=10000)
        n0 = await page.locator(".claim").count()
        print(f"[复验前] 卡片数={n0}")

        # 1) 复验前:点证据 id,验证右栏加载
        await page.locator(".ev a").first.click()
        await page.wait_for_selector("#pane .doc", timeout=8000)
        title_before = await page.locator("#pane h3").inner_text()
        print(f"[复验前] 点证据 → 右栏标题={title_before.strip()[:50]!r}")

        # 复验前:点 T0 页签也验证一下
        await page.locator("#pane .tabs button", has_text="T0").click()
        await page.wait_for_selector("#pane .doc", timeout=8000)
        print("[复验前] T0 页签可点")

        # 2) 点「开始复验」
        await page.locator("#btn-run").click()
        await page.wait_for_function("!document.getElementById('btn-run').disabled", timeout=300000)
        status = await page.locator("#status").inner_text()
        print(f"[复验后] 状态栏={status.strip()[:120]!r}")
        n1 = await page.locator(".claim").count()
        print(f"[复验后] 卡片数={n1}")

        # 3) 复验后:点另一张卡片的证据 id
        links = page.locator(".ev a")
        cnt = await links.count()
        print(f"[复验后] 证据链接数={cnt}")
        if cnt >= 2:
            await links.nth(1).click()
            await page.wait_for_timeout(1500)
            try:
                title_after = await page.locator("#pane h3").inner_text()
            except Exception:
                title_after = "<无标题/无文档>"
            print(f"[复验后] 点第2个证据 → 右栏标题={title_after.strip()[:50]!r}")

        # 4) 复验后:点卡片(选中高亮)
        await page.locator(".claim").nth(2).click()
        await page.wait_for_timeout(300)
        sel_count = await page.locator(".claim.sel").count()
        print(f"[复验后] 点卡片 → 高亮卡片数={sel_count}")

        # 5) 右栏 T0/T1 是否还能切
        tabs = page.locator("#pane .tabs button")
        tc = await tabs.count()
        if tc:
            try:
                on_before = await page.locator("#pane .tabs button.on").inner_text()
            except Exception:
                on_before = "?"
            await tabs.nth(0).click()
            await page.wait_for_timeout(500)
            try:
                on_after = await page.locator("#pane .tabs button.on").inner_text()
            except Exception:
                on_after = "?"
            print(f"[复验后] T0/T1 页签: {on_before.strip()!r} → 点击后 {on_after.strip()!r}")

        print(f"[console 错误] {errors if errors else '无'}")
        await browser.close()


asyncio.run(main())
