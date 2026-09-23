"""DEM-5 / #93:检索零命中 UI 强提示。挂复验单 UI 套件(TestClient + 源码红线)。

验收锁:
- retrieve 空命中时 UI 出现强提示
- UI 不自动把主张改成 unknown / 不冒充判定闸
- 旁注标明 unknown 仍须 Lead 显式落档(mark_gap / reverify_claim(unknown))
- 不断言「自动 unknown」;验收措辞不升格为 latch 已证明
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.llm import DecodingParams
from freshlatch.runner import RunContext, RunResult, list_retrieve_zero_hits


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
        "retrieve_zero_hits": [],
    })
    appmod._reset_t1_source(store)
    return TestClient(appmod.app)


# -- 源码/DOM 红线(DEM-5 成交面) ----------------------------------------------------


def test_zero_hit_banner_surface_and_explicit_unknown_note():
    """DEM-5:强提示面在位;旁注标明 unknown 须 Lead 显式落档;禁止升格/自动判定措辞。"""
    html = appmod.HTML_PAGE
    assert 'id="retrieve-zero-hit"' in html
    assert "检索零命中" in html or "零命中" in html
    # 旁注:显式落档路径(mark_gap / reverify_claim(unknown))
    assert "mark_gap" in html
    assert "reverify_claim" in html and "unknown" in html
    assert "显式" in html
    # 不得把 UI 提示写成自动改写判定 / latch 已证明
    assert "自动 unknown" not in html
    assert "自动改成 unknown" not in html
    assert "latch 已证明" not in html
    assert "产品已验证" not in html
    assert "一期测量闭合" not in html


def test_list_retrieve_zero_hits_from_events():
    """事件真源:hits==0 的 retrieve 计入;预算耗尽与有命中不计入。"""
    events = [
        {"type": "retrieve", "query": "无覆盖查询", "as_of": "T1", "used": 1, "hits": 0},
        {"type": "retrieve", "query": "有命中", "as_of": "T1", "used": 2, "hits": 3},
        {"type": "budget", "kind": "retrieval_exhausted", "used": 24},
        {"type": "retrieve", "query": "又一次空", "as_of": "T0", "used": 3, "hits": 0},
        {"type": "claim_result", "claim_id": "c1", "status": "fresh"},
    ]
    zeros = list_retrieve_zero_hits(events)
    assert len(zeros) == 2
    assert zeros[0]["query"] == "无覆盖查询"
    assert zeros[0]["as_of"] == "T1"
    assert zeros[0]["hits"] == 0
    assert zeros[1]["query"] == "又一次空"


# -- API 行为:提示在位、不改写判定 -------------------------------------------------


def test_reverify_exposes_zero_hits_without_auto_unknown(client, monkeypatch, tmp_path):
    """复验返回零命中告警;主张 status 不被 UI/API 层因零命中改写为 unknown。"""
    # 选定合法 T1(合成包),否则 /api/reverify 400
    assert client.post("/api/t1-source/synthetic").status_code == 200
    client.post("/api/import")

    traj = tmp_path / "run-zero.jsonl"
    traj.write_text("{}\n", encoding="utf-8")
    zero = [{"query": "找不到的关键词XYZ", "as_of": "T1", "used": 1, "hits": 0}]

    class _FakeRunner:
        def __init__(self, store, **_kwargs):
            self.store = store
            self.ctx = RunContext(store=store)

        def run(self, claims):
            # 与真 Runner 同构:原地改写传入列表;故意保持 fresh——
            # 证明 UI/API 不会因零命中清单把判定改成 unknown
            for c in claims:
                c.status = "fresh"
                c.t1_evidence_ids = ["doc#p1@T1"]
                c.reason = "有 T1 覆盖(测 UI 不因零命中改写)"
            return RunResult(
                claims=claims,
                decisions={},
                trajectory_path=traj,
                steps_by_claim={c.claim_id: 1 for c in claims},
                retrieval_used=1,
                decoding=DecodingParams(model="mock", temperature=0.0),
                retrieve_zero_hits=list(zero),
            )

    monkeypatch.setattr(appmod, "Runner", _FakeRunner)
    # 短路人审进入:无 pending,不碰 SqliteSaver
    monkeypatch.setattr(
        appmod, "_latch",
        lambda: type("L", (), {
            "enter_round": lambda self, claims: type("R", (), {
                "thread_id": None, "pending": [],
            })(),
        })(),
    )

    r = client.post("/api/reverify")
    assert r.status_code == 200
    body = r.json()
    assert body["retrieve_zero_hits"]
    assert body["retrieve_zero_hits"][0]["hits"] == 0
    assert body["retrieve_zero_hits"][0]["query"] == "找不到的关键词XYZ"
    # 关键断言:不得因零命中把主张改成 unknown
    assert body["claims"], "应有主张投影"
    for c in body["claims"]:
        assert c["status"] == "fresh"
        assert c["status"] != "unknown"

    # /api/claims 投影也暴露告警,供刷新后 UI 仍能画强提示
    proj = client.get("/api/claims").json()
    assert proj["retrieve_zero_hits"]
    assert proj["retrieve_zero_hits"][0]["hits"] == 0
    for c in proj["claims"]:
        assert c["status"] == "fresh"
