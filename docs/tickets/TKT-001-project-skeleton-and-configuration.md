---
id: TKT-001
title: "Project skeleton and configuration"
version: 0.1.1
status: in_review
arch_ref: ARCH-001@0.1.1
component: "all"
depends_on: []
blocks: [TKT-002, TKT-003, TKT-004, TKT-005a, TKT-005b, TKT-005c, TKT-006, TKT-007, TKT-008, TKT-009]
estimate: M
assigned_executor: "glm-5.1"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-001: Project skeleton and configuration

## 1. Goal (one sentence, no "and")
Create the Python project structure with async entrypoint, SQLite database initialization (WAL mode, all tables from ARCH-001@0.1.1 §5), Docker configuration with resource limits, and dependency pinning.

## 2. In Scope
- `src/smm_autopilot/__init__.py`, `src/smm_autopilot/__main__.py` (async entrypoint)
- `src/smm_autopilot/db.py` (SQLite connection pool with aiosqlite, WAL mode, async write queue)
- `src/smm_autopilot/models.py` (dataclass definitions matching ARCH-001@0.1.1 §5 schemas, including the `Metrics` table)
- `src/smm_autopilot/config.py` (environment variable loading via `os.environ`, config dataclass)
- `requirements.txt` with pinned versions
- `Dockerfile` (Python 3.12-slim base)
- `docker-compose.yml` with `cpus: 2.0`, `mem_limit: 4g`, `restart: unless-stopped`
- `.env.example` with all required environment variables (placeholder values)
- `tests/test_db.py` (unit tests for DB init, WAL mode verification, write queue)
- SQLite migration system (version tracking in `schema_version` table)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- Any business logic (ingestion, classification, drafting, publishing) — belongs to TKT-002@0.1.1 through TKT-008@0.1.1 and the split approval-bot tickets
- Observability configuration beyond basic structlog setup — belongs to TKT-009@0.1.1
- Deployment scripts — belongs to TKT-009@0.1.1

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.1 §5 Data Model / Schemas (all table definitions, including `Metrics`)
- ARCH-001@0.1.1 §8 Observability (counter row names to seed into `Metrics` at DB init)
- ARCH-001@0.1.1 §10 Deployment (Docker resource limits, container structure)
- ADR-001@0.1.0 (Python 3.12 + asyncio)
- ADR-002@0.1.0 (SQLite via aiosqlite, WAL mode)
- ADR-004@0.1.0 (APScheduler — add to requirements.txt)

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/__init__.py`
- [ ] `src/smm_autopilot/__main__.py`
- [ ] `src/smm_autopilot/db.py`
- [ ] `src/smm_autopilot/models.py`
- [ ] `src/smm_autopilot/config.py`
- [ ] `requirements.txt`
- [ ] `Dockerfile`
- [ ] `docker-compose.yml`
- [ ] `.env.example`
- [ ] `tests/__init__.py`
- [ ] `tests/test_db.py`

## 6. Acceptance Criteria (machine-checkable)
- [ ] `python -m smm_autopilot` starts without error and exits cleanly on SIGINT
- [ ] `pytest tests/test_db.py -v` passes
- [ ] SQLite database is created at the configured path with WAL mode enabled (`PRAGMA journal_mode` returns `wal`)
- [ ] All tables from ARCH-001@0.1.1 §5 exist with correct columns, including `SchemaVersion` and `Metrics` (composite PK `(name, period, period_date)`)
  - [ ] `Metrics` table is seeded at DB init with the counter rows listed in ARCH-001@0.1.1 §8 Observability (one row per counter name × period bucket, `period_date` set per §5 semantics: current calendar date for daily rows, Monday of the current ISO week for weekly rows, first day of the current month for monthly rows, `'1970-01-01'` sentinel for total rows)
- [ ] `docker compose build` succeeds
- [ ] `docker compose up -d` starts the container with CPU/memory limits visible in `docker stats`
- [ ] `ruff check src/ tests/` clean
- [ ] `mypy src/ --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add dependencies beyond: `aiosqlite>=0.20.0`, `httpx>=0.27.0`, `python-telegram-bot>=21.0`, `apscheduler>=3.10,<4.0`, `sqlalchemy>=1.4,<3.0` (APScheduler `SQLAlchemyJobStore` only), `structlog>=24.0`, `feedparser>=6.0`, `beautifulsoup4>=4.12`, `lxml>=5.0`, `pydantic>=2.0` (for config validation)
- Do NOT use SQLAlchemy ORM for application data models or CRUD — use raw SQL via aiosqlite for SMM Autopilot tables; SQLAlchemy is allowed only as the APScheduler job-store dependency
- Do NOT create any `.env` file — only `.env.example`
- Pin Python 3.12 in Dockerfile
- All SQL must be parameterised (no f-string SQL)

## 8. Definition of Done
- [ ] All Acceptance Criteria pass
- [ ] PR opened with link to this TKT in description
- [ ] No TODO / FIXME left in code
- [ ] Executor filled §10 Execution Log

## 9. Questions (empty at creation; Executor appends here if blocked — do NOT start code)

## 10. Execution Log (Executor fills as work proceeds)

- 2026-04-25: Claimed ticket. Read ARCH-001§5/§8/§10, ADR-001/002/004. Sanity-check passed.
- 2026-04-25: Branch `tkt/TKT-001-project-skeleton` created.
- 2026-04-25: Implemented all 11 output files. All SQL parameterized. No SQLAlchemy ORM. Dependencies exactly per §7 allowlist.
- 2026-04-25: `pytest tests/test_db.py -v` → 9/9 passed. `ruff check src/ tests/` → clean. `mypy src/ --strict` → clean. `python -m smm_autopilot` → starts and exits on SIGTERM.
- 2026-04-25: Self-review: all files in §5 Outputs only. All ACs verifiable. No TODOs/FIXMEs. No scope drift.
- 2026-04-25: Committed. Status → in_review. PR opened.

---

## Handoff Checklist (Architect ticks before setting status to `ready`)
- [x] Goal is one sentence, no conjunctions
- [x] NOT In Scope has ≥1 explicit item
- [x] Acceptance Criteria are machine-checkable (no "looks good")
- [x] Constraints explicitly list forbidden actions
- [x] All ArchSpec/ADR references are version-pinned
- [x] `depends_on` accurately reflects prerequisites
