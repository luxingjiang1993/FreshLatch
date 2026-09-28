# How to use AGENTS.md + tickets with Agent Guards

## What each file is for

| File | Role |
|------|------|
| `AGENTS.md` | Always-on repo rules (Done, stop, Trust defaults, authority commands) |
| `tasks/<ID>.md` | One slice: what to build + Agent Guards fields |
| Agent Guards skills | How to enrich / gate / hand off to Matt `/implement` |
| Matt skills | Spec, tickets, TDD implement, code-review |

Skills do **not** replace AGENTS or tickets. They assume both exist (thinly).

## Recommended loop

1. `/grill-with-docs` → `/to-spec` → `/to-tickets` (Matt)
2. `/enrich-tickets` — fills thin Guards; you approve the table
3. `/before-implement <ID>` — gate only
4. **New session** `/implement` (Matt) for that one ticket
5. Fill Evidence (3 lines); move ticket to `tasks/done/` when you confirm

## Setup once

```bash
npx skills@latest add luxingjiang1993/agent-guards-skills
npx skills add mattpocock/skills
```

In the agent: `/setup-agent-guards`

Optionally copy starter templates from this pack:

- `docs/repo-templates/AGENTS.md` → repo root (merge; don’t duplicate Agent Guards section)
- `docs/repo-templates/TASK.md` → `tasks/_template.md`

## What you still fill by hand

Usually: **goal one-liner** + **Trust** (and skim Acceptance / Paths / Provenance). Everything else can be drafted by enrich.
