"""共享内存模型。语料/金标单一真相在 data/,本模块只是运行时对象。

模型名、平台、base_url 与密钥环境变量名集中登记在本模块。各用途一行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Status = Literal["fresh", "stale", "unknown", "void"]
AsOf = Literal["T0", "T1"]


@dataclass
class Claim:
    """主张(§2.2 schema)。statement 与 t0_evidence_ids 导入后只读。"""

    claim_id: str
    statement: str
    t0_evidence_ids: list[str] = field(default_factory=list)
    t1_evidence_ids: list[str] = field(default_factory=list)
    dimension: str | None = None  # 签发登记维度(ADR-0011;封闭枚举同 FOCUS_DIMENSIONS,load_docket 硬校验)
    status: Status = "unknown"
    reason: str = ""
    last_confirmed_at: str | None = None
    validity_basis: dict | None = None  # {doc_id, checksum},W5 起续命写入
    voided: bool = False  # 人的决定(ADR-0006 §3);与 status 的机器判定并存不互斥
    voided_at: str | None = None
    dissent: dict | None = None  # 异议记录(ADR-0009/0010/0012):{kind, auditor_verdict, reason, evidence_ids}
    # kind:auditor_semantic(不变量7)/mechanical_crosscheck(不变量8)/mechanical_precheck(ADR-0012 受理层)


@dataclass(frozen=True)
class ModelEntry:
    """一个用途上的模型登记。

    生成与检索行的值与搬迁前的字面量相同。评委行以 PREREG Amendment 1 为准。
    """

    purpose: str
    model: str
    platform: str
    base_url: str | None = None
    env_key: str | None = None
    max_output_tokens: int | None = None
    temperature: float | None = None
    forbidden_models: frozenset[str] = field(default_factory=frozenset)


_DASHSCOPE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

MODEL_REGISTRY: dict[str, ModelEntry] = {
    "default_llm": ModelEntry(
        purpose="default_llm",
        model="qwen-flash",
        platform="dashscope",
        base_url=_DASHSCOPE,
        env_key="DASHSCOPE_API_KEY",
    ),
    "embed": ModelEntry(
        purpose="embed",
        model="text-embedding-v4",
        platform="dashscope",
        base_url=_DASHSCOPE,
        env_key="DASHSCOPE_API_KEY",
    ),
    "local_embed": ModelEntry(
        purpose="local_embed",
        model="BAAI/bge-small-zh-v1.5",
        platform="fastembed",
    ),
    "neural_rerank": ModelEntry(
        purpose="neural_rerank",
        model="BAAI/bge-reranker-base",
        platform="fastembed",
    ),
    "x1_draft": ModelEntry(
        purpose="x1_draft",
        model="qwen-flash",
        platform="dashscope",
        base_url=_DASHSCOPE,
        env_key="DASHSCOPE_API_KEY",
        max_output_tokens=32768,
    ),
    "x1_flag": ModelEntry(
        purpose="x1_flag",
        model="qwen-plus",
        platform="dashscope",
        base_url=_DASHSCOPE,
        env_key="DASHSCOPE_API_KEY",
        max_output_tokens=32768,
    ),
    "judge_qwen": ModelEntry(
        purpose="judge_qwen",
        model="qwen2.5-72b-instruct",
        platform="dashscope",
        base_url=_DASHSCOPE,
        env_key="DASHSCOPE_API_KEY",
        temperature=0,
        forbidden_models=frozenset({"qwen-flash", "qwen-plus", "qwen-max"}),
    ),
    "judge_deepseek": ModelEntry(
        purpose="judge_deepseek",
        model="deepseek-flash",
        platform="deepseek",
        base_url="https://api.deepseek.com",
        env_key="DEEPSEEK_API_KEY",
        temperature=0,
        forbidden_models=frozenset(
            {
                "deepseek-ai/DeepSeek-V3",
                "deepseek-chat",
                "deepseek-reasoner",
                "deepseek-v4-pro",
            }
        ),
    ),
    "judge_kimi": ModelEntry(
        purpose="judge_kimi",
        model="kimi-k2.6",
        platform="moonshot",
        base_url="https://api.moonshot.cn/v1",
        env_key="MOONSHOT_API_KEY",
        temperature=0.6,
        forbidden_models=frozenset({"kimi-latest", "kimi-k3", "kimi-k2.7-code"}),
    ),
}

DEFAULT_MODEL = MODEL_REGISTRY["default_llm"].model
EMBED_MODEL = MODEL_REGISTRY["embed"].model
LOCAL_EMBED_MODEL = MODEL_REGISTRY["local_embed"].model
NEURAL_RERANK_MODEL = MODEL_REGISTRY["neural_rerank"].model
# 精排成功时 last_rerank_mode 的标签。不是模型 id，模型 id 仍是上面的 NEURAL_RERANK_MODEL。
RERANK_MODE_NEURAL = "bge-reranker-base"
DRAFT_MODEL = MODEL_REGISTRY["x1_draft"].model
FLAG_MODEL = MODEL_REGISTRY["x1_flag"].model


def _output_cap(purpose: str) -> int:
    cap = MODEL_REGISTRY[purpose].max_output_tokens
    if cap is None:
        raise RuntimeError(f"{purpose} 缺少 max_output_tokens")
    return cap


# qwen-flash / qwen-plus 最大输出 token。来源：help.aliyun.com/zh/model-studio/qwen-flash 与 qwen-plus，2026-10-06。
MODEL_MAX_OUTPUT_TOKENS = {
    DRAFT_MODEL: _output_cap("x1_draft"),
    FLAG_MODEL: _output_cap("x1_flag"),
}
