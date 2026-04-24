---
id: TKT-004
title: "Draft generation service"
status: draft
arch_ref: ARCH-001@0.1.0
component: "DraftGenerator"
depends_on: [TKT-001, TKT-003]
blocks: []
estimate: M
assigned_executor: "glm-5.1"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-004: Draft generation service

## 1. Goal (one sentence, no "and")
Implement the DraftGenerator component that produces 1–3 channel-tailored Russian-language posts with exactly 2 textual variants (A/B) per post for each classified item, using the LLMClient from TKT-003@0.1.0.

## 2. In Scope
- `src/smm_autopilot/drafting/__init__.py`
- `src/smm_autopilot/drafting/service.py` (main draft generation logic: iterate classified items × active channels, call LLM, persist drafts)
- `src/smm_autopilot/drafting/prompts.py` (system prompt template for draft generation with `<source_text>` delimiter injection mitigation, channel format constraints)
- `src/smm_autopilot/drafting/validation.py` (post-generation attribution check: verify factual claims are traceable to source; flag UNVERIFIED if not)
- `tests/test_drafting.py` (unit tests with mocked LLM responses)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- LLM client implementation — already done in TKT-003@0.1.0 (`llm/client.py`, `llm/providers.py`)
- Classification logic — belongs to TKT-003@0.1.0
- Approval queue UI — belongs to TKT-005@0.1.0
- Publishing — belongs to TKT-006@0.1.0

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.0 §3.3 DraftGenerator (responsibility, inputs, outputs, LLM usage, failure modes, prompt-injection mitigation)
- ARCH-001@0.1.0 §5 Data Model (`Draft`, `Channel` schemas)
- ARCH-001@0.1.0 §6 External Interfaces (channel character limits)
- ADR-003@0.1.0 (direct HTTP calls for LLM)
- TKT-001@0.1.0 outputs: `db.py`, `models.py`, `config.py`
- TKT-003@0.1.0 outputs: `llm/client.py`, `llm/providers.py`

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/drafting/__init__.py`
- [ ] `src/smm_autopilot/drafting/service.py`
- [ ] `src/smm_autopilot/drafting/prompts.py`
- [ ] `src/smm_autopilot/drafting/validation.py`
- [ ] `tests/test_drafting.py` (coverage ≥80% for drafting module)

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_drafting.py -v` passes
- [ ] Given a classified item and 2 active channels, when draft generation runs, then 2 `Draft` rows are created (one per channel), each with non-empty `variant_a_text` and `variant_b_text` in Russian
- [ ] Given a channel with `char_limit=280` (X), when a draft is generated, then both variants are ≤280 characters
- [ ] Given the LLM response contains a factual claim not traceable to the source text, when validation runs, then the draft is flagged `status=unverified`
- [ ] Given the LLM times out, when draft generation retries 2×, then on final failure the item is marked `status=generation_failed`
- [ ] Given source text containing prompt-injection attempts, when passed to the draft prompt, then the output is valid draft JSON (not injected content)
- [ ] `ruff check src/smm_autopilot/drafting/ tests/test_drafting.py` clean
- [ ] `mypy src/smm_autopilot/drafting/ --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.0's `requirements.txt`
- Do NOT modify `llm/client.py` or `llm/providers.py` — if changes are needed, return a question
- Source text MUST be wrapped in `<source_text>` delimiters in the prompt
- All generated text MUST be in Russian (prompt must enforce this)
- All LLM responses MUST be parsed against a strict JSON schema
- All SQL parameterised (no f-string SQL)

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
