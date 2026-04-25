---
id: RV-CODE-002
type: code
target_pr: "https://github.com/OpenClown-bot/agents-office/pull/9"
ticket_ref: TKT-002@0.1.1
status: in_review
reviewer_model: "kimi-k2.6"
created: 2026-04-25
version: 0.1.1
---

# Code Review — PR #9 (TKT-002@0.1.1)

## Summary
24/24 tests pass, ruff and mypy (`--strict`) are clean. However, a new high-severity defect was found in the Telegram channel ingestion path: `SourceIngester.run_once()` passes the raw `source_url` (from `Source.url`) to `telegram.fetch()` as `channel_username`, which breaks filtering and URL construction when the stored value is a `https://t.me/…` URL. No integration test exercises this path, so the bug is silent. Additional medium-severity test-quality gaps and one out-of-zone file edit were found.

## Verdict
`fail` — one high-severity functional defect breaks Telegram channel ingestion for the natural URL schema; plus medium-severity test gaps and an out-of-zone backlog edit.

## Contract compliance
- [x] PR modifies ONLY files listed in TKT `Outputs`
  - Exception: the TKT-002@0.1.1 ticket file was edited within allowed zones (status flip + Execution Log append).
  - Exception: the v0.1.2 backlog artifact was edited — **out of Executor write-zone** (see F-M5).
- [x] No changes to `NOT In Scope` items
- [x] No new dependencies beyond TKT `Constraints` allowlist
- [x] All Acceptance Criteria pass (CI green)
  - `pytest tests/test_ingestion.py -v` → 24/24 passed (verified locally)
  - `ruff check src/smm_autopilot/ingestion/ tests/test_ingestion.py` → clean
  - `mypy src/smm_autopilot/ingestion/ --strict` → clean
- [ ] Definition of Done complete
  - AC-2 is only weakly verified: no test asserts `published_at` is persisted to the DB (see F-M1).

## Findings

### High
- **F-H1 (`src/smm_autopilot/ingestion/service.py:58-60`, `src/smm_autopilot/ingestion/telegram.py:69-74`, `telegram.py:146-148`, `telegram.py:56-58`):** `SourceIngester.run_once()` passes `source_url` (from `Source.url`) directly to `telegram.fetch(client, self._bot_token, source_url)` as the `channel_username` parameter. The `Source` schema defines `url TEXT NOT NULL`; for Telegram channels the natural stored value is `https://t.me/channelname`. `telegram.fetch()` normalises with `.lstrip("@").lower()`, so `normalized_channel` becomes `"https://t.me/channelname"`. This never matches `chat.get("username")` (e.g. `"channelname"`), causing **all** Telegram channel updates to be silently discarded. Additionally the constructed `FetchedItem.url` becomes the malformed string `"https://t.me/https://t.me/channelname/42"`.
  - **Responsible:** Executor
  - **Remediation:** In `service.py`, extract the username from `source_url` before calling `telegram.fetch()`: strip the `https://t.me/` prefix (and any trailing path), then pass the bare username. Or, have `telegram.fetch()` accept a URL and extract the username internally. Add an end-to-end test (`test_service_run_once_telegram`) that seeds a `telegram_channel` source with a realistic URL (`https://t.me/testchannel`) and asserts items are persisted.

### Medium
- **F-M1 (`tests/test_ingestion.py:274-285`, `tests/test_ingestion.py:108-120`):** AC-2 requires correct `published_at` persistence, yet no test queries the `published_at` column from the DB or asserts the parsed `published_at` value on the `FetchedItem`. `test_service_rss_persist_raw_item` SELECTs `source_id, external_id, title, body, url, status` only; `test_rss_fetch_success` asserts `external_id`, `title`, `body`, `url`, `image_url`, but not `published_at`.
  - **Responsible:** Executor
  - **Remediation:** Extend `test_service_rss_persist_raw_item` to SELECT `published_at` and assert it matches the expected ISO timestamp from `SAMPLE_RSS_XML`. Also assert `items[0].published_at` in `test_rss_fetch_success`.

- **F-M2 (`tests/test_ingestion.py:460-469`):** `test_service_unknown_source_type_skipped` is a no-op test. It seeds a source, builds a local `fake_sources` list, asserts a string is not in a tuple, and checks that `raw_item` is empty — which is trivially true because `SourceIngester.run_once()` is **never invoked**. The test therefore provides zero coverage for the "unknown source type skipped" behaviour in `service.py`.
  - **Responsible:** Executor
  - **Remediation:** Seed a source with `type = 'unknown_type'` in the DB (bypassing the CHECK constraint or using a direct INSERT), instantiate `SourceIngester`, call `run_once()`, and assert no raw items are created and the `ingestion_unknown_source_type` event is logged.

- **F-M3 (`tests/test_ingestion.py:400-419`, `tests/test_ingestion.py:434-453`):** `test_service_run_once_rss` and `test_service_run_once_web` monkey-patch `SourceIngester.run_once` on the **class object**, replacing it with a hard-coded re-implementation that only calls the corresponding fetcher. The real `run_once()` — including `httpx.AsyncClient` lifecycle, exception handling, source-type dispatch loop, and per-item `_persist_item` calls — is **never exercised** end-to-end for any source type. This gives false confidence in the orchestrator.
  - **Responsible:** Executor
  - **Remediation:** Refactor `SourceIngester` to accept an optional `httpx.AsyncClient` factory (or inject a transport), then test the **actual** `run_once()` method with a mock client. Alternatively, use `respx` or `pytest-httpx` to intercept real `httpx.AsyncClient` requests without replacing the method body.

- **F-M4 (`tests/test_ingestion.py` missing):** There is **no** end-to-end test that exercises `SourceIngester.run_once()` for `telegram_channel` sources. Combined with F-H1, this means the Telegram ingestion path is completely untested at the service level.
  - **Responsible:** Executor
  - **Remediation:** Add `test_service_run_once_telegram` that seeds a `telegram_channel` source, mocks the Bot API `getUpdates` response, calls `ingester.run_once()`, and asserts `RawItem` rows are created with correct fields.

- **F-M5 (backlog artifact):** The Executor removed the "From Devin Review on PR#9" section from the v0.1.2 backlog file. That file is **not** listed in TKT-002@0.1.1 §5 Outputs, and per CONTRIBUTING.md §5 the Executor may only modify files explicitly listed in the Ticket's Outputs (plus Execution Log append). Editing a backlog artifact is an out-of-zone change.
  - **Responsible:** Executor
  - **Remediation:** Revert the backlog file to restore the deferred Devin Review findings (§6), or, if the PO requested removal, let the PO make the edit directly on `main`. The Executor must not touch backlog/docs files.

### Low
- **F-L1 (`src/smm_autopilot/ingestion/service.py:103-109`):** Duplicate detection relies on string-matching `"UNIQUE constraint failed" in str(exc)` instead of an explicit `isinstance` check against `sqlite3.IntegrityError` (or `aiosqlite.IntegrityError`). If aiosqlite changes exception wrapping in a future release, dedup detection would break and all duplicates would be logged as `ingestion_persist_error`.
  - **Responsible:** Executor
  - **Remediation:** Catch `sqlite3.IntegrityError` explicitly (aiosqlite wraps it), or use `getattr(exc, "__cause__", exc)` and check `isinstance(..., sqlite3.IntegrityError)`.

- **F-L2 (`src/smm_autopilot/ingestion/service.py:118`):** `_increment_items_ingested()` is called outside the `try/except` block in `_persist_item`. If the metrics upsert fails (e.g. DB locked, disk full), the exception propagates up through `run_once()` and aborts the entire ingestion cycle for all remaining sources and items. The `run_once()` `try/except` only wraps the fetcher calls, not the persist loop.
  - **Responsible:** Executor
  - **Remediation:** Move `_increment_items_ingested()` inside the `try/except` in `_persist_item`, or wrap the `for item in fetched:` loop in `run_once()` with its own `try/except` that logs and continues on any persist error.

- **F-L3 (`tests/test_ingestion.py:400-419`, `tests/test_ingestion.py:434-453`):** Class-level monkey-patching of `SourceIngester.run_once` in `test_service_run_once_rss` and `test_service_run_once_web` is fragile; if a future test runner executes these concurrently or if an exception escapes before the `finally` restore, global state is corrupted.
  - **Responsible:** Executor
  - **Remediation:** Replace class patching with instance-level patching (`unittest.mock.patch.object(ingester, 'run_once', ...)`) or refactor to inject the client/transport as suggested in F-M3.

## Red-team probes (did the executor consider these?)
- **Error paths:** RSS/web/Telegram fetchers all have 3-attempt retry with backoff and log on exhaustion. Good. `_persist_item` catches IntegrityError for dedup and logs other DB errors. However, `_increment_items_ingested` is unprotected (F-L2), and `run_once()` does not guard the persist loop against unexpected exceptions.
- **Concurrency:** Sources are fetched sequentially inside `run_once()`. Acceptable for MVP load. The async write queue in `db.py` serialises writes; WAL mode allows concurrent reads. Good.
- **Input validation:** `telegram.fetch` correctly restricts `allowed_updates` to `["channel_post"]` and filters by `chat.username`, mitigating cross-channel contamination (fixed in PR). No XML/HTML sanitisation for LLM ingestion yet (LLM not used here).
- **Observability:** Structured JSON logs with component-scoped events (`rss_fetch_http_error`, `telegram_fetch_error`, `ingestion_duplicate_skipped`, etc.) and per-item identifiers (`source_id`, `external_id`). Sufficient for 3 a.m. debugging.

## Verdict justification
`fail` — F-H1 is a correctness bug that silently drops all Telegram channel updates when `Source.url` is stored as a URL (the schema semantics). It is not caught by any test because the Telegram service-level path is untested (F-M4). The out-of-zone backlog edit (F-M5) is a process violation. These must be fixed before merge.

---

## Re-review (after Executor fixes)

**Date:** 2026-04-25  
**Commits examined:** `ccab6c7`, `12c9535`, `2661d97` on executor branch `tkt/002-source-ingestion`

### New verdict
`pass` — all blocking findings (F-H1, F-M1–F-M4) are resolved. F-M5 was a false positive. Low findings (F-L1, F-L2) are acknowledged and do not block merge.

### Per-finding status

| Finding | Severity | Status | Notes |
|---------|----------|--------|-------|
| F-H1 | High | **resolved** | `_extract_telegram_channel_username()` added in `service.py`; handles `https://t.me/…`, `t.me/…`, `@…`, and bare username. Five parametric unit tests verify parsing. `test_service_run_once_telegram` end-to-end validates `https://t.me/devin_test_chan` → persisted `RawItem` with correct URL. |
| F-M1 | Medium | **resolved** | `test_service_rss_persist_raw_item` now SELECTs `published_at` and asserts `startswith("2026-04-24T12:00:00+00:00")`. `test_service_run_once_rss`, `test_service_run_once_telegram`, and `test_service_run_once_web` also assert `published_at`. |
| F-M2 | Medium | **resolved** | `test_service_unknown_source_type_skipped` rewritten: mocks `db.execute_read` to return `type="invalid_type"`, calls real `ingester.run_once()`, asserts zero `raw_item` rows. |
| F-M3 | Medium | **resolved** | Class-level monkey-patching eliminated. Tests now `patch.object(httpx, "AsyncClient", client_factory)` injecting `MockTransport`; real `SourceIngester.run_once()` exercised end-to-end for RSS, web, and Telegram. |
| F-M4 | Medium | **resolved** | New `test_service_run_once_telegram` added — seeds `telegram_channel` source with `https://t.me/devin_test_chan`, mocks Bot API `getUpdates`, calls `run_once()`, asserts `RawItem` with `external_id="5"` and `url="https://t.me/devin_test_chan/5"`. |
| F-M5 | Medium | **retracted** | False positive. `git log main..origin/tkt/002-source-ingestion --name-only -- docs/backlog/` returns empty; the backlog edit was present on the local `pr9` fetch but not in the Executor's actual branch. Executor never touched the backlog. |
| F-L1 | Low | acknowledged | Duplicate detection still string-matches `"UNIQUE constraint failed"`. Non-blocking; unlikely to regress with pinned `aiosqlite==0.20.0`. |
| F-L2 | Low | acknowledged | `_increment_items_ingested()` remains outside `_persist_item` try/except. Non-blocking for MVP; metrics loss is acceptable vs. ingestion abort. |
| F-L3 | Low | **resolved** | Class-level patching removed; now uses `unittest.mock.patch.object(httpx, "AsyncClient", ...)` at module level — safe and reversible per-test. |

### CI re-run
- `pytest tests/test_ingestion.py -v` → **30/30 passed** (was 24/24)
- `ruff check src/smm_autopilot/ingestion/ tests/test_ingestion.py` → clean
- `mypy src/smm_autopilot/ingestion/ --strict` → clean
- `python3 scripts/validate_docs.py` → clean (all 22 artifacts pass)
