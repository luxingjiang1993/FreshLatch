# 流程启动 · 停在第一步

日期：2026-10-08。基线是 main `3d9b084`。这一页只记录技能查找和停点。不是预注册，不改 `PREREG.md`，不改 `RESULT.md`，不写提示词正文，不填温度，不发请求。

## 要走的链

`grill-with-docs` → `to-spec` → `to-tickets` → `enrich-tickets` → `before-implement` → `/implement`

闸门技能名：`setup-agent-guards`、`enrich-tickets`、`provenance-check`、`before-implement`。闸门技能不写代码。没有 `/implement` 就不算跑过实现。

## 查找

查了本仓 `SKILL.md`、`docs/agents/`、`.claude/`，以及本机会话的 skill 列表（`/home/ubuntu/.cursor/skills-cursor` 与已装插件）。

仓里有的是配置和提示词模板，不是这链上的 skill：

- `docs/agents/agent-guards.md` 写明 Matt 技能要另装：`npx skills add mattpocock/skills`
- `docs/agents/HOW-TO-AGENTS-TASK.md` 写明闸门要另装：`npx skills@latest add luxingjiang1993/agent-guards-skills`，然后才是 `/setup-agent-guards`
- `docs/prompts/grill-with-docs-freshlatch.md` 是一段给人手贴的开场模板
- `docs/spec/22-工程卫生与可维护性整改.md` 写明本仓未安装 upstream `/to-spec` skill

没有找到这些 skill 文件：`grill-with-docs`、`to-spec`、`to-tickets`、`enrich-tickets`、`provenance-check`、`before-implement`、`setup-agent-guards`、`/implement`。

## 停点

停在链的第一步 `grill-with-docs`。这一步的 skill 不在仓库里，也不在本会话的 skill 列表里。

没有往下走。没有跑 `to-spec`、`to-tickets`、`enrich-tickets`、`provenance-check`、`before-implement`、`/implement`。没有拆票。没有自己编一套替代流程。

三块工作都还没进票：提示词空段与温度、生成器；四臂 n=30 与 T 的消融；把跑出来的指标填进结果表。抽检一致率和用户对评委 κ 这一轮没有填。
