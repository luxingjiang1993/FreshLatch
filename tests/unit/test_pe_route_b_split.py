"""路线 B n=100 写死名单与缺额结果语义。不发模型，不激活正式主跑。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_formal as formal
from freshlatch.eval import patch_events_split as split
from freshlatch.eval.patch_events_construct import QUOTAS

ROOT = Path(__file__).resolve().parents[2]
_ROUTE_B = ROOT / "docs" / "evidence" / "patch-events" / "SPLIT-pe-v2-route-b.json"
_PE_V2 = ROOT / "docs" / "evidence" / "patch-events" / "SPLIT-pe-v2.json"
_PREREG_B = ROOT / "docs" / "evidence" / "patch-events" / "PREREG-B.md"
_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")


@pytest.fixture(autouse=True)
def _drop_keys(monkeypatch):
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)


def test_route_b_split_path_is_hardcoded():
    path = split.route_b_split_path(ROOT)
    assert path == _ROUTE_B
    assert path.name == "SPLIT-pe-v2-route-b.json"
    assert formal._PE_V2_ROUTE_B_SPLIT.as_posix() == "docs/evidence/patch-events/SPLIT-pe-v2-route-b.json"


def test_route_b_n100_confirmed_pilot_excluded_and_quota_unchanged():
    payload = split.load_route_b_manifest(ROOT)
    pe_v2 = json.loads(_PE_V2.read_text(encoding="utf-8"))
    ids = split.load_route_b_formal_n100_ids(ROOT)
    pilot_ids = {row["claim_id"] for row in payload["pilot"]}

    assert payload["protocol"] == "PREREG-B"
    assert "未激活" in payload["status"]
    assert payload["quotas_target"]["n100"] == 100
    assert sum(c + b for c, b in QUOTAS["n100"].values()) == 100
    assert len(ids) == 100
    assert len(set(ids)) == 100
    assert set(ids).isdisjoint(pilot_ids)
    assert ids == [row["claim_id"] for row in pe_v2["n100"]]
    assert payload["gaps"]["n100"] == 0
    assert payload["result_fields"]["语料缺额"] == 0

    prereg = _PREREG_B.read_text(encoding="utf-8")
    assert "| n=100（路线 B 满样本门槛） |" in prereg
    assert "25（12 / 13）" in prereg
    assert "冲甲正式主跑未激活" in prereg
    assert "不得为凑齐改小" not in prereg or "不在本页把配额改小" in prereg


def test_route_b_shortfall_result_fields_and_no_quota_shrink(tmp_path: Path):
    raw = split.load_route_b_manifest(ROOT)
    # 模拟语料缺额：去掉末尾 3 条，配额目标仍为 100，不得改小。
    short = dict(raw)
    short["n100"] = list(raw["n100"][:-3])
    short["counts"] = {
        "pilot": len(short["pilot"]),
        "n100": len(short["n100"]),
        "shortfalls": 3,
    }
    short["gaps"] = {
        "n100": 3,
        "by_stratum": dict(raw["gaps"]["by_stratum"]),
    }
    short["result_fields"] = {"语料缺额": 3}
    short["quotas_target"] = {"n100": 100, "by_stratum": dict(raw["quotas_target"]["by_stratum"])}
    dest = tmp_path / "docs" / "evidence" / "patch-events"
    dest.mkdir(parents=True)
    (dest / "SPLIT-pe-v2-route-b.json").write_text(
        json.dumps(short, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    ids = split.load_route_b_formal_n100_ids(tmp_path)
    fields = split.route_b_result_fields(tmp_path)
    assert len(ids) == 97
    assert fields == {"语料缺额": 3}
    assert short["quotas_target"]["n100"] == 100

    shrunk = dict(short)
    shrunk["quotas_target"] = {"n100": 97, "by_stratum": short["quotas_target"]["by_stratum"]}
    shrunk["gaps"] = {"n100": 0, "by_stratum": short["gaps"]["by_stratum"]}
    shrunk["result_fields"] = {"语料缺额": 0}
    (dest / "SPLIT-pe-v2-route-b.json").write_text(
        json.dumps(shrunk, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="不得改小"):
        split.load_route_b_formal_n100_ids(tmp_path)


def test_route_b_loader_not_in_main_and_default_stays_dark(monkeypatch, capsys):
    source = Path(formal.__file__).read_text(encoding="utf-8")
    assert "load_pe_v2_route_b_formal_n100" in source
    assert "load_pe_v2_route_b_formal_n100()" not in source.split("def main", 1)[1]

    def blocked(*_args, **_kwargs):
        raise AssertionError("默认入口不得构造或加载路线 B 正式集")

    monkeypatch.setattr(formal, "construct_samples", blocked)
    monkeypatch.setattr(formal, "load_pe_v2_route_b_formal_n100", blocked)
    monkeypatch.setattr(formal, "load_pe_v2_formal_n30", blocked)
    assert formal.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_route_b_formal_loader_returns_pinned_n100():
    rows = formal.load_pe_v2_route_b_formal_n100(ROOT)
    assert [row["claim_id"] for row in rows] == split.load_route_b_formal_n100_ids(ROOT)
    assert len(rows) == 100
    assert split.route_b_result_fields(ROOT) == {"语料缺额": 0}
    pilot_ids = set(split.load_pilot_ids(ROOT, split=_ROUTE_B))
    assert {row["claim_id"] for row in rows}.isdisjoint(pilot_ids)
