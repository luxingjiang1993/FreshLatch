# G2 should-abstain 金标表 v0（工程金标）

日期：2026-10-16  
状态：工程金标（由已合单测升格）；主人可事后抽检「保持/争议」  
权威枚举：`ABSTENTION_REASONS`（`src/freshlatch/roles/loop.py`）  
禁：写入 `data/eval/gold.json`；禁 SESOI；禁注册 `counted_as_pass`

| id | label | expected | 场景 | 既有锚点（不得改其语义） |
|----|-------|----------|------|--------------------------|
| G2-IE-01 | must_abstain | `insufficient_evidence` | 零/空 hits → 不得 fresh | AG-02 / RAG-01 |
| G2-CR-01 | must_abstain | `cite_outside_registry` | cite ∉ turn registry | EV-02 / FC-CITE |
| G2-NM-01 | must_abstain | `numeric_mismatch` | 假数字 quote | B-01 `test_fake_quote_fixture_is_not_fresh_and_names_numeric_mismatch` |
| G2-CF-01 | must_abstain | `conflicting_evidence` | 互斥 @T1 对 | B-02 `test_exclusive_fixture_is_not_fresh_and_names_conflicting_evidence` |
| G2-RN-01 | must_block_renew | `RENEW_NO_EVIDENCE` | 无 T1 续命 blocked | `tests/unit/test_renew.py` / `test_ui_latch.py` |
| G2-OK-01 | must_not_abstain | （不得误判为上表码） | 足证据对照路径 | B-01 match / B-02 agreeing 类 |

砍行：v0 **不含** `grade_ambiguous` / `grade_incorrect_exhausted`（可 Phase D 扩表）。

互相同意栏（抽检用）：每行只答 `保持|争议`。
