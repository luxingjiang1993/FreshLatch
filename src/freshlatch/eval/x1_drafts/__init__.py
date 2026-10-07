"""生成 x1 文档/题目草稿，并用 qwen-plus 非思考抽检（RET-01.7）。

温度与 seed 只从配置读取；缺省或 JSON null 时拒绝，不落入 DecodingParams 的 temperature 0。
generate 按 spec 分批各调用一次模型，合并进 --out。单价只读 spec.pricing，抽检单价只读 spec.flag_pricing，脚本不内置价格。
P2 不由模型生成。花费按上界预检，用量缺失、截断或调用异常都记失败并停止。清单、题目和文档都经临时文件替换写入。
检查器退出码 2（阈值未写入）与 1（结构/许可）都打印，已通过校验的草稿仍写入 --out。
不把去污染阈值写进配置，也不把任何数字缺省传给检查器。
"""

from freshlatch.eval.x1_checks import PUBLIC_LICENSES, check_x1
from freshlatch.llm import DecodingParams, LLMClient
from freshlatch.store.ingest import CLAUSE_RE, META_RE

from freshlatch.eval.x1_drafts.constants import (
    ROOT,
    FORBIDDEN_OUT_ROOTS,
    RETRIEVE_X1,
    MARKER_NAME,
    SIDECAR_MARKER,
    DRAFT_MODEL,
    FLAG_MODEL,
    MODEL_MAX_OUTPUT_TOKENS,
    FLAG_LEDGER_NAME,
    CONSECUTIVE_VALIDATION_LIMIT,
    GOLD_PLACEHOLDER,
    GOLD_QUESTION_KEYS,
    NOTE_FIELDS,
    RAW_GOLD_NOTE,
    BATCH_GENRES,
    BATCH_DOMAINS,
    BATCH_AS_OF,
    DOC_SOURCE_TYPES,
    LICENSE_SYNTHETIC,
    P2_MODEL_REFUSAL,
    DECODING_MISMATCH,
    FRONTMATTER_KEYS,
    EST_OUTPUT_TOKENS_PER_CHUNK,
    EST_OUTPUT_TOKENS_PER_DOC,
    EST_OUTPUT_TOKENS_PER_QUESTION,
    PUBLIC_CORPUS,
    PUBLIC_TRAPS,
    _BATCH_ID_RE,
    _RESERVED_BATCH_RE,
    _BLOCK_ID_RE,
    _H2_LINE_RE,
    _NBS_MARKERS,
    _DOC_BUCKETS,
    _DOC_SNAPSHOTS,
)

from freshlatch.eval.x1_drafts.paths import (
    DraftShapeError,
    _resolved,
    _is_under,
    _forbidden_resolved,
    is_forbidden_out,
    is_forbidden_sidecar,
    _is_script_sidecar,
    _can_write_sidecar,
    _can_overwrite_out,
)

from freshlatch.eval.x1_drafts.shape import (
    _load_config,
    _decoding_number,
    _require_draft_decoding,
    _parse_json_content,
    _whitelist_notes,
    _is_gold_key,
    _strip_nested_gold,
    _looks_like_question,
    _as_question_list,
    _extract_questions,
    _normalize_question,
    _document_path_syntax_error,
    _document_paths_collide,
    _strictly_inside,
    _content_has_frontmatter_block,
    _yaml_scalar,
    _render_yaml_frontmatter,
    _absorb_frontmatter_objects,
    _normalize_documents,
    _normalize_generate_payload,
    _materialize_drafts,
    _print_checker,
    _token_usage_dict,
)

from freshlatch.eval.x1_drafts.io import (
    _atomic_write_text,
    _write_manifest,
)

from freshlatch.eval.x1_drafts.batch import (
    _is_int,
    _expected_rel_dir,
    _batch_canon,
    _prompt_sha256,
    _decoding_fields,
    _batch_fingerprint,
    _optional_positive_int,
    _validate_batch,
    _load_spec,
    _parse_pricing_block,
    _parse_pricing,
    _parse_max_cny,
    _is_pair,
    _file_count,
    _question_allowance,
    _per_chunk_tokens,
    _output_token_upper,
    _input_token_upper,
    _chunk_count_line,
    _example_sections,
    _prompt_document_example,
    _build_batch_prompt,
    _flag_skeleton,
    _estimate_spec,
    _format_estimate,
    _cost_cny,
    _flag_output_upper,
)

from freshlatch.eval.x1_drafts.documents import (
    _split_frontmatter,
    _duplicate_frontmatter_key,
    _doc_id_ok,
    _parse_blocks,
    _validate_blocks,
    _validate_markdown,
    _validate_batch_documents,
    _prefix_question_ids,
    _question_as_of_error,
    _question_ids,
    _load_out_questions,
    _is_public_corpus_meta,
    _scan_doc_keys,
)

from freshlatch.eval.x1_drafts.ledger import (
    _load_manifest,
    _usage_pair,
    _finite_money,
    _held_charge_error,
    _recorded_cost_total,
    _spend_below_recorded,
    _manifest_anomaly,
    _resume_action,
    _recorded_doc_rel_ok,
    _discard_committing,
    _drop_committing_question_ids,
    _discard_open_commits,
    _public_doc_ids,
    _manifest_body,
    _flush_manifest,
    _commit_batch,
)

from freshlatch.eval.x1_drafts.generate import (
    _build_parser,
    _NoThinkingCreate,
    _pin_create,
    _pin_flag_thinking_off,
    _write_failure_out,
    _run_generate,
)

from freshlatch.eval.x1_drafts.flagging import (
    _load_flag_questions,
    _flag_prompt,
    _flag_input_dir,
    _flag_ledger_path,
    _read_flag_ledger,
    _write_flag_ledger,
    _write_flag_payload,
    _run_flag,
)

from freshlatch.eval.x1_drafts.cli import (
    main,
)

