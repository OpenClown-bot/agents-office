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

- 2026-04-29: Branch `exec/TKT-004-draft-generation-service` created, status set to in_progress
- 2026-04-29: Implemented `src/smm_autopilot/drafting/__init__.py` — lazy-import pattern matching classifier
- 2026-04-29: Implemented `src/smm_autopilot/drafting/prompts.py` — system prompt with XML-escaped source_text delimiters, injection mitigation, HEADLINE/CTA/TONE/ATTRIBUTION checklist (inspired by Aaron-SEO structural patterns per ADR-005@0.1.0), Russian-only enforcement, char_limit support
- 2026-04-29: Implemented `src/smm_autopilot/drafting/validation.py` — deterministic attribution validation via source-span keyword overlap + citation-URL matching; min_overlap=1 for cross-language (Russian draft vs English source) keyword matching
- 2026-04-29: Implemented `src/smm_autopilot/drafting/service.py` — DraftGeneratorService: iterates classified items × active channels, calls LLMClient.classify, parses JSON response, enforces char_limit, validates attribution (ready/unverified), persists drafts, handles retry with generation_failed + retry counters, increments metrics
- 2026-04-29: Implemented `tests/test_drafting.py` — 36 tests covering all 7 ACs
- 2026-04-29: ruff check clean, mypy --strict clean
- 2026-04-29: Coverage 94% (well above 80% threshold)
- 2026-04-29: Decision: min_overlap=1 for attribution validation — cross-language drafts (Russian) vs source (English) share few exact word matches; a single shared keyword (e.g. "vpn") suffices for deterministic attribution
- 2026-04-29: Decision: reused LLMClient.classify() for draft generation (same system/user prompt pattern as classification) — no new method needed on LLMClient, per constraint
- 2026-04-29: Status set to in_review
- 2026-04-30: F-4 schema amendment landed via TKT-004@0.1.3 (PR #20). Beginning fix iteration for F-1, F-2, F-3, F-4 (db.py UNIQUE + INSERT OR IGNORE), F-6, F-7. RV-CODE-004@in_review F-5 and F-8 deferred to backlog per orchestrator PR #19.
- 2026-04-30: F-1 fix — restructured generate_drafts to collect channel success/failure per item; _generate_draft_for_channel now returns bool; _mark_generation_failed called at most once per item per cycle (only when all channels fail, partial success is acceptable per ARCH-001@0.1.2 §3.3). Tests: test_multi_channel_failure_increments_once, test_partial_success_does_not_mark_failed.
- 2026-04-30: F-2 fix — changed int(channel.get("char_limit", 0)) or 0 to int(channel.get("char_limit") or 0) to handle NULL char_limit without TypeError. Test: test_null_char_limit_falls_back_to_zero.
- 2026-04-30: F-3 fix — split attribution validation to per-variant; each variant must independently contain a citation URL or pass source-span overlap. Test: test_per_variant_attribution_one_unattributed_marks_unverified.
- 2026-04-30: F-4 fix — added UNIQUE(classified_item_id, channel_id) to draft table in db.py per TKT-004@0.1.3 §2/§5/§7; replaced SELECT-then-INSERT dedup with INSERT OR IGNORE (single atomic SQL statement per TKT-004@0.1.3 §7 "database constraint is the concurrency authority"). Test: test_concurrent_generate_drafts_no_duplicate_rows (fresh in-memory DB per AC9). Note: existing dev DBs with pre-UNIQUE schema will re-create on next init since IF NOT EXISTS won't migrate — no migration scripts added per constraint.
- 2026-04-30: F-6 fix — extended xml_escape_source to replace fullwidth \uff1c and \uff1e with &lt; and &gt;. Extended test_prompt_injection_mitigation with explicit fullwidth-homoglyph case. Test: test_xml_escape_source_fullwidth_homoglyphs.
- 2026-04-30: All 43 tests pass, ruff clean, mypy --strict clean, validate_docs 0 failed.
- 2026-04-30: F-9 fix — moved existence-check upstream as performance/budget guard inside _generate_draft_for_channel; SELECT 1 FROM draft WHERE classified_item_id = ? AND channel_id = ? early-skip prevents wasted LLM calls and metrics inflation for already-existing drafts. UNIQUE + INSERT OR IGNORE remains the concurrency authority per TKT-004@0.1.3 §7. Post-INSERT verification read prevents metric increment on OR IGNORE skip in concurrent-race scenarios. Residual metric inflation in concurrent-race scenarios (both calls pass early-skip simultaneously) accepted as MVP behaviour — bounded to at most 1 extra increment per race. Tests: test_generate_drafts_skips_items_with_existing_drafts, test_generate_drafts_partial_coverage_processes_remaining_channels, test_concurrent_generate_drafts_no_duplicate_rows extended with metric assertion.
- 2026-04-30: All 45 tests pass, ruff clean, mypy --strict clean, validate_docs 0 failed.
- 2026-04-30: Reverted accidental §8 Definition of Done checkbox changes (write-zone hygiene per CONTRIBUTING.md; Executor write-zone is §10 only). Fixed _make_draft_response helper to distinguish explicit empty citations list from default fallback (`citations if citations is not None else [...]`). RV-CODE-004@in_review.

---

## Handoff Checklist (Architect ticks before setting status to `ready`)
- [x] Goal is one sentence, no conjunctions
- [x] NOT In Scope has ≥1 explicit item
- [x] Acceptance Criteria are machine-checkable (no "looks good")
- [x] Constraints explicitly list forbidden actions
- [x] All ArchSpec/ADR references are version-pinned
- [x] `depends_on` accurately reflects prerequisites
