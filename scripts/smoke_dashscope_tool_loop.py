"""冒烟验证:DashScope 最便宜模型(qwen-flash / qwen-turbo)的多轮工具调用能力。

对应 wayfinder 工单 #2。模拟 FreshLatch Lead 复验循环的最小形态:
中文工具描述 + 中文语料 + 多轮 tool_calls 循环,验证:
  A. 多轮循环稳定性(目标 >=18 轮不崩、不忘调工具、不输出非法 JSON 参数)
  B. 单轮并行 tool_calls
  C. 长上下文(主张列表+检索块+作废名单)下的判定质量
  D. 无工具假绿对照(同模型不带工具读 T0 摘要,是否把已死主张判绿)
  E. token 用量与成本估算

用法: python scripts/smoke_dashscope_tool_loop.py [--model qwen-flash] [--runs 2]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# ---------------------------------------------------------------------------
# 中文合成语料(与 FreshLatch 语料形态同构但更小)
# ---------------------------------------------------------------------------
CORPUS: dict[str, str] = {
    "D01": "FreshLatch 官网定价页(2026-03):专业版 299 元/席/月,含 5 个复验席位。",
    "D02": "FreshLatch 帮助中心(2026-04):复验席位可跨项目共享,按自然月计费。",
    "D03": "内部公告(2026-05-15):自 2026-06-01 起,专业版取消按自然月计费,改为按 30 天滚动计费。",
    "D04": "内部公告(2026-06-01):专业版 299 元档正式下线,合并入 399 元团队版。",
    "D05": "招聘页(2026-02):FreshLatch 北京办公室开放高级后端工程师岗位。",
    "D06": "招聘页(2026-04):北京办公室高级后端岗位已停止接收简历,团队已满编。",
    "D07": "安全白皮书(2026-01):所有客户数据存储于华北 1 地域。",
    "D08": "合规更新(2026-05):新增华东 2 地域选项,客户可自选存储地域。",
    "D09": "合作伙伴名录(2026-03):认证实施伙伴共 12 家,覆盖华东与华南。",
    "D10": "合作伙伴名录(2026-06):认证实施伙伴扩至 20 家,新增西南大区。",
    "D11": "API 文档 v1(2026-02):webhook 仅支持验签,不支持重放窗口配置。",
    "D12": "API 文档 v2(2026-05):webhook 新增重放窗口配置,默认 5 分钟。",
}

# 主张 -> 金标(gold): alive(仍成立) / dead(已失效)
CLAIMS: dict[str, dict] = {
    "C1": {"text": "FreshLatch 专业版定价为 299 元/席/月", "gold": "dead",
           "why": "D04:299 元档 2026-06-01 已下线"},
    "C2": {"text": "FreshLatch 复验席位可跨项目共享", "gold": "alive",
           "why": "D02 支持,且后续公告未推翻"},
    "C3": {"text": "FreshLatch 北京办公室正在招聘高级后端工程师", "gold": "dead",
           "why": "D06:岗位已满编停止接收"},
    "C4": {"text": "客户数据只能存储在华北 1 地域", "gold": "dead",
           "why": "D08:新增华东 2 可选"},
    "C5": {"text": "认证实施伙伴覆盖华东与华南", "gold": "alive",
           "why": "D10 扩至 20 家仍含华东华南"},
    "C6": {"text": "webhook 支持配置重放窗口", "gold": "alive",
           "why": "D12:v2 新增该能力"},
    "C7": {"text": "专业版按自然月计费", "gold": "dead",
           "why": "D03:2026-06 起改 30 天滚动"},
    "C8": {"text": "webhook 仅支持验签", "gold": "dead",
           "why": "D12 新增重放窗口后表述过时"},
}

# 干扰项:看似死其实活 / 看似活其实死已在 CLAIMS 中体现;此处提供噪声文档
NOISE_DOCS = {
    "N01": "员工手册(2026-01):办公时间为 9:30 至 18:30,弹性一小时。",
    "N02": "品牌规范(2026-02):主色为深海蓝 #0A2540。",
    "N03": "报销制度(2026-03):差旅住宿上限 450 元/晚。",
}

# must_stale 作废名单(长上下文场景注入)
INVALIDATION_LIST = [
    {"claim": "C7", "reason": "2026-06-01 计费规则变更公告已作废", "source": "D03"},
    {"claim": "C1", "reason": "定价页下线公告", "source": "D04"},
]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_claims",
            "description": "列出本次需要复验的全部主张,返回主张编号与文本",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "按关键词检索内部文档库,返回命中的文档编号与摘要(只是线索,需再读原文)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "中文检索词"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_doc",
            "description": "按文档编号读取文档全文",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "形如 D01 的文档编号"},
                },
                "required": ["doc_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_verdict",
            "description": "对某条主张给出复验结论并结束该主张的复验",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string", "description": "主张编号,如 C1"},
                    "verdict": {"type": "string", "enum": ["alive", "dead", "uncertain"],
                               "description": "alive=仍成立;dead=已失效;uncertain=证据不足"},
                    "reason": {"type": "string", "description": "一句话中文理由,必须引用文档编号"},
                },
                "required": ["claim_id", "verdict", "reason"],
                "additionalProperties": False,
            },
        },
    },
]

SYSTEM_PROMPT = """你是 FreshLatch 的复验 Lead。你的任务是逐条复验用户主张是否仍然成立。
规则:
1. 先用 list_claims 看全部主张,再逐条检索与阅读文档取证。
2. 每条主张必须调用 write_verdict 结束,且 reason 必须引用文档编号(如 D03)。
3. 判定 dead 需要找到推翻它的更新文档;判定 alive 需要确认没有更新文档推翻它。
4. 不确定就判 uncertain,不要猜。
5. 一条主张给出 verdict 后不要再重复处理它。"""


# ---------------------------------------------------------------------------
# 工具执行宿主
# ---------------------------------------------------------------------------
def execute_tool(name: str, args: dict) -> dict:
    if name == "list_claims":
        return {cid: c["text"] for cid, c in CLAIMS.items()}
    if name == "search_docs":
        q = args.get("query", "")
        hits = {}
        for did, text in {**CORPUS, **NOISE_DOCS}.items():
            if any(tok and tok in text for tok in q.replace("，", " ").replace(",", " ").split()):
                hits[did] = text[:60]
        return {"hits": hits}
    if name == "read_doc":
        did = args.get("doc_id", "")
        text = CORPUS.get(did) or NOISE_DOCS.get(did)
        return {"doc_id": did, "content": text} if text else {"error": f"文档不存在: {did}"}
    if name == "write_verdict":
        return {"ok": True, "recorded": args}
    return {"error": f"未知工具: {name}"}


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    requests: int = 0


@dataclass
class LoopResult:
    rounds: int = 0
    tool_calls: int = 0
    invalid_json: int = 0
    crashed: bool = False
    crash_reason: str = ""
    verdicts: dict = field(default_factory=dict)
    usage: Usage = field(default_factory=Usage)


def chat(client: OpenAI, model: str, messages: list, tools=None, tool_choice=None,
         temperature: float = 0.0) -> tuple[object, Usage]:
    kwargs = dict(model=model, messages=messages, temperature=temperature)
    if tools is not None:
        kwargs["tools"] = tools
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(**kwargs)
            u = resp.usage
            return resp, Usage(prompt_tokens=u.prompt_tokens, completion_tokens=u.completion_tokens, requests=1)
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            wait = 2 ** attempt
            print(f"    [retry {attempt + 1}] {type(e).__name__}: {e}; {wait}s 后重试", flush=True)
            time.sleep(wait)


def run_loop(client: OpenAI, model: str, max_rounds: int = 30) -> LoopResult:
    """场景 A:多轮 tool_calls 循环,直到全部主张有 verdict 或轮数耗尽。"""
    result = LoopResult()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "请复验本次全部主张,给出每条结论。"},
    ]
    for round_no in range(1, max_rounds + 1):
        result.rounds = round_no
        try:
            resp, usage = chat(client, model, messages, tools=TOOLS)
        except Exception as e:  # noqa: BLE001
            result.crashed = True
            result.crash_reason = f"round {round_no}: {type(e).__name__}: {e}"
            return result
        result.usage.prompt_tokens += usage.prompt_tokens
        result.usage.completion_tokens += usage.completion_tokens
        result.usage.requests += 1

        msg = resp.choices[0].message
        messages.append(msg)
        tool_calls = msg.tool_calls or []
        if not tool_calls:
            # 模型不再调工具:要么全做完,要么忘调工具
            if len(result.verdicts) >= len(CLAIMS):
                return result
            result.crashed = True
            result.crash_reason = f"round {round_no}: 提前停止调工具(已出 verdict {len(result.verdicts)}/{len(CLAIMS)})"
            return result

        if len(tool_calls) > 1:
            result.parallel_calls = getattr(result, "parallel_calls", 0) + 1

        for tc in tool_calls:
            result.tool_calls += 1
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                result.invalid_json += 1
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": json.dumps({"error": "非法 JSON 参数"}, ensure_ascii=False)})
                continue
            out = execute_tool(tc.function.name, args)
            if tc.function.name == "write_verdict":
                cid = args.get("claim_id", "?")
                if cid in CLAIMS and cid not in result.verdicts:
                    result.verdicts[cid] = args.get("verdict", "?")
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(out, ensure_ascii=False)})
    return result


def score_verdicts(verdicts: dict) -> dict:
    correct = sum(1 for cid, gold in ((c, v["gold"]) for c, v in CLAIMS.items())
                  if verdicts.get(cid) == gold)
    return {"correct": correct, "total": len(CLAIMS),
            "accuracy": round(correct / len(CLAIMS), 3),
            "missing": [c for c in CLAIMS if c not in verdicts]}


def run_no_tool_control(client: OpenAI, model: str) -> dict:
    """场景 D:同模型不带工具,只读 T0 摘要(旧文档拼成的支持面),问主张是否仍成立。"""
    t0_summary = "\n".join(
        f"- 文档 {did}({text.split('(')[1].split(')')[0]}):{text.split(':', 1)[-1]}"
        for did, text in CORPUS.items() if did in ("D01", "D02", "D05", "D07", "D09", "D11")
    )
    dead_claims = [c for c, v in CLAIMS.items() if v["gold"] == "dead"]
    prompt = (
        "以下是从内部文档整理的旧摘要:\n" + t0_summary + "\n\n"
        "请逐条判断下列主张是否仍然成立,回答 成立/不成立:\n"
        + "\n".join(f"{cid}. {CLAIMS[cid]['text']}" for cid in dead_claims)
    )
    resp, usage = chat(client, model, [
        {"role": "user", "content": prompt},
    ])
    text = resp.choices[0].message.content or ""
    false_green = sum(1 for cid in dead_claims
                      if cid in text and ("成立" in text.split(cid)[1][:60]) and ("不成立" not in text.split(cid)[1][:60]))
    return {"output": text, "usage": usage, "false_green_ratio": round(false_green / len(dead_claims), 3)}


def run_long_context(client: OpenAI, model: str) -> dict:
    """场景 C:长上下文(全部主张 + 检索块 + 作废名单),直接问 verdict,考察判定质量。"""
    blocks = "\n\n".join(f"[{did}] {text}" for did, text in {**CORPUS, **NOISE_DOCS}.items())
    inv = "\n".join(f"- {i['claim']}: {i['reason']}({i['source']})" for i in INVALIDATION_LIST)
    prompt = (
        "你是复验员。以下是检索到的全部文档块:\n\n" + blocks +
        "\n\n作废名单(以下旧主张已被公告作废):\n" + inv +
        "\n\n请对每条主张输出一行:编号 alive/dead/uncertain 理由。主张:\n"
        + "\n".join(f"{cid}. {v['text']}" for cid, v in CLAIMS.items())
    )
    resp, usage = chat(client, model, [{"role": "user", "content": prompt}])
    text = resp.choices[0].message.content or ""
    correct = 0
    for cid, v in CLAIMS.items():
        seg = text.split(cid)
        if len(seg) > 1 and v["gold"] in seg[1][:40]:
            correct += 1
    return {"accuracy": round(correct / len(CLAIMS), 3), "usage": usage, "output_head": text[:400]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen-flash")
    parser.add_argument("--runs", type=int, default=2)
    args = parser.parse_args()

    load_dotenv(find_dotenv(usecwd=True))
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        sys.exit("缺少 DASHSCOPE_API_KEY")

    client = OpenAI(api_key=api_key, base_url=BASE_URL, timeout=120)

    print(f"===== 模型: {args.model} | 循环轮数 x{args.runs} =====\n", flush=True)

    # ---- 场景 A+B:多轮循环 ----
    loop_scores = []
    total_usage = Usage()
    for i in range(1, args.runs + 1):
        print(f"--- A/B 循环 run {i} ---", flush=True)
        r = run_loop(client, args.model)
        total_usage.prompt_tokens += r.usage.prompt_tokens
        total_usage.completion_tokens += r.usage.completion_tokens
        total_usage.requests += r.usage.requests
        sc = score_verdicts(r.verdicts)
        loop_scores.append(sc)
        print(f"  rounds={r.rounds} tool_calls={r.tool_calls} invalid_json={r.invalid_json} "
              f"crashed={r.crashed} {r.crash_reason}", flush=True)
        print(f"  并行轮次={getattr(r, 'parallel_calls', 0)} accuracy={sc['accuracy']} missing={sc['missing']}", flush=True)

    # ---- 场景 C:长上下文 ----
    print("\n--- C 长上下文 ---", flush=True)
    lc = run_long_context(client, args.model)
    total_usage.prompt_tokens += lc["usage"].prompt_tokens
    total_usage.completion_tokens += lc["usage"].completion_tokens
    total_usage.requests += 1
    print(f"  accuracy={lc['accuracy']} prompt_tokens={lc['usage'].prompt_tokens}", flush=True)

    # ---- 场景 D:无工具假绿对照 ----
    print("\n--- D 无工具假绿对照 ---", flush=True)
    fg = run_no_tool_control(client, args.model)
    total_usage.prompt_tokens += fg["usage"].prompt_tokens
    total_usage.completion_tokens += fg["usage"].completion_tokens
    total_usage.requests += 1
    print(f"  false_green_ratio(dead 主张被判'成立')={fg['false_green_ratio']}", flush=True)

    # ---- 汇总 ----
    report = {
        "model": args.model,
        "loop": {"runs": loop_scores,
                 "avg_accuracy": round(sum(s["accuracy"] for s in loop_scores) / len(loop_scores), 3)},
        "long_context_accuracy": lc["accuracy"],
        "no_tool_false_green_ratio": fg["false_green_ratio"],
        "usage": {"prompt_tokens": total_usage.prompt_tokens,
                  "completion_tokens": total_usage.completion_tokens,
                  "requests": total_usage.requests},
    }
    print("\n===== 汇总 =====")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
