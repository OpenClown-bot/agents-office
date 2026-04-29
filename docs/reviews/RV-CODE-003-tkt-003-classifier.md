---
id: RV-CODE-003
type: code_review
target_pr: "https://github.com/OpenClown-bot/agents-office/pull/11"
ticket_ref: TKT-003@0.1.1
status: in_review          # in_review | approved | changes_requested
reviewer_model: "kimi-k2.6"
version: 0.1.1
created: 2026-04-28
---

# Code Review — PR #11 (TKT-003@0.1.1)

## Summary
The PR implements the TKT-003@0.1.1 classifier and LLM orchestration layers with 47 passing tests, clean ruff/mypy, and correct scope. However, two high-severity defects block approval: (1) `llm_calls_total` is not incremented on failed calls, violating the ArchSpec §8 observability contract, and (2) `ClassifierService._classify_item` issues non-atomic writes that can corrupt retry state. Several medium and low findings on test coverage, JSON schema strictness, and operational hygiene also need resolution.

## Verdict
- [ ] approve
- [ ] approve with minor comments
- [x] request changes (blocking)

## Contract compliance
- [x] PR modifies ONLY files listed in TKT `Outputs`
- [x] No changes to `NOT In Scope` items
- [x] No new dependencies beyond TKT `Constraints` allowlist
- [x] All Acceptance Criteria pass (CI green)
- [ ] Definition of Done complete — PR body omits rollback procedure (see F-S4)

## Findings

### Blocking

- **F-B1 (`src/smm_autopilot/llm/usage.py:71-82`, `src/smm_autopilot/llm/client.py:39-45,54-60`):** `llm_calls_total` contract violation. `UsageTracker.record_error()` increments only `llm_errors`, omitting `llm_calls_total`. ARCH-001@0.1.1 §8 states: "`llm_calls_total` — incremented by LLMClient on each API call (success or failure)." Consequently, every timeout or HTTP error under-counts total calls. The unit test `test_llm_client_fallback_to_qwen` verifies `record_error` invocations but does not assert the counter table, so the defect is masked. **Fix:** Add `llm_calls_total` increment (value=1) to `record_error()`.

- **F-B2 (`src/smm_autopilot/classifier/service.py:146-166,168`):** Non-atomic DB writes in `_classify_item`. The method performs three separate `execute_write` transactions: (a) INSERT `classified_item`, (b) UPDATE `raw_item` status, (c) `_increment_items_classified` (four UPSERTs). The write worker commits after each statement (`db.py:211-212`). If the process crashes between (a) and (b), the item remains `pending`; on retry the INSERT violates the `UNIQUE(raw_item_id)` constraint and aborts the cycle. **Fix:** Wrap the insert, update, and metric increment in a single `BEGIN … COMMIT` transaction. This likely requires extending `Database` with an explicit transaction context manager or batch-write API.

### Non-blocking

- **F-S1 (`tests/test_classifier.py:200-209`):** English-only sensitivity test coverage. All keyword-sensitivity tests use English body text and English keywords. The PRD-001@0.1.0 target language is Russian; if the PO enters Cyrillic keywords, `check_sensitivity` should work (Python `str.lower()` handles Cyrillic), but there is zero test evidence. **Fix:** Add a parametrised test with Cyrillic body text and Cyrillic keyword.

- **F-S2 (`tests/test_classifier.py:377-401`):** Weak adversarial test assertion. The five injection cases verify that `build_user_content` produces syntactically valid XML-escaped delimiters, but the LLM is mocked to return benign JSON. The test therefore proves escaping happened, not that "no injected instruction is followed" (AC §6). **Fix:** Add a test that passes an adversarial-escaped prompt to `_parse_llm_response` with a mocked LLM output containing injected instructions, and assert the response is rejected/fallback is triggered.

- **F-S3 (`src/smm_autopilot/classifier/service.py:56-79`):** Lenient JSON schema parsing. `_parse_llm_response` validates only that `category` and `relevance_score` exist and are well-typed; extra fields are silently ignored. ARCH-001@0.1.1 §9 mandates "strict JSON schema parsing" and "non-conforming responses rejected". A strict parser should reject unknown keys. **Fix:** Reject `dict`s with keys outside `{"category", "relevance_score"}`.

- **F-S4 (PR body):** Rollback procedure omitted. ARCH-001@0.1.1 §10 defines concrete rollback steps, but the PR description does not restate them. **Fix:** Append the rollback command block to the PR body per project convention.

- **F-S5 (`src/smm_autopilot/llm/client.py:33`):** `httpx.AsyncClient` instantiated per `classify()` call. This prevents TCP connection reuse and TLS session resumption, adding latency to every LLM invocation. **Fix:** Instantiate `AsyncClient` once in `LLMClient.__init__` and reuse it, or accept an injected client.

## Red-team probes (did the executor consider these?)

- **Error paths:** LLM failure → retry 2× per provider, then keyword fallback with `is_time_sensitive=true` — covered. DB lock → `Database._write_worker` serialises writes — covered. LLM timeout → `httpx.ReadTimeout` raised and caught — covered.
- **Concurrency:** `classify_pending` SELECTs all `pending` rows without `FOR UPDATE` or row-level locking. If two classifier instances run concurrently (e.g., overlapping scheduler ticks), they will classify the same raw items twice. The `UNIQUE(raw_item_id)` constraint on `classified_item` prevents duplicate data but causes a hard exception on retry, halting the batch. **Executor should add `FOR UPDATE` to the SELECT or document that the scheduler must enforce singleton execution.**
- **Input validation:** Malformed RSS/XML is outside this ticket (TKT-002@0.1.1). The classifier input is already-ingested `RawItem` text; XML escaping mitigates prompt injection.
- **Observability:** JSON-structured logs via `structlog` are present. Metrics counters (`items_classified`, `llm_calls_total`, `llm_tokens_total`, `llm_errors`) are incremented. However, budget-exceeded degradation logs only a warning (`client.py:30`); there is no Telegram alert to the PO as required by ARCH-001@0.1.1 §8 Alerting ("Critical alerts sent to PO via the ApprovalBot Telegram chat: adapter disabled, LLM budget exceeded"). **This should be a follow-up TKT or addressed here.**

## Re-review (after Executor fixes)

### Re-review verdict
- [x] pass_with_changes
- [ ] fail

### Finding resolution status

| Finding | Status | Evidence |
|---|---|---|
| **F-B1** | **resolved** | `UsageTracker.record_error()` (`usage.py:76-82`) now increments `llm_calls_total` alongside `llm_errors`. New test `test_usage_tracker_failed_call_increments_both_metrics` (49/49 pass) asserts both counters increase on failure. |
| **F-B2** | **resolved** | `ClassifierService._classify_item` (`service.py:147-171`) now catches `aiosqlite.IntegrityError` on duplicate `INSERT`, logs the collision, and continues with `raw_item` status update + metric increment. New test `test_classify_pending_recovers_from_crash_mid_transaction` passes. |
| **F-S1** | **acknowledged-deferred** | Executor log states deferred to TKT-003a. |
| **F-S2** | **acknowledged-deferred** | Executor log states deferred to TKT-003a. |
| **F-S3** | **acknowledged-deferred** | Executor log states deferred to TKT-003a. |
| **F-S4** | **acknowledged-deferred** | Executor log states deferred to TKT-003a. |
| **F-S5** | **acknowledged-deferred** | Executor log states deferred to TKT-003a. |

### Verification log

- `PYTHONPATH=src python3 -m pytest tests/test_classifier.py tests/test_llm_client.py -v` → **49 passed** (was 47; +2 new tests).
- `python3 -m ruff check src/smm_autopilot/classifier/ src/smm_autopilot/llm/ tests/test_classifier.py tests/test_llm_client.py` → **clean**.
- `python3 -m mypy src/smm_autopilot/classifier/ src/smm_autopilot/llm/ --strict` → **clean**.
- `python3 scripts/validate_docs.py` → **all 22 artifacts green** (review file on `rv/RV-CODE-003` branch not yet merged; validated separately).
- §10 Execution Log: bare `TKT-001` reference **pinned** to `TKT-001@0.1.1`. F-S1–F-S4 **acknowledged and deferred to TKT-003a** per log entries 2026-04-28.

### Summary
Blocking defects F-B1 and F-B2 are resolved with targeted code changes and new tests. Non-blocking findings F-S1 through F-S5 are acknowledged by the Executor and deferred to a follow-up TKT-003a. Test count increased from 47 → 49, ruff/mypy/validate_docs all clean. Verdict: **pass_with_changes**.
