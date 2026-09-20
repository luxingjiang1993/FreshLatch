"""W4 验收编排器:一条命令跑完所有机器可执行项,人工项留档待填。

阶段(pre-registration 判据已锁定于 docs/evidence/w4/checklist.md,本脚本不改判据):
  0. 预检:.env / DASHSCOPE_API_KEY、语料、金标、db(缺则自动 ingest)
  1. P2+J1 机器层:金标 runner N=1(temperature=0)
  2. J2 机器层:3 seed × 非零温度(默认 0.7),逐 seed 一遍;按主张计有效反证条数
  3. J5:假绿对照 control
  4. 汇编:reports/ 报告 + raw JSON(进 git)+ docs/evidence/w4/ 材料骨架
  5. J4 准备:repro-check.md 写入「本会话基准」数字,供 AFK 冷启动会话对照

人工项(脚本不碰,结尾打印清单):J1 人点回 + 两段录屏、J2 ②语义复核(抽 2 条)、
J3-4/P4 真人盲看复述、checklist 签字、CI 绿确认(推 main 后看 Actions)。

用法:python scripts/run_w4_acceptance.py [--seeds 11 22 33] [--temperature 0.7]
          [--skip-j2] [--skip-control] [--db data/freshlatch.db] [--out reports]
触发纪律:烧 LLM 额度,由人在判据锁定后按下(执行环境登记先填 checklist 头部)。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from dotenv import find_dotenv, load_dotenv  # noqa: E402

from freshlatch.eval.control import run_control  # noqa: E402
from freshlatch.eval.report import console_summary, write_outputs  # noqa: E402
from freshlatch.eval.runner import run_gold  # noqa: E402
from freshlatch.llm import DecodingParams  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402

GOLD = REPO_ROOT / "data" / "eval" / "gold.json"
DOCKET = REPO_ROOT / "data" / "t0_docket.json"
EVIDENCE = REPO_ROOT / "docs" / "evidence" / "w4"
MUST_STALE = json.loads(GOLD.read_text(encoding="utf-8"))["must_stale"]


# -- 阶段 0:预检 ------------------------------------------------------------


def preflight(db_path: Path) -> SQLiteStore:
    load_dotenv(find_dotenv(usecwd=True))
    if not os.getenv("DASHSCOPE_API_KEY"):
        sys.exit("预检失败:未找到 DASHSCOPE_API_KEY(.env 或环境变量)——验收运行由人触发,先配 key。")
    for p in (GOLD, DOCKET, REPO_ROOT / "data" / "corpus"):
        if not p.exists():
            sys.exit(f"预检失败:缺少 {p}")
    if not db_path.exists():
        print(f"[预检] {db_path} 不存在,自动 ingest …")
        subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "ingest_corpus.py"),
                        "--db", str(db_path)], check=True, cwd=REPO_ROOT)
    return SQLiteStore(db_path)


# -- 机器层判据汇总 ------------------------------------------------------------


def j1_machine_summary(raw: dict) -> tuple[bool, list[str]]:
    """point_back_j1 表:8 条非豁免全命中 = 机器层过(必要不充分,人点回才算数)。"""
    rows = []
    ok = True
    for cid, pb in sorted(raw["point_back_j1"].items(), key=lambda kv: int(kv[0][1:])):
        if pb["exempt"]:
            rows.append(f"| {cid} | 豁免(无 T1 原文) | — |")
            continue
        hit = "✅" if pb["hit"] else "❌"
        ok = ok and pb["hit"]
        rows.append(f"| {cid} | {pb['expected_anchor']} | {hit} |")
    return ok, rows


def j2_machine_summary(raw: dict) -> tuple[int, list[str]]:
    """按主张计机器层有效反证条数(①可点回 + ③锚对齐;②代理另列,终判归人工)。"""
    checks = raw["counterevidence_j2"]
    valid = [cid for cid in MUST_STALE if checks[cid] and checks[cid][0]["valid_machine"]]
    rows = []
    for cid in MUST_STALE:
        c = checks[cid][0]
        rows.append(f"| {cid} | {'✅' if c['pointable'] else '❌'} | {'✅' if c['anchor_aligned'] else '❌'} "
                    f"| {'✅' if c['causal_sentence_proxy'] else '❌'} | {'✅' if c['valid_machine'] else '❌'} |")
    return len(valid), rows


def guardrail_ok(raw: dict) -> bool:
    return all(all(v) for v in raw["fresh_guardrail_j2"].values())


# -- 阶段 4/5:材料汇编 ---------------------------------------------------------


def assemble(args: argparse.Namespace, *, gold_raw: dict, j2_raws: list[dict],
             control_raw: dict | None) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    j1_ok, j1_rows = j1_machine_summary(gold_raw)
    j2_counts = [j2_machine_summary(r)[0] for r in j2_raws]
    j2_hits = [n >= 1 for n in j2_counts]  # 该 seed 遍是否出现 ≥1 条机器层有效反证
    machine_stop = sum(j2_hits) >= 2  # 停止条件的机器层读数(②终判归人工)

    machine_md = [
        f"# W4 机器层执行结果(自动生成 {now[:19]}Z)",
        "",
        "> 本文件由 scripts/run_w4_acceptance.py 生成,只含机器可执行判据;"
        "人工判据(J1 人点回/录屏、J2②语义复核、J3-4 复述测试)以 checklist.md 签字为准。",
        "",
        "## P2/J1 金标运行(N=1,temperature=0)",
        "",
        f"- raw JSON: 见 reports/(report-*.json,kind=gold_run,runs=1)",
        f"- 机器层点回 8/8: {'✅' if j1_ok else '❌'}(必要不充分,人点回才算数)",
        "",
        "| claim_id | 登记锚段落 | 判定证据命中 |", "|---|---|---|",
        *j1_rows,
        "",
        "## J2 有效反证机器层(按主张计;②语义终判归人工复述复核)",
        "",
        "| seed | must_stale 机器层有效反证条数 | 该遍 ≥1 条 |",
        "|---|---|---|",
    ]
    for seed, r, n, hit in zip(args.seeds, j2_raws, j2_counts, j2_hits):
        machine_md.append(f"| {seed} | {n}/4 | {'✅' if hit else '❌'} |")
    machine_md += [
        "",
        f"- 停止条件机器层读数(≥2/3 遍出现 ≥1 条): {'✅ 达成' if machine_stop else '❌ 未达成'}"
        "——最终以人工②复核后判定为准",
        f"- 反向护栏(must_fresh 无机器层有效反证): {'✅' if guardrail_ok(gold_raw) else '❌'}",
        "",
        "### J2 逐 seed 明细(N=1 各一遍)",
    ]
    for seed, r in zip(args.seeds, j2_raws):
        _, rows = j2_machine_summary(r)
        machine_md += ["", f"seed={seed}:", "",
                       "| claim_id | ①可点回 | ③锚对齐 | ②代理 | 机器层有效 |", "|---|---|---|---|---|",
                       *rows]
    if control_raw is not None:
        machine_md += [
            "",
            "## 假绿对照(control)",
            "",
            f"- must_stale 假绿 {len(control_raw['false_green_must_stale'])}/4;"
            f"对照成立: {'✅' if control_raw['control_pass'] else '❌'}",
            f"- must_unknown 盲判绿: {len(control_raw['blind_green_must_unknown'])} 条"
            f"({', '.join(control_raw['blind_green_must_unknown']) or '无'})",
        ]
    (EVIDENCE / "machine-results.md").write_text("\n".join(machine_md) + "\n", encoding="utf-8")

    # 假绿对照摘录(J5 材料)
    if control_raw is not None:
        (EVIDENCE / "false-green-control.md").write_text("\n".join([
            "# 假绿对照结果(J5,机器层自动摘录)",
            "",
            f"> 生成 {now[:19]}Z;完整 raw JSON 见 reports/(kind=control_run)。",
            "",
            f"- 对照成立(must_stale 全判 alive): {'✅' if control_raw['control_pass'] else '❌'}",
            f"- must_stale 假绿: {', '.join(control_raw['false_green_must_stale']) or '无'}",
            f"- must_unknown 盲判绿: {', '.join(control_raw['blind_green_must_unknown']) or '无'}",
            "",
            "| claim_id | 基线判定 |", "|---|---|",
            *[f"| {cid} | {r['verdict']} |" for cid, r in
              sorted(control_raw["results"].items(), key=lambda kv: int(kv[0][1:]))],
            "",
            "人工补录:对照 prompt 红线人工复核一句(模板与红线单测已机器盯死,此处留确认签名):",
            "复核人:______  日期:______",
        ]) + "\n", encoding="utf-8")

    # P1–P5 预检留档骨架(P2 机器层已跑;P1/P4/P5 待人工)
    (EVIDENCE / "p1-p5-precheck.md").write_text("\n".join([
        "# W3 预检 P1–P5 执行留档",
        "",
        f"> 生成 {now[:19]}Z;P2/P3 为机器层结果,其余待人工执行后补录。",
        "",
        "| # | 预检项 | 通过线 | 结果 |",
        "|---|---|---|---|",
        "| P1 | 点回冒烟:随机 2 条主张 T1 点回,anchor 命中且高亮可见 | 2/2 | ⏳ 待人工(点哪两条、是否命中高亮,记此处) |",
        f"| P2 | 金标 runner 试跑 N=1,console 摘要 + 报告落 reports/ | 跑通,不看分数 | ✅ 机器层跑通(见 reports/ 与 machine-results.md) |",
        "| P3 | 红线单测 CI 绿 | CI 绿 | ⏳ 推 main 后看 Actions(测试本身已绿:pytest 全套本地通过) |",
        "| P4 | 盲看首测:真人盲看 3 分钟 + 一句话定位 + 探针 | 记录即过 | ⏳ 待真人(原话记此处) |",
        "| P5 | Critic 派驻冒烟:合法/非法 focus 各一次 | 非法值回列词表、计步;结论回吐 Lead | ⏳ 待人工(可 UI 操作或写临时脚本驱动) |",
        "",
        "P4 盲看原话:______",
        "",
        "P4 探针回答:______",
        "",
        "P1 点回记录:______",
        "",
        "P5 派驻记录:______",
    ]) + "\n", encoding="utf-8")

    # J4 复现抽查底稿:本会话基准数字,AFK 会话冷启动重跑后对照填入
    last_matrix = gold_raw["per_run"][-1]["matrix"]
    (EVIDENCE / "repro-check.md").write_text("\n".join([
        "# J4 复现抽查记录(闸层逐位复现;判定层按文档化容差)",
        "",
        f"> 生成 {now[:19]}Z。**本表「基准」列由编排器写入(本会话);"
        "AFK 会话须冷启动(新会话、新进程)重跑 `run` N=1 后填「复现」列并做容差判定。**",
        "",
        "## 执行环境(两次运行各自登记)",
        "",
        "| 项 | 基准(本会话) | 复现(AFK 会话) |",
        "|---|---|---|",
        f"| 运行时间(UTC) | {gold_raw['recorded_at']} | ______ |",
        f"| 模型版本 | {gold_raw['decoding']['model']} | ______ |",
        f"| temperature / seed | {gold_raw['decoding']['temperature']} / {gold_raw['decoding']['seed']} | ______ |",
        "",
        "## 闸层(逐位复现:must_* 零违例)",
        "",
        "| 项 | 基准 | 复现 | 逐位一致 |",
        "|---|---|---|---|",
        f"| 判定字典(decisions) | {json.dumps(gold_raw['per_run'][-1]['decisions'], ensure_ascii=False, sort_keys=True)} | ______ | ______ |",
        "",
        "## 判定层(文档化容差:矩阵条数一致;单条判定翻转记背离并人查)",
        "",
        "| 项 | 基准 | 复现 | 容差内 |",
        "|---|---|---|---|",
        f"| 每桶命中条数 | {json.dumps(last_matrix['hits'], sort_keys=True)} | ______ | ______ |",
        f"| 漏判条数 | {json.dumps({b: len(m) for b, m in last_matrix['misses'].items()}, sort_keys=True)} | ______ | ______ |",
        "",
        "违例级背离(must_stale 被判 fresh 等):______(有则人查,记录处置)",
        "",
        "容差判定人:______ 日期:______",
        "",
        "> qwen-flash 是活托管端点,跨会话复现只能近似,此限制为留档声明(§4.7)。",
    ]) + "\n", encoding="utf-8")

    # README 状态刷新(登记目录由本目录 README 承载)
    (EVIDENCE / "README.md").write_text("\n".join([
        "# W4 验收证据目录(docs/evidence/w4/)",
        "",
        "目录登记即 J5 判据的一部分(ADR-0007 后果)。全部材料 commit;录屏 mp4 不进 git(体积),本地留档、检查表记路径。",
        "",
        "| 文件 | 内容 | 状态 |",
        "|---|---|---|",
        "| `checklist.md` | 锁定判据检查表(§7.4 底稿,头部锁定语) | ✅ 已落(W4 验收前锁定);逐项签字待终审 |",
        "| `machine-results.md` | 机器层执行结果(P2/J1 表/J2 三 seed/对照/护栏,自动生成) | ✅ 已生成(以 checklist 签字为准) |",
        "| `restatement.md` | 复述测试记录:盲看原话 + 探针回答 + 判定(W4 与 W12 共用仪器) | ⏳ 待真人盲看(P4/J3) |",
        "| `repro-check.md` | AFK 会话复现抽查:基准列已写入,待冷启动会话填复现列 | ⏳ 待抽查(J4) |",
        "| `false-green-control.md` | 假绿对照结果摘录(机器层已填,人工复核签名留空) | ✅ 机器层;⏳ 人工签名 |",
        "| `p1-p5-precheck.md` | W3 预检 P1–P5 留档(P2 机器层✅;P1/P4/P5 待人工) | ⏳ 待人工补录 |",
        "| `reports/report-<date>.md` + raw JSON | 金标运行记录(含 decoding 参数,进 git) | ✅ 编排器落盘(每 seed 一份) |",
        "| 录屏 mp4(本地) | J1 一镜到底点回录屏;J3 红线复核录屏 | ⏳ 待录制,路径登记进 checklist |",
    ]) + "\n", encoding="utf-8")


# -- 主流程 -------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="W4 验收编排器(机器可执行项一次跑完)")
    ap.add_argument("--seeds", type=int, nargs=3, default=[11, 22, 33],
                    help="J2 三个 seed(各跑一遍,默认 11 22 33)")
    ap.add_argument("--temperature", type=float, default=0.7,
                    help="J2 显式非零温度(temp=0 时 seed 是摆设,§7.4)")
    ap.add_argument("--skip-j2", action="store_true")
    ap.add_argument("--skip-control", action="store_true")
    ap.add_argument("--db", default="data/freshlatch.db")
    args = ap.parse_args()

    if args.temperature <= 0 and not args.skip_j2:
        sys.exit("J2 采样场景必须显式非零温度(temp=0 时 seed 是摆设,三遍相同结果 = 假信心,§7.4)")

    store = preflight(REPO_ROOT / args.db)

    print("== P2/J1:金标 runner N=1(temperature=0) ==")
    gold_raw = run_gold(store, None, gold_path=GOLD, docket_path=DOCKET, runs=1,
                        decoding=DecodingParams(temperature=0.0))
    print(console_summary(gold_raw))
    md, js = write_outputs(gold_raw, REPO_ROOT / "reports")
    print(f"  -> {md.name}, {js.name}")

    j2_raws: list[dict] = []
    if not args.skip_j2:
        for seed in args.seeds:
            print(f"== J2:seed={seed} temperature={args.temperature} ==")
            raw = run_gold(store, None, gold_path=GOLD, docket_path=DOCKET, runs=1,
                           decoding=DecodingParams(temperature=args.temperature, seed=seed))
            print(console_summary(raw))
            j2_raws.append(raw)
            md, js = write_outputs(raw, REPO_ROOT / "reports")
            print(f"  -> {md.name}, {js.name}")

    control_raw = None
    if not args.skip_control:
        print("== J5:假绿对照 ==")
        control_raw = run_control(store, None, gold_path=GOLD, docket_path=DOCKET)
        print(console_summary(control_raw))
        md, js = write_outputs(control_raw, REPO_ROOT / "reports")
        print(f"  -> {md.name}, {js.name}")

    assemble(args, gold_raw=gold_raw, j2_raws=j2_raws, control_raw=control_raw)

    print("\n== 机器层完成。剩余人工动作 ==")
    for item in (
        "1. J1:人逐条点回 8 主张(机器表见 machine-results.md,必要不充分)+ 一镜到底录屏,路径记入 checklist",
        "2. J2:真人抽 2 条复述复核②(机器三 hard 已过线项),checklist J2 表签字",
        "3. J3:红线录屏复核 + 真人盲看复述测试,原话落 restatement.md",
        "4. J4:新开 AFK 会话冷启动重跑 run N=1,按 repro-check.md 基准列对照填复现列",
        "5. P1/P4/P5:点回冒烟、盲看首测、Critic 派驻冒烟,补录 p1-p5-precheck.md",
        "6. 推 main 看 CI 绿(P3),checklist.md 全部签字后 commit",
    ):
        print(f"  {item}")


if __name__ == "__main__":
    main()
