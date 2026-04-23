# Architecture Specifications

Owner: **Technical Architect** (Opus 4.6 Thinking).

## Rules

- 1 PRD → 1 ArchSpec. Cross-epic architecture goes into separate, higher-level specs (create a new `ARCH-NNN`, do not mash).
- Must pin `prd_ref` to a specific PRD version (`PRD-NNN@X.Y.Z`).
- Every tech-stack choice backed by an `ADR-NNN` under `adr/`.
- Work Breakdown enumerates tickets; tickets live in `docs/tickets/`.
- Resource budget MUST fit the PRD's Technical Envelope. If it doesn't, escalate back to Business with `Q_TO_BUSINESS`.

## Lifecycle

Same as PRD: `draft → in_review → approved → superseded`.
