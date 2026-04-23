---
id: RV-CODE-PR-NN
type: code_review
target_pr: "https://github.com/<you>/vpn-agents/pull/NN"
ticket_ref: TKT-XXX
status: in_review          # in_review | approved | changes_requested
reviewer_model: "kimi-k2.6"
created: YYYY-MM-DD
---

# Code Review — PR #NN (TKT-XXX)

## Summary
<Overall verdict in 2-3 sentences.>

## Verdict
- [ ] approve
- [ ] approve with minor comments
- [ ] request changes (blocking)

## Contract compliance
- [ ] PR modifies ONLY files listed in TKT `Outputs`
- [ ] No changes to `NOT In Scope` items
- [ ] No new dependencies beyond TKT `Constraints` allowlist
- [ ] All Acceptance Criteria pass (CI green)
- [ ] Definition of Done complete

## Findings

### Blocking
- **F-B1 (path/to/file.py:NN):** <issue>

### Non-blocking
- **F-S1 (path/to/file.py:NN):** <suggestion>

## Red-team probes (did the executor consider these?)
- Error paths: what happens on API failure, DB lock, LLM timeout?
- Concurrency: can two schedulers run the same task?
- Input validation: what if RSS feed returns malformed XML?
- Observability: can you debug this at 3am from logs alone?
