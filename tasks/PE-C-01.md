# PE-C-01 · 强制抄句生成缝 + 同 after 继承夹具

## Parent

Part of #484（spec）· #485· #485 · 地图 #482 · 决议 #483

## Destination

实装路线 C 增量：T `after_text` 强制抄句硬契约；正确槽可抄保证；保持 T/B1 同 after 再分叉。不激活 `PREREG-C`，不发模型，不改 B 归档。

## Acceptance criteria

- [ ] T 契约路径产出的 after 去空白后与 `evidence_text` 逐字相同（单测可证；非仅断言提示词含子串）
- [ ] 同 after 夹具：绑定缝类坏样上 T reject / B1 release 可复现
- [ ] 未放松 `verify_edit` 逐字语义；T 核验不过仍 hard reject
- [ ] 未改 `PREREG-B` / `RESULT-B` / `formal-generations-b`；未激活 `PREREG-C`
- [ ] `python -m compileall -q src` 与相关 `pytest` 绿

## Agent Guards

- **ID**: PE-C-01 · **Trust**: Watch · **Blast**: none  
- **Paths**: `src/freshlatch/eval/`（生成/arms 旁路或扩展）；`tests/unit/test_pe_*`；`docs/evidence/patch-events/prompts/`（若需 C 专用提示，须标明补定 draft≠预注册）  
- **Do-not-touch**: B 归档；旧 PREREG；主比较成立定义；ALT 主表；金标进 score  

## Blocked by

无（文档四件套已落）。若 B 机制未合 main：base 须含选取 R + 同 after，或票内写明依赖 PR。
