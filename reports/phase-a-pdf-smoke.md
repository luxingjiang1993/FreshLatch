# Phase A PDF 冒烟（#165）

- 样本：`data/smoke/phase-a-smoke.pdf`（合成脱敏文本，无真实个人信息）
- 路径：抽出 PDF 字面量 → 打 `## pN` 同构锚 → ingest → `retrieve`
- 命中锚：`SMOKE-ANCHOR-165`
- 本样本不进入主指标 n，也不写入 `data/corpus/`
- 主切块契约仍是结构锚，不是字数窗；不做表格 / HTML / OCR
- 重建：`PYTHONPATH=src python3 scripts/smoke_pdf_ingest.py`（exit 0 即冒烟通过）
