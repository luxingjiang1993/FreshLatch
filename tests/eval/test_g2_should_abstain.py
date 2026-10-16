"""G2-01: GOLD-TABLE-v0 拒答行为夹具。表驱动,离线。

合成 CI 夹具。脚本假 LLM / InMemoryStore / 已合 Runner 与 HumanLatch。
不调用付费 LLM,不读 data/eval/gold.json,不改 src/。
夹具绿不等于注册 G1/A1 过线,不等于 RESULT-Y 乙,不等于 SESOI。
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.evidence import CITE_OUTSIDE_REGISTRY
from freshlatch.guardrails import Guardrails
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.numeric_gate import REASON_NUMERIC_MISMATCH
from freshlatch.roles.conflict_evidence import REASON_CONFLICTING_EVIDENCE
from freshlatch.roles.loop import ABSTENTION_REASONS
from freshlatch.roles.retrieve_sufficiency import REASON_INSUFFICIENT_EVIDENCE
from freshlatch.runner import Runner
from freshlatch.store.base import Chunk, Document, InMemoryStore
from freshlatch.store.sqlite_store import SQLiteStore

REPO = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "g2_should_abstain.json"
GOLD = REPO / "docs/ops/GOLD-TABLE-v0.md"
OPS = REPO / "docs/ops/拒答行为夹具.md"

_ROW_IDS = (
    "G2-IE-01",
    "G2-CR-01",
    "G2-NM-01",
    "G2-CF-01",
    "G2-RN-01",
    "G2-OK-01",
)

_DO_NOT_TOUCH = (
    "src/freshlatch/store/base.py",
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/neural-rerank/summary.json",
    "docs/evidence/neural-rerank/per-query.json",
    "data/eval/gold.json",
    "data/eval/guard_should.json",
    "data/eval/cite_sentence.json",
    "data/eval/temporal_new_over_old.json",
    ".github/workflows/ci.yml",
    "requirements.txt",
    "requirements-eval-neural-rerank.txt",
    "pyproject.toml",
)

_ALLOWED_DIFF = {
    "tasks/G2-01.md",
    "tasks/G2-02.md",
    "docs/ops/GOLD-TABLE-v0.md",
    "docs/ops/拒答行为夹具.md",
    "tests/eval/fixtures/g2_should_abstain.json",
    "tests/eval/test_g2_should_abstain.py",
}

_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_g2_{_tc_counter}",
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
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
        self.calls = 0

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self.calls += 1
        if not self._script:
            raise AssertionError("脚本已尽,测试不得再调用 LLM")
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


class _FixtureStore(InMemoryStore):
    """按构造时给定的块返回,不走嵌入,不打网。"""

    def __init__(self, hits: list[Chunk]) -> None:
        super().__init__()
        self._hits = list(hits)

    def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None):
        self.last_retrieval_mode = "bm25"
        self.last_rerank_mode = "none"
        return list(self._hits)


class _Hit:
    def __init__(self, status: str, reason_code: str | None, surface: str, *, green: bool | None = None):
        self.status = status
        self.reason_code = reason_code
        self.surface = surface
        self.green = green


def _load() -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["version"] == "v0"
    assert payload["counted_as_pass"] is False
    rows = payload["rows"]
    assert [row["id"] for row in rows] == list(_ROW_IDS)
    return payload


def _refusal_codes(rows: list[dict]) -> list[str]:
    return [row["expected"] for row in rows if row["label"] != "must_not_abstain"]


def _chunk(clause_id: str, text: str) -> Chunk:
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
        tokens=12,
    )


def _claim(claim_id: str, statement: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        statement=statement,
        t0_evidence_ids=["fix-memo#p1"],
        dimension="competitor_pricing",
    )


def _aud(payload: dict) -> _Msg:
    return _Msg(content=json.dumps(payload, ensure_ascii=False))


def _lead_tool_results(events: list[dict], tool: str) -> list[dict]:
    return [
        event["result"]
        for event in events
        if event.get("type") == "lead_step" and event.get("tool") == tool
    ]


def _bind(store: _FixtureStore, chunks: list[Chunk]) -> _FixtureStore:
    if not chunks:
        return store
    store.add_document(
        Document(
            doc_id="fix-memo",
            as_of="T1",
            source_type="public",
            title="备忘",
            doc_version="v1",
            checksum="",
            full_text="\n".join(chunk.text for chunk in chunks),
        ),
        chunks,
    )
    return store


def _run_lead(store: _FixtureStore, claim: Claim, script: list, tmp_path: Path):
    llm = _ScriptLLM(script)
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    result = runner.run([claim], trajectory_dir=tmp_path)
    assert llm._script == []
    return result, runner


def _from_reverify(result, runner, claim_id: str) -> _Hit:
    refused = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    status = result.decisions[claim_id].status
    surface = result.trajectory_path.read_text(encoding="utf-8")
    return _Hit(status, refused.get("reason_code"), surface)


def _refuse_script(claim_id: str, evidence_ids: list[str]) -> list:
    return [
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": claim_id,
            "status": "fresh",
            "evidence_ids": evidence_ids,
        })]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="不得写 fresh"),
    ]


def _run_ie(tmp_path: Path) -> _Hit:
    """零 hits。同 RAG-01 判定出口:不得 fresh,reason=insufficient_evidence。"""
    claim_id = "c-g2-ie"
    evidence_id = "fix-memo#p1@T1"
    result, runner = _run_lead(
        _FixtureStore([]),
        _claim(claim_id, "专业版定价仍为 299 元/席/月"),
        _refuse_script(claim_id, [evidence_id]),
        tmp_path,
    )
    hit = _from_reverify(result, runner, claim_id)
    assert hit.reason_code == REASON_INSUFFICIENT_EVIDENCE
    assert hit.reason_code in ABSTENTION_REASONS
    return hit


def _run_cr(tmp_path: Path) -> _Hit:
    """cite 不在本轮 registry。同 FC-CITE:不得 fresh,reason=cite_outside_registry。"""
    claim_id = "c-g2-cr"
    cited = _chunk("p1", "T1 原文确认条款 p1 定价仍为 299,仍可点回。")
    other = _chunk("p2", "T1 原文确认条款 p2 定价仍为 299,仍可点回。")
    outside = "ghost-doc#p9@T1"
    result, runner = _run_lead(
        _bind(_FixtureStore([cited, other]), [cited, other]),
        _claim(claim_id, "专业版定价仍为 299 元/席/月"),
        _refuse_script(claim_id, [outside]),
        tmp_path,
    )
    hit = _from_reverify(result, runner, claim_id)
    assert hit.reason_code == CITE_OUTSIDE_REGISTRY
    assert hit.reason_code in ABSTENTION_REASONS
    assert "recorded" not in _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    return hit


def _run_nm(tmp_path: Path) -> _Hit:
    """假 quote。同 B-01:不得 fresh,reason=numeric_mismatch。"""
    claim_id = "c-g2-nm"
    evidence_id = "fix-memo#p1@T1"
    span = "T1 原文把专业版定价改写成 199 元/席/月。"
    chunk = _chunk("p1", span)
    result, runner = _run_lead(
        _bind(_FixtureStore([chunk]), [chunk]),
        _claim(claim_id, "专业版定价仍为 299 元/席/月"),
        _refuse_script(claim_id, [evidence_id]),
        tmp_path,
    )
    hit = _from_reverify(result, runner, claim_id)
    assert hit.reason_code == REASON_NUMERIC_MISMATCH
    assert hit.reason_code in ABSTENTION_REASONS
    return hit


def _run_cf(tmp_path: Path) -> _Hit:
    """互斥 @T1 对。同 B-02:只引用较顺一侧也不得 fresh。"""
    claim_id = "c-g2-cf"
    left_id = "fix-memo#p1@T1"
    smooth = "T1 原文确认专业版月费仍为 299 元/席/月。"
    other = "T1 原文确认专业版月费已改为 199 元/席/月。"
    chunks = [_chunk("p1", smooth), _chunk("p2", other)]
    result, runner = _run_lead(
        _bind(_FixtureStore(chunks), chunks),
        _claim(claim_id, "专业版月费仍为 299 元/席/月"),
        _refuse_script(claim_id, [left_id]),
        tmp_path,
    )
    hit = _from_reverify(result, runner, claim_id)
    assert hit.reason_code == REASON_CONFLICTING_EVIDENCE
    assert hit.reason_code in ABSTENTION_REASONS
    return hit


def _run_rn(tmp_path: Path) -> _Hit:
    """无 evidence_id 的续命。同 test_renew 无证据路径,不用 UI disabled 字符串。"""
    claim_id = "c-g2-rn"
    doc_id = "t0-competitor-notes"
    chunk = Chunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}-p2",
        clause_id="p2",
        title="竞品笔记",
        text="T1:竞品客单价仍显著高于我们。",
        source_type="competitor",
        as_of="T1",
        doc_version="v2",
        checksum="",
        tokens=20,
    )
    store = SQLiteStore(tmp_path / "freshlatch.db")
    store.add_document(
        Document(
            doc_id=doc_id,
            as_of="T1",
            source_type="competitor",
            title="竞品笔记",
            doc_version="v2",
            checksum="",
            full_text=chunk.text,
        ),
        [chunk],
    )
    claim = Claim(
        claim_id=claim_id,
        statement="竞品客单价仍显著高于我们",
        status="stale",
        reason="T1 竞品降价至我们 70%",
    )
    latch = HumanLatch(store, tmp_path / "checkpoints.db")
    rnd = latch.enter_round([claim])
    results = latch.decide(rnd.thread_id, [{"claim_id": claim_id, "action": "renew"}])
    assert results[0]["ok"] is False
    assert results[0]["error_code"] == "RENEW_NO_EVIDENCE"
    assert claim.status == "stale"
    assert claim.last_confirmed_at is None
    with store._conn() as conn:
        logged = conn.execute(
            "SELECT action FROM latch_log WHERE claim_id=?",
            (claim_id,),
        ).fetchall()
    assert logged == []
    return _Hit(
        claim.status,
        results[0]["error_code"],
        results[0]["error_code"],
        green=False,
    )


def _run_ok(tmp_path: Path) -> _Hit:
    """足证据对照。同 B-01 match:fresh,且轨迹不含上表拒答码。"""
    claim_id = "c-g2-ok"
    evidence_id = "fix-memo#p1@T1"
    statement = "专业版定价仍为 299 元/席/月"
    span = "T1 原文确认专业版定价仍为 299 元/席/月。"
    chunk = _chunk("p1", span)
    result, runner = _run_lead(
        _bind(_FixtureStore([chunk]), [chunk]),
        _claim(claim_id, statement),
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": claim_id,
                "status": "fresh",
                "evidence_ids": [evidence_id],
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
    recorded = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert recorded.get("reason_code") not in _refusal_codes(_load()["rows"])
    assert recorded["recorded"]["status"] == "fresh"
    surface = result.trajectory_path.read_text(encoding="utf-8")
    return _Hit(result.decisions[claim_id].status, recorded.get("reason_code"), surface, green=True)


_RUNNERS = {
    "G2-IE-01": _run_ie,
    "G2-CR-01": _run_cr,
    "G2-NM-01": _run_nm,
    "G2-CF-01": _run_cf,
    "G2-RN-01": _run_rn,
    "G2-OK-01": _run_ok,
}


def test_fixture_matches_gold_table_v0():
    """夹具六行的 id / label / expected 与金标表 v0 同一行。"""
    payload = _load()
    lines = [line for line in GOLD.read_text(encoding="utf-8").splitlines() if line.startswith("| G2-")]
    assert len(lines) == 6
    assert "grade_ambiguous" not in "".join(lines)
    assert "grade_incorrect_exhausted" not in "".join(lines)
    for row, line in zip(payload["rows"], lines, strict=True):
        assert row["id"] in line
        assert row["label"] in line
        if row["label"] == "must_not_abstain":
            assert row["expected"] == "（不得误判为上表码）"
            assert "不得误判为上表码" in line
        elif row["label"] == "must_abstain":
            assert f"`{row['expected']}`" in line
            assert row["expected"] in ABSTENTION_REASONS
        else:
            assert row["label"] == "must_block_renew"
            assert row["expected"] == "RENEW_NO_EVIDENCE"
            assert f"`{row['expected']}`" in line
            assert row["wired"] == "human_latch_no_evidence"


def test_ops_one_pager_names_command_and_negations():
    """G2-02:一页纸含跑法、表 v0、三句否写。"""
    text = OPS.read_text(encoding="utf-8")
    assert "pytest tests/eval/test_g2_should_abstain.py" in text
    assert "v0" in text
    for row_id in _ROW_IDS:
        assert row_id in text
    assert "夹具绿 ≠ 注册 G1/A1 过线" in text
    assert "夹具绿 ≠ RESULT-Y 乙" in text
    assert "夹具绿 ≠ SESOI" in text
    assert "counted_as_pass" in text


@pytest.mark.parametrize("row", _load()["rows"], ids=_ROW_IDS)
def test_g2_row(row, tmp_path):
    """表驱动:该拒的行命中 expected;对照行不发出这些码。"""
    runner = _RUNNERS.get(row["id"])
    if runner is None:
        pytest.fail(f"{row['id']} 没有接到已有机制。缺接线时不得改 src/,应在本行 xfail 并写明原因")
    hit = runner(tmp_path)
    if row["label"] == "must_abstain":
        assert hit.status != "fresh"
        assert hit.reason_code == row["expected"]
        assert row["expected"] in hit.surface
    elif row["label"] == "must_block_renew":
        assert hit.green is False
        assert hit.status != "fresh"
        assert hit.reason_code == row["expected"]
        assert row["expected"] in hit.surface
    else:
        assert row["label"] == "must_not_abstain"
        assert hit.status == "fresh"
        for code in _refusal_codes(_load()["rows"]):
            assert code not in hit.surface


def _git_base_ref() -> str | None:
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


def test_do_not_touch_and_ci_still_collects_eval():
    """未改 ci.yml / floors / gold / requirements / src。pytest tests/ 已覆盖本文件。"""
    ci = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python -m pytest tests/" in ci
    rel = FIXTURE.relative_to(REPO).as_posix()
    assert rel.startswith("tests/")
    assert not rel.startswith("data/exp/x1/")
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
    # -z 避免中文路径被 core.quotepath 编成八进制引号,白名单才能逐字对比。
    diff = subprocess.run(
        ["git", "diff", "-z", "--name-only", base],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        pytest.skip("无法对 base 做 git diff,跳过 Do-not-touch git 路径检查")
    changed = [part.strip().replace("\\", "/") for part in diff.stdout.split("\0") if part.strip()]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
    assert not any(path.startswith("src/") for path in changed)
    assert not any(path.startswith("data/exp/x1/") for path in changed)
    assert not any(path.startswith("data/eval/") for path in changed)
    if changed:
        assert set(changed) <= _ALLOWED_DIFF
