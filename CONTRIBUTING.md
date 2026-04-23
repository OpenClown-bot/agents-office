# Contributing — Process Rules

This file defines **how humans and LLMs collaborate** in this repo. These are not suggestions. CI enforces the machine-checkable parts; Reviewers enforce the rest.

## Roles

| Role | Model | Writes | Never writes |
|---|---|---|---|
| Product Owner (human) | — | Anything (final authority) | — |
| Business Planner | Opus 4.7 (Claude.ai web) | `docs/prd/` | `docs/architecture/`, `src/` |
| Tech Architect | Opus 4.6 Thinking | `docs/architecture/`, `docs/tickets/` | `docs/prd/`, `src/` |
| Reviewer | Kimi K2.6 (opencode) | `docs/reviews/` | Everything else |
| Code Executor (primary) | GLM 5.1 (opencode) | `src/`, `tests/`, may append to `docs/tickets/<id>.md#Execution Log` and `docs/questions/` | `docs/prd/`, `docs/architecture/`, anything outside assigned ticket's `In Scope` |
| Code Executor (parallel) | Qwen 3.6 Plus (opencode) | Same as primary | Same as primary |
| Code Executor (specialist) | Codex GPT 5.3 | Same as primary | Same as primary |

## Hard rules

1. **Never skip upstream.** You cannot write a Ticket without an approved ArchSpec. You cannot write an ArchSpec without an approved PRD.
2. **Version-pinned references only.** Inside any artifact, reference upstream docs by `ID@version`, e.g. `PRD-001@1.2.0`. Bare `PRD-001` is rejected by CI.
3. **Status gates.**
   - `draft` → anyone may edit.
   - `in_review` → only Reviewer adds comments in a separate `docs/reviews/RV-*.md`.
   - `approved` → immutable. Any change = bump version and create a new revision.
   - `superseded` → read-only; `superseded_by` must point to the replacement.
4. **Non-goals / NOT In Scope are mandatory.** PRDs must list ≥1 Non-Goal. Tickets must list ≥1 "NOT In Scope" item.
5. **Executor guardrails.**
   - Executor may ONLY modify files explicitly listed in the Ticket's `Outputs`.
   - If a Ticket is ambiguous or contradicts the ArchSpec, Executor MUST stop and create `docs/questions/Q-TKT-XXX-NN.md` before writing code.
   - Executor may NOT add new dependencies unless explicitly allowed in the Ticket's `Constraints`.
6. **Reviewer independence.** Reviewer must be a different model family from the Architect. A Claude-written ArchSpec must not be reviewed by another Claude.
7. **No secrets in git.** Ever. Use `.env.example` and document in ArchSpec §9 Security.

## Handoff contracts

Each artifact ends with a "Handoff Checklist". CI validates the frontmatter; Reviewer validates the checklist.

## Change requests

If Business wants to change an already-approved PRD:

1. Bump PRD version (e.g. `1.0.0 → 1.1.0`).
2. Open a PR modifying the PRD.
3. Architect reviews the PR and annotates which ArchSpec sections are impacted.
4. Affected ArchSpec is bumped, re-reviewed, and affected Tickets are re-opened or split.

**Do not** let a "small tweak" propagate silently to code. Every change walks the pipeline.

## Parallelism

- Multiple Tickets may be executed in parallel **only if** `depends_on` is empty or all dependencies are `done`.
- Primary Executor (GLM) and parallel Executor (Qwen) must never work on the same Ticket.
- Specialist Executor (Codex) is assigned by the Architect per-Ticket, not opportunistically.

## LLM hygiene

- Each LLM session starts with a fresh context. Paste the role's system prompt (from `docs/prompts/`) first, then the artifact to work on, then the question.
- Never dump the entire repo into context — only what the artifact explicitly references.
- If an LLM produces output that doesn't fit its role (e.g. Architect writing code, Executor redesigning the queue), reject the output without merging. Model drift is real.
