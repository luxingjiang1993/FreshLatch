"""HumanLatch 管道实装:LangGraph interrupt + SqliteSaver(ADR-0006)。

图形状(§5.5):START → prepare_review → await_review(interrupt) → execute → END。
- 一轮复验 = 一个 thread_id(`reverify-round-{ts}`),轮次级单 interrupt,resume 值 = 整个决定列表。
- interrupt 前代码幂等、零副作用;全部落档副作用在 execute(= gates/human_latch.apply_decisions)。
- 重跑 = 人点按钮 → 新 thread(`reverify-{claim_id}-{ts}`)单主张迷你复验(Lead+规则闸),
  结果挂 rerun_log 时间线;即使 Lead 判 fresh,规则闸查作废名单强制打回。
- checkpoint 文件独立 `data/checkpoints.db`;同一主张只留最近 5 个 thread(§9,业务侧删行)。
- SqliteSaver 每次 invoke 开关连接(函数内 with):不长期持有 Windows 文件锁(#11 §5.10)。
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, TypedDict

from freshlatch.gates.human_latch import apply_decisions
from freshlatch.models import Claim

CHECKPOINT_KEEP = 5  # 同一主张保留的最近 thread 数(ADR-0006 §9)


class HumanLatchError(Exception):
    """人审管道的可预期违例(端点转 4xx,不转 5xx)。"""


class LatchState(TypedDict, total=False):
    """图状态:只装可序列化纯数据(claim 快照字典,不装 Claim 对象)。"""

    pending: list[dict]   # 待审主张快照 [{claim_id, statement, status, reason}]
    decisions: list[dict]  # resume 传入的整个决定列表
    results: list[dict]    # execute 落档结果


class RerunState(TypedDict, total=False):
    """重跑 thread 的终态(一次复验 = 一个 thread,重跑也不例外):"""

    claim_id: str
    verdict: str
    note: str


@dataclass
class LatchRound:
    """一轮人审的中断态(图停在 interrupt,等人)。"""
    thread_id: str | None
    pending: list[dict] = field(default_factory=list)
    ts: str = ""

    @property
    def waiting(self) -> bool:
        return self.thread_id is not None


def _pending_item(c: Claim) -> dict:
    return {"claim_id": c.claim_id, "statement": c.statement,
            "status": c.status, "reason": c.reason}


def _build_graph(apply_fn: Callable[[list[dict]], list[dict]]):
    """图定义。langgraph 延迟导入:评测/Agent 循环路径零依赖(§0.4.1 图不是 Agent)。"""
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import interrupt

    def prepare_review(state: LatchState) -> dict:
        # 幂等、零副作用:只整理待审清单(红/黄灯 = stale/unknown)
        return {"pending": [p for p in state.get("pending", []) if p.get("status") in ("stale", "unknown")]}

    def await_review(state: LatchState) -> dict:
        # 收尾节点中断:把待审清单抛给复验单;resume 值 = 整个决定列表(轮次级批量,§5.2)
        decisions = interrupt({"pending": state["pending"]})
        return {"decisions": decisions or []}

    def execute(state: LatchState) -> dict:
        # 副作用唯一落点(节点重执行语义下 apply_decisions 幂等:重复 discard 跳过)
        return {"results": apply_fn(state.get("decisions") or [])}

    builder = StateGraph(LatchState)
    builder.add_node("prepare_review", prepare_review)
    builder.add_node("await_review", await_review)
    builder.add_node("execute", execute)
    builder.add_edge(START, "prepare_review")
    builder.add_edge("prepare_review", "await_review")
    builder.add_edge("await_review", "execute")
    builder.add_edge("execute", END)
    return builder


def _build_rerun_graph():
    """重跑线程图:无 interrupt,START → record → END。图只做 checkpoint 容器(图不是 Agent)——
    让「一次复验 = 一个 thread」对重跑也字面成立,checkpoint 供 prune 清理与重启后回溯。"""
    from langgraph.graph import END, START, StateGraph

    def record(state: RerunState) -> dict:
        return {}  # 终态即输入(claim_id/verdict/note),零副作用

    builder = StateGraph(RerunState)
    builder.add_node("record", record)
    builder.add_edge(START, "record")
    builder.add_edge("record", END)
    return builder


class HumanLatch:
    """人审管道入口(UI 端点用):enter_round → decide;rerun → 时间线。"""

    def __init__(self, store, checkpoint_path: str | Path, *, mode: str = "online",
                 reverify_fn: Callable[[Claim], tuple[str, str]] | None = None,
                 now: Callable[[], datetime] | None = None,
                 checksum_fn: Callable[[str, str], str | None] | None = None) -> None:
        self.store = store
        self.checkpoint_path = Path(checkpoint_path)
        self.mode = mode  # online | eval(eval 代码级跳过,ADR-0006 §7)
        self._reverify_fn = reverify_fn  # 测试可注入;默认 Runner 真主链迷你复验
        self._now = now or datetime.now
        # 续命链 checksum 注入点(#23;留位:None = checksum 未启用,闸不拦,同 runner._checksum_fn)
        self._checksum_fn = checksum_fn
        self._claims_by_id: dict[str, Claim] = {}  # enter_round/decide 时绑定的本轮主张表
        self._pending_ids: set[str] = set()  # 本轮待审 id(重跑恢复时从 checkpoint 回填)
        self._run_id: str | None = None  # 本轮 thread,成功人审行可选写入 latch_log.run_id

    # -- 轮次:一轮复验 = 一个 thread -------------------------------------------------

    def enter_round(self, claims: list[Claim], *, ts: str | None = None) -> LatchRound:
        """整轮复验收尾:图跑到 interrupt 并落盘,返回待审清单;无红/黄灯则直接完成。"""
        ts = ts or self._now().strftime("%Y%m%d-%H%M%S")
        if self.mode == "eval":
            return LatchRound(thread_id=None, pending=[], ts=ts)  # 代码级跳过(ADR-0006 §7)
        self._claims_by_id = {c.claim_id: c for c in claims}
        pending = [_pending_item(c) for c in claims if c.status in ("stale", "unknown")]
        self._pending_ids = {p["claim_id"] for p in pending}
        if not pending:
            return LatchRound(thread_id=None, pending=[], ts=ts)
        thread_id = f"reverify-round-{ts}"
        self._run_id = thread_id
        with self._saver() as saver:
            graph = self._graph(saver)
            graph.invoke({"pending": pending}, self._config(thread_id))
        return LatchRound(thread_id=thread_id, pending=pending, ts=ts)

    def decide(self, thread_id: str, decisions: list[dict],
               *, claims: list[Claim] | None = None) -> list[dict]:
        """人审提交:`Command(resume=整个决定列表)` 恢复 interrupt,execute 落档。

        claims:进程重启后恢复场景重绑主张表(UI 重新导入 docket 后传入);
        缺省时沿用 enter_round 绑定的表。待审清单也从 checkpoint 回填校验。
        """
        if self.mode == "eval":
            raise HumanLatchError("eval 模式代码级跳过 HumanLatch(ADR-0006 §7)")
        self._run_id = thread_id
        if claims is not None:
            self._claims_by_id = {c.claim_id: c for c in claims}
        if not self._pending_ids:
            state = self.review_state(thread_id)
            if state:
                self._pending_ids = {p["claim_id"] for p in state["pending"]}
        from langgraph.types import Command  # langgraph 面收口在本模块(§0.4.1 隔离纪律)

        with self._saver() as saver:
            graph = self._graph(saver)
            result = graph.invoke(Command(resume=decisions), self._config(thread_id))
        return result.get("results", [])

    def review_state(self, thread_id: str) -> dict | None:
        """进程重启后查询 thread 是否还在等人(只看 get_state,不恢复;#11 §5.10)。"""
        if self.mode == "eval" or not self.checkpoint_path.exists():
            return None
        with self._saver() as saver:
            graph = self._graph(saver)
            snap = graph.get_state(self._config(thread_id))
        if not snap.next:
            return None
        return {"thread_id": thread_id, "next": list(snap.next),
                "pending": (snap.values or {}).get("pending", [])}

    # -- 重跑:单主张迷你复验(人点按钮触发,不自动;§5.3)------------------------------

    def rerun(self, claim: Claim, *, ts: str | None = None) -> dict:
        """人点「重跑作废主张」:新 thread 只重跑该主张,结果挂时间线。

        规则闸查作废名单:即使 Lead 判 fresh 也强制打回(Runner._finalize 已含该闸)。
        """
        if self.mode == "eval":
            raise HumanLatchError("eval 模式代码级跳过 HumanLatch(ADR-0006 §7)")
        if claim.claim_id not in set(self.store.list_invalidation()):
            raise HumanLatchError(f"{claim.claim_id} 不在作废名单,仅作废主张可重跑")
        ts = ts or self._now().strftime("%Y%m%d-%H%M%S")
        thread_id = f"reverify-{claim.claim_id}-{ts}"
        reverify_fn = self._reverify_fn or self._default_reverify
        verdict, note = reverify_fn(claim)
        # 新开 LangGraph thread 落终态 checkpoint(CONTEXT.md 重跑定义:一次复验 = 一个 thread)
        with self._saver() as saver:
            graph = _build_rerun_graph().compile(checkpointer=saver)
            graph.invoke({"claim_id": claim.claim_id, "verdict": verdict, "note": note},
                         self._config(thread_id))
        nth = len(self.store.list_reruns(claim.claim_id)) + 1
        self.store.log_rerun(ts, claim.claim_id, thread_id, verdict, nth, note)
        self.store.log_latch(ts, claim.claim_id, "rerun", evidence_id=None, actor="human")
        self.prune(claim.claim_id)
        return {"claim_id": claim.claim_id, "thread_id": thread_id, "verdict": verdict,
                "nth": nth, "note": note, "label": self.timeline_label(verdict, nth)}

    @staticmethod
    def timeline_label(verdict: str, nth: int) -> str:
        if verdict == "fresh":
            return f"重跑后转绿(第 {nth} 次)"  # 理论上闸已拦截;防御性文案
        return f"重跑后仍红(第 {nth} 次)"

    def _default_reverify(self, claim: Claim) -> tuple[str, str]:
        """真主链迷你复验:Lead 裸循环 + 规则闸(Runner._finalize)。

        注入与续命链同一 checksum_fn,使档 3b 跨轮腐烂前置在迷你复验入口生效。
        """
        from freshlatch.runner import Runner  # 延迟导入避免环

        runner = Runner(self.store, checksum_fn=self._checksum_fn)
        result = runner.run([claim])
        lead_decision = result.decisions[claim.claim_id]
        note = ""
        if lead_decision.status == "fresh" and claim.status != "fresh":
            note = "Lead 判 fresh,规则闸按作废名单打回(INVALIDATED)"
        return claim.status, note

    # -- checkpoint 清理(ADR-0006 §9:留最近 5 个 thread,业务侧删行)-------------------

    def prune(self, claim_id: str, keep: int = CHECKPOINT_KEEP) -> int:
        """同一主张的重跑 thread(`reverify-{claim_id}-*`)只留最近 keep 个。"""
        return self._prune_prefix(f"reverify-{claim_id}-", keep)

    def prune_rounds(self, keep: int = CHECKPOINT_KEEP) -> int:
        """轮次 thread(`reverify-round-*`)只留最近 keep 个(每轮一个,不清理会无限增长)。"""
        return self._prune_prefix("reverify-round-", keep)

    def _prune_prefix(self, prefix: str, keep: int) -> int:
        if not self.checkpoint_path.exists():
            return 0
        # 表名以 sqlite_master 探测为准(pin 版 3.1.1 = checkpoints/writes);
        # thread_id 时间戳字典序即时序。
        candidates = ("checkpoints", "writes")
        with sqlite3.connect(self.checkpoint_path) as conn:
            existing = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            tables = [t for t in candidates if t in existing]
            if "checkpoints" not in tables:
                return 0
            rows = conn.execute(
                "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?"
                " ORDER BY thread_id DESC",
                (prefix + "%",),
            ).fetchall()
            stale = [r[0] for r in rows[keep:]]
            for tid in stale:
                for table in tables:
                    conn.execute(f"DELETE FROM {table} WHERE thread_id = ?", (tid,))
        return len(stale)

    # -- langgraph 面(全部收口在本模块:模块外零 langgraph import)---------------------

    def _apply(self, decisions: list[dict]) -> list[dict]:
        """写路径唯一:execute 节点的落档函数(由 gates/human_latch 执行)。"""
        return apply_decisions(self.store, self._claims_by_id, decisions,
                               pending_ids=self._pending_ids, checksum_fn=self._checksum_fn,
                               run_id=self._run_id)

    @contextmanager
    def _saver(self):
        from langgraph.checkpoint.sqlite import SqliteSaver

        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with SqliteSaver.from_conn_string(str(self.checkpoint_path)) as saver:
            yield saver

    def _graph(self, saver):
        return _build_graph(self._apply).compile(checkpointer=saver)

    @staticmethod
    def _config(thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}
