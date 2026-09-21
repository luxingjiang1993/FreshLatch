"""复验单 UI:FastAPI 薄壳 + 手写 HTML/JS 双栏(左主张卡片,右原文面板)。

形态红线(§5.1):主界面是复验单,不是聊天框;主按钮 =「开始复验」;界面标注 SYNTHETIC。
HumanLatch 端点(W3 起,§5.5)为同步 def 端点:FastAPI 线程池执行,同步 SqliteSaver
不阻塞事件循环(ADR-0006 §8);写路径唯一 = gates/human_latch.py,核心包零 Web 依赖。
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from freshlatch.latch import HumanLatch, HumanLatchError  # noqa: E402
from freshlatch.runner import Runner, load_docket  # noqa: E402
from freshlatch.store.ingest import parse_document  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORPUS = REPO_ROOT / "data" / "corpus"
DEMO_DOCKET = REPO_ROOT / "data" / "t0_docket.json"
CHECKPOINTS = REPO_ROOT / "data" / "checkpoints.db"

BADGE = {
    "fresh": ("绿 · 仍成立", "#1a7f37"),
    "stale": ("红 · 已失效", "#cf222e"),
    "unknown": ("灰 · 证据不足", "#6e7781"),
    "void": ("void · 已作废", "#8250df"),
}
MAIN_BUTTON_TEXT = "开始复验"  # 文案白名单(红线 2):主按钮唯一合法文案
EMPTY_LATCH = {"thread_id": None, "pending": []}  # 人审轮状态收口(不各处字面造 dict)
# 人审动作时间线文案(后端唯一生成,前端不复制分支);重跑文案走 HumanLatch.timeline_label
LATCH_EVENT_LABELS = {"discard": "人审作废", "renew": "人审续命"}

app = FastAPI(title="FreshLatch 复验单")
_state: dict = {"claims": [], "question": "", "trajectory": None, "running": False,
                "latch": dict(EMPTY_LATCH)}


def _store() -> SQLiteStore:
    return SQLiteStore(REPO_ROOT / "data" / "freshlatch.db")


def _latch() -> HumanLatch:
    return HumanLatch(_store(), CHECKPOINTS, mode="online")


def _claim_to_dict(store: SQLiteStore, c) -> dict:
    # 时间线 = 重跑(rerun_log)+ 人审动作(latch_log 的作废/续命)两条审计迹按 ts 合并;
    # rerun 同时写两表,只从 rerun_log 计一次,不重复。单一真相在库表。
    events = [{**t, "kind": "rerun", "evidence_id": None,
               "label": HumanLatch.timeline_label(t["verdict"], t["nth"])}
              for t in store.list_reruns(c.claim_id)]
    events += [{"kind": e["action"], "ts": e["ts"], "thread_id": None, "note": "",
                "evidence_id": e["evidence_id"],
                "label": LATCH_EVENT_LABELS.get(e["action"], e["action"])}
               for e in store.list_latch_events(c.claim_id) if e["action"] != "rerun"]
    events.sort(key=lambda e: e["ts"])
    return {
        "claim_id": c.claim_id,
        "statement": c.statement,
        "t0_evidence_ids": c.t0_evidence_ids,
        "t1_evidence_ids": c.t1_evidence_ids,
        "status": c.status,
        "reason": c.reason,
        "voided": c.voided,
        "voided_at": c.voided_at,
        "last_confirmed_at": c.last_confirmed_at,      # 续命时间戳(§5.4)
        "validity_basis": c.validity_basis,            # 续命写的新有效性依据(§5.4)
        "timeline": events,
    }


@app.get("/api/claims")
def api_claims() -> dict:
    store = _store()
    return {
        "question": _state["question"],
        "claims": [_claim_to_dict(store, c) for c in _state["claims"]],
        "trajectory": str(_state["trajectory"]) if _state["trajectory"] else None,
        "running": _state["running"],
        "latch": _state["latch"],
    }


@app.post("/api/import")
def api_import() -> dict:
    """docket 导入(Workflow):只读 statement 与 t0_evidence_ids,不做新调查。"""
    docket = load_docket(DEMO_DOCKET)
    _state["claims"] = docket.claims
    _state["question"] = docket.question  # 单一真相:data/t0_docket.json
    return {"imported": len(docket.claims)}


@app.post("/api/reverify")
def api_reverify() -> JSONResponse:
    """主按钮「开始复验」:端到端真主链(Lead 裸循环 + 规则闸),轨迹落盘。

    整轮跑完(W3 起)进 HumanLatch:图在收尾节点 interrupt,红/黄灯主张进待审清单,
    复验单顶部出「待人工」横幅(轮次级单 interrupt,一次 resume 传整个决定列表)。
    """
    if _state["running"]:
        return JSONResponse({"error": "已有复验在进行中"}, status_code=409)
    if not _state["claims"]:
        api_import()
    _state["running"] = True
    try:
        runner = Runner(_store())
        result = runner.run(list(_state["claims"]))
        _state["trajectory"] = result.trajectory_path
        rnd = _latch().enter_round(_state["claims"])  # 无红/黄灯则 thread_id=None 直接完成
        _state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    finally:
        _state["running"] = False
    return JSONResponse({
        "claims": [_claim_to_dict(_store(), c) for c in _state["claims"]],
        "trajectory": str(result.trajectory_path),
        "retrieval_used": result.retrieval_used,
        "steps_by_claim": result.steps_by_claim,
        "decoding": result.decoding.__dict__,
        "latch": _state["latch"],
    })


class DecideRequest(BaseModel):
    thread_id: str
    decisions: list[dict] = []


@app.post("/api/latch/decide")
def api_latch_decide(req: DecideRequest) -> JSONResponse:
    """人审批量提交(同步 def):Command(resume=整个决定列表)恢复 interrupt,execute 落档。"""
    if _state["latch"].get("thread_id") != req.thread_id:
        return JSONResponse({"error": "该轮人审不存在或已提交(刷新复验单查看最新状态)"}, status_code=409)
    try:
        latch = _latch()
        results = latch.decide(req.thread_id, req.decisions, claims=list(_state["claims"]))
        latch.prune_rounds()  # 轮次 checkpoint 留最近 5 个(ADR-0006 §9,业务侧删行)
    except HumanLatchError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    _state["latch"] = dict(EMPTY_LATCH)
    return JSONResponse({"results": results, "claims": [_claim_to_dict(_store(), c) for c in _state["claims"]],
                         "latch": _state["latch"]})


class RerunRequest(BaseModel):
    claim_id: str


@app.post("/api/latch/rerun")
def api_latch_rerun(req: RerunRequest) -> JSONResponse:
    """人点「重跑作废主张」(同步 def,不自动):新 thread 单主张迷你复验,结果挂时间线。"""
    claim = next((c for c in _state["claims"] if c.claim_id == req.claim_id), None)
    if claim is None:
        return JSONResponse({"error": f"未找到主张 {req.claim_id}"}, status_code=404)
    try:
        entry = _latch().rerun(claim)
    except HumanLatchError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return JSONResponse({"entry": entry, "claim": _claim_to_dict(_store(), claim)})


@app.get("/api/latch/status")
def api_latch_status() -> dict:
    """人审轮状态;进程重启后可用 thread_id 从 checkpoint 恢复待审清单(#11 §5.10)。"""
    return {"latch": _state["latch"]}


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
 .claim.voided{opacity:.55;background:#f0f0f2}
 .badge{font-size:12px;font-weight:600;margin-left:8px}
 .reason{font-size:13px;color:#57606a;margin-top:4px;white-space:pre-wrap}
 .ev{font-size:12px;margin-top:4px}
 .ev a{color:#0969da;cursor:pointer;text-decoration:none;margin-right:8px}
 .ev a:hover{text-decoration:underline}
 button.big{background:#1f883d;color:#fff;border:0;border-radius:6px;padding:8px 18px;font-size:15px;cursor:pointer}
 button.big:disabled{background:#9e9e9e;cursor:wait}
 .latch button{margin-right:8px;padding:6px 14px;border-radius:6px;border:1px solid #d0d7de;cursor:pointer}
 .latch button.void{background:#8250df;color:#fff;border-color:#8250df}
 .latch button.rerun{background:#fff;color:#8250df}
 .latch button.renew{background:#1a7f37;color:#fff;border-color:#1a7f37}
 /* 已选待提交态:与 .renew 同特异性且靠后,才能盖过按钮本色(卡片在 .latch 内) */
 .latch button.picked,#banner button.picked{background:#fff8c5;border-color:#d4a72c;color:#8250df;cursor:default}
 #banner{background:#fff8c5;border:1px solid #d4a72c;border-radius:6px;padding:10px 12px;margin-bottom:10px}
 #banner .pend{border-top:1px dashed #d4a72c;margin-top:8px;padding-top:8px}
 #banner .pend .picked{color:#8250df;font-weight:600}
 .doc{background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:10px 14px;margin-bottom:10px}
 .doc .clause{margin:8px 0;padding:6px 8px;border-radius:4px;cursor:pointer}
 .doc .clause:hover{background:#f6f8fa}
 .doc .clause.hit{background:#fff8c5;outline:2px solid #d4a72c}
 mark{background:#fff8c5;padding:1px 3px;border-radius:3px}
 .asof{font-size:11px;color:#fff;background:#57606a;border-radius:4px;padding:1px 6px;margin-right:6px}
 .tabs button{padding:4px 12px;border:1px solid #d0d7de;background:#fff;cursor:pointer}
 .tabs button.on{background:#0a2540;color:#fff}
 #status{font-size:13px;color:#57606a}
 details{margin-top:12px;background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:8px 12px}
 code{background:#eff1f3;padding:1px 5px;border-radius:4px}
 .timeline{font-size:12px;color:#57606a;margin-top:6px;border-top:1px dashed #d0d7de;padding-top:4px}
 .timeline div{margin:2px 0}
 .modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:10}
 .modal .box{background:#fff;border-radius:8px;max-width:520px;margin:14vh auto;padding:18px 22px}
 .modal button{margin-right:10px;padding:8px 16px;border-radius:6px;border:1px solid #d0d7de;cursor:pointer}
 .modal .ok{background:#8250df;color:#fff;border-color:#8250df}          /* 作废确认 */
 .modal .renew-ok{background:#1a7f37;color:#fff;border-color:#1a7f37}     /* 续命确认 */
 .modal select{width:100%;margin-top:6px;padding:6px 8px;border-radius:6px;border:1px solid #d0d7de;
               font-family:ui-monospace,monospace;font-size:12px}
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
<div id="modal" class="modal"><div class="box">
  <p><b>作废确认</b></p>
  <p id="modal-claim" style="color:#57606a"></p>
  <p>作废后重跑不得再绿,确认?</p>
  <button class="ok" onclick="confirmVoid()">确认作废</button>
  <button onclick="closeModal()">取消</button>
</div></div>
<div id="renew-modal" class="modal"><div class="box">
  <p><b>续命确认</b></p>
  <p id="renew-claim" style="color:#57606a"></p>
  <p>续命 = 人主张「该主张在 T1 仍然成立」。必须锚 T1 原文证据(ADR-0006 §4),
     证据从<b>本轮已检索的 T1 块</b>下拉选择,不接受自由填写:</p>
  <select id="renew-evidence"></select>
  <div style="margin-top:12px">
    <button class="renew-ok" onclick="confirmRenew()">确认续命</button>
    <button onclick="previewRenewEvidence()">点回原文核对</button>
    <button onclick="closeRenew()">取消</button>
  </div>
</div></div>
<script>
let STATE = {claims: [], question: "", latch: {thread_id: null, pending: []}};
let CURRENT_ANCHOR = null;  // 用户在右栏当前选中的小节(手动选择优先于证据锚点)
let PENDING_DECISIONS = []; // 本轮已选的人审决定(批量提交)
let MODAL_CLAIM = null;
let RENEW_CLAIM = null;
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
const BADGE = {fresh:["绿 · 仍成立","#1a7f37"],stale:["红 · 已失效","#cf222e"],
               unknown:["灰 · 证据不足","#6e7781"],void:["void · 已作废","#8250df"]};

async function boot(){
  await fetch('/api/import',{method:'POST'});
  const j = await (await fetch('/api/claims')).json();
  STATE = j; renderClaims();
}
function pickedAction(cid){
  const d = PENDING_DECISIONS.find(x=>x.claim_id===cid);
  return d ? d.action : null;
}
function renewOptions(cid){
  // 续命证据来源 = 本轮已检索的 T1 块(ADR-0006 §4 下拉选择,非自由文本)
  const c = STATE.claims.find(x=>x.claim_id===cid);
  return ((c && c.t1_evidence_ids) || []).filter(e=>e.endsWith('@T1'));
}
function renewButton(cid){
  // §5.4 + ADR-0006 §6 交互层:无 evidence_id 续命不可用(前端拦截,后端闸兜底)
  if(pickedAction(cid)==='renew') return '<button class="renew picked" disabled>已选:续命(待提交)</button>';
  if(!renewOptions(cid).length)
    return '<button disabled title="本轮无已检索 T1 原文块,续命不可用">续命</button>';
  return '<button class="renew" onclick="event.stopPropagation();openRenew(&quot;'+cid+'&quot;)">续命</button>';
}
function renderBanner(){
  const el = document.getElementById('banner-wrap');
  const L = STATE.latch || {};
  if(!L.thread_id){ el.innerHTML=''; return; }
  let h = '<div id="banner"><b>待人工</b> · 本轮复验已跑完,'
        + L.pending.length + ' 条红/黄灯主张待人审(轮次级批量审批)';
  for(const p of L.pending){
    const act = pickedAction(p.claim_id);
    h += '<div class="pend"><b>'+esc(p.claim_id)+'</b> '
       + '<span class="badge" style="color:'+(BADGE[p.status]?BADGE[p.status][1]:'#6e7781')+'">'
       + (BADGE[p.status]?BADGE[p.status][0]:p.status)+'</span> '
       + esc(p.statement);
    if(act==='discard'){
      h += ' <span class="picked">已选:作废(待提交)</span>';
    } else {
      h += ' <button class="void" onclick="openVoidConfirm(&quot;'+p.claim_id+'&quot;)">作废</button>';
    }
    h += ' ' + renewButton(p.claim_id) + '</div>';
  }
  h += '<div style="margin-top:10px">'
     + '<button class="void" onclick="submitDecisions()">提交人审决定('
     + PENDING_DECISIONS.length + ' 项)</button> '
     + '<button onclick="submitDecisions(true)">全部搁置,结束本轮</button></div></div>';
  el.innerHTML = h;
}
function renderClaims(){
  const el = document.getElementById('claims');
  let h = '<div id="banner-wrap"></div>';
  h += '<h3 style="margin:4px 0 10px">主张复验单 <span style="font-weight:400;font-size:13px;color:#57606a">'
        + esc(STATE.question||'') + '</span></h3>';
  for(const c of STATE.claims){
    const [label,color] = BADGE[c.status] || BADGE.unknown;
    h += '<div class="claim'+(c.voided?' voided':'')+'" id="c-'+c.claim_id+'" style="border-left-color:'+color+'" '
       + 'onclick="pickClaim(&quot;'+c.claim_id+'&quot;)">'
       + '<b>'+c.claim_id+'</b><span class="badge" style="color:'+color+'">'+label+'</span>';
    if(c.voided) h += '<span class="badge" style="color:#8250df">'+BADGE.void[0]
                    + (c.voided_at?(' · '+esc(c.voided_at)):'') + '</span>';
    if(c.last_confirmed_at) h += '<span class="badge" style="color:#1a7f37">续命 · '
                    + esc(c.last_confirmed_at)+'</span>';
    h += '<div>'+esc(c.statement)+'</div>';
    if(c.reason) h += '<div class="reason">'+esc(c.reason)+'</div>';
    h += '<div class="ev">';
    for(const e of c.t0_evidence_ids||[]) {
      const bare=(e.split('@')[0]||'').split('#'); const asOf=e.split('@')[1]||'T0';
      h += '<a onclick="event.stopPropagation();showSource(&quot;'+bare[0]+'&quot;,&quot;'+bare[1]+'&quot;,&quot;'+asOf+'&quot;)">'+esc(e)+'</a>';
    }
    for(const e of c.t1_evidence_ids||[]) {
      const bare=(e.split('@')[0]||'').split('#'); const asOf=e.split('@')[1]||'T1';
      h += '<a onclick="event.stopPropagation();showSource(&quot;'+bare[0]+'&quot;,&quot;'+bare[1]+'&quot;,&quot;'+asOf+'&quot;)">'+esc(e)+'</a>';
    }
    h += '</div>';
    h += '<div class="latch" style="margin-top:6px">';
    if(c.voided){
      h += '<button class="rerun" onclick="event.stopPropagation();rerunClaim(&quot;'+c.claim_id+'&quot;)">重跑作废主张</button>';
    } else if(c.status==='stale' || c.status==='unknown'){
      h += renewButton(c.claim_id);  // 续命只对人审范围内的红/黄灯主张(fresh 无需续命)
    }
    h += '</div>';
    if(c.timeline && c.timeline.length){
      h += '<div class="timeline">';
      for(const t of c.timeline){
        h += '<div>· '+esc(t.ts)+' '+esc(t.label)
           + (t.evidence_id?(' · 依据 <code>'+esc(t.evidence_id)+'</code>'):'')
           + (t.note?(' — '+esc(t.note)):'')
           + (t.thread_id?(' <code>'+esc(t.thread_id)+'</code>'):'')+'</div>';
      }
      h += '</div>';
    }
    h += '</div>';  // 闭合 .claim 卡片(T9 加时间线时丢了这行,卡片互相嵌套堆积)
  }
  el.innerHTML = h;
  renderBanner();
}
function pickClaim(cid){
  document.querySelectorAll('.claim').forEach(e=>e.classList.remove('sel'));
  document.getElementById('c-'+cid)?.classList.add('sel');
}
function pickClause(anchor){
  document.querySelectorAll('#pane .clause').forEach(e=>e.classList.remove('hit'));
  document.getElementById('anchor-'+anchor)?.classList.add('hit');
  CURRENT_ANCHOR = anchor;
}
async function showSource(docId, anchor, asOf){
  const j = await (await fetch('/api/source/'+encodeURIComponent(docId)+'?as_of='+(asOf||'T1'))).json();
  if(j.error){ document.getElementById('pane').innerHTML = '<p>'+esc(j.error)+'</p>'; return; }
  let h = '<h3>'+esc(j.title)+' <span class="asof">'+j.as_of+'</span> <span class="asof">'+esc(j.source_type)+'</span></h3>';
  h += '<div class="tabs" style="margin-bottom:8px">'
     + '<button class="'+((asOf||'T1')==='T0'?'on':'')+'" onclick="showSource(&quot;'+docId+'&quot;,CURRENT_ANCHOR,&quot;T0&quot;)">T0 签发时</button>'
     + '<button class="'+((asOf||'T1')==='T1'?'on':'')+'" onclick="showSource(&quot;'+docId+'&quot;,CURRENT_ANCHOR,&quot;T1&quot;)">T1 复验时刻</button></div>';
  h += '<div class="doc">';
  for(const s of j.sections){
    const hit = s.anchor === anchor;
    h += '<div class="clause'+(hit?' hit':'')+'" id="anchor-'+s.anchor+'" onclick="pickClause(&quot;'+s.anchor+'&quot;)">'
       + '<code>## '+esc(s.anchor)+'</code>' + esc(s.text.replace('## '+s.anchor,'')) + '</div>';
  }
  h += '</div>';
  CURRENT_ANCHOR = anchor;
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
    STATE.claims = j.claims; STATE.latch = j.latch; PENDING_DECISIONS = [];
    renderClaims();
    document.getElementById('status').textContent =
      '复验完成 · 检索 '+j.retrieval_used+'/24 · 轨迹 '+j.trajectory
      +' · '+j.decoding.model+' temp='+j.decoding.temperature+' '+j.decoding.recorded_at;
  } finally { btn.disabled = false; }
}
function openVoidConfirm(cid){
  MODAL_CLAIM = cid;
  const c = STATE.claims.find(x=>x.claim_id===cid);
  document.getElementById('modal-claim').textContent = cid + ': ' + (c?c.statement:'');
  document.getElementById('modal').style.display = 'block';
}
function closeModal(){ document.getElementById('modal').style.display = 'none'; MODAL_CLAIM = null; }
function confirmVoid(){  // 双重确认弹窗的第二重(§5.3:点作废 → 弹窗「作废后重跑不得再绿,确认?」)
  if(MODAL_CLAIM){
    PENDING_DECISIONS = PENDING_DECISIONS.filter(x=>x.claim_id!==MODAL_CLAIM);
    PENDING_DECISIONS.push({claim_id: MODAL_CLAIM, action: 'discard'});
  }
  closeModal(); renderBanner();
}
function openRenew(cid){
  const opts = renewOptions(cid);
  if(!opts.length) return;  // 前端拦截:无 T1 证据不开放(后端闸兜底,§5.4)
  RENEW_CLAIM = cid;
  const c = STATE.claims.find(x=>x.claim_id===cid);
  document.getElementById('renew-claim').textContent = cid + ': ' + (c?c.statement:'');
  document.getElementById('renew-evidence').innerHTML =
    opts.map(e=>'<option value="'+esc(e)+'">'+esc(e)+'</option>').join('');
  document.getElementById('renew-modal').style.display = 'block';
}
function closeRenew(){ document.getElementById('renew-modal').style.display='none'; RENEW_CLAIM=null; }
function previewRenewEvidence(){  // 续命证据 id 必须可点回(#23 红线:不得凭印象续命)
  const eid = document.getElementById('renew-evidence').value;
  const bare = (eid.split('@')[0]||'').split('#');
  showSource(bare[0], bare[1], eid.split('@')[1]||'T1');
}
function confirmRenew(){
  if(RENEW_CLAIM){
    PENDING_DECISIONS = PENDING_DECISIONS.filter(x=>x.claim_id!==RENEW_CLAIM);
    PENDING_DECISIONS.push({claim_id: RENEW_CLAIM, action:'renew',
                            evidence_id: document.getElementById('renew-evidence').value});
  }
  closeRenew(); renderClaims();
}
async function submitDecisions(settleAll){
  const decisions = settleAll ? [] : PENDING_DECISIONS;
  const j = await (await fetch('/api/latch/decide',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({thread_id: STATE.latch.thread_id, decisions: decisions})})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  STATE.claims = j.claims; STATE.latch = j.latch; PENDING_DECISIONS = [];
  renderClaims();
  // 单条被闸打回不拖垮其余(apply_decisions 语义);打回项带 error_code 如实上屏
  const bad = (j.results||[]).filter(r=>!r.ok);
  document.getElementById('status').textContent = bad.length
    ? '部分人审决定被规则闸打回(该条零写): '+bad.map(r=>r.claim_id+' → '+r.error_code).join('; ')
    : '人审决定已落档(写路径唯一:invalidation_list + latch_log)';
}
async function rerunClaim(cid){
  document.getElementById('status').textContent = '重跑中(新 thread 单主张迷你复验:'+cid +')……';
  const j = await (await fetch('/api/latch/rerun',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({claim_id: cid})})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  const idx = STATE.claims.findIndex(x=>x.claim_id===cid);
  if(idx>=0) STATE.claims[idx] = j.claim;
  renderClaims();
  document.getElementById('status').textContent = '重跑完成:'+j.entry.label
    + (j.entry.note?(' — '+j.entry.note):'') + ' · thread '+j.entry.thread_id;
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
