# 成立 patch 实验 · 正式结果（C-04）

口径：`docs/evidence/patch-establishment/PREREG.md`（Amendment-01/02）。
主比较只认 **T−C**（L1：点估计 > 0 且 95% CI 下界 > 0）。`sesoi=null`。本页不发明 SESOI。
`second_formal_y=false`。不得标产品 L5。不得称优于 RARR·KPR。不得改判历史结果丙。

## 跑针

- **代码针**：`471cb665e3685d3acdc7b88603aaa75cc2ded48c`
- **授权**：主人 Oriental Ronin 明文「跑」+ Amendment-02 + `--authorize-run`
- **built_n** = 91（target_n=100；gap_n=9；不得把 91 假装成 100）
- **生成路径**：`docs/evidence/patch-establishment/formal-generations.jsonl`（n_lines=182；sha256=`8593bf784d75edbb910c59b1342a998bf567cb3728b3c1b6be11701f3d5025da`）
- **解码**：model=`qwen-flash`；temperature=`0`；Decoding.seed=`20261007`；API seed=`None`；n_boot=`10000`；k_min=`10`
- **NLI**：`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`；τ=`0.5`（禁止 exact-match 回退）
- **run_status** = `ran`
- **measurement_status** = `measured`

## 主比较（T−C · L1）

| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立（C-04 L1） |
|---|---|---|---|---|---|
| T 对 C | false-accept rate | 0.1515151515151515 | -0.07407407407407407 | 0.3823529411764706 | 不成立 |

- **固定放行数 k** = 33
- **k_min** = 10
- **establishment.status** = `not_established`
- **counted_as_pass** = `false`
- **product_l5** = `false`
- **sesoi** = `null`

## 丙防火墙

- 历史 `docs/evidence/patch-events/RESULT-Y.md` 分层仍是结果丙。本页未改写。
- B-04 夹具 `counts_as_establishment=false`。
- 不改 floors。不改默认臂。`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。

## 边界

- 本页不是路线 Y 的另一次正式主跑。
- 即便成立格通过，本票仍不得单独把产品标成 L5。
- 同一预注册禁止第二次正式主跑充数。

