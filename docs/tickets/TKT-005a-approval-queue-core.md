---
id: TKT-005a
title: "Approval queue core"
version: 0.1.0
status: draft
arch_ref: ARCH-001@0.1.1
component: "ApprovalBot"
depends_on: [TKT-001]
blocks: [TKT-005b, TKT-005c, TKT-007]
estimate: M
assigned_executor: "qwen-3.6-plus"
created: 2026-04-24
updated: 2026-04-24
---

# TKT&#45;005a: Approval queue core

## 1. Goal (one sentence, no "and")

Implement the ApprovalBot approval queue core for PO draft review across normal plus sensitive flows.

## 2. In Scope

- `src/smm_autopilot/bot/__init__.py`
- `src/smm_autopilot/bot/handlers.py` (queue command plus callback_query handlers for approval flow)
- `src/smm_autopilot/bot/keyboards.py` (inline keyboard builders for approval flow)
- `src/smm_autopilot/bot/formatters.py` (draft display formatting for Telegram messages)
- `src/smm_autopilot/bot/auth.py` (PO user ID allowlist check)
- `tests/test_bot_queue.py` (unit tests with mocked Telegram API)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)

- Admin commands for sources, cadence, channels, sensitivity keywords, or help — belongs to TKT&#45;005b@0.1.0
- Discovery-candidate approval or stats reporting — belongs to TKT&#45;005c@0.1.0
- Publishing logic — belongs to TKT-006@0.1.1
- Scheduler logic — belongs to TKT-007@0.1.1

## 4. Inputs (Executor MUST read before writing code)

- ARCH-001@0.1.1 §3.4 ApprovalBot (responsibility, inputs, outputs, failure modes)
- ARCH-001@0.1.1 §5 Data Model (`Draft`, `Channel`, `CadenceConfig` schemas)
- ARCH-001@0.1.1 §6 External Interfaces (Telegram Bot API PO bot)
- ADR-001@0.1.0 (python-telegram-bot v21+ async)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`

## 5. Outputs (deliverables)

- [ ] `src/smm_autopilot/bot/__init__.py`
- [ ] `src/smm_autopilot/bot/handlers.py`
- [ ] `src/smm_autopilot/bot/keyboards.py`
- [ ] `src/smm_autopilot/bot/formatters.py`
- [ ] `src/smm_autopilot/bot/auth.py`
- [ ] `tests/test_bot_queue.py` (coverage ≥80% for queue core)

## 6. Acceptance Criteria (machine-checkable)

- [ ] `pytest tests/test_bot_queue.py -v` passes
- [ ] Given a draft with `status=ready` and `is_sensitive=false`, when the PO sends `/queue`, then a Telegram message is sent with variant A/B text and inline buttons [Approve A] [Approve B] [Edit] [Reject] [Defer]
- [ ] Given a draft with `is_sensitive=true`, when the PO sends `/queue`, then the item appears only in the sensitive sub-queue and the approve button requires a second confirmation tap
- [ ] Given the PO taps [Approve A], when the callback is processed, then `Draft.status` is set to `approved`, `chosen_variant=a`, and `approved_at` is set
- [ ] Given the PO edits a variant, when the edit is approved, then `po_edit_text` is persisted and `chosen_variant` records the edited source variant
- [ ] Given the PO taps [Reject] or [Defer], when the callback is processed, then `Draft.status` is set to `rejected` or `deferred` respectively
- [ ] Given a Telegram message from a user ID not in the allowlist, when received, then it is silently ignored (no response)
- [ ] Given the same callback is received twice, when processed, then the second attempt returns "already processed" and does not mutate state
- [ ] `ruff check src/smm_autopilot/bot/ tests/test_bot_queue.py` clean
- [ ] `mypy src/smm_autopilot/bot/ --strict` clean

## 7. Constraints (hard rules for Executor)

- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `db.py` or `models.py` — if schema changes are needed, return a question
- Use `python-telegram-bot` v21+ async API exclusively
- PO user ID MUST be loaded from environment variable `PO_TELEGRAM_USER_ID`
- Bot token MUST be loaded from environment variable `APPROVAL_BOT_TOKEN`
- All callback_data strings MUST be ≤64 bytes (Telegram API limit)
- All SQL parameterised (no f-string SQL)
- Idempotent callback handling: pressing the same button twice must not corrupt state

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
