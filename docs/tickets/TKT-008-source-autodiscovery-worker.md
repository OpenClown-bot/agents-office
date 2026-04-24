---
id: TKT-008
title: "Source autodiscovery worker"
version: 0.1.1
status: draft
arch_ref: ARCH-001@0.1.1
component: "SourceDiscovery"
depends_on: [TKT-001, TKT-002]
blocks: [TKT-005c]
estimate: S
assigned_executor: "qwen-3.6-plus"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-008: Source autodiscovery worker

## 1. Goal (one sentence, no "and")
Implement the SourceDiscovery worker that scans ingested item bodies for cross-references to new RSS feeds, Telegram channels, and websites, queuing discovered candidates for PO approval.

## 2. In Scope
- `src/smm_autopilot/discovery/__init__.py`
- `src/smm_autopilot/discovery/service.py` (scan RawItem.body for URLs/links, validate, deduplicate, persist as SourceCandidate)
- `src/smm_autopilot/discovery/extractors.py` (regex patterns for RSS URLs, Telegram `t.me/` links, generic URLs)
- `tests/test_discovery.py` (unit tests with sample HTML/text containing various link patterns)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- Web-search-based source discovery — explicitly excluded per Q_TO_BUSINESS_3 answer
- Source CRUD commands in the bot — belongs to TKT&#45;005b@0.1.0
- Source ingestion — belongs to TKT-002@0.1.1
- PO candidate approval UI — belongs to TKT&#45;005c@0.1.0

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.1 §3.7 SourceDiscovery (responsibility, inputs, outputs, failure modes)
- ARCH-001@0.1.1 §5 Data Model (`SourceCandidate`, `RawItem` schemas)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`
- TKT-002@0.1.1 outputs: `RawItem` rows populated by ingestion

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/discovery/__init__.py`
- [ ] `src/smm_autopilot/discovery/service.py`
- [ ] `src/smm_autopilot/discovery/extractors.py`
- [ ] `tests/test_discovery.py` (coverage ≥80% for discovery module)

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_discovery.py -v` passes
- [ ] Given a RawItem body containing `https://example.com/rss.xml`, when discovery runs, then a `SourceCandidate` is created with `type=rss`, `url=https://example.com/rss.xml`, `status=pending_approval`
- [ ] Given a RawItem body containing `https://t.me/somechannel`, when discovery runs, then a `SourceCandidate` is created with `type=telegram_channel`
- [ ] Given a URL that already exists in `SourceCandidate`, when discovery runs, then no duplicate is created
- [ ] Given a malformed URL like `htp://not-a-url`, when extraction runs, then it is skipped (not persisted)
- [ ] `ruff check src/smm_autopilot/discovery/ tests/test_discovery.py` clean
- [ ] `mypy src/smm_autopilot/discovery/ --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `db.py` or `models.py`
- Do NOT perform web searches or call external APIs — extraction is regex-based on already-ingested content only
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
