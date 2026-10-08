"""提示词正文未写。自动核验已按一致那句实现。默认入口不发请求。"""

from __future__ import annotations

from pathlib import Path

from freshlatch.eval import patch_events_formal as formal
from freshlatch.models import MODEL_REGISTRY

ROOT = Path(__file__).resolve().parents[2]
GAPS = ROOT / "docs" / "evidence" / "patch-events" / "PROMPT-AND-VERIFY-GAPS.md"
_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")


def test_default_entry_does_not_send(monkeypatch, capsys):
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)
    seen: list[str] = []

    def wrapped(key, default=None):
        seen.append(str(key))
        return None

    monkeypatch.setattr("os.getenv", wrapped)

    def blocked(*_args, **_kwargs):
        raise AssertionError("默认入口不得构造样本或发请求")

    monkeypatch.setattr(formal, "construct_samples", blocked)
    monkeypatch.setattr(formal, "run_formal", blocked)
    assert MODEL_REGISTRY["default_llm"].temperature == 0
    assert MODEL_REGISTRY["judge_qwen"].temperature == 0
    assert MODEL_REGISTRY["judge_deepseek"].temperature == 0
    assert MODEL_REGISTRY["judge_kimi"].temperature == 0.6
    assert formal.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for key in _SECRET_ENV:
        assert key not in seen


def _status_rows(text: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] == "事项" or set(cells[1]) <= {"-", ":"}:
            continue
        rows.append((cells[0], cells[1], cells[2], cells[3]))
    return rows


def test_gap_note_lists_sentences_that_block_prompt_and_verifier():
    text = GAPS.read_text(encoding="utf-8")
    assert "状态：C、T、B1 的 rewrite 与 B2 的 claim 已有可发送正文。" in text
    for sentence in (
        "C 的提示词不放证据。预注册写的是无证据改写。",
        "四臂各一份提示词，不共用一份再加约束。做法表是把四臂分开的。",
        "核验函数只看现在已经传入的臂、`claim_id`、`after_text`、`evidence_id`、`evidence_text`。",
        "入库检查已经在核验前面做完。",
        "模型输出是纯文本。生成阶段要 `after_text`，B2 的 claim 阶段要 `claim_text`。不要求模型直接输出 JSON 或 diff。",
        "T 的证据只用请求里已有的 `evidence_text`。提示词里不再检索。",
        "无法修改时不另设失败标记。缺 `after_text` 或 `void` 已经算生成失败。",
        "`score` 不另定范围。已有规则仍是有分就按分从高到低，同分按 `claim_id`。",
        "claim 是一句纯文本，只陈述要改什么，不带 diff。",
        "diff 是后一阶段从 `before_text` 到 `after_text` 的差异，不在 claim 阶段输出。",
        "`after_text` 去掉首尾空白后，和所绑 `evidence_text` 逐字相同才算一致，否则核验不过。",
        "支撑和矛盾不另判。",
        "不是预注册原文。",
        "2026-10-08",
        "高分不代表放行，也不代表拒绝。score 继续为空，不把 score 当结果。放行只使用已经写好的 decision。",
        "逐字相同则过，不同则不过，只多了首尾空白仍过。",
        "`score` 为空。",
        "不新编任务、角色或评分规则。",
        "补定 draft，不是预注册原文",
        "根据下面给出的 before_text、上一阶段的 claim_text，以及请求里已经有的 evidence_text，改写一句纯文本。这一句是 after_text。claim_text 不是 after_text。不要输出 diff 标记。提示词不再检索。",
        "不规定分数刻度。",
        "四臂生成用的模型温度是 0。补定，2026-10-08。不是预注册原文。",
        "根据下面给出的 before_text，改写一句纯文本。补定，2026-10-09。不是预注册原文。",
        "不把 2026-10-08 的补定写成预注册原文。",
    ):
        assert sentence in text
    rows = _status_rows(text)
    assert rows
    for item, status, date, blocks in rows:
        assert status in {"已定", "补定", "留空"}
        if status == "补定":
            if item == "根据下面给出的 before_text，改写一句纯文本。":
                assert date == "2026-10-09"
            elif item in {"B2 diff 段提示词", "高分代表放行还是拒绝"}:
                assert date == "draft"
            else:
                assert date == "2026-10-08"
            assert blocks == ""
        elif status == "留空":
            assert blocks
            assert date == ""
        else:
            assert date == ""
            assert blocks == ""
    by_item = {item: (status, date, blocks) for item, status, date, blocks in rows}
    assert by_item["claim 是一句纯文本，diff 不在 claim 阶段输出"] == ("补定", "2026-10-08", "")
    assert by_item["一致是去掉首尾空白后的逐字相同，支撑和矛盾不另判"] == ("补定", "2026-10-08", "")
    assert by_item["高分代表放行还是拒绝"] == ("补定", "draft", "")
    assert by_item["before_text 写进 C、T、B1 和 B2 的 claim 提示词"] == ("补定", "2026-10-08", "")
    assert by_item["B1 带上请求里已经有的 evidence_text"] == ("补定", "2026-10-08", "")
    assert by_item["B2 的 claim 也带上这份 evidence_text"] == ("补定", "2026-10-08", "")
    assert by_item["四臂生成温度是 0"] == ("补定", "2026-10-08", "")
    assert by_item["C、T、B1 的 rewrite 与 B2 的 claim 有可发送正文"] == ("补定", "2026-10-08", "")
    assert by_item["根据下面给出的 before_text，改写一句纯文本。"] == ("补定", "2026-10-09", "")
    assert by_item["T/B1 同 after 再分叉（共用一次 rewrite，闸分叉）"] == ("补定", "2026-10-08", "")
    assert by_item[
        "若 after_text 要对齐所绑 evidence_text，输出必须与 evidence_text 去掉首尾空白后逐字相同"
    ] == ("补定", "2026-10-08", "")
    assert {item: blocks for item, status, _date, blocks in rows if status == "留空"} == {}
    for closed in (
        "没有一句规定提示词删掉这两段，还是留着但禁止使用。",
        "没有一句规定 rewrite 阶段各写一份，还是共用一份。",
        "没有一句规定自动核验在这道闸之外还要看什么。",
        "没有一句规定模型看到的是一行 JSON、纯文本，还是 diff。",
        "没有一句规定提示词只根据给定 T1 chunk 改写，还是先按检索模式取 chunk 再改写。",
        "没有一句规定提示词要求模型在无法修改时输出的标记。",
        "没有一句规定分数的范围、高分是否更该放行，或没有分数时如何排序。",
        "没有一句定义 claim 与 `before_text` 的差别",
        "没有一句定义 diff 相对 `after_text` 的形状。",
        "没有一句把「不过」写成可执行谓词。",
        "没有一句规定一致是子串包含、同一数字，还是别的关系。",
        "没有一句说自动核验复用这两句，也没有一句说不复用。",
        "claim 相对 `before_text` 是什么，diff 相对 `after_text` 是什么。未定。",
        "「一致」「支撑」「矛盾」怎么比。未定。",
        "高分代表放行还是拒绝。未定。",
        "高分代表放行还是拒绝。留空。",
        "没有一句规定高分代表放行还是拒绝。",
        "高分代表放行还是拒绝仍留空",
        "输出是 JSON、纯文本还是 diff。",
        "T 的证据是请求里现成的还是提示词里再检索。",
        "无法修改时模型回什么。",
        "`score` 的范围和方向。",
        "仍然空着的六句",
        "不规定一致、支撑、矛盾的算法。",
        "因此没有可调用的自动核验函数。",
        "这次不锁这类例子。",
        "没有可调用的自动核验器",
        "不锁定生成温度",
        "不把生成温度写成 0，也不写成已锁定。",
        "正式入口不把温度补成 0。",
        "`default_llm.temperature` 为空",
        "不写四臂提示词正文。",
        "状态：正文未写",
        "指示正文仍留空",
        "提示词正文这次不写",
        "不是可发送的提示词正文。",
    ):
        assert closed not in text
    assert "你是修改核对员" not in text
    assert (ROOT / "src" / "freshlatch" / "eval" / "patch_events_verify.py").is_file()
