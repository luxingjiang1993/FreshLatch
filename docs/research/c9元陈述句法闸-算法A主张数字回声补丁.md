# c9 元陈述句法闸 · 算法 A 补丁（主张数字回声）

> 工单:#241（规格 `docs/spec/16-must-unknown-c9-护栏.md`）。性质:**工程修复,非判据修订**——金标 gold.json、must_unknown 口径不动。  
> 本页是 ADR-0008 / `docs/research/c9元陈述句法闸设计评估.md` 的**算法边界增量补丁**,不是推翻原选型。  
> 预登记:算法 A 边界写于活模验收之前;事后改边界 = 本补丁作废重签。

## §问题 + 前置约束

**问题**:#239 关单后 N=1 gold(`report-20260930-214533`)出现新逃逸——c9 期望 unknown、机判 stale。根因不是闸消失,而是 reason 进化为「元标记 + 主张数字回声」:剥除元子句后残留含 `70%` 的子句,`70` 来自主张 statement 复述而非 T1 独立数值反证,骗过 ADR-0008 步骤 4「含阿拉伯数字 ⇒ 放行」。

**前置约束(不得违反)**:

1. ADR-0008 选型仍成立:确定性句法启发式;禁止 LLM judge;禁止闸读 T1 正文语义比对。
2. 禁止改 gold / 提高 `DIMENSION_RECOVERY_QUOTA` / 回滚 #239 换维教义 / claim_id 特判。
3. 缺省不传 `claim_statement` 时,对无回声依赖的历史形状打回不得弱化。
4. 误伤只允许 stale→unknown(不对称安全)。

## §候选路线(本增量)

| 候选 | 原理 | 结论 |
|------|------|------|
| A. 主张陈述数字集合作回声黑名单 | 残留子句数字若**全部**出现在 claim.statement,不算实质锚 | ✅ **拍板** |
| B. 残留须含独立变化谓词 | 更语义,仍须启发式 | ❌ 易误伤,须另开评估 |
| C. 仅扩标记词表 | 「停追踪」等 | ❌ 不够:本逃逸已含旧标记 |

## §拍板(算法 A 增量)

在原算法步骤 4 上增加:

```text
若调用方传入 claim_statement:
  对含数字的非元子句,抽取数字串(先剥除理由中的 cN 主张编号噪声);
  若全部数字均以独立数位边界出现在 claim_statement 中 ⇒ 该子句不算实质锚(继续扫描);
  若存在不见于 statement 的数字 ⇒ 实质锚,放行。
缺省 claim_statement=None ⇒ 行为与 ADR-0008 当日一致(有数字即实质锚)。
```

API:`is_meta_only_disproof(reason, *, claim_statement=None)`。Lead/Critic `mark_stale` 与 `rule_gate` 不变量 6 共用,传入 `Claim.statement`。打回码仍 `META_ONLY_DISPROOF`。

## §已知边界增量

- **B4(回声)**:主张数字回声与独立数值锚共存时,因「非全部在 statement」仍放行——正确。  
- **B5(编号噪声)**:理由中的 `c9`/`c12` 等主张编号剥除后再抽数字,避免单数字误当独立锚。  
- **B6(未传 statement)**:工具/闸接线必须传 statement;纯函数缺省路径不保证拦回声形(契约由接线保证)。

## §验收分层

- **确定性**:修后 c9 实录 reason + 最小回声合成形打回;C9_RUN2/C9_REPRO2 打回;C3/C7 合法锚放行;元+独立锚放行。  
- **表现层(N=1 冒烟)**:`qwen-flash`·temp=`0.0`·seed=`None`;点名 c9=unknown、c3/c7=stale、must_stale→fresh=0;不报方差;all_hit 非硬 Exit。

## §面试讲法(增量)

**Q:为什么不改 gold 把 c9 改成 stale?**  
A:尺子没变。T1 仍只有停追踪元陈述,正确档仍是 unknown。变的是 harness 被新逃逸形状骗过——修闸对齐既有判据,同 ADR-0008 §4。

**Q:传入 statement 是不是闸在读语义?**  
A:不是。只做数字串集合的子串/边界比对,零模型、零证据正文 I/O。statement 本就是闸已持有的 Claim 字段。
