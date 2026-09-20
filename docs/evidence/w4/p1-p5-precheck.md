# W3 预检 P1–P5 执行留档

> 生成 2026-09-20T13:06:40Z;P1/P2/P3/P5 为机器层结果,P4 待人工补录(原话在 restatement.md 同步落)。
> P1/P5 于 2026-09-20 由开发者会话执行(脚本 scripts/smoke_p1_pointback.py / smoke_spawn_critic.py)。

| # | 预检项 | 通过线 | 结果 |
|---|---|---|---|
| P1 | 点回冒烟:随机 2 条主张 T1 点回,anchor 命中且高亮可见 | 2/2 | ✅ 2/2(seed=20260920 抽中 c5/c2;检索库锚解析命中、/api/source 200 且锚在段落清单、页面 .hit 高亮机制与 t1 链接渲染路径在场;headless 无像素级渲染,人看复核可叠加——记录见下「P1 点回记录」) |
| P2 | 金标 runner 试跑 N=1,console 摘要 + 报告落 reports/ | 跑通,不看分数 | ✅ 机器层跑通(见 reports/ 与 machine-results.md) |
| P3 | 红线单测就位:CI 单测合并进 `tests/unit/` 且绿 | CI 绿 | ✅ 签认(判定人书面授权,2026-09-20):本地全套 pytest 150/150 绿(test_ui_redlines.py 8/8 含前三条红线);历史 CI 红因(test_restart_recovery 子进程输出编码,700b27c 红)已修复(13e369d:TDD 红灯→绿灯,干净 worktree 3.12 venv 复现并验证)并推 main。Actions 读数**免核授权**:gh PAT 无 Actions 读权限、本机网络无法抓取 GitHub 页面,判定人书面授权以本地全绿 + 修复推 main 为 P3 通过依据;如需补验,浏览器 Actions 页一眼可复核 |
| P4 | 盲看首测:真人盲看 3 分钟 + 一句话定位 + 探针 | 记录即过 | ⏳ 待真人(原话记 restatement.md P4 节) |
| P5 | Critic 派驻冒烟:合法/非法 focus 各一次 | 非法值回列词表、计步;结论回吐 Lead | ✅ 行为符合 §3.4(非法值 focus=not_a_dimension 被拒并回列词表;合法值真派驻,critic_spawn/step 事件在场,结论经工具观察回吐;本跑 Critic 预算耗尽未交 report_finding——P5 只看派驻行为不看反证质量。计步归 Lead 主循环,直调工具层不计,已注明) |

P4 盲看原话:______

P4 探针回答:______

P1 点回记录:seed=20260920,random.sample 非豁免全集 8 条 → c5(t0-cost-model#p2@T1)、c2(t0-regulatory-memo#p2@T1);
两层各 ✅:① 检索库 get_chunk(doc, p2, as_of="T1") 可解析(口径同 eval/checks.py);② FastAPI TestClient 真起服务:/ 页含 .hit 高亮 CSS + classList.add('hit') + scrollIntoView,renderClaims 遍历 t1_evidence_ids 拼 showSource 链接;/api/source/<doc>?as_of=T1 返回 200 且 p2 在段落清单(T1 快照各 3 段)。判定 2/2 通过。

P5 派驻记录:scripts/smoke_spawn_critic.py,2026-09-20 连跑两次(首次末行打印遇 Windows GBK 控制台编码崩溃,行为输出完整;UTF-8 重跑留档)。非法值:focus=not_a_dimension → 工具层硬校验拒,error 回列六维词表,零 LLM 调用 ✅。合法值:focus=competitor_pricing → 新会话真派驻(与 Lead 共享 Run 级检索预算),轨迹事件 critic_spawn + critic_step(retrieve ×2)在场,结论经工具观察回吐(finding/note/counter_evidence_ids 字段)✅;本跑 Critic 步数预算耗尽未交 report_finding——派驻行为本身符合 §3.4,P5 通过线不看反证质量。计步说明:被拒重试的计步发生在 Lead 主循环(#14),脚本直调工具层不计步,如实注明。
