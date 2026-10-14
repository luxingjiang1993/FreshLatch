"""L4-B-03: 审计面主张句可点回 T1 句 id。支撑句与反对句分列。

TestClient 读 HTML,不开浏览器,不调用付费 LLM。
偏移方案只认句 id。夹具轨迹只放在本文件生成的 tmp 路径。
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.claim_span import (
    SENTENCE_SCHEME,
    build_claim_span_event,
    split_sentences,
)
from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.runner import Runner
from freshlatch.sheet import project_audit
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, Chunk, InMemoryStore

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_ID = "fix-memo#p1@T1"
OPPOSE_ID = "fix-memo#p2@T1"
CLAIM_TEXT = "专业版月费为 99 元。"
OPPOSE_TEXT = "专业版月费已改为 79 元。"
SUPPORT_ANCHOR = f"{EVIDENCE_ID}#s0"
OPPOSE_ANCHOR = f"{OPPOSE_ID}#s1"

_DO_NOT_TOUCH = (
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/neural-rerank/summary.json",
    "docs/evidence/neural-rerank/per-query.json",
    "data/eval/guard_should.json",
    "data/eval/cite_sentence.json",
    "data/eval/temporal_new_over_old.json",
    "data/eval/gold.json",
    "src/freshlatch/latch/pipeline.py",
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    saved = {
        "trajectory": appmod._state.get("trajectory"),
        "claims": list(appmod._state.get("claims") or []),
        "running": appmod._state.get("running"),
        "latch": dict(appmod._state.get("latch") or appmod.EMPTY_LATCH),
    }
    appmod._state["trajectory"] = None
    appmod._state["claims"] = []
    appmod._state["running"] = False
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    try:
        yield TestClient(appmod.app)
    finally:
        appmod._state["trajectory"] = saved["trajectory"]
        appmod._state["claims"] = saved["claims"]
        appmod._state["running"] = saved["running"]
        appmod._state["latch"] = saved["latch"]


def _write_jsonl(path: Path, events: list[dict]) -> None:
    lines = [json.dumps(event, ensure_ascii=False) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _span(
    evidence_id: str,
    sentence_id: str,
    text: str,
    role: str,
) -> dict:
    return {
        "role": role,
        "evidence_id": evidence_id,
        "sentence_id": sentence_id,
        "anchor": f"{evidence_id}#{sentence_id}",
        "text": text,
    }


def _claim_event(
    claim_id: str,
    claim_text: str,
    *,
    support: list[dict] | None = None,
    oppose: list[dict] | None = None,
    unsupported: bool = False,
    scheme: str = SENTENCE_SCHEME,
) -> dict:
    return {
        "type": "claim_span",
        "claim_id": claim_id,
        "claim_text": claim_text,
        "sentence_scheme": scheme,
        "unsupported": unsupported,
        "support": list(support or []),
        "oppose": list(oppose or []),
    }


def _card(html: str, claim_id: str) -> str:
    marker = f'data-claim-id="{claim_id}"'
    assert marker in html
    return html.split(marker, 1)[1].split("</li>", 1)[0]


def test_sentence_split_keeps_decimal_and_drops_heading():
    """句 id 切句:小数点不切,块标题不进句子。"""
    assert split_sentences("毛利 12.5%。下一句。") == ["毛利 12.5%。", "下一句。"]
    assert split_sentences("## p1\n专业版月费为 99 元。") == ["专业版月费为 99 元。"]
    assert SENTENCE_SCHEME == "sentence_id"


def test_verbatim_sentence_binds_support_only():
    """逐字相同才是支撑。包住主张的更长句不是支撑。多句 stale 不挑反对句。"""
    matched = build_claim_span_event(
        claim_id="c-bind",
        claim_text=CLAIM_TEXT,
        status="fresh",
        evidence_ids=[EVIDENCE_ID],
        blocks={EVIDENCE_ID: f"## p1\n{CLAIM_TEXT}"},
    )
    assert matched["sentence_scheme"] == "sentence_id"
    assert matched["unsupported"] is False
    assert matched["support"] == [
        _span(EVIDENCE_ID, "s0", CLAIM_TEXT, "support"),
    ]
    assert matched["oppose"] == []
    assert "char_start" not in matched

    longer = build_claim_span_event(
        claim_id="c-long",
        claim_text=CLAIM_TEXT,
        status="fresh",
        evidence_ids=[EVIDENCE_ID],
        blocks={EVIDENCE_ID: "T1 原文确认专业版月费为 99 元。"},
    )
    assert longer["support"] == []
    assert longer["unsupported"] is True

    multi = build_claim_span_event(
        claim_id="c-multi",
        claim_text="别的主张。",
        status="stale",
        evidence_ids=[EVIDENCE_ID],
        blocks={EVIDENCE_ID: "第一句反对。第二句也在。"},
    )
    assert multi["oppose"] == []
    assert multi["unsupported"] is True


def test_stale_one_sentence_is_oppose():
    """所引块恰好一句且不是主张句时,记为反对句,不记为支撑。"""
    event = build_claim_span_event(
        claim_id="c-stale",
        claim_text="专业版仍在售。",
        status="stale",
        evidence_ids=[EVIDENCE_ID],
        blocks={EVIDENCE_ID: "T1 原文写明专业版已经停售。"},
    )
    assert event["support"] == []
    assert event["unsupported"] is True
    assert event["oppose"] == [
        _span(EVIDENCE_ID, "s0", "T1 原文写明专业版已经停售。", "oppose"),
    ]


def test_audit_support_span_is_clickable(client, tmp_path):
    """验收 1:一句 claim + 支撑 span,HTML 可点回 evidence id 与句 id。"""
    path = tmp_path / "support.jsonl"
    _write_jsonl(path, [
        _claim_event(
            "c-span",
            CLAIM_TEXT,
            support=[_span(EVIDENCE_ID, "s0", CLAIM_TEXT, "support")],
        ),
    ])
    projected = project_audit(path)
    assert projected["parsed"] is True
    assert projected["claim_spans"][0]["support"][0]["sentence_id"] == "s0"
    assert projected["claim_spans"][0]["support"][0]["anchor"] == SUPPORT_ANCHOR
    assert projected["claim_spans"][0]["unsupported"] is False

    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    card = _card(html, "c-span")
    assert 'class="span-support"' in card
    assert 'data-evidence-id="fix-memo#p1@T1"' in card
    assert 'data-sentence-id="s0"' in card
    assert SUPPORT_ANCHOR in card
    assert "openClaimSpan(this)" in card
    assert f'href="#{SUPPORT_ANCHOR}"' in card
    support, oppose = card.split('class="claim-span-oppose"', 1)
    assert "span-support" in support
    assert "span-oppose" not in support
    assert "无" in oppose
    assert "相关块" not in html
    assert "char_start" not in html


def test_audit_oppose_is_separate_from_support(client, tmp_path):
    """验收 2:反对句与支撑句分列,且都有句级锚。"""
    path = tmp_path / "oppose.jsonl"
    _write_jsonl(path, [
        _claim_event(
            "c-both",
            CLAIM_TEXT,
            support=[_span(EVIDENCE_ID, "s0", CLAIM_TEXT, "support")],
            oppose=[_span(OPPOSE_ID, "s1", OPPOSE_TEXT, "oppose")],
        ),
    ])
    projected = project_audit(path)
    assert [row["sentence_id"] for row in projected["claim_spans"][0]["support"]] == ["s0"]
    assert [row["sentence_id"] for row in projected["claim_spans"][0]["oppose"]] == ["s1"]

    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    card = _card(html, "c-both")
    support, oppose = card.split('class="claim-span-oppose"', 1)
    assert 'class="span-support"' in support
    assert SUPPORT_ANCHOR in support
    assert "span-oppose" not in support
    assert 'class="span-oppose"' in oppose
    assert 'data-sentence-id="s1"' in oppose
    assert OPPOSE_ANCHOR in oppose
    assert "span-support" not in oppose
    assert "相关块" not in html


def test_unsupported_claim_has_no_support_highlight(client, tmp_path):
    """验收 3:unsupported 不画支撑高亮,即使事件里塞了假支撑、旁边仍有命中块。"""
    path = tmp_path / "unsupported.jsonl"
    _write_jsonl(path, [
        {
            "type": "retrieve",
            "query": "月费",
            "claim_id": "c-none",
            "evidence_ids": [EVIDENCE_ID],
            "hits": [{
                "evidence_id": EVIDENCE_ID,
                "scores": {"bm25": 0.5, "dense": None, "rrf": None, "rerank": None},
            }],
        },
        {
            "type": "lead_loop_end",
            "claim_id": "c-none",
            "evidence_ids": [EVIDENCE_ID],
            "grade": None,
            "retry_count": 0,
            "reason_code": "insufficient_evidence",
        },
        _claim_event(
            "c-none",
            "专业版月费为 199 元。",
            unsupported=True,
            support=[_span(EVIDENCE_ID, "s0", "这是假支撑句。", "support")],
        ),
    ])
    projected = project_audit(path)
    assert projected["hits"][0]["evidence_id"] == EVIDENCE_ID
    assert projected["claim_spans"][0]["unsupported"] is True
    assert projected["claim_spans"][0]["support"] == []
    assert projected["unknown_reason"] == "insufficient_evidence"

    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    card = _card(html, "c-none")
    assert 'data-unsupported="true"' in card
    assert 'class="span-support"' not in card
    assert 'class="span-oppose"' not in card
    assert "support-hit" not in card
    assert "这是假支撑句" not in card
    assert "专业版月费为 199 元。" in card
    assert EVIDENCE_ID in html.split('id="audit-hits"', 1)[1].split('id="audit-attribution"', 1)[0]
    assert "0.5" in html
    assert "相关块" not in html


def test_hits_alone_do_not_invent_sentence_anchors(client, tmp_path):
    """只有块级命中时,不生成句锚,也不出现支撑链接。"""
    path = tmp_path / "hits-only.jsonl"
    _write_jsonl(path, [
        {
            "type": "retrieve",
            "query": "只有块",
            "claim_id": "c-hit",
            "evidence_ids": [EVIDENCE_ID],
            "hits": 1,
        },
    ])
    projected = project_audit(path)
    assert projected["claim_spans"] == []
    assert projected["hits"][0]["evidence_id"] == EVIDENCE_ID
    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    assert 'class="span-support"' not in html
    assert 'class="span-oppose"' not in html
    assert "主张句" in html
    assert "无" in html.split('id="audit-claim-spans"', 1)[1].split("</div>", 1)[0]


def test_char_scheme_is_not_rendered(client, tmp_path):
    """字符偏移事件不投影,避免两套方案各做一半。"""
    path = tmp_path / "char.jsonl"
    _write_jsonl(path, [
        _claim_event(
            "c-char",
            CLAIM_TEXT,
            scheme="char",
            support=[{
                "role": "support",
                "evidence_id": EVIDENCE_ID,
                "sentence_id": "s0",
                "text": CLAIM_TEXT,
                "char_start": 0,
                "char_end": 4,
            }],
        ),
    ])
    assert project_audit(path)["claim_spans"] == []
    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    assert 'class="span-support"' not in html
    assert "char_start" not in html


def test_source_api_lists_sentence_ids(client):
    """点回原文的条款带句 id,与切句函数同一序号。"""
    body = client.get("/api/source/t0-competitor-notes?as_of=T1").json()
    section = next(row for row in body["sections"] if row["anchor"] == "p2")
    sentences = section["sentences"]
    assert [row["sentence_id"] for row in sentences] == [
        f"s{index}" for index in range(len(sentences))
    ]
    assert sentences[0]["text"].startswith("复访发现")
    assert "char_start" not in sentences[0]
    assert len(sentences) >= 2


_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_b03_{_tc_counter}",
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(args, ensure_ascii=False),
        ),
    )


class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        dumped = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            dumped["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in self.tool_calls
            ]
        return dumped


class _ScriptLLM:
    """FIFO 脚本。耗尽即失败,避免落到付费客户端。"""

    def __init__(self, script):
        self._script = list(script)

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        if not self._script:
            raise AssertionError("脚本已尽,测试不得再调用 LLM")
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


class _FixtureStore(InMemoryStore):
    def __init__(self, hits: list[Chunk]) -> None:
        super().__init__()
        self._hits = list(hits)

    def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None,
                 patch_id=None, valid_at=None):
        self.last_retrieval_mode = "bm25"
        self.last_rerank_mode = "none"
        return list(self._hits)


def _chunk(text: str, clause_id: str = "p1") -> Chunk:
    return Chunk(
        doc_id="fix-memo",
        chunk_id=f"fix-memo-{clause_id}",
        clause_id=clause_id,
        title="备忘",
        text=text,
        source_type="public",
        as_of="T1",
        doc_version="v1",
        checksum="",
        tokens=8,
    )


def _run(statement: str, span: str, script: list, tmp_path: Path):
    chunk = _chunk(span)
    store = _FixtureStore([chunk])
    store.add_document(
        SimpleNamespace(
            doc_id="fix-memo",
            as_of="T1",
            source_type="public",
            title="备忘",
            doc_version="v1",
            checksum="",
            full_text=span,
        ),
        [chunk],
    )
    llm = _ScriptLLM(script)
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    claim = Claim(
        claim_id="c-b03",
        statement=statement,
        t0_evidence_ids=["fix-memo#p1"],
        dimension="competitor_pricing",
    )
    result = runner.run([claim], trajectory_dir=tmp_path)
    return result, llm


def _events(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _aud(payload: dict) -> _Msg:
    return _Msg(content=json.dumps(payload, ensure_ascii=False))


def test_cite_emit_writes_sentence_span_without_changing_judgment(tmp_path):
    """写入点与 cite_registry_judgment 同次。后者字段不变。逐字句才有支撑。"""
    sentence = "专业版定价仍为 299 元。"
    result, llm = _run(
        sentence,
        sentence,
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": "c-b03",
                "status": "fresh",
                "evidence_ids": [EVIDENCE_ID],
            })]),
            _Msg(tool_calls=[_tc("report_finding", {
                "finding": "按不限方向检索后未见推翻性 T1 证据",
            })]),
            _Msg(content="无反证"),
            _aud({"status": "fresh", "reason": "T1 原文直接支持该定价", "dimension_match": True}),
            _Msg(tool_calls=[_tc("finish_reverify", {})]),
            _Msg(content="复验结束"),
        ],
        tmp_path,
    )
    events = _events(result.trajectory_path)
    judgments = [event for event in events if event.get("type") == "cite_registry_judgment"]
    assert judgments == [{
        "type": "cite_registry_judgment",
        "claim_id": "c-b03",
        "status": "fresh",
        "evidence_ids": [EVIDENCE_ID],
    }]
    spans = [event for event in events if event.get("type") == "claim_span"]
    assert len(spans) == 1
    assert spans[0]["sentence_scheme"] == "sentence_id"
    assert spans[0]["unsupported"] is False
    assert spans[0]["support"][0]["sentence_id"] == "s0"
    assert spans[0]["support"][0]["anchor"] == SUPPORT_ANCHOR
    assert spans[0]["oppose"] == []
    assert "char_start" not in spans[0]
    assert llm._script == []


def test_cite_emit_does_not_fake_support_for_longer_sentence(tmp_path):
    """所引块只是包住主张,不是同一句。轨迹里 unsupported,支撑列表为空。"""
    result, llm = _run(
        "专业版定价仍为 299 元。",
        "T1 原文确认专业版定价仍为 299 元。",
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": "c-b03",
                "status": "fresh",
                "evidence_ids": [EVIDENCE_ID],
            })]),
            _Msg(tool_calls=[_tc("report_finding", {
                "finding": "按不限方向检索后未见推翻性 T1 证据",
            })]),
            _Msg(content="无反证"),
            _aud({"status": "fresh", "reason": "T1 原文直接支持该定价", "dimension_match": True}),
            _Msg(tool_calls=[_tc("finish_reverify", {})]),
            _Msg(content="复验结束"),
        ],
        tmp_path,
    )
    events = _events(result.trajectory_path)
    spans = [event for event in events if event.get("type") == "claim_span"]
    assert spans[0]["unsupported"] is True
    assert spans[0]["support"] == []
    assert spans[0]["oppose"] == []
    assert llm._script == []


def test_cite_emit_stale_one_sentence_oppose(tmp_path):
    """stale 且所引块只有一句时,写入反对句锚,不写支撑链接。"""
    result, llm = _run(
        "专业版定价仍为 299 元。",
        "T1 原文写明专业版已经停售并退出报价单。",
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("mark_stale", {
                "claim_id": "c-b03",
                "reason": "T1 原文写明专业版已经停售并退出报价单,原先仍在售卖的前提被推翻。",
                "evidence_ids": [EVIDENCE_ID],
                "dimension": "competitor_pricing",
            })]),
            _aud({"status": "stale", "reason": "T1 原文推翻仍在售的前提", "dimension_match": True}),
            _Msg(content="复验结束"),
        ],
        tmp_path,
    )
    events = _events(result.trajectory_path)
    judgments = [event for event in events if event.get("type") == "cite_registry_judgment"]
    assert judgments[0]["status"] == "stale"
    assert judgments[0]["evidence_ids"] == [EVIDENCE_ID]
    spans = [event for event in events if event.get("type") == "claim_span"]
    assert spans[0]["support"] == []
    assert spans[0]["unsupported"] is True
    assert spans[0]["oppose"][0]["sentence_id"] == "s0"
    assert spans[0]["oppose"][0]["role"] == "oppose"
    assert llm._script == []
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"


def _git_base_ref() -> str | None:
    """浅克隆没有 origin/main 时返回 None,不 fetch。"""
    candidates = ["origin/main"]
    extra = os.environ.get("GITHUB_BASE_REF", "").strip()
    if extra:
        candidates.append(f"origin/{extra}")
    seen: list[str] = []
    for ref in candidates:
        if ref in seen:
            continue
        seen.append(ref)
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return ref
    return None


def test_do_not_touch_paths_skip_when_base_missing():
    """有 base 时 Do-not-touch 路径不在 diff 里。缺 ref 则跳过,避免 CI exit 128。"""
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
    diff = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if diff.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过 Do-not-touch git 路径检查: "
            + (diff.stderr or "").strip()
        )
    changed = [
        line.strip().replace("\\", "/")
        for line in diff.stdout.splitlines()
        if line.strip()
    ]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
    assert not any(item.startswith("data/exp/x1/") for item in changed)
    assert not any(item.startswith("docs/evidence/neural-rerank/") for item in changed)
