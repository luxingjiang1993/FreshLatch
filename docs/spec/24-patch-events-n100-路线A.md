# patch_events n=100 · 路线 A 推进规格

> 基线：`main` `a5e424c`（#416）。决议 #420 · 地图 #419 · ADR-0034。  
> 评估见 `docs/research/patch_events-n100路线与阶段成功收口设计评估.md`。  
> 口径：`docs/evidence/当前可说口径.md`。

## 已钉死

- 路线 **A**：继续现有 `PREREG.md`，做满 n=100（n=30 超集）。不回写 PREREG。
- n=30：k=3；T-C / T-B1 / T-B2 都不成立。既有 `formal-generations.jsonl` 行不动。
- B2 既有 21 回声 + 9 小改：不重跑、不加强提示词。
- 阶段成功：结果 **乙** 也算；甲为 Findings 前提；丙不得称「T 更好」。
- 「T 更好」只由同一次 `compare_primary` 判决；不是 implement 验收项。
- 正式发模型：仅真人授权会话；云端默认禁发。
- 五处冻表面仍冻在 `101c81e`，直到甲/乙/丙收口且数字来自同一次比较。

## 用户故事（工程可开票）

1. As a 构造审计者, I want n=100 名单是 pe_v2 清单超集且 gap 写入 RESULT, so that 不事后改配额。
2. As a 生成操作者, I want 显式 `--formal` 才发送四臂请求且缺温度/种子则作废, so that 禁止事后补 seed。
3. As a 统计抄表者, I want 回放已保存行后只调用一次 `compare_primary` 并抄入 RESULT, so that 三行 false-accept 同源。
4. As a 次要指标读者, I want 自然放行、误拒、错改、可复验、消融、延迟、成本有写入缝, so that 未填格可被真跑填上。
5. As a 抽检操作者, I want 按 PREREG 导出抽检配对与用户标签入口, so that 人可写标签、算一致率与 κ。
6. As a 论文作者, I want 附加预注册草稿可起草但不回改 PREREG, so that 两名真人盲审有独立协议页。

## 明确不要做

- 回写 `PREREG.md`；夹具填主表；改成立定义凑甲
- 把 `claim_text` 当 `after_text`；为抬差削弱 B1/B2
- 用检索 Recall/MRR/nDCG 声称放行闸成立
- 未做附加预注册就写「两名真人盲审」
- 未收口就改五处冻表面或开写论文主结论
- 仓外试改产物写入正式 jsonl / RESULT 主表
- 在路线 A 下更换 T 的正式生成配置（须改定义 → 路线 B）

## 依赖与顺序

1. 人：可选仓外试改 T（闸见 ADR-0034）→ 决定是否仍走 A
2. 工程：名单确认 →（人授）四臂生成 → 回放抄表 → 消融/次要格 → 抽检入口
3. 人并行：附加预注册 + 双人盲审；检索全库金标另轨
4. 另图：「不能保持绿」测量
5. 收口后才动冻表面

## 验收总闸

- `python -m compileall -q src`
- `pytest`（各票覆盖断言）
- RESULT 主比较数字若填写，必须可指回同一次 `compare_primary` 输出
- `PREREG.md` 相对本规格基线零 diff（除本规格明确禁止编辑）
