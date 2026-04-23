# Product Requirements Documents (PRDs)

Owner: **Business Planner** (Opus 4.7 via Claude.ai web).

## Rules

- 1 epic = 1 PRD. Do not combine epics.
- Filename pattern: `PRD-NNN-<kebab-slug>.md`.
- Scaffold with: `python scripts/new_artifact.py prd "Title"`.
- Never edit a PRD with status `approved` — bump the version (`1.0.0 → 1.1.0`) and save the change as a new revision (git diff is your audit trail).

## Lifecycle

`draft` → `in_review` (Reviewer opens `docs/reviews/RV-SPEC-*` referencing this PRD) → `approved` → (later) `superseded` if replaced.
