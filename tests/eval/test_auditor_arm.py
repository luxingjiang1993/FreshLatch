"""Auditor 判定臂离线评测 harness(I-08,#697)的单测:金标加载校验 / 闸后路由 / 3×3 矩阵
+ false-accept / false-reject + unknown 率 / 报告与协议节。

纪律声明(Anthropic 清单 #1/#2):本文件全部用脚本假 LLM(零付费、零网络),
是 harness 机械正确性层(确定性层);真实判定读数由 CLI 实跑落 docs/evidence/,
不在 CI 内。假件不充当判定臂通过率证据。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval import auditor_arm
from freshlatch.eval.auditor_arm import (
    AuditorArmSample,
    arm_confusion,
    load_auditor_arm_gold,
    load_t1_texts,
    post_gate,
    render_auditor_arm_report,
    run_auditor_arm,
    write_auditor_arm_outputs,
)
from freshlatch.eval.matrix import VERDICTS
from freshlatch.gates.rule_gate import arbitrate_fresh, arbitrate_stale_mark
from freshlatch.roles.auditor import Auditor, AuditorVerdict

GOLD_PATH = Path("data/eval/auditor_arm_gold.json")


class _Msg:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeLLM:
    """脚本假 LLM:按调用顺序吐出预写 JSON;记录收到的消息入档断言用。"""

    def __init__(self, scripted: list[str]) -> None:
        self._scripted = list(scripted)
        self.calls: list[dict] = []

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self.calls.append({"messages": messages, "decoding": decoding})
        if not self._scripted:
            raise AssertionError("FakeLLM 脚本耗尽")
        return _Msg(self._scripted.pop(0))

    def expect_no_more(self) -> None:
        assert not self._scripted, f"脚本未用尽: {self._scripted}"


def _sample(**kw) -> AuditorArmSample:
    base = dict(
        sample_id="s1", claim_id="c1", statement="主张", dimension="d",
        t0_evidence_ids=["t0-x#p2"], bucket="matrix", path="mark_stale",
        gold="stale", human_curated=True, provenance="t",
        lead_status="stale", lead_reason="r", lead_evidence_ids=["t0-x#p2@T1"],
    )
    base.update(kw)
    return AuditorArmSample(**base)


def _load_samples():
    return load_auditor_arm_gold(GOLD_PATH).samples


# -- 金标加载与校验 -------------------------------------------------------------


def test_load_gold_ok():
    data = load_auditor_arm_gold(GOLD_PATH)
    assert data.schema_version == "1"
    assert data.thresholds == {"min_total": 100, "min_human": 30}
    assert len(data.samples) == 14
    assert all(s.human_curated for s in data.samples)
    assert data.protocol_note
    matrix_n = sum(1 for s in data.samples if s.bucket == "matrix")
    assert matrix_n == 12


def test_load_gold_bad_verdict_rejected(tmp_path):
    data = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    data["samples"][0]["gold"] = "alive"
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="gold"):
        load_auditor_arm_gold(p)


def test_load_gold_matrix_path_gold_consistency(tmp_path):
    """matrix 桶:mark_stale 只能配 gold=stale;fresh_attempt 只能配 fresh/unknown。"""
    data = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    data["samples"][0]["gold"] = "fresh"  # c1 是 mark_stale
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="mark_stale"):
        load_auditor_arm_gold(p)


def test_load_gold_fresh_attempt_requires_evidence_for_fresh(tmp_path):
    data = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    for s in data["samples"]:  # 找 c4(fresh_attempt + gold fresh)
        if s["sample_id"] == "c4":
            s["lead_evidence_ids"] = []
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="fresh"):
        load_auditor_arm_gold(p)


# -- T1 文本解析(复用生产 ingest 单一真相) ---------------------------------------


def test_load_t1_texts_resolves_anchor_ids():
    texts = load_t1_texts(Path("data/corpus/t1"))
    eid = "t0-competitor-notes#p2@T1"
    assert eid in texts
    assert "SeaDesk" in texts[eid]
    # 全样本的 lead_evidence_ids 必须都能在 T1 语料解析到(缺了要炸,不静默)
    for s in _load_samples():
        for e in s.lead_evidence_ids:
            assert e in texts, f"{s.sample_id}: {e} 不在 T1 语料"


# -- 闸后路由(生产真值表,不复制逻辑) --------------------------------------------


def test_post_gate_mark_stale_routes_through_arbitrate_stale_mark():
    s = _sample(path="mark_stale", gold="stale")
    assert post_gate(s, AuditorVerdict(status="stale", dimension_match=None)) \
        == arbitrate_stale_mark("stale", None) == ("stale", False)
    assert post_gate(s, AuditorVerdict(status="stale", dimension_match=False)) \
        == arbitrate_stale_mark("stale", False) == ("unknown", True)
    # auditor fresh/unknown 不拦 stale(安全不对称)
    assert post_gate(s, AuditorVerdict(status="fresh")) == ("stale", True)
    assert post_gate(s, AuditorVerdict(status="unknown")) == ("stale", False)


def test_post_gate_fresh_attempt_routes_through_arbitrate_fresh():
    s = _sample(path="fresh_attempt", gold="fresh", lead_status="fresh",
                lead_evidence_ids=["t0-x#p2@T1"])
    assert post_gate(s, AuditorVerdict(status="fresh")) == ("fresh", False)
    assert post_gate(s, AuditorVerdict(status="stale")) == ("stale", False)
    assert post_gate(s, AuditorVerdict(status="unknown")) == ("unknown", False)


# -- 端到端(假 LLM):矩阵 / FA / FR / unknown 率 ---------------------------------


def _run_scripted(samples, scripted, *, t1_texts=None, doctrine="doctrine-x"):
    llm = FakeLLM(scripted)
    raw = run_auditor_arm(
        samples, llm, doctrine=doctrine,
        decoding=None, t1_texts=t1_texts or {},
    )
    llm.expect_no_more()
    return raw


def test_run_records_verdict_and_gate_status_per_sample():
    samples = [_sample(sample_id="s1"), _sample(sample_id="s2", gold="stale")]
    raw = _run_scripted(samples, [
        json.dumps({"status": "stale", "reason": "r1", "dimension_match": True}),
        json.dumps({"status": "unknown", "reason": "r2"}),
    ])
    assert [r["sample_id"] for r in raw["records"]] == ["s1", "s2"]
    assert raw["records"][0]["auditor_status"] == "stale"
    assert raw["records"][0]["gated_status"] == "stale"
    assert raw["records"][1]["auditor_status"] == "unknown"
    assert raw["records"][1]["gated_status"] == "stale"  # auditor unknown 不拦 stale
    assert raw["doctrine_loaded"] is True


def test_run_non_json_fails_closed_to_unknown():
    samples = [_sample(path="fresh_attempt", gold="fresh", lead_status="fresh")]
    raw = _run_scripted(samples, ["<not json>"])
    rec = raw["records"][0]
    assert rec["auditor_status"] == "unknown"
    assert rec["gated_status"] == "unknown"  # arbitrate_fresh(unknown)
    assert "fail-closed" in rec["auditor_reason"]


def test_run_doctrine_fallback_recorded_not_silent():
    samples = [_sample()]
    llm = FakeLLM([json.dumps({"status": "stale"})])
    raw = run_auditor_arm(samples, llm, doctrine=None, decoding=None, t1_texts={})
    assert raw["doctrine_loaded"] is False
    # 不静默降级:报告必须能呈现 fallback 事实(由渲染测试断言字段存在)
    assert "skill_fallback" in raw["records"][0]


def test_arm_confusion_3x3_and_rates():
    samples = [
        _sample(sample_id="s1", gold="stale"),
        _sample(sample_id="s2", claim_id="c2", gold="stale"),
        _sample(sample_id="s3", claim_id="c4", path="fresh_attempt", gold="fresh",
                lead_status="fresh"),
        _sample(sample_id="s4", claim_id="c5", path="fresh_attempt", gold="fresh",
                lead_status="fresh"),
        _sample(sample_id="s5", claim_id="c9", path="fresh_attempt", gold="unknown",
                lead_status="fresh", lead_evidence_ids=[]),
    ]
    # 脚本:stale 样本一个判 stale(命中)、一个判 fresh(FA 原料,mark_stale 路径
    # 闸后仍落 stale——原始判定层才看得到);fresh 样本一个判 fresh(命中)、
    # 一个判 stale(FR);unknown 样本判 unknown(命中)。
    raw = _run_scripted(samples, [
        json.dumps({"status": "stale", "dimension_match": True}),
        json.dumps({"status": "fresh"}),
        json.dumps({"status": "fresh"}),
        json.dumps({"status": "stale"}),
        json.dumps({"status": "unknown"}),
    ])
    m = arm_confusion(raw)
    assert m["n"] == 5
    # 闸后 3×3:gold stale 行 → [fresh 0, stale 2, unknown 0](FA 被闸安全不对称吸收)
    assert m["gated_matrix"]["stale"] == {"fresh": 0, "stale": 2, "unknown": 0}
    # fresh 行 → stale 1(FR),fresh 1
    assert m["gated_matrix"]["fresh"] == {"fresh": 1, "stale": 1, "unknown": 0}
    assert m["gated_matrix"]["unknown"] == {"fresh": 0, "stale": 0, "unknown": 1}
    assert m["false_accept"] == {"count": 0, "rate": 0.0}
    assert m["false_reject"] == {"count": 1, "rate": 0.2}
    assert m["unknown_rate"] == {"count": 1, "rate": 1 / 5}
    # 原始判定层(臂层读数):FA=1(s2 原始判 fresh)
    assert m["raw_matrix"]["stale"]["fresh"] == 1
    for row in m["gated_matrix"].values():
        assert set(row) == set(VERDICTS)
    # 真人子集:全部 human_curated → 与全量矩阵重合(#691 分栏)
    assert m["n_human"] == m["n"]
    assert m["human_matrix"] == m["gated_matrix"]


def test_arm_confusion_sensitivity_bucket_excluded_from_matrix():
    samples = [
        _sample(sample_id="s1", bucket="matrix", gold="stale"),
        _sample(sample_id="c13", bucket="sensitivity", gold="fresh"),
    ]
    raw = _run_scripted(samples, [
        json.dumps({"status": "stale"}),
        json.dumps({"status": "stale", "dimension_match": False}),
    ])
    m = arm_confusion(raw)
    assert m["n"] == 1  # 敏感度探针不进判分矩阵
    assert m["sensitivity"]["c13"]["gated_status"] == "unknown"  # dm=false 打回
    assert m["sensitivity"]["c13"]["auditor_dimension_match"] is False


# -- 报告与协议节 ----------------------------------------------------------------


def test_report_contains_matrix_fa_fr_unknown_and_protocol(tmp_path):
    samples = _load_samples()
    scripted = []
    for s in samples:
        if s.gold == "stale":
            scripted.append(json.dumps({"status": "stale", "reason": "r",
                                        "dimension_match": True}))
        elif s.gold == "fresh":
            scripted.append(json.dumps({"status": "fresh", "reason": "r"}))
        else:
            scripted.append(json.dumps({"status": "unknown", "reason": "r"}))
    t1_texts = load_t1_texts(Path("data/corpus/t1"))
    raw = _run_scripted(samples, scripted, t1_texts=t1_texts)
    md = render_auditor_arm_report(raw)
    assert "3×3" in md
    assert "false-accept" in md
    assert "false-reject" in md
    assert "unknown 率" in md
    # 样本量协议节:阈值 + 未达标声明 + 原因(协议已文档化路径)
    assert "≥100" in md and "≥30" in md
    assert "未达标" in md
    assert "Trust L1" in md
    # 只测不调参声明
    assert "未改" in md and "temperature" in md
    # 敏感度附表不计通过线
    assert "敏感度" in md and "c13" in md
    # 全量 vs 真人子集分栏(#691)
    assert "真人子集" in md
    # 每样本明细表齐全(含真人策展列)
    for s in samples:
        assert s.sample_id in md
    assert "真人策展" in md


def test_write_outputs_md_and_json(tmp_path):
    samples = [_sample()]
    raw = _run_scripted(samples, [json.dumps({"status": "stale"})])
    md_path, json_path = write_auditor_arm_outputs(raw, tmp_path)
    assert md_path.exists() and json_path.exists()
    reread = json.loads(json_path.read_text(encoding="utf-8"))
    assert reread["kind"] == "auditor_arm_run"
    assert reread["records"][0]["gated_status"] == "stale"
    assert "false-accept" in md_path.read_text(encoding="utf-8")


def test_write_outputs_refuses_frozen_dirs(tmp_path):
    raw = _run_scripted([_sample()], [json.dumps({"status": "stale"})])
    # 冻结目录(l4-ev-01-arm-table 等既有证据锚)拒绝写入
    for frozen in ("docs/evidence/l4-ev-01-arm-table", "docs/evidence/temporal-trained-retrieval"):
        with pytest.raises(ValueError, match="冻结|frozen"):
            write_auditor_arm_outputs(raw, Path(frozen) / "sub")
    # 默认落点(新 sibling)允许
    out = tmp_path / "docs" / "evidence" / "auditor-arm-eval"
    md_path, _ = write_auditor_arm_outputs(raw, out)
    assert md_path.exists()


# -- 只测不调参护栏 ---------------------------------------------------------------


def test_harness_uses_production_single_truth():
    """harness 必须复用生产 Auditor / 闸真值表,不得自带副本或改生产常量。"""
    import freshlatch.eval.auditor_arm as aa
    import inspect

    assert aa.Auditor is Auditor
    assert aa.arbitrate_stale_mark is arbitrate_stale_mark
    assert aa.arbitrate_fresh is arbitrate_fresh
    src = inspect.getsource(aa)
    # 不复制真值表逻辑、不碰 UI/服务层
    assert "def arbitrate" not in src
    assert "freshlatch.ui" not in src
    assert "serving" not in src


def test_cli_auditor_arm_defaults_match_production():
    """CLI 默认 decoding 与生产一致(t=0),模型走 resolve_model 不另写死。"""
    from freshlatch.eval.__main__ import build_parser
    from freshlatch.model_profile import resolve_model

    parser = build_parser()
    args = parser.parse_args(["auditor-arm"])
    assert args.temperature == 0.0
    assert args.seed is None
    assert args.gold == "data/eval/auditor_arm_gold.json"
    assert args.out == "docs/evidence/auditor-arm-eval"
    assert resolve_model("default_llm").model  # 生产默认模型可解析(不改动,只读断言)
