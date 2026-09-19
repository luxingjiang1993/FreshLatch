"""复验单 UI:FastAPI 薄壳 + 手写 HTML/JS 双栏(左主张卡片,右原文面板)。

形态红线(§5.1):主界面是复验单,不是聊天框;主按钮 =「开始复验」;界面标注 SYNTHETIC。
HumanLatch 端点(W3 起)为同步 def 端点设计(§5.5),本期不挂载;核心包零 Web 依赖。
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from freshlatch.runner import Runner, load_docket  # noqa: E402
from freshlatch.store.ingest import parse_document  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORPUS = REPO_ROOT / "data" / "corpus"
DEMO_DOCKET = REPO_ROOT / "data" / "t0_docket.json"

BADGE = {
    "fresh": ("绿 · 仍成立", "#1a7f37"),
    "stale": ("红 · 已失效", "#cf222e"),
    "unknown": ("灰 · 证据不足", "#6e7781"),
    "void": ("void · 已作废", "#8250df"),
}
MAIN_BUTTON_TEXT = "开始复验"  # 文案白名单(红线 2):主按钮唯一合法文案

app = FastAPI(title="FreshLatch 复验单")
_state: dict = {"claims": [], "question": "", "trajectory": None, "running": False}


def _store() -> SQLiteStore:
    return SQLiteStore(REPO_ROOT / "data" / "freshlatch.db")


@app.get("/api/claims")
def api_claims() -> dict:
    return {
        "question": _state["question"],
        "claims": [_claim_to_dict(c) for c in _state["claims"]],
        "trajectory": str(_state["trajectory"]) if _state["trajectory"] else None,
        "running": _state["running"],
    }


def _claim_to_dict(c) -> dict:
    return {
        "claim_id": c.claim_id,
        "statement": c.statement,
        "t0_evidence_ids": c.t0_evidence_ids,
        "t1_evidence_ids": c.t1_evidence_ids,
        "status": c.status,
        "reason": c.reason,
    }


@app.post("/api/import")
def api_import() -> dict:
    """docket 导入(Workflow):只读 statement 与 t0_evidence_ids,不做新调查。"""
    claims = load_docket(DEMO_DOCKET)
    _state["claims"] = claims
    _state["question"] = "是否应该在未来 12 个月进入东南亚中小企业 AI 客服市场?"
    return {"imported": len(claims)}


@app.post("/api/reverify")
def api_reverify() -> JSONResponse:
    """主按钮「开始复验」:端到端真主链(Lead 裸循环 + 规则闸),轨迹落盘。"""
    if _state["running"]:
        return JSONResponse({"error": "已有复验在进行中"}, status_code=409)
    if not _state["claims"]:
        api_import()
    _state["running"] = True
    try:
        runner = Runner(_store())
        result = runner.run(list(_state["claims"]))
        _state["trajectory"] = result.trajectory_path
    finally:
        _state["running"] = False
    return JSONResponse({
        "claims": [_claim_to_dict(c) for c in _state["claims"]],
        "trajectory": str(result.trajectory_path),
        "retrieval_used": result.retrieval_used,
        "steps_by_claim": result.steps_by_claim,
        "decoding": result.decoding.__dict__,
    })


@app.get("/api/source/{doc_id}")
def api_source(doc_id: str, as_of: str = Query("T1", pattern="^(T0|T1)$")) -> dict:
    """点回原文:返回条款级锚点段落,前端定位 + 高亮。"""
    path = CORPUS / as_of.lower() / f"{doc_id}.md"
    if not path.exists():
        return JSONResponse({"error": f"未找到 {doc_id} 的 {as_of} 快照"}, status_code=404)
    doc, chunks = parse_document(path)
    return {
        "doc_id": doc_id,
        "as_of": as_of,
        "title": doc.title,
        "source_type": doc.source_type,
        "sections": [{"anchor": c.clause_id, "text": c.text} for c in chunks],
    }


HTML_PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>FreshLatch 复验单 — SYNTHETIC</title>
<style>
 body{font-family:system-ui,"Microsoft YaHei",sans-serif;margin:0;background:#f6f8fa}
 header{background:#0a2540;color:#fff;padding:12px 24px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
 header .syn{background:#b45309;color:#fff;font-size:12px;padding:2px 10px;border-radius:10px}
 main{display:grid;grid-template-columns:44% 56%;gap:0;height:calc(100vh - 53px)}
 #claims{overflow-y:auto;border-right:1px solid #d0d7de;padding:12px 16px}
 #pane{overflow-y:auto;padding:12px 16px}
 .claim{border:1px solid #d0d7de;border-left:6px solid #999;border-radius:6px;padding:8px 12px;
        margin-bottom:8px;cursor:pointer;background:#fff}
 .claim.sel{outline:2px solid #0969da}
 .badge{font-size:12px;font-weight:600;margin-left:8px}
 .reason{font-size:13px;color:#57606a;margin-top:4px;white-space:pre-wrap}
 .ev{font-size:12px;margin-top:4px}
 .ev a{color:#0969da;cursor:pointer;text-decoration:none;margin-right:8px}
 .ev a:hover{text-decoration:underline}
 button.big{background:#1f883d;color:#fff;border:0;border-radius:6px;padding:8px 18px;font-size:15px;cursor:pointer}
 button.big:disabled{background:#9e9e9e;cursor:wait}
 .latch button{margin-right:8px;padding:6px 14px;border-radius:6px;border:1px solid #d0d7de;cursor:pointer}
 .doc{background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:10px 14px;margin-bottom:10px}
 .doc .clause{margin:8px 0;padding:6px 8px;border-radius:4px}
 .doc .clause.hit{background:#fff8c5;outline:2px solid #d4a72c}
 mark{background:#fff8c5;padding:1px 3px;border-radius:3px}
 .asof{font-size:11px;color:#fff;background:#57606a;border-radius:4px;padding:1px 6px;margin-right:6px}
 .tabs button{padding:4px 12px;border:1px solid #d0d7de;background:#fff;cursor:pointer}
 .tabs button.on{background:#0a2540;color:#fff}
 #status{font-size:13px;color:#57606a}
 details{margin-top:12px;background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:8px 12px}
 code{background:#eff1f3;padding:1px 5px;border-radius:4px}
</style>
</head>
<body>
<header>
 <strong>FreshLatch 复验单</strong>
 <span class="syn">SYNTHETIC · 合成语料,非真实客户数据</span>
 <span id="status"></span>
 <span style="flex:1"></span>
 <button class="big" id="btn-run" onclick="runReverify()">开始复验</button>
</header>
<main>
 <section id="claims"><p style="color:#57606a">加载中……</p></section>
 <section id="pane"><p style="color:#57606a">← 点击主张的证据 id,这里显示 T0/T1 原文并高亮锚点段落</p></section>
</main>
<script>
let STATE = {claims: [], question: ""};
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
const BADGE = {fresh:["绿 · 仍成立","#1a7f37"],stale:["红 · 已失效","#cf222e"],
               unknown:["灰 · 证据不足","#6e7781"],void:["void · 已作废","#8250df"]};

async function boot(){
  await fetch('/api/import',{method:'POST'});
  const j = await (await fetch('/api/claims')).json();
  STATE = j; renderClaims();
}
function renderClaims(){
  const el = document.getElementById('claims');
  let h = '<h3 style="margin:4px 0 10px">主张复验单 <span style="font-weight:400;font-size:13px;color:#57606a">'
        + esc(STATE.question||'') + '</span></h3>';
  for(const c of STATE.claims){
    const [label,color] = BADGE[c.status] || BADGE.unknown;
    h += '<div class="claim" id="c-'+c.claim_id+'" style="border-left-color:'+color+'" '
       + 'onclick="pickClaim(\''+c.claim_id+'\')">'
       + '<b>'+c.claim_id+'</b><span class="badge" style="color:'+color+'">'+label+'</span>'
       + '<div>'+esc(c.statement)+'</div>';
    if(c.reason) h += '<div class="reason">'+esc(c.reason)+'</div>';
    h += '<div class="ev">';
    for(const e of c.t0_evidence_ids||[]) h += '<a onclick="event.stopPropagation();showSource(\''+e.split('#')[0]+'\',\''+e.split('#')[1]+'\',\'T0\')">'+esc(e)+'</a>';
    for(const e of c.t1_evidence_ids||[]) h += '<a onclick="event.stopPropagation();showSource(\''+e.split('#')[0]+'\',\''+e.split('#')[1]+'\',\'T1\')">'+esc(e)+'</a>';
    h += '</div>';
    h += '<div class="latch" style="margin-top:6px">'
       + '<button disabled title="W5 开放:续命必须带 T1 原文证据">续命(W5 开放)</button>'
       + '</div></div>';
  }
  el.innerHTML = h;
}
function pickClaim(cid){
  document.querySelectorAll('.claim').forEach(e=>e.classList.remove('sel'));
  document.getElementById('c-'+cid)?.classList.add('sel');
}
async function showSource(docId, anchor, asOf){
  const j = await (await fetch('/api/source/'+encodeURIComponent(docId)+'?as_of='+(asOf||'T1'))).json();
  if(j.error){ document.getElementById('pane').innerHTML = '<p>'+esc(j.error)+'</p>'; return; }
  let h = '<h3>'+esc(j.title)+' <span class="asof">'+j.as_of+'</span> <span class="asof">'+esc(j.source_type)+'</span></h3>';
  h += '<div class="tabs" style="margin-bottom:8px">'
     + '<button class="'+((asOf||'T1')==='T0'?'on':'')+'" onclick="showSource(\''+docId+'\',\''+anchor+'\',\'T0\')">T0 签发时</button>'
     + '<button class="'+((asOf||'T1')==='T1'?'on':'')+'" onclick="showSource(\''+docId+'\',\''+anchor+'\',\'T1\')">T1 复验时刻</button></div>';
  h += '<div class="doc">';
  for(const s of j.sections){
    const hit = s.anchor === anchor;
    h += '<div class="clause'+(hit?' hit':'')+'" id="anchor-'+s.anchor+'">'
       + '<code>## '+esc(s.anchor)+'</code>' + esc(s.text.replace('## '+s.anchor,'')) + '</div>';
  }
  h += '</div>';
  document.getElementById('pane').innerHTML = h;
  const target = document.getElementById('anchor-'+anchor);
  if(target) target.scrollIntoView({behavior:'smooth', block:'center'});
}
async function runReverify(){
  const btn = document.getElementById('btn-run');
  btn.disabled = true;
  document.getElementById('status').textContent = '复验中(端到端真主链:Lead 循环 + 规则闸)……';
  try{
    const j = await (await fetch('/api/reverify',{method:'POST'})).json();
    if(j.error){ document.getElementById('status').textContent = j.error; return; }
    STATE.claims = j.claims;
    renderClaims();
    document.getElementById('status').textContent =
      '复验完成 · 检索 '+j.retrieval_used+'/24 · 轨迹 '+j.trajectory
      +' · '+j.decoding.model+' temp='+j.decoding.temperature+' '+j.decoding.recorded_at;
  } finally { btn.disabled = false; }
}
boot();
</script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return HTML_PAGE


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
