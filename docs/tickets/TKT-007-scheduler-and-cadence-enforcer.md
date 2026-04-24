---
id: TKT-007
title: "Scheduler and cadence enforcer"
version: 0.1.1
status: draft
arch_ref: ARCH-001@0.1.1
component: "Scheduler"
depends_on: [TKT-001, TKT-005a, TKT-005b, TKT-006]
blocks: []
estimate: M
assigned_executor: "glm-5.1"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-007: Scheduler and cadence enforcer

## 1. Goal (one sentence, no "and")
Implement the Scheduler component that creates publish jobs for approved drafts within per-channel cadence ceilings, manages static time-window scheduling, enforces the global kill-switch, and auto-expires stale time-sensitive items.

## 2. In Scope
- `src/smm_autopilot/scheduler/__init__.py`
- `src/smm_autopilot/scheduler/service.py` (core scheduling logic: pick approved drafts, create PublishJobs within cadence limits, assign time windows)
- `src/smm_autopilot/scheduler/expiry.py` (time-sensitive item expiry: 24h SLA enforcement)
- `src/smm_autopilot/scheduler/executor.py` (publish job executor: pick due jobs, dispatch to ChannelPublisher adapters)
- `src/smm_autopilot/scheduler/recovery.py` (bounded re-queue for generation failures and failed publish jobs)
- `src/smm_autopilot/scheduler/jobs.py` (APScheduler job registration: all periodic tasks from ARCH-001@0.1.1 §4)
- `tests/test_scheduler.py` (unit tests for cadence enforcement, expiry, time windows)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- Publisher adapter implementations — belongs to TKT-006@0.1.1
- Approval queue core — belongs to TKT&#45;005a@0.1.0
- Approval bot admin commands — belongs to TKT&#45;005b@0.1.0
- Draft generation — belongs to TKT-004@0.1.1
- Analytics-driven optimal-times posting (PRD-001@0.1.0 §3 NG11) — explicitly excluded

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.1 §3.5 Scheduler (responsibility, inputs, outputs, failure modes)
- ARCH-001@0.1.1 §4 Data Flow (steps 5–8: schedule, publish, expire, recover)
- ARCH-001@0.1.1 §5 Data Model (`PublishJob`, `Draft`, `Channel`, `CadenceConfig`, `ClassifiedItem` retry metadata schemas)
- ADR-004@0.1.0 (APScheduler 3.x with AsyncIOScheduler)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`
- TKT&#45;005a@0.1.0 outputs: approved/rejected/deferred draft state transitions
- TKT&#45;005b@0.1.0 outputs: cadence config stored in DB by bot commands
- TKT-006@0.1.1 outputs: `publishers/base.py` interface and retryable failure metadata

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/scheduler/__init__.py`
- [ ] `src/smm_autopilot/scheduler/service.py`
- [ ] `src/smm_autopilot/scheduler/expiry.py`
- [ ] `src/smm_autopilot/scheduler/executor.py`
- [ ] `src/smm_autopilot/scheduler/recovery.py`
- [ ] `src/smm_autopilot/scheduler/jobs.py`
- [ ] `tests/test_scheduler.py` (coverage ≥80% for scheduler module)

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_scheduler.py -v` passes
- [ ] Given an approved draft for Telegram and the channel cadence is ≤1/day, when scheduling runs, then at most 1 `PublishJob` per day is created for that channel
- [ ] Given 3 approved drafts for X and the daily limit is 1, when scheduling runs, then surplus drafts are queued for subsequent days (not dropped)
- [ ] Given the global kill-switch is `true`, when scheduling runs, then no new `PublishJob` rows are created
- [ ] Given a time-sensitive draft where `source_published_at + 24h < now` and `Draft.status != approved`, when expiry check runs, then `Draft.status` is set to `expired`
- [ ] Given the PO changes cadence via bot command, when the scheduler's next 5-minute check runs, then the new cadence is respected
- [ ] Given a `PublishJob` with `scheduled_at <= now` and `status=scheduled`, when the executor runs, then it calls the appropriate `Publisher.publish()` method
- [ ] Given a `ClassifiedItem` with `status=generation_failed`, `generation_retry_count < 3`, and `next_generation_attempt_at <= now`, when recovery runs, then it is reset to `status=classified` for draft regeneration
- [ ] Given a retryable failed publish job with `retry_count < max_retry_count`, when recovery runs, then `retry_count` increments and `scheduled_at` is moved to the next available channel publish window
- [ ] Given a failed publish job with `retry_count >= max_retry_count`, when recovery runs, then it remains `status=failed` and a PO alert is emitted
- [ ] `ruff check src/smm_autopilot/scheduler/ tests/test_scheduler.py` clean
- [ ] `mypy src/smm_autopilot/scheduler/ --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `db.py`, `models.py`, or publisher adapters — if changes are needed, return a question
- Use `APScheduler` `AsyncIOScheduler` for all periodic jobs
- Static time windows only — no analytics-driven scheduling (PRD-001@0.1.0 §3 NG11)
- All timestamps in UTC
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
