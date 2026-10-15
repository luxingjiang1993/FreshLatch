"""成立 patch 实验的新预注册脚手架。

口径锁在 ``docs/evidence/patch-establishment/PREREG.md``。
本期不开跑、不打分、不发明 SESOI。
Amendment-01 只把判据行锁成 ``registered:interval_gt0``,成立格分数仍全是 null。
冻结语料可以写入 ``sources.experiment_corpus`` 的 path 与 sha256；
``measurement_status`` 仍是 unmeasured，分数仍是 null。
不改 ``PRODUCTION_RETRIEVAL_MODE``。不写路线 Y 的历史成立格,不写质量闸地板。
"""

from __future__ import annotations

import json
from pathlib import Path

from freshlatch.models import LOCAL_EMBED_MODEL, NEURAL_RERANK_MODEL
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.checksum import aggregate_checksum, normalize_newlines, sha256_hex
from freshlatch.store.local_embed import LOCAL_EMBED_DIM
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K

SCHEMA_VERSION = "l4-c-04-v1"
LEVEL = "scaffold"
MANIFEST_STATUS = "schema_frozen_unmeasured"
RUN_STATUS = "unrun"
MEASUREMENT_STATUS = "unmeasured"
NUMERIC_LINE = "unregistered"
# Amendment-01 锁的是判据行,不是 SESOI,也不是已测量分数。
CRITERIA_NUMERIC_LINE = "registered:interval_gt0"
HISTORICAL_RESULT_Y = "丙"
CONCLUSION_DIR = "docs/evidence/patch-establishment/"
MANIFEST_NAME = "manifest.json"
MEASUREMENT_NAME = "measurement.json"
PREREG_REL = Path("docs/evidence/patch-establishment/PREREG.md")
RESULT_REL = Path("docs/evidence/patch-establishment/RESULT.md")
FASTEMBED_PIN = "fastembed==0.8.1"
FUSION = "RRF"

FALSE_POSITIVE_IDS = (
    "FP-UNMEASURED",
    "FP-B04",
    "FP-REJUDGE",
    "FP-SECOND-Y",
    "FP-L5",
    "FP-SUPERIOR",
    "FP-FLOORS",
    "FP-SESOI",
    "FP-NULL-AS-ZERO",
)
STOP_IDS = (
    "STOP-UNRUN",
    "STOP-FAIL",
    "STOP-PASS",
    "STOP-SAME-YARDSTICK",
)

RETRIEVAL_FIELDS = (
    "mode",
    "embedding_model",
    "embedding_dim",
    "fusion",
    "rrf_k",
    "rerank_model",
    "rerank_k",
    "fastembed",
    "production_default_unchanged",
    "weight_sha256",
)
MODEL_FIELDS = (
    "generator_model",
    "generator_sha256",
    "nli_model",
    "nli_sha256",
    "temperature",
    "seed",
    "measurement_status",
)
SOURCE_FIELDS = (
    "result_y",
    "prereg_y",
    "quality_gate_prereg",
    "frozen_per_query",
    "frozen_summary",
    "gold",
    "x1_questions",
    "b04_fixtures",
    "experiment_corpus",
)
DECODING_FIELDS = ("temperature", "seed", "model", "note")
ESTABLISHMENT_FIELDS = (
    "status",
    "counted_as_pass",
    "sesoi",
    "numeric_line",
    "false_accept_rate",
    "point_estimate",
    "ci95_low",
    "ci95_high",
    "n",
    "k",
)
FIREWALL_FIELDS = (
    "historical_result_y",
    "historical_cells_rewritten",
    "b04_counts_as_establishment",
    "second_formal_y",
    "claims_rarr_kpr_superiority",
    "product_l5",
    "floors_unchanged",
    "production_arm_unchanged",
)
CRITERIA_FIELDS = ("false_positive", "stop", "sesoi", "numeric_line")
FIELD_GROUPS = (
    ("retrieval", RETRIEVAL_FIELDS),
    ("model", MODEL_FIELDS),
    ("sources", SOURCE_FIELDS),
    ("decoding", DECODING_FIELDS),
    ("establishment", ESTABLISHMENT_FIELDS),
    ("firewall", FIREWALL_FIELDS),
    ("criteria", CRITERIA_FIELDS),
)

REQUIRED_PROSE = (
    "不改默认臂",
    "不改 floors",
    "不得称优于 RARR·KPR",
    "不得标产品 L5",
    "不得把历史结果丙改判为乙",
    "本页不发明 SESOI",
    "numeric_line=unregistered",
    "Amendment-01",
    "registered:interval_gt0",
    "比较 A",
    "n=100",
    "sesoi=null",
    "不得把该线叫做 SESOI",
    "measurement_status=unmeasured",
    "run_status=unrun",
    "counted_as_pass=false",
    "counts_as_establishment=false",
    "second_formal_y=false",
    "PRODUCTION_RETRIEVAL_MODE",
    "hybrid+rerank",
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/patch-establishment/",
    "replaces_frozen_baseline=false",
    "夹具绿不是结果乙",
    "本页不是路线 Y 的另一次正式主跑",
    "空着不是 0",
)

ANCHOR_FILES = {
    "result_y": "docs/evidence/patch-events/RESULT-Y.md",
    "prereg_y": "docs/evidence/patch-events/PREREG-Y.md",
    "quality_gate_prereg": "docs/evidence/quality-gate/PREREG.md",
    "frozen_per_query": "docs/evidence/neural-rerank/per-query.json",
    "frozen_summary": "docs/evidence/neural-rerank/summary.json",
}
GOLD_FILES = (
    "data/eval/gold.json",
    "data/eval/guard_should.json",
    "data/eval/cite_sentence.json",
    "data/eval/temporal_new_over_old.json",
)
X1_QUESTIONS = "data/exp/x1/questions.json"
# 新实验语料只许落在这棵树。不得指向 pe_v2 正式名单，也不得指向 x1。
FROZEN_CORPUS_REL = "data/patch-establishment/v1"
CORPUS_ROLE_FROZEN = "frozen_corpus_unrun"
CORPUS_ROLE_EMPTY = "unmeasured"
_ROUTE_Y_SPLIT = Path("docs/evidence/patch-events/SPLIT-pe-v2-route-y.json")
_STRATUM_NAMES = ("数值", "日期", "条款替换", "删除")
B04_FILES = (
    "tests/fixtures/l4_b_04/b04-price-blank-filler.md",
    "tests/fixtures/l4_b_04/b04-price-blank.md",
    "tests/fixtures/l4_b_04/b04-price-drop.md",
    "tests/fixtures/l4_b_04/b04-price-expired.md",
    "tests/fixtures/l4_b_04/b04-price-keep-t0.md",
    "tests/fixtures/l4_b_04/b04-price-keep.md",
)
SCORE_FIELDS = (
    "false_accept_rate",
    "point_estimate",
    "ci95_low",
    "ci95_high",
    "n",
    "k",
)
_BLOCKED_OUT = (
    ("docs", "evidence", "neural-rerank"),
    ("docs", "evidence", "quality-gate"),
    ("docs", "evidence", "patch-events"),
    ("docs", "evidence", "temporal-trained-retrieval"),
    ("data", "exp", "x1"),
    ("data", "eval"),
)
_BANNED_OUTPUT_NAMES = frozenset({
    "RESULT-Y.md",
    "PREREG-Y.md",
    "per-query.json",
    "PREREG.md",
})


def banned_needles() -> tuple[str, ...]:
    """文案与测试里不得出现的两句。返回值只用于拒绝,调用方不得把它写进文档。"""
    return (
        "B-04 = " + "乙",
        "二次主跑" + " Y",
    )


def manifest_field_line() -> str:
    """预注册页上的冻结字段行。顺序与 FIELD_GROUPS 一致。"""
    parts: list[str] = []
    for block, names in FIELD_GROUPS:
        for name in names:
            parts.append(f"{block}.{name}")
    return "manifest_fields: " + ", ".join(parts)


def _reject_banned(text: str) -> None:
    for needle in banned_needles():
        if needle in text:
            raise ValueError("文本含丙防火墙禁止的句子")


def _path_parts(path: Path | str) -> tuple[str, ...]:
    text = str(path).replace("\\", "/").strip()
    stack: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
            continue
        stack.append(part)
    return tuple(stack)


def _path_contains(path: Path | str, needle: tuple[str, ...]) -> bool:
    parts = _path_parts(path)
    width = len(needle)
    if width == 0 or len(parts) < width:
        return False
    return any(parts[index:index + width] == needle for index in range(len(parts) - width + 1))


def _reject_out_dir(path: Path | str) -> None:
    for needle in _BLOCKED_OUT:
        if _path_contains(path, needle):
            joined = "/".join(needle)
            raise ValueError(f"拒绝把测量写进 {joined}")


def file_sha256(path: Path) -> str:
    """CRLF 折成 LF 再哈希。与质量闸冻结指纹同一换行口径。"""
    return sha256_hex(normalize_newlines(path.read_bytes(), "lf"))


def frozen_corpus_files(root: Path) -> list[Path]:
    """冻结树里的全部文件。目录未建时返回空列表。"""
    base = Path(root) / FROZEN_CORPUS_REL
    if not base.is_dir():
        return []
    return [path for path in base.rglob("*") if path.is_file()]


def experiment_corpus_sha256(root: Path) -> str:
    """对冻结树做 aggregate checksum。``newline=lf``。"""
    files = frozen_corpus_files(root)
    if not files:
        raise ValueError("冻结实验语料目录没有文件")
    return aggregate_checksum(files, root=Path(root), newline="lf")


def _experiment_corpus_block(root: Path) -> dict:
    """盘上有冻结树就写入 path 与 sha256。没有则保持 null。分数不在这里。"""
    if not frozen_corpus_files(root):
        return {
            "path": None,
            "sha256": None,
            "role": CORPUS_ROLE_EMPTY,
            "measurement_status": MEASUREMENT_STATUS,
            "counts_as_establishment": False,
        }
    return {
        "path": FROZEN_CORPUS_REL,
        "sha256": experiment_corpus_sha256(root),
        "role": CORPUS_ROLE_FROZEN,
        "measurement_status": MEASUREMENT_STATUS,
        "counts_as_establishment": False,
    }


def _read_anchor(root: Path, rel: str) -> dict:
    path = root / rel
    if not path.is_file():
        raise ValueError(f"锚文件不存在: {rel}")
    return {
        "path": rel,
        "sha256": file_sha256(path),
        "role": "historical_read_only",
        "counts_as_establishment": False,
    }


def _fastembed_pin(root: Path) -> str:
    for rel in ("pyproject.toml", "requirements.txt"):
        text = (root / rel).read_text(encoding="utf-8")
        if FASTEMBED_PIN not in text:
            raise ValueError(f"{rel} 缺少 {FASTEMBED_PIN}")
    return "0.8.1"


def _source_block(root: Path) -> dict:
    sources = {
        key: _read_anchor(root, rel)
        for key, rel in ANCHOR_FILES.items()
    }
    sources["frozen_per_query"]["role"] = "frozen_read_only"
    sources["frozen_summary"]["role"] = "frozen_read_only"
    sources["result_y"]["historical_cell"] = HISTORICAL_RESULT_Y
    sources["prereg_y"]["historical_cell"] = "read_only"
    gold = []
    for rel in GOLD_FILES:
        row = _read_anchor(root, rel)
        row["role"] = "frozen_read_only"
        gold.append(row)
    sources["gold"] = {
        "role": "frozen_read_only",
        "counts_as_establishment": False,
        "files": gold,
    }
    x1 = _read_anchor(root, X1_QUESTIONS)
    x1["role"] = "frozen_read_only"
    sources["x1_questions"] = x1
    b04_paths = []
    for rel in B04_FILES:
        path = root / rel
        if not path.is_file():
            raise ValueError(f"B-04 夹具不存在: {rel}")
        b04_paths.append(path)
    extra = sorted((root / "tests" / "fixtures" / "l4_b_04").glob("*.md"))
    if [path.relative_to(root).as_posix() for path in extra] != list(B04_FILES):
        raise ValueError("B-04 夹具名单与冻结边界不一致")
    files = []
    for rel, path in zip(B04_FILES, b04_paths, strict=True):
        files.append({
            "path": rel,
            "sha256": file_sha256(path),
            "counts_as_establishment": False,
        })
    sources["b04_fixtures"] = {
        "path": "tests/fixtures/l4_b_04",
        "sha256": aggregate_checksum(b04_paths, root=root, newline="lf"),
        "role": "fixture_boundary",
        "counts_as_establishment": False,
        "files": files,
    }
    sources["experiment_corpus"] = _experiment_corpus_block(root)
    return sources


def _retrieval_block(root: Path) -> dict:
    if PRODUCTION_RETRIEVAL_MODE != "hybrid+rerank":
        raise ValueError("生产臂不是 hybrid+rerank")
    return {
        "mode": PRODUCTION_RETRIEVAL_MODE,
        "embedding_model": LOCAL_EMBED_MODEL,
        "embedding_dim": LOCAL_EMBED_DIM,
        "fusion": FUSION,
        "rrf_k": RRF_K,
        "rerank_model": NEURAL_RERANK_MODEL,
        "rerank_k": NEURAL_RERANK_K,
        "fastembed": _fastembed_pin(root),
        "production_default_unchanged": True,
        "weight_sha256": None,
    }


def _model_block() -> dict:
    return {
        "generator_model": None,
        "generator_sha256": None,
        "nli_model": None,
        "nli_sha256": None,
        "temperature": None,
        "seed": None,
        "measurement_status": MEASUREMENT_STATUS,
    }


def _decoding_block() -> dict:
    return {
        "temperature": None,
        "seed": None,
        "model": None,
        "note": "scaffold, no LLM, temperature/seed/model unused",
    }


def _establishment_block() -> dict:
    return {
        "status": MEASUREMENT_STATUS,
        "counted_as_pass": False,
        "sesoi": None,
        "numeric_line": NUMERIC_LINE,
        "false_accept_rate": None,
        "point_estimate": None,
        "ci95_low": None,
        "ci95_high": None,
        "n": None,
        "k": None,
    }


def _firewall_block() -> dict:
    return {
        "historical_result_y": HISTORICAL_RESULT_Y,
        "historical_cells_rewritten": False,
        "b04_counts_as_establishment": False,
        "second_formal_y": False,
        "claims_rarr_kpr_superiority": False,
        "product_l5": False,
        "floors_unchanged": True,
        "production_arm_unchanged": True,
    }


def _criteria_block() -> dict:
    return {
        "false_positive": list(FALSE_POSITIVE_IDS),
        "stop": list(STOP_IDS),
        "sesoi": None,
        "numeric_line": CRITERIA_NUMERIC_LINE,
    }


def require_prereg(text: str) -> None:
    """预注册页必须写死判据、字段行和防火墙句。缺一句就拒绝落测量。"""
    _reject_banned(text)
    missing = [item for item in REQUIRED_PROSE if item not in text]
    if missing:
        raise ValueError("预注册页缺少锁句: " + ", ".join(missing))
    for item in FALSE_POSITIVE_IDS + STOP_IDS:
        if item not in text:
            raise ValueError(f"预注册页缺少判据 {item}")
    line = manifest_field_line()
    if line not in text:
        raise ValueError("预注册页缺少 manifest 字段行")


def build_scaffold(root: Path) -> tuple[dict, dict]:
    """空 manifest 与空测量。数字位保持 null。"""
    root = Path(root)
    prereg = root / PREREG_REL
    if not prereg.is_file():
        raise ValueError(f"预注册页不存在: {PREREG_REL.as_posix()}")
    require_prereg(prereg.read_text(encoding="utf-8"))
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "level": LEVEL,
        "manifest_status": MANIFEST_STATUS,
        "replaces_frozen_baseline": False,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "retrieval": _retrieval_block(root),
        "model": _model_block(),
        "sources": _source_block(root),
        "decoding": _decoding_block(),
        "establishment": _establishment_block(),
        "firewall": _firewall_block(),
        "criteria": _criteria_block(),
    }
    measurement = {
        "schema_version": SCHEMA_VERSION,
        "level": LEVEL,
        "run_status": RUN_STATUS,
        "measurement_status": MEASUREMENT_STATUS,
        "replaces_frozen_baseline": False,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "conclusion_dir": CONCLUSION_DIR,
        "decoding": _decoding_block(),
        "establishment": _establishment_block(),
        "firewall": _firewall_block(),
        "criteria": _criteria_block(),
    }
    validate_scaffold(manifest, measurement, root=root)
    return manifest, measurement


def _require_equal(got: object, expected: object, label: str) -> None:
    if got != expected:
        raise ValueError(f"{label} 不符合未开跑脚手架")


def _reject_scores(block: dict, *, numeric_line: str = NUMERIC_LINE) -> None:
    """分数位保持 null。sesoi 保持 null。numeric_line 只能等于调用方给出的已锁值。"""
    if block.get("sesoi") is not None:
        raise ValueError("本页不发明 SESOI")
    if block.get("numeric_line") != numeric_line:
        if numeric_line == NUMERIC_LINE:
            raise ValueError("numeric_line 必须是 unregistered")
        raise ValueError("criteria.numeric_line 必须是 registered:interval_gt0")
    for name in SCORE_FIELDS:
        if name == "sesoi" or name == "numeric_line":
            continue
        if name in block and block[name] is not None:
            raise ValueError(f"{name} 本期必须是 null")


def validate_scaffold(manifest: dict, measurement: dict, *, root: Path) -> None:
    """未开跑脚手架的不变量。任一分数、改判或产品 L5 都拒绝。"""
    root = Path(root)
    _require_equal(manifest.get("schema_version"), SCHEMA_VERSION, "manifest.schema_version")
    _require_equal(manifest.get("level"), LEVEL, "manifest.level")
    _require_equal(manifest.get("manifest_status"), MANIFEST_STATUS, "manifest_status")
    _require_equal(manifest.get("replaces_frozen_baseline"), False, "replaces_frozen_baseline")
    _require_equal(
        manifest.get("production_retrieval_mode"),
        PRODUCTION_RETRIEVAL_MODE,
        "production_retrieval_mode",
    )
    retrieval = manifest.get("retrieval")
    if not isinstance(retrieval, dict):
        raise ValueError("retrieval 必须是对象")
    _require_equal(retrieval.get("mode"), PRODUCTION_RETRIEVAL_MODE, "retrieval.mode")
    _require_equal(retrieval.get("embedding_model"), LOCAL_EMBED_MODEL, "embedding_model")
    _require_equal(retrieval.get("embedding_dim"), LOCAL_EMBED_DIM, "embedding_dim")
    _require_equal(retrieval.get("fusion"), FUSION, "fusion")
    _require_equal(retrieval.get("rrf_k"), RRF_K, "rrf_k")
    _require_equal(retrieval.get("rerank_model"), NEURAL_RERANK_MODEL, "rerank_model")
    _require_equal(retrieval.get("rerank_k"), NEURAL_RERANK_K, "rerank_k")
    _require_equal(retrieval.get("fastembed"), "0.8.1", "fastembed")
    _require_equal(retrieval.get("production_default_unchanged"), True, "production_default")
    if retrieval.get("weight_sha256") is not None:
        raise ValueError("weight_sha256 本期必须是 null")
    model = manifest.get("model")
    if not isinstance(model, dict):
        raise ValueError("model 必须是对象")
    for name in ("generator_model", "generator_sha256", "nli_model", "nli_sha256", "temperature", "seed"):
        if model.get(name) is not None:
            raise ValueError(f"model.{name} 本期必须是 null")
    _require_equal(model.get("measurement_status"), MEASUREMENT_STATUS, "model.measurement_status")
    decoding = manifest.get("decoding")
    if not isinstance(decoding, dict):
        raise ValueError("decoding 必须是对象")
    for name in ("temperature", "seed", "model"):
        if decoding.get(name) is not None:
            raise ValueError(f"decoding.{name} 本期必须是 null")
    establishment = manifest.get("establishment")
    firewall = manifest.get("firewall")
    criteria = manifest.get("criteria")
    if not isinstance(establishment, dict) or not isinstance(firewall, dict) or not isinstance(criteria, dict):
        raise ValueError("establishment / firewall / criteria 必须是对象")
    _reject_scores(establishment)
    _reject_scores(criteria, numeric_line=CRITERIA_NUMERIC_LINE)
    _require_equal(establishment.get("status"), MEASUREMENT_STATUS, "establishment.status")
    _require_equal(establishment.get("counted_as_pass"), False, "counted_as_pass")
    _require_equal(criteria.get("false_positive"), list(FALSE_POSITIVE_IDS), "false_positive")
    _require_equal(criteria.get("stop"), list(STOP_IDS), "stop")
    _require_firewall(firewall)
    _require_sources(manifest.get("sources"), root)
    _require_equal(measurement.get("schema_version"), SCHEMA_VERSION, "measurement.schema_version")
    _require_equal(measurement.get("level"), LEVEL, "measurement.level")
    _require_equal(measurement.get("run_status"), RUN_STATUS, "run_status")
    _require_equal(measurement.get("measurement_status"), MEASUREMENT_STATUS, "measurement_status")
    _require_equal(measurement.get("replaces_frozen_baseline"), False, "measurement.replaces_frozen_baseline")
    _require_equal(
        measurement.get("production_retrieval_mode"),
        PRODUCTION_RETRIEVAL_MODE,
        "measurement.production_retrieval_mode",
    )
    _require_equal(measurement.get("conclusion_dir"), CONCLUSION_DIR, "conclusion_dir")
    if measurement.get("establishment") != establishment:
        raise ValueError("测量的成立格与 manifest 不一致")
    if measurement.get("firewall") != firewall:
        raise ValueError("测量的防火墙与 manifest 不一致")
    if measurement.get("criteria") != criteria:
        raise ValueError("测量的判据与 manifest 不一致")
    if measurement.get("decoding") != decoding:
        raise ValueError("测量的解码参数与 manifest 不一致")


def _require_firewall(firewall: dict) -> None:
    _require_equal(firewall.get("historical_result_y"), HISTORICAL_RESULT_Y, "historical_result_y")
    _require_equal(firewall.get("historical_cells_rewritten"), False, "historical_cells_rewritten")
    _require_equal(firewall.get("b04_counts_as_establishment"), False, "b04_counts_as_establishment")
    _require_equal(firewall.get("second_formal_y"), False, "second_formal_y")
    _require_equal(firewall.get("claims_rarr_kpr_superiority"), False, "claims_rarr_kpr_superiority")
    _require_equal(firewall.get("product_l5"), False, "product_l5")
    _require_equal(firewall.get("floors_unchanged"), True, "floors_unchanged")
    _require_equal(firewall.get("production_arm_unchanged"), True, "production_arm_unchanged")


def _require_sources(sources: object, root: Path) -> None:
    if not isinstance(sources, dict):
        raise ValueError("sources 必须是对象")
    for key, rel in ANCHOR_FILES.items():
        row = sources.get(key)
        if not isinstance(row, dict):
            raise ValueError(f"sources.{key} 必须是对象")
        _require_equal(row.get("path"), rel, f"sources.{key}.path")
        _require_equal(row.get("sha256"), file_sha256(root / rel), f"sources.{key}.sha256")
        _require_equal(row.get("counts_as_establishment"), False, f"sources.{key}.counts")
    if sources.get("result_y", {}).get("historical_cell") != HISTORICAL_RESULT_Y:
        raise ValueError("RESULT-Y 锚必须仍是结果丙")
    gold = sources.get("gold")
    if not isinstance(gold, dict) or gold.get("counts_as_establishment") is not False:
        raise ValueError("gold 不得进入成立格")
    files = gold.get("files") if isinstance(gold, dict) else None
    if not isinstance(files, list) or [row.get("path") for row in files] != list(GOLD_FILES):
        raise ValueError("gold 名单与冻结金标不一致")
    for row, rel in zip(files, GOLD_FILES, strict=True):
        _require_equal(row.get("sha256"), file_sha256(root / rel), f"gold {rel}")
    x1 = sources.get("x1_questions")
    if not isinstance(x1, dict):
        raise ValueError("x1_questions 必须是对象")
    _require_equal(x1.get("path"), X1_QUESTIONS, "x1 path")
    _require_equal(x1.get("sha256"), file_sha256(root / X1_QUESTIONS), "x1 sha256")
    _require_equal(x1.get("counts_as_establishment"), False, "x1 counts")
    b04 = sources.get("b04_fixtures")
    if not isinstance(b04, dict):
        raise ValueError("b04_fixtures 必须是对象")
    _require_equal(b04.get("counts_as_establishment"), False, "b04 counts")
    _require_equal(b04.get("role"), "fixture_boundary", "b04 role")
    listed = b04.get("files")
    if not isinstance(listed, list) or [row.get("path") for row in listed] != list(B04_FILES):
        raise ValueError("B-04 夹具名单与冻结边界不一致")
    for row, rel in zip(listed, B04_FILES, strict=True):
        if row.get("counts_as_establishment") is not False:
            raise ValueError("B-04 单文件不得进入成立格")
        _require_equal(row.get("sha256"), file_sha256(root / rel), f"b04 {rel}")
    _require_experiment_corpus(sources.get("experiment_corpus"), root)


def _reject_experiment_corpus_path(path: str) -> None:
    """只接受冻结树。``data/corpus/pe_v2`` 与 ``data/exp/x1`` 因此被拒绝。"""
    normal = "/".join(_path_parts(path))
    if normal != FROZEN_CORPUS_REL:
        raise ValueError("experiment_corpus 必须落在 data/patch-establishment/v1")


def _require_experiment_corpus(corpus: object, root: Path) -> None:
    """path 与 sha256 可以是冻结树，也可以在树不存在时同为 null。分数仍不在本块。"""
    if not isinstance(corpus, dict):
        raise ValueError("experiment_corpus 必须是对象")
    _require_equal(corpus.get("measurement_status"), MEASUREMENT_STATUS, "experiment_corpus")
    _require_equal(corpus.get("counts_as_establishment"), False, "experiment_corpus counts")
    path = corpus.get("path")
    digest = corpus.get("sha256")
    on_disk = bool(frozen_corpus_files(root))
    if path is None and digest is None:
        if on_disk:
            raise ValueError("冻结实验语料已在盘上, path 与 sha256 不得为 null")
        _require_equal(corpus.get("role"), CORPUS_ROLE_EMPTY, "experiment_corpus role")
        return
    if not isinstance(path, str) or not isinstance(digest, str):
        raise ValueError("experiment_corpus path 与 sha256 必须同时填写或同时为 null")
    _reject_experiment_corpus_path(path)
    _require_equal(corpus.get("role"), CORPUS_ROLE_FROZEN, "experiment_corpus role")
    if not on_disk:
        raise ValueError("experiment_corpus 指向的冻结目录没有文件")
    _require_equal(digest, experiment_corpus_sha256(root), "experiment_corpus sha256")
    _require_frozen_roster(root)


def _require_frozen_roster(root: Path) -> None:
    """配额目标保持 100。与路线 Y 的 n400、pilot 无交。second_formal_y 必须为 false。"""
    base = Path(root) / FROZEN_CORPUS_REL
    split_path = base / "SPLIT.json"
    docket_path = base / "docket.json"
    if not split_path.is_file() or not docket_path.is_file():
        raise ValueError("冻结实验语料缺 SPLIT.json 或 docket.json")
    split = json.loads(split_path.read_text(encoding="utf-8"))
    docket = json.loads(docket_path.read_text(encoding="utf-8"))
    _require_equal(split.get("second_formal_y"), False, "corpus second_formal_y")
    _require_equal(split.get("target_n"), 100, "corpus target_n")
    _require_equal(split.get("run_status"), RUN_STATUS, "corpus run_status")
    _require_equal(split.get("measurement_status"), MEASUREMENT_STATUS, "corpus measurement_status")
    _require_equal(split.get("counts_as_establishment"), False, "corpus counts")
    _require_equal(split.get("role"), CORPUS_ROLE_FROZEN, "corpus role")
    formal = split.get("formal")
    if not isinstance(formal, list) or not formal:
        raise ValueError("formal 必须是非空列表")
    ids = [str(row.get("claim_id") or "") for row in formal]
    if any(not item for item in ids):
        raise ValueError("formal claim_id 缺失")
    if len(ids) != len(set(ids)):
        raise ValueError("formal claim_id 重复")
    if split.get("built_n") != len(ids) or split.get("gap_n") != 100 - len(ids):
        raise ValueError("built_n / gap_n 与 formal 不一致")
    claims = docket.get("claims") if isinstance(docket, dict) else None
    if not isinstance(claims, list):
        raise ValueError("docket.claims 必须是列表")
    docket_ids = {str(row.get("claim_id") or "") for row in claims}
    if docket_ids != set(ids):
        raise ValueError("docket 与 formal 主张不一致")
    route = json.loads((Path(root) / _ROUTE_Y_SPLIT).read_text(encoding="utf-8"))
    banned = {str(row["claim_id"]) for row in route.get("n400") or []} | {
        str(row["claim_id"]) for row in route.get("pilot") or []
    }
    if set(ids) & banned:
        raise ValueError("实验语料与路线 Y 正式名单相交")
    for cid in ids:
        for folder in ("t0", "t1"):
            path = base / "corpus" / folder / f"{cid}.md"
            if not path.is_file():
                raise ValueError(f"冻结语料缺正文: corpus/{folder}/{cid}.md")
    by_stratum = split.get("by_stratum")
    if not isinstance(by_stratum, dict):
        raise ValueError("by_stratum 必须是对象")
    for name in _STRATUM_NAMES:
        block = by_stratum.get(name)
        if not isinstance(block, dict):
            raise ValueError(f"缺层 {name}")
        if block.get("target") != 25:
            raise ValueError(f"{name} 目标被改小")
        if block.get("correct_target") != 12 or block.get("bad_target") != 13:
            raise ValueError(f"{name} 余数目标被改")
        got = [row for row in formal if row.get("edit_type") == name]
        correct = sum(1 for row in got if row.get("construction_gold") == "正确")
        bad = sum(1 for row in got if row.get("construction_gold") == "坏")
        if (
            block.get("built") != len(got)
            or block.get("correct") != correct
            or block.get("bad") != bad
            or block.get("gap") != 25 - len(got)
        ):
            raise ValueError(f"{name} 计数与 formal 不一致")


def _dump(payload: dict) -> str:
    document = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _reject_banned(document)
    return document


def write_scaffold(*, out_dir: Path, root: Path) -> dict:
    """写出 manifest.json 与 measurement.json。不改 PREREG,不写冻结目录。"""
    _reject_out_dir(out_dir)
    manifest, measurement = build_scaffold(root)
    out = Path(out_dir)
    if out.exists() and not out.is_dir():
        raise ValueError(f"输出路径不是目录: {out.as_posix()}")
    out.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, payload in (
        (MANIFEST_NAME, manifest),
        (MEASUREMENT_NAME, measurement),
    ):
        if name in _BANNED_OUTPUT_NAMES:
            raise ValueError(f"拒绝写入 {name}")
        destination = out / name
        if destination.name in _BANNED_OUTPUT_NAMES:
            raise ValueError(f"拒绝写入 {destination.name}")
        destination.write_text(_dump(payload), encoding="utf-8", newline="\n")
        written[name] = destination.as_posix()
    return {
        "manifest_status": manifest["manifest_status"],
        "run_status": measurement["run_status"],
        "measurement_status": measurement["measurement_status"],
        "establishment": measurement["establishment"]["status"],
        "counted_as_pass": measurement["establishment"]["counted_as_pass"],
        "product_l5": measurement["firewall"]["product_l5"],
        "paths": written,
    }
