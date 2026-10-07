# 分差题抽查清单（给 Oriental Ronin 看）

这份清单由模型按下面的固定规则起草，供 Oriental Ronin 人工审。
还没有人逐条看过。这里的「建议」不是切换决定，也不是人工审核结论。
数据是模型双标 + Ronin 代理人（模型）代审，不是人工逐行审核。

分差：两边前 10 条的证据编号集合或顺序不同。只比有没有撞上金标不够，名次不同也算。
分母只含作答臂（score_role=arm）。护栏题不在这里。

规则：
- 三条路的前 10 条都没有金标 → 需要改题。
- 只有一边撞上金标 → 建议走撞上的那一边（词法写成「保持 bm25」）。
- 两边都撞上，但一边把金标排得更靠前 → 建议走更靠前的那一边。
- 撞上和排位都没变，只是旁边材料换了次序 → 保持 bm25。
- 慢查询 p95 超过 800 毫秒的臂，不写成可议。

## 条数

- 词法 vs 混合：224 题。保持 bm25 172，可议 hybrid 48，可议 hybrid+rerank 0，需要改题 4。
- 词法 vs 重排：224 题。保持 bm25 172，可议 hybrid 0，可议 hybrid+rerank 48，需要改题 4。
- 混合 vs 重排：208 题。保持 bm25 149，可议 hybrid 36，可议 hybrid+rerank 19，需要改题 4。

## 词法 vs 混合

### 1. `p1-lx-01-new`

- 问：数据出境安全评估办法规定评估结果有效期为几年？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p13@T0
- 金标要点：通过数据出境安全评估的结果有效期为2年
- 词法前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p5@T0 4.p1-cac-o11#p3@T0 5.p1-cac-o11#p15@T0 6.p1-cac-o11#p11@T0 7.p1-cac-o11#p7@T0 8.p1-cac-o11#p12@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p2@T0
- 混合前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p11@T0 3.p1-cac-o11#p15@T0 4.p1-cac-o11#p5@T0 5.p1-cac-o11#p3@T0 6.p1-cac-o11#p1@T0 7.p1-cac-o11#p12@T0 8.p1-cac-o11#p14@T0 9.p1-cac-o11#p7@T0 10.p1-cac-o11#p17@T0
- 重排前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p11@T0 3.p1-cac-o11#p1@T0 4.p1-cac-o11#p7@T0 5.p1-cac-o11#p15@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p3@T0 8.p1-cac-o11#p14@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p12@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 2. `p1-lx-02-new`

- 问：个人信息出境标准合同办法要求合同生效后多少个工作日内备案？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p6@T0
- 金标要点：在标准合同生效之日起10个工作日内向所在地省级网信部门备案
- 词法前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p7@T0 5.p1-cac-o13#p4@T0 6.p1-cac-o13#p8@T0 7.p1-cac-o13#p2@T0 8.p1-cac-o11#p4@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p15@T0
- 混合前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p8@T0 5.p1-cac-o13#p7@T0 6.p1-cac-o13#p2@T0 7.p1-cac-o11#p17@T0 8.p1-cac-o13#p4@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p6@T0
- 重排前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p4@T0 5.p1-cac-o13#p8@T0 6.p1-cac-o13#p7@T0 7.p1-cac-o13#p2@T0 8.p1-cac-o11#p17@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p6@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 3. `p1-lx-03-new`

- 问：数据出境安全评估办法：省级网信部门收到申报材料后几个工作日内完成完备性查验？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p6@T1
- 金标要点：自收到申报材料之日起5个工作日内完成完备性查验
- 词法前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.s6-d1-c1-memo#p2@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p12@T1 6.p1-cac-o11#p11@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p6@T1 9.p1-cac-o13#p6@T1 10.p1-cac-o16#p7@T1
- 混合前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.p1-cac-o11#p15@T1 5.s6-d1-c1-memo#p2@T1 6.p1-cac-o11#p12@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p7@T1 9.p1-cac-o13#p6@T1 10.p1-cac-o11#p13@T1
- 重排前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p2@T1 6.p1-cac-o16#p7@T1 7.s6-d1-c1-memo#p2@T1 8.p1-cac-o13#p6@T1 9.p1-cac-o11#p12@T1 10.p1-cac-o11#p13@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 4. `p1-lx-04-new`

- 问：数据出境安全评估办法规定国家网信部门发出书面受理通知书后多少个工作日内完成评估？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p11@T1
- 金标要点：自向数据处理者发出书面受理通知书之日起45个工作日内完成数据出境安全评估
- 词法前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p6@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p15@T1 6.p1-cac-o11#p12@T1 7.p1-cac-o16#p6@T1 8.p1-cac-o11#p2@T1 9.p1-cac-o20#p3@T1 10.p1-cac-o16#p11@T1
- 混合前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p6@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p12@T1 6.s6-d1-c1-memo#p2@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p7@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o11#p17@T1
- 重排前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p15@T1 4.p1-cac-o11#p2@T1 5.p1-cac-o16#p7@T1 6.p1-cac-o11#p6@T1 7.s6-d1-c1-memo#p2@T1 8.p1-cac-o16#p11@T1 9.p1-cac-o11#p12@T1 10.p1-cac-o11#p17@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 5. `p1-lx-05-new`

- 问：数据处理者对评估结果有异议的，收到结果后多少个工作日内可以申请复评？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p12@T1
- 金标要点：在收到评估结果15个工作日内向国家网信部门申请复评
- 词法前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p6@T1 6.s6-d1-c1-memo#p3@T1 7.p1-cac-o11#p13@T1 8.p1-colaw-liquidation#p6@T1 9.p1-cac-o11#p15@T1 10.p1-cac-o11#p2@T1
- 混合前 10：1.p1-cac-o11#p12@T1 2.s6-d1-c1-memo#p2@T1 3.p1-cac-o16#p9@T1 4.p1-cac-o11#p11@T1 5.p1-cac-o11#p13@T1 6.s6-d1-c1-memo#p3@T1 7.p1-cac-o11#p6@T1 8.p1-cac-o11#p15@T1 9.p1-cac-o13#p6@T1 10.s4-d0-t1-91-eval#p2@T1
- 重排前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p6@T1 6.p1-cac-o11#p13@T1 7.s6-d1-c1-memo#p3@T1 8.p1-cac-o11#p15@T1 9.p1-cac-o13#p6@T1 10.s4-d0-t1-91-eval#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 6. `p1-lx-06-new`

- 问：个人信息出境认证办法自哪一天起施行？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o20#p9@T1
- 金标要点：本办法自2026年1月1日起施行
- 词法前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p9@T1 5.p1-cac-o20#p1@T1 6.p1-cac-o20#p6@T1 7.p1-cac-o20#p2@T1 8.s6-d1-c3-memo#p2@T1 9.p1-cac-o16#p3@T1 10.p1-cac-o13#p1@T1
- 混合前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p2@T1 5.p1-cac-o20#p6@T1 6.p1-cac-o20#p1@T1 7.p1-cac-o20#p7@T1 8.p1-cac-o16#p8@T1 9.p1-cac-o16#p11@T1 10.s6-d1-c3-memo#p2@T1
- 重排前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p2@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o20#p6@T1 7.p1-cac-o20#p1@T1 8.p1-cac-o20#p7@T1 9.p1-cac-o16#p11@T1 10.s6-d1-c3-memo#p2@T1
- 建议：保持 bm25
- 理由：词法的前 10 条里有金标，混合没有。

### 7. `p1-lx-07-new`

- 问：公司法规定，通过简易程序注销公司登记的公告期限不少于多少日？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p6@T1
- 金标要点：公告期限不少于二十日
- 词法前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p1@T1 5.s6-d2-g2-memo#p3@T1 6.s6-d1-t1-91-patch#p1@T1 7.p1-colaw-capital#p2@T1 8.p1-colaw-liquidation#p3@T1 9.p1-colaw-equity#p4@T1 10.p1-colaw-capital-call#p3@T1
- 混合前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g2-memo#p1@T1 4.p1-colaw-liquidation#p3@T1 5.p1-colaw-capital#p1@T1 6.s6-d2-g1-memo#p1@T1 7.s6-d2-g2-memo#p3@T1 8.p1-colaw-capital-call#p3@T1 9.s6-d2-g1-memo#p2@T1 10.p1-colaw-equity#p5@T1
- 重排前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g2-memo#p1@T1 4.p1-colaw-capital#p1@T1 5.s6-d2-g2-memo#p3@T1 6.p1-colaw-liquidation#p3@T1 7.p1-colaw-capital-call#p3@T1 8.s6-d2-g1-memo#p2@T1 9.p1-colaw-equity#p5@T1 10.s6-d2-g1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 8. `p1-lx-08-new`

- 问：股东对失权有异议的，应当自接到失权通知之日起多少日内向人民法院提起诉讼？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p3@T1
- 金标要点：自接到失权通知之日起三十日内，向人民法院提起诉讼
- 词法前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p3@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-liquidation#p3@T1 6.p1-colaw-equity#p1@T1 7.p1-colaw-liquidation#p6@T1 8.s6-d3-t1-91-notice#p1@T1 9.s6-d2-g3-memo#p1@T1 10.p1-cac-o11#p12@T1
- 混合前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p3@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-liquidation#p3@T1 6.p1-colaw-equity#p1@T1 7.p1-colaw-liquidation#p6@T1 8.s6-d2-g3-memo#p1@T1 9.p1-colaw-capital-call#p1@T1 10.p1-colaw-liquidation#p5@T1
- 重排前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p5@T1 3.p1-colaw-equity#p3@T1 4.p1-colaw-equity#p1@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-liquidation#p3@T1 7.p1-colaw-liquidation#p6@T1 8.p1-colaw-liquidation#p5@T1 9.p1-colaw-capital-call#p1@T1 10.s6-d2-g3-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 9. `p1-lx-09-new`

- 问：公司法（2018）规定一个自然人可以投资设立几个一人有限责任公司？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-oneperson#p3@T0
- 金标要点：一个自然人只能投资设立一个一人有限责任公司
- 词法前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-governance#p3@T0 4.p1-colaw-oneperson#p1@T0 5.p1-colaw-governance#p2@T0 6.p1-colaw-equity#p4@T0 7.p1-colaw-governance-board#p3@T0 8.p1-colaw-equity#p5@T0 9.p1-colaw-governance-board#p2@T0 10.p1-colaw-capital#p1@T0
- 混合前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-oneperson#p1@T0 4.p1-colaw-governance-board#p3@T0 5.p1-colaw-governance-board#p2@T0 6.p1-colaw-governance#p2@T0 7.p1-colaw-equity#p4@T0 8.p1-colaw-governance-supervisor#p1@T0 9.p1-colaw-capital#p2@T0 10.p1-colaw-governance#p3@T0
- 重排前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-equity#p4@T0 4.p1-colaw-governance#p3@T0 5.p1-colaw-governance-board#p3@T0 6.p1-colaw-governance-board#p2@T0 7.p1-colaw-governance#p2@T0 8.p1-colaw-governance-supervisor#p1@T0 9.p1-colaw-oneperson#p1@T0 10.p1-colaw-capital#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 10. `p1-lx-10-new`

- 问：2023年全国国内生产总值修订后的现价总量是多少亿元？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p2-gdp-national#p1@T1
- 金标要点：2023年全国国内生产总值修订后的现价总量是1294272亿元
- 词法前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s7-d2-t1-04-data#p2@T1 7.p1-cac-o13#p8@T1 8.s2-d3-t1-91-minutes#p1@T1 9.p1-cac-o16#p11@T1 10.s6-d2-g2-memo#p3@T1
- 混合前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s5-d3-t1-05-report#p1@T1 6.s5-d1-t1-03-report#p2@T1 7.s4-d2-t1-91-model-v3#p2@T1 8.s7-d2-t1-04-data#p2@T1 9.s5-d3-t1-05-report#p2@T1 10.s6-d3-t1-03-memo#p3@T1
- 重排前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s5-d1-t1-03-report#p2@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s7-d2-t1-04-data#p2@T1 8.s5-d3-t1-05-report#p1@T1 9.s5-d3-t1-05-report#p2@T1 10.s6-d3-t1-03-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 11. `p1-lx-11-new`

- 问：公司法规定公司减少注册资本，应当自股东会作出决议之日起几日内通知债权人？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p3@T1
- 金标要点：自股东会作出减少注册资本决议之日起十日内通知债权人
- 词法前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-governance#p2@T1 7.p1-colaw-governance#p3@T1 8.p1-colaw-capital#p1@T1 9.s6-d2-g1-memo#p1@T1 10.p1-colaw-liquidation#p4@T1
- 混合前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-equity#p5@T1 3.p1-colaw-liquidation#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-governance#p3@T1 7.p1-colaw-liquidation#p4@T1 8.s6-d2-g1-memo#p1@T1 9.p1-colaw-equity#p3@T1 10.p1-colaw-governance#p2@T1
- 重排前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-equity#p3@T1 7.p1-colaw-governance#p2@T1 8.p1-colaw-governance#p3@T1 9.p1-colaw-liquidation#p4@T1 10.s6-d2-g1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 12. `p1-lx-12-new`

- 问：数据出境安全评估办法所称重要数据是指什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p16@T0
- 金标要点：本办法所称重要数据，是指一旦遭到篡改、破坏、泄露或者非法获取、非法利用等，可能危害国家安全、经济运行、社会稳定、公共健康和安全等的数据。
- 词法前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p3@T0 4.p1-cac-o11#p15@T0 5.p1-cac-o11#p13@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p2@T0 8.p1-cac-o11#p7@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p11@T0
- 混合前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p3@T0 4.p1-cac-o11#p15@T0 5.p1-cac-o11#p7@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p13@T0 8.p1-cac-o11#p2@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p4@T0
- 重排前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p13@T0 4.p1-cac-o11#p2@T0 5.p1-cac-o11#p3@T0 6.p1-cac-o11#p15@T0 7.p1-cac-o11#p7@T0 8.p1-cac-o11#p5@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p4@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 13. `p1-mh-02-new`

- 问：非关基企业出境一般个人信息（不含敏感个人信息），旧规和新规分别到多少人就要报安全评估？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p2@T1；p1-cac-o16#p7@T1
- 金标要点：自上年1月1日起累计向境外提供10万人个人信息；自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）
- 词法前 10：1.s6-d1-c2-memo#p1@T1 2.s6-d1-c3-memo#p3@T1 3.p1-cac-o20#p2@T1 4.p1-cac-o16#p5@T1 5.p1-cac-o13#p3@T1 6.p1-cac-o20#p5@T1 7.p1-cac-o16#p7@T1 8.p1-cac-o11#p2@T1 9.p1-cac-o16#p6@T1 10.p1-cac-o13#p4@T1
- 混合前 10：1.s6-d1-c2-memo#p1@T1 2.s6-d1-c3-memo#p3@T1 3.p1-cac-o20#p2@T1 4.p1-cac-o16#p7@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o16#p5@T1 7.p1-cac-o13#p3@T1 8.p1-cac-o11#p2@T1 9.s6-d1-c4-memo#p1@T1 10.p1-cac-o13#p2@T1
- 重排前 10：1.s6-d1-c2-memo#p1@T1 2.p1-cac-o16#p7@T1 3.p1-cac-o16#p5@T1 4.p1-cac-o11#p2@T1 5.s6-d1-c4-memo#p1@T1 6.s6-d1-c3-memo#p3@T1 7.p1-cac-o20#p2@T1 8.p1-cac-o16#p8@T1 9.p1-cac-o13#p3@T1 10.p1-cac-o13#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 14. `p1-mh-03-new`

- 问：只算一般个人信息、不涉及敏感个人信息的话，签标准合同这条路，老办法和新规定各卡在多少人？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p2@T1；p1-cac-o16#p8@T1
- 金标要点：自上年1月1日起累计向境外提供个人信息不满10万人的；处理个人信息不满100万人的；自当年1月1日起累计向境外提供10万人以上、不满100万人个人信息（不含敏感个人信息）
- 词法前 10：1.s6-d1-c3-memo#p3@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p8@T1 4.p1-cac-o16#p2@T1 5.s6-d1-c2-memo#p3@T1 6.p1-cac-o13#p7@T1 7.p1-cac-o16#p3@T1 8.p1-cac-o16#p6@T1 9.s6-d1-c4-memo#p1@T1 10.s6-d1-c3-memo#p1@T1
- 混合前 10：1.s6-d1-c3-memo#p3@T1 2.p1-cac-o16#p8@T1 3.s6-d1-c2-memo#p3@T1 4.s6-d1-c3-memo#p2@T1 5.p1-cac-o13#p2@T1 6.p1-cac-o13#p7@T1 7.s6-d1-c3-memo#p1@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o13#p5@T1 10.p1-cac-o20#p2@T1
- 重排前 10：1.s6-d1-c3-memo#p3@T1 2.p1-cac-o16#p8@T1 3.s6-d1-c3-memo#p2@T1 4.p1-cac-o13#p7@T1 5.p1-cac-o13#p2@T1 6.s6-d1-c4-memo#p1@T1 7.s6-d1-c2-memo#p3@T1 8.s6-d1-c3-memo#p1@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o13#p5@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 15. `p1-mh-04-new`

- 问：不是关基、也不涉及重要数据的小公司，一年只出境几千人的一般个人信息，过去要签标准合同，如今还需要吗？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p2@T1；p1-cac-o16#p4@T1；p1-cac-o16#p5@T1
- 金标要点：自上年1月1日起累计向境外提供个人信息不满10万人的；关键信息基础设施运营者以外的数据处理者自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息）的；免予申报数据出境安全评估、订立个人信息出境标准合同、通过个人信息保护认证
- 词法前 10：1.p1-cac-o16#p2@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p3@T1 4.p1-cac-o16#p6@T1 5.s6-d1-c3-memo#p3@T1 6.s6-d1-c3-memo#p1@T1 7.p1-cac-o16#p1@T1 8.p1-cac-o16#p4@T1 9.p1-cac-o20#p3@T1 10.s6-d1-c4-memo#p1@T1
- 混合前 10：1.p1-cac-o16#p2@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o20#p3@T1 4.p1-cac-o16#p4@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o16#p3@T1 7.s6-d1-c3-memo#p3@T1 8.s6-d1-c3-memo#p1@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o16#p6@T1
- 重排前 10：1.p1-cac-o16#p2@T1 2.p1-cac-o16#p3@T1 3.p1-cac-o16#p11@T1 4.p1-cac-o16#p6@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o20#p3@T1 7.p1-cac-o16#p4@T1 8.p1-cac-o16#p8@T1 9.s6-d1-c3-memo#p3@T1 10.s6-d1-c3-memo#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 16. `p1-mh-05-new`

- 问：认证办法从哪天开始施行？新规下走标准合同的人数区间是多少？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o20#p9@T1；p1-cac-o16#p8@T1
- 金标要点：本办法自2026年1月1日起施行；自当年1月1日起累计向境外提供10万人以上、不满100万人个人信息（不含敏感个人信息）或者不满1万人敏感个人信息的
- 词法前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o20#p8@T1 3.s6-d1-c3-memo#p2@T1 4.s6-d1-c3-memo#p3@T1 5.p1-cac-o11#p17@T1 6.p1-cac-o13#p8@T1 7.p1-cac-o13#p1@T1 8.p1-cac-o13#p5@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o20#p9@T1
- 混合前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o20#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o13#p5@T1 5.p1-cac-o13#p8@T1 6.p1-cac-o16#p11@T1 7.p1-cac-o20#p9@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o16#p8@T1 10.p1-cac-o13#p1@T1
- 重排前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o16#p8@T1 3.p1-cac-o20#p8@T1 4.p1-cac-o16#p11@T1 5.s6-d1-c4-memo#p1@T1 6.p1-cac-o13#p1@T1 7.p1-cac-o11#p17@T1 8.p1-cac-o13#p5@T1 9.p1-cac-o13#p8@T1 10.p1-cac-o20#p9@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 17. `p1-mh-06-new`

- 问：有限公司股东认缴的钱要几年内交齐？新法生效前设立、期限更长的公司要怎么处理？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital#p1@T1；p1-colaw-capital-transition#p1@T1
- 金标要点：自公司成立之日起五年内缴足；应当逐步调整至本法规定的期限以内
- 词法前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p2@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital#p4@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-transition#p1@T1 8.s6-d2-g1-memo#p1@T1 9.s2-d0-t1-91-interview#p2@T1 10.p1-colaw-equity#p5@T1
- 混合前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g1-memo#p1@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g3-memo#p3@T1 6.s6-d2-g2-memo#p3@T1 7.p1-colaw-capital-call#p4@T1 8.p1-colaw-capital-transition#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-capital#p4@T1
- 重排前 10：1.s6-d2-g1-memo#p2@T1 2.p1-colaw-capital#p1@T1 3.s6-d2-g2-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital-transition#p1@T1 6.p1-colaw-capital#p4@T1 7.s6-d2-g1-memo#p1@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital-transition#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 18. `p1-mh-07-new`

- 问：股东逾期不交出资，除了补交还要担什么？宽限期过了公司能怎么处置他的股权？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-transition#p2@T1；p1-colaw-capital-call#p2@T1
- 金标要点：该股东丧失其未缴纳出资的股权；还应当对给公司造成的损失承担赔偿责任；公司经董事会决议可以向该股东发出失权通知
- 词法前 10：1.p1-colaw-capital-call#p2@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-equity#p3@T1 7.s6-d2-g3-memo#p2@T1 8.p1-colaw-capital-call#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-capital-call#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p2@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-capital-call#p1@T1 4.p1-colaw-capital-call#p3@T1 5.s6-d2-g3-memo#p1@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-transition#p2@T1 8.s6-d2-g3-memo#p2@T1 9.p1-colaw-equity#p5@T1 10.p1-colaw-equity#p1@T1
- 重排前 10：1.p1-colaw-capital-call#p2@T1 2.s6-d2-g3-memo#p2@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-capital-call#p1@T1 7.s6-d2-g3-memo#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-equity#p5@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 19. `p1-mh-08-new`

- 问：董事会没去催缴出资导致损失，谁来赔？欠缴股东本人又要对公司赔什么？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p1@T1；p1-colaw-capital-transition#p2@T1
- 金标要点：负有责任的董事应当承担赔偿责任；还应当对给公司造成的损失承担赔偿责任
- 词法前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.p1-colaw-capital-call#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-governance-board#p3@T1 7.s6-d2-g1-memo#p2@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-governance-board#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.p1-colaw-capital-call#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-call#p3@T1 8.p1-colaw-capital-call#p5@T1 9.p1-colaw-governance-board#p3@T1 10.p1-colaw-capital#p1@T1
- 重排前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.s6-d2-g3-memo#p2@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p3@T1 7.p1-colaw-capital#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital-call#p5@T1 10.p1-colaw-governance-board#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 20. `p1-mh-09-new`

- 问：现在一个人能单独设有限公司吗？他认缴的出资几年内要缴完？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-oneperson#p1@T1；p1-colaw-capital#p1@T1
- 金标要点：自公司成立之日起五年内缴足；有限责任公司由一个以上五十个以下股东出资设立。
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-governance-board#p2@T1 4.p1-colaw-capital#p4@T1 5.p1-colaw-governance-supervisor-js#p5@T1 6.p1-colaw-oneperson#p1@T1 7.p1-colaw-governance-board#p4@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-liquidation#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital#p1@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-call#p5@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-oneperson#p1@T1 7.p1-colaw-capital-call#p1@T1 8.p1-colaw-capital-call#p2@T1 9.p1-colaw-governance-supervisor-js#p5@T1 10.p1-colaw-capital#p3@T1
- 重排前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-governance-supervisor-js#p5@T1 6.s6-d2-g1-memo#p1@T1 7.p1-colaw-oneperson#p1@T1 8.p1-colaw-capital-call#p1@T1 9.p1-colaw-capital-call#p2@T1 10.p1-colaw-capital#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 21. `p1-mh-10-new`

- 问：减资补亏之后，股东没交的出资能免掉吗？公司还不上债时，没到期的出资能被要求提前交吗？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p5@T1；p1-colaw-capital-call#p4@T1
- 金标要点：不得免除股东缴纳出资或者股款的义务；有权要求已认缴出资但未届出资期限的股东提前缴纳出资
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p2@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-capital#p3@T1 7.s6-d2-g3-memo#p2@T1 8.p1-colaw-liquidation#p5@T1 9.s6-d2-g1-memo#p3@T1 10.p1-colaw-capital-call#p3@T1
- 混合前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-call#p2@T1 3.p1-colaw-capital-call#p1@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-liquidation#p5@T1 7.s6-d2-g3-memo#p1@T1 8.p1-colaw-capital-call#p3@T1 9.s6-d2-g3-memo#p2@T1 10.s6-d2-g3-memo#p3@T1
- 重排前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-capital-transition#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-capital-call#p1@T1 7.p1-colaw-capital-call#p5@T1 8.s6-d2-g3-memo#p1@T1 9.p1-colaw-capital-call#p3@T1 10.s6-d2-g3-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 22. `p1-mh-11-new`

- 问：股东把股权卖给外人要先通知谁、别人有什么权利？卖的若是还没到期的认缴出资，由谁来交？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-equity#p1@T1；p1-colaw-capital-call#p5@T1
- 金标要点：其他股东在同等条件下有优先购买权；由受让人承担缴纳该出资的义务；应当将股权转让的数量、价格、支付方式和期限等事项书面通知其他股东
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p3@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-equity#p3@T1 7.p1-colaw-equity#p1@T1 8.p1-colaw-equity#p5@T1 9.s6-d2-g3-memo#p3@T1 10.p1-colaw-capital#p1@T1
- 混合前 10：1.p1-colaw-capital-call#p5@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-equity#p1@T1 5.p1-colaw-equity#p3@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-capital-call#p3@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital#p3@T1 10.p1-colaw-equity#p5@T1
- 重排前 10：1.p1-colaw-capital-transition#p2@T1 2.p1-colaw-equity#p1@T1 3.p1-colaw-capital-call#p3@T1 4.s6-d2-g3-memo#p3@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-equity#p3@T1 8.p1-colaw-capital-call#p2@T1 9.p1-colaw-equity#p5@T1 10.p1-colaw-capital#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 23. `p1-mh-13-new`

- 问：旧规下出境一般个人信息（不含敏感个人信息）到多少人要报评估，多少人以下可以签标准合同？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p2@T0；p1-cac-o13#p2@T0
- 金标要点：自上年1月1日起累计向境外提供10万人个人信息；自上年1月1日起累计向境外提供个人信息不满10万人的
- 词法前 10：1.p1-cac-o13#p1@T0 2.p1-cac-o13#p7@T0 3.p1-cac-o13#p3@T0 4.p1-cac-o13#p2@T0 5.p1-cac-o13#p4@T0 6.p1-cac-o13#p6@T0 7.p1-cac-o11#p2@T0 8.p1-cac-o13#p5@T0 9.p1-cac-o11#p4@T0 10.p1-cac-o11#p5@T0
- 混合前 10：1.p1-cac-o13#p1@T0 2.p1-cac-o13#p2@T0 3.p1-cac-o13#p3@T0 4.p1-cac-o13#p7@T0 5.p1-cac-o13#p5@T0 6.p1-cac-o13#p6@T0 7.p1-cac-o11#p5@T0 8.p1-cac-o11#p2@T0 9.p1-cac-o13#p4@T0 10.p1-cac-o13#p8@T0
- 重排前 10：1.p1-cac-o13#p2@T0 2.p1-cac-o13#p1@T0 3.p1-cac-o13#p7@T0 4.p1-cac-o13#p3@T0 5.p1-cac-o13#p6@T0 6.p1-cac-o11#p2@T0 7.p1-cac-o13#p4@T0 8.p1-cac-o13#p5@T0 9.p1-cac-o11#p5@T0 10.p1-cac-o13#p8@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 24. `p1-mh-14-new`

- 问：评估办法和标准合同办法分别是哪天开始施行的？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p17@T0；p1-cac-o13#p8@T0
- 金标要点：本办法自2022年9月1日起施行；本办法自2023年6月1日起施行
- 词法前 10：1.p1-cac-o11#p17@T0 2.p1-cac-o13#p8@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p5@T0 5.p1-cac-o11#p1@T0 6.p1-cac-o11#p16@T0 7.p1-cac-o13#p6@T0 8.p1-cac-o13#p7@T0 9.p1-cac-o13#p2@T0 10.p1-cac-o13#p4@T0
- 混合前 10：1.p1-cac-o11#p17@T0 2.p1-cac-o13#p8@T0 3.p1-cac-o13#p5@T0 4.p1-cac-o13#p6@T0 5.p1-colaw-capital-transition#p1@T0 6.p1-cac-o13#p1@T0 7.p1-cac-o13#p7@T0 8.s1-d0-01-analysis#p3@T0 9.p1-cac-o13#p2@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.p1-cac-o13#p7@T0 2.p1-cac-o13#p6@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p2@T0 5.p1-cac-o11#p1@T0 6.p1-cac-o11#p17@T0 7.p1-cac-o13#p8@T0 8.p1-cac-o13#p5@T0 9.s1-d0-01-analysis#p3@T0 10.p1-colaw-capital-transition#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 25. `s1-d0-02-q2`

- 问：原材料交付周期拉长到45天的那家公司，T1 时技术系统性能还能满足原定的业务扩展需求吗？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-02-memo#p2@T1
- 金标要点：系统需进行架构优化，否则无法支撑下一阶段业务扩张；核心模块在高负载压力下暴露出性能瓶颈，已触发两次非预期中断
- 词法前 10：1.s1-d0-02-report#p2@T1 2.s4-d0-t1-02-report#p1@T1 3.s5-d2-t1-91-digest#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-01-analysis#p1@T1 6.s1-d1-t1-91-brief#p2@T1 7.s1-d0-02-memo#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s6-d0-t1-02-memo#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 混合前 10：1.s6-d0-t1-02-memo#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s1-d0-02-memo#p2@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-02-internal#p1@T1 7.s1-d0-01-memo#p1@T1 8.s1-d0-01-analysis#p1@T1 9.s4-d0-t1-02-report#p1@T1 10.s2-d1-01-memo#p1@T1
- 重排前 10：1.s1-d0-02-report#p2@T1 2.s4-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d0-t1-02-report#p1@T1 5.s1-d0-02-memo#p2@T1 6.s4-d2-t1-04-internal#p1@T1 7.s1-d0-01-memo#p1@T1 8.s1-d0-01-analysis#p1@T1 9.s2-d1-01-memo#p1@T1 10.s6-d0-t1-02-internal#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 26. `s1-d0-03-q2`

- 问：T0 时认为有效的缓冲机制，在 T1 中是否仍具备应对能力？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-03-memo#p2@T1
- 金标要点：技术团队更新分析指出，外部环境变化已导致核心资源获取路径发生不可逆断裂，现有缓冲机制已无法覆盖新风险敞口
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d2-t1-04-summary#p2@T1 3.s5-d3-t1-05-analysis#p2@T1 4.p1-cac-o11#p8@T1 5.s1-d0-03-memo#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s4-d0-t1-02-report#p2@T1 8.s4-d2-t1-04-report#p2@T1 9.s7-d3-t1-05-memo#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s1-d0-03-memo#p2@T1 2.s2-d0-02-interview#p3@T1 3.s4-d2-t1-04-summary#p2@T1 4.s1-d0-05-warn#p2@T1 5.s4-d2-t1-04-internal#p1@T1 6.s4-d0-t1-02-report#p2@T1 7.s4-d2-t1-04-report#p2@T1 8.s5-d3-t1-05-analysis#p2@T1 9.s2-d3-01-interview#p2@T1 10.s7-d3-t1-05-claim#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p2@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d2-t1-04-report#p2@T1 4.s7-d3-t1-05-claim#p1@T1 5.s2-d0-02-interview#p3@T1 6.s4-d2-t1-04-summary#p2@T1 7.s1-d0-03-memo#p2@T1 8.s1-d0-05-warn#p2@T1 9.s4-d2-t1-04-internal#p1@T1 10.s2-d3-01-interview#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 27. `s1-d0-04-q1`

- 问：T0 时点下，核心市场渗透率是否处于稳定状态？其依据是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p1@T0
- 金标要点：近期数据显示，核心市场渗透率在连续三周维持在68%以上，表明当前战略执行路径具备初步成效；团队评估认为，该数值已进入稳定区间，可作为后续资源调配的重要依据
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s1-d0-04-memo#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s1-d0-01-memo#p1@T0 5.s7-d0-t0-01-qa#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s1-d1-01-analysis#p1@T0 8.s2-d2-01-memo#p2@T0 9.s7-d0-t0-01-report#p3@T0 10.s1-d1-01-analysis#p3@T0
- 混合前 10：1.s1-d0-04-memo#p1@T0 2.s1-d0-01-memo#p1@T0 3.s1-d0-02-memo#p1@T0 4.s1-d1-01-memo#p1@T0 5.s2-d0-03-memo#p2@T0 6.s2-d2-01-memo#p2@T0 7.s1-d1-01-analysis#p1@T0 8.s1-d2-01-memo#p1@T0 9.s1-d0-02-report#p1@T0 10.s4-d3-t0-05-memo#p1@T0
- 重排前 10：1.s1-d0-04-memo#p1@T0 2.s1-d0-01-memo#p1@T0 3.s4-d3-t0-05-memo#p1@T0 4.s1-d0-02-memo#p1@T0 5.s1-d1-01-memo#p1@T0 6.s2-d0-03-memo#p2@T0 7.s2-d2-01-memo#p2@T0 8.s1-d1-01-analysis#p1@T0 9.s1-d2-01-memo#p1@T0 10.s1-d0-02-report#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 28. `s1-d0-04-q2`

- 问：核心市场渗透率回落到66.2%的那家公司，T1 时供应链中哪一环节明显恶化？具体表现是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p2@T1
- 金标要点：供应链韧性测试中，尽管整体准时率仍达92%，但某关键节点延误率上升至11%，暴露出单一依赖风险
- 词法前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-03-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s2-d0-02-interview#p3@T1 5.s6-d2-g3-memo#p3@T1 6.s1-d0-01-memo#p1@T1 7.s1-d1-t1-91-memo#p2@T1 8.s7-d2-t1-04-data#p1@T1 9.s1-d1-01-memo#p1@T1 10.s1-d2-01-memo#p1@T1
- 混合前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-03-memo#p1@T1 3.s2-d0-02-interview#p3@T1 4.s1-d0-01-memo#p1@T1 5.s1-d1-01-memo#p1@T1 6.s1-d0-02-memo#p1@T1 7.s1-d2-01-memo#p1@T1 8.s1-d3-01-memo#p1@T1 9.s7-d2-t1-04-data#p1@T1 10.s1-d1-01-analysis#p2@T1
- 重排前 10：1.s1-d0-04-memo#p1@T1 2.s7-d2-t1-04-data#p1@T1 3.s1-d0-03-memo#p1@T1 4.s2-d0-02-interview#p3@T1 5.s1-d0-01-memo#p1@T1 6.s1-d1-01-memo#p1@T1 7.s1-d0-02-memo#p1@T1 8.s1-d2-01-memo#p1@T1 9.s1-d3-01-memo#p1@T1 10.s1-d1-01-analysis#p2@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 29. `s1-d0-04-q3`

- 问：渗透率回落至66.2%、三条海运通道被临时关闭的那家公司，T0 到 T1 客户满意度的描述有何关键变化？预示什么趋势？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p3@T1
- 金标要点：客户反馈调查中，尽管平均满意度维持在4.3分，但针对售后服务的负面评论数量同比增加37%，提示服务模式存在结构性短板，亟待调整
- 词法前 10：1.s1-d0-04-risk#p2@T1 2.s7-d3-t1-05-conflict#p2@T1 3.s1-d0-04-memo#p1@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s5-d1-t1-03-note#p2@T1 6.p1-colaw-governance-supervisor-js#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s1-d0-01-memo#p2@T1 9.s3-d0-02-c#p2@T1 10.s5-d3-t1-05-analysis#p3@T1
- 混合前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-04-risk#p2@T1 3.s1-d0-01-memo#p2@T1 4.s7-d3-t1-05-conflict#p2@T1 5.s2-d0-03-memo#p1@T1 6.s5-d1-t1-03-note#p2@T1 7.s1-d0-04-memo#p3@T1 8.s3-d0-02-c#p2@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s2-d2-01-report#p2@T1
- 重排前 10：1.s1-d0-04-risk#p2@T1 2.s7-d3-t1-05-conflict#p2@T1 3.s5-d1-t1-03-note#p2@T1 4.s1-d0-01-memo#p2@T1 5.s3-d0-02-c#p2@T1 6.s1-d0-04-memo#p1@T1 7.s2-d0-03-memo#p1@T1 8.s1-d0-04-memo#p3@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s2-d2-01-report#p2@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 30. `s1-d0-04-q4`

- 问：面临三条海运通道被临时关闭的那家出口企业，T1 文档中新法案对数据处理流程有什么影响？该如何应对？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-risk#p3@T1
- 金标要点：新法案正式进入立法听证阶段，预计将在未来六个月内实施，现有数据跨境架构必须在四十五天内完成合规改造；否则将面临运营中断
- 词法前 10：1.s1-d0-04-risk#p2@T1 2.s1-d0-05-warn#p2@T1 3.s5-d3-t1-05-analysis#p1@T1 4.s1-d0-04-risk#p1@T1 5.s7-d0-t1-02-memo#p3@T1 6.s1-d0-04-risk#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s1-d1-01-report#p3@T1 9.s6-d2-g1-memo#p3@T1 10.s6-d1-c4-memo#p2@T1
- 混合前 10：1.s1-d0-04-risk#p2@T1 2.s1-d1-01-report#p3@T1 3.s1-d0-04-risk#p3@T1 4.s6-d1-c4-memo#p2@T1 5.p1-cac-o11#p14@T1 6.s6-d3-t1-03-memo#p3@T1 7.s6-d2-g2-memo#p2@T1 8.s7-d0-t1-02-update#p2@T1 9.s1-d0-05-memo#p3@T1 10.p1-cac-o11#p15@T1
- 重排前 10：1.s1-d0-04-risk#p2@T1 2.s7-d0-t1-02-update#p2@T1 3.s6-d1-c4-memo#p2@T1 4.s6-d2-g2-memo#p2@T1 5.s1-d1-01-report#p3@T1 6.p1-cac-o11#p14@T1 7.s6-d3-t1-03-memo#p3@T1 8.p1-cac-o11#p15@T1 9.s1-d0-04-risk#p3@T1 10.s1-d0-05-memo#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 31. `s1-d0-05-q1`

- 问：T0 时点关于目标区域基础设施状况的评估结论是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p1@T0
- 金标要点：根据当前情报，目标区域的基础设施部署已进入稳定阶段；主要通道保持畅通，未发现异常干扰迹象；该区域具备长期战略价值
- 词法前 10：1.s1-d0-05-memo#p1@T0 2.s4-d0-t0-01-analysis#p2@T0 3.s1-d0-03-memo#p1@T0 4.s7-d0-t0-01-qa#p1@T0 5.s1-d1-01-analysis#p3@T0 6.p1-cac-o11#p12@T0 7.s1-d3-01-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s2-d0-03-interview#p1@T0 10.s4-d1-t0-03-plan#p1@T0
- 混合前 10：1.s1-d0-05-memo#p1@T0 2.s1-d0-03-memo#p1@T0 3.s1-d3-01-memo#p1@T0 4.s5-d0-t0-01-summary#p3@T0 5.s2-d0-02-memo#p2@T0 6.p1-cac-o11#p12@T0 7.s1-d0-01-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d0-t0-01-analysis#p1@T0
- 重排前 10：1.s1-d0-05-memo#p1@T0 2.s1-d0-03-memo#p1@T0 3.s1-d3-01-memo#p1@T0 4.p1-cac-o11#p12@T0 5.s1-d0-01-memo#p1@T0 6.s5-d0-t0-01-summary#p3@T0 7.s2-d0-02-memo#p2@T0 8.s7-d0-t0-01-report#p3@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d0-t0-01-analysis#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 32. `s1-d0-05-q2`

- 问：T1 时点对同一区域基础设施状况的最新判断有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p1@T1
- 金标要点：最新监测显示，目标区域主要通道出现结构性损伤，部分路段存在非正常闭塞现象；需重新评估其战略可用性
- 词法前 10：1.s1-d0-05-warn#p1@T1 2.s4-d2-t1-04-report#p1@T1 3.s7-d0-t1-02-claim#p2@T1 4.s1-d0-03-memo#p1@T1 5.s1-d0-05-memo#p1@T1 6.s5-d3-t1-05-memo#p2@T1 7.s6-d3-t1-02-report#p1@T1 8.s6-d1-c4-memo#p3@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d2-t1-04-internal#p1@T1
- 混合前 10：1.s1-d0-03-memo#p1@T1 2.s7-d0-t1-02-claim#p2@T1 3.s1-d0-05-memo#p1@T1 4.s1-d3-01-memo#p1@T1 5.s1-d0-05-warn#p1@T1 6.s4-d2-t1-04-report#p1@T1 7.s6-d0-t1-01-patch#p2@T1 8.s5-d3-t1-05-memo#p3@T1 9.s6-d1-c4-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 重排前 10：1.s1-d0-03-memo#p1@T1 2.s7-d0-t1-02-claim#p2@T1 3.s1-d0-05-memo#p1@T1 4.s1-d0-05-warn#p1@T1 5.s4-d2-t1-04-report#p1@T1 6.s6-d1-c4-memo#p3@T1 7.s1-d3-01-memo#p1@T1 8.s6-d0-t1-01-patch#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 33. `s1-d0-05-q3`

- 问：T0 时点，安全团队对周边势力活动态势作出判断的依据是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p2@T0
- 金标要点：安全团队报告称，周边势力活动频率在近两周内维持低位，无明显升级信号
- 词法前 10：1.s1-d0-05-memo#p2@T0 2.s7-d0-t0-01-qa#p1@T0 3.s4-d0-t0-01-analysis#p2@T0 4.p1-colaw-governance#p3@T0 5.s2-d0-04-memo#p3@T0 6.p1-cac-o11#p15@T0 7.s4-d0-t0-01-plan#p2@T0 8.s7-d1-t0-03-fact#p3@T0 9.s5-d2-t0-04-analysis#p1@T0 10.p1-cac-o11#p16@T0
- 混合前 10：1.s1-d0-05-memo#p2@T0 2.p1-cac-o11#p7@T0 3.s4-d0-t0-01-analysis#p2@T0 4.p1-cac-o11#p16@T0 5.s7-d1-t0-03-fact#p3@T0 6.s7-d1-t0-03-reason#p3@T0 7.s7-d0-t0-01-memo#p2@T0 8.s2-d0-04-memo#p3@T0 9.s1-d3-01-report#p1@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.s1-d0-05-memo#p2@T0 2.p1-cac-o11#p7@T0 3.s7-d1-t0-03-fact#p3@T0 4.s4-d0-t0-01-analysis#p2@T0 5.p1-cac-o11#p16@T0 6.s7-d1-t0-03-reason#p3@T0 7.s7-d0-t0-01-memo#p2@T0 8.s2-d0-04-memo#p3@T0 9.p1-cac-o11#p1@T0 10.s1-d3-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 34. `s1-d0-05-q4`

- 问：T1 时点的安全预警是否基于新的技术监测数据？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-warn#p1@T1；s1-d0-05-warn#p3@T1
- 金标要点：技术监测发现，加密链路遭遇定向干扰攻击，虽未突破防护，但暴露了系统脆弱点；多源情报证实，敏感议题已转化为实际军事集结信号
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.p1-cac-o13#p4@T1 3.p1-cac-o20#p5@T1 4.s6-d3-t1-02-report#p2@T1 5.p1-cac-o11#p4@T1 6.s2-d0-02-memo#p2@T1 7.s1-d3-01-memo#p2@T1 8.s2-d3-01-memo#p3@T1 9.s4-d2-t1-04-report#p1@T1 10.s2-d0-t1-91-interview#p2@T1
- 混合前 10：1.s2-d3-01-memo#p3@T1 2.s1-d3-01-memo#p2@T1 3.s1-d0-05-warn#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-03-memo#p1@T1 6.s4-d2-t1-04-report#p3@T1 7.p1-cac-o11#p1@T1 8.p1-cac-o11#p7@T1 9.s6-d1-c2-memo#p1@T1 10.s6-d1-t1-91-release#p3@T1
- 重排前 10：1.s1-d3-01-memo#p2@T1 2.s2-d3-01-memo#p3@T1 3.s1-d0-05-warn#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-03-memo#p1@T1 6.p1-cac-o11#p1@T1 7.p1-cac-o11#p7@T1 8.s6-d1-c2-memo#p1@T1 9.s6-d1-t1-91-release#p3@T1 10.s4-d2-t1-04-report#p3@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 35. `s1-d1-01-q1`

- 问：T0 时，核心功能平均停留4.8分钟的那款产品，目标市场渗透率达到预期阈值的多少？文档把增长归因于什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d1-01-memo#p1@T0
- 金标要点：目标市场渗透率已达到预期阈值的87%；主要得益于渠道扩张与客户反馈优化
- 词法前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-01-memo#p1@T0 4.s5-d1-t0-91-repost#p1@T0 5.s1-d0-02-memo#p1@T0 6.s2-d0-03-memo#p1@T0 7.s1-d0-04-memo#p1@T0 8.s1-d1-01-memo#p3@T0 9.s2-d2-01-memo#p1@T0 10.s1-d1-01-analysis#p3@T0
- 混合前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-02-memo#p1@T0 4.s1-d0-01-memo#p1@T0 5.s1-d0-04-memo#p1@T0 6.s1-d1-01-memo#p3@T0 7.s2-d2-01-memo#p1@T0 8.s1-d0-01-memo#p2@T0 9.s1-d2-01-memo#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 重排前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-01-memo#p1@T0 4.s1-d0-02-memo#p1@T0 5.s1-d0-04-memo#p1@T0 6.s2-d2-01-memo#p1@T0 7.s1-d1-01-memo#p3@T0 8.s1-d0-01-memo#p2@T0 9.s1-d2-01-memo#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 36. `s1-d2-01-q1`

- 问：在评级机构把短期展望调到负面观察的那份宏观研判里，T0 与 T1 对通胀走势的描述根本差异在哪？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-memo#p1@T1
- 金标要点：尽管前期数据显示通胀回落，最新数据揭示核心通胀存在反弹苗头，部分服务类项目价格再度上扬
- 词法前 10：1.s1-d2-01-analysis#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s1-d1-t1-91-memo#p2@T1 4.s5-d3-t1-05-memo#p1@T1 5.s5-d1-t1-03-memo#p3@T1 6.s2-d0-t1-91-memo#p1@T1 7.s4-d0-t1-02-report#p2@T1 8.s5-d2-t1-91-digest#p3@T1 9.s6-d2-g3-memo#p3@T1 10.s6-d3-t1-02-report#p1@T1
- 混合前 10：1.s1-d2-01-analysis#p3@T1 2.s1-d2-01-memo#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s1-d0-04-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s5-d1-t1-03-summary#p3@T1 7.s7-d3-t1-05-claim#p2@T1 8.s7-d2-t1-04-memo#p3@T1 9.s1-d0-04-risk#p1@T1 10.s5-d3-t1-05-analysis#p3@T1
- 重排前 10：1.s1-d2-01-analysis#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s5-d1-t1-03-memo#p3@T1 4.s5-d1-t1-03-summary#p3@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s1-d0-04-memo#p3@T1 7.s7-d3-t1-05-claim#p2@T1 8.s7-d2-t1-04-memo#p3@T1 9.s1-d2-01-memo#p1@T1 10.s1-d0-04-risk#p1@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 37. `s1-d2-01-q2`

- 问：对比 T0 和 T1 的报告，企业资本开支的乐观预期是否依然成立？请说明依据。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-memo#p2@T1
- 金标要点：企业资本开支虽有小幅回升，但实际投资增速仍低于预期，尤其在高端制造领域出现观望情绪；信心修复不均衡
- 词法前 10：1.s1-d2-01-memo#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p2@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d3-t1-03-memo#p2@T1 6.s7-d2-t1-04-memo#p3@T1 7.s4-d0-t1-02-guide#p3@T1 8.p1-colaw-liquidation#p1@T1 9.p1-colaw-liquidation#p2@T1 10.s6-d2-g1-memo#p2@T1
- 混合前 10：1.s1-d2-01-memo#p2@T1 2.s4-d0-t1-02-review#p1@T1 3.s6-d2-g1-memo#p2@T1 4.s4-d2-t1-04-internal#p1@T1 5.p1-colaw-capital-call#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s5-d3-t1-05-memo#p3@T1 8.s4-d0-t1-02-analysis#p1@T1 9.s5-d3-t1-05-analysis#p1@T1 10.s6-d2-g2-memo#p2@T1
- 重排前 10：1.s1-d2-01-memo#p2@T1 2.s6-d2-g1-memo#p2@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s5-d3-t1-05-memo#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s6-d2-g2-memo#p2@T1 7.s4-d0-t1-02-review#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.p1-colaw-capital-call#p1@T1 10.s5-d3-t1-05-analysis#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 38. `s1-d2-01-q3`

- 问：T1 文档中提到的跨境支付系统部署延迟，其主要原因是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-report#p3@T1
- 金标要点：跨境支付系统测试中发现兼容性瓶颈，部署时间或延后至下一财年，影响预期效率提升
- 词法前 10：1.s1-d2-01-report#p3@T1 2.p1-cac-o16#p4@T1 3.s7-d2-t1-04-brief#p2@T1 4.s2-d1-01-memo#p1@T1 5.s7-d0-t1-02-report#p1@T1 6.s4-d2-t1-04-internal#p1@T1 7.s7-d0-t1-02-brief#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s7-d0-t1-02-report#p3@T1 10.s7-d0-t1-02-memo#p2@T1
- 混合前 10：1.s1-d2-01-report#p3@T1 2.s7-d0-t1-02-report#p1@T1 3.s7-d2-t1-04-brief#p2@T1 4.s2-d1-01-memo#p1@T1 5.s1-d3-01-memo#p2@T1 6.s7-d0-t1-02-memo#p2@T1 7.s2-d3-01-memo#p3@T1 8.s6-d1-c4-memo#p2@T1 9.s1-d1-01-memo#p2@T1 10.s1-d0-01-memo#p2@T1
- 重排前 10：1.s1-d2-01-report#p3@T1 2.s7-d2-t1-04-brief#p2@T1 3.s7-d0-t1-02-memo#p2@T1 4.s7-d0-t1-02-report#p1@T1 5.s2-d1-01-memo#p1@T1 6.s1-d3-01-memo#p2@T1 7.s6-d1-c4-memo#p2@T1 8.s1-d0-01-memo#p2@T1 9.s2-d3-01-memo#p3@T1 10.s1-d1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 39. `s1-d2-01-q6`

- 问：T1 时，评级机构对主权信用展望作了什么调整？核心通胀和区域消费又各出现了什么信号？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-analysis#p3@T1；s1-d2-01-memo#p1@T1；s1-d2-01-report#p1@T1
- 金标要点：整体需求动能不足；国际评级机构下调短期展望至负面观察；最新数据揭示核心通胀存在反弹苗头；区域消费指数增长势头减弱
- 词法前 10：1.s1-d0-04-risk#p1@T1 2.s1-d2-01-analysis#p3@T1 3.s1-d2-01-memo#p1@T1 4.s4-d0-t1-02-memo#p2@T1 5.s1-d0-05-warn#p1@T1 6.s1-d3-01-memo#p1@T1 7.s4-d2-t1-04-summary#p1@T1 8.s1-d2-01-report#p1@T1 9.s5-d1-t1-03-memo#p1@T1 10.s5-d3-t1-05-memo#p1@T1
- 混合前 10：1.s1-d0-04-risk#p1@T1 2.s1-d2-01-analysis#p3@T1 3.s1-d2-01-memo#p1@T1 4.s5-d1-t1-03-memo#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s1-d2-01-report#p1@T1 7.s1-d0-05-warn#p1@T1 8.s7-d2-t1-04-memo#p3@T1 9.s2-d0-02-interview#p3@T1 10.s1-d3-01-report#p1@T1
- 重排前 10：1.s1-d0-04-risk#p1@T1 2.s4-d0-t1-02-memo#p2@T1 3.s1-d2-01-analysis#p3@T1 4.s5-d1-t1-03-memo#p1@T1 5.s1-d0-05-warn#p1@T1 6.s7-d2-t1-04-memo#p3@T1 7.s1-d2-01-memo#p1@T1 8.s1-d2-01-report#p1@T1 9.s2-d0-02-interview#p3@T1 10.s1-d3-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 40. `s1-d3-01-q4`

- 问：物流周期普遍延长超过48小时的那个区域，T1 报告里通信网络与多边合作的变化如何影响整体战略态势？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d3-01-report#p2@T1；s1-d3-01-report#p3@T1
- 金标要点：主干通信网络在近三日内遭遇三次区域性中断，峰值负载达92%，冗余链路已被迫启用；公开声明中出现立场分化，合作意愿显著减弱，存在集体脱钩趋势；多边协调机制出现明显裂痕
- 词法前 10：1.s1-d3-01-memo#p1@T1 2.s2-d1-01-memo#p1@T1 3.s1-d0-03-report#p2@T1 4.s5-d0-t1-02-memo#p1@T1 5.s6-d0-t1-01-memo#p1@T1 6.s1-d0-02-report#p2@T1 7.s5-d0-t1-02-memo#p2@T1 8.s1-d0-04-risk#p2@T1 9.s1-d3-01-report#p2@T1 10.s6-d0-t1-02-internal#p1@T1
- 混合前 10：1.s1-d3-01-memo#p1@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-04-risk#p2@T1 4.s5-d0-t1-02-memo#p1@T1 5.s2-d1-01-memo#p1@T1 6.s1-d3-01-report#p2@T1 7.s6-d0-t1-02-internal#p1@T1 8.s2-d0-02-report#p3@T1 9.s1-d0-05-memo#p1@T1 10.s1-d2-01-report#p1@T1
- 重排前 10：1.s1-d3-01-memo#p1@T1 2.s2-d1-01-memo#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s1-d0-03-report#p2@T1 5.s6-d0-t1-02-internal#p1@T1 6.s1-d0-05-memo#p1@T1 7.s1-d0-04-risk#p2@T1 8.s1-d3-01-report#p2@T1 9.s2-d0-02-report#p3@T1 10.s1-d2-01-report#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 41. `s2-d0-01-q1`

- 问：渠道成本已占总成本34%的那家公司，T0 时线下门店的营收占比大约多少？线上流量转化率又是多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-memo#p1@T0
- 金标要点：线下门店占比不足15%；线上流量转化率稳定在6.8%
- 词法前 10：1.s2-d0-01-memo#p3@T0 2.s2-d0-01-memo#p1@T0 3.s2-d1-01-memo#p3@T0 4.s2-d0-01-report#p1@T0 5.p2-gdp-national#p2@T0 6.s1-d1-01-analysis#p3@T0 7.s2-d0-03-memo#p1@T0 8.s2-d0-02-report#p1@T0 9.s4-d0-t0-01-plan#p2@T0 10.s2-d3-01-memo#p1@T0
- 混合前 10：1.s2-d0-01-memo#p3@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-02-report#p1@T0 4.s2-d1-01-memo#p3@T0 5.s2-d0-01-report#p1@T0 6.s2-d0-03-memo#p1@T0 7.s2-d1-01-memo#p2@T0 8.s2-d0-02-memo#p1@T0 9.s3-d3-01-report#p1@T0 10.s2-d3-01-memo#p1@T0
- 重排前 10：1.s2-d0-01-memo#p1@T0 2.s2-d0-01-memo#p3@T0 3.s2-d0-03-memo#p1@T0 4.s2-d1-01-memo#p3@T0 5.s2-d0-01-report#p1@T0 6.s2-d1-01-memo#p2@T0 7.s2-d0-02-memo#p1@T0 8.s2-d3-01-memo#p1@T0 9.s2-d0-02-report#p1@T0 10.s3-d3-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 42. `s2-d0-01-q2`

- 问：T1 时渠道成本占总成本的比例发生了什么变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-memo#p3@T1
- 金标要点：渠道成本压力持续加剧，目前占总成本达41%，其中平台佣金上涨22%；新方案拟通过自建私域流量降低对外部平台依赖
- 词法前 10：1.s2-d0-01-memo#p3@T1 2.p1-cac-o11#p10@T1 3.s4-d2-t1-04-internal#p1@T1 4.s1-d0-03-memo#p2@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s2-d0-01-memo#p1@T1 7.s5-d3-t1-05-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s2-d3-01-memo#p1@T1 10.p2-gdp-national#p2@T1
- 混合前 10：1.s2-d0-01-memo#p3@T1 2.s2-d0-01-memo#p1@T1 3.s3-d3-01-report#p2@T1 4.s2-d0-02-report#p1@T1 5.s4-d2-t1-04-report#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s6-d3-t1-03-memo#p3@T1 8.s3-d1-t1-91-quote#p1@T1 9.s3-d2-t1-91-contract#p2@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s2-d0-01-memo#p3@T1 2.s2-d0-01-memo#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d3-01-memo#p1@T1 6.s3-d3-01-report#p2@T1 7.s2-d0-02-report#p1@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-contract#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 43. `s2-d0-01-q4`

- 问：T1 时渠道信息同步机制升级后，投诉量和关键节点更新延迟分别有什么变化？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-report#p3@T1
- 金标要点：投诉量下降至周均43起；关键节点更新延迟已减少80%
- 词法前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-05-warn#p2@T1 4.s1-d0-03-memo#p1@T1 5.s4-d2-t1-04-internal#p1@T1 6.s1-d0-03-memo#p2@T1 7.p1-cac-o20#p7@T1 8.s5-d1-t1-03-report#p3@T1 9.s6-d3-t1-02-memo#p1@T1 10.s6-d3-t1-03-memo#p3@T1
- 混合前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s6-d3-t1-03-memo#p3@T1 4.s2-d1-01-memo#p1@T1 5.s6-d3-t1-03-report#p2@T1 6.s2-d1-01-memo#p2@T1 7.s1-d0-01-memo#p2@T1 8.s1-d0-05-warn#p2@T1 9.s6-d0-t1-01-channel#p2@T1 10.s6-d0-t1-02-report#p1@T1
- 重排前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-05-warn#p2@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d1-01-memo#p1@T1 6.s6-d3-t1-03-report#p2@T1 7.s2-d1-01-memo#p2@T1 8.s1-d0-01-memo#p2@T1 9.s6-d0-t1-01-channel#p2@T1 10.s6-d0-t1-02-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 44. `s2-d0-02-q1`

- 问：根据T0文档，新客户获取成本上升的主要原因是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-memo#p1@T0
- 金标要点：近期渠道反馈显示，新客户获取成本在上季度上升了18%，主要源于线上广告投放效率下降；团队初步判断是算法推荐系统未及时适配用户行为变化
- 词法前 10：1.s2-d0-02-memo#p1@T0 2.s3-d0-03-report#p1@T0 3.s4-d0-t0-01-analysis#p1@T0 4.s4-d0-t0-01-plan#p2@T0 5.s4-d0-t0-01-analysis#p2@T0 6.s2-d0-04-memo#p1@T0 7.s3-d0-01-memo#p3@T0 8.s3-d2-01-competitor-pricing#p1@T0 9.s2-d0-03-memo#p1@T0 10.s7-d0-t0-01-qa#p1@T0
- 混合前 10：1.s2-d0-02-memo#p1@T0 2.s3-d0-03-report#p1@T0 3.s2-d0-03-memo#p1@T0 4.s4-d0-t0-01-analysis#p1@T0 5.s3-d3-01-report#p1@T0 6.s3-d0-01-memo#p3@T0 7.s3-d1-01-report#p3@T0 8.s3-d0-02-b#p1@T0 9.s4-d0-t0-01-analysis#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s2-d0-02-memo#p1@T0 2.s2-d0-03-memo#p1@T0 3.s4-d0-t0-01-analysis#p1@T0 4.s3-d0-03-report#p1@T0 5.s3-d3-01-report#p1@T0 6.s3-d0-01-memo#p3@T0 7.s3-d1-01-report#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s3-d0-02-b#p1@T0 10.s4-d3-t0-05-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 45. `s2-d0-02-q2`

- 问：T1版本中关于新客户获取成本的解释有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-memo#p1@T1
- 金标要点：最新数据分析表明，新客户获取成本上升主因并非算法问题，而是外部市场环境波动导致流量质量整体下滑；原有投放模型仍具有效性
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s1-d0-03-memo#p2@T1 3.s2-d0-02-memo#p1@T1 4.s1-d1-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s1-d0-01-memo#p2@T1 7.s4-d0-t1-02-report#p1@T1 8.s4-d0-t1-02-memo#p1@T1 9.s4-d2-t1-04-internal#p1@T1 10.s7-d3-t1-05-conflict#p2@T1
- 混合前 10：1.s2-d0-02-memo#p1@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s2-d0-03-memo#p1@T1 4.s4-d0-t1-02-review#p2@T1 5.s1-d1-01-memo#p3@T1 6.s4-d2-t1-04-memo#p1@T1 7.s4-d0-t1-02-memo#p1@T1 8.s3-d2-01-competitor-pricing#p2@T1 9.s2-d3-01-memo#p1@T1 10.s4-d0-t1-02-report#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-review#p2@T1 4.s1-d1-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s2-d0-02-memo#p1@T1 8.s2-d0-03-memo#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s2-d3-01-memo#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 46. `s2-d0-02-q3`

- 问：T0报告中提到的电商平台旗舰店贡献占比是多少？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-report#p1@T0
- 金标要点：本月渠道销售总额环比增长9.4%，主要驱动来自新上线的电商平台旗舰店，其首月贡献占比达23%
- 词法前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-01-memo#p3@T0 4.s5-d2-t0-04-analysis#p2@T0 5.s4-d0-t0-01-plan#p2@T0 6.s1-d1-01-analysis#p3@T0 7.p2-gdp-national#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s5-d2-t0-04-analysis#p3@T0 10.s2-d3-01-interview#p2@T0
- 混合前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-01-memo#p3@T0 4.s2-d3-01-memo#p2@T0 5.s5-d2-t0-04-analysis#p1@T0 6.s2-d1-01-report#p1@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s2-d1-01-memo#p1@T0 9.s2-d0-01-report#p1@T0 10.s2-d3-01-interview#p2@T0
- 重排前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s2-d0-01-memo#p3@T0 5.s5-d2-t0-04-analysis#p1@T0 6.s2-d1-01-memo#p1@T0 7.s2-d1-01-report#p1@T0 8.s2-d3-01-memo#p2@T0 9.s2-d0-01-report#p1@T0 10.s2-d3-01-interview#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 47. `s2-d0-02-q4`

- 问：T1报告修正后的销售总额变化趋势是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-report#p1@T1
- 金标要点：本月渠道销售总额实际为环比下降3.1%，此前公布的9.4%增长数据系系统误报，现已修正
- 词法前 10：1.s2-d0-02-report#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s4-d2-t1-91-model-v3#p2@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s7-d2-t1-04-claim#p3@T1 6.s5-d0-t1-02-report#p2@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s5-d0-t1-02-analysis#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 混合前 10：1.s2-d0-02-report#p1@T1 2.s3-d0-01-report#p3@T1 3.p2-gdp-national#p1@T1 4.s4-d0-t1-02-plan#p1@T1 5.s5-d1-t1-03-memo#p1@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s3-d0-01-report#p2@T1 8.s1-d0-02-report#p3@T1 9.s2-d0-01-report#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 重排前 10：1.s2-d0-02-report#p1@T1 2.p2-gdp-national#p1@T1 3.s4-d2-t1-91-model-v3#p2@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-plan#p1@T1 6.s5-d1-t1-03-memo#p1@T1 7.s3-d0-01-report#p2@T1 8.s2-d0-01-report#p3@T1 9.s6-d0-t1-03-internal#p1@T1 10.s1-d0-02-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 48. `s2-d0-02-q5`

- 问：高管访谈中关于海外扩张的初始态度如何？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-interview#p2@T0
- 金标要点：关于海外扩张，目前暂无明确计划，重点仍将聚焦于国内市场的深度渗透与服务优化
- 词法前 10：1.s2-d0-02-interview#p2@T0 2.p1-colaw-governance-board#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d0-t0-01-report#p2@T0 5.s2-d0-03-interview#p1@T0 6.s2-d3-01-interview#p1@T0 7.s2-d1-01-memo#p1@T0 8.s1-d0-05-warn#p2@T0 9.s1-d1-01-report#p3@T0 10.s1-d1-01-memo#p1@T0
- 混合前 10：1.s2-d0-02-interview#p2@T0 2.s2-d0-03-interview#p1@T0 3.s1-d0-05-warn#p2@T0 4.s2-d1-01-memo#p3@T0 5.s2-d3-01-interview#p1@T0 6.s1-d1-01-report#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s2-d1-01-memo#p1@T0 9.s2-d0-02-interview#p3@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.s2-d0-02-interview#p2@T0 2.s2-d3-01-interview#p1@T0 3.s7-d1-t0-03-claim#p1@T0 4.s2-d1-01-memo#p1@T0 5.s2-d0-03-interview#p1@T0 6.s2-d1-01-memo#p3@T0 7.s2-d0-02-interview#p3@T0 8.p1-cac-o11#p1@T0 9.s1-d0-05-warn#p2@T0 10.s1-d1-01-report#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 49. `s2-d0-04-q1`

- 问：T1时点下，该产品线在华东地区的实际销售表现与最初预期有何差异？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-04-memo#p1@T1
- 金标要点：华东地区经销商反映实际订单量低于预期，导致部分门店出现滞销风险；最新渠道反馈显示，尽管初期销售表现强劲，但部分区域出现库存积压问题；实际增幅仅为5%
- 词法前 10：1.s2-d0-04-memo#p1@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s1-d1-01-report#p1@T1 4.s6-d0-t1-02-report#p2@T1 5.s2-d0-03-memo#p2@T1 6.s4-d0-t1-02-report#p2@T1 7.s1-d3-01-memo#p3@T1 8.s2-d2-01-report#p1@T1 9.s2-d1-01-memo#p2@T1 10.s5-d1-t1-03-memo#p2@T1
- 混合前 10：1.s2-d0-04-memo#p1@T1 2.s1-d1-01-report#p1@T1 3.s2-d0-03-memo#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s2-d0-01-report#p1@T1 7.s2-d1-01-report#p3@T1 8.s2-d0-02-report#p2@T1 9.s2-d0-02-memo#p2@T1 10.s5-d1-t1-03-memo#p3@T1
- 重排前 10：1.s2-d0-04-memo#p1@T1 2.s6-d0-t1-02-report#p2@T1 3.s1-d1-01-report#p1@T1 4.s2-d0-03-memo#p2@T1 5.s5-d1-t1-03-memo#p3@T1 6.s2-d1-01-report#p3@T1 7.s6-d0-t1-02-memo#p2@T1 8.s2-d0-01-report#p1@T1 9.s2-d0-02-memo#p2@T1 10.s2-d0-02-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 50. `s2-d0-04-q2`

- 问：暂停了30万台出货计划的那条产品线，从 T0 到 T1 推广策略有哪些关键调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-04-memo#p3@T1
- 金标要点：原定第三季度的全国推广活动已被推迟至第四季度，重点转向解决现有渠道库存与售后问题；强化经销商支持体系
- 词法前 10：1.s2-d0-04-memo#p2@T1 2.s2-d0-03-memo#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-report#p2@T1 6.s2-d2-01-report#p1@T1 7.s5-d2-t1-91-digest#p3@T1 8.s4-d2-t1-04-internal#p1@T1 9.s6-d1-c2-memo#p3@T1 10.s6-d3-t1-03-report#p3@T1
- 混合前 10：1.s2-d0-04-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s2-d0-03-memo#p2@T1 4.s2-d3-01-memo#p2@T1 5.s6-d3-t1-03-report#p3@T1 6.s1-d1-01-report#p1@T1 7.s3-d3-01-report#p2@T1 8.s1-d0-02-report#p2@T1 9.s3-d3-01-memo#p3@T1 10.s2-d0-04-memo#p3@T1
- 重排前 10：1.s2-d0-04-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s2-d0-03-memo#p2@T1 4.s2-d3-01-memo#p2@T1 5.s3-d3-01-report#p2@T1 6.s6-d3-t1-03-report#p3@T1 7.s1-d1-01-report#p1@T1 8.s1-d0-02-report#p2@T1 9.s3-d3-01-memo#p3@T1 10.s2-d0-04-memo#p3@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 51. `s2-d1-01-q1`

- 问：T0 与 T1 版本中关于渠道合作进展的描述有何差异？请指出具体事实变更。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d1-01-memo#p1@T1
- 金标要点：经重新评估，原定新增15家核心分销商的计划已调整为仅拓展6家，主要因部分平台准入；库存同步机制虽已部署，但实际响应延迟仍常超过 6 小时；部分平台准入门槛提高及结算周期延长
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s6-d3-t1-03-report#p2@T1 3.s7-d0-t1-02-claim#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s4-d0-t1-02-review#p1@T1 6.s2-d3-01-memo#p2@T1 7.s4-d0-t1-02-report#p2@T1 8.s4-d0-t1-02-guide#p3@T1 9.s6-d0-t1-01-channel#p3@T1 10.s6-d3-t1-03-memo#p3@T1
- 混合前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d3-t1-03-memo#p3@T1 4.s2-d3-01-memo#p2@T1 5.s2-d2-01-memo#p1@T1 6.s6-d0-t1-02-report#p1@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s2-d0-01-report#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s6-d0-t1-01-channel#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s6-d3-t1-03-memo#p2@T1 3.s6-d3-t1-03-report#p2@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d3-01-memo#p2@T1 6.s2-d2-01-memo#p1@T1 7.s6-d0-t1-01-channel#p1@T1 8.s6-d0-t1-02-report#p1@T1 9.s2-d0-01-report#p3@T1 10.s7-d0-t1-02-brief#p3@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 52. `s2-d1-01-q3`

- 问：短视频互动率掉到18%的那家品牌，T0 与 T1 对线下门店扩张的态度有何变化？反映了怎样的战略调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d1-01-memo#p3@T1
- 金标要点：目前优先考虑现有门店的数字化改造，以提升运营效率而非扩大规模；原计划新开 8 家直营店的方案已被暂缓
- 词法前 10：1.s2-d1-01-report#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s2-d0-01-memo#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s2-d0-01-memo#p2@T1 7.s6-d2-g3-memo#p3@T1 8.s5-d2-t1-91-digest#p3@T1 9.s1-d0-02-memo#p3@T1 10.s2-d1-01-report#p1@T1
- 混合前 10：1.s2-d1-01-report#p2@T1 2.s2-d0-01-memo#p1@T1 3.s3-d0-01-report#p3@T1 4.s2-d3-01-memo#p2@T1 5.s2-d1-01-memo#p3@T1 6.s2-d0-t1-91-interview#p3@T1 7.s2-d3-01-memo#p1@T1 8.s3-d0-01-memo#p3@T1 9.s2-d0-01-memo#p2@T1 10.s2-d1-01-report#p1@T1
- 重排前 10：1.s2-d1-01-report#p2@T1 2.s2-d1-01-report#p1@T1 3.s2-d0-01-memo#p1@T1 4.s3-d0-01-report#p3@T1 5.s2-d3-01-memo#p2@T1 6.s2-d0-t1-91-interview#p3@T1 7.s2-d3-01-memo#p1@T1 8.s2-d0-01-memo#p2@T1 9.s2-d1-01-memo#p3@T1 10.s3-d0-01-memo#p3@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 53. `s2-d2-01-q1`

- 问：T0与T1版本中关于新版本界面的评价有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d2-01-memo#p1@T1
- 金标要点：最新一轮渠道评估表明，新版本界面虽在初期获得好评，但用户实际使用中出现导航路径不清晰的问题；已启动UI重设计
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s2-d2-01-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-guide#p3@T1 6.s4-d2-t1-04-memo#p1@T1 7.s4-d0-t1-02-plan#p3@T1 8.s6-d0-t1-01-channel#p3@T1 9.s1-d1-01-memo#p3@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s2-d2-01-memo#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s1-d1-01-memo#p3@T1 5.s4-d0-t1-02-guide#p3@T1 6.s6-d0-t1-01-channel#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s4-d2-t1-04-memo#p1@T1 9.s4-d0-t1-02-memo#p1@T1 10.s4-d0-t1-02-report#p2@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s2-d2-01-memo#p1@T1 3.s4-d0-t1-02-review#p1@T1 4.s7-d0-t1-02-claim#p3@T1 5.s4-d0-t1-02-memo#p1@T1 6.s4-d0-t1-02-report#p2@T1 7.s1-d1-01-memo#p3@T1 8.s4-d0-t1-02-guide#p3@T1 9.s6-d0-t1-01-channel#p3@T1 10.s4-d2-t1-04-memo#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 54. `s2-d2-01-q2`

- 问：客服平均响应缩短到1.5小时的那家公司，T0 与 T1 关于定价策略的建议是否一致？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d2-01-memo#p2@T1
- 金标要点：经重新核算成本与利润模型，原定阶梯折扣方案被调整为捆绑促销策略，以增强整体收益而非单纯降低售价；该方案已在试点区域上线
- 词法前 10：1.s2-d2-01-report#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s2-d0-t1-91-memo#p2@T1 4.s2-d0-t1-91-interview#p2@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.p1-cac-o20#p8@T1 7.s1-d1-t1-91-brief#p2@T1 8.s1-d1-t1-91-memo#p2@T1 9.s3-d0-03-report#p3@T1 10.s3-d1-01-report#p2@T1
- 混合前 10：1.s2-d2-01-report#p2@T1 2.s4-d2-t1-04-internal#p1@T1 3.s3-d0-01-report#p3@T1 4.s1-d0-01-memo#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s3-d0-03-report#p3@T1 8.s3-d1-01-report#p2@T1 9.s3-d2-01-quotation-snapshot#p2@T1 10.s2-d0-02-report#p3@T1
- 重排前 10：1.s2-d2-01-report#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s2-d0-t1-91-memo#p2@T1 4.s3-d2-01-quotation-snapshot#p2@T1 5.s4-d2-t1-04-internal#p1@T1 6.s3-d0-01-report#p3@T1 7.s1-d0-01-memo#p2@T1 8.s3-d0-03-report#p3@T1 9.s3-d1-01-report#p2@T1 10.s2-d0-02-report#p3@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 55. `s2-d3-01-q1`

- 问：T0 与 T1 版本中关于渠道合作目标的变化是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-memo#p1@T1
- 金标要点：经重新评估，原定 15% 的用户增长目标已调整为 8%，主要因市场环境变化及渠道反馈实际转化率低于预期；后续策略将更注重质量而非数量
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s2-d3-01-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s2-d3-01-memo#p2@T1 6.s4-d0-t1-02-guide#p3@T1 7.s6-d3-t1-03-report#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.p1-cac-o20#p8@T1 10.s5-d1-t1-03-note#p2@T1
- 混合前 10：1.s2-d3-01-memo#p2@T1 2.s2-d3-01-interview#p1@T1 3.s2-d2-01-memo#p1@T1 4.s6-d3-t1-03-report#p2@T1 5.s6-d0-t1-01-channel#p1@T1 6.s1-d0-02-memo#p1@T1 7.s2-d0-01-memo#p1@T1 8.s4-d0-t1-02-plan#p3@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s2-d3-01-memo#p2@T1 3.s2-d2-01-memo#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s2-d3-01-memo#p1@T1 6.s2-d3-01-interview#p1@T1 7.s6-d3-t1-03-report#p2@T1 8.s1-d0-02-memo#p1@T1 9.s2-d0-01-memo#p1@T1 10.s4-d0-t1-02-plan#p3@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 56. `s2-d3-01-q2`

- 问：T1 版本中为何原定的合作渠道数量减少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-memo#p2@T1
- 金标要点：原计划中的两家核心渠道中，仅电商平台明确继续推进，垂直类应用因战略调整已退出合作；目前合作方数量缩减至单一
- 词法前 10：1.s2-d3-01-memo#p2@T1 2.s2-d3-01-memo#p1@T1 3.s6-d3-t1-03-report#p2@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s2-d0-01-report#p3@T1 6.s2-d3-01-interview#p2@T1 7.s2-d0-04-memo#p3@T1 8.s4-d0-t1-02-guide#p3@T1 9.p1-colaw-liquidation#p5@T1 10.s2-d2-01-memo#p1@T1
- 混合前 10：1.s2-d3-01-memo#p2@T1 2.s2-d0-01-report#p3@T1 3.s6-d3-t1-03-report#p2@T1 4.s2-d0-04-memo#p3@T1 5.s2-d3-01-interview#p2@T1 6.s4-d2-t1-04-report#p2@T1 7.s2-d2-01-memo#p1@T1 8.s2-d0-02-report#p1@T1 9.s1-d3-01-report#p3@T1 10.s2-d0-01-memo#p1@T1
- 重排前 10：1.s2-d3-01-memo#p2@T1 2.s2-d2-01-memo#p1@T1 3.s2-d0-01-report#p3@T1 4.s6-d3-t1-03-report#p2@T1 5.s2-d0-04-memo#p3@T1 6.s2-d3-01-interview#p2@T1 7.s4-d2-t1-04-report#p2@T1 8.s2-d0-02-report#p1@T1 9.s1-d3-01-report#p3@T1 10.s2-d0-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 57. `s2-d3-01-q4`

- 问：高管在两次访谈中对渠道拓展策略的表述有何根本性转变？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-interview#p1@T1
- 金标要点：CEO 改口称，由于外部竞争加剧，公司战略将转向“精耕细作”，新渠道拓展目标下调至覆盖 25% 的关键市场；不再追求广泛铺开
- 词法前 10：1.s2-d3-01-interview#p1@T1 2.s6-d3-t1-01-note#p2@T1 3.s7-d3-t1-05-synthetic#p3@T1 4.s2-d0-t1-91-interview#p1@T1 5.s7-d3-t1-05-synthetic#p1@T1 6.s2-d3-01-memo#p1@T1 7.s7-d2-t1-04-brief#p2@T1 8.s2-d3-t1-91-interview#p2@T1 9.s2-d0-t1-91-interview#p3@T1 10.s2-d3-01-interview#p2@T1
- 混合前 10：1.s2-d3-01-interview#p1@T1 2.s2-d3-01-memo#p1@T1 3.s5-d3-t1-05-analysis#p3@T1 4.s1-d0-02-memo#p1@T1 5.s2-d0-03-interview#p1@T1 6.s6-d0-t1-01-channel#p1@T1 7.s2-d3-01-memo#p2@T1 8.s2-d0-01-memo#p1@T1 9.s2-d0-t1-91-interview#p3@T1 10.s5-d1-t1-03-memo#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s5-d1-t1-03-memo#p1@T1 3.s2-d3-01-interview#p1@T1 4.s2-d3-01-memo#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s2-d3-01-memo#p2@T1 7.s2-d0-t1-91-interview#p3@T1 8.s1-d0-02-memo#p1@T1 9.s2-d0-01-memo#p1@T1 10.s2-d0-03-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 58. `s3-d0-01-q2`

- 问：竞品B在T1阶段新增了哪些服务功能？其价格如何调整？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-01-memo#p2@T1
- 金标要点：竞品B在高端套餐基础上新增家庭共享功能，价格上调至每月219元，尽管涨幅明显，但用户留存率仍维持在92%以上
- 词法前 10：1.s3-d0-01-memo#p2@T1 2.s3-d1-01-report#p2@T1 3.s3-d1-01-memo#p2@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s3-d0-01-report#p3@T1 6.s3-d0-02-a#p2@T1 7.s3-d0-04-memo#p1@T1 8.s3-d0-03-memo#p2@T1 9.s3-d0-01-report#p2@T1 10.s3-d3-01-report#p2@T1
- 混合前 10：1.s3-d0-04-memo#p1@T1 2.s3-d1-01-report#p2@T1 3.s3-d0-01-memo#p2@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-03-memo#p2@T1 6.s3-d0-03-memo#p1@T1 7.s3-d1-01-memo#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p2@T1 10.s3-d2-01-competitor-pricing#p2@T1
- 重排前 10：1.s3-d0-01-memo#p2@T1 2.s3-d1-01-memo#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d0-04-memo#p1@T1 5.s3-d1-01-report#p2@T1 6.s3-d3-01-report#p2@T1 7.s3-d0-03-memo#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p2@T1 10.s3-d0-03-memo#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 59. `s3-d0-01-q3`

- 问：在流量通话套餐比价里（竞品B新增家庭共享的那份），竞品C 在 T0 与 T1 之间调整了促销策略吗？具体变化是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-01-memo#p3@T1
- 金标要点：竞品C已于本季度初结束促销活动，标准套餐恢复至每月99元，且推出捆绑视频会员的新组合方案
- 词法前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-01-memo#p1@T1 5.s5-d2-t1-91-digest#p3@T1 6.s7-d0-t1-02-analysis#p3@T1 7.s3-d0-03-memo#p2@T1 8.s3-d3-01-report#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d3-01-memo#p3@T1
- 混合前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-memo#p1@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d0-04-memo#p2@T1 6.s3-d0-03-memo#p2@T1 7.s3-d3-01-memo#p3@T1 8.s3-d3-01-report#p2@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p2@T1
- 重排前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-01-memo#p1@T1 6.s3-d0-04-memo#p2@T1 7.s3-d0-03-memo#p2@T1 8.s3-d3-01-memo#p3@T1 9.s3-d1-01-report#p2@T1 10.s3-d3-01-memo#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 60. `s3-d0-02-q1`

- 问：在A、B、C三家公司的基础版比价中，T0 时A公司的基础版定价是多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p1@T0；s3-d0-02-b#p1@T0；s3-d0-02-c#p1@T0
- 金标要点：A公司推出基础版服务，定价为每月99元，包含核心功能模块，支持5个用户席位；基础款月费99元；A公司以99元定位形成价格优势
- 词法前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-b#p3@T0 3.s3-d0-04-memo#p3@T0 4.s3-d1-01-memo#p2@T0 5.s3-d0-03-memo#p1@T0 6.s3-d0-04-memo#p1@T0 7.s3-d0-02-b#p1@T0 8.s3-d0-01-report#p1@T0 9.s3-d0-03-report#p1@T0 10.s3-d3-01-memo#p1@T0
- 混合前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-04-memo#p3@T0 3.s3-d1-01-memo#p2@T0 4.s3-d0-03-memo#p1@T0 5.s3-d0-04-memo#p1@T0 6.s3-d0-02-c#p1@T0 7.s3-d3-01-memo#p1@T0 8.s3-d0-01-report#p1@T0 9.s3-d0-01-memo#p1@T0 10.s3-d0-03-report#p1@T0
- 重排前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-04-memo#p1@T0 4.s3-d3-01-memo#p1@T0 5.s3-d0-01-report#p1@T0 6.s3-d0-04-memo#p3@T0 7.s3-d1-01-memo#p2@T0 8.s3-d0-01-memo#p1@T0 9.s3-d0-03-report#p1@T0 10.s3-d0-02-c#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 61. `s3-d0-02-q2`

- 问：T1时B公司是否降低了其标准版的月费？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p2@T1；s3-d0-02-b#p2@T1；s3-d0-02-c#p2@T1
- 金标要点：B公司宣布全面降价，标准版降至109元/月，取消独立报表工具，转而整合入主控台，优化系统性能并降低运维门槛；B公司下调基础套餐价格至每月109元，移除部分高级功能以控制成本，但维持8人用户上限；B公司经过价格下调后
- 词法前 10：1.s3-d0-02-b#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d0-02-c#p2@T1 6.s3-d3-01-memo#p2@T1 7.s3-d1-01-memo#p2@T1 8.s3-d0-02-a#p2@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.p1-colaw-liquidation#p1@T1
- 混合前 10：1.s3-d0-02-b#p2@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d3-01-memo#p2@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d0-02-a#p2@T1 6.s3-d1-01-memo#p2@T1 7.s3-d0-04-memo#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d2-01-competitor-pricing#p3@T1
- 重排前 10：1.s3-d0-02-b#p2@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d3-01-memo#p2@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d0-02-a#p2@T1 6.s3-d1-01-memo#p2@T1 7.s3-d0-04-memo#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d2-01-competitor-pricing#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 62. `s3-d0-02-q3`

- 问：C公司在T0时提供的基础版是否包含客户支持？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T0
- 金标要点：C公司以低价切入市场，基础版仅售每月69元，但限制功能数量，且不提供客户支持；尽管性价比突出，但用户反馈对长期维护能力存疑
- 词法前 10：1.s3-d0-02-a#p3@T0 2.s3-d0-02-a#p1@T0 3.s3-d0-04-memo#p1@T0 4.s3-d0-02-b#p3@T0 5.s3-d0-03-report#p1@T0 6.s3-d2-01-quotation-snapshot#p1@T0 7.s3-d0-03-memo#p1@T0 8.s3-d1-01-memo#p2@T0 9.s3-d1-01-memo#p1@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-b#p3@T0 3.s3-d0-02-a#p3@T0 4.s7-d0-t0-01-qa#p2@T0 5.s3-d0-04-memo#p1@T0 6.s3-d2-01-quotation-snapshot#p1@T0 7.s3-d0-03-memo#p1@T0 8.s3-d0-02-c#p3@T0 9.s2-d0-02-interview#p1@T0 10.s3-d0-03-report#p1@T0
- 重排前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-a#p3@T0 3.s3-d0-04-memo#p1@T0 4.s3-d0-03-memo#p1@T0 5.s3-d0-03-report#p1@T0 6.s3-d0-02-b#p3@T0 7.s3-d2-01-quotation-snapshot#p1@T0 8.s2-d0-02-interview#p1@T0 9.s7-d0-t0-01-qa#p2@T0 10.s3-d0-02-c#p3@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 63. `s3-d0-02-q4`

- 问：T1时A公司基础版新增了哪些核心功能？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p1@T1；s3-d0-02-b#p1@T1
- 金标要点：新增团队协作工具；新增实时协同编辑与自动化工作流引擎
- 词法前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d2-01-quotation-snapshot#p1@T1 4.s3-d1-01-memo#p2@T1 5.s3-d0-02-c#p1@T1 6.s3-d0-02-a#p2@T1 7.s3-d0-04-memo#p1@T1 8.s3-d0-04-memo#p3@T1 9.s3-d3-01-memo#p1@T1 10.s3-d0-01-memo#p2@T1
- 混合前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-02-b#p3@T1 5.s4-d0-t1-02-guide#p3@T1 6.s6-d1-t1-91-release#p3@T1 7.s3-d0-02-a#p2@T1 8.s6-d0-t1-01-channel#p3@T1 9.s3-d0-03-memo#p2@T1 10.s3-d0-02-c#p1@T1
- 重排前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-02-a#p2@T1 5.s3-d0-02-c#p1@T1 6.s3-d0-02-b#p3@T1 7.s6-d1-t1-91-release#p3@T1 8.s6-d0-t1-01-channel#p3@T1 9.s3-d0-03-memo#p2@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 64. `s3-d0-02-q5`

- 问：在A、B、C三家公司的比价里，T0 时哪一家的定价低于90元？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T0；s3-d0-02-b#p3@T0；s3-d0-02-c#p3@T0
- 金标要点：C公司以低价切入市场，基础版仅售每月69元；C公司以69元最低价进入市场；C公司依托开源生态，推出免费基础版
- 词法前 10：1.s3-d0-03-memo#p1@T0 2.s3-d0-04-memo#p1@T0 3.p1-colaw-liquidation#p1@T0 4.s3-d0-02-c#p3@T0 5.s3-d3-01-report#p2@T0 6.p1-colaw-governance-supervisor-js#p1@T0 7.p1-colaw-capital#p1@T0 8.p1-colaw-governance-supervisor#p1@T0 9.s3-d0-01-report#p1@T0 10.p1-cac-o11#p10@T0
- 混合前 10：1.s3-d0-04-memo#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-02-c#p3@T0 4.s3-d0-01-report#p1@T0 5.s3-d3-01-report#p2@T0 6.s3-d1-01-memo#p2@T0 7.s3-d0-04-memo#p3@T0 8.s3-d0-02-c#p2@T0 9.s3-d0-01-memo#p2@T0 10.s3-d0-02-c#p1@T0
- 重排前 10：1.s3-d0-04-memo#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-01-report#p1@T0 4.s3-d0-01-memo#p2@T0 5.s3-d0-02-c#p3@T0 6.s3-d3-01-report#p2@T0 7.s3-d1-01-memo#p2@T0 8.s3-d0-02-c#p2@T0 9.s3-d0-04-memo#p3@T0 10.s3-d0-02-c#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 65. `s3-d0-02-q6`

- 问：T1时C公司是否仍然提供免费的基础版本？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-b#p3@T1；s3-d0-02-a#p3@T1
- 金标要点：C公司关闭免费基础版入口，改推“成长计划”订阅制，首年费用149元，含全功能访问及优先技术支持；C公司因技术债务问题暂停新客户注册，原69元套餐已取消，现仅开放限时试用，正式版本将于下季度以149元起售
- 词法前 10：1.s3-d0-02-b#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d0-02-b#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s3-d0-02-a#p3@T1 8.s3-d0-03-report#p1@T1 9.s3-d3-01-report#p3@T1 10.s3-d0-02-a#p1@T1
- 混合前 10：1.s3-d0-02-b#p3@T1 2.s3-d0-02-b#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d0-02-a#p1@T1 5.s3-d0-02-a#p3@T1 6.s3-d0-04-memo#p3@T1 7.s3-d2-t1-91-brochure#p1@T1 8.s3-d0-03-report#p1@T1 9.s4-d0-t1-02-guide#p3@T1 10.s3-d3-01-report#p3@T1
- 重排前 10：1.s3-d0-02-b#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d0-02-b#p1@T1 4.s3-d0-02-a#p1@T1 5.s3-d0-02-a#p3@T1 6.s3-d2-t1-91-brochure#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d3-01-report#p3@T1 9.s3-d0-04-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 66. `s3-d0-03-q2`

- 问：竞品B 的“精英版”套餐在 T1 有哪些新优惠或功能调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-03-memo#p2@T1
- 金标要点：竞品B更新其“精英版”套餐，新增30天免费试用，并将价格调整为每月420元，市场推广力度加大
- 词法前 10：1.s3-d0-03-memo#p2@T1 2.s3-d1-01-memo#p2@T1 3.s3-d0-03-report#p2@T1 4.s3-d0-01-memo#p2@T1 5.s3-d0-01-report#p2@T1 6.s3-d3-01-memo#p2@T1 7.s3-d0-04-memo#p2@T1 8.s3-d1-01-report#p2@T1 9.s7-d3-t1-05-claim#p1@T1 10.s3-d0-02-a#p2@T1
- 混合前 10：1.s3-d0-03-memo#p2@T1 2.s3-d0-04-memo#p2@T1 3.s3-d0-01-memo#p2@T1 4.s3-d3-01-memo#p2@T1 5.s3-d0-03-report#p2@T1 6.s3-d0-01-memo#p3@T1 7.s3-d1-01-memo#p2@T1 8.s3-d2-01-competitor-pricing#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d1-01-memo#p1@T1
- 重排前 10：1.s3-d0-03-memo#p2@T1 2.s3-d0-03-report#p2@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-01-memo#p2@T1 5.s3-d2-01-competitor-pricing#p2@T1 6.s3-d0-04-memo#p2@T1 7.s3-d0-01-memo#p3@T1 8.s3-d1-01-report#p2@T1 9.s3-d3-01-memo#p2@T1 10.s3-d1-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 67. `s3-d0-03-q3`

- 问：我方主推套餐在T0和T1之间是否有价格或服务内容的变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-03-memo#p3@T1
- 金标要点：我方主推套餐维持每月380元不变，但新增一项“客户忠诚计划”作为附加价值，涵盖额外培训资源
- 词法前 10：1.s3-d0-03-report#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d0-03-memo#p3@T1 4.s7-d3-t1-05-memo#p3@T1 5.p1-colaw-equity#p1@T1 6.s3-d1-01-report#p1@T1 7.s1-d0-01-analysis#p2@T1 8.s5-d2-t1-91-digest#p3@T1 9.s3-d0-01-memo#p2@T1 10.s7-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s3-d0-03-memo#p3@T1 2.s3-d1-01-report#p1@T1 3.s3-d0-03-report#p3@T1 4.s3-d0-01-memo#p2@T1 5.s3-d0-04-memo#p3@T1 6.s3-d0-03-memo#p1@T1 7.s3-d3-01-memo#p1@T1 8.s3-d3-01-report#p1@T1 9.s1-d0-01-analysis#p2@T1 10.s3-d0-02-a#p2@T1
- 重排前 10：1.s3-d0-03-report#p3@T1 2.s3-d0-03-memo#p3@T1 3.s3-d1-01-report#p1@T1 4.s3-d0-01-memo#p2@T1 5.s1-d0-01-analysis#p2@T1 6.s3-d0-04-memo#p3@T1 7.s3-d0-03-memo#p1@T1 8.s3-d3-01-memo#p1@T1 9.s3-d3-01-report#p1@T1 10.s3-d0-02-a#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 68. `s3-d1-01-q1`

- 问：在竞品C年度订阅价2,800元的那份比价中，竞品A 在 T1 的价格策略有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d1-01-memo#p1@T1；s3-d1-01-report#p1@T1
- 金标要点：竞品A已完成服务整合，将原独立模块打包进主套餐，价格上调至349元/月，但用户满意度调查显示其综合性价比获得认可；至本周期末，竞品A已将基础套餐调涨至每月349元，并将高级功能模块纳入主套餐内，不再单独计价
- 词法前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d1-01-report#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p1@T1 7.s3-d0-01-report#p1@T1 8.s3-d3-01-memo#p1@T1 9.s3-d0-01-memo#p3@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-03-report#p1@T1 5.s3-d3-01-report#p1@T1 6.s3-d1-01-report#p3@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p1@T1
- 重排前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d3-01-report#p1@T1 5.s3-d0-03-report#p1@T1 6.s3-d1-01-report#p3@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p1@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 69. `s3-d1-01-q3`

- 问：年度订阅价2,800元的那个竞品C，T0 时提供什么订阅方式？T1 又增加了哪些新选项？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d1-01-memo#p3@T1
- 金标要点：竞品C推出按月订阅选项，月费为269元，同时保留年度优惠价2,800元，进一步增强对中小客户的吸引力
- 词法前 10：1.s3-d1-01-memo#p3@T1 2.s3-d1-01-report#p3@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s3-d2-01-competitor-pricing#p2@T1 6.s3-d0-01-report#p3@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s3-d2-01-competitor-pricing#p3@T1 9.s3-d0-01-memo#p3@T1 10.s3-d0-03-report#p2@T1
- 混合前 10：1.s3-d1-01-memo#p3@T1 2.s3-d1-01-report#p3@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-03-report#p2@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d2-01-competitor-pricing#p2@T1 7.s3-d3-01-report#p1@T1 8.s3-d0-01-memo#p3@T1 9.s3-d0-03-report#p1@T1 10.s3-d0-02-b#p3@T1
- 重排前 10：1.s3-d1-01-memo#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d0-01-memo#p3@T1 4.s3-d1-01-report#p3@T1 5.s3-d3-01-memo#p3@T1 6.s3-d0-03-report#p2@T1 7.s3-d0-03-report#p1@T1 8.s3-d1-t1-91-quote#p3@T1 9.s3-d3-01-report#p1@T1 10.s3-d0-02-b#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 70. `s3-d2-01-q2`

- 问：在竞品C月费调到195元的那份比价里，以自动化报告为卖点的竞品B，T1 相比 T0 增加了哪些新服务内容？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d2-01-competitor-pricing#p2@T1
- 金标要点：竞品B在新版本基础上增加30天免费试用期，并将月费降至229元，同时优化了报告生成算法；显著提升响应速度
- 词法前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d0-04-memo#p2@T1 3.s3-d3-01-report#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s6-d0-t1-03-report#p3@T1 8.s3-d0-01-report#p3@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-04-memo#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-memo#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s3-d0-03-report#p1@T1 9.s3-d3-01-memo#p2@T1 10.s3-d0-01-report#p3@T1
- 重排前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-04-memo#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-memo#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s3-d0-03-report#p1@T1 9.s3-d0-01-report#p3@T1 10.s3-d3-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 71. `s3-d2-01-q3`

- 问：我方基础版服务包在T1时的定价与服务范围是否发生变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d2-01-quotation-snapshot#p1@T1
- 金标要点：基础版服务包价格上调至每月189元，巡检周期由月度改为双周一次，同时新增云端日志分析功能
- 词法前 10：1.s3-d0-03-report#p3@T1 2.s3-d0-04-memo#p3@T1 3.s3-d0-03-memo#p1@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s1-d0-01-analysis#p2@T1 7.s4-d0-t1-02-review#p2@T1 8.s3-d0-02-a#p1@T1 9.s6-d0-t1-03-report#p3@T1 10.s3-d2-01-quotation-snapshot#p2@T1
- 混合前 10：1.s3-d0-04-memo#p3@T1 2.s3-d0-03-memo#p1@T1 3.s3-d0-03-report#p3@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s3-d1-01-memo#p2@T1 8.s1-d0-01-analysis#p2@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s4-d0-t1-02-review#p2@T1
- 重排前 10：1.s3-d0-04-memo#p3@T1 2.s3-d0-03-memo#p1@T1 3.s3-d0-03-report#p3@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s3-d2-01-quotation-snapshot#p1@T1 6.s3-d2-01-quotation-snapshot#p2@T1 7.s3-d1-01-memo#p2@T1 8.s1-d0-01-analysis#p2@T1 9.s4-d0-t1-02-review#p2@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 72. `s3-d3-01-q3`

- 问：在竞品A附带云存储的那份比价里，竞品C的报价结构在T1相比T0发生了哪些关键调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p3@T1；s3-d3-01-report#p3@T1
- 金标要点：竞品C的报价结构已完成标准化改革，所有功能模块统一纳入89元基础包，有效降低用户决策成本；竞品C调整订阅策略，取消阶梯加价，统一为89元/月，涵盖全部功能模块，价格透明度大幅提升
- 词法前 10：1.s3-d3-01-memo#p1@T1 2.s3-d3-01-report#p3@T1 3.s3-d3-01-report#p2@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-01-report#p3@T1 8.s3-d1-t1-91-quote#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 混合前 10：1.s3-d3-01-memo#p1@T1 2.s3-d3-01-report#p3@T1 3.s3-d3-01-report#p2@T1 4.s3-d0-01-report#p3@T1 5.s3-d1-t1-91-quote#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-t1-91-pricesheet#p3@T1 8.s3-d0-03-report#p1@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 重排前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-01-report#p3@T1 4.s3-d3-01-memo#p1@T1 5.s3-d1-t1-91-quote#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d2-01-competitor-pricing#p1@T1 9.s3-d1-t1-91-pricesheet#p2@T1 10.s3-d1-t1-91-pricesheet#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 73. `s3-d3-01-q4`

- 问：在竞品C统一为89元基础包的那份比价里，从 T0 到 T1 各竞品的定价策略如何影响其市场定位？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p3@T1；s3-d3-01-report#p1@T1；s3-d3-01-report#p2@T1
- 金标要点：竞品A已全面推行新版套餐，价格上调至119元/月，同时增加企业级安全认证，目标客户转向中大型组织；竞品B的报价策略发生重大调整，取消固定高价，转而采用按需计费模式，月费最低可至99元，配合灵活服务包，大幅增强市场渗透力；竞品C调整订阅策略，取消阶梯加价，统一为89元/月，涵盖全部功能模块，价格透明度大幅提升，吸引大量中小客户迁移
- 词法前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d3-01-report#p2@T1 6.s3-d1-01-memo#p3@T1 7.s3-d0-01-report#p1@T1 8.s3-d1-01-memo#p2@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-report#p2@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d0-01-report#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d0-03-memo#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s3-d1-01-memo#p3@T1
- 重排前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-01-report#p3@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-01-memo#p3@T1 8.s3-d0-01-report#p1@T1 9.s3-d0-03-report#p1@T1 10.s3-d0-03-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 74. `s4-d0-t0-01-q1`

- 问：v2.3 版成本模型相比旧版在哪些方面实现了性能提升？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p1@T0；s4-d0-t0-01-memo#p2@T0；s4-d0-t0-01-report#p1@T0；s4-d0-t0-01-report#p3@T0
- 金标要点：新模型的准确率从76%提升至89%；模型运行时长由平均4.7秒降至2.3秒；平均误差率下降至3.2%，较上一版本降低1.8个百分点；日均处理效率提升约15%
- 词法前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-report#p3@T0 6.s4-d3-t0-05-summary#p1@T0 7.s1-d0-02-report#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d0-t0-01-plan#p1@T0
- 混合前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d3-t0-05-summary#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s4-d0-t0-01-report#p3@T0 5.s4-d1-t0-03-memo#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d3-t0-05-memo#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d3-t0-05-summary#p1@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-summary#p1@T0 8.s4-d0-t0-01-report#p3@T0 9.s4-d3-t0-05-memo#p2@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 75. `s4-d0-t0-01-q2`

- 问：为何在高层会议中使用旧版模型的决策方案被质疑？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-analysis#p2@T0
- 金标要点：在高层管理会议中，使用T0模型的决策方案被质疑为过于保守；而新模型提供更精细的成本拆解，有助于识别隐藏成本点，提升资源配置透明度
- 词法前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s4-d0-t0-01-report#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s5-d0-t0-01-internal#p3@T0 5.s3-d3-01-report#p3@T0 6.s5-d0-t0-01-internal#p1@T0 7.p1-colaw-governance#p2@T0 8.s4-d0-t0-01-summary#p1@T0 9.p1-colaw-equity#p5@T0 10.s2-d0-03-memo#p1@T0
- 混合前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s5-d0-t0-01-internal#p1@T0 3.s4-d0-t0-01-report#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s3-d3-01-report#p3@T0 7.s7-d1-t0-03-reason#p1@T0 8.s4-d1-t0-03-analysis#p1@T0 9.s4-d0-t0-01-summary#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s4-d0-t0-01-report#p1@T0 3.s5-d0-t0-01-internal#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s7-d1-t0-03-reason#p1@T0 7.s3-d3-01-report#p3@T0 8.s4-d1-t0-03-analysis#p1@T0 9.s4-d0-t0-01-summary#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 76. `s4-d0-t0-01-q3`

- 问：新模型在处理非标准流程时存在什么局限性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p3@T0
- 金标要点：当前模型仍存在对非标准流程的覆盖不足问题
- 词法前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d1-t0-03-memo#p1@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s4-d1-t0-03-report#p3@T0 8.s5-d0-t0-01-report#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d1-t0-03-analysis#p3@T0
- 混合前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d0-t0-01-summary#p1@T0 5.s4-d0-t0-01-summary#p3@T0 6.s4-d0-t0-01-report#p1@T0 7.s4-d1-t0-03-analysis#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d1-t0-03-memo#p1@T0 10.s1-d3-01-memo#p2@T0
- 重排前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d1-t0-03-memo#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d0-t0-01-report#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-summary#p3@T0 9.s4-d1-t0-03-analysis#p3@T0 10.s1-d3-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 77. `s4-d0-t0-01-q4`

- 问：为确保模型平滑过渡，已采取哪些协同措施？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-plan#p3@T0
- 金标要点：已启动跨团队协作机制，确保模型变更前完成影响评估与沟通预案，保障平滑过渡
- 词法前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d0-03-report#p3@T0 3.s1-d0-03-memo#p3@T0 4.s1-d0-04-memo#p2@T0 5.s1-d3-01-memo#p3@T0 6.p1-colaw-capital#p2@T0 7.s3-d0-03-report#p2@T0 8.s7-d0-t0-01-qa#p2@T0 9.s1-d2-01-analysis#p1@T0 10.s4-d1-t0-03-report#p3@T0
- 混合前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d3-01-memo#p3@T0 3.s1-d0-04-memo#p2@T0 4.s4-d0-t0-01-memo#p3@T0 5.s4-d0-t0-01-summary#p2@T0 6.s4-d0-t0-01-summary#p3@T0 7.s4-d0-t0-01-report#p1@T0 8.s1-d0-03-report#p3@T0 9.s4-d1-t0-03-analysis#p1@T0 10.s1-d0-03-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d0-03-report#p3@T0 3.s1-d3-01-memo#p3@T0 4.s1-d0-04-memo#p2@T0 5.s1-d0-03-memo#p3@T0 6.s4-d0-t0-01-memo#p3@T0 7.s4-d0-t0-01-summary#p2@T0 8.s4-d0-t0-01-summary#p3@T0 9.s4-d0-t0-01-report#p1@T0 10.s4-d1-t0-03-analysis#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 78. `s4-d0-t0-01-q5`

- 问：v2.3 版成本模型在哪些业务场景下表现出更强的适应性？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p2@T0；s4-d0-t0-01-report#p1@T0；s4-d0-t0-01-summary#p2@T0
- 金标要点：在复杂项目核算中，新模型的准确率从76%提升至89%；尤其在原材料价格波动场景下保持稳定输出；尤其在高负载时段表现更稳定
- 词法前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d0-t0-01-summary#p2@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d3-t0-05-memo#p1@T0 6.s4-d3-t0-05-summary#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d3-t0-05-analysis#p1@T0 10.s4-d0-t0-01-memo#p2@T0
- 混合前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d0-t0-01-summary#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s4-d3-t0-05-memo#p1@T0 5.s4-d3-t0-05-summary#p1@T0 6.s4-d0-t0-01-summary#p2@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 79. `s4-d0-t0-01-q6`

- 问：多方反馈中提出的三个改进建议分别是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-feedback#p1@T0；s4-d0-t0-01-feedback#p2@T0；s4-d0-t0-01-feedback#p3@T0
- 金标要点：来自财务部反馈：希望增加“人工工时”维度的细分统计，以便更精确地分配间接人力成本；技术团队建议：应明确模型版本标识规则，避免在报表中出现混淆引用；运营部门提出：期望在模型中加入季节性因子调节功能，以应对周期性业务高峰
- 词法前 10：1.s5-d0-t0-01-internal#p2@T0 2.s1-d0-05-warn#p1@T0 3.s4-d0-t0-01-feedback#p3@T0 4.s5-d0-t0-01-memo#p3@T0 5.s1-d0-01-memo#p2@T0 6.s5-d2-t0-04-analysis#p2@T0 7.s5-d0-t0-01-internal#p1@T0 8.s4-d3-t0-05-analysis#p1@T0 9.s2-d0-01-report#p2@T0 10.s4-d0-t0-01-report#p2@T0
- 混合前 10：1.s1-d0-05-warn#p1@T0 2.s5-d0-t0-01-memo#p3@T0 3.s5-d0-t0-01-internal#p2@T0 4.s2-d0-01-report#p2@T0 5.s1-d0-01-memo#p2@T0 6.s5-d0-t0-01-internal#p1@T0 7.s4-d0-t0-01-analysis#p3@T0 8.s2-d0-02-memo#p3@T0 9.s1-d1-01-memo#p3@T0 10.s2-d2-01-memo#p1@T0
- 重排前 10：1.s1-d0-01-memo#p2@T0 2.s2-d2-01-memo#p1@T0 3.s1-d0-05-warn#p1@T0 4.s5-d0-t0-01-memo#p3@T0 5.s5-d0-t0-01-internal#p2@T0 6.s2-d0-01-report#p2@T0 7.s5-d0-t0-01-internal#p1@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s2-d0-02-memo#p3@T0 10.s1-d1-01-memo#p3@T0
- 建议：保持 bm25
- 理由：词法的前 10 条里有金标，混合没有。

### 80. `s4-d0-t1-02-q1`

- 问：计划11月启动全量灰度的那版成本模型，T1 版本相比 T0 版本有哪些改进？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-memo#p1@T1；s4-d0-t1-02-memo#p2@T1；s4-d0-t1-02-report#p2@T1
- 金标要点：预测准确率从76.3%升至89.1%；引入动态分摊算法以提升跨项目资源分配的准确性；对人力工时与设备折旧的非线性权重调整
- 词法前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d2-t1-04-internal#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-review#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d2-t1-04-report#p1@T1 9.s4-d0-t1-02-review#p1@T1 10.s4-d0-t1-02-memo#p1@T1
- 混合前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d2-t1-04-memo#p3@T1 8.s6-d0-t1-03-memo#p2@T1 9.s4-d2-t1-04-summary#p1@T1 10.s3-d2-01-competitor-pricing#p2@T1
- 重排前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s4-d2-t1-04-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 81. `s4-d0-t1-02-q2`

- 问：计划11月全量灰度的那版成本模型，在高并发场景下的预测表现如何？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-memo#p2@T1；s4-d0-t1-02-report#p2@T1
- 金标要点：特别强化了高并发场景下的弹性成本预测能力；平均预算偏差减少28%；预测准确率从76.3%升至89.1%
- 词法前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d0-t1-02-memo#p2@T1 4.s4-d0-t1-02-plan#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s2-d3-01-memo#p3@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-report#p1@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s1-d3-01-memo#p3@T1
- 混合前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-plan#p1@T1 9.s4-d2-t1-04-summary#p1@T1 10.s4-d2-t1-04-summary#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d0-t1-02-plan#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-plan#p1@T1 9.s4-d2-t1-04-summary#p2@T1 10.s4-d2-t1-04-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 82. `s4-d0-t1-02-q3`

- 问：为何新版本在低频任务中出现预算预留增加？其优势是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-analysis#p2@T1；s4-d0-t1-02-analysis#p3@T1
- 金标要点：在低频任务中，新版模型倾向于保守估计，导致预算预留增加约7.6%，但有效避免了超支风险；该策略已被运营团队采纳为标准配置；整体风险控制收益远超成本波动影响
- 词法前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s3-d0-02-c#p2@T1 5.s2-d2-01-memo#p1@T1 6.s4-d0-t1-02-review#p1@T1 7.s2-d2-01-memo#p3@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-claim#p3@T1 10.s3-d0-03-report#p2@T1
- 混合前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s2-d2-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d0-t1-02-report#p1@T1 8.s4-d0-t1-02-memo#p2@T1 9.s4-d0-t1-02-review#p2@T1 10.s2-d2-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s2-d2-01-memo#p1@T1 5.s4-d0-t1-02-memo#p1@T1 6.s2-d2-01-memo#p3@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-report#p1@T1 9.s4-d0-t1-02-memo#p2@T1 10.s4-d0-t1-02-review#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 83. `s4-d0-t1-02-q4`

- 问：成本模型的下一步迭代路线图包含哪些关键任务？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-plan#p1@T1；s4-d0-t1-02-plan#p2@T1；s4-d0-t1-02-plan#p3@T1
- 金标要点：本年度模型优化计划聚焦三大方向：一是增强对异构硬件的成本映射能力，二是建立实时反馈闭环以动态修正参数；路线图明确要求每季度进行一次跨部门验证，确保模型适应实际业务变化；整合外部市场数据源实现成本趋势预警；模型可解释性模块的开发
- 词法前 10：1.s4-d2-t1-04-summary#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d2-t1-04-memo#p1@T1 5.s6-d0-t1-03-internal#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-report#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s6-d0-t1-02-memo#p3@T1 10.s6-d0-t1-02-report#p3@T1
- 混合前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d2-t1-04-summary#p3@T1 4.s4-d0-t1-02-plan#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d0-t1-02-analysis#p1@T1 9.s6-d0-t1-03-internal#p2@T1 10.s4-d2-t1-04-internal#p3@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s4-d2-t1-04-summary#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d2-t1-04-internal#p3@T1 10.s4-d0-t1-02-plan#p3@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 84. `s4-d0-t1-02-q5`

- 问：使用T1版本模型时，用户需要注意哪些操作规范？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-guide#p1@T1；s4-d0-t1-02-guide#p2@T1；s4-d0-t1-02-guide#p3@T1
- 金标要点：本指南更新内容涵盖新模型的参数配置方法、典型场景应用示例及常见错误规避建议；用户应定期检查模型输出中的置信区间，当低于85%时需人工复核；所有新建项目必须采用T1版本作为默认测算基准，旧版本仅限历史数据追溯用途；需启用“弹性阈值”选项以适配突发流量场景
- 词法前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s6-d3-t1-02-memo#p1@T1 5.s2-d2-01-memo#p1@T1 6.s4-d2-t1-04-summary#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s2-d0-03-memo#p1@T1 9.s6-d0-t1-01-channel#p3@T1 10.s1-d1-01-analysis#p1@T1
- 混合前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p3@T1 3.s4-d0-t1-02-guide#p2@T1 4.s7-d0-t1-02-update#p2@T1 5.s4-d2-t1-04-summary#p1@T1 6.s2-d2-01-memo#p1@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.s6-d3-t1-03-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p2@T1 3.s2-d2-01-memo#p1@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s7-d0-t1-02-update#p3@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-summary#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.s6-d3-t1-03-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 85. `s4-d0-t1-02-q6`

- 问：评审会议对模型的后续发展提出了哪些建议？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-review#p2@T1
- 金标要点：在未来版本中加入成本敏感度分析功能；扩展对云服务阶梯定价的支持
- 词法前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-review#p3@T1 3.s7-d2-t1-04-memo#p3@T1 4.s4-d0-t1-02-plan#p2@T1 5.p1-colaw-governance-supervisor#p4@T1 6.p1-colaw-governance-supervisor-js#p2@T1 7.s2-d3-t1-91-minutes#p1@T1 8.s5-d3-t1-05-memo#p1@T1 9.s5-d0-t1-02-analysis#p1@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-plan#p2@T1 3.s4-d0-t1-02-report#p3@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s4-d2-t1-04-internal#p1@T1 6.s4-d0-t1-02-review#p3@T1 7.s4-d2-t1-04-internal#p2@T1 8.s7-d0-t1-02-brief#p2@T1 9.s1-d2-01-analysis#p2@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-plan#p2@T1 3.s4-d0-t1-02-review#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s4-d0-t1-02-report#p3@T1 6.s2-d3-t1-91-minutes#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d2-t1-04-internal#p2@T1 9.s2-d3-01-memo#p1@T1 10.s1-d2-01-analysis#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 86. `s4-d1-t0-03-q1`

- 问：新版本成本模型如何改进固定与可变成本的区分精度？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p1@T0
- 金标要点：本次内部测算模型在成本结构分析中引入了动态分摊机制，显著提升了对固定成本与可变成本的区分精度；新版本通过加权平均法处理跨周期投入，使单位产出成本估算偏差率下降至5.2%以下
- 词法前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d0-t0-01-analysis#p2@T0 4.s4-d3-t0-05-memo#p3@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d0-t0-01-summary#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s4-d3-t0-05-analysis#p3@T0 10.s4-d3-t0-05-analysis#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-analysis#p2@T0 6.s4-d0-t0-01-summary#p1@T0 7.s4-d0-t0-01-report#p1@T0 8.s4-d1-t0-03-analysis#p3@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d3-t0-05-analysis#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d1-t0-03-analysis#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 87. `s4-d1-t0-03-q2`

- 问：本次模型迭代中移除了哪些冗余计算项？带来了什么影响？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p2@T0
- 金标要点：针对历史数据中存在冗余计算项的问题，已剔除重复归集的间接费用模块；该调整使模型运行效率提升约18%，同时增强结果可解释性
- 词法前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d1-t0-03-memo#p1@T0 4.s7-d0-t0-01-qa#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s7-d0-t0-01-qa#p1@T0 7.s4-d3-t0-05-memo#p3@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s4-d3-t0-05-memo#p1@T0 10.s4-d3-t0-05-analysis#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-analysis#p3@T0 5.s4-d0-t0-01-analysis#p1@T0 6.s4-d3-t0-05-memo#p3@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d0-t0-01-analysis#p2@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-analysis#p3@T0 5.s4-d0-t0-01-analysis#p1@T0 6.s4-d3-t0-05-memo#p3@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d0-t0-01-report#p1@T0 10.s4-d0-t0-01-analysis#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 88. `s4-d1-t0-03-q3`

- 问：新版本模型支持哪几类核心成本拆解？对预算规划有何帮助？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p3@T0
- 金标要点：当前版本支持多维度成本拆解，包括人力、设备、运维及外部服务四类核心支出，为后续预算规划提供更细粒度支撑
- 词法前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d0-t0-01-analysis#p2@T0 3.s4-d0-t0-01-plan#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d1-t0-03-plan#p2@T0 9.s4-d1-t0-03-report#p1@T0 10.s4-d0-t0-01-report#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s4-d1-t0-03-analysis#p3@T0 4.s4-d0-t0-01-analysis#p2@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d1-t0-03-plan#p2@T0 8.s4-d0-t0-01-plan#p2@T0 9.s4-d3-t0-05-summary#p1@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s4-d1-t0-03-memo#p1@T0 4.s4-d0-t0-01-plan#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s4-d0-t0-01-analysis#p2@T0 7.s4-d0-t0-01-report#p1@T0 8.s4-d3-t0-05-summary#p1@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d1-t0-03-plan#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 89. `s4-d1-t0-03-q4`

- 问：未来版本计划引入哪些关键技术能力？预期达到什么效果？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-plan#p1@T0；s4-d1-t0-03-plan#p2@T0；s4-d1-t0-03-plan#p3@T0
- 金标要点：计划下一阶段引入实时数据流接入能力，以支持动态成本重估，目标是将响应延迟压缩至分钟级；增加成本敏感度分析模块，帮助识别关键影响因子，辅助管理层制定策略调整预案；探索与外部经济指标联动建模，提升宏观环境变化应对能力
- 词法前 10：1.s4-d1-t0-03-plan#p1@T0 2.s7-d0-t0-01-qa#p2@T0 3.s1-d1-01-memo#p1@T0 4.s1-d0-01-memo#p1@T0 5.s7-d0-t0-01-qa#p1@T0 6.s1-d0-02-report#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s1-d0-03-memo#p3@T0 9.s2-d0-02-interview#p1@T0 10.s2-d0-03-interview#p3@T0
- 混合前 10：1.s1-d0-01-memo#p1@T0 2.s4-d1-t0-03-plan#p1@T0 3.s1-d0-02-report#p3@T0 4.s4-d3-t0-05-summary#p3@T0 5.s2-d0-03-interview#p3@T0 6.s2-d2-01-memo#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s2-d0-03-memo#p3@T0 9.s1-d0-03-memo#p3@T0 10.s1-d1-01-memo#p1@T0
- 重排前 10：1.s4-d1-t0-03-plan#p1@T0 2.s1-d0-01-memo#p1@T0 3.s1-d0-02-report#p3@T0 4.s4-d3-t0-05-summary#p3@T0 5.s2-d0-03-interview#p3@T0 6.s2-d2-01-memo#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s1-d0-03-memo#p3@T0 9.s1-d1-01-memo#p1@T0 10.s2-d0-03-memo#p3@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 90. `s4-d2-t1-04-q1`

- 问：可用性维持在99.98%以上的那版成本模型，相比旧版预测准确率提升了多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p2@T1
- 金标要点：误差率由原先的8.7%降至4.3%
- 词法前 10：1.s4-d2-t1-04-summary#p2@T1 2.s4-d2-t1-04-memo#p1@T1 3.s4-d0-t1-02-report#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s3-d0-02-c#p2@T1 6.s6-d0-t1-03-memo#p2@T1 7.s4-d0-t1-02-memo#p1@T1 8.s6-d0-t1-03-report#p2@T1 9.s6-d0-t1-03-internal#p2@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s4-d0-t1-02-report#p2@T1 2.s4-d0-t1-02-analysis#p3@T1 3.s4-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-report#p1@T1 5.s4-d2-t1-04-summary#p2@T1 6.s4-d2-t1-04-memo#p2@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s4-d0-t1-02-memo#p1@T1 10.s7-d2-t1-04-memo#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d2-t1-04-summary#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p2@T1 8.s7-d2-t1-04-memo#p2@T1 9.s6-d0-t1-03-memo#p2@T1 10.s4-d2-t1-04-summary#p1@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 91. `s4-d2-t1-04-q2`

- 问：跨区域部署时，边缘机房每单位算力的花费比中心机房便宜多少百分比？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-report#p1@T1
- 金标要点：结果显示，边缘节点的单位计算成本较中心节点低19.6%；本报告基于最新版本的成本模型进行测算，重点分析了多区域部署下的资源利用率差异
- 词法前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s1-d0-03-report#p2@T1 4.s6-d0-t1-01-patch#p1@T1 5.s4-d2-t1-91-review#p2@T1 6.s5-d0-t1-02-analysis#p3@T1 7.s3-d0-03-report#p1@T1 8.s2-d0-04-memo#p2@T1 9.s4-d2-t1-04-internal#p2@T1 10.p2-gdp-national#p3@T1
- 混合前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d2-t1-91-review#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s1-d0-03-report#p2@T1 5.s2-d1-01-memo#p1@T1 6.s3-d2-01-competitor-pricing#p1@T1 7.s3-d1-t1-91-pricesheet#p1@T1 8.s5-d0-t1-02-analysis#p3@T1 9.s5-d1-t1-03-memo#p3@T1 10.s3-d0-04-memo#p2@T1
- 重排前 10：1.s4-d2-t1-04-report#p1@T1 2.s5-d0-t1-02-analysis#p3@T1 3.s4-d2-t1-91-review#p2@T1 4.s4-d0-t1-02-memo#p1@T1 5.s1-d0-03-report#p2@T1 6.s2-d1-01-memo#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s3-d2-01-competitor-pricing#p1@T1 9.s3-d1-t1-91-pricesheet#p1@T1 10.s3-d0-04-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 92. `s4-d2-t1-04-q3`

- 问：边缘节点单位成本比中心低近两成的那版成本模型，做了哪些关键优化来减少资源浪费？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p1@T1；s4-d2-t1-04-report#p2@T1
- 金标要点：引入弹性伸缩阈值优化；资源浪费减少31%；引入动态权重调整机制以提升预测准确率
- 词法前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d2-t1-04-report#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s2-d0-01-report#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s1-d0-04-memo#p2@T1 8.s4-d0-t1-02-memo#p2@T1 9.s4-d0-t1-02-analysis#p3@T1 10.s4-d2-t1-04-memo#p1@T1
- 混合前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-plan#p1@T1 4.s4-d2-t1-04-report#p2@T1 5.s4-d0-t1-02-memo#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-analysis#p3@T1 9.s4-d2-t1-91-model-v3#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 重排前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d2-t1-04-report#p2@T1 4.s4-d0-t1-02-plan#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-analysis#p3@T1 9.s4-d2-t1-91-model-v3#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 93. `s4-d2-t1-04-q4`

- 问：为确保模型长期适用性，计划采取什么措施进行持续优化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p3@T1
- 金标要点：后续将基于真实流量数据持续优化参数，确保长期适应性
- 词法前 10：1.s4-d2-t1-04-memo#p3@T1 2.s4-d0-t1-02-plan#p3@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-plan#p1@T1 5.s7-d0-t1-02-update#p2@T1 6.s3-d0-03-memo#p3@T1 7.s2-d1-01-memo#p2@T1 8.s2-d0-02-interview#p3@T1 9.s3-d2-01-quotation-snapshot#p3@T1 10.s1-d0-02-memo#p2@T1
- 混合前 10：1.s4-d2-t1-04-memo#p3@T1 2.s4-d0-t1-02-plan#p1@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-plan#p3@T1 5.s2-d0-02-interview#p3@T1 6.s6-d0-t1-03-report#p1@T1 7.s4-d0-t1-02-analysis#p2@T1 8.s1-d0-02-memo#p2@T1 9.s3-d0-03-memo#p3@T1 10.s4-d0-t1-02-plan#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p3@T1 2.s4-d0-t1-02-plan#p1@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-plan#p3@T1 5.s2-d0-02-interview#p3@T1 6.s6-d0-t1-03-report#p1@T1 7.s4-d0-t1-02-analysis#p2@T1 8.s1-d0-02-memo#p2@T1 9.s3-d0-03-memo#p3@T1 10.s4-d0-t1-02-plan#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 94. `s4-d3-t0-05-q1`

- 问：新版本成本模型在高并发场景下的平均响应延迟是多少？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-memo#p1@T0
- 金标要点：模型在模拟高并发场景下表现稳定，平均响应延迟控制在210毫秒以内，资源峰值使用率未超过78%
- 词法前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d1-t0-03-report#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s2-d2-01-memo#p3@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-analysis#p1@T0 7.s4-d1-t0-03-plan#p1@T0 8.s4-d3-t0-05-analysis#p3@T0 9.s4-d0-t0-01-summary#p2@T0 10.s2-d2-01-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d3-t0-05-summary#p1@T0 3.s4-d1-t0-03-analysis#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-plan#p1@T0 7.s4-d3-t0-05-memo#p3@T0 8.s4-d1-t0-03-memo#p1@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d1-t0-03-report#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d0-t0-01-report#p1@T0 5.s4-d1-t0-03-analysis#p1@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 95. `s4-d3-t0-05-q2`

- 问：v1.4版本相比v1.2在初始化时间上缩短了多少秒？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-analysis#p2@T0
- 金标要点：其初始化时间平均为47秒，较v1.2缩短了12秒，且具备更优的容错恢复能力；v1.4的部署复杂度略有上升，但通过自动化脚本可有效缓解
- 词法前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s4-d3-t0-05-analysis#p1@T0 3.s7-d0-t0-01-arch#p3@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s4-d0-t0-01-memo#p1@T0 6.s4-d0-t0-01-report#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s3-d0-t0-91-flyer#p2@T0 9.s5-d2-t0-04-analysis#p3@T0 10.s4-d3-t0-05-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s4-d3-t0-05-analysis#p1@T0 3.s7-d0-t0-01-arch#p3@T0 4.s4-d0-t0-01-report#p3@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s4-d0-t0-01-memo#p1@T0 7.s5-d2-t0-04-analysis#p3@T0 8.s4-d1-t0-03-analysis#p2@T0 9.s4-d3-t0-05-memo#p1@T0 10.s4-d3-t0-05-summary#p1@T0
- 重排前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s7-d0-t0-01-arch#p3@T0 3.s4-d3-t0-05-analysis#p1@T0 4.s4-d0-t0-01-memo#p1@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s5-d2-t0-04-analysis#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s4-d3-t0-05-memo#p1@T0 9.s4-d3-t0-05-summary#p1@T0 10.s4-d0-t0-01-report#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 96. `s4-d3-t0-05-q3`

- 问：新版本成本模型在数据预处理阶段的效率提升了多少百分比？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-memo#p2@T0
- 金标要点：测算结果显示，新模型在数据预处理阶段效率提升约19%，主要得益于动态调度机制的优化；该改进使任务队列吞吐量增加至每分钟1200条，较旧版本提升近三成
- 词法前 10：1.s4-d3-t0-05-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d0-t0-01-analysis#p2@T0 5.s4-d0-t0-01-memo#p2@T0 6.s4-d0-t0-01-summary#p3@T0 7.s4-d0-t0-01-summary#p1@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d1-t0-03-report#p1@T0 10.s2-d0-02-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d0-t0-01-report#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d1-t0-03-report#p1@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d0-t0-01-summary#p3@T0
- 重排前 10：1.s4-d3-t0-05-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d0-t0-01-report#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d1-t0-03-report#p1@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d0-t0-01-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 97. `s4-d3-t0-05-q4`

- 问：为解决内存泄漏问题，团队采取了哪些具体措施？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-report#p2@T0
- 金标要点：针对该问题，团队已实施缓冲区大小动态调整策略，并引入周期性垃圾回收机制
- 词法前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d3-t0-05-summary#p2@T0 5.p1-colaw-capital#p2@T0 6.s7-d0-t0-01-qa#p2@T0 7.s3-d0-03-report#p2@T0 8.s2-d0-04-memo#p2@T0 9.s1-d0-03-report#p3@T0 10.s4-d0-t0-01-report#p3@T0
- 混合前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s4-d3-t0-05-summary#p2@T0 4.s5-d0-t0-01-memo#p2@T0 5.p1-cac-o11#p10@T0 6.s7-d0-t0-01-internal#p1@T0 7.s1-d0-03-memo#p2@T0 8.s1-d0-02-memo#p2@T0 9.s4-d0-t0-01-memo#p1@T0 10.s7-d0-t0-01-qa#p1@T0
- 重排前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d3-t0-05-summary#p2@T0 5.s5-d0-t0-01-memo#p2@T0 6.p1-cac-o11#p10@T0 7.s7-d0-t0-01-internal#p1@T0 8.s1-d0-03-memo#p2@T0 9.s1-d0-02-memo#p2@T0 10.s4-d0-t0-01-memo#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 98. `s5-d0-t0-01-q1`

- 问：综合多份文档来看，协作机制在响应速度和响应时间上有哪些量化成效？其推广又面临哪三大挑战？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-report#p1@T0；s5-d0-t0-01-analysis#p1@T0；s5-d0-t0-01-summary#p2@T0
- 金标要点：在公共服务响应速度上平均提升了约40%；在处理突发事件时平均缩短响应时间2.3小时；技术适配性不足、组织惯性阻力大、外部监督机制缺失
- 词法前 10：1.s5-d0-t0-01-memo#p3@T0 2.s5-d0-t0-01-summary#p2@T0 3.s4-d3-t0-05-summary#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s5-d0-t0-01-summary#p1@T0 6.s5-d0-t0-01-analysis#p1@T0 7.s5-d0-t0-01-report#p1@T0 8.s3-d0-01-report#p2@T0 9.s7-d0-t0-01-arch#p3@T0 10.s5-d2-t0-04-memo#p3@T0
- 混合前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d0-t0-01-summary#p2@T0 3.s5-d0-t0-01-summary#p1@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-report#p1@T0 7.s5-d0-t0-01-press#p1@T0 8.s5-d0-t0-01-memo#p3@T0 9.s1-d0-03-report#p2@T0 10.s2-d2-01-report#p2@T0
- 重排前 10：1.s5-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-summary#p3@T0 3.s5-d0-t0-01-summary#p1@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-report#p1@T0 7.s5-d0-t0-01-press#p1@T0 8.s5-d0-t0-01-summary#p2@T0 9.s1-d0-03-report#p2@T0 10.s2-d2-01-report#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 99. `s5-d0-t0-01-q2`

- 问：关于社区服务里的协作平台（某市智慧协作平台），不同来源的评价有矛盾吗？请举例并分析原因。
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-memo#p2@T0；s5-d0-t0-01-press#p1@T0；s5-d0-t0-01-press#p2@T0
- 金标要点：得分达87分；被视为创新典范；报道强调其“零延迟”响应能力；该平台实际覆盖范围仅限于主城区，偏远社区仍依赖传统方式，存在信息孤岛现象；在试点阶段曾出现沟通延迟问题；主要因责任划分不清导致执行脱节
- 词法前 10：1.s5-d0-t0-01-press#p1@T0 2.s5-d0-t0-01-report#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s5-d2-t0-04-analysis#p1@T0 5.s1-d0-04-memo#p3@T0 6.p1-colaw-governance#p3@T0 7.s5-d0-t0-01-memo#p1@T0 8.s5-d2-t0-04-report#p2@T0 9.p1-colaw-equity#p4@T0 10.s5-d2-t0-04-analysis#p2@T0
- 混合前 10：1.s5-d0-t0-01-report#p1@T0 2.s5-d0-t0-01-press#p1@T0 3.s5-d0-t0-01-memo#p1@T0 4.s5-d0-t0-01-summary#p1@T0 5.s5-d0-t0-01-internal#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-03-report#p2@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s5-d2-t0-04-analysis#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s5-d0-t0-01-press#p1@T0 2.s5-d0-t0-01-report#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s5-d2-t0-04-analysis#p2@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-summary#p1@T0 7.s5-d0-t0-01-internal#p2@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s4-d3-t0-05-summary#p3@T0 10.s1-d0-03-report#p2@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 100. `s5-d0-t0-01-q3`

- 问：从文档中提取支持‘该机制在偏远地区效果不佳’这一观点的证据。
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-press#p2@T0；s5-d0-t0-01-report#p2@T0
- 金标要点：在资源紧张区域效果不显著；偏远社区仍依赖传统方式，存在信息孤岛现象
- 词法前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-claim#p3@T0 4.s7-d1-t0-03-fact#p2@T0 5.s7-d1-t0-03-reason#p3@T0 6.s7-d1-t0-03-memo#p1@T0 7.s7-d1-t0-03-reason#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s4-d3-t0-05-summary#p3@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-memo#p3@T0 3.s7-d1-t0-03-fact#p2@T0 4.s5-d0-t0-01-memo#p3@T0 5.s5-d0-t0-01-memo#p1@T0 6.s7-d1-t0-03-reason#p2@T0 7.s7-d1-t0-03-reason#p1@T0 8.s5-d0-t0-01-report#p2@T0 9.s5-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-fact#p2@T0 3.s5-d0-t0-01-memo#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d1-t0-03-memo#p3@T0 7.s5-d0-t0-01-summary#p1@T0 8.s4-d3-t0-05-summary#p3@T0 9.s5-d0-t0-01-memo#p3@T0 10.s5-d0-t0-01-report#p2@T0
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 101. `s5-d0-t0-01-q4`

- 问：哪份文档最直接支持‘系统界面复杂影响使用率’这一说法？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-internal#p1@T0
- 金标要点：在2023年第一季度的跨部门协调会上，多位负责人反映系统界面复杂，操作门槛高，导致基层人员使用意愿低；此问题被列为优先改进项
- 词法前 10：1.s7-d1-t0-03-claim#p3@T0 2.s7-d1-t0-03-reason#p2@T0 3.s7-d1-t0-03-claim#p1@T0 4.s7-d1-t0-03-reason#p3@T0 5.s5-d0-t0-01-analysis#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-memo#p2@T0 8.s5-d0-t0-01-internal#p1@T0 9.s5-d2-t0-04-memo#p3@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s5-d0-t0-01-analysis#p2@T0 2.s7-d1-t0-03-reason#p2@T0 3.s7-d0-t0-01-qa#p2@T0 4.s5-d0-t0-01-internal#p1@T0 5.s7-d0-t0-01-arch#p2@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d1-t0-03-reason#p1@T0 8.s7-d1-t0-03-memo#p2@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-claim#p1@T0
- 重排前 10：1.s7-d1-t0-03-reason#p2@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-claim#p1@T0 4.s5-d0-t0-01-analysis#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s5-d0-t0-01-internal#p1@T0 7.s7-d1-t0-03-fact#p3@T0 8.s7-d0-t0-01-arch#p2@T0 9.s7-d0-t0-01-internal#p3@T0 10.s7-d1-t0-03-reason#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 102. `s5-d0-t0-01-q5`

- 问：根据现有材料，能否得出‘该机制已证明完全可行’的结论？为什么？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-memo#p3@T0；s5-d0-t0-01-report#p2@T0；s5-d0-t0-01-summary#p3@T0
- 金标要点：当前所有结论均基于局部经验与间接数据，尚无权威机构出具全面评估报告，应谨慎对待其广泛推广建议。；平台运行依赖人工协调，自动化程度不足，且在资源紧张区域效果不显著。；该机制的成效存在争议，需更多实证研究以明确其适用边界与改进方向。
- 词法前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-reason#p2@T0 3.s2-d3-01-interview#p3@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-memo#p2@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d1-t0-03-memo#p1@T0 8.s5-d2-t0-04-report#p3@T0 9.s7-d0-t0-01-qa#p2@T0 10.s7-d1-t0-03-reason#p1@T0
- 混合前 10：1.s7-d1-t0-03-memo#p3@T0 2.s2-d3-01-interview#p3@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-claim#p2@T0 5.s7-d1-t0-03-claim#p3@T0 6.s5-d0-t0-01-memo#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s7-d0-t0-01-report#p3@T0 10.s5-d0-t0-01-summary#p1@T0
- 重排前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-memo#p3@T0 3.s7-d1-t0-03-claim#p2@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-reason#p2@T0 6.s2-d3-01-interview#p3@T0 7.s5-d0-t0-01-memo#p3@T0 8.s7-d1-t0-03-claim#p1@T0 9.s5-d0-t0-01-summary#p1@T0 10.s7-d0-t0-01-report#p3@T0
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 103. `s5-d0-t0-01-q6`

- 问：如果要在未来一年内推动该机制全面推广，基于文档内容，应优先解决哪些问题？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-analysis#p3@T0；s5-d0-t0-01-internal#p1@T0；s5-d0-t0-01-internal#p2@T0；s5-d0-t0-01-summary#p2@T0
- 金标要点：建议在全面推广前，建立标准化培训体系，并设定阶段性评估节点，以动态优化机制设计。；多位负责人反映系统界面复杂，操作门槛高，导致基层人员使用意愿低。；若能整合现有政务平台接口，可降低重复录入负担，提升数据一致性。；但其推广面临三大挑战：技术适配性不足、组织惯性阻力大、外部监督机制缺失。这些因素共同制约其规模化应用
- 词法前 10：1.s4-d3-t0-05-summary#p3@T0 2.s7-d0-t0-01-qa#p1@T0 3.s5-d0-t0-01-analysis#p3@T0 4.s1-d0-03-report#p2@T0 5.s5-d2-t0-04-memo#p3@T0 6.s5-d0-t0-01-summary#p3@T0 7.s5-d0-t0-01-internal#p1@T0 8.s1-d0-01-memo#p2@T0 9.s4-d3-t0-05-report#p2@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d0-t0-01-analysis#p3@T0 3.s5-d0-t0-01-summary#p3@T0 4.s5-d0-t0-01-internal#p1@T0 5.s2-d0-02-interview#p1@T0 6.s1-d0-03-report#p2@T0 7.s5-d2-t0-04-analysis#p3@T0 8.s4-d1-t0-03-plan#p3@T0 9.s1-d0-02-memo#p1@T0 10.s5-d0-t0-01-memo#p1@T0
- 重排前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s5-d0-t0-01-analysis#p3@T0 4.s5-d0-t0-01-internal#p1@T0 5.s2-d0-02-interview#p1@T0 6.s1-d0-03-report#p2@T0 7.s1-d0-02-memo#p1@T0 8.s5-d0-t0-01-memo#p1@T0 9.s5-d0-t0-01-summary#p3@T0 10.s4-d1-t0-03-plan#p3@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 104. `s5-d0-t1-02-q1`

- 问：以城市交通拥堵指标和“青少年近视率超一半”为例，二手数据是怎样通过反复引用变成“被接受的真相”的？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p1@T1；s5-d0-t1-02-memo#p3@T1；s5-d0-t1-02-summary#p1@T1；s5-d0-t1-02-summary#p2@T1
- 金标要点：被多家媒体和智库间接转述；最早可追溯至2014年某高校调研；即使原始数据无法验证，只要被多次引用并嵌入正式论述，便可能成为“事实”本身；这些数据往往经过多次转述，每一次传递都可能引入轻微变形，最终形成一种“集体记忆式事实”。；尽管近年新调查显示实际比例为48.6%，但该“旧共识”仍主导舆论讨论，甚至影响教育政策方向。
- 词法前 10：1.s5-d0-t1-02-summary#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-summary#p3@T1 4.s5-d0-t1-02-memo#p2@T1 5.s5-d0-t1-02-memo#p1@T1 6.s5-d0-t1-02-report#p2@T1 7.s7-d3-t1-05-memo#p2@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s5-d0-t1-02-summary#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d0-t1-02-memo#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s5-d0-t1-02-analysis#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-summary#p3@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d0-t1-02-summary#p2@T1 5.s5-d0-t1-02-memo#p2@T1 6.s5-d1-t1-03-memo#p3@T1 7.s5-d0-t1-02-analysis#p1@T1 8.s5-d1-t1-03-note#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 105. `s5-d0-t1-02-q2`

- 问：当原始数据无法验证时，为何某些被转述的数据仍能在政策讨论中获得高度可信度？请从引用行为与制度惯性角度分析。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p2@T1；s5-d0-t1-02-memo#p3@T1；s5-d0-t1-02-summary#p3@T1
- 金标要点：即使原始数据无法验证，只要被多次引用并嵌入正式论述，便可能成为“事实”本身；由于原始报告的权威性已被广泛接受，修正数据并未引发足够关注，反而被归因于“样本偏差”或“测量误差”，反映出信息传播中的“确认偏误”现象。；尤其当新数据与既有叙事冲突时，往往面临更高的质疑门槛，导致认知滞后。；当一个数字被反复提及并嵌入主流话语，其真实性便逐渐让位于其象征意义。
- 词法前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d1-t1-03-memo#p1@T1 4.s5-d0-t1-02-memo#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d0-t1-02-report#p3@T1 7.s6-d3-t1-01-memo#p1@T1 8.s6-d3-t1-01-memo#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d0-t1-02-report#p3@T1 4.s6-d3-t1-01-memo#p3@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d0-t1-02-analysis#p3@T1 8.s7-d2-t1-04-data#p3@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s5-d1-t1-03-report#p3@T1
- 重排前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d1-t1-03-memo#p1@T1 4.s5-d0-t1-02-report#p3@T1 5.s5-d0-t1-02-analysis#p3@T1 6.s5-d1-t1-03-report#p3@T1 7.s7-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d2-t1-04-data#p3@T1 10.s6-d3-t1-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 106. `s5-d0-t1-02-q3`

- 问：通勤白皮书被政府简报引用时出现的“数据语义微调”，会怎样影响政策的科学性？请举例说明后果。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-report#p2@T1；s5-d0-t1-02-report#p3@T1
- 金标要点：这种语义微调虽无恶意，却导致政策推演基础出现偏差；值得注意的是，该报告在发布后不久即被多家政府简报引用，作为制定“弹性工作制试点”政策的重要依据；有地方部门将“平均通勤时间”解释为“最常见通勤时长”，而原始定义实为“中位数时间”；其解释权便可能被重新分配。
- 词法前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d3-t1-05-report#p1@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d3-t1-05-analysis#p2@T1 5.s5-d0-t1-02-report#p1@T1 6.s5-d3-t1-05-memo#p1@T1 7.s5-d1-t1-03-report#p1@T1 8.s5-d0-t1-02-report#p3@T1 9.s5-d3-t1-05-report#p2@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d0-t1-02-report#p3@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d3-t1-05-report#p2@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.s5-d0-t1-02-report#p1@T1 9.s7-d0-t1-02-brief#p2@T1 10.s5-d0-t1-02-analysis#p3@T1
- 重排前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-report#p3@T1 4.s5-d3-t1-05-analysis#p2@T1 5.s5-d0-t1-02-report#p1@T1 6.s5-d3-t1-05-report#p2@T1 7.s5-d0-t1-02-summary#p1@T1 8.s7-d0-t1-02-brief#p2@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s5-d1-t1-03-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 107. `s5-d0-t1-02-q4`

- 问：关于通勤白皮书数据被重新诠释一事，材料认为引用公开数据除追溯源头外还要关注什么？民生报告一案又暴露了什么盲点？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-report#p3@T1；s5-d0-t1-02-analysis#p3@T1
- 金标要点：对公开数据的引用不仅需要追溯源头，更需关注其在不同语境下的再诠释过程，防止“数字神话”在制度层面固化。；此事件暴露了内部数据整合机制中的结构性盲点：权威性不等于准确性，一致性也不代表全面性。
- 词法前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-analysis#p3@T1 4.s5-d0-t1-02-report#p2@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d0-t1-02-memo#p1@T1 7.s5-d3-t1-05-memo#p1@T1 8.s5-d3-t1-05-report#p1@T1 9.s7-d2-t1-04-memo#p3@T1 10.s5-d1-t1-03-report#p1@T1
- 混合前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s5-d0-t1-02-analysis#p3@T1 5.s5-d0-t1-02-memo#p3@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d0-t1-02-memo#p1@T1 8.s7-d2-t1-04-memo#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.p1-cac-o16#p1@T1
- 重排前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d0-t1-02-analysis#p3@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d2-t1-04-memo#p3@T1 7.s5-d0-t1-02-analysis#p2@T1 8.s5-d0-t1-02-memo#p3@T1 9.p1-cac-o16#p1@T1 10.s5-d0-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 108. `s5-d1-t1-03-q1`

- 问：在多个非官方渠道中流传的2018年消费者行为调查的核心结论，为何可能影响后续研究判断？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-memo#p1@T1；s5-d1-t1-03-memo#p2@T1；s5-d1-t1-03-memo#p3@T1
- 金标要点：尽管这一细节未在正式发布版本中说明，但在多份行业笔记中被反复提及，成为后续分析的重要参考依据；尽管原始数据已不再公开，但其核心结论被多次引用。；关于“线上购物渗透率”的统计值，在三份独立文档中分别记载为42%、46%和48%；这种不一致促使学者提出应谨慎对待二手引述，避免误读历史数据脉络
- 词法前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d0-t1-02-memo#p1@T1 3.s5-d3-t1-05-memo#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s5-d1-t1-03-summary#p1@T1 7.s5-d3-t1-05-report#p1@T1 8.s5-d1-t1-03-report#p2@T1 9.s1-d0-01-analysis#p2@T1 10.p1-colaw-governance-supervisor-js#p3@T1
- 混合前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d1-t1-03-report#p2@T1 3.s7-d2-t1-04-memo#p3@T1 4.s5-d1-t1-03-memo#p2@T1 5.s5-d0-t1-02-summary#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s5-d1-t1-03-summary#p1@T1 8.s6-d0-t1-01-channel#p1@T1 9.s5-d1-t1-03-summary#p3@T1 10.s7-d0-t1-02-brief#p2@T1
- 重排前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d0-t1-02-analysis#p2@T1 3.s5-d1-t1-03-summary#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d1-t1-03-report#p2@T1 6.s5-d1-t1-03-memo#p2@T1 7.s5-d1-t1-03-summary#p3@T1 8.s7-d0-t1-02-brief#p2@T1 9.s7-d2-t1-04-memo#p3@T1 10.s5-d0-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 109. `s5-d1-t1-03-q2`

- 问：为什么说2019年白皮书中关于手机更换周期的数据虽然被广泛引用，但仍存在可靠性风险？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-report#p1@T1；s5-d1-t1-03-report#p2@T1
- 金标要点：值得注意的是，该数据源自一项2018年的小型调研，样本量仅为850人，且主要集中在一线城市；该报告指出，用户平均更换手机的时间为2.7年，这一数字在后续三年内被多次复述，甚至成为政策制定者的参考基准。；由于缺乏更新的权威数据，许多研究直接沿用此数值，未加批判性评估，导致长期形成认知惯性。
- 词法前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d3-t1-05-report#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d3-t1-05-analysis#p2@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d0-t1-02-memo#p2@T1 9.s5-d1-t1-03-memo#p1@T1 10.s4-d2-t1-04-memo#p2@T1
- 混合前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d3-t1-05-analysis#p2@T1 3.s5-d3-t1-05-report#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s5-d3-t1-05-report#p2@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-claim#p3@T1 9.s5-d1-t1-03-note#p1@T1 10.s6-d3-t1-01-note#p3@T1
- 重排前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d3-t1-05-analysis#p2@T1 3.s5-d3-t1-05-report#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s5-d1-t1-03-memo#p1@T1 6.s5-d1-t1-03-note#p1@T1 7.s5-d0-t1-02-memo#p3@T1 8.s5-d3-t1-05-report#p2@T1 9.s7-d0-t1-02-claim#p3@T1 10.s6-d3-t1-01-note#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 110. `s5-d1-t1-03-q3`

- 问：那份记录2015年市场反馈的内部备忘录，其数据是怎样经非正式渠道被当作正式成果的？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-note#p1@T1；s5-d1-t1-03-note#p2@T1
- 金标要点：一份2017年的项目备忘录提到，某部门曾收集2015年市场反馈数据，用于支持战略规划；在2021年的审计审查中发现，其中一份内部幻灯片将原始数据中的“满意度得分”从3.4夸大至4.1；该数据集虽未正式对外公布，但通过邮件流转，被多个团队间接引用，形成了隐性的信息传播网络。；其中一份内部幻灯片将原始数据中的“满意度得分”从3.4夸大至4.1，理由是“符合预期目标”；此类微调虽未改变整体趋势，却在后续汇报中被当作真实成果展示，引发信任危机。
- 词法前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-note#p2@T1 3.s7-d0-t1-02-claim#p3@T1 4.s5-d1-t1-03-memo#p1@T1 5.s2-d3-01-memo#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s6-d0-t1-02-report#p2@T1 8.s7-d0-t1-02-brief#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s6-d0-t1-02-memo#p2@T1
- 混合前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-memo#p2@T1 8.s5-d3-t1-05-analysis#p3@T1 9.s2-d3-01-memo#p1@T1 10.s1-d1-t1-91-memo#p2@T1
- 重排前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s2-d3-01-memo#p1@T1 7.s5-d1-t1-03-memo#p2@T1 8.s5-d3-t1-05-analysis#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.s1-d1-t1-91-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 111. `s5-d1-t1-03-q4`

- 问：当多份来源对同一事件的描述存在数值差异时，应采取何种方法确保汇编叙述的可信度？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-summary#p2@T1；s5-d1-t1-03-summary#p3@T1
- 金标要点：经交叉验证，发现前者包含了预注册人数，后者仅统计现场出席者；最终研究团队决定采用“分层标注法”，对每条信息注明其来源类型与潜在偏见
- 词法前 10：1.s5-d1-t1-03-memo#p3@T1 2.s5-d0-t1-02-analysis#p3@T1 3.s7-d2-t1-04-brief#p3@T1 4.s7-d0-t1-02-brief#p3@T1 5.s6-d3-t1-01-note#p2@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d0-t1-02-claim#p2@T1 10.s5-d1-t1-03-summary#p3@T1
- 混合前 10：1.s5-d0-t1-02-analysis#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s5-d1-t1-03-memo#p3@T1 4.s7-d2-t1-04-data#p3@T1 5.s7-d0-t1-02-analysis#p3@T1 6.s6-d3-t1-01-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s7-d2-t1-04-claim#p3@T1 9.s5-d1-t1-03-summary#p3@T1 10.s6-d3-t1-01-memo#p2@T1
- 重排前 10：1.s5-d0-t1-02-analysis#p3@T1 2.s5-d1-t1-03-memo#p3@T1 3.s7-d2-t1-04-brief#p3@T1 4.s7-d2-t1-04-claim#p3@T1 5.s5-d1-t1-03-summary#p3@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s6-d3-t1-01-memo#p3@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 112. `s5-d2-t0-04-q1`

- 问：三份二手交易材料各自给出了哪些增长数字？它们是否引用了同一个数据点？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-memo#p1@T0；s5-d2-t0-04-analysis#p1@T0；s5-d2-t0-04-report#p2@T0；s5-d2-t0-04-memo#p3@T0
- 金标要点：全国二手交易市场在2019年至2020年间年均增长率达17.3%；二手商品成交额在当年第四季度环比增长26.5%；2021年“二手”相关话题在微博上的讨论量同比增长35%；线上二手平台用户活跃度较前一年提升约22%
- 词法前 10：1.s5-d2-t0-04-report#p3@T0 2.s7-d0-t0-01-qa#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s5-d2-t0-04-memo#p1@T0 5.p1-cac-o11#p4@T0 6.s4-d0-t0-01-memo#p1@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s7-d0-t0-01-memo#p1@T0 9.p1-cac-o11#p5@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s5-d2-t0-04-memo#p1@T0 2.s5-d2-t0-04-report#p3@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s1-d3-t0-91-memo#p1@T0 5.s5-d2-t0-04-analysis#p3@T0 6.s5-d1-t0-91-repost#p3@T0 7.s5-d2-t0-04-report#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s2-d0-03-memo#p2@T0 10.s5-d2-t0-04-report#p1@T0
- 重排前 10：1.s5-d2-t0-04-report#p3@T0 2.s5-d2-t0-04-memo#p1@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s1-d3-t0-91-memo#p1@T0 5.s5-d2-t0-04-analysis#p3@T0 6.s5-d2-t0-04-report#p2@T0 7.s5-d2-t0-04-analysis#p1@T0 8.s2-d0-03-memo#p2@T0 9.s5-d1-t0-91-repost#p3@T0 10.s5-d2-t0-04-report#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 113. `s5-d2-t0-04-q2`

- 问：在二手交易相关材料里，哪些文档提到了未公开的内部数据？这些内容为什么被当作参考？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-analysis#p1@T0；s5-d2-t0-04-analysis#p3@T0；s5-d2-t0-04-memo#p1@T0
- 金标要点：此数据未对外公布，但在跨部门会议纪要中被提及，并成为后续策略调整的依据之一。；该信息未进入正式文档体系，但在团队交流中频繁被引用，形成隐性共识。；尽管原始报告未公开，但其结论在若干非正式渠道中广泛流传。
- 词法前 10：1.s5-d2-t0-04-report#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-analysis#p3@T0 4.s5-d2-t0-04-memo#p1@T0 5.s5-d1-t0-91-repost#p1@T0 6.s7-d0-t0-01-arch#p2@T0 7.s5-d2-t0-04-report#p2@T0 8.s7-d1-t0-03-memo#p3@T0 9.s2-d2-t0-91-callnotes#p2@T0 10.s4-d0-t0-01-memo#p1@T0
- 混合前 10：1.s5-d2-t0-04-analysis#p2@T0 2.s5-d2-t0-04-report#p3@T0 3.s5-d2-t0-04-memo#p1@T0 4.s5-d2-t0-04-analysis#p3@T0 5.s5-d2-t0-04-report#p2@T0 6.s7-d1-t0-03-memo#p3@T0 7.s5-d2-t0-04-analysis#p1@T0 8.s4-d0-t0-01-memo#p1@T0 9.s5-d2-t0-04-report#p1@T0 10.p1-cac-o11#p4@T0
- 重排前 10：1.s5-d2-t0-04-analysis#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-report#p3@T0 4.s5-d2-t0-04-memo#p1@T0 5.s5-d2-t0-04-report#p2@T0 6.s5-d2-t0-04-analysis#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.p1-cac-o11#p4@T0 9.s7-d1-t0-03-memo#p3@T0 10.s5-d2-t0-04-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 114. `s5-d2-t0-04-q3`

- 问：三份文档如何处理未经证实或来源模糊的信息？请举例说明。
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-analysis#p3@T0；s5-d2-t0-04-memo#p1@T0；s5-d2-t0-04-memo#p3@T0；s5-d2-t0-04-report#p1@T0；s5-d2-t0-04-report#p2@T0
- 金标要点：尽管原始报告未公开，但其结论在若干非正式渠道中广泛流传。；这一趋势被部分媒体归因于疫情推动的居家消费习惯变化，但缺乏直接数据支持。；该报告虽无官方背书，但被多家自媒体转载并作为论据使用。；尽管该数据来源未提供完整统计口径，仍被用于佐证市场热度。；该信息未进入正式文档体系，但在团队交流中频繁被引用，形成隐性共识。
- 词法前 10：1.s7-d0-t0-01-qa#p1@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s7-d0-t0-01-qa#p3@T0 4.s5-d2-t0-04-analysis#p3@T0 5.s1-d3-01-report#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s7-d0-t0-01-report#p1@T0 9.s7-d0-t0-01-arch#p3@T0 10.s3-d1-01-memo#p2@T0
- 混合前 10：1.s7-d0-t0-01-qa#p3@T0 2.s7-d1-t0-03-fact#p3@T0 3.s4-d3-t0-05-summary#p3@T0 4.s7-d0-t0-01-report#p1@T0 5.s7-d0-t0-01-internal#p3@T0 6.s7-d0-t0-01-arch#p3@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s5-d2-t0-04-analysis#p3@T0 9.s7-d0-t0-01-qa#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-qa#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-analysis#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d1-t0-03-fact#p3@T0 6.s4-d3-t0-05-summary#p3@T0 7.s7-d0-t0-01-report#p1@T0 8.s7-d0-t0-01-internal#p3@T0 9.s7-d0-t0-01-arch#p3@T0 10.s7-d1-t0-03-memo#p3@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 115. `s5-d3-t1-05-q1`

- 问：在2022年与2023年间，某城市公共交通使用率的变化情况如何？有哪些因素导致了信息滞后？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-memo#p1@T1；s5-d3-t1-05-memo#p2@T1
- 金标要点：在2022年的一项研究中，某机构对城市居民的通勤模式进行了调查，结果显示约43%的人每日乘坐公共交通工具；2023年另一项独立调查显示，使用公共交通的比例上升至51%，但该结果未被广泛传播；部分媒体和报告仍沿用旧数据，导致公众对实际变化产生误判，形成认知偏差。
- 词法前 10：1.s5-d3-t1-05-memo#p2@T1 2.s5-d3-t1-05-memo#p3@T1 3.s5-d3-t1-05-memo#p1@T1 4.p1-cac-o16#p11@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d0-t1-02-report#p1@T1 9.s5-d0-t1-02-memo#p3@T1 10.s5-d1-t1-03-report#p2@T1
- 混合前 10：1.s5-d3-t1-05-memo#p2@T1 2.s5-d3-t1-05-memo#p1@T1 3.s5-d3-t1-05-memo#p3@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d3-t1-05-report#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s2-d0-03-memo#p2@T1 8.s5-d0-t1-02-analysis#p1@T1 9.s5-d0-t1-02-memo#p1@T1 10.s5-d1-t1-03-report#p2@T1
- 重排前 10：1.s5-d3-t1-05-memo#p3@T1 2.s5-d3-t1-05-memo#p2@T1 3.s5-d3-t1-05-memo#p1@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d0-t1-02-analysis#p1@T1 6.s5-d0-t1-02-memo#p1@T1 7.s5-d1-t1-03-report#p2@T1 8.s5-d3-t1-05-report#p2@T1 9.s5-d0-t1-02-summary#p1@T1 10.s2-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 116. `s5-d3-t1-05-q2`

- 问：以公交使用率、制造业占比和员工满意度为例，为何新数据出现后旧统计仍被政策文件广泛引用？反映了什么问题？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p2@T1；s5-d3-t1-05-report#p2@T1；s5-d3-t1-05-memo#p2@T1
- 金标要点：事实固化；数据惯性；但该结果未被广泛传播；部分媒体和报告仍沿用旧数据，导致公众对实际变化产生误判，形成认知偏差。；但多数地方政府报告仍沿用旧值，造成政策目标与现实脱节。；管理层对此类引用持默许态度，认为其具有稳定预期的作用。
- 词法前 10：1.s5-d3-t1-05-report#p1@T1 2.s1-d0-02-report#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s1-d0-01-memo#p2@T1 5.s5-d1-t1-03-report#p1@T1 6.s2-d0-04-memo#p1@T1 7.s5-d3-t1-05-memo#p1@T1 8.s6-d3-t1-01-memo#p2@T1 9.p1-cac-o11#p4@T1 10.s5-d3-t1-05-analysis#p1@T1
- 混合前 10：1.s5-d3-t1-05-memo#p1@T1 2.s5-d3-t1-05-analysis#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s1-d0-02-report#p1@T1 5.s5-d0-t1-02-analysis#p1@T1 6.s5-d3-t1-05-report#p2@T1 7.s5-d3-t1-05-memo#p2@T1 8.s6-d3-t1-91-changelog#p1@T1 9.s5-d0-t1-02-memo#p1@T1 10.s5-d3-t1-05-memo#p3@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d3-t1-05-memo#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s5-d0-t1-02-analysis#p1@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s1-d0-02-report#p1@T1 7.s5-d3-t1-05-report#p2@T1 8.s5-d3-t1-05-memo#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s6-d3-t1-91-changelog#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 117. `s5-d3-t1-05-q3`

- 问：离职面谈与匿名反馈交叉分析后，发现了哪项没写进正式报告的员工侧趋势？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p3@T1
- 金标要点：通过对离职面谈记录与匿名反馈系统的交叉分析，可识别出员工对远程办公支持度的显著提升；可识别出员工对远程办公支持度的显著提升，这一趋势虽未体现在正式报告中，但已被高层视为关键管理改进方向。
- 词法前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s7-d2-t1-04-claim#p3@T1 3.s5-d1-t1-03-memo#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s4-d2-t1-04-report#p1@T1 6.s5-d3-t1-05-memo#p3@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d1-t1-03-memo#p1@T1 9.s4-d0-t1-02-plan#p1@T1 10.s7-d0-t1-02-memo#p1@T1
- 混合前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s5-d1-t1-03-memo#p2@T1 3.s5-d1-t1-03-note#p1@T1 4.s5-d1-t1-03-memo#p1@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d0-t1-02-memo#p1@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s7-d2-t1-04-claim#p3@T1 3.s5-d1-t1-03-memo#p2@T1 4.s5-d1-t1-03-note#p1@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d0-t1-02-memo#p1@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 118. `s6-d0-t1-01-q1`

- 问：顾问备忘中复验窗口的最新调整是什么？旧窗口如何处理？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-memo#p1@T1
- 金标要点：顾问备忘中关于复验窗口的调整已正式生效，原定两周的复验周期现已延长至三周；旧版中的两周窗口仅保留用于历史对照参考，不再作为现行标准执行
- 词法前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d1-t1-91-patch#p1@T1 4.s6-d3-t1-01-note#p1@T1 5.s1-d1-t1-91-memo#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s1-d0-03-memo#p1@T1 8.s6-d3-t1-01-memo#p1@T1 9.s6-d3-t1-02-memo#p2@T1 10.s6-d0-t1-91-change#p1@T1
- 混合前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d3-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p1@T1 5.s6-d3-t1-01-note#p2@T1 6.s6-d3-t1-02-report#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s6-d3-t1-01-memo#p1@T1 9.s1-d1-t1-91-memo#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 重排前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d3-t1-01-note#p1@T1 4.s6-d3-t1-02-memo#p2@T1 5.s6-d3-t1-02-report#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s6-d3-t1-01-memo#p1@T1 8.s1-d1-t1-91-memo#p2@T1 9.s6-d3-t1-01-note#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 119. `s6-d0-t1-01-q2`

- 问：渠道纪要中关于口头折扣的信息发生了什么位置变动？原因是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-channel#p1@T1
- 金标要点：渠道纪要中涉及口头折扣的条款已从主文迁移至附录，此举旨在分离操作细节与核心政策声明，避免信息冗余影响关键判断的传达效率。
- 词法前 10：1.s6-d0-t1-01-channel#p1@T1 2.s6-d0-t1-01-memo#p2@T1 3.s6-d0-t1-02-internal#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-report#p2@T1 6.s2-d3-t1-91-minutes#p1@T1 7.s5-d1-t1-03-memo#p1@T1 8.s5-d0-t1-02-memo#p1@T1 9.s2-d0-03-memo#p1@T1 10.s6-d0-t1-02-memo#p2@T1
- 混合前 10：1.s6-d0-t1-01-channel#p1@T1 2.s6-d0-t1-01-memo#p2@T1 3.s6-d0-t1-02-internal#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-report#p2@T1 6.s5-d1-t1-03-memo#p1@T1 7.s6-d0-t1-02-memo#p2@T1 8.s2-d0-03-memo#p1@T1 9.s6-d3-t1-03-memo#p3@T1 10.s2-d0-01-report#p3@T1
- 重排前 10：1.s6-d0-t1-01-channel#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s6-d0-t1-01-memo#p2@T1 4.s6-d0-t1-02-internal#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s6-d3-t1-03-memo#p2@T1 7.s6-d3-t1-03-report#p2@T1 8.s2-d0-03-memo#p1@T1 9.s6-d3-t1-03-memo#p3@T1 10.s2-d0-01-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 120. `s6-d0-t1-01-q3`

- 问：战略判断的结论段目前处于什么状态？为何不再标记为已签发？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-memo#p3@T1
- 金标要点：战略判断部分的结论段落已更新为“待复验”状态，不再以“已签发”形式呈现，反映当前评估仍需进一步验证，确保风险控制闭环完整。
- 词法前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s6-d0-t1-03-internal#p1@T1 5.s6-d3-t1-02-summary#p3@T1 6.s1-d0-05-warn#p1@T1 7.s2-d3-01-memo#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s2-d3-01-interview#p1@T1 10.s5-d1-t1-03-memo#p1@T1
- 混合前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s1-d0-03-memo#p1@T1 5.s1-d0-05-memo#p1@T1 6.s1-d0-05-warn#p1@T1 7.s2-d3-01-interview#p1@T1 8.s6-d0-t1-03-internal#p1@T1 9.s2-d0-02-interview#p1@T1 10.s7-d0-t1-02-claim#p2@T1
- 重排前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s1-d0-05-warn#p1@T1 5.s6-d0-t1-03-internal#p1@T1 6.s1-d0-03-memo#p1@T1 7.s1-d0-05-memo#p1@T1 8.s2-d3-01-interview#p1@T1 9.s7-d0-t1-02-claim#p2@T1 10.s2-d0-02-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 121. `s6-d0-t1-02-q1`

- 问：供应商交付周期从四周改为六周后，这一变更分别被同步到了哪些工具或排期里？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-internal#p1@T1；s6-d0-t1-02-memo#p1@T1；s6-d0-t1-02-report#p1@T1
- 金标要点：系统上线计划也已重新排期；该变更已录入项目管理工具，影响范围覆盖所有依赖模块。；该调整已在本周内部通报，并同步更新至项目排期表。
- 词法前 10：1.s6-d0-t1-02-internal#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s1-d0-02-report#p2@T1 5.s6-d0-t1-91-change#p1@T1 6.s6-d3-t1-02-summary#p2@T1 7.s6-d1-c2-memo#p3@T1 8.s6-d0-t1-03-internal#p1@T1 9.s6-d0-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p2@T1
- 混合前 10：1.s6-d0-t1-02-report#p1@T1 2.s6-d0-t1-02-internal#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d3-t1-02-summary#p2@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-91-change#p1@T1 7.s2-d1-01-memo#p1@T1 8.s6-d3-t1-02-report#p2@T1 9.s6-d3-t1-02-memo#p2@T1 10.s6-d0-t1-01-patch#p2@T1
- 重排前 10：1.s6-d0-t1-02-internal#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d3-t1-02-summary#p2@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-91-change#p1@T1 7.s6-d0-t1-01-patch#p2@T1 8.s2-d1-01-memo#p1@T1 9.s6-d3-t1-02-report#p2@T1 10.s6-d3-t1-02-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 122. `s6-d0-t1-02-q2`

- 问：渠道纪要中关于对手入门档产品的最新说法是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-internal#p2@T1；s6-d0-t1-02-memo#p2@T1；s6-d0-t1-02-report#p2@T1
- 金标要点：渠道纪要中新增信息：对手入门档产品已停止销售，当前无直接竞争压力，建议加快市场推广节奏；渠道方面，新增一条对手产品线的动态信息：其入门档型号已于上季度末正式停售，目前市场中无同级竞品可替代；渠道反馈补充指出，此前误传的对手入门档仍在售信息已被更正，实际该产品线已全面下架
- 词法前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d3-t1-02-memo#p1@T1 6.s6-d0-t1-01-channel#p1@T1 7.s2-d3-t1-91-minutes#p1@T1 8.s2-d0-04-memo#p2@T1 9.s6-d0-t1-02-memo#p1@T1 10.s6-d0-t1-02-report#p1@T1
- 混合前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s6-d3-t1-02-memo#p1@T1 7.s2-d2-01-memo#p1@T1 8.s2-d0-01-memo#p1@T1 9.s6-d3-t1-02-summary#p1@T1 10.s6-d0-t1-02-memo#p1@T1
- 重排前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s2-d2-01-memo#p1@T1 7.s6-d3-t1-02-memo#p1@T1 8.s2-d0-01-memo#p1@T1 9.s6-d0-t1-02-memo#p1@T1 10.s6-d3-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 123. `s6-d0-t1-02-q3`

- 问：项目负责人从甲组调到乙组这件事，会议记录里是怎么写的？乙组接手后负责什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-memo#p3@T1
- 金标要点：原由甲组负责的项目推进工作现已移交至乙组；乙组将全面接管后续协调与执行任务
- 词法前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d0-t1-03-internal#p1@T1 6.s6-d0-t1-91-sop#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-t1-91-interview#p2@T1 9.s4-d0-t1-02-guide#p2@T1 10.s6-d0-t1-03-report#p1@T1
- 混合前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s6-d3-t1-02-summary#p3@T1 5.s4-d2-t1-04-internal#p3@T1 6.s6-d2-g3-memo#p3@T1 7.s6-d0-t1-03-internal#p1@T1 8.s2-d0-t1-91-memo#p1@T1 9.s2-d0-t1-91-interview#p2@T1 10.p1-colaw-capital-call#p1@T1
- 重排前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s6-d0-t1-03-internal#p1@T1 5.s6-d2-g3-memo#p3@T1 6.s2-d0-t1-91-interview#p2@T1 7.s6-d3-t1-02-summary#p3@T1 8.s4-d2-t1-04-internal#p3@T1 9.s2-d0-t1-91-memo#p1@T1 10.p1-colaw-capital-call#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 124. `s6-d0-t1-03-q1`

- 问：在最新的成本测算中，外包单价是否仍被使用？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-memo#p1@T1；s6-d0-t1-03-internal#p1@T1；s6-d0-t1-03-report#p1@T1
- 金标要点：内部测算把外包单价从上一版模型里撤下，以避免误导后续成本评估；内部测算把外包单价从上一版模型里撤下，该字段已被标记为过时，后续分析将基于更新后的参数集；内部测算把外包单价从上一版模型里撤下，确保当前评估不依赖已废弃的数据字段，防止误用历史偏差影响决策；该调整已同步至最新数据管道，确保分析基准的一致性。
- 词法前 10：1.s6-d0-t1-03-memo#p1@T1 2.s6-d0-t1-03-internal#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d0-t1-03-report#p1@T1 5.s4-d2-t1-91-model-v3#p1@T1 6.s5-d1-t1-03-report#p1@T1 7.s7-d0-t1-02-update#p2@T1 8.s4-d0-t1-02-memo#p1@T1 9.s2-d2-01-memo#p1@T1 10.s3-d3-01-report#p3@T1
- 混合前 10：1.s6-d0-t1-03-memo#p1@T1 2.s6-d0-t1-03-internal#p1@T1 3.s6-d0-t1-03-report#p1@T1 4.s4-d2-t1-91-model-v3#p1@T1 5.s3-d3-01-report#p3@T1 6.s4-d2-t1-04-report#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s2-d0-02-interview#p3@T1 9.s4-d0-t1-02-memo#p1@T1 10.s3-d3-01-report#p2@T1
- 重排前 10：1.s6-d0-t1-03-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s6-d0-t1-03-internal#p1@T1 4.s4-d2-t1-04-report#p1@T1 5.s2-d0-02-interview#p3@T1 6.s6-d0-t1-03-report#p1@T1 7.s4-d2-t1-91-model-v3#p1@T1 8.s3-d3-01-report#p3@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s3-d3-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 125. `s6-d0-t1-03-q2`

- 问：成本模型版本号发生了什么变化？旧版本如何处理？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-memo#p2@T1；s6-d0-t1-03-internal#p2@T1；s6-d0-t1-03-report#p2@T1
- 金标要点：成本模型版本号从甲版改成乙版，旧版只作归档处理，不再参与任何实时计算流程；成本模型版本号从甲版改成乙版，旧版仅保留于历史存档库，不参与任何实时或批量计算任务；成本模型版本号从甲版改成乙版，旧版只作归档，相关文档已标注“仅历史参考”标签，禁止在新项目中启用
- 词法前 10：1.s6-d0-t1-03-memo#p2@T1 2.s6-d0-t1-03-internal#p2@T1 3.s6-d0-t1-03-report#p2@T1 4.s1-d0-03-memo#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d2-t1-04-report#p1@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.p1-cac-o11#p10@T1
- 混合前 10：1.s6-d0-t1-03-memo#p2@T1 2.s6-d0-t1-03-internal#p2@T1 3.s6-d0-t1-03-report#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-memo#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d0-t1-02-plan#p1@T1 8.s4-d2-t1-04-memo#p1@T1 9.s6-d3-t1-03-report#p1@T1 10.s4-d2-t1-04-memo#p2@T1
- 重排前 10：1.s6-d0-t1-03-memo#p2@T1 2.s6-d0-t1-03-internal#p2@T1 3.s6-d0-t1-03-report#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-memo#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d0-t1-02-plan#p1@T1 8.s4-d2-t1-04-memo#p1@T1 9.s6-d3-t1-03-report#p1@T1 10.s4-d2-t1-04-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 126. `s6-d0-t1-03-q3`

- 问：报价单里的打包项改成分行列出后，三份材料各自说这样做是为了什么？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-internal#p3@T1；s6-d0-t1-03-memo#p3@T1；s6-d0-t1-03-report#p3@T1
- 金标要点：符合最新合规披露要求；提升明细可读性并支持独立定价校验；为未来自动化比价提供结构化基础
- 词法前 10：1.s4-d0-t1-91-deck#p3@T1 2.s2-d0-t1-91-memo#p1@T1 3.s6-d0-t1-91-sop#p2@T1 4.s6-d3-t1-01-report#p2@T1 5.s6-d3-t1-91-changelog#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s1-d1-t1-91-memo#p2@T1 8.s2-d0-t1-91-interview#p2@T1 9.s7-d3-t1-05-synthetic#p2@T1 10.s4-d2-t1-91-model-v3#p2@T1
- 混合前 10：1.s6-d0-t1-03-internal#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s6-d0-t1-03-report#p3@T1 4.s3-d2-t1-91-contract#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s6-d0-t1-03-internal#p3@T1 7.s6-d0-t1-03-memo#p3@T1 8.s6-d3-t1-01-report#p2@T1 9.s6-d0-t1-03-report#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 重排前 10：1.s6-d0-t1-03-internal#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s3-d2-t1-91-contract#p1@T1 4.s6-d0-t1-03-report#p3@T1 5.s6-d3-t1-01-report#p2@T1 6.s6-d0-t1-03-report#p1@T1 7.s6-d0-t1-03-memo#p1@T1 8.s3-d2-t1-91-contract#p3@T1 9.s6-d0-t1-03-internal#p3@T1 10.s6-d0-t1-03-memo#p3@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 127. `s6-d1-c1-q1`

- 问：出境评估结论现在的有效期是多长？满足什么条件可以续期，续期能延多久？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p9@T1；s6-d1-c1-memo#p1@T1；s6-d1-c1-memo#p2@T1
- 金标要点：通过数据出境安全评估的结果有效期为3年，自评估结果出具之日起计算。；有效期届满，需要继续开展数据出境活动且未发生需要重新申报数据出境安全评估情形的，数据处理者可以在有效期届满前60个工作日内通过所在地省级网信部门向国家网信部门提出延长评估结果有效期申请。；经国家网信部门批准，可以延长评估结果有效期3年。
- 词法前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.p1-cac-o11#p12@T1 4.s6-d1-c3-memo#p2@T1 5.s6-d1-c1-memo#p1@T1 6.p1-cac-o11#p14@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d1-c1-memo#p2@T1 9.p1-cac-o16#p6@T1 10.s6-d1-c1-memo#p3@T1
- 混合前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.s6-d1-c1-memo#p1@T1 4.s6-d1-c1-memo#p2@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o11#p14@T1 7.p1-cac-o11#p12@T1 8.s6-d1-c1-memo#p3@T1 9.p1-cac-o11#p11@T1 10.p1-cac-o11#p15@T1
- 重排前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.s6-d1-c1-memo#p1@T1 4.p1-cac-o11#p14@T1 5.p1-cac-o11#p12@T1 6.p1-cac-o11#p11@T1 7.s6-d1-c1-memo#p2@T1 8.s6-d1-c3-memo#p2@T1 9.s6-d1-c1-memo#p3@T1 10.p1-cac-o11#p15@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 128. `s6-d1-c1-q2-new`

- 问：出境评估结论原先管两年，现在能管几年？到期前多久可以申请续期？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p13@T1；p1-cac-o16#p9@T1
- 金标要点：通过数据出境安全评估的结果有效期为2年；通过数据出境安全评估的结果有效期为3年；可以在有效期届满前60个工作日内通过所在地省级网信部门向国家网信部门提出延长评估结果有效期申请
- 词法前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.s6-d1-c1-memo#p3@T1 4.s5-d2-t1-91-digest#p1@T1 5.s6-d1-c1-memo#p2@T1 6.p1-cac-o20#p6@T1 7.s1-d1-t1-91-memo#p1@T1 8.p1-cac-o20#p4@T1 9.p1-cac-o16#p6@T1 10.s6-d3-t1-02-memo#p3@T1
- 混合前 10：1.p1-cac-o16#p9@T1 2.s6-d1-c1-memo#p2@T1 3.s6-d1-c1-memo#p3@T1 4.p1-cac-o11#p12@T1 5.p1-cac-o11#p11@T1 6.p1-cac-o11#p15@T1 7.p1-cac-o13#p8@T1 8.p1-cac-o11#p17@T1 9.p1-cac-o11#p13@T1 10.s6-d3-t1-02-memo#p3@T1
- 重排前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p12@T1 3.s6-d1-c1-memo#p2@T1 4.s6-d1-c1-memo#p3@T1 5.p1-cac-o11#p11@T1 6.p1-cac-o11#p15@T1 7.p1-cac-o13#p8@T1 8.p1-cac-o11#p17@T1 9.p1-cac-o11#p13@T1 10.s6-d3-t1-02-memo#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 129. `s6-d1-c2-q1`

- 问：不属于关基的企业，出境个人信息到多少人才需要报评估？这条线和以前比有什么不同？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p7@T1；p1-cac-o11#p2@T1；s6-d1-c2-memo#p1@T1；s6-d1-c2-memo#p2@T1；s6-d1-c2-memo#p3@T1
- 金标要点：关键信息基础设施运营者以外的数据处理者向境外提供重要数据，或者自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）或者1万人以上敏感个人信息；自上年1月1日起累计向境外提供10万人个人信息或者1万人敏感个人信息的数据处理者向境外提供个人信息；此次更新把一般个人信息的申报线从10万人提高到100万人，统计起点由上年改为当年，实际放宽了一般运营者的申报义务；敏感个人信息仍以1万人为线
- 词法前 10：1.p1-cac-o16#p6@T1 2.p1-cac-o16#p2@T1 3.p1-cac-o16#p3@T1 4.p1-cac-o13#p3@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o20#p3@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o20#p5@T1 9.p1-cac-o16#p8@T1 10.p1-cac-o11#p13@T1
- 混合前 10：1.p1-cac-o20#p3@T1 2.s6-d1-c2-memo#p1@T1 3.p1-cac-o16#p2@T1 4.p1-cac-o11#p2@T1 5.p1-cac-o16#p3@T1 6.p1-cac-o16#p8@T1 7.p1-cac-o13#p3@T1 8.p1-cac-o16#p7@T1 9.s6-d1-c3-memo#p2@T1 10.s6-d1-c3-memo#p3@T1
- 重排前 10：1.p1-cac-o16#p2@T1 2.p1-cac-o11#p2@T1 3.p1-cac-o16#p7@T1 4.p1-cac-o20#p3@T1 5.s6-d1-c2-memo#p1@T1 6.p1-cac-o16#p3@T1 7.p1-cac-o16#p8@T1 8.p1-cac-o13#p3@T1 9.s6-d1-c3-memo#p2@T1 10.s6-d1-c3-memo#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 130. `s6-d1-c3-q1`

- 问：标准合同的适用区间在新规下有何变化？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d1-c3-memo#p1@T1；p1-cac-o13#p2@T1；p1-cac-o16#p8@T1
- 金标要点：累计向境外提供10万人以上、不满100万人个人信息；不满1万人敏感个人信息；自上年1月1日起累计向境外提供个人信息不满10万人的
- 词法前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p1@T1 3.s6-d1-c3-memo#p3@T1 4.p1-cac-o13#p6@T1 5.s3-d2-t1-91-contract#p1@T1 6.s5-d2-t1-91-digest#p3@T1 7.p1-cac-o16#p11@T1 8.p1-cac-o13#p5@T1 9.s6-d1-c3-memo#p2@T1 10.p1-cac-o13#p7@T1
- 混合前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p6@T1 3.p1-cac-o13#p5@T1 4.p1-cac-o13#p7@T1 5.p1-cac-o16#p11@T1 6.p1-cac-o13#p1@T1 7.s6-d1-c4-memo#p1@T1 8.s6-d2-g1-memo#p2@T1 9.s3-d2-t1-91-contract#p1@T1 10.s2-d0-t1-91-memo#p1@T1
- 重排前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p6@T1 3.p1-cac-o13#p7@T1 4.p1-cac-o16#p11@T1 5.p1-cac-o13#p1@T1 6.s6-d1-c4-memo#p1@T1 7.s6-d2-g1-memo#p2@T1 8.s3-d2-t1-91-contract#p1@T1 9.p1-cac-o13#p5@T1 10.s2-d0-t1-91-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 131. `s6-d1-c4-q1`

- 问：令16新增的个人信息出境豁免，哪些主体能享受？要满足什么条件？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p4@T1；p1-cac-o16#p5@T1；s6-d1-c4-memo#p1@T1
- 金标要点：为订立、履行个人作为一方当事人的合同，如跨境购物、跨境寄递、跨境汇款、跨境支付、跨境开户、机票酒店预订、签证办理、考试服务等，确需向境外提供个人信息的；按照依法制定的劳动规章制度和依法签订的集体合同实施跨境人力资源管理，确需向境外提供员工个人信息的；紧急情况下为保护自然人的生命健康和财产安全，确需向境外提供个人信息的；关键信息基础设施运营者以外的数据处理者自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息）的。
- 词法前 10：1.s6-d1-c4-memo#p1@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p11@T1 4.p1-cac-o16#p4@T1 5.s6-d1-c1-memo#p1@T1 6.s6-d1-c3-memo#p1@T1 7.s6-d1-c2-memo#p3@T1 8.p1-cac-o20#p5@T1 9.p1-cac-o16#p3@T1 10.p1-cac-o20#p6@T1
- 混合前 10：1.s6-d1-c4-memo#p1@T1 2.p1-cac-o20#p6@T1 3.s6-d1-c3-memo#p2@T1 4.p1-cac-o16#p4@T1 5.p1-cac-o20#p5@T1 6.p1-cac-o16#p11@T1 7.p1-cac-o20#p8@T1 8.p1-cac-o13#p4@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o20#p4@T1
- 重排前 10：1.s6-d1-c4-memo#p1@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p4@T1 4.p1-cac-o16#p11@T1 5.p1-cac-o20#p6@T1 6.p1-cac-o20#p5@T1 7.p1-cac-o20#p8@T1 8.p1-cac-o13#p4@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o20#p4@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 132. `s6-d2-g1-q1`

- 问：根据2023年公司法，有限责任公司股东认缴出资的最长期限是什么？此前法律有何不同？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d2-g1-memo#p1@T1；p1-colaw-capital#p1@T1
- 金标要点：2018法第二十六条无此期限；全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足。
- 词法前 10：1.s6-d2-g1-memo#p1@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-liquidation#p4@T1 6.s6-d2-g2-memo#p2@T1 7.p1-colaw-capital#p4@T1 8.p1-colaw-capital-transition#p1@T1 9.s6-d2-g2-memo#p1@T1 10.p1-colaw-capital-call#p1@T1
- 混合前 10：1.s6-d2-g1-memo#p1@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-transition#p1@T1 6.p1-colaw-capital-call#p1@T1 7.s6-d2-g1-memo#p2@T1 8.s6-d2-g2-memo#p2@T1 9.s6-d2-g2-memo#p1@T1 10.s6-d2-g3-memo#p1@T1
- 重排前 10：1.p1-colaw-capital#p1@T1 2.s6-d2-g1-memo#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g2-memo#p2@T1 7.s6-d2-g2-memo#p1@T1 8.p1-colaw-capital-call#p1@T1 9.s6-d2-g1-memo#p2@T1 10.s6-d2-g3-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 133. `s6-d2-g2-q1`

- 问：新公司法（2023修订）的施行日期是什么？其第二百六十六条对出资期限有何要求？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d2-g2-memo#p1@T1；p1-colaw-capital-transition#p1@T1
- 金标要点：本法自2024年7月1日起施行；第二百六十六条要求出资期限超出法定上限的存量公司逐步调整到位；本法施行前已登记设立的公司，出资期限超过本法规定的期限的，除法律、行政法规或者国务院另有规定外，应当逐步调整至本法规定的期限以内
- 词法前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g1-memo#p2@T1 6.p1-cac-o16#p11@T1 7.s6-d2-g2-memo#p3@T1 8.p1-colaw-capital#p4@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital-call#p5@T1
- 混合前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g1-memo#p2@T1 6.s6-d2-g2-memo#p3@T1 7.p1-colaw-capital-call#p4@T1 8.p1-cac-o13#p8@T1 9.p1-colaw-capital-call#p5@T1 10.p1-colaw-capital#p3@T1
- 重排前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.s6-d2-g2-memo#p2@T1 6.p1-colaw-capital-call#p5@T1 7.s6-d2-g1-memo#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital#p3@T1 10.p1-cac-o13#p8@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 134. `s6-d2-g3-q1`

- 问：根据2023年最新法规，未按期出资的责任主体和责任形式发生了哪些变化？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p1@T1；p1-colaw-capital-call#p2@T1；p1-colaw-capital-call#p5@T1；p1-colaw-capital-transition#p2@T1；s6-d2-g3-memo#p1@T1
- 金标要点：由受让人承担缴纳该出资的义务；2018法向已足额出资股东承担违约责任；2023法改为对公司损失承担赔偿责任，并新增董事会核查催缴、宽限期不少于六十日后失权、加速到期、未届期转让由受让人缴纳。；股东未按期足额缴纳出资的，除应当向公司足额缴纳外，还应当对给公司造成的损失承担赔偿责任。；未及时履行前款规定的义务，给公司造成损失的，负有责任的董事应当承担赔偿责任。；宽限期自公司发出催缴书之日起，不得少于六十日。
- 词法前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.s5-d3-t1-05-memo#p2@T1 6.s6-d2-g3-memo#p2@T1 7.s6-d1-c1-memo#p2@T1 8.s6-d2-g3-memo#p3@T1 9.s6-d1-c1-memo#p1@T1 10.p1-cac-o11#p10@T1
- 混合前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.s6-d2-g3-memo#p2@T1 4.p1-colaw-capital-call#p5@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g3-memo#p3@T1 7.p1-colaw-capital-transition#p2@T1 8.p1-colaw-capital-call#p2@T1 9.s6-d1-c1-memo#p1@T1 10.s6-d2-g1-memo#p2@T1
- 重排前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.s6-d2-g3-memo#p2@T1 6.p1-colaw-capital-transition#p1@T1 7.s6-d2-g3-memo#p3@T1 8.s6-d1-c1-memo#p1@T1 9.s6-d2-g1-memo#p2@T1 10.p1-colaw-capital-call#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 135. `s6-d3-t1-01-q1`

- 问：在最新版本中，二手转述如何处理旧报价？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p1@T1；s6-d3-t1-01-note#p1@T1；s6-d3-t1-01-report#p1@T1
- 金标要点：二手转述把旧报价标成已过期，不再当现行口径
- 词法前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s6-d3-t1-01-report#p1@T1 4.s5-d1-t1-03-report#p3@T1 5.s6-d3-t1-02-report#p1@T1 6.s6-d0-t1-02-report#p1@T1 7.s2-d2-01-memo#p1@T1 8.s6-d0-t1-03-internal#p3@T1 9.s6-d3-t1-03-memo#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s6-d3-t1-01-report#p1@T1 4.s6-d0-t1-91-change#p1@T1 5.s5-d0-t1-02-memo#p3@T1 6.s5-d1-t1-03-report#p3@T1 7.s5-d0-t1-02-summary#p1@T1 8.s6-d3-t1-03-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-03-memo#p3@T1
- 重排前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s5-d1-t1-03-report#p3@T1 4.s6-d3-t1-01-report#p1@T1 5.s5-d0-t1-02-memo#p3@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d3-t1-03-memo#p1@T1 8.s6-d0-t1-91-change#p1@T1 9.s5-d0-t1-02-summary#p1@T1 10.s6-d0-t1-03-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 136. `s6-d3-t1-01-q2`

- 问：汇编备注中的信息来源发生了什么变化？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p2@T1；s6-d3-t1-01-note#p2@T1；s6-d3-t1-01-report#p2@T1
- 金标要点：汇编备注把出处从访谈改成备忘附件，以反映信息来源的真实文件形式，增强可追溯性；汇编备注把出处从访谈改成备忘附件，体现对原始资料来源的规范标注；汇编备注把出处从访谈改成备忘附件，使原始材料定位更准确，便于后续查证
- 词法前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s6-d3-t1-01-report#p2@T1 4.s1-d0-03-memo#p2@T1 5.s5-d2-t1-91-digest#p3@T1 6.s5-d0-t1-02-analysis#p3@T1 7.p1-cac-o11#p10@T1 8.s7-d2-t1-04-claim#p3@T1 9.s5-d1-t1-03-summary#p3@T1 10.s5-d2-t1-91-digest#p1@T1
- 混合前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s6-d3-t1-01-report#p2@T1 4.s5-d2-t1-91-digest#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s5-d0-t1-02-summary#p3@T1 7.s5-d0-t1-02-summary#p1@T1 8.s5-d1-t1-03-summary#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s5-d1-t1-03-summary#p3@T1
- 重排前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s5-d1-t1-03-summary#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.s5-d2-t1-91-digest#p3@T1 9.s6-d3-t1-01-report#p2@T1 10.s5-d2-t1-91-digest#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 137. `s6-d3-t1-01-q3`

- 问：转述稿中关于份额的说法有何变动？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p3@T1；s6-d3-t1-01-note#p3@T1；s6-d3-t1-01-report#p3@T1
- 金标要点：转述稿删掉了未核实的份额说法，确保内容仅包含经确认的数据，提升整体可信度；转述稿删掉了未核实的份额说法，符合内容审核标准，强化信息可靠性；转述稿删掉了未核实的份额说法，保证输出内容基于可验证事实，减少推测成分
- 词法前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-report#p3@T1 3.s6-d3-t1-01-memo#p3@T1 4.s6-d0-t1-01-memo#p1@T1 5.s5-d0-t1-02-memo#p1@T1 6.s1-d0-01-memo#p2@T1 7.p1-cac-o20#p8@T1 8.p1-colaw-capital#p3@T1 9.s5-d1-t1-03-memo#p1@T1 10.s7-d2-t1-04-brief#p1@T1
- 混合前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-memo#p3@T1 3.s6-d3-t1-01-report#p3@T1 4.s6-d3-t1-01-note#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d3-t1-01-report#p1@T1 7.s6-d3-t1-01-memo#p1@T1 8.s5-d2-t1-91-digest#p1@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d1-t1-03-note#p3@T1
- 重排前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-memo#p3@T1 3.s6-d3-t1-01-report#p3@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d1-t1-03-memo#p3@T1 6.s6-d3-t1-01-note#p1@T1 7.s6-d3-t1-01-memo#p1@T1 8.s5-d2-t1-91-digest#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s6-d3-t1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 138. `s6-d3-t1-02-q1`

- 问：补丁记录中对竞品入门档的最新状态是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p1@T1；s6-d3-t1-02-report#p1@T1；s6-d3-t1-02-summary#p1@T1
- 金标要点：补丁记录把竞品入门档标成停售，相关系统已同步更新状态；补丁记录把竞品入门档标成停售，此变更已在最新版本中生效，建议停止对该型号的市场推广活动；补丁记录把竞品入门档标成停售，系统标记已更新，影响范围涵盖所有对外展示与内部分析模块
- 词法前 10：1.s6-d3-t1-02-report#p1@T1 2.s6-d3-t1-02-memo#p1@T1 3.s6-d3-t1-02-summary#p1@T1 4.s6-d0-t1-02-memo#p2@T1 5.s6-d0-t1-02-internal#p2@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d3-t1-03-memo#p1@T1 8.s6-d0-t1-02-report#p2@T1 9.s2-d0-t1-91-interview#p2@T1 10.s5-d3-t1-05-analysis#p3@T1
- 混合前 10：1.s6-d3-t1-02-memo#p1@T1 2.s6-d3-t1-02-report#p1@T1 3.s6-d3-t1-02-summary#p1@T1 4.s6-d0-t1-02-memo#p2@T1 5.s6-d0-t1-02-internal#p2@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d0-t1-02-report#p2@T1 8.s6-d0-t1-02-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p1@T1
- 重排前 10：1.s6-d3-t1-02-report#p1@T1 2.s6-d3-t1-02-memo#p1@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-summary#p1@T1 5.s6-d3-t1-03-report#p1@T1 6.s6-d0-t1-02-internal#p2@T1 7.s6-d0-t1-02-report#p2@T1 8.s6-d0-t1-02-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 139. `s6-d3-t1-02-q2`

- 问：复验安排在变更说明中发生了什么变动？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p2@T1；s6-d3-t1-02-report#p2@T1；s6-d3-t1-02-summary#p2@T1
- 金标要点：变更说明把复验安排从下月初改到月中，原定流程已调整，相关团队须重新规划时间节点并确认执行进度；变更说明把复验安排从下月初改到月中，相关责任部门需在本周内提交新的时间表以确保流程衔接；变更说明把复验安排从下月初改到月中，相关协调会议已重新排期，确保各环节无缝对接
- 词法前 10：1.s6-d3-t1-02-summary#p2@T1 2.s6-d3-t1-02-report#p2@T1 3.s6-d3-t1-02-memo#p2@T1 4.s6-d0-t1-01-patch#p3@T1 5.s6-d0-t1-01-patch#p1@T1 6.s6-d2-g1-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d1-t1-91-release#p3@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d1-t1-91-release#p2@T1
- 混合前 10：1.s6-d3-t1-02-summary#p2@T1 2.s6-d3-t1-02-memo#p2@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d0-t1-01-patch#p1@T1 5.s6-d0-t1-01-patch#p3@T1 6.s6-d2-g1-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d3-t1-03-memo#p2@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d3-t1-03-report#p2@T1
- 重排前 10：1.s6-d3-t1-02-summary#p2@T1 2.s6-d3-t1-02-memo#p2@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d0-t1-01-patch#p1@T1 5.s6-d0-t1-01-patch#p3@T1 6.s6-d2-g1-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d3-t1-03-memo#p2@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d3-t1-03-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 140. `s6-d3-t1-02-q3`

- 问：汇编中关于两份纪要的结论目前处于什么状态？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p3@T1；s6-d3-t1-02-report#p3@T1；s6-d3-t1-02-summary#p3@T1
- 金标要点：汇编把两份纪要的结论合成一条待核，当前尚未完成最终验证，需在下一周期前完成核实并归档；汇编把两份纪要的结论合成一条待核，目前处于待确认状态，暂不纳入正式决策依据；汇编把两份纪要的结论合成一条待核，当前状态为“待核实”，需指定负责人推进闭环处理
- 词法前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s6-d0-t1-01-memo#p3@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d0-t1-01-memo#p1@T1 7.s2-d3-01-memo#p2@T1 8.s5-d0-t1-02-analysis#p2@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d3-t1-91-minutes#p3@T1
- 混合前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d0-t1-01-memo#p1@T1 7.s6-d0-t1-01-memo#p3@T1 8.s5-d2-t1-91-digest#p1@T1 9.s6-d3-t1-01-note#p2@T1 10.s5-d0-t1-02-analysis#p2@T1
- 重排前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d0-t1-02-analysis#p2@T1 6.s6-d0-t1-01-channel#p1@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d0-t1-01-memo#p3@T1 9.s5-d2-t1-91-digest#p1@T1 10.s6-d3-t1-01-note#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 141. `s6-d3-t1-03-q1`

- 问：补丁记录中关于旧成本模型的用途是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-03-memo#p1@T1；s6-d3-t1-03-report#p1@T1
- 金标要点：补丁记录注明旧成本模型只供对照，不得用于实际核算；补丁记录注明旧成本模型只供对照，用于对比分析新方案的效益差异，严禁在正式决策中引用
- 词法前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s6-d3-t1-02-memo#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s6-d3-t1-02-summary#p1@T1 7.s6-d0-t1-01-patch#p1@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s5-d1-t1-03-summary#p2@T1 10.s4-d0-t1-02-memo#p1@T1
- 混合前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s6-d3-t1-02-summary#p1@T1 5.s6-d3-t1-02-memo#p1@T1 6.s6-d0-t1-03-memo#p2@T1 7.s4-d2-t1-91-model-v3#p1@T1 8.s4-d0-t1-02-memo#p1@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 重排前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s4-d0-t1-02-memo#p1@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s6-d3-t1-02-memo#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s4-d0-t1-02-plan#p1@T1 10.s6-d3-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 142. `s6-d3-t1-03-q2`

- 问：变更说明中对渠道折扣的最新状态如何描述？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-03-memo#p2@T1；s6-d3-t1-03-report#p2@T1
- 金标要点：变更说明中将渠道折扣描述为已撤回，表明此前发布的折扣政策不再有效，相关合作方需依据现行协议执行；变更说明把渠道折扣写成已撤回，明确指出原定优惠机制已终止，相关客户需重新协商合作条款
- 词法前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s6-d3-t1-02-report#p2@T1 7.s7-d0-t1-02-memo#p3@T1 8.s6-d3-t1-02-summary#p2@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d3-t1-02-memo#p2@T1
- 混合前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-channel#p1@T1 4.s6-d0-t1-01-memo#p2@T1 5.s6-d3-t1-02-summary#p2@T1 6.s6-d3-t1-02-report#p2@T1 7.s6-d3-t1-02-memo#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 重排前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-channel#p1@T1 4.s6-d0-t1-01-memo#p2@T1 5.s6-d3-t1-02-report#p2@T1 6.s6-d3-t1-02-summary#p2@T1 7.s6-d3-t1-02-memo#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 143. `s6-mh-12-new`

- 问：顾问备忘列了哪些未按期出资的新规则？转让未到期股权后受让人没交，原股东还要担什么责？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p5@T1；s6-d2-g3-memo#p1@T1；s6-d2-g3-memo#p3@T1
- 金标要点：转让人对受让人未按期缴纳的出资承担补充责任；2023法改为对公司损失承担赔偿责任，并新增董事会核查催缴、宽限期不少于六十日后失权、加速到期、未届期转让由受让人缴纳。
- 词法前 10：1.p1-colaw-capital-call#p5@T1 2.s6-d2-g3-memo#p3@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-capital-transition#p2@T1 7.p1-colaw-capital-call#p2@T1 8.p1-colaw-capital-call#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-equity#p5@T1
- 混合前 10：1.p1-colaw-capital-call#p5@T1 2.s6-d2-g3-memo#p3@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-capital-call#p4@T1 8.p1-colaw-equity#p1@T1 9.p1-colaw-capital-call#p3@T1 10.p1-colaw-equity#p3@T1
- 重排前 10：1.s6-d2-g3-memo#p3@T1 2.p1-colaw-capital-call#p5@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-equity#p1@T1 8.p1-colaw-capital-call#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-equity#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 144. `s6-mh-15-new`

- 问：顾问备忘说存量公司要调整出资期限；新法本身给新设公司的缴足期限是几年？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital#p1@T1
- 金标要点：全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足
- 词法前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p2@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-transition#p1@T1 5.s6-d2-g2-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.p1-colaw-capital-call#p4@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-capital-transition#p2@T1
- 混合前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p1@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-transition#p1@T1 5.s6-d2-g2-memo#p2@T1 6.s6-d2-g2-memo#p3@T1 7.s6-d2-g3-memo#p3@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital#p1@T1
- 重排前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p1@T1 3.s6-d2-g2-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g3-memo#p3@T1 7.s6-d2-g1-memo#p1@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-capital-call#p4@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 145. `s7-d0-t0-01-q1`

- 问：系统日志中‘连接超时’的真实原因是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-log#p1@T0
- 金标要点：系统日志中频繁出现“连接超时”警告，但网络监控工具显示带宽正常、延迟极低；经排查发现，该“超时”实为应用层心跳检测机制误判，而非真实网络故障
- 词法前 10：1.s7-d0-t0-01-log#p1@T0 2.s7-d1-t0-03-memo#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s7-d1-t0-03-fact#p3@T0 9.s7-d1-t0-03-claim#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 混合前 10：1.s7-d0-t0-01-log#p1@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-memo#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d1-t0-03-reason#p3@T0 7.s4-d3-t0-05-report#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d0-t0-01-log#p2@T0 10.s7-d0-t0-01-memo#p1@T0
- 重排前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-memo#p1@T0 3.s7-d0-t0-01-log#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-memo#p1@T0 7.s7-d1-t0-03-reason#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d0-t0-01-log#p2@T0 10.s4-d3-t0-05-report#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 146. `s7-d0-t0-01-q2`

- 问：关于每月首日的安全重置，系统文档和内部备忘录的说法一致吗？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-memo#p2@T0
- 金标要点：系统文档中提及“所有用户必须在每月首日完成安全重置”，而另一份内部备忘录指出“安全重置仅对高权限账户强制执行”；这两条信息存在同快照冲突陈述，同一时间点内出现矛盾指令，若未明确上下文，可能引发操作偏差
- 词法前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.p1-cac-o11#p1@T0 4.s7-d1-t0-03-memo#p3@T0 5.p1-cac-o11#p3@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d1-t0-03-claim#p3@T0 8.p1-cac-o13#p4@T0 9.p1-cac-o11#p13@T0 10.s2-d0-02-interview#p2@T0
- 混合前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.p1-cac-o11#p16@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d0-t0-01-internal#p3@T0 6.s7-d1-t0-03-memo#p2@T0 7.p1-cac-o11#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s7-d0-t0-01-arch#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s7-d0-t0-01-internal#p3@T0 4.p1-cac-o11#p16@T0 5.s7-d1-t0-03-memo#p2@T0 6.p1-cac-o11#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s7-d0-t0-01-arch#p1@T0 9.s7-d1-t0-03-memo#p3@T0 10.s7-d1-t0-03-reason#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 147. `s7-d0-t0-01-q3`

- 问：系统自称眼下没有已知漏洞，这种说法靠得住吗？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-memo#p3@T0
- 金标要点：该声明发布于一次重大补丁前，且未说明其时效性；可能误将“无漏洞”视为绝对事实
- 词法前 10：1.s7-d1-t0-03-claim#p3@T0 2.s7-d0-t0-01-memo#p3@T0 3.s5-d1-t0-91-repost#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s2-d2-t0-91-callnotes#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-memo#p1@T0 8.s1-d2-01-report#p3@T0 9.s4-d3-t0-91-method#p2@T0 10.s2-d2-01-report#p2@T0
- 混合前 10：1.s7-d0-t0-01-memo#p3@T0 2.s7-d1-t0-03-claim#p3@T0 3.s1-d0-05-warn#p3@T0 4.s2-d0-02-interview#p1@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p1@T0 7.s2-d3-01-memo#p3@T0 8.s1-d0-01-memo#p1@T0 9.s7-d1-t0-03-reason#p2@T0 10.s7-d1-t0-03-reason#p3@T0
- 重排前 10：1.s7-d0-t0-01-memo#p3@T0 2.s7-d1-t0-03-claim#p3@T0 3.s7-d0-t0-01-qa#p2@T0 4.s1-d0-05-warn#p3@T0 5.s2-d0-02-interview#p1@T0 6.s7-d1-t0-03-memo#p1@T0 7.s2-d3-01-memo#p3@T0 8.s1-d0-01-memo#p1@T0 9.s7-d1-t0-03-reason#p2@T0 10.s7-d1-t0-03-reason#p3@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 148. `s7-d0-t0-01-q4`

- 问：‘用户活跃度提升30%’这一数据是否具有代表性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-report#p1@T0
- 金标要点：该合成叙述通过选择性呈现数据构建积极表象，实则掩盖了真实流失率上升的事实，属于典型的合成叙述误导；数据来源为仅包含注册用户的样本池，未涵盖流失用户
- 词法前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s7-d0-t0-01-report#p3@T0 4.s7-d1-t0-03-reason#p3@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-qa#p2@T0 7.p1-cac-o11#p4@T0 8.s7-d1-t0-03-memo#p1@T0 9.s7-d1-t0-03-claim#p3@T0 10.s7-d1-t0-03-claim#p1@T0
- 混合前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s2-d2-01-report#p1@T0 4.s1-d0-02-report#p1@T0 5.s7-d0-t0-01-qa#p2@T0 6.s5-d0-t0-01-report#p1@T0 7.s1-d1-01-analysis#p3@T0 8.s3-d0-01-report#p2@T0 9.s2-d0-01-report#p1@T0 10.s4-d3-t0-05-memo#p2@T0
- 重排前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s2-d2-01-report#p1@T0 4.s7-d0-t0-01-qa#p2@T0 5.s5-d0-t0-01-report#p1@T0 6.s3-d0-01-report#p2@T0 7.s4-d3-t0-05-memo#p2@T0 8.s1-d0-02-report#p1@T0 9.s1-d1-01-analysis#p3@T0 10.s2-d0-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 149. `s7-d0-t0-01-q5`

- 问：说全部服务都能不停机升级，这话有没有例外？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-arch#p2@T0
- 金标要点：文档中写道：“所有服务均支持热升级”，但部分老旧服务仍需重启才能更新；尽管“支持热升级”在多数情况下成立，但未说明例外情况，导致该陈述在检索时被当作普遍规则使用
- 词法前 10：1.s4-d1-t0-03-analysis#p1@T0 2.s7-d0-t0-01-arch#p2@T0 3.s1-d0-05-memo#p2@T0 4.p1-colaw-equity#p1@T0 5.s5-d1-t0-91-repost#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s3-d0-04-memo#p2@T0 8.s1-d0-04-risk#p2@T0 9.s3-d1-01-memo#p2@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s7-d0-t0-01-arch#p2@T0 2.s1-d0-05-memo#p2@T0 3.s2-d0-02-interview#p2@T0 4.s5-d0-t0-01-report#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-04-risk#p2@T0 8.s2-d0-03-interview#p2@T0 9.s1-d0-01-analysis#p2@T0 10.s1-d0-04-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-arch#p2@T0 2.s1-d0-05-memo#p2@T0 3.s2-d0-02-interview#p2@T0 4.s5-d0-t0-01-report#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-04-risk#p2@T0 8.s1-d0-01-analysis#p2@T0 9.s1-d0-04-memo#p3@T0 10.s2-d0-03-interview#p2@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 150. `s7-d0-t0-01-q6`

- 问：FAQ中‘支持多设备登录’的限制条件是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-qa#p2@T0
- 金标要点：同时在线设备数上限为3个
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s7-d1-t0-03-claim#p3@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-claim#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s3-d0-t0-91-flyer#p3@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-fact#p2@T0
- 混合前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s4-d1-t0-03-memo#p3@T0 4.s1-d0-04-risk#p3@T0 5.s7-d0-t0-01-arch#p2@T0 6.s3-d0-t0-91-flyer#p3@T0 7.s3-d1-01-report#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d1-t0-03-memo#p2@T0 10.s3-d3-01-memo#p2@T0
- 重排前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s3-d0-t0-91-flyer#p3@T0 5.s7-d0-t0-01-qa#p1@T0 6.s4-d1-t0-03-memo#p3@T0 7.s1-d0-04-risk#p3@T0 8.s7-d0-t0-01-arch#p2@T0 9.s3-d1-01-report#p3@T0 10.s3-d3-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 151. `s7-d0-t1-02-q1`

- 问：用户报“搜索功能失效”但服务状态正常的案例中，系统为什么会误判与‘搜索’相关的请求？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p1@T1
- 金标要点：进一步排查发现，该问题源于关键词‘搜索’在不同上下文中具有双重含义——既指系统核心功能；检索模型误判请求意图，从而返回无关结果
- 词法前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d2-t1-04-memo#p1@T1 3.s7-d0-t1-02-claim#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d3-t1-05-synthetic#p3@T1 7.s7-d0-t1-02-claim#p2@T1 8.s7-d2-t1-04-data#p2@T1 9.s7-d3-t1-05-memo#p3@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d2-t1-04-memo#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d3-t1-05-claim#p1@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s7-d3-t1-05-conflict#p2@T1 9.s7-d0-t1-02-analysis#p3@T1 10.s7-d2-t1-04-brief#p3@T1
- 重排前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d2-t1-04-memo#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d3-t1-05-memo#p3@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s7-d2-t1-04-brief#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 152. `s7-d0-t1-02-q2`

- 问：一份材料先后被打上“已核实”和“待复查”两种标签，检索系统同时读到时会出什么问题？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p2@T1
- 金标要点：值得注意的是，同一份文档在多个时间点被标记为“已验证”和“待审查”；当检索系统同时加载两个快照时，其判断依据出现冲突：一个版本声称内容准确，另一个则指出存在偏差；系统难以确定哪一信息应作为权威参考
- 词法前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d3-t1-02-summary#p3@T1 3.s7-d0-t1-02-brief#p1@T1 4.s5-d0-t1-02-memo#p2@T1 5.s7-d2-t1-04-brief#p1@T1 6.s6-d0-t1-01-patch#p2@T1 7.s6-d0-t1-03-report#p2@T1 8.s7-d3-t1-05-conflict#p1@T1 9.s6-d0-t1-01-memo#p3@T1 10.s7-d3-t1-05-memo#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d0-t1-01-patch#p2@T1 3.s7-d3-t1-05-memo#p3@T1 4.s6-d3-t1-02-summary#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s6-d0-t1-01-memo#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-brief#p3@T1 9.s7-d2-t1-04-data#p3@T1 10.s7-d0-t1-02-update#p2@T1
- 重排前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-summary#p3@T1 4.s7-d0-t1-02-claim#p2@T1 5.s6-d0-t1-01-memo#p3@T1 6.s7-d0-t1-02-update#p2@T1 7.s7-d3-t1-05-memo#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s7-d2-t1-04-data#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 153. `s7-d0-t1-02-q3`

- 问：文档里注明“此处只是推测”的自我说明，模型为什么会把它当成事实来用？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p3@T1
- 金标要点：此外，文档中的元陈述如“本节内容为推测性分析”被误认为是事实陈述，导致检索结果中混入非确定性信息；此类自我指涉的描述虽有助于说明可信度，却常被模型当作真实数据处理，形成合成叙述陷阱
- 词法前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s5-d1-t1-03-summary#p3@T1 4.s7-d0-t1-02-analysis#p2@T1 5.s6-d3-t1-01-report#p3@T1 6.s7-d3-t1-05-memo#p3@T1 7.s6-d0-t1-03-internal#p1@T1 8.s6-d0-t1-03-report#p1@T1 9.s6-d1-t1-91-release#p1@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 混合前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d0-t1-02-analysis#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s6-d3-t1-01-report#p3@T1 8.s7-d2-t1-04-data#p3@T1 9.s7-d2-t1-04-brief#p3@T1 10.s6-d0-t1-03-report#p2@T1
- 重排前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d0-t1-02-analysis#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d2-t1-04-brief#p3@T1 9.s6-d0-t1-03-report#p2@T1 10.s6-d3-t1-01-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 154. `s7-d0-t1-02-q4`

- 问：在医疗术语中，‘心衰’与‘心力衰竭’为何可能导致检索偏差？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-brief#p1@T1
- 金标要点：在医疗知识库中，“心衰”与“心力衰竭”被用作同义词，但在部分文献中，“心衰”特指急性发作阶段；当检索系统未区分语义层级时，将两者等同处理，导致部分患者治疗方案被错误推荐；“心衰”特指急性发作阶段，而“心力衰竭”涵盖慢性与急性
- 词法前 10：1.s7-d0-t1-02-claim#p1@T1 2.s7-d0-t1-02-brief#p1@T1 3.s7-d0-t1-02-memo#p1@T1 4.s7-d0-t1-02-report#p3@T1 5.s7-d3-t1-05-synthetic#p3@T1 6.s7-d0-t1-02-memo#p3@T1 7.s5-d0-t1-02-memo#p3@T1 8.s7-d3-t1-05-claim#p2@T1 9.s4-d0-t1-02-memo#p2@T1 10.s5-d3-t1-05-memo#p2@T1
- 混合前 10：1.s7-d0-t1-02-brief#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d3-t1-05-claim#p2@T1 4.s4-d0-t1-02-memo#p2@T1 5.s7-d0-t1-02-claim#p1@T1 6.s7-d2-t1-04-memo#p1@T1 7.s7-d0-t1-02-brief#p2@T1 8.s7-d3-t1-05-conflict#p3@T1 9.s7-d3-t1-05-conflict#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 重排前 10：1.s7-d0-t1-02-brief#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-memo#p2@T1 5.s7-d2-t1-04-memo#p1@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-brief#p2@T1 8.s7-d3-t1-05-conflict#p3@T1 9.s7-d3-t1-05-conflict#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 155. `s7-d0-t1-02-q5`

- 问：系统如何因未识别版本时效性而产生矛盾输出？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-brief#p3@T1
- 金标要点：系统还曾因同时引用两版修订稿而产生矛盾输出：一版称“剂量上限为50mg”，另一版则标注“需根据个体调整”；当检索器未能识别版本时效性差异时，生成的回答包含相互排斥的信息，严重削弱可信度
- 词法前 10：1.s7-d0-t1-02-brief#p3@T1 2.s7-d0-t1-02-claim#p2@T1 3.s4-d2-t1-04-report#p3@T1 4.s4-d0-t1-02-guide#p2@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s2-d0-03-interview#p3@T1 7.s2-d2-01-memo#p3@T1 8.s7-d3-t1-05-synthetic#p3@T1 9.s6-d3-t1-01-report#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 混合前 10：1.s7-d0-t1-02-brief#p3@T1 2.s7-d0-t1-02-claim#p2@T1 3.s7-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-guide#p2@T1 5.s2-d2-01-memo#p3@T1 6.s7-d0-t1-02-memo#p2@T1 7.s4-d2-t1-04-report#p3@T1 8.s7-d3-t1-05-memo#p3@T1 9.s7-d0-t1-02-update#p3@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 重排前 10：1.s7-d0-t1-02-brief#p3@T1 2.s7-d0-t1-02-claim#p2@T1 3.s7-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-guide#p2@T1 5.s2-d2-01-memo#p3@T1 6.s7-d0-t1-02-memo#p2@T1 7.s4-d2-t1-04-report#p3@T1 8.s7-d3-t1-05-memo#p3@T1 9.s7-d0-t1-02-update#p3@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 156. `s7-d0-t1-02-q6`

- 问：为什么预测性元陈述容易在合成叙述中被当作事实？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-claim#p3@T1
- 金标要点：更为隐蔽的是，文档中一句“我们预计下季度将有新版本发布”被多次引用，且每次都被当作事实陈述使用；实际上，该句属于预测性元陈述，未经过正式确认
- 词法前 10：1.s7-d0-t1-02-claim#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d0-t1-02-brief#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d0-t1-02-report#p2@T1 6.s7-d0-t1-02-analysis#p2@T1 7.s7-d2-t1-04-claim#p3@T1 8.s7-d3-t1-05-memo#p3@T1 9.s7-d2-t1-04-brief#p1@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-report#p2@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d0-t1-02-analysis#p2@T1 7.s5-d1-t1-03-summary#p3@T1 8.s5-d0-t1-02-analysis#p3@T1 9.s7-d0-t1-02-analysis#p3@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 重排前 10：1.s7-d0-t1-02-claim#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d0-t1-02-brief#p2@T1 4.s7-d0-t1-02-report#p2@T1 5.s5-d1-t1-03-summary#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d3-t1-05-synthetic#p3@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s7-d0-t1-02-analysis#p3@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 157. `s7-d1-t0-03-q1`

- 问：两个看似矛盾的系统状态报告为什么可能同时为真？材料给出了哪几种解释？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-memo#p2@T0；s7-d1-t0-03-reason#p1@T0；s7-d1-t0-03-reason#p2@T0
- 金标要点：二者均真实，但反映不同时间快照；源于部署流水线中各组件更新节奏不一致，造成同一时间点下多版本共存的快照冲突；系统在达成最终一致性前的短暂状态
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-reason#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-report#p3@T0 7.p1-cac-o11#p5@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s5-d2-t0-04-report#p3@T0 10.p1-cac-o13#p6@T0
- 混合前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-reason#p3@T0 3.s7-d1-t0-03-reason#p2@T0 4.s4-d0-t0-01-analysis#p3@T0 5.s7-d1-t0-03-claim#p2@T0 6.s4-d3-t0-05-summary#p3@T0 7.p1-cac-o13#p6@T0 8.s7-d0-t0-01-internal#p1@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d0-t0-01-qa#p2@T0
- 重排前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-reason#p3@T0 3.s7-d1-t0-03-reason#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s7-d1-t0-03-claim#p2@T0 6.s4-d3-t0-05-summary#p3@T0 7.p1-cac-o13#p6@T0 8.s7-d0-t0-01-internal#p1@T0 9.s7-d1-t0-03-fact#p3@T0 10.s4-d0-t0-01-analysis#p3@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 158. `s7-d1-t0-03-q2`

- 问：以密钥轮换不同步导致‘认证失败’被误读为例，什么是词面撞车？它在技术文档里怎样表现？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-memo#p1@T0
- 金标要点：这种词面撞车现象常导致误判；在某次跨部门协作中，系统日志显示‘用户认证失败’频繁出现；表面冲突，实则源于对‘失败’一词的语义理解差异；前者指连接中断，后者指验证机制失效
- 词法前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d1-t0-03-reason#p1@T0 7.s7-d1-t0-03-claim#p3@T0 8.s2-d2-t0-91-callnotes#p2@T0 9.s5-d1-t0-91-repost#p1@T0 10.s7-d0-t0-01-report#p2@T0
- 混合前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-log#p2@T0 7.s7-d1-t0-03-memo#p2@T0 8.s7-d0-t0-01-report#p2@T0 9.s7-d1-t0-03-claim#p3@T0 10.s7-d1-t0-03-fact#p3@T0
- 重排前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d1-t0-03-reason#p2@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d0-t0-01-log#p2@T0 9.s7-d0-t0-01-report#p2@T0 10.s7-d1-t0-03-fact#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 159. `s7-d1-t0-03-q3`

- 问：如何判断一篇报告中的‘共识’描述是否具有误导性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-claim#p1@T0；s7-d1-t0-03-claim#p3@T0；s7-d1-t0-03-fact#p2@T0
- 金标要点：这些引述均源自少数几位学者的非公开访谈，且未提供原始立场记录；有两项结论为负面或中性，且未被充分讨论；一个说法被‘多位分析师确认’，而该说法本身又‘基于行业标准’，形成闭环论证
- 词法前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-reason#p2@T0 4.s5-d1-t0-91-repost#p1@T0 5.s7-d1-t0-03-fact#p2@T0 6.s7-d1-t0-03-reason#p1@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d1-t0-03-memo#p2@T0 9.p1-cac-o11#p4@T0 10.s7-d0-t0-01-report#p3@T0
- 混合前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d0-t0-01-report#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d1-t0-03-reason#p3@T0 9.s7-d1-t0-03-claim#p2@T0 10.s7-d1-t0-03-memo#p1@T0
- 重排前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d1-t0-03-claim#p3@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d1-t0-03-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-reason#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 160. `s7-d1-t0-03-q4`

- 问：第三方综述称“研究一致支持某疗法”的案例里，合成叙述如何靠选择性整合制造虚假一致性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-fact#p2@T0
- 金标要点：该叙述通过选择性强调正向结果构建了虚假共识，构成典型的合成叙述陷阱；有两项结论为负面或中性，且未被充分讨论
- 词法前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d0-t0-01-qa#p2@T0 3.s7-d0-t0-01-report#p1@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d0-t0-01-arch#p1@T0 6.s7-d1-t0-03-claim#p2@T0 7.s5-d0-t0-01-press#p1@T0 8.s7-d1-t0-03-fact#p1@T0 9.s5-d0-t0-01-internal#p2@T0 10.s7-d1-t0-03-claim#p1@T0
- 混合前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-claim#p2@T0 3.s7-d0-t0-01-report#p1@T0 4.s7-d1-t0-03-claim#p1@T0 5.s7-d1-t0-03-fact#p1@T0 6.s5-d0-t0-01-internal#p2@T0 7.s7-d1-t0-03-memo#p3@T0 8.s5-d0-t0-01-memo#p3@T0 9.s7-d0-t0-01-internal#p3@T0 10.s7-d0-t0-01-memo#p3@T0
- 重排前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d0-t0-01-report#p1@T0 3.s7-d1-t0-03-fact#p1@T0 4.s7-d1-t0-03-claim#p2@T0 5.s7-d1-t0-03-claim#p1@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d0-t0-01-memo#p3@T0 8.s5-d0-t0-01-internal#p2@T0 9.s7-d1-t0-03-memo#p3@T0 10.s5-d0-t0-01-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 161. `s7-d2-t1-04-q1`

- 问：以“搜索结果未按时间排序”的投诉为例，怎样识别术语歧义造成的词面撞车？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-memo#p1@T1
- 金标要点：此现象源于术语“时间”的词面撞车——同一词汇在不同语境中指向不同维度，导致用户预期与系统行为错位；用户所指的“时间”实为“提交时间”，而系统默认按“处理时间”排序
- 词法前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-conflict#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s7-d3-t1-05-memo#p1@T1 7.s7-d2-t1-04-claim#p1@T1 8.s7-d2-t1-04-claim#p2@T1 9.s5-d0-t1-02-report#p2@T1 10.s7-d3-t1-05-memo#p3@T1
- 混合前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-memo#p1@T1 5.s7-d3-t1-05-conflict#p3@T1 6.s7-d3-t1-05-memo#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-claim#p2@T1 9.s5-d0-t1-02-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 重排前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-conflict#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s7-d3-t1-05-memo#p1@T1 7.s7-d3-t1-05-memo#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s5-d0-t1-02-summary#p3@T1 10.s5-d0-t1-02-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 162. `s7-d2-t1-04-q2`

- 问：多份文档用同一组原始数据、一份说显著改善另一份说没达标时，怎么判断这算不算同快照冲突陈述？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-data#p3@T1
- 金标要点：这种基于相同快照的不同解释，反映合成叙述中对数据的多重建构能力，若缺乏上下文比对，极易引发检索误解
- 词法前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p2@T1 5.s7-d2-t1-04-data#p1@T1 6.s5-d1-t1-03-summary#p2@T1 7.s7-d3-t1-05-claim#p1@T1 8.s7-d0-t1-02-report#p2@T1 9.s2-d0-t1-91-memo#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d2-t1-04-data#p1@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d2-t1-04-brief#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-claim#p2@T1 9.s5-d1-t1-03-summary#p2@T1 10.s5-d0-t1-02-memo#p3@T1
- 重排前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d2-t1-04-data#p1@T1 5.s7-d3-t1-05-claim#p1@T1 6.s5-d0-t1-02-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s5-d1-t1-03-summary#p2@T1 10.s7-d0-t1-02-claim#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 163. `s7-d2-t1-04-q3`

- 问：元陈述与实际内容不一致时，可能引发哪些检索风险？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-claim#p3@T1；s7-d2-t1-04-memo#p3@T1
- 金标要点：此自相矛盾的元声明削弱了整份材料的可信度，构成元层级的检索陷阱，即对内容真实性本身的宣称与实际内容不符；自我宣称与实际证据链之间的脱节
- 词法前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s6-d2-g1-memo#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p3@T1 8.p1-cac-o20#p8@T1 9.s7-d0-t1-02-claim#p1@T1 10.s7-d3-t1-05-memo#p2@T1
- 混合前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d2-t1-04-claim#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d0-t1-02-analysis#p3@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-report#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 重排前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d2-t1-04-claim#p3@T1 4.s7-d0-t1-02-analysis#p3@T1 5.s7-d0-t1-02-brief#p2@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-report#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 164. `s7-d2-t1-04-q4`

- 问：合成叙述如何通过模糊定义和选择性呈现误导用户判断？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-brief#p1@T1
- 金标要点：这种合成叙述通过选择性呈现数据和模糊操作定义，构建出看似合理但有偏差的整体印象，典型体现为对事实的非透明重构；一份关于用户满意度的分析报告称：“多数受访者表示体验良好；“满意”选项的定义被刻意模糊；样本仅来自高活跃用户群体
- 词法前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-synthetic#p2@T1 4.s7-d0-t1-02-claim#p2@T1 5.s7-d0-t1-02-report#p3@T1 6.s6-d0-t1-01-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s3-d0-03-report#p3@T1 10.s7-d3-t1-05-claim#p3@T1
- 混合前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-claim#p3@T1 4.s7-d0-t1-02-report#p2@T1 5.s7-d3-t1-05-synthetic#p2@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s5-d1-t1-03-summary#p3@T1 9.s7-d3-t1-05-memo#p3@T1 10.s7-d2-t1-04-brief#p3@T1
- 重排前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-synthetic#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s7-d2-t1-04-brief#p3@T1 6.s7-d3-t1-05-claim#p3@T1 7.s7-d0-t1-02-report#p2@T1 8.s7-d0-t1-02-memo#p3@T1 9.s7-d3-t1-05-synthetic#p3@T1 10.s5-d1-t1-03-summary#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 165. `s7-d3-t1-05-q1`

- 问：技术组说日志里没有登录失败记录、审计组却说全都抓到了，哪份材料解释了这是术语口径不同？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-memo#p1@T1
- 金标要点：在某次跨部门数据对齐会议中，技术团队报告称“系统日志未记录用户登录失败事件”，而安全审计组却声称“所有登录失败均被完整捕获”；表面上看二者矛盾，实则因术语定义不同：前者指未写入特定日志文件，后者指已通过集中式监控平台覆盖；这种词面撞车现象常引发误判
- 词法前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d3-t1-91-changelog#p2@T1 5.s2-d0-t1-91-memo#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s7-d0-t1-02-report#p1@T1 8.s2-d0-t1-91-interview#p2@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s7-d0-t1-02-claim#p1@T1
- 混合前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p2@T1 3.s6-d1-t1-91-release#p2@T1 4.s7-d0-t1-02-claim#p1@T1 5.s6-d3-t1-91-changelog#p1@T1 6.s6-d3-t1-91-changelog#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d0-t1-02-memo#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 重排前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p2@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d3-t1-91-changelog#p3@T1 5.s7-d0-t1-02-claim#p1@T1 6.s6-d3-t1-91-changelog#p1@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d0-t1-02-memo#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 166. `s7-d3-t1-05-q2`

- 问：哪份文档借“完成度87%仍算达标”一例，揭示了‘达标’在不同评价标准下的多重解释？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-memo#p2@T1
- 金标要点：该指标实际完成度为87%，但经评估后仍视为达标。；这表明系统性地使用“达标”一词掩盖了真实绩效差距，构成元层面的陈述冲突。
- 词法前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d3-t1-05-memo#p3@T1 4.s7-d0-t1-02-memo#p1@T1 5.s7-d2-t1-04-memo#p2@T1 6.s7-d0-t1-02-claim#p1@T1 7.s7-d0-t1-02-update#p3@T1 8.s7-d2-t1-04-memo#p1@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d0-t1-02-report#p3@T1
- 混合前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s7-d3-t1-05-conflict#p2@T1 7.s7-d0-t1-02-claim#p3@T1 8.s6-d3-t1-01-note#p3@T1 9.s5-d1-t1-03-note#p2@T1 10.s7-d2-t1-04-claim#p3@T1
- 重排前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s7-d0-t1-02-claim#p3@T1 7.s7-d2-t1-04-claim#p3@T1 8.s5-d1-t1-03-note#p2@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s6-d3-t1-01-note#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 167. `s7-d3-t1-05-q3`

- 问：哪一个文档展示了通过选择性引用专家来构建虚假权威的现象？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-synthetic#p2@T1
- 金标要点：这种通过选择性引用构建权威感，是合成叙述的常见手法；更隐蔽的是，该材料同时引用“专家普遍认可”作为背书，但所列专家中仅有两人发表过相关研究
- 词法前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-brief#p1@T1 4.s7-d0-t1-02-claim#p3@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d1-t1-03-note#p3@T1 7.s7-d2-t1-04-memo#p3@T1 8.s7-d0-t1-02-update#p1@T1 9.s7-d2-t1-04-brief#p2@T1 10.s5-d1-t1-03-note#p1@T1
- 混合前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-update#p1@T1 4.s7-d2-t1-04-claim#p3@T1 5.s7-d3-t1-05-conflict#p2@T1 6.s5-d0-t1-02-analysis#p3@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-memo#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s5-d1-t1-03-note#p1@T1
- 重排前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-update#p1@T1 4.s7-d2-t1-04-memo#p3@T1 5.s5-d1-t1-03-note#p1@T1 6.s7-d2-t1-04-claim#p3@T1 7.s5-d0-t1-02-analysis#p3@T1 8.s5-d1-t1-03-memo#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s7-d3-t1-05-conflict#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 168. `s7-d3-t1-05-q4`

- 问：哪份文档分析了‘进度保持在预期轨道上’这一说法与实际延迟之间的语义断裂？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-conflict#p1@T1
- 金标要点：在一份项目总结报告中，反复强调“进度保持在预期轨道上”；但详细日程表显示，关键里程碑已延迟两周，且资源调配不足；这里的“预期轨道”未明确定义，导致词面重复掩盖了实质延误，形成语义断裂。
- 词法前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d3-t1-05-conflict#p3@T1 3.s7-d0-t1-02-analysis#p3@T1 4.s5-d2-t1-91-digest#p3@T1 5.s7-d2-t1-04-claim#p3@T1 6.s5-d3-t1-05-analysis#p3@T1 7.s6-d3-t1-91-changelog#p3@T1 8.s6-d3-t1-01-note#p3@T1 9.s6-d3-t1-01-memo#p3@T1 10.s6-d3-t1-01-report#p3@T1
- 混合前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d3-t1-05-conflict#p3@T1 4.s7-d2-t1-04-brief#p2@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s7-d2-t1-04-brief#p3@T1 7.s1-d0-03-memo#p2@T1 8.s7-d2-t1-04-claim#p3@T1 9.s7-d0-t1-02-analysis#p1@T1 10.s7-d0-t1-02-report#p1@T1
- 重排前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d3-t1-05-conflict#p3@T1 3.s7-d0-t1-02-analysis#p3@T1 4.s5-d3-t1-05-analysis#p3@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d2-t1-04-brief#p2@T1 7.s7-d0-t1-02-analysis#p1@T1 8.s7-d2-t1-04-brief#p3@T1 9.s7-d0-t1-02-report#p1@T1 10.s1-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 169. `r4m-s5-d3-t1-05-q4`

- 问：按官方最新统计，这个地区的制造业在经济总量里还占三成以上吗？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-report#p2@T1
- 金标要点：该比例已下降至28%
- 词法前 10：1.s5-d3-t1-05-report#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-01-memo#p1@T1 4.p2-gdp-national#p2@T1 5.s6-d0-t1-03-memo#p1@T1 6.s1-d1-01-analysis#p3@T1 7.s5-d2-t1-91-digest#p3@T1 8.s2-d0-t1-91-interview#p3@T1 9.s6-d0-t1-91-sop#p2@T1 10.s6-d3-t1-91-changelog#p3@T1
- 混合前 10：1.s5-d3-t1-05-report#p1@T1 2.p2-gdp-national#p2@T1 3.s5-d2-t1-91-digest#p3@T1 4.s2-d0-t1-91-memo#p1@T1 5.s6-d3-t1-91-changelog#p3@T1 6.s2-d0-01-memo#p1@T1 7.s5-d2-t1-91-digest#p1@T1 8.s2-d0-t1-91-interview#p3@T1 9.s5-d3-t1-05-report#p2@T1 10.s5-d3-t1-05-memo#p3@T1
- 重排前 10：1.s5-d3-t1-05-report#p1@T1 2.s5-d2-t1-91-digest#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-01-memo#p1@T1 5.s2-d0-t1-91-interview#p3@T1 6.s5-d3-t1-05-memo#p3@T1 7.p2-gdp-national#p2@T1 8.s6-d3-t1-91-changelog#p3@T1 9.s5-d2-t1-91-digest#p1@T1 10.s5-d3-t1-05-report#p2@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 170. `r4m-s5-d3-t1-05-q5`

- 问：员工对工作环境满不满意，最新一轮调查给出的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p2@T1
- 金标要点：满意度已升至67%
- 词法前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s2-d2-01-memo#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d3-t1-05-memo#p2@T1 5.p1-colaw-equity#p3@T1 6.s5-d3-t1-05-analysis#p3@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-cac-o16#p5@T1 9.s2-d0-02-memo#p1@T1 10.s7-d2-t1-04-brief#p1@T1
- 混合前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s7-d2-t1-04-brief#p1@T1 3.s5-d3-t1-05-analysis#p3@T1 4.s1-d1-01-memo#p3@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s1-d0-04-memo#p3@T1 7.s5-d3-t1-05-memo#p2@T1 8.s2-d0-02-memo#p1@T1 9.s1-d0-02-memo#p3@T1 10.s2-d2-01-memo#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s5-d3-t1-05-memo#p2@T1 3.s2-d2-01-memo#p1@T1 4.s7-d2-t1-04-brief#p1@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s5-d3-t1-05-analysis#p2@T1 7.s1-d0-02-memo#p3@T1 8.s1-d1-01-memo#p3@T1 9.s1-d0-04-memo#p3@T1 10.s2-d0-02-memo#p1@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

### 171. `r4m-s5-d3-t1-05-q6`

- 问：城市居民每天坐公交出行的人，最近那次独立调查测出来占多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-memo#p2@T1
- 金标要点：使用公共交通的比例上升至51%
- 词法前 10：1.s5-d3-t1-05-memo#p1@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.p1-colaw-governance#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s3-d1-01-report#p1@T1 6.p2-gdp-national#p2@T1 7.s6-d1-c3-memo#p3@T1 8.p1-colaw-capital-call#p5@T1 9.s1-d3-01-memo#p2@T1 10.s6-d0-t1-03-report#p3@T1
- 混合前 10：1.s5-d3-t1-05-memo#p1@T1 2.s5-d3-t1-05-memo#p2@T1 3.s5-d1-t1-03-report#p2@T1 4.s5-d0-t1-02-analysis#p1@T1 5.s5-d1-t1-03-memo#p2@T1 6.s7-d3-t1-05-synthetic#p1@T1 7.s5-d0-t1-02-memo#p2@T1 8.s6-d1-c3-memo#p3@T1 9.s5-d1-t1-03-memo#p3@T1 10.s6-d0-t1-03-report#p3@T1
- 重排前 10：1.s5-d3-t1-05-memo#p1@T1 2.s5-d3-t1-05-memo#p2@T1 3.s5-d1-t1-03-report#p2@T1 4.s5-d0-t1-02-analysis#p1@T1 5.s5-d1-t1-03-memo#p2@T1 6.s7-d3-t1-05-synthetic#p1@T1 7.s5-d0-t1-02-memo#p2@T1 8.s6-d1-c3-memo#p3@T1 9.s5-d1-t1-03-memo#p3@T1 10.s6-d0-t1-03-report#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 172. `r4m-s5-d0-t1-02-q5`

- 问：被媒体反复转述的早高峰车速和拥堵时长，独立研究实际测到的是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p2@T1
- 金标要点：真实车速为16公里/小时；拥堵时长约为3.2小时
- 词法前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s2-d0-t1-91-interview#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-report#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.p1-cac-o11#p10@T1 9.s5-d0-t1-02-memo#p3@T1 10.s5-d0-t1-02-report#p2@T1
- 混合前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d1-t1-03-summary#p1@T1 7.s5-d0-t1-02-report#p2@T1 8.s4-d0-t1-91-eval#p2@T1 9.s2-d0-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d0-t1-02-report#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s5-d3-t1-05-memo#p1@T1 8.s5-d1-t1-03-summary#p1@T1 9.s4-d0-t1-91-eval#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 173. `r4m-s3-d3-01-q5`

- 问：竞品B这一期的月费，两份比价材料写得一样吗？各写了多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p2@T1；s3-d3-01-report#p2@T1
- 金标要点：月费最低可至99元；月费降至129元
- 词法前 10：1.s3-d1-t1-91-pricesheet#p2@T1 2.s3-d3-01-memo#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d2-01-competitor-pricing#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d1-01-memo#p2@T1 7.s3-d1-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p3@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d0-01-report#p2@T1
- 混合前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d1-t1-91-quote#p3@T1 4.s3-d1-t1-91-pricesheet#p2@T1 5.s3-d3-01-report#p2@T1 6.s3-d1-01-memo#p2@T1 7.s3-d3-01-memo#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-brochure#p2@T1
- 重排前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d3-01-memo#p2@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-01-memo#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-brochure#p2@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 174. `r4m-s3-d0-02-q7`

- 问：C公司149元的新方案现在已经开卖了吗？两份比价材料怎么说？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T1；s3-d0-02-b#p3@T1
- 金标要点：改推“成长计划”订阅制，首年费用149元，含全功能访问及优先技术支持，用户迁移率已达72%；现仅开放限时试用，正式版本将于下季度以149元起售
- 词法前 10：1.s3-d0-02-a#p3@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s7-d2-t1-04-memo#p3@T1 6.s3-d1-t1-91-pricesheet#p3@T1 7.s3-d1-t1-91-pricesheet#p1@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-01-memo#p3@T1 10.p1-colaw-governance#p1@T1
- 混合前 10：1.s3-d0-02-a#p3@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-01-memo#p3@T1 6.s3-d0-01-memo#p3@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-t1-91-pricesheet#p3@T1 9.s3-d0-02-b#p3@T1 10.s3-d0-01-report#p1@T1
- 重排前 10：1.s3-d0-02-a#p3@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-report#p1@T1 7.s3-d1-01-memo#p3@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-t1-91-pricesheet#p3@T1 10.s3-d0-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 175. `r4n-s2-d0-t1-91-qa`

- 问：越南那边的经销商返点，最终按多少给？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d0-t1-91-memo#p1@T1
- 金标要点：把返点比例定为5%
- 词法前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.p2-gdp-national#p3@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-interview#p3@T1 7.s6-d1-t1-91-patch#p1@T1 8.s2-d0-04-memo#p3@T1 9.s6-d3-t1-91-notice#p1@T1 10.p1-colaw-capital-call#p1@T1
- 混合前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-04-memo#p3@T1 5.s4-d2-t1-91-review#p2@T1 6.s2-d0-t1-91-interview#p3@T1 7.s6-d0-t1-91-sop#p3@T1 8.s3-d3-01-report#p2@T1 9.s2-d0-04-memo#p1@T1 10.s2-d0-02-memo#p3@T1
- 重排前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-memo#p3@T1 4.s2-d0-04-memo#p3@T1 5.s2-d0-t1-91-interview#p3@T1 6.s3-d3-01-report#p2@T1 7.s4-d2-t1-91-review#p2@T1 8.s6-d0-t1-91-sop#p3@T1 9.s2-d0-04-memo#p1@T1 10.s2-d0-02-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 176. `r4n-s2-d0-t1-91-qb`

- 问：关于越南经销商返点，访谈里的口径和后来正式签的约有什么出入？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d0-t1-91-interview#p1@T1；s2-d0-t1-91-memo#p1@T1
- 金标要点：返点比例会维持在8%；把返点比例定为5%
- 词法前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d3-t1-91-interview#p2@T1 4.s2-d0-t1-91-interview#p3@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s7-d2-t1-04-brief#p1@T1 9.s6-d3-t1-91-changelog#p1@T1 10.p1-colaw-governance-supervisor-js#p4@T1
- 混合前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s6-d0-t1-91-sop#p3@T1 5.s2-d0-t1-91-memo#p3@T1 6.s6-d3-t1-91-changelog#p1@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-cac-o20#p8@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d0-04-memo#p3@T1
- 重排前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s2-d3-t1-91-interview#p2@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-memo#p3@T1 7.s6-d3-t1-91-changelog#p1@T1 8.p1-cac-o20#p8@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d0-04-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 177. `r4n-s3-d1-t1-91-qa`

- 问：竞品E标准版一年现在要花多少钱？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-quote#p1@T1
- 金标要点：把标准版年费调整为4200元
- 词法前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d1-t1-91-quote#p1@T1 4.s3-d1-t1-91-quote#p3@T1 5.s3-d0-03-report#p1@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d0-02-b#p2@T1 8.s5-d3-t1-05-report#p3@T1 9.s7-d2-t1-04-data#p2@T1 10.s3-d1-01-report#p3@T1
- 混合前 10：1.s3-d1-t1-91-quote#p1@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d0-03-report#p1@T1 4.s3-d1-t1-91-quote#p2@T1 5.s3-d3-01-report#p1@T1 6.s3-d1-t1-91-quote#p3@T1 7.s3-d0-03-memo#p1@T1 8.s3-d0-04-memo#p1@T1 9.s3-d0-03-memo#p2@T1 10.s3-d1-01-report#p3@T1
- 重排前 10：1.s3-d1-t1-91-quote#p1@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p1@T1 7.s3-d0-03-memo#p1@T1 8.s3-d0-04-memo#p1@T1 9.s3-d0-03-memo#p2@T1 10.s3-d1-01-report#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 178. `r4n-s3-d1-t1-91-qb`

- 问：两份材料给竞品E标准版标的年价不一样，分别是多少，哪份更可信？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-pricesheet#p1@T1；s3-d1-t1-91-quote#p1@T1
- 金标要点：竞品E的标准版年费为3600元；把标准版年费调整为4200元
- 词法前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s7-d3-t1-05-synthetic#p2@T1 5.s6-d1-t1-91-patch#p1@T1 6.s6-d3-t1-01-report#p2@T1 7.s6-d3-t1-02-report#p3@T1 8.s3-d1-t1-91-quote#p3@T1 9.s3-d1-t1-91-pricesheet#p2@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p1@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d2-t1-91-contract#p2@T1
- 重排前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d3-01-report#p1@T1 8.s3-d3-01-report#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d2-t1-91-contract#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 179. `r4n-s3-d1-t1-91-qc`

- 问：竞品E标准版一个账号最多能开几个座位？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-quote#p2@T1
- 金标要点：标准版单账号席位上限为25个
- 词法前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.p1-colaw-oneperson#p1@T1 7.s7-d0-t1-02-memo#p2@T1 8.s3-d0-02-b#p2@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s3-d1-01-report#p3@T1
- 混合前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-01-report#p3@T1 6.s6-d3-t1-02-report#p1@T1 7.s3-d3-01-report#p1@T1 8.s5-d2-t1-91-digest#p3@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d0-01-memo#p1@T1
- 重排前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d1-01-report#p3@T1 7.s6-d3-t1-02-report#p1@T1 8.s3-d3-01-report#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s3-d0-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 180. `r4n-s4-d2-t1-91-qa`

- 问：每单履约到底要花多少成本？财务那边怎么认定的？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-review#p1@T1
- 金标要点：单票履约成本应修正为7.4元
- 词法前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s2-d0-02-report#p3@T1 4.s4-d0-t1-02-report#p3@T1 5.s4-d2-t1-04-summary#p3@T1 6.s2-d3-t1-91-minutes#p3@T1 7.s4-d0-t1-02-plan#p1@T1 8.s4-d2-t1-04-report#p1@T1 9.s1-d0-03-report#p3@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s6-d0-t1-03-memo#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s6-d0-t1-03-memo#p1@T1 6.s2-d0-02-report#p3@T1 7.s2-d3-t1-91-minutes#p3@T1 8.s1-d0-02-report#p3@T1 9.p1-colaw-capital#p1@T1 10.s1-d0-01-memo#p3@T1
- 重排前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d0-t1-03-memo#p1@T1 5.s2-d0-02-report#p3@T1 6.s2-d3-t1-91-minutes#p3@T1 7.s6-d0-t1-03-memo#p3@T1 8.s1-d0-02-report#p3@T1 9.p1-colaw-capital#p1@T1 10.s1-d0-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 181. `r4n-s4-d2-t1-91-qb`

- 问：v3模型和财务复核给的每单履约成本差了多少，为什么不一样？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-model-v3#p1@T1；s4-d2-t1-91-review#p1@T1
- 金标要点：单票履约成本应修正为7.4元；单票履约成本为6.8元；漏计包材费用
- 词法前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s4-d0-t1-02-report#p3@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-summary#p3@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d0-t1-02-memo#p1@T1 10.s4-d2-t1-91-review#p2@T1
- 混合前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-91-review#p2@T1 5.s6-d0-t1-03-memo#p2@T1 6.s4-d2-t1-04-report#p1@T1 7.s4-d0-t1-02-memo#p1@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d2-t1-04-memo#p2@T1 10.s4-d0-t1-02-analysis#p1@T1
- 重排前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s4-d0-t1-02-memo#p1@T1 6.s6-d0-t1-03-memo#p2@T1 7.s6-d0-t1-03-internal#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d2-t1-91-review#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 182. `r4n-s4-d2-t1-91-qc`

- 问：复核时用的退货率是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-review#p2@T1
- 金标要点：退货率参数取4.1%
- 词法前 10：1.s4-d2-t1-91-review#p2@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.s6-d0-t1-91-sop#p2@T1 4.s4-d2-t1-91-review#p1@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d2-t1-91-review#p3@T1 7.s2-d0-01-report#p1@T1 8.s7-d3-t1-05-memo#p2@T1 9.s4-d0-t1-91-deck#p2@T1 10.s1-d1-t1-91-memo#p2@T1
- 混合前 10：1.s4-d2-t1-91-review#p2@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.s4-d2-t1-91-review#p1@T1 4.s4-d0-t1-02-guide#p2@T1 5.s6-d0-t1-91-sop#p2@T1 6.s2-d0-02-report#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s4-d2-t1-91-review#p3@T1 9.s2-d0-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s4-d2-t1-91-model-v3#p2@T1 2.s4-d2-t1-91-review#p2@T1 3.s6-d0-t1-91-sop#p2@T1 4.s4-d0-t1-02-guide#p2@T1 5.s2-d0-02-report#p3@T1 6.s1-d1-t1-91-memo#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s4-d0-t1-91-deck#p2@T1 9.s4-d2-t1-91-review#p1@T1 10.s4-d2-t1-91-review#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 183. `r4n-s6-d3-t1-91-qa`

- 问：住户收入的新统计口径到底哪天开始用？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-notice#p1@T1
- 金标要点：新口径的启用时间推迟到6月1日
- 词法前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s1-d1-t1-91-brief#p2@T1 3.s6-d3-t1-91-notice#p1@T1 4.s6-d0-t1-01-patch#p1@T1 5.s4-d0-t1-91-eval#p1@T1 6.s3-d2-01-competitor-pricing#p2@T1 7.s3-d0-01-report#p2@T1 8.s1-d2-01-analysis#p3@T1 9.s5-d3-t1-05-memo#p3@T1 10.s5-d2-t1-91-digest#p1@T1
- 混合前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s6-d3-t1-91-notice#p1@T1 3.s5-d2-t1-91-digest#p1@T1 4.s6-d1-c2-memo#p3@T1 5.s5-d3-t1-05-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.s1-d1-t1-91-brief#p2@T1 8.s1-d0-02-report#p3@T1 9.s1-d0-01-analysis#p3@T1 10.s6-d0-t1-01-patch#p1@T1
- 重排前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s6-d3-t1-91-notice#p1@T1 3.s5-d3-t1-05-memo#p3@T1 4.s5-d2-t1-91-digest#p1@T1 5.s6-d1-c2-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.s1-d1-t1-91-brief#p2@T1 8.s6-d0-t1-01-patch#p1@T1 9.s1-d0-02-report#p3@T1 10.s1-d0-01-analysis#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 184. `r4n-s6-d3-t1-91-qb`

- 问：新收入口径的启用日期，变更日志和执行通知各写的是哪天？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-changelog#p1@T1；s6-d3-t1-91-notice#p1@T1
- 金标要点：新口径的启用时间推迟到6月1日；自5月1日起启用
- 词法前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.p1-colaw-capital-call#p2@T1 4.p1-colaw-capital#p4@T1 5.s6-d3-t1-91-notice#p3@T1 6.p1-colaw-governance#p1@T1 7.s6-d3-t1-03-memo#p3@T1 8.p1-colaw-equity#p3@T1 9.s3-d0-01-report#p2@T1 10.s6-d3-t1-03-memo#p2@T1
- 混合前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-memo#p3@T1 6.s6-d3-t1-02-memo#p2@T1 7.s6-d3-t1-91-notice#p3@T1 8.s6-d2-g2-memo#p2@T1 9.p1-colaw-capital-call#p2@T1 10.s6-d1-c1-memo#p1@T1
- 重排前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-memo#p3@T1 6.s6-d2-g2-memo#p2@T1 7.p1-colaw-capital-call#p2@T1 8.s6-d3-t1-02-memo#p2@T1 9.s6-d3-t1-91-notice#p3@T1 10.s6-d1-c1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 185. `r4n-s6-d3-t1-91-qc`

- 问：这一期调查一共抽了多少户？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-notice#p2@T1
- 金标要点：本期样本户数为1.2万户
- 词法前 10：1.s6-d1-t1-91-release#p2@T1 2.s5-d3-t1-05-memo#p1@T1 3.s7-d0-t1-02-report#p2@T1 4.s5-d1-t1-03-memo#p1@T1 5.s6-d2-t1-91-bulletin#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s7-d3-t1-05-memo#p2@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s7-d2-t1-04-data#p1@T1 10.p2-gdp-national#p1@T1
- 混合前 10：1.s6-d3-t1-91-changelog#p2@T1 2.s4-d0-t1-91-deck#p2@T1 3.s2-d0-t1-91-memo#p2@T1 4.s5-d1-t1-03-memo#p2@T1 5.s5-d1-t1-03-memo#p1@T1 6.s5-d2-t1-91-digest#p3@T1 7.s6-d2-t1-91-bulletin#p2@T1 8.s6-d3-t1-91-changelog#p3@T1 9.s5-d3-t1-05-memo#p1@T1 10.p2-gdp-national#p1@T1
- 重排前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d3-t1-05-memo#p1@T1 3.s6-d3-t1-91-changelog#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.s2-d0-t1-91-memo#p2@T1 6.s5-d1-t1-03-memo#p2@T1 7.s5-d2-t1-91-digest#p3@T1 8.s6-d2-t1-91-bulletin#p2@T1 9.s6-d3-t1-91-changelog#p3@T1 10.p2-gdp-national#p1@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 186. `r4n-s1-d1-t1-91-qa`

- 问：我们在印尼的电子支付牌照现在是什么状态？还需要借别人的通道吗？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-brief#p1@T1
- 金标要点：该电子支付牌照已于8月获批；无需再借合作方通道
- 词法前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s5-d2-t1-91-digest#p3@T1 4.s2-d0-t1-91-interview#p3@T1 5.s5-d0-t1-02-summary#p3@T1 6.s6-d3-t1-91-changelog#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s6-d0-t1-91-sop#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.s7-d2-t1-04-claim#p2@T1
- 混合前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s6-d3-t1-91-changelog#p3@T1 4.s6-d1-c4-memo#p1@T1 5.s7-d2-t1-04-claim#p2@T1 6.s6-d0-t1-91-sop#p1@T1 7.p1-cac-o16#p9@T1 8.p1-cac-o16#p4@T1 9.s1-d0-04-risk#p2@T1 10.p1-colaw-capital-transition#p2@T1
- 重排前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d2-t1-04-claim#p2@T1 4.s6-d0-t1-91-sop#p1@T1 5.p1-cac-o16#p9@T1 6.p1-colaw-capital-transition#p2@T1 7.s6-d3-t1-91-changelog#p3@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o16#p4@T1 10.s1-d0-04-risk#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 187. `r4n-s1-d1-t1-91-qb`

- 问：印尼支付牌照这件事，进入备忘和监管简报的说法有什么冲突？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-memo#p1@T1；s1-d1-t1-91-brief#p1@T1
- 金标要点：该电子支付牌照已于8月获批；电子支付牌照申请仍在审理中；需要借用合作方通道；无需再借合作方通道
- 词法前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s1-d1-t1-91-memo#p3@T1 4.p1-colaw-equity#p1@T1 5.s6-d3-t1-01-memo#p3@T1 6.s6-d3-t1-01-note#p3@T1 7.s6-d3-t1-01-report#p3@T1 8.s7-d0-t1-02-memo#p2@T1 9.s1-d1-t1-91-brief#p3@T1 10.p1-colaw-oneperson#p2@T1
- 混合前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d0-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p2@T1 5.s6-d3-t1-01-memo#p2@T1 6.s1-d1-t1-91-brief#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d3-t1-01-report#p2@T1 9.s6-d3-t1-01-note#p3@T1 10.s6-d2-g2-memo#p2@T1
- 重排前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d0-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p2@T1 5.s6-d3-t1-01-memo#p2@T1 6.s1-d1-t1-91-brief#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d3-t1-01-note#p3@T1 9.s6-d2-g2-memo#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 188. `r4n-s1-d1-t1-91-qc`

- 问：这个季度用户退款平均几天能到账？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-brief#p2@T1
- 金标要点：本季度平均退款到账时长为2.6天
- 词法前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s4-d0-t1-91-eval#p2@T1 4.s1-d1-01-analysis#p1@T1 5.s3-d0-02-a#p1@T1 6.s6-d0-t1-91-change#p3@T1 7.s6-d0-t1-91-sop#p3@T1 8.s6-d0-t1-91-change#p1@T1 9.s6-d0-t1-91-sop#p1@T1 10.s5-d2-t1-91-annual#p3@T1
- 混合前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s6-d0-t1-91-sop#p1@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s4-d0-t1-91-eval#p2@T1 6.s4-d2-t1-91-review#p2@T1 7.s3-d0-02-a#p1@T1 8.s1-d0-03-report#p3@T1 9.s6-d0-t1-91-change#p1@T1 10.s6-d3-t1-91-notice#p1@T1
- 重排前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s4-d0-t1-91-eval#p2@T1 4.s3-d0-02-a#p1@T1 5.s6-d0-t1-91-sop#p1@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s4-d2-t1-91-review#p2@T1 8.s1-d0-03-report#p3@T1 9.s6-d0-t1-91-change#p1@T1 10.s6-d3-t1-91-notice#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 189. `r4n-s5-d2-t1-91-qa`

- 问：这个本地生活平台按最新年报有多少家在营商户？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-annual#p1@T1
- 金标要点：截至年末活跃商户为53万家
- 词法前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s2-d0-01-report#p2@T1 4.s2-d1-01-memo#p1@T1 5.s5-d2-t1-91-digest#p1@T1 6.s5-d2-t1-91-annual#p3@T1 7.p1-colaw-oneperson#p2@T1 8.s5-d1-t1-03-report#p3@T1 9.s1-d1-t1-91-memo#p3@T1 10.s4-d2-t1-91-model-v3#p3@T1
- 混合前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p3@T1 5.s2-d1-01-memo#p1@T1 6.s2-d0-01-report#p2@T1 7.s6-d3-t1-91-changelog#p2@T1 8.p1-colaw-oneperson#p2@T1 9.s3-d1-t1-91-quote#p2@T1 10.s2-d0-01-memo#p3@T1
- 重排前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p3@T1 5.s2-d1-01-memo#p1@T1 6.s2-d0-01-report#p2@T1 7.p1-colaw-oneperson#p2@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s3-d1-t1-91-quote#p2@T1 10.s2-d0-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 190. `r4n-s5-d2-t1-91-qb`

- 问：汇编和年报给出的平台活跃商户规模各是多少？汇编的数为什么不能直接用？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-digest#p1@T1；s5-d2-t1-91-annual#p1@T1
- 金标要点：截至年末活跃商户为53万家；该平台活跃商户约48万家；源自两年前的媒体报道
- 词法前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d2-t1-91-digest#p3@T1 5.s6-d3-t1-01-note#p2@T1 6.s1-d1-t1-91-memo#p3@T1 7.s6-d3-t1-02-report#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d3-t1-01-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 混合前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d2-t1-91-digest#p3@T1 5.s5-d1-t1-03-summary#p2@T1 6.s5-d2-t1-91-annual#p2@T1 7.s5-d0-t1-02-analysis#p2@T1 8.s5-d1-t1-03-report#p2@T1 9.s6-d3-t1-01-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 重排前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d2-t1-91-digest#p3@T1 7.s5-d2-t1-91-annual#p2@T1 8.s5-d0-t1-02-analysis#p2@T1 9.s5-d1-t1-03-report#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 191. `r4n-s5-d2-t1-91-qc`

- 问：平台商户一年下来的留存比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-annual#p2@T1
- 金标要点：年度商户留存率为71%
- 词法前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p1@T1 5.s2-d0-02-memo#p2@T1 6.s1-d1-t1-91-memo#p3@T1 7.s2-d0-t1-91-memo#p1@T1 8.s2-d0-01-report#p1@T1 9.p1-colaw-governance-supervisor#p3@T1 10.p1-colaw-governance-supervisor-js#p1@T1
- 混合前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-annual#p1@T1 4.s5-d2-t1-91-digest#p1@T1 5.s2-d0-01-report#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.s5-d2-t1-91-annual#p3@T1 8.s2-d0-t1-91-interview#p1@T1 9.s2-d1-01-memo#p1@T1 10.s1-d0-02-report#p1@T1
- 重排前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-digest#p1@T1 3.s5-d2-t1-91-annual#p2@T1 4.s5-d2-t1-91-annual#p1@T1 5.s2-d0-01-report#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.s2-d0-t1-91-interview#p1@T1 8.s2-d1-01-memo#p1@T1 9.s5-d2-t1-91-annual#p3@T1 10.s1-d0-02-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 192. `r4n-s2-d2-t0-91-qa`

- 问：这批包装材料最后确认几天能交货？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-email#p1@T0
- 金标要点：交期更正为14天
- 词法前 10：1.s2-d2-t0-91-email#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.s2-d2-t0-91-email#p3@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s1-d1-01-memo#p2@T0 8.s1-d0-05-warn#p3@T0 9.s1-d0-05-memo#p3@T0 10.s2-d2-01-report#p1@T0
- 混合前 10：1.s2-d2-t0-91-email#p1@T0 2.s2-d2-t0-91-callnotes#p1@T0 3.s2-d2-t0-91-email#p3@T0 4.s1-d1-01-memo#p2@T0 5.s1-d0-05-memo#p3@T0 6.s2-d0-04-memo#p2@T0 7.s1-d0-03-memo#p1@T0 8.s2-d0-03-memo#p3@T0 9.s1-d0-05-warn#p3@T0 10.s2-d2-01-report#p1@T0
- 重排前 10：1.s2-d2-t0-91-email#p1@T0 2.s2-d2-t0-91-callnotes#p1@T0 3.s2-d2-t0-91-email#p3@T0 4.s1-d1-01-memo#p2@T0 5.s1-d0-05-memo#p3@T0 6.s2-d0-04-memo#p2@T0 7.s1-d0-03-memo#p1@T0 8.s2-d0-03-memo#p3@T0 9.s1-d0-05-warn#p3@T0 10.s2-d2-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 193. `r4n-s2-d2-t0-91-qb`

- 问：包装材料交期，电话里说的和邮件里确认的各是几天？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-callnotes#p1@T0；s2-d2-t0-91-email#p1@T0
- 金标要点：交期更正为14天；交期为10天
- 词法前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s2-d2-t0-91-callnotes#p2@T0 4.s7-d0-t0-01-internal#p1@T0 5.s5-d1-t0-91-repost#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s2-d2-t0-91-email#p3@T0 8.s7-d1-t0-03-fact#p3@T0 9.s2-d2-t0-91-email#p2@T0 10.s2-d3-01-memo#p1@T0
- 混合前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s2-d2-t0-91-email#p3@T0 4.s2-d2-t0-91-email#p2@T0 5.s7-d1-t0-03-memo#p2@T0 6.p1-cac-o11#p13@T0 7.s2-d2-t0-91-callnotes#p2@T0 8.s1-d0-03-memo#p1@T0 9.s7-d0-t0-01-internal#p1@T0 10.s5-d1-t0-91-repost#p2@T0
- 重排前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s2-d2-t0-91-callnotes#p2@T0 5.s7-d0-t0-01-internal#p1@T0 6.s2-d2-t0-91-email#p2@T0 7.p1-cac-o11#p13@T0 8.s1-d0-03-memo#p1@T0 9.s5-d1-t0-91-repost#p2@T0 10.s2-d2-t0-91-email#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 194. `r4n-s2-d2-t0-91-qc`

- 问：这一批货抽检的次品比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-email#p2@T0
- 金标要点：本批抽检不良率为0.9%
- 词法前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.p1-colaw-governance-supervisor-js#p1@T0 3.p1-colaw-governance-supervisor#p1@T0 4.s2-d2-t0-91-callnotes#p1@T0 5.p1-colaw-equity#p2@T0 6.s2-d2-t0-91-email#p2@T0 7.s7-d1-t0-03-memo#p2@T0 8.s1-d1-01-analysis#p3@T0 9.s1-d0-04-memo#p3@T0 10.s5-d0-t0-01-analysis#p2@T0
- 混合前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.s2-d2-t0-91-email#p2@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.p2-gdp-national#p2@T0 5.p1-colaw-governance-supervisor-js#p1@T0 6.s4-d0-t0-01-report#p2@T0 7.s5-d2-t0-04-analysis#p1@T0 8.p2-gdp-national#p1@T0 9.s5-d1-t0-91-repost#p1@T0 10.p1-colaw-governance-supervisor#p1@T0
- 重排前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.s2-d2-t0-91-email#p2@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.p2-gdp-national#p2@T0 5.p1-colaw-governance-supervisor-js#p1@T0 6.p2-gdp-national#p1@T0 7.p1-colaw-governance-supervisor#p1@T0 8.s4-d0-t0-01-report#p2@T0 9.s5-d2-t0-04-analysis#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 195. `r4n-s3-d0-t0-91-qa`

- 问：竞品H客服坐席现在每个席位每月什么价？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-pricing#p1@T0
- 金标要点：当前标价为每席每月52美元
- 词法前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d0-t0-91-flyer#p3@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d2-01-competitor-pricing#p3@T0 6.s3-d0-02-a#p1@T0 7.s3-d0-02-b#p2@T0 8.s3-d0-01-report#p2@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s3-d0-04-memo#p2@T0
- 混合前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d2-01-competitor-pricing#p3@T0 4.s3-d0-03-report#p1@T0 5.s3-d0-01-memo#p1@T0 6.s3-d0-01-memo#p2@T0 7.s3-d1-01-memo#p1@T0 8.s3-d0-03-memo#p1@T0 9.s3-d0-04-memo#p2@T0 10.s3-d2-01-competitor-pricing#p1@T0
- 重排前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d2-01-competitor-pricing#p3@T0 3.s3-d0-t0-91-pricing#p1@T0 4.s3-d0-03-report#p1@T0 5.s3-d0-01-memo#p1@T0 6.s3-d0-01-memo#p2@T0 7.s3-d1-01-memo#p1@T0 8.s3-d0-03-memo#p1@T0 9.s3-d0-04-memo#p2@T0 10.s3-d2-01-competitor-pricing#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 196. `r4n-s3-d0-t0-91-qb`

- 问：竞品H坐席价格，传单和官网标的不一样，各是多少、差在哪？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-flyer#p1@T0；s3-d0-t0-91-pricing#p1@T0
- 金标要点：当前标价为每席每月52美元；传单价格为上一季度活动价；每席每月45美元
- 词法前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-flyer#p3@T0 3.s3-d0-t0-91-pricing#p1@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d0-04-memo#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s3-d1-01-report#p2@T0 8.s3-d0-t0-91-pricing#p2@T0 9.p1-colaw-governance-supervisor-js#p2@T0 10.s3-d0-01-report#p3@T0
- 混合前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d0-01-memo#p1@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d2-01-competitor-pricing#p1@T0 6.s3-d1-01-report#p2@T0 7.s3-d0-03-report#p3@T0 8.s3-d0-04-memo#p2@T0 9.s3-d0-01-report#p3@T0 10.s3-d3-01-memo#p3@T0
- 重排前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d0-01-memo#p1@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d2-01-competitor-pricing#p1@T0 6.s3-d1-01-report#p2@T0 7.s3-d0-03-report#p3@T0 8.s3-d0-04-memo#p2@T0 9.s3-d0-01-report#p3@T0 10.s3-d3-01-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 197. `r4n-s3-d0-t0-91-qc`

- 问：新团队注册竞品H能免费试多久？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-pricing#p2@T0
- 金标要点：可获得14天免费试用
- 词法前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d0-t0-91-flyer#p3@T0 4.s3-d2-01-competitor-pricing#p2@T0 5.s3-d0-t0-91-flyer#p1@T0 6.s3-d0-03-memo#p2@T0 7.s4-d1-t0-03-analysis#p1@T0 8.s3-d0-03-report#p2@T0 9.s3-d1-01-report#p3@T0 10.s2-d0-03-memo#p3@T0
- 混合前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d2-01-competitor-pricing#p2@T0 4.s3-d0-03-report#p2@T0 5.s3-d0-03-memo#p2@T0 6.s3-d1-01-report#p3@T0 7.s3-d3-01-memo#p3@T0 8.s3-d0-t0-91-flyer#p1@T0 9.s3-d1-01-report#p1@T0 10.s3-d0-01-memo#p3@T0
- 重排前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d2-01-competitor-pricing#p2@T0 4.s3-d0-03-memo#p2@T0 5.s3-d0-03-report#p2@T0 6.s3-d1-01-report#p3@T0 7.s3-d3-01-memo#p3@T0 8.s3-d0-t0-91-flyer#p1@T0 9.s3-d0-01-memo#p3@T0 10.s3-d1-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 198. `r4n-s4-d0-t1-91-qa`

- 问：工单自动分派用全量数据复评后准确率是多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-eval#p1@T1
- 金标要点：自动分派准确率为86%
- 词法前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-eval#p3@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s4-d0-t1-02-guide#p2@T1 7.p1-cac-o11#p12@T1 8.s2-d3-t1-91-minutes#p1@T1 9.s7-d0-t1-02-brief#p2@T1 10.s7-d2-t1-04-claim#p2@T1
- 混合前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.p1-cac-o11#p12@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d0-t1-91-eval#p3@T1 7.s4-d2-t1-04-internal#p1@T1 8.s2-d0-t1-91-memo#p2@T1 9.s4-d2-t1-91-model-v3#p2@T1 10.s7-d2-t1-04-memo#p2@T1
- 重排前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d0-t1-91-eval#p3@T1 7.s7-d2-t1-04-memo#p2@T1 8.p1-cac-o11#p12@T1 9.s4-d2-t1-04-internal#p1@T1 10.s2-d0-t1-91-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 199. `r4n-s4-d0-t1-91-qb`

- 问：自动分派准确率，汇报材料和复评报告各报了多少？哪个是小样本？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-deck#p1@T1；s4-d0-t1-91-eval#p1@T1
- 金标要点：自动分派准确率为86%；准确率达到92%；只来自早期小样本
- 词法前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p3@T1 5.s4-d0-t1-91-deck#p2@T1 6.s7-d2-t1-04-memo#p3@T1 7.p1-cac-o11#p12@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d2-t1-04-brief#p1@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.p1-cac-o11#p12@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-report#p1@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s7-d2-t1-04-memo#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 重排前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.s4-d2-t1-04-report#p1@T1 6.s7-d2-t1-04-memo#p2@T1 7.p1-cac-o11#p12@T1 8.s4-d0-t1-02-guide#p2@T1 9.s6-d3-t1-91-changelog#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 200. `r4n-s4-d0-t1-91-qc`

- 问：上了自动分派以后，一张工单平均多久处理完？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-eval#p2@T1
- 金标要点：工单平均处理时长下降到18分钟
- 词法前 10：1.s4-d0-t1-91-eval#p2@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p1@T1 4.s1-d1-t1-91-brief#p2@T1 5.s4-d0-t1-91-deck#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s1-d1-01-analysis#p1@T1 8.s3-d3-01-memo#p2@T1 9.s6-d3-t1-91-changelog#p2@T1 10.s4-d2-t1-04-report#p3@T1
- 混合前 10：1.s4-d0-t1-91-eval#p2@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p1@T1 4.s2-d0-t1-91-memo#p2@T1 5.s4-d0-t1-91-deck#p2@T1 6.s1-d1-t1-91-brief#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s4-d0-t1-02-guide#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d2-t1-04-report#p3@T1
- 重排前 10：1.s4-d0-t1-91-eval#p2@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p1@T1 4.s2-d0-t1-91-memo#p2@T1 5.s4-d0-t1-91-deck#p2@T1 6.s1-d1-t1-91-brief#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s4-d0-t1-02-guide#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d2-t1-04-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 201. `r4n-s6-d1-t1-91-qa`

- 问：老的v1接口最终什么时候停？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-patch#p1@T1
- 金标要点：下线时间延期至11月30日
- 词法前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-patch#p2@T1 5.s6-d1-t1-91-release#p2@T1 6.s4-d2-t1-04-summary#p3@T1 7.s6-d3-t1-02-memo#p3@T1 8.p1-cac-o11#p12@T1 9.p2-gdp-national#p3@T1 10.s4-d0-t1-02-memo#p3@T1
- 混合前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s6-d1-t1-91-patch#p2@T1 6.s2-d3-01-memo#p3@T1 7.s4-d0-t1-02-memo#p3@T1 8.s6-d3-t1-02-memo#p3@T1 9.s6-d3-t1-91-notice#p1@T1 10.s4-d2-t1-04-summary#p3@T1
- 重排前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s6-d1-t1-91-patch#p2@T1 6.s6-d3-t1-02-memo#p3@T1 7.s4-d2-t1-04-summary#p3@T1 8.s2-d3-01-memo#p3@T1 9.s4-d0-t1-02-memo#p3@T1 10.s6-d3-t1-91-notice#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 202. `r4n-s6-d1-t1-91-qb`

- 问：v1接口下线时间，发布说明和补丁公告分别怎么写的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-release#p1@T1；s6-d1-t1-91-patch#p1@T1
- 金标要点：下线时间延期至11月30日；将于9月30日下线
- 词法前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p3@T1 5.s6-d1-t1-91-patch#p2@T1 6.s5-d0-t1-02-report#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s7-d0-t1-02-report#p3@T1 9.p2-gdp-national#p3@T1 10.s3-d2-t1-91-brochure#p1@T1
- 混合前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s1-d0-01-analysis#p3@T1 6.s6-d3-t1-02-memo#p1@T1 7.s6-d1-t1-91-patch#p2@T1 8.s3-d2-t1-91-brochure#p1@T1 9.s6-d3-t1-02-report#p1@T1 10.s6-d3-t1-03-report#p1@T1
- 重排前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p3@T1 5.s6-d1-t1-91-patch#p2@T1 6.s1-d0-01-analysis#p3@T1 7.s6-d3-t1-02-memo#p1@T1 8.s3-d2-t1-91-brochure#p1@T1 9.s6-d3-t1-02-report#p1@T1 10.s6-d3-t1-03-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 203. `r4n-s6-d1-t1-91-qc`

- 问：v2接口最近一周调用成功的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-patch#p2@T1
- 金标要点：上周v2接口调用成功率为99.2%
- 词法前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s4-d2-t1-91-model-v3#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.p1-colaw-governance-supervisor#p3@T1 8.p1-colaw-governance-supervisor-js#p1@T1 9.s1-d3-01-memo#p2@T1 10.s6-d1-t1-91-patch#p1@T1
- 混合前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s6-d1-t1-91-patch#p1@T1 6.s4-d0-t1-02-memo#p3@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-01-report#p1@T1 9.s4-d2-t1-04-summary#p3@T1 10.s2-d3-01-memo#p3@T1
- 重排前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s6-d1-t1-91-patch#p1@T1 6.s4-d0-t1-91-deck#p2@T1 7.s4-d2-t1-04-summary#p3@T1 8.s4-d0-t1-02-memo#p3@T1 9.s2-d0-01-report#p1@T1 10.s2-d3-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 204. `r4n-s1-d3-t0-91-qa`

- 问：本季度出口同比增长按修订后的数是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-statbrief#p1@T0
- 金标要点：本季度出口同比增速为5.4%
- 词法前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s2-d1-01-report#p3@T0 4.s1-d3-t0-91-statbrief#p2@T0 5.s1-d3-t0-91-statbrief#p3@T0 6.s2-d0-02-report#p2@T0 7.s5-d2-t0-04-report#p2@T0 8.s4-d3-t0-05-report#p1@T0 9.s4-d3-t0-91-method#p1@T0 10.s2-d1-01-report#p2@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s2-d1-01-report#p3@T0 4.s1-d3-t0-91-statbrief#p3@T0 5.s2-d0-02-report#p1@T0 6.s1-d3-t0-91-statbrief#p2@T0 7.s2-d0-02-report#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s3-d0-t0-91-pricing#p1@T0 10.s1-d2-01-report#p1@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s2-d1-01-report#p3@T0 4.s1-d3-t0-91-statbrief#p3@T0 5.s2-d0-02-report#p1@T0 6.s1-d3-t0-91-statbrief#p2@T0 7.s2-d0-02-report#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s3-d0-t0-91-pricing#p1@T0 10.s1-d2-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 205. `r4n-s1-d3-t0-91-qb`

- 问：出口增速，研判备忘和统计快报各用的是多少？哪个是修订后的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-memo#p1@T0；s1-d3-t0-91-statbrief#p1@T0
- 金标要点：本季度出口同比增速为6.1%；本季度出口同比增速为5.4%；比初步数下调0.7个百分点
- 词法前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s1-d3-t0-91-statbrief#p3@T0 4.s2-d2-t0-91-callnotes#p2@T0 5.s1-d1-01-analysis#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s5-d0-t0-01-analysis#p2@T0 8.p1-cac-o11#p16@T0 9.s1-d3-t0-91-memo#p2@T0 10.s7-d0-t0-01-qa#p1@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s1-d3-t0-91-statbrief#p3@T0 4.s1-d3-t0-91-memo#p2@T0 5.s1-d3-t0-91-memo#p3@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d3-t0-91-statbrief#p2@T0 8.s4-d3-t0-91-method#p1@T0 9.p1-cac-o11#p16@T0 10.s4-d0-t0-01-feedback#p1@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.p1-cac-o11#p16@T0 4.s1-d3-t0-91-statbrief#p3@T0 5.s1-d3-t0-91-memo#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s4-d3-t0-91-method#p1@T0 8.s4-d0-t0-01-feedback#p1@T0 9.s1-d3-t0-91-memo#p3@T0 10.s1-d3-t0-91-statbrief#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 206. `r4n-s1-d3-t0-91-qc`

- 问：主要港口的货物吞吐比去年同期增长了多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-statbrief#p2@T0
- 金标要点：主要港口货物吞吐量同比增长3.8%
- 词法前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s2-d0-01-memo#p3@T0 3.s1-d3-t0-91-memo#p2@T0 4.s2-d0-02-report#p1@T0 5.s2-d0-01-report#p1@T0 6.s5-d2-t0-04-analysis#p2@T0 7.s4-d0-t0-01-plan#p2@T0 8.s1-d2-01-report#p1@T0 9.s2-d1-01-report#p3@T0 10.s1-d3-t0-91-statbrief#p1@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s1-d3-t0-91-memo#p2@T0 3.s1-d3-t0-91-statbrief#p1@T0 4.s2-d0-01-memo#p3@T0 5.s1-d2-01-report#p1@T0 6.s1-d0-01-memo#p3@T0 7.s2-d0-02-report#p1@T0 8.s2-d1-01-report#p3@T0 9.s1-d3-t0-91-statbrief#p3@T0 10.s1-d3-t0-91-memo#p3@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s2-d0-01-memo#p3@T0 3.s2-d0-02-report#p1@T0 4.s1-d3-t0-91-memo#p2@T0 5.s1-d2-01-report#p1@T0 6.s1-d0-01-memo#p3@T0 7.s2-d1-01-report#p3@T0 8.s1-d3-t0-91-statbrief#p3@T0 9.s1-d3-t0-91-memo#p3@T0 10.s1-d3-t0-91-statbrief#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 207. `r4n-s5-d1-t0-91-qa`

- 问：按原始调研，本地消费者网购渗透率实际是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d1-t0-91-survey#p1@T0
- 金标要点：线上购物渗透率实测为54%
- 词法前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d2-t0-04-memo#p2@T0 5.s1-d0-01-analysis#p2@T0 6.s4-d3-t0-91-method#p1@T0 7.s1-d1-01-report#p3@T0 8.s3-d1-01-memo#p3@T0 9.s5-d1-t0-91-survey#p3@T0 10.s3-d2-01-quotation-snapshot#p2@T0
- 混合前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d1-t0-91-survey#p3@T0 5.s5-d2-t0-04-memo#p2@T0 6.s2-d0-03-memo#p2@T0 7.s1-d0-02-memo#p1@T0 8.s2-d2-01-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s1-d0-01-memo#p1@T0
- 重排前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d2-t0-04-memo#p2@T0 5.s5-d1-t0-91-survey#p3@T0 6.s2-d0-03-memo#p2@T0 7.s1-d0-02-memo#p1@T0 8.s2-d2-01-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s1-d0-01-memo#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 208. `r4n-s5-d1-t0-91-qb`

- 问：网购渗透率，转述文章和原始调研各说了多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d1-t0-91-repost#p1@T0；s5-d1-t0-91-survey#p1@T0
- 金标要点：线上购物渗透率已经超过六成；线上购物渗透率实测为54%
- 词法前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s5-d2-t0-04-memo#p1@T0 4.s5-d1-t0-91-repost#p3@T0 5.s5-d2-t0-04-report#p3@T0 6.s5-d2-t0-04-memo#p2@T0 7.s7-d0-t0-01-qa#p1@T0 8.s2-d0-04-memo#p1@T0 9.s5-d1-t0-91-repost#p2@T0 10.s7-d1-t0-03-fact#p2@T0
- 混合前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s5-d2-t0-04-memo#p2@T0 4.s2-d0-04-memo#p1@T0 5.s5-d1-t0-91-survey#p3@T0 6.s1-d0-02-memo#p1@T0 7.s1-d0-04-memo#p1@T0 8.s2-d0-03-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s2-d2-01-memo#p2@T0
- 重排前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s5-d2-t0-04-memo#p2@T0 4.s2-d0-04-memo#p1@T0 5.s5-d1-t0-91-survey#p3@T0 6.s1-d0-02-memo#p1@T0 7.s1-d0-04-memo#p1@T0 8.s2-d0-03-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s2-d2-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 209. `r4n-s5-d1-t0-91-qc`

- 问：消费者平均隔多少天会再次下单？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d1-t0-91-survey#p2@T0
- 金标要点：平均复购周期为37天
- 词法前 10：1.s5-d1-t0-91-survey#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s2-d2-t0-91-email#p3@T0 4.s1-d0-01-analysis#p2@T0 5.s5-d1-t0-91-repost#p1@T0 6.s3-d0-t0-91-pricing#p2@T0 7.s2-d2-t0-91-email#p1@T0 8.s2-d2-t0-91-callnotes#p1@T0 9.s2-d1-01-report#p1@T0 10.s7-d1-t0-03-reason#p2@T0
- 混合前 10：1.s5-d1-t0-91-survey#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.s5-d1-t0-91-repost#p1@T0 5.s2-d2-01-report#p2@T0 6.s2-d2-t0-91-email#p1@T0 7.s1-d1-01-analysis#p1@T0 8.s2-d2-t0-91-email#p3@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s2-d1-01-report#p1@T0
- 重排前 10：1.s5-d1-t0-91-survey#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.s5-d1-t0-91-repost#p1@T0 5.s2-d2-01-report#p2@T0 6.s2-d2-t0-91-email#p1@T0 7.s1-d1-01-analysis#p1@T0 8.s2-d2-t0-91-email#p3@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s2-d1-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 210. `r4n-s2-d3-t1-91-qa`

- 问：区域试点今年获批的是几个城市？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-minutes#p1@T1
- 金标要点：会议批准的试点范围是8个城市
- 词法前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s4-d0-t1-91-deck#p2@T1 5.s1-d2-01-report#p1@T1 6.s2-d0-03-memo#p2@T1 7.s1-d1-t1-91-brief#p3@T1 8.s2-d0-02-memo#p2@T1 9.s2-d0-02-interview#p2@T1 10.s5-d1-t1-03-report#p2@T1
- 混合前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d0-02-interview#p2@T1 5.s2-d0-03-memo#p2@T1 6.s1-d2-01-report#p1@T1 7.s1-d1-t1-91-memo#p3@T1 8.s2-d0-02-memo#p2@T1 9.s5-d1-t1-03-report#p2@T1 10.s2-d0-t1-91-interview#p1@T1
- 重排前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d0-03-memo#p2@T1 5.s2-d0-02-memo#p2@T1 6.s5-d1-t1-03-report#p2@T1 7.s2-d0-02-interview#p2@T1 8.s1-d2-01-report#p1@T1 9.s1-d1-t1-91-memo#p3@T1 10.s2-d0-t1-91-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 211. `r4n-s2-d3-t1-91-qb`

- 问：试点城市数量，CEO访谈和董事会纪要说法差在哪？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-interview#p1@T1；s2-d3-t1-91-minutes#p1@T1
- 金标要点：会议批准的试点范围是8个城市；今年会扩到12个城市
- 词法前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.s6-d0-t1-02-report#p1@T1 7.s6-d0-t1-02-memo#p1@T1 8.s6-d0-t1-02-internal#p1@T1 9.s1-d2-01-report#p1@T1 10.s1-d1-t1-91-memo#p3@T1
- 混合前 10：1.s2-d3-t1-91-minutes#p1@T1 2.s2-d3-t1-91-interview#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.p1-colaw-governance-board#p4@T1 7.p1-colaw-governance-board#p3@T1 8.s1-d2-01-report#p1@T1 9.s2-d0-03-memo#p2@T1 10.s2-d0-t1-91-interview#p1@T1
- 重排前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.s2-d0-t1-91-interview#p1@T1 7.p1-colaw-governance-board#p4@T1 8.p1-colaw-governance-board#p3@T1 9.s1-d2-01-report#p1@T1 10.s2-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 212. `r4n-s2-d3-t1-91-qc`

- 问：每个试点城市最多能拿多少补贴？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-minutes#p2@T1
- 金标要点：每城试点补贴上限为300万元
- 词法前 10：1.s2-d3-t1-91-interview#p2@T1 2.s2-d3-t1-91-minutes#p2@T1 3.s2-d3-t1-91-minutes#p1@T1 4.s2-d3-t1-91-minutes#p3@T1 5.s2-d3-t1-91-interview#p1@T1 6.s1-d2-01-report#p1@T1 7.s2-d0-03-memo#p2@T1 8.s1-d1-t1-91-memo#p3@T1 9.s5-d2-t1-91-annual#p3@T1 10.s4-d0-t1-91-deck#p2@T1
- 混合前 10：1.s2-d3-t1-91-minutes#p2@T1 2.s2-d3-t1-91-interview#p2@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s2-d3-t1-91-interview#p1@T1 6.s2-d3-01-interview#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-02-interview#p2@T1 9.s1-d1-t1-91-memo#p3@T1 10.s1-d2-01-report#p1@T1
- 重排前 10：1.s2-d3-t1-91-minutes#p2@T1 2.s2-d3-t1-91-interview#p2@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s2-d3-t1-91-interview#p1@T1 6.s2-d3-01-interview#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-02-interview#p2@T1 9.s1-d1-t1-91-memo#p3@T1 10.s1-d2-01-report#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 213. `r4n-s3-d2-t1-91-qa`

- 问：竞品G的合规模块按合同到底收不收钱？多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-contract#p1@T1
- 金标要点：合规模块单独计费每月800元
- 词法前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p2@T1 3.s3-d2-t1-91-contract#p1@T1 4.s3-d2-t1-91-brochure#p3@T1 5.s6-d1-c3-memo#p2@T1 6.s3-d2-t1-91-brochure#p2@T1 7.s3-d1-t1-91-quote#p1@T1 8.s2-d0-t1-91-memo#p1@T1 9.s3-d2-01-quotation-snapshot#p2@T1 10.s3-d1-t1-91-pricesheet#p1@T1
- 混合前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d1-01-memo#p3@T1 10.s3-d0-03-report#p1@T1
- 重排前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p2@T1 3.s3-d2-t1-91-contract#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d0-03-report#p1@T1 10.s3-d1-01-report#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 214. `r4n-s3-d2-t1-91-qb`

- 问：竞品G合规模块的收费，宣传册和合同报价单怎么说的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-brochure#p1@T1；s3-d2-t1-91-contract#p1@T1
- 金标要点：合规模块单独计费每月800元；数据合规模块免费附送；只适用于首年促销
- 词法前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-brochure#p3@T1 4.s3-d2-t1-91-brochure#p2@T1 5.s3-d2-t1-91-contract#p2@T1 6.s3-d2-t1-91-contract#p3@T1 7.s2-d0-t1-91-memo#p1@T1 8.s3-d2-01-quotation-snapshot#p2@T1 9.s6-d1-c3-memo#p2@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 混合前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-contract#p2@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d2-t1-91-brochure#p2@T1 6.s3-d2-01-quotation-snapshot#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d2-t1-91-contract#p3@T1 9.s3-d1-01-report#p1@T1 10.s3-d2-t1-91-brochure#p3@T1
- 重排前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-contract#p2@T1 4.s3-d2-t1-91-brochure#p2@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d2-t1-91-brochure#p3@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d2-t1-91-contract#p3@T1 10.s3-d1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 215. `r4n-s3-d2-t1-91-qc`

- 问：竞品G在合同里承诺的服务可用性是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-contract#p2@T1
- 金标要点：SLA承诺为99.95%
- 词法前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-brochure#p3@T1 3.s6-d0-t1-91-sop#p2@T1 4.s2-d0-t1-91-memo#p1@T1 5.s3-d2-t1-91-brochure#p1@T1 6.s3-d2-t1-91-brochure#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s4-d2-t1-04-summary#p2@T1 9.s1-d1-t1-91-memo#p2@T1 10.s2-d0-t1-91-interview#p2@T1
- 混合前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d0-03-memo#p1@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d1-t1-91-pricesheet#p2@T1 5.s3-d0-03-report#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-01-report#p1@T1 8.s3-d0-04-memo#p1@T1 9.s2-d0-t1-91-memo#p1@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 重排前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-brochure#p1@T1 3.s3-d1-t1-91-pricesheet#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d3-01-report#p2@T1 6.s2-d0-t1-91-memo#p1@T1 7.s3-d0-03-memo#p1@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p1@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 216. `r4n-s4-d3-t0-91-qa`

- 问：电力折算标准煤现在该用多大的系数？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-method#p1@T0
- 金标要点：该折算系数应为0.76
- 词法前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s7-d0-t0-01-qa#p2@T0 4.s3-d0-t0-91-flyer#p3@T0 5.s5-d0-t0-01-memo#p3@T0 6.s5-d0-t0-01-summary#p2@T0 7.s7-d1-t0-03-reason#p1@T0 8.s4-d0-t0-01-memo#p2@T0 9.s3-d0-03-report#p2@T0 10.s3-d0-02-a#p2@T0
- 混合前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s1-d0-03-memo#p1@T0 4.s4-d3-t0-05-memo#p3@T0 5.s1-d3-01-memo#p2@T0 6.s4-d3-t0-91-calc#p2@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s2-d2-t0-91-callnotes#p1@T0 10.p1-colaw-capital-transition#p2@T0
- 重排前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s1-d0-03-memo#p1@T0 4.s4-d3-t0-05-memo#p3@T0 5.s1-d3-01-memo#p2@T0 6.s4-d3-t0-91-calc#p2@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s2-d2-t0-91-callnotes#p1@T0 10.p1-colaw-capital-transition#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 217. `r4n-s4-d3-t0-91-qb`

- 问：电力折标煤系数，测算表和方法更新说明各取多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-calc#p1@T0；s4-d3-t0-91-method#p1@T0
- 金标要点：该折算系数应为0.76；系数取0.82
- 词法前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s3-d2-01-quotation-snapshot#p3@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d0-t0-01-qa#p1@T0 8.s7-d1-t0-03-fact#p3@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s1-d1-01-analysis#p2@T0
- 混合前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s4-d3-t0-91-calc#p3@T0 6.s4-d0-t0-01-summary#p1@T0 7.s1-d3-t0-91-statbrief#p3@T0 8.s2-d2-t0-91-email#p1@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d1-t0-03-memo#p1@T0
- 重排前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s4-d0-t0-01-summary#p1@T0 6.s2-d2-t0-91-email#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d1-t0-03-memo#p1@T0 9.s4-d3-t0-91-calc#p3@T0 10.s1-d3-t0-91-statbrief#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 218. `r4n-s4-d3-t0-91-qc`

- 问：今年产线实际利用了多少产能？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-method#p2@T0
- 金标要点：本年度产线利用率为78%
- 词法前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d3-t0-91-method#p2@T0 3.s4-d0-t0-01-summary#p1@T0 4.s1-d0-02-report#p2@T0 5.s7-d0-t0-01-internal#p1@T0 6.s7-d0-t0-01-memo#p1@T0 7.s7-d0-t0-01-arch#p1@T0 8.s2-d0-04-memo#p2@T0 9.s7-d0-t0-01-qa#p2@T0 10.p1-cac-o11#p10@T0
- 混合前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d3-t0-91-method#p2@T0 3.s1-d0-02-report#p2@T0 4.s2-d0-04-memo#p2@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-91-calc#p3@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d1-t0-03-memo#p1@T0 9.s7-d0-t0-01-internal#p1@T0 10.s7-d0-t0-01-arch#p1@T0
- 重排前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d0-t0-01-summary#p1@T0 3.s7-d0-t0-01-internal#p1@T0 4.s7-d0-t0-01-arch#p1@T0 5.s4-d3-t0-91-method#p2@T0 6.s1-d0-02-report#p2@T0 7.s2-d0-04-memo#p2@T0 8.s4-d3-t0-91-calc#p3@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d1-t0-03-memo#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 219. `r4n-s6-d0-t1-91-qa`

- 问：退款多少钱以上才要主管点头？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-change#p1@T1
- 金标要点：退款审批阈值改为500美元以上
- 词法前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s2-d0-t1-91-interview#p2@T1 4.s6-d0-t1-91-change#p3@T1 5.s6-d0-t1-02-internal#p3@T1 6.s6-d0-t1-91-sop#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s1-d1-t1-91-brief#p2@T1 9.p1-colaw-oneperson#p1@T1 10.p1-colaw-oneperson#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d0-t1-91-change#p3@T1 4.s1-d1-t1-91-brief#p2@T1 5.s1-d1-t1-91-memo#p2@T1 6.s6-d0-t1-02-internal#p3@T1 7.s2-d0-t1-91-interview#p2@T1 8.p1-colaw-oneperson#p2@T1 9.p1-colaw-oneperson#p1@T1 10.s6-d0-t1-91-sop#p3@T1
- 重排前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d0-t1-91-change#p3@T1 4.s1-d1-t1-91-brief#p2@T1 5.s1-d1-t1-91-memo#p2@T1 6.s6-d0-t1-02-internal#p3@T1 7.s2-d0-t1-91-interview#p2@T1 8.p1-colaw-oneperson#p2@T1 9.p1-colaw-oneperson#p1@T1 10.s6-d0-t1-91-sop#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 220. `r4n-s6-d0-t1-91-qb`

- 问：退款要主管审批的金额线，手册和变更单各写的是多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-sop#p1@T1；s6-d0-t1-91-change#p1@T1
- 金标要点：金额在300美元以上的退款需要主管审批；退款审批阈值改为500美元以上
- 词法前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d0-t1-91-sop#p3@T1 4.s6-d0-t1-91-sop#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.s1-d1-t1-91-memo#p2@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-colaw-liquidation#p2@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d3-t1-03-memo#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d3-t1-03-memo#p2@T1 4.s6-d0-t1-91-change#p3@T1 5.s1-d1-t1-91-memo#p2@T1 6.s6-d2-g2-memo#p2@T1 7.s6-d0-t1-01-patch#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s6-d0-t1-91-sop#p3@T1
- 重排前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d3-t1-03-memo#p2@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d2-g2-memo#p2@T1 6.s6-d0-t1-01-patch#p2@T1 7.s6-d0-t1-91-sop#p3@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s6-d0-t1-91-change#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 221. `r4n-s6-d0-t1-91-qc`

- 问：客服上个月一次就把问题解决的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-change#p2@T1
- 金标要点：上月首次解决率为74%
- 词法前 10：1.s6-d0-t1-91-sop#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-04-memo#p3@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-03-interview#p3@T1 7.s6-d2-t1-91-audit#p1@T1 8.s6-d2-t1-91-bulletin#p1@T1 9.s1-d3-01-memo#p2@T1 10.s6-d0-t1-91-change#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s6-d0-t1-91-change#p2@T1 4.s2-d0-t1-91-memo#p1@T1 5.s2-d0-02-report#p3@T1 6.s2-d0-t1-91-memo#p2@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d0-t1-91-sop#p1@T1 9.s2-d2-01-report#p2@T1 10.s6-d2-t1-91-bulletin#p1@T1
- 重排前 10：1.s6-d0-t1-91-sop#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s2-d0-t1-91-memo#p1@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d0-t1-91-change#p2@T1 6.s2-d0-02-report#p3@T1 7.s2-d0-t1-91-memo#p2@T1 8.s6-d0-t1-91-sop#p1@T1 9.s6-d2-t1-91-bulletin#p1@T1 10.s2-d2-01-report#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 222. `r4n-s6-d2-t1-91-qa`

- 问：夜班也算进去的话，仓库安检过关的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-audit#p1@T1
- 金标要点：仓库安检通过比例写成百分之九十一
- 词法前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s2-d0-t1-91-memo#p1@T1 4.p1-colaw-governance-supervisor#p1@T1 5.p1-colaw-governance-supervisor#p3@T1 6.p1-colaw-governance-supervisor-js#p1@T1 7.s3-d2-t1-91-contract#p2@T1 8.s6-d2-t1-91-audit#p3@T1 9.p1-colaw-equity#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 混合前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s6-d2-t1-91-audit#p3@T1 4.s2-d0-t1-91-memo#p1@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.p1-colaw-governance-supervisor#p1@T1 8.p1-colaw-governance-supervisor#p3@T1 9.s3-d2-t1-91-contract#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s2-d0-t1-91-memo#p1@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.p1-colaw-governance-supervisor#p1@T1 7.p1-colaw-governance-supervisor#p3@T1 8.s3-d2-t1-91-contract#p2@T1 9.s4-d0-t1-91-deck#p2@T1 10.s6-d2-t1-91-audit#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 223. `r4n-s6-d2-t1-91-qb`

- 问：一份只覆盖白班，另一份把夜班补了进去，过关比例两边分别是什么？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-bulletin#p1@T1；s6-d2-t1-91-audit#p1@T1
- 金标要点：仓库安检通过比例写成百分之九十六；仓库安检通过比例写成百分之九十一
- 词法前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s7-d3-t1-05-memo#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d2-t1-91-digest#p2@T1 6.s7-d2-t1-04-data#p3@T1 7.s7-d2-t1-04-claim#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d2-t1-04-data#p2@T1 10.s7-d2-t1-04-memo#p2@T1
- 混合前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s6-d2-t1-91-audit#p3@T1 4.s7-d2-t1-04-data#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s6-d3-t1-91-changelog#p1@T1 8.s7-d2-t1-04-claim#p2@T1 9.s4-d2-t1-91-review#p3@T1 10.s2-d3-t1-91-interview#p1@T1
- 重排前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s7-d2-t1-04-claim#p2@T1 4.s7-d2-t1-04-data#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s6-d2-t1-91-audit#p3@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s6-d3-t1-91-changelog#p1@T1 9.s4-d2-t1-91-review#p3@T1 10.s2-d3-t1-91-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 224. `r4n-s6-d2-t1-91-qc`

- 问：这个月仓库里工伤报了几起？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-audit#p2@T1
- 金标要点：该月因工受伤为七件
- 词法前 10：1.s6-d2-t1-91-bulletin#p2@T1 2.s6-d1-t1-91-release#p2@T1 3.s6-d2-t1-91-audit#p1@T1 4.s6-d2-t1-91-bulletin#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-t1-91-memo#p1@T1 7.s3-d1-t1-91-quote#p3@T1 8.s6-d0-t1-91-sop#p2@T1 9.s2-d3-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 混合前 10：1.s6-d2-t1-91-bulletin#p2@T1 2.s6-d2-t1-91-audit#p1@T1 3.s6-d2-t1-91-bulletin#p1@T1 4.s2-d0-t1-91-interview#p2@T1 5.s6-d2-t1-91-audit#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s6-d0-t1-91-sop#p2@T1 9.s6-d2-t1-91-audit#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 重排前 10：1.s2-d0-t1-91-interview#p2@T1 2.s6-d2-t1-91-bulletin#p2@T1 3.s6-d2-t1-91-audit#p1@T1 4.s6-d2-t1-91-bulletin#p1@T1 5.s6-d2-t1-91-audit#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s6-d0-t1-91-sop#p2@T1 9.s6-d2-t1-91-audit#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 建议：可议 hybrid
- 理由：混合的前 10 条里有金标，词法没有。

## 词法 vs 重排

### 1. `p1-lx-01-new`

- 问：数据出境安全评估办法规定评估结果有效期为几年？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p13@T0
- 金标要点：通过数据出境安全评估的结果有效期为2年
- 词法前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p5@T0 4.p1-cac-o11#p3@T0 5.p1-cac-o11#p15@T0 6.p1-cac-o11#p11@T0 7.p1-cac-o11#p7@T0 8.p1-cac-o11#p12@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p2@T0
- 混合前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p11@T0 3.p1-cac-o11#p15@T0 4.p1-cac-o11#p5@T0 5.p1-cac-o11#p3@T0 6.p1-cac-o11#p1@T0 7.p1-cac-o11#p12@T0 8.p1-cac-o11#p14@T0 9.p1-cac-o11#p7@T0 10.p1-cac-o11#p17@T0
- 重排前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p11@T0 3.p1-cac-o11#p1@T0 4.p1-cac-o11#p7@T0 5.p1-cac-o11#p15@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p3@T0 8.p1-cac-o11#p14@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p12@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 2. `p1-lx-02-new`

- 问：个人信息出境标准合同办法要求合同生效后多少个工作日内备案？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p6@T0
- 金标要点：在标准合同生效之日起10个工作日内向所在地省级网信部门备案
- 词法前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p7@T0 5.p1-cac-o13#p4@T0 6.p1-cac-o13#p8@T0 7.p1-cac-o13#p2@T0 8.p1-cac-o11#p4@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p15@T0
- 混合前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p8@T0 5.p1-cac-o13#p7@T0 6.p1-cac-o13#p2@T0 7.p1-cac-o11#p17@T0 8.p1-cac-o13#p4@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p6@T0
- 重排前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p4@T0 5.p1-cac-o13#p8@T0 6.p1-cac-o13#p7@T0 7.p1-cac-o13#p2@T0 8.p1-cac-o11#p17@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p6@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 3. `p1-lx-03-new`

- 问：数据出境安全评估办法：省级网信部门收到申报材料后几个工作日内完成完备性查验？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p6@T1
- 金标要点：自收到申报材料之日起5个工作日内完成完备性查验
- 词法前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.s6-d1-c1-memo#p2@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p12@T1 6.p1-cac-o11#p11@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p6@T1 9.p1-cac-o13#p6@T1 10.p1-cac-o16#p7@T1
- 混合前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.p1-cac-o11#p15@T1 5.s6-d1-c1-memo#p2@T1 6.p1-cac-o11#p12@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p7@T1 9.p1-cac-o13#p6@T1 10.p1-cac-o11#p13@T1
- 重排前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p2@T1 6.p1-cac-o16#p7@T1 7.s6-d1-c1-memo#p2@T1 8.p1-cac-o13#p6@T1 9.p1-cac-o11#p12@T1 10.p1-cac-o11#p13@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 4. `p1-lx-04-new`

- 问：数据出境安全评估办法规定国家网信部门发出书面受理通知书后多少个工作日内完成评估？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p11@T1
- 金标要点：自向数据处理者发出书面受理通知书之日起45个工作日内完成数据出境安全评估
- 词法前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p6@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p15@T1 6.p1-cac-o11#p12@T1 7.p1-cac-o16#p6@T1 8.p1-cac-o11#p2@T1 9.p1-cac-o20#p3@T1 10.p1-cac-o16#p11@T1
- 混合前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p6@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p12@T1 6.s6-d1-c1-memo#p2@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p7@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o11#p17@T1
- 重排前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p15@T1 4.p1-cac-o11#p2@T1 5.p1-cac-o16#p7@T1 6.p1-cac-o11#p6@T1 7.s6-d1-c1-memo#p2@T1 8.p1-cac-o16#p11@T1 9.p1-cac-o11#p12@T1 10.p1-cac-o11#p17@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 5. `p1-lx-05-new`

- 问：数据处理者对评估结果有异议的，收到结果后多少个工作日内可以申请复评？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p12@T1
- 金标要点：在收到评估结果15个工作日内向国家网信部门申请复评
- 词法前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p6@T1 6.s6-d1-c1-memo#p3@T1 7.p1-cac-o11#p13@T1 8.p1-colaw-liquidation#p6@T1 9.p1-cac-o11#p15@T1 10.p1-cac-o11#p2@T1
- 混合前 10：1.p1-cac-o11#p12@T1 2.s6-d1-c1-memo#p2@T1 3.p1-cac-o16#p9@T1 4.p1-cac-o11#p11@T1 5.p1-cac-o11#p13@T1 6.s6-d1-c1-memo#p3@T1 7.p1-cac-o11#p6@T1 8.p1-cac-o11#p15@T1 9.p1-cac-o13#p6@T1 10.s4-d0-t1-91-eval#p2@T1
- 重排前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p6@T1 6.p1-cac-o11#p13@T1 7.s6-d1-c1-memo#p3@T1 8.p1-cac-o11#p15@T1 9.p1-cac-o13#p6@T1 10.s4-d0-t1-91-eval#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 6. `p1-lx-06-new`

- 问：个人信息出境认证办法自哪一天起施行？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o20#p9@T1
- 金标要点：本办法自2026年1月1日起施行
- 词法前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p9@T1 5.p1-cac-o20#p1@T1 6.p1-cac-o20#p6@T1 7.p1-cac-o20#p2@T1 8.s6-d1-c3-memo#p2@T1 9.p1-cac-o16#p3@T1 10.p1-cac-o13#p1@T1
- 混合前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p2@T1 5.p1-cac-o20#p6@T1 6.p1-cac-o20#p1@T1 7.p1-cac-o20#p7@T1 8.p1-cac-o16#p8@T1 9.p1-cac-o16#p11@T1 10.s6-d1-c3-memo#p2@T1
- 重排前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p2@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o20#p6@T1 7.p1-cac-o20#p1@T1 8.p1-cac-o20#p7@T1 9.p1-cac-o16#p11@T1 10.s6-d1-c3-memo#p2@T1
- 建议：保持 bm25
- 理由：词法的前 10 条里有金标，重排没有。

### 7. `p1-lx-07-new`

- 问：公司法规定，通过简易程序注销公司登记的公告期限不少于多少日？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p6@T1
- 金标要点：公告期限不少于二十日
- 词法前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p1@T1 5.s6-d2-g2-memo#p3@T1 6.s6-d1-t1-91-patch#p1@T1 7.p1-colaw-capital#p2@T1 8.p1-colaw-liquidation#p3@T1 9.p1-colaw-equity#p4@T1 10.p1-colaw-capital-call#p3@T1
- 混合前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g2-memo#p1@T1 4.p1-colaw-liquidation#p3@T1 5.p1-colaw-capital#p1@T1 6.s6-d2-g1-memo#p1@T1 7.s6-d2-g2-memo#p3@T1 8.p1-colaw-capital-call#p3@T1 9.s6-d2-g1-memo#p2@T1 10.p1-colaw-equity#p5@T1
- 重排前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g2-memo#p1@T1 4.p1-colaw-capital#p1@T1 5.s6-d2-g2-memo#p3@T1 6.p1-colaw-liquidation#p3@T1 7.p1-colaw-capital-call#p3@T1 8.s6-d2-g1-memo#p2@T1 9.p1-colaw-equity#p5@T1 10.s6-d2-g1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 8. `p1-lx-08-new`

- 问：股东对失权有异议的，应当自接到失权通知之日起多少日内向人民法院提起诉讼？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p3@T1
- 金标要点：自接到失权通知之日起三十日内，向人民法院提起诉讼
- 词法前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p3@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-liquidation#p3@T1 6.p1-colaw-equity#p1@T1 7.p1-colaw-liquidation#p6@T1 8.s6-d3-t1-91-notice#p1@T1 9.s6-d2-g3-memo#p1@T1 10.p1-cac-o11#p12@T1
- 混合前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p3@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-liquidation#p3@T1 6.p1-colaw-equity#p1@T1 7.p1-colaw-liquidation#p6@T1 8.s6-d2-g3-memo#p1@T1 9.p1-colaw-capital-call#p1@T1 10.p1-colaw-liquidation#p5@T1
- 重排前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p5@T1 3.p1-colaw-equity#p3@T1 4.p1-colaw-equity#p1@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-liquidation#p3@T1 7.p1-colaw-liquidation#p6@T1 8.p1-colaw-liquidation#p5@T1 9.p1-colaw-capital-call#p1@T1 10.s6-d2-g3-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 9. `p1-lx-09-new`

- 问：公司法（2018）规定一个自然人可以投资设立几个一人有限责任公司？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-oneperson#p3@T0
- 金标要点：一个自然人只能投资设立一个一人有限责任公司
- 词法前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-governance#p3@T0 4.p1-colaw-oneperson#p1@T0 5.p1-colaw-governance#p2@T0 6.p1-colaw-equity#p4@T0 7.p1-colaw-governance-board#p3@T0 8.p1-colaw-equity#p5@T0 9.p1-colaw-governance-board#p2@T0 10.p1-colaw-capital#p1@T0
- 混合前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-oneperson#p1@T0 4.p1-colaw-governance-board#p3@T0 5.p1-colaw-governance-board#p2@T0 6.p1-colaw-governance#p2@T0 7.p1-colaw-equity#p4@T0 8.p1-colaw-governance-supervisor#p1@T0 9.p1-colaw-capital#p2@T0 10.p1-colaw-governance#p3@T0
- 重排前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-equity#p4@T0 4.p1-colaw-governance#p3@T0 5.p1-colaw-governance-board#p3@T0 6.p1-colaw-governance-board#p2@T0 7.p1-colaw-governance#p2@T0 8.p1-colaw-governance-supervisor#p1@T0 9.p1-colaw-oneperson#p1@T0 10.p1-colaw-capital#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 10. `p1-lx-10-new`

- 问：2023年全国国内生产总值修订后的现价总量是多少亿元？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p2-gdp-national#p1@T1
- 金标要点：2023年全国国内生产总值修订后的现价总量是1294272亿元
- 词法前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s7-d2-t1-04-data#p2@T1 7.p1-cac-o13#p8@T1 8.s2-d3-t1-91-minutes#p1@T1 9.p1-cac-o16#p11@T1 10.s6-d2-g2-memo#p3@T1
- 混合前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s5-d3-t1-05-report#p1@T1 6.s5-d1-t1-03-report#p2@T1 7.s4-d2-t1-91-model-v3#p2@T1 8.s7-d2-t1-04-data#p2@T1 9.s5-d3-t1-05-report#p2@T1 10.s6-d3-t1-03-memo#p3@T1
- 重排前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s5-d1-t1-03-report#p2@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s7-d2-t1-04-data#p2@T1 8.s5-d3-t1-05-report#p1@T1 9.s5-d3-t1-05-report#p2@T1 10.s6-d3-t1-03-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 11. `p1-lx-11-new`

- 问：公司法规定公司减少注册资本，应当自股东会作出决议之日起几日内通知债权人？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p3@T1
- 金标要点：自股东会作出减少注册资本决议之日起十日内通知债权人
- 词法前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-governance#p2@T1 7.p1-colaw-governance#p3@T1 8.p1-colaw-capital#p1@T1 9.s6-d2-g1-memo#p1@T1 10.p1-colaw-liquidation#p4@T1
- 混合前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-equity#p5@T1 3.p1-colaw-liquidation#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-governance#p3@T1 7.p1-colaw-liquidation#p4@T1 8.s6-d2-g1-memo#p1@T1 9.p1-colaw-equity#p3@T1 10.p1-colaw-governance#p2@T1
- 重排前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-equity#p3@T1 7.p1-colaw-governance#p2@T1 8.p1-colaw-governance#p3@T1 9.p1-colaw-liquidation#p4@T1 10.s6-d2-g1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 12. `p1-lx-12-new`

- 问：数据出境安全评估办法所称重要数据是指什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p16@T0
- 金标要点：本办法所称重要数据，是指一旦遭到篡改、破坏、泄露或者非法获取、非法利用等，可能危害国家安全、经济运行、社会稳定、公共健康和安全等的数据。
- 词法前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p3@T0 4.p1-cac-o11#p15@T0 5.p1-cac-o11#p13@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p2@T0 8.p1-cac-o11#p7@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p11@T0
- 混合前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p3@T0 4.p1-cac-o11#p15@T0 5.p1-cac-o11#p7@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p13@T0 8.p1-cac-o11#p2@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p4@T0
- 重排前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p13@T0 4.p1-cac-o11#p2@T0 5.p1-cac-o11#p3@T0 6.p1-cac-o11#p15@T0 7.p1-cac-o11#p7@T0 8.p1-cac-o11#p5@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p4@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 13. `p1-mh-02-new`

- 问：非关基企业出境一般个人信息（不含敏感个人信息），旧规和新规分别到多少人就要报安全评估？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p2@T1；p1-cac-o16#p7@T1
- 金标要点：自上年1月1日起累计向境外提供10万人个人信息；自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）
- 词法前 10：1.s6-d1-c2-memo#p1@T1 2.s6-d1-c3-memo#p3@T1 3.p1-cac-o20#p2@T1 4.p1-cac-o16#p5@T1 5.p1-cac-o13#p3@T1 6.p1-cac-o20#p5@T1 7.p1-cac-o16#p7@T1 8.p1-cac-o11#p2@T1 9.p1-cac-o16#p6@T1 10.p1-cac-o13#p4@T1
- 混合前 10：1.s6-d1-c2-memo#p1@T1 2.s6-d1-c3-memo#p3@T1 3.p1-cac-o20#p2@T1 4.p1-cac-o16#p7@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o16#p5@T1 7.p1-cac-o13#p3@T1 8.p1-cac-o11#p2@T1 9.s6-d1-c4-memo#p1@T1 10.p1-cac-o13#p2@T1
- 重排前 10：1.s6-d1-c2-memo#p1@T1 2.p1-cac-o16#p7@T1 3.p1-cac-o16#p5@T1 4.p1-cac-o11#p2@T1 5.s6-d1-c4-memo#p1@T1 6.s6-d1-c3-memo#p3@T1 7.p1-cac-o20#p2@T1 8.p1-cac-o16#p8@T1 9.p1-cac-o13#p3@T1 10.p1-cac-o13#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 14. `p1-mh-03-new`

- 问：只算一般个人信息、不涉及敏感个人信息的话，签标准合同这条路，老办法和新规定各卡在多少人？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p2@T1；p1-cac-o16#p8@T1
- 金标要点：自上年1月1日起累计向境外提供个人信息不满10万人的；处理个人信息不满100万人的；自当年1月1日起累计向境外提供10万人以上、不满100万人个人信息（不含敏感个人信息）
- 词法前 10：1.s6-d1-c3-memo#p3@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p8@T1 4.p1-cac-o16#p2@T1 5.s6-d1-c2-memo#p3@T1 6.p1-cac-o13#p7@T1 7.p1-cac-o16#p3@T1 8.p1-cac-o16#p6@T1 9.s6-d1-c4-memo#p1@T1 10.s6-d1-c3-memo#p1@T1
- 混合前 10：1.s6-d1-c3-memo#p3@T1 2.p1-cac-o16#p8@T1 3.s6-d1-c2-memo#p3@T1 4.s6-d1-c3-memo#p2@T1 5.p1-cac-o13#p2@T1 6.p1-cac-o13#p7@T1 7.s6-d1-c3-memo#p1@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o13#p5@T1 10.p1-cac-o20#p2@T1
- 重排前 10：1.s6-d1-c3-memo#p3@T1 2.p1-cac-o16#p8@T1 3.s6-d1-c3-memo#p2@T1 4.p1-cac-o13#p7@T1 5.p1-cac-o13#p2@T1 6.s6-d1-c4-memo#p1@T1 7.s6-d1-c2-memo#p3@T1 8.s6-d1-c3-memo#p1@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o13#p5@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 15. `p1-mh-04-new`

- 问：不是关基、也不涉及重要数据的小公司，一年只出境几千人的一般个人信息，过去要签标准合同，如今还需要吗？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p2@T1；p1-cac-o16#p4@T1；p1-cac-o16#p5@T1
- 金标要点：自上年1月1日起累计向境外提供个人信息不满10万人的；关键信息基础设施运营者以外的数据处理者自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息）的；免予申报数据出境安全评估、订立个人信息出境标准合同、通过个人信息保护认证
- 词法前 10：1.p1-cac-o16#p2@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p3@T1 4.p1-cac-o16#p6@T1 5.s6-d1-c3-memo#p3@T1 6.s6-d1-c3-memo#p1@T1 7.p1-cac-o16#p1@T1 8.p1-cac-o16#p4@T1 9.p1-cac-o20#p3@T1 10.s6-d1-c4-memo#p1@T1
- 混合前 10：1.p1-cac-o16#p2@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o20#p3@T1 4.p1-cac-o16#p4@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o16#p3@T1 7.s6-d1-c3-memo#p3@T1 8.s6-d1-c3-memo#p1@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o16#p6@T1
- 重排前 10：1.p1-cac-o16#p2@T1 2.p1-cac-o16#p3@T1 3.p1-cac-o16#p11@T1 4.p1-cac-o16#p6@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o20#p3@T1 7.p1-cac-o16#p4@T1 8.p1-cac-o16#p8@T1 9.s6-d1-c3-memo#p3@T1 10.s6-d1-c3-memo#p1@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 16. `p1-mh-05-new`

- 问：认证办法从哪天开始施行？新规下走标准合同的人数区间是多少？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o20#p9@T1；p1-cac-o16#p8@T1
- 金标要点：本办法自2026年1月1日起施行；自当年1月1日起累计向境外提供10万人以上、不满100万人个人信息（不含敏感个人信息）或者不满1万人敏感个人信息的
- 词法前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o20#p8@T1 3.s6-d1-c3-memo#p2@T1 4.s6-d1-c3-memo#p3@T1 5.p1-cac-o11#p17@T1 6.p1-cac-o13#p8@T1 7.p1-cac-o13#p1@T1 8.p1-cac-o13#p5@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o20#p9@T1
- 混合前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o20#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o13#p5@T1 5.p1-cac-o13#p8@T1 6.p1-cac-o16#p11@T1 7.p1-cac-o20#p9@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o16#p8@T1 10.p1-cac-o13#p1@T1
- 重排前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o16#p8@T1 3.p1-cac-o20#p8@T1 4.p1-cac-o16#p11@T1 5.s6-d1-c4-memo#p1@T1 6.p1-cac-o13#p1@T1 7.p1-cac-o11#p17@T1 8.p1-cac-o13#p5@T1 9.p1-cac-o13#p8@T1 10.p1-cac-o20#p9@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 17. `p1-mh-06-new`

- 问：有限公司股东认缴的钱要几年内交齐？新法生效前设立、期限更长的公司要怎么处理？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital#p1@T1；p1-colaw-capital-transition#p1@T1
- 金标要点：自公司成立之日起五年内缴足；应当逐步调整至本法规定的期限以内
- 词法前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p2@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital#p4@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-transition#p1@T1 8.s6-d2-g1-memo#p1@T1 9.s2-d0-t1-91-interview#p2@T1 10.p1-colaw-equity#p5@T1
- 混合前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g1-memo#p1@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g3-memo#p3@T1 6.s6-d2-g2-memo#p3@T1 7.p1-colaw-capital-call#p4@T1 8.p1-colaw-capital-transition#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-capital#p4@T1
- 重排前 10：1.s6-d2-g1-memo#p2@T1 2.p1-colaw-capital#p1@T1 3.s6-d2-g2-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital-transition#p1@T1 6.p1-colaw-capital#p4@T1 7.s6-d2-g1-memo#p1@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital-transition#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 18. `p1-mh-07-new`

- 问：股东逾期不交出资，除了补交还要担什么？宽限期过了公司能怎么处置他的股权？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-transition#p2@T1；p1-colaw-capital-call#p2@T1
- 金标要点：该股东丧失其未缴纳出资的股权；还应当对给公司造成的损失承担赔偿责任；公司经董事会决议可以向该股东发出失权通知
- 词法前 10：1.p1-colaw-capital-call#p2@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-equity#p3@T1 7.s6-d2-g3-memo#p2@T1 8.p1-colaw-capital-call#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-capital-call#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p2@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-capital-call#p1@T1 4.p1-colaw-capital-call#p3@T1 5.s6-d2-g3-memo#p1@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-transition#p2@T1 8.s6-d2-g3-memo#p2@T1 9.p1-colaw-equity#p5@T1 10.p1-colaw-equity#p1@T1
- 重排前 10：1.p1-colaw-capital-call#p2@T1 2.s6-d2-g3-memo#p2@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-capital-call#p1@T1 7.s6-d2-g3-memo#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-equity#p5@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 19. `p1-mh-08-new`

- 问：董事会没去催缴出资导致损失，谁来赔？欠缴股东本人又要对公司赔什么？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p1@T1；p1-colaw-capital-transition#p2@T1
- 金标要点：负有责任的董事应当承担赔偿责任；还应当对给公司造成的损失承担赔偿责任
- 词法前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.p1-colaw-capital-call#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-governance-board#p3@T1 7.s6-d2-g1-memo#p2@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-governance-board#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.p1-colaw-capital-call#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-call#p3@T1 8.p1-colaw-capital-call#p5@T1 9.p1-colaw-governance-board#p3@T1 10.p1-colaw-capital#p1@T1
- 重排前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.s6-d2-g3-memo#p2@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p3@T1 7.p1-colaw-capital#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital-call#p5@T1 10.p1-colaw-governance-board#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 20. `p1-mh-09-new`

- 问：现在一个人能单独设有限公司吗？他认缴的出资几年内要缴完？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-oneperson#p1@T1；p1-colaw-capital#p1@T1
- 金标要点：自公司成立之日起五年内缴足；有限责任公司由一个以上五十个以下股东出资设立。
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-governance-board#p2@T1 4.p1-colaw-capital#p4@T1 5.p1-colaw-governance-supervisor-js#p5@T1 6.p1-colaw-oneperson#p1@T1 7.p1-colaw-governance-board#p4@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-liquidation#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital#p1@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-call#p5@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-oneperson#p1@T1 7.p1-colaw-capital-call#p1@T1 8.p1-colaw-capital-call#p2@T1 9.p1-colaw-governance-supervisor-js#p5@T1 10.p1-colaw-capital#p3@T1
- 重排前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-governance-supervisor-js#p5@T1 6.s6-d2-g1-memo#p1@T1 7.p1-colaw-oneperson#p1@T1 8.p1-colaw-capital-call#p1@T1 9.p1-colaw-capital-call#p2@T1 10.p1-colaw-capital#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 21. `p1-mh-10-new`

- 问：减资补亏之后，股东没交的出资能免掉吗？公司还不上债时，没到期的出资能被要求提前交吗？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p5@T1；p1-colaw-capital-call#p4@T1
- 金标要点：不得免除股东缴纳出资或者股款的义务；有权要求已认缴出资但未届出资期限的股东提前缴纳出资
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p2@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-capital#p3@T1 7.s6-d2-g3-memo#p2@T1 8.p1-colaw-liquidation#p5@T1 9.s6-d2-g1-memo#p3@T1 10.p1-colaw-capital-call#p3@T1
- 混合前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-call#p2@T1 3.p1-colaw-capital-call#p1@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-liquidation#p5@T1 7.s6-d2-g3-memo#p1@T1 8.p1-colaw-capital-call#p3@T1 9.s6-d2-g3-memo#p2@T1 10.s6-d2-g3-memo#p3@T1
- 重排前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-capital-transition#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-capital-call#p1@T1 7.p1-colaw-capital-call#p5@T1 8.s6-d2-g3-memo#p1@T1 9.p1-colaw-capital-call#p3@T1 10.s6-d2-g3-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 22. `p1-mh-11-new`

- 问：股东把股权卖给外人要先通知谁、别人有什么权利？卖的若是还没到期的认缴出资，由谁来交？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-equity#p1@T1；p1-colaw-capital-call#p5@T1
- 金标要点：其他股东在同等条件下有优先购买权；由受让人承担缴纳该出资的义务；应当将股权转让的数量、价格、支付方式和期限等事项书面通知其他股东
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p3@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-equity#p3@T1 7.p1-colaw-equity#p1@T1 8.p1-colaw-equity#p5@T1 9.s6-d2-g3-memo#p3@T1 10.p1-colaw-capital#p1@T1
- 混合前 10：1.p1-colaw-capital-call#p5@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-equity#p1@T1 5.p1-colaw-equity#p3@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-capital-call#p3@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital#p3@T1 10.p1-colaw-equity#p5@T1
- 重排前 10：1.p1-colaw-capital-transition#p2@T1 2.p1-colaw-equity#p1@T1 3.p1-colaw-capital-call#p3@T1 4.s6-d2-g3-memo#p3@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-equity#p3@T1 8.p1-colaw-capital-call#p2@T1 9.p1-colaw-equity#p5@T1 10.p1-colaw-capital#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 23. `p1-mh-13-new`

- 问：旧规下出境一般个人信息（不含敏感个人信息）到多少人要报评估，多少人以下可以签标准合同？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p2@T0；p1-cac-o13#p2@T0
- 金标要点：自上年1月1日起累计向境外提供10万人个人信息；自上年1月1日起累计向境外提供个人信息不满10万人的
- 词法前 10：1.p1-cac-o13#p1@T0 2.p1-cac-o13#p7@T0 3.p1-cac-o13#p3@T0 4.p1-cac-o13#p2@T0 5.p1-cac-o13#p4@T0 6.p1-cac-o13#p6@T0 7.p1-cac-o11#p2@T0 8.p1-cac-o13#p5@T0 9.p1-cac-o11#p4@T0 10.p1-cac-o11#p5@T0
- 混合前 10：1.p1-cac-o13#p1@T0 2.p1-cac-o13#p2@T0 3.p1-cac-o13#p3@T0 4.p1-cac-o13#p7@T0 5.p1-cac-o13#p5@T0 6.p1-cac-o13#p6@T0 7.p1-cac-o11#p5@T0 8.p1-cac-o11#p2@T0 9.p1-cac-o13#p4@T0 10.p1-cac-o13#p8@T0
- 重排前 10：1.p1-cac-o13#p2@T0 2.p1-cac-o13#p1@T0 3.p1-cac-o13#p7@T0 4.p1-cac-o13#p3@T0 5.p1-cac-o13#p6@T0 6.p1-cac-o11#p2@T0 7.p1-cac-o13#p4@T0 8.p1-cac-o13#p5@T0 9.p1-cac-o11#p5@T0 10.p1-cac-o13#p8@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 24. `p1-mh-14-new`

- 问：评估办法和标准合同办法分别是哪天开始施行的？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p17@T0；p1-cac-o13#p8@T0
- 金标要点：本办法自2022年9月1日起施行；本办法自2023年6月1日起施行
- 词法前 10：1.p1-cac-o11#p17@T0 2.p1-cac-o13#p8@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p5@T0 5.p1-cac-o11#p1@T0 6.p1-cac-o11#p16@T0 7.p1-cac-o13#p6@T0 8.p1-cac-o13#p7@T0 9.p1-cac-o13#p2@T0 10.p1-cac-o13#p4@T0
- 混合前 10：1.p1-cac-o11#p17@T0 2.p1-cac-o13#p8@T0 3.p1-cac-o13#p5@T0 4.p1-cac-o13#p6@T0 5.p1-colaw-capital-transition#p1@T0 6.p1-cac-o13#p1@T0 7.p1-cac-o13#p7@T0 8.s1-d0-01-analysis#p3@T0 9.p1-cac-o13#p2@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.p1-cac-o13#p7@T0 2.p1-cac-o13#p6@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p2@T0 5.p1-cac-o11#p1@T0 6.p1-cac-o11#p17@T0 7.p1-cac-o13#p8@T0 8.p1-cac-o13#p5@T0 9.s1-d0-01-analysis#p3@T0 10.p1-colaw-capital-transition#p1@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 25. `s1-d0-02-q2`

- 问：原材料交付周期拉长到45天的那家公司，T1 时技术系统性能还能满足原定的业务扩展需求吗？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-02-memo#p2@T1
- 金标要点：系统需进行架构优化，否则无法支撑下一阶段业务扩张；核心模块在高负载压力下暴露出性能瓶颈，已触发两次非预期中断
- 词法前 10：1.s1-d0-02-report#p2@T1 2.s4-d0-t1-02-report#p1@T1 3.s5-d2-t1-91-digest#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-01-analysis#p1@T1 6.s1-d1-t1-91-brief#p2@T1 7.s1-d0-02-memo#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s6-d0-t1-02-memo#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 混合前 10：1.s6-d0-t1-02-memo#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s1-d0-02-memo#p2@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-02-internal#p1@T1 7.s1-d0-01-memo#p1@T1 8.s1-d0-01-analysis#p1@T1 9.s4-d0-t1-02-report#p1@T1 10.s2-d1-01-memo#p1@T1
- 重排前 10：1.s1-d0-02-report#p2@T1 2.s4-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d0-t1-02-report#p1@T1 5.s1-d0-02-memo#p2@T1 6.s4-d2-t1-04-internal#p1@T1 7.s1-d0-01-memo#p1@T1 8.s1-d0-01-analysis#p1@T1 9.s2-d1-01-memo#p1@T1 10.s6-d0-t1-02-internal#p1@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 26. `s1-d0-03-q2`

- 问：T0 时认为有效的缓冲机制，在 T1 中是否仍具备应对能力？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-03-memo#p2@T1
- 金标要点：技术团队更新分析指出，外部环境变化已导致核心资源获取路径发生不可逆断裂，现有缓冲机制已无法覆盖新风险敞口
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d2-t1-04-summary#p2@T1 3.s5-d3-t1-05-analysis#p2@T1 4.p1-cac-o11#p8@T1 5.s1-d0-03-memo#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s4-d0-t1-02-report#p2@T1 8.s4-d2-t1-04-report#p2@T1 9.s7-d3-t1-05-memo#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s1-d0-03-memo#p2@T1 2.s2-d0-02-interview#p3@T1 3.s4-d2-t1-04-summary#p2@T1 4.s1-d0-05-warn#p2@T1 5.s4-d2-t1-04-internal#p1@T1 6.s4-d0-t1-02-report#p2@T1 7.s4-d2-t1-04-report#p2@T1 8.s5-d3-t1-05-analysis#p2@T1 9.s2-d3-01-interview#p2@T1 10.s7-d3-t1-05-claim#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p2@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d2-t1-04-report#p2@T1 4.s7-d3-t1-05-claim#p1@T1 5.s2-d0-02-interview#p3@T1 6.s4-d2-t1-04-summary#p2@T1 7.s1-d0-03-memo#p2@T1 8.s1-d0-05-warn#p2@T1 9.s4-d2-t1-04-internal#p1@T1 10.s2-d3-01-interview#p2@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 27. `s1-d0-04-q1`

- 问：T0 时点下，核心市场渗透率是否处于稳定状态？其依据是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p1@T0
- 金标要点：近期数据显示，核心市场渗透率在连续三周维持在68%以上，表明当前战略执行路径具备初步成效；团队评估认为，该数值已进入稳定区间，可作为后续资源调配的重要依据
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s1-d0-04-memo#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s1-d0-01-memo#p1@T0 5.s7-d0-t0-01-qa#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s1-d1-01-analysis#p1@T0 8.s2-d2-01-memo#p2@T0 9.s7-d0-t0-01-report#p3@T0 10.s1-d1-01-analysis#p3@T0
- 混合前 10：1.s1-d0-04-memo#p1@T0 2.s1-d0-01-memo#p1@T0 3.s1-d0-02-memo#p1@T0 4.s1-d1-01-memo#p1@T0 5.s2-d0-03-memo#p2@T0 6.s2-d2-01-memo#p2@T0 7.s1-d1-01-analysis#p1@T0 8.s1-d2-01-memo#p1@T0 9.s1-d0-02-report#p1@T0 10.s4-d3-t0-05-memo#p1@T0
- 重排前 10：1.s1-d0-04-memo#p1@T0 2.s1-d0-01-memo#p1@T0 3.s4-d3-t0-05-memo#p1@T0 4.s1-d0-02-memo#p1@T0 5.s1-d1-01-memo#p1@T0 6.s2-d0-03-memo#p2@T0 7.s2-d2-01-memo#p2@T0 8.s1-d1-01-analysis#p1@T0 9.s1-d2-01-memo#p1@T0 10.s1-d0-02-report#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 28. `s1-d0-04-q2`

- 问：核心市场渗透率回落到66.2%的那家公司，T1 时供应链中哪一环节明显恶化？具体表现是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p2@T1
- 金标要点：供应链韧性测试中，尽管整体准时率仍达92%，但某关键节点延误率上升至11%，暴露出单一依赖风险
- 词法前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-03-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s2-d0-02-interview#p3@T1 5.s6-d2-g3-memo#p3@T1 6.s1-d0-01-memo#p1@T1 7.s1-d1-t1-91-memo#p2@T1 8.s7-d2-t1-04-data#p1@T1 9.s1-d1-01-memo#p1@T1 10.s1-d2-01-memo#p1@T1
- 混合前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-03-memo#p1@T1 3.s2-d0-02-interview#p3@T1 4.s1-d0-01-memo#p1@T1 5.s1-d1-01-memo#p1@T1 6.s1-d0-02-memo#p1@T1 7.s1-d2-01-memo#p1@T1 8.s1-d3-01-memo#p1@T1 9.s7-d2-t1-04-data#p1@T1 10.s1-d1-01-analysis#p2@T1
- 重排前 10：1.s1-d0-04-memo#p1@T1 2.s7-d2-t1-04-data#p1@T1 3.s1-d0-03-memo#p1@T1 4.s2-d0-02-interview#p3@T1 5.s1-d0-01-memo#p1@T1 6.s1-d1-01-memo#p1@T1 7.s1-d0-02-memo#p1@T1 8.s1-d2-01-memo#p1@T1 9.s1-d3-01-memo#p1@T1 10.s1-d1-01-analysis#p2@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 29. `s1-d0-04-q3`

- 问：渗透率回落至66.2%、三条海运通道被临时关闭的那家公司，T0 到 T1 客户满意度的描述有何关键变化？预示什么趋势？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p3@T1
- 金标要点：客户反馈调查中，尽管平均满意度维持在4.3分，但针对售后服务的负面评论数量同比增加37%，提示服务模式存在结构性短板，亟待调整
- 词法前 10：1.s1-d0-04-risk#p2@T1 2.s7-d3-t1-05-conflict#p2@T1 3.s1-d0-04-memo#p1@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s5-d1-t1-03-note#p2@T1 6.p1-colaw-governance-supervisor-js#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s1-d0-01-memo#p2@T1 9.s3-d0-02-c#p2@T1 10.s5-d3-t1-05-analysis#p3@T1
- 混合前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-04-risk#p2@T1 3.s1-d0-01-memo#p2@T1 4.s7-d3-t1-05-conflict#p2@T1 5.s2-d0-03-memo#p1@T1 6.s5-d1-t1-03-note#p2@T1 7.s1-d0-04-memo#p3@T1 8.s3-d0-02-c#p2@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s2-d2-01-report#p2@T1
- 重排前 10：1.s1-d0-04-risk#p2@T1 2.s7-d3-t1-05-conflict#p2@T1 3.s5-d1-t1-03-note#p2@T1 4.s1-d0-01-memo#p2@T1 5.s3-d0-02-c#p2@T1 6.s1-d0-04-memo#p1@T1 7.s2-d0-03-memo#p1@T1 8.s1-d0-04-memo#p3@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s2-d2-01-report#p2@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 30. `s1-d0-04-q4`

- 问：面临三条海运通道被临时关闭的那家出口企业，T1 文档中新法案对数据处理流程有什么影响？该如何应对？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-risk#p3@T1
- 金标要点：新法案正式进入立法听证阶段，预计将在未来六个月内实施，现有数据跨境架构必须在四十五天内完成合规改造；否则将面临运营中断
- 词法前 10：1.s1-d0-04-risk#p2@T1 2.s1-d0-05-warn#p2@T1 3.s5-d3-t1-05-analysis#p1@T1 4.s1-d0-04-risk#p1@T1 5.s7-d0-t1-02-memo#p3@T1 6.s1-d0-04-risk#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s1-d1-01-report#p3@T1 9.s6-d2-g1-memo#p3@T1 10.s6-d1-c4-memo#p2@T1
- 混合前 10：1.s1-d0-04-risk#p2@T1 2.s1-d1-01-report#p3@T1 3.s1-d0-04-risk#p3@T1 4.s6-d1-c4-memo#p2@T1 5.p1-cac-o11#p14@T1 6.s6-d3-t1-03-memo#p3@T1 7.s6-d2-g2-memo#p2@T1 8.s7-d0-t1-02-update#p2@T1 9.s1-d0-05-memo#p3@T1 10.p1-cac-o11#p15@T1
- 重排前 10：1.s1-d0-04-risk#p2@T1 2.s7-d0-t1-02-update#p2@T1 3.s6-d1-c4-memo#p2@T1 4.s6-d2-g2-memo#p2@T1 5.s1-d1-01-report#p3@T1 6.p1-cac-o11#p14@T1 7.s6-d3-t1-03-memo#p3@T1 8.p1-cac-o11#p15@T1 9.s1-d0-04-risk#p3@T1 10.s1-d0-05-memo#p3@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 31. `s1-d0-05-q1`

- 问：T0 时点关于目标区域基础设施状况的评估结论是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p1@T0
- 金标要点：根据当前情报，目标区域的基础设施部署已进入稳定阶段；主要通道保持畅通，未发现异常干扰迹象；该区域具备长期战略价值
- 词法前 10：1.s1-d0-05-memo#p1@T0 2.s4-d0-t0-01-analysis#p2@T0 3.s1-d0-03-memo#p1@T0 4.s7-d0-t0-01-qa#p1@T0 5.s1-d1-01-analysis#p3@T0 6.p1-cac-o11#p12@T0 7.s1-d3-01-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s2-d0-03-interview#p1@T0 10.s4-d1-t0-03-plan#p1@T0
- 混合前 10：1.s1-d0-05-memo#p1@T0 2.s1-d0-03-memo#p1@T0 3.s1-d3-01-memo#p1@T0 4.s5-d0-t0-01-summary#p3@T0 5.s2-d0-02-memo#p2@T0 6.p1-cac-o11#p12@T0 7.s1-d0-01-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d0-t0-01-analysis#p1@T0
- 重排前 10：1.s1-d0-05-memo#p1@T0 2.s1-d0-03-memo#p1@T0 3.s1-d3-01-memo#p1@T0 4.p1-cac-o11#p12@T0 5.s1-d0-01-memo#p1@T0 6.s5-d0-t0-01-summary#p3@T0 7.s2-d0-02-memo#p2@T0 8.s7-d0-t0-01-report#p3@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d0-t0-01-analysis#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 32. `s1-d0-05-q2`

- 问：T1 时点对同一区域基础设施状况的最新判断有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p1@T1
- 金标要点：最新监测显示，目标区域主要通道出现结构性损伤，部分路段存在非正常闭塞现象；需重新评估其战略可用性
- 词法前 10：1.s1-d0-05-warn#p1@T1 2.s4-d2-t1-04-report#p1@T1 3.s7-d0-t1-02-claim#p2@T1 4.s1-d0-03-memo#p1@T1 5.s1-d0-05-memo#p1@T1 6.s5-d3-t1-05-memo#p2@T1 7.s6-d3-t1-02-report#p1@T1 8.s6-d1-c4-memo#p3@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d2-t1-04-internal#p1@T1
- 混合前 10：1.s1-d0-03-memo#p1@T1 2.s7-d0-t1-02-claim#p2@T1 3.s1-d0-05-memo#p1@T1 4.s1-d3-01-memo#p1@T1 5.s1-d0-05-warn#p1@T1 6.s4-d2-t1-04-report#p1@T1 7.s6-d0-t1-01-patch#p2@T1 8.s5-d3-t1-05-memo#p3@T1 9.s6-d1-c4-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 重排前 10：1.s1-d0-03-memo#p1@T1 2.s7-d0-t1-02-claim#p2@T1 3.s1-d0-05-memo#p1@T1 4.s1-d0-05-warn#p1@T1 5.s4-d2-t1-04-report#p1@T1 6.s6-d1-c4-memo#p3@T1 7.s1-d3-01-memo#p1@T1 8.s6-d0-t1-01-patch#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 33. `s1-d0-05-q3`

- 问：T0 时点，安全团队对周边势力活动态势作出判断的依据是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p2@T0
- 金标要点：安全团队报告称，周边势力活动频率在近两周内维持低位，无明显升级信号
- 词法前 10：1.s1-d0-05-memo#p2@T0 2.s7-d0-t0-01-qa#p1@T0 3.s4-d0-t0-01-analysis#p2@T0 4.p1-colaw-governance#p3@T0 5.s2-d0-04-memo#p3@T0 6.p1-cac-o11#p15@T0 7.s4-d0-t0-01-plan#p2@T0 8.s7-d1-t0-03-fact#p3@T0 9.s5-d2-t0-04-analysis#p1@T0 10.p1-cac-o11#p16@T0
- 混合前 10：1.s1-d0-05-memo#p2@T0 2.p1-cac-o11#p7@T0 3.s4-d0-t0-01-analysis#p2@T0 4.p1-cac-o11#p16@T0 5.s7-d1-t0-03-fact#p3@T0 6.s7-d1-t0-03-reason#p3@T0 7.s7-d0-t0-01-memo#p2@T0 8.s2-d0-04-memo#p3@T0 9.s1-d3-01-report#p1@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.s1-d0-05-memo#p2@T0 2.p1-cac-o11#p7@T0 3.s7-d1-t0-03-fact#p3@T0 4.s4-d0-t0-01-analysis#p2@T0 5.p1-cac-o11#p16@T0 6.s7-d1-t0-03-reason#p3@T0 7.s7-d0-t0-01-memo#p2@T0 8.s2-d0-04-memo#p3@T0 9.p1-cac-o11#p1@T0 10.s1-d3-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 34. `s1-d0-05-q4`

- 问：T1 时点的安全预警是否基于新的技术监测数据？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-warn#p1@T1；s1-d0-05-warn#p3@T1
- 金标要点：技术监测发现，加密链路遭遇定向干扰攻击，虽未突破防护，但暴露了系统脆弱点；多源情报证实，敏感议题已转化为实际军事集结信号
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.p1-cac-o13#p4@T1 3.p1-cac-o20#p5@T1 4.s6-d3-t1-02-report#p2@T1 5.p1-cac-o11#p4@T1 6.s2-d0-02-memo#p2@T1 7.s1-d3-01-memo#p2@T1 8.s2-d3-01-memo#p3@T1 9.s4-d2-t1-04-report#p1@T1 10.s2-d0-t1-91-interview#p2@T1
- 混合前 10：1.s2-d3-01-memo#p3@T1 2.s1-d3-01-memo#p2@T1 3.s1-d0-05-warn#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-03-memo#p1@T1 6.s4-d2-t1-04-report#p3@T1 7.p1-cac-o11#p1@T1 8.p1-cac-o11#p7@T1 9.s6-d1-c2-memo#p1@T1 10.s6-d1-t1-91-release#p3@T1
- 重排前 10：1.s1-d3-01-memo#p2@T1 2.s2-d3-01-memo#p3@T1 3.s1-d0-05-warn#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-03-memo#p1@T1 6.p1-cac-o11#p1@T1 7.p1-cac-o11#p7@T1 8.s6-d1-c2-memo#p1@T1 9.s6-d1-t1-91-release#p3@T1 10.s4-d2-t1-04-report#p3@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 35. `s1-d1-01-q1`

- 问：T0 时，核心功能平均停留4.8分钟的那款产品，目标市场渗透率达到预期阈值的多少？文档把增长归因于什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d1-01-memo#p1@T0
- 金标要点：目标市场渗透率已达到预期阈值的87%；主要得益于渠道扩张与客户反馈优化
- 词法前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-01-memo#p1@T0 4.s5-d1-t0-91-repost#p1@T0 5.s1-d0-02-memo#p1@T0 6.s2-d0-03-memo#p1@T0 7.s1-d0-04-memo#p1@T0 8.s1-d1-01-memo#p3@T0 9.s2-d2-01-memo#p1@T0 10.s1-d1-01-analysis#p3@T0
- 混合前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-02-memo#p1@T0 4.s1-d0-01-memo#p1@T0 5.s1-d0-04-memo#p1@T0 6.s1-d1-01-memo#p3@T0 7.s2-d2-01-memo#p1@T0 8.s1-d0-01-memo#p2@T0 9.s1-d2-01-memo#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 重排前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-01-memo#p1@T0 4.s1-d0-02-memo#p1@T0 5.s1-d0-04-memo#p1@T0 6.s2-d2-01-memo#p1@T0 7.s1-d1-01-memo#p3@T0 8.s1-d0-01-memo#p2@T0 9.s1-d2-01-memo#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 36. `s1-d2-01-q1`

- 问：在评级机构把短期展望调到负面观察的那份宏观研判里，T0 与 T1 对通胀走势的描述根本差异在哪？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-memo#p1@T1
- 金标要点：尽管前期数据显示通胀回落，最新数据揭示核心通胀存在反弹苗头，部分服务类项目价格再度上扬
- 词法前 10：1.s1-d2-01-analysis#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s1-d1-t1-91-memo#p2@T1 4.s5-d3-t1-05-memo#p1@T1 5.s5-d1-t1-03-memo#p3@T1 6.s2-d0-t1-91-memo#p1@T1 7.s4-d0-t1-02-report#p2@T1 8.s5-d2-t1-91-digest#p3@T1 9.s6-d2-g3-memo#p3@T1 10.s6-d3-t1-02-report#p1@T1
- 混合前 10：1.s1-d2-01-analysis#p3@T1 2.s1-d2-01-memo#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s1-d0-04-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s5-d1-t1-03-summary#p3@T1 7.s7-d3-t1-05-claim#p2@T1 8.s7-d2-t1-04-memo#p3@T1 9.s1-d0-04-risk#p1@T1 10.s5-d3-t1-05-analysis#p3@T1
- 重排前 10：1.s1-d2-01-analysis#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s5-d1-t1-03-memo#p3@T1 4.s5-d1-t1-03-summary#p3@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s1-d0-04-memo#p3@T1 7.s7-d3-t1-05-claim#p2@T1 8.s7-d2-t1-04-memo#p3@T1 9.s1-d2-01-memo#p1@T1 10.s1-d0-04-risk#p1@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 37. `s1-d2-01-q2`

- 问：对比 T0 和 T1 的报告，企业资本开支的乐观预期是否依然成立？请说明依据。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-memo#p2@T1
- 金标要点：企业资本开支虽有小幅回升，但实际投资增速仍低于预期，尤其在高端制造领域出现观望情绪；信心修复不均衡
- 词法前 10：1.s1-d2-01-memo#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p2@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d3-t1-03-memo#p2@T1 6.s7-d2-t1-04-memo#p3@T1 7.s4-d0-t1-02-guide#p3@T1 8.p1-colaw-liquidation#p1@T1 9.p1-colaw-liquidation#p2@T1 10.s6-d2-g1-memo#p2@T1
- 混合前 10：1.s1-d2-01-memo#p2@T1 2.s4-d0-t1-02-review#p1@T1 3.s6-d2-g1-memo#p2@T1 4.s4-d2-t1-04-internal#p1@T1 5.p1-colaw-capital-call#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s5-d3-t1-05-memo#p3@T1 8.s4-d0-t1-02-analysis#p1@T1 9.s5-d3-t1-05-analysis#p1@T1 10.s6-d2-g2-memo#p2@T1
- 重排前 10：1.s1-d2-01-memo#p2@T1 2.s6-d2-g1-memo#p2@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s5-d3-t1-05-memo#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s6-d2-g2-memo#p2@T1 7.s4-d0-t1-02-review#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.p1-colaw-capital-call#p1@T1 10.s5-d3-t1-05-analysis#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 38. `s1-d2-01-q3`

- 问：T1 文档中提到的跨境支付系统部署延迟，其主要原因是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-report#p3@T1
- 金标要点：跨境支付系统测试中发现兼容性瓶颈，部署时间或延后至下一财年，影响预期效率提升
- 词法前 10：1.s1-d2-01-report#p3@T1 2.p1-cac-o16#p4@T1 3.s7-d2-t1-04-brief#p2@T1 4.s2-d1-01-memo#p1@T1 5.s7-d0-t1-02-report#p1@T1 6.s4-d2-t1-04-internal#p1@T1 7.s7-d0-t1-02-brief#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s7-d0-t1-02-report#p3@T1 10.s7-d0-t1-02-memo#p2@T1
- 混合前 10：1.s1-d2-01-report#p3@T1 2.s7-d0-t1-02-report#p1@T1 3.s7-d2-t1-04-brief#p2@T1 4.s2-d1-01-memo#p1@T1 5.s1-d3-01-memo#p2@T1 6.s7-d0-t1-02-memo#p2@T1 7.s2-d3-01-memo#p3@T1 8.s6-d1-c4-memo#p2@T1 9.s1-d1-01-memo#p2@T1 10.s1-d0-01-memo#p2@T1
- 重排前 10：1.s1-d2-01-report#p3@T1 2.s7-d2-t1-04-brief#p2@T1 3.s7-d0-t1-02-memo#p2@T1 4.s7-d0-t1-02-report#p1@T1 5.s2-d1-01-memo#p1@T1 6.s1-d3-01-memo#p2@T1 7.s6-d1-c4-memo#p2@T1 8.s1-d0-01-memo#p2@T1 9.s2-d3-01-memo#p3@T1 10.s1-d1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 39. `s1-d2-01-q6`

- 问：T1 时，评级机构对主权信用展望作了什么调整？核心通胀和区域消费又各出现了什么信号？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-analysis#p3@T1；s1-d2-01-memo#p1@T1；s1-d2-01-report#p1@T1
- 金标要点：整体需求动能不足；国际评级机构下调短期展望至负面观察；最新数据揭示核心通胀存在反弹苗头；区域消费指数增长势头减弱
- 词法前 10：1.s1-d0-04-risk#p1@T1 2.s1-d2-01-analysis#p3@T1 3.s1-d2-01-memo#p1@T1 4.s4-d0-t1-02-memo#p2@T1 5.s1-d0-05-warn#p1@T1 6.s1-d3-01-memo#p1@T1 7.s4-d2-t1-04-summary#p1@T1 8.s1-d2-01-report#p1@T1 9.s5-d1-t1-03-memo#p1@T1 10.s5-d3-t1-05-memo#p1@T1
- 混合前 10：1.s1-d0-04-risk#p1@T1 2.s1-d2-01-analysis#p3@T1 3.s1-d2-01-memo#p1@T1 4.s5-d1-t1-03-memo#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s1-d2-01-report#p1@T1 7.s1-d0-05-warn#p1@T1 8.s7-d2-t1-04-memo#p3@T1 9.s2-d0-02-interview#p3@T1 10.s1-d3-01-report#p1@T1
- 重排前 10：1.s1-d0-04-risk#p1@T1 2.s4-d0-t1-02-memo#p2@T1 3.s1-d2-01-analysis#p3@T1 4.s5-d1-t1-03-memo#p1@T1 5.s1-d0-05-warn#p1@T1 6.s7-d2-t1-04-memo#p3@T1 7.s1-d2-01-memo#p1@T1 8.s1-d2-01-report#p1@T1 9.s2-d0-02-interview#p3@T1 10.s1-d3-01-report#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 40. `s1-d3-01-q4`

- 问：物流周期普遍延长超过48小时的那个区域，T1 报告里通信网络与多边合作的变化如何影响整体战略态势？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d3-01-report#p2@T1；s1-d3-01-report#p3@T1
- 金标要点：主干通信网络在近三日内遭遇三次区域性中断，峰值负载达92%，冗余链路已被迫启用；公开声明中出现立场分化，合作意愿显著减弱，存在集体脱钩趋势；多边协调机制出现明显裂痕
- 词法前 10：1.s1-d3-01-memo#p1@T1 2.s2-d1-01-memo#p1@T1 3.s1-d0-03-report#p2@T1 4.s5-d0-t1-02-memo#p1@T1 5.s6-d0-t1-01-memo#p1@T1 6.s1-d0-02-report#p2@T1 7.s5-d0-t1-02-memo#p2@T1 8.s1-d0-04-risk#p2@T1 9.s1-d3-01-report#p2@T1 10.s6-d0-t1-02-internal#p1@T1
- 混合前 10：1.s1-d3-01-memo#p1@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-04-risk#p2@T1 4.s5-d0-t1-02-memo#p1@T1 5.s2-d1-01-memo#p1@T1 6.s1-d3-01-report#p2@T1 7.s6-d0-t1-02-internal#p1@T1 8.s2-d0-02-report#p3@T1 9.s1-d0-05-memo#p1@T1 10.s1-d2-01-report#p1@T1
- 重排前 10：1.s1-d3-01-memo#p1@T1 2.s2-d1-01-memo#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s1-d0-03-report#p2@T1 5.s6-d0-t1-02-internal#p1@T1 6.s1-d0-05-memo#p1@T1 7.s1-d0-04-risk#p2@T1 8.s1-d3-01-report#p2@T1 9.s2-d0-02-report#p3@T1 10.s1-d2-01-report#p1@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 41. `s2-d0-01-q1`

- 问：渠道成本已占总成本34%的那家公司，T0 时线下门店的营收占比大约多少？线上流量转化率又是多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-memo#p1@T0
- 金标要点：线下门店占比不足15%；线上流量转化率稳定在6.8%
- 词法前 10：1.s2-d0-01-memo#p3@T0 2.s2-d0-01-memo#p1@T0 3.s2-d1-01-memo#p3@T0 4.s2-d0-01-report#p1@T0 5.p2-gdp-national#p2@T0 6.s1-d1-01-analysis#p3@T0 7.s2-d0-03-memo#p1@T0 8.s2-d0-02-report#p1@T0 9.s4-d0-t0-01-plan#p2@T0 10.s2-d3-01-memo#p1@T0
- 混合前 10：1.s2-d0-01-memo#p3@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-02-report#p1@T0 4.s2-d1-01-memo#p3@T0 5.s2-d0-01-report#p1@T0 6.s2-d0-03-memo#p1@T0 7.s2-d1-01-memo#p2@T0 8.s2-d0-02-memo#p1@T0 9.s3-d3-01-report#p1@T0 10.s2-d3-01-memo#p1@T0
- 重排前 10：1.s2-d0-01-memo#p1@T0 2.s2-d0-01-memo#p3@T0 3.s2-d0-03-memo#p1@T0 4.s2-d1-01-memo#p3@T0 5.s2-d0-01-report#p1@T0 6.s2-d1-01-memo#p2@T0 7.s2-d0-02-memo#p1@T0 8.s2-d3-01-memo#p1@T0 9.s2-d0-02-report#p1@T0 10.s3-d3-01-report#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 42. `s2-d0-01-q2`

- 问：T1 时渠道成本占总成本的比例发生了什么变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-memo#p3@T1
- 金标要点：渠道成本压力持续加剧，目前占总成本达41%，其中平台佣金上涨22%；新方案拟通过自建私域流量降低对外部平台依赖
- 词法前 10：1.s2-d0-01-memo#p3@T1 2.p1-cac-o11#p10@T1 3.s4-d2-t1-04-internal#p1@T1 4.s1-d0-03-memo#p2@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s2-d0-01-memo#p1@T1 7.s5-d3-t1-05-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s2-d3-01-memo#p1@T1 10.p2-gdp-national#p2@T1
- 混合前 10：1.s2-d0-01-memo#p3@T1 2.s2-d0-01-memo#p1@T1 3.s3-d3-01-report#p2@T1 4.s2-d0-02-report#p1@T1 5.s4-d2-t1-04-report#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s6-d3-t1-03-memo#p3@T1 8.s3-d1-t1-91-quote#p1@T1 9.s3-d2-t1-91-contract#p2@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s2-d0-01-memo#p3@T1 2.s2-d0-01-memo#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d3-01-memo#p1@T1 6.s3-d3-01-report#p2@T1 7.s2-d0-02-report#p1@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-contract#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 43. `s2-d0-01-q4`

- 问：T1 时渠道信息同步机制升级后，投诉量和关键节点更新延迟分别有什么变化？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-report#p3@T1
- 金标要点：投诉量下降至周均43起；关键节点更新延迟已减少80%
- 词法前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-05-warn#p2@T1 4.s1-d0-03-memo#p1@T1 5.s4-d2-t1-04-internal#p1@T1 6.s1-d0-03-memo#p2@T1 7.p1-cac-o20#p7@T1 8.s5-d1-t1-03-report#p3@T1 9.s6-d3-t1-02-memo#p1@T1 10.s6-d3-t1-03-memo#p3@T1
- 混合前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s6-d3-t1-03-memo#p3@T1 4.s2-d1-01-memo#p1@T1 5.s6-d3-t1-03-report#p2@T1 6.s2-d1-01-memo#p2@T1 7.s1-d0-01-memo#p2@T1 8.s1-d0-05-warn#p2@T1 9.s6-d0-t1-01-channel#p2@T1 10.s6-d0-t1-02-report#p1@T1
- 重排前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-05-warn#p2@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d1-01-memo#p1@T1 6.s6-d3-t1-03-report#p2@T1 7.s2-d1-01-memo#p2@T1 8.s1-d0-01-memo#p2@T1 9.s6-d0-t1-01-channel#p2@T1 10.s6-d0-t1-02-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 44. `s2-d0-02-q1`

- 问：根据T0文档，新客户获取成本上升的主要原因是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-memo#p1@T0
- 金标要点：近期渠道反馈显示，新客户获取成本在上季度上升了18%，主要源于线上广告投放效率下降；团队初步判断是算法推荐系统未及时适配用户行为变化
- 词法前 10：1.s2-d0-02-memo#p1@T0 2.s3-d0-03-report#p1@T0 3.s4-d0-t0-01-analysis#p1@T0 4.s4-d0-t0-01-plan#p2@T0 5.s4-d0-t0-01-analysis#p2@T0 6.s2-d0-04-memo#p1@T0 7.s3-d0-01-memo#p3@T0 8.s3-d2-01-competitor-pricing#p1@T0 9.s2-d0-03-memo#p1@T0 10.s7-d0-t0-01-qa#p1@T0
- 混合前 10：1.s2-d0-02-memo#p1@T0 2.s3-d0-03-report#p1@T0 3.s2-d0-03-memo#p1@T0 4.s4-d0-t0-01-analysis#p1@T0 5.s3-d3-01-report#p1@T0 6.s3-d0-01-memo#p3@T0 7.s3-d1-01-report#p3@T0 8.s3-d0-02-b#p1@T0 9.s4-d0-t0-01-analysis#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s2-d0-02-memo#p1@T0 2.s2-d0-03-memo#p1@T0 3.s4-d0-t0-01-analysis#p1@T0 4.s3-d0-03-report#p1@T0 5.s3-d3-01-report#p1@T0 6.s3-d0-01-memo#p3@T0 7.s3-d1-01-report#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s3-d0-02-b#p1@T0 10.s4-d3-t0-05-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 45. `s2-d0-02-q2`

- 问：T1版本中关于新客户获取成本的解释有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-memo#p1@T1
- 金标要点：最新数据分析表明，新客户获取成本上升主因并非算法问题，而是外部市场环境波动导致流量质量整体下滑；原有投放模型仍具有效性
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s1-d0-03-memo#p2@T1 3.s2-d0-02-memo#p1@T1 4.s1-d1-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s1-d0-01-memo#p2@T1 7.s4-d0-t1-02-report#p1@T1 8.s4-d0-t1-02-memo#p1@T1 9.s4-d2-t1-04-internal#p1@T1 10.s7-d3-t1-05-conflict#p2@T1
- 混合前 10：1.s2-d0-02-memo#p1@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s2-d0-03-memo#p1@T1 4.s4-d0-t1-02-review#p2@T1 5.s1-d1-01-memo#p3@T1 6.s4-d2-t1-04-memo#p1@T1 7.s4-d0-t1-02-memo#p1@T1 8.s3-d2-01-competitor-pricing#p2@T1 9.s2-d3-01-memo#p1@T1 10.s4-d0-t1-02-report#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-review#p2@T1 4.s1-d1-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s2-d0-02-memo#p1@T1 8.s2-d0-03-memo#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s2-d3-01-memo#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 46. `s2-d0-02-q3`

- 问：T0报告中提到的电商平台旗舰店贡献占比是多少？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-report#p1@T0
- 金标要点：本月渠道销售总额环比增长9.4%，主要驱动来自新上线的电商平台旗舰店，其首月贡献占比达23%
- 词法前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-01-memo#p3@T0 4.s5-d2-t0-04-analysis#p2@T0 5.s4-d0-t0-01-plan#p2@T0 6.s1-d1-01-analysis#p3@T0 7.p2-gdp-national#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s5-d2-t0-04-analysis#p3@T0 10.s2-d3-01-interview#p2@T0
- 混合前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-01-memo#p3@T0 4.s2-d3-01-memo#p2@T0 5.s5-d2-t0-04-analysis#p1@T0 6.s2-d1-01-report#p1@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s2-d1-01-memo#p1@T0 9.s2-d0-01-report#p1@T0 10.s2-d3-01-interview#p2@T0
- 重排前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s2-d0-01-memo#p3@T0 5.s5-d2-t0-04-analysis#p1@T0 6.s2-d1-01-memo#p1@T0 7.s2-d1-01-report#p1@T0 8.s2-d3-01-memo#p2@T0 9.s2-d0-01-report#p1@T0 10.s2-d3-01-interview#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 47. `s2-d0-02-q4`

- 问：T1报告修正后的销售总额变化趋势是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-report#p1@T1
- 金标要点：本月渠道销售总额实际为环比下降3.1%，此前公布的9.4%增长数据系系统误报，现已修正
- 词法前 10：1.s2-d0-02-report#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s4-d2-t1-91-model-v3#p2@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s7-d2-t1-04-claim#p3@T1 6.s5-d0-t1-02-report#p2@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s5-d0-t1-02-analysis#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 混合前 10：1.s2-d0-02-report#p1@T1 2.s3-d0-01-report#p3@T1 3.p2-gdp-national#p1@T1 4.s4-d0-t1-02-plan#p1@T1 5.s5-d1-t1-03-memo#p1@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s3-d0-01-report#p2@T1 8.s1-d0-02-report#p3@T1 9.s2-d0-01-report#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 重排前 10：1.s2-d0-02-report#p1@T1 2.p2-gdp-national#p1@T1 3.s4-d2-t1-91-model-v3#p2@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-plan#p1@T1 6.s5-d1-t1-03-memo#p1@T1 7.s3-d0-01-report#p2@T1 8.s2-d0-01-report#p3@T1 9.s6-d0-t1-03-internal#p1@T1 10.s1-d0-02-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 48. `s2-d0-02-q5`

- 问：高管访谈中关于海外扩张的初始态度如何？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-interview#p2@T0
- 金标要点：关于海外扩张，目前暂无明确计划，重点仍将聚焦于国内市场的深度渗透与服务优化
- 词法前 10：1.s2-d0-02-interview#p2@T0 2.p1-colaw-governance-board#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d0-t0-01-report#p2@T0 5.s2-d0-03-interview#p1@T0 6.s2-d3-01-interview#p1@T0 7.s2-d1-01-memo#p1@T0 8.s1-d0-05-warn#p2@T0 9.s1-d1-01-report#p3@T0 10.s1-d1-01-memo#p1@T0
- 混合前 10：1.s2-d0-02-interview#p2@T0 2.s2-d0-03-interview#p1@T0 3.s1-d0-05-warn#p2@T0 4.s2-d1-01-memo#p3@T0 5.s2-d3-01-interview#p1@T0 6.s1-d1-01-report#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s2-d1-01-memo#p1@T0 9.s2-d0-02-interview#p3@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.s2-d0-02-interview#p2@T0 2.s2-d3-01-interview#p1@T0 3.s7-d1-t0-03-claim#p1@T0 4.s2-d1-01-memo#p1@T0 5.s2-d0-03-interview#p1@T0 6.s2-d1-01-memo#p3@T0 7.s2-d0-02-interview#p3@T0 8.p1-cac-o11#p1@T0 9.s1-d0-05-warn#p2@T0 10.s1-d1-01-report#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 49. `s2-d0-04-q1`

- 问：T1时点下，该产品线在华东地区的实际销售表现与最初预期有何差异？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-04-memo#p1@T1
- 金标要点：华东地区经销商反映实际订单量低于预期，导致部分门店出现滞销风险；最新渠道反馈显示，尽管初期销售表现强劲，但部分区域出现库存积压问题；实际增幅仅为5%
- 词法前 10：1.s2-d0-04-memo#p1@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s1-d1-01-report#p1@T1 4.s6-d0-t1-02-report#p2@T1 5.s2-d0-03-memo#p2@T1 6.s4-d0-t1-02-report#p2@T1 7.s1-d3-01-memo#p3@T1 8.s2-d2-01-report#p1@T1 9.s2-d1-01-memo#p2@T1 10.s5-d1-t1-03-memo#p2@T1
- 混合前 10：1.s2-d0-04-memo#p1@T1 2.s1-d1-01-report#p1@T1 3.s2-d0-03-memo#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s2-d0-01-report#p1@T1 7.s2-d1-01-report#p3@T1 8.s2-d0-02-report#p2@T1 9.s2-d0-02-memo#p2@T1 10.s5-d1-t1-03-memo#p3@T1
- 重排前 10：1.s2-d0-04-memo#p1@T1 2.s6-d0-t1-02-report#p2@T1 3.s1-d1-01-report#p1@T1 4.s2-d0-03-memo#p2@T1 5.s5-d1-t1-03-memo#p3@T1 6.s2-d1-01-report#p3@T1 7.s6-d0-t1-02-memo#p2@T1 8.s2-d0-01-report#p1@T1 9.s2-d0-02-memo#p2@T1 10.s2-d0-02-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 50. `s2-d0-04-q2`

- 问：暂停了30万台出货计划的那条产品线，从 T0 到 T1 推广策略有哪些关键调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-04-memo#p3@T1
- 金标要点：原定第三季度的全国推广活动已被推迟至第四季度，重点转向解决现有渠道库存与售后问题；强化经销商支持体系
- 词法前 10：1.s2-d0-04-memo#p2@T1 2.s2-d0-03-memo#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-report#p2@T1 6.s2-d2-01-report#p1@T1 7.s5-d2-t1-91-digest#p3@T1 8.s4-d2-t1-04-internal#p1@T1 9.s6-d1-c2-memo#p3@T1 10.s6-d3-t1-03-report#p3@T1
- 混合前 10：1.s2-d0-04-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s2-d0-03-memo#p2@T1 4.s2-d3-01-memo#p2@T1 5.s6-d3-t1-03-report#p3@T1 6.s1-d1-01-report#p1@T1 7.s3-d3-01-report#p2@T1 8.s1-d0-02-report#p2@T1 9.s3-d3-01-memo#p3@T1 10.s2-d0-04-memo#p3@T1
- 重排前 10：1.s2-d0-04-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s2-d0-03-memo#p2@T1 4.s2-d3-01-memo#p2@T1 5.s3-d3-01-report#p2@T1 6.s6-d3-t1-03-report#p3@T1 7.s1-d1-01-report#p1@T1 8.s1-d0-02-report#p2@T1 9.s3-d3-01-memo#p3@T1 10.s2-d0-04-memo#p3@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 51. `s2-d1-01-q1`

- 问：T0 与 T1 版本中关于渠道合作进展的描述有何差异？请指出具体事实变更。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d1-01-memo#p1@T1
- 金标要点：经重新评估，原定新增15家核心分销商的计划已调整为仅拓展6家，主要因部分平台准入；库存同步机制虽已部署，但实际响应延迟仍常超过 6 小时；部分平台准入门槛提高及结算周期延长
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s6-d3-t1-03-report#p2@T1 3.s7-d0-t1-02-claim#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s4-d0-t1-02-review#p1@T1 6.s2-d3-01-memo#p2@T1 7.s4-d0-t1-02-report#p2@T1 8.s4-d0-t1-02-guide#p3@T1 9.s6-d0-t1-01-channel#p3@T1 10.s6-d3-t1-03-memo#p3@T1
- 混合前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d3-t1-03-memo#p3@T1 4.s2-d3-01-memo#p2@T1 5.s2-d2-01-memo#p1@T1 6.s6-d0-t1-02-report#p1@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s2-d0-01-report#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s6-d0-t1-01-channel#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s6-d3-t1-03-memo#p2@T1 3.s6-d3-t1-03-report#p2@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d3-01-memo#p2@T1 6.s2-d2-01-memo#p1@T1 7.s6-d0-t1-01-channel#p1@T1 8.s6-d0-t1-02-report#p1@T1 9.s2-d0-01-report#p3@T1 10.s7-d0-t1-02-brief#p3@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 52. `s2-d1-01-q3`

- 问：短视频互动率掉到18%的那家品牌，T0 与 T1 对线下门店扩张的态度有何变化？反映了怎样的战略调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d1-01-memo#p3@T1
- 金标要点：目前优先考虑现有门店的数字化改造，以提升运营效率而非扩大规模；原计划新开 8 家直营店的方案已被暂缓
- 词法前 10：1.s2-d1-01-report#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s2-d0-01-memo#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s2-d0-01-memo#p2@T1 7.s6-d2-g3-memo#p3@T1 8.s5-d2-t1-91-digest#p3@T1 9.s1-d0-02-memo#p3@T1 10.s2-d1-01-report#p1@T1
- 混合前 10：1.s2-d1-01-report#p2@T1 2.s2-d0-01-memo#p1@T1 3.s3-d0-01-report#p3@T1 4.s2-d3-01-memo#p2@T1 5.s2-d1-01-memo#p3@T1 6.s2-d0-t1-91-interview#p3@T1 7.s2-d3-01-memo#p1@T1 8.s3-d0-01-memo#p3@T1 9.s2-d0-01-memo#p2@T1 10.s2-d1-01-report#p1@T1
- 重排前 10：1.s2-d1-01-report#p2@T1 2.s2-d1-01-report#p1@T1 3.s2-d0-01-memo#p1@T1 4.s3-d0-01-report#p3@T1 5.s2-d3-01-memo#p2@T1 6.s2-d0-t1-91-interview#p3@T1 7.s2-d3-01-memo#p1@T1 8.s2-d0-01-memo#p2@T1 9.s2-d1-01-memo#p3@T1 10.s3-d0-01-memo#p3@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 53. `s2-d2-01-q1`

- 问：T0与T1版本中关于新版本界面的评价有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d2-01-memo#p1@T1
- 金标要点：最新一轮渠道评估表明，新版本界面虽在初期获得好评，但用户实际使用中出现导航路径不清晰的问题；已启动UI重设计
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s2-d2-01-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-guide#p3@T1 6.s4-d2-t1-04-memo#p1@T1 7.s4-d0-t1-02-plan#p3@T1 8.s6-d0-t1-01-channel#p3@T1 9.s1-d1-01-memo#p3@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s2-d2-01-memo#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s1-d1-01-memo#p3@T1 5.s4-d0-t1-02-guide#p3@T1 6.s6-d0-t1-01-channel#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s4-d2-t1-04-memo#p1@T1 9.s4-d0-t1-02-memo#p1@T1 10.s4-d0-t1-02-report#p2@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s2-d2-01-memo#p1@T1 3.s4-d0-t1-02-review#p1@T1 4.s7-d0-t1-02-claim#p3@T1 5.s4-d0-t1-02-memo#p1@T1 6.s4-d0-t1-02-report#p2@T1 7.s1-d1-01-memo#p3@T1 8.s4-d0-t1-02-guide#p3@T1 9.s6-d0-t1-01-channel#p3@T1 10.s4-d2-t1-04-memo#p1@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 54. `s2-d2-01-q2`

- 问：客服平均响应缩短到1.5小时的那家公司，T0 与 T1 关于定价策略的建议是否一致？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d2-01-memo#p2@T1
- 金标要点：经重新核算成本与利润模型，原定阶梯折扣方案被调整为捆绑促销策略，以增强整体收益而非单纯降低售价；该方案已在试点区域上线
- 词法前 10：1.s2-d2-01-report#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s2-d0-t1-91-memo#p2@T1 4.s2-d0-t1-91-interview#p2@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.p1-cac-o20#p8@T1 7.s1-d1-t1-91-brief#p2@T1 8.s1-d1-t1-91-memo#p2@T1 9.s3-d0-03-report#p3@T1 10.s3-d1-01-report#p2@T1
- 混合前 10：1.s2-d2-01-report#p2@T1 2.s4-d2-t1-04-internal#p1@T1 3.s3-d0-01-report#p3@T1 4.s1-d0-01-memo#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s3-d0-03-report#p3@T1 8.s3-d1-01-report#p2@T1 9.s3-d2-01-quotation-snapshot#p2@T1 10.s2-d0-02-report#p3@T1
- 重排前 10：1.s2-d2-01-report#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s2-d0-t1-91-memo#p2@T1 4.s3-d2-01-quotation-snapshot#p2@T1 5.s4-d2-t1-04-internal#p1@T1 6.s3-d0-01-report#p3@T1 7.s1-d0-01-memo#p2@T1 8.s3-d0-03-report#p3@T1 9.s3-d1-01-report#p2@T1 10.s2-d0-02-report#p3@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 55. `s2-d3-01-q1`

- 问：T0 与 T1 版本中关于渠道合作目标的变化是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-memo#p1@T1
- 金标要点：经重新评估，原定 15% 的用户增长目标已调整为 8%，主要因市场环境变化及渠道反馈实际转化率低于预期；后续策略将更注重质量而非数量
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s2-d3-01-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s2-d3-01-memo#p2@T1 6.s4-d0-t1-02-guide#p3@T1 7.s6-d3-t1-03-report#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.p1-cac-o20#p8@T1 10.s5-d1-t1-03-note#p2@T1
- 混合前 10：1.s2-d3-01-memo#p2@T1 2.s2-d3-01-interview#p1@T1 3.s2-d2-01-memo#p1@T1 4.s6-d3-t1-03-report#p2@T1 5.s6-d0-t1-01-channel#p1@T1 6.s1-d0-02-memo#p1@T1 7.s2-d0-01-memo#p1@T1 8.s4-d0-t1-02-plan#p3@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s2-d3-01-memo#p2@T1 3.s2-d2-01-memo#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s2-d3-01-memo#p1@T1 6.s2-d3-01-interview#p1@T1 7.s6-d3-t1-03-report#p2@T1 8.s1-d0-02-memo#p1@T1 9.s2-d0-01-memo#p1@T1 10.s4-d0-t1-02-plan#p3@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 56. `s2-d3-01-q2`

- 问：T1 版本中为何原定的合作渠道数量减少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-memo#p2@T1
- 金标要点：原计划中的两家核心渠道中，仅电商平台明确继续推进，垂直类应用因战略调整已退出合作；目前合作方数量缩减至单一
- 词法前 10：1.s2-d3-01-memo#p2@T1 2.s2-d3-01-memo#p1@T1 3.s6-d3-t1-03-report#p2@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s2-d0-01-report#p3@T1 6.s2-d3-01-interview#p2@T1 7.s2-d0-04-memo#p3@T1 8.s4-d0-t1-02-guide#p3@T1 9.p1-colaw-liquidation#p5@T1 10.s2-d2-01-memo#p1@T1
- 混合前 10：1.s2-d3-01-memo#p2@T1 2.s2-d0-01-report#p3@T1 3.s6-d3-t1-03-report#p2@T1 4.s2-d0-04-memo#p3@T1 5.s2-d3-01-interview#p2@T1 6.s4-d2-t1-04-report#p2@T1 7.s2-d2-01-memo#p1@T1 8.s2-d0-02-report#p1@T1 9.s1-d3-01-report#p3@T1 10.s2-d0-01-memo#p1@T1
- 重排前 10：1.s2-d3-01-memo#p2@T1 2.s2-d2-01-memo#p1@T1 3.s2-d0-01-report#p3@T1 4.s6-d3-t1-03-report#p2@T1 5.s2-d0-04-memo#p3@T1 6.s2-d3-01-interview#p2@T1 7.s4-d2-t1-04-report#p2@T1 8.s2-d0-02-report#p1@T1 9.s1-d3-01-report#p3@T1 10.s2-d0-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 57. `s2-d3-01-q4`

- 问：高管在两次访谈中对渠道拓展策略的表述有何根本性转变？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-interview#p1@T1
- 金标要点：CEO 改口称，由于外部竞争加剧，公司战略将转向“精耕细作”，新渠道拓展目标下调至覆盖 25% 的关键市场；不再追求广泛铺开
- 词法前 10：1.s2-d3-01-interview#p1@T1 2.s6-d3-t1-01-note#p2@T1 3.s7-d3-t1-05-synthetic#p3@T1 4.s2-d0-t1-91-interview#p1@T1 5.s7-d3-t1-05-synthetic#p1@T1 6.s2-d3-01-memo#p1@T1 7.s7-d2-t1-04-brief#p2@T1 8.s2-d3-t1-91-interview#p2@T1 9.s2-d0-t1-91-interview#p3@T1 10.s2-d3-01-interview#p2@T1
- 混合前 10：1.s2-d3-01-interview#p1@T1 2.s2-d3-01-memo#p1@T1 3.s5-d3-t1-05-analysis#p3@T1 4.s1-d0-02-memo#p1@T1 5.s2-d0-03-interview#p1@T1 6.s6-d0-t1-01-channel#p1@T1 7.s2-d3-01-memo#p2@T1 8.s2-d0-01-memo#p1@T1 9.s2-d0-t1-91-interview#p3@T1 10.s5-d1-t1-03-memo#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s5-d1-t1-03-memo#p1@T1 3.s2-d3-01-interview#p1@T1 4.s2-d3-01-memo#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s2-d3-01-memo#p2@T1 7.s2-d0-t1-91-interview#p3@T1 8.s1-d0-02-memo#p1@T1 9.s2-d0-01-memo#p1@T1 10.s2-d0-03-interview#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 58. `s3-d0-01-q2`

- 问：竞品B在T1阶段新增了哪些服务功能？其价格如何调整？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-01-memo#p2@T1
- 金标要点：竞品B在高端套餐基础上新增家庭共享功能，价格上调至每月219元，尽管涨幅明显，但用户留存率仍维持在92%以上
- 词法前 10：1.s3-d0-01-memo#p2@T1 2.s3-d1-01-report#p2@T1 3.s3-d1-01-memo#p2@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s3-d0-01-report#p3@T1 6.s3-d0-02-a#p2@T1 7.s3-d0-04-memo#p1@T1 8.s3-d0-03-memo#p2@T1 9.s3-d0-01-report#p2@T1 10.s3-d3-01-report#p2@T1
- 混合前 10：1.s3-d0-04-memo#p1@T1 2.s3-d1-01-report#p2@T1 3.s3-d0-01-memo#p2@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-03-memo#p2@T1 6.s3-d0-03-memo#p1@T1 7.s3-d1-01-memo#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p2@T1 10.s3-d2-01-competitor-pricing#p2@T1
- 重排前 10：1.s3-d0-01-memo#p2@T1 2.s3-d1-01-memo#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d0-04-memo#p1@T1 5.s3-d1-01-report#p2@T1 6.s3-d3-01-report#p2@T1 7.s3-d0-03-memo#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p2@T1 10.s3-d0-03-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 59. `s3-d0-01-q3`

- 问：在流量通话套餐比价里（竞品B新增家庭共享的那份），竞品C 在 T0 与 T1 之间调整了促销策略吗？具体变化是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-01-memo#p3@T1
- 金标要点：竞品C已于本季度初结束促销活动，标准套餐恢复至每月99元，且推出捆绑视频会员的新组合方案
- 词法前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-01-memo#p1@T1 5.s5-d2-t1-91-digest#p3@T1 6.s7-d0-t1-02-analysis#p3@T1 7.s3-d0-03-memo#p2@T1 8.s3-d3-01-report#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d3-01-memo#p3@T1
- 混合前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-memo#p1@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d0-04-memo#p2@T1 6.s3-d0-03-memo#p2@T1 7.s3-d3-01-memo#p3@T1 8.s3-d3-01-report#p2@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p2@T1
- 重排前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-01-memo#p1@T1 6.s3-d0-04-memo#p2@T1 7.s3-d0-03-memo#p2@T1 8.s3-d3-01-memo#p3@T1 9.s3-d1-01-report#p2@T1 10.s3-d3-01-memo#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 60. `s3-d0-02-q1`

- 问：在A、B、C三家公司的基础版比价中，T0 时A公司的基础版定价是多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p1@T0；s3-d0-02-b#p1@T0；s3-d0-02-c#p1@T0
- 金标要点：A公司推出基础版服务，定价为每月99元，包含核心功能模块，支持5个用户席位；基础款月费99元；A公司以99元定位形成价格优势
- 词法前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-b#p3@T0 3.s3-d0-04-memo#p3@T0 4.s3-d1-01-memo#p2@T0 5.s3-d0-03-memo#p1@T0 6.s3-d0-04-memo#p1@T0 7.s3-d0-02-b#p1@T0 8.s3-d0-01-report#p1@T0 9.s3-d0-03-report#p1@T0 10.s3-d3-01-memo#p1@T0
- 混合前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-04-memo#p3@T0 3.s3-d1-01-memo#p2@T0 4.s3-d0-03-memo#p1@T0 5.s3-d0-04-memo#p1@T0 6.s3-d0-02-c#p1@T0 7.s3-d3-01-memo#p1@T0 8.s3-d0-01-report#p1@T0 9.s3-d0-01-memo#p1@T0 10.s3-d0-03-report#p1@T0
- 重排前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-04-memo#p1@T0 4.s3-d3-01-memo#p1@T0 5.s3-d0-01-report#p1@T0 6.s3-d0-04-memo#p3@T0 7.s3-d1-01-memo#p2@T0 8.s3-d0-01-memo#p1@T0 9.s3-d0-03-report#p1@T0 10.s3-d0-02-c#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 61. `s3-d0-02-q2`

- 问：T1时B公司是否降低了其标准版的月费？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p2@T1；s3-d0-02-b#p2@T1；s3-d0-02-c#p2@T1
- 金标要点：B公司宣布全面降价，标准版降至109元/月，取消独立报表工具，转而整合入主控台，优化系统性能并降低运维门槛；B公司下调基础套餐价格至每月109元，移除部分高级功能以控制成本，但维持8人用户上限；B公司经过价格下调后
- 词法前 10：1.s3-d0-02-b#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d0-02-c#p2@T1 6.s3-d3-01-memo#p2@T1 7.s3-d1-01-memo#p2@T1 8.s3-d0-02-a#p2@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.p1-colaw-liquidation#p1@T1
- 混合前 10：1.s3-d0-02-b#p2@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d3-01-memo#p2@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d0-02-a#p2@T1 6.s3-d1-01-memo#p2@T1 7.s3-d0-04-memo#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d2-01-competitor-pricing#p3@T1
- 重排前 10：1.s3-d0-02-b#p2@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d3-01-memo#p2@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d0-02-a#p2@T1 6.s3-d1-01-memo#p2@T1 7.s3-d0-04-memo#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d2-01-competitor-pricing#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 62. `s3-d0-02-q3`

- 问：C公司在T0时提供的基础版是否包含客户支持？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T0
- 金标要点：C公司以低价切入市场，基础版仅售每月69元，但限制功能数量，且不提供客户支持；尽管性价比突出，但用户反馈对长期维护能力存疑
- 词法前 10：1.s3-d0-02-a#p3@T0 2.s3-d0-02-a#p1@T0 3.s3-d0-04-memo#p1@T0 4.s3-d0-02-b#p3@T0 5.s3-d0-03-report#p1@T0 6.s3-d2-01-quotation-snapshot#p1@T0 7.s3-d0-03-memo#p1@T0 8.s3-d1-01-memo#p2@T0 9.s3-d1-01-memo#p1@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-b#p3@T0 3.s3-d0-02-a#p3@T0 4.s7-d0-t0-01-qa#p2@T0 5.s3-d0-04-memo#p1@T0 6.s3-d2-01-quotation-snapshot#p1@T0 7.s3-d0-03-memo#p1@T0 8.s3-d0-02-c#p3@T0 9.s2-d0-02-interview#p1@T0 10.s3-d0-03-report#p1@T0
- 重排前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-a#p3@T0 3.s3-d0-04-memo#p1@T0 4.s3-d0-03-memo#p1@T0 5.s3-d0-03-report#p1@T0 6.s3-d0-02-b#p3@T0 7.s3-d2-01-quotation-snapshot#p1@T0 8.s2-d0-02-interview#p1@T0 9.s7-d0-t0-01-qa#p2@T0 10.s3-d0-02-c#p3@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 63. `s3-d0-02-q4`

- 问：T1时A公司基础版新增了哪些核心功能？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p1@T1；s3-d0-02-b#p1@T1
- 金标要点：新增团队协作工具；新增实时协同编辑与自动化工作流引擎
- 词法前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d2-01-quotation-snapshot#p1@T1 4.s3-d1-01-memo#p2@T1 5.s3-d0-02-c#p1@T1 6.s3-d0-02-a#p2@T1 7.s3-d0-04-memo#p1@T1 8.s3-d0-04-memo#p3@T1 9.s3-d3-01-memo#p1@T1 10.s3-d0-01-memo#p2@T1
- 混合前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-02-b#p3@T1 5.s4-d0-t1-02-guide#p3@T1 6.s6-d1-t1-91-release#p3@T1 7.s3-d0-02-a#p2@T1 8.s6-d0-t1-01-channel#p3@T1 9.s3-d0-03-memo#p2@T1 10.s3-d0-02-c#p1@T1
- 重排前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-02-a#p2@T1 5.s3-d0-02-c#p1@T1 6.s3-d0-02-b#p3@T1 7.s6-d1-t1-91-release#p3@T1 8.s6-d0-t1-01-channel#p3@T1 9.s3-d0-03-memo#p2@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 64. `s3-d0-02-q5`

- 问：在A、B、C三家公司的比价里，T0 时哪一家的定价低于90元？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T0；s3-d0-02-b#p3@T0；s3-d0-02-c#p3@T0
- 金标要点：C公司以低价切入市场，基础版仅售每月69元；C公司以69元最低价进入市场；C公司依托开源生态，推出免费基础版
- 词法前 10：1.s3-d0-03-memo#p1@T0 2.s3-d0-04-memo#p1@T0 3.p1-colaw-liquidation#p1@T0 4.s3-d0-02-c#p3@T0 5.s3-d3-01-report#p2@T0 6.p1-colaw-governance-supervisor-js#p1@T0 7.p1-colaw-capital#p1@T0 8.p1-colaw-governance-supervisor#p1@T0 9.s3-d0-01-report#p1@T0 10.p1-cac-o11#p10@T0
- 混合前 10：1.s3-d0-04-memo#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-02-c#p3@T0 4.s3-d0-01-report#p1@T0 5.s3-d3-01-report#p2@T0 6.s3-d1-01-memo#p2@T0 7.s3-d0-04-memo#p3@T0 8.s3-d0-02-c#p2@T0 9.s3-d0-01-memo#p2@T0 10.s3-d0-02-c#p1@T0
- 重排前 10：1.s3-d0-04-memo#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-01-report#p1@T0 4.s3-d0-01-memo#p2@T0 5.s3-d0-02-c#p3@T0 6.s3-d3-01-report#p2@T0 7.s3-d1-01-memo#p2@T0 8.s3-d0-02-c#p2@T0 9.s3-d0-04-memo#p3@T0 10.s3-d0-02-c#p1@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 65. `s3-d0-02-q6`

- 问：T1时C公司是否仍然提供免费的基础版本？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-b#p3@T1；s3-d0-02-a#p3@T1
- 金标要点：C公司关闭免费基础版入口，改推“成长计划”订阅制，首年费用149元，含全功能访问及优先技术支持；C公司因技术债务问题暂停新客户注册，原69元套餐已取消，现仅开放限时试用，正式版本将于下季度以149元起售
- 词法前 10：1.s3-d0-02-b#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d0-02-b#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s3-d0-02-a#p3@T1 8.s3-d0-03-report#p1@T1 9.s3-d3-01-report#p3@T1 10.s3-d0-02-a#p1@T1
- 混合前 10：1.s3-d0-02-b#p3@T1 2.s3-d0-02-b#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d0-02-a#p1@T1 5.s3-d0-02-a#p3@T1 6.s3-d0-04-memo#p3@T1 7.s3-d2-t1-91-brochure#p1@T1 8.s3-d0-03-report#p1@T1 9.s4-d0-t1-02-guide#p3@T1 10.s3-d3-01-report#p3@T1
- 重排前 10：1.s3-d0-02-b#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d0-02-b#p1@T1 4.s3-d0-02-a#p1@T1 5.s3-d0-02-a#p3@T1 6.s3-d2-t1-91-brochure#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d3-01-report#p3@T1 9.s3-d0-04-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 66. `s3-d0-03-q2`

- 问：竞品B 的“精英版”套餐在 T1 有哪些新优惠或功能调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-03-memo#p2@T1
- 金标要点：竞品B更新其“精英版”套餐，新增30天免费试用，并将价格调整为每月420元，市场推广力度加大
- 词法前 10：1.s3-d0-03-memo#p2@T1 2.s3-d1-01-memo#p2@T1 3.s3-d0-03-report#p2@T1 4.s3-d0-01-memo#p2@T1 5.s3-d0-01-report#p2@T1 6.s3-d3-01-memo#p2@T1 7.s3-d0-04-memo#p2@T1 8.s3-d1-01-report#p2@T1 9.s7-d3-t1-05-claim#p1@T1 10.s3-d0-02-a#p2@T1
- 混合前 10：1.s3-d0-03-memo#p2@T1 2.s3-d0-04-memo#p2@T1 3.s3-d0-01-memo#p2@T1 4.s3-d3-01-memo#p2@T1 5.s3-d0-03-report#p2@T1 6.s3-d0-01-memo#p3@T1 7.s3-d1-01-memo#p2@T1 8.s3-d2-01-competitor-pricing#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d1-01-memo#p1@T1
- 重排前 10：1.s3-d0-03-memo#p2@T1 2.s3-d0-03-report#p2@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-01-memo#p2@T1 5.s3-d2-01-competitor-pricing#p2@T1 6.s3-d0-04-memo#p2@T1 7.s3-d0-01-memo#p3@T1 8.s3-d1-01-report#p2@T1 9.s3-d3-01-memo#p2@T1 10.s3-d1-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 67. `s3-d0-03-q3`

- 问：我方主推套餐在T0和T1之间是否有价格或服务内容的变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-03-memo#p3@T1
- 金标要点：我方主推套餐维持每月380元不变，但新增一项“客户忠诚计划”作为附加价值，涵盖额外培训资源
- 词法前 10：1.s3-d0-03-report#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d0-03-memo#p3@T1 4.s7-d3-t1-05-memo#p3@T1 5.p1-colaw-equity#p1@T1 6.s3-d1-01-report#p1@T1 7.s1-d0-01-analysis#p2@T1 8.s5-d2-t1-91-digest#p3@T1 9.s3-d0-01-memo#p2@T1 10.s7-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s3-d0-03-memo#p3@T1 2.s3-d1-01-report#p1@T1 3.s3-d0-03-report#p3@T1 4.s3-d0-01-memo#p2@T1 5.s3-d0-04-memo#p3@T1 6.s3-d0-03-memo#p1@T1 7.s3-d3-01-memo#p1@T1 8.s3-d3-01-report#p1@T1 9.s1-d0-01-analysis#p2@T1 10.s3-d0-02-a#p2@T1
- 重排前 10：1.s3-d0-03-report#p3@T1 2.s3-d0-03-memo#p3@T1 3.s3-d1-01-report#p1@T1 4.s3-d0-01-memo#p2@T1 5.s1-d0-01-analysis#p2@T1 6.s3-d0-04-memo#p3@T1 7.s3-d0-03-memo#p1@T1 8.s3-d3-01-memo#p1@T1 9.s3-d3-01-report#p1@T1 10.s3-d0-02-a#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 68. `s3-d1-01-q1`

- 问：在竞品C年度订阅价2,800元的那份比价中，竞品A 在 T1 的价格策略有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d1-01-memo#p1@T1；s3-d1-01-report#p1@T1
- 金标要点：竞品A已完成服务整合，将原独立模块打包进主套餐，价格上调至349元/月，但用户满意度调查显示其综合性价比获得认可；至本周期末，竞品A已将基础套餐调涨至每月349元，并将高级功能模块纳入主套餐内，不再单独计价
- 词法前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d1-01-report#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p1@T1 7.s3-d0-01-report#p1@T1 8.s3-d3-01-memo#p1@T1 9.s3-d0-01-memo#p3@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-03-report#p1@T1 5.s3-d3-01-report#p1@T1 6.s3-d1-01-report#p3@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p1@T1
- 重排前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d3-01-report#p1@T1 5.s3-d0-03-report#p1@T1 6.s3-d1-01-report#p3@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p1@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 69. `s3-d1-01-q3`

- 问：年度订阅价2,800元的那个竞品C，T0 时提供什么订阅方式？T1 又增加了哪些新选项？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d1-01-memo#p3@T1
- 金标要点：竞品C推出按月订阅选项，月费为269元，同时保留年度优惠价2,800元，进一步增强对中小客户的吸引力
- 词法前 10：1.s3-d1-01-memo#p3@T1 2.s3-d1-01-report#p3@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s3-d2-01-competitor-pricing#p2@T1 6.s3-d0-01-report#p3@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s3-d2-01-competitor-pricing#p3@T1 9.s3-d0-01-memo#p3@T1 10.s3-d0-03-report#p2@T1
- 混合前 10：1.s3-d1-01-memo#p3@T1 2.s3-d1-01-report#p3@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-03-report#p2@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d2-01-competitor-pricing#p2@T1 7.s3-d3-01-report#p1@T1 8.s3-d0-01-memo#p3@T1 9.s3-d0-03-report#p1@T1 10.s3-d0-02-b#p3@T1
- 重排前 10：1.s3-d1-01-memo#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d0-01-memo#p3@T1 4.s3-d1-01-report#p3@T1 5.s3-d3-01-memo#p3@T1 6.s3-d0-03-report#p2@T1 7.s3-d0-03-report#p1@T1 8.s3-d1-t1-91-quote#p3@T1 9.s3-d3-01-report#p1@T1 10.s3-d0-02-b#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 70. `s3-d2-01-q2`

- 问：在竞品C月费调到195元的那份比价里，以自动化报告为卖点的竞品B，T1 相比 T0 增加了哪些新服务内容？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d2-01-competitor-pricing#p2@T1
- 金标要点：竞品B在新版本基础上增加30天免费试用期，并将月费降至229元，同时优化了报告生成算法；显著提升响应速度
- 词法前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d0-04-memo#p2@T1 3.s3-d3-01-report#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s6-d0-t1-03-report#p3@T1 8.s3-d0-01-report#p3@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-04-memo#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-memo#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s3-d0-03-report#p1@T1 9.s3-d3-01-memo#p2@T1 10.s3-d0-01-report#p3@T1
- 重排前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-04-memo#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-memo#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s3-d0-03-report#p1@T1 9.s3-d0-01-report#p3@T1 10.s3-d3-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 71. `s3-d2-01-q3`

- 问：我方基础版服务包在T1时的定价与服务范围是否发生变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d2-01-quotation-snapshot#p1@T1
- 金标要点：基础版服务包价格上调至每月189元，巡检周期由月度改为双周一次，同时新增云端日志分析功能
- 词法前 10：1.s3-d0-03-report#p3@T1 2.s3-d0-04-memo#p3@T1 3.s3-d0-03-memo#p1@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s1-d0-01-analysis#p2@T1 7.s4-d0-t1-02-review#p2@T1 8.s3-d0-02-a#p1@T1 9.s6-d0-t1-03-report#p3@T1 10.s3-d2-01-quotation-snapshot#p2@T1
- 混合前 10：1.s3-d0-04-memo#p3@T1 2.s3-d0-03-memo#p1@T1 3.s3-d0-03-report#p3@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s3-d1-01-memo#p2@T1 8.s1-d0-01-analysis#p2@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s4-d0-t1-02-review#p2@T1
- 重排前 10：1.s3-d0-04-memo#p3@T1 2.s3-d0-03-memo#p1@T1 3.s3-d0-03-report#p3@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s3-d2-01-quotation-snapshot#p1@T1 6.s3-d2-01-quotation-snapshot#p2@T1 7.s3-d1-01-memo#p2@T1 8.s1-d0-01-analysis#p2@T1 9.s4-d0-t1-02-review#p2@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 72. `s3-d3-01-q3`

- 问：在竞品A附带云存储的那份比价里，竞品C的报价结构在T1相比T0发生了哪些关键调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p3@T1；s3-d3-01-report#p3@T1
- 金标要点：竞品C的报价结构已完成标准化改革，所有功能模块统一纳入89元基础包，有效降低用户决策成本；竞品C调整订阅策略，取消阶梯加价，统一为89元/月，涵盖全部功能模块，价格透明度大幅提升
- 词法前 10：1.s3-d3-01-memo#p1@T1 2.s3-d3-01-report#p3@T1 3.s3-d3-01-report#p2@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-01-report#p3@T1 8.s3-d1-t1-91-quote#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 混合前 10：1.s3-d3-01-memo#p1@T1 2.s3-d3-01-report#p3@T1 3.s3-d3-01-report#p2@T1 4.s3-d0-01-report#p3@T1 5.s3-d1-t1-91-quote#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-t1-91-pricesheet#p3@T1 8.s3-d0-03-report#p1@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 重排前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-01-report#p3@T1 4.s3-d3-01-memo#p1@T1 5.s3-d1-t1-91-quote#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d2-01-competitor-pricing#p1@T1 9.s3-d1-t1-91-pricesheet#p2@T1 10.s3-d1-t1-91-pricesheet#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 73. `s3-d3-01-q4`

- 问：在竞品C统一为89元基础包的那份比价里，从 T0 到 T1 各竞品的定价策略如何影响其市场定位？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p3@T1；s3-d3-01-report#p1@T1；s3-d3-01-report#p2@T1
- 金标要点：竞品A已全面推行新版套餐，价格上调至119元/月，同时增加企业级安全认证，目标客户转向中大型组织；竞品B的报价策略发生重大调整，取消固定高价，转而采用按需计费模式，月费最低可至99元，配合灵活服务包，大幅增强市场渗透力；竞品C调整订阅策略，取消阶梯加价，统一为89元/月，涵盖全部功能模块，价格透明度大幅提升，吸引大量中小客户迁移
- 词法前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d3-01-report#p2@T1 6.s3-d1-01-memo#p3@T1 7.s3-d0-01-report#p1@T1 8.s3-d1-01-memo#p2@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-report#p2@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d0-01-report#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d0-03-memo#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s3-d1-01-memo#p3@T1
- 重排前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-01-report#p3@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-01-memo#p3@T1 8.s3-d0-01-report#p1@T1 9.s3-d0-03-report#p1@T1 10.s3-d0-03-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 74. `s4-d0-t0-01-q1`

- 问：v2.3 版成本模型相比旧版在哪些方面实现了性能提升？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p1@T0；s4-d0-t0-01-memo#p2@T0；s4-d0-t0-01-report#p1@T0；s4-d0-t0-01-report#p3@T0
- 金标要点：新模型的准确率从76%提升至89%；模型运行时长由平均4.7秒降至2.3秒；平均误差率下降至3.2%，较上一版本降低1.8个百分点；日均处理效率提升约15%
- 词法前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-report#p3@T0 6.s4-d3-t0-05-summary#p1@T0 7.s1-d0-02-report#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d0-t0-01-plan#p1@T0
- 混合前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d3-t0-05-summary#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s4-d0-t0-01-report#p3@T0 5.s4-d1-t0-03-memo#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d3-t0-05-memo#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d3-t0-05-summary#p1@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-summary#p1@T0 8.s4-d0-t0-01-report#p3@T0 9.s4-d3-t0-05-memo#p2@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 75. `s4-d0-t0-01-q2`

- 问：为何在高层会议中使用旧版模型的决策方案被质疑？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-analysis#p2@T0
- 金标要点：在高层管理会议中，使用T0模型的决策方案被质疑为过于保守；而新模型提供更精细的成本拆解，有助于识别隐藏成本点，提升资源配置透明度
- 词法前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s4-d0-t0-01-report#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s5-d0-t0-01-internal#p3@T0 5.s3-d3-01-report#p3@T0 6.s5-d0-t0-01-internal#p1@T0 7.p1-colaw-governance#p2@T0 8.s4-d0-t0-01-summary#p1@T0 9.p1-colaw-equity#p5@T0 10.s2-d0-03-memo#p1@T0
- 混合前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s5-d0-t0-01-internal#p1@T0 3.s4-d0-t0-01-report#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s3-d3-01-report#p3@T0 7.s7-d1-t0-03-reason#p1@T0 8.s4-d1-t0-03-analysis#p1@T0 9.s4-d0-t0-01-summary#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s4-d0-t0-01-report#p1@T0 3.s5-d0-t0-01-internal#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s7-d1-t0-03-reason#p1@T0 7.s3-d3-01-report#p3@T0 8.s4-d1-t0-03-analysis#p1@T0 9.s4-d0-t0-01-summary#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 76. `s4-d0-t0-01-q3`

- 问：新模型在处理非标准流程时存在什么局限性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p3@T0
- 金标要点：当前模型仍存在对非标准流程的覆盖不足问题
- 词法前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d1-t0-03-memo#p1@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s4-d1-t0-03-report#p3@T0 8.s5-d0-t0-01-report#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d1-t0-03-analysis#p3@T0
- 混合前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d0-t0-01-summary#p1@T0 5.s4-d0-t0-01-summary#p3@T0 6.s4-d0-t0-01-report#p1@T0 7.s4-d1-t0-03-analysis#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d1-t0-03-memo#p1@T0 10.s1-d3-01-memo#p2@T0
- 重排前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d1-t0-03-memo#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d0-t0-01-report#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-summary#p3@T0 9.s4-d1-t0-03-analysis#p3@T0 10.s1-d3-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 77. `s4-d0-t0-01-q4`

- 问：为确保模型平滑过渡，已采取哪些协同措施？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-plan#p3@T0
- 金标要点：已启动跨团队协作机制，确保模型变更前完成影响评估与沟通预案，保障平滑过渡
- 词法前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d0-03-report#p3@T0 3.s1-d0-03-memo#p3@T0 4.s1-d0-04-memo#p2@T0 5.s1-d3-01-memo#p3@T0 6.p1-colaw-capital#p2@T0 7.s3-d0-03-report#p2@T0 8.s7-d0-t0-01-qa#p2@T0 9.s1-d2-01-analysis#p1@T0 10.s4-d1-t0-03-report#p3@T0
- 混合前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d3-01-memo#p3@T0 3.s1-d0-04-memo#p2@T0 4.s4-d0-t0-01-memo#p3@T0 5.s4-d0-t0-01-summary#p2@T0 6.s4-d0-t0-01-summary#p3@T0 7.s4-d0-t0-01-report#p1@T0 8.s1-d0-03-report#p3@T0 9.s4-d1-t0-03-analysis#p1@T0 10.s1-d0-03-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d0-03-report#p3@T0 3.s1-d3-01-memo#p3@T0 4.s1-d0-04-memo#p2@T0 5.s1-d0-03-memo#p3@T0 6.s4-d0-t0-01-memo#p3@T0 7.s4-d0-t0-01-summary#p2@T0 8.s4-d0-t0-01-summary#p3@T0 9.s4-d0-t0-01-report#p1@T0 10.s4-d1-t0-03-analysis#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 78. `s4-d0-t0-01-q5`

- 问：v2.3 版成本模型在哪些业务场景下表现出更强的适应性？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p2@T0；s4-d0-t0-01-report#p1@T0；s4-d0-t0-01-summary#p2@T0
- 金标要点：在复杂项目核算中，新模型的准确率从76%提升至89%；尤其在原材料价格波动场景下保持稳定输出；尤其在高负载时段表现更稳定
- 词法前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d0-t0-01-summary#p2@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d3-t0-05-memo#p1@T0 6.s4-d3-t0-05-summary#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d3-t0-05-analysis#p1@T0 10.s4-d0-t0-01-memo#p2@T0
- 混合前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d0-t0-01-summary#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s4-d3-t0-05-memo#p1@T0 5.s4-d3-t0-05-summary#p1@T0 6.s4-d0-t0-01-summary#p2@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 79. `s4-d0-t0-01-q6`

- 问：多方反馈中提出的三个改进建议分别是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-feedback#p1@T0；s4-d0-t0-01-feedback#p2@T0；s4-d0-t0-01-feedback#p3@T0
- 金标要点：来自财务部反馈：希望增加“人工工时”维度的细分统计，以便更精确地分配间接人力成本；技术团队建议：应明确模型版本标识规则，避免在报表中出现混淆引用；运营部门提出：期望在模型中加入季节性因子调节功能，以应对周期性业务高峰
- 词法前 10：1.s5-d0-t0-01-internal#p2@T0 2.s1-d0-05-warn#p1@T0 3.s4-d0-t0-01-feedback#p3@T0 4.s5-d0-t0-01-memo#p3@T0 5.s1-d0-01-memo#p2@T0 6.s5-d2-t0-04-analysis#p2@T0 7.s5-d0-t0-01-internal#p1@T0 8.s4-d3-t0-05-analysis#p1@T0 9.s2-d0-01-report#p2@T0 10.s4-d0-t0-01-report#p2@T0
- 混合前 10：1.s1-d0-05-warn#p1@T0 2.s5-d0-t0-01-memo#p3@T0 3.s5-d0-t0-01-internal#p2@T0 4.s2-d0-01-report#p2@T0 5.s1-d0-01-memo#p2@T0 6.s5-d0-t0-01-internal#p1@T0 7.s4-d0-t0-01-analysis#p3@T0 8.s2-d0-02-memo#p3@T0 9.s1-d1-01-memo#p3@T0 10.s2-d2-01-memo#p1@T0
- 重排前 10：1.s1-d0-01-memo#p2@T0 2.s2-d2-01-memo#p1@T0 3.s1-d0-05-warn#p1@T0 4.s5-d0-t0-01-memo#p3@T0 5.s5-d0-t0-01-internal#p2@T0 6.s2-d0-01-report#p2@T0 7.s5-d0-t0-01-internal#p1@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s2-d0-02-memo#p3@T0 10.s1-d1-01-memo#p3@T0
- 建议：保持 bm25
- 理由：词法的前 10 条里有金标，重排没有。

### 80. `s4-d0-t1-02-q1`

- 问：计划11月启动全量灰度的那版成本模型，T1 版本相比 T0 版本有哪些改进？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-memo#p1@T1；s4-d0-t1-02-memo#p2@T1；s4-d0-t1-02-report#p2@T1
- 金标要点：预测准确率从76.3%升至89.1%；引入动态分摊算法以提升跨项目资源分配的准确性；对人力工时与设备折旧的非线性权重调整
- 词法前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d2-t1-04-internal#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-review#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d2-t1-04-report#p1@T1 9.s4-d0-t1-02-review#p1@T1 10.s4-d0-t1-02-memo#p1@T1
- 混合前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d2-t1-04-memo#p3@T1 8.s6-d0-t1-03-memo#p2@T1 9.s4-d2-t1-04-summary#p1@T1 10.s3-d2-01-competitor-pricing#p2@T1
- 重排前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s4-d2-t1-04-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 81. `s4-d0-t1-02-q2`

- 问：计划11月全量灰度的那版成本模型，在高并发场景下的预测表现如何？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-memo#p2@T1；s4-d0-t1-02-report#p2@T1
- 金标要点：特别强化了高并发场景下的弹性成本预测能力；平均预算偏差减少28%；预测准确率从76.3%升至89.1%
- 词法前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d0-t1-02-memo#p2@T1 4.s4-d0-t1-02-plan#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s2-d3-01-memo#p3@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-report#p1@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s1-d3-01-memo#p3@T1
- 混合前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-plan#p1@T1 9.s4-d2-t1-04-summary#p1@T1 10.s4-d2-t1-04-summary#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d0-t1-02-plan#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-plan#p1@T1 9.s4-d2-t1-04-summary#p2@T1 10.s4-d2-t1-04-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 82. `s4-d0-t1-02-q3`

- 问：为何新版本在低频任务中出现预算预留增加？其优势是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-analysis#p2@T1；s4-d0-t1-02-analysis#p3@T1
- 金标要点：在低频任务中，新版模型倾向于保守估计，导致预算预留增加约7.6%，但有效避免了超支风险；该策略已被运营团队采纳为标准配置；整体风险控制收益远超成本波动影响
- 词法前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s3-d0-02-c#p2@T1 5.s2-d2-01-memo#p1@T1 6.s4-d0-t1-02-review#p1@T1 7.s2-d2-01-memo#p3@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-claim#p3@T1 10.s3-d0-03-report#p2@T1
- 混合前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s2-d2-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d0-t1-02-report#p1@T1 8.s4-d0-t1-02-memo#p2@T1 9.s4-d0-t1-02-review#p2@T1 10.s2-d2-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s2-d2-01-memo#p1@T1 5.s4-d0-t1-02-memo#p1@T1 6.s2-d2-01-memo#p3@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-report#p1@T1 9.s4-d0-t1-02-memo#p2@T1 10.s4-d0-t1-02-review#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 83. `s4-d0-t1-02-q4`

- 问：成本模型的下一步迭代路线图包含哪些关键任务？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-plan#p1@T1；s4-d0-t1-02-plan#p2@T1；s4-d0-t1-02-plan#p3@T1
- 金标要点：本年度模型优化计划聚焦三大方向：一是增强对异构硬件的成本映射能力，二是建立实时反馈闭环以动态修正参数；路线图明确要求每季度进行一次跨部门验证，确保模型适应实际业务变化；整合外部市场数据源实现成本趋势预警；模型可解释性模块的开发
- 词法前 10：1.s4-d2-t1-04-summary#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d2-t1-04-memo#p1@T1 5.s6-d0-t1-03-internal#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-report#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s6-d0-t1-02-memo#p3@T1 10.s6-d0-t1-02-report#p3@T1
- 混合前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d2-t1-04-summary#p3@T1 4.s4-d0-t1-02-plan#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d0-t1-02-analysis#p1@T1 9.s6-d0-t1-03-internal#p2@T1 10.s4-d2-t1-04-internal#p3@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s4-d2-t1-04-summary#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d2-t1-04-internal#p3@T1 10.s4-d0-t1-02-plan#p3@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 84. `s4-d0-t1-02-q5`

- 问：使用T1版本模型时，用户需要注意哪些操作规范？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-guide#p1@T1；s4-d0-t1-02-guide#p2@T1；s4-d0-t1-02-guide#p3@T1
- 金标要点：本指南更新内容涵盖新模型的参数配置方法、典型场景应用示例及常见错误规避建议；用户应定期检查模型输出中的置信区间，当低于85%时需人工复核；所有新建项目必须采用T1版本作为默认测算基准，旧版本仅限历史数据追溯用途；需启用“弹性阈值”选项以适配突发流量场景
- 词法前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s6-d3-t1-02-memo#p1@T1 5.s2-d2-01-memo#p1@T1 6.s4-d2-t1-04-summary#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s2-d0-03-memo#p1@T1 9.s6-d0-t1-01-channel#p3@T1 10.s1-d1-01-analysis#p1@T1
- 混合前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p3@T1 3.s4-d0-t1-02-guide#p2@T1 4.s7-d0-t1-02-update#p2@T1 5.s4-d2-t1-04-summary#p1@T1 6.s2-d2-01-memo#p1@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.s6-d3-t1-03-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p2@T1 3.s2-d2-01-memo#p1@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s7-d0-t1-02-update#p3@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-summary#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.s6-d3-t1-03-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 85. `s4-d0-t1-02-q6`

- 问：评审会议对模型的后续发展提出了哪些建议？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-review#p2@T1
- 金标要点：在未来版本中加入成本敏感度分析功能；扩展对云服务阶梯定价的支持
- 词法前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-review#p3@T1 3.s7-d2-t1-04-memo#p3@T1 4.s4-d0-t1-02-plan#p2@T1 5.p1-colaw-governance-supervisor#p4@T1 6.p1-colaw-governance-supervisor-js#p2@T1 7.s2-d3-t1-91-minutes#p1@T1 8.s5-d3-t1-05-memo#p1@T1 9.s5-d0-t1-02-analysis#p1@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-plan#p2@T1 3.s4-d0-t1-02-report#p3@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s4-d2-t1-04-internal#p1@T1 6.s4-d0-t1-02-review#p3@T1 7.s4-d2-t1-04-internal#p2@T1 8.s7-d0-t1-02-brief#p2@T1 9.s1-d2-01-analysis#p2@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-plan#p2@T1 3.s4-d0-t1-02-review#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s4-d0-t1-02-report#p3@T1 6.s2-d3-t1-91-minutes#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d2-t1-04-internal#p2@T1 9.s2-d3-01-memo#p1@T1 10.s1-d2-01-analysis#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 86. `s4-d1-t0-03-q1`

- 问：新版本成本模型如何改进固定与可变成本的区分精度？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p1@T0
- 金标要点：本次内部测算模型在成本结构分析中引入了动态分摊机制，显著提升了对固定成本与可变成本的区分精度；新版本通过加权平均法处理跨周期投入，使单位产出成本估算偏差率下降至5.2%以下
- 词法前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d0-t0-01-analysis#p2@T0 4.s4-d3-t0-05-memo#p3@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d0-t0-01-summary#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s4-d3-t0-05-analysis#p3@T0 10.s4-d3-t0-05-analysis#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-analysis#p2@T0 6.s4-d0-t0-01-summary#p1@T0 7.s4-d0-t0-01-report#p1@T0 8.s4-d1-t0-03-analysis#p3@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d3-t0-05-analysis#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d1-t0-03-analysis#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 87. `s4-d1-t0-03-q2`

- 问：本次模型迭代中移除了哪些冗余计算项？带来了什么影响？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p2@T0
- 金标要点：针对历史数据中存在冗余计算项的问题，已剔除重复归集的间接费用模块；该调整使模型运行效率提升约18%，同时增强结果可解释性
- 词法前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d1-t0-03-memo#p1@T0 4.s7-d0-t0-01-qa#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s7-d0-t0-01-qa#p1@T0 7.s4-d3-t0-05-memo#p3@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s4-d3-t0-05-memo#p1@T0 10.s4-d3-t0-05-analysis#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-analysis#p3@T0 5.s4-d0-t0-01-analysis#p1@T0 6.s4-d3-t0-05-memo#p3@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d0-t0-01-analysis#p2@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-analysis#p3@T0 5.s4-d0-t0-01-analysis#p1@T0 6.s4-d3-t0-05-memo#p3@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d0-t0-01-report#p1@T0 10.s4-d0-t0-01-analysis#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 88. `s4-d1-t0-03-q3`

- 问：新版本模型支持哪几类核心成本拆解？对预算规划有何帮助？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p3@T0
- 金标要点：当前版本支持多维度成本拆解，包括人力、设备、运维及外部服务四类核心支出，为后续预算规划提供更细粒度支撑
- 词法前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d0-t0-01-analysis#p2@T0 3.s4-d0-t0-01-plan#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d1-t0-03-plan#p2@T0 9.s4-d1-t0-03-report#p1@T0 10.s4-d0-t0-01-report#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s4-d1-t0-03-analysis#p3@T0 4.s4-d0-t0-01-analysis#p2@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d1-t0-03-plan#p2@T0 8.s4-d0-t0-01-plan#p2@T0 9.s4-d3-t0-05-summary#p1@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s4-d1-t0-03-memo#p1@T0 4.s4-d0-t0-01-plan#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s4-d0-t0-01-analysis#p2@T0 7.s4-d0-t0-01-report#p1@T0 8.s4-d3-t0-05-summary#p1@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d1-t0-03-plan#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 89. `s4-d1-t0-03-q4`

- 问：未来版本计划引入哪些关键技术能力？预期达到什么效果？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-plan#p1@T0；s4-d1-t0-03-plan#p2@T0；s4-d1-t0-03-plan#p3@T0
- 金标要点：计划下一阶段引入实时数据流接入能力，以支持动态成本重估，目标是将响应延迟压缩至分钟级；增加成本敏感度分析模块，帮助识别关键影响因子，辅助管理层制定策略调整预案；探索与外部经济指标联动建模，提升宏观环境变化应对能力
- 词法前 10：1.s4-d1-t0-03-plan#p1@T0 2.s7-d0-t0-01-qa#p2@T0 3.s1-d1-01-memo#p1@T0 4.s1-d0-01-memo#p1@T0 5.s7-d0-t0-01-qa#p1@T0 6.s1-d0-02-report#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s1-d0-03-memo#p3@T0 9.s2-d0-02-interview#p1@T0 10.s2-d0-03-interview#p3@T0
- 混合前 10：1.s1-d0-01-memo#p1@T0 2.s4-d1-t0-03-plan#p1@T0 3.s1-d0-02-report#p3@T0 4.s4-d3-t0-05-summary#p3@T0 5.s2-d0-03-interview#p3@T0 6.s2-d2-01-memo#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s2-d0-03-memo#p3@T0 9.s1-d0-03-memo#p3@T0 10.s1-d1-01-memo#p1@T0
- 重排前 10：1.s4-d1-t0-03-plan#p1@T0 2.s1-d0-01-memo#p1@T0 3.s1-d0-02-report#p3@T0 4.s4-d3-t0-05-summary#p3@T0 5.s2-d0-03-interview#p3@T0 6.s2-d2-01-memo#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s1-d0-03-memo#p3@T0 9.s1-d1-01-memo#p1@T0 10.s2-d0-03-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 90. `s4-d2-t1-04-q1`

- 问：可用性维持在99.98%以上的那版成本模型，相比旧版预测准确率提升了多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p2@T1
- 金标要点：误差率由原先的8.7%降至4.3%
- 词法前 10：1.s4-d2-t1-04-summary#p2@T1 2.s4-d2-t1-04-memo#p1@T1 3.s4-d0-t1-02-report#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s3-d0-02-c#p2@T1 6.s6-d0-t1-03-memo#p2@T1 7.s4-d0-t1-02-memo#p1@T1 8.s6-d0-t1-03-report#p2@T1 9.s6-d0-t1-03-internal#p2@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s4-d0-t1-02-report#p2@T1 2.s4-d0-t1-02-analysis#p3@T1 3.s4-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-report#p1@T1 5.s4-d2-t1-04-summary#p2@T1 6.s4-d2-t1-04-memo#p2@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s4-d0-t1-02-memo#p1@T1 10.s7-d2-t1-04-memo#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d2-t1-04-summary#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p2@T1 8.s7-d2-t1-04-memo#p2@T1 9.s6-d0-t1-03-memo#p2@T1 10.s4-d2-t1-04-summary#p1@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 91. `s4-d2-t1-04-q2`

- 问：跨区域部署时，边缘机房每单位算力的花费比中心机房便宜多少百分比？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-report#p1@T1
- 金标要点：结果显示，边缘节点的单位计算成本较中心节点低19.6%；本报告基于最新版本的成本模型进行测算，重点分析了多区域部署下的资源利用率差异
- 词法前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s1-d0-03-report#p2@T1 4.s6-d0-t1-01-patch#p1@T1 5.s4-d2-t1-91-review#p2@T1 6.s5-d0-t1-02-analysis#p3@T1 7.s3-d0-03-report#p1@T1 8.s2-d0-04-memo#p2@T1 9.s4-d2-t1-04-internal#p2@T1 10.p2-gdp-national#p3@T1
- 混合前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d2-t1-91-review#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s1-d0-03-report#p2@T1 5.s2-d1-01-memo#p1@T1 6.s3-d2-01-competitor-pricing#p1@T1 7.s3-d1-t1-91-pricesheet#p1@T1 8.s5-d0-t1-02-analysis#p3@T1 9.s5-d1-t1-03-memo#p3@T1 10.s3-d0-04-memo#p2@T1
- 重排前 10：1.s4-d2-t1-04-report#p1@T1 2.s5-d0-t1-02-analysis#p3@T1 3.s4-d2-t1-91-review#p2@T1 4.s4-d0-t1-02-memo#p1@T1 5.s1-d0-03-report#p2@T1 6.s2-d1-01-memo#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s3-d2-01-competitor-pricing#p1@T1 9.s3-d1-t1-91-pricesheet#p1@T1 10.s3-d0-04-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 92. `s4-d2-t1-04-q3`

- 问：边缘节点单位成本比中心低近两成的那版成本模型，做了哪些关键优化来减少资源浪费？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p1@T1；s4-d2-t1-04-report#p2@T1
- 金标要点：引入弹性伸缩阈值优化；资源浪费减少31%；引入动态权重调整机制以提升预测准确率
- 词法前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d2-t1-04-report#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s2-d0-01-report#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s1-d0-04-memo#p2@T1 8.s4-d0-t1-02-memo#p2@T1 9.s4-d0-t1-02-analysis#p3@T1 10.s4-d2-t1-04-memo#p1@T1
- 混合前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-plan#p1@T1 4.s4-d2-t1-04-report#p2@T1 5.s4-d0-t1-02-memo#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-analysis#p3@T1 9.s4-d2-t1-91-model-v3#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 重排前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d2-t1-04-report#p2@T1 4.s4-d0-t1-02-plan#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-analysis#p3@T1 9.s4-d2-t1-91-model-v3#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 93. `s4-d2-t1-04-q4`

- 问：为确保模型长期适用性，计划采取什么措施进行持续优化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p3@T1
- 金标要点：后续将基于真实流量数据持续优化参数，确保长期适应性
- 词法前 10：1.s4-d2-t1-04-memo#p3@T1 2.s4-d0-t1-02-plan#p3@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-plan#p1@T1 5.s7-d0-t1-02-update#p2@T1 6.s3-d0-03-memo#p3@T1 7.s2-d1-01-memo#p2@T1 8.s2-d0-02-interview#p3@T1 9.s3-d2-01-quotation-snapshot#p3@T1 10.s1-d0-02-memo#p2@T1
- 混合前 10：1.s4-d2-t1-04-memo#p3@T1 2.s4-d0-t1-02-plan#p1@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-plan#p3@T1 5.s2-d0-02-interview#p3@T1 6.s6-d0-t1-03-report#p1@T1 7.s4-d0-t1-02-analysis#p2@T1 8.s1-d0-02-memo#p2@T1 9.s3-d0-03-memo#p3@T1 10.s4-d0-t1-02-plan#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p3@T1 2.s4-d0-t1-02-plan#p1@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-plan#p3@T1 5.s2-d0-02-interview#p3@T1 6.s6-d0-t1-03-report#p1@T1 7.s4-d0-t1-02-analysis#p2@T1 8.s1-d0-02-memo#p2@T1 9.s3-d0-03-memo#p3@T1 10.s4-d0-t1-02-plan#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 94. `s4-d3-t0-05-q1`

- 问：新版本成本模型在高并发场景下的平均响应延迟是多少？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-memo#p1@T0
- 金标要点：模型在模拟高并发场景下表现稳定，平均响应延迟控制在210毫秒以内，资源峰值使用率未超过78%
- 词法前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d1-t0-03-report#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s2-d2-01-memo#p3@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-analysis#p1@T0 7.s4-d1-t0-03-plan#p1@T0 8.s4-d3-t0-05-analysis#p3@T0 9.s4-d0-t0-01-summary#p2@T0 10.s2-d2-01-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d3-t0-05-summary#p1@T0 3.s4-d1-t0-03-analysis#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-plan#p1@T0 7.s4-d3-t0-05-memo#p3@T0 8.s4-d1-t0-03-memo#p1@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d1-t0-03-report#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d0-t0-01-report#p1@T0 5.s4-d1-t0-03-analysis#p1@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 95. `s4-d3-t0-05-q2`

- 问：v1.4版本相比v1.2在初始化时间上缩短了多少秒？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-analysis#p2@T0
- 金标要点：其初始化时间平均为47秒，较v1.2缩短了12秒，且具备更优的容错恢复能力；v1.4的部署复杂度略有上升，但通过自动化脚本可有效缓解
- 词法前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s4-d3-t0-05-analysis#p1@T0 3.s7-d0-t0-01-arch#p3@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s4-d0-t0-01-memo#p1@T0 6.s4-d0-t0-01-report#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s3-d0-t0-91-flyer#p2@T0 9.s5-d2-t0-04-analysis#p3@T0 10.s4-d3-t0-05-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s4-d3-t0-05-analysis#p1@T0 3.s7-d0-t0-01-arch#p3@T0 4.s4-d0-t0-01-report#p3@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s4-d0-t0-01-memo#p1@T0 7.s5-d2-t0-04-analysis#p3@T0 8.s4-d1-t0-03-analysis#p2@T0 9.s4-d3-t0-05-memo#p1@T0 10.s4-d3-t0-05-summary#p1@T0
- 重排前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s7-d0-t0-01-arch#p3@T0 3.s4-d3-t0-05-analysis#p1@T0 4.s4-d0-t0-01-memo#p1@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s5-d2-t0-04-analysis#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s4-d3-t0-05-memo#p1@T0 9.s4-d3-t0-05-summary#p1@T0 10.s4-d0-t0-01-report#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 96. `s4-d3-t0-05-q3`

- 问：新版本成本模型在数据预处理阶段的效率提升了多少百分比？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-memo#p2@T0
- 金标要点：测算结果显示，新模型在数据预处理阶段效率提升约19%，主要得益于动态调度机制的优化；该改进使任务队列吞吐量增加至每分钟1200条，较旧版本提升近三成
- 词法前 10：1.s4-d3-t0-05-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d0-t0-01-analysis#p2@T0 5.s4-d0-t0-01-memo#p2@T0 6.s4-d0-t0-01-summary#p3@T0 7.s4-d0-t0-01-summary#p1@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d1-t0-03-report#p1@T0 10.s2-d0-02-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d0-t0-01-report#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d1-t0-03-report#p1@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d0-t0-01-summary#p3@T0
- 重排前 10：1.s4-d3-t0-05-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d0-t0-01-report#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d1-t0-03-report#p1@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d0-t0-01-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 97. `s4-d3-t0-05-q4`

- 问：为解决内存泄漏问题，团队采取了哪些具体措施？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-report#p2@T0
- 金标要点：针对该问题，团队已实施缓冲区大小动态调整策略，并引入周期性垃圾回收机制
- 词法前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d3-t0-05-summary#p2@T0 5.p1-colaw-capital#p2@T0 6.s7-d0-t0-01-qa#p2@T0 7.s3-d0-03-report#p2@T0 8.s2-d0-04-memo#p2@T0 9.s1-d0-03-report#p3@T0 10.s4-d0-t0-01-report#p3@T0
- 混合前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s4-d3-t0-05-summary#p2@T0 4.s5-d0-t0-01-memo#p2@T0 5.p1-cac-o11#p10@T0 6.s7-d0-t0-01-internal#p1@T0 7.s1-d0-03-memo#p2@T0 8.s1-d0-02-memo#p2@T0 9.s4-d0-t0-01-memo#p1@T0 10.s7-d0-t0-01-qa#p1@T0
- 重排前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d3-t0-05-summary#p2@T0 5.s5-d0-t0-01-memo#p2@T0 6.p1-cac-o11#p10@T0 7.s7-d0-t0-01-internal#p1@T0 8.s1-d0-03-memo#p2@T0 9.s1-d0-02-memo#p2@T0 10.s4-d0-t0-01-memo#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 98. `s5-d0-t0-01-q1`

- 问：综合多份文档来看，协作机制在响应速度和响应时间上有哪些量化成效？其推广又面临哪三大挑战？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-report#p1@T0；s5-d0-t0-01-analysis#p1@T0；s5-d0-t0-01-summary#p2@T0
- 金标要点：在公共服务响应速度上平均提升了约40%；在处理突发事件时平均缩短响应时间2.3小时；技术适配性不足、组织惯性阻力大、外部监督机制缺失
- 词法前 10：1.s5-d0-t0-01-memo#p3@T0 2.s5-d0-t0-01-summary#p2@T0 3.s4-d3-t0-05-summary#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s5-d0-t0-01-summary#p1@T0 6.s5-d0-t0-01-analysis#p1@T0 7.s5-d0-t0-01-report#p1@T0 8.s3-d0-01-report#p2@T0 9.s7-d0-t0-01-arch#p3@T0 10.s5-d2-t0-04-memo#p3@T0
- 混合前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d0-t0-01-summary#p2@T0 3.s5-d0-t0-01-summary#p1@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-report#p1@T0 7.s5-d0-t0-01-press#p1@T0 8.s5-d0-t0-01-memo#p3@T0 9.s1-d0-03-report#p2@T0 10.s2-d2-01-report#p2@T0
- 重排前 10：1.s5-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-summary#p3@T0 3.s5-d0-t0-01-summary#p1@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-report#p1@T0 7.s5-d0-t0-01-press#p1@T0 8.s5-d0-t0-01-summary#p2@T0 9.s1-d0-03-report#p2@T0 10.s2-d2-01-report#p2@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 99. `s5-d0-t0-01-q2`

- 问：关于社区服务里的协作平台（某市智慧协作平台），不同来源的评价有矛盾吗？请举例并分析原因。
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-memo#p2@T0；s5-d0-t0-01-press#p1@T0；s5-d0-t0-01-press#p2@T0
- 金标要点：得分达87分；被视为创新典范；报道强调其“零延迟”响应能力；该平台实际覆盖范围仅限于主城区，偏远社区仍依赖传统方式，存在信息孤岛现象；在试点阶段曾出现沟通延迟问题；主要因责任划分不清导致执行脱节
- 词法前 10：1.s5-d0-t0-01-press#p1@T0 2.s5-d0-t0-01-report#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s5-d2-t0-04-analysis#p1@T0 5.s1-d0-04-memo#p3@T0 6.p1-colaw-governance#p3@T0 7.s5-d0-t0-01-memo#p1@T0 8.s5-d2-t0-04-report#p2@T0 9.p1-colaw-equity#p4@T0 10.s5-d2-t0-04-analysis#p2@T0
- 混合前 10：1.s5-d0-t0-01-report#p1@T0 2.s5-d0-t0-01-press#p1@T0 3.s5-d0-t0-01-memo#p1@T0 4.s5-d0-t0-01-summary#p1@T0 5.s5-d0-t0-01-internal#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-03-report#p2@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s5-d2-t0-04-analysis#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s5-d0-t0-01-press#p1@T0 2.s5-d0-t0-01-report#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s5-d2-t0-04-analysis#p2@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-summary#p1@T0 7.s5-d0-t0-01-internal#p2@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s4-d3-t0-05-summary#p3@T0 10.s1-d0-03-report#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 100. `s5-d0-t0-01-q3`

- 问：从文档中提取支持‘该机制在偏远地区效果不佳’这一观点的证据。
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-press#p2@T0；s5-d0-t0-01-report#p2@T0
- 金标要点：在资源紧张区域效果不显著；偏远社区仍依赖传统方式，存在信息孤岛现象
- 词法前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-claim#p3@T0 4.s7-d1-t0-03-fact#p2@T0 5.s7-d1-t0-03-reason#p3@T0 6.s7-d1-t0-03-memo#p1@T0 7.s7-d1-t0-03-reason#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s4-d3-t0-05-summary#p3@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-memo#p3@T0 3.s7-d1-t0-03-fact#p2@T0 4.s5-d0-t0-01-memo#p3@T0 5.s5-d0-t0-01-memo#p1@T0 6.s7-d1-t0-03-reason#p2@T0 7.s7-d1-t0-03-reason#p1@T0 8.s5-d0-t0-01-report#p2@T0 9.s5-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-fact#p2@T0 3.s5-d0-t0-01-memo#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d1-t0-03-memo#p3@T0 7.s5-d0-t0-01-summary#p1@T0 8.s4-d3-t0-05-summary#p3@T0 9.s5-d0-t0-01-memo#p3@T0 10.s5-d0-t0-01-report#p2@T0
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 101. `s5-d0-t0-01-q4`

- 问：哪份文档最直接支持‘系统界面复杂影响使用率’这一说法？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-internal#p1@T0
- 金标要点：在2023年第一季度的跨部门协调会上，多位负责人反映系统界面复杂，操作门槛高，导致基层人员使用意愿低；此问题被列为优先改进项
- 词法前 10：1.s7-d1-t0-03-claim#p3@T0 2.s7-d1-t0-03-reason#p2@T0 3.s7-d1-t0-03-claim#p1@T0 4.s7-d1-t0-03-reason#p3@T0 5.s5-d0-t0-01-analysis#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-memo#p2@T0 8.s5-d0-t0-01-internal#p1@T0 9.s5-d2-t0-04-memo#p3@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s5-d0-t0-01-analysis#p2@T0 2.s7-d1-t0-03-reason#p2@T0 3.s7-d0-t0-01-qa#p2@T0 4.s5-d0-t0-01-internal#p1@T0 5.s7-d0-t0-01-arch#p2@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d1-t0-03-reason#p1@T0 8.s7-d1-t0-03-memo#p2@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-claim#p1@T0
- 重排前 10：1.s7-d1-t0-03-reason#p2@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-claim#p1@T0 4.s5-d0-t0-01-analysis#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s5-d0-t0-01-internal#p1@T0 7.s7-d1-t0-03-fact#p3@T0 8.s7-d0-t0-01-arch#p2@T0 9.s7-d0-t0-01-internal#p3@T0 10.s7-d1-t0-03-reason#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 102. `s5-d0-t0-01-q5`

- 问：根据现有材料，能否得出‘该机制已证明完全可行’的结论？为什么？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-memo#p3@T0；s5-d0-t0-01-report#p2@T0；s5-d0-t0-01-summary#p3@T0
- 金标要点：当前所有结论均基于局部经验与间接数据，尚无权威机构出具全面评估报告，应谨慎对待其广泛推广建议。；平台运行依赖人工协调，自动化程度不足，且在资源紧张区域效果不显著。；该机制的成效存在争议，需更多实证研究以明确其适用边界与改进方向。
- 词法前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-reason#p2@T0 3.s2-d3-01-interview#p3@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-memo#p2@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d1-t0-03-memo#p1@T0 8.s5-d2-t0-04-report#p3@T0 9.s7-d0-t0-01-qa#p2@T0 10.s7-d1-t0-03-reason#p1@T0
- 混合前 10：1.s7-d1-t0-03-memo#p3@T0 2.s2-d3-01-interview#p3@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-claim#p2@T0 5.s7-d1-t0-03-claim#p3@T0 6.s5-d0-t0-01-memo#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s7-d0-t0-01-report#p3@T0 10.s5-d0-t0-01-summary#p1@T0
- 重排前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-memo#p3@T0 3.s7-d1-t0-03-claim#p2@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-reason#p2@T0 6.s2-d3-01-interview#p3@T0 7.s5-d0-t0-01-memo#p3@T0 8.s7-d1-t0-03-claim#p1@T0 9.s5-d0-t0-01-summary#p1@T0 10.s7-d0-t0-01-report#p3@T0
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 103. `s5-d0-t0-01-q6`

- 问：如果要在未来一年内推动该机制全面推广，基于文档内容，应优先解决哪些问题？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-analysis#p3@T0；s5-d0-t0-01-internal#p1@T0；s5-d0-t0-01-internal#p2@T0；s5-d0-t0-01-summary#p2@T0
- 金标要点：建议在全面推广前，建立标准化培训体系，并设定阶段性评估节点，以动态优化机制设计。；多位负责人反映系统界面复杂，操作门槛高，导致基层人员使用意愿低。；若能整合现有政务平台接口，可降低重复录入负担，提升数据一致性。；但其推广面临三大挑战：技术适配性不足、组织惯性阻力大、外部监督机制缺失。这些因素共同制约其规模化应用
- 词法前 10：1.s4-d3-t0-05-summary#p3@T0 2.s7-d0-t0-01-qa#p1@T0 3.s5-d0-t0-01-analysis#p3@T0 4.s1-d0-03-report#p2@T0 5.s5-d2-t0-04-memo#p3@T0 6.s5-d0-t0-01-summary#p3@T0 7.s5-d0-t0-01-internal#p1@T0 8.s1-d0-01-memo#p2@T0 9.s4-d3-t0-05-report#p2@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d0-t0-01-analysis#p3@T0 3.s5-d0-t0-01-summary#p3@T0 4.s5-d0-t0-01-internal#p1@T0 5.s2-d0-02-interview#p1@T0 6.s1-d0-03-report#p2@T0 7.s5-d2-t0-04-analysis#p3@T0 8.s4-d1-t0-03-plan#p3@T0 9.s1-d0-02-memo#p1@T0 10.s5-d0-t0-01-memo#p1@T0
- 重排前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s5-d0-t0-01-analysis#p3@T0 4.s5-d0-t0-01-internal#p1@T0 5.s2-d0-02-interview#p1@T0 6.s1-d0-03-report#p2@T0 7.s1-d0-02-memo#p1@T0 8.s5-d0-t0-01-memo#p1@T0 9.s5-d0-t0-01-summary#p3@T0 10.s4-d1-t0-03-plan#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 104. `s5-d0-t1-02-q1`

- 问：以城市交通拥堵指标和“青少年近视率超一半”为例，二手数据是怎样通过反复引用变成“被接受的真相”的？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p1@T1；s5-d0-t1-02-memo#p3@T1；s5-d0-t1-02-summary#p1@T1；s5-d0-t1-02-summary#p2@T1
- 金标要点：被多家媒体和智库间接转述；最早可追溯至2014年某高校调研；即使原始数据无法验证，只要被多次引用并嵌入正式论述，便可能成为“事实”本身；这些数据往往经过多次转述，每一次传递都可能引入轻微变形，最终形成一种“集体记忆式事实”。；尽管近年新调查显示实际比例为48.6%，但该“旧共识”仍主导舆论讨论，甚至影响教育政策方向。
- 词法前 10：1.s5-d0-t1-02-summary#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-summary#p3@T1 4.s5-d0-t1-02-memo#p2@T1 5.s5-d0-t1-02-memo#p1@T1 6.s5-d0-t1-02-report#p2@T1 7.s7-d3-t1-05-memo#p2@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s5-d0-t1-02-summary#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d0-t1-02-memo#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s5-d0-t1-02-analysis#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-summary#p3@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d0-t1-02-summary#p2@T1 5.s5-d0-t1-02-memo#p2@T1 6.s5-d1-t1-03-memo#p3@T1 7.s5-d0-t1-02-analysis#p1@T1 8.s5-d1-t1-03-note#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 105. `s5-d0-t1-02-q2`

- 问：当原始数据无法验证时，为何某些被转述的数据仍能在政策讨论中获得高度可信度？请从引用行为与制度惯性角度分析。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p2@T1；s5-d0-t1-02-memo#p3@T1；s5-d0-t1-02-summary#p3@T1
- 金标要点：即使原始数据无法验证，只要被多次引用并嵌入正式论述，便可能成为“事实”本身；由于原始报告的权威性已被广泛接受，修正数据并未引发足够关注，反而被归因于“样本偏差”或“测量误差”，反映出信息传播中的“确认偏误”现象。；尤其当新数据与既有叙事冲突时，往往面临更高的质疑门槛，导致认知滞后。；当一个数字被反复提及并嵌入主流话语，其真实性便逐渐让位于其象征意义。
- 词法前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d1-t1-03-memo#p1@T1 4.s5-d0-t1-02-memo#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d0-t1-02-report#p3@T1 7.s6-d3-t1-01-memo#p1@T1 8.s6-d3-t1-01-memo#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d0-t1-02-report#p3@T1 4.s6-d3-t1-01-memo#p3@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d0-t1-02-analysis#p3@T1 8.s7-d2-t1-04-data#p3@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s5-d1-t1-03-report#p3@T1
- 重排前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d1-t1-03-memo#p1@T1 4.s5-d0-t1-02-report#p3@T1 5.s5-d0-t1-02-analysis#p3@T1 6.s5-d1-t1-03-report#p3@T1 7.s7-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d2-t1-04-data#p3@T1 10.s6-d3-t1-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 106. `s5-d0-t1-02-q3`

- 问：通勤白皮书被政府简报引用时出现的“数据语义微调”，会怎样影响政策的科学性？请举例说明后果。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-report#p2@T1；s5-d0-t1-02-report#p3@T1
- 金标要点：这种语义微调虽无恶意，却导致政策推演基础出现偏差；值得注意的是，该报告在发布后不久即被多家政府简报引用，作为制定“弹性工作制试点”政策的重要依据；有地方部门将“平均通勤时间”解释为“最常见通勤时长”，而原始定义实为“中位数时间”；其解释权便可能被重新分配。
- 词法前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d3-t1-05-report#p1@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d3-t1-05-analysis#p2@T1 5.s5-d0-t1-02-report#p1@T1 6.s5-d3-t1-05-memo#p1@T1 7.s5-d1-t1-03-report#p1@T1 8.s5-d0-t1-02-report#p3@T1 9.s5-d3-t1-05-report#p2@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d0-t1-02-report#p3@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d3-t1-05-report#p2@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.s5-d0-t1-02-report#p1@T1 9.s7-d0-t1-02-brief#p2@T1 10.s5-d0-t1-02-analysis#p3@T1
- 重排前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-report#p3@T1 4.s5-d3-t1-05-analysis#p2@T1 5.s5-d0-t1-02-report#p1@T1 6.s5-d3-t1-05-report#p2@T1 7.s5-d0-t1-02-summary#p1@T1 8.s7-d0-t1-02-brief#p2@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s5-d1-t1-03-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 107. `s5-d0-t1-02-q4`

- 问：关于通勤白皮书数据被重新诠释一事，材料认为引用公开数据除追溯源头外还要关注什么？民生报告一案又暴露了什么盲点？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-report#p3@T1；s5-d0-t1-02-analysis#p3@T1
- 金标要点：对公开数据的引用不仅需要追溯源头，更需关注其在不同语境下的再诠释过程，防止“数字神话”在制度层面固化。；此事件暴露了内部数据整合机制中的结构性盲点：权威性不等于准确性，一致性也不代表全面性。
- 词法前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-analysis#p3@T1 4.s5-d0-t1-02-report#p2@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d0-t1-02-memo#p1@T1 7.s5-d3-t1-05-memo#p1@T1 8.s5-d3-t1-05-report#p1@T1 9.s7-d2-t1-04-memo#p3@T1 10.s5-d1-t1-03-report#p1@T1
- 混合前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s5-d0-t1-02-analysis#p3@T1 5.s5-d0-t1-02-memo#p3@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d0-t1-02-memo#p1@T1 8.s7-d2-t1-04-memo#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.p1-cac-o16#p1@T1
- 重排前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d0-t1-02-analysis#p3@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d2-t1-04-memo#p3@T1 7.s5-d0-t1-02-analysis#p2@T1 8.s5-d0-t1-02-memo#p3@T1 9.p1-cac-o16#p1@T1 10.s5-d0-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 108. `s5-d1-t1-03-q1`

- 问：在多个非官方渠道中流传的2018年消费者行为调查的核心结论，为何可能影响后续研究判断？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-memo#p1@T1；s5-d1-t1-03-memo#p2@T1；s5-d1-t1-03-memo#p3@T1
- 金标要点：尽管这一细节未在正式发布版本中说明，但在多份行业笔记中被反复提及，成为后续分析的重要参考依据；尽管原始数据已不再公开，但其核心结论被多次引用。；关于“线上购物渗透率”的统计值，在三份独立文档中分别记载为42%、46%和48%；这种不一致促使学者提出应谨慎对待二手引述，避免误读历史数据脉络
- 词法前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d0-t1-02-memo#p1@T1 3.s5-d3-t1-05-memo#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s5-d1-t1-03-summary#p1@T1 7.s5-d3-t1-05-report#p1@T1 8.s5-d1-t1-03-report#p2@T1 9.s1-d0-01-analysis#p2@T1 10.p1-colaw-governance-supervisor-js#p3@T1
- 混合前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d1-t1-03-report#p2@T1 3.s7-d2-t1-04-memo#p3@T1 4.s5-d1-t1-03-memo#p2@T1 5.s5-d0-t1-02-summary#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s5-d1-t1-03-summary#p1@T1 8.s6-d0-t1-01-channel#p1@T1 9.s5-d1-t1-03-summary#p3@T1 10.s7-d0-t1-02-brief#p2@T1
- 重排前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d0-t1-02-analysis#p2@T1 3.s5-d1-t1-03-summary#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d1-t1-03-report#p2@T1 6.s5-d1-t1-03-memo#p2@T1 7.s5-d1-t1-03-summary#p3@T1 8.s7-d0-t1-02-brief#p2@T1 9.s7-d2-t1-04-memo#p3@T1 10.s5-d0-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 109. `s5-d1-t1-03-q2`

- 问：为什么说2019年白皮书中关于手机更换周期的数据虽然被广泛引用，但仍存在可靠性风险？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-report#p1@T1；s5-d1-t1-03-report#p2@T1
- 金标要点：值得注意的是，该数据源自一项2018年的小型调研，样本量仅为850人，且主要集中在一线城市；该报告指出，用户平均更换手机的时间为2.7年，这一数字在后续三年内被多次复述，甚至成为政策制定者的参考基准。；由于缺乏更新的权威数据，许多研究直接沿用此数值，未加批判性评估，导致长期形成认知惯性。
- 词法前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d3-t1-05-report#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d3-t1-05-analysis#p2@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d0-t1-02-memo#p2@T1 9.s5-d1-t1-03-memo#p1@T1 10.s4-d2-t1-04-memo#p2@T1
- 混合前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d3-t1-05-analysis#p2@T1 3.s5-d3-t1-05-report#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s5-d3-t1-05-report#p2@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-claim#p3@T1 9.s5-d1-t1-03-note#p1@T1 10.s6-d3-t1-01-note#p3@T1
- 重排前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d3-t1-05-analysis#p2@T1 3.s5-d3-t1-05-report#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s5-d1-t1-03-memo#p1@T1 6.s5-d1-t1-03-note#p1@T1 7.s5-d0-t1-02-memo#p3@T1 8.s5-d3-t1-05-report#p2@T1 9.s7-d0-t1-02-claim#p3@T1 10.s6-d3-t1-01-note#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 110. `s5-d1-t1-03-q3`

- 问：那份记录2015年市场反馈的内部备忘录，其数据是怎样经非正式渠道被当作正式成果的？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-note#p1@T1；s5-d1-t1-03-note#p2@T1
- 金标要点：一份2017年的项目备忘录提到，某部门曾收集2015年市场反馈数据，用于支持战略规划；在2021年的审计审查中发现，其中一份内部幻灯片将原始数据中的“满意度得分”从3.4夸大至4.1；该数据集虽未正式对外公布，但通过邮件流转，被多个团队间接引用，形成了隐性的信息传播网络。；其中一份内部幻灯片将原始数据中的“满意度得分”从3.4夸大至4.1，理由是“符合预期目标”；此类微调虽未改变整体趋势，却在后续汇报中被当作真实成果展示，引发信任危机。
- 词法前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-note#p2@T1 3.s7-d0-t1-02-claim#p3@T1 4.s5-d1-t1-03-memo#p1@T1 5.s2-d3-01-memo#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s6-d0-t1-02-report#p2@T1 8.s7-d0-t1-02-brief#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s6-d0-t1-02-memo#p2@T1
- 混合前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-memo#p2@T1 8.s5-d3-t1-05-analysis#p3@T1 9.s2-d3-01-memo#p1@T1 10.s1-d1-t1-91-memo#p2@T1
- 重排前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s2-d3-01-memo#p1@T1 7.s5-d1-t1-03-memo#p2@T1 8.s5-d3-t1-05-analysis#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.s1-d1-t1-91-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 111. `s5-d1-t1-03-q4`

- 问：当多份来源对同一事件的描述存在数值差异时，应采取何种方法确保汇编叙述的可信度？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-summary#p2@T1；s5-d1-t1-03-summary#p3@T1
- 金标要点：经交叉验证，发现前者包含了预注册人数，后者仅统计现场出席者；最终研究团队决定采用“分层标注法”，对每条信息注明其来源类型与潜在偏见
- 词法前 10：1.s5-d1-t1-03-memo#p3@T1 2.s5-d0-t1-02-analysis#p3@T1 3.s7-d2-t1-04-brief#p3@T1 4.s7-d0-t1-02-brief#p3@T1 5.s6-d3-t1-01-note#p2@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d0-t1-02-claim#p2@T1 10.s5-d1-t1-03-summary#p3@T1
- 混合前 10：1.s5-d0-t1-02-analysis#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s5-d1-t1-03-memo#p3@T1 4.s7-d2-t1-04-data#p3@T1 5.s7-d0-t1-02-analysis#p3@T1 6.s6-d3-t1-01-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s7-d2-t1-04-claim#p3@T1 9.s5-d1-t1-03-summary#p3@T1 10.s6-d3-t1-01-memo#p2@T1
- 重排前 10：1.s5-d0-t1-02-analysis#p3@T1 2.s5-d1-t1-03-memo#p3@T1 3.s7-d2-t1-04-brief#p3@T1 4.s7-d2-t1-04-claim#p3@T1 5.s5-d1-t1-03-summary#p3@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s6-d3-t1-01-memo#p3@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 112. `s5-d2-t0-04-q1`

- 问：三份二手交易材料各自给出了哪些增长数字？它们是否引用了同一个数据点？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-memo#p1@T0；s5-d2-t0-04-analysis#p1@T0；s5-d2-t0-04-report#p2@T0；s5-d2-t0-04-memo#p3@T0
- 金标要点：全国二手交易市场在2019年至2020年间年均增长率达17.3%；二手商品成交额在当年第四季度环比增长26.5%；2021年“二手”相关话题在微博上的讨论量同比增长35%；线上二手平台用户活跃度较前一年提升约22%
- 词法前 10：1.s5-d2-t0-04-report#p3@T0 2.s7-d0-t0-01-qa#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s5-d2-t0-04-memo#p1@T0 5.p1-cac-o11#p4@T0 6.s4-d0-t0-01-memo#p1@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s7-d0-t0-01-memo#p1@T0 9.p1-cac-o11#p5@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s5-d2-t0-04-memo#p1@T0 2.s5-d2-t0-04-report#p3@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s1-d3-t0-91-memo#p1@T0 5.s5-d2-t0-04-analysis#p3@T0 6.s5-d1-t0-91-repost#p3@T0 7.s5-d2-t0-04-report#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s2-d0-03-memo#p2@T0 10.s5-d2-t0-04-report#p1@T0
- 重排前 10：1.s5-d2-t0-04-report#p3@T0 2.s5-d2-t0-04-memo#p1@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s1-d3-t0-91-memo#p1@T0 5.s5-d2-t0-04-analysis#p3@T0 6.s5-d2-t0-04-report#p2@T0 7.s5-d2-t0-04-analysis#p1@T0 8.s2-d0-03-memo#p2@T0 9.s5-d1-t0-91-repost#p3@T0 10.s5-d2-t0-04-report#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 113. `s5-d2-t0-04-q2`

- 问：在二手交易相关材料里，哪些文档提到了未公开的内部数据？这些内容为什么被当作参考？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-analysis#p1@T0；s5-d2-t0-04-analysis#p3@T0；s5-d2-t0-04-memo#p1@T0
- 金标要点：此数据未对外公布，但在跨部门会议纪要中被提及，并成为后续策略调整的依据之一。；该信息未进入正式文档体系，但在团队交流中频繁被引用，形成隐性共识。；尽管原始报告未公开，但其结论在若干非正式渠道中广泛流传。
- 词法前 10：1.s5-d2-t0-04-report#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-analysis#p3@T0 4.s5-d2-t0-04-memo#p1@T0 5.s5-d1-t0-91-repost#p1@T0 6.s7-d0-t0-01-arch#p2@T0 7.s5-d2-t0-04-report#p2@T0 8.s7-d1-t0-03-memo#p3@T0 9.s2-d2-t0-91-callnotes#p2@T0 10.s4-d0-t0-01-memo#p1@T0
- 混合前 10：1.s5-d2-t0-04-analysis#p2@T0 2.s5-d2-t0-04-report#p3@T0 3.s5-d2-t0-04-memo#p1@T0 4.s5-d2-t0-04-analysis#p3@T0 5.s5-d2-t0-04-report#p2@T0 6.s7-d1-t0-03-memo#p3@T0 7.s5-d2-t0-04-analysis#p1@T0 8.s4-d0-t0-01-memo#p1@T0 9.s5-d2-t0-04-report#p1@T0 10.p1-cac-o11#p4@T0
- 重排前 10：1.s5-d2-t0-04-analysis#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-report#p3@T0 4.s5-d2-t0-04-memo#p1@T0 5.s5-d2-t0-04-report#p2@T0 6.s5-d2-t0-04-analysis#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.p1-cac-o11#p4@T0 9.s7-d1-t0-03-memo#p3@T0 10.s5-d2-t0-04-report#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 114. `s5-d2-t0-04-q3`

- 问：三份文档如何处理未经证实或来源模糊的信息？请举例说明。
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-analysis#p3@T0；s5-d2-t0-04-memo#p1@T0；s5-d2-t0-04-memo#p3@T0；s5-d2-t0-04-report#p1@T0；s5-d2-t0-04-report#p2@T0
- 金标要点：尽管原始报告未公开，但其结论在若干非正式渠道中广泛流传。；这一趋势被部分媒体归因于疫情推动的居家消费习惯变化，但缺乏直接数据支持。；该报告虽无官方背书，但被多家自媒体转载并作为论据使用。；尽管该数据来源未提供完整统计口径，仍被用于佐证市场热度。；该信息未进入正式文档体系，但在团队交流中频繁被引用，形成隐性共识。
- 词法前 10：1.s7-d0-t0-01-qa#p1@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s7-d0-t0-01-qa#p3@T0 4.s5-d2-t0-04-analysis#p3@T0 5.s1-d3-01-report#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s7-d0-t0-01-report#p1@T0 9.s7-d0-t0-01-arch#p3@T0 10.s3-d1-01-memo#p2@T0
- 混合前 10：1.s7-d0-t0-01-qa#p3@T0 2.s7-d1-t0-03-fact#p3@T0 3.s4-d3-t0-05-summary#p3@T0 4.s7-d0-t0-01-report#p1@T0 5.s7-d0-t0-01-internal#p3@T0 6.s7-d0-t0-01-arch#p3@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s5-d2-t0-04-analysis#p3@T0 9.s7-d0-t0-01-qa#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-qa#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-analysis#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d1-t0-03-fact#p3@T0 6.s4-d3-t0-05-summary#p3@T0 7.s7-d0-t0-01-report#p1@T0 8.s7-d0-t0-01-internal#p3@T0 9.s7-d0-t0-01-arch#p3@T0 10.s7-d1-t0-03-memo#p3@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 115. `s5-d3-t1-05-q1`

- 问：在2022年与2023年间，某城市公共交通使用率的变化情况如何？有哪些因素导致了信息滞后？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-memo#p1@T1；s5-d3-t1-05-memo#p2@T1
- 金标要点：在2022年的一项研究中，某机构对城市居民的通勤模式进行了调查，结果显示约43%的人每日乘坐公共交通工具；2023年另一项独立调查显示，使用公共交通的比例上升至51%，但该结果未被广泛传播；部分媒体和报告仍沿用旧数据，导致公众对实际变化产生误判，形成认知偏差。
- 词法前 10：1.s5-d3-t1-05-memo#p2@T1 2.s5-d3-t1-05-memo#p3@T1 3.s5-d3-t1-05-memo#p1@T1 4.p1-cac-o16#p11@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d0-t1-02-report#p1@T1 9.s5-d0-t1-02-memo#p3@T1 10.s5-d1-t1-03-report#p2@T1
- 混合前 10：1.s5-d3-t1-05-memo#p2@T1 2.s5-d3-t1-05-memo#p1@T1 3.s5-d3-t1-05-memo#p3@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d3-t1-05-report#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s2-d0-03-memo#p2@T1 8.s5-d0-t1-02-analysis#p1@T1 9.s5-d0-t1-02-memo#p1@T1 10.s5-d1-t1-03-report#p2@T1
- 重排前 10：1.s5-d3-t1-05-memo#p3@T1 2.s5-d3-t1-05-memo#p2@T1 3.s5-d3-t1-05-memo#p1@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d0-t1-02-analysis#p1@T1 6.s5-d0-t1-02-memo#p1@T1 7.s5-d1-t1-03-report#p2@T1 8.s5-d3-t1-05-report#p2@T1 9.s5-d0-t1-02-summary#p1@T1 10.s2-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 116. `s5-d3-t1-05-q2`

- 问：以公交使用率、制造业占比和员工满意度为例，为何新数据出现后旧统计仍被政策文件广泛引用？反映了什么问题？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p2@T1；s5-d3-t1-05-report#p2@T1；s5-d3-t1-05-memo#p2@T1
- 金标要点：事实固化；数据惯性；但该结果未被广泛传播；部分媒体和报告仍沿用旧数据，导致公众对实际变化产生误判，形成认知偏差。；但多数地方政府报告仍沿用旧值，造成政策目标与现实脱节。；管理层对此类引用持默许态度，认为其具有稳定预期的作用。
- 词法前 10：1.s5-d3-t1-05-report#p1@T1 2.s1-d0-02-report#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s1-d0-01-memo#p2@T1 5.s5-d1-t1-03-report#p1@T1 6.s2-d0-04-memo#p1@T1 7.s5-d3-t1-05-memo#p1@T1 8.s6-d3-t1-01-memo#p2@T1 9.p1-cac-o11#p4@T1 10.s5-d3-t1-05-analysis#p1@T1
- 混合前 10：1.s5-d3-t1-05-memo#p1@T1 2.s5-d3-t1-05-analysis#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s1-d0-02-report#p1@T1 5.s5-d0-t1-02-analysis#p1@T1 6.s5-d3-t1-05-report#p2@T1 7.s5-d3-t1-05-memo#p2@T1 8.s6-d3-t1-91-changelog#p1@T1 9.s5-d0-t1-02-memo#p1@T1 10.s5-d3-t1-05-memo#p3@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d3-t1-05-memo#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s5-d0-t1-02-analysis#p1@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s1-d0-02-report#p1@T1 7.s5-d3-t1-05-report#p2@T1 8.s5-d3-t1-05-memo#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s6-d3-t1-91-changelog#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 117. `s5-d3-t1-05-q3`

- 问：离职面谈与匿名反馈交叉分析后，发现了哪项没写进正式报告的员工侧趋势？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p3@T1
- 金标要点：通过对离职面谈记录与匿名反馈系统的交叉分析，可识别出员工对远程办公支持度的显著提升；可识别出员工对远程办公支持度的显著提升，这一趋势虽未体现在正式报告中，但已被高层视为关键管理改进方向。
- 词法前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s7-d2-t1-04-claim#p3@T1 3.s5-d1-t1-03-memo#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s4-d2-t1-04-report#p1@T1 6.s5-d3-t1-05-memo#p3@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d1-t1-03-memo#p1@T1 9.s4-d0-t1-02-plan#p1@T1 10.s7-d0-t1-02-memo#p1@T1
- 混合前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s5-d1-t1-03-memo#p2@T1 3.s5-d1-t1-03-note#p1@T1 4.s5-d1-t1-03-memo#p1@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d0-t1-02-memo#p1@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s7-d2-t1-04-claim#p3@T1 3.s5-d1-t1-03-memo#p2@T1 4.s5-d1-t1-03-note#p1@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d0-t1-02-memo#p1@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 118. `s6-d0-t1-01-q1`

- 问：顾问备忘中复验窗口的最新调整是什么？旧窗口如何处理？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-memo#p1@T1
- 金标要点：顾问备忘中关于复验窗口的调整已正式生效，原定两周的复验周期现已延长至三周；旧版中的两周窗口仅保留用于历史对照参考，不再作为现行标准执行
- 词法前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d1-t1-91-patch#p1@T1 4.s6-d3-t1-01-note#p1@T1 5.s1-d1-t1-91-memo#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s1-d0-03-memo#p1@T1 8.s6-d3-t1-01-memo#p1@T1 9.s6-d3-t1-02-memo#p2@T1 10.s6-d0-t1-91-change#p1@T1
- 混合前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d3-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p1@T1 5.s6-d3-t1-01-note#p2@T1 6.s6-d3-t1-02-report#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s6-d3-t1-01-memo#p1@T1 9.s1-d1-t1-91-memo#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 重排前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d3-t1-01-note#p1@T1 4.s6-d3-t1-02-memo#p2@T1 5.s6-d3-t1-02-report#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s6-d3-t1-01-memo#p1@T1 8.s1-d1-t1-91-memo#p2@T1 9.s6-d3-t1-01-note#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 119. `s6-d0-t1-01-q2`

- 问：渠道纪要中关于口头折扣的信息发生了什么位置变动？原因是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-channel#p1@T1
- 金标要点：渠道纪要中涉及口头折扣的条款已从主文迁移至附录，此举旨在分离操作细节与核心政策声明，避免信息冗余影响关键判断的传达效率。
- 词法前 10：1.s6-d0-t1-01-channel#p1@T1 2.s6-d0-t1-01-memo#p2@T1 3.s6-d0-t1-02-internal#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-report#p2@T1 6.s2-d3-t1-91-minutes#p1@T1 7.s5-d1-t1-03-memo#p1@T1 8.s5-d0-t1-02-memo#p1@T1 9.s2-d0-03-memo#p1@T1 10.s6-d0-t1-02-memo#p2@T1
- 混合前 10：1.s6-d0-t1-01-channel#p1@T1 2.s6-d0-t1-01-memo#p2@T1 3.s6-d0-t1-02-internal#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-report#p2@T1 6.s5-d1-t1-03-memo#p1@T1 7.s6-d0-t1-02-memo#p2@T1 8.s2-d0-03-memo#p1@T1 9.s6-d3-t1-03-memo#p3@T1 10.s2-d0-01-report#p3@T1
- 重排前 10：1.s6-d0-t1-01-channel#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s6-d0-t1-01-memo#p2@T1 4.s6-d0-t1-02-internal#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s6-d3-t1-03-memo#p2@T1 7.s6-d3-t1-03-report#p2@T1 8.s2-d0-03-memo#p1@T1 9.s6-d3-t1-03-memo#p3@T1 10.s2-d0-01-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 120. `s6-d0-t1-01-q3`

- 问：战略判断的结论段目前处于什么状态？为何不再标记为已签发？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-memo#p3@T1
- 金标要点：战略判断部分的结论段落已更新为“待复验”状态，不再以“已签发”形式呈现，反映当前评估仍需进一步验证，确保风险控制闭环完整。
- 词法前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s6-d0-t1-03-internal#p1@T1 5.s6-d3-t1-02-summary#p3@T1 6.s1-d0-05-warn#p1@T1 7.s2-d3-01-memo#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s2-d3-01-interview#p1@T1 10.s5-d1-t1-03-memo#p1@T1
- 混合前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s1-d0-03-memo#p1@T1 5.s1-d0-05-memo#p1@T1 6.s1-d0-05-warn#p1@T1 7.s2-d3-01-interview#p1@T1 8.s6-d0-t1-03-internal#p1@T1 9.s2-d0-02-interview#p1@T1 10.s7-d0-t1-02-claim#p2@T1
- 重排前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s1-d0-05-warn#p1@T1 5.s6-d0-t1-03-internal#p1@T1 6.s1-d0-03-memo#p1@T1 7.s1-d0-05-memo#p1@T1 8.s2-d3-01-interview#p1@T1 9.s7-d0-t1-02-claim#p2@T1 10.s2-d0-02-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 121. `s6-d0-t1-02-q1`

- 问：供应商交付周期从四周改为六周后，这一变更分别被同步到了哪些工具或排期里？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-internal#p1@T1；s6-d0-t1-02-memo#p1@T1；s6-d0-t1-02-report#p1@T1
- 金标要点：系统上线计划也已重新排期；该变更已录入项目管理工具，影响范围覆盖所有依赖模块。；该调整已在本周内部通报，并同步更新至项目排期表。
- 词法前 10：1.s6-d0-t1-02-internal#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s1-d0-02-report#p2@T1 5.s6-d0-t1-91-change#p1@T1 6.s6-d3-t1-02-summary#p2@T1 7.s6-d1-c2-memo#p3@T1 8.s6-d0-t1-03-internal#p1@T1 9.s6-d0-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p2@T1
- 混合前 10：1.s6-d0-t1-02-report#p1@T1 2.s6-d0-t1-02-internal#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d3-t1-02-summary#p2@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-91-change#p1@T1 7.s2-d1-01-memo#p1@T1 8.s6-d3-t1-02-report#p2@T1 9.s6-d3-t1-02-memo#p2@T1 10.s6-d0-t1-01-patch#p2@T1
- 重排前 10：1.s6-d0-t1-02-internal#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d3-t1-02-summary#p2@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-91-change#p1@T1 7.s6-d0-t1-01-patch#p2@T1 8.s2-d1-01-memo#p1@T1 9.s6-d3-t1-02-report#p2@T1 10.s6-d3-t1-02-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 122. `s6-d0-t1-02-q2`

- 问：渠道纪要中关于对手入门档产品的最新说法是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-internal#p2@T1；s6-d0-t1-02-memo#p2@T1；s6-d0-t1-02-report#p2@T1
- 金标要点：渠道纪要中新增信息：对手入门档产品已停止销售，当前无直接竞争压力，建议加快市场推广节奏；渠道方面，新增一条对手产品线的动态信息：其入门档型号已于上季度末正式停售，目前市场中无同级竞品可替代；渠道反馈补充指出，此前误传的对手入门档仍在售信息已被更正，实际该产品线已全面下架
- 词法前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d3-t1-02-memo#p1@T1 6.s6-d0-t1-01-channel#p1@T1 7.s2-d3-t1-91-minutes#p1@T1 8.s2-d0-04-memo#p2@T1 9.s6-d0-t1-02-memo#p1@T1 10.s6-d0-t1-02-report#p1@T1
- 混合前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s6-d3-t1-02-memo#p1@T1 7.s2-d2-01-memo#p1@T1 8.s2-d0-01-memo#p1@T1 9.s6-d3-t1-02-summary#p1@T1 10.s6-d0-t1-02-memo#p1@T1
- 重排前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s2-d2-01-memo#p1@T1 7.s6-d3-t1-02-memo#p1@T1 8.s2-d0-01-memo#p1@T1 9.s6-d0-t1-02-memo#p1@T1 10.s6-d3-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 123. `s6-d0-t1-02-q3`

- 问：项目负责人从甲组调到乙组这件事，会议记录里是怎么写的？乙组接手后负责什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-memo#p3@T1
- 金标要点：原由甲组负责的项目推进工作现已移交至乙组；乙组将全面接管后续协调与执行任务
- 词法前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d0-t1-03-internal#p1@T1 6.s6-d0-t1-91-sop#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-t1-91-interview#p2@T1 9.s4-d0-t1-02-guide#p2@T1 10.s6-d0-t1-03-report#p1@T1
- 混合前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s6-d3-t1-02-summary#p3@T1 5.s4-d2-t1-04-internal#p3@T1 6.s6-d2-g3-memo#p3@T1 7.s6-d0-t1-03-internal#p1@T1 8.s2-d0-t1-91-memo#p1@T1 9.s2-d0-t1-91-interview#p2@T1 10.p1-colaw-capital-call#p1@T1
- 重排前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s6-d0-t1-03-internal#p1@T1 5.s6-d2-g3-memo#p3@T1 6.s2-d0-t1-91-interview#p2@T1 7.s6-d3-t1-02-summary#p3@T1 8.s4-d2-t1-04-internal#p3@T1 9.s2-d0-t1-91-memo#p1@T1 10.p1-colaw-capital-call#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 124. `s6-d0-t1-03-q1`

- 问：在最新的成本测算中，外包单价是否仍被使用？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-memo#p1@T1；s6-d0-t1-03-internal#p1@T1；s6-d0-t1-03-report#p1@T1
- 金标要点：内部测算把外包单价从上一版模型里撤下，以避免误导后续成本评估；内部测算把外包单价从上一版模型里撤下，该字段已被标记为过时，后续分析将基于更新后的参数集；内部测算把外包单价从上一版模型里撤下，确保当前评估不依赖已废弃的数据字段，防止误用历史偏差影响决策；该调整已同步至最新数据管道，确保分析基准的一致性。
- 词法前 10：1.s6-d0-t1-03-memo#p1@T1 2.s6-d0-t1-03-internal#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d0-t1-03-report#p1@T1 5.s4-d2-t1-91-model-v3#p1@T1 6.s5-d1-t1-03-report#p1@T1 7.s7-d0-t1-02-update#p2@T1 8.s4-d0-t1-02-memo#p1@T1 9.s2-d2-01-memo#p1@T1 10.s3-d3-01-report#p3@T1
- 混合前 10：1.s6-d0-t1-03-memo#p1@T1 2.s6-d0-t1-03-internal#p1@T1 3.s6-d0-t1-03-report#p1@T1 4.s4-d2-t1-91-model-v3#p1@T1 5.s3-d3-01-report#p3@T1 6.s4-d2-t1-04-report#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s2-d0-02-interview#p3@T1 9.s4-d0-t1-02-memo#p1@T1 10.s3-d3-01-report#p2@T1
- 重排前 10：1.s6-d0-t1-03-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s6-d0-t1-03-internal#p1@T1 4.s4-d2-t1-04-report#p1@T1 5.s2-d0-02-interview#p3@T1 6.s6-d0-t1-03-report#p1@T1 7.s4-d2-t1-91-model-v3#p1@T1 8.s3-d3-01-report#p3@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s3-d3-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 125. `s6-d0-t1-03-q2`

- 问：成本模型版本号发生了什么变化？旧版本如何处理？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-memo#p2@T1；s6-d0-t1-03-internal#p2@T1；s6-d0-t1-03-report#p2@T1
- 金标要点：成本模型版本号从甲版改成乙版，旧版只作归档处理，不再参与任何实时计算流程；成本模型版本号从甲版改成乙版，旧版仅保留于历史存档库，不参与任何实时或批量计算任务；成本模型版本号从甲版改成乙版，旧版只作归档，相关文档已标注“仅历史参考”标签，禁止在新项目中启用
- 词法前 10：1.s6-d0-t1-03-memo#p2@T1 2.s6-d0-t1-03-internal#p2@T1 3.s6-d0-t1-03-report#p2@T1 4.s1-d0-03-memo#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d2-t1-04-report#p1@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.p1-cac-o11#p10@T1
- 混合前 10：1.s6-d0-t1-03-memo#p2@T1 2.s6-d0-t1-03-internal#p2@T1 3.s6-d0-t1-03-report#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-memo#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d0-t1-02-plan#p1@T1 8.s4-d2-t1-04-memo#p1@T1 9.s6-d3-t1-03-report#p1@T1 10.s4-d2-t1-04-memo#p2@T1
- 重排前 10：1.s6-d0-t1-03-memo#p2@T1 2.s6-d0-t1-03-internal#p2@T1 3.s6-d0-t1-03-report#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-memo#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d0-t1-02-plan#p1@T1 8.s4-d2-t1-04-memo#p1@T1 9.s6-d3-t1-03-report#p1@T1 10.s4-d2-t1-04-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 126. `s6-d0-t1-03-q3`

- 问：报价单里的打包项改成分行列出后，三份材料各自说这样做是为了什么？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-internal#p3@T1；s6-d0-t1-03-memo#p3@T1；s6-d0-t1-03-report#p3@T1
- 金标要点：符合最新合规披露要求；提升明细可读性并支持独立定价校验；为未来自动化比价提供结构化基础
- 词法前 10：1.s4-d0-t1-91-deck#p3@T1 2.s2-d0-t1-91-memo#p1@T1 3.s6-d0-t1-91-sop#p2@T1 4.s6-d3-t1-01-report#p2@T1 5.s6-d3-t1-91-changelog#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s1-d1-t1-91-memo#p2@T1 8.s2-d0-t1-91-interview#p2@T1 9.s7-d3-t1-05-synthetic#p2@T1 10.s4-d2-t1-91-model-v3#p2@T1
- 混合前 10：1.s6-d0-t1-03-internal#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s6-d0-t1-03-report#p3@T1 4.s3-d2-t1-91-contract#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s6-d0-t1-03-internal#p3@T1 7.s6-d0-t1-03-memo#p3@T1 8.s6-d3-t1-01-report#p2@T1 9.s6-d0-t1-03-report#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 重排前 10：1.s6-d0-t1-03-internal#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s3-d2-t1-91-contract#p1@T1 4.s6-d0-t1-03-report#p3@T1 5.s6-d3-t1-01-report#p2@T1 6.s6-d0-t1-03-report#p1@T1 7.s6-d0-t1-03-memo#p1@T1 8.s3-d2-t1-91-contract#p3@T1 9.s6-d0-t1-03-internal#p3@T1 10.s6-d0-t1-03-memo#p3@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 127. `s6-d1-c1-q1`

- 问：出境评估结论现在的有效期是多长？满足什么条件可以续期，续期能延多久？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p9@T1；s6-d1-c1-memo#p1@T1；s6-d1-c1-memo#p2@T1
- 金标要点：通过数据出境安全评估的结果有效期为3年，自评估结果出具之日起计算。；有效期届满，需要继续开展数据出境活动且未发生需要重新申报数据出境安全评估情形的，数据处理者可以在有效期届满前60个工作日内通过所在地省级网信部门向国家网信部门提出延长评估结果有效期申请。；经国家网信部门批准，可以延长评估结果有效期3年。
- 词法前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.p1-cac-o11#p12@T1 4.s6-d1-c3-memo#p2@T1 5.s6-d1-c1-memo#p1@T1 6.p1-cac-o11#p14@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d1-c1-memo#p2@T1 9.p1-cac-o16#p6@T1 10.s6-d1-c1-memo#p3@T1
- 混合前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.s6-d1-c1-memo#p1@T1 4.s6-d1-c1-memo#p2@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o11#p14@T1 7.p1-cac-o11#p12@T1 8.s6-d1-c1-memo#p3@T1 9.p1-cac-o11#p11@T1 10.p1-cac-o11#p15@T1
- 重排前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.s6-d1-c1-memo#p1@T1 4.p1-cac-o11#p14@T1 5.p1-cac-o11#p12@T1 6.p1-cac-o11#p11@T1 7.s6-d1-c1-memo#p2@T1 8.s6-d1-c3-memo#p2@T1 9.s6-d1-c1-memo#p3@T1 10.p1-cac-o11#p15@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 128. `s6-d1-c1-q2-new`

- 问：出境评估结论原先管两年，现在能管几年？到期前多久可以申请续期？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p13@T1；p1-cac-o16#p9@T1
- 金标要点：通过数据出境安全评估的结果有效期为2年；通过数据出境安全评估的结果有效期为3年；可以在有效期届满前60个工作日内通过所在地省级网信部门向国家网信部门提出延长评估结果有效期申请
- 词法前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.s6-d1-c1-memo#p3@T1 4.s5-d2-t1-91-digest#p1@T1 5.s6-d1-c1-memo#p2@T1 6.p1-cac-o20#p6@T1 7.s1-d1-t1-91-memo#p1@T1 8.p1-cac-o20#p4@T1 9.p1-cac-o16#p6@T1 10.s6-d3-t1-02-memo#p3@T1
- 混合前 10：1.p1-cac-o16#p9@T1 2.s6-d1-c1-memo#p2@T1 3.s6-d1-c1-memo#p3@T1 4.p1-cac-o11#p12@T1 5.p1-cac-o11#p11@T1 6.p1-cac-o11#p15@T1 7.p1-cac-o13#p8@T1 8.p1-cac-o11#p17@T1 9.p1-cac-o11#p13@T1 10.s6-d3-t1-02-memo#p3@T1
- 重排前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p12@T1 3.s6-d1-c1-memo#p2@T1 4.s6-d1-c1-memo#p3@T1 5.p1-cac-o11#p11@T1 6.p1-cac-o11#p15@T1 7.p1-cac-o13#p8@T1 8.p1-cac-o11#p17@T1 9.p1-cac-o11#p13@T1 10.s6-d3-t1-02-memo#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 129. `s6-d1-c2-q1`

- 问：不属于关基的企业，出境个人信息到多少人才需要报评估？这条线和以前比有什么不同？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p7@T1；p1-cac-o11#p2@T1；s6-d1-c2-memo#p1@T1；s6-d1-c2-memo#p2@T1；s6-d1-c2-memo#p3@T1
- 金标要点：关键信息基础设施运营者以外的数据处理者向境外提供重要数据，或者自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）或者1万人以上敏感个人信息；自上年1月1日起累计向境外提供10万人个人信息或者1万人敏感个人信息的数据处理者向境外提供个人信息；此次更新把一般个人信息的申报线从10万人提高到100万人，统计起点由上年改为当年，实际放宽了一般运营者的申报义务；敏感个人信息仍以1万人为线
- 词法前 10：1.p1-cac-o16#p6@T1 2.p1-cac-o16#p2@T1 3.p1-cac-o16#p3@T1 4.p1-cac-o13#p3@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o20#p3@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o20#p5@T1 9.p1-cac-o16#p8@T1 10.p1-cac-o11#p13@T1
- 混合前 10：1.p1-cac-o20#p3@T1 2.s6-d1-c2-memo#p1@T1 3.p1-cac-o16#p2@T1 4.p1-cac-o11#p2@T1 5.p1-cac-o16#p3@T1 6.p1-cac-o16#p8@T1 7.p1-cac-o13#p3@T1 8.p1-cac-o16#p7@T1 9.s6-d1-c3-memo#p2@T1 10.s6-d1-c3-memo#p3@T1
- 重排前 10：1.p1-cac-o16#p2@T1 2.p1-cac-o11#p2@T1 3.p1-cac-o16#p7@T1 4.p1-cac-o20#p3@T1 5.s6-d1-c2-memo#p1@T1 6.p1-cac-o16#p3@T1 7.p1-cac-o16#p8@T1 8.p1-cac-o13#p3@T1 9.s6-d1-c3-memo#p2@T1 10.s6-d1-c3-memo#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 130. `s6-d1-c3-q1`

- 问：标准合同的适用区间在新规下有何变化？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d1-c3-memo#p1@T1；p1-cac-o13#p2@T1；p1-cac-o16#p8@T1
- 金标要点：累计向境外提供10万人以上、不满100万人个人信息；不满1万人敏感个人信息；自上年1月1日起累计向境外提供个人信息不满10万人的
- 词法前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p1@T1 3.s6-d1-c3-memo#p3@T1 4.p1-cac-o13#p6@T1 5.s3-d2-t1-91-contract#p1@T1 6.s5-d2-t1-91-digest#p3@T1 7.p1-cac-o16#p11@T1 8.p1-cac-o13#p5@T1 9.s6-d1-c3-memo#p2@T1 10.p1-cac-o13#p7@T1
- 混合前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p6@T1 3.p1-cac-o13#p5@T1 4.p1-cac-o13#p7@T1 5.p1-cac-o16#p11@T1 6.p1-cac-o13#p1@T1 7.s6-d1-c4-memo#p1@T1 8.s6-d2-g1-memo#p2@T1 9.s3-d2-t1-91-contract#p1@T1 10.s2-d0-t1-91-memo#p1@T1
- 重排前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p6@T1 3.p1-cac-o13#p7@T1 4.p1-cac-o16#p11@T1 5.p1-cac-o13#p1@T1 6.s6-d1-c4-memo#p1@T1 7.s6-d2-g1-memo#p2@T1 8.s3-d2-t1-91-contract#p1@T1 9.p1-cac-o13#p5@T1 10.s2-d0-t1-91-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 131. `s6-d1-c4-q1`

- 问：令16新增的个人信息出境豁免，哪些主体能享受？要满足什么条件？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p4@T1；p1-cac-o16#p5@T1；s6-d1-c4-memo#p1@T1
- 金标要点：为订立、履行个人作为一方当事人的合同，如跨境购物、跨境寄递、跨境汇款、跨境支付、跨境开户、机票酒店预订、签证办理、考试服务等，确需向境外提供个人信息的；按照依法制定的劳动规章制度和依法签订的集体合同实施跨境人力资源管理，确需向境外提供员工个人信息的；紧急情况下为保护自然人的生命健康和财产安全，确需向境外提供个人信息的；关键信息基础设施运营者以外的数据处理者自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息）的。
- 词法前 10：1.s6-d1-c4-memo#p1@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p11@T1 4.p1-cac-o16#p4@T1 5.s6-d1-c1-memo#p1@T1 6.s6-d1-c3-memo#p1@T1 7.s6-d1-c2-memo#p3@T1 8.p1-cac-o20#p5@T1 9.p1-cac-o16#p3@T1 10.p1-cac-o20#p6@T1
- 混合前 10：1.s6-d1-c4-memo#p1@T1 2.p1-cac-o20#p6@T1 3.s6-d1-c3-memo#p2@T1 4.p1-cac-o16#p4@T1 5.p1-cac-o20#p5@T1 6.p1-cac-o16#p11@T1 7.p1-cac-o20#p8@T1 8.p1-cac-o13#p4@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o20#p4@T1
- 重排前 10：1.s6-d1-c4-memo#p1@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p4@T1 4.p1-cac-o16#p11@T1 5.p1-cac-o20#p6@T1 6.p1-cac-o20#p5@T1 7.p1-cac-o20#p8@T1 8.p1-cac-o13#p4@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o20#p4@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 132. `s6-d2-g1-q1`

- 问：根据2023年公司法，有限责任公司股东认缴出资的最长期限是什么？此前法律有何不同？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d2-g1-memo#p1@T1；p1-colaw-capital#p1@T1
- 金标要点：2018法第二十六条无此期限；全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足。
- 词法前 10：1.s6-d2-g1-memo#p1@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-liquidation#p4@T1 6.s6-d2-g2-memo#p2@T1 7.p1-colaw-capital#p4@T1 8.p1-colaw-capital-transition#p1@T1 9.s6-d2-g2-memo#p1@T1 10.p1-colaw-capital-call#p1@T1
- 混合前 10：1.s6-d2-g1-memo#p1@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-transition#p1@T1 6.p1-colaw-capital-call#p1@T1 7.s6-d2-g1-memo#p2@T1 8.s6-d2-g2-memo#p2@T1 9.s6-d2-g2-memo#p1@T1 10.s6-d2-g3-memo#p1@T1
- 重排前 10：1.p1-colaw-capital#p1@T1 2.s6-d2-g1-memo#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g2-memo#p2@T1 7.s6-d2-g2-memo#p1@T1 8.p1-colaw-capital-call#p1@T1 9.s6-d2-g1-memo#p2@T1 10.s6-d2-g3-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 133. `s6-d2-g2-q1`

- 问：新公司法（2023修订）的施行日期是什么？其第二百六十六条对出资期限有何要求？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d2-g2-memo#p1@T1；p1-colaw-capital-transition#p1@T1
- 金标要点：本法自2024年7月1日起施行；第二百六十六条要求出资期限超出法定上限的存量公司逐步调整到位；本法施行前已登记设立的公司，出资期限超过本法规定的期限的，除法律、行政法规或者国务院另有规定外，应当逐步调整至本法规定的期限以内
- 词法前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g1-memo#p2@T1 6.p1-cac-o16#p11@T1 7.s6-d2-g2-memo#p3@T1 8.p1-colaw-capital#p4@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital-call#p5@T1
- 混合前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g1-memo#p2@T1 6.s6-d2-g2-memo#p3@T1 7.p1-colaw-capital-call#p4@T1 8.p1-cac-o13#p8@T1 9.p1-colaw-capital-call#p5@T1 10.p1-colaw-capital#p3@T1
- 重排前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.s6-d2-g2-memo#p2@T1 6.p1-colaw-capital-call#p5@T1 7.s6-d2-g1-memo#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital#p3@T1 10.p1-cac-o13#p8@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 134. `s6-d2-g3-q1`

- 问：根据2023年最新法规，未按期出资的责任主体和责任形式发生了哪些变化？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p1@T1；p1-colaw-capital-call#p2@T1；p1-colaw-capital-call#p5@T1；p1-colaw-capital-transition#p2@T1；s6-d2-g3-memo#p1@T1
- 金标要点：由受让人承担缴纳该出资的义务；2018法向已足额出资股东承担违约责任；2023法改为对公司损失承担赔偿责任，并新增董事会核查催缴、宽限期不少于六十日后失权、加速到期、未届期转让由受让人缴纳。；股东未按期足额缴纳出资的，除应当向公司足额缴纳外，还应当对给公司造成的损失承担赔偿责任。；未及时履行前款规定的义务，给公司造成损失的，负有责任的董事应当承担赔偿责任。；宽限期自公司发出催缴书之日起，不得少于六十日。
- 词法前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.s5-d3-t1-05-memo#p2@T1 6.s6-d2-g3-memo#p2@T1 7.s6-d1-c1-memo#p2@T1 8.s6-d2-g3-memo#p3@T1 9.s6-d1-c1-memo#p1@T1 10.p1-cac-o11#p10@T1
- 混合前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.s6-d2-g3-memo#p2@T1 4.p1-colaw-capital-call#p5@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g3-memo#p3@T1 7.p1-colaw-capital-transition#p2@T1 8.p1-colaw-capital-call#p2@T1 9.s6-d1-c1-memo#p1@T1 10.s6-d2-g1-memo#p2@T1
- 重排前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.s6-d2-g3-memo#p2@T1 6.p1-colaw-capital-transition#p1@T1 7.s6-d2-g3-memo#p3@T1 8.s6-d1-c1-memo#p1@T1 9.s6-d2-g1-memo#p2@T1 10.p1-colaw-capital-call#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 135. `s6-d3-t1-01-q1`

- 问：在最新版本中，二手转述如何处理旧报价？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p1@T1；s6-d3-t1-01-note#p1@T1；s6-d3-t1-01-report#p1@T1
- 金标要点：二手转述把旧报价标成已过期，不再当现行口径
- 词法前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s6-d3-t1-01-report#p1@T1 4.s5-d1-t1-03-report#p3@T1 5.s6-d3-t1-02-report#p1@T1 6.s6-d0-t1-02-report#p1@T1 7.s2-d2-01-memo#p1@T1 8.s6-d0-t1-03-internal#p3@T1 9.s6-d3-t1-03-memo#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s6-d3-t1-01-report#p1@T1 4.s6-d0-t1-91-change#p1@T1 5.s5-d0-t1-02-memo#p3@T1 6.s5-d1-t1-03-report#p3@T1 7.s5-d0-t1-02-summary#p1@T1 8.s6-d3-t1-03-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-03-memo#p3@T1
- 重排前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s5-d1-t1-03-report#p3@T1 4.s6-d3-t1-01-report#p1@T1 5.s5-d0-t1-02-memo#p3@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d3-t1-03-memo#p1@T1 8.s6-d0-t1-91-change#p1@T1 9.s5-d0-t1-02-summary#p1@T1 10.s6-d0-t1-03-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 136. `s6-d3-t1-01-q2`

- 问：汇编备注中的信息来源发生了什么变化？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p2@T1；s6-d3-t1-01-note#p2@T1；s6-d3-t1-01-report#p2@T1
- 金标要点：汇编备注把出处从访谈改成备忘附件，以反映信息来源的真实文件形式，增强可追溯性；汇编备注把出处从访谈改成备忘附件，体现对原始资料来源的规范标注；汇编备注把出处从访谈改成备忘附件，使原始材料定位更准确，便于后续查证
- 词法前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s6-d3-t1-01-report#p2@T1 4.s1-d0-03-memo#p2@T1 5.s5-d2-t1-91-digest#p3@T1 6.s5-d0-t1-02-analysis#p3@T1 7.p1-cac-o11#p10@T1 8.s7-d2-t1-04-claim#p3@T1 9.s5-d1-t1-03-summary#p3@T1 10.s5-d2-t1-91-digest#p1@T1
- 混合前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s6-d3-t1-01-report#p2@T1 4.s5-d2-t1-91-digest#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s5-d0-t1-02-summary#p3@T1 7.s5-d0-t1-02-summary#p1@T1 8.s5-d1-t1-03-summary#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s5-d1-t1-03-summary#p3@T1
- 重排前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s5-d1-t1-03-summary#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.s5-d2-t1-91-digest#p3@T1 9.s6-d3-t1-01-report#p2@T1 10.s5-d2-t1-91-digest#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 137. `s6-d3-t1-01-q3`

- 问：转述稿中关于份额的说法有何变动？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p3@T1；s6-d3-t1-01-note#p3@T1；s6-d3-t1-01-report#p3@T1
- 金标要点：转述稿删掉了未核实的份额说法，确保内容仅包含经确认的数据，提升整体可信度；转述稿删掉了未核实的份额说法，符合内容审核标准，强化信息可靠性；转述稿删掉了未核实的份额说法，保证输出内容基于可验证事实，减少推测成分
- 词法前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-report#p3@T1 3.s6-d3-t1-01-memo#p3@T1 4.s6-d0-t1-01-memo#p1@T1 5.s5-d0-t1-02-memo#p1@T1 6.s1-d0-01-memo#p2@T1 7.p1-cac-o20#p8@T1 8.p1-colaw-capital#p3@T1 9.s5-d1-t1-03-memo#p1@T1 10.s7-d2-t1-04-brief#p1@T1
- 混合前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-memo#p3@T1 3.s6-d3-t1-01-report#p3@T1 4.s6-d3-t1-01-note#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d3-t1-01-report#p1@T1 7.s6-d3-t1-01-memo#p1@T1 8.s5-d2-t1-91-digest#p1@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d1-t1-03-note#p3@T1
- 重排前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-memo#p3@T1 3.s6-d3-t1-01-report#p3@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d1-t1-03-memo#p3@T1 6.s6-d3-t1-01-note#p1@T1 7.s6-d3-t1-01-memo#p1@T1 8.s5-d2-t1-91-digest#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s6-d3-t1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 138. `s6-d3-t1-02-q1`

- 问：补丁记录中对竞品入门档的最新状态是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p1@T1；s6-d3-t1-02-report#p1@T1；s6-d3-t1-02-summary#p1@T1
- 金标要点：补丁记录把竞品入门档标成停售，相关系统已同步更新状态；补丁记录把竞品入门档标成停售，此变更已在最新版本中生效，建议停止对该型号的市场推广活动；补丁记录把竞品入门档标成停售，系统标记已更新，影响范围涵盖所有对外展示与内部分析模块
- 词法前 10：1.s6-d3-t1-02-report#p1@T1 2.s6-d3-t1-02-memo#p1@T1 3.s6-d3-t1-02-summary#p1@T1 4.s6-d0-t1-02-memo#p2@T1 5.s6-d0-t1-02-internal#p2@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d3-t1-03-memo#p1@T1 8.s6-d0-t1-02-report#p2@T1 9.s2-d0-t1-91-interview#p2@T1 10.s5-d3-t1-05-analysis#p3@T1
- 混合前 10：1.s6-d3-t1-02-memo#p1@T1 2.s6-d3-t1-02-report#p1@T1 3.s6-d3-t1-02-summary#p1@T1 4.s6-d0-t1-02-memo#p2@T1 5.s6-d0-t1-02-internal#p2@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d0-t1-02-report#p2@T1 8.s6-d0-t1-02-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p1@T1
- 重排前 10：1.s6-d3-t1-02-report#p1@T1 2.s6-d3-t1-02-memo#p1@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-summary#p1@T1 5.s6-d3-t1-03-report#p1@T1 6.s6-d0-t1-02-internal#p2@T1 7.s6-d0-t1-02-report#p2@T1 8.s6-d0-t1-02-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 139. `s6-d3-t1-02-q2`

- 问：复验安排在变更说明中发生了什么变动？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p2@T1；s6-d3-t1-02-report#p2@T1；s6-d3-t1-02-summary#p2@T1
- 金标要点：变更说明把复验安排从下月初改到月中，原定流程已调整，相关团队须重新规划时间节点并确认执行进度；变更说明把复验安排从下月初改到月中，相关责任部门需在本周内提交新的时间表以确保流程衔接；变更说明把复验安排从下月初改到月中，相关协调会议已重新排期，确保各环节无缝对接
- 词法前 10：1.s6-d3-t1-02-summary#p2@T1 2.s6-d3-t1-02-report#p2@T1 3.s6-d3-t1-02-memo#p2@T1 4.s6-d0-t1-01-patch#p3@T1 5.s6-d0-t1-01-patch#p1@T1 6.s6-d2-g1-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d1-t1-91-release#p3@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d1-t1-91-release#p2@T1
- 混合前 10：1.s6-d3-t1-02-summary#p2@T1 2.s6-d3-t1-02-memo#p2@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d0-t1-01-patch#p1@T1 5.s6-d0-t1-01-patch#p3@T1 6.s6-d2-g1-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d3-t1-03-memo#p2@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d3-t1-03-report#p2@T1
- 重排前 10：1.s6-d3-t1-02-summary#p2@T1 2.s6-d3-t1-02-memo#p2@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d0-t1-01-patch#p1@T1 5.s6-d0-t1-01-patch#p3@T1 6.s6-d2-g1-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d3-t1-03-memo#p2@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d3-t1-03-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 140. `s6-d3-t1-02-q3`

- 问：汇编中关于两份纪要的结论目前处于什么状态？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p3@T1；s6-d3-t1-02-report#p3@T1；s6-d3-t1-02-summary#p3@T1
- 金标要点：汇编把两份纪要的结论合成一条待核，当前尚未完成最终验证，需在下一周期前完成核实并归档；汇编把两份纪要的结论合成一条待核，目前处于待确认状态，暂不纳入正式决策依据；汇编把两份纪要的结论合成一条待核，当前状态为“待核实”，需指定负责人推进闭环处理
- 词法前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s6-d0-t1-01-memo#p3@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d0-t1-01-memo#p1@T1 7.s2-d3-01-memo#p2@T1 8.s5-d0-t1-02-analysis#p2@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d3-t1-91-minutes#p3@T1
- 混合前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d0-t1-01-memo#p1@T1 7.s6-d0-t1-01-memo#p3@T1 8.s5-d2-t1-91-digest#p1@T1 9.s6-d3-t1-01-note#p2@T1 10.s5-d0-t1-02-analysis#p2@T1
- 重排前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d0-t1-02-analysis#p2@T1 6.s6-d0-t1-01-channel#p1@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d0-t1-01-memo#p3@T1 9.s5-d2-t1-91-digest#p1@T1 10.s6-d3-t1-01-note#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 141. `s6-d3-t1-03-q1`

- 问：补丁记录中关于旧成本模型的用途是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-03-memo#p1@T1；s6-d3-t1-03-report#p1@T1
- 金标要点：补丁记录注明旧成本模型只供对照，不得用于实际核算；补丁记录注明旧成本模型只供对照，用于对比分析新方案的效益差异，严禁在正式决策中引用
- 词法前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s6-d3-t1-02-memo#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s6-d3-t1-02-summary#p1@T1 7.s6-d0-t1-01-patch#p1@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s5-d1-t1-03-summary#p2@T1 10.s4-d0-t1-02-memo#p1@T1
- 混合前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s6-d3-t1-02-summary#p1@T1 5.s6-d3-t1-02-memo#p1@T1 6.s6-d0-t1-03-memo#p2@T1 7.s4-d2-t1-91-model-v3#p1@T1 8.s4-d0-t1-02-memo#p1@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 重排前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s4-d0-t1-02-memo#p1@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s6-d3-t1-02-memo#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s4-d0-t1-02-plan#p1@T1 10.s6-d3-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 142. `s6-d3-t1-03-q2`

- 问：变更说明中对渠道折扣的最新状态如何描述？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-03-memo#p2@T1；s6-d3-t1-03-report#p2@T1
- 金标要点：变更说明中将渠道折扣描述为已撤回，表明此前发布的折扣政策不再有效，相关合作方需依据现行协议执行；变更说明把渠道折扣写成已撤回，明确指出原定优惠机制已终止，相关客户需重新协商合作条款
- 词法前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s6-d3-t1-02-report#p2@T1 7.s7-d0-t1-02-memo#p3@T1 8.s6-d3-t1-02-summary#p2@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d3-t1-02-memo#p2@T1
- 混合前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-channel#p1@T1 4.s6-d0-t1-01-memo#p2@T1 5.s6-d3-t1-02-summary#p2@T1 6.s6-d3-t1-02-report#p2@T1 7.s6-d3-t1-02-memo#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 重排前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-channel#p1@T1 4.s6-d0-t1-01-memo#p2@T1 5.s6-d3-t1-02-report#p2@T1 6.s6-d3-t1-02-summary#p2@T1 7.s6-d3-t1-02-memo#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 143. `s6-mh-12-new`

- 问：顾问备忘列了哪些未按期出资的新规则？转让未到期股权后受让人没交，原股东还要担什么责？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p5@T1；s6-d2-g3-memo#p1@T1；s6-d2-g3-memo#p3@T1
- 金标要点：转让人对受让人未按期缴纳的出资承担补充责任；2023法改为对公司损失承担赔偿责任，并新增董事会核查催缴、宽限期不少于六十日后失权、加速到期、未届期转让由受让人缴纳。
- 词法前 10：1.p1-colaw-capital-call#p5@T1 2.s6-d2-g3-memo#p3@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-capital-transition#p2@T1 7.p1-colaw-capital-call#p2@T1 8.p1-colaw-capital-call#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-equity#p5@T1
- 混合前 10：1.p1-colaw-capital-call#p5@T1 2.s6-d2-g3-memo#p3@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-capital-call#p4@T1 8.p1-colaw-equity#p1@T1 9.p1-colaw-capital-call#p3@T1 10.p1-colaw-equity#p3@T1
- 重排前 10：1.s6-d2-g3-memo#p3@T1 2.p1-colaw-capital-call#p5@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-equity#p1@T1 8.p1-colaw-capital-call#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-equity#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 144. `s6-mh-15-new`

- 问：顾问备忘说存量公司要调整出资期限；新法本身给新设公司的缴足期限是几年？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital#p1@T1
- 金标要点：全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足
- 词法前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p2@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-transition#p1@T1 5.s6-d2-g2-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.p1-colaw-capital-call#p4@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-capital-transition#p2@T1
- 混合前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p1@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-transition#p1@T1 5.s6-d2-g2-memo#p2@T1 6.s6-d2-g2-memo#p3@T1 7.s6-d2-g3-memo#p3@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital#p1@T1
- 重排前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p1@T1 3.s6-d2-g2-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g3-memo#p3@T1 7.s6-d2-g1-memo#p1@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-capital-call#p4@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 145. `s7-d0-t0-01-q1`

- 问：系统日志中‘连接超时’的真实原因是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-log#p1@T0
- 金标要点：系统日志中频繁出现“连接超时”警告，但网络监控工具显示带宽正常、延迟极低；经排查发现，该“超时”实为应用层心跳检测机制误判，而非真实网络故障
- 词法前 10：1.s7-d0-t0-01-log#p1@T0 2.s7-d1-t0-03-memo#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s7-d1-t0-03-fact#p3@T0 9.s7-d1-t0-03-claim#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 混合前 10：1.s7-d0-t0-01-log#p1@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-memo#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d1-t0-03-reason#p3@T0 7.s4-d3-t0-05-report#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d0-t0-01-log#p2@T0 10.s7-d0-t0-01-memo#p1@T0
- 重排前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-memo#p1@T0 3.s7-d0-t0-01-log#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-memo#p1@T0 7.s7-d1-t0-03-reason#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d0-t0-01-log#p2@T0 10.s4-d3-t0-05-report#p3@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 146. `s7-d0-t0-01-q2`

- 问：关于每月首日的安全重置，系统文档和内部备忘录的说法一致吗？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-memo#p2@T0
- 金标要点：系统文档中提及“所有用户必须在每月首日完成安全重置”，而另一份内部备忘录指出“安全重置仅对高权限账户强制执行”；这两条信息存在同快照冲突陈述，同一时间点内出现矛盾指令，若未明确上下文，可能引发操作偏差
- 词法前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.p1-cac-o11#p1@T0 4.s7-d1-t0-03-memo#p3@T0 5.p1-cac-o11#p3@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d1-t0-03-claim#p3@T0 8.p1-cac-o13#p4@T0 9.p1-cac-o11#p13@T0 10.s2-d0-02-interview#p2@T0
- 混合前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.p1-cac-o11#p16@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d0-t0-01-internal#p3@T0 6.s7-d1-t0-03-memo#p2@T0 7.p1-cac-o11#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s7-d0-t0-01-arch#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s7-d0-t0-01-internal#p3@T0 4.p1-cac-o11#p16@T0 5.s7-d1-t0-03-memo#p2@T0 6.p1-cac-o11#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s7-d0-t0-01-arch#p1@T0 9.s7-d1-t0-03-memo#p3@T0 10.s7-d1-t0-03-reason#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 147. `s7-d0-t0-01-q3`

- 问：系统自称眼下没有已知漏洞，这种说法靠得住吗？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-memo#p3@T0
- 金标要点：该声明发布于一次重大补丁前，且未说明其时效性；可能误将“无漏洞”视为绝对事实
- 词法前 10：1.s7-d1-t0-03-claim#p3@T0 2.s7-d0-t0-01-memo#p3@T0 3.s5-d1-t0-91-repost#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s2-d2-t0-91-callnotes#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-memo#p1@T0 8.s1-d2-01-report#p3@T0 9.s4-d3-t0-91-method#p2@T0 10.s2-d2-01-report#p2@T0
- 混合前 10：1.s7-d0-t0-01-memo#p3@T0 2.s7-d1-t0-03-claim#p3@T0 3.s1-d0-05-warn#p3@T0 4.s2-d0-02-interview#p1@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p1@T0 7.s2-d3-01-memo#p3@T0 8.s1-d0-01-memo#p1@T0 9.s7-d1-t0-03-reason#p2@T0 10.s7-d1-t0-03-reason#p3@T0
- 重排前 10：1.s7-d0-t0-01-memo#p3@T0 2.s7-d1-t0-03-claim#p3@T0 3.s7-d0-t0-01-qa#p2@T0 4.s1-d0-05-warn#p3@T0 5.s2-d0-02-interview#p1@T0 6.s7-d1-t0-03-memo#p1@T0 7.s2-d3-01-memo#p3@T0 8.s1-d0-01-memo#p1@T0 9.s7-d1-t0-03-reason#p2@T0 10.s7-d1-t0-03-reason#p3@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 148. `s7-d0-t0-01-q4`

- 问：‘用户活跃度提升30%’这一数据是否具有代表性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-report#p1@T0
- 金标要点：该合成叙述通过选择性呈现数据构建积极表象，实则掩盖了真实流失率上升的事实，属于典型的合成叙述误导；数据来源为仅包含注册用户的样本池，未涵盖流失用户
- 词法前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s7-d0-t0-01-report#p3@T0 4.s7-d1-t0-03-reason#p3@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-qa#p2@T0 7.p1-cac-o11#p4@T0 8.s7-d1-t0-03-memo#p1@T0 9.s7-d1-t0-03-claim#p3@T0 10.s7-d1-t0-03-claim#p1@T0
- 混合前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s2-d2-01-report#p1@T0 4.s1-d0-02-report#p1@T0 5.s7-d0-t0-01-qa#p2@T0 6.s5-d0-t0-01-report#p1@T0 7.s1-d1-01-analysis#p3@T0 8.s3-d0-01-report#p2@T0 9.s2-d0-01-report#p1@T0 10.s4-d3-t0-05-memo#p2@T0
- 重排前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s2-d2-01-report#p1@T0 4.s7-d0-t0-01-qa#p2@T0 5.s5-d0-t0-01-report#p1@T0 6.s3-d0-01-report#p2@T0 7.s4-d3-t0-05-memo#p2@T0 8.s1-d0-02-report#p1@T0 9.s1-d1-01-analysis#p3@T0 10.s2-d0-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 149. `s7-d0-t0-01-q5`

- 问：说全部服务都能不停机升级，这话有没有例外？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-arch#p2@T0
- 金标要点：文档中写道：“所有服务均支持热升级”，但部分老旧服务仍需重启才能更新；尽管“支持热升级”在多数情况下成立，但未说明例外情况，导致该陈述在检索时被当作普遍规则使用
- 词法前 10：1.s4-d1-t0-03-analysis#p1@T0 2.s7-d0-t0-01-arch#p2@T0 3.s1-d0-05-memo#p2@T0 4.p1-colaw-equity#p1@T0 5.s5-d1-t0-91-repost#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s3-d0-04-memo#p2@T0 8.s1-d0-04-risk#p2@T0 9.s3-d1-01-memo#p2@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s7-d0-t0-01-arch#p2@T0 2.s1-d0-05-memo#p2@T0 3.s2-d0-02-interview#p2@T0 4.s5-d0-t0-01-report#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-04-risk#p2@T0 8.s2-d0-03-interview#p2@T0 9.s1-d0-01-analysis#p2@T0 10.s1-d0-04-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-arch#p2@T0 2.s1-d0-05-memo#p2@T0 3.s2-d0-02-interview#p2@T0 4.s5-d0-t0-01-report#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-04-risk#p2@T0 8.s1-d0-01-analysis#p2@T0 9.s1-d0-04-memo#p3@T0 10.s2-d0-03-interview#p2@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 150. `s7-d0-t0-01-q6`

- 问：FAQ中‘支持多设备登录’的限制条件是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-qa#p2@T0
- 金标要点：同时在线设备数上限为3个
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s7-d1-t0-03-claim#p3@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-claim#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s3-d0-t0-91-flyer#p3@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-fact#p2@T0
- 混合前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s4-d1-t0-03-memo#p3@T0 4.s1-d0-04-risk#p3@T0 5.s7-d0-t0-01-arch#p2@T0 6.s3-d0-t0-91-flyer#p3@T0 7.s3-d1-01-report#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d1-t0-03-memo#p2@T0 10.s3-d3-01-memo#p2@T0
- 重排前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s3-d0-t0-91-flyer#p3@T0 5.s7-d0-t0-01-qa#p1@T0 6.s4-d1-t0-03-memo#p3@T0 7.s1-d0-04-risk#p3@T0 8.s7-d0-t0-01-arch#p2@T0 9.s3-d1-01-report#p3@T0 10.s3-d3-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 151. `s7-d0-t1-02-q1`

- 问：用户报“搜索功能失效”但服务状态正常的案例中，系统为什么会误判与‘搜索’相关的请求？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p1@T1
- 金标要点：进一步排查发现，该问题源于关键词‘搜索’在不同上下文中具有双重含义——既指系统核心功能；检索模型误判请求意图，从而返回无关结果
- 词法前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d2-t1-04-memo#p1@T1 3.s7-d0-t1-02-claim#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d3-t1-05-synthetic#p3@T1 7.s7-d0-t1-02-claim#p2@T1 8.s7-d2-t1-04-data#p2@T1 9.s7-d3-t1-05-memo#p3@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d2-t1-04-memo#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d3-t1-05-claim#p1@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s7-d3-t1-05-conflict#p2@T1 9.s7-d0-t1-02-analysis#p3@T1 10.s7-d2-t1-04-brief#p3@T1
- 重排前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d2-t1-04-memo#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d3-t1-05-memo#p3@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s7-d2-t1-04-brief#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 152. `s7-d0-t1-02-q2`

- 问：一份材料先后被打上“已核实”和“待复查”两种标签，检索系统同时读到时会出什么问题？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p2@T1
- 金标要点：值得注意的是，同一份文档在多个时间点被标记为“已验证”和“待审查”；当检索系统同时加载两个快照时，其判断依据出现冲突：一个版本声称内容准确，另一个则指出存在偏差；系统难以确定哪一信息应作为权威参考
- 词法前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d3-t1-02-summary#p3@T1 3.s7-d0-t1-02-brief#p1@T1 4.s5-d0-t1-02-memo#p2@T1 5.s7-d2-t1-04-brief#p1@T1 6.s6-d0-t1-01-patch#p2@T1 7.s6-d0-t1-03-report#p2@T1 8.s7-d3-t1-05-conflict#p1@T1 9.s6-d0-t1-01-memo#p3@T1 10.s7-d3-t1-05-memo#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d0-t1-01-patch#p2@T1 3.s7-d3-t1-05-memo#p3@T1 4.s6-d3-t1-02-summary#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s6-d0-t1-01-memo#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-brief#p3@T1 9.s7-d2-t1-04-data#p3@T1 10.s7-d0-t1-02-update#p2@T1
- 重排前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-summary#p3@T1 4.s7-d0-t1-02-claim#p2@T1 5.s6-d0-t1-01-memo#p3@T1 6.s7-d0-t1-02-update#p2@T1 7.s7-d3-t1-05-memo#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s7-d2-t1-04-data#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 153. `s7-d0-t1-02-q3`

- 问：文档里注明“此处只是推测”的自我说明，模型为什么会把它当成事实来用？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p3@T1
- 金标要点：此外，文档中的元陈述如“本节内容为推测性分析”被误认为是事实陈述，导致检索结果中混入非确定性信息；此类自我指涉的描述虽有助于说明可信度，却常被模型当作真实数据处理，形成合成叙述陷阱
- 词法前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s5-d1-t1-03-summary#p3@T1 4.s7-d0-t1-02-analysis#p2@T1 5.s6-d3-t1-01-report#p3@T1 6.s7-d3-t1-05-memo#p3@T1 7.s6-d0-t1-03-internal#p1@T1 8.s6-d0-t1-03-report#p1@T1 9.s6-d1-t1-91-release#p1@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 混合前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d0-t1-02-analysis#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s6-d3-t1-01-report#p3@T1 8.s7-d2-t1-04-data#p3@T1 9.s7-d2-t1-04-brief#p3@T1 10.s6-d0-t1-03-report#p2@T1
- 重排前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d0-t1-02-analysis#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d2-t1-04-brief#p3@T1 9.s6-d0-t1-03-report#p2@T1 10.s6-d3-t1-01-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 154. `s7-d0-t1-02-q4`

- 问：在医疗术语中，‘心衰’与‘心力衰竭’为何可能导致检索偏差？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-brief#p1@T1
- 金标要点：在医疗知识库中，“心衰”与“心力衰竭”被用作同义词，但在部分文献中，“心衰”特指急性发作阶段；当检索系统未区分语义层级时，将两者等同处理，导致部分患者治疗方案被错误推荐；“心衰”特指急性发作阶段，而“心力衰竭”涵盖慢性与急性
- 词法前 10：1.s7-d0-t1-02-claim#p1@T1 2.s7-d0-t1-02-brief#p1@T1 3.s7-d0-t1-02-memo#p1@T1 4.s7-d0-t1-02-report#p3@T1 5.s7-d3-t1-05-synthetic#p3@T1 6.s7-d0-t1-02-memo#p3@T1 7.s5-d0-t1-02-memo#p3@T1 8.s7-d3-t1-05-claim#p2@T1 9.s4-d0-t1-02-memo#p2@T1 10.s5-d3-t1-05-memo#p2@T1
- 混合前 10：1.s7-d0-t1-02-brief#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d3-t1-05-claim#p2@T1 4.s4-d0-t1-02-memo#p2@T1 5.s7-d0-t1-02-claim#p1@T1 6.s7-d2-t1-04-memo#p1@T1 7.s7-d0-t1-02-brief#p2@T1 8.s7-d3-t1-05-conflict#p3@T1 9.s7-d3-t1-05-conflict#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 重排前 10：1.s7-d0-t1-02-brief#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-memo#p2@T1 5.s7-d2-t1-04-memo#p1@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-brief#p2@T1 8.s7-d3-t1-05-conflict#p3@T1 9.s7-d3-t1-05-conflict#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 155. `s7-d0-t1-02-q5`

- 问：系统如何因未识别版本时效性而产生矛盾输出？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-brief#p3@T1
- 金标要点：系统还曾因同时引用两版修订稿而产生矛盾输出：一版称“剂量上限为50mg”，另一版则标注“需根据个体调整”；当检索器未能识别版本时效性差异时，生成的回答包含相互排斥的信息，严重削弱可信度
- 词法前 10：1.s7-d0-t1-02-brief#p3@T1 2.s7-d0-t1-02-claim#p2@T1 3.s4-d2-t1-04-report#p3@T1 4.s4-d0-t1-02-guide#p2@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s2-d0-03-interview#p3@T1 7.s2-d2-01-memo#p3@T1 8.s7-d3-t1-05-synthetic#p3@T1 9.s6-d3-t1-01-report#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 混合前 10：1.s7-d0-t1-02-brief#p3@T1 2.s7-d0-t1-02-claim#p2@T1 3.s7-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-guide#p2@T1 5.s2-d2-01-memo#p3@T1 6.s7-d0-t1-02-memo#p2@T1 7.s4-d2-t1-04-report#p3@T1 8.s7-d3-t1-05-memo#p3@T1 9.s7-d0-t1-02-update#p3@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 重排前 10：1.s7-d0-t1-02-brief#p3@T1 2.s7-d0-t1-02-claim#p2@T1 3.s7-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-guide#p2@T1 5.s2-d2-01-memo#p3@T1 6.s7-d0-t1-02-memo#p2@T1 7.s4-d2-t1-04-report#p3@T1 8.s7-d3-t1-05-memo#p3@T1 9.s7-d0-t1-02-update#p3@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 156. `s7-d0-t1-02-q6`

- 问：为什么预测性元陈述容易在合成叙述中被当作事实？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-claim#p3@T1
- 金标要点：更为隐蔽的是，文档中一句“我们预计下季度将有新版本发布”被多次引用，且每次都被当作事实陈述使用；实际上，该句属于预测性元陈述，未经过正式确认
- 词法前 10：1.s7-d0-t1-02-claim#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d0-t1-02-brief#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d0-t1-02-report#p2@T1 6.s7-d0-t1-02-analysis#p2@T1 7.s7-d2-t1-04-claim#p3@T1 8.s7-d3-t1-05-memo#p3@T1 9.s7-d2-t1-04-brief#p1@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-report#p2@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d0-t1-02-analysis#p2@T1 7.s5-d1-t1-03-summary#p3@T1 8.s5-d0-t1-02-analysis#p3@T1 9.s7-d0-t1-02-analysis#p3@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 重排前 10：1.s7-d0-t1-02-claim#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d0-t1-02-brief#p2@T1 4.s7-d0-t1-02-report#p2@T1 5.s5-d1-t1-03-summary#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d3-t1-05-synthetic#p3@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s7-d0-t1-02-analysis#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 157. `s7-d1-t0-03-q1`

- 问：两个看似矛盾的系统状态报告为什么可能同时为真？材料给出了哪几种解释？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-memo#p2@T0；s7-d1-t0-03-reason#p1@T0；s7-d1-t0-03-reason#p2@T0
- 金标要点：二者均真实，但反映不同时间快照；源于部署流水线中各组件更新节奏不一致，造成同一时间点下多版本共存的快照冲突；系统在达成最终一致性前的短暂状态
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-reason#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-report#p3@T0 7.p1-cac-o11#p5@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s5-d2-t0-04-report#p3@T0 10.p1-cac-o13#p6@T0
- 混合前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-reason#p3@T0 3.s7-d1-t0-03-reason#p2@T0 4.s4-d0-t0-01-analysis#p3@T0 5.s7-d1-t0-03-claim#p2@T0 6.s4-d3-t0-05-summary#p3@T0 7.p1-cac-o13#p6@T0 8.s7-d0-t0-01-internal#p1@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d0-t0-01-qa#p2@T0
- 重排前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-reason#p3@T0 3.s7-d1-t0-03-reason#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s7-d1-t0-03-claim#p2@T0 6.s4-d3-t0-05-summary#p3@T0 7.p1-cac-o13#p6@T0 8.s7-d0-t0-01-internal#p1@T0 9.s7-d1-t0-03-fact#p3@T0 10.s4-d0-t0-01-analysis#p3@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 158. `s7-d1-t0-03-q2`

- 问：以密钥轮换不同步导致‘认证失败’被误读为例，什么是词面撞车？它在技术文档里怎样表现？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-memo#p1@T0
- 金标要点：这种词面撞车现象常导致误判；在某次跨部门协作中，系统日志显示‘用户认证失败’频繁出现；表面冲突，实则源于对‘失败’一词的语义理解差异；前者指连接中断，后者指验证机制失效
- 词法前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d1-t0-03-reason#p1@T0 7.s7-d1-t0-03-claim#p3@T0 8.s2-d2-t0-91-callnotes#p2@T0 9.s5-d1-t0-91-repost#p1@T0 10.s7-d0-t0-01-report#p2@T0
- 混合前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-log#p2@T0 7.s7-d1-t0-03-memo#p2@T0 8.s7-d0-t0-01-report#p2@T0 9.s7-d1-t0-03-claim#p3@T0 10.s7-d1-t0-03-fact#p3@T0
- 重排前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d1-t0-03-reason#p2@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d0-t0-01-log#p2@T0 9.s7-d0-t0-01-report#p2@T0 10.s7-d1-t0-03-fact#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 159. `s7-d1-t0-03-q3`

- 问：如何判断一篇报告中的‘共识’描述是否具有误导性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-claim#p1@T0；s7-d1-t0-03-claim#p3@T0；s7-d1-t0-03-fact#p2@T0
- 金标要点：这些引述均源自少数几位学者的非公开访谈，且未提供原始立场记录；有两项结论为负面或中性，且未被充分讨论；一个说法被‘多位分析师确认’，而该说法本身又‘基于行业标准’，形成闭环论证
- 词法前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-reason#p2@T0 4.s5-d1-t0-91-repost#p1@T0 5.s7-d1-t0-03-fact#p2@T0 6.s7-d1-t0-03-reason#p1@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d1-t0-03-memo#p2@T0 9.p1-cac-o11#p4@T0 10.s7-d0-t0-01-report#p3@T0
- 混合前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d0-t0-01-report#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d1-t0-03-reason#p3@T0 9.s7-d1-t0-03-claim#p2@T0 10.s7-d1-t0-03-memo#p1@T0
- 重排前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d1-t0-03-claim#p3@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d1-t0-03-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-reason#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 160. `s7-d1-t0-03-q4`

- 问：第三方综述称“研究一致支持某疗法”的案例里，合成叙述如何靠选择性整合制造虚假一致性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-fact#p2@T0
- 金标要点：该叙述通过选择性强调正向结果构建了虚假共识，构成典型的合成叙述陷阱；有两项结论为负面或中性，且未被充分讨论
- 词法前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d0-t0-01-qa#p2@T0 3.s7-d0-t0-01-report#p1@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d0-t0-01-arch#p1@T0 6.s7-d1-t0-03-claim#p2@T0 7.s5-d0-t0-01-press#p1@T0 8.s7-d1-t0-03-fact#p1@T0 9.s5-d0-t0-01-internal#p2@T0 10.s7-d1-t0-03-claim#p1@T0
- 混合前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-claim#p2@T0 3.s7-d0-t0-01-report#p1@T0 4.s7-d1-t0-03-claim#p1@T0 5.s7-d1-t0-03-fact#p1@T0 6.s5-d0-t0-01-internal#p2@T0 7.s7-d1-t0-03-memo#p3@T0 8.s5-d0-t0-01-memo#p3@T0 9.s7-d0-t0-01-internal#p3@T0 10.s7-d0-t0-01-memo#p3@T0
- 重排前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d0-t0-01-report#p1@T0 3.s7-d1-t0-03-fact#p1@T0 4.s7-d1-t0-03-claim#p2@T0 5.s7-d1-t0-03-claim#p1@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d0-t0-01-memo#p3@T0 8.s5-d0-t0-01-internal#p2@T0 9.s7-d1-t0-03-memo#p3@T0 10.s5-d0-t0-01-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 161. `s7-d2-t1-04-q1`

- 问：以“搜索结果未按时间排序”的投诉为例，怎样识别术语歧义造成的词面撞车？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-memo#p1@T1
- 金标要点：此现象源于术语“时间”的词面撞车——同一词汇在不同语境中指向不同维度，导致用户预期与系统行为错位；用户所指的“时间”实为“提交时间”，而系统默认按“处理时间”排序
- 词法前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-conflict#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s7-d3-t1-05-memo#p1@T1 7.s7-d2-t1-04-claim#p1@T1 8.s7-d2-t1-04-claim#p2@T1 9.s5-d0-t1-02-report#p2@T1 10.s7-d3-t1-05-memo#p3@T1
- 混合前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-memo#p1@T1 5.s7-d3-t1-05-conflict#p3@T1 6.s7-d3-t1-05-memo#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-claim#p2@T1 9.s5-d0-t1-02-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 重排前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-conflict#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s7-d3-t1-05-memo#p1@T1 7.s7-d3-t1-05-memo#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s5-d0-t1-02-summary#p3@T1 10.s5-d0-t1-02-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 162. `s7-d2-t1-04-q2`

- 问：多份文档用同一组原始数据、一份说显著改善另一份说没达标时，怎么判断这算不算同快照冲突陈述？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-data#p3@T1
- 金标要点：这种基于相同快照的不同解释，反映合成叙述中对数据的多重建构能力，若缺乏上下文比对，极易引发检索误解
- 词法前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p2@T1 5.s7-d2-t1-04-data#p1@T1 6.s5-d1-t1-03-summary#p2@T1 7.s7-d3-t1-05-claim#p1@T1 8.s7-d0-t1-02-report#p2@T1 9.s2-d0-t1-91-memo#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d2-t1-04-data#p1@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d2-t1-04-brief#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-claim#p2@T1 9.s5-d1-t1-03-summary#p2@T1 10.s5-d0-t1-02-memo#p3@T1
- 重排前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d2-t1-04-data#p1@T1 5.s7-d3-t1-05-claim#p1@T1 6.s5-d0-t1-02-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s5-d1-t1-03-summary#p2@T1 10.s7-d0-t1-02-claim#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 163. `s7-d2-t1-04-q3`

- 问：元陈述与实际内容不一致时，可能引发哪些检索风险？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-claim#p3@T1；s7-d2-t1-04-memo#p3@T1
- 金标要点：此自相矛盾的元声明削弱了整份材料的可信度，构成元层级的检索陷阱，即对内容真实性本身的宣称与实际内容不符；自我宣称与实际证据链之间的脱节
- 词法前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s6-d2-g1-memo#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p3@T1 8.p1-cac-o20#p8@T1 9.s7-d0-t1-02-claim#p1@T1 10.s7-d3-t1-05-memo#p2@T1
- 混合前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d2-t1-04-claim#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d0-t1-02-analysis#p3@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-report#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 重排前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d2-t1-04-claim#p3@T1 4.s7-d0-t1-02-analysis#p3@T1 5.s7-d0-t1-02-brief#p2@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-report#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 164. `s7-d2-t1-04-q4`

- 问：合成叙述如何通过模糊定义和选择性呈现误导用户判断？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-brief#p1@T1
- 金标要点：这种合成叙述通过选择性呈现数据和模糊操作定义，构建出看似合理但有偏差的整体印象，典型体现为对事实的非透明重构；一份关于用户满意度的分析报告称：“多数受访者表示体验良好；“满意”选项的定义被刻意模糊；样本仅来自高活跃用户群体
- 词法前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-synthetic#p2@T1 4.s7-d0-t1-02-claim#p2@T1 5.s7-d0-t1-02-report#p3@T1 6.s6-d0-t1-01-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s3-d0-03-report#p3@T1 10.s7-d3-t1-05-claim#p3@T1
- 混合前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-claim#p3@T1 4.s7-d0-t1-02-report#p2@T1 5.s7-d3-t1-05-synthetic#p2@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s5-d1-t1-03-summary#p3@T1 9.s7-d3-t1-05-memo#p3@T1 10.s7-d2-t1-04-brief#p3@T1
- 重排前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-synthetic#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s7-d2-t1-04-brief#p3@T1 6.s7-d3-t1-05-claim#p3@T1 7.s7-d0-t1-02-report#p2@T1 8.s7-d0-t1-02-memo#p3@T1 9.s7-d3-t1-05-synthetic#p3@T1 10.s5-d1-t1-03-summary#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 165. `s7-d3-t1-05-q1`

- 问：技术组说日志里没有登录失败记录、审计组却说全都抓到了，哪份材料解释了这是术语口径不同？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-memo#p1@T1
- 金标要点：在某次跨部门数据对齐会议中，技术团队报告称“系统日志未记录用户登录失败事件”，而安全审计组却声称“所有登录失败均被完整捕获”；表面上看二者矛盾，实则因术语定义不同：前者指未写入特定日志文件，后者指已通过集中式监控平台覆盖；这种词面撞车现象常引发误判
- 词法前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d3-t1-91-changelog#p2@T1 5.s2-d0-t1-91-memo#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s7-d0-t1-02-report#p1@T1 8.s2-d0-t1-91-interview#p2@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s7-d0-t1-02-claim#p1@T1
- 混合前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p2@T1 3.s6-d1-t1-91-release#p2@T1 4.s7-d0-t1-02-claim#p1@T1 5.s6-d3-t1-91-changelog#p1@T1 6.s6-d3-t1-91-changelog#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d0-t1-02-memo#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 重排前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p2@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d3-t1-91-changelog#p3@T1 5.s7-d0-t1-02-claim#p1@T1 6.s6-d3-t1-91-changelog#p1@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d0-t1-02-memo#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 166. `s7-d3-t1-05-q2`

- 问：哪份文档借“完成度87%仍算达标”一例，揭示了‘达标’在不同评价标准下的多重解释？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-memo#p2@T1
- 金标要点：该指标实际完成度为87%，但经评估后仍视为达标。；这表明系统性地使用“达标”一词掩盖了真实绩效差距，构成元层面的陈述冲突。
- 词法前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d3-t1-05-memo#p3@T1 4.s7-d0-t1-02-memo#p1@T1 5.s7-d2-t1-04-memo#p2@T1 6.s7-d0-t1-02-claim#p1@T1 7.s7-d0-t1-02-update#p3@T1 8.s7-d2-t1-04-memo#p1@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d0-t1-02-report#p3@T1
- 混合前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s7-d3-t1-05-conflict#p2@T1 7.s7-d0-t1-02-claim#p3@T1 8.s6-d3-t1-01-note#p3@T1 9.s5-d1-t1-03-note#p2@T1 10.s7-d2-t1-04-claim#p3@T1
- 重排前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s7-d0-t1-02-claim#p3@T1 7.s7-d2-t1-04-claim#p3@T1 8.s5-d1-t1-03-note#p2@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s6-d3-t1-01-note#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 167. `s7-d3-t1-05-q3`

- 问：哪一个文档展示了通过选择性引用专家来构建虚假权威的现象？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-synthetic#p2@T1
- 金标要点：这种通过选择性引用构建权威感，是合成叙述的常见手法；更隐蔽的是，该材料同时引用“专家普遍认可”作为背书，但所列专家中仅有两人发表过相关研究
- 词法前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-brief#p1@T1 4.s7-d0-t1-02-claim#p3@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d1-t1-03-note#p3@T1 7.s7-d2-t1-04-memo#p3@T1 8.s7-d0-t1-02-update#p1@T1 9.s7-d2-t1-04-brief#p2@T1 10.s5-d1-t1-03-note#p1@T1
- 混合前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-update#p1@T1 4.s7-d2-t1-04-claim#p3@T1 5.s7-d3-t1-05-conflict#p2@T1 6.s5-d0-t1-02-analysis#p3@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-memo#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s5-d1-t1-03-note#p1@T1
- 重排前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-update#p1@T1 4.s7-d2-t1-04-memo#p3@T1 5.s5-d1-t1-03-note#p1@T1 6.s7-d2-t1-04-claim#p3@T1 7.s5-d0-t1-02-analysis#p3@T1 8.s5-d1-t1-03-memo#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s7-d3-t1-05-conflict#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 168. `s7-d3-t1-05-q4`

- 问：哪份文档分析了‘进度保持在预期轨道上’这一说法与实际延迟之间的语义断裂？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-conflict#p1@T1
- 金标要点：在一份项目总结报告中，反复强调“进度保持在预期轨道上”；但详细日程表显示，关键里程碑已延迟两周，且资源调配不足；这里的“预期轨道”未明确定义，导致词面重复掩盖了实质延误，形成语义断裂。
- 词法前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d3-t1-05-conflict#p3@T1 3.s7-d0-t1-02-analysis#p3@T1 4.s5-d2-t1-91-digest#p3@T1 5.s7-d2-t1-04-claim#p3@T1 6.s5-d3-t1-05-analysis#p3@T1 7.s6-d3-t1-91-changelog#p3@T1 8.s6-d3-t1-01-note#p3@T1 9.s6-d3-t1-01-memo#p3@T1 10.s6-d3-t1-01-report#p3@T1
- 混合前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d3-t1-05-conflict#p3@T1 4.s7-d2-t1-04-brief#p2@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s7-d2-t1-04-brief#p3@T1 7.s1-d0-03-memo#p2@T1 8.s7-d2-t1-04-claim#p3@T1 9.s7-d0-t1-02-analysis#p1@T1 10.s7-d0-t1-02-report#p1@T1
- 重排前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d3-t1-05-conflict#p3@T1 3.s7-d0-t1-02-analysis#p3@T1 4.s5-d3-t1-05-analysis#p3@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d2-t1-04-brief#p2@T1 7.s7-d0-t1-02-analysis#p1@T1 8.s7-d2-t1-04-brief#p3@T1 9.s7-d0-t1-02-report#p1@T1 10.s1-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 169. `r4m-s5-d3-t1-05-q4`

- 问：按官方最新统计，这个地区的制造业在经济总量里还占三成以上吗？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-report#p2@T1
- 金标要点：该比例已下降至28%
- 词法前 10：1.s5-d3-t1-05-report#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-01-memo#p1@T1 4.p2-gdp-national#p2@T1 5.s6-d0-t1-03-memo#p1@T1 6.s1-d1-01-analysis#p3@T1 7.s5-d2-t1-91-digest#p3@T1 8.s2-d0-t1-91-interview#p3@T1 9.s6-d0-t1-91-sop#p2@T1 10.s6-d3-t1-91-changelog#p3@T1
- 混合前 10：1.s5-d3-t1-05-report#p1@T1 2.p2-gdp-national#p2@T1 3.s5-d2-t1-91-digest#p3@T1 4.s2-d0-t1-91-memo#p1@T1 5.s6-d3-t1-91-changelog#p3@T1 6.s2-d0-01-memo#p1@T1 7.s5-d2-t1-91-digest#p1@T1 8.s2-d0-t1-91-interview#p3@T1 9.s5-d3-t1-05-report#p2@T1 10.s5-d3-t1-05-memo#p3@T1
- 重排前 10：1.s5-d3-t1-05-report#p1@T1 2.s5-d2-t1-91-digest#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-01-memo#p1@T1 5.s2-d0-t1-91-interview#p3@T1 6.s5-d3-t1-05-memo#p3@T1 7.p2-gdp-national#p2@T1 8.s6-d3-t1-91-changelog#p3@T1 9.s5-d2-t1-91-digest#p1@T1 10.s5-d3-t1-05-report#p2@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 170. `r4m-s5-d3-t1-05-q5`

- 问：员工对工作环境满不满意，最新一轮调查给出的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p2@T1
- 金标要点：满意度已升至67%
- 词法前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s2-d2-01-memo#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d3-t1-05-memo#p2@T1 5.p1-colaw-equity#p3@T1 6.s5-d3-t1-05-analysis#p3@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-cac-o16#p5@T1 9.s2-d0-02-memo#p1@T1 10.s7-d2-t1-04-brief#p1@T1
- 混合前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s7-d2-t1-04-brief#p1@T1 3.s5-d3-t1-05-analysis#p3@T1 4.s1-d1-01-memo#p3@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s1-d0-04-memo#p3@T1 7.s5-d3-t1-05-memo#p2@T1 8.s2-d0-02-memo#p1@T1 9.s1-d0-02-memo#p3@T1 10.s2-d2-01-memo#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s5-d3-t1-05-memo#p2@T1 3.s2-d2-01-memo#p1@T1 4.s7-d2-t1-04-brief#p1@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s5-d3-t1-05-analysis#p2@T1 7.s1-d0-02-memo#p3@T1 8.s1-d1-01-memo#p3@T1 9.s1-d0-04-memo#p3@T1 10.s2-d0-02-memo#p1@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

### 171. `r4m-s5-d3-t1-05-q6`

- 问：城市居民每天坐公交出行的人，最近那次独立调查测出来占多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-memo#p2@T1
- 金标要点：使用公共交通的比例上升至51%
- 词法前 10：1.s5-d3-t1-05-memo#p1@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.p1-colaw-governance#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s3-d1-01-report#p1@T1 6.p2-gdp-national#p2@T1 7.s6-d1-c3-memo#p3@T1 8.p1-colaw-capital-call#p5@T1 9.s1-d3-01-memo#p2@T1 10.s6-d0-t1-03-report#p3@T1
- 混合前 10：1.s5-d3-t1-05-memo#p1@T1 2.s5-d3-t1-05-memo#p2@T1 3.s5-d1-t1-03-report#p2@T1 4.s5-d0-t1-02-analysis#p1@T1 5.s5-d1-t1-03-memo#p2@T1 6.s7-d3-t1-05-synthetic#p1@T1 7.s5-d0-t1-02-memo#p2@T1 8.s6-d1-c3-memo#p3@T1 9.s5-d1-t1-03-memo#p3@T1 10.s6-d0-t1-03-report#p3@T1
- 重排前 10：1.s5-d3-t1-05-memo#p1@T1 2.s5-d3-t1-05-memo#p2@T1 3.s5-d1-t1-03-report#p2@T1 4.s5-d0-t1-02-analysis#p1@T1 5.s5-d1-t1-03-memo#p2@T1 6.s7-d3-t1-05-synthetic#p1@T1 7.s5-d0-t1-02-memo#p2@T1 8.s6-d1-c3-memo#p3@T1 9.s5-d1-t1-03-memo#p3@T1 10.s6-d0-t1-03-report#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 172. `r4m-s5-d0-t1-02-q5`

- 问：被媒体反复转述的早高峰车速和拥堵时长，独立研究实际测到的是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p2@T1
- 金标要点：真实车速为16公里/小时；拥堵时长约为3.2小时
- 词法前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s2-d0-t1-91-interview#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-report#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.p1-cac-o11#p10@T1 9.s5-d0-t1-02-memo#p3@T1 10.s5-d0-t1-02-report#p2@T1
- 混合前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d1-t1-03-summary#p1@T1 7.s5-d0-t1-02-report#p2@T1 8.s4-d0-t1-91-eval#p2@T1 9.s2-d0-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d0-t1-02-report#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s5-d3-t1-05-memo#p1@T1 8.s5-d1-t1-03-summary#p1@T1 9.s4-d0-t1-91-eval#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 173. `r4m-s3-d3-01-q5`

- 问：竞品B这一期的月费，两份比价材料写得一样吗？各写了多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p2@T1；s3-d3-01-report#p2@T1
- 金标要点：月费最低可至99元；月费降至129元
- 词法前 10：1.s3-d1-t1-91-pricesheet#p2@T1 2.s3-d3-01-memo#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d2-01-competitor-pricing#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d1-01-memo#p2@T1 7.s3-d1-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p3@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d0-01-report#p2@T1
- 混合前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d1-t1-91-quote#p3@T1 4.s3-d1-t1-91-pricesheet#p2@T1 5.s3-d3-01-report#p2@T1 6.s3-d1-01-memo#p2@T1 7.s3-d3-01-memo#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-brochure#p2@T1
- 重排前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d3-01-memo#p2@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-01-memo#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-brochure#p2@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 174. `r4m-s3-d0-02-q7`

- 问：C公司149元的新方案现在已经开卖了吗？两份比价材料怎么说？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T1；s3-d0-02-b#p3@T1
- 金标要点：改推“成长计划”订阅制，首年费用149元，含全功能访问及优先技术支持，用户迁移率已达72%；现仅开放限时试用，正式版本将于下季度以149元起售
- 词法前 10：1.s3-d0-02-a#p3@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s7-d2-t1-04-memo#p3@T1 6.s3-d1-t1-91-pricesheet#p3@T1 7.s3-d1-t1-91-pricesheet#p1@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-01-memo#p3@T1 10.p1-colaw-governance#p1@T1
- 混合前 10：1.s3-d0-02-a#p3@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-01-memo#p3@T1 6.s3-d0-01-memo#p3@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-t1-91-pricesheet#p3@T1 9.s3-d0-02-b#p3@T1 10.s3-d0-01-report#p1@T1
- 重排前 10：1.s3-d0-02-a#p3@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-report#p1@T1 7.s3-d1-01-memo#p3@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-t1-91-pricesheet#p3@T1 10.s3-d0-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 175. `r4n-s2-d0-t1-91-qa`

- 问：越南那边的经销商返点，最终按多少给？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d0-t1-91-memo#p1@T1
- 金标要点：把返点比例定为5%
- 词法前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.p2-gdp-national#p3@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-interview#p3@T1 7.s6-d1-t1-91-patch#p1@T1 8.s2-d0-04-memo#p3@T1 9.s6-d3-t1-91-notice#p1@T1 10.p1-colaw-capital-call#p1@T1
- 混合前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-04-memo#p3@T1 5.s4-d2-t1-91-review#p2@T1 6.s2-d0-t1-91-interview#p3@T1 7.s6-d0-t1-91-sop#p3@T1 8.s3-d3-01-report#p2@T1 9.s2-d0-04-memo#p1@T1 10.s2-d0-02-memo#p3@T1
- 重排前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-memo#p3@T1 4.s2-d0-04-memo#p3@T1 5.s2-d0-t1-91-interview#p3@T1 6.s3-d3-01-report#p2@T1 7.s4-d2-t1-91-review#p2@T1 8.s6-d0-t1-91-sop#p3@T1 9.s2-d0-04-memo#p1@T1 10.s2-d0-02-memo#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 176. `r4n-s2-d0-t1-91-qb`

- 问：关于越南经销商返点，访谈里的口径和后来正式签的约有什么出入？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d0-t1-91-interview#p1@T1；s2-d0-t1-91-memo#p1@T1
- 金标要点：返点比例会维持在8%；把返点比例定为5%
- 词法前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d3-t1-91-interview#p2@T1 4.s2-d0-t1-91-interview#p3@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s7-d2-t1-04-brief#p1@T1 9.s6-d3-t1-91-changelog#p1@T1 10.p1-colaw-governance-supervisor-js#p4@T1
- 混合前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s6-d0-t1-91-sop#p3@T1 5.s2-d0-t1-91-memo#p3@T1 6.s6-d3-t1-91-changelog#p1@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-cac-o20#p8@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d0-04-memo#p3@T1
- 重排前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s2-d3-t1-91-interview#p2@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-memo#p3@T1 7.s6-d3-t1-91-changelog#p1@T1 8.p1-cac-o20#p8@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d0-04-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 177. `r4n-s3-d1-t1-91-qa`

- 问：竞品E标准版一年现在要花多少钱？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-quote#p1@T1
- 金标要点：把标准版年费调整为4200元
- 词法前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d1-t1-91-quote#p1@T1 4.s3-d1-t1-91-quote#p3@T1 5.s3-d0-03-report#p1@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d0-02-b#p2@T1 8.s5-d3-t1-05-report#p3@T1 9.s7-d2-t1-04-data#p2@T1 10.s3-d1-01-report#p3@T1
- 混合前 10：1.s3-d1-t1-91-quote#p1@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d0-03-report#p1@T1 4.s3-d1-t1-91-quote#p2@T1 5.s3-d3-01-report#p1@T1 6.s3-d1-t1-91-quote#p3@T1 7.s3-d0-03-memo#p1@T1 8.s3-d0-04-memo#p1@T1 9.s3-d0-03-memo#p2@T1 10.s3-d1-01-report#p3@T1
- 重排前 10：1.s3-d1-t1-91-quote#p1@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p1@T1 7.s3-d0-03-memo#p1@T1 8.s3-d0-04-memo#p1@T1 9.s3-d0-03-memo#p2@T1 10.s3-d1-01-report#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 178. `r4n-s3-d1-t1-91-qb`

- 问：两份材料给竞品E标准版标的年价不一样，分别是多少，哪份更可信？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-pricesheet#p1@T1；s3-d1-t1-91-quote#p1@T1
- 金标要点：竞品E的标准版年费为3600元；把标准版年费调整为4200元
- 词法前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s7-d3-t1-05-synthetic#p2@T1 5.s6-d1-t1-91-patch#p1@T1 6.s6-d3-t1-01-report#p2@T1 7.s6-d3-t1-02-report#p3@T1 8.s3-d1-t1-91-quote#p3@T1 9.s3-d1-t1-91-pricesheet#p2@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p1@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d2-t1-91-contract#p2@T1
- 重排前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d3-01-report#p1@T1 8.s3-d3-01-report#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d2-t1-91-contract#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 179. `r4n-s3-d1-t1-91-qc`

- 问：竞品E标准版一个账号最多能开几个座位？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-quote#p2@T1
- 金标要点：标准版单账号席位上限为25个
- 词法前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.p1-colaw-oneperson#p1@T1 7.s7-d0-t1-02-memo#p2@T1 8.s3-d0-02-b#p2@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s3-d1-01-report#p3@T1
- 混合前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-01-report#p3@T1 6.s6-d3-t1-02-report#p1@T1 7.s3-d3-01-report#p1@T1 8.s5-d2-t1-91-digest#p3@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d0-01-memo#p1@T1
- 重排前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d1-01-report#p3@T1 7.s6-d3-t1-02-report#p1@T1 8.s3-d3-01-report#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s3-d0-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 180. `r4n-s4-d2-t1-91-qa`

- 问：每单履约到底要花多少成本？财务那边怎么认定的？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-review#p1@T1
- 金标要点：单票履约成本应修正为7.4元
- 词法前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s2-d0-02-report#p3@T1 4.s4-d0-t1-02-report#p3@T1 5.s4-d2-t1-04-summary#p3@T1 6.s2-d3-t1-91-minutes#p3@T1 7.s4-d0-t1-02-plan#p1@T1 8.s4-d2-t1-04-report#p1@T1 9.s1-d0-03-report#p3@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s6-d0-t1-03-memo#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s6-d0-t1-03-memo#p1@T1 6.s2-d0-02-report#p3@T1 7.s2-d3-t1-91-minutes#p3@T1 8.s1-d0-02-report#p3@T1 9.p1-colaw-capital#p1@T1 10.s1-d0-01-memo#p3@T1
- 重排前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d0-t1-03-memo#p1@T1 5.s2-d0-02-report#p3@T1 6.s2-d3-t1-91-minutes#p3@T1 7.s6-d0-t1-03-memo#p3@T1 8.s1-d0-02-report#p3@T1 9.p1-colaw-capital#p1@T1 10.s1-d0-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 181. `r4n-s4-d2-t1-91-qb`

- 问：v3模型和财务复核给的每单履约成本差了多少，为什么不一样？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-model-v3#p1@T1；s4-d2-t1-91-review#p1@T1
- 金标要点：单票履约成本应修正为7.4元；单票履约成本为6.8元；漏计包材费用
- 词法前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s4-d0-t1-02-report#p3@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-summary#p3@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d0-t1-02-memo#p1@T1 10.s4-d2-t1-91-review#p2@T1
- 混合前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-91-review#p2@T1 5.s6-d0-t1-03-memo#p2@T1 6.s4-d2-t1-04-report#p1@T1 7.s4-d0-t1-02-memo#p1@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d2-t1-04-memo#p2@T1 10.s4-d0-t1-02-analysis#p1@T1
- 重排前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s4-d0-t1-02-memo#p1@T1 6.s6-d0-t1-03-memo#p2@T1 7.s6-d0-t1-03-internal#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d2-t1-91-review#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 182. `r4n-s4-d2-t1-91-qc`

- 问：复核时用的退货率是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-review#p2@T1
- 金标要点：退货率参数取4.1%
- 词法前 10：1.s4-d2-t1-91-review#p2@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.s6-d0-t1-91-sop#p2@T1 4.s4-d2-t1-91-review#p1@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d2-t1-91-review#p3@T1 7.s2-d0-01-report#p1@T1 8.s7-d3-t1-05-memo#p2@T1 9.s4-d0-t1-91-deck#p2@T1 10.s1-d1-t1-91-memo#p2@T1
- 混合前 10：1.s4-d2-t1-91-review#p2@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.s4-d2-t1-91-review#p1@T1 4.s4-d0-t1-02-guide#p2@T1 5.s6-d0-t1-91-sop#p2@T1 6.s2-d0-02-report#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s4-d2-t1-91-review#p3@T1 9.s2-d0-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s4-d2-t1-91-model-v3#p2@T1 2.s4-d2-t1-91-review#p2@T1 3.s6-d0-t1-91-sop#p2@T1 4.s4-d0-t1-02-guide#p2@T1 5.s2-d0-02-report#p3@T1 6.s1-d1-t1-91-memo#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s4-d0-t1-91-deck#p2@T1 9.s4-d2-t1-91-review#p1@T1 10.s4-d2-t1-91-review#p3@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 183. `r4n-s6-d3-t1-91-qa`

- 问：住户收入的新统计口径到底哪天开始用？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-notice#p1@T1
- 金标要点：新口径的启用时间推迟到6月1日
- 词法前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s1-d1-t1-91-brief#p2@T1 3.s6-d3-t1-91-notice#p1@T1 4.s6-d0-t1-01-patch#p1@T1 5.s4-d0-t1-91-eval#p1@T1 6.s3-d2-01-competitor-pricing#p2@T1 7.s3-d0-01-report#p2@T1 8.s1-d2-01-analysis#p3@T1 9.s5-d3-t1-05-memo#p3@T1 10.s5-d2-t1-91-digest#p1@T1
- 混合前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s6-d3-t1-91-notice#p1@T1 3.s5-d2-t1-91-digest#p1@T1 4.s6-d1-c2-memo#p3@T1 5.s5-d3-t1-05-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.s1-d1-t1-91-brief#p2@T1 8.s1-d0-02-report#p3@T1 9.s1-d0-01-analysis#p3@T1 10.s6-d0-t1-01-patch#p1@T1
- 重排前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s6-d3-t1-91-notice#p1@T1 3.s5-d3-t1-05-memo#p3@T1 4.s5-d2-t1-91-digest#p1@T1 5.s6-d1-c2-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.s1-d1-t1-91-brief#p2@T1 8.s6-d0-t1-01-patch#p1@T1 9.s1-d0-02-report#p3@T1 10.s1-d0-01-analysis#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 184. `r4n-s6-d3-t1-91-qb`

- 问：新收入口径的启用日期，变更日志和执行通知各写的是哪天？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-changelog#p1@T1；s6-d3-t1-91-notice#p1@T1
- 金标要点：新口径的启用时间推迟到6月1日；自5月1日起启用
- 词法前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.p1-colaw-capital-call#p2@T1 4.p1-colaw-capital#p4@T1 5.s6-d3-t1-91-notice#p3@T1 6.p1-colaw-governance#p1@T1 7.s6-d3-t1-03-memo#p3@T1 8.p1-colaw-equity#p3@T1 9.s3-d0-01-report#p2@T1 10.s6-d3-t1-03-memo#p2@T1
- 混合前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-memo#p3@T1 6.s6-d3-t1-02-memo#p2@T1 7.s6-d3-t1-91-notice#p3@T1 8.s6-d2-g2-memo#p2@T1 9.p1-colaw-capital-call#p2@T1 10.s6-d1-c1-memo#p1@T1
- 重排前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-memo#p3@T1 6.s6-d2-g2-memo#p2@T1 7.p1-colaw-capital-call#p2@T1 8.s6-d3-t1-02-memo#p2@T1 9.s6-d3-t1-91-notice#p3@T1 10.s6-d1-c1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 185. `r4n-s6-d3-t1-91-qc`

- 问：这一期调查一共抽了多少户？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-notice#p2@T1
- 金标要点：本期样本户数为1.2万户
- 词法前 10：1.s6-d1-t1-91-release#p2@T1 2.s5-d3-t1-05-memo#p1@T1 3.s7-d0-t1-02-report#p2@T1 4.s5-d1-t1-03-memo#p1@T1 5.s6-d2-t1-91-bulletin#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s7-d3-t1-05-memo#p2@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s7-d2-t1-04-data#p1@T1 10.p2-gdp-national#p1@T1
- 混合前 10：1.s6-d3-t1-91-changelog#p2@T1 2.s4-d0-t1-91-deck#p2@T1 3.s2-d0-t1-91-memo#p2@T1 4.s5-d1-t1-03-memo#p2@T1 5.s5-d1-t1-03-memo#p1@T1 6.s5-d2-t1-91-digest#p3@T1 7.s6-d2-t1-91-bulletin#p2@T1 8.s6-d3-t1-91-changelog#p3@T1 9.s5-d3-t1-05-memo#p1@T1 10.p2-gdp-national#p1@T1
- 重排前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d3-t1-05-memo#p1@T1 3.s6-d3-t1-91-changelog#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.s2-d0-t1-91-memo#p2@T1 6.s5-d1-t1-03-memo#p2@T1 7.s5-d2-t1-91-digest#p3@T1 8.s6-d2-t1-91-bulletin#p2@T1 9.s6-d3-t1-91-changelog#p3@T1 10.p2-gdp-national#p1@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 186. `r4n-s1-d1-t1-91-qa`

- 问：我们在印尼的电子支付牌照现在是什么状态？还需要借别人的通道吗？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-brief#p1@T1
- 金标要点：该电子支付牌照已于8月获批；无需再借合作方通道
- 词法前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s5-d2-t1-91-digest#p3@T1 4.s2-d0-t1-91-interview#p3@T1 5.s5-d0-t1-02-summary#p3@T1 6.s6-d3-t1-91-changelog#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s6-d0-t1-91-sop#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.s7-d2-t1-04-claim#p2@T1
- 混合前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s6-d3-t1-91-changelog#p3@T1 4.s6-d1-c4-memo#p1@T1 5.s7-d2-t1-04-claim#p2@T1 6.s6-d0-t1-91-sop#p1@T1 7.p1-cac-o16#p9@T1 8.p1-cac-o16#p4@T1 9.s1-d0-04-risk#p2@T1 10.p1-colaw-capital-transition#p2@T1
- 重排前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d2-t1-04-claim#p2@T1 4.s6-d0-t1-91-sop#p1@T1 5.p1-cac-o16#p9@T1 6.p1-colaw-capital-transition#p2@T1 7.s6-d3-t1-91-changelog#p3@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o16#p4@T1 10.s1-d0-04-risk#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 187. `r4n-s1-d1-t1-91-qb`

- 问：印尼支付牌照这件事，进入备忘和监管简报的说法有什么冲突？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-memo#p1@T1；s1-d1-t1-91-brief#p1@T1
- 金标要点：该电子支付牌照已于8月获批；电子支付牌照申请仍在审理中；需要借用合作方通道；无需再借合作方通道
- 词法前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s1-d1-t1-91-memo#p3@T1 4.p1-colaw-equity#p1@T1 5.s6-d3-t1-01-memo#p3@T1 6.s6-d3-t1-01-note#p3@T1 7.s6-d3-t1-01-report#p3@T1 8.s7-d0-t1-02-memo#p2@T1 9.s1-d1-t1-91-brief#p3@T1 10.p1-colaw-oneperson#p2@T1
- 混合前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d0-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p2@T1 5.s6-d3-t1-01-memo#p2@T1 6.s1-d1-t1-91-brief#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d3-t1-01-report#p2@T1 9.s6-d3-t1-01-note#p3@T1 10.s6-d2-g2-memo#p2@T1
- 重排前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d0-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p2@T1 5.s6-d3-t1-01-memo#p2@T1 6.s1-d1-t1-91-brief#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d3-t1-01-note#p3@T1 9.s6-d2-g2-memo#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 188. `r4n-s1-d1-t1-91-qc`

- 问：这个季度用户退款平均几天能到账？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-brief#p2@T1
- 金标要点：本季度平均退款到账时长为2.6天
- 词法前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s4-d0-t1-91-eval#p2@T1 4.s1-d1-01-analysis#p1@T1 5.s3-d0-02-a#p1@T1 6.s6-d0-t1-91-change#p3@T1 7.s6-d0-t1-91-sop#p3@T1 8.s6-d0-t1-91-change#p1@T1 9.s6-d0-t1-91-sop#p1@T1 10.s5-d2-t1-91-annual#p3@T1
- 混合前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s6-d0-t1-91-sop#p1@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s4-d0-t1-91-eval#p2@T1 6.s4-d2-t1-91-review#p2@T1 7.s3-d0-02-a#p1@T1 8.s1-d0-03-report#p3@T1 9.s6-d0-t1-91-change#p1@T1 10.s6-d3-t1-91-notice#p1@T1
- 重排前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s4-d0-t1-91-eval#p2@T1 4.s3-d0-02-a#p1@T1 5.s6-d0-t1-91-sop#p1@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s4-d2-t1-91-review#p2@T1 8.s1-d0-03-report#p3@T1 9.s6-d0-t1-91-change#p1@T1 10.s6-d3-t1-91-notice#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 189. `r4n-s5-d2-t1-91-qa`

- 问：这个本地生活平台按最新年报有多少家在营商户？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-annual#p1@T1
- 金标要点：截至年末活跃商户为53万家
- 词法前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s2-d0-01-report#p2@T1 4.s2-d1-01-memo#p1@T1 5.s5-d2-t1-91-digest#p1@T1 6.s5-d2-t1-91-annual#p3@T1 7.p1-colaw-oneperson#p2@T1 8.s5-d1-t1-03-report#p3@T1 9.s1-d1-t1-91-memo#p3@T1 10.s4-d2-t1-91-model-v3#p3@T1
- 混合前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p3@T1 5.s2-d1-01-memo#p1@T1 6.s2-d0-01-report#p2@T1 7.s6-d3-t1-91-changelog#p2@T1 8.p1-colaw-oneperson#p2@T1 9.s3-d1-t1-91-quote#p2@T1 10.s2-d0-01-memo#p3@T1
- 重排前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p3@T1 5.s2-d1-01-memo#p1@T1 6.s2-d0-01-report#p2@T1 7.p1-colaw-oneperson#p2@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s3-d1-t1-91-quote#p2@T1 10.s2-d0-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 190. `r4n-s5-d2-t1-91-qb`

- 问：汇编和年报给出的平台活跃商户规模各是多少？汇编的数为什么不能直接用？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-digest#p1@T1；s5-d2-t1-91-annual#p1@T1
- 金标要点：截至年末活跃商户为53万家；该平台活跃商户约48万家；源自两年前的媒体报道
- 词法前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d2-t1-91-digest#p3@T1 5.s6-d3-t1-01-note#p2@T1 6.s1-d1-t1-91-memo#p3@T1 7.s6-d3-t1-02-report#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d3-t1-01-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 混合前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d2-t1-91-digest#p3@T1 5.s5-d1-t1-03-summary#p2@T1 6.s5-d2-t1-91-annual#p2@T1 7.s5-d0-t1-02-analysis#p2@T1 8.s5-d1-t1-03-report#p2@T1 9.s6-d3-t1-01-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 重排前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d2-t1-91-digest#p3@T1 7.s5-d2-t1-91-annual#p2@T1 8.s5-d0-t1-02-analysis#p2@T1 9.s5-d1-t1-03-report#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 191. `r4n-s5-d2-t1-91-qc`

- 问：平台商户一年下来的留存比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-annual#p2@T1
- 金标要点：年度商户留存率为71%
- 词法前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p1@T1 5.s2-d0-02-memo#p2@T1 6.s1-d1-t1-91-memo#p3@T1 7.s2-d0-t1-91-memo#p1@T1 8.s2-d0-01-report#p1@T1 9.p1-colaw-governance-supervisor#p3@T1 10.p1-colaw-governance-supervisor-js#p1@T1
- 混合前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-annual#p1@T1 4.s5-d2-t1-91-digest#p1@T1 5.s2-d0-01-report#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.s5-d2-t1-91-annual#p3@T1 8.s2-d0-t1-91-interview#p1@T1 9.s2-d1-01-memo#p1@T1 10.s1-d0-02-report#p1@T1
- 重排前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-digest#p1@T1 3.s5-d2-t1-91-annual#p2@T1 4.s5-d2-t1-91-annual#p1@T1 5.s2-d0-01-report#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.s2-d0-t1-91-interview#p1@T1 8.s2-d1-01-memo#p1@T1 9.s5-d2-t1-91-annual#p3@T1 10.s1-d0-02-report#p1@T1
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 192. `r4n-s2-d2-t0-91-qa`

- 问：这批包装材料最后确认几天能交货？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-email#p1@T0
- 金标要点：交期更正为14天
- 词法前 10：1.s2-d2-t0-91-email#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.s2-d2-t0-91-email#p3@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s1-d1-01-memo#p2@T0 8.s1-d0-05-warn#p3@T0 9.s1-d0-05-memo#p3@T0 10.s2-d2-01-report#p1@T0
- 混合前 10：1.s2-d2-t0-91-email#p1@T0 2.s2-d2-t0-91-callnotes#p1@T0 3.s2-d2-t0-91-email#p3@T0 4.s1-d1-01-memo#p2@T0 5.s1-d0-05-memo#p3@T0 6.s2-d0-04-memo#p2@T0 7.s1-d0-03-memo#p1@T0 8.s2-d0-03-memo#p3@T0 9.s1-d0-05-warn#p3@T0 10.s2-d2-01-report#p1@T0
- 重排前 10：1.s2-d2-t0-91-email#p1@T0 2.s2-d2-t0-91-callnotes#p1@T0 3.s2-d2-t0-91-email#p3@T0 4.s1-d1-01-memo#p2@T0 5.s1-d0-05-memo#p3@T0 6.s2-d0-04-memo#p2@T0 7.s1-d0-03-memo#p1@T0 8.s2-d0-03-memo#p3@T0 9.s1-d0-05-warn#p3@T0 10.s2-d2-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 193. `r4n-s2-d2-t0-91-qb`

- 问：包装材料交期，电话里说的和邮件里确认的各是几天？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-callnotes#p1@T0；s2-d2-t0-91-email#p1@T0
- 金标要点：交期更正为14天；交期为10天
- 词法前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s2-d2-t0-91-callnotes#p2@T0 4.s7-d0-t0-01-internal#p1@T0 5.s5-d1-t0-91-repost#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s2-d2-t0-91-email#p3@T0 8.s7-d1-t0-03-fact#p3@T0 9.s2-d2-t0-91-email#p2@T0 10.s2-d3-01-memo#p1@T0
- 混合前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s2-d2-t0-91-email#p3@T0 4.s2-d2-t0-91-email#p2@T0 5.s7-d1-t0-03-memo#p2@T0 6.p1-cac-o11#p13@T0 7.s2-d2-t0-91-callnotes#p2@T0 8.s1-d0-03-memo#p1@T0 9.s7-d0-t0-01-internal#p1@T0 10.s5-d1-t0-91-repost#p2@T0
- 重排前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s2-d2-t0-91-callnotes#p2@T0 5.s7-d0-t0-01-internal#p1@T0 6.s2-d2-t0-91-email#p2@T0 7.p1-cac-o11#p13@T0 8.s1-d0-03-memo#p1@T0 9.s5-d1-t0-91-repost#p2@T0 10.s2-d2-t0-91-email#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 194. `r4n-s2-d2-t0-91-qc`

- 问：这一批货抽检的次品比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-email#p2@T0
- 金标要点：本批抽检不良率为0.9%
- 词法前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.p1-colaw-governance-supervisor-js#p1@T0 3.p1-colaw-governance-supervisor#p1@T0 4.s2-d2-t0-91-callnotes#p1@T0 5.p1-colaw-equity#p2@T0 6.s2-d2-t0-91-email#p2@T0 7.s7-d1-t0-03-memo#p2@T0 8.s1-d1-01-analysis#p3@T0 9.s1-d0-04-memo#p3@T0 10.s5-d0-t0-01-analysis#p2@T0
- 混合前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.s2-d2-t0-91-email#p2@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.p2-gdp-national#p2@T0 5.p1-colaw-governance-supervisor-js#p1@T0 6.s4-d0-t0-01-report#p2@T0 7.s5-d2-t0-04-analysis#p1@T0 8.p2-gdp-national#p1@T0 9.s5-d1-t0-91-repost#p1@T0 10.p1-colaw-governance-supervisor#p1@T0
- 重排前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.s2-d2-t0-91-email#p2@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.p2-gdp-national#p2@T0 5.p1-colaw-governance-supervisor-js#p1@T0 6.p2-gdp-national#p1@T0 7.p1-colaw-governance-supervisor#p1@T0 8.s4-d0-t0-01-report#p2@T0 9.s5-d2-t0-04-analysis#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 195. `r4n-s3-d0-t0-91-qa`

- 问：竞品H客服坐席现在每个席位每月什么价？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-pricing#p1@T0
- 金标要点：当前标价为每席每月52美元
- 词法前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d0-t0-91-flyer#p3@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d2-01-competitor-pricing#p3@T0 6.s3-d0-02-a#p1@T0 7.s3-d0-02-b#p2@T0 8.s3-d0-01-report#p2@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s3-d0-04-memo#p2@T0
- 混合前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d2-01-competitor-pricing#p3@T0 4.s3-d0-03-report#p1@T0 5.s3-d0-01-memo#p1@T0 6.s3-d0-01-memo#p2@T0 7.s3-d1-01-memo#p1@T0 8.s3-d0-03-memo#p1@T0 9.s3-d0-04-memo#p2@T0 10.s3-d2-01-competitor-pricing#p1@T0
- 重排前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d2-01-competitor-pricing#p3@T0 3.s3-d0-t0-91-pricing#p1@T0 4.s3-d0-03-report#p1@T0 5.s3-d0-01-memo#p1@T0 6.s3-d0-01-memo#p2@T0 7.s3-d1-01-memo#p1@T0 8.s3-d0-03-memo#p1@T0 9.s3-d0-04-memo#p2@T0 10.s3-d2-01-competitor-pricing#p1@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 196. `r4n-s3-d0-t0-91-qb`

- 问：竞品H坐席价格，传单和官网标的不一样，各是多少、差在哪？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-flyer#p1@T0；s3-d0-t0-91-pricing#p1@T0
- 金标要点：当前标价为每席每月52美元；传单价格为上一季度活动价；每席每月45美元
- 词法前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-flyer#p3@T0 3.s3-d0-t0-91-pricing#p1@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d0-04-memo#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s3-d1-01-report#p2@T0 8.s3-d0-t0-91-pricing#p2@T0 9.p1-colaw-governance-supervisor-js#p2@T0 10.s3-d0-01-report#p3@T0
- 混合前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d0-01-memo#p1@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d2-01-competitor-pricing#p1@T0 6.s3-d1-01-report#p2@T0 7.s3-d0-03-report#p3@T0 8.s3-d0-04-memo#p2@T0 9.s3-d0-01-report#p3@T0 10.s3-d3-01-memo#p3@T0
- 重排前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d0-01-memo#p1@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d2-01-competitor-pricing#p1@T0 6.s3-d1-01-report#p2@T0 7.s3-d0-03-report#p3@T0 8.s3-d0-04-memo#p2@T0 9.s3-d0-01-report#p3@T0 10.s3-d3-01-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 197. `r4n-s3-d0-t0-91-qc`

- 问：新团队注册竞品H能免费试多久？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-pricing#p2@T0
- 金标要点：可获得14天免费试用
- 词法前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d0-t0-91-flyer#p3@T0 4.s3-d2-01-competitor-pricing#p2@T0 5.s3-d0-t0-91-flyer#p1@T0 6.s3-d0-03-memo#p2@T0 7.s4-d1-t0-03-analysis#p1@T0 8.s3-d0-03-report#p2@T0 9.s3-d1-01-report#p3@T0 10.s2-d0-03-memo#p3@T0
- 混合前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d2-01-competitor-pricing#p2@T0 4.s3-d0-03-report#p2@T0 5.s3-d0-03-memo#p2@T0 6.s3-d1-01-report#p3@T0 7.s3-d3-01-memo#p3@T0 8.s3-d0-t0-91-flyer#p1@T0 9.s3-d1-01-report#p1@T0 10.s3-d0-01-memo#p3@T0
- 重排前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d2-01-competitor-pricing#p2@T0 4.s3-d0-03-memo#p2@T0 5.s3-d0-03-report#p2@T0 6.s3-d1-01-report#p3@T0 7.s3-d3-01-memo#p3@T0 8.s3-d0-t0-91-flyer#p1@T0 9.s3-d0-01-memo#p3@T0 10.s3-d1-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 198. `r4n-s4-d0-t1-91-qa`

- 问：工单自动分派用全量数据复评后准确率是多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-eval#p1@T1
- 金标要点：自动分派准确率为86%
- 词法前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-eval#p3@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s4-d0-t1-02-guide#p2@T1 7.p1-cac-o11#p12@T1 8.s2-d3-t1-91-minutes#p1@T1 9.s7-d0-t1-02-brief#p2@T1 10.s7-d2-t1-04-claim#p2@T1
- 混合前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.p1-cac-o11#p12@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d0-t1-91-eval#p3@T1 7.s4-d2-t1-04-internal#p1@T1 8.s2-d0-t1-91-memo#p2@T1 9.s4-d2-t1-91-model-v3#p2@T1 10.s7-d2-t1-04-memo#p2@T1
- 重排前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d0-t1-91-eval#p3@T1 7.s7-d2-t1-04-memo#p2@T1 8.p1-cac-o11#p12@T1 9.s4-d2-t1-04-internal#p1@T1 10.s2-d0-t1-91-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 199. `r4n-s4-d0-t1-91-qb`

- 问：自动分派准确率，汇报材料和复评报告各报了多少？哪个是小样本？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-deck#p1@T1；s4-d0-t1-91-eval#p1@T1
- 金标要点：自动分派准确率为86%；准确率达到92%；只来自早期小样本
- 词法前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p3@T1 5.s4-d0-t1-91-deck#p2@T1 6.s7-d2-t1-04-memo#p3@T1 7.p1-cac-o11#p12@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d2-t1-04-brief#p1@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.p1-cac-o11#p12@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-report#p1@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s7-d2-t1-04-memo#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 重排前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.s4-d2-t1-04-report#p1@T1 6.s7-d2-t1-04-memo#p2@T1 7.p1-cac-o11#p12@T1 8.s4-d0-t1-02-guide#p2@T1 9.s6-d3-t1-91-changelog#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 200. `r4n-s4-d0-t1-91-qc`

- 问：上了自动分派以后，一张工单平均多久处理完？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-eval#p2@T1
- 金标要点：工单平均处理时长下降到18分钟
- 词法前 10：1.s4-d0-t1-91-eval#p2@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p1@T1 4.s1-d1-t1-91-brief#p2@T1 5.s4-d0-t1-91-deck#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s1-d1-01-analysis#p1@T1 8.s3-d3-01-memo#p2@T1 9.s6-d3-t1-91-changelog#p2@T1 10.s4-d2-t1-04-report#p3@T1
- 混合前 10：1.s4-d0-t1-91-eval#p2@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p1@T1 4.s2-d0-t1-91-memo#p2@T1 5.s4-d0-t1-91-deck#p2@T1 6.s1-d1-t1-91-brief#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s4-d0-t1-02-guide#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d2-t1-04-report#p3@T1
- 重排前 10：1.s4-d0-t1-91-eval#p2@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p1@T1 4.s2-d0-t1-91-memo#p2@T1 5.s4-d0-t1-91-deck#p2@T1 6.s1-d1-t1-91-brief#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s4-d0-t1-02-guide#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d2-t1-04-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 201. `r4n-s6-d1-t1-91-qa`

- 问：老的v1接口最终什么时候停？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-patch#p1@T1
- 金标要点：下线时间延期至11月30日
- 词法前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-patch#p2@T1 5.s6-d1-t1-91-release#p2@T1 6.s4-d2-t1-04-summary#p3@T1 7.s6-d3-t1-02-memo#p3@T1 8.p1-cac-o11#p12@T1 9.p2-gdp-national#p3@T1 10.s4-d0-t1-02-memo#p3@T1
- 混合前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s6-d1-t1-91-patch#p2@T1 6.s2-d3-01-memo#p3@T1 7.s4-d0-t1-02-memo#p3@T1 8.s6-d3-t1-02-memo#p3@T1 9.s6-d3-t1-91-notice#p1@T1 10.s4-d2-t1-04-summary#p3@T1
- 重排前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s6-d1-t1-91-patch#p2@T1 6.s6-d3-t1-02-memo#p3@T1 7.s4-d2-t1-04-summary#p3@T1 8.s2-d3-01-memo#p3@T1 9.s4-d0-t1-02-memo#p3@T1 10.s6-d3-t1-91-notice#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 202. `r4n-s6-d1-t1-91-qb`

- 问：v1接口下线时间，发布说明和补丁公告分别怎么写的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-release#p1@T1；s6-d1-t1-91-patch#p1@T1
- 金标要点：下线时间延期至11月30日；将于9月30日下线
- 词法前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p3@T1 5.s6-d1-t1-91-patch#p2@T1 6.s5-d0-t1-02-report#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s7-d0-t1-02-report#p3@T1 9.p2-gdp-national#p3@T1 10.s3-d2-t1-91-brochure#p1@T1
- 混合前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s1-d0-01-analysis#p3@T1 6.s6-d3-t1-02-memo#p1@T1 7.s6-d1-t1-91-patch#p2@T1 8.s3-d2-t1-91-brochure#p1@T1 9.s6-d3-t1-02-report#p1@T1 10.s6-d3-t1-03-report#p1@T1
- 重排前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p3@T1 5.s6-d1-t1-91-patch#p2@T1 6.s1-d0-01-analysis#p3@T1 7.s6-d3-t1-02-memo#p1@T1 8.s3-d2-t1-91-brochure#p1@T1 9.s6-d3-t1-02-report#p1@T1 10.s6-d3-t1-03-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 203. `r4n-s6-d1-t1-91-qc`

- 问：v2接口最近一周调用成功的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-patch#p2@T1
- 金标要点：上周v2接口调用成功率为99.2%
- 词法前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s4-d2-t1-91-model-v3#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.p1-colaw-governance-supervisor#p3@T1 8.p1-colaw-governance-supervisor-js#p1@T1 9.s1-d3-01-memo#p2@T1 10.s6-d1-t1-91-patch#p1@T1
- 混合前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s6-d1-t1-91-patch#p1@T1 6.s4-d0-t1-02-memo#p3@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-01-report#p1@T1 9.s4-d2-t1-04-summary#p3@T1 10.s2-d3-01-memo#p3@T1
- 重排前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s6-d1-t1-91-patch#p1@T1 6.s4-d0-t1-91-deck#p2@T1 7.s4-d2-t1-04-summary#p3@T1 8.s4-d0-t1-02-memo#p3@T1 9.s2-d0-01-report#p1@T1 10.s2-d3-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 204. `r4n-s1-d3-t0-91-qa`

- 问：本季度出口同比增长按修订后的数是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-statbrief#p1@T0
- 金标要点：本季度出口同比增速为5.4%
- 词法前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s2-d1-01-report#p3@T0 4.s1-d3-t0-91-statbrief#p2@T0 5.s1-d3-t0-91-statbrief#p3@T0 6.s2-d0-02-report#p2@T0 7.s5-d2-t0-04-report#p2@T0 8.s4-d3-t0-05-report#p1@T0 9.s4-d3-t0-91-method#p1@T0 10.s2-d1-01-report#p2@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s2-d1-01-report#p3@T0 4.s1-d3-t0-91-statbrief#p3@T0 5.s2-d0-02-report#p1@T0 6.s1-d3-t0-91-statbrief#p2@T0 7.s2-d0-02-report#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s3-d0-t0-91-pricing#p1@T0 10.s1-d2-01-report#p1@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s2-d1-01-report#p3@T0 4.s1-d3-t0-91-statbrief#p3@T0 5.s2-d0-02-report#p1@T0 6.s1-d3-t0-91-statbrief#p2@T0 7.s2-d0-02-report#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s3-d0-t0-91-pricing#p1@T0 10.s1-d2-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 205. `r4n-s1-d3-t0-91-qb`

- 问：出口增速，研判备忘和统计快报各用的是多少？哪个是修订后的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-memo#p1@T0；s1-d3-t0-91-statbrief#p1@T0
- 金标要点：本季度出口同比增速为6.1%；本季度出口同比增速为5.4%；比初步数下调0.7个百分点
- 词法前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s1-d3-t0-91-statbrief#p3@T0 4.s2-d2-t0-91-callnotes#p2@T0 5.s1-d1-01-analysis#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s5-d0-t0-01-analysis#p2@T0 8.p1-cac-o11#p16@T0 9.s1-d3-t0-91-memo#p2@T0 10.s7-d0-t0-01-qa#p1@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s1-d3-t0-91-statbrief#p3@T0 4.s1-d3-t0-91-memo#p2@T0 5.s1-d3-t0-91-memo#p3@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d3-t0-91-statbrief#p2@T0 8.s4-d3-t0-91-method#p1@T0 9.p1-cac-o11#p16@T0 10.s4-d0-t0-01-feedback#p1@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.p1-cac-o11#p16@T0 4.s1-d3-t0-91-statbrief#p3@T0 5.s1-d3-t0-91-memo#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s4-d3-t0-91-method#p1@T0 8.s4-d0-t0-01-feedback#p1@T0 9.s1-d3-t0-91-memo#p3@T0 10.s1-d3-t0-91-statbrief#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 206. `r4n-s1-d3-t0-91-qc`

- 问：主要港口的货物吞吐比去年同期增长了多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-statbrief#p2@T0
- 金标要点：主要港口货物吞吐量同比增长3.8%
- 词法前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s2-d0-01-memo#p3@T0 3.s1-d3-t0-91-memo#p2@T0 4.s2-d0-02-report#p1@T0 5.s2-d0-01-report#p1@T0 6.s5-d2-t0-04-analysis#p2@T0 7.s4-d0-t0-01-plan#p2@T0 8.s1-d2-01-report#p1@T0 9.s2-d1-01-report#p3@T0 10.s1-d3-t0-91-statbrief#p1@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s1-d3-t0-91-memo#p2@T0 3.s1-d3-t0-91-statbrief#p1@T0 4.s2-d0-01-memo#p3@T0 5.s1-d2-01-report#p1@T0 6.s1-d0-01-memo#p3@T0 7.s2-d0-02-report#p1@T0 8.s2-d1-01-report#p3@T0 9.s1-d3-t0-91-statbrief#p3@T0 10.s1-d3-t0-91-memo#p3@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s2-d0-01-memo#p3@T0 3.s2-d0-02-report#p1@T0 4.s1-d3-t0-91-memo#p2@T0 5.s1-d2-01-report#p1@T0 6.s1-d0-01-memo#p3@T0 7.s2-d1-01-report#p3@T0 8.s1-d3-t0-91-statbrief#p3@T0 9.s1-d3-t0-91-memo#p3@T0 10.s1-d3-t0-91-statbrief#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 207. `r4n-s5-d1-t0-91-qa`

- 问：按原始调研，本地消费者网购渗透率实际是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d1-t0-91-survey#p1@T0
- 金标要点：线上购物渗透率实测为54%
- 词法前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d2-t0-04-memo#p2@T0 5.s1-d0-01-analysis#p2@T0 6.s4-d3-t0-91-method#p1@T0 7.s1-d1-01-report#p3@T0 8.s3-d1-01-memo#p3@T0 9.s5-d1-t0-91-survey#p3@T0 10.s3-d2-01-quotation-snapshot#p2@T0
- 混合前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d1-t0-91-survey#p3@T0 5.s5-d2-t0-04-memo#p2@T0 6.s2-d0-03-memo#p2@T0 7.s1-d0-02-memo#p1@T0 8.s2-d2-01-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s1-d0-01-memo#p1@T0
- 重排前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d2-t0-04-memo#p2@T0 5.s5-d1-t0-91-survey#p3@T0 6.s2-d0-03-memo#p2@T0 7.s1-d0-02-memo#p1@T0 8.s2-d2-01-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s1-d0-01-memo#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 208. `r4n-s5-d1-t0-91-qb`

- 问：网购渗透率，转述文章和原始调研各说了多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d1-t0-91-repost#p1@T0；s5-d1-t0-91-survey#p1@T0
- 金标要点：线上购物渗透率已经超过六成；线上购物渗透率实测为54%
- 词法前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s5-d2-t0-04-memo#p1@T0 4.s5-d1-t0-91-repost#p3@T0 5.s5-d2-t0-04-report#p3@T0 6.s5-d2-t0-04-memo#p2@T0 7.s7-d0-t0-01-qa#p1@T0 8.s2-d0-04-memo#p1@T0 9.s5-d1-t0-91-repost#p2@T0 10.s7-d1-t0-03-fact#p2@T0
- 混合前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s5-d2-t0-04-memo#p2@T0 4.s2-d0-04-memo#p1@T0 5.s5-d1-t0-91-survey#p3@T0 6.s1-d0-02-memo#p1@T0 7.s1-d0-04-memo#p1@T0 8.s2-d0-03-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s2-d2-01-memo#p2@T0
- 重排前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s5-d2-t0-04-memo#p2@T0 4.s2-d0-04-memo#p1@T0 5.s5-d1-t0-91-survey#p3@T0 6.s1-d0-02-memo#p1@T0 7.s1-d0-04-memo#p1@T0 8.s2-d0-03-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s2-d2-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 209. `r4n-s5-d1-t0-91-qc`

- 问：消费者平均隔多少天会再次下单？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d1-t0-91-survey#p2@T0
- 金标要点：平均复购周期为37天
- 词法前 10：1.s5-d1-t0-91-survey#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s2-d2-t0-91-email#p3@T0 4.s1-d0-01-analysis#p2@T0 5.s5-d1-t0-91-repost#p1@T0 6.s3-d0-t0-91-pricing#p2@T0 7.s2-d2-t0-91-email#p1@T0 8.s2-d2-t0-91-callnotes#p1@T0 9.s2-d1-01-report#p1@T0 10.s7-d1-t0-03-reason#p2@T0
- 混合前 10：1.s5-d1-t0-91-survey#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.s5-d1-t0-91-repost#p1@T0 5.s2-d2-01-report#p2@T0 6.s2-d2-t0-91-email#p1@T0 7.s1-d1-01-analysis#p1@T0 8.s2-d2-t0-91-email#p3@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s2-d1-01-report#p1@T0
- 重排前 10：1.s5-d1-t0-91-survey#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.s5-d1-t0-91-repost#p1@T0 5.s2-d2-01-report#p2@T0 6.s2-d2-t0-91-email#p1@T0 7.s1-d1-01-analysis#p1@T0 8.s2-d2-t0-91-email#p3@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s2-d1-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 210. `r4n-s2-d3-t1-91-qa`

- 问：区域试点今年获批的是几个城市？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-minutes#p1@T1
- 金标要点：会议批准的试点范围是8个城市
- 词法前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s4-d0-t1-91-deck#p2@T1 5.s1-d2-01-report#p1@T1 6.s2-d0-03-memo#p2@T1 7.s1-d1-t1-91-brief#p3@T1 8.s2-d0-02-memo#p2@T1 9.s2-d0-02-interview#p2@T1 10.s5-d1-t1-03-report#p2@T1
- 混合前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d0-02-interview#p2@T1 5.s2-d0-03-memo#p2@T1 6.s1-d2-01-report#p1@T1 7.s1-d1-t1-91-memo#p3@T1 8.s2-d0-02-memo#p2@T1 9.s5-d1-t1-03-report#p2@T1 10.s2-d0-t1-91-interview#p1@T1
- 重排前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d0-03-memo#p2@T1 5.s2-d0-02-memo#p2@T1 6.s5-d1-t1-03-report#p2@T1 7.s2-d0-02-interview#p2@T1 8.s1-d2-01-report#p1@T1 9.s1-d1-t1-91-memo#p3@T1 10.s2-d0-t1-91-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 211. `r4n-s2-d3-t1-91-qb`

- 问：试点城市数量，CEO访谈和董事会纪要说法差在哪？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-interview#p1@T1；s2-d3-t1-91-minutes#p1@T1
- 金标要点：会议批准的试点范围是8个城市；今年会扩到12个城市
- 词法前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.s6-d0-t1-02-report#p1@T1 7.s6-d0-t1-02-memo#p1@T1 8.s6-d0-t1-02-internal#p1@T1 9.s1-d2-01-report#p1@T1 10.s1-d1-t1-91-memo#p3@T1
- 混合前 10：1.s2-d3-t1-91-minutes#p1@T1 2.s2-d3-t1-91-interview#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.p1-colaw-governance-board#p4@T1 7.p1-colaw-governance-board#p3@T1 8.s1-d2-01-report#p1@T1 9.s2-d0-03-memo#p2@T1 10.s2-d0-t1-91-interview#p1@T1
- 重排前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.s2-d0-t1-91-interview#p1@T1 7.p1-colaw-governance-board#p4@T1 8.p1-colaw-governance-board#p3@T1 9.s1-d2-01-report#p1@T1 10.s2-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 212. `r4n-s2-d3-t1-91-qc`

- 问：每个试点城市最多能拿多少补贴？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-minutes#p2@T1
- 金标要点：每城试点补贴上限为300万元
- 词法前 10：1.s2-d3-t1-91-interview#p2@T1 2.s2-d3-t1-91-minutes#p2@T1 3.s2-d3-t1-91-minutes#p1@T1 4.s2-d3-t1-91-minutes#p3@T1 5.s2-d3-t1-91-interview#p1@T1 6.s1-d2-01-report#p1@T1 7.s2-d0-03-memo#p2@T1 8.s1-d1-t1-91-memo#p3@T1 9.s5-d2-t1-91-annual#p3@T1 10.s4-d0-t1-91-deck#p2@T1
- 混合前 10：1.s2-d3-t1-91-minutes#p2@T1 2.s2-d3-t1-91-interview#p2@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s2-d3-t1-91-interview#p1@T1 6.s2-d3-01-interview#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-02-interview#p2@T1 9.s1-d1-t1-91-memo#p3@T1 10.s1-d2-01-report#p1@T1
- 重排前 10：1.s2-d3-t1-91-minutes#p2@T1 2.s2-d3-t1-91-interview#p2@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s2-d3-t1-91-interview#p1@T1 6.s2-d3-01-interview#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-02-interview#p2@T1 9.s1-d1-t1-91-memo#p3@T1 10.s1-d2-01-report#p1@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 213. `r4n-s3-d2-t1-91-qa`

- 问：竞品G的合规模块按合同到底收不收钱？多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-contract#p1@T1
- 金标要点：合规模块单独计费每月800元
- 词法前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p2@T1 3.s3-d2-t1-91-contract#p1@T1 4.s3-d2-t1-91-brochure#p3@T1 5.s6-d1-c3-memo#p2@T1 6.s3-d2-t1-91-brochure#p2@T1 7.s3-d1-t1-91-quote#p1@T1 8.s2-d0-t1-91-memo#p1@T1 9.s3-d2-01-quotation-snapshot#p2@T1 10.s3-d1-t1-91-pricesheet#p1@T1
- 混合前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d1-01-memo#p3@T1 10.s3-d0-03-report#p1@T1
- 重排前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p2@T1 3.s3-d2-t1-91-contract#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d0-03-report#p1@T1 10.s3-d1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 214. `r4n-s3-d2-t1-91-qb`

- 问：竞品G合规模块的收费，宣传册和合同报价单怎么说的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-brochure#p1@T1；s3-d2-t1-91-contract#p1@T1
- 金标要点：合规模块单独计费每月800元；数据合规模块免费附送；只适用于首年促销
- 词法前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-brochure#p3@T1 4.s3-d2-t1-91-brochure#p2@T1 5.s3-d2-t1-91-contract#p2@T1 6.s3-d2-t1-91-contract#p3@T1 7.s2-d0-t1-91-memo#p1@T1 8.s3-d2-01-quotation-snapshot#p2@T1 9.s6-d1-c3-memo#p2@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 混合前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-contract#p2@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d2-t1-91-brochure#p2@T1 6.s3-d2-01-quotation-snapshot#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d2-t1-91-contract#p3@T1 9.s3-d1-01-report#p1@T1 10.s3-d2-t1-91-brochure#p3@T1
- 重排前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-contract#p2@T1 4.s3-d2-t1-91-brochure#p2@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d2-t1-91-brochure#p3@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d2-t1-91-contract#p3@T1 10.s3-d1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 215. `r4n-s3-d2-t1-91-qc`

- 问：竞品G在合同里承诺的服务可用性是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-contract#p2@T1
- 金标要点：SLA承诺为99.95%
- 词法前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-brochure#p3@T1 3.s6-d0-t1-91-sop#p2@T1 4.s2-d0-t1-91-memo#p1@T1 5.s3-d2-t1-91-brochure#p1@T1 6.s3-d2-t1-91-brochure#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s4-d2-t1-04-summary#p2@T1 9.s1-d1-t1-91-memo#p2@T1 10.s2-d0-t1-91-interview#p2@T1
- 混合前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d0-03-memo#p1@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d1-t1-91-pricesheet#p2@T1 5.s3-d0-03-report#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-01-report#p1@T1 8.s3-d0-04-memo#p1@T1 9.s2-d0-t1-91-memo#p1@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 重排前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-brochure#p1@T1 3.s3-d1-t1-91-pricesheet#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d3-01-report#p2@T1 6.s2-d0-t1-91-memo#p1@T1 7.s3-d0-03-memo#p1@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p1@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 216. `r4n-s4-d3-t0-91-qa`

- 问：电力折算标准煤现在该用多大的系数？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-method#p1@T0
- 金标要点：该折算系数应为0.76
- 词法前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s7-d0-t0-01-qa#p2@T0 4.s3-d0-t0-91-flyer#p3@T0 5.s5-d0-t0-01-memo#p3@T0 6.s5-d0-t0-01-summary#p2@T0 7.s7-d1-t0-03-reason#p1@T0 8.s4-d0-t0-01-memo#p2@T0 9.s3-d0-03-report#p2@T0 10.s3-d0-02-a#p2@T0
- 混合前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s1-d0-03-memo#p1@T0 4.s4-d3-t0-05-memo#p3@T0 5.s1-d3-01-memo#p2@T0 6.s4-d3-t0-91-calc#p2@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s2-d2-t0-91-callnotes#p1@T0 10.p1-colaw-capital-transition#p2@T0
- 重排前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s1-d0-03-memo#p1@T0 4.s4-d3-t0-05-memo#p3@T0 5.s1-d3-01-memo#p2@T0 6.s4-d3-t0-91-calc#p2@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s2-d2-t0-91-callnotes#p1@T0 10.p1-colaw-capital-transition#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 217. `r4n-s4-d3-t0-91-qb`

- 问：电力折标煤系数，测算表和方法更新说明各取多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-calc#p1@T0；s4-d3-t0-91-method#p1@T0
- 金标要点：该折算系数应为0.76；系数取0.82
- 词法前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s3-d2-01-quotation-snapshot#p3@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d0-t0-01-qa#p1@T0 8.s7-d1-t0-03-fact#p3@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s1-d1-01-analysis#p2@T0
- 混合前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s4-d3-t0-91-calc#p3@T0 6.s4-d0-t0-01-summary#p1@T0 7.s1-d3-t0-91-statbrief#p3@T0 8.s2-d2-t0-91-email#p1@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d1-t0-03-memo#p1@T0
- 重排前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s4-d0-t0-01-summary#p1@T0 6.s2-d2-t0-91-email#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d1-t0-03-memo#p1@T0 9.s4-d3-t0-91-calc#p3@T0 10.s1-d3-t0-91-statbrief#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 218. `r4n-s4-d3-t0-91-qc`

- 问：今年产线实际利用了多少产能？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-method#p2@T0
- 金标要点：本年度产线利用率为78%
- 词法前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d3-t0-91-method#p2@T0 3.s4-d0-t0-01-summary#p1@T0 4.s1-d0-02-report#p2@T0 5.s7-d0-t0-01-internal#p1@T0 6.s7-d0-t0-01-memo#p1@T0 7.s7-d0-t0-01-arch#p1@T0 8.s2-d0-04-memo#p2@T0 9.s7-d0-t0-01-qa#p2@T0 10.p1-cac-o11#p10@T0
- 混合前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d3-t0-91-method#p2@T0 3.s1-d0-02-report#p2@T0 4.s2-d0-04-memo#p2@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-91-calc#p3@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d1-t0-03-memo#p1@T0 9.s7-d0-t0-01-internal#p1@T0 10.s7-d0-t0-01-arch#p1@T0
- 重排前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d0-t0-01-summary#p1@T0 3.s7-d0-t0-01-internal#p1@T0 4.s7-d0-t0-01-arch#p1@T0 5.s4-d3-t0-91-method#p2@T0 6.s1-d0-02-report#p2@T0 7.s2-d0-04-memo#p2@T0 8.s4-d3-t0-91-calc#p3@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d1-t0-03-memo#p1@T0
- 建议：保持 bm25
- 理由：两边都碰上了金标，词法把金标排得更靠前。

### 219. `r4n-s6-d0-t1-91-qa`

- 问：退款多少钱以上才要主管点头？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-change#p1@T1
- 金标要点：退款审批阈值改为500美元以上
- 词法前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s2-d0-t1-91-interview#p2@T1 4.s6-d0-t1-91-change#p3@T1 5.s6-d0-t1-02-internal#p3@T1 6.s6-d0-t1-91-sop#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s1-d1-t1-91-brief#p2@T1 9.p1-colaw-oneperson#p1@T1 10.p1-colaw-oneperson#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d0-t1-91-change#p3@T1 4.s1-d1-t1-91-brief#p2@T1 5.s1-d1-t1-91-memo#p2@T1 6.s6-d0-t1-02-internal#p3@T1 7.s2-d0-t1-91-interview#p2@T1 8.p1-colaw-oneperson#p2@T1 9.p1-colaw-oneperson#p1@T1 10.s6-d0-t1-91-sop#p3@T1
- 重排前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d0-t1-91-change#p3@T1 4.s1-d1-t1-91-brief#p2@T1 5.s1-d1-t1-91-memo#p2@T1 6.s6-d0-t1-02-internal#p3@T1 7.s2-d0-t1-91-interview#p2@T1 8.p1-colaw-oneperson#p2@T1 9.p1-colaw-oneperson#p1@T1 10.s6-d0-t1-91-sop#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 220. `r4n-s6-d0-t1-91-qb`

- 问：退款要主管审批的金额线，手册和变更单各写的是多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-sop#p1@T1；s6-d0-t1-91-change#p1@T1
- 金标要点：金额在300美元以上的退款需要主管审批；退款审批阈值改为500美元以上
- 词法前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d0-t1-91-sop#p3@T1 4.s6-d0-t1-91-sop#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.s1-d1-t1-91-memo#p2@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-colaw-liquidation#p2@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d3-t1-03-memo#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d3-t1-03-memo#p2@T1 4.s6-d0-t1-91-change#p3@T1 5.s1-d1-t1-91-memo#p2@T1 6.s6-d2-g2-memo#p2@T1 7.s6-d0-t1-01-patch#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s6-d0-t1-91-sop#p3@T1
- 重排前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d3-t1-03-memo#p2@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d2-g2-memo#p2@T1 6.s6-d0-t1-01-patch#p2@T1 7.s6-d0-t1-91-sop#p3@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s6-d0-t1-91-change#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 221. `r4n-s6-d0-t1-91-qc`

- 问：客服上个月一次就把问题解决的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-change#p2@T1
- 金标要点：上月首次解决率为74%
- 词法前 10：1.s6-d0-t1-91-sop#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-04-memo#p3@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-03-interview#p3@T1 7.s6-d2-t1-91-audit#p1@T1 8.s6-d2-t1-91-bulletin#p1@T1 9.s1-d3-01-memo#p2@T1 10.s6-d0-t1-91-change#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s6-d0-t1-91-change#p2@T1 4.s2-d0-t1-91-memo#p1@T1 5.s2-d0-02-report#p3@T1 6.s2-d0-t1-91-memo#p2@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d0-t1-91-sop#p1@T1 9.s2-d2-01-report#p2@T1 10.s6-d2-t1-91-bulletin#p1@T1
- 重排前 10：1.s6-d0-t1-91-sop#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s2-d0-t1-91-memo#p1@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d0-t1-91-change#p2@T1 6.s2-d0-02-report#p3@T1 7.s2-d0-t1-91-memo#p2@T1 8.s6-d0-t1-91-sop#p1@T1 9.s6-d2-t1-91-bulletin#p1@T1 10.s2-d2-01-report#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 222. `r4n-s6-d2-t1-91-qa`

- 问：夜班也算进去的话，仓库安检过关的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-audit#p1@T1
- 金标要点：仓库安检通过比例写成百分之九十一
- 词法前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s2-d0-t1-91-memo#p1@T1 4.p1-colaw-governance-supervisor#p1@T1 5.p1-colaw-governance-supervisor#p3@T1 6.p1-colaw-governance-supervisor-js#p1@T1 7.s3-d2-t1-91-contract#p2@T1 8.s6-d2-t1-91-audit#p3@T1 9.p1-colaw-equity#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 混合前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s6-d2-t1-91-audit#p3@T1 4.s2-d0-t1-91-memo#p1@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.p1-colaw-governance-supervisor#p1@T1 8.p1-colaw-governance-supervisor#p3@T1 9.s3-d2-t1-91-contract#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s2-d0-t1-91-memo#p1@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.p1-colaw-governance-supervisor#p1@T1 7.p1-colaw-governance-supervisor#p3@T1 8.s3-d2-t1-91-contract#p2@T1 9.s4-d0-t1-91-deck#p2@T1 10.s6-d2-t1-91-audit#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 223. `r4n-s6-d2-t1-91-qb`

- 问：一份只覆盖白班，另一份把夜班补了进去，过关比例两边分别是什么？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-bulletin#p1@T1；s6-d2-t1-91-audit#p1@T1
- 金标要点：仓库安检通过比例写成百分之九十六；仓库安检通过比例写成百分之九十一
- 词法前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s7-d3-t1-05-memo#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d2-t1-91-digest#p2@T1 6.s7-d2-t1-04-data#p3@T1 7.s7-d2-t1-04-claim#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d2-t1-04-data#p2@T1 10.s7-d2-t1-04-memo#p2@T1
- 混合前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s6-d2-t1-91-audit#p3@T1 4.s7-d2-t1-04-data#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s6-d3-t1-91-changelog#p1@T1 8.s7-d2-t1-04-claim#p2@T1 9.s4-d2-t1-91-review#p3@T1 10.s2-d3-t1-91-interview#p1@T1
- 重排前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s7-d2-t1-04-claim#p2@T1 4.s7-d2-t1-04-data#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s6-d2-t1-91-audit#p3@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s6-d3-t1-91-changelog#p1@T1 9.s4-d2-t1-91-review#p3@T1 10.s2-d3-t1-91-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 224. `r4n-s6-d2-t1-91-qc`

- 问：这个月仓库里工伤报了几起？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-audit#p2@T1
- 金标要点：该月因工受伤为七件
- 词法前 10：1.s6-d2-t1-91-bulletin#p2@T1 2.s6-d1-t1-91-release#p2@T1 3.s6-d2-t1-91-audit#p1@T1 4.s6-d2-t1-91-bulletin#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-t1-91-memo#p1@T1 7.s3-d1-t1-91-quote#p3@T1 8.s6-d0-t1-91-sop#p2@T1 9.s2-d3-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 混合前 10：1.s6-d2-t1-91-bulletin#p2@T1 2.s6-d2-t1-91-audit#p1@T1 3.s6-d2-t1-91-bulletin#p1@T1 4.s2-d0-t1-91-interview#p2@T1 5.s6-d2-t1-91-audit#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s6-d0-t1-91-sop#p2@T1 9.s6-d2-t1-91-audit#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 重排前 10：1.s2-d0-t1-91-interview#p2@T1 2.s6-d2-t1-91-bulletin#p2@T1 3.s6-d2-t1-91-audit#p1@T1 4.s6-d2-t1-91-bulletin#p1@T1 5.s6-d2-t1-91-audit#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s6-d0-t1-91-sop#p2@T1 9.s6-d2-t1-91-audit#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 建议：可议 hybrid+rerank
- 理由：重排的前 10 条里有金标，词法没有。

## 混合 vs 重排

### 1. `p1-lx-01-new`

- 问：数据出境安全评估办法规定评估结果有效期为几年？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p13@T0
- 金标要点：通过数据出境安全评估的结果有效期为2年
- 词法前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p5@T0 4.p1-cac-o11#p3@T0 5.p1-cac-o11#p15@T0 6.p1-cac-o11#p11@T0 7.p1-cac-o11#p7@T0 8.p1-cac-o11#p12@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p2@T0
- 混合前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p11@T0 3.p1-cac-o11#p15@T0 4.p1-cac-o11#p5@T0 5.p1-cac-o11#p3@T0 6.p1-cac-o11#p1@T0 7.p1-cac-o11#p12@T0 8.p1-cac-o11#p14@T0 9.p1-cac-o11#p7@T0 10.p1-cac-o11#p17@T0
- 重排前 10：1.p1-cac-o11#p13@T0 2.p1-cac-o11#p11@T0 3.p1-cac-o11#p1@T0 4.p1-cac-o11#p7@T0 5.p1-cac-o11#p15@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p3@T0 8.p1-cac-o11#p14@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p12@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 2. `p1-lx-02-new`

- 问：个人信息出境标准合同办法要求合同生效后多少个工作日内备案？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p6@T0
- 金标要点：在标准合同生效之日起10个工作日内向所在地省级网信部门备案
- 词法前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p7@T0 5.p1-cac-o13#p4@T0 6.p1-cac-o13#p8@T0 7.p1-cac-o13#p2@T0 8.p1-cac-o11#p4@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p15@T0
- 混合前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p8@T0 5.p1-cac-o13#p7@T0 6.p1-cac-o13#p2@T0 7.p1-cac-o11#p17@T0 8.p1-cac-o13#p4@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p6@T0
- 重排前 10：1.p1-cac-o13#p6@T0 2.p1-cac-o13#p5@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p4@T0 5.p1-cac-o13#p8@T0 6.p1-cac-o13#p7@T0 7.p1-cac-o13#p2@T0 8.p1-cac-o11#p17@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p6@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 3. `p1-lx-03-new`

- 问：数据出境安全评估办法：省级网信部门收到申报材料后几个工作日内完成完备性查验？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p6@T1
- 金标要点：自收到申报材料之日起5个工作日内完成完备性查验
- 词法前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.s6-d1-c1-memo#p2@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p12@T1 6.p1-cac-o11#p11@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p6@T1 9.p1-cac-o13#p6@T1 10.p1-cac-o16#p7@T1
- 混合前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.p1-cac-o11#p15@T1 5.s6-d1-c1-memo#p2@T1 6.p1-cac-o11#p12@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p7@T1 9.p1-cac-o13#p6@T1 10.p1-cac-o11#p13@T1
- 重排前 10：1.p1-cac-o11#p6@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p2@T1 6.p1-cac-o16#p7@T1 7.s6-d1-c1-memo#p2@T1 8.p1-cac-o13#p6@T1 9.p1-cac-o11#p12@T1 10.p1-cac-o11#p13@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 4. `p1-lx-04-new`

- 问：数据出境安全评估办法规定国家网信部门发出书面受理通知书后多少个工作日内完成评估？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p11@T1
- 金标要点：自向数据处理者发出书面受理通知书之日起45个工作日内完成数据出境安全评估
- 词法前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p6@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p15@T1 6.p1-cac-o11#p12@T1 7.p1-cac-o16#p6@T1 8.p1-cac-o11#p2@T1 9.p1-cac-o20#p3@T1 10.p1-cac-o16#p11@T1
- 混合前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p6@T1 4.p1-cac-o11#p15@T1 5.p1-cac-o11#p12@T1 6.s6-d1-c1-memo#p2@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o16#p7@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o11#p17@T1
- 重排前 10：1.p1-cac-o11#p11@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p15@T1 4.p1-cac-o11#p2@T1 5.p1-cac-o16#p7@T1 6.p1-cac-o11#p6@T1 7.s6-d1-c1-memo#p2@T1 8.p1-cac-o16#p11@T1 9.p1-cac-o11#p12@T1 10.p1-cac-o11#p17@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 5. `p1-lx-05-new`

- 问：数据处理者对评估结果有异议的，收到结果后多少个工作日内可以申请复评？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p12@T1
- 金标要点：在收到评估结果15个工作日内向国家网信部门申请复评
- 词法前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p6@T1 6.s6-d1-c1-memo#p3@T1 7.p1-cac-o11#p13@T1 8.p1-colaw-liquidation#p6@T1 9.p1-cac-o11#p15@T1 10.p1-cac-o11#p2@T1
- 混合前 10：1.p1-cac-o11#p12@T1 2.s6-d1-c1-memo#p2@T1 3.p1-cac-o16#p9@T1 4.p1-cac-o11#p11@T1 5.p1-cac-o11#p13@T1 6.s6-d1-c1-memo#p3@T1 7.p1-cac-o11#p6@T1 8.p1-cac-o11#p15@T1 9.p1-cac-o13#p6@T1 10.s4-d0-t1-91-eval#p2@T1
- 重排前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.p1-cac-o11#p11@T1 4.s6-d1-c1-memo#p2@T1 5.p1-cac-o11#p6@T1 6.p1-cac-o11#p13@T1 7.s6-d1-c1-memo#p3@T1 8.p1-cac-o11#p15@T1 9.p1-cac-o13#p6@T1 10.s4-d0-t1-91-eval#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 6. `p1-lx-06-new`

- 问：个人信息出境认证办法自哪一天起施行？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o20#p9@T1
- 金标要点：本办法自2026年1月1日起施行
- 词法前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p9@T1 5.p1-cac-o20#p1@T1 6.p1-cac-o20#p6@T1 7.p1-cac-o20#p2@T1 8.s6-d1-c3-memo#p2@T1 9.p1-cac-o16#p3@T1 10.p1-cac-o13#p1@T1
- 混合前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p2@T1 5.p1-cac-o20#p6@T1 6.p1-cac-o20#p1@T1 7.p1-cac-o20#p7@T1 8.p1-cac-o16#p8@T1 9.p1-cac-o16#p11@T1 10.s6-d1-c3-memo#p2@T1
- 重排前 10：1.p1-cac-o20#p8@T1 2.p1-cac-o13#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o20#p2@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o20#p6@T1 7.p1-cac-o20#p1@T1 8.p1-cac-o20#p7@T1 9.p1-cac-o16#p11@T1 10.s6-d1-c3-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 7. `p1-lx-07-new`

- 问：公司法规定，通过简易程序注销公司登记的公告期限不少于多少日？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p6@T1
- 金标要点：公告期限不少于二十日
- 词法前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p1@T1 5.s6-d2-g2-memo#p3@T1 6.s6-d1-t1-91-patch#p1@T1 7.p1-colaw-capital#p2@T1 8.p1-colaw-liquidation#p3@T1 9.p1-colaw-equity#p4@T1 10.p1-colaw-capital-call#p3@T1
- 混合前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g2-memo#p1@T1 4.p1-colaw-liquidation#p3@T1 5.p1-colaw-capital#p1@T1 6.s6-d2-g1-memo#p1@T1 7.s6-d2-g2-memo#p3@T1 8.p1-colaw-capital-call#p3@T1 9.s6-d2-g1-memo#p2@T1 10.p1-colaw-equity#p5@T1
- 重排前 10：1.p1-colaw-liquidation#p6@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g2-memo#p1@T1 4.p1-colaw-capital#p1@T1 5.s6-d2-g2-memo#p3@T1 6.p1-colaw-liquidation#p3@T1 7.p1-colaw-capital-call#p3@T1 8.s6-d2-g1-memo#p2@T1 9.p1-colaw-equity#p5@T1 10.s6-d2-g1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 8. `p1-lx-08-new`

- 问：股东对失权有异议的，应当自接到失权通知之日起多少日内向人民法院提起诉讼？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p3@T1
- 金标要点：自接到失权通知之日起三十日内，向人民法院提起诉讼
- 词法前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p3@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-liquidation#p3@T1 6.p1-colaw-equity#p1@T1 7.p1-colaw-liquidation#p6@T1 8.s6-d3-t1-91-notice#p1@T1 9.s6-d2-g3-memo#p1@T1 10.p1-cac-o11#p12@T1
- 混合前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p3@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-liquidation#p3@T1 6.p1-colaw-equity#p1@T1 7.p1-colaw-liquidation#p6@T1 8.s6-d2-g3-memo#p1@T1 9.p1-colaw-capital-call#p1@T1 10.p1-colaw-liquidation#p5@T1
- 重排前 10：1.p1-colaw-capital-call#p3@T1 2.p1-colaw-equity#p5@T1 3.p1-colaw-equity#p3@T1 4.p1-colaw-equity#p1@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-liquidation#p3@T1 7.p1-colaw-liquidation#p6@T1 8.p1-colaw-liquidation#p5@T1 9.p1-colaw-capital-call#p1@T1 10.s6-d2-g3-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 9. `p1-lx-09-new`

- 问：公司法（2018）规定一个自然人可以投资设立几个一人有限责任公司？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-oneperson#p3@T0
- 金标要点：一个自然人只能投资设立一个一人有限责任公司
- 词法前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-governance#p3@T0 4.p1-colaw-oneperson#p1@T0 5.p1-colaw-governance#p2@T0 6.p1-colaw-equity#p4@T0 7.p1-colaw-governance-board#p3@T0 8.p1-colaw-equity#p5@T0 9.p1-colaw-governance-board#p2@T0 10.p1-colaw-capital#p1@T0
- 混合前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-oneperson#p1@T0 4.p1-colaw-governance-board#p3@T0 5.p1-colaw-governance-board#p2@T0 6.p1-colaw-governance#p2@T0 7.p1-colaw-equity#p4@T0 8.p1-colaw-governance-supervisor#p1@T0 9.p1-colaw-capital#p2@T0 10.p1-colaw-governance#p3@T0
- 重排前 10：1.p1-colaw-oneperson#p3@T0 2.p1-colaw-governance-board#p1@T0 3.p1-colaw-equity#p4@T0 4.p1-colaw-governance#p3@T0 5.p1-colaw-governance-board#p3@T0 6.p1-colaw-governance-board#p2@T0 7.p1-colaw-governance#p2@T0 8.p1-colaw-governance-supervisor#p1@T0 9.p1-colaw-oneperson#p1@T0 10.p1-colaw-capital#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 10. `p1-lx-10-new`

- 问：2023年全国国内生产总值修订后的现价总量是多少亿元？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p2-gdp-national#p1@T1
- 金标要点：2023年全国国内生产总值修订后的现价总量是1294272亿元
- 词法前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s7-d2-t1-04-data#p2@T1 7.p1-cac-o13#p8@T1 8.s2-d3-t1-91-minutes#p1@T1 9.p1-cac-o16#p11@T1 10.s6-d2-g2-memo#p3@T1
- 混合前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s5-d3-t1-05-report#p1@T1 6.s5-d1-t1-03-report#p2@T1 7.s4-d2-t1-91-model-v3#p2@T1 8.s7-d2-t1-04-data#p2@T1 9.s5-d3-t1-05-report#p2@T1 10.s6-d3-t1-03-memo#p3@T1
- 重排前 10：1.p2-gdp-national#p1@T1 2.p2-gdp-national#p3@T1 3.p2-gdp-national#p2@T1 4.s6-d2-g2-memo#p1@T1 5.s5-d1-t1-03-report#p2@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s7-d2-t1-04-data#p2@T1 8.s5-d3-t1-05-report#p1@T1 9.s5-d3-t1-05-report#p2@T1 10.s6-d3-t1-03-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 11. `p1-lx-11-new`

- 问：公司法规定公司减少注册资本，应当自股东会作出决议之日起几日内通知债权人？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p3@T1
- 金标要点：自股东会作出减少注册资本决议之日起十日内通知债权人
- 词法前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-governance#p2@T1 7.p1-colaw-governance#p3@T1 8.p1-colaw-capital#p1@T1 9.s6-d2-g1-memo#p1@T1 10.p1-colaw-liquidation#p4@T1
- 混合前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-equity#p5@T1 3.p1-colaw-liquidation#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-governance#p3@T1 7.p1-colaw-liquidation#p4@T1 8.s6-d2-g1-memo#p1@T1 9.p1-colaw-equity#p3@T1 10.p1-colaw-governance#p2@T1
- 重排前 10：1.p1-colaw-liquidation#p3@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-equity#p3@T1 7.p1-colaw-governance#p2@T1 8.p1-colaw-governance#p3@T1 9.p1-colaw-liquidation#p4@T1 10.s6-d2-g1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 12. `p1-lx-12-new`

- 问：数据出境安全评估办法所称重要数据是指什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p16@T0
- 金标要点：本办法所称重要数据，是指一旦遭到篡改、破坏、泄露或者非法获取、非法利用等，可能危害国家安全、经济运行、社会稳定、公共健康和安全等的数据。
- 词法前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p3@T0 4.p1-cac-o11#p15@T0 5.p1-cac-o11#p13@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p2@T0 8.p1-cac-o11#p7@T0 9.p1-cac-o11#p17@T0 10.p1-cac-o11#p11@T0
- 混合前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p3@T0 4.p1-cac-o11#p15@T0 5.p1-cac-o11#p7@T0 6.p1-cac-o11#p5@T0 7.p1-cac-o11#p13@T0 8.p1-cac-o11#p2@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p4@T0
- 重排前 10：1.p1-cac-o11#p16@T0 2.p1-cac-o11#p1@T0 3.p1-cac-o11#p13@T0 4.p1-cac-o11#p2@T0 5.p1-cac-o11#p3@T0 6.p1-cac-o11#p15@T0 7.p1-cac-o11#p7@T0 8.p1-cac-o11#p5@T0 9.p1-cac-o11#p11@T0 10.p1-cac-o11#p4@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 13. `p1-mh-02-new`

- 问：非关基企业出境一般个人信息（不含敏感个人信息），旧规和新规分别到多少人就要报安全评估？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p2@T1；p1-cac-o16#p7@T1
- 金标要点：自上年1月1日起累计向境外提供10万人个人信息；自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）
- 词法前 10：1.s6-d1-c2-memo#p1@T1 2.s6-d1-c3-memo#p3@T1 3.p1-cac-o20#p2@T1 4.p1-cac-o16#p5@T1 5.p1-cac-o13#p3@T1 6.p1-cac-o20#p5@T1 7.p1-cac-o16#p7@T1 8.p1-cac-o11#p2@T1 9.p1-cac-o16#p6@T1 10.p1-cac-o13#p4@T1
- 混合前 10：1.s6-d1-c2-memo#p1@T1 2.s6-d1-c3-memo#p3@T1 3.p1-cac-o20#p2@T1 4.p1-cac-o16#p7@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o16#p5@T1 7.p1-cac-o13#p3@T1 8.p1-cac-o11#p2@T1 9.s6-d1-c4-memo#p1@T1 10.p1-cac-o13#p2@T1
- 重排前 10：1.s6-d1-c2-memo#p1@T1 2.p1-cac-o16#p7@T1 3.p1-cac-o16#p5@T1 4.p1-cac-o11#p2@T1 5.s6-d1-c4-memo#p1@T1 6.s6-d1-c3-memo#p3@T1 7.p1-cac-o20#p2@T1 8.p1-cac-o16#p8@T1 9.p1-cac-o13#p3@T1 10.p1-cac-o13#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 14. `p1-mh-03-new`

- 问：只算一般个人信息、不涉及敏感个人信息的话，签标准合同这条路，老办法和新规定各卡在多少人？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p2@T1；p1-cac-o16#p8@T1
- 金标要点：自上年1月1日起累计向境外提供个人信息不满10万人的；处理个人信息不满100万人的；自当年1月1日起累计向境外提供10万人以上、不满100万人个人信息（不含敏感个人信息）
- 词法前 10：1.s6-d1-c3-memo#p3@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p8@T1 4.p1-cac-o16#p2@T1 5.s6-d1-c2-memo#p3@T1 6.p1-cac-o13#p7@T1 7.p1-cac-o16#p3@T1 8.p1-cac-o16#p6@T1 9.s6-d1-c4-memo#p1@T1 10.s6-d1-c3-memo#p1@T1
- 混合前 10：1.s6-d1-c3-memo#p3@T1 2.p1-cac-o16#p8@T1 3.s6-d1-c2-memo#p3@T1 4.s6-d1-c3-memo#p2@T1 5.p1-cac-o13#p2@T1 6.p1-cac-o13#p7@T1 7.s6-d1-c3-memo#p1@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o13#p5@T1 10.p1-cac-o20#p2@T1
- 重排前 10：1.s6-d1-c3-memo#p3@T1 2.p1-cac-o16#p8@T1 3.s6-d1-c3-memo#p2@T1 4.p1-cac-o13#p7@T1 5.p1-cac-o13#p2@T1 6.s6-d1-c4-memo#p1@T1 7.s6-d1-c2-memo#p3@T1 8.s6-d1-c3-memo#p1@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o13#p5@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 15. `p1-mh-04-new`

- 问：不是关基、也不涉及重要数据的小公司，一年只出境几千人的一般个人信息，过去要签标准合同，如今还需要吗？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o13#p2@T1；p1-cac-o16#p4@T1；p1-cac-o16#p5@T1
- 金标要点：自上年1月1日起累计向境外提供个人信息不满10万人的；关键信息基础设施运营者以外的数据处理者自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息）的；免予申报数据出境安全评估、订立个人信息出境标准合同、通过个人信息保护认证
- 词法前 10：1.p1-cac-o16#p2@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p3@T1 4.p1-cac-o16#p6@T1 5.s6-d1-c3-memo#p3@T1 6.s6-d1-c3-memo#p1@T1 7.p1-cac-o16#p1@T1 8.p1-cac-o16#p4@T1 9.p1-cac-o20#p3@T1 10.s6-d1-c4-memo#p1@T1
- 混合前 10：1.p1-cac-o16#p2@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o20#p3@T1 4.p1-cac-o16#p4@T1 5.p1-cac-o16#p8@T1 6.p1-cac-o16#p3@T1 7.s6-d1-c3-memo#p3@T1 8.s6-d1-c3-memo#p1@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o16#p6@T1
- 重排前 10：1.p1-cac-o16#p2@T1 2.p1-cac-o16#p3@T1 3.p1-cac-o16#p11@T1 4.p1-cac-o16#p6@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o20#p3@T1 7.p1-cac-o16#p4@T1 8.p1-cac-o16#p8@T1 9.s6-d1-c3-memo#p3@T1 10.s6-d1-c3-memo#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 16. `p1-mh-05-new`

- 问：认证办法从哪天开始施行？新规下走标准合同的人数区间是多少？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o20#p9@T1；p1-cac-o16#p8@T1
- 金标要点：本办法自2026年1月1日起施行；自当年1月1日起累计向境外提供10万人以上、不满100万人个人信息（不含敏感个人信息）或者不满1万人敏感个人信息的
- 词法前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o20#p8@T1 3.s6-d1-c3-memo#p2@T1 4.s6-d1-c3-memo#p3@T1 5.p1-cac-o11#p17@T1 6.p1-cac-o13#p8@T1 7.p1-cac-o13#p1@T1 8.p1-cac-o13#p5@T1 9.p1-cac-o16#p11@T1 10.p1-cac-o20#p9@T1
- 混合前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o20#p8@T1 3.p1-cac-o11#p17@T1 4.p1-cac-o13#p5@T1 5.p1-cac-o13#p8@T1 6.p1-cac-o16#p11@T1 7.p1-cac-o20#p9@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o16#p8@T1 10.p1-cac-o13#p1@T1
- 重排前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o16#p8@T1 3.p1-cac-o20#p8@T1 4.p1-cac-o16#p11@T1 5.s6-d1-c4-memo#p1@T1 6.p1-cac-o13#p1@T1 7.p1-cac-o11#p17@T1 8.p1-cac-o13#p5@T1 9.p1-cac-o13#p8@T1 10.p1-cac-o20#p9@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 17. `p1-mh-06-new`

- 问：有限公司股东认缴的钱要几年内交齐？新法生效前设立、期限更长的公司要怎么处理？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital#p1@T1；p1-colaw-capital-transition#p1@T1
- 金标要点：自公司成立之日起五年内缴足；应当逐步调整至本法规定的期限以内
- 词法前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p2@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital#p4@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-transition#p1@T1 8.s6-d2-g1-memo#p1@T1 9.s2-d0-t1-91-interview#p2@T1 10.p1-colaw-equity#p5@T1
- 混合前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g1-memo#p1@T1 3.p1-colaw-capital#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g3-memo#p3@T1 6.s6-d2-g2-memo#p3@T1 7.p1-colaw-capital-call#p4@T1 8.p1-colaw-capital-transition#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-capital#p4@T1
- 重排前 10：1.s6-d2-g1-memo#p2@T1 2.p1-colaw-capital#p1@T1 3.s6-d2-g2-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital-transition#p1@T1 6.p1-colaw-capital#p4@T1 7.s6-d2-g1-memo#p1@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital-transition#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 18. `p1-mh-07-new`

- 问：股东逾期不交出资，除了补交还要担什么？宽限期过了公司能怎么处置他的股权？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-transition#p2@T1；p1-colaw-capital-call#p2@T1
- 金标要点：该股东丧失其未缴纳出资的股权；还应当对给公司造成的损失承担赔偿责任；公司经董事会决议可以向该股东发出失权通知
- 词法前 10：1.p1-colaw-capital-call#p2@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-equity#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-equity#p3@T1 7.s6-d2-g3-memo#p2@T1 8.p1-colaw-capital-call#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-capital-call#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p2@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-capital-call#p1@T1 4.p1-colaw-capital-call#p3@T1 5.s6-d2-g3-memo#p1@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-transition#p2@T1 8.s6-d2-g3-memo#p2@T1 9.p1-colaw-equity#p5@T1 10.p1-colaw-equity#p1@T1
- 重排前 10：1.p1-colaw-capital-call#p2@T1 2.s6-d2-g3-memo#p2@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-call#p3@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-capital-call#p1@T1 7.s6-d2-g3-memo#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital-transition#p2@T1 10.p1-colaw-equity#p5@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 19. `p1-mh-08-new`

- 问：董事会没去催缴出资导致损失，谁来赔？欠缴股东本人又要对公司赔什么？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p1@T1；p1-colaw-capital-transition#p2@T1
- 金标要点：负有责任的董事应当承担赔偿责任；还应当对给公司造成的损失承担赔偿责任
- 词法前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.p1-colaw-capital-call#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-governance-board#p3@T1 7.s6-d2-g1-memo#p2@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-governance-board#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.p1-colaw-capital-call#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-capital-call#p3@T1 8.p1-colaw-capital-call#p5@T1 9.p1-colaw-governance-board#p3@T1 10.p1-colaw-capital#p1@T1
- 重排前 10：1.p1-colaw-capital-call#p1@T1 2.s6-d2-g3-memo#p1@T1 3.s6-d2-g3-memo#p2@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p3@T1 7.p1-colaw-capital#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital-call#p5@T1 10.p1-colaw-governance-board#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 20. `p1-mh-09-new`

- 问：现在一个人能单独设有限公司吗？他认缴的出资几年内要缴完？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-oneperson#p1@T1；p1-colaw-capital#p1@T1
- 金标要点：自公司成立之日起五年内缴足；有限责任公司由一个以上五十个以下股东出资设立。
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-call#p5@T1 3.p1-colaw-governance-board#p2@T1 4.p1-colaw-capital#p4@T1 5.p1-colaw-governance-supervisor-js#p5@T1 6.p1-colaw-oneperson#p1@T1 7.p1-colaw-governance-board#p4@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-liquidation#p4@T1
- 混合前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital#p1@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-call#p5@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-oneperson#p1@T1 7.p1-colaw-capital-call#p1@T1 8.p1-colaw-capital-call#p2@T1 9.p1-colaw-governance-supervisor-js#p5@T1 10.p1-colaw-capital#p3@T1
- 重排前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-governance-supervisor-js#p5@T1 6.s6-d2-g1-memo#p1@T1 7.p1-colaw-oneperson#p1@T1 8.p1-colaw-capital-call#p1@T1 9.p1-colaw-capital-call#p2@T1 10.p1-colaw-capital#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 21. `p1-mh-10-new`

- 问：减资补亏之后，股东没交的出资能免掉吗？公司还不上债时，没到期的出资能被要求提前交吗？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-liquidation#p5@T1；p1-colaw-capital-call#p4@T1
- 金标要点：不得免除股东缴纳出资或者股款的义务；有权要求已认缴出资但未届出资期限的股东提前缴纳出资
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p2@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-capital#p3@T1 7.s6-d2-g3-memo#p2@T1 8.p1-colaw-liquidation#p5@T1 9.s6-d2-g1-memo#p3@T1 10.p1-colaw-capital-call#p3@T1
- 混合前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-call#p2@T1 3.p1-colaw-capital-call#p1@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-liquidation#p5@T1 7.s6-d2-g3-memo#p1@T1 8.p1-colaw-capital-call#p3@T1 9.s6-d2-g3-memo#p2@T1 10.s6-d2-g3-memo#p3@T1
- 重排前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-liquidation#p5@T1 3.p1-colaw-capital-transition#p2@T1 4.s6-d2-g3-memo#p2@T1 5.p1-colaw-capital-call#p2@T1 6.p1-colaw-capital-call#p1@T1 7.p1-colaw-capital-call#p5@T1 8.s6-d2-g3-memo#p1@T1 9.p1-colaw-capital-call#p3@T1 10.s6-d2-g3-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 22. `p1-mh-11-new`

- 问：股东把股权卖给外人要先通知谁、别人有什么权利？卖的若是还没到期的认缴出资，由谁来交？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-equity#p1@T1；p1-colaw-capital-call#p5@T1
- 金标要点：其他股东在同等条件下有优先购买权；由受让人承担缴纳该出资的义务；应当将股权转让的数量、价格、支付方式和期限等事项书面通知其他股东
- 词法前 10：1.p1-colaw-capital-call#p4@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p3@T1 4.p1-colaw-capital-call#p2@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-equity#p3@T1 7.p1-colaw-equity#p1@T1 8.p1-colaw-equity#p5@T1 9.s6-d2-g3-memo#p3@T1 10.p1-colaw-capital#p1@T1
- 混合前 10：1.p1-colaw-capital-call#p5@T1 2.p1-colaw-capital-transition#p2@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-equity#p1@T1 5.p1-colaw-equity#p3@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-capital-call#p3@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital#p3@T1 10.p1-colaw-equity#p5@T1
- 重排前 10：1.p1-colaw-capital-transition#p2@T1 2.p1-colaw-equity#p1@T1 3.p1-colaw-capital-call#p3@T1 4.s6-d2-g3-memo#p3@T1 5.p1-colaw-capital-call#p5@T1 6.p1-colaw-capital-call#p4@T1 7.p1-colaw-equity#p3@T1 8.p1-colaw-capital-call#p2@T1 9.p1-colaw-equity#p5@T1 10.p1-colaw-capital#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 23. `p1-mh-13-new`

- 问：旧规下出境一般个人信息（不含敏感个人信息）到多少人要报评估，多少人以下可以签标准合同？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p2@T0；p1-cac-o13#p2@T0
- 金标要点：自上年1月1日起累计向境外提供10万人个人信息；自上年1月1日起累计向境外提供个人信息不满10万人的
- 词法前 10：1.p1-cac-o13#p1@T0 2.p1-cac-o13#p7@T0 3.p1-cac-o13#p3@T0 4.p1-cac-o13#p2@T0 5.p1-cac-o13#p4@T0 6.p1-cac-o13#p6@T0 7.p1-cac-o11#p2@T0 8.p1-cac-o13#p5@T0 9.p1-cac-o11#p4@T0 10.p1-cac-o11#p5@T0
- 混合前 10：1.p1-cac-o13#p1@T0 2.p1-cac-o13#p2@T0 3.p1-cac-o13#p3@T0 4.p1-cac-o13#p7@T0 5.p1-cac-o13#p5@T0 6.p1-cac-o13#p6@T0 7.p1-cac-o11#p5@T0 8.p1-cac-o11#p2@T0 9.p1-cac-o13#p4@T0 10.p1-cac-o13#p8@T0
- 重排前 10：1.p1-cac-o13#p2@T0 2.p1-cac-o13#p1@T0 3.p1-cac-o13#p7@T0 4.p1-cac-o13#p3@T0 5.p1-cac-o13#p6@T0 6.p1-cac-o11#p2@T0 7.p1-cac-o13#p4@T0 8.p1-cac-o13#p5@T0 9.p1-cac-o11#p5@T0 10.p1-cac-o13#p8@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 24. `p1-mh-14-new`

- 问：评估办法和标准合同办法分别是哪天开始施行的？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p17@T0；p1-cac-o13#p8@T0
- 金标要点：本办法自2022年9月1日起施行；本办法自2023年6月1日起施行
- 词法前 10：1.p1-cac-o11#p17@T0 2.p1-cac-o13#p8@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p5@T0 5.p1-cac-o11#p1@T0 6.p1-cac-o11#p16@T0 7.p1-cac-o13#p6@T0 8.p1-cac-o13#p7@T0 9.p1-cac-o13#p2@T0 10.p1-cac-o13#p4@T0
- 混合前 10：1.p1-cac-o11#p17@T0 2.p1-cac-o13#p8@T0 3.p1-cac-o13#p5@T0 4.p1-cac-o13#p6@T0 5.p1-colaw-capital-transition#p1@T0 6.p1-cac-o13#p1@T0 7.p1-cac-o13#p7@T0 8.s1-d0-01-analysis#p3@T0 9.p1-cac-o13#p2@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.p1-cac-o13#p7@T0 2.p1-cac-o13#p6@T0 3.p1-cac-o13#p1@T0 4.p1-cac-o13#p2@T0 5.p1-cac-o11#p1@T0 6.p1-cac-o11#p17@T0 7.p1-cac-o13#p8@T0 8.p1-cac-o13#p5@T0 9.s1-d0-01-analysis#p3@T0 10.p1-colaw-capital-transition#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 25. `s1-d0-02-q2`

- 问：原材料交付周期拉长到45天的那家公司，T1 时技术系统性能还能满足原定的业务扩展需求吗？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-02-memo#p2@T1
- 金标要点：系统需进行架构优化，否则无法支撑下一阶段业务扩张；核心模块在高负载压力下暴露出性能瓶颈，已触发两次非预期中断
- 词法前 10：1.s1-d0-02-report#p2@T1 2.s4-d0-t1-02-report#p1@T1 3.s5-d2-t1-91-digest#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-01-analysis#p1@T1 6.s1-d1-t1-91-brief#p2@T1 7.s1-d0-02-memo#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s6-d0-t1-02-memo#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 混合前 10：1.s6-d0-t1-02-memo#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s1-d0-02-memo#p2@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-02-internal#p1@T1 7.s1-d0-01-memo#p1@T1 8.s1-d0-01-analysis#p1@T1 9.s4-d0-t1-02-report#p1@T1 10.s2-d1-01-memo#p1@T1
- 重排前 10：1.s1-d0-02-report#p2@T1 2.s4-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d0-t1-02-report#p1@T1 5.s1-d0-02-memo#p2@T1 6.s4-d2-t1-04-internal#p1@T1 7.s1-d0-01-memo#p1@T1 8.s1-d0-01-analysis#p1@T1 9.s2-d1-01-memo#p1@T1 10.s6-d0-t1-02-internal#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 26. `s1-d0-03-q2`

- 问：T0 时认为有效的缓冲机制，在 T1 中是否仍具备应对能力？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-03-memo#p2@T1
- 金标要点：技术团队更新分析指出，外部环境变化已导致核心资源获取路径发生不可逆断裂，现有缓冲机制已无法覆盖新风险敞口
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d2-t1-04-summary#p2@T1 3.s5-d3-t1-05-analysis#p2@T1 4.p1-cac-o11#p8@T1 5.s1-d0-03-memo#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s4-d0-t1-02-report#p2@T1 8.s4-d2-t1-04-report#p2@T1 9.s7-d3-t1-05-memo#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s1-d0-03-memo#p2@T1 2.s2-d0-02-interview#p3@T1 3.s4-d2-t1-04-summary#p2@T1 4.s1-d0-05-warn#p2@T1 5.s4-d2-t1-04-internal#p1@T1 6.s4-d0-t1-02-report#p2@T1 7.s4-d2-t1-04-report#p2@T1 8.s5-d3-t1-05-analysis#p2@T1 9.s2-d3-01-interview#p2@T1 10.s7-d3-t1-05-claim#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p2@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d2-t1-04-report#p2@T1 4.s7-d3-t1-05-claim#p1@T1 5.s2-d0-02-interview#p3@T1 6.s4-d2-t1-04-summary#p2@T1 7.s1-d0-03-memo#p2@T1 8.s1-d0-05-warn#p2@T1 9.s4-d2-t1-04-internal#p1@T1 10.s2-d3-01-interview#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 27. `s1-d0-04-q1`

- 问：T0 时点下，核心市场渗透率是否处于稳定状态？其依据是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p1@T0
- 金标要点：近期数据显示，核心市场渗透率在连续三周维持在68%以上，表明当前战略执行路径具备初步成效；团队评估认为，该数值已进入稳定区间，可作为后续资源调配的重要依据
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s1-d0-04-memo#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s1-d0-01-memo#p1@T0 5.s7-d0-t0-01-qa#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s1-d1-01-analysis#p1@T0 8.s2-d2-01-memo#p2@T0 9.s7-d0-t0-01-report#p3@T0 10.s1-d1-01-analysis#p3@T0
- 混合前 10：1.s1-d0-04-memo#p1@T0 2.s1-d0-01-memo#p1@T0 3.s1-d0-02-memo#p1@T0 4.s1-d1-01-memo#p1@T0 5.s2-d0-03-memo#p2@T0 6.s2-d2-01-memo#p2@T0 7.s1-d1-01-analysis#p1@T0 8.s1-d2-01-memo#p1@T0 9.s1-d0-02-report#p1@T0 10.s4-d3-t0-05-memo#p1@T0
- 重排前 10：1.s1-d0-04-memo#p1@T0 2.s1-d0-01-memo#p1@T0 3.s4-d3-t0-05-memo#p1@T0 4.s1-d0-02-memo#p1@T0 5.s1-d1-01-memo#p1@T0 6.s2-d0-03-memo#p2@T0 7.s2-d2-01-memo#p2@T0 8.s1-d1-01-analysis#p1@T0 9.s1-d2-01-memo#p1@T0 10.s1-d0-02-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 28. `s1-d0-04-q2`

- 问：核心市场渗透率回落到66.2%的那家公司，T1 时供应链中哪一环节明显恶化？具体表现是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p2@T1
- 金标要点：供应链韧性测试中，尽管整体准时率仍达92%，但某关键节点延误率上升至11%，暴露出单一依赖风险
- 词法前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-03-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s2-d0-02-interview#p3@T1 5.s6-d2-g3-memo#p3@T1 6.s1-d0-01-memo#p1@T1 7.s1-d1-t1-91-memo#p2@T1 8.s7-d2-t1-04-data#p1@T1 9.s1-d1-01-memo#p1@T1 10.s1-d2-01-memo#p1@T1
- 混合前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-03-memo#p1@T1 3.s2-d0-02-interview#p3@T1 4.s1-d0-01-memo#p1@T1 5.s1-d1-01-memo#p1@T1 6.s1-d0-02-memo#p1@T1 7.s1-d2-01-memo#p1@T1 8.s1-d3-01-memo#p1@T1 9.s7-d2-t1-04-data#p1@T1 10.s1-d1-01-analysis#p2@T1
- 重排前 10：1.s1-d0-04-memo#p1@T1 2.s7-d2-t1-04-data#p1@T1 3.s1-d0-03-memo#p1@T1 4.s2-d0-02-interview#p3@T1 5.s1-d0-01-memo#p1@T1 6.s1-d1-01-memo#p1@T1 7.s1-d0-02-memo#p1@T1 8.s1-d2-01-memo#p1@T1 9.s1-d3-01-memo#p1@T1 10.s1-d1-01-analysis#p2@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 29. `s1-d0-04-q3`

- 问：渗透率回落至66.2%、三条海运通道被临时关闭的那家公司，T0 到 T1 客户满意度的描述有何关键变化？预示什么趋势？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-memo#p3@T1
- 金标要点：客户反馈调查中，尽管平均满意度维持在4.3分，但针对售后服务的负面评论数量同比增加37%，提示服务模式存在结构性短板，亟待调整
- 词法前 10：1.s1-d0-04-risk#p2@T1 2.s7-d3-t1-05-conflict#p2@T1 3.s1-d0-04-memo#p1@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s5-d1-t1-03-note#p2@T1 6.p1-colaw-governance-supervisor-js#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s1-d0-01-memo#p2@T1 9.s3-d0-02-c#p2@T1 10.s5-d3-t1-05-analysis#p3@T1
- 混合前 10：1.s1-d0-04-memo#p1@T1 2.s1-d0-04-risk#p2@T1 3.s1-d0-01-memo#p2@T1 4.s7-d3-t1-05-conflict#p2@T1 5.s2-d0-03-memo#p1@T1 6.s5-d1-t1-03-note#p2@T1 7.s1-d0-04-memo#p3@T1 8.s3-d0-02-c#p2@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s2-d2-01-report#p2@T1
- 重排前 10：1.s1-d0-04-risk#p2@T1 2.s7-d3-t1-05-conflict#p2@T1 3.s5-d1-t1-03-note#p2@T1 4.s1-d0-01-memo#p2@T1 5.s3-d0-02-c#p2@T1 6.s1-d0-04-memo#p1@T1 7.s2-d0-03-memo#p1@T1 8.s1-d0-04-memo#p3@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s2-d2-01-report#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 30. `s1-d0-04-q4`

- 问：面临三条海运通道被临时关闭的那家出口企业，T1 文档中新法案对数据处理流程有什么影响？该如何应对？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-04-risk#p3@T1
- 金标要点：新法案正式进入立法听证阶段，预计将在未来六个月内实施，现有数据跨境架构必须在四十五天内完成合规改造；否则将面临运营中断
- 词法前 10：1.s1-d0-04-risk#p2@T1 2.s1-d0-05-warn#p2@T1 3.s5-d3-t1-05-analysis#p1@T1 4.s1-d0-04-risk#p1@T1 5.s7-d0-t1-02-memo#p3@T1 6.s1-d0-04-risk#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s1-d1-01-report#p3@T1 9.s6-d2-g1-memo#p3@T1 10.s6-d1-c4-memo#p2@T1
- 混合前 10：1.s1-d0-04-risk#p2@T1 2.s1-d1-01-report#p3@T1 3.s1-d0-04-risk#p3@T1 4.s6-d1-c4-memo#p2@T1 5.p1-cac-o11#p14@T1 6.s6-d3-t1-03-memo#p3@T1 7.s6-d2-g2-memo#p2@T1 8.s7-d0-t1-02-update#p2@T1 9.s1-d0-05-memo#p3@T1 10.p1-cac-o11#p15@T1
- 重排前 10：1.s1-d0-04-risk#p2@T1 2.s7-d0-t1-02-update#p2@T1 3.s6-d1-c4-memo#p2@T1 4.s6-d2-g2-memo#p2@T1 5.s1-d1-01-report#p3@T1 6.p1-cac-o11#p14@T1 7.s6-d3-t1-03-memo#p3@T1 8.p1-cac-o11#p15@T1 9.s1-d0-04-risk#p3@T1 10.s1-d0-05-memo#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 31. `s1-d0-05-q1`

- 问：T0 时点关于目标区域基础设施状况的评估结论是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p1@T0
- 金标要点：根据当前情报，目标区域的基础设施部署已进入稳定阶段；主要通道保持畅通，未发现异常干扰迹象；该区域具备长期战略价值
- 词法前 10：1.s1-d0-05-memo#p1@T0 2.s4-d0-t0-01-analysis#p2@T0 3.s1-d0-03-memo#p1@T0 4.s7-d0-t0-01-qa#p1@T0 5.s1-d1-01-analysis#p3@T0 6.p1-cac-o11#p12@T0 7.s1-d3-01-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s2-d0-03-interview#p1@T0 10.s4-d1-t0-03-plan#p1@T0
- 混合前 10：1.s1-d0-05-memo#p1@T0 2.s1-d0-03-memo#p1@T0 3.s1-d3-01-memo#p1@T0 4.s5-d0-t0-01-summary#p3@T0 5.s2-d0-02-memo#p2@T0 6.p1-cac-o11#p12@T0 7.s1-d0-01-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d0-t0-01-analysis#p1@T0
- 重排前 10：1.s1-d0-05-memo#p1@T0 2.s1-d0-03-memo#p1@T0 3.s1-d3-01-memo#p1@T0 4.p1-cac-o11#p12@T0 5.s1-d0-01-memo#p1@T0 6.s5-d0-t0-01-summary#p3@T0 7.s2-d0-02-memo#p2@T0 8.s7-d0-t0-01-report#p3@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d0-t0-01-analysis#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 32. `s1-d0-05-q2`

- 问：T1 时点对同一区域基础设施状况的最新判断有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p1@T1
- 金标要点：最新监测显示，目标区域主要通道出现结构性损伤，部分路段存在非正常闭塞现象；需重新评估其战略可用性
- 词法前 10：1.s1-d0-05-warn#p1@T1 2.s4-d2-t1-04-report#p1@T1 3.s7-d0-t1-02-claim#p2@T1 4.s1-d0-03-memo#p1@T1 5.s1-d0-05-memo#p1@T1 6.s5-d3-t1-05-memo#p2@T1 7.s6-d3-t1-02-report#p1@T1 8.s6-d1-c4-memo#p3@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d2-t1-04-internal#p1@T1
- 混合前 10：1.s1-d0-03-memo#p1@T1 2.s7-d0-t1-02-claim#p2@T1 3.s1-d0-05-memo#p1@T1 4.s1-d3-01-memo#p1@T1 5.s1-d0-05-warn#p1@T1 6.s4-d2-t1-04-report#p1@T1 7.s6-d0-t1-01-patch#p2@T1 8.s5-d3-t1-05-memo#p3@T1 9.s6-d1-c4-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 重排前 10：1.s1-d0-03-memo#p1@T1 2.s7-d0-t1-02-claim#p2@T1 3.s1-d0-05-memo#p1@T1 4.s1-d0-05-warn#p1@T1 5.s4-d2-t1-04-report#p1@T1 6.s6-d1-c4-memo#p3@T1 7.s1-d3-01-memo#p1@T1 8.s6-d0-t1-01-patch#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 33. `s1-d0-05-q3`

- 问：T0 时点，安全团队对周边势力活动态势作出判断的依据是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-memo#p2@T0
- 金标要点：安全团队报告称，周边势力活动频率在近两周内维持低位，无明显升级信号
- 词法前 10：1.s1-d0-05-memo#p2@T0 2.s7-d0-t0-01-qa#p1@T0 3.s4-d0-t0-01-analysis#p2@T0 4.p1-colaw-governance#p3@T0 5.s2-d0-04-memo#p3@T0 6.p1-cac-o11#p15@T0 7.s4-d0-t0-01-plan#p2@T0 8.s7-d1-t0-03-fact#p3@T0 9.s5-d2-t0-04-analysis#p1@T0 10.p1-cac-o11#p16@T0
- 混合前 10：1.s1-d0-05-memo#p2@T0 2.p1-cac-o11#p7@T0 3.s4-d0-t0-01-analysis#p2@T0 4.p1-cac-o11#p16@T0 5.s7-d1-t0-03-fact#p3@T0 6.s7-d1-t0-03-reason#p3@T0 7.s7-d0-t0-01-memo#p2@T0 8.s2-d0-04-memo#p3@T0 9.s1-d3-01-report#p1@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.s1-d0-05-memo#p2@T0 2.p1-cac-o11#p7@T0 3.s7-d1-t0-03-fact#p3@T0 4.s4-d0-t0-01-analysis#p2@T0 5.p1-cac-o11#p16@T0 6.s7-d1-t0-03-reason#p3@T0 7.s7-d0-t0-01-memo#p2@T0 8.s2-d0-04-memo#p3@T0 9.p1-cac-o11#p1@T0 10.s1-d3-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 34. `s1-d0-05-q4`

- 问：T1 时点的安全预警是否基于新的技术监测数据？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d0-05-warn#p1@T1；s1-d0-05-warn#p3@T1
- 金标要点：技术监测发现，加密链路遭遇定向干扰攻击，虽未突破防护，但暴露了系统脆弱点；多源情报证实，敏感议题已转化为实际军事集结信号
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.p1-cac-o13#p4@T1 3.p1-cac-o20#p5@T1 4.s6-d3-t1-02-report#p2@T1 5.p1-cac-o11#p4@T1 6.s2-d0-02-memo#p2@T1 7.s1-d3-01-memo#p2@T1 8.s2-d3-01-memo#p3@T1 9.s4-d2-t1-04-report#p1@T1 10.s2-d0-t1-91-interview#p2@T1
- 混合前 10：1.s2-d3-01-memo#p3@T1 2.s1-d3-01-memo#p2@T1 3.s1-d0-05-warn#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-03-memo#p1@T1 6.s4-d2-t1-04-report#p3@T1 7.p1-cac-o11#p1@T1 8.p1-cac-o11#p7@T1 9.s6-d1-c2-memo#p1@T1 10.s6-d1-t1-91-release#p3@T1
- 重排前 10：1.s1-d3-01-memo#p2@T1 2.s2-d3-01-memo#p3@T1 3.s1-d0-05-warn#p3@T1 4.s4-d2-t1-04-internal#p1@T1 5.s1-d0-03-memo#p1@T1 6.p1-cac-o11#p1@T1 7.p1-cac-o11#p7@T1 8.s6-d1-c2-memo#p1@T1 9.s6-d1-t1-91-release#p3@T1 10.s4-d2-t1-04-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 35. `s1-d1-01-q1`

- 问：T0 时，核心功能平均停留4.8分钟的那款产品，目标市场渗透率达到预期阈值的多少？文档把增长归因于什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d1-01-memo#p1@T0
- 金标要点：目标市场渗透率已达到预期阈值的87%；主要得益于渠道扩张与客户反馈优化
- 词法前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-01-memo#p1@T0 4.s5-d1-t0-91-repost#p1@T0 5.s1-d0-02-memo#p1@T0 6.s2-d0-03-memo#p1@T0 7.s1-d0-04-memo#p1@T0 8.s1-d1-01-memo#p3@T0 9.s2-d2-01-memo#p1@T0 10.s1-d1-01-analysis#p3@T0
- 混合前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-02-memo#p1@T0 4.s1-d0-01-memo#p1@T0 5.s1-d0-04-memo#p1@T0 6.s1-d1-01-memo#p3@T0 7.s2-d2-01-memo#p1@T0 8.s1-d0-01-memo#p2@T0 9.s1-d2-01-memo#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 重排前 10：1.s1-d1-01-analysis#p1@T0 2.s1-d1-01-memo#p1@T0 3.s1-d0-01-memo#p1@T0 4.s1-d0-02-memo#p1@T0 5.s1-d0-04-memo#p1@T0 6.s2-d2-01-memo#p1@T0 7.s1-d1-01-memo#p3@T0 8.s1-d0-01-memo#p2@T0 9.s1-d2-01-memo#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 36. `s1-d2-01-q1`

- 问：在评级机构把短期展望调到负面观察的那份宏观研判里，T0 与 T1 对通胀走势的描述根本差异在哪？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-memo#p1@T1
- 金标要点：尽管前期数据显示通胀回落，最新数据揭示核心通胀存在反弹苗头，部分服务类项目价格再度上扬
- 词法前 10：1.s1-d2-01-analysis#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s1-d1-t1-91-memo#p2@T1 4.s5-d3-t1-05-memo#p1@T1 5.s5-d1-t1-03-memo#p3@T1 6.s2-d0-t1-91-memo#p1@T1 7.s4-d0-t1-02-report#p2@T1 8.s5-d2-t1-91-digest#p3@T1 9.s6-d2-g3-memo#p3@T1 10.s6-d3-t1-02-report#p1@T1
- 混合前 10：1.s1-d2-01-analysis#p3@T1 2.s1-d2-01-memo#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s1-d0-04-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s5-d1-t1-03-summary#p3@T1 7.s7-d3-t1-05-claim#p2@T1 8.s7-d2-t1-04-memo#p3@T1 9.s1-d0-04-risk#p1@T1 10.s5-d3-t1-05-analysis#p3@T1
- 重排前 10：1.s1-d2-01-analysis#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s5-d1-t1-03-memo#p3@T1 4.s5-d1-t1-03-summary#p3@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s1-d0-04-memo#p3@T1 7.s7-d3-t1-05-claim#p2@T1 8.s7-d2-t1-04-memo#p3@T1 9.s1-d2-01-memo#p1@T1 10.s1-d0-04-risk#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 37. `s1-d2-01-q2`

- 问：对比 T0 和 T1 的报告，企业资本开支的乐观预期是否依然成立？请说明依据。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-memo#p2@T1
- 金标要点：企业资本开支虽有小幅回升，但实际投资增速仍低于预期，尤其在高端制造领域出现观望情绪；信心修复不均衡
- 词法前 10：1.s1-d2-01-memo#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p2@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d3-t1-03-memo#p2@T1 6.s7-d2-t1-04-memo#p3@T1 7.s4-d0-t1-02-guide#p3@T1 8.p1-colaw-liquidation#p1@T1 9.p1-colaw-liquidation#p2@T1 10.s6-d2-g1-memo#p2@T1
- 混合前 10：1.s1-d2-01-memo#p2@T1 2.s4-d0-t1-02-review#p1@T1 3.s6-d2-g1-memo#p2@T1 4.s4-d2-t1-04-internal#p1@T1 5.p1-colaw-capital-call#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s5-d3-t1-05-memo#p3@T1 8.s4-d0-t1-02-analysis#p1@T1 9.s5-d3-t1-05-analysis#p1@T1 10.s6-d2-g2-memo#p2@T1
- 重排前 10：1.s1-d2-01-memo#p2@T1 2.s6-d2-g1-memo#p2@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s5-d3-t1-05-memo#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s6-d2-g2-memo#p2@T1 7.s4-d0-t1-02-review#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.p1-colaw-capital-call#p1@T1 10.s5-d3-t1-05-analysis#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 38. `s1-d2-01-q3`

- 问：T1 文档中提到的跨境支付系统部署延迟，其主要原因是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-report#p3@T1
- 金标要点：跨境支付系统测试中发现兼容性瓶颈，部署时间或延后至下一财年，影响预期效率提升
- 词法前 10：1.s1-d2-01-report#p3@T1 2.p1-cac-o16#p4@T1 3.s7-d2-t1-04-brief#p2@T1 4.s2-d1-01-memo#p1@T1 5.s7-d0-t1-02-report#p1@T1 6.s4-d2-t1-04-internal#p1@T1 7.s7-d0-t1-02-brief#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s7-d0-t1-02-report#p3@T1 10.s7-d0-t1-02-memo#p2@T1
- 混合前 10：1.s1-d2-01-report#p3@T1 2.s7-d0-t1-02-report#p1@T1 3.s7-d2-t1-04-brief#p2@T1 4.s2-d1-01-memo#p1@T1 5.s1-d3-01-memo#p2@T1 6.s7-d0-t1-02-memo#p2@T1 7.s2-d3-01-memo#p3@T1 8.s6-d1-c4-memo#p2@T1 9.s1-d1-01-memo#p2@T1 10.s1-d0-01-memo#p2@T1
- 重排前 10：1.s1-d2-01-report#p3@T1 2.s7-d2-t1-04-brief#p2@T1 3.s7-d0-t1-02-memo#p2@T1 4.s7-d0-t1-02-report#p1@T1 5.s2-d1-01-memo#p1@T1 6.s1-d3-01-memo#p2@T1 7.s6-d1-c4-memo#p2@T1 8.s1-d0-01-memo#p2@T1 9.s2-d3-01-memo#p3@T1 10.s1-d1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 39. `s1-d2-01-q6`

- 问：T1 时，评级机构对主权信用展望作了什么调整？核心通胀和区域消费又各出现了什么信号？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d2-01-analysis#p3@T1；s1-d2-01-memo#p1@T1；s1-d2-01-report#p1@T1
- 金标要点：整体需求动能不足；国际评级机构下调短期展望至负面观察；最新数据揭示核心通胀存在反弹苗头；区域消费指数增长势头减弱
- 词法前 10：1.s1-d0-04-risk#p1@T1 2.s1-d2-01-analysis#p3@T1 3.s1-d2-01-memo#p1@T1 4.s4-d0-t1-02-memo#p2@T1 5.s1-d0-05-warn#p1@T1 6.s1-d3-01-memo#p1@T1 7.s4-d2-t1-04-summary#p1@T1 8.s1-d2-01-report#p1@T1 9.s5-d1-t1-03-memo#p1@T1 10.s5-d3-t1-05-memo#p1@T1
- 混合前 10：1.s1-d0-04-risk#p1@T1 2.s1-d2-01-analysis#p3@T1 3.s1-d2-01-memo#p1@T1 4.s5-d1-t1-03-memo#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s1-d2-01-report#p1@T1 7.s1-d0-05-warn#p1@T1 8.s7-d2-t1-04-memo#p3@T1 9.s2-d0-02-interview#p3@T1 10.s1-d3-01-report#p1@T1
- 重排前 10：1.s1-d0-04-risk#p1@T1 2.s4-d0-t1-02-memo#p2@T1 3.s1-d2-01-analysis#p3@T1 4.s5-d1-t1-03-memo#p1@T1 5.s1-d0-05-warn#p1@T1 6.s7-d2-t1-04-memo#p3@T1 7.s1-d2-01-memo#p1@T1 8.s1-d2-01-report#p1@T1 9.s2-d0-02-interview#p3@T1 10.s1-d3-01-report#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 40. `s1-d3-01-q4`

- 问：物流周期普遍延长超过48小时的那个区域，T1 报告里通信网络与多边合作的变化如何影响整体战略态势？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s1-d3-01-report#p2@T1；s1-d3-01-report#p3@T1
- 金标要点：主干通信网络在近三日内遭遇三次区域性中断，峰值负载达92%，冗余链路已被迫启用；公开声明中出现立场分化，合作意愿显著减弱，存在集体脱钩趋势；多边协调机制出现明显裂痕
- 词法前 10：1.s1-d3-01-memo#p1@T1 2.s2-d1-01-memo#p1@T1 3.s1-d0-03-report#p2@T1 4.s5-d0-t1-02-memo#p1@T1 5.s6-d0-t1-01-memo#p1@T1 6.s1-d0-02-report#p2@T1 7.s5-d0-t1-02-memo#p2@T1 8.s1-d0-04-risk#p2@T1 9.s1-d3-01-report#p2@T1 10.s6-d0-t1-02-internal#p1@T1
- 混合前 10：1.s1-d3-01-memo#p1@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-04-risk#p2@T1 4.s5-d0-t1-02-memo#p1@T1 5.s2-d1-01-memo#p1@T1 6.s1-d3-01-report#p2@T1 7.s6-d0-t1-02-internal#p1@T1 8.s2-d0-02-report#p3@T1 9.s1-d0-05-memo#p1@T1 10.s1-d2-01-report#p1@T1
- 重排前 10：1.s1-d3-01-memo#p1@T1 2.s2-d1-01-memo#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s1-d0-03-report#p2@T1 5.s6-d0-t1-02-internal#p1@T1 6.s1-d0-05-memo#p1@T1 7.s1-d0-04-risk#p2@T1 8.s1-d3-01-report#p2@T1 9.s2-d0-02-report#p3@T1 10.s1-d2-01-report#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 41. `s2-d0-01-q1`

- 问：渠道成本已占总成本34%的那家公司，T0 时线下门店的营收占比大约多少？线上流量转化率又是多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-memo#p1@T0
- 金标要点：线下门店占比不足15%；线上流量转化率稳定在6.8%
- 词法前 10：1.s2-d0-01-memo#p3@T0 2.s2-d0-01-memo#p1@T0 3.s2-d1-01-memo#p3@T0 4.s2-d0-01-report#p1@T0 5.p2-gdp-national#p2@T0 6.s1-d1-01-analysis#p3@T0 7.s2-d0-03-memo#p1@T0 8.s2-d0-02-report#p1@T0 9.s4-d0-t0-01-plan#p2@T0 10.s2-d3-01-memo#p1@T0
- 混合前 10：1.s2-d0-01-memo#p3@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-02-report#p1@T0 4.s2-d1-01-memo#p3@T0 5.s2-d0-01-report#p1@T0 6.s2-d0-03-memo#p1@T0 7.s2-d1-01-memo#p2@T0 8.s2-d0-02-memo#p1@T0 9.s3-d3-01-report#p1@T0 10.s2-d3-01-memo#p1@T0
- 重排前 10：1.s2-d0-01-memo#p1@T0 2.s2-d0-01-memo#p3@T0 3.s2-d0-03-memo#p1@T0 4.s2-d1-01-memo#p3@T0 5.s2-d0-01-report#p1@T0 6.s2-d1-01-memo#p2@T0 7.s2-d0-02-memo#p1@T0 8.s2-d3-01-memo#p1@T0 9.s2-d0-02-report#p1@T0 10.s3-d3-01-report#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 42. `s2-d0-01-q2`

- 问：T1 时渠道成本占总成本的比例发生了什么变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-memo#p3@T1
- 金标要点：渠道成本压力持续加剧，目前占总成本达41%，其中平台佣金上涨22%；新方案拟通过自建私域流量降低对外部平台依赖
- 词法前 10：1.s2-d0-01-memo#p3@T1 2.p1-cac-o11#p10@T1 3.s4-d2-t1-04-internal#p1@T1 4.s1-d0-03-memo#p2@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s2-d0-01-memo#p1@T1 7.s5-d3-t1-05-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s2-d3-01-memo#p1@T1 10.p2-gdp-national#p2@T1
- 混合前 10：1.s2-d0-01-memo#p3@T1 2.s2-d0-01-memo#p1@T1 3.s3-d3-01-report#p2@T1 4.s2-d0-02-report#p1@T1 5.s4-d2-t1-04-report#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s6-d3-t1-03-memo#p3@T1 8.s3-d1-t1-91-quote#p1@T1 9.s3-d2-t1-91-contract#p2@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s2-d0-01-memo#p3@T1 2.s2-d0-01-memo#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d3-01-memo#p1@T1 6.s3-d3-01-report#p2@T1 7.s2-d0-02-report#p1@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-contract#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 43. `s2-d0-01-q4`

- 问：T1 时渠道信息同步机制升级后，投诉量和关键节点更新延迟分别有什么变化？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-01-report#p3@T1
- 金标要点：投诉量下降至周均43起；关键节点更新延迟已减少80%
- 词法前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-05-warn#p2@T1 4.s1-d0-03-memo#p1@T1 5.s4-d2-t1-04-internal#p1@T1 6.s1-d0-03-memo#p2@T1 7.p1-cac-o20#p7@T1 8.s5-d1-t1-03-report#p3@T1 9.s6-d3-t1-02-memo#p1@T1 10.s6-d3-t1-03-memo#p3@T1
- 混合前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s6-d3-t1-03-memo#p3@T1 4.s2-d1-01-memo#p1@T1 5.s6-d3-t1-03-report#p2@T1 6.s2-d1-01-memo#p2@T1 7.s1-d0-01-memo#p2@T1 8.s1-d0-05-warn#p2@T1 9.s6-d0-t1-01-channel#p2@T1 10.s6-d0-t1-02-report#p1@T1
- 重排前 10：1.s2-d0-01-report#p3@T1 2.s1-d0-03-report#p2@T1 3.s1-d0-05-warn#p2@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d1-01-memo#p1@T1 6.s6-d3-t1-03-report#p2@T1 7.s2-d1-01-memo#p2@T1 8.s1-d0-01-memo#p2@T1 9.s6-d0-t1-01-channel#p2@T1 10.s6-d0-t1-02-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 44. `s2-d0-02-q1`

- 问：根据T0文档，新客户获取成本上升的主要原因是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-memo#p1@T0
- 金标要点：近期渠道反馈显示，新客户获取成本在上季度上升了18%，主要源于线上广告投放效率下降；团队初步判断是算法推荐系统未及时适配用户行为变化
- 词法前 10：1.s2-d0-02-memo#p1@T0 2.s3-d0-03-report#p1@T0 3.s4-d0-t0-01-analysis#p1@T0 4.s4-d0-t0-01-plan#p2@T0 5.s4-d0-t0-01-analysis#p2@T0 6.s2-d0-04-memo#p1@T0 7.s3-d0-01-memo#p3@T0 8.s3-d2-01-competitor-pricing#p1@T0 9.s2-d0-03-memo#p1@T0 10.s7-d0-t0-01-qa#p1@T0
- 混合前 10：1.s2-d0-02-memo#p1@T0 2.s3-d0-03-report#p1@T0 3.s2-d0-03-memo#p1@T0 4.s4-d0-t0-01-analysis#p1@T0 5.s3-d3-01-report#p1@T0 6.s3-d0-01-memo#p3@T0 7.s3-d1-01-report#p3@T0 8.s3-d0-02-b#p1@T0 9.s4-d0-t0-01-analysis#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s2-d0-02-memo#p1@T0 2.s2-d0-03-memo#p1@T0 3.s4-d0-t0-01-analysis#p1@T0 4.s3-d0-03-report#p1@T0 5.s3-d3-01-report#p1@T0 6.s3-d0-01-memo#p3@T0 7.s3-d1-01-report#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s3-d0-02-b#p1@T0 10.s4-d3-t0-05-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 45. `s2-d0-02-q2`

- 问：T1版本中关于新客户获取成本的解释有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-memo#p1@T1
- 金标要点：最新数据分析表明，新客户获取成本上升主因并非算法问题，而是外部市场环境波动导致流量质量整体下滑；原有投放模型仍具有效性
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s1-d0-03-memo#p2@T1 3.s2-d0-02-memo#p1@T1 4.s1-d1-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s1-d0-01-memo#p2@T1 7.s4-d0-t1-02-report#p1@T1 8.s4-d0-t1-02-memo#p1@T1 9.s4-d2-t1-04-internal#p1@T1 10.s7-d3-t1-05-conflict#p2@T1
- 混合前 10：1.s2-d0-02-memo#p1@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s2-d0-03-memo#p1@T1 4.s4-d0-t1-02-review#p2@T1 5.s1-d1-01-memo#p3@T1 6.s4-d2-t1-04-memo#p1@T1 7.s4-d0-t1-02-memo#p1@T1 8.s3-d2-01-competitor-pricing#p2@T1 9.s2-d3-01-memo#p1@T1 10.s4-d0-t1-02-report#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-review#p2@T1 4.s1-d1-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s2-d0-02-memo#p1@T1 8.s2-d0-03-memo#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s2-d3-01-memo#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 46. `s2-d0-02-q3`

- 问：T0报告中提到的电商平台旗舰店贡献占比是多少？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-report#p1@T0
- 金标要点：本月渠道销售总额环比增长9.4%，主要驱动来自新上线的电商平台旗舰店，其首月贡献占比达23%
- 词法前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-01-memo#p3@T0 4.s5-d2-t0-04-analysis#p2@T0 5.s4-d0-t0-01-plan#p2@T0 6.s1-d1-01-analysis#p3@T0 7.p2-gdp-national#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s5-d2-t0-04-analysis#p3@T0 10.s2-d3-01-interview#p2@T0
- 混合前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s2-d0-01-memo#p3@T0 4.s2-d3-01-memo#p2@T0 5.s5-d2-t0-04-analysis#p1@T0 6.s2-d1-01-report#p1@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s2-d1-01-memo#p1@T0 9.s2-d0-01-report#p1@T0 10.s2-d3-01-interview#p2@T0
- 重排前 10：1.s2-d0-02-report#p1@T0 2.s2-d0-01-memo#p1@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s2-d0-01-memo#p3@T0 5.s5-d2-t0-04-analysis#p1@T0 6.s2-d1-01-memo#p1@T0 7.s2-d1-01-report#p1@T0 8.s2-d3-01-memo#p2@T0 9.s2-d0-01-report#p1@T0 10.s2-d3-01-interview#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 47. `s2-d0-02-q4`

- 问：T1报告修正后的销售总额变化趋势是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-report#p1@T1
- 金标要点：本月渠道销售总额实际为环比下降3.1%，此前公布的9.4%增长数据系系统误报，现已修正
- 词法前 10：1.s2-d0-02-report#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s4-d2-t1-91-model-v3#p2@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s7-d2-t1-04-claim#p3@T1 6.s5-d0-t1-02-report#p2@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s5-d0-t1-02-analysis#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 混合前 10：1.s2-d0-02-report#p1@T1 2.s3-d0-01-report#p3@T1 3.p2-gdp-national#p1@T1 4.s4-d0-t1-02-plan#p1@T1 5.s5-d1-t1-03-memo#p1@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s3-d0-01-report#p2@T1 8.s1-d0-02-report#p3@T1 9.s2-d0-01-report#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 重排前 10：1.s2-d0-02-report#p1@T1 2.p2-gdp-national#p1@T1 3.s4-d2-t1-91-model-v3#p2@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-plan#p1@T1 6.s5-d1-t1-03-memo#p1@T1 7.s3-d0-01-report#p2@T1 8.s2-d0-01-report#p3@T1 9.s6-d0-t1-03-internal#p1@T1 10.s1-d0-02-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 48. `s2-d0-02-q5`

- 问：高管访谈中关于海外扩张的初始态度如何？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-02-interview#p2@T0
- 金标要点：关于海外扩张，目前暂无明确计划，重点仍将聚焦于国内市场的深度渗透与服务优化
- 词法前 10：1.s2-d0-02-interview#p2@T0 2.p1-colaw-governance-board#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d0-t0-01-report#p2@T0 5.s2-d0-03-interview#p1@T0 6.s2-d3-01-interview#p1@T0 7.s2-d1-01-memo#p1@T0 8.s1-d0-05-warn#p2@T0 9.s1-d1-01-report#p3@T0 10.s1-d1-01-memo#p1@T0
- 混合前 10：1.s2-d0-02-interview#p2@T0 2.s2-d0-03-interview#p1@T0 3.s1-d0-05-warn#p2@T0 4.s2-d1-01-memo#p3@T0 5.s2-d3-01-interview#p1@T0 6.s1-d1-01-report#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s2-d1-01-memo#p1@T0 9.s2-d0-02-interview#p3@T0 10.p1-cac-o11#p1@T0
- 重排前 10：1.s2-d0-02-interview#p2@T0 2.s2-d3-01-interview#p1@T0 3.s7-d1-t0-03-claim#p1@T0 4.s2-d1-01-memo#p1@T0 5.s2-d0-03-interview#p1@T0 6.s2-d1-01-memo#p3@T0 7.s2-d0-02-interview#p3@T0 8.p1-cac-o11#p1@T0 9.s1-d0-05-warn#p2@T0 10.s1-d1-01-report#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 49. `s2-d0-04-q1`

- 问：T1时点下，该产品线在华东地区的实际销售表现与最初预期有何差异？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-04-memo#p1@T1
- 金标要点：华东地区经销商反映实际订单量低于预期，导致部分门店出现滞销风险；最新渠道反馈显示，尽管初期销售表现强劲，但部分区域出现库存积压问题；实际增幅仅为5%
- 词法前 10：1.s2-d0-04-memo#p1@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s1-d1-01-report#p1@T1 4.s6-d0-t1-02-report#p2@T1 5.s2-d0-03-memo#p2@T1 6.s4-d0-t1-02-report#p2@T1 7.s1-d3-01-memo#p3@T1 8.s2-d2-01-report#p1@T1 9.s2-d1-01-memo#p2@T1 10.s5-d1-t1-03-memo#p2@T1
- 混合前 10：1.s2-d0-04-memo#p1@T1 2.s1-d1-01-report#p1@T1 3.s2-d0-03-memo#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s2-d0-01-report#p1@T1 7.s2-d1-01-report#p3@T1 8.s2-d0-02-report#p2@T1 9.s2-d0-02-memo#p2@T1 10.s5-d1-t1-03-memo#p3@T1
- 重排前 10：1.s2-d0-04-memo#p1@T1 2.s6-d0-t1-02-report#p2@T1 3.s1-d1-01-report#p1@T1 4.s2-d0-03-memo#p2@T1 5.s5-d1-t1-03-memo#p3@T1 6.s2-d1-01-report#p3@T1 7.s6-d0-t1-02-memo#p2@T1 8.s2-d0-01-report#p1@T1 9.s2-d0-02-memo#p2@T1 10.s2-d0-02-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 50. `s2-d0-04-q2`

- 问：暂停了30万台出货计划的那条产品线，从 T0 到 T1 推广策略有哪些关键调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d0-04-memo#p3@T1
- 金标要点：原定第三季度的全国推广活动已被推迟至第四季度，重点转向解决现有渠道库存与售后问题；强化经销商支持体系
- 词法前 10：1.s2-d0-04-memo#p2@T1 2.s2-d0-03-memo#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-report#p2@T1 6.s2-d2-01-report#p1@T1 7.s5-d2-t1-91-digest#p3@T1 8.s4-d2-t1-04-internal#p1@T1 9.s6-d1-c2-memo#p3@T1 10.s6-d3-t1-03-report#p3@T1
- 混合前 10：1.s2-d0-04-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s2-d0-03-memo#p2@T1 4.s2-d3-01-memo#p2@T1 5.s6-d3-t1-03-report#p3@T1 6.s1-d1-01-report#p1@T1 7.s3-d3-01-report#p2@T1 8.s1-d0-02-report#p2@T1 9.s3-d3-01-memo#p3@T1 10.s2-d0-04-memo#p3@T1
- 重排前 10：1.s2-d0-04-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s2-d0-03-memo#p2@T1 4.s2-d3-01-memo#p2@T1 5.s3-d3-01-report#p2@T1 6.s6-d3-t1-03-report#p3@T1 7.s1-d1-01-report#p1@T1 8.s1-d0-02-report#p2@T1 9.s3-d3-01-memo#p3@T1 10.s2-d0-04-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 51. `s2-d1-01-q1`

- 问：T0 与 T1 版本中关于渠道合作进展的描述有何差异？请指出具体事实变更。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d1-01-memo#p1@T1
- 金标要点：经重新评估，原定新增15家核心分销商的计划已调整为仅拓展6家，主要因部分平台准入；库存同步机制虽已部署，但实际响应延迟仍常超过 6 小时；部分平台准入门槛提高及结算周期延长
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s6-d3-t1-03-report#p2@T1 3.s7-d0-t1-02-claim#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s4-d0-t1-02-review#p1@T1 6.s2-d3-01-memo#p2@T1 7.s4-d0-t1-02-report#p2@T1 8.s4-d0-t1-02-guide#p3@T1 9.s6-d0-t1-01-channel#p3@T1 10.s6-d3-t1-03-memo#p3@T1
- 混合前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d3-t1-03-memo#p3@T1 4.s2-d3-01-memo#p2@T1 5.s2-d2-01-memo#p1@T1 6.s6-d0-t1-02-report#p1@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s2-d0-01-report#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s6-d0-t1-01-channel#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s6-d3-t1-03-memo#p2@T1 3.s6-d3-t1-03-report#p2@T1 4.s6-d3-t1-03-memo#p3@T1 5.s2-d3-01-memo#p2@T1 6.s2-d2-01-memo#p1@T1 7.s6-d0-t1-01-channel#p1@T1 8.s6-d0-t1-02-report#p1@T1 9.s2-d0-01-report#p3@T1 10.s7-d0-t1-02-brief#p3@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 52. `s2-d1-01-q3`

- 问：短视频互动率掉到18%的那家品牌，T0 与 T1 对线下门店扩张的态度有何变化？反映了怎样的战略调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d1-01-memo#p3@T1
- 金标要点：目前优先考虑现有门店的数字化改造，以提升运营效率而非扩大规模；原计划新开 8 家直营店的方案已被暂缓
- 词法前 10：1.s2-d1-01-report#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s2-d0-01-memo#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s2-d0-01-memo#p2@T1 7.s6-d2-g3-memo#p3@T1 8.s5-d2-t1-91-digest#p3@T1 9.s1-d0-02-memo#p3@T1 10.s2-d1-01-report#p1@T1
- 混合前 10：1.s2-d1-01-report#p2@T1 2.s2-d0-01-memo#p1@T1 3.s3-d0-01-report#p3@T1 4.s2-d3-01-memo#p2@T1 5.s2-d1-01-memo#p3@T1 6.s2-d0-t1-91-interview#p3@T1 7.s2-d3-01-memo#p1@T1 8.s3-d0-01-memo#p3@T1 9.s2-d0-01-memo#p2@T1 10.s2-d1-01-report#p1@T1
- 重排前 10：1.s2-d1-01-report#p2@T1 2.s2-d1-01-report#p1@T1 3.s2-d0-01-memo#p1@T1 4.s3-d0-01-report#p3@T1 5.s2-d3-01-memo#p2@T1 6.s2-d0-t1-91-interview#p3@T1 7.s2-d3-01-memo#p1@T1 8.s2-d0-01-memo#p2@T1 9.s2-d1-01-memo#p3@T1 10.s3-d0-01-memo#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 53. `s2-d2-01-q1`

- 问：T0与T1版本中关于新版本界面的评价有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d2-01-memo#p1@T1
- 金标要点：最新一轮渠道评估表明，新版本界面虽在初期获得好评，但用户实际使用中出现导航路径不清晰的问题；已启动UI重设计
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s2-d2-01-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-guide#p3@T1 6.s4-d2-t1-04-memo#p1@T1 7.s4-d0-t1-02-plan#p3@T1 8.s6-d0-t1-01-channel#p3@T1 9.s1-d1-01-memo#p3@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s2-d2-01-memo#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s1-d1-01-memo#p3@T1 5.s4-d0-t1-02-guide#p3@T1 6.s6-d0-t1-01-channel#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s4-d2-t1-04-memo#p1@T1 9.s4-d0-t1-02-memo#p1@T1 10.s4-d0-t1-02-report#p2@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s2-d2-01-memo#p1@T1 3.s4-d0-t1-02-review#p1@T1 4.s7-d0-t1-02-claim#p3@T1 5.s4-d0-t1-02-memo#p1@T1 6.s4-d0-t1-02-report#p2@T1 7.s1-d1-01-memo#p3@T1 8.s4-d0-t1-02-guide#p3@T1 9.s6-d0-t1-01-channel#p3@T1 10.s4-d2-t1-04-memo#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 54. `s2-d2-01-q2`

- 问：客服平均响应缩短到1.5小时的那家公司，T0 与 T1 关于定价策略的建议是否一致？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d2-01-memo#p2@T1
- 金标要点：经重新核算成本与利润模型，原定阶梯折扣方案被调整为捆绑促销策略，以增强整体收益而非单纯降低售价；该方案已在试点区域上线
- 词法前 10：1.s2-d2-01-report#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s2-d0-t1-91-memo#p2@T1 4.s2-d0-t1-91-interview#p2@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.p1-cac-o20#p8@T1 7.s1-d1-t1-91-brief#p2@T1 8.s1-d1-t1-91-memo#p2@T1 9.s3-d0-03-report#p3@T1 10.s3-d1-01-report#p2@T1
- 混合前 10：1.s2-d2-01-report#p2@T1 2.s4-d2-t1-04-internal#p1@T1 3.s3-d0-01-report#p3@T1 4.s1-d0-01-memo#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s3-d0-03-report#p3@T1 8.s3-d1-01-report#p2@T1 9.s3-d2-01-quotation-snapshot#p2@T1 10.s2-d0-02-report#p3@T1
- 重排前 10：1.s2-d2-01-report#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s2-d0-t1-91-memo#p2@T1 4.s3-d2-01-quotation-snapshot#p2@T1 5.s4-d2-t1-04-internal#p1@T1 6.s3-d0-01-report#p3@T1 7.s1-d0-01-memo#p2@T1 8.s3-d0-03-report#p3@T1 9.s3-d1-01-report#p2@T1 10.s2-d0-02-report#p3@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 55. `s2-d3-01-q1`

- 问：T0 与 T1 版本中关于渠道合作目标的变化是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-memo#p1@T1
- 金标要点：经重新评估，原定 15% 的用户增长目标已调整为 8%，主要因市场环境变化及渠道反馈实际转化率低于预期；后续策略将更注重质量而非数量
- 词法前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s4-d0-t1-02-review#p1@T1 3.s2-d3-01-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s2-d3-01-memo#p2@T1 6.s4-d0-t1-02-guide#p3@T1 7.s6-d3-t1-03-report#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.p1-cac-o20#p8@T1 10.s5-d1-t1-03-note#p2@T1
- 混合前 10：1.s2-d3-01-memo#p2@T1 2.s2-d3-01-interview#p1@T1 3.s2-d2-01-memo#p1@T1 4.s6-d3-t1-03-report#p2@T1 5.s6-d0-t1-01-channel#p1@T1 6.s1-d0-02-memo#p1@T1 7.s2-d0-01-memo#p1@T1 8.s4-d0-t1-02-plan#p3@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p1@T1 2.s2-d3-01-memo#p2@T1 3.s2-d2-01-memo#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s2-d3-01-memo#p1@T1 6.s2-d3-01-interview#p1@T1 7.s6-d3-t1-03-report#p2@T1 8.s1-d0-02-memo#p1@T1 9.s2-d0-01-memo#p1@T1 10.s4-d0-t1-02-plan#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 56. `s2-d3-01-q2`

- 问：T1 版本中为何原定的合作渠道数量减少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-memo#p2@T1
- 金标要点：原计划中的两家核心渠道中，仅电商平台明确继续推进，垂直类应用因战略调整已退出合作；目前合作方数量缩减至单一
- 词法前 10：1.s2-d3-01-memo#p2@T1 2.s2-d3-01-memo#p1@T1 3.s6-d3-t1-03-report#p2@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s2-d0-01-report#p3@T1 6.s2-d3-01-interview#p2@T1 7.s2-d0-04-memo#p3@T1 8.s4-d0-t1-02-guide#p3@T1 9.p1-colaw-liquidation#p5@T1 10.s2-d2-01-memo#p1@T1
- 混合前 10：1.s2-d3-01-memo#p2@T1 2.s2-d0-01-report#p3@T1 3.s6-d3-t1-03-report#p2@T1 4.s2-d0-04-memo#p3@T1 5.s2-d3-01-interview#p2@T1 6.s4-d2-t1-04-report#p2@T1 7.s2-d2-01-memo#p1@T1 8.s2-d0-02-report#p1@T1 9.s1-d3-01-report#p3@T1 10.s2-d0-01-memo#p1@T1
- 重排前 10：1.s2-d3-01-memo#p2@T1 2.s2-d2-01-memo#p1@T1 3.s2-d0-01-report#p3@T1 4.s6-d3-t1-03-report#p2@T1 5.s2-d0-04-memo#p3@T1 6.s2-d3-01-interview#p2@T1 7.s4-d2-t1-04-report#p2@T1 8.s2-d0-02-report#p1@T1 9.s1-d3-01-report#p3@T1 10.s2-d0-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 57. `s2-d3-01-q4`

- 问：高管在两次访谈中对渠道拓展策略的表述有何根本性转变？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s2-d3-01-interview#p1@T1
- 金标要点：CEO 改口称，由于外部竞争加剧，公司战略将转向“精耕细作”，新渠道拓展目标下调至覆盖 25% 的关键市场；不再追求广泛铺开
- 词法前 10：1.s2-d3-01-interview#p1@T1 2.s6-d3-t1-01-note#p2@T1 3.s7-d3-t1-05-synthetic#p3@T1 4.s2-d0-t1-91-interview#p1@T1 5.s7-d3-t1-05-synthetic#p1@T1 6.s2-d3-01-memo#p1@T1 7.s7-d2-t1-04-brief#p2@T1 8.s2-d3-t1-91-interview#p2@T1 9.s2-d0-t1-91-interview#p3@T1 10.s2-d3-01-interview#p2@T1
- 混合前 10：1.s2-d3-01-interview#p1@T1 2.s2-d3-01-memo#p1@T1 3.s5-d3-t1-05-analysis#p3@T1 4.s1-d0-02-memo#p1@T1 5.s2-d0-03-interview#p1@T1 6.s6-d0-t1-01-channel#p1@T1 7.s2-d3-01-memo#p2@T1 8.s2-d0-01-memo#p1@T1 9.s2-d0-t1-91-interview#p3@T1 10.s5-d1-t1-03-memo#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s5-d1-t1-03-memo#p1@T1 3.s2-d3-01-interview#p1@T1 4.s2-d3-01-memo#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s2-d3-01-memo#p2@T1 7.s2-d0-t1-91-interview#p3@T1 8.s1-d0-02-memo#p1@T1 9.s2-d0-01-memo#p1@T1 10.s2-d0-03-interview#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 58. `s3-d0-01-q2`

- 问：竞品B在T1阶段新增了哪些服务功能？其价格如何调整？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-01-memo#p2@T1
- 金标要点：竞品B在高端套餐基础上新增家庭共享功能，价格上调至每月219元，尽管涨幅明显，但用户留存率仍维持在92%以上
- 词法前 10：1.s3-d0-01-memo#p2@T1 2.s3-d1-01-report#p2@T1 3.s3-d1-01-memo#p2@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s3-d0-01-report#p3@T1 6.s3-d0-02-a#p2@T1 7.s3-d0-04-memo#p1@T1 8.s3-d0-03-memo#p2@T1 9.s3-d0-01-report#p2@T1 10.s3-d3-01-report#p2@T1
- 混合前 10：1.s3-d0-04-memo#p1@T1 2.s3-d1-01-report#p2@T1 3.s3-d0-01-memo#p2@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-03-memo#p2@T1 6.s3-d0-03-memo#p1@T1 7.s3-d1-01-memo#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p2@T1 10.s3-d2-01-competitor-pricing#p2@T1
- 重排前 10：1.s3-d0-01-memo#p2@T1 2.s3-d1-01-memo#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d0-04-memo#p1@T1 5.s3-d1-01-report#p2@T1 6.s3-d3-01-report#p2@T1 7.s3-d0-03-memo#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p2@T1 10.s3-d0-03-memo#p1@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 59. `s3-d0-01-q3`

- 问：在流量通话套餐比价里（竞品B新增家庭共享的那份），竞品C 在 T0 与 T1 之间调整了促销策略吗？具体变化是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-01-memo#p3@T1
- 金标要点：竞品C已于本季度初结束促销活动，标准套餐恢复至每月99元，且推出捆绑视频会员的新组合方案
- 词法前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-01-memo#p1@T1 5.s5-d2-t1-91-digest#p3@T1 6.s7-d0-t1-02-analysis#p3@T1 7.s3-d0-03-memo#p2@T1 8.s3-d3-01-report#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d3-01-memo#p3@T1
- 混合前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-memo#p1@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d0-04-memo#p2@T1 6.s3-d0-03-memo#p2@T1 7.s3-d3-01-memo#p3@T1 8.s3-d3-01-report#p2@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p2@T1
- 重排前 10：1.s3-d0-01-memo#p2@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-01-memo#p1@T1 6.s3-d0-04-memo#p2@T1 7.s3-d0-03-memo#p2@T1 8.s3-d3-01-memo#p3@T1 9.s3-d1-01-report#p2@T1 10.s3-d3-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 60. `s3-d0-02-q1`

- 问：在A、B、C三家公司的基础版比价中，T0 时A公司的基础版定价是多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p1@T0；s3-d0-02-b#p1@T0；s3-d0-02-c#p1@T0
- 金标要点：A公司推出基础版服务，定价为每月99元，包含核心功能模块，支持5个用户席位；基础款月费99元；A公司以99元定位形成价格优势
- 词法前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-b#p3@T0 3.s3-d0-04-memo#p3@T0 4.s3-d1-01-memo#p2@T0 5.s3-d0-03-memo#p1@T0 6.s3-d0-04-memo#p1@T0 7.s3-d0-02-b#p1@T0 8.s3-d0-01-report#p1@T0 9.s3-d0-03-report#p1@T0 10.s3-d3-01-memo#p1@T0
- 混合前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-04-memo#p3@T0 3.s3-d1-01-memo#p2@T0 4.s3-d0-03-memo#p1@T0 5.s3-d0-04-memo#p1@T0 6.s3-d0-02-c#p1@T0 7.s3-d3-01-memo#p1@T0 8.s3-d0-01-report#p1@T0 9.s3-d0-01-memo#p1@T0 10.s3-d0-03-report#p1@T0
- 重排前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-04-memo#p1@T0 4.s3-d3-01-memo#p1@T0 5.s3-d0-01-report#p1@T0 6.s3-d0-04-memo#p3@T0 7.s3-d1-01-memo#p2@T0 8.s3-d0-01-memo#p1@T0 9.s3-d0-03-report#p1@T0 10.s3-d0-02-c#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 61. `s3-d0-02-q3`

- 问：C公司在T0时提供的基础版是否包含客户支持？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T0
- 金标要点：C公司以低价切入市场，基础版仅售每月69元，但限制功能数量，且不提供客户支持；尽管性价比突出，但用户反馈对长期维护能力存疑
- 词法前 10：1.s3-d0-02-a#p3@T0 2.s3-d0-02-a#p1@T0 3.s3-d0-04-memo#p1@T0 4.s3-d0-02-b#p3@T0 5.s3-d0-03-report#p1@T0 6.s3-d2-01-quotation-snapshot#p1@T0 7.s3-d0-03-memo#p1@T0 8.s3-d1-01-memo#p2@T0 9.s3-d1-01-memo#p1@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-b#p3@T0 3.s3-d0-02-a#p3@T0 4.s7-d0-t0-01-qa#p2@T0 5.s3-d0-04-memo#p1@T0 6.s3-d2-01-quotation-snapshot#p1@T0 7.s3-d0-03-memo#p1@T0 8.s3-d0-02-c#p3@T0 9.s2-d0-02-interview#p1@T0 10.s3-d0-03-report#p1@T0
- 重排前 10：1.s3-d0-02-a#p1@T0 2.s3-d0-02-a#p3@T0 3.s3-d0-04-memo#p1@T0 4.s3-d0-03-memo#p1@T0 5.s3-d0-03-report#p1@T0 6.s3-d0-02-b#p3@T0 7.s3-d2-01-quotation-snapshot#p1@T0 8.s2-d0-02-interview#p1@T0 9.s7-d0-t0-01-qa#p2@T0 10.s3-d0-02-c#p3@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 62. `s3-d0-02-q4`

- 问：T1时A公司基础版新增了哪些核心功能？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p1@T1；s3-d0-02-b#p1@T1
- 金标要点：新增团队协作工具；新增实时协同编辑与自动化工作流引擎
- 词法前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d2-01-quotation-snapshot#p1@T1 4.s3-d1-01-memo#p2@T1 5.s3-d0-02-c#p1@T1 6.s3-d0-02-a#p2@T1 7.s3-d0-04-memo#p1@T1 8.s3-d0-04-memo#p3@T1 9.s3-d3-01-memo#p1@T1 10.s3-d0-01-memo#p2@T1
- 混合前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-02-b#p3@T1 5.s4-d0-t1-02-guide#p3@T1 6.s6-d1-t1-91-release#p3@T1 7.s3-d0-02-a#p2@T1 8.s6-d0-t1-01-channel#p3@T1 9.s3-d0-03-memo#p2@T1 10.s3-d0-02-c#p1@T1
- 重排前 10：1.s3-d0-02-a#p1@T1 2.s3-d0-02-b#p1@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-02-a#p2@T1 5.s3-d0-02-c#p1@T1 6.s3-d0-02-b#p3@T1 7.s6-d1-t1-91-release#p3@T1 8.s6-d0-t1-01-channel#p3@T1 9.s3-d0-03-memo#p2@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 63. `s3-d0-02-q5`

- 问：在A、B、C三家公司的比价里，T0 时哪一家的定价低于90元？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T0；s3-d0-02-b#p3@T0；s3-d0-02-c#p3@T0
- 金标要点：C公司以低价切入市场，基础版仅售每月69元；C公司以69元最低价进入市场；C公司依托开源生态，推出免费基础版
- 词法前 10：1.s3-d0-03-memo#p1@T0 2.s3-d0-04-memo#p1@T0 3.p1-colaw-liquidation#p1@T0 4.s3-d0-02-c#p3@T0 5.s3-d3-01-report#p2@T0 6.p1-colaw-governance-supervisor-js#p1@T0 7.p1-colaw-capital#p1@T0 8.p1-colaw-governance-supervisor#p1@T0 9.s3-d0-01-report#p1@T0 10.p1-cac-o11#p10@T0
- 混合前 10：1.s3-d0-04-memo#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-02-c#p3@T0 4.s3-d0-01-report#p1@T0 5.s3-d3-01-report#p2@T0 6.s3-d1-01-memo#p2@T0 7.s3-d0-04-memo#p3@T0 8.s3-d0-02-c#p2@T0 9.s3-d0-01-memo#p2@T0 10.s3-d0-02-c#p1@T0
- 重排前 10：1.s3-d0-04-memo#p1@T0 2.s3-d0-03-memo#p1@T0 3.s3-d0-01-report#p1@T0 4.s3-d0-01-memo#p2@T0 5.s3-d0-02-c#p3@T0 6.s3-d3-01-report#p2@T0 7.s3-d1-01-memo#p2@T0 8.s3-d0-02-c#p2@T0 9.s3-d0-04-memo#p3@T0 10.s3-d0-02-c#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 64. `s3-d0-02-q6`

- 问：T1时C公司是否仍然提供免费的基础版本？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-02-b#p3@T1；s3-d0-02-a#p3@T1
- 金标要点：C公司关闭免费基础版入口，改推“成长计划”订阅制，首年费用149元，含全功能访问及优先技术支持；C公司因技术债务问题暂停新客户注册，原69元套餐已取消，现仅开放限时试用，正式版本将于下季度以149元起售
- 词法前 10：1.s3-d0-02-b#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d0-02-b#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s3-d0-02-a#p3@T1 8.s3-d0-03-report#p1@T1 9.s3-d3-01-report#p3@T1 10.s3-d0-02-a#p1@T1
- 混合前 10：1.s3-d0-02-b#p3@T1 2.s3-d0-02-b#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d0-02-a#p1@T1 5.s3-d0-02-a#p3@T1 6.s3-d0-04-memo#p3@T1 7.s3-d2-t1-91-brochure#p1@T1 8.s3-d0-03-report#p1@T1 9.s4-d0-t1-02-guide#p3@T1 10.s3-d3-01-report#p3@T1
- 重排前 10：1.s3-d0-02-b#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d0-02-b#p1@T1 4.s3-d0-02-a#p1@T1 5.s3-d0-02-a#p3@T1 6.s3-d2-t1-91-brochure#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d3-01-report#p3@T1 9.s3-d0-04-memo#p3@T1 10.s4-d0-t1-02-guide#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 65. `s3-d0-03-q2`

- 问：竞品B 的“精英版”套餐在 T1 有哪些新优惠或功能调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-03-memo#p2@T1
- 金标要点：竞品B更新其“精英版”套餐，新增30天免费试用，并将价格调整为每月420元，市场推广力度加大
- 词法前 10：1.s3-d0-03-memo#p2@T1 2.s3-d1-01-memo#p2@T1 3.s3-d0-03-report#p2@T1 4.s3-d0-01-memo#p2@T1 5.s3-d0-01-report#p2@T1 6.s3-d3-01-memo#p2@T1 7.s3-d0-04-memo#p2@T1 8.s3-d1-01-report#p2@T1 9.s7-d3-t1-05-claim#p1@T1 10.s3-d0-02-a#p2@T1
- 混合前 10：1.s3-d0-03-memo#p2@T1 2.s3-d0-04-memo#p2@T1 3.s3-d0-01-memo#p2@T1 4.s3-d3-01-memo#p2@T1 5.s3-d0-03-report#p2@T1 6.s3-d0-01-memo#p3@T1 7.s3-d1-01-memo#p2@T1 8.s3-d2-01-competitor-pricing#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d1-01-memo#p1@T1
- 重排前 10：1.s3-d0-03-memo#p2@T1 2.s3-d0-03-report#p2@T1 3.s3-d1-01-memo#p2@T1 4.s3-d0-01-memo#p2@T1 5.s3-d2-01-competitor-pricing#p2@T1 6.s3-d0-04-memo#p2@T1 7.s3-d0-01-memo#p3@T1 8.s3-d1-01-report#p2@T1 9.s3-d3-01-memo#p2@T1 10.s3-d1-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 66. `s3-d0-03-q3`

- 问：我方主推套餐在T0和T1之间是否有价格或服务内容的变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d0-03-memo#p3@T1
- 金标要点：我方主推套餐维持每月380元不变，但新增一项“客户忠诚计划”作为附加价值，涵盖额外培训资源
- 词法前 10：1.s3-d0-03-report#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d0-03-memo#p3@T1 4.s7-d3-t1-05-memo#p3@T1 5.p1-colaw-equity#p1@T1 6.s3-d1-01-report#p1@T1 7.s1-d0-01-analysis#p2@T1 8.s5-d2-t1-91-digest#p3@T1 9.s3-d0-01-memo#p2@T1 10.s7-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s3-d0-03-memo#p3@T1 2.s3-d1-01-report#p1@T1 3.s3-d0-03-report#p3@T1 4.s3-d0-01-memo#p2@T1 5.s3-d0-04-memo#p3@T1 6.s3-d0-03-memo#p1@T1 7.s3-d3-01-memo#p1@T1 8.s3-d3-01-report#p1@T1 9.s1-d0-01-analysis#p2@T1 10.s3-d0-02-a#p2@T1
- 重排前 10：1.s3-d0-03-report#p3@T1 2.s3-d0-03-memo#p3@T1 3.s3-d1-01-report#p1@T1 4.s3-d0-01-memo#p2@T1 5.s1-d0-01-analysis#p2@T1 6.s3-d0-04-memo#p3@T1 7.s3-d0-03-memo#p1@T1 8.s3-d3-01-memo#p1@T1 9.s3-d3-01-report#p1@T1 10.s3-d0-02-a#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 67. `s3-d1-01-q1`

- 问：在竞品C年度订阅价2,800元的那份比价中，竞品A 在 T1 的价格策略有何变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d1-01-memo#p1@T1；s3-d1-01-report#p1@T1
- 金标要点：竞品A已完成服务整合，将原独立模块打包进主套餐，价格上调至349元/月，但用户满意度调查显示其综合性价比获得认可；至本周期末，竞品A已将基础套餐调涨至每月349元，并将高级功能模块纳入主套餐内，不再单独计价
- 词法前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d1-01-report#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p1@T1 7.s3-d0-01-report#p1@T1 8.s3-d3-01-memo#p1@T1 9.s3-d0-01-memo#p3@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-03-report#p1@T1 5.s3-d3-01-report#p1@T1 6.s3-d1-01-report#p3@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p1@T1
- 重排前 10：1.s3-d1-01-memo#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d3-01-report#p1@T1 5.s3-d0-03-report#p1@T1 6.s3-d1-01-report#p3@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d3-01-memo#p1@T1 10.s3-d1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 68. `s3-d1-01-q3`

- 问：年度订阅价2,800元的那个竞品C，T0 时提供什么订阅方式？T1 又增加了哪些新选项？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d1-01-memo#p3@T1
- 金标要点：竞品C推出按月订阅选项，月费为269元，同时保留年度优惠价2,800元，进一步增强对中小客户的吸引力
- 词法前 10：1.s3-d1-01-memo#p3@T1 2.s3-d1-01-report#p3@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s3-d2-01-competitor-pricing#p2@T1 6.s3-d0-01-report#p3@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s3-d2-01-competitor-pricing#p3@T1 9.s3-d0-01-memo#p3@T1 10.s3-d0-03-report#p2@T1
- 混合前 10：1.s3-d1-01-memo#p3@T1 2.s3-d1-01-report#p3@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-03-report#p2@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d2-01-competitor-pricing#p2@T1 7.s3-d3-01-report#p1@T1 8.s3-d0-01-memo#p3@T1 9.s3-d0-03-report#p1@T1 10.s3-d0-02-b#p3@T1
- 重排前 10：1.s3-d1-01-memo#p3@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d0-01-memo#p3@T1 4.s3-d1-01-report#p3@T1 5.s3-d3-01-memo#p3@T1 6.s3-d0-03-report#p2@T1 7.s3-d0-03-report#p1@T1 8.s3-d1-t1-91-quote#p3@T1 9.s3-d3-01-report#p1@T1 10.s3-d0-02-b#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 69. `s3-d2-01-q2`

- 问：在竞品C月费调到195元的那份比价里，以自动化报告为卖点的竞品B，T1 相比 T0 增加了哪些新服务内容？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d2-01-competitor-pricing#p2@T1
- 金标要点：竞品B在新版本基础上增加30天免费试用期，并将月费降至229元，同时优化了报告生成算法；显著提升响应速度
- 词法前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d0-04-memo#p2@T1 3.s3-d3-01-report#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s6-d0-t1-03-report#p3@T1 8.s3-d0-01-report#p3@T1 9.s3-d2-01-competitor-pricing#p3@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-04-memo#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-memo#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s3-d0-03-report#p1@T1 9.s3-d3-01-memo#p2@T1 10.s3-d0-01-report#p3@T1
- 重排前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-04-memo#p2@T1 4.s3-d1-01-memo#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-memo#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s3-d0-03-report#p1@T1 9.s3-d0-01-report#p3@T1 10.s3-d3-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 70. `s3-d2-01-q3`

- 问：我方基础版服务包在T1时的定价与服务范围是否发生变化？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d2-01-quotation-snapshot#p1@T1
- 金标要点：基础版服务包价格上调至每月189元，巡检周期由月度改为双周一次，同时新增云端日志分析功能
- 词法前 10：1.s3-d0-03-report#p3@T1 2.s3-d0-04-memo#p3@T1 3.s3-d0-03-memo#p1@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s1-d0-01-analysis#p2@T1 7.s4-d0-t1-02-review#p2@T1 8.s3-d0-02-a#p1@T1 9.s6-d0-t1-03-report#p3@T1 10.s3-d2-01-quotation-snapshot#p2@T1
- 混合前 10：1.s3-d0-04-memo#p3@T1 2.s3-d0-03-memo#p1@T1 3.s3-d0-03-report#p3@T1 4.s3-d2-01-quotation-snapshot#p1@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.s4-d0-t1-02-analysis#p1@T1 7.s3-d1-01-memo#p2@T1 8.s1-d0-01-analysis#p2@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s4-d0-t1-02-review#p2@T1
- 重排前 10：1.s3-d0-04-memo#p3@T1 2.s3-d0-03-memo#p1@T1 3.s3-d0-03-report#p3@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s3-d2-01-quotation-snapshot#p1@T1 6.s3-d2-01-quotation-snapshot#p2@T1 7.s3-d1-01-memo#p2@T1 8.s1-d0-01-analysis#p2@T1 9.s4-d0-t1-02-review#p2@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 71. `s3-d3-01-q3`

- 问：在竞品A附带云存储的那份比价里，竞品C的报价结构在T1相比T0发生了哪些关键调整？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p3@T1；s3-d3-01-report#p3@T1
- 金标要点：竞品C的报价结构已完成标准化改革，所有功能模块统一纳入89元基础包，有效降低用户决策成本；竞品C调整订阅策略，取消阶梯加价，统一为89元/月，涵盖全部功能模块，价格透明度大幅提升
- 词法前 10：1.s3-d3-01-memo#p1@T1 2.s3-d3-01-report#p3@T1 3.s3-d3-01-report#p2@T1 4.s3-d0-01-report#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-01-report#p3@T1 8.s3-d1-t1-91-quote#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 混合前 10：1.s3-d3-01-memo#p1@T1 2.s3-d3-01-report#p3@T1 3.s3-d3-01-report#p2@T1 4.s3-d0-01-report#p3@T1 5.s3-d1-t1-91-quote#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-t1-91-pricesheet#p3@T1 8.s3-d0-03-report#p1@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 重排前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-report#p2@T1 3.s3-d0-01-report#p3@T1 4.s3-d3-01-memo#p1@T1 5.s3-d1-t1-91-quote#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d2-01-competitor-pricing#p1@T1 9.s3-d1-t1-91-pricesheet#p2@T1 10.s3-d1-t1-91-pricesheet#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 72. `s3-d3-01-q4`

- 问：在竞品C统一为89元基础包的那份比价里，从 T0 到 T1 各竞品的定价策略如何影响其市场定位？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p3@T1；s3-d3-01-report#p1@T1；s3-d3-01-report#p2@T1
- 金标要点：竞品A已全面推行新版套餐，价格上调至119元/月，同时增加企业级安全认证，目标客户转向中大型组织；竞品B的报价策略发生重大调整，取消固定高价，转而采用按需计费模式，月费最低可至99元，配合灵活服务包，大幅增强市场渗透力；竞品C调整订阅策略，取消阶梯加价，统一为89元/月，涵盖全部功能模块，价格透明度大幅提升，吸引大量中小客户迁移
- 词法前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d0-01-report#p3@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d3-01-report#p2@T1 6.s3-d1-01-memo#p3@T1 7.s3-d0-01-report#p1@T1 8.s3-d1-01-memo#p2@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s3-d0-03-report#p1@T1
- 混合前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-report#p2@T1 3.s3-d3-01-memo#p3@T1 4.s3-d0-01-report#p3@T1 5.s3-d0-01-report#p1@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d0-03-report#p1@T1 8.s3-d0-03-memo#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s3-d1-01-memo#p3@T1
- 重排前 10：1.s3-d3-01-report#p3@T1 2.s3-d3-01-memo#p3@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d3-01-report#p2@T1 5.s3-d0-01-report#p3@T1 6.s3-d1-t1-91-pricesheet#p1@T1 7.s3-d1-01-memo#p3@T1 8.s3-d0-01-report#p1@T1 9.s3-d0-03-report#p1@T1 10.s3-d0-03-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 73. `s4-d0-t0-01-q1`

- 问：v2.3 版成本模型相比旧版在哪些方面实现了性能提升？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p1@T0；s4-d0-t0-01-memo#p2@T0；s4-d0-t0-01-report#p1@T0；s4-d0-t0-01-report#p3@T0
- 金标要点：新模型的准确率从76%提升至89%；模型运行时长由平均4.7秒降至2.3秒；平均误差率下降至3.2%，较上一版本降低1.8个百分点；日均处理效率提升约15%
- 词法前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-report#p3@T0 6.s4-d3-t0-05-summary#p1@T0 7.s1-d0-02-report#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d0-t0-01-plan#p1@T0
- 混合前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d3-t0-05-summary#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s4-d0-t0-01-report#p3@T0 5.s4-d1-t0-03-memo#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d3-t0-05-memo#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d3-t0-05-summary#p1@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-summary#p1@T0 8.s4-d0-t0-01-report#p3@T0 9.s4-d3-t0-05-memo#p2@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 74. `s4-d0-t0-01-q2`

- 问：为何在高层会议中使用旧版模型的决策方案被质疑？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-analysis#p2@T0
- 金标要点：在高层管理会议中，使用T0模型的决策方案被质疑为过于保守；而新模型提供更精细的成本拆解，有助于识别隐藏成本点，提升资源配置透明度
- 词法前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s4-d0-t0-01-report#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s5-d0-t0-01-internal#p3@T0 5.s3-d3-01-report#p3@T0 6.s5-d0-t0-01-internal#p1@T0 7.p1-colaw-governance#p2@T0 8.s4-d0-t0-01-summary#p1@T0 9.p1-colaw-equity#p5@T0 10.s2-d0-03-memo#p1@T0
- 混合前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s5-d0-t0-01-internal#p1@T0 3.s4-d0-t0-01-report#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s3-d3-01-report#p3@T0 7.s7-d1-t0-03-reason#p1@T0 8.s4-d1-t0-03-analysis#p1@T0 9.s4-d0-t0-01-summary#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s4-d0-t0-01-analysis#p2@T0 2.s4-d0-t0-01-report#p1@T0 3.s5-d0-t0-01-internal#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s7-d1-t0-03-reason#p1@T0 7.s3-d3-01-report#p3@T0 8.s4-d1-t0-03-analysis#p1@T0 9.s4-d0-t0-01-summary#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 75. `s4-d0-t0-01-q3`

- 问：新模型在处理非标准流程时存在什么局限性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p3@T0
- 金标要点：当前模型仍存在对非标准流程的覆盖不足问题
- 词法前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d1-t0-03-memo#p1@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s4-d1-t0-03-report#p3@T0 8.s5-d0-t0-01-report#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d1-t0-03-analysis#p3@T0
- 混合前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d0-t0-01-summary#p1@T0 5.s4-d0-t0-01-summary#p3@T0 6.s4-d0-t0-01-report#p1@T0 7.s4-d1-t0-03-analysis#p3@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d1-t0-03-memo#p1@T0 10.s1-d3-01-memo#p2@T0
- 重排前 10：1.s4-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s7-d1-t0-03-reason#p1@T0 4.s4-d1-t0-03-memo#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d0-t0-01-report#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-summary#p3@T0 9.s4-d1-t0-03-analysis#p3@T0 10.s1-d3-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 76. `s4-d0-t0-01-q4`

- 问：为确保模型平滑过渡，已采取哪些协同措施？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-plan#p3@T0
- 金标要点：已启动跨团队协作机制，确保模型变更前完成影响评估与沟通预案，保障平滑过渡
- 词法前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d0-03-report#p3@T0 3.s1-d0-03-memo#p3@T0 4.s1-d0-04-memo#p2@T0 5.s1-d3-01-memo#p3@T0 6.p1-colaw-capital#p2@T0 7.s3-d0-03-report#p2@T0 8.s7-d0-t0-01-qa#p2@T0 9.s1-d2-01-analysis#p1@T0 10.s4-d1-t0-03-report#p3@T0
- 混合前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d3-01-memo#p3@T0 3.s1-d0-04-memo#p2@T0 4.s4-d0-t0-01-memo#p3@T0 5.s4-d0-t0-01-summary#p2@T0 6.s4-d0-t0-01-summary#p3@T0 7.s4-d0-t0-01-report#p1@T0 8.s1-d0-03-report#p3@T0 9.s4-d1-t0-03-analysis#p1@T0 10.s1-d0-03-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-plan#p3@T0 2.s1-d0-03-report#p3@T0 3.s1-d3-01-memo#p3@T0 4.s1-d0-04-memo#p2@T0 5.s1-d0-03-memo#p3@T0 6.s4-d0-t0-01-memo#p3@T0 7.s4-d0-t0-01-summary#p2@T0 8.s4-d0-t0-01-summary#p3@T0 9.s4-d0-t0-01-report#p1@T0 10.s4-d1-t0-03-analysis#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 77. `s4-d0-t0-01-q5`

- 问：v2.3 版成本模型在哪些业务场景下表现出更强的适应性？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-memo#p2@T0；s4-d0-t0-01-report#p1@T0；s4-d0-t0-01-summary#p2@T0
- 金标要点：在复杂项目核算中，新模型的准确率从76%提升至89%；尤其在原材料价格波动场景下保持稳定输出；尤其在高负载时段表现更稳定
- 词法前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d0-t0-01-summary#p2@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d3-t0-05-memo#p1@T0 6.s4-d3-t0-05-summary#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d3-t0-05-analysis#p1@T0 10.s4-d0-t0-01-memo#p2@T0
- 混合前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d0-t0-01-summary#p2@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d3-t0-05-memo#p1@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 重排前 10：1.s4-d0-t0-01-report#p1@T0 2.s4-d1-t0-03-analysis#p1@T0 3.s4-d1-t0-03-report#p1@T0 4.s4-d3-t0-05-memo#p1@T0 5.s4-d3-t0-05-summary#p1@T0 6.s4-d0-t0-01-summary#p2@T0 7.s4-d3-t0-05-analysis#p1@T0 8.s4-d0-t0-01-analysis#p2@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 78. `s4-d0-t0-01-q6`

- 问：多方反馈中提出的三个改进建议分别是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t0-01-feedback#p1@T0；s4-d0-t0-01-feedback#p2@T0；s4-d0-t0-01-feedback#p3@T0
- 金标要点：来自财务部反馈：希望增加“人工工时”维度的细分统计，以便更精确地分配间接人力成本；技术团队建议：应明确模型版本标识规则，避免在报表中出现混淆引用；运营部门提出：期望在模型中加入季节性因子调节功能，以应对周期性业务高峰
- 词法前 10：1.s5-d0-t0-01-internal#p2@T0 2.s1-d0-05-warn#p1@T0 3.s4-d0-t0-01-feedback#p3@T0 4.s5-d0-t0-01-memo#p3@T0 5.s1-d0-01-memo#p2@T0 6.s5-d2-t0-04-analysis#p2@T0 7.s5-d0-t0-01-internal#p1@T0 8.s4-d3-t0-05-analysis#p1@T0 9.s2-d0-01-report#p2@T0 10.s4-d0-t0-01-report#p2@T0
- 混合前 10：1.s1-d0-05-warn#p1@T0 2.s5-d0-t0-01-memo#p3@T0 3.s5-d0-t0-01-internal#p2@T0 4.s2-d0-01-report#p2@T0 5.s1-d0-01-memo#p2@T0 6.s5-d0-t0-01-internal#p1@T0 7.s4-d0-t0-01-analysis#p3@T0 8.s2-d0-02-memo#p3@T0 9.s1-d1-01-memo#p3@T0 10.s2-d2-01-memo#p1@T0
- 重排前 10：1.s1-d0-01-memo#p2@T0 2.s2-d2-01-memo#p1@T0 3.s1-d0-05-warn#p1@T0 4.s5-d0-t0-01-memo#p3@T0 5.s5-d0-t0-01-internal#p2@T0 6.s2-d0-01-report#p2@T0 7.s5-d0-t0-01-internal#p1@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s2-d0-02-memo#p3@T0 10.s1-d1-01-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 79. `s4-d0-t1-02-q1`

- 问：计划11月启动全量灰度的那版成本模型，T1 版本相比 T0 版本有哪些改进？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-memo#p1@T1；s4-d0-t1-02-memo#p2@T1；s4-d0-t1-02-report#p2@T1
- 金标要点：预测准确率从76.3%升至89.1%；引入动态分摊算法以提升跨项目资源分配的准确性；对人力工时与设备折旧的非线性权重调整
- 词法前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d2-t1-04-internal#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-review#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d2-t1-04-report#p1@T1 9.s4-d0-t1-02-review#p1@T1 10.s4-d0-t1-02-memo#p1@T1
- 混合前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d2-t1-04-memo#p3@T1 8.s6-d0-t1-03-memo#p2@T1 9.s4-d2-t1-04-summary#p1@T1 10.s3-d2-01-competitor-pricing#p2@T1
- 重排前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-report#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s3-d2-01-competitor-pricing#p2@T1 10.s4-d2-t1-04-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 80. `s4-d0-t1-02-q2`

- 问：计划11月全量灰度的那版成本模型，在高并发场景下的预测表现如何？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-memo#p2@T1；s4-d0-t1-02-report#p2@T1
- 金标要点：特别强化了高并发场景下的弹性成本预测能力；平均预算偏差减少28%；预测准确率从76.3%升至89.1%
- 词法前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d0-t1-02-memo#p2@T1 4.s4-d0-t1-02-plan#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s2-d3-01-memo#p3@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-report#p1@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s1-d3-01-memo#p3@T1
- 混合前 10：1.s4-d0-t1-02-plan#p2@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-plan#p1@T1 9.s4-d2-t1-04-summary#p1@T1 10.s4-d2-t1-04-summary#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s4-d0-t1-02-plan#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d0-t1-02-plan#p1@T1 9.s4-d2-t1-04-summary#p2@T1 10.s4-d2-t1-04-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 81. `s4-d0-t1-02-q3`

- 问：为何新版本在低频任务中出现预算预留增加？其优势是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-analysis#p2@T1；s4-d0-t1-02-analysis#p3@T1
- 金标要点：在低频任务中，新版模型倾向于保守估计，导致预算预留增加约7.6%，但有效避免了超支风险；该策略已被运营团队采纳为标准配置；整体风险控制收益远超成本波动影响
- 词法前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s3-d0-02-c#p2@T1 5.s2-d2-01-memo#p1@T1 6.s4-d0-t1-02-review#p1@T1 7.s2-d2-01-memo#p3@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-claim#p3@T1 10.s3-d0-03-report#p2@T1
- 混合前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s2-d2-01-memo#p3@T1 5.s4-d2-t1-04-memo#p1@T1 6.s4-d0-t1-02-memo#p1@T1 7.s4-d0-t1-02-report#p1@T1 8.s4-d0-t1-02-memo#p2@T1 9.s4-d0-t1-02-review#p2@T1 10.s2-d2-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-analysis#p2@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s2-d2-01-memo#p1@T1 5.s4-d0-t1-02-memo#p1@T1 6.s2-d2-01-memo#p3@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-report#p1@T1 9.s4-d0-t1-02-memo#p2@T1 10.s4-d0-t1-02-review#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 82. `s4-d0-t1-02-q4`

- 问：成本模型的下一步迭代路线图包含哪些关键任务？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-plan#p1@T1；s4-d0-t1-02-plan#p2@T1；s4-d0-t1-02-plan#p3@T1
- 金标要点：本年度模型优化计划聚焦三大方向：一是增强对异构硬件的成本映射能力，二是建立实时反馈闭环以动态修正参数；路线图明确要求每季度进行一次跨部门验证，确保模型适应实际业务变化；整合外部市场数据源实现成本趋势预警；模型可解释性模块的开发
- 词法前 10：1.s4-d2-t1-04-summary#p3@T1 2.s4-d0-t1-02-analysis#p1@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d2-t1-04-memo#p1@T1 5.s6-d0-t1-03-internal#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-report#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s6-d0-t1-02-memo#p3@T1 10.s6-d0-t1-02-report#p3@T1
- 混合前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d2-t1-04-summary#p3@T1 4.s4-d0-t1-02-plan#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d0-t1-02-analysis#p1@T1 9.s6-d0-t1-03-internal#p2@T1 10.s4-d2-t1-04-internal#p3@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s4-d2-t1-04-summary#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d2-t1-04-internal#p3@T1 10.s4-d0-t1-02-plan#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 83. `s4-d0-t1-02-q5`

- 问：使用T1版本模型时，用户需要注意哪些操作规范？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-guide#p1@T1；s4-d0-t1-02-guide#p2@T1；s4-d0-t1-02-guide#p3@T1
- 金标要点：本指南更新内容涵盖新模型的参数配置方法、典型场景应用示例及常见错误规避建议；用户应定期检查模型输出中的置信区间，当低于85%时需人工复核；所有新建项目必须采用T1版本作为默认测算基准，旧版本仅限历史数据追溯用途；需启用“弹性阈值”选项以适配突发流量场景
- 词法前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p2@T1 3.s4-d0-t1-02-analysis#p1@T1 4.s6-d3-t1-02-memo#p1@T1 5.s2-d2-01-memo#p1@T1 6.s4-d2-t1-04-summary#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s2-d0-03-memo#p1@T1 9.s6-d0-t1-01-channel#p3@T1 10.s1-d1-01-analysis#p1@T1
- 混合前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p3@T1 3.s4-d0-t1-02-guide#p2@T1 4.s7-d0-t1-02-update#p2@T1 5.s4-d2-t1-04-summary#p1@T1 6.s2-d2-01-memo#p1@T1 7.s4-d0-t1-02-analysis#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.s6-d3-t1-03-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-guide#p3@T1 2.s7-d0-t1-02-update#p2@T1 3.s2-d2-01-memo#p1@T1 4.s4-d0-t1-02-analysis#p1@T1 5.s7-d0-t1-02-update#p3@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-summary#p1@T1 8.s4-d2-t1-04-internal#p1@T1 9.s4-d0-t1-02-plan#p3@T1 10.s6-d3-t1-03-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 84. `s4-d0-t1-02-q6`

- 问：评审会议对模型的后续发展提出了哪些建议？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d0-t1-02-review#p2@T1
- 金标要点：在未来版本中加入成本敏感度分析功能；扩展对云服务阶梯定价的支持
- 词法前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-review#p3@T1 3.s7-d2-t1-04-memo#p3@T1 4.s4-d0-t1-02-plan#p2@T1 5.p1-colaw-governance-supervisor#p4@T1 6.p1-colaw-governance-supervisor-js#p2@T1 7.s2-d3-t1-91-minutes#p1@T1 8.s5-d3-t1-05-memo#p1@T1 9.s5-d0-t1-02-analysis#p1@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-plan#p2@T1 3.s4-d0-t1-02-report#p3@T1 4.s2-d3-t1-91-minutes#p1@T1 5.s4-d2-t1-04-internal#p1@T1 6.s4-d0-t1-02-review#p3@T1 7.s4-d2-t1-04-internal#p2@T1 8.s7-d0-t1-02-brief#p2@T1 9.s1-d2-01-analysis#p2@T1 10.s2-d3-01-memo#p1@T1
- 重排前 10：1.s4-d0-t1-02-review#p2@T1 2.s4-d0-t1-02-plan#p2@T1 3.s4-d0-t1-02-review#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s4-d0-t1-02-report#p3@T1 6.s2-d3-t1-91-minutes#p1@T1 7.s4-d2-t1-04-internal#p1@T1 8.s4-d2-t1-04-internal#p2@T1 9.s2-d3-01-memo#p1@T1 10.s1-d2-01-analysis#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 85. `s4-d1-t0-03-q1`

- 问：新版本成本模型如何改进固定与可变成本的区分精度？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p1@T0
- 金标要点：本次内部测算模型在成本结构分析中引入了动态分摊机制，显著提升了对固定成本与可变成本的区分精度；新版本通过加权平均法处理跨周期投入，使单位产出成本估算偏差率下降至5.2%以下
- 词法前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d0-t0-01-analysis#p2@T0 4.s4-d3-t0-05-memo#p3@T0 5.s4-d1-t0-03-report#p1@T0 6.s4-d0-t0-01-summary#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s4-d3-t0-05-analysis#p3@T0 10.s4-d3-t0-05-analysis#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-analysis#p2@T0 6.s4-d0-t0-01-summary#p1@T0 7.s4-d0-t0-01-report#p1@T0 8.s4-d1-t0-03-analysis#p3@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d3-t0-05-analysis#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p1@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-05-analysis#p1@T0 7.s4-d0-t0-01-analysis#p2@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d3-t0-05-memo#p3@T0 10.s4-d1-t0-03-analysis#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 86. `s4-d1-t0-03-q2`

- 问：本次模型迭代中移除了哪些冗余计算项？带来了什么影响？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p2@T0
- 金标要点：针对历史数据中存在冗余计算项的问题，已剔除重复归集的间接费用模块；该调整使模型运行效率提升约18%，同时增强结果可解释性
- 词法前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d0-t0-01-memo#p1@T0 3.s4-d1-t0-03-memo#p1@T0 4.s7-d0-t0-01-qa#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s7-d0-t0-01-qa#p1@T0 7.s4-d3-t0-05-memo#p3@T0 8.s4-d0-t0-01-analysis#p1@T0 9.s4-d3-t0-05-memo#p1@T0 10.s4-d3-t0-05-analysis#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-analysis#p3@T0 5.s4-d0-t0-01-analysis#p1@T0 6.s4-d3-t0-05-memo#p3@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d0-t0-01-report#p1@T0 9.s4-d0-t0-01-analysis#p2@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p2@T0 2.s4-d1-t0-03-memo#p1@T0 3.s4-d0-t0-01-memo#p1@T0 4.s4-d1-t0-03-analysis#p3@T0 5.s4-d0-t0-01-analysis#p1@T0 6.s4-d3-t0-05-memo#p3@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d0-t0-01-report#p1@T0 10.s4-d0-t0-01-analysis#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 87. `s4-d1-t0-03-q3`

- 问：新版本模型支持哪几类核心成本拆解？对预算规划有何帮助？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-memo#p3@T0
- 金标要点：当前版本支持多维度成本拆解，包括人力、设备、运维及外部服务四类核心支出，为后续预算规划提供更细粒度支撑
- 词法前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d0-t0-01-analysis#p2@T0 3.s4-d0-t0-01-plan#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d3-t0-05-memo#p1@T0 8.s4-d1-t0-03-plan#p2@T0 9.s4-d1-t0-03-report#p1@T0 10.s4-d0-t0-01-report#p1@T0
- 混合前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s4-d1-t0-03-analysis#p3@T0 4.s4-d0-t0-01-analysis#p2@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d1-t0-03-plan#p2@T0 8.s4-d0-t0-01-plan#p2@T0 9.s4-d3-t0-05-summary#p1@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d1-t0-03-memo#p3@T0 2.s4-d3-t0-05-memo#p1@T0 3.s4-d1-t0-03-memo#p1@T0 4.s4-d0-t0-01-plan#p2@T0 5.s4-d1-t0-03-analysis#p3@T0 6.s4-d0-t0-01-analysis#p2@T0 7.s4-d0-t0-01-report#p1@T0 8.s4-d3-t0-05-summary#p1@T0 9.s4-d0-t0-01-summary#p1@T0 10.s4-d1-t0-03-plan#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 88. `s4-d1-t0-03-q4`

- 问：未来版本计划引入哪些关键技术能力？预期达到什么效果？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d1-t0-03-plan#p1@T0；s4-d1-t0-03-plan#p2@T0；s4-d1-t0-03-plan#p3@T0
- 金标要点：计划下一阶段引入实时数据流接入能力，以支持动态成本重估，目标是将响应延迟压缩至分钟级；增加成本敏感度分析模块，帮助识别关键影响因子，辅助管理层制定策略调整预案；探索与外部经济指标联动建模，提升宏观环境变化应对能力
- 词法前 10：1.s4-d1-t0-03-plan#p1@T0 2.s7-d0-t0-01-qa#p2@T0 3.s1-d1-01-memo#p1@T0 4.s1-d0-01-memo#p1@T0 5.s7-d0-t0-01-qa#p1@T0 6.s1-d0-02-report#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s1-d0-03-memo#p3@T0 9.s2-d0-02-interview#p1@T0 10.s2-d0-03-interview#p3@T0
- 混合前 10：1.s1-d0-01-memo#p1@T0 2.s4-d1-t0-03-plan#p1@T0 3.s1-d0-02-report#p3@T0 4.s4-d3-t0-05-summary#p3@T0 5.s2-d0-03-interview#p3@T0 6.s2-d2-01-memo#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s2-d0-03-memo#p3@T0 9.s1-d0-03-memo#p3@T0 10.s1-d1-01-memo#p1@T0
- 重排前 10：1.s4-d1-t0-03-plan#p1@T0 2.s1-d0-01-memo#p1@T0 3.s1-d0-02-report#p3@T0 4.s4-d3-t0-05-summary#p3@T0 5.s2-d0-03-interview#p3@T0 6.s2-d2-01-memo#p1@T0 7.s4-d3-t0-05-summary#p1@T0 8.s1-d0-03-memo#p3@T0 9.s1-d1-01-memo#p1@T0 10.s2-d0-03-memo#p3@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 89. `s4-d2-t1-04-q1`

- 问：可用性维持在99.98%以上的那版成本模型，相比旧版预测准确率提升了多少？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p2@T1
- 金标要点：误差率由原先的8.7%降至4.3%
- 词法前 10：1.s4-d2-t1-04-summary#p2@T1 2.s4-d2-t1-04-memo#p1@T1 3.s4-d0-t1-02-report#p2@T1 4.s4-d0-t1-02-analysis#p3@T1 5.s3-d0-02-c#p2@T1 6.s6-d0-t1-03-memo#p2@T1 7.s4-d0-t1-02-memo#p1@T1 8.s6-d0-t1-03-report#p2@T1 9.s6-d0-t1-03-internal#p2@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s4-d0-t1-02-report#p2@T1 2.s4-d0-t1-02-analysis#p3@T1 3.s4-d2-t1-04-memo#p1@T1 4.s4-d0-t1-02-report#p1@T1 5.s4-d2-t1-04-summary#p2@T1 6.s4-d2-t1-04-memo#p2@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-04-summary#p1@T1 9.s4-d0-t1-02-memo#p1@T1 10.s7-d2-t1-04-memo#p2@T1
- 重排前 10：1.s4-d2-t1-04-memo#p1@T1 2.s4-d2-t1-04-summary#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-report#p2@T1 5.s4-d0-t1-02-analysis#p3@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p2@T1 8.s7-d2-t1-04-memo#p2@T1 9.s6-d0-t1-03-memo#p2@T1 10.s4-d2-t1-04-summary#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 90. `s4-d2-t1-04-q2`

- 问：跨区域部署时，边缘机房每单位算力的花费比中心机房便宜多少百分比？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-report#p1@T1
- 金标要点：结果显示，边缘节点的单位计算成本较中心节点低19.6%；本报告基于最新版本的成本模型进行测算，重点分析了多区域部署下的资源利用率差异
- 词法前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-report#p2@T1 3.s1-d0-03-report#p2@T1 4.s6-d0-t1-01-patch#p1@T1 5.s4-d2-t1-91-review#p2@T1 6.s5-d0-t1-02-analysis#p3@T1 7.s3-d0-03-report#p1@T1 8.s2-d0-04-memo#p2@T1 9.s4-d2-t1-04-internal#p2@T1 10.p2-gdp-national#p3@T1
- 混合前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d2-t1-91-review#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s1-d0-03-report#p2@T1 5.s2-d1-01-memo#p1@T1 6.s3-d2-01-competitor-pricing#p1@T1 7.s3-d1-t1-91-pricesheet#p1@T1 8.s5-d0-t1-02-analysis#p3@T1 9.s5-d1-t1-03-memo#p3@T1 10.s3-d0-04-memo#p2@T1
- 重排前 10：1.s4-d2-t1-04-report#p1@T1 2.s5-d0-t1-02-analysis#p3@T1 3.s4-d2-t1-91-review#p2@T1 4.s4-d0-t1-02-memo#p1@T1 5.s1-d0-03-report#p2@T1 6.s2-d1-01-memo#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s3-d2-01-competitor-pricing#p1@T1 9.s3-d1-t1-91-pricesheet#p1@T1 10.s3-d0-04-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 91. `s4-d2-t1-04-q3`

- 问：边缘节点单位成本比中心低近两成的那版成本模型，做了哪些关键优化来减少资源浪费？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d2-t1-04-memo#p1@T1；s4-d2-t1-04-report#p2@T1
- 金标要点：引入弹性伸缩阈值优化；资源浪费减少31%；引入动态权重调整机制以提升预测准确率
- 词法前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d2-t1-04-report#p2@T1 3.s4-d0-t1-02-memo#p1@T1 4.s2-d0-01-report#p3@T1 5.s4-d0-t1-02-report#p1@T1 6.s4-d0-t1-02-plan#p1@T1 7.s1-d0-04-memo#p2@T1 8.s4-d0-t1-02-memo#p2@T1 9.s4-d0-t1-02-analysis#p3@T1 10.s4-d2-t1-04-memo#p1@T1
- 混合前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d0-t1-02-plan#p1@T1 4.s4-d2-t1-04-report#p2@T1 5.s4-d0-t1-02-memo#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-analysis#p3@T1 9.s4-d2-t1-91-model-v3#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 重排前 10：1.s4-d2-t1-04-report#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s4-d2-t1-04-report#p2@T1 4.s4-d0-t1-02-plan#p1@T1 5.s4-d0-t1-02-memo#p2@T1 6.s4-d0-t1-02-report#p1@T1 7.s4-d2-t1-04-memo#p1@T1 8.s4-d0-t1-02-analysis#p3@T1 9.s4-d2-t1-91-model-v3#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 92. `s4-d3-t0-05-q1`

- 问：新版本成本模型在高并发场景下的平均响应延迟是多少？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-memo#p1@T0
- 金标要点：模型在模拟高并发场景下表现稳定，平均响应延迟控制在210毫秒以内，资源峰值使用率未超过78%
- 词法前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d1-t0-03-report#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s2-d2-01-memo#p3@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-analysis#p1@T0 7.s4-d1-t0-03-plan#p1@T0 8.s4-d3-t0-05-analysis#p3@T0 9.s4-d0-t0-01-summary#p2@T0 10.s2-d2-01-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d3-t0-05-summary#p1@T0 3.s4-d1-t0-03-analysis#p1@T0 4.s4-d1-t0-03-report#p1@T0 5.s4-d0-t0-01-report#p1@T0 6.s4-d1-t0-03-plan#p1@T0 7.s4-d3-t0-05-memo#p3@T0 8.s4-d1-t0-03-memo#p1@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d0-t0-01-summary#p1@T0
- 重排前 10：1.s4-d3-t0-05-memo#p1@T0 2.s4-d1-t0-03-report#p1@T0 3.s4-d3-t0-05-summary#p1@T0 4.s4-d0-t0-01-report#p1@T0 5.s4-d1-t0-03-analysis#p1@T0 6.s4-d1-t0-03-memo#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d0-t0-01-summary#p1@T0 9.s4-d1-t0-03-plan#p1@T0 10.s4-d3-t0-05-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 93. `s4-d3-t0-05-q2`

- 问：v1.4版本相比v1.2在初始化时间上缩短了多少秒？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-analysis#p2@T0
- 金标要点：其初始化时间平均为47秒，较v1.2缩短了12秒，且具备更优的容错恢复能力；v1.4的部署复杂度略有上升，但通过自动化脚本可有效缓解
- 词法前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s4-d3-t0-05-analysis#p1@T0 3.s7-d0-t0-01-arch#p3@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s4-d0-t0-01-memo#p1@T0 6.s4-d0-t0-01-report#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s3-d0-t0-91-flyer#p2@T0 9.s5-d2-t0-04-analysis#p3@T0 10.s4-d3-t0-05-memo#p1@T0
- 混合前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s4-d3-t0-05-analysis#p1@T0 3.s7-d0-t0-01-arch#p3@T0 4.s4-d0-t0-01-report#p3@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s4-d0-t0-01-memo#p1@T0 7.s5-d2-t0-04-analysis#p3@T0 8.s4-d1-t0-03-analysis#p2@T0 9.s4-d3-t0-05-memo#p1@T0 10.s4-d3-t0-05-summary#p1@T0
- 重排前 10：1.s4-d3-t0-05-analysis#p2@T0 2.s7-d0-t0-01-arch#p3@T0 3.s4-d3-t0-05-analysis#p1@T0 4.s4-d0-t0-01-memo#p1@T0 5.s5-d0-t0-01-analysis#p1@T0 6.s5-d2-t0-04-analysis#p3@T0 7.s4-d1-t0-03-analysis#p2@T0 8.s4-d3-t0-05-memo#p1@T0 9.s4-d3-t0-05-summary#p1@T0 10.s4-d0-t0-01-report#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 94. `s4-d3-t0-05-q4`

- 问：为解决内存泄漏问题，团队采取了哪些具体措施？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s4-d3-t0-05-report#p2@T0
- 金标要点：针对该问题，团队已实施缓冲区大小动态调整策略，并引入周期性垃圾回收机制
- 词法前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d3-t0-05-summary#p2@T0 5.p1-colaw-capital#p2@T0 6.s7-d0-t0-01-qa#p2@T0 7.s3-d0-03-report#p2@T0 8.s2-d0-04-memo#p2@T0 9.s1-d0-03-report#p3@T0 10.s4-d0-t0-01-report#p3@T0
- 混合前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s4-d3-t0-05-summary#p2@T0 4.s5-d0-t0-01-memo#p2@T0 5.p1-cac-o11#p10@T0 6.s7-d0-t0-01-internal#p1@T0 7.s1-d0-03-memo#p2@T0 8.s1-d0-02-memo#p2@T0 9.s4-d0-t0-01-memo#p1@T0 10.s7-d0-t0-01-qa#p1@T0
- 重排前 10：1.s4-d3-t0-05-report#p1@T0 2.s4-d3-t0-05-report#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s4-d3-t0-05-summary#p2@T0 5.s5-d0-t0-01-memo#p2@T0 6.p1-cac-o11#p10@T0 7.s7-d0-t0-01-internal#p1@T0 8.s1-d0-03-memo#p2@T0 9.s1-d0-02-memo#p2@T0 10.s4-d0-t0-01-memo#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 95. `s5-d0-t0-01-q1`

- 问：综合多份文档来看，协作机制在响应速度和响应时间上有哪些量化成效？其推广又面临哪三大挑战？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-report#p1@T0；s5-d0-t0-01-analysis#p1@T0；s5-d0-t0-01-summary#p2@T0
- 金标要点：在公共服务响应速度上平均提升了约40%；在处理突发事件时平均缩短响应时间2.3小时；技术适配性不足、组织惯性阻力大、外部监督机制缺失
- 词法前 10：1.s5-d0-t0-01-memo#p3@T0 2.s5-d0-t0-01-summary#p2@T0 3.s4-d3-t0-05-summary#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s5-d0-t0-01-summary#p1@T0 6.s5-d0-t0-01-analysis#p1@T0 7.s5-d0-t0-01-report#p1@T0 8.s3-d0-01-report#p2@T0 9.s7-d0-t0-01-arch#p3@T0 10.s5-d2-t0-04-memo#p3@T0
- 混合前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d0-t0-01-summary#p2@T0 3.s5-d0-t0-01-summary#p1@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-report#p1@T0 7.s5-d0-t0-01-press#p1@T0 8.s5-d0-t0-01-memo#p3@T0 9.s1-d0-03-report#p2@T0 10.s2-d2-01-report#p2@T0
- 重排前 10：1.s5-d0-t0-01-memo#p3@T0 2.s4-d3-t0-05-summary#p3@T0 3.s5-d0-t0-01-summary#p1@T0 4.s5-d0-t0-01-analysis#p1@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-report#p1@T0 7.s5-d0-t0-01-press#p1@T0 8.s5-d0-t0-01-summary#p2@T0 9.s1-d0-03-report#p2@T0 10.s2-d2-01-report#p2@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 96. `s5-d0-t0-01-q2`

- 问：关于社区服务里的协作平台（某市智慧协作平台），不同来源的评价有矛盾吗？请举例并分析原因。
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-memo#p2@T0；s5-d0-t0-01-press#p1@T0；s5-d0-t0-01-press#p2@T0
- 金标要点：得分达87分；被视为创新典范；报道强调其“零延迟”响应能力；该平台实际覆盖范围仅限于主城区，偏远社区仍依赖传统方式，存在信息孤岛现象；在试点阶段曾出现沟通延迟问题；主要因责任划分不清导致执行脱节
- 词法前 10：1.s5-d0-t0-01-press#p1@T0 2.s5-d0-t0-01-report#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s5-d2-t0-04-analysis#p1@T0 5.s1-d0-04-memo#p3@T0 6.p1-colaw-governance#p3@T0 7.s5-d0-t0-01-memo#p1@T0 8.s5-d2-t0-04-report#p2@T0 9.p1-colaw-equity#p4@T0 10.s5-d2-t0-04-analysis#p2@T0
- 混合前 10：1.s5-d0-t0-01-report#p1@T0 2.s5-d0-t0-01-press#p1@T0 3.s5-d0-t0-01-memo#p1@T0 4.s5-d0-t0-01-summary#p1@T0 5.s5-d0-t0-01-internal#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-03-report#p2@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s5-d2-t0-04-analysis#p2@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s5-d0-t0-01-press#p1@T0 2.s5-d0-t0-01-report#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s5-d2-t0-04-analysis#p2@T0 5.s5-d0-t0-01-memo#p1@T0 6.s5-d0-t0-01-summary#p1@T0 7.s5-d0-t0-01-internal#p2@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s4-d3-t0-05-summary#p3@T0 10.s1-d0-03-report#p2@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 97. `s5-d0-t0-01-q3`

- 问：从文档中提取支持‘该机制在偏远地区效果不佳’这一观点的证据。
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-press#p2@T0；s5-d0-t0-01-report#p2@T0
- 金标要点：在资源紧张区域效果不显著；偏远社区仍依赖传统方式，存在信息孤岛现象
- 词法前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-claim#p3@T0 4.s7-d1-t0-03-fact#p2@T0 5.s7-d1-t0-03-reason#p3@T0 6.s7-d1-t0-03-memo#p1@T0 7.s7-d1-t0-03-reason#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s4-d3-t0-05-summary#p3@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-memo#p3@T0 3.s7-d1-t0-03-fact#p2@T0 4.s5-d0-t0-01-memo#p3@T0 5.s5-d0-t0-01-memo#p1@T0 6.s7-d1-t0-03-reason#p2@T0 7.s7-d1-t0-03-reason#p1@T0 8.s5-d0-t0-01-report#p2@T0 9.s5-d0-t0-01-summary#p1@T0 10.s4-d3-t0-05-summary#p3@T0
- 重排前 10：1.s7-d1-t0-03-claim#p1@T0 2.s7-d1-t0-03-fact#p2@T0 3.s5-d0-t0-01-memo#p1@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d1-t0-03-memo#p3@T0 7.s5-d0-t0-01-summary#p1@T0 8.s4-d3-t0-05-summary#p3@T0 9.s5-d0-t0-01-memo#p3@T0 10.s5-d0-t0-01-report#p2@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 98. `s5-d0-t0-01-q4`

- 问：哪份文档最直接支持‘系统界面复杂影响使用率’这一说法？请说明理由。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-internal#p1@T0
- 金标要点：在2023年第一季度的跨部门协调会上，多位负责人反映系统界面复杂，操作门槛高，导致基层人员使用意愿低；此问题被列为优先改进项
- 词法前 10：1.s7-d1-t0-03-claim#p3@T0 2.s7-d1-t0-03-reason#p2@T0 3.s7-d1-t0-03-claim#p1@T0 4.s7-d1-t0-03-reason#p3@T0 5.s5-d0-t0-01-analysis#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-memo#p2@T0 8.s5-d0-t0-01-internal#p1@T0 9.s5-d2-t0-04-memo#p3@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s5-d0-t0-01-analysis#p2@T0 2.s7-d1-t0-03-reason#p2@T0 3.s7-d0-t0-01-qa#p2@T0 4.s5-d0-t0-01-internal#p1@T0 5.s7-d0-t0-01-arch#p2@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d1-t0-03-reason#p1@T0 8.s7-d1-t0-03-memo#p2@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-claim#p1@T0
- 重排前 10：1.s7-d1-t0-03-reason#p2@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-claim#p1@T0 4.s5-d0-t0-01-analysis#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s5-d0-t0-01-internal#p1@T0 7.s7-d1-t0-03-fact#p3@T0 8.s7-d0-t0-01-arch#p2@T0 9.s7-d0-t0-01-internal#p3@T0 10.s7-d1-t0-03-reason#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 99. `s5-d0-t0-01-q5`

- 问：根据现有材料，能否得出‘该机制已证明完全可行’的结论？为什么？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-memo#p3@T0；s5-d0-t0-01-report#p2@T0；s5-d0-t0-01-summary#p3@T0
- 金标要点：当前所有结论均基于局部经验与间接数据，尚无权威机构出具全面评估报告，应谨慎对待其广泛推广建议。；平台运行依赖人工协调，自动化程度不足，且在资源紧张区域效果不显著。；该机制的成效存在争议，需更多实证研究以明确其适用边界与改进方向。
- 词法前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-reason#p2@T0 3.s2-d3-01-interview#p3@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-memo#p2@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d1-t0-03-memo#p1@T0 8.s5-d2-t0-04-report#p3@T0 9.s7-d0-t0-01-qa#p2@T0 10.s7-d1-t0-03-reason#p1@T0
- 混合前 10：1.s7-d1-t0-03-memo#p3@T0 2.s2-d3-01-interview#p3@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-claim#p2@T0 5.s7-d1-t0-03-claim#p3@T0 6.s5-d0-t0-01-memo#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s7-d0-t0-01-report#p3@T0 10.s5-d0-t0-01-summary#p1@T0
- 重排前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-memo#p3@T0 3.s7-d1-t0-03-claim#p2@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-reason#p2@T0 6.s2-d3-01-interview#p3@T0 7.s5-d0-t0-01-memo#p3@T0 8.s7-d1-t0-03-claim#p1@T0 9.s5-d0-t0-01-summary#p1@T0 10.s7-d0-t0-01-report#p3@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 100. `s5-d0-t0-01-q6`

- 问：如果要在未来一年内推动该机制全面推广，基于文档内容，应优先解决哪些问题？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t0-01-analysis#p3@T0；s5-d0-t0-01-internal#p1@T0；s5-d0-t0-01-internal#p2@T0；s5-d0-t0-01-summary#p2@T0
- 金标要点：建议在全面推广前，建立标准化培训体系，并设定阶段性评估节点，以动态优化机制设计。；多位负责人反映系统界面复杂，操作门槛高，导致基层人员使用意愿低。；若能整合现有政务平台接口，可降低重复录入负担，提升数据一致性。；但其推广面临三大挑战：技术适配性不足、组织惯性阻力大、外部监督机制缺失。这些因素共同制约其规模化应用
- 词法前 10：1.s4-d3-t0-05-summary#p3@T0 2.s7-d0-t0-01-qa#p1@T0 3.s5-d0-t0-01-analysis#p3@T0 4.s1-d0-03-report#p2@T0 5.s5-d2-t0-04-memo#p3@T0 6.s5-d0-t0-01-summary#p3@T0 7.s5-d0-t0-01-internal#p1@T0 8.s1-d0-01-memo#p2@T0 9.s4-d3-t0-05-report#p2@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d0-t0-01-analysis#p3@T0 3.s5-d0-t0-01-summary#p3@T0 4.s5-d0-t0-01-internal#p1@T0 5.s2-d0-02-interview#p1@T0 6.s1-d0-03-report#p2@T0 7.s5-d2-t0-04-analysis#p3@T0 8.s4-d1-t0-03-plan#p3@T0 9.s1-d0-02-memo#p1@T0 10.s5-d0-t0-01-memo#p1@T0
- 重排前 10：1.s4-d3-t0-05-summary#p3@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s5-d0-t0-01-analysis#p3@T0 4.s5-d0-t0-01-internal#p1@T0 5.s2-d0-02-interview#p1@T0 6.s1-d0-03-report#p2@T0 7.s1-d0-02-memo#p1@T0 8.s5-d0-t0-01-memo#p1@T0 9.s5-d0-t0-01-summary#p3@T0 10.s4-d1-t0-03-plan#p3@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 101. `s5-d0-t1-02-q1`

- 问：以城市交通拥堵指标和“青少年近视率超一半”为例，二手数据是怎样通过反复引用变成“被接受的真相”的？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p1@T1；s5-d0-t1-02-memo#p3@T1；s5-d0-t1-02-summary#p1@T1；s5-d0-t1-02-summary#p2@T1
- 金标要点：被多家媒体和智库间接转述；最早可追溯至2014年某高校调研；即使原始数据无法验证，只要被多次引用并嵌入正式论述，便可能成为“事实”本身；这些数据往往经过多次转述，每一次传递都可能引入轻微变形，最终形成一种“集体记忆式事实”。；尽管近年新调查显示实际比例为48.6%，但该“旧共识”仍主导舆论讨论，甚至影响教育政策方向。
- 词法前 10：1.s5-d0-t1-02-summary#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-summary#p3@T1 4.s5-d0-t1-02-memo#p2@T1 5.s5-d0-t1-02-memo#p1@T1 6.s5-d0-t1-02-report#p2@T1 7.s7-d3-t1-05-memo#p2@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s5-d0-t1-02-summary#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d0-t1-02-memo#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s5-d0-t1-02-analysis#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-summary#p3@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d0-t1-02-summary#p2@T1 5.s5-d0-t1-02-memo#p2@T1 6.s5-d1-t1-03-memo#p3@T1 7.s5-d0-t1-02-analysis#p1@T1 8.s5-d1-t1-03-note#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 102. `s5-d0-t1-02-q2`

- 问：当原始数据无法验证时，为何某些被转述的数据仍能在政策讨论中获得高度可信度？请从引用行为与制度惯性角度分析。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p2@T1；s5-d0-t1-02-memo#p3@T1；s5-d0-t1-02-summary#p3@T1
- 金标要点：即使原始数据无法验证，只要被多次引用并嵌入正式论述，便可能成为“事实”本身；由于原始报告的权威性已被广泛接受，修正数据并未引发足够关注，反而被归因于“样本偏差”或“测量误差”，反映出信息传播中的“确认偏误”现象。；尤其当新数据与既有叙事冲突时，往往面临更高的质疑门槛，导致认知滞后。；当一个数字被反复提及并嵌入主流话语，其真实性便逐渐让位于其象征意义。
- 词法前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d1-t1-03-memo#p1@T1 4.s5-d0-t1-02-memo#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d0-t1-02-report#p3@T1 7.s6-d3-t1-01-memo#p1@T1 8.s6-d3-t1-01-memo#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d0-t1-02-report#p3@T1 4.s6-d3-t1-01-memo#p3@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d0-t1-02-analysis#p3@T1 8.s7-d2-t1-04-data#p3@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s5-d1-t1-03-report#p3@T1
- 重排前 10：1.s5-d0-t1-02-memo#p3@T1 2.s5-d1-t1-03-note#p3@T1 3.s5-d1-t1-03-memo#p1@T1 4.s5-d0-t1-02-report#p3@T1 5.s5-d0-t1-02-analysis#p3@T1 6.s5-d1-t1-03-report#p3@T1 7.s7-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d2-t1-04-data#p3@T1 10.s6-d3-t1-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 103. `s5-d0-t1-02-q3`

- 问：通勤白皮书被政府简报引用时出现的“数据语义微调”，会怎样影响政策的科学性？请举例说明后果。
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-report#p2@T1；s5-d0-t1-02-report#p3@T1
- 金标要点：这种语义微调虽无恶意，却导致政策推演基础出现偏差；值得注意的是，该报告在发布后不久即被多家政府简报引用，作为制定“弹性工作制试点”政策的重要依据；有地方部门将“平均通勤时间”解释为“最常见通勤时长”，而原始定义实为“中位数时间”；其解释权便可能被重新分配。
- 词法前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d3-t1-05-report#p1@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d3-t1-05-analysis#p2@T1 5.s5-d0-t1-02-report#p1@T1 6.s5-d3-t1-05-memo#p1@T1 7.s5-d1-t1-03-report#p1@T1 8.s5-d0-t1-02-report#p3@T1 9.s5-d3-t1-05-report#p2@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d0-t1-02-report#p3@T1 3.s5-d0-t1-02-memo#p3@T1 4.s5-d3-t1-05-report#p2@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.s5-d0-t1-02-report#p1@T1 9.s7-d0-t1-02-brief#p2@T1 10.s5-d0-t1-02-analysis#p3@T1
- 重排前 10：1.s5-d0-t1-02-report#p2@T1 2.s5-d0-t1-02-memo#p3@T1 3.s5-d0-t1-02-report#p3@T1 4.s5-d3-t1-05-analysis#p2@T1 5.s5-d0-t1-02-report#p1@T1 6.s5-d3-t1-05-report#p2@T1 7.s5-d0-t1-02-summary#p1@T1 8.s7-d0-t1-02-brief#p2@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s5-d1-t1-03-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 104. `s5-d0-t1-02-q4`

- 问：关于通勤白皮书数据被重新诠释一事，材料认为引用公开数据除追溯源头外还要关注什么？民生报告一案又暴露了什么盲点？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-report#p3@T1；s5-d0-t1-02-analysis#p3@T1
- 金标要点：对公开数据的引用不仅需要追溯源头，更需关注其在不同语境下的再诠释过程，防止“数字神话”在制度层面固化。；此事件暴露了内部数据整合机制中的结构性盲点：权威性不等于准确性，一致性也不代表全面性。
- 词法前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-analysis#p3@T1 4.s5-d0-t1-02-report#p2@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d0-t1-02-memo#p1@T1 7.s5-d3-t1-05-memo#p1@T1 8.s5-d3-t1-05-report#p1@T1 9.s7-d2-t1-04-memo#p3@T1 10.s5-d1-t1-03-report#p1@T1
- 混合前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s5-d0-t1-02-analysis#p3@T1 5.s5-d0-t1-02-memo#p3@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d0-t1-02-memo#p1@T1 8.s7-d2-t1-04-memo#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.p1-cac-o16#p1@T1
- 重排前 10：1.s5-d0-t1-02-report#p3@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d0-t1-02-analysis#p3@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d2-t1-04-memo#p3@T1 7.s5-d0-t1-02-analysis#p2@T1 8.s5-d0-t1-02-memo#p3@T1 9.p1-cac-o16#p1@T1 10.s5-d0-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 105. `s5-d1-t1-03-q1`

- 问：在多个非官方渠道中流传的2018年消费者行为调查的核心结论，为何可能影响后续研究判断？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-memo#p1@T1；s5-d1-t1-03-memo#p2@T1；s5-d1-t1-03-memo#p3@T1
- 金标要点：尽管这一细节未在正式发布版本中说明，但在多份行业笔记中被反复提及，成为后续分析的重要参考依据；尽管原始数据已不再公开，但其核心结论被多次引用。；关于“线上购物渗透率”的统计值，在三份独立文档中分别记载为42%、46%和48%；这种不一致促使学者提出应谨慎对待二手引述，避免误读历史数据脉络
- 词法前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d0-t1-02-memo#p1@T1 3.s5-d3-t1-05-memo#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s5-d1-t1-03-summary#p1@T1 7.s5-d3-t1-05-report#p1@T1 8.s5-d1-t1-03-report#p2@T1 9.s1-d0-01-analysis#p2@T1 10.p1-colaw-governance-supervisor-js#p3@T1
- 混合前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d1-t1-03-report#p2@T1 3.s7-d2-t1-04-memo#p3@T1 4.s5-d1-t1-03-memo#p2@T1 5.s5-d0-t1-02-summary#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s5-d1-t1-03-summary#p1@T1 8.s6-d0-t1-01-channel#p1@T1 9.s5-d1-t1-03-summary#p3@T1 10.s7-d0-t1-02-brief#p2@T1
- 重排前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d0-t1-02-analysis#p2@T1 3.s5-d1-t1-03-summary#p1@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d1-t1-03-report#p2@T1 6.s5-d1-t1-03-memo#p2@T1 7.s5-d1-t1-03-summary#p3@T1 8.s7-d0-t1-02-brief#p2@T1 9.s7-d2-t1-04-memo#p3@T1 10.s5-d0-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 106. `s5-d1-t1-03-q2`

- 问：为什么说2019年白皮书中关于手机更换周期的数据虽然被广泛引用，但仍存在可靠性风险？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-report#p1@T1；s5-d1-t1-03-report#p2@T1
- 金标要点：值得注意的是，该数据源自一项2018年的小型调研，样本量仅为850人，且主要集中在一线城市；该报告指出，用户平均更换手机的时间为2.7年，这一数字在后续三年内被多次复述，甚至成为政策制定者的参考基准。；由于缺乏更新的权威数据，许多研究直接沿用此数值，未加批判性评估，导致长期形成认知惯性。
- 词法前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d0-t1-02-report#p1@T1 3.s5-d0-t1-02-memo#p1@T1 4.s5-d3-t1-05-report#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d3-t1-05-analysis#p2@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d0-t1-02-memo#p2@T1 9.s5-d1-t1-03-memo#p1@T1 10.s4-d2-t1-04-memo#p2@T1
- 混合前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d3-t1-05-analysis#p2@T1 3.s5-d3-t1-05-report#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s5-d3-t1-05-report#p2@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-claim#p3@T1 9.s5-d1-t1-03-note#p1@T1 10.s6-d3-t1-01-note#p3@T1
- 重排前 10：1.s5-d1-t1-03-report#p1@T1 2.s5-d3-t1-05-analysis#p2@T1 3.s5-d3-t1-05-report#p1@T1 4.s5-d3-t1-05-memo#p2@T1 5.s5-d1-t1-03-memo#p1@T1 6.s5-d1-t1-03-note#p1@T1 7.s5-d0-t1-02-memo#p3@T1 8.s5-d3-t1-05-report#p2@T1 9.s7-d0-t1-02-claim#p3@T1 10.s6-d3-t1-01-note#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 107. `s5-d1-t1-03-q3`

- 问：那份记录2015年市场反馈的内部备忘录，其数据是怎样经非正式渠道被当作正式成果的？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-note#p1@T1；s5-d1-t1-03-note#p2@T1
- 金标要点：一份2017年的项目备忘录提到，某部门曾收集2015年市场反馈数据，用于支持战略规划；在2021年的审计审查中发现，其中一份内部幻灯片将原始数据中的“满意度得分”从3.4夸大至4.1；该数据集虽未正式对外公布，但通过邮件流转，被多个团队间接引用，形成了隐性的信息传播网络。；其中一份内部幻灯片将原始数据中的“满意度得分”从3.4夸大至4.1，理由是“符合预期目标”；此类微调虽未改变整体趋势，却在后续汇报中被当作真实成果展示，引发信任危机。
- 词法前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-note#p2@T1 3.s7-d0-t1-02-claim#p3@T1 4.s5-d1-t1-03-memo#p1@T1 5.s2-d3-01-memo#p1@T1 6.s5-d0-t1-02-analysis#p2@T1 7.s6-d0-t1-02-report#p2@T1 8.s7-d0-t1-02-brief#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s6-d0-t1-02-memo#p2@T1
- 混合前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-memo#p2@T1 8.s5-d3-t1-05-analysis#p3@T1 9.s2-d3-01-memo#p1@T1 10.s1-d1-t1-91-memo#p2@T1
- 重排前 10：1.s5-d1-t1-03-note#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s5-d0-t1-02-analysis#p2@T1 4.s6-d0-t1-02-report#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s2-d3-01-memo#p1@T1 7.s5-d1-t1-03-memo#p2@T1 8.s5-d3-t1-05-analysis#p3@T1 9.s5-d0-t1-02-summary#p1@T1 10.s1-d1-t1-91-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 108. `s5-d1-t1-03-q4`

- 问：当多份来源对同一事件的描述存在数值差异时，应采取何种方法确保汇编叙述的可信度？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d1-t1-03-summary#p2@T1；s5-d1-t1-03-summary#p3@T1
- 金标要点：经交叉验证，发现前者包含了预注册人数，后者仅统计现场出席者；最终研究团队决定采用“分层标注法”，对每条信息注明其来源类型与潜在偏见
- 词法前 10：1.s5-d1-t1-03-memo#p3@T1 2.s5-d0-t1-02-analysis#p3@T1 3.s7-d2-t1-04-brief#p3@T1 4.s7-d0-t1-02-brief#p3@T1 5.s6-d3-t1-01-note#p2@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d0-t1-02-memo#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d0-t1-02-claim#p2@T1 10.s5-d1-t1-03-summary#p3@T1
- 混合前 10：1.s5-d0-t1-02-analysis#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s5-d1-t1-03-memo#p3@T1 4.s7-d2-t1-04-data#p3@T1 5.s7-d0-t1-02-analysis#p3@T1 6.s6-d3-t1-01-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s7-d2-t1-04-claim#p3@T1 9.s5-d1-t1-03-summary#p3@T1 10.s6-d3-t1-01-memo#p2@T1
- 重排前 10：1.s5-d0-t1-02-analysis#p3@T1 2.s5-d1-t1-03-memo#p3@T1 3.s7-d2-t1-04-brief#p3@T1 4.s7-d2-t1-04-claim#p3@T1 5.s5-d1-t1-03-summary#p3@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s6-d3-t1-01-memo#p3@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 109. `s5-d2-t0-04-q1`

- 问：三份二手交易材料各自给出了哪些增长数字？它们是否引用了同一个数据点？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-memo#p1@T0；s5-d2-t0-04-analysis#p1@T0；s5-d2-t0-04-report#p2@T0；s5-d2-t0-04-memo#p3@T0
- 金标要点：全国二手交易市场在2019年至2020年间年均增长率达17.3%；二手商品成交额在当年第四季度环比增长26.5%；2021年“二手”相关话题在微博上的讨论量同比增长35%；线上二手平台用户活跃度较前一年提升约22%
- 词法前 10：1.s5-d2-t0-04-report#p3@T0 2.s7-d0-t0-01-qa#p2@T0 3.s7-d0-t0-01-qa#p1@T0 4.s5-d2-t0-04-memo#p1@T0 5.p1-cac-o11#p4@T0 6.s4-d0-t0-01-memo#p1@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s7-d0-t0-01-memo#p1@T0 9.p1-cac-o11#p5@T0 10.s5-d2-t0-04-analysis#p3@T0
- 混合前 10：1.s5-d2-t0-04-memo#p1@T0 2.s5-d2-t0-04-report#p3@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s1-d3-t0-91-memo#p1@T0 5.s5-d2-t0-04-analysis#p3@T0 6.s5-d1-t0-91-repost#p3@T0 7.s5-d2-t0-04-report#p2@T0 8.s5-d2-t0-04-analysis#p1@T0 9.s2-d0-03-memo#p2@T0 10.s5-d2-t0-04-report#p1@T0
- 重排前 10：1.s5-d2-t0-04-report#p3@T0 2.s5-d2-t0-04-memo#p1@T0 3.s5-d2-t0-04-analysis#p2@T0 4.s1-d3-t0-91-memo#p1@T0 5.s5-d2-t0-04-analysis#p3@T0 6.s5-d2-t0-04-report#p2@T0 7.s5-d2-t0-04-analysis#p1@T0 8.s2-d0-03-memo#p2@T0 9.s5-d1-t0-91-repost#p3@T0 10.s5-d2-t0-04-report#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 110. `s5-d2-t0-04-q2`

- 问：在二手交易相关材料里，哪些文档提到了未公开的内部数据？这些内容为什么被当作参考？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-analysis#p1@T0；s5-d2-t0-04-analysis#p3@T0；s5-d2-t0-04-memo#p1@T0
- 金标要点：此数据未对外公布，但在跨部门会议纪要中被提及，并成为后续策略调整的依据之一。；该信息未进入正式文档体系，但在团队交流中频繁被引用，形成隐性共识。；尽管原始报告未公开，但其结论在若干非正式渠道中广泛流传。
- 词法前 10：1.s5-d2-t0-04-report#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-analysis#p3@T0 4.s5-d2-t0-04-memo#p1@T0 5.s5-d1-t0-91-repost#p1@T0 6.s7-d0-t0-01-arch#p2@T0 7.s5-d2-t0-04-report#p2@T0 8.s7-d1-t0-03-memo#p3@T0 9.s2-d2-t0-91-callnotes#p2@T0 10.s4-d0-t0-01-memo#p1@T0
- 混合前 10：1.s5-d2-t0-04-analysis#p2@T0 2.s5-d2-t0-04-report#p3@T0 3.s5-d2-t0-04-memo#p1@T0 4.s5-d2-t0-04-analysis#p3@T0 5.s5-d2-t0-04-report#p2@T0 6.s7-d1-t0-03-memo#p3@T0 7.s5-d2-t0-04-analysis#p1@T0 8.s4-d0-t0-01-memo#p1@T0 9.s5-d2-t0-04-report#p1@T0 10.p1-cac-o11#p4@T0
- 重排前 10：1.s5-d2-t0-04-analysis#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-report#p3@T0 4.s5-d2-t0-04-memo#p1@T0 5.s5-d2-t0-04-report#p2@T0 6.s5-d2-t0-04-analysis#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.p1-cac-o11#p4@T0 9.s7-d1-t0-03-memo#p3@T0 10.s5-d2-t0-04-report#p1@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 111. `s5-d2-t0-04-q3`

- 问：三份文档如何处理未经证实或来源模糊的信息？请举例说明。
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d2-t0-04-analysis#p3@T0；s5-d2-t0-04-memo#p1@T0；s5-d2-t0-04-memo#p3@T0；s5-d2-t0-04-report#p1@T0；s5-d2-t0-04-report#p2@T0
- 金标要点：尽管原始报告未公开，但其结论在若干非正式渠道中广泛流传。；这一趋势被部分媒体归因于疫情推动的居家消费习惯变化，但缺乏直接数据支持。；该报告虽无官方背书，但被多家自媒体转载并作为论据使用。；尽管该数据来源未提供完整统计口径，仍被用于佐证市场热度。；该信息未进入正式文档体系，但在团队交流中频繁被引用，形成隐性共识。
- 词法前 10：1.s7-d0-t0-01-qa#p1@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s7-d0-t0-01-qa#p3@T0 4.s5-d2-t0-04-analysis#p3@T0 5.s1-d3-01-report#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s7-d1-t0-03-claim#p1@T0 8.s7-d0-t0-01-report#p1@T0 9.s7-d0-t0-01-arch#p3@T0 10.s3-d1-01-memo#p2@T0
- 混合前 10：1.s7-d0-t0-01-qa#p3@T0 2.s7-d1-t0-03-fact#p3@T0 3.s4-d3-t0-05-summary#p3@T0 4.s7-d0-t0-01-report#p1@T0 5.s7-d0-t0-01-internal#p3@T0 6.s7-d0-t0-01-arch#p3@T0 7.s5-d2-t0-04-analysis#p2@T0 8.s5-d2-t0-04-analysis#p3@T0 9.s7-d0-t0-01-qa#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-qa#p3@T0 2.s5-d2-t0-04-analysis#p2@T0 3.s5-d2-t0-04-analysis#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d1-t0-03-fact#p3@T0 6.s4-d3-t0-05-summary#p3@T0 7.s7-d0-t0-01-report#p1@T0 8.s7-d0-t0-01-internal#p3@T0 9.s7-d0-t0-01-arch#p3@T0 10.s7-d1-t0-03-memo#p3@T0
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 112. `s5-d3-t1-05-q1`

- 问：在2022年与2023年间，某城市公共交通使用率的变化情况如何？有哪些因素导致了信息滞后？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-memo#p1@T1；s5-d3-t1-05-memo#p2@T1
- 金标要点：在2022年的一项研究中，某机构对城市居民的通勤模式进行了调查，结果显示约43%的人每日乘坐公共交通工具；2023年另一项独立调查显示，使用公共交通的比例上升至51%，但该结果未被广泛传播；部分媒体和报告仍沿用旧数据，导致公众对实际变化产生误判，形成认知偏差。
- 词法前 10：1.s5-d3-t1-05-memo#p2@T1 2.s5-d3-t1-05-memo#p3@T1 3.s5-d3-t1-05-memo#p1@T1 4.p1-cac-o16#p11@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s5-d1-t1-03-memo#p1@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d0-t1-02-report#p1@T1 9.s5-d0-t1-02-memo#p3@T1 10.s5-d1-t1-03-report#p2@T1
- 混合前 10：1.s5-d3-t1-05-memo#p2@T1 2.s5-d3-t1-05-memo#p1@T1 3.s5-d3-t1-05-memo#p3@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d3-t1-05-report#p2@T1 6.s5-d0-t1-02-summary#p1@T1 7.s2-d0-03-memo#p2@T1 8.s5-d0-t1-02-analysis#p1@T1 9.s5-d0-t1-02-memo#p1@T1 10.s5-d1-t1-03-report#p2@T1
- 重排前 10：1.s5-d3-t1-05-memo#p3@T1 2.s5-d3-t1-05-memo#p2@T1 3.s5-d3-t1-05-memo#p1@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d0-t1-02-analysis#p1@T1 6.s5-d0-t1-02-memo#p1@T1 7.s5-d1-t1-03-report#p2@T1 8.s5-d3-t1-05-report#p2@T1 9.s5-d0-t1-02-summary#p1@T1 10.s2-d0-03-memo#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 113. `s5-d3-t1-05-q2`

- 问：以公交使用率、制造业占比和员工满意度为例，为何新数据出现后旧统计仍被政策文件广泛引用？反映了什么问题？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p2@T1；s5-d3-t1-05-report#p2@T1；s5-d3-t1-05-memo#p2@T1
- 金标要点：事实固化；数据惯性；但该结果未被广泛传播；部分媒体和报告仍沿用旧数据，导致公众对实际变化产生误判，形成认知偏差。；但多数地方政府报告仍沿用旧值，造成政策目标与现实脱节。；管理层对此类引用持默许态度，认为其具有稳定预期的作用。
- 词法前 10：1.s5-d3-t1-05-report#p1@T1 2.s1-d0-02-report#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s1-d0-01-memo#p2@T1 5.s5-d1-t1-03-report#p1@T1 6.s2-d0-04-memo#p1@T1 7.s5-d3-t1-05-memo#p1@T1 8.s6-d3-t1-01-memo#p2@T1 9.p1-cac-o11#p4@T1 10.s5-d3-t1-05-analysis#p1@T1
- 混合前 10：1.s5-d3-t1-05-memo#p1@T1 2.s5-d3-t1-05-analysis#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s1-d0-02-report#p1@T1 5.s5-d0-t1-02-analysis#p1@T1 6.s5-d3-t1-05-report#p2@T1 7.s5-d3-t1-05-memo#p2@T1 8.s6-d3-t1-91-changelog#p1@T1 9.s5-d0-t1-02-memo#p1@T1 10.s5-d3-t1-05-memo#p3@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d3-t1-05-memo#p1@T1 3.s5-d3-t1-05-analysis#p2@T1 4.s5-d0-t1-02-analysis#p1@T1 5.s5-d3-t1-05-analysis#p1@T1 6.s1-d0-02-report#p1@T1 7.s5-d3-t1-05-report#p2@T1 8.s5-d3-t1-05-memo#p2@T1 9.s5-d3-t1-05-memo#p3@T1 10.s6-d3-t1-91-changelog#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 114. `s5-d3-t1-05-q3`

- 问：离职面谈与匿名反馈交叉分析后，发现了哪项没写进正式报告的员工侧趋势？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p3@T1
- 金标要点：通过对离职面谈记录与匿名反馈系统的交叉分析，可识别出员工对远程办公支持度的显著提升；可识别出员工对远程办公支持度的显著提升，这一趋势虽未体现在正式报告中，但已被高层视为关键管理改进方向。
- 词法前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s7-d2-t1-04-claim#p3@T1 3.s5-d1-t1-03-memo#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s4-d2-t1-04-report#p1@T1 6.s5-d3-t1-05-memo#p3@T1 7.s5-d1-t1-03-note#p1@T1 8.s5-d1-t1-03-memo#p1@T1 9.s4-d0-t1-02-plan#p1@T1 10.s7-d0-t1-02-memo#p1@T1
- 混合前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s5-d1-t1-03-memo#p2@T1 3.s5-d1-t1-03-note#p1@T1 4.s5-d1-t1-03-memo#p1@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d0-t1-02-memo#p1@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p3@T1 2.s7-d2-t1-04-claim#p3@T1 3.s5-d1-t1-03-memo#p2@T1 4.s5-d1-t1-03-note#p1@T1 5.s5-d1-t1-03-memo#p1@T1 6.s7-d0-t1-02-memo#p1@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d0-t1-03-internal#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 115. `s6-d0-t1-01-q1`

- 问：顾问备忘中复验窗口的最新调整是什么？旧窗口如何处理？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-memo#p1@T1
- 金标要点：顾问备忘中关于复验窗口的调整已正式生效，原定两周的复验周期现已延长至三周；旧版中的两周窗口仅保留用于历史对照参考，不再作为现行标准执行
- 词法前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d1-t1-91-patch#p1@T1 4.s6-d3-t1-01-note#p1@T1 5.s1-d1-t1-91-memo#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s1-d0-03-memo#p1@T1 8.s6-d3-t1-01-memo#p1@T1 9.s6-d3-t1-02-memo#p2@T1 10.s6-d0-t1-91-change#p1@T1
- 混合前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d3-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p1@T1 5.s6-d3-t1-01-note#p2@T1 6.s6-d3-t1-02-report#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s6-d3-t1-01-memo#p1@T1 9.s1-d1-t1-91-memo#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 重排前 10：1.s6-d0-t1-01-memo#p1@T1 2.s6-d0-t1-01-patch#p1@T1 3.s6-d3-t1-01-note#p1@T1 4.s6-d3-t1-02-memo#p2@T1 5.s6-d3-t1-02-report#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s6-d3-t1-01-memo#p1@T1 8.s1-d1-t1-91-memo#p2@T1 9.s6-d3-t1-01-note#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 116. `s6-d0-t1-01-q2`

- 问：渠道纪要中关于口头折扣的信息发生了什么位置变动？原因是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-channel#p1@T1
- 金标要点：渠道纪要中涉及口头折扣的条款已从主文迁移至附录，此举旨在分离操作细节与核心政策声明，避免信息冗余影响关键判断的传达效率。
- 词法前 10：1.s6-d0-t1-01-channel#p1@T1 2.s6-d0-t1-01-memo#p2@T1 3.s6-d0-t1-02-internal#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-report#p2@T1 6.s2-d3-t1-91-minutes#p1@T1 7.s5-d1-t1-03-memo#p1@T1 8.s5-d0-t1-02-memo#p1@T1 9.s2-d0-03-memo#p1@T1 10.s6-d0-t1-02-memo#p2@T1
- 混合前 10：1.s6-d0-t1-01-channel#p1@T1 2.s6-d0-t1-01-memo#p2@T1 3.s6-d0-t1-02-internal#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-report#p2@T1 6.s5-d1-t1-03-memo#p1@T1 7.s6-d0-t1-02-memo#p2@T1 8.s2-d0-03-memo#p1@T1 9.s6-d3-t1-03-memo#p3@T1 10.s2-d0-01-report#p3@T1
- 重排前 10：1.s6-d0-t1-01-channel#p1@T1 2.s5-d1-t1-03-memo#p1@T1 3.s6-d0-t1-01-memo#p2@T1 4.s6-d0-t1-02-internal#p2@T1 5.s6-d0-t1-02-memo#p2@T1 6.s6-d3-t1-03-memo#p2@T1 7.s6-d3-t1-03-report#p2@T1 8.s2-d0-03-memo#p1@T1 9.s6-d3-t1-03-memo#p3@T1 10.s2-d0-01-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 117. `s6-d0-t1-01-q3`

- 问：战略判断的结论段目前处于什么状态？为何不再标记为已签发？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-01-memo#p3@T1
- 金标要点：战略判断部分的结论段落已更新为“待复验”状态，不再以“已签发”形式呈现，反映当前评估仍需进一步验证，确保风险控制闭环完整。
- 词法前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s6-d0-t1-03-internal#p1@T1 5.s6-d3-t1-02-summary#p3@T1 6.s1-d0-05-warn#p1@T1 7.s2-d3-01-memo#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s2-d3-01-interview#p1@T1 10.s5-d1-t1-03-memo#p1@T1
- 混合前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s1-d0-03-memo#p1@T1 5.s1-d0-05-memo#p1@T1 6.s1-d0-05-warn#p1@T1 7.s2-d3-01-interview#p1@T1 8.s6-d0-t1-03-internal#p1@T1 9.s2-d0-02-interview#p1@T1 10.s7-d0-t1-02-claim#p2@T1
- 重排前 10：1.s6-d0-t1-01-memo#p3@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-report#p3@T1 4.s1-d0-05-warn#p1@T1 5.s6-d0-t1-03-internal#p1@T1 6.s1-d0-03-memo#p1@T1 7.s1-d0-05-memo#p1@T1 8.s2-d3-01-interview#p1@T1 9.s7-d0-t1-02-claim#p2@T1 10.s2-d0-02-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 118. `s6-d0-t1-02-q1`

- 问：供应商交付周期从四周改为六周后，这一变更分别被同步到了哪些工具或排期里？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-internal#p1@T1；s6-d0-t1-02-memo#p1@T1；s6-d0-t1-02-report#p1@T1
- 金标要点：系统上线计划也已重新排期；该变更已录入项目管理工具，影响范围覆盖所有依赖模块。；该调整已在本周内部通报，并同步更新至项目排期表。
- 词法前 10：1.s6-d0-t1-02-internal#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s1-d0-02-report#p2@T1 5.s6-d0-t1-91-change#p1@T1 6.s6-d3-t1-02-summary#p2@T1 7.s6-d1-c2-memo#p3@T1 8.s6-d0-t1-03-internal#p1@T1 9.s6-d0-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p2@T1
- 混合前 10：1.s6-d0-t1-02-report#p1@T1 2.s6-d0-t1-02-internal#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d3-t1-02-summary#p2@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-91-change#p1@T1 7.s2-d1-01-memo#p1@T1 8.s6-d3-t1-02-report#p2@T1 9.s6-d3-t1-02-memo#p2@T1 10.s6-d0-t1-01-patch#p2@T1
- 重排前 10：1.s6-d0-t1-02-internal#p1@T1 2.s6-d0-t1-02-report#p1@T1 3.s6-d0-t1-02-memo#p1@T1 4.s6-d3-t1-02-summary#p2@T1 5.s1-d0-02-report#p2@T1 6.s6-d0-t1-91-change#p1@T1 7.s6-d0-t1-01-patch#p2@T1 8.s2-d1-01-memo#p1@T1 9.s6-d3-t1-02-report#p2@T1 10.s6-d3-t1-02-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 119. `s6-d0-t1-02-q2`

- 问：渠道纪要中关于对手入门档产品的最新说法是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-internal#p2@T1；s6-d0-t1-02-memo#p2@T1；s6-d0-t1-02-report#p2@T1
- 金标要点：渠道纪要中新增信息：对手入门档产品已停止销售，当前无直接竞争压力，建议加快市场推广节奏；渠道方面，新增一条对手产品线的动态信息：其入门档型号已于上季度末正式停售，目前市场中无同级竞品可替代；渠道反馈补充指出，此前误传的对手入门档仍在售信息已被更正，实际该产品线已全面下架
- 词法前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d3-t1-02-memo#p1@T1 6.s6-d0-t1-01-channel#p1@T1 7.s2-d3-t1-91-minutes#p1@T1 8.s2-d0-04-memo#p2@T1 9.s6-d0-t1-02-memo#p1@T1 10.s6-d0-t1-02-report#p1@T1
- 混合前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s6-d3-t1-02-memo#p1@T1 7.s2-d2-01-memo#p1@T1 8.s2-d0-01-memo#p1@T1 9.s6-d3-t1-02-summary#p1@T1 10.s6-d0-t1-02-memo#p1@T1
- 重排前 10：1.s6-d0-t1-02-internal#p2@T1 2.s6-d0-t1-02-report#p2@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s2-d2-01-memo#p1@T1 7.s6-d3-t1-02-memo#p1@T1 8.s2-d0-01-memo#p1@T1 9.s6-d0-t1-02-memo#p1@T1 10.s6-d3-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 120. `s6-d0-t1-02-q3`

- 问：项目负责人从甲组调到乙组这件事，会议记录里是怎么写的？乙组接手后负责什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-02-memo#p3@T1
- 金标要点：原由甲组负责的项目推进工作现已移交至乙组；乙组将全面接管后续协调与执行任务
- 词法前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d0-t1-03-internal#p1@T1 6.s6-d0-t1-91-sop#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-t1-91-interview#p2@T1 9.s4-d0-t1-02-guide#p2@T1 10.s6-d0-t1-03-report#p1@T1
- 混合前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s6-d3-t1-02-summary#p3@T1 5.s4-d2-t1-04-internal#p3@T1 6.s6-d2-g3-memo#p3@T1 7.s6-d0-t1-03-internal#p1@T1 8.s2-d0-t1-91-memo#p1@T1 9.s2-d0-t1-91-interview#p2@T1 10.p1-colaw-capital-call#p1@T1
- 重排前 10：1.s6-d0-t1-02-memo#p3@T1 2.s6-d0-t1-02-report#p3@T1 3.s6-d0-t1-02-internal#p3@T1 4.s6-d0-t1-03-internal#p1@T1 5.s6-d2-g3-memo#p3@T1 6.s2-d0-t1-91-interview#p2@T1 7.s6-d3-t1-02-summary#p3@T1 8.s4-d2-t1-04-internal#p3@T1 9.s2-d0-t1-91-memo#p1@T1 10.p1-colaw-capital-call#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 121. `s6-d0-t1-03-q1`

- 问：在最新的成本测算中，外包单价是否仍被使用？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-memo#p1@T1；s6-d0-t1-03-internal#p1@T1；s6-d0-t1-03-report#p1@T1
- 金标要点：内部测算把外包单价从上一版模型里撤下，以避免误导后续成本评估；内部测算把外包单价从上一版模型里撤下，该字段已被标记为过时，后续分析将基于更新后的参数集；内部测算把外包单价从上一版模型里撤下，确保当前评估不依赖已废弃的数据字段，防止误用历史偏差影响决策；该调整已同步至最新数据管道，确保分析基准的一致性。
- 词法前 10：1.s6-d0-t1-03-memo#p1@T1 2.s6-d0-t1-03-internal#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d0-t1-03-report#p1@T1 5.s4-d2-t1-91-model-v3#p1@T1 6.s5-d1-t1-03-report#p1@T1 7.s7-d0-t1-02-update#p2@T1 8.s4-d0-t1-02-memo#p1@T1 9.s2-d2-01-memo#p1@T1 10.s3-d3-01-report#p3@T1
- 混合前 10：1.s6-d0-t1-03-memo#p1@T1 2.s6-d0-t1-03-internal#p1@T1 3.s6-d0-t1-03-report#p1@T1 4.s4-d2-t1-91-model-v3#p1@T1 5.s3-d3-01-report#p3@T1 6.s4-d2-t1-04-report#p1@T1 7.s3-d2-01-competitor-pricing#p1@T1 8.s2-d0-02-interview#p3@T1 9.s4-d0-t1-02-memo#p1@T1 10.s3-d3-01-report#p2@T1
- 重排前 10：1.s6-d0-t1-03-memo#p1@T1 2.s4-d0-t1-02-memo#p1@T1 3.s6-d0-t1-03-internal#p1@T1 4.s4-d2-t1-04-report#p1@T1 5.s2-d0-02-interview#p3@T1 6.s6-d0-t1-03-report#p1@T1 7.s4-d2-t1-91-model-v3#p1@T1 8.s3-d3-01-report#p3@T1 9.s3-d2-01-competitor-pricing#p1@T1 10.s3-d3-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 122. `s6-d0-t1-03-q3`

- 问：报价单里的打包项改成分行列出后，三份材料各自说这样做是为了什么？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d0-t1-03-internal#p3@T1；s6-d0-t1-03-memo#p3@T1；s6-d0-t1-03-report#p3@T1
- 金标要点：符合最新合规披露要求；提升明细可读性并支持独立定价校验；为未来自动化比价提供结构化基础
- 词法前 10：1.s4-d0-t1-91-deck#p3@T1 2.s2-d0-t1-91-memo#p1@T1 3.s6-d0-t1-91-sop#p2@T1 4.s6-d3-t1-01-report#p2@T1 5.s6-d3-t1-91-changelog#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s1-d1-t1-91-memo#p2@T1 8.s2-d0-t1-91-interview#p2@T1 9.s7-d3-t1-05-synthetic#p2@T1 10.s4-d2-t1-91-model-v3#p2@T1
- 混合前 10：1.s6-d0-t1-03-internal#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s6-d0-t1-03-report#p3@T1 4.s3-d2-t1-91-contract#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s6-d0-t1-03-internal#p3@T1 7.s6-d0-t1-03-memo#p3@T1 8.s6-d3-t1-01-report#p2@T1 9.s6-d0-t1-03-report#p1@T1 10.s6-d0-t1-03-memo#p1@T1
- 重排前 10：1.s6-d0-t1-03-internal#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s3-d2-t1-91-contract#p1@T1 4.s6-d0-t1-03-report#p3@T1 5.s6-d3-t1-01-report#p2@T1 6.s6-d0-t1-03-report#p1@T1 7.s6-d0-t1-03-memo#p1@T1 8.s3-d2-t1-91-contract#p3@T1 9.s6-d0-t1-03-internal#p3@T1 10.s6-d0-t1-03-memo#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 123. `s6-d1-c1-q1`

- 问：出境评估结论现在的有效期是多长？满足什么条件可以续期，续期能延多久？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p9@T1；s6-d1-c1-memo#p1@T1；s6-d1-c1-memo#p2@T1
- 金标要点：通过数据出境安全评估的结果有效期为3年，自评估结果出具之日起计算。；有效期届满，需要继续开展数据出境活动且未发生需要重新申报数据出境安全评估情形的，数据处理者可以在有效期届满前60个工作日内通过所在地省级网信部门向国家网信部门提出延长评估结果有效期申请。；经国家网信部门批准，可以延长评估结果有效期3年。
- 词法前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.p1-cac-o11#p12@T1 4.s6-d1-c3-memo#p2@T1 5.s6-d1-c1-memo#p1@T1 6.p1-cac-o11#p14@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d1-c1-memo#p2@T1 9.p1-cac-o16#p6@T1 10.s6-d1-c1-memo#p3@T1
- 混合前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.s6-d1-c1-memo#p1@T1 4.s6-d1-c1-memo#p2@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o11#p14@T1 7.p1-cac-o11#p12@T1 8.s6-d1-c1-memo#p3@T1 9.p1-cac-o11#p11@T1 10.p1-cac-o11#p15@T1
- 重排前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p13@T1 3.s6-d1-c1-memo#p1@T1 4.p1-cac-o11#p14@T1 5.p1-cac-o11#p12@T1 6.p1-cac-o11#p11@T1 7.s6-d1-c1-memo#p2@T1 8.s6-d1-c3-memo#p2@T1 9.s6-d1-c1-memo#p3@T1 10.p1-cac-o11#p15@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 124. `s6-d1-c1-q2-new`

- 问：出境评估结论原先管两年，现在能管几年？到期前多久可以申请续期？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o11#p13@T1；p1-cac-o16#p9@T1
- 金标要点：通过数据出境安全评估的结果有效期为2年；通过数据出境安全评估的结果有效期为3年；可以在有效期届满前60个工作日内通过所在地省级网信部门向国家网信部门提出延长评估结果有效期申请
- 词法前 10：1.p1-cac-o11#p12@T1 2.p1-cac-o16#p9@T1 3.s6-d1-c1-memo#p3@T1 4.s5-d2-t1-91-digest#p1@T1 5.s6-d1-c1-memo#p2@T1 6.p1-cac-o20#p6@T1 7.s1-d1-t1-91-memo#p1@T1 8.p1-cac-o20#p4@T1 9.p1-cac-o16#p6@T1 10.s6-d3-t1-02-memo#p3@T1
- 混合前 10：1.p1-cac-o16#p9@T1 2.s6-d1-c1-memo#p2@T1 3.s6-d1-c1-memo#p3@T1 4.p1-cac-o11#p12@T1 5.p1-cac-o11#p11@T1 6.p1-cac-o11#p15@T1 7.p1-cac-o13#p8@T1 8.p1-cac-o11#p17@T1 9.p1-cac-o11#p13@T1 10.s6-d3-t1-02-memo#p3@T1
- 重排前 10：1.p1-cac-o16#p9@T1 2.p1-cac-o11#p12@T1 3.s6-d1-c1-memo#p2@T1 4.s6-d1-c1-memo#p3@T1 5.p1-cac-o11#p11@T1 6.p1-cac-o11#p15@T1 7.p1-cac-o13#p8@T1 8.p1-cac-o11#p17@T1 9.p1-cac-o11#p13@T1 10.s6-d3-t1-02-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 125. `s6-d1-c2-q1`

- 问：不属于关基的企业，出境个人信息到多少人才需要报评估？这条线和以前比有什么不同？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p7@T1；p1-cac-o11#p2@T1；s6-d1-c2-memo#p1@T1；s6-d1-c2-memo#p2@T1；s6-d1-c2-memo#p3@T1
- 金标要点：关键信息基础设施运营者以外的数据处理者向境外提供重要数据，或者自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）或者1万人以上敏感个人信息；自上年1月1日起累计向境外提供10万人个人信息或者1万人敏感个人信息的数据处理者向境外提供个人信息；此次更新把一般个人信息的申报线从10万人提高到100万人，统计起点由上年改为当年，实际放宽了一般运营者的申报义务；敏感个人信息仍以1万人为线
- 词法前 10：1.p1-cac-o16#p6@T1 2.p1-cac-o16#p2@T1 3.p1-cac-o16#p3@T1 4.p1-cac-o13#p3@T1 5.s6-d1-c3-memo#p2@T1 6.p1-cac-o20#p3@T1 7.p1-cac-o11#p2@T1 8.p1-cac-o20#p5@T1 9.p1-cac-o16#p8@T1 10.p1-cac-o11#p13@T1
- 混合前 10：1.p1-cac-o20#p3@T1 2.s6-d1-c2-memo#p1@T1 3.p1-cac-o16#p2@T1 4.p1-cac-o11#p2@T1 5.p1-cac-o16#p3@T1 6.p1-cac-o16#p8@T1 7.p1-cac-o13#p3@T1 8.p1-cac-o16#p7@T1 9.s6-d1-c3-memo#p2@T1 10.s6-d1-c3-memo#p3@T1
- 重排前 10：1.p1-cac-o16#p2@T1 2.p1-cac-o11#p2@T1 3.p1-cac-o16#p7@T1 4.p1-cac-o20#p3@T1 5.s6-d1-c2-memo#p1@T1 6.p1-cac-o16#p3@T1 7.p1-cac-o16#p8@T1 8.p1-cac-o13#p3@T1 9.s6-d1-c3-memo#p2@T1 10.s6-d1-c3-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 126. `s6-d1-c3-q1`

- 问：标准合同的适用区间在新规下有何变化？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d1-c3-memo#p1@T1；p1-cac-o13#p2@T1；p1-cac-o16#p8@T1
- 金标要点：累计向境外提供10万人以上、不满100万人个人信息；不满1万人敏感个人信息；自上年1月1日起累计向境外提供个人信息不满10万人的
- 词法前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p1@T1 3.s6-d1-c3-memo#p3@T1 4.p1-cac-o13#p6@T1 5.s3-d2-t1-91-contract#p1@T1 6.s5-d2-t1-91-digest#p3@T1 7.p1-cac-o16#p11@T1 8.p1-cac-o13#p5@T1 9.s6-d1-c3-memo#p2@T1 10.p1-cac-o13#p7@T1
- 混合前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p6@T1 3.p1-cac-o13#p5@T1 4.p1-cac-o13#p7@T1 5.p1-cac-o16#p11@T1 6.p1-cac-o13#p1@T1 7.s6-d1-c4-memo#p1@T1 8.s6-d2-g1-memo#p2@T1 9.s3-d2-t1-91-contract#p1@T1 10.s2-d0-t1-91-memo#p1@T1
- 重排前 10：1.s6-d1-c3-memo#p1@T1 2.p1-cac-o13#p6@T1 3.p1-cac-o13#p7@T1 4.p1-cac-o16#p11@T1 5.p1-cac-o13#p1@T1 6.s6-d1-c4-memo#p1@T1 7.s6-d2-g1-memo#p2@T1 8.s3-d2-t1-91-contract#p1@T1 9.p1-cac-o13#p5@T1 10.s2-d0-t1-91-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 127. `s6-d1-c4-q1`

- 问：令16新增的个人信息出境豁免，哪些主体能享受？要满足什么条件？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：p1-cac-o16#p4@T1；p1-cac-o16#p5@T1；s6-d1-c4-memo#p1@T1
- 金标要点：为订立、履行个人作为一方当事人的合同，如跨境购物、跨境寄递、跨境汇款、跨境支付、跨境开户、机票酒店预订、签证办理、考试服务等，确需向境外提供个人信息的；按照依法制定的劳动规章制度和依法签订的集体合同实施跨境人力资源管理，确需向境外提供员工个人信息的；紧急情况下为保护自然人的生命健康和财产安全，确需向境外提供个人信息的；关键信息基础设施运营者以外的数据处理者自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息）的。
- 词法前 10：1.s6-d1-c4-memo#p1@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p11@T1 4.p1-cac-o16#p4@T1 5.s6-d1-c1-memo#p1@T1 6.s6-d1-c3-memo#p1@T1 7.s6-d1-c2-memo#p3@T1 8.p1-cac-o20#p5@T1 9.p1-cac-o16#p3@T1 10.p1-cac-o20#p6@T1
- 混合前 10：1.s6-d1-c4-memo#p1@T1 2.p1-cac-o20#p6@T1 3.s6-d1-c3-memo#p2@T1 4.p1-cac-o16#p4@T1 5.p1-cac-o20#p5@T1 6.p1-cac-o16#p11@T1 7.p1-cac-o20#p8@T1 8.p1-cac-o13#p4@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o20#p4@T1
- 重排前 10：1.s6-d1-c4-memo#p1@T1 2.s6-d1-c3-memo#p2@T1 3.p1-cac-o16#p4@T1 4.p1-cac-o16#p11@T1 5.p1-cac-o20#p6@T1 6.p1-cac-o20#p5@T1 7.p1-cac-o20#p8@T1 8.p1-cac-o13#p4@T1 9.p1-cac-o20#p2@T1 10.p1-cac-o20#p4@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 128. `s6-d2-g1-q1`

- 问：根据2023年公司法，有限责任公司股东认缴出资的最长期限是什么？此前法律有何不同？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d2-g1-memo#p1@T1；p1-colaw-capital#p1@T1
- 金标要点：2018法第二十六条无此期限；全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足。
- 词法前 10：1.s6-d2-g1-memo#p1@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-liquidation#p4@T1 6.s6-d2-g2-memo#p2@T1 7.p1-colaw-capital#p4@T1 8.p1-colaw-capital-transition#p1@T1 9.s6-d2-g2-memo#p1@T1 10.p1-colaw-capital-call#p1@T1
- 混合前 10：1.s6-d2-g1-memo#p1@T1 2.p1-colaw-capital#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-transition#p1@T1 6.p1-colaw-capital-call#p1@T1 7.s6-d2-g1-memo#p2@T1 8.s6-d2-g2-memo#p2@T1 9.s6-d2-g2-memo#p1@T1 10.s6-d2-g3-memo#p1@T1
- 重排前 10：1.p1-colaw-capital#p1@T1 2.s6-d2-g1-memo#p1@T1 3.p1-colaw-capital-call#p4@T1 4.p1-colaw-capital-transition#p2@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g2-memo#p2@T1 7.s6-d2-g2-memo#p1@T1 8.p1-colaw-capital-call#p1@T1 9.s6-d2-g1-memo#p2@T1 10.s6-d2-g3-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 129. `s6-d2-g2-q1`

- 问：新公司法（2023修订）的施行日期是什么？其第二百六十六条对出资期限有何要求？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d2-g2-memo#p1@T1；p1-colaw-capital-transition#p1@T1
- 金标要点：本法自2024年7月1日起施行；第二百六十六条要求出资期限超出法定上限的存量公司逐步调整到位；本法施行前已登记设立的公司，出资期限超过本法规定的期限的，除法律、行政法规或者国务院另有规定外，应当逐步调整至本法规定的期限以内
- 词法前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g1-memo#p2@T1 6.p1-cac-o16#p11@T1 7.s6-d2-g2-memo#p3@T1 8.p1-colaw-capital#p4@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital-call#p5@T1
- 混合前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p1@T1 4.s6-d2-g2-memo#p2@T1 5.s6-d2-g1-memo#p2@T1 6.s6-d2-g2-memo#p3@T1 7.p1-colaw-capital-call#p4@T1 8.p1-cac-o13#p8@T1 9.p1-colaw-capital-call#p5@T1 10.p1-colaw-capital#p3@T1
- 重排前 10：1.s6-d2-g2-memo#p1@T1 2.p1-colaw-capital-transition#p1@T1 3.s6-d2-g1-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.s6-d2-g2-memo#p2@T1 6.p1-colaw-capital-call#p5@T1 7.s6-d2-g1-memo#p1@T1 8.p1-colaw-capital-call#p4@T1 9.p1-colaw-capital#p3@T1 10.p1-cac-o13#p8@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 130. `s6-d2-g3-q1`

- 问：根据2023年最新法规，未按期出资的责任主体和责任形式发生了哪些变化？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p1@T1；p1-colaw-capital-call#p2@T1；p1-colaw-capital-call#p5@T1；p1-colaw-capital-transition#p2@T1；s6-d2-g3-memo#p1@T1
- 金标要点：由受让人承担缴纳该出资的义务；2018法向已足额出资股东承担违约责任；2023法改为对公司损失承担赔偿责任，并新增董事会核查催缴、宽限期不少于六十日后失权、加速到期、未届期转让由受让人缴纳。；股东未按期足额缴纳出资的，除应当向公司足额缴纳外，还应当对给公司造成的损失承担赔偿责任。；未及时履行前款规定的义务，给公司造成损失的，负有责任的董事应当承担赔偿责任。；宽限期自公司发出催缴书之日起，不得少于六十日。
- 词法前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.s5-d3-t1-05-memo#p2@T1 6.s6-d2-g3-memo#p2@T1 7.s6-d1-c1-memo#p2@T1 8.s6-d2-g3-memo#p3@T1 9.s6-d1-c1-memo#p1@T1 10.p1-cac-o11#p10@T1
- 混合前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.s6-d2-g3-memo#p2@T1 4.p1-colaw-capital-call#p5@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g3-memo#p3@T1 7.p1-colaw-capital-transition#p2@T1 8.p1-colaw-capital-call#p2@T1 9.s6-d1-c1-memo#p1@T1 10.s6-d2-g1-memo#p2@T1
- 重排前 10：1.s6-d2-g3-memo#p1@T1 2.p1-colaw-capital-call#p1@T1 3.p1-colaw-capital-call#p5@T1 4.p1-colaw-capital-transition#p2@T1 5.s6-d2-g3-memo#p2@T1 6.p1-colaw-capital-transition#p1@T1 7.s6-d2-g3-memo#p3@T1 8.s6-d1-c1-memo#p1@T1 9.s6-d2-g1-memo#p2@T1 10.p1-colaw-capital-call#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 131. `s6-d3-t1-01-q1`

- 问：在最新版本中，二手转述如何处理旧报价？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p1@T1；s6-d3-t1-01-note#p1@T1；s6-d3-t1-01-report#p1@T1
- 金标要点：二手转述把旧报价标成已过期，不再当现行口径
- 词法前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s6-d3-t1-01-report#p1@T1 4.s5-d1-t1-03-report#p3@T1 5.s6-d3-t1-02-report#p1@T1 6.s6-d0-t1-02-report#p1@T1 7.s2-d2-01-memo#p1@T1 8.s6-d0-t1-03-internal#p3@T1 9.s6-d3-t1-03-memo#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s6-d3-t1-01-report#p1@T1 4.s6-d0-t1-91-change#p1@T1 5.s5-d0-t1-02-memo#p3@T1 6.s5-d1-t1-03-report#p3@T1 7.s5-d0-t1-02-summary#p1@T1 8.s6-d3-t1-03-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-03-memo#p3@T1
- 重排前 10：1.s6-d3-t1-01-note#p1@T1 2.s6-d3-t1-01-memo#p1@T1 3.s5-d1-t1-03-report#p3@T1 4.s6-d3-t1-01-report#p1@T1 5.s5-d0-t1-02-memo#p3@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d3-t1-03-memo#p1@T1 8.s6-d0-t1-91-change#p1@T1 9.s5-d0-t1-02-summary#p1@T1 10.s6-d0-t1-03-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 132. `s6-d3-t1-01-q2`

- 问：汇编备注中的信息来源发生了什么变化？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p2@T1；s6-d3-t1-01-note#p2@T1；s6-d3-t1-01-report#p2@T1
- 金标要点：汇编备注把出处从访谈改成备忘附件，以反映信息来源的真实文件形式，增强可追溯性；汇编备注把出处从访谈改成备忘附件，体现对原始资料来源的规范标注；汇编备注把出处从访谈改成备忘附件，使原始材料定位更准确，便于后续查证
- 词法前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s6-d3-t1-01-report#p2@T1 4.s1-d0-03-memo#p2@T1 5.s5-d2-t1-91-digest#p3@T1 6.s5-d0-t1-02-analysis#p3@T1 7.p1-cac-o11#p10@T1 8.s7-d2-t1-04-claim#p3@T1 9.s5-d1-t1-03-summary#p3@T1 10.s5-d2-t1-91-digest#p1@T1
- 混合前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s6-d3-t1-01-report#p2@T1 4.s5-d2-t1-91-digest#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s5-d0-t1-02-summary#p3@T1 7.s5-d0-t1-02-summary#p1@T1 8.s5-d1-t1-03-summary#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s5-d1-t1-03-summary#p3@T1
- 重排前 10：1.s6-d3-t1-01-memo#p2@T1 2.s6-d3-t1-01-note#p2@T1 3.s5-d1-t1-03-summary#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-summary#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.s5-d2-t1-91-digest#p3@T1 9.s6-d3-t1-01-report#p2@T1 10.s5-d2-t1-91-digest#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 133. `s6-d3-t1-01-q3`

- 问：转述稿中关于份额的说法有何变动？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-01-memo#p3@T1；s6-d3-t1-01-note#p3@T1；s6-d3-t1-01-report#p3@T1
- 金标要点：转述稿删掉了未核实的份额说法，确保内容仅包含经确认的数据，提升整体可信度；转述稿删掉了未核实的份额说法，符合内容审核标准，强化信息可靠性；转述稿删掉了未核实的份额说法，保证输出内容基于可验证事实，减少推测成分
- 词法前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-report#p3@T1 3.s6-d3-t1-01-memo#p3@T1 4.s6-d0-t1-01-memo#p1@T1 5.s5-d0-t1-02-memo#p1@T1 6.s1-d0-01-memo#p2@T1 7.p1-cac-o20#p8@T1 8.p1-colaw-capital#p3@T1 9.s5-d1-t1-03-memo#p1@T1 10.s7-d2-t1-04-brief#p1@T1
- 混合前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-memo#p3@T1 3.s6-d3-t1-01-report#p3@T1 4.s6-d3-t1-01-note#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d3-t1-01-report#p1@T1 7.s6-d3-t1-01-memo#p1@T1 8.s5-d2-t1-91-digest#p1@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d1-t1-03-note#p3@T1
- 重排前 10：1.s6-d3-t1-01-note#p3@T1 2.s6-d3-t1-01-memo#p3@T1 3.s6-d3-t1-01-report#p3@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d1-t1-03-memo#p3@T1 6.s6-d3-t1-01-note#p1@T1 7.s6-d3-t1-01-memo#p1@T1 8.s5-d2-t1-91-digest#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s6-d3-t1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 134. `s6-d3-t1-02-q1`

- 问：补丁记录中对竞品入门档的最新状态是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p1@T1；s6-d3-t1-02-report#p1@T1；s6-d3-t1-02-summary#p1@T1
- 金标要点：补丁记录把竞品入门档标成停售，相关系统已同步更新状态；补丁记录把竞品入门档标成停售，此变更已在最新版本中生效，建议停止对该型号的市场推广活动；补丁记录把竞品入门档标成停售，系统标记已更新，影响范围涵盖所有对外展示与内部分析模块
- 词法前 10：1.s6-d3-t1-02-report#p1@T1 2.s6-d3-t1-02-memo#p1@T1 3.s6-d3-t1-02-summary#p1@T1 4.s6-d0-t1-02-memo#p2@T1 5.s6-d0-t1-02-internal#p2@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d3-t1-03-memo#p1@T1 8.s6-d0-t1-02-report#p2@T1 9.s2-d0-t1-91-interview#p2@T1 10.s5-d3-t1-05-analysis#p3@T1
- 混合前 10：1.s6-d3-t1-02-memo#p1@T1 2.s6-d3-t1-02-report#p1@T1 3.s6-d3-t1-02-summary#p1@T1 4.s6-d0-t1-02-memo#p2@T1 5.s6-d0-t1-02-internal#p2@T1 6.s6-d3-t1-03-report#p1@T1 7.s6-d0-t1-02-report#p2@T1 8.s6-d0-t1-02-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p1@T1
- 重排前 10：1.s6-d3-t1-02-report#p1@T1 2.s6-d3-t1-02-memo#p1@T1 3.s6-d0-t1-02-memo#p2@T1 4.s6-d3-t1-02-summary#p1@T1 5.s6-d3-t1-03-report#p1@T1 6.s6-d0-t1-02-internal#p2@T1 7.s6-d0-t1-02-report#p2@T1 8.s6-d0-t1-02-report#p1@T1 9.s6-d3-t1-03-memo#p1@T1 10.s6-d0-t1-01-patch#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 135. `s6-d3-t1-02-q3`

- 问：汇编中关于两份纪要的结论目前处于什么状态？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-02-memo#p3@T1；s6-d3-t1-02-report#p3@T1；s6-d3-t1-02-summary#p3@T1
- 金标要点：汇编把两份纪要的结论合成一条待核，当前尚未完成最终验证，需在下一周期前完成核实并归档；汇编把两份纪要的结论合成一条待核，目前处于待确认状态，暂不纳入正式决策依据；汇编把两份纪要的结论合成一条待核，当前状态为“待核实”，需指定负责人推进闭环处理
- 词法前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s6-d0-t1-01-memo#p3@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d0-t1-01-memo#p1@T1 7.s2-d3-01-memo#p2@T1 8.s5-d0-t1-02-analysis#p2@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d3-t1-91-minutes#p3@T1
- 混合前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s6-d0-t1-01-channel#p1@T1 5.s5-d1-t1-03-summary#p2@T1 6.s6-d0-t1-01-memo#p1@T1 7.s6-d0-t1-01-memo#p3@T1 8.s5-d2-t1-91-digest#p1@T1 9.s6-d3-t1-01-note#p2@T1 10.s5-d0-t1-02-analysis#p2@T1
- 重排前 10：1.s6-d3-t1-02-report#p3@T1 2.s6-d3-t1-02-summary#p3@T1 3.s6-d3-t1-02-memo#p3@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d0-t1-02-analysis#p2@T1 6.s6-d0-t1-01-channel#p1@T1 7.s6-d0-t1-01-memo#p1@T1 8.s6-d0-t1-01-memo#p3@T1 9.s5-d2-t1-91-digest#p1@T1 10.s6-d3-t1-01-note#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 136. `s6-d3-t1-03-q1`

- 问：补丁记录中关于旧成本模型的用途是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-03-memo#p1@T1；s6-d3-t1-03-report#p1@T1
- 金标要点：补丁记录注明旧成本模型只供对照，不得用于实际核算；补丁记录注明旧成本模型只供对照，用于对比分析新方案的效益差异，严禁在正式决策中引用
- 词法前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s6-d3-t1-02-memo#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s6-d3-t1-02-summary#p1@T1 7.s6-d0-t1-01-patch#p1@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s5-d1-t1-03-summary#p2@T1 10.s4-d0-t1-02-memo#p1@T1
- 混合前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s6-d3-t1-02-summary#p1@T1 5.s6-d3-t1-02-memo#p1@T1 6.s6-d0-t1-03-memo#p2@T1 7.s4-d2-t1-91-model-v3#p1@T1 8.s4-d0-t1-02-memo#p1@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d0-t1-02-plan#p1@T1
- 重排前 10：1.s6-d3-t1-03-report#p1@T1 2.s6-d3-t1-03-memo#p1@T1 3.s6-d3-t1-02-report#p1@T1 4.s4-d0-t1-02-memo#p1@T1 5.s4-d0-t1-02-analysis#p1@T1 6.s6-d3-t1-02-memo#p1@T1 7.s6-d0-t1-03-memo#p2@T1 8.s4-d2-t1-91-model-v3#p1@T1 9.s4-d0-t1-02-plan#p1@T1 10.s6-d3-t1-02-summary#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 137. `s6-d3-t1-03-q2`

- 问：变更说明中对渠道折扣的最新状态如何描述？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s6-d3-t1-03-memo#p2@T1；s6-d3-t1-03-report#p2@T1
- 金标要点：变更说明中将渠道折扣描述为已撤回，表明此前发布的折扣政策不再有效，相关合作方需依据现行协议执行；变更说明把渠道折扣写成已撤回，明确指出原定优惠机制已终止，相关客户需重新协商合作条款
- 词法前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-memo#p2@T1 4.s6-d3-t1-02-report#p1@T1 5.s6-d0-t1-01-channel#p1@T1 6.s6-d3-t1-02-report#p2@T1 7.s7-d0-t1-02-memo#p3@T1 8.s6-d3-t1-02-summary#p2@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d3-t1-02-memo#p2@T1
- 混合前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-channel#p1@T1 4.s6-d0-t1-01-memo#p2@T1 5.s6-d3-t1-02-summary#p2@T1 6.s6-d3-t1-02-report#p2@T1 7.s6-d3-t1-02-memo#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 重排前 10：1.s6-d3-t1-03-memo#p2@T1 2.s6-d3-t1-03-report#p2@T1 3.s6-d0-t1-01-channel#p1@T1 4.s6-d0-t1-01-memo#p2@T1 5.s6-d3-t1-02-report#p2@T1 6.s6-d3-t1-02-summary#p2@T1 7.s6-d3-t1-02-memo#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d0-t1-01-patch#p3@T1 10.s6-d0-t1-02-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 138. `s6-mh-12-new`

- 问：顾问备忘列了哪些未按期出资的新规则？转让未到期股权后受让人没交，原股东还要担什么责？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital-call#p5@T1；s6-d2-g3-memo#p1@T1；s6-d2-g3-memo#p3@T1
- 金标要点：转让人对受让人未按期缴纳的出资承担补充责任；2023法改为对公司损失承担赔偿责任，并新增董事会核查催缴、宽限期不少于六十日后失权、加速到期、未届期转让由受让人缴纳。
- 词法前 10：1.p1-colaw-capital-call#p5@T1 2.s6-d2-g3-memo#p3@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-equity#p1@T1 6.p1-colaw-capital-transition#p2@T1 7.p1-colaw-capital-call#p2@T1 8.p1-colaw-capital-call#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-equity#p5@T1
- 混合前 10：1.p1-colaw-capital-call#p5@T1 2.s6-d2-g3-memo#p3@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-capital-call#p4@T1 8.p1-colaw-equity#p1@T1 9.p1-colaw-capital-call#p3@T1 10.p1-colaw-equity#p3@T1
- 重排前 10：1.s6-d2-g3-memo#p3@T1 2.p1-colaw-capital-call#p5@T1 3.s6-d2-g3-memo#p1@T1 4.p1-colaw-capital-call#p1@T1 5.p1-colaw-capital-transition#p2@T1 6.p1-colaw-capital-call#p2@T1 7.p1-colaw-equity#p1@T1 8.p1-colaw-capital-call#p3@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-equity#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 139. `s6-mh-15-new`

- 问：顾问备忘说存量公司要调整出资期限；新法本身给新设公司的缴足期限是几年？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：p1-colaw-capital#p1@T1
- 金标要点：全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足
- 词法前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p2@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-transition#p1@T1 5.s6-d2-g2-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.p1-colaw-capital-call#p4@T1 8.s6-d2-g3-memo#p3@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-capital-transition#p2@T1
- 混合前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p1@T1 3.s6-d2-g1-memo#p1@T1 4.p1-colaw-capital-transition#p1@T1 5.s6-d2-g2-memo#p2@T1 6.s6-d2-g2-memo#p3@T1 7.s6-d2-g3-memo#p3@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital-call#p4@T1 10.p1-colaw-capital#p1@T1
- 重排前 10：1.s6-d2-g1-memo#p2@T1 2.s6-d2-g2-memo#p1@T1 3.s6-d2-g2-memo#p2@T1 4.s6-d2-g2-memo#p3@T1 5.p1-colaw-capital-transition#p1@T1 6.s6-d2-g3-memo#p3@T1 7.s6-d2-g1-memo#p1@T1 8.p1-colaw-capital-transition#p2@T1 9.p1-colaw-capital#p1@T1 10.p1-colaw-capital-call#p4@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 140. `s7-d0-t0-01-q1`

- 问：系统日志中‘连接超时’的真实原因是什么？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-log#p1@T0
- 金标要点：系统日志中频繁出现“连接超时”警告，但网络监控工具显示带宽正常、延迟极低；经排查发现，该“超时”实为应用层心跳检测机制误判，而非真实网络故障
- 词法前 10：1.s7-d0-t0-01-log#p1@T0 2.s7-d1-t0-03-memo#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s7-d1-t0-03-claim#p3@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s7-d1-t0-03-fact#p3@T0 9.s7-d1-t0-03-claim#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 混合前 10：1.s7-d0-t0-01-log#p1@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-memo#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d1-t0-03-reason#p3@T0 7.s4-d3-t0-05-report#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d0-t0-01-log#p2@T0 10.s7-d0-t0-01-memo#p1@T0
- 重排前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-memo#p1@T0 3.s7-d0-t0-01-log#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-memo#p1@T0 7.s7-d1-t0-03-reason#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d0-t0-01-log#p2@T0 10.s4-d3-t0-05-report#p3@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 141. `s7-d0-t0-01-q2`

- 问：关于每月首日的安全重置，系统文档和内部备忘录的说法一致吗？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-memo#p2@T0
- 金标要点：系统文档中提及“所有用户必须在每月首日完成安全重置”，而另一份内部备忘录指出“安全重置仅对高权限账户强制执行”；这两条信息存在同快照冲突陈述，同一时间点内出现矛盾指令，若未明确上下文，可能引发操作偏差
- 词法前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.p1-cac-o11#p1@T0 4.s7-d1-t0-03-memo#p3@T0 5.p1-cac-o11#p3@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d1-t0-03-claim#p3@T0 8.p1-cac-o13#p4@T0 9.p1-cac-o11#p13@T0 10.s2-d0-02-interview#p2@T0
- 混合前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.p1-cac-o11#p16@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d0-t0-01-internal#p3@T0 6.s7-d1-t0-03-memo#p2@T0 7.p1-cac-o11#p1@T0 8.s7-d1-t0-03-reason#p2@T0 9.s7-d0-t0-01-arch#p1@T0 10.s7-d1-t0-03-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-memo#p2@T0 2.s5-d2-t0-04-analysis#p3@T0 3.s7-d0-t0-01-internal#p3@T0 4.p1-cac-o11#p16@T0 5.s7-d1-t0-03-memo#p2@T0 6.p1-cac-o11#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s7-d0-t0-01-arch#p1@T0 9.s7-d1-t0-03-memo#p3@T0 10.s7-d1-t0-03-reason#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 142. `s7-d0-t0-01-q3`

- 问：系统自称眼下没有已知漏洞，这种说法靠得住吗？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-memo#p3@T0
- 金标要点：该声明发布于一次重大补丁前，且未说明其时效性；可能误将“无漏洞”视为绝对事实
- 词法前 10：1.s7-d1-t0-03-claim#p3@T0 2.s7-d0-t0-01-memo#p3@T0 3.s5-d1-t0-91-repost#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s2-d2-t0-91-callnotes#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-memo#p1@T0 8.s1-d2-01-report#p3@T0 9.s4-d3-t0-91-method#p2@T0 10.s2-d2-01-report#p2@T0
- 混合前 10：1.s7-d0-t0-01-memo#p3@T0 2.s7-d1-t0-03-claim#p3@T0 3.s1-d0-05-warn#p3@T0 4.s2-d0-02-interview#p1@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p1@T0 7.s2-d3-01-memo#p3@T0 8.s1-d0-01-memo#p1@T0 9.s7-d1-t0-03-reason#p2@T0 10.s7-d1-t0-03-reason#p3@T0
- 重排前 10：1.s7-d0-t0-01-memo#p3@T0 2.s7-d1-t0-03-claim#p3@T0 3.s7-d0-t0-01-qa#p2@T0 4.s1-d0-05-warn#p3@T0 5.s2-d0-02-interview#p1@T0 6.s7-d1-t0-03-memo#p1@T0 7.s2-d3-01-memo#p3@T0 8.s1-d0-01-memo#p1@T0 9.s7-d1-t0-03-reason#p2@T0 10.s7-d1-t0-03-reason#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 143. `s7-d0-t0-01-q4`

- 问：‘用户活跃度提升30%’这一数据是否具有代表性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-report#p1@T0
- 金标要点：该合成叙述通过选择性呈现数据构建积极表象，实则掩盖了真实流失率上升的事实，属于典型的合成叙述误导；数据来源为仅包含注册用户的样本池，未涵盖流失用户
- 词法前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s7-d0-t0-01-report#p3@T0 4.s7-d1-t0-03-reason#p3@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-qa#p2@T0 7.p1-cac-o11#p4@T0 8.s7-d1-t0-03-memo#p1@T0 9.s7-d1-t0-03-claim#p3@T0 10.s7-d1-t0-03-claim#p1@T0
- 混合前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s2-d2-01-report#p1@T0 4.s1-d0-02-report#p1@T0 5.s7-d0-t0-01-qa#p2@T0 6.s5-d0-t0-01-report#p1@T0 7.s1-d1-01-analysis#p3@T0 8.s3-d0-01-report#p2@T0 9.s2-d0-01-report#p1@T0 10.s4-d3-t0-05-memo#p2@T0
- 重排前 10：1.s7-d0-t0-01-report#p1@T0 2.s5-d2-t0-04-memo#p3@T0 3.s2-d2-01-report#p1@T0 4.s7-d0-t0-01-qa#p2@T0 5.s5-d0-t0-01-report#p1@T0 6.s3-d0-01-report#p2@T0 7.s4-d3-t0-05-memo#p2@T0 8.s1-d0-02-report#p1@T0 9.s1-d1-01-analysis#p3@T0 10.s2-d0-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 144. `s7-d0-t0-01-q5`

- 问：说全部服务都能不停机升级，这话有没有例外？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-arch#p2@T0
- 金标要点：文档中写道：“所有服务均支持热升级”，但部分老旧服务仍需重启才能更新；尽管“支持热升级”在多数情况下成立，但未说明例外情况，导致该陈述在检索时被当作普遍规则使用
- 词法前 10：1.s4-d1-t0-03-analysis#p1@T0 2.s7-d0-t0-01-arch#p2@T0 3.s1-d0-05-memo#p2@T0 4.p1-colaw-equity#p1@T0 5.s5-d1-t0-91-repost#p2@T0 6.s7-d0-t0-01-qa#p1@T0 7.s3-d0-04-memo#p2@T0 8.s1-d0-04-risk#p2@T0 9.s3-d1-01-memo#p2@T0 10.s7-d0-t0-01-qa#p2@T0
- 混合前 10：1.s7-d0-t0-01-arch#p2@T0 2.s1-d0-05-memo#p2@T0 3.s2-d0-02-interview#p2@T0 4.s5-d0-t0-01-report#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-04-risk#p2@T0 8.s2-d0-03-interview#p2@T0 9.s1-d0-01-analysis#p2@T0 10.s1-d0-04-memo#p3@T0
- 重排前 10：1.s7-d0-t0-01-arch#p2@T0 2.s1-d0-05-memo#p2@T0 3.s2-d0-02-interview#p2@T0 4.s5-d0-t0-01-report#p2@T0 5.s7-d0-t0-01-qa#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d0-04-risk#p2@T0 8.s1-d0-01-analysis#p2@T0 9.s1-d0-04-memo#p3@T0 10.s2-d0-03-interview#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 145. `s7-d0-t0-01-q6`

- 问：FAQ中‘支持多设备登录’的限制条件是什么？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t0-01-qa#p2@T0
- 金标要点：同时在线设备数上限为3个
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s7-d1-t0-03-claim#p3@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-claim#p1@T0 6.s7-d0-t0-01-qa#p1@T0 7.s7-d1-t0-03-reason#p2@T0 8.s3-d0-t0-91-flyer#p3@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-fact#p2@T0
- 混合前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s4-d1-t0-03-memo#p3@T0 4.s1-d0-04-risk#p3@T0 5.s7-d0-t0-01-arch#p2@T0 6.s3-d0-t0-91-flyer#p3@T0 7.s3-d1-01-report#p3@T0 8.s7-d0-t0-01-qa#p1@T0 9.s7-d1-t0-03-memo#p2@T0 10.s3-d3-01-memo#p2@T0
- 重排前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-reason#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s3-d0-t0-91-flyer#p3@T0 5.s7-d0-t0-01-qa#p1@T0 6.s4-d1-t0-03-memo#p3@T0 7.s1-d0-04-risk#p3@T0 8.s7-d0-t0-01-arch#p2@T0 9.s3-d1-01-report#p3@T0 10.s3-d3-01-memo#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 146. `s7-d0-t1-02-q1`

- 问：用户报“搜索功能失效”但服务状态正常的案例中，系统为什么会误判与‘搜索’相关的请求？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p1@T1
- 金标要点：进一步排查发现，该问题源于关键词‘搜索’在不同上下文中具有双重含义——既指系统核心功能；检索模型误判请求意图，从而返回无关结果
- 词法前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d2-t1-04-memo#p1@T1 3.s7-d0-t1-02-claim#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d3-t1-05-synthetic#p3@T1 7.s7-d0-t1-02-claim#p2@T1 8.s7-d2-t1-04-data#p2@T1 9.s7-d3-t1-05-memo#p3@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d2-t1-04-memo#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d3-t1-05-claim#p1@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s7-d3-t1-05-conflict#p2@T1 9.s7-d0-t1-02-analysis#p3@T1 10.s7-d2-t1-04-brief#p3@T1
- 重排前 10：1.s7-d0-t1-02-memo#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d2-t1-04-memo#p1@T1 4.s7-d0-t1-02-update#p2@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d3-t1-05-memo#p3@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s7-d0-t1-02-analysis#p3@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s7-d2-t1-04-brief#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 147. `s7-d0-t1-02-q2`

- 问：一份材料先后被打上“已核实”和“待复查”两种标签，检索系统同时读到时会出什么问题？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p2@T1
- 金标要点：值得注意的是，同一份文档在多个时间点被标记为“已验证”和“待审查”；当检索系统同时加载两个快照时，其判断依据出现冲突：一个版本声称内容准确，另一个则指出存在偏差；系统难以确定哪一信息应作为权威参考
- 词法前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d3-t1-02-summary#p3@T1 3.s7-d0-t1-02-brief#p1@T1 4.s5-d0-t1-02-memo#p2@T1 5.s7-d2-t1-04-brief#p1@T1 6.s6-d0-t1-01-patch#p2@T1 7.s6-d0-t1-03-report#p2@T1 8.s7-d3-t1-05-conflict#p1@T1 9.s6-d0-t1-01-memo#p3@T1 10.s7-d3-t1-05-memo#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d0-t1-01-patch#p2@T1 3.s7-d3-t1-05-memo#p3@T1 4.s6-d3-t1-02-summary#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s6-d0-t1-01-memo#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-brief#p3@T1 9.s7-d2-t1-04-data#p3@T1 10.s7-d0-t1-02-update#p2@T1
- 重排前 10：1.s7-d0-t1-02-memo#p2@T1 2.s6-d0-t1-01-patch#p2@T1 3.s6-d3-t1-02-summary#p3@T1 4.s7-d0-t1-02-claim#p2@T1 5.s6-d0-t1-01-memo#p3@T1 6.s7-d0-t1-02-update#p2@T1 7.s7-d3-t1-05-memo#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s7-d0-t1-02-brief#p3@T1 10.s7-d2-t1-04-data#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 148. `s7-d0-t1-02-q3`

- 问：文档里注明“此处只是推测”的自我说明，模型为什么会把它当成事实来用？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-memo#p3@T1
- 金标要点：此外，文档中的元陈述如“本节内容为推测性分析”被误认为是事实陈述，导致检索结果中混入非确定性信息；此类自我指涉的描述虽有助于说明可信度，却常被模型当作真实数据处理，形成合成叙述陷阱
- 词法前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s5-d1-t1-03-summary#p3@T1 4.s7-d0-t1-02-analysis#p2@T1 5.s6-d3-t1-01-report#p3@T1 6.s7-d3-t1-05-memo#p3@T1 7.s6-d0-t1-03-internal#p1@T1 8.s6-d0-t1-03-report#p1@T1 9.s6-d1-t1-91-release#p1@T1 10.s7-d3-t1-05-synthetic#p1@T1
- 混合前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d0-t1-02-analysis#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s6-d3-t1-01-report#p3@T1 8.s7-d2-t1-04-data#p3@T1 9.s7-d2-t1-04-brief#p3@T1 10.s6-d0-t1-03-report#p2@T1
- 重排前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d0-t1-02-analysis#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d3-t1-05-memo#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d2-t1-04-brief#p3@T1 9.s6-d0-t1-03-report#p2@T1 10.s6-d3-t1-01-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 149. `s7-d0-t1-02-q4`

- 问：在医疗术语中，‘心衰’与‘心力衰竭’为何可能导致检索偏差？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-brief#p1@T1
- 金标要点：在医疗知识库中，“心衰”与“心力衰竭”被用作同义词，但在部分文献中，“心衰”特指急性发作阶段；当检索系统未区分语义层级时，将两者等同处理，导致部分患者治疗方案被错误推荐；“心衰”特指急性发作阶段，而“心力衰竭”涵盖慢性与急性
- 词法前 10：1.s7-d0-t1-02-claim#p1@T1 2.s7-d0-t1-02-brief#p1@T1 3.s7-d0-t1-02-memo#p1@T1 4.s7-d0-t1-02-report#p3@T1 5.s7-d3-t1-05-synthetic#p3@T1 6.s7-d0-t1-02-memo#p3@T1 7.s5-d0-t1-02-memo#p3@T1 8.s7-d3-t1-05-claim#p2@T1 9.s4-d0-t1-02-memo#p2@T1 10.s5-d3-t1-05-memo#p2@T1
- 混合前 10：1.s7-d0-t1-02-brief#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d3-t1-05-claim#p2@T1 4.s4-d0-t1-02-memo#p2@T1 5.s7-d0-t1-02-claim#p1@T1 6.s7-d2-t1-04-memo#p1@T1 7.s7-d0-t1-02-brief#p2@T1 8.s7-d3-t1-05-conflict#p3@T1 9.s7-d3-t1-05-conflict#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 重排前 10：1.s7-d0-t1-02-brief#p1@T1 2.s7-d0-t1-02-claim#p1@T1 3.s7-d0-t1-02-memo#p1@T1 4.s4-d0-t1-02-memo#p2@T1 5.s7-d2-t1-04-memo#p1@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-brief#p2@T1 8.s7-d3-t1-05-conflict#p3@T1 9.s7-d3-t1-05-conflict#p1@T1 10.s7-d0-t1-02-brief#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 150. `s7-d0-t1-02-q6`

- 问：为什么预测性元陈述容易在合成叙述中被当作事实？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d0-t1-02-claim#p3@T1
- 金标要点：更为隐蔽的是，文档中一句“我们预计下季度将有新版本发布”被多次引用，且每次都被当作事实陈述使用；实际上，该句属于预测性元陈述，未经过正式确认
- 词法前 10：1.s7-d0-t1-02-claim#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d0-t1-02-brief#p2@T1 4.s5-d1-t1-03-summary#p3@T1 5.s7-d0-t1-02-report#p2@T1 6.s7-d0-t1-02-analysis#p2@T1 7.s7-d2-t1-04-claim#p3@T1 8.s7-d3-t1-05-memo#p3@T1 9.s7-d2-t1-04-brief#p1@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 混合前 10：1.s7-d0-t1-02-memo#p3@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-report#p2@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d0-t1-02-analysis#p2@T1 7.s5-d1-t1-03-summary#p3@T1 8.s5-d0-t1-02-analysis#p3@T1 9.s7-d0-t1-02-analysis#p3@T1 10.s7-d3-t1-05-synthetic#p3@T1
- 重排前 10：1.s7-d0-t1-02-claim#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d0-t1-02-brief#p2@T1 4.s7-d0-t1-02-report#p2@T1 5.s5-d1-t1-03-summary#p3@T1 6.s7-d2-t1-04-claim#p3@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d3-t1-05-synthetic#p3@T1 9.s5-d0-t1-02-analysis#p3@T1 10.s7-d0-t1-02-analysis#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 151. `s7-d1-t0-03-q1`

- 问：两个看似矛盾的系统状态报告为什么可能同时为真？材料给出了哪几种解释？
- 题型：要拼多处（multi_hop） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-memo#p2@T0；s7-d1-t0-03-reason#p1@T0；s7-d1-t0-03-reason#p2@T0
- 金标要点：二者均真实，但反映不同时间快照；源于部署流水线中各组件更新节奏不一致，造成同一时间点下多版本共存的快照冲突；系统在达成最终一致性前的短暂状态
- 词法前 10：1.s7-d0-t0-01-qa#p2@T0 2.s7-d1-t0-03-memo#p2@T0 3.s7-d1-t0-03-reason#p3@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-report#p3@T0 7.p1-cac-o11#p5@T0 8.s4-d0-t0-01-analysis#p3@T0 9.s5-d2-t0-04-report#p3@T0 10.p1-cac-o13#p6@T0
- 混合前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-reason#p3@T0 3.s7-d1-t0-03-reason#p2@T0 4.s4-d0-t0-01-analysis#p3@T0 5.s7-d1-t0-03-claim#p2@T0 6.s4-d3-t0-05-summary#p3@T0 7.p1-cac-o13#p6@T0 8.s7-d0-t0-01-internal#p1@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d0-t0-01-qa#p2@T0
- 重排前 10：1.s7-d1-t0-03-memo#p2@T0 2.s7-d1-t0-03-reason#p3@T0 3.s7-d1-t0-03-reason#p2@T0 4.s7-d0-t0-01-qa#p2@T0 5.s7-d1-t0-03-claim#p2@T0 6.s4-d3-t0-05-summary#p3@T0 7.p1-cac-o13#p6@T0 8.s7-d0-t0-01-internal#p1@T0 9.s7-d1-t0-03-fact#p3@T0 10.s4-d0-t0-01-analysis#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 152. `s7-d1-t0-03-q2`

- 问：以密钥轮换不同步导致‘认证失败’被误读为例，什么是词面撞车？它在技术文档里怎样表现？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-memo#p1@T0
- 金标要点：这种词面撞车现象常导致误判；在某次跨部门协作中，系统日志显示‘用户认证失败’频繁出现；表面冲突，实则源于对‘失败’一词的语义理解差异；前者指连接中断，后者指验证机制失效
- 词法前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d1-t0-03-reason#p1@T0 7.s7-d1-t0-03-claim#p3@T0 8.s2-d2-t0-91-callnotes#p2@T0 9.s5-d1-t0-91-repost#p1@T0 10.s7-d0-t0-01-report#p2@T0
- 混合前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-reason#p1@T0 5.s7-d1-t0-03-reason#p2@T0 6.s7-d0-t0-01-log#p2@T0 7.s7-d1-t0-03-memo#p2@T0 8.s7-d0-t0-01-report#p2@T0 9.s7-d1-t0-03-claim#p3@T0 10.s7-d1-t0-03-fact#p3@T0
- 重排前 10：1.s7-d1-t0-03-memo#p1@T0 2.s7-d0-t0-01-memo#p1@T0 3.s7-d0-t0-01-qa#p1@T0 4.s7-d1-t0-03-memo#p2@T0 5.s7-d1-t0-03-reason#p1@T0 6.s7-d1-t0-03-reason#p2@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d0-t0-01-log#p2@T0 9.s7-d0-t0-01-report#p2@T0 10.s7-d1-t0-03-fact#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 153. `s7-d1-t0-03-q3`

- 问：如何判断一篇报告中的‘共识’描述是否具有误导性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-claim#p1@T0；s7-d1-t0-03-claim#p3@T0；s7-d1-t0-03-fact#p2@T0
- 金标要点：这些引述均源自少数几位学者的非公开访谈，且未提供原始立场记录；有两项结论为负面或中性，且未被充分讨论；一个说法被‘多位分析师确认’，而该说法本身又‘基于行业标准’，形成闭环论证
- 词法前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-reason#p2@T0 4.s5-d1-t0-91-repost#p1@T0 5.s7-d1-t0-03-fact#p2@T0 6.s7-d1-t0-03-reason#p1@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d1-t0-03-memo#p2@T0 9.p1-cac-o11#p4@T0 10.s7-d0-t0-01-report#p3@T0
- 混合前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d0-t0-01-report#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s7-d1-t0-03-claim#p3@T0 8.s7-d1-t0-03-reason#p3@T0 9.s7-d1-t0-03-claim#p2@T0 10.s7-d1-t0-03-memo#p1@T0
- 重排前 10：1.s7-d1-t0-03-memo#p3@T0 2.s7-d1-t0-03-claim#p1@T0 3.s7-d1-t0-03-fact#p2@T0 4.s7-d1-t0-03-reason#p2@T0 5.s7-d1-t0-03-claim#p3@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d1-t0-03-memo#p1@T0 8.s7-d0-t0-01-report#p3@T0 9.s7-d1-t0-03-fact#p3@T0 10.s7-d1-t0-03-reason#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 154. `s7-d1-t0-03-q4`

- 问：第三方综述称“研究一致支持某疗法”的案例里，合成叙述如何靠选择性整合制造虚假一致性？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d1-t0-03-fact#p2@T0
- 金标要点：该叙述通过选择性强调正向结果构建了虚假共识，构成典型的合成叙述陷阱；有两项结论为负面或中性，且未被充分讨论
- 词法前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d0-t0-01-qa#p2@T0 3.s7-d0-t0-01-report#p1@T0 4.s7-d0-t0-01-qa#p1@T0 5.s7-d0-t0-01-arch#p1@T0 6.s7-d1-t0-03-claim#p2@T0 7.s5-d0-t0-01-press#p1@T0 8.s7-d1-t0-03-fact#p1@T0 9.s5-d0-t0-01-internal#p2@T0 10.s7-d1-t0-03-claim#p1@T0
- 混合前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d1-t0-03-claim#p2@T0 3.s7-d0-t0-01-report#p1@T0 4.s7-d1-t0-03-claim#p1@T0 5.s7-d1-t0-03-fact#p1@T0 6.s5-d0-t0-01-internal#p2@T0 7.s7-d1-t0-03-memo#p3@T0 8.s5-d0-t0-01-memo#p3@T0 9.s7-d0-t0-01-internal#p3@T0 10.s7-d0-t0-01-memo#p3@T0
- 重排前 10：1.s7-d1-t0-03-fact#p2@T0 2.s7-d0-t0-01-report#p1@T0 3.s7-d1-t0-03-fact#p1@T0 4.s7-d1-t0-03-claim#p2@T0 5.s7-d1-t0-03-claim#p1@T0 6.s7-d0-t0-01-internal#p3@T0 7.s7-d0-t0-01-memo#p3@T0 8.s5-d0-t0-01-internal#p2@T0 9.s7-d1-t0-03-memo#p3@T0 10.s5-d0-t0-01-memo#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 155. `s7-d2-t1-04-q1`

- 问：以“搜索结果未按时间排序”的投诉为例，怎样识别术语歧义造成的词面撞车？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-memo#p1@T1
- 金标要点：此现象源于术语“时间”的词面撞车——同一词汇在不同语境中指向不同维度，导致用户预期与系统行为错位；用户所指的“时间”实为“提交时间”，而系统默认按“处理时间”排序
- 词法前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-conflict#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s7-d3-t1-05-memo#p1@T1 7.s7-d2-t1-04-claim#p1@T1 8.s7-d2-t1-04-claim#p2@T1 9.s5-d0-t1-02-report#p2@T1 10.s7-d3-t1-05-memo#p3@T1
- 混合前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-memo#p1@T1 5.s7-d3-t1-05-conflict#p3@T1 6.s7-d3-t1-05-memo#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-claim#p2@T1 9.s5-d0-t1-02-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 重排前 10：1.s7-d2-t1-04-memo#p1@T1 2.s7-d0-t1-02-memo#p1@T1 3.s7-d0-t1-02-report#p3@T1 4.s7-d3-t1-05-conflict#p3@T1 5.s7-d0-t1-02-claim#p2@T1 6.s7-d3-t1-05-memo#p1@T1 7.s7-d3-t1-05-memo#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s5-d0-t1-02-summary#p3@T1 10.s5-d0-t1-02-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 156. `s7-d2-t1-04-q2`

- 问：多份文档用同一组原始数据、一份说显著改善另一份说没达标时，怎么判断这算不算同快照冲突陈述？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-data#p3@T1
- 金标要点：这种基于相同快照的不同解释，反映合成叙述中对数据的多重建构能力，若缺乏上下文比对，极易引发检索误解
- 词法前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p2@T1 5.s7-d2-t1-04-data#p1@T1 6.s5-d1-t1-03-summary#p2@T1 7.s7-d3-t1-05-claim#p1@T1 8.s7-d0-t1-02-report#p2@T1 9.s2-d0-t1-91-memo#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 混合前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d2-t1-04-data#p1@T1 5.s7-d3-t1-05-claim#p1@T1 6.s7-d2-t1-04-brief#p3@T1 7.s7-d3-t1-05-claim#p3@T1 8.s7-d0-t1-02-claim#p2@T1 9.s5-d1-t1-03-summary#p2@T1 10.s5-d0-t1-02-memo#p3@T1
- 重排前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d2-t1-04-data#p1@T1 5.s7-d3-t1-05-claim#p1@T1 6.s5-d0-t1-02-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s7-d3-t1-05-claim#p3@T1 9.s5-d1-t1-03-summary#p2@T1 10.s7-d0-t1-02-claim#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 157. `s7-d2-t1-04-q3`

- 问：元陈述与实际内容不一致时，可能引发哪些检索风险？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-claim#p3@T1；s7-d2-t1-04-memo#p3@T1
- 金标要点：此自相矛盾的元声明削弱了整份材料的可信度，构成元层级的检索陷阱，即对内容真实性本身的宣称与实际内容不符；自我宣称与实际证据链之间的脱节
- 词法前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s6-d2-g1-memo#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p3@T1 8.p1-cac-o20#p8@T1 9.s7-d0-t1-02-claim#p1@T1 10.s7-d3-t1-05-memo#p2@T1
- 混合前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d2-t1-04-claim#p3@T1 4.s7-d0-t1-02-brief#p2@T1 5.s7-d0-t1-02-analysis#p3@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-report#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 重排前 10：1.s7-d2-t1-04-memo#p3@T1 2.s7-d0-t1-02-memo#p3@T1 3.s7-d2-t1-04-claim#p3@T1 4.s7-d0-t1-02-analysis#p3@T1 5.s7-d0-t1-02-brief#p2@T1 6.s7-d3-t1-05-claim#p2@T1 7.s7-d0-t1-02-analysis#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d0-t1-02-report#p1@T1 10.s5-d0-t1-02-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 158. `s7-d2-t1-04-q4`

- 问：合成叙述如何通过模糊定义和选择性呈现误导用户判断？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d2-t1-04-brief#p1@T1
- 金标要点：这种合成叙述通过选择性呈现数据和模糊操作定义，构建出看似合理但有偏差的整体印象，典型体现为对事实的非透明重构；一份关于用户满意度的分析报告称：“多数受访者表示体验良好；“满意”选项的定义被刻意模糊；样本仅来自高活跃用户群体
- 词法前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-synthetic#p2@T1 4.s7-d0-t1-02-claim#p2@T1 5.s7-d0-t1-02-report#p3@T1 6.s6-d0-t1-01-memo#p3@T1 7.s7-d2-t1-04-brief#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s3-d0-03-report#p3@T1 10.s7-d3-t1-05-claim#p3@T1
- 混合前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-claim#p3@T1 4.s7-d0-t1-02-report#p2@T1 5.s7-d3-t1-05-synthetic#p2@T1 6.s7-d0-t1-02-memo#p3@T1 7.s7-d3-t1-05-synthetic#p3@T1 8.s5-d1-t1-03-summary#p3@T1 9.s7-d3-t1-05-memo#p3@T1 10.s7-d2-t1-04-brief#p3@T1
- 重排前 10：1.s7-d2-t1-04-brief#p1@T1 2.s7-d3-t1-05-synthetic#p1@T1 3.s7-d3-t1-05-synthetic#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s7-d2-t1-04-brief#p3@T1 6.s7-d3-t1-05-claim#p3@T1 7.s7-d0-t1-02-report#p2@T1 8.s7-d0-t1-02-memo#p3@T1 9.s7-d3-t1-05-synthetic#p3@T1 10.s5-d1-t1-03-summary#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 159. `s7-d3-t1-05-q1`

- 问：技术组说日志里没有登录失败记录、审计组却说全都抓到了，哪份材料解释了这是术语口径不同？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-memo#p1@T1
- 金标要点：在某次跨部门数据对齐会议中，技术团队报告称“系统日志未记录用户登录失败事件”，而安全审计组却声称“所有登录失败均被完整捕获”；表面上看二者矛盾，实则因术语定义不同：前者指未写入特定日志文件，后者指已通过集中式监控平台覆盖；这种词面撞车现象常引发误判
- 词法前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d3-t1-91-changelog#p2@T1 5.s2-d0-t1-91-memo#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s7-d0-t1-02-report#p1@T1 8.s2-d0-t1-91-interview#p2@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s7-d0-t1-02-claim#p1@T1
- 混合前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p2@T1 3.s6-d1-t1-91-release#p2@T1 4.s7-d0-t1-02-claim#p1@T1 5.s6-d3-t1-91-changelog#p1@T1 6.s6-d3-t1-91-changelog#p3@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d0-t1-02-memo#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 重排前 10：1.s7-d3-t1-05-memo#p1@T1 2.s6-d3-t1-91-changelog#p2@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d3-t1-91-changelog#p3@T1 5.s7-d0-t1-02-claim#p1@T1 6.s6-d3-t1-91-changelog#p1@T1 7.s7-d2-t1-04-data#p3@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d0-t1-02-memo#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 160. `s7-d3-t1-05-q2`

- 问：哪份文档借“完成度87%仍算达标”一例，揭示了‘达标’在不同评价标准下的多重解释？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-memo#p2@T1
- 金标要点：该指标实际完成度为87%，但经评估后仍视为达标。；这表明系统性地使用“达标”一词掩盖了真实绩效差距，构成元层面的陈述冲突。
- 词法前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d3-t1-05-memo#p3@T1 4.s7-d0-t1-02-memo#p1@T1 5.s7-d2-t1-04-memo#p2@T1 6.s7-d0-t1-02-claim#p1@T1 7.s7-d0-t1-02-update#p3@T1 8.s7-d2-t1-04-memo#p1@T1 9.s5-d1-t1-03-memo#p3@T1 10.s5-d0-t1-02-report#p3@T1
- 混合前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s7-d3-t1-05-conflict#p2@T1 7.s7-d0-t1-02-claim#p3@T1 8.s6-d3-t1-01-note#p3@T1 9.s5-d1-t1-03-note#p2@T1 10.s7-d2-t1-04-claim#p3@T1
- 重排前 10：1.s7-d2-t1-04-data#p3@T1 2.s7-d3-t1-05-memo#p2@T1 3.s7-d2-t1-04-memo#p2@T1 4.s7-d3-t1-05-memo#p3@T1 5.s5-d1-t1-03-memo#p3@T1 6.s7-d0-t1-02-claim#p3@T1 7.s7-d2-t1-04-claim#p3@T1 8.s5-d1-t1-03-note#p2@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s6-d3-t1-01-note#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 161. `s7-d3-t1-05-q3`

- 问：哪一个文档展示了通过选择性引用专家来构建虚假权威的现象？
- 题型：换一种说法（paraphrase） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-synthetic#p2@T1
- 金标要点：这种通过选择性引用构建权威感，是合成叙述的常见手法；更隐蔽的是，该材料同时引用“专家普遍认可”作为背书，但所列专家中仅有两人发表过相关研究
- 词法前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-memo#p2@T1 3.s7-d2-t1-04-brief#p1@T1 4.s7-d0-t1-02-claim#p3@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s5-d1-t1-03-note#p3@T1 7.s7-d2-t1-04-memo#p3@T1 8.s7-d0-t1-02-update#p1@T1 9.s7-d2-t1-04-brief#p2@T1 10.s5-d1-t1-03-note#p1@T1
- 混合前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-update#p1@T1 4.s7-d2-t1-04-claim#p3@T1 5.s7-d3-t1-05-conflict#p2@T1 6.s5-d0-t1-02-analysis#p3@T1 7.s7-d2-t1-04-memo#p3@T1 8.s5-d1-t1-03-memo#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s5-d1-t1-03-note#p1@T1
- 重排前 10：1.s7-d3-t1-05-synthetic#p2@T1 2.s7-d0-t1-02-claim#p3@T1 3.s7-d0-t1-02-update#p1@T1 4.s7-d2-t1-04-memo#p3@T1 5.s5-d1-t1-03-note#p1@T1 6.s7-d2-t1-04-claim#p3@T1 7.s5-d0-t1-02-analysis#p3@T1 8.s5-d1-t1-03-memo#p1@T1 9.s5-d1-t1-03-note#p3@T1 10.s7-d3-t1-05-conflict#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 162. `s7-d3-t1-05-q4`

- 问：哪份文档分析了‘进度保持在预期轨道上’这一说法与实际延迟之间的语义断裂？
- 题型：字面题（lexical） · 类别：普通难例（hard） · 合成模板陷阱：否
- 金标证据：s7-d3-t1-05-conflict#p1@T1
- 金标要点：在一份项目总结报告中，反复强调“进度保持在预期轨道上”；但详细日程表显示，关键里程碑已延迟两周，且资源调配不足；这里的“预期轨道”未明确定义，导致词面重复掩盖了实质延误，形成语义断裂。
- 词法前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d3-t1-05-conflict#p3@T1 3.s7-d0-t1-02-analysis#p3@T1 4.s5-d2-t1-91-digest#p3@T1 5.s7-d2-t1-04-claim#p3@T1 6.s5-d3-t1-05-analysis#p3@T1 7.s6-d3-t1-91-changelog#p3@T1 8.s6-d3-t1-01-note#p3@T1 9.s6-d3-t1-01-memo#p3@T1 10.s6-d3-t1-01-report#p3@T1
- 混合前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d0-t1-02-analysis#p3@T1 3.s7-d3-t1-05-conflict#p3@T1 4.s7-d2-t1-04-brief#p2@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s7-d2-t1-04-brief#p3@T1 7.s1-d0-03-memo#p2@T1 8.s7-d2-t1-04-claim#p3@T1 9.s7-d0-t1-02-analysis#p1@T1 10.s7-d0-t1-02-report#p1@T1
- 重排前 10：1.s7-d3-t1-05-conflict#p1@T1 2.s7-d3-t1-05-conflict#p3@T1 3.s7-d0-t1-02-analysis#p3@T1 4.s5-d3-t1-05-analysis#p3@T1 5.s7-d2-t1-04-claim#p3@T1 6.s7-d2-t1-04-brief#p2@T1 7.s7-d0-t1-02-analysis#p1@T1 8.s7-d2-t1-04-brief#p3@T1 9.s7-d0-t1-02-report#p1@T1 10.s1-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 163. `r4m-s5-d3-t1-05-q4`

- 问：按官方最新统计，这个地区的制造业在经济总量里还占三成以上吗？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-report#p2@T1
- 金标要点：该比例已下降至28%
- 词法前 10：1.s5-d3-t1-05-report#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-01-memo#p1@T1 4.p2-gdp-national#p2@T1 5.s6-d0-t1-03-memo#p1@T1 6.s1-d1-01-analysis#p3@T1 7.s5-d2-t1-91-digest#p3@T1 8.s2-d0-t1-91-interview#p3@T1 9.s6-d0-t1-91-sop#p2@T1 10.s6-d3-t1-91-changelog#p3@T1
- 混合前 10：1.s5-d3-t1-05-report#p1@T1 2.p2-gdp-national#p2@T1 3.s5-d2-t1-91-digest#p3@T1 4.s2-d0-t1-91-memo#p1@T1 5.s6-d3-t1-91-changelog#p3@T1 6.s2-d0-01-memo#p1@T1 7.s5-d2-t1-91-digest#p1@T1 8.s2-d0-t1-91-interview#p3@T1 9.s5-d3-t1-05-report#p2@T1 10.s5-d3-t1-05-memo#p3@T1
- 重排前 10：1.s5-d3-t1-05-report#p1@T1 2.s5-d2-t1-91-digest#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-01-memo#p1@T1 5.s2-d0-t1-91-interview#p3@T1 6.s5-d3-t1-05-memo#p3@T1 7.p2-gdp-national#p2@T1 8.s6-d3-t1-91-changelog#p3@T1 9.s5-d2-t1-91-digest#p1@T1 10.s5-d3-t1-05-report#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 164. `r4m-s5-d3-t1-05-q5`

- 问：员工对工作环境满不满意，最新一轮调查给出的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d3-t1-05-analysis#p2@T1
- 金标要点：满意度已升至67%
- 词法前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s2-d2-01-memo#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d3-t1-05-memo#p2@T1 5.p1-colaw-equity#p3@T1 6.s5-d3-t1-05-analysis#p3@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-cac-o16#p5@T1 9.s2-d0-02-memo#p1@T1 10.s7-d2-t1-04-brief#p1@T1
- 混合前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s7-d2-t1-04-brief#p1@T1 3.s5-d3-t1-05-analysis#p3@T1 4.s1-d1-01-memo#p3@T1 5.s5-d3-t1-05-analysis#p2@T1 6.s1-d0-04-memo#p3@T1 7.s5-d3-t1-05-memo#p2@T1 8.s2-d0-02-memo#p1@T1 9.s1-d0-02-memo#p3@T1 10.s2-d2-01-memo#p1@T1
- 重排前 10：1.s5-d3-t1-05-analysis#p1@T1 2.s5-d3-t1-05-memo#p2@T1 3.s2-d2-01-memo#p1@T1 4.s7-d2-t1-04-brief#p1@T1 5.s5-d3-t1-05-analysis#p3@T1 6.s5-d3-t1-05-analysis#p2@T1 7.s1-d0-02-memo#p3@T1 8.s1-d1-01-memo#p3@T1 9.s1-d0-04-memo#p3@T1 10.s2-d0-02-memo#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 165. `r4m-s5-d0-t1-02-q5`

- 问：被媒体反复转述的早高峰车速和拥堵时长，独立研究实际测到的是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s5-d0-t1-02-memo#p2@T1
- 金标要点：真实车速为16公里/小时；拥堵时长约为3.2小时
- 词法前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s2-d0-t1-91-interview#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d0-t1-02-report#p1@T1 7.s5-d1-t1-03-summary#p1@T1 8.p1-cac-o11#p10@T1 9.s5-d0-t1-02-memo#p3@T1 10.s5-d0-t1-02-report#p2@T1
- 混合前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d3-t1-05-memo#p1@T1 6.s5-d1-t1-03-summary#p1@T1 7.s5-d0-t1-02-report#p2@T1 8.s4-d0-t1-91-eval#p2@T1 9.s2-d0-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s5-d0-t1-02-memo#p1@T1 2.s5-d0-t1-02-memo#p2@T1 3.s5-d3-t1-05-memo#p2@T1 4.s5-d0-t1-02-report#p1@T1 5.s5-d0-t1-02-report#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.s5-d3-t1-05-memo#p1@T1 8.s5-d1-t1-03-summary#p1@T1 9.s4-d0-t1-91-eval#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 166. `r4m-s3-d3-01-q5`

- 问：竞品B这一期的月费，两份比价材料写得一样吗？各写了多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d3-01-memo#p2@T1；s3-d3-01-report#p2@T1
- 金标要点：月费最低可至99元；月费降至129元
- 词法前 10：1.s3-d1-t1-91-pricesheet#p2@T1 2.s3-d3-01-memo#p2@T1 3.s3-d2-01-competitor-pricing#p2@T1 4.s3-d2-01-competitor-pricing#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d1-01-memo#p2@T1 7.s3-d1-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p3@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d0-01-report#p2@T1
- 混合前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d2-01-competitor-pricing#p2@T1 3.s3-d1-t1-91-quote#p3@T1 4.s3-d1-t1-91-pricesheet#p2@T1 5.s3-d3-01-report#p2@T1 6.s3-d1-01-memo#p2@T1 7.s3-d3-01-memo#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-brochure#p2@T1
- 重排前 10：1.s3-d2-01-competitor-pricing#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d3-01-memo#p2@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-01-memo#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d1-t1-91-quote#p1@T1 10.s3-d2-t1-91-brochure#p2@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 167. `r4m-s3-d0-02-q7`

- 问：C公司149元的新方案现在已经开卖了吗？两份比价材料怎么说？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s3-d0-02-a#p3@T1；s3-d0-02-b#p3@T1
- 金标要点：改推“成长计划”订阅制，首年费用149元，含全功能访问及优先技术支持，用户迁移率已达72%；现仅开放限时试用，正式版本将于下季度以149元起售
- 词法前 10：1.s3-d0-02-a#p3@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s7-d2-t1-04-memo#p3@T1 6.s3-d1-t1-91-pricesheet#p3@T1 7.s3-d1-t1-91-pricesheet#p1@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-01-memo#p3@T1 10.p1-colaw-governance#p1@T1
- 混合前 10：1.s3-d0-02-a#p3@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d0-01-report#p3@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-01-memo#p3@T1 6.s3-d0-01-memo#p3@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-t1-91-pricesheet#p3@T1 9.s3-d0-02-b#p3@T1 10.s3-d0-01-report#p1@T1
- 重排前 10：1.s3-d0-02-a#p3@T1 2.s3-d0-01-report#p3@T1 3.s3-d0-01-memo#p3@T1 4.s3-d0-02-b#p3@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d0-03-report#p1@T1 7.s3-d1-01-memo#p3@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-t1-91-pricesheet#p3@T1 10.s3-d0-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 168. `r4n-s2-d0-t1-91-qa`

- 问：越南那边的经销商返点，最终按多少给？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d0-t1-91-memo#p1@T1
- 金标要点：把返点比例定为5%
- 词法前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.p2-gdp-national#p3@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-interview#p3@T1 7.s6-d1-t1-91-patch#p1@T1 8.s2-d0-04-memo#p3@T1 9.s6-d3-t1-91-notice#p1@T1 10.p1-colaw-capital-call#p1@T1
- 混合前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p3@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-04-memo#p3@T1 5.s4-d2-t1-91-review#p2@T1 6.s2-d0-t1-91-interview#p3@T1 7.s6-d0-t1-91-sop#p3@T1 8.s3-d3-01-report#p2@T1 9.s2-d0-04-memo#p1@T1 10.s2-d0-02-memo#p3@T1
- 重排前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-memo#p3@T1 4.s2-d0-04-memo#p3@T1 5.s2-d0-t1-91-interview#p3@T1 6.s3-d3-01-report#p2@T1 7.s4-d2-t1-91-review#p2@T1 8.s6-d0-t1-91-sop#p3@T1 9.s2-d0-04-memo#p1@T1 10.s2-d0-02-memo#p3@T1
- 建议：可议 hybrid+rerank
- 理由：两边都碰上了金标，重排把金标排得更靠前。

### 169. `r4n-s2-d0-t1-91-qb`

- 问：关于越南经销商返点，访谈里的口径和后来正式签的约有什么出入？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d0-t1-91-interview#p1@T1；s2-d0-t1-91-memo#p1@T1
- 金标要点：返点比例会维持在8%；把返点比例定为5%
- 词法前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d3-t1-91-interview#p2@T1 4.s2-d0-t1-91-interview#p3@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-memo#p3@T1 7.s6-d0-t1-01-memo#p1@T1 8.s7-d2-t1-04-brief#p1@T1 9.s6-d3-t1-91-changelog#p1@T1 10.p1-colaw-governance-supervisor-js#p4@T1
- 混合前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s6-d0-t1-91-sop#p3@T1 5.s2-d0-t1-91-memo#p3@T1 6.s6-d3-t1-91-changelog#p1@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-cac-o20#p8@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d0-04-memo#p3@T1
- 重排前 10：1.s2-d0-t1-91-interview#p1@T1 2.s2-d0-t1-91-memo#p1@T1 3.s2-d0-t1-91-interview#p3@T1 4.s2-d3-t1-91-interview#p2@T1 5.s6-d0-t1-91-sop#p3@T1 6.s2-d0-t1-91-memo#p3@T1 7.s6-d3-t1-91-changelog#p1@T1 8.p1-cac-o20#p8@T1 9.s5-d2-t1-91-digest#p1@T1 10.s2-d0-04-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 170. `r4n-s3-d1-t1-91-qa`

- 问：竞品E标准版一年现在要花多少钱？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-quote#p1@T1
- 金标要点：把标准版年费调整为4200元
- 词法前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d1-t1-91-quote#p1@T1 4.s3-d1-t1-91-quote#p3@T1 5.s3-d0-03-report#p1@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d0-02-b#p2@T1 8.s5-d3-t1-05-report#p3@T1 9.s7-d2-t1-04-data#p2@T1 10.s3-d1-01-report#p3@T1
- 混合前 10：1.s3-d1-t1-91-quote#p1@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d0-03-report#p1@T1 4.s3-d1-t1-91-quote#p2@T1 5.s3-d3-01-report#p1@T1 6.s3-d1-t1-91-quote#p3@T1 7.s3-d0-03-memo#p1@T1 8.s3-d0-04-memo#p1@T1 9.s3-d0-03-memo#p2@T1 10.s3-d1-01-report#p3@T1
- 重排前 10：1.s3-d1-t1-91-quote#p1@T1 2.s3-d1-t1-91-pricesheet#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p1@T1 7.s3-d0-03-memo#p1@T1 8.s3-d0-04-memo#p1@T1 9.s3-d0-03-memo#p2@T1 10.s3-d1-01-report#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 171. `r4n-s3-d1-t1-91-qb`

- 问：两份材料给竞品E标准版标的年价不一样，分别是多少，哪份更可信？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-pricesheet#p1@T1；s3-d1-t1-91-quote#p1@T1
- 金标要点：竞品E的标准版年费为3600元；把标准版年费调整为4200元
- 词法前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s7-d3-t1-05-synthetic#p2@T1 5.s6-d1-t1-91-patch#p1@T1 6.s6-d3-t1-01-report#p2@T1 7.s6-d3-t1-02-report#p3@T1 8.s3-d1-t1-91-quote#p3@T1 9.s3-d1-t1-91-pricesheet#p2@T1 10.s5-d0-t1-02-analysis#p3@T1
- 混合前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d3-01-report#p1@T1 7.s3-d3-01-report#p2@T1 8.s3-d1-t1-91-pricesheet#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d2-t1-91-contract#p2@T1
- 重排前 10：1.s3-d1-t1-91-pricesheet#p1@T1 2.s3-d1-t1-91-quote#p1@T1 3.s3-d1-t1-91-quote#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d3-01-report#p1@T1 8.s3-d3-01-report#p2@T1 9.s3-d1-01-report#p2@T1 10.s3-d2-t1-91-contract#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 172. `r4n-s3-d1-t1-91-qc`

- 问：竞品E标准版一个账号最多能开几个座位？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d1-t1-91-quote#p2@T1
- 金标要点：标准版单账号席位上限为25个
- 词法前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.p1-colaw-oneperson#p1@T1 7.s7-d0-t1-02-memo#p2@T1 8.s3-d0-02-b#p2@T1 9.s7-d3-t1-05-conflict#p2@T1 10.s3-d1-01-report#p3@T1
- 混合前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-01-report#p3@T1 6.s6-d3-t1-02-report#p1@T1 7.s3-d3-01-report#p1@T1 8.s5-d2-t1-91-digest#p3@T1 9.s3-d1-t1-91-quote#p3@T1 10.s3-d0-01-memo#p1@T1
- 重排前 10：1.s3-d1-t1-91-quote#p2@T1 2.s3-d1-t1-91-pricesheet#p2@T1 3.s3-d1-t1-91-pricesheet#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-quote#p3@T1 6.s3-d1-01-report#p3@T1 7.s6-d3-t1-02-report#p1@T1 8.s3-d3-01-report#p1@T1 9.s5-d2-t1-91-digest#p3@T1 10.s3-d0-01-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 173. `r4n-s4-d2-t1-91-qa`

- 问：每单履约到底要花多少成本？财务那边怎么认定的？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-review#p1@T1
- 金标要点：单票履约成本应修正为7.4元
- 词法前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s2-d0-02-report#p3@T1 4.s4-d0-t1-02-report#p3@T1 5.s4-d2-t1-04-summary#p3@T1 6.s2-d3-t1-91-minutes#p3@T1 7.s4-d0-t1-02-plan#p1@T1 8.s4-d2-t1-04-report#p1@T1 9.s1-d0-03-report#p3@T1 10.s4-d0-t1-02-report#p1@T1
- 混合前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s6-d0-t1-03-memo#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s6-d0-t1-03-memo#p1@T1 6.s2-d0-02-report#p3@T1 7.s2-d3-t1-91-minutes#p3@T1 8.s1-d0-02-report#p3@T1 9.p1-colaw-capital#p1@T1 10.s1-d0-01-memo#p3@T1
- 重排前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d2-t1-04-report#p1@T1 4.s6-d0-t1-03-memo#p1@T1 5.s2-d0-02-report#p3@T1 6.s2-d3-t1-91-minutes#p3@T1 7.s6-d0-t1-03-memo#p3@T1 8.s1-d0-02-report#p3@T1 9.p1-colaw-capital#p1@T1 10.s1-d0-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 174. `r4n-s4-d2-t1-91-qb`

- 问：v3模型和财务复核给的每单履约成本差了多少，为什么不一样？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-model-v3#p1@T1；s4-d2-t1-91-review#p1@T1
- 金标要点：单票履约成本应修正为7.4元；单票履约成本为6.8元；漏计包材费用
- 词法前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s4-d0-t1-02-report#p3@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-summary#p3@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d0-t1-02-memo#p1@T1 10.s4-d2-t1-91-review#p2@T1
- 混合前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-91-review#p2@T1 5.s6-d0-t1-03-memo#p2@T1 6.s4-d2-t1-04-report#p1@T1 7.s4-d0-t1-02-memo#p1@T1 8.s6-d0-t1-03-internal#p2@T1 9.s4-d2-t1-04-memo#p2@T1 10.s4-d0-t1-02-analysis#p1@T1
- 重排前 10：1.s4-d2-t1-91-review#p1@T1 2.s4-d2-t1-91-model-v3#p1@T1 3.s4-d0-t1-02-analysis#p3@T1 4.s4-d2-t1-04-report#p1@T1 5.s4-d0-t1-02-memo#p1@T1 6.s6-d0-t1-03-memo#p2@T1 7.s6-d0-t1-03-internal#p2@T1 8.s4-d2-t1-04-memo#p2@T1 9.s4-d0-t1-02-analysis#p1@T1 10.s4-d2-t1-91-review#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 175. `r4n-s4-d2-t1-91-qc`

- 问：复核时用的退货率是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d2-t1-91-review#p2@T1
- 金标要点：退货率参数取4.1%
- 词法前 10：1.s4-d2-t1-91-review#p2@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.s6-d0-t1-91-sop#p2@T1 4.s4-d2-t1-91-review#p1@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d2-t1-91-review#p3@T1 7.s2-d0-01-report#p1@T1 8.s7-d3-t1-05-memo#p2@T1 9.s4-d0-t1-91-deck#p2@T1 10.s1-d1-t1-91-memo#p2@T1
- 混合前 10：1.s4-d2-t1-91-review#p2@T1 2.s4-d2-t1-91-model-v3#p2@T1 3.s4-d2-t1-91-review#p1@T1 4.s4-d0-t1-02-guide#p2@T1 5.s6-d0-t1-91-sop#p2@T1 6.s2-d0-02-report#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s4-d2-t1-91-review#p3@T1 9.s2-d0-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s4-d2-t1-91-model-v3#p2@T1 2.s4-d2-t1-91-review#p2@T1 3.s6-d0-t1-91-sop#p2@T1 4.s4-d0-t1-02-guide#p2@T1 5.s2-d0-02-report#p3@T1 6.s1-d1-t1-91-memo#p2@T1 7.s2-d0-t1-91-interview#p2@T1 8.s4-d0-t1-91-deck#p2@T1 9.s4-d2-t1-91-review#p1@T1 10.s4-d2-t1-91-review#p3@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 176. `r4n-s6-d3-t1-91-qa`

- 问：住户收入的新统计口径到底哪天开始用？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-notice#p1@T1
- 金标要点：新口径的启用时间推迟到6月1日
- 词法前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s1-d1-t1-91-brief#p2@T1 3.s6-d3-t1-91-notice#p1@T1 4.s6-d0-t1-01-patch#p1@T1 5.s4-d0-t1-91-eval#p1@T1 6.s3-d2-01-competitor-pricing#p2@T1 7.s3-d0-01-report#p2@T1 8.s1-d2-01-analysis#p3@T1 9.s5-d3-t1-05-memo#p3@T1 10.s5-d2-t1-91-digest#p1@T1
- 混合前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s6-d3-t1-91-notice#p1@T1 3.s5-d2-t1-91-digest#p1@T1 4.s6-d1-c2-memo#p3@T1 5.s5-d3-t1-05-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.s1-d1-t1-91-brief#p2@T1 8.s1-d0-02-report#p3@T1 9.s1-d0-01-analysis#p3@T1 10.s6-d0-t1-01-patch#p1@T1
- 重排前 10：1.s6-d3-t1-91-changelog#p1@T1 2.s6-d3-t1-91-notice#p1@T1 3.s5-d3-t1-05-memo#p3@T1 4.s5-d2-t1-91-digest#p1@T1 5.s6-d1-c2-memo#p3@T1 6.s6-d2-g2-memo#p1@T1 7.s1-d1-t1-91-brief#p2@T1 8.s6-d0-t1-01-patch#p1@T1 9.s1-d0-02-report#p3@T1 10.s1-d0-01-analysis#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 177. `r4n-s6-d3-t1-91-qb`

- 问：新收入口径的启用日期，变更日志和执行通知各写的是哪天？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-changelog#p1@T1；s6-d3-t1-91-notice#p1@T1
- 金标要点：新口径的启用时间推迟到6月1日；自5月1日起启用
- 词法前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.p1-colaw-capital-call#p2@T1 4.p1-colaw-capital#p4@T1 5.s6-d3-t1-91-notice#p3@T1 6.p1-colaw-governance#p1@T1 7.s6-d3-t1-03-memo#p3@T1 8.p1-colaw-equity#p3@T1 9.s3-d0-01-report#p2@T1 10.s6-d3-t1-03-memo#p2@T1
- 混合前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-memo#p3@T1 6.s6-d3-t1-02-memo#p2@T1 7.s6-d3-t1-91-notice#p3@T1 8.s6-d2-g2-memo#p2@T1 9.p1-colaw-capital-call#p2@T1 10.s6-d1-c1-memo#p1@T1
- 重排前 10：1.s6-d3-t1-91-notice#p1@T1 2.s6-d3-t1-91-changelog#p1@T1 3.s6-d3-t1-02-report#p2@T1 4.s6-d3-t1-03-memo#p2@T1 5.s6-d3-t1-03-memo#p3@T1 6.s6-d2-g2-memo#p2@T1 7.p1-colaw-capital-call#p2@T1 8.s6-d3-t1-02-memo#p2@T1 9.s6-d3-t1-91-notice#p3@T1 10.s6-d1-c1-memo#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 178. `r4n-s6-d3-t1-91-qc`

- 问：这一期调查一共抽了多少户？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d3-t1-91-notice#p2@T1
- 金标要点：本期样本户数为1.2万户
- 词法前 10：1.s6-d1-t1-91-release#p2@T1 2.s5-d3-t1-05-memo#p1@T1 3.s7-d0-t1-02-report#p2@T1 4.s5-d1-t1-03-memo#p1@T1 5.s6-d2-t1-91-bulletin#p2@T1 6.s4-d0-t1-91-deck#p2@T1 7.s7-d3-t1-05-memo#p2@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s7-d2-t1-04-data#p1@T1 10.p2-gdp-national#p1@T1
- 混合前 10：1.s6-d3-t1-91-changelog#p2@T1 2.s4-d0-t1-91-deck#p2@T1 3.s2-d0-t1-91-memo#p2@T1 4.s5-d1-t1-03-memo#p2@T1 5.s5-d1-t1-03-memo#p1@T1 6.s5-d2-t1-91-digest#p3@T1 7.s6-d2-t1-91-bulletin#p2@T1 8.s6-d3-t1-91-changelog#p3@T1 9.s5-d3-t1-05-memo#p1@T1 10.p2-gdp-national#p1@T1
- 重排前 10：1.s5-d1-t1-03-memo#p1@T1 2.s5-d3-t1-05-memo#p1@T1 3.s6-d3-t1-91-changelog#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.s2-d0-t1-91-memo#p2@T1 6.s5-d1-t1-03-memo#p2@T1 7.s5-d2-t1-91-digest#p3@T1 8.s6-d2-t1-91-bulletin#p2@T1 9.s6-d3-t1-91-changelog#p3@T1 10.p2-gdp-national#p1@T1
- 建议：需要改题
- 理由：词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。

### 179. `r4n-s1-d1-t1-91-qa`

- 问：我们在印尼的电子支付牌照现在是什么状态？还需要借别人的通道吗？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-brief#p1@T1
- 金标要点：该电子支付牌照已于8月获批；无需再借合作方通道
- 词法前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s5-d2-t1-91-digest#p3@T1 4.s2-d0-t1-91-interview#p3@T1 5.s5-d0-t1-02-summary#p3@T1 6.s6-d3-t1-91-changelog#p3@T1 7.s7-d0-t1-02-claim#p3@T1 8.s6-d0-t1-91-sop#p1@T1 9.p1-colaw-capital-transition#p2@T1 10.s7-d2-t1-04-claim#p2@T1
- 混合前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s6-d3-t1-91-changelog#p3@T1 4.s6-d1-c4-memo#p1@T1 5.s7-d2-t1-04-claim#p2@T1 6.s6-d0-t1-91-sop#p1@T1 7.p1-cac-o16#p9@T1 8.p1-cac-o16#p4@T1 9.s1-d0-04-risk#p2@T1 10.p1-colaw-capital-transition#p2@T1
- 重排前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d2-t1-04-claim#p2@T1 4.s6-d0-t1-91-sop#p1@T1 5.p1-cac-o16#p9@T1 6.p1-colaw-capital-transition#p2@T1 7.s6-d3-t1-91-changelog#p3@T1 8.s6-d1-c4-memo#p1@T1 9.p1-cac-o16#p4@T1 10.s1-d0-04-risk#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 180. `r4n-s1-d1-t1-91-qb`

- 问：印尼支付牌照这件事，进入备忘和监管简报的说法有什么冲突？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-memo#p1@T1；s1-d1-t1-91-brief#p1@T1
- 金标要点：该电子支付牌照已于8月获批；电子支付牌照申请仍在审理中；需要借用合作方通道；无需再借合作方通道
- 词法前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s1-d1-t1-91-memo#p3@T1 4.p1-colaw-equity#p1@T1 5.s6-d3-t1-01-memo#p3@T1 6.s6-d3-t1-01-note#p3@T1 7.s6-d3-t1-01-report#p3@T1 8.s7-d0-t1-02-memo#p2@T1 9.s1-d1-t1-91-brief#p3@T1 10.p1-colaw-oneperson#p2@T1
- 混合前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d0-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p2@T1 5.s6-d3-t1-01-memo#p2@T1 6.s1-d1-t1-91-brief#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d3-t1-01-report#p2@T1 9.s6-d3-t1-01-note#p3@T1 10.s6-d2-g2-memo#p2@T1
- 重排前 10：1.s1-d1-t1-91-memo#p1@T1 2.s1-d1-t1-91-brief#p1@T1 3.s7-d0-t1-02-memo#p2@T1 4.s6-d3-t1-01-note#p2@T1 5.s6-d3-t1-01-memo#p2@T1 6.s1-d1-t1-91-brief#p3@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d3-t1-01-note#p3@T1 9.s6-d2-g2-memo#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 181. `r4n-s1-d1-t1-91-qc`

- 问：这个季度用户退款平均几天能到账？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d1-t1-91-brief#p2@T1
- 金标要点：本季度平均退款到账时长为2.6天
- 词法前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s4-d0-t1-91-eval#p2@T1 4.s1-d1-01-analysis#p1@T1 5.s3-d0-02-a#p1@T1 6.s6-d0-t1-91-change#p3@T1 7.s6-d0-t1-91-sop#p3@T1 8.s6-d0-t1-91-change#p1@T1 9.s6-d0-t1-91-sop#p1@T1 10.s5-d2-t1-91-annual#p3@T1
- 混合前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s6-d0-t1-91-sop#p1@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s4-d0-t1-91-eval#p2@T1 6.s4-d2-t1-91-review#p2@T1 7.s3-d0-02-a#p1@T1 8.s1-d0-03-report#p3@T1 9.s6-d0-t1-91-change#p1@T1 10.s6-d3-t1-91-notice#p1@T1
- 重排前 10：1.s1-d1-t1-91-brief#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s4-d0-t1-91-eval#p2@T1 4.s3-d0-02-a#p1@T1 5.s6-d0-t1-91-sop#p1@T1 6.s4-d2-t1-91-model-v3#p2@T1 7.s4-d2-t1-91-review#p2@T1 8.s1-d0-03-report#p3@T1 9.s6-d0-t1-91-change#p1@T1 10.s6-d3-t1-91-notice#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 182. `r4n-s5-d2-t1-91-qa`

- 问：这个本地生活平台按最新年报有多少家在营商户？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-annual#p1@T1
- 金标要点：截至年末活跃商户为53万家
- 词法前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s2-d0-01-report#p2@T1 4.s2-d1-01-memo#p1@T1 5.s5-d2-t1-91-digest#p1@T1 6.s5-d2-t1-91-annual#p3@T1 7.p1-colaw-oneperson#p2@T1 8.s5-d1-t1-03-report#p3@T1 9.s1-d1-t1-91-memo#p3@T1 10.s4-d2-t1-91-model-v3#p3@T1
- 混合前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p3@T1 5.s2-d1-01-memo#p1@T1 6.s2-d0-01-report#p2@T1 7.s6-d3-t1-91-changelog#p2@T1 8.p1-colaw-oneperson#p2@T1 9.s3-d1-t1-91-quote#p2@T1 10.s2-d0-01-memo#p3@T1
- 重排前 10：1.s5-d2-t1-91-annual#p1@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p3@T1 5.s2-d1-01-memo#p1@T1 6.s2-d0-01-report#p2@T1 7.p1-colaw-oneperson#p2@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s3-d1-t1-91-quote#p2@T1 10.s2-d0-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 183. `r4n-s5-d2-t1-91-qb`

- 问：汇编和年报给出的平台活跃商户规模各是多少？汇编的数为什么不能直接用？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-digest#p1@T1；s5-d2-t1-91-annual#p1@T1
- 金标要点：截至年末活跃商户为53万家；该平台活跃商户约48万家；源自两年前的媒体报道
- 词法前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d2-t1-91-digest#p3@T1 5.s6-d3-t1-01-note#p2@T1 6.s1-d1-t1-91-memo#p3@T1 7.s6-d3-t1-02-report#p3@T1 8.s5-d1-t1-03-summary#p2@T1 9.s6-d3-t1-01-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 混合前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d2-t1-91-digest#p3@T1 5.s5-d1-t1-03-summary#p2@T1 6.s5-d2-t1-91-annual#p2@T1 7.s5-d0-t1-02-analysis#p2@T1 8.s5-d1-t1-03-report#p2@T1 9.s6-d3-t1-01-memo#p2@T1 10.s5-d0-t1-02-summary#p3@T1
- 重排前 10：1.s5-d2-t1-91-digest#p1@T1 2.s5-d2-t1-91-annual#p1@T1 3.s5-d2-t1-91-digest#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d0-t1-02-summary#p3@T1 6.s5-d2-t1-91-digest#p3@T1 7.s5-d2-t1-91-annual#p2@T1 8.s5-d0-t1-02-analysis#p2@T1 9.s5-d1-t1-03-report#p2@T1 10.s6-d3-t1-01-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 184. `r4n-s5-d2-t1-91-qc`

- 问：平台商户一年下来的留存比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d2-t1-91-annual#p2@T1
- 金标要点：年度商户留存率为71%
- 词法前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-digest#p1@T1 4.s5-d2-t1-91-annual#p1@T1 5.s2-d0-02-memo#p2@T1 6.s1-d1-t1-91-memo#p3@T1 7.s2-d0-t1-91-memo#p1@T1 8.s2-d0-01-report#p1@T1 9.p1-colaw-governance-supervisor#p3@T1 10.p1-colaw-governance-supervisor-js#p1@T1
- 混合前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-annual#p2@T1 3.s5-d2-t1-91-annual#p1@T1 4.s5-d2-t1-91-digest#p1@T1 5.s2-d0-01-report#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.s5-d2-t1-91-annual#p3@T1 8.s2-d0-t1-91-interview#p1@T1 9.s2-d1-01-memo#p1@T1 10.s1-d0-02-report#p1@T1
- 重排前 10：1.s5-d2-t1-91-digest#p2@T1 2.s5-d2-t1-91-digest#p1@T1 3.s5-d2-t1-91-annual#p2@T1 4.s5-d2-t1-91-annual#p1@T1 5.s2-d0-01-report#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.s2-d0-t1-91-interview#p1@T1 8.s2-d1-01-memo#p1@T1 9.s5-d2-t1-91-annual#p3@T1 10.s1-d0-02-report#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 185. `r4n-s2-d2-t0-91-qb`

- 问：包装材料交期，电话里说的和邮件里确认的各是几天？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-callnotes#p1@T0；s2-d2-t0-91-email#p1@T0
- 金标要点：交期更正为14天；交期为10天
- 词法前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s2-d2-t0-91-callnotes#p2@T0 4.s7-d0-t0-01-internal#p1@T0 5.s5-d1-t0-91-repost#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s2-d2-t0-91-email#p3@T0 8.s7-d1-t0-03-fact#p3@T0 9.s2-d2-t0-91-email#p2@T0 10.s2-d3-01-memo#p1@T0
- 混合前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s2-d2-t0-91-email#p3@T0 4.s2-d2-t0-91-email#p2@T0 5.s7-d1-t0-03-memo#p2@T0 6.p1-cac-o11#p13@T0 7.s2-d2-t0-91-callnotes#p2@T0 8.s1-d0-03-memo#p1@T0 9.s7-d0-t0-01-internal#p1@T0 10.s5-d1-t0-91-repost#p2@T0
- 重排前 10：1.s2-d2-t0-91-callnotes#p1@T0 2.s2-d2-t0-91-email#p1@T0 3.s7-d1-t0-03-memo#p2@T0 4.s2-d2-t0-91-callnotes#p2@T0 5.s7-d0-t0-01-internal#p1@T0 6.s2-d2-t0-91-email#p2@T0 7.p1-cac-o11#p13@T0 8.s1-d0-03-memo#p1@T0 9.s5-d1-t0-91-repost#p2@T0 10.s2-d2-t0-91-email#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 186. `r4n-s2-d2-t0-91-qc`

- 问：这一批货抽检的次品比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d2-t0-91-email#p2@T0
- 金标要点：本批抽检不良率为0.9%
- 词法前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.p1-colaw-governance-supervisor-js#p1@T0 3.p1-colaw-governance-supervisor#p1@T0 4.s2-d2-t0-91-callnotes#p1@T0 5.p1-colaw-equity#p2@T0 6.s2-d2-t0-91-email#p2@T0 7.s7-d1-t0-03-memo#p2@T0 8.s1-d1-01-analysis#p3@T0 9.s1-d0-04-memo#p3@T0 10.s5-d0-t0-01-analysis#p2@T0
- 混合前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.s2-d2-t0-91-email#p2@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.p2-gdp-national#p2@T0 5.p1-colaw-governance-supervisor-js#p1@T0 6.s4-d0-t0-01-report#p2@T0 7.s5-d2-t0-04-analysis#p1@T0 8.p2-gdp-national#p1@T0 9.s5-d1-t0-91-repost#p1@T0 10.p1-colaw-governance-supervisor#p1@T0
- 重排前 10：1.s2-d2-t0-91-callnotes#p2@T0 2.s2-d2-t0-91-email#p2@T0 3.s2-d2-t0-91-callnotes#p1@T0 4.p2-gdp-national#p2@T0 5.p1-colaw-governance-supervisor-js#p1@T0 6.p2-gdp-national#p1@T0 7.p1-colaw-governance-supervisor#p1@T0 8.s4-d0-t0-01-report#p2@T0 9.s5-d2-t0-04-analysis#p1@T0 10.s5-d1-t0-91-repost#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 187. `r4n-s3-d0-t0-91-qa`

- 问：竞品H客服坐席现在每个席位每月什么价？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-pricing#p1@T0
- 金标要点：当前标价为每席每月52美元
- 词法前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d0-t0-91-flyer#p3@T0 4.s3-d0-t0-91-flyer#p2@T0 5.s3-d2-01-competitor-pricing#p3@T0 6.s3-d0-02-a#p1@T0 7.s3-d0-02-b#p2@T0 8.s3-d0-01-report#p2@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s3-d0-04-memo#p2@T0
- 混合前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d0-t0-91-pricing#p1@T0 3.s3-d2-01-competitor-pricing#p3@T0 4.s3-d0-03-report#p1@T0 5.s3-d0-01-memo#p1@T0 6.s3-d0-01-memo#p2@T0 7.s3-d1-01-memo#p1@T0 8.s3-d0-03-memo#p1@T0 9.s3-d0-04-memo#p2@T0 10.s3-d2-01-competitor-pricing#p1@T0
- 重排前 10：1.s3-d0-t0-91-flyer#p1@T0 2.s3-d2-01-competitor-pricing#p3@T0 3.s3-d0-t0-91-pricing#p1@T0 4.s3-d0-03-report#p1@T0 5.s3-d0-01-memo#p1@T0 6.s3-d0-01-memo#p2@T0 7.s3-d1-01-memo#p1@T0 8.s3-d0-03-memo#p1@T0 9.s3-d0-04-memo#p2@T0 10.s3-d2-01-competitor-pricing#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 188. `r4n-s3-d0-t0-91-qc`

- 问：新团队注册竞品H能免费试多久？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d0-t0-91-pricing#p2@T0
- 金标要点：可获得14天免费试用
- 词法前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d0-t0-91-flyer#p3@T0 4.s3-d2-01-competitor-pricing#p2@T0 5.s3-d0-t0-91-flyer#p1@T0 6.s3-d0-03-memo#p2@T0 7.s4-d1-t0-03-analysis#p1@T0 8.s3-d0-03-report#p2@T0 9.s3-d1-01-report#p3@T0 10.s2-d0-03-memo#p3@T0
- 混合前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d2-01-competitor-pricing#p2@T0 4.s3-d0-03-report#p2@T0 5.s3-d0-03-memo#p2@T0 6.s3-d1-01-report#p3@T0 7.s3-d3-01-memo#p3@T0 8.s3-d0-t0-91-flyer#p1@T0 9.s3-d1-01-report#p1@T0 10.s3-d0-01-memo#p3@T0
- 重排前 10：1.s3-d0-t0-91-pricing#p2@T0 2.s3-d0-t0-91-flyer#p2@T0 3.s3-d2-01-competitor-pricing#p2@T0 4.s3-d0-03-memo#p2@T0 5.s3-d0-03-report#p2@T0 6.s3-d1-01-report#p3@T0 7.s3-d3-01-memo#p3@T0 8.s3-d0-t0-91-flyer#p1@T0 9.s3-d0-01-memo#p3@T0 10.s3-d1-01-report#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 189. `r4n-s4-d0-t1-91-qa`

- 问：工单自动分派用全量数据复评后准确率是多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-eval#p1@T1
- 金标要点：自动分派准确率为86%
- 词法前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-eval#p3@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s4-d0-t1-02-guide#p2@T1 7.p1-cac-o11#p12@T1 8.s2-d3-t1-91-minutes#p1@T1 9.s7-d0-t1-02-brief#p2@T1 10.s7-d2-t1-04-claim#p2@T1
- 混合前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.p1-cac-o11#p12@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d0-t1-91-eval#p3@T1 7.s4-d2-t1-04-internal#p1@T1 8.s2-d0-t1-91-memo#p2@T1 9.s4-d2-t1-91-model-v3#p2@T1 10.s7-d2-t1-04-memo#p2@T1
- 重排前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s4-d0-t1-02-guide#p2@T1 6.s4-d0-t1-91-eval#p3@T1 7.s7-d2-t1-04-memo#p2@T1 8.p1-cac-o11#p12@T1 9.s4-d2-t1-04-internal#p1@T1 10.s2-d0-t1-91-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 190. `r4n-s4-d0-t1-91-qb`

- 问：自动分派准确率，汇报材料和复评报告各报了多少？哪个是小样本？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d0-t1-91-deck#p1@T1；s4-d0-t1-91-eval#p1@T1
- 金标要点：自动分派准确率为86%；准确率达到92%；只来自早期小样本
- 词法前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p3@T1 5.s4-d0-t1-91-deck#p2@T1 6.s7-d2-t1-04-memo#p3@T1 7.p1-cac-o11#p12@T1 8.s7-d3-t1-05-synthetic#p2@T1 9.s7-d2-t1-04-brief#p1@T1 10.s7-d0-t1-02-brief#p2@T1
- 混合前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.p1-cac-o11#p12@T1 6.s4-d0-t1-02-guide#p2@T1 7.s4-d2-t1-04-report#p1@T1 8.s6-d3-t1-91-changelog#p2@T1 9.s7-d2-t1-04-memo#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 重排前 10：1.s4-d0-t1-91-eval#p1@T1 2.s4-d0-t1-91-deck#p1@T1 3.s4-d0-t1-91-eval#p2@T1 4.s4-d0-t1-91-deck#p2@T1 5.s4-d2-t1-04-report#p1@T1 6.s7-d2-t1-04-memo#p2@T1 7.p1-cac-o11#p12@T1 8.s4-d0-t1-02-guide#p2@T1 9.s6-d3-t1-91-changelog#p2@T1 10.s6-d3-t1-01-report#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 191. `r4n-s6-d1-t1-91-qa`

- 问：老的v1接口最终什么时候停？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-patch#p1@T1
- 金标要点：下线时间延期至11月30日
- 词法前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-patch#p2@T1 5.s6-d1-t1-91-release#p2@T1 6.s4-d2-t1-04-summary#p3@T1 7.s6-d3-t1-02-memo#p3@T1 8.p1-cac-o11#p12@T1 9.p2-gdp-national#p3@T1 10.s4-d0-t1-02-memo#p3@T1
- 混合前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s6-d1-t1-91-patch#p2@T1 6.s2-d3-01-memo#p3@T1 7.s4-d0-t1-02-memo#p3@T1 8.s6-d3-t1-02-memo#p3@T1 9.s6-d3-t1-91-notice#p1@T1 10.s4-d2-t1-04-summary#p3@T1
- 重排前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s6-d1-t1-91-patch#p2@T1 6.s6-d3-t1-02-memo#p3@T1 7.s4-d2-t1-04-summary#p3@T1 8.s2-d3-01-memo#p3@T1 9.s4-d0-t1-02-memo#p3@T1 10.s6-d3-t1-91-notice#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 192. `r4n-s6-d1-t1-91-qb`

- 问：v1接口下线时间，发布说明和补丁公告分别怎么写的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-release#p1@T1；s6-d1-t1-91-patch#p1@T1
- 金标要点：下线时间延期至11月30日；将于9月30日下线
- 词法前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p3@T1 5.s6-d1-t1-91-patch#p2@T1 6.s5-d0-t1-02-report#p1@T1 7.s5-d1-t1-03-memo#p3@T1 8.s7-d0-t1-02-report#p3@T1 9.p2-gdp-national#p3@T1 10.s3-d2-t1-91-brochure#p1@T1
- 混合前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p3@T1 4.s6-d1-t1-91-release#p2@T1 5.s1-d0-01-analysis#p3@T1 6.s6-d3-t1-02-memo#p1@T1 7.s6-d1-t1-91-patch#p2@T1 8.s3-d2-t1-91-brochure#p1@T1 9.s6-d3-t1-02-report#p1@T1 10.s6-d3-t1-03-report#p1@T1
- 重排前 10：1.s6-d1-t1-91-patch#p1@T1 2.s6-d1-t1-91-release#p1@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p3@T1 5.s6-d1-t1-91-patch#p2@T1 6.s1-d0-01-analysis#p3@T1 7.s6-d3-t1-02-memo#p1@T1 8.s3-d2-t1-91-brochure#p1@T1 9.s6-d3-t1-02-report#p1@T1 10.s6-d3-t1-03-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 193. `r4n-s6-d1-t1-91-qc`

- 问：v2接口最近一周调用成功的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d1-t1-91-patch#p2@T1
- 金标要点：上周v2接口调用成功率为99.2%
- 词法前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s4-d2-t1-91-model-v3#p1@T1 6.s2-d0-t1-91-memo#p1@T1 7.p1-colaw-governance-supervisor#p3@T1 8.p1-colaw-governance-supervisor-js#p1@T1 9.s1-d3-01-memo#p2@T1 10.s6-d1-t1-91-patch#p1@T1
- 混合前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s6-d1-t1-91-patch#p1@T1 6.s4-d0-t1-02-memo#p3@T1 7.s4-d0-t1-91-deck#p2@T1 8.s2-d0-01-report#p1@T1 9.s4-d2-t1-04-summary#p3@T1 10.s2-d3-01-memo#p3@T1
- 重排前 10：1.s6-d1-t1-91-patch#p2@T1 2.s6-d1-t1-91-release#p3@T1 3.s6-d1-t1-91-release#p2@T1 4.s6-d1-t1-91-release#p1@T1 5.s6-d1-t1-91-patch#p1@T1 6.s4-d0-t1-91-deck#p2@T1 7.s4-d2-t1-04-summary#p3@T1 8.s4-d0-t1-02-memo#p3@T1 9.s2-d0-01-report#p1@T1 10.s2-d3-01-memo#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 194. `r4n-s1-d3-t0-91-qb`

- 问：出口增速，研判备忘和统计快报各用的是多少？哪个是修订后的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-memo#p1@T0；s1-d3-t0-91-statbrief#p1@T0
- 金标要点：本季度出口同比增速为6.1%；本季度出口同比增速为5.4%；比初步数下调0.7个百分点
- 词法前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s1-d3-t0-91-statbrief#p3@T0 4.s2-d2-t0-91-callnotes#p2@T0 5.s1-d1-01-analysis#p3@T0 6.s7-d1-t0-03-fact#p3@T0 7.s5-d0-t0-01-analysis#p2@T0 8.p1-cac-o11#p16@T0 9.s1-d3-t0-91-memo#p2@T0 10.s7-d0-t0-01-qa#p1@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.s1-d3-t0-91-statbrief#p3@T0 4.s1-d3-t0-91-memo#p2@T0 5.s1-d3-t0-91-memo#p3@T0 6.s7-d1-t0-03-memo#p2@T0 7.s1-d3-t0-91-statbrief#p2@T0 8.s4-d3-t0-91-method#p1@T0 9.p1-cac-o11#p16@T0 10.s4-d0-t0-01-feedback#p1@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p1@T0 2.s1-d3-t0-91-memo#p1@T0 3.p1-cac-o11#p16@T0 4.s1-d3-t0-91-statbrief#p3@T0 5.s1-d3-t0-91-memo#p2@T0 6.s7-d1-t0-03-memo#p2@T0 7.s4-d3-t0-91-method#p1@T0 8.s4-d0-t0-01-feedback#p1@T0 9.s1-d3-t0-91-memo#p3@T0 10.s1-d3-t0-91-statbrief#p2@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 195. `r4n-s1-d3-t0-91-qc`

- 问：主要港口的货物吞吐比去年同期增长了多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s1-d3-t0-91-statbrief#p2@T0
- 金标要点：主要港口货物吞吐量同比增长3.8%
- 词法前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s2-d0-01-memo#p3@T0 3.s1-d3-t0-91-memo#p2@T0 4.s2-d0-02-report#p1@T0 5.s2-d0-01-report#p1@T0 6.s5-d2-t0-04-analysis#p2@T0 7.s4-d0-t0-01-plan#p2@T0 8.s1-d2-01-report#p1@T0 9.s2-d1-01-report#p3@T0 10.s1-d3-t0-91-statbrief#p1@T0
- 混合前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s1-d3-t0-91-memo#p2@T0 3.s1-d3-t0-91-statbrief#p1@T0 4.s2-d0-01-memo#p3@T0 5.s1-d2-01-report#p1@T0 6.s1-d0-01-memo#p3@T0 7.s2-d0-02-report#p1@T0 8.s2-d1-01-report#p3@T0 9.s1-d3-t0-91-statbrief#p3@T0 10.s1-d3-t0-91-memo#p3@T0
- 重排前 10：1.s1-d3-t0-91-statbrief#p2@T0 2.s2-d0-01-memo#p3@T0 3.s2-d0-02-report#p1@T0 4.s1-d3-t0-91-memo#p2@T0 5.s1-d2-01-report#p1@T0 6.s1-d0-01-memo#p3@T0 7.s2-d1-01-report#p3@T0 8.s1-d3-t0-91-statbrief#p3@T0 9.s1-d3-t0-91-memo#p3@T0 10.s1-d3-t0-91-statbrief#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 196. `r4n-s5-d1-t0-91-qa`

- 问：按原始调研，本地消费者网购渗透率实际是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s5-d1-t0-91-survey#p1@T0
- 金标要点：线上购物渗透率实测为54%
- 词法前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d2-t0-04-memo#p2@T0 5.s1-d0-01-analysis#p2@T0 6.s4-d3-t0-91-method#p1@T0 7.s1-d1-01-report#p3@T0 8.s3-d1-01-memo#p3@T0 9.s5-d1-t0-91-survey#p3@T0 10.s3-d2-01-quotation-snapshot#p2@T0
- 混合前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d1-t0-91-survey#p3@T0 5.s5-d2-t0-04-memo#p2@T0 6.s2-d0-03-memo#p2@T0 7.s1-d0-02-memo#p1@T0 8.s2-d2-01-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s1-d0-01-memo#p1@T0
- 重排前 10：1.s5-d1-t0-91-survey#p1@T0 2.s5-d1-t0-91-repost#p1@T0 3.s2-d1-01-report#p1@T0 4.s5-d2-t0-04-memo#p2@T0 5.s5-d1-t0-91-survey#p3@T0 6.s2-d0-03-memo#p2@T0 7.s1-d0-02-memo#p1@T0 8.s2-d2-01-memo#p2@T0 9.s1-d1-01-memo#p1@T0 10.s1-d0-01-memo#p1@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 197. `r4n-s2-d3-t1-91-qa`

- 问：区域试点今年获批的是几个城市？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-minutes#p1@T1
- 金标要点：会议批准的试点范围是8个城市
- 词法前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s4-d0-t1-91-deck#p2@T1 5.s1-d2-01-report#p1@T1 6.s2-d0-03-memo#p2@T1 7.s1-d1-t1-91-brief#p3@T1 8.s2-d0-02-memo#p2@T1 9.s2-d0-02-interview#p2@T1 10.s5-d1-t1-03-report#p2@T1
- 混合前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d0-02-interview#p2@T1 5.s2-d0-03-memo#p2@T1 6.s1-d2-01-report#p1@T1 7.s1-d1-t1-91-memo#p3@T1 8.s2-d0-02-memo#p2@T1 9.s5-d1-t1-03-report#p2@T1 10.s2-d0-t1-91-interview#p1@T1
- 重排前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d0-03-memo#p2@T1 5.s2-d0-02-memo#p2@T1 6.s5-d1-t1-03-report#p2@T1 7.s2-d0-02-interview#p2@T1 8.s1-d2-01-report#p1@T1 9.s1-d1-t1-91-memo#p3@T1 10.s2-d0-t1-91-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 198. `r4n-s2-d3-t1-91-qb`

- 问：试点城市数量，CEO访谈和董事会纪要说法差在哪？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s2-d3-t1-91-interview#p1@T1；s2-d3-t1-91-minutes#p1@T1
- 金标要点：会议批准的试点范围是8个城市；今年会扩到12个城市
- 词法前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.s6-d0-t1-02-report#p1@T1 7.s6-d0-t1-02-memo#p1@T1 8.s6-d0-t1-02-internal#p1@T1 9.s1-d2-01-report#p1@T1 10.s1-d1-t1-91-memo#p3@T1
- 混合前 10：1.s2-d3-t1-91-minutes#p1@T1 2.s2-d3-t1-91-interview#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.p1-colaw-governance-board#p4@T1 7.p1-colaw-governance-board#p3@T1 8.s1-d2-01-report#p1@T1 9.s2-d0-03-memo#p2@T1 10.s2-d0-t1-91-interview#p1@T1
- 重排前 10：1.s2-d3-t1-91-interview#p1@T1 2.s2-d3-t1-91-minutes#p1@T1 3.s2-d3-t1-91-minutes#p3@T1 4.s2-d3-t1-91-minutes#p2@T1 5.s2-d3-t1-91-interview#p2@T1 6.s2-d0-t1-91-interview#p1@T1 7.p1-colaw-governance-board#p4@T1 8.p1-colaw-governance-board#p3@T1 9.s1-d2-01-report#p1@T1 10.s2-d0-03-memo#p2@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 199. `r4n-s3-d2-t1-91-qa`

- 问：竞品G的合规模块按合同到底收不收钱？多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-contract#p1@T1
- 金标要点：合规模块单独计费每月800元
- 词法前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p2@T1 3.s3-d2-t1-91-contract#p1@T1 4.s3-d2-t1-91-brochure#p3@T1 5.s6-d1-c3-memo#p2@T1 6.s3-d2-t1-91-brochure#p2@T1 7.s3-d1-t1-91-quote#p1@T1 8.s2-d0-t1-91-memo#p1@T1 9.s3-d2-01-quotation-snapshot#p2@T1 10.s3-d1-t1-91-pricesheet#p1@T1
- 混合前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-01-report#p1@T1 9.s3-d1-01-memo#p3@T1 10.s3-d0-03-report#p1@T1
- 重排前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p2@T1 3.s3-d2-t1-91-contract#p1@T1 4.s3-d1-t1-91-quote#p1@T1 5.s3-d1-t1-91-pricesheet#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d1-01-memo#p3@T1 9.s3-d0-03-report#p1@T1 10.s3-d1-01-report#p1@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 200. `r4n-s3-d2-t1-91-qb`

- 问：竞品G合规模块的收费，宣传册和合同报价单怎么说的？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-brochure#p1@T1；s3-d2-t1-91-contract#p1@T1
- 金标要点：合规模块单独计费每月800元；数据合规模块免费附送；只适用于首年促销
- 词法前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-brochure#p3@T1 4.s3-d2-t1-91-brochure#p2@T1 5.s3-d2-t1-91-contract#p2@T1 6.s3-d2-t1-91-contract#p3@T1 7.s2-d0-t1-91-memo#p1@T1 8.s3-d2-01-quotation-snapshot#p2@T1 9.s6-d1-c3-memo#p2@T1 10.s3-d1-t1-91-pricesheet#p2@T1
- 混合前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-contract#p2@T1 4.s3-d1-t1-91-pricesheet#p1@T1 5.s3-d2-t1-91-brochure#p2@T1 6.s3-d2-01-quotation-snapshot#p2@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s3-d2-t1-91-contract#p3@T1 9.s3-d1-01-report#p1@T1 10.s3-d2-t1-91-brochure#p3@T1
- 重排前 10：1.s3-d2-t1-91-brochure#p1@T1 2.s3-d2-t1-91-contract#p1@T1 3.s3-d2-t1-91-contract#p2@T1 4.s3-d2-t1-91-brochure#p2@T1 5.s3-d2-01-quotation-snapshot#p2@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s3-d2-t1-91-brochure#p3@T1 8.s3-d1-t1-91-pricesheet#p1@T1 9.s3-d2-t1-91-contract#p3@T1 10.s3-d1-01-report#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 201. `r4n-s3-d2-t1-91-qc`

- 问：竞品G在合同里承诺的服务可用性是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s3-d2-t1-91-contract#p2@T1
- 金标要点：SLA承诺为99.95%
- 词法前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-brochure#p3@T1 3.s6-d0-t1-91-sop#p2@T1 4.s2-d0-t1-91-memo#p1@T1 5.s3-d2-t1-91-brochure#p1@T1 6.s3-d2-t1-91-brochure#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s4-d2-t1-04-summary#p2@T1 9.s1-d1-t1-91-memo#p2@T1 10.s2-d0-t1-91-interview#p2@T1
- 混合前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d0-03-memo#p1@T1 3.s3-d2-t1-91-brochure#p1@T1 4.s3-d1-t1-91-pricesheet#p2@T1 5.s3-d0-03-report#p1@T1 6.s3-d3-01-report#p2@T1 7.s3-d1-01-report#p1@T1 8.s3-d0-04-memo#p1@T1 9.s2-d0-t1-91-memo#p1@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 重排前 10：1.s3-d2-t1-91-contract#p2@T1 2.s3-d2-t1-91-brochure#p1@T1 3.s3-d1-t1-91-pricesheet#p2@T1 4.s3-d0-03-report#p1@T1 5.s3-d3-01-report#p2@T1 6.s2-d0-t1-91-memo#p1@T1 7.s3-d0-03-memo#p1@T1 8.s3-d1-01-report#p1@T1 9.s3-d0-04-memo#p1@T1 10.s3-d2-01-competitor-pricing#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 202. `r4n-s4-d3-t0-91-qb`

- 问：电力折标煤系数，测算表和方法更新说明各取多少？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-calc#p1@T0；s4-d3-t0-91-method#p1@T0
- 金标要点：该折算系数应为0.76；系数取0.82
- 词法前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s3-d2-01-quotation-snapshot#p3@T0 6.s7-d1-t0-03-claim#p2@T0 7.s7-d0-t0-01-qa#p1@T0 8.s7-d1-t0-03-fact#p3@T0 9.s3-d0-t0-91-pricing#p2@T0 10.s1-d1-01-analysis#p2@T0
- 混合前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s4-d3-t0-91-calc#p3@T0 6.s4-d0-t0-01-summary#p1@T0 7.s1-d3-t0-91-statbrief#p3@T0 8.s2-d2-t0-91-email#p1@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d1-t0-03-memo#p1@T0
- 重排前 10：1.s4-d3-t0-91-calc#p1@T0 2.s4-d3-t0-91-method#p1@T0 3.s4-d3-t0-91-method#p3@T0 4.s4-d3-t0-91-calc#p2@T0 5.s4-d0-t0-01-summary#p1@T0 6.s2-d2-t0-91-email#p1@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d1-t0-03-memo#p1@T0 9.s4-d3-t0-91-calc#p3@T0 10.s1-d3-t0-91-statbrief#p3@T0
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 203. `r4n-s4-d3-t0-91-qc`

- 问：今年产线实际利用了多少产能？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s4-d3-t0-91-method#p2@T0
- 金标要点：本年度产线利用率为78%
- 词法前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d3-t0-91-method#p2@T0 3.s4-d0-t0-01-summary#p1@T0 4.s1-d0-02-report#p2@T0 5.s7-d0-t0-01-internal#p1@T0 6.s7-d0-t0-01-memo#p1@T0 7.s7-d0-t0-01-arch#p1@T0 8.s2-d0-04-memo#p2@T0 9.s7-d0-t0-01-qa#p2@T0 10.p1-cac-o11#p10@T0
- 混合前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d3-t0-91-method#p2@T0 3.s1-d0-02-report#p2@T0 4.s2-d0-04-memo#p2@T0 5.s4-d0-t0-01-summary#p1@T0 6.s4-d3-t0-91-calc#p3@T0 7.s4-d0-t0-01-memo#p1@T0 8.s4-d1-t0-03-memo#p1@T0 9.s7-d0-t0-01-internal#p1@T0 10.s7-d0-t0-01-arch#p1@T0
- 重排前 10：1.s4-d3-t0-91-calc#p2@T0 2.s4-d0-t0-01-summary#p1@T0 3.s7-d0-t0-01-internal#p1@T0 4.s7-d0-t0-01-arch#p1@T0 5.s4-d3-t0-91-method#p2@T0 6.s1-d0-02-report#p2@T0 7.s2-d0-04-memo#p2@T0 8.s4-d3-t0-91-calc#p3@T0 9.s4-d0-t0-01-memo#p1@T0 10.s4-d1-t0-03-memo#p1@T0
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 204. `r4n-s6-d0-t1-91-qb`

- 问：退款要主管审批的金额线，手册和变更单各写的是多少？
- 题型：字面题（lexical） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-sop#p1@T1；s6-d0-t1-91-change#p1@T1
- 金标要点：金额在300美元以上的退款需要主管审批；退款审批阈值改为500美元以上
- 词法前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d0-t1-91-sop#p3@T1 4.s6-d0-t1-91-sop#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.s1-d1-t1-91-memo#p2@T1 7.s2-d3-t1-91-interview#p2@T1 8.p1-colaw-liquidation#p2@T1 9.s6-d0-t1-01-patch#p2@T1 10.s6-d3-t1-03-memo#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d3-t1-03-memo#p2@T1 4.s6-d0-t1-91-change#p3@T1 5.s1-d1-t1-91-memo#p2@T1 6.s6-d2-g2-memo#p2@T1 7.s6-d0-t1-01-patch#p2@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s6-d0-t1-91-sop#p3@T1
- 重排前 10：1.s6-d0-t1-91-sop#p1@T1 2.s6-d0-t1-91-change#p1@T1 3.s6-d3-t1-03-memo#p2@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d2-g2-memo#p2@T1 6.s6-d0-t1-01-patch#p2@T1 7.s6-d0-t1-91-sop#p3@T1 8.s6-d3-t1-03-memo#p3@T1 9.s6-d3-t1-91-changelog#p1@T1 10.s6-d0-t1-91-change#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 205. `r4n-s6-d0-t1-91-qc`

- 问：客服上个月一次就把问题解决的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：是
- 金标证据：s6-d0-t1-91-change#p2@T1
- 金标要点：上月首次解决率为74%
- 词法前 10：1.s6-d0-t1-91-sop#p2@T1 2.s1-d1-t1-91-memo#p2@T1 3.s2-d0-t1-91-memo#p1@T1 4.s2-d0-04-memo#p3@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-03-interview#p3@T1 7.s6-d2-t1-91-audit#p1@T1 8.s6-d2-t1-91-bulletin#p1@T1 9.s1-d3-01-memo#p2@T1 10.s6-d0-t1-91-change#p2@T1
- 混合前 10：1.s6-d0-t1-91-sop#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s6-d0-t1-91-change#p2@T1 4.s2-d0-t1-91-memo#p1@T1 5.s2-d0-02-report#p3@T1 6.s2-d0-t1-91-memo#p2@T1 7.s1-d1-t1-91-memo#p2@T1 8.s6-d0-t1-91-sop#p1@T1 9.s2-d2-01-report#p2@T1 10.s6-d2-t1-91-bulletin#p1@T1
- 重排前 10：1.s6-d0-t1-91-sop#p2@T1 2.s2-d0-t1-91-interview#p2@T1 3.s2-d0-t1-91-memo#p1@T1 4.s1-d1-t1-91-memo#p2@T1 5.s6-d0-t1-91-change#p2@T1 6.s2-d0-02-report#p3@T1 7.s2-d0-t1-91-memo#p2@T1 8.s6-d0-t1-91-sop#p1@T1 9.s6-d2-t1-91-bulletin#p1@T1 10.s2-d2-01-report#p2@T1
- 建议：可议 hybrid
- 理由：两边都碰上了金标，混合把金标排得更靠前。

### 206. `r4n-s6-d2-t1-91-qa`

- 问：夜班也算进去的话，仓库安检过关的比例是多少？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-audit#p1@T1
- 金标要点：仓库安检通过比例写成百分之九十一
- 词法前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s2-d0-t1-91-memo#p1@T1 4.p1-colaw-governance-supervisor#p1@T1 5.p1-colaw-governance-supervisor#p3@T1 6.p1-colaw-governance-supervisor-js#p1@T1 7.s3-d2-t1-91-contract#p2@T1 8.s6-d2-t1-91-audit#p3@T1 9.p1-colaw-equity#p1@T1 10.s6-d0-t1-91-sop#p2@T1
- 混合前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s6-d2-t1-91-audit#p3@T1 4.s2-d0-t1-91-memo#p1@T1 5.s4-d2-t1-91-model-v3#p2@T1 6.s2-d0-t1-91-interview#p2@T1 7.p1-colaw-governance-supervisor#p1@T1 8.p1-colaw-governance-supervisor#p3@T1 9.s3-d2-t1-91-contract#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 重排前 10：1.s6-d2-t1-91-audit#p1@T1 2.s6-d2-t1-91-bulletin#p1@T1 3.s2-d0-t1-91-memo#p1@T1 4.s4-d2-t1-91-model-v3#p2@T1 5.s2-d0-t1-91-interview#p2@T1 6.p1-colaw-governance-supervisor#p1@T1 7.p1-colaw-governance-supervisor#p3@T1 8.s3-d2-t1-91-contract#p2@T1 9.s4-d0-t1-91-deck#p2@T1 10.s6-d2-t1-91-audit#p3@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 207. `r4n-s6-d2-t1-91-qb`

- 问：一份只覆盖白班，另一份把夜班补了进去，过关比例两边分别是什么？
- 题型：要拼多处（multi_hop） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-bulletin#p1@T1；s6-d2-t1-91-audit#p1@T1
- 金标要点：仓库安检通过比例写成百分之九十六；仓库安检通过比例写成百分之九十一
- 词法前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s7-d3-t1-05-memo#p2@T1 4.s5-d1-t1-03-summary#p2@T1 5.s5-d2-t1-91-digest#p2@T1 6.s7-d2-t1-04-data#p3@T1 7.s7-d2-t1-04-claim#p2@T1 8.s7-d0-t1-02-memo#p2@T1 9.s7-d2-t1-04-data#p2@T1 10.s7-d2-t1-04-memo#p2@T1
- 混合前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s6-d2-t1-91-audit#p3@T1 4.s7-d2-t1-04-data#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s3-d1-t1-91-pricesheet#p2@T1 7.s6-d3-t1-91-changelog#p1@T1 8.s7-d2-t1-04-claim#p2@T1 9.s4-d2-t1-91-review#p3@T1 10.s2-d3-t1-91-interview#p1@T1
- 重排前 10：1.s6-d2-t1-91-bulletin#p1@T1 2.s6-d2-t1-91-audit#p1@T1 3.s7-d2-t1-04-claim#p2@T1 4.s7-d2-t1-04-data#p3@T1 5.s2-d0-t1-91-memo#p1@T1 6.s6-d2-t1-91-audit#p3@T1 7.s3-d1-t1-91-pricesheet#p2@T1 8.s6-d3-t1-91-changelog#p1@T1 9.s4-d2-t1-91-review#p3@T1 10.s2-d3-t1-91-interview#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。

### 208. `r4n-s6-d2-t1-91-qc`

- 问：这个月仓库里工伤报了几起？
- 题型：换一种说法（paraphrase） · 类别：陷阱（trap） · 合成模板陷阱：否
- 金标证据：s6-d2-t1-91-audit#p2@T1
- 金标要点：该月因工受伤为七件
- 词法前 10：1.s6-d2-t1-91-bulletin#p2@T1 2.s6-d1-t1-91-release#p2@T1 3.s6-d2-t1-91-audit#p1@T1 4.s6-d2-t1-91-bulletin#p1@T1 5.s2-d0-t1-91-interview#p2@T1 6.s2-d0-t1-91-memo#p1@T1 7.s3-d1-t1-91-quote#p3@T1 8.s6-d0-t1-91-sop#p2@T1 9.s2-d3-t1-91-interview#p2@T1 10.s4-d0-t1-91-deck#p2@T1
- 混合前 10：1.s6-d2-t1-91-bulletin#p2@T1 2.s6-d2-t1-91-audit#p1@T1 3.s6-d2-t1-91-bulletin#p1@T1 4.s2-d0-t1-91-interview#p2@T1 5.s6-d2-t1-91-audit#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s6-d0-t1-91-sop#p2@T1 9.s6-d2-t1-91-audit#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 重排前 10：1.s2-d0-t1-91-interview#p2@T1 2.s6-d2-t1-91-bulletin#p2@T1 3.s6-d2-t1-91-audit#p1@T1 4.s6-d2-t1-91-bulletin#p1@T1 5.s6-d2-t1-91-audit#p2@T1 6.s2-d0-t1-91-memo#p2@T1 7.s4-d0-t1-91-deck#p2@T1 8.s6-d0-t1-91-sop#p2@T1 9.s6-d2-t1-91-audit#p3@T1 10.s6-d0-t1-03-internal#p1@T1
- 建议：保持 bm25
- 理由：金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。
