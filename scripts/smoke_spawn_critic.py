"""P5 冒烟:spawn_critic(focus) 合法/非法值各一次(§7.3 P5,行为符合 §3.4)。

- 非法值:工具层硬校验在派发前拦截——回列词表、不产生 LLM 调用;
  计步发生在 Lead 主循环(每次被拒的重试消耗一步,#14),此处直调工具层不计步,冒烟记录中注明。
- 合法值:真派驻一次 Critic(新会话/人格/白名单/预算 8,与 Lead 共享 Run 级检索预算),
  结论经工具观察回吐。烧少量 LLM 额度,由人触发。

输出原样贴进 docs/evidence/w4/p1-p5-precheck.md 的 P5 行。
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from freshlatch.llm import LLMClient  # noqa: E402
from freshlatch.models import Claim  # noqa: E402
from freshlatch.roles.lead import LeadReverifier  # noqa: E402
from freshlatch.runner import RunContext, load_docket  # noqa: E402
from freshlatch.store.base import InMemoryStore  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="P5: spawn_critic 合法/非法 focus 冒烟")
    ap.add_argument("--focus", default="competitor_pricing",
                    help="合法 focus 值(默认 competitor_pricing)")
    args = ap.parse_args()

    docket = load_docket(REPO_ROOT / "data" / "t0_docket.json")
    claim = next(c for c in docket.claims if c.claim_id == "c1")  # must_stale 代表
    ctx = RunContext(store=InMemoryStore())  # 空库:冒烟只看派驻行为,不看找反证质量
    lead = LeadReverifier(ctx, claim, LLMClient())

    bad = lead._t_spawn_critic({"focus": "not_a_dimension"})
    print("[非法值] focus=not_a_dimension")
    print(f"  error(应回列词表): {bad.get('error', '')[:200]}")
    assert "error" in bad, "非法 focus 必须被拒"

    good = lead._t_spawn_critic({"focus": args.focus})
    print(f"\n[合法值] focus={args.focus}")
    print(f"  回吐字段: {sorted(good.keys())}")
    print(f"  finding(前 200 字): {str(good.get('finding', ''))[:200]}")
    print(f"  counter_evidence_ids: {good.get('counter_evidence_ids')}")

    critic_events = [e for e in ctx.events if e["type"].startswith("critic")]
    print(f"\n[critic 轨迹事件] {json.dumps(critic_events, ensure_ascii=False, default=str)[:400]}")
    print("\nP5 记录要点:非法值回列词表 ✅(计步归 Lead 主循环,直调工具层不计);"
          "合法值结论经工具观察回吐 ✅;事件类型 critic_spawn/critic_result 在场 ✅")


if __name__ == "__main__":
    main()
