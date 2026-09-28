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

## Authority commands
- typecheck: `python -m compileall -q src`
- test: `pytest`
- lint: *(none locked; optional `ruff` if added later)*
