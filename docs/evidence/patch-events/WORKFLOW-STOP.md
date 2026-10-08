# 流程启动 · 技能已装，停在 grill 第一轮

日期：2026-10-08。基线是 main `3d9b084`。这一页记录技能安装和停点。不是预注册，不改 `PREREG.md`，不改 `RESULT.md`，不写提示词正文，不填温度，不发请求。

## 要走的链

`grill-with-docs` → `to-spec` → `to-tickets` → `enrich-tickets` → `before-implement` → `/implement`

闸门技能不写代码。没有跑完 `/implement` 就不算实现。

## 安装

在本会话执行：

- `npx skills add mattpocock/skills -g -y --copy --agent cursor`，只装链上要读的 skill
- `npx skills@latest add luxingjiang1993/agent-guards-skills -g -y --copy --agent cursor`

装上并能读到 `SKILL.md` 的：

| 调用名 | 文件 | 状态 |
| --- | --- | --- |
| `grill-with-docs` | `~/.agents/skills/grill-with-docs/SKILL.md` | 已装 |
| `to-spec` | `~/.agents/skills/to-spec/SKILL.md` | 已装 |
| `to-tickets` | `~/.agents/skills/to-tickets/SKILL.md` | 已装 |
| `setup-agent-guards` | `~/.agents/skills/setup-agent-guards/SKILL.md` | 已装 |
| `enrich-tickets` | `~/.agents/skills/enrich-tickets/SKILL.md` | 已装 |
| `provenance-check` | `~/.agents/skills/provenance-check/SKILL.md` | 已装 |
| `before-implement` | `~/.agents/skills/before-implement/SKILL.md` | 已装 |
| `/implement` | `~/.agents/skills/implement/SKILL.md` | 已装。技能名是 `implement`，没有单独的 `/implement` 文件 |

`grill-with-docs` 要求再读 `grilling` 和 `domain-modeling`。这两份也已装：`~/.agents/skills/grilling/SKILL.md`、`~/.agents/skills/domain-modeling/SKILL.md`。

没装、因此不往下替代的：`tdd`、`code-review`。`implement` 写明要调用它们。这一轮还没到 `/implement`，所以不现编这两步。`setup-matt-pocock-skills` 也没装。本仓已有 `docs/agents/agent-guards.md`，这一轮不重写它。

## 停点

按已装的 `grill-with-docs` 读了 `grilling` 和 `domain-modeling`。`grilling` 要求先问完这一轮，等回答，共享理解确认之前不往下做。

没有跑 `to-spec`、`to-tickets`、`enrich-tickets`、`provenance-check`、`before-implement`、`/implement`。没有拆票。没有改词表，没有新 ADR。`CONTEXT.md` 里没有和这三块冲突的已定词。

## grill 第一轮

问句在 PR 说明里。推荐都是「是」：四段空白和高分方向继续留空；温度不新写数值；实跑和填表可以日后建票，但现在被温度和这些空白挡住。
