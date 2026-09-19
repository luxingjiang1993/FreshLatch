"""PROTOTYPE(ui_streamlit)— 复验单 UI 糙样,Streamlit 报告式,静态假数据。

运行:streamlit run prototypes/ui_streamlit/app.py → http://127.0.0.1:8501
这是 throwaway 代码,回答工单 #4 的「Streamlit 形态长什么样」,不是生产代码。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fake_data import CLAIMS, DOCS_T0, DOCS_T1, TRACE  # noqa: E402

BADGE = {"fresh": "🟢 仍成立", "stale": "🔴 已失效", "unknown": "⚪ 证据不足"}

st.set_page_config(page_title="FreshLatch 复验单 PROTOTYPE", layout="wide")

st.title("FreshLatch 复验单")
st.caption("🚧 SYNTHETIC DEMO · 合成语料,非真实客户数据 · PROTOTYPE")

if st.button("▶ 开始复验", type="primary"):
    st.info("PROTOTYPE:这里触发一次完整复验 Run(W1 实现)")

left, right = st.columns([2, 3])

with left:
    st.subheader("主张列表")
    sel = st.radio(
        "点击主张 → 右侧点回 T0/T1 原文",
        [f'{c["id"]}  {BADGE[c["verdict"]]}  {c["text"]}' for c in CLAIMS],
        label_visibility="collapsed",
    )
    cid = sel.split()[0]
    claim = next(c for c in CLAIMS if c["id"] == cid)
    st.markdown(f"**判定理由**:{claim['reason']}")

    with st.expander("工具轨迹(展开,非首页)"):
        for t in TRACE:
            st.markdown(f"`{t['t']}` **{t['actor']}** `{t['tool']}` {t['args']} — {t['note']}")

with right:
    st.subheader(f"{cid} 原文点回")
    st.markdown("**T0 签发时快照**")
    for did, quote in claim["evidence"]:
        text = DOCS_T0.get(did)
        if text:
            st.markdown(f"`T0` **{did}** " + text.replace(quote, f"**:red-background[{quote}]**"))
    st.markdown("**T1 复验时刻快照**")
    for did, quote in claim["evidence"]:
        text = DOCS_T1.get(did)
        if text:
            st.markdown(f"`T1` **{did}** " + text.replace(quote, f"**:red-background[{quote}]**"))

    st.divider()
    st.markdown("**人审(HumanLatch)**")
    c1, c2 = st.columns(2)
    deprecate = c1.button("作废", key=f"dep-{cid}")
    ev = st.text_input("续命必须带 T1 evidence_id(如 D12)", key=f"ev-{cid}")
    renew = c2.button("续命", key=f"ren-{cid}")
    if renew and not ev:
        st.error("续命必须带 T1 evidence_id")
    elif deprecate or renew:
        st.success(json.dumps({"claim_id": cid,
                               "action": "deprecate" if deprecate else "renew",
                               "evidence_id": ev}, ensure_ascii=False))
