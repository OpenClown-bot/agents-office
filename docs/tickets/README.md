# Task Tickets

Owner: **Technical Architect** writes them. **Code Executors** consume them.

## Rules

- Every ticket MUST reference an approved ArchSpec (`arch_ref: ARCH-NNN@X.Y.Z`).
- A ticket is atomic: one concern, one sentence Goal.
- `NOT In Scope` is mandatory and must be non-empty.
- `assigned_executor` is a suggestion; the orchestrator (you) may reassign.
- `status: ready` means the ticket is unambiguous and the Executor can start immediately.

## Lifecycle

`draft → ready → in_progress → in_review → done` (or `blocked` if a `Q-TKT-*` is open).
