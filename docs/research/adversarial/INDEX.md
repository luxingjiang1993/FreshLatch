# Adversarial Catalog INDEX

**catalog_version**: `0.1.0`  
**生成说明**: Batch 5 骨架；全部 `status=skeleton`；禁止填写通过率。

## FG 族（假绿 / 对照指针）

| id | family | title | status | catalog_version | prereg_ptr | gold_ptr | notes |
|---|---|---|---|---|---|---|---|
| ATK-FG-01 | FG | 无工具假绿对照（旧仪器指针） | skeleton | 0.1.0 | `docs/evidence/w4/false-green-control-prereg.md`；ACCEPTANCE 假绿分条 | （不复制） | 不重审成立；目录≠已过 |
| ATK-FG-02 | FG | 假绿仪器 C（只读指针） | skeleton | 0.1.0 | `docs/evidence/w4/false-green-control-c-prereg.md` | （不复制） | 只读；禁改 prompt/通过线 |
| ATK-FG-03 | FG | 主链抗假绿（预登记指针） | skeleton | 0.1.0 | `docs/evidence/w4/main-chain-anti-false-green-prereg.md`（若缺则评估/ACCEPTANCE 指针） | （不复制） | 与 γ 分条；γ 通过≠本条已过 |

## CS 族（指针节 — 正文在 β）

| id | family | title | status | catalog_version | prereg_ptr | gold_ptr | notes |
|---|---|---|---|---|---|---|---|
| ATK-CS-01 | CS | 语料篡改 renew 负例 | skeleton | 0.1.0 | `docs/research/β-checksum攻击面用例集合设计评估.md` | — | 本目录不复制机械期望 |
| ATK-CS-02 | CS | 套套哨兵（禁读库列） | skeleton | 0.1.0 | 同上 | — | 同上 |
| ATK-CS-03 | CS | 空 claimed 拦截 | skeleton | 0.1.0 | 同上 | — | 同上 |
| ATK-CS-04 | CS | 正例对照（非断路） | skeleton | 0.1.0 | 同上 | — | 同上 |

## 禁升格（摘录）

- 不得声称「INDEX 有行 ⇒ 对抗套件已通过」。  
- 不得在本文件增加统计结论列或填写通过率。
