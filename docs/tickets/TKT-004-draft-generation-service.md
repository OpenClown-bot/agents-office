---
id: TKT-004
title: "Draft generation service"
version: 0.1.3
status: ready
arch_ref: ARCH-001@0.1.2
component: "DraftGenerator"
depends_on: [TKT-001, TKT-003]
blocks: []
estimate: M
assigned_executor: "glm-5.1"
created: 2026-04-24
updated: 2026-04-30
---

# TKT-004: Draft generation service

## 1. Goal (one sentence, no "and")
Implement the DraftGenerator component that produces 1–3 channel-tailored Russian-language posts with exactly 2 textual variants (A/B) per post for each classified item, using the LLMClient from TKT-003@0.1.1.

Revision 0.1.3 is a narrow review-remediation amendment for RV-CODE-004@in_review F-4. It relaxes this ticket's prior write-zone only enough to authorize the draft-table uniqueness hardening needed to make concurrent draft generation idempotent.

## 2. In Scope
- `src/smm_autopilot/drafting/__init__.py`
- `src/smm_autopilot/drafting/service.py` (main draft generation logic: iterate classified items × active channels, call LLM, persist drafts)
- `src/smm_autopilot/drafting/prompts.py` (system prompt template for draft generation with XML-escaped `<source_text>` delimiter injection mitigation, channel format constraints)
- `src/smm_autopilot/drafting/validation.py` (deterministic post-generation attribution check: source-span or citation-URL matching; flag UNVERIFIED if not)
- `tests/test_drafting.py` (unit tests with mocked LLM responses)
- `src/smm_autopilot/db.py` (only the `draft` table schema hardening required by RV-CODE-004@in_review F-4: add `UNIQUE(classified_item_id, channel_id)`; no unrelated schema, migration-system, connection, queue, or model changes)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- LLM client implementation — already done in TKT-003@0.1.1 (`llm/client.py`, `llm/providers.py`)
- Classification logic — belongs to TKT-003@0.1.1
- Approval queue UI — belongs to TKT&#45;005a@0.1.0
- Publishing — belongs to TKT-006@0.1.1

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.2 §3.3 DraftGenerator (responsibility, inputs, outputs, LLM usage, failure modes, prompt-injection mitigation)
- ARCH-001@0.1.2 §5 Data Model (`Draft`, `Channel`, `ClassifiedItem` retry metadata, `Metrics` schemas) + §8 Observability (`service.py` increments `drafts_generated` to the `Metrics` table)
- ARCH-001@0.1.2 §6 External Interfaces (channel character limits)
- ADR-003@0.1.0 (direct HTTP calls for LLM)
- ADR-005@0.1.0 (no-orchestrator decision — explains why third-party skill bundles like Aaron-SEO must NOT be loaded into runtime)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`
- TKT-003@0.1.1 outputs: `llm/client.py`, `llm/providers.py`
- **Inspiration source (read-only reference; do NOT import as code)**: Aaron-SEO content-quality checklists at `https://github.com/aaron-he-zhu/seo-geo-claude-skills`. Use the structural ideas (e.g. presence of headline/CTA/tone constraints) as input when designing the system prompt's content-quality assertions in `prompts.py`. Adapt to Russian SMM context. Per ADR-005@0.1.0 these skills are NOT a runtime dependency — ClawHub plugin runtime, Node.js, and OpenClaw Gateway are out of scope. Reference for prompt-engineering only.

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/drafting/__init__.py`
- [ ] `src/smm_autopilot/drafting/service.py`
- [ ] `src/smm_autopilot/drafting/prompts.py`
- [ ] `src/smm_autopilot/drafting/validation.py`
- [ ] `tests/test_drafting.py` (coverage ≥80% for drafting module)
- [ ] `src/smm_autopilot/db.py` (only add `UNIQUE(classified_item_id, channel_id)` to the existing `draft` table schema)

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_drafting.py -v` passes
- [ ] Given a classified item and 2 active channels, when draft generation runs, then 2 `Draft` rows are created (one per channel), each with non-empty `variant_a_text` and `variant_b_text` in Russian
- [ ] Given a channel with `char_limit=280` (X), when a draft is generated, then both variants are ≤280 characters
- [ ] Given the LLM response contains a factual claim without a citation URL or deterministic source-span/keyword overlap with the source text, when validation runs, then the draft is flagged `status=unverified`
- [ ] Given the LLM times out, when draft generation retries 2×, then on final failure the classified item is marked `status=generation_failed`, `generation_retry_count` is incremented, and `next_generation_attempt_at` is set
- [ ] Given an adversarial suite with ≥5 source-text injection cases (nested `<source_text>` delimiters, role-play instructions, unicode delimiter homoglyphs, multi-turn leakage requests, and closing-tag injection), when each case is passed to the draft prompt, then the output is valid draft JSON and no injected instruction is followed
- [ ] `ruff check src/smm_autopilot/drafting/ tests/test_drafting.py` clean
- [ ] `mypy src/smm_autopilot/drafting/ --strict` clean
- [ ] Given two concurrent `generate_drafts()` calls for the same classified item and active channel, when both calls attempt to persist a draft, then at most one `draft` row exists for `(classified_item_id, channel_id)` and no uncaught database integrity exception aborts the generation cycle

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `llm/client.py` or `llm/providers.py` — if changes are needed, return a question
- Do NOT import or vendor any code from the Aaron-SEO skill bundles (per ADR-005@0.1.0). Inspiration only.
- Source text MUST be XML-escaped per ARCH-001@0.1.2 §9 before being wrapped in `<source_text>` delimiters in the prompt
- All generated text MUST be in Russian (prompt must enforce this)
- All LLM responses MUST be parsed against a strict JSON schema
- Attribution validation MUST use deterministic source-span/citation matching, not an additional NLI or LLM call
- All SQL parameterised (no f-string SQL)
- To satisfy RV-CODE-004@in_review F-4, `src/smm_autopilot/db.py` MAY be edited only to add `UNIQUE(classified_item_id, channel_id)` to the `draft` table; the draft insertion path in `service.py` MUST use `INSERT OR IGNORE` or an equivalent single-statement/transactional conflict-safe write so the database constraint, not a prior read check, is the concurrency authority
- Do NOT make broader TKT-001@0.1.1 schema or migration-system changes while applying the F-4 amendment

## 8. Definition of Done
- [ ] All Acceptance Criteria pass
- [ ] PR opened with link to this TKT in description
- [ ] No TODO / FIXME left in code
- [ ] Executor filled §10 Execution Log

## 9. Questions (empty at creation; Executor appends here if blocked — do NOT start code)

## 10. Execution Log (Executor fills as work proceeds)

---

## Handoff Checklist (Architect ticks before setting status to `ready`)
- [x] Goal is one sentence, no conjunctions
- [x] NOT In Scope has ≥1 explicit item
- [x] Acceptance Criteria are machine-checkable (no "looks good")
- [x] Constraints explicitly list forbidden actions
- [x] All ArchSpec/ADR references are version-pinned
- [x] `depends_on` accurately reflects prerequisites
