"""#753 LOCAL-P0-DOCTOR-PRECHECK-PARITY:doctor 与 precheck 同根同判。"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.doctor as doctor
import freshlatch.ui.app as appmod
from freshlatch.doctor import check_weights, main
from freshlatch.ui import weight_precheck as wp


def _plant_both(root: Path) -> None:
    for short in ("bge-small-zh-v1.5", "bge-reranker-base"):
        d = root / f"models--BAAI--{short}" / "snapshots" / "rev" / "onnx"
        d.mkdir(parents=True)
        (d / "model.onnx").write_bytes(b"w")


@pytest.fixture()
def no_cache_env(monkeypatch):
    monkeypatch.delenv("FASTEMBED_CACHE_PATH", raising=False)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    yield TestClient(appmod.app)


def test_precheck_cache_dir_resolved_when_env_unset(client, no_cache_env):
    """验收1:未设 env 时 cache_dir 为解析后的临时根字符串,不得为 null。"""
    expected = str((Path(tempfile.gettempdir()) / "fastembed_cache").resolve())
    body = client.get("/api/retrieval/precheck").json()
    assert body["cache_dir"] is not None
    assert isinstance(body["cache_dir"], str)
    assert body["cache_dir"] == expected
    assert body["cache_dir"] == wp.resolved_cache_dir()


def test_doctor_and_precheck_agree_when_only_temp_root_has_weights(
    client, tmp_path, monkeypatch, no_cache_env, capsys,
):
    """验收2:仅解析根有快照 → doctor 与 precheck 同绿,路径一致。"""
    temp_parent = tmp_path / "tmpdir"
    temp_parent.mkdir()
    temp_root = temp_parent / "fastembed_cache"
    _plant_both(temp_root)
    monkeypatch.setattr(wp.tempfile, "gettempdir", lambda: str(temp_parent))
    monkeypatch.setattr(doctor, "check_encoding", lambda streams=None: doctor.CheckResult(
        "UTF-8 编码", True, "测试桩",
    ))

    resolved = wp.resolved_cache_dir()
    assert resolved == str(temp_root.resolve())

    wr = check_weights()
    assert wr.ok is True
    assert resolved in wr.detail

    body = client.get("/api/retrieval/precheck").json()
    assert body["cache_dir"] == resolved
    assert body["cache_dir"] == wr.detail[wr.detail.rfind("(") + 1 : -1]
    assert body["ok"] is True
    assert body["embedding"] is True
    assert body["reranker"] is True

    assert main(["--offline"]) == 0
    out = capsys.readouterr().out
    assert "权重路径" in out
    assert "跳过" in out
    assert "网络可达" in out
    assert resolved in out


def test_doctor_and_precheck_agree_missing_when_only_home_cache(
    client, tmp_path, monkeypatch, no_cache_env,
):
    """验收3:仅 ~/.cache 有快照 → 两者同为缺权重。"""
    temp_parent = tmp_path / "tmpdir"
    temp_parent.mkdir()
    (temp_parent / "fastembed_cache").mkdir()
    home_cache = tmp_path / "home" / ".cache" / "fastembed_cache"
    _plant_both(home_cache)
    monkeypatch.setattr(wp.tempfile, "gettempdir", lambda: str(temp_parent))

    wr = check_weights()
    body = client.get("/api/retrieval/precheck").json()
    assert wr.ok is False
    assert body["ok"] is False
    assert body["embedding"] is False
    assert body["reranker"] is False
    assert body["cache_dir"] == wp.resolved_cache_dir()
    assert wr.ok == body["ok"]


def test_doctor_and_precheck_honor_explicit_env(client, tmp_path, monkeypatch):
    """验收4:显式 FASTEMBED_CACHE_PATH 时两者只认该目录。"""
    explicit = tmp_path / "explicit"
    other = tmp_path / "fastembed_cache"
    _plant_both(other)
    explicit.mkdir()
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(explicit))
    monkeypatch.setattr(wp.tempfile, "gettempdir", lambda: str(tmp_path))

    # 权重只在默认 temp 根 → 显式空目录下两者同为缺
    wr_miss = check_weights()
    body_miss = client.get("/api/retrieval/precheck").json()
    assert wr_miss.ok is False
    assert body_miss["ok"] is False
    assert body_miss["cache_dir"] == wp.resolved_cache_dir()
    assert Path(body_miss["cache_dir"]) == explicit.resolve()

    _plant_both(explicit)
    resolved = wp.resolved_cache_dir()
    assert Path(resolved) == explicit.resolve()
    wr = check_weights()
    body = client.get("/api/retrieval/precheck").json()
    assert wr.ok is True
    assert body["ok"] is True
    assert body["cache_dir"] == resolved
    assert resolved in wr.detail


def test_production_retrieval_mode_untouched():
    """验收5:不改检索默认臂。"""
    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
