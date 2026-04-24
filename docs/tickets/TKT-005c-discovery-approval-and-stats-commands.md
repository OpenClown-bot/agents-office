---
id: TKT-005c
title: "Discovery approval and stats commands"
version: 0.1.0
status: draft
arch_ref: ARCH-001@0.1.1
component: "ApprovalBot"
depends_on: [TKT-001, TKT-005a, TKT-008]
blocks: []
estimate: S
assigned_executor: "qwen-3.6-plus"
created: 2026-04-24
updated: 2026-04-24
---

# TKT&#45;005c: Discovery approval plus stats commands

## 1. Goal (one sentence, no "and")

Implement ApprovalBot discovery-candidate approval plus stats reporting commands.

## 2. In Scope

- `src/smm_autopilot/bot/commands/discovery.py` (`/discover` pending candidate approval/rejection)
- `src/smm_autopilot/bot/commands/stats.py` (`/stats` daily/weekly summary)
- `tests/test_bot_discovery_stats.py` (unit tests with mocked Telegram API)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)

- Source candidate extraction — belongs to TKT-008@0.1.1
- Source CRUD, cadence, channel, sensitivity, or help commands — belongs to TKT&#45;005b@0.1.0
- Structured logging or deployment configuration — belongs to TKT-009@0.1.1
- Publishing logic — belongs to TKT-006@0.1.1

## 4. Inputs (Executor MUST read before writing code)

- ARCH-001@0.1.1 §3.4 ApprovalBot (source-discovery candidate approval)
- ARCH-001@0.1.1 §3.7 SourceDiscovery (candidate lifecycle)
- ARCH-001@0.1.1 §5 Data Model (`Source`, `SourceCandidate`, `Draft`, `PublishJob`, `PublishLog` schemas)
- ARCH-001@0.1.1 §8 Observability (`/stats` daily/weekly summary)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`
- TKT&#45;005a@0.1.0 outputs: bot package, auth helper, handler registration pattern
- TKT-008@0.1.1 outputs: `SourceCandidate` rows populated by discovery

## 5. Outputs (deliverables)

- [ ] `src/smm_autopilot/bot/commands/discovery.py`
- [ ] `src/smm_autopilot/bot/commands/stats.py`
- [ ] `tests/test_bot_discovery_stats.py` (coverage ≥80% for discovery/stats commands)

## 6. Acceptance Criteria (machine-checkable)

- [ ] `pytest tests/test_bot_discovery_stats.py -v` passes
- [ ] Given pending `SourceCandidate` rows, when the PO sends `/discover`, then candidates are shown with [Approve] and [Reject] buttons
- [ ] Given the PO approves a candidate, when the callback is processed, then a `Source` row is created with `added_by=autodiscovery` and `SourceCandidate.status=approved`
- [ ] Given the PO rejects a candidate, when the callback is processed, then `SourceCandidate.status=rejected` and no `Source` row is created
- [ ] Given duplicate candidate approval would violate `Source.url` uniqueness, when processed, then the command reports "already exists" without crashing
- [ ] Given the PO sends `/stats`, then the bot replies with daily and weekly counts for ingested items, generated drafts, approvals, rejections, published posts, failed posts, LLM calls, and freshness SLA breaches from SQLite tables
- [ ] Given a Telegram message from a user ID not in the allowlist, when received, then it is silently ignored (no response)
- [ ] `ruff check src/smm_autopilot/bot/commands/discovery.py src/smm_autopilot/bot/commands/stats.py tests/test_bot_discovery_stats.py` clean
- [ ] `mypy src/smm_autopilot/bot/ --strict` clean

## 7. Constraints (hard rules for Executor)

- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `db.py` or `models.py` — if schema changes are needed, return a question
- Reuse the auth helper from the approval queue core dependency
- Use `python-telegram-bot` v21+ async API exclusively
- All SQL parameterised (no f-string SQL)
- `/stats` MUST be read-only

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
