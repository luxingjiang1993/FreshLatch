# 模型统一管理 — 状态

- **批准**：APPROVED（主人 Oriental Ronin，2026-10-15）
- **本切片**：S0、S1 进行中。本分支落地计划文档与字面量收口。Trust=Watch，未合并前不标完成。
- **后续 pending（不在本 PR）**：S6 连通性体检、S7 正式跑前闸。S2 profile 与 S3 运维文档已在 main。
- **S3 落点**：[`docs/ops/model-profiles.md`](../../ops/model-profiles.md)（冒烟 `scripts/smoke_model_resolve.py`，不发网络）。未合并前不标完成。
- **S5 落点**：[`docs/ops/model-fit-report.md`](../../ops/model-fit-report.md)（模板 [`docs/ops/model-fit-scorecard.template.md`](../../ops/model-fit-scorecard.template.md)；首轮 [`docs/evidence/model-fit/2026-10-15.md`](../../evidence/model-fit/2026-10-15.md)；只读 `scripts/model_fit_review.py`，默认不发网络、不依赖 LM Studio）。Trust=Watch。未合并前不标完成。分析不改 registry 生产默认模型 id。
- **S4**：deferred。C-04 manifest 对齐，默认不做
- **ADR**：不新开。理由见 [01-plan.md](01-plan.md) 文首
- **不做**：不改 floors / gold / x1 / production arm；不开 C-04；不写 RESULT；不把 C-04 manifest 的 `generator_model` / `nli_model` 从 null 改掉；不发明 SESOI。fixtures 绿不等于注册分
- **S1 仪器**：`patch_events_verify.py` 改为从 `MODEL_REGISTRY["nli"]` 读同一 model id 之后，`VERIFY_PY_SHA256` 按新的 LF 字节重钉。τ、ok 公式、model id 字符串未改。历史 evidence 里的旧 sha256 是当时跑次的记录，本 PR 不改那些文件
