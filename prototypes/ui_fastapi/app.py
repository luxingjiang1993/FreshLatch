"""PROTOTYPE(ui_fastapi)— 复验单 UI 糙样,FastAPI+纯 HTML/JS,静态假数据。

运行:python prototypes/ui_fastapi/app.py → http://127.0.0.1:8000
这是 throwaway 代码,回答工单 #4 的「FastAPI+HTML 形态长什么样」,不是生产代码。
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fake_data import CLAIMS, DOCS_T0, DOCS_T1, LATCH_LOG, TRACE  # noqa: E402

app = FastAPI(title="FreshLatch 复验单 PROTOTYPE")

BADGE = {"fresh": ("绿 · 仍成立", "#1a7f37"), "stale": ("红 · 已失效", "#cf222e"),
         "unknown": ("灰 · 证据不足", "#6e7781")}

HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>FreshLatch 复验单 — SYNTHETIC DEMO</title>
<style>
 body{font-family:system-ui,"Microsoft YaHei",sans-serif;margin:0;background:#f6f8fa}
 header{background:#0a2540;color:#fff;padding:12px 24px;display:flex;gap:16px;align-items:center}
 header .syn{background:#b45309;color:#fff;font-size:12px;padding:2px 10px;border-radius:10px}
 main{display:grid;grid-template-columns:44% 56%;gap:0;height:calc(100vh - 53px)}
 #claims{overflow-y:auto;border-right:1px solid #d0d7de;padding:12px 16px}
 #pane{overflow-y:auto;padding:12px 16px}
 .claim{border:1px solid #d0d7de;border-left:6px solid #999;border-radius:6px;padding:8px 12px;
        margin-bottom:8px;cursor:pointer;background:#fff}
 .claim.sel{outline:2px solid #0969da}
 .badge{font-size:12px;font-weight:600;margin-left:8px}
 .reason{font-size:13px;color:#57606a;margin-top:4px}
 button.big{background:#1f883d;color:#fff;border:0;border-radius:6px;padding:8px 18px;font-size:15px;cursor:pointer}
 .latch button{margin-right:8px;padding:6px 14px;border-radius:6px;border:1px solid #d0d7de;cursor:pointer}
 .latch .dep{background:#cf222e;color:#fff}.latch .ren{background:#1a7f37;color:#fff}
 .doc{background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:10px 14px;margin-bottom:10px}
 mark{background:#fff8c5;padding:1px 3px;border-radius:3px}
 .asof{font-size:11px;color:#fff;background:#57606a;border-radius:4px;padding:1px 6px;margin-right:6px}
 details{margin-top:12px;background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:8px 12px}
 table{border-collapse:collapse;width:100%;font-size:13px}
 td,th{border-bottom:1px solid #eaeef2;padding:4px 8px;text-align:left;vertical-align:top}
 code{background:#eff1f3;padding:1px 5px;border-radius:4px}
 #log{font-size:13px;color:#57606a;margin-top:8px}
 input{padding:6px 8px;border:1px solid #d0d7de;border-radius:6px;width:280px}
</style>
</head>
<body>
<header>
 <strong>FreshLatch 复验单</strong>
 <span class="syn">SYNTHETIC DEMO · 合成语料,非真实客户数据</span>
 <span style="flex:1"></span>
 <button class="big" onclick="alert('PROTOTYPE:这里触发一次完整复验 Run(W1 实现)')">开始复验</button>
</header>
<main>
 <section id="claims">
   <h3 style="margin:4px 0 10px">主张列表 <span style="font-weight:400;font-size:13px;color:#57606a">点击主张 → 右侧点回 T0/T1 原文</span></h3>
   __CLAIMS__
   <details>
     <summary>工具轨迹(展开,非首页)</summary>
     <table><tr><th>#</th><th>角色</th><th>工具</th><th>参数</th><th>说明</th></tr>
     __TRACE__
     </table>
   </details>
 </section>
 <section id="pane"><p style="color:#57606a">← 点一条主张,这里显示 T0/T1 原文与证据高亮</p></section>
</main>
<script>
const DOCS_T0 = __DOCS_T0__, DOCS_T1 = __DOCS_T1__;
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function show(cid){
 document.querySelectorAll('.claim').forEach(e=>e.classList.remove('sel'));
 document.getElementById('c-'+cid).classList.add('sel');
 const ev = JSON.parse(document.getElementById('c-'+cid).dataset.ev);
 let html = '<h3>'+cid+' 原文点回</h3>';
 html += '<div class="doc"><b>T0 签发时快照</b><br>';
 for(const [d,q] of ev){
   const t = DOCS_T0[d];
   if(t) html += '<p><span class="asof">T0</span><b>'+d+'</b> '+esc(t).replace(esc(q),'<mark>'+esc(q)+'</mark>')+'</p>';
 }
 html += '</div><div class="doc"><b>T1 复验时刻快照</b><br>';
 for(const [d,q] of ev){
   const t = DOCS_T1[d];
   if(t) html += '<p><span class="asof">T1</span><b>'+d+'</b> '+esc(t).replace(esc(q),'<mark>'+esc(q)+'</mark>')+'</p>';
 }
 html += '</div>';
 html += '<div class="latch"><b>人审(HumanLatch):</b> ';
 html += '<button class="dep" onclick="latch(\\''+cid+'\\',\\'deprecate\\')">作废</button>';
 html += '<button class="ren" onclick="latch(\\''+cid+'\\',\\'renew\\')">续命(必须带 T1 evidence_id)</button> ';
 html += '<input id="ev-'+cid+'" placeholder="T1 evidence_id,如 D12"></div>';
 html += '<div id="log"></div>';
 document.getElementById('pane').innerHTML = html;
}
function latch(cid, action){
 const ev = document.getElementById('ev-'+cid)?.value || '';
 if(action==='renew' && !ev){ alert('续命必须带 T1 evidence_id'); return; }
 fetch('/api/latch', {method:'POST', headers:{'Content-Type':'application/json'},
   body: JSON.stringify({claim_id: cid, action, evidence_id: ev})})
 .then(r=>r.json()).then(j=>{
   document.getElementById('log').innerHTML = '<div id="log">动作记录:'+JSON.stringify(j)+'</div>';
 });
}
</script>
</body></html>"""


def render() -> str:
    claims_html = ""
    for c in CLAIMS:
        label, color = BADGE[c["verdict"]]
        claims_html += (
            f'<div class="claim" id="c-{c["id"]}" data-ev=\'{__import__("json").dumps(c["evidence"], ensure_ascii=False)}\''
            f' style="border-left-color:{color}" onclick="show(\'{c["id"]}\')">'
            f'<b>{c["id"]}</b> {c["text"]}'
            f'<span class="badge" style="color:{color}">{label}</span>'
            f'<div class="reason">{c["reason"]}</div></div>'
        )
    trace_html = "".join(
        f"<tr><td>{t['t']}</td><td>{t['actor']}</td><td><code>{t['tool']}</code></td>"
        f"<td><code>{t['args']}</code></td><td>{t['note']}</td></tr>" for t in TRACE
    )
    import json as _json
    return (HTML.replace("__CLAIMS__", claims_html)
                .replace("__TRACE__", trace_html)
                .replace("__DOCS_T0__", _json.dumps(DOCS_T0, ensure_ascii=False))
                .replace("__DOCS_T1__", _json.dumps(DOCS_T1, ensure_ascii=False)))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return render()


@app.post("/api/latch")
async def latch(req: Request) -> JSONResponse:
    body = await req.json()
    LATCH_LOG.append(body)  # PROTOTYPE: 只记内存
    return JSONResponse({"ok": True, "log": LATCH_LOG[-3:]})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
