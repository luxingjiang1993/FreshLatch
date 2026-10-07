# AGENTS.md — slim (with Agent Guards + Matt Pocock)

Keep this short. Per-ticket state lives in `tasks/*.md` (or Matt’s tracker), not here.

## Role
- **Human**: goal, Trust, ship / merge
- **Agent**: explore → plan → implement; never self-approve Gate
- **Validators**: typecheck, tests, Matt `/code-review`, optional hooks

## Authority commands (edit per repo)
- Package manager: `pip` (`pip install -e ".[dev]"`; pins in `requirements.txt` and `pyproject.toml`)
- Typecheck: `python -m compileall -q src`
- Test: `pytest`
- Lint: `ruff check`

## Agent Guards
Config: `docs/agents/agent-guards.md` (from `/setup-agent-guards`).

Daily chain:

```text
grill-with-docs → to-spec → to-tickets → enrich-tickets → before-implement → /implement
```

- After Matt `/to-tickets` → `/enrich-tickets`
- Before coding → `/before-implement <id>` then **fresh** session `/implement`
- Do **not** use a custom implement loop; Matt owns TDD + code-review

## Ticket rules (thin)
- **Required on each ticket**: ID, Acceptance (≥1 executable), Paths
- **Provenance** when Paths touch existing code or Kind is adapt|port (path and/or pinned URL)
- **Trust / Blast**: usually auto-filled by enrich; Gate if auth|db|pay
- Branch / PR / commit: include Ticket ID
- One ticket ≈ one agent session

## Done
- Typecheck + tests green (authority commands)
- Acceptance checked by human (Watch/Gate)
- Evidence on ticket ≤3 lines (typecheck · tests · paths)
- No `git reset --hard` / force-push unless asked this turn

## Stop and ask
Scope leave · secrets/prod/authz · missing Acceptance/Paths · Provenance fail · two failed approaches · low confidence

## Trust / Autonomy
Auto | Watch | Gate · default Autonomy A3 unless stated (A5 merge/deploy = human)
