# QA Playbook — agents-office

## Purpose
Consolidated reference for how the PO validates each artifact before it moves to the next pipeline stage. The PO is the **only** human in the loop and thus the sole QA driver. Agents produce artifacts; the PO runs the checklists below to decide merge/approve/block.

## Principle
Every artifact crosses **two** quality gates before being used downstream:
1. **Self-check** — the producing agent walks its own Handoff Checklist from the template.
2. **Red-team check** — the PO asks the producing agent a batch of red-team questions *before* approving. If any answer is weak (vague, hedged, or admits a gap) — send back for revision.

Red-team answers are **not saved** to the artifact. They are a conversational probe. If they surface a defect, the defect is fixed in the artifact via a version bump or revision.

## When to run which checklist

| Stage | Producing role | Artifact | Red-team checklist | Who runs it |
|---|---|---|---|---|
| After PRD draft, before approve | Business Planner | PRD | §1 Business Planner red-team (8 Q) | PO |
| After ArchSpec draft, before Reviewer | Architect | ArchSpec + ADRs + Tickets | §2 Architect red-team (8 Q) | PO |
| After Executor PR, before Reviewer | Executor | Code PR | §3 Executor quick-check (3 Q) | PO |
| After Reviewer verdict | Reviewer | Review artifact | §4 Reviewer meta-check (3 Q) | PO |

## §1. Business Planner red-team (8 questions)

Run **after** the PRD is in PR but **before** `status: approved`. Paste all 8 in one message to the Planner session.

1. **Assumptions audit.** "List the top 3 assumptions embedded in the PRD that are NOT explicitly stated in my answers. For each: impact if wrong, and how we'd detect that."
2. **Weakest AC.** "Identify the single weakest Acceptance Criterion across all User Stories (least testable, most subjective). Rewrite it to be machine-verifiable."
3. **Scope cut stress-test.** "If I had to ship at 60% of current scope in half the time, which Goals and User Stories would you cut, and in what order? Justify."
4. **Fastest invalidation path.** "What is the cheapest experiment (≤1 week, ≤$100) that would invalidate this epic — i.e. prove it's not worth building?"
5. **Leading vs lagging metrics.** "For each KPI, classify as leading or lagging. If all are lagging, propose one leading indicator we can measure daily."
6. **Hidden dependencies.** "Are any of the stated Non-Goals secretly prerequisites for the Goals? Find at least one case where removing a Non-Goal is necessary, or confirm there isn't one."
7. **Architect pre-warning.** "What is the #1 constraint from the Technical Envelope that the Architect will find most painful? Justify why it must not be relaxed."
8. **Budget sensitivity.** "If the LLM budget is cut by 50%, which Goal becomes infeasible? What's the minimum budget to keep all Goals viable?"

**Weak-answer signals (red flags):**
- "Not applicable" / "None" on 2+ questions → shallow PRD, iterate.
- Q5: all KPIs are lagging and no leading indicator proposed → Architect will build blind.
- Q4: "wait and see" instead of a concrete experiment → epic has no validation path.
- Q7: "none come to mind" → Planner didn't engage with the envelope.

## §2. Architect red-team (8 questions)

Run **after** the ArchSpec + Tickets are in PR but **before** dispatching to Reviewer.

1. **Trace completeness.** "List every PRD Goal and map it to the component(s) and Ticket(s) that cover it. Any uncovered Goal? Any component not traced to a Goal?"
2. **Non-Goal leakage.** "Grep the ArchSpec and Tickets for every term in the PRD Non-Goals. Report any match. If any, explain why and whether it's drift."
3. **Envelope fit.** "Sum resource estimates (RAM, CPU, $/month) across all components. Compare to the PRD Technical Envelope. Show the math."
4. **ADR rigour.** "For the weakest ADR, what was the second-best option and why exactly does it lose? If the loser's downside could be mitigated, does the ADR still hold?"
5. **Ticket atomicity.** "Of all Tickets, which one has the broadest scope? Can it be split into ≥2 smaller tickets? If yes, do it now."
6. **Dependency graph.** "Render the depends_on DAG. Any cycles? Any ticket with >3 dependencies?"
7. **Failure modes.** "For each component, what happens if its primary external dependency is down for 1 hour? Is there graceful degradation or an error loop?"
8. **Prompt-injection surface.** "Which components consume external text and feed it to an LLM? For each, list the specific mitigation. 'Review outputs' is NOT a mitigation."

**Weak-answer signals:**
- Q1: any uncovered Goal → send back.
- Q3: math doesn't add up or is hand-waved → send back.
- Q4: "all other options were clearly worse" → shallow ADR, demand re-writing.
- Q5: "all tickets are minimally atomic" → almost never true, probe deeper.

## §3. Executor quick-check (3 questions)

Run **after** the Executor opens the PR but **before** the Reviewer picks it up.

1. "List every file in the PR diff. For each, is it in the Ticket §5 Outputs? Any file that isn't?"
2. "What did you suggest as follow-up TKTs that you intentionally did NOT fix? Give me the top 3 by impact."
3. "If I revert this PR tomorrow, what state is the system in? Is there a migration or config change that needs to be rolled back separately?"

**Weak-answer signals:**
- Q1: Executor claims diff is in-scope but PO sees a file that isn't → PR is rejected; model lied about its own work.
- Q2: "None" → probably untrue; there's always something.
- Q3: "No rollback considerations" for a PR that adds DB/migration/config → high risk.

## §4. Reviewer meta-check (3 questions)

Run **after** the Reviewer outputs its review artifact. Sanity-check the review itself.

1. "Show exact-line references (file:line) for every high-severity finding."
2. "Under a slightly looser standard, which single finding would become the principal blocker instead?"
3. "For each high-severity finding, who is responsible for the fix — PRD author, Architect, or Executor?"

**Weak-answer signals:**
- Q1: Reviewer can't cite a line for a high finding → finding is made up, downgrade.
- Q3: Reviewer routes defects to the wrong role → review is muddled, request re-routing.

## §5. Cross-role coherence (run quarterly or after every 3 epics)

Low-frequency audit of the whole pipeline:

1. Pick a random merged PRD. Read its ArchSpec. Does the ArchSpec match the PRD you just read, or did the team quietly drift?
2. Pick a random merged Ticket. Read the resulting code. Does the code deliver the Acceptance Criteria as written?
3. Pick a random code review. Re-read the PR it reviewed. Did the Reviewer miss anything an outsider can now spot?
4. Count supersessions in the last quarter. If >30% of ArchSpecs got superseded by rework → Architect is overcommitting. If >30% of PRDs got superseded → Business Planner is under-specifying.

## §6. Procedure when a red-team finding is blocking

1. Do NOT approve / do NOT dispatch to the next stage.
2. Message the producing agent with the specific finding:
   > "Per red-team Q{N}: your answer reveals {concrete gap}. Bump to v0.{minor+1}.0 addressing: {list}. Reply here when the new PR is up."
3. On the v-bump PR, re-run **only the red-team questions whose answers were weak** — not the whole 8.
4. If the v-bump still doesn't address the finding — swap the agent (e.g. new Business Planner session with fresh context). Persistent blindness to a defect is a sign of contaminated context.
