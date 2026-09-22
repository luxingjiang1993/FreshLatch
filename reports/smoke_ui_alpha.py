# -*- coding: utf-8 -*-
"""本地冒烟(α-demo):T1 三卡 → 主张导入稿 → 复验 → 职人/审计切换 → client-memo 导出。

对已启动的 http://127.0.0.1:8765/ 跑 Playwright + API 收口。
层:α-demo / 冒烟;不得升格为 latch 已证明 / 一期测量闭合。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "reports" / "batch1_alpha" / "local_smoke_ui"
SHOT = OUT / "screenshots"

# 小导入稿:2 条,缩短冒烟墙钟(仍走真主链)
DRAFT = """# 是否应在未来 12 个月内进入东南亚中小企业 AI 客服市场?

## c1
竞品 SeaDesk 在该市场的客单价显著高于我方公开定价 59 美元/席/月定价

## c2
印尼与泰国目前无客服数据本地化强制要求
"""


def _ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SHOT.mkdir(parents=True, exist_ok=True)


def _shot(page, name: str) -> None:
    path = SHOT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"[shot] {path.relative_to(REPO).as_posix()}")


def _api(page, method: str, path: str, **kwargs):
    # GET/HEAD 不得带 body;仅 POST 等传 JSON
    payload = {"method": method, "path": path}
    if "body" in kwargs:
        payload["body"] = kwargs["body"]
    return page.evaluate(
        """async (payload) => {
          const opt = {method: payload.method, headers: {}};
          if (Object.prototype.hasOwnProperty.call(payload, 'body')) {
            opt.headers['Content-Type'] = 'application/json';
            opt.body = JSON.stringify(payload.body);
          }
          const r = await fetch(payload.path, opt);
          const text = await r.text();
          let j = null;
          try { j = JSON.parse(text); } catch(e) { j = {raw: text}; }
          return {status: r.status, body: j};
        }""",
        payload,
    )


def run() -> dict:
    _ensure_dirs()
    t0 = time.perf_counter()
    log: dict = {
        "layer": "α-demo",
        "label": "local-smoke-ui",
        "base": BASE,
        "steps": [],
        "ok": False,
        "note": (
            "本地冒烟;不得说成产品已验证 / 一期测量闭合 / UX 证明了 latch。"
        ),
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(60_000)

        # 1) 打开复验单
        page.goto(BASE + "/", wait_until="networkidle")
        page.wait_for_selector("#t1-source")
        _shot(page, "01_boot")
        log["steps"].append({"step": "boot", "ok": True})

        # 2) T1 三卡:选用合成评测包
        page.click("text=选用合成评测包")
        page.wait_for_function(
            """() => {
              const m = document.getElementById('t1-msg');
              return m && m.textContent && m.textContent.length > 0;
            }"""
        )
        t1 = _api(page, "GET", "/api/t1-source")
        ready = bool((t1.get("body") or {}).get("ready"))
        syn = bool((t1.get("body") or {}).get("synthetic"))
        _shot(page, "02_t1_synthetic")
        log["steps"].append(
            {
                "step": "t1_three_cards_synthetic",
                "ok": ready and syn,
                "ready": ready,
                "synthetic": syn,
                "message": (t1.get("body") or {}).get("message"),
            }
        )
        if not (ready and syn):
            raise RuntimeError(f"T1 三卡未就绪: {t1}")

        # 3) 主张导入稿
        page.click("button:has-text('主张导入稿')")
        page.wait_for_selector("#claim-import-draft", state="visible")
        page.fill("#claim-import-draft", DRAFT)
        page.click("button:has-text('导入主张导入稿')")
        page.wait_for_function(
            """() => {
              const s = document.getElementById('status');
              return s && s.textContent && s.textContent.includes('导入');
            }"""
        )
        claims = _api(page, "GET", "/api/claims")
        body = claims.get("body") or {}
        n = len(body.get("claims") or [])
        ids = [c.get("claim_id") for c in (body.get("claims") or [])]
        _shot(page, "03_import_draft")
        log["steps"].append(
            {
                "step": "import_draft",
                "ok": n == 2 and ids == ["c1", "c2"],
                "imported": n,
                "ids": ids,
                "question": body.get("question"),
            }
        )
        if n != 2:
            raise RuntimeError(f"导入稿条数异常: {ids}")

        # 4) 开始复验(真主链;墙钟可能数分钟)
        page.click("#btn-run")
        page.wait_for_function(
            """() => {
              const s = document.getElementById('status');
              return s && s.textContent && s.textContent.indexOf('复验中') === 0;
            }""",
            timeout=30_000,
        )
        _shot(page, "04_reverify_running")
        # 等待完成:状态离开「复验中」且主张带 status
        page.wait_for_function(
            """() => {
              const s = document.getElementById('status');
              if (!s || !s.textContent) return false;
              const t = s.textContent;
              if (t.indexOf('复验中') === 0) return false;
              return t.includes('复验完成') || t.includes('轨迹') || t.includes('人审');
            }""",
            timeout=900_000,  # 15min 上限
        )
        after = _api(page, "GET", "/api/claims")
        ab = after.get("body") or {}
        statuses = {c["claim_id"]: c.get("status") for c in (ab.get("claims") or [])}
        _shot(page, "05_reverify_done")
        log["steps"].append(
            {
                "step": "reverify",
                "ok": bool(ab.get("trajectory")) and len(statuses) == 2,
                "trajectory": ab.get("trajectory"),
                "statuses": statuses,
                "retrieve_zero_hits": len(ab.get("retrieve_zero_hits") or []),
                "status_bar": page.locator("#status").inner_text(),
            }
        )

        # 5) 职人 / 审计切换
        # 默认职人:审计面板不可见
        craftsman_hidden = not page.locator("#audit-panel.visible").count()
        page.click("#view-audit")
        page.wait_for_selector("#audit-panel.visible")
        audit_on = page.locator("#view-audit.on").count() == 1
        _shot(page, "06_view_audit")
        page.click("#view-craftsman")
        page.wait_for_function(
            """() => !document.getElementById('audit-panel').classList.contains('visible')"""
        )
        craftsman_on = page.locator("#view-craftsman.on").count() == 1
        _shot(page, "07_view_craftsman")
        log["steps"].append(
            {
                "step": "view_toggle",
                "ok": craftsman_hidden and audit_on and craftsman_on,
                "craftsman_default_panel_hidden": craftsman_hidden,
                "audit_toggle_ok": audit_on,
                "craftsman_toggle_ok": craftsman_on,
            }
        )

        # 6) 落快照 + client-memo 导出(CLI;UI 无导出钮,契约口在 export)
        snap_path = OUT / "smoke_snapshot.json"
        db_path = REPO / "data" / "freshlatch.db"
        snap = {
            "question": ab.get("question") or "",
            "store": str(db_path),
            "trajectory": ab.get("trajectory"),
            "claims": ab.get("claims") or [],
            "synthetic": True,
            "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        snap_path.write_text(
            json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        memo_path = OUT / "client_memo.md"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "freshlatch.export",
                "client-memo",
                "--snapshot",
                str(snap_path),
                "--db",
                str(db_path),
                "--out",
                str(memo_path),
            ],
            cwd=str(REPO),
            env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        memo_text = memo_path.read_text(encoding="utf-8") if memo_path.exists() else ""
        # INV-3:角色禁语只查正文;DEM-3 勾选面可出现禁语字样作检查项标题
        memo_body = memo_text.split("## DEM-3")[0] if memo_text else ""
        memo_ok = (
            proc.returncode == 0
            and memo_text.startswith("# 客户向复验备忘")
            and all(h in memo_text for h in ("## 仍成立", "## 已作废", "## 缺口"))
            and "Lead" not in memo_body
            and "Critic" not in memo_body
            and "建议进入" not in memo_body
            and "建议不进入" not in memo_body
        )
        log["steps"].append(
            {
                "step": "client_memo_export",
                "ok": memo_ok,
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "").strip()[:400],
                "stderr": (proc.stderr or "").strip()[:400],
                "memo_path": memo_path.relative_to(REPO).as_posix()
                if memo_path.exists()
                else None,
                "memo_chars": len(memo_text),
                "has_title": memo_text.startswith("# 客户向复验备忘"),
            }
        )

        browser.close()

    elapsed_s = time.perf_counter() - t0
    log["elapsed_seconds"] = round(elapsed_s, 2)
    log["elapsed_minutes"] = round(elapsed_s / 60.0, 4)
    log["ok"] = all(s.get("ok") for s in log["steps"])
    log["recorded_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = OUT / "smoke-result.json"
    record.write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(log, ensure_ascii=False, indent=2))
    print(f"\n记录: {record}")
    return log


if __name__ == "__main__":
    result = run()
    sys.exit(0 if result.get("ok") else 1)
