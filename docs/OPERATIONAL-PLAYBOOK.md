# Operational Playbook — agents-office

## Purpose
Defines the mechanics of how artifacts change over time: versioning, status lifecycle, supersessions, rollbacks, change-requests, parallelism. This is the "how the train tracks work" document.

## §1. Version semantics (semver for docs)

Every artifact's frontmatter has a `version` field in `MAJOR.MINOR.PATCH` form.

### For PRDs

| Bump | When | Example |
|---|---|---|
| PATCH (0.1.0 → 0.1.1) | Typo, clarification, non-material tightening, added risk note | Fix wording in §5 User Story; rewrite AC for clarity without changing intent |
| MINOR (0.1.0 → 0.2.0) | New Goal, new Non-Goal, new User Story, changed KPI target within same epic scope | Add leading KPI; widen audience definition |
| MAJOR (0.1.0 → 1.0.0) | First "approved" version OR a material reframing of the epic | Move from draft-only to approved; add/remove a whole persona or channel set |

**Rule of thumb:** if downstream ArchSpec/Tickets need to be re-read but not torn down → MINOR. If they must be torn down → MAJOR, supersede.

### For ArchSpecs and ADRs

| Bump | When | Example |
|---|---|---|
| PATCH | Clarify wording, fix typo, tighten non-normative text | Fix section numbering |
| MINOR | Add component, add ADR, change resource estimate, refine failure modes | Introduce caching layer |
| MAJOR | Change protocol / storage / framework / topology | Swap Postgres for SQLite, or vice versa |

### For Tickets

Tickets are **mostly immutable once `in_progress`**. If a Ticket needs substantive change mid-work — close it, open a new one linked via `supersedes`. Only minor clarifications get a PATCH bump (e.g. fixing a file path in §5 Outputs).

## §2. Status lifecycle

All artifacts: `draft → in_review → approved → superseded`.

- **draft** — work in progress by the producing agent.
- **in_review** — PR open, waiting for Reviewer (or for PO in PRD case).
- **approved** — PO approved; artifact is immutable from this point. Any change requires a version bump (new branch, new PR).
- **superseded** — a newer version (or a different artifact) replaces this one. Frontmatter `superseded_by` points to the replacement.

**Who can transition what:**
| Transition | Who |
|---|---|
| draft → in_review | producing agent (opens PR) |
| in_review → approved | PO only |
| approved → superseded | PO only (via newer version's `supersedes` field) |
| any → draft | NEVER — bump version instead |

## §3. Change-request flows

### Scenario A: PO wants to pivot mid-epic

Example: after ARCH-001 is already being implemented, PO decides to add a new channel.

Procedure:
1. PO creates a Business Planner session: "Add `<change>` to PRD-001".
2. Planner opens a NEW branch off `main`, bumps `PRD-001@0.X.0 → 0.Y.0`, commits the change (MINOR or MAJOR per §1).
3. If the bump is MAJOR — Architect must re-evaluate ARCH-001.
4. If the bump is MINOR — Architect checks if existing Tickets are still valid; closes/opens tickets as needed.
5. Any in-flight Executor work:
   - Ticket not yet `in_progress` → safe, re-point to new ArchSpec version.
   - Ticket `in_progress` → depends on whether the change touches its scope. If not — let it finish; if yes — close the Executor's PR with a note, open a new Ticket.

### Scenario B: Architect realises PRD is wrong

The Architect's system prompt forbids modifying PRDs. Procedure:

1. Architect raises `Q_TO_BUSINESS_N` in the ArchSpec's §13 Open Questions with: "PRD-NNN @ §X states Y; this is infeasible/incoherent/missing-info because Z. Needed: [specific decision from PO]."
2. PO answers in the ArchSpec PR, OR opens a Business Planner session if a PRD revision is needed.
3. If PRD is revised → version bump per §1. Architect updates `prd_ref` in the ArchSpec to the new version once approved.
4. Architect does NOT continue designing around the old PRD while waiting. Either pauses the component in question, or marks it `pending_prd_clarification`.

### Scenario C: Executor realises Ticket is wrong

Executor files a Q-TKT per their role's Question Protocol. Procedure:

1. Executor runs `scripts/new_artifact.py question "TKT-NNN <topic>"`.
2. Ticket status → `blocked`.
3. Architect reviews, answers in `docs/questions/Q-NNN.md`.
4. If answer only needs clarification → Ticket gets a PATCH version bump, Executor resumes.
5. If answer requires Ticket rescoping → close Ticket as `superseded`, open a new Ticket with `supersedes: TKT-NNN@X.Y.Z`.

### Scenario D: Reviewer finds a blocking defect in an already-merged artifact

Rare but happens. Procedure:

1. PO opens a hotfix branch.
2. PO dispatches the original role (Architect or Executor) with an explicit "fix this defect, bump to v+1" instruction.
3. Normal PR + Review flow on the hotfix branch.
4. If the defect is in CODE that already shipped to production — follow the project's incident protocol (out of scope for this playbook, but add as soon as production exists).

## §4. Supersession rules

Use `supersedes` and `superseded_by` frontmatter fields to create an audit trail:

```yaml
# in the newer artifact
supersedes: PRD-001@0.1.0

# in the older artifact (updated when superseded)
superseded_by: PRD-001@1.0.0
```

Rules:
- Do NOT delete superseded files. They remain in the repo, their `status` changes to `superseded`.
- The validator enforces that every `superseded_by` resolves to an existing artifact.
- If an artifact is superseded mid-work by a downstream agent (e.g. ArchSpec still draft when PRD jumps from 0.1.0 to 1.0.0), the downstream agent re-points its `prd_ref` to the new version and re-validates its own content.

## §5. Parallelism

### Multiple epics in flight

Different PRDs can be active simultaneously:
- PRD-001 (SMM Autopilot) in approved status, ARCH-001 in draft
- PRD-002 (Advisor) in draft
- PRD-003 (Billing) in in_review

Each follows the full pipeline independently. `depends_on` at the PRD level only exists informally in §8 Risks.

### Multiple Executors on different tickets

Safe when tickets' §5 Outputs do not overlap. The Architect is responsible for ensuring this when assigning tickets. If two tickets must touch the same file — they must be ordered via `depends_on`, never parallel.

### Multiple Executors on the SAME ticket

Never. One ticket = one Executor = one PR. Diverging work = lose both.

### Multiple pipelines per day

A single PO can safely keep 2–3 agent sessions active in parallel (e.g. one Business Planner drafting PRD-002, one Architect designing ARCH-001, two Executors on non-overlapping tickets of ARCH-001). More than 4 simultaneous sessions → the PO becomes the bottleneck on clarifying questions; artifacts degrade.

## §6. Rollback

Case 1: merged PR has a bad artifact.
- `git revert <merge-commit>` on `main`.
- Open a commentary commit in `docs/reviews/` explaining the revert.
- The reverted artifact's version remains; just the "approved" state is undone.

Case 2: deployed code has a bug.
- Revert the merge commit; redeploy.
- Open a hotfix Ticket via Architect session with one-sentence Goal ("revert regression from TKT-NNN").
- Root-cause analysis goes in a review artifact, not a retrospective-as-code.

## §7. Pipeline health metrics

Informal, PO-owned. Review every 5 merged PRDs:

- **Cycle time PRD → Code live.** Target <14 days for MVP epics.
- **Reviewer block rate.** % of PRs that Reviewer marks `fail` on first pass. 20–40% is healthy. <10% suggests Reviewer is too soft. >60% suggests upstream roles are too sloppy.
- **Supersession rate.** % of artifacts that get superseded within 90 days. >30% = process noise; too many reworks.
- **Q_TO_BUSINESS per ArchSpec.** Avg number of clarifying questions Architect raises. High number is actually GOOD (means Architect is catching PRD gaps). 0 is a bad sign (means Architect is assuming).
- **Q-TKT per Ticket.** Avg Executor questions per Ticket. Low is GOOD (means Architect wrote clear tickets). High means tickets are under-specified.

## §8. Emergency: pipeline deadlock

If the pipeline gets stuck (e.g. Architect says "waiting for PRD clarification" and PRD session closed):

1. PO opens a fresh Business Planner session.
2. Paste the exact Q_TO_BUSINESS question and context.
3. Planner produces a PRD patch (PATCH or MINOR bump).
4. Planner closes. Architect resumes its previous session OR a new one with the new PRD ref.

If the same deadlock recurs → pipeline design flaw; revisit role boundaries in CONTRIBUTING.md.

## §9. Retiring an epic

When an epic is "done" (code in production, PRD goals met):

1. PRD status stays `approved` permanently (audit trail).
2. Related ArchSpec and ADRs stay `approved`.
3. Add a top-level note in the PRD §6 KPIs section: "MVP closed YYYY-MM-DD. Actual KPI results: …".
4. Any ongoing maintenance work → new epic (PRD-NNN with a fresh scope).
