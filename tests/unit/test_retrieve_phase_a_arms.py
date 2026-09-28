"""#160 陷阱分列与 #164 变换对比。默认路径不调用 LLM。"""

from pathlib import Path

from freshlatch.eval.retrieve_eval import run_transform_compare, run_trap_eval


def test_trap_kinds_are_separate(tmp_path):
    payload = run_trap_eval(
        trap_root=Path("data/traps"),
        trap_gold_path=Path("data/eval/retrieve_traps.json"),
        out_dir=tmp_path,
    )
    text = (tmp_path / "retrieve-traps.md").read_text(encoding="utf-8")
    assert payload["n"] >= 3
    for kind in ("快照取代", "同快照冲突", "元陈述"):
        assert kind in text
    assert "不标成必须当反证命中" in text
    assert "主指标" in text
    assert "Recall@10（陷阱子集）: 1.0000" in text


def test_transform_compare_default_skips_llm(tmp_path):
    payload = run_transform_compare(
        corpus=Path("data/corpus"),
        docket_path=Path("data/t0_docket.json"),
        distractor_path=Path("data/eval/distractor_docket.json"),
        gold_path=Path("data/eval/gold.json"),
        out_dir=tmp_path,
    )
    text = (tmp_path / "retrieve-transform-compare.md").read_text(encoding="utf-8")
    assert "裸 statement" in text and "模板变换" in text and "LLM 臂" in text
    assert "temperature:" in text and "seed:" in text
    assert "不依赖 LLM" in text
    assert payload["llm_record"]["enabled"] is False


def test_llm_arm_records_decoding_and_falls_back(tmp_path):
    def _fail(statement, *, model, temperature, seed):
        raise RuntimeError("模拟改写失败")

    payload = run_transform_compare(
        corpus=Path("data/corpus"),
        docket_path=Path("data/t0_docket.json"),
        distractor_path=Path("data/eval/distractor_docket.json"),
        gold_path=Path("data/eval/gold.json"),
        out_dir=tmp_path,
        llm_rewrite=_fail,
        llm_record={"model": "fake-rewrite", "temperature": 0.0, "seed": 7},
    )
    text = (tmp_path / "retrieve-transform-compare.md").read_text(encoding="utf-8")
    assert "fake-rewrite" in text
    assert "temperature: 0.0" in text
    assert "seed: 7" in text
    assert payload["llm"] == payload["bare"]
