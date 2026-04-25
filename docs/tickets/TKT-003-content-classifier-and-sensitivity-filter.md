---
id: TKT-003
title: "Content classifier and sensitivity filter"
version: 0.1.1
status: draft
arch_ref: ARCH-001@0.1.1
component: "Classifier"
depends_on: [TKT-001]
blocks: [TKT-004]
estimate: M
assigned_executor: "glm-5.1"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-003: Content classifier and sensitivity filter

## 1. Goal (one sentence, no "and")
Implement the Classifier component that categorises raw items via a free-tier LLM call against a fixed taxonomy and flags politically sensitive items using a PO-maintained static keyword list.

## 2. In Scope
- `src/smm_autopilot/classifier/__init__.py`
- `src/smm_autopilot/classifier/service.py` (main classifier logic)
- `src/smm_autopilot/classifier/prompts.py` (system prompt template for LLM classification with XML-escaped `<user_content>` delimiter injection mitigation)
- `src/smm_autopilot/classifier/sensitivity.py` (keyword-based sensitivity filter)
- `src/smm_autopilot/llm/__init__.py`
- `src/smm_autopilot/llm/client.py` (LLMClient class with provider routing: GLM-4-Flash primary, Qwen-Turbo fallback, keyword-only degradation)
- `src/smm_autopilot/llm/providers.py` (HTTP wrappers for GLM and Qwen APIs)
- `src/smm_autopilot/llm/usage.py` (token tracking and monthly budget enforcement)
- `tests/test_classifier.py` (unit tests with mocked LLM responses)
- `tests/test_llm_client.py` (unit tests for routing, fallback, budget enforcement)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- Draft generation — belongs to TKT-004@0.1.1
- Source ingestion — belongs to TKT-002@0.1.1
- Sensitivity keyword CRUD via bot commands — belongs to TKT&#45;005b@0.1.0

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.1 §3.2 Classifier (responsibility, inputs, outputs, LLM usage, failure modes, prompt-injection mitigation)
- ARCH-001@0.1.1 §5 Data Model (`ClassifiedItem`, `SensitivityKeyword`, `Metrics` schemas) + §8 Observability (`service.py` increments `items_classified`; `usage.py` persists `llm_calls_total`, `llm_tokens_total`, `llm_errors` to the `Metrics` table)
- ARCH-001@0.1.1 §6 External Interfaces (GLM-4-Flash, Qwen-Turbo rate limits)
- ADR-003@0.1.0 (direct HTTP calls via httpx for LLM orchestration)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/classifier/__init__.py`
- [ ] `src/smm_autopilot/classifier/service.py`
- [ ] `src/smm_autopilot/classifier/prompts.py`
- [ ] `src/smm_autopilot/classifier/sensitivity.py`
- [ ] `src/smm_autopilot/llm/__init__.py`
- [ ] `src/smm_autopilot/llm/client.py`
- [ ] `src/smm_autopilot/llm/providers.py`
- [ ] `src/smm_autopilot/llm/usage.py`
- [ ] `tests/test_classifier.py` (coverage ≥80% for classifier module)
- [ ] `tests/test_llm_client.py` (coverage ≥80% for llm module)

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_classifier.py tests/test_llm_client.py -v` passes
- [ ] Given a mocked GLM-4-Flash response with a valid category JSON, when classification runs, then a `ClassifiedItem` is persisted with the correct category
- [ ] Given a raw item body containing a sensitivity keyword from the DB, when classification runs, then `is_sensitive=true` on the `ClassifiedItem`
- [ ] Given GLM-4-Flash returns a timeout, when classification retries 2×, then it falls back to Qwen-Turbo
- [ ] Given both LLM providers fail, when classification runs, then it falls back to keyword-only classification with `classification_method=keyword_fallback` and `is_time_sensitive=true`
- [ ] Given the monthly token budget is exceeded, when a classification is attempted, then it degrades to keyword-only and logs a warning
- [ ] Given an adversarial suite with ≥5 source-text injection cases (nested `<user_content>` delimiters, role-play instructions, unicode delimiter homoglyphs, multi-turn leakage requests, and closing-tag injection), when each case is passed to the classifier prompt, then the output is valid category JSON and no injected instruction is followed
- [ ] `ruff check src/smm_autopilot/classifier/ src/smm_autopilot/llm/ tests/test_classifier.py tests/test_llm_client.py` clean
- [ ] `mypy src/smm_autopilot/classifier/ src/smm_autopilot/llm/ --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `db.py` or `models.py` — if schema changes are needed, return a question
- Use `httpx.AsyncClient` for LLM API calls
- All LLM responses MUST be parsed against a strict JSON schema; non-conforming responses MUST be rejected
- Source text MUST be XML-escaped per ARCH-001@0.1.1 §9 before being wrapped in `<user_content>` delimiters in the prompt
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
