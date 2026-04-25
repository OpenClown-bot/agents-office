---
id: TKT-002
title: "Source ingestion service"
version: 0.1.1
status: draft
arch_ref: ARCH-001@0.1.1
component: "SourceIngester"
depends_on: [TKT-001]
blocks: [TKT-008]
estimate: M
assigned_executor: "glm-5.1"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-002: Source ingestion service

## 1. Goal (one sentence, no "and")
Implement the SourceIngester component that polls configured RSS feeds, public Telegram channels, and web pages on a 15-minute interval, persisting deduplicated raw items to SQLite.

## 2. In Scope
- `src/smm_autopilot/ingestion/__init__.py`
- `src/smm_autopilot/ingestion/rss.py` (RSS feed fetcher using feedparser)
- `src/smm_autopilot/ingestion/telegram.py` (Telegram channel reader via Bot API forwarded messages)
- `src/smm_autopilot/ingestion/web.py` (web page scraper using beautifulsoup4 + lxml)
- `src/smm_autopilot/ingestion/service.py` (orchestrator: iterate sources, dispatch to correct fetcher, persist)
- `tests/test_ingestion.py` (unit tests with mocked HTTP responses)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- Classification logic — belongs to TKT-003@0.1.1
- Source autodiscovery — belongs to TKT-008@0.1.1
- Source CRUD via bot commands — belongs to TKT&#45;005b@0.1.0
- APScheduler job registration — belongs to TKT-007@0.1.1

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.1 §3.1 SourceIngester (responsibility, inputs, outputs, failure modes)
- ARCH-001@0.1.1 §5 Data Model (`Source`, `RawItem`, `Metrics` schemas) + §8 Observability (`service.py` increments `items_ingested` to the `Metrics` table)
- ARCH-001@0.1.1 §6 External Interfaces (RSS, Telegram Bot API source ingestion)
- ADR-001@0.1.0 (Python + httpx + feedparser + beautifulsoup4)
- ADR-002@0.1.0 (SQLite via aiosqlite)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/ingestion/__init__.py`
- [ ] `src/smm_autopilot/ingestion/rss.py`
- [ ] `src/smm_autopilot/ingestion/telegram.py`
- [ ] `src/smm_autopilot/ingestion/web.py`
- [ ] `src/smm_autopilot/ingestion/service.py`
- [ ] `tests/test_ingestion.py` (coverage ≥80% for ingestion module)

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_ingestion.py -v` passes
- [ ] Given a mock RSS feed XML, when `rss.fetch()` is called, then a `RawItem` is persisted with correct `source_id`, `external_id`, `title`, `body`, `url`, `published_at`
- [ ] Given a duplicate `(source_id, external_id)`, when ingestion runs, then no duplicate row is created (UNIQUE constraint)
- [ ] Given a source that returns HTTP 500, when ingestion runs, then a warning is logged and the source is skipped (no crash)
- [ ] Given a malformed RSS XML, when parsing fails, then the error is logged and the item is skipped
- [ ] `ruff check src/smm_autopilot/ingestion/ tests/test_ingestion.py` clean
- [ ] `mypy src/smm_autopilot/ingestion/ --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `db.py` or `models.py` — if schema changes are needed, return a question
- Use `httpx.AsyncClient` for all HTTP requests (not `requests` or `aiohttp`)
- All SQL parameterised (no f-string SQL)
- Retry logic: max 3 attempts with exponential backoff (5s, 15s, 45s) for HTTP errors

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
