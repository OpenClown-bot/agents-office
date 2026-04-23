---
id: RV-SPEC-ARCH-XXX
type: spec_review
target_ref: ARCH-XXX@X.Y.Z
status: in_review          # in_review | approved | changes_requested
reviewer_model: "kimi-k2.6"
created: YYYY-MM-DD
---

# Spec Review — ARCH-XXX

## Summary
<Overall verdict in 2-3 sentences.>

## Verdict
- [ ] approve
- [ ] approve with minor comments
- [ ] request changes (blocking)

## Findings

### Blocking
- **F-B1 (§section):** <issue that must be resolved before handoff to Executor>

### Non-blocking suggestions
- **F-S1 (§section):** <nice-to-have improvement>

### Questions for Architect
- **Q1:** <clarification needed>

## Cross-reference check
- [ ] All PRD sections claimed as "implemented" are actually covered
- [ ] All Non-Goals from PRD are respected
- [ ] Resource budget fits Technical Envelope
- [ ] Every Ticket in Work Breakdown is atomic (single-concern)
- [ ] No hidden assumptions about external systems

## Specific weak points to probe (reviewer red-team)
- <What happens if component X crashes mid-flow?>
- <How does the system behave at 10× expected load?>
- <Which prompt-injection vectors apply to the Generator component?>
- <What's the data-retention story?>
