"""划分清单：重跑逐字节一致，pilot 未结束时不得读取正式集。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_construct import QUOTAS
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

ROOT = Path(__file__).resolve().parents[2]
SPLIT = ROOT / "docs" / "evidence" / "patch-events" / "SPLIT.json"
NOTE = ROOT / "docs" / "evidence" / "patch-events" / "PILOT-NOTE.md"

_EXPECTED_QUOTAS = {
    "pilot": {
        "数值": (2, 2),
        "日期": (2, 2),
        "条款替换": (2, 2),
        "删除": (1, 2),
    },
    "n30": {
        "数值": (4, 4),
        "日期": (4, 4),
        "条款替换": (4, 4),
        "删除": (3, 3),
    },
    "n100": {
        "数值": (12, 13),
        "日期": (12, 13),
        "条款替换": (12, 13),
        "删除": (12, 13),
    },
}


def _canonical(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def test_repeat_render_matches_file_and_hash():
    from freshlatch.eval.patch_events_split import render_manifest

    first = render_manifest()
    second = render_manifest()
    assert first == second
    disk = SPLIT.read_bytes().replace(b"\r\n", b"\n")
    assert disk.decode("utf-8") == first
    assert SPLIT.read_bytes().replace(b"\r\n", b"\n") == disk

    payload = json.loads(first)
    digest = payload.pop("sha256")
    assert hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest() == digest


def test_inventory_ids_gaps_and_disjoint_sets():
    from freshlatch.eval.patch_events_split import load_pilot_ids, render_manifest

    payload = json.loads(render_manifest())
    assert QUOTAS == _EXPECTED_QUOTAS
    assert payload["conformal_reserve"] == "未做"
    assert "校准" not in json.dumps(payload, ensure_ascii=False)
    assert payload["gaps"] == {"pilot": 11, "n30": 28, "n100": 98}
    assert payload["counts"] == {"pilot": 4, "n30": 2, "n100": 2, "shortfalls": 136}
    assert len(payload["shortfalls"]) == 136

    pilot = [(row["claim_id"], row["edit_type"], row["construction_gold"]) for row in payload["pilot"]]
    n30 = [(row["claim_id"], row["edit_type"], row["construction_gold"]) for row in payload["n30"]]
    n100 = [(row["claim_id"], row["edit_type"], row["construction_gold"]) for row in payload["n100"]]
    assert pilot == [
        ("c1", "数值", "坏"),
        ("c10", "数值", "正确"),
        ("c11", "数值", "坏"),
        ("c3", "数值", "正确"),
    ]
    assert n30 == [("c7", "数值", "正确"), ("c9", "数值", "正确")]
    assert n100 == n30
    pilot_ids = {row[0] for row in pilot}
    n30_ids = {row[0] for row in n30}
    n100_ids = {row[0] for row in n100}
    assert pilot_ids.isdisjoint(n30_ids)
    assert pilot_ids.isdisjoint(n100_ids)
    assert n30_ids <= n100_ids
    assert load_pilot_ids(ROOT) == [row[0] for row in pilot]
    assert not NOTE.is_file()


def test_formal_ids_stay_unread_until_pilot_note(tmp_path: Path):
    from freshlatch.eval.patch_events_split import load_formal_ids

    with pytest.raises(RuntimeError, match="pilot 未结束，不得读取正式集") as missing:
        load_formal_ids(tmp_path)
    assert "c7" not in str(missing.value)
    assert "c9" not in str(missing.value)

    folder = tmp_path / "docs" / "evidence" / "patch-events"
    folder.mkdir(parents=True)
    (folder / "SPLIT.json").write_text("not-json c7 c9", encoding="utf-8")
    with pytest.raises(RuntimeError, match="pilot 未结束，不得读取正式集") as corrupt:
        load_formal_ids(tmp_path)
    assert "c7" not in str(corrupt.value)
    assert "c9" not in str(corrupt.value)

    with pytest.raises(RuntimeError, match="pilot 未结束，不得读取正式集") as live:
        load_formal_ids(ROOT)
    assert "c7" not in str(live.value)
    assert "c9" not in str(live.value)

    (folder / "PILOT-NOTE.md").write_text("流程已走完\n", encoding="utf-8")
    (folder / "SPLIT.json").write_text(
        json.dumps(
            {
                "n30": [{"claim_id": "a", "edit_type": "数值", "construction_gold": "正确"}],
                "n100": [
                    {"claim_id": "a", "edit_type": "数值", "construction_gold": "正确"},
                    {"claim_id": "b", "edit_type": "数值", "construction_gold": "坏"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert load_formal_ids(tmp_path) == {"n30": ["a"], "n100": ["a", "b"]}


def test_module_does_not_read_secrets_or_touch_locked_files():
    import freshlatch.eval.patch_events_split as patch_events_split

    text = Path(patch_events_split.__file__).read_text(encoding="utf-8")
    for token in (
        "DASHSCOPE_API_KEY",
        "DEEPSEEK_API_KEY",
        "MOONSHOT_API_KEY",
        "getenv",
        "environ",
        "random",
        "named_streams",
    ):
        assert token not in text
    prereg = ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
    gold = ROOT / "data" / "eval" / "gold.json"
    sample = ROOT / "data" / "corpus" / "t1" / "t0-competitor-notes.md"
    decision = ROOT / "docs" / "evidence" / "patch-events" / "DECISION-LOG.md"
    before = {path: path.read_bytes() for path in (prereg, gold, sample, decision, SPLIT)}
    patch_events_split.render_manifest()
    after = {path: path.read_bytes() for path in (prereg, gold, sample, decision, SPLIT)}
    assert before == after
    base = (ROOT / "src" / "freshlatch" / "store" / "base.py").read_text(encoding="utf-8")
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
