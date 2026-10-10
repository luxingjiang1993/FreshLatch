"""自动核验：本地 mDeBERTa-v3 XNLI 判断绑定 chunk 是否支撑 after_text。

主核验（ADR-0040 / #527）：
- premise = ``evidence_text``，hypothesis = ``after_text``
- ``ok`` 当且仅当 argmax=entailment 且 P(entailment)≥τ
- released（ok）：``score`` = P(entailment)∈[0,1]，禁止 None
- rejected / hard reject（not ok）：``score`` = −∞，禁止 None 混池
- 仍返回 ``ok`` / ``score`` / ``reason``

调用方传入臂、``claim_id``、``after_text``、``evidence_id``、``evidence_text``。
比较只用 ``after_text`` 与 ``evidence_text``。入库检查在核验前面做完，这里不再看。
禁止金标 / 评委 / 用户裁决进 score。不把仓外 XNLI Acc 当本仓过线。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# 型号与 τ 跑前锁死（Pin · ADR-0040）。τ 为冒烟标定默认针；#520 可收紧，禁止放宽凑绿。
XNLI_MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
ENTAILMENT_TAU = 0.5

_REJECT_SCORE = float("-inf")
_LABEL_ENTAILMENT = "entailment"

# 懒加载缓存：(tokenizer, model, id2label)
_xnli_bundle: tuple[Any, Any, Mapping[int, str]] | None = None


def _normalize_label(raw: object) -> str:
    """把型号 id2label 统一成小写英文标签名。"""
    text = str(raw).strip().lower()
    # 少数卡写成 LABEL_0 / entailment 混排；只认英文三分类名
    if "entail" in text:
        return _LABEL_ENTAILMENT
    if "contra" in text:
        return "contradiction"
    if "neutral" in text:
        return "neutral"
    return text


def _load_xnli() -> tuple[Any, Any, Mapping[int, str]]:
    """首次推理才加载权重。单测应 monkeypatch ``predict_xnli_probs``，避免下模型。"""
    global _xnli_bundle
    if _xnli_bundle is not None:
        return _xnli_bundle

    # 延迟导入：权威命令 compileall / 未装 NLI 依赖的单测 stub 路径不强制 import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(XNLI_MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(XNLI_MODEL_ID)
    model.eval()
    id2label = {int(idx): _normalize_label(name) for idx, name in model.config.id2label.items()}
    _xnli_bundle = (tokenizer, model, id2label)
    return _xnli_bundle


def predict_xnli_probs(premise: str, hypothesis: str) -> dict[str, float]:
    """对 (premise, hypothesis) 跑 XNLI，返回三分类 softmax 概率。

    键为 ``entailment`` / ``neutral`` / ``contradiction``。
    正式主跑前须本地缓存型号；本函数不读密钥、不发托管 LLM。
    """
    import torch

    tokenizer, model, id2label = _load_xnli()
    encoded = tokenizer(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )
    with torch.no_grad():
        logits = model(**encoded).logits[0]
        probs = torch.softmax(logits, dim=-1).tolist()

    out: dict[str, float] = {
        _LABEL_ENTAILMENT: 0.0,
        "neutral": 0.0,
        "contradiction": 0.0,
    }
    for idx, value in enumerate(probs):
        label = id2label.get(idx, str(idx))
        out[label] = float(value)
    return out


def verify_edit(request: Mapping[str, Any]) -> dict[str, Any]:
    """返回 ``ok``、``score``、``reason``。score 永不为 None。"""
    after = request.get("after_text")
    evidence = request.get("evidence_text")
    if not isinstance(after, str) or not isinstance(evidence, str):
        return {"ok": False, "score": _REJECT_SCORE, "reason": "核验不过"}

    # premise=绑定 chunk，hypothesis=改写后文（ADR-0040）
    probs = predict_xnli_probs(evidence, after)
    p_entailment = float(probs[_LABEL_ENTAILMENT])
    argmax_label = max(probs, key=probs.__getitem__)
    ok = argmax_label == _LABEL_ENTAILMENT and p_entailment >= ENTAILMENT_TAU
    if ok:
        return {"ok": True, "score": p_entailment, "reason": "支撑成立"}
    return {"ok": False, "score": _REJECT_SCORE, "reason": "核验不过"}
