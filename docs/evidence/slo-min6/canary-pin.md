# SLI 6 · 冻结 canary 集与版本针

> **生产观测 ≠ 乙尺。**  
> **Canary ≠ 乙尺。**  
> 本页是 [#562](https://github.com/luxingjiang1993/FreshLatch/issues/562)（Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)）的 pin 记录。跑法在 [`docs/ops/冻结金标canary跑法.md`](../../ops/冻结金标canary跑法.md)。  
> 本页**没有** pass rate。未跑。禁止把下面的 blob 读成「已经 3/3」或「可以发车」。  
> 未编辑 `RESULT-Y` / `PREREG-Y` / SESOI。未改 `data/eval/gold.json`。金标不进生产 score。  
> 日期：2026-10-12（Asia/Shanghai）。预锁先于任何本协议的 pass rate。

## 预锁（dataset pin）

| 项 | 值 |
|----|----|
| 文件 | `data/eval/gold.json` |
| 读取 | 只读。本记录不写回 |
| git blob | `c7a14683de82bb795fd67bbb505bd6f7128b7c2a` |
| 所在 tip | `642733bc97ff1fa7183aeb21aa68f4651b327f6d` |
| 桶 | `must_stale` |
| 成员 | `c1`、`c2`、`c3`、`c7` |
| canary 集大小 | 4 |
| 当前金标门 | 每一遍 hits == 4，期望判定 `stale`。不得低于这一门 |
| 周报列 | `canary_pin` = 上述 blob + `\|must_stale` |

这个 blob 是 tip 上该文件的内容标识，不是一次 canary 执行的成绩。

## code pin

| 项 | 值 |
|----|----|
| 协议落盘基线 | `642733bc97ff1fa7183aeb21aa68f4651b327f6d` |
| 本页是否代表一次 canary 执行 | 否 |
| 周报 `code_pin` | `<未跑>`。真跑之前另写执行 sha，跑后不得改 |

## 不在分母里

| 文件 | blob | 原因 |
|------|------|------|
| `data/eval/retrieve_hard_gold.json` | `615eeca6aa04752842513f3594b14841985e7531` | Hard-Gold 检索骨架（n=20，`level=hard_gold_skeleton`）。ADR-0033：主张金标不得顶替该门。不混进 pass rate |

## 防火墙

- [x] 未填 pass rate，未写 0% 或 100%  
- [x] 未回写 Y  
- [x] 掉线处置尚未触发（因为未跑）。触发后的句子只允许是「停发列车讨论」  
- [x] Canary ≠ 乙尺
