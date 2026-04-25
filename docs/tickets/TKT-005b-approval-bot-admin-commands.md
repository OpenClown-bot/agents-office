---
id: TKT-005b
title: "Approval bot admin commands"
version: 0.1.0
status: draft
arch_ref: ARCH-001@0.1.1
component: "ApprovalBot"
depends_on: [TKT-001, TKT-005a]
blocks: [TKT-007]
estimate: M
assigned_executor: "qwen-3.6-plus"
created: 2026-04-24
updated: 2026-04-24
---

# TKT&#45;005b: Approval bot admin commands

## 1. Goal (one sentence, no "and")

Implement ApprovalBot admin commands for sources, cadence, channels, sensitivity keywords, plus help.

## 2. In Scope

- `src/smm_autopilot/bot/commands/__init__.py`
- `src/smm_autopilot/bot/commands/sources.py` (`/sources` CRUD)
- `src/smm_autopilot/bot/commands/cadence.py` (`/cadence` global kill-switch plus per-channel cadence)
- `src/smm_autopilot/bot/commands/channels.py` (`/channels` enable/disable plus credential status)
- `src/smm_autopilot/bot/commands/sensitivity.py` (`/sensitivity` keyword CRUD)
- `src/smm_autopilot/bot/commands/help.py` (`/help` command summary)
- `tests/test_bot_admin.py` (unit tests with mocked Telegram API)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)

- Approval queue callback flow — belongs to TKT&#45;005a@0.1.0
- Discovery-candidate approval or stats reporting — belongs to TKT&#45;005c@0.1.0
- Scheduler cadence enforcement — belongs to TKT-007@0.1.1
- Source ingestion implementation — belongs to TKT-002@0.1.1

## 4. Inputs (Executor MUST read before writing code)

- ARCH-001@0.1.1 §3.4 ApprovalBot (admin interface responsibility)
- ARCH-001@0.1.1 §5 Data Model (`Source`, `Channel`, `CadenceConfig`, `SensitivityKeyword` schemas) + §8 Observability (no counter writes — admin commands do not modify Metrics rows)
- ARCH-001@0.1.1 §6 External Interfaces (Telegram Bot API PO bot)
- ADR-001@0.1.0 (python-telegram-bot v21+ async)
- TKT-001@0.1.1 outputs: `db.py`, `models.py`, `config.py`
- TKT&#45;005a@0.1.0 outputs: bot package, auth helper, handler registration pattern

## 5. Outputs (deliverables)

- [ ] `src/smm_autopilot/bot/commands/__init__.py`
- [ ] `src/smm_autopilot/bot/commands/sources.py`
- [ ] `src/smm_autopilot/bot/commands/cadence.py`
- [ ] `src/smm_autopilot/bot/commands/channels.py`
- [ ] `src/smm_autopilot/bot/commands/sensitivity.py`
- [ ] `src/smm_autopilot/bot/commands/help.py`
- [ ] `tests/test_bot_admin.py` (coverage ≥80% for admin commands)

## 6. Acceptance Criteria (machine-checkable)

- [ ] `pytest tests/test_bot_admin.py -v` passes
- [ ] Given the PO sends `/sources add rss https://example.com/feed`, then a new `Source` row is created with `type=rss`, `url=https://example.com/feed`, `is_active=true`
- [ ] Given the PO sends `/sources disable https://example.com/feed`, then the matching `Source.is_active` is set to `false`
- [ ] Given the PO sends `/cadence telegram 3`, then `Channel.cadence_posts_per_week_target` is updated to 3 for the Telegram channel
- [ ] Given the PO sends `/cadence kill on`, then `CadenceConfig.global_kill_switch` is set to `true`
- [ ] Given the PO sends `/channels x disable`, then the X channel is disabled without affecting other channels
- [ ] Given the PO sends `/sensitivity add протест`, then a `SensitivityKeyword` row is created if absent
- [ ] Given a Telegram message from a user ID not in the allowlist, when received, then it is silently ignored (no response)
- [ ] `ruff check src/smm_autopilot/bot/commands/ tests/test_bot_admin.py` clean
- [ ] `mypy src/smm_autopilot/bot/ --strict` clean

## 7. Constraints (hard rules for Executor)

- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt`
- Do NOT modify `db.py` or `models.py` — if schema changes are needed, return a question
- Reuse the auth helper from the approval queue core dependency
- Use `python-telegram-bot` v21+ async API exclusively
- All SQL parameterised (no f-string SQL)
- Admin commands MUST validate platform names against `telegram`, `x`, `threads`, `instagram`

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
