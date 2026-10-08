"""pe_v2 公开语料能填满预注册配额。不调用评委，不读密钥。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from freshlatch.eval.patch_events_construct import QUOTAS, STRATA, construct_samples

_ROOT = Path(__file__).resolve().parents[2]
_DOCKET = _ROOT / "data" / "pe_v2_docket.json"
_CORPUS = _ROOT / "data" / "corpus" / "pe_v2"
_MANIFEST = _ROOT / "docs" / "evidence" / "patch-events" / "SPLIT-pe-v2.json"


def _lf(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def test_pe_v2_decision_is_confirmed_after_amendment_3():
    log = _lf(_ROOT / "docs" / "evidence" / "patch-events" / "DECISION-LOG.md").decode("utf-8")
    draft = _ROOT / "docs" / "evidence" / "patch-events" / "DECISION-LOG-pe-v2-DRAFT.md"
    assert not draft.exists()
    amendment = log.index("## 跑数据前偏离 · Amendment 3")
    missing = log.index("## 跑数据前偏离 · 非拒绝类错误记缺失")
    confirmed = log.index("## 跑数据前偏离 · 扩充公开语料")
    assert amendment < missing < confirmed
    section = log[confirmed:]
    assert "决定人：用户（Oriental Ronin，2026-10-08 13:32 UTC+8）" in section
    assert "转录人：Ronin 代理人" in section
    assert "此时尚无 pilot，也尚无正式评委数据" in section
    assert "不改 `PREREG.md`" in section
    assert "日期与条款替换大多取自同一现行文本的两段，而不是新旧版本。" in section
    assert "删除层存在算子伪影：修饰词表含「约」，会从「约定」里删字。" in section


def test_pe_v2_fills_quotas_and_keeps_margin():
    result = construct_samples(_DOCKET, _CORPUS)
    manifest = json.loads(_lf(_MANIFEST).decode("utf-8"))
    assert len(result.pilot) == 15
    assert len(result.n30) == 30
    assert len(result.n100) == 100
    assert not any(item.claim_id == "" for item in result.shortfalls)
    for tier, rows in (
        ("pilot", result.pilot),
        ("n30", result.n30),
        ("n100", result.n100),
    ):
        for name in STRATA:
            correct, bad = QUOTAS[tier][name]
            got_c = sum(
                1
                for row in rows
                if row.record["edit_type"] == name and row.record["construction_gold"] == "正确"
            )
            got_b = sum(
                1
                for row in rows
                if row.record["edit_type"] == name and row.record["construction_gold"] == "坏"
            )
            assert (got_c, got_b) == (correct, bad)
            assert manifest["by_stratum"][tier][name]["gap"] == 0
    assert [row.record["claim_id"] for row in result.pilot] == [
        item["claim_id"] for item in manifest["pilot"]
    ]
    assert [row.record["claim_id"] for row in result.n100] == [
        item["claim_id"] for item in manifest["n100"]
    ]


def test_pe_v2_claims_are_verbatim_and_hashed():
    docket = json.loads(_lf(_DOCKET).decode("utf-8"))
    provenance = json.loads(_lf(_CORPUS / "PROVENANCE.json").decode("utf-8"))
    by_id = {row["claim_id"]: row for row in provenance["claims"]}
    assert len(docket["claims"]) == len(by_id) == 178
    for claim in docket["claims"]:
        claim_id = claim["claim_id"]
        statement = claim["statement"]
        t0 = _lf(_CORPUS / "t0" / f"{claim_id}.md").decode("utf-8")
        assert statement in t0
        row = by_id[claim_id]
        assert row["fetch_time"]
        assert row["license"]
        assert row["t0_source"]["source_url"]
        assert hashlib.sha256(_lf(_CORPUS / "t0" / f"{claim_id}.md")).hexdigest() == row["t0_sha256"]
        assert hashlib.sha256(_lf(_CORPUS / "t1" / f"{claim_id}.md")).hexdigest() == row["t1_sha256"]
        assert row["t0_source"]["offset"] >= 0
    inventory = json.loads(_lf(_MANIFEST).decode("utf-8"))["inventory"]
    for name, block in inventory.items():
        assert block["leftover"] >= 5
        assert block["claims"] * 10 >= block["with_conformal"] * 13
