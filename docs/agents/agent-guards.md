# Agent Guards (per-repo)

## Ticket location
- **Mode**: github
- **Tracker**: GitHub Issues via `gh` (see `.claude/rules/issue-tracker.md`)
- **Local mirror (optional)**: `tasks/**/*.md` (exclude `tasks/done/**`, `tasks/_template.md`)
- **Done folder**: `tasks/done/`

## Defaults
- **Default Trust**: Watch
- **Auto allowed when**: Blast is only `ui` or `none`, and Provenance kind is `new`
- **Gate when**: Blast includes `auth` or `db` or `pay`, or ticket says production
- **Ticket ID pattern**: `^[A-Z]+-[0-9]+(\.[0-9]+)?$` OR `^(?i)(feat|fix|refactor|chore|spike)-[0-9]{8}-[0-9]{3}$` OR `^#?[0-9]+$` (GitHub issue number)

## Thin required fields
- Always: ID, Acceptance (≥1 executable), Paths
- Provenance when Paths touch existing code or Kind is adapt|port
- Trust/Blast: auto from rules; human confirms on Gate

## Evidence (after Matt /implement)
Three lines only: typecheck exit · tests exit · paths ok|drift

## Matt Pocock
```text
grill-with-docs → to-spec → to-tickets → enrich-tickets → before-implement → /implement
```
Install separately: `npx skills add mattpocock/skills`

## Hooks
Advanced/optional — not enabled in this repo by default.

L4-SK-01 样板放在 `docs/agents/hooks/`，对应清单 A-SK-01。Cursor 只自动加载仓库根的 `.cursor/hooks.json`（以及用户级 `~/.cursor/hooks.json`）。样板不在这两处，所以默认不启用，现有开发环保持原样。`.cursor/` 已在 `.gitignore` 中；本票不提交 `.cursor/hooks.json`。

样板两份文件：

- `docs/agents/hooks/hooks.json`：`beforeShellExecution` 一条，`failClosed` 为 `true`
- `docs/agents/hooks/deny_exit_2.py`：读完 stdin 后以退出码 2 结束

Cursor 命令钩子约定：退出码 `2` 等于 `permission: "deny"`，这次动作被拒绝。退出码 `0` 时采用 stdout 的 JSON。其他退出码默认放行。`failClosed: true` 时，脚本崩溃、超时、非 0 退出或没有输出也拒绝该动作。样板把 `failClosed` 设为 `true`，并且脚本固定返回退出码 2。

该样板不进入 `run_loop`，不改 `src/freshlatch/roles/loop.py`，也不替换 `LEAD_TOOLS_W3` 工具白名单。

### 如何显式启用

只在本机演练。启用结果留在本机，不要提交。

1. 把 `docs/agents/hooks/hooks.json` 复制为仓库根的 `.cursor/hooks.json`。
2. 保存后 Cursor 重载 project hooks。命令相对仓库根执行：`python docs/agents/hooks/deny_exit_2.py`。
3. 演练：在已启用的工作区里让 Agent 执行一条 shell。脚本返回退出码 2，Cursor 拒绝这次 `beforeShellExecution`。`failClosed: true` 写在样板里，钩子自身失败时同样拒绝。
4. 停用：删除本机 `.cursor/hooks.json`。

启用之后，每一次 shell 都会被这个样板拒绝，直到删除本机 `.cursor/hooks.json`。这是拒绝演练，用来核对退出码 2 与 `failClosed`。

## Authority commands
- typecheck: `python -m compileall -q src`
- test: `pytest`
- lint: `ruff check`（规则集锁在 `pyproject.toml` 的 `[tool.ruff.lint] select`；首版只拦语法级与未定义名）
