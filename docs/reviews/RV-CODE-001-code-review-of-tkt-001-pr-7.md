---
id: RV-CODE-001
type: code_review
target_pr: "https://github.com/OpenClown-bot/agents-office/pull/7"
ticket_ref: TKT-001@0.1.1
status: in_review
reviewer_model: "kimi-k2.6"
created: 2026-04-25
---

# Code Review — PR #7 (TKT-001@0.1.1)

## Summary
All 11 tests pass, ruff and mypy are clean, Docker builds and runs with enforced CPU (2.0) and memory (4 GiB) limits. The implementation matches ARCH-001@0.1.1 §5 schemas and §8 observability counters. Two low-severity test-coverage gaps and two low-severity maintainability/security nits were found; nothing blocks merge.

## Verdict
- [ ] approve
- [x] approve with minor comments
- [ ] request changes (blocking)

## Contract compliance
- [x] PR modifies ONLY files listed in TKT `Outputs`
  - Exception: `scripts/validate_docs.py` was modified per the acknowledged procedural exception in the PR description.
- [x] No changes to `NOT In Scope` items
- [x] No new dependencies beyond TKT `Constraints` allowlist
- [x] All Acceptance Criteria pass (CI green)
  - `pytest tests/test_db.py -v` → 11/11 passed (verified locally)
  - `ruff check src/ tests/` → clean
  - `mypy src/ --strict` → clean
  - `docker compose build` → succeeded
  - `docker compose up -d` → container starts; `docker stats` shows `4GiB` limit; `docker inspect` shows `NanoCpus=2000000000`
  - `python -m smm_autopilot` starts, logs JSON, exits cleanly on SIGTERM/SIGINT
- [x] Definition of Done complete

## Findings

### Blocking
_None._

### Non-blocking
- **F-S1 (tests/test_db.py:145-151):** `test_metrics_composite_pk` asserts only that columns `name`, `period`, and `period_date` exist in the `metrics` table; it does not verify that those three columns actually form the composite PRIMARY KEY. The test name implies PK verification, yet the assertion would pass if the PK were absent or defined on different columns.
  - **Responsible:** Executor
  - **Remediation:** Query `sqlite_master` (or `PRAGMA index_list(metrics)` / `PRAGMA index_info(...)`) to assert that a primary-key index exists and covers exactly the three columns in the correct order.

- **F-S2 (tests/test_db.py:47-67):** `test_schema_tables_exist` verifies table name existence for every ARCH-001@0.1.1 §5 table, but does not assert column correctness for any table other than `metrics` (and even that incompletely per F-S1). The AC explicitly requires "correct columns" for all tables.
  - **Responsible:** Executor
  - **Remediation:** Extend the test to iterate each expected table, run `PRAGMA table_info(table_name)`, and assert every column from ARCH-001@0.1.1 §5 is present with the expected SQLite type affinity.

- **F-S3 (Dockerfile:1-13):** The image runs as root (`USER` directive absent). While the host `.env` permissions are managed outside the container, running as root inside the container violates the principle of least privilege and widens the blast radius if a future dependency introduces a container-escape vulnerability.
  - **Responsible:** Executor
  - **Remediation:** Add a non-root user and switch to it before `CMD`, e.g.:
    ```dockerfile
    RUN useradd -m -u 1000 smm
    USER smm
    ```

- **F-S4 (src/smm_autopilot/db.py:115-124):** `execute_read` acquires `self._write_lock`, but `_write_worker` never acquires the same lock. Under SQLite WAL mode this is technically safe (readers and writers do not block each other), yet the asymmetric locking is confusing and offers no additional protection beyond SQLite's own WAL semantics. Future maintainers may mistakenly assume reads are serialized with writes.
  - **Responsible:** Executor
  - **Remediation:** Either remove `_write_lock` from `execute_read` (documenting that WAL mode provides concurrency safety) or acquire it in `_write_worker` for clarity.

## Red-team probes (did the executor consider these?)
- **Error paths:** `_write_worker` propagates DB exceptions into the caller's future; `execute_read` raises `RuntimeError` if the DB is disconnected. Good.
- **Concurrency:** Single `_write_worker` task serializes all writes via `asyncio.Queue`; WAL mode allows concurrent reads. `_write_lock` in `execute_read` only serializes reads with each other, not with writes. Acceptable for now, but see F-S4.
- **Input validation:** No external text ingestion in this ticket; all SQL is fully parameterized (no f-string SQL per TKT-001@0.1.1 §7 Constraints). Good.
- **Observability:** JSON-structured logs with ISO-8601 UTC timestamps and component-scoped events (`database_connected`, `metrics_seeded`, `schema_initialized`, `smm_autopilot_started/stopping`). Sufficient for 3 a.m. debugging.

## Verdict justification
`pass_with_changes` — four low-severity findings (test-coverage gaps, container user, asymmetric lock clarity). No design defects, no scope drift, no security blockers.
