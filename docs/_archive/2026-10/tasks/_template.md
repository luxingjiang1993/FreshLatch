# TASK / ticket — one slice (copy to `tasks/<ID>.md`)

Matt `/to-tickets` may create this file; `/enrich-tickets` fills **Agent Guards**. Humans mainly set **Trust** and skim Acceptance / Paths / Provenance.

## Ticket
- **ID**:
- **Title**: `TYPE(scope): …`
- **Paths**:

## Agent Guards
- **Blast**: none | ui | types | api | db | auth *(auto OK)*
- **Trust**: Auto | Watch | Gate *(you confirm on Gate)*
- **Acceptance**: *(≥1 executable Given/When/Then or exact command)*
- **Provenance**: *(only if adapt/port / existing Paths)*
  - Kind: new | adapt | port | generated
  - Source: `path#symbol` and/or `https://…`
  - Pin: *(SHA/tag if URL)*
  - What changed:
  - Why not copy as-is:
  - License note:
- **Tests**: added | updated | waived(reason + due) *(optional if Auto/ui)*
- **Rollback**: *(optional)*
- **Do-not-touch**: *(optional)*

### Provenance status
- result: pass | warn | fail
- notes:

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`[time] | [id] | [done|blocked] | [next]`
