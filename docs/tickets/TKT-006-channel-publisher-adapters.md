---
id: TKT-006
title: "Channel publisher adapters"
status: draft
arch_ref: ARCH-001@0.1.0
component: "ChannelPublishers"
depends_on: [TKT-001]
blocks: []
estimate: L
assigned_executor: "codex-gpt-5.3"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-006: Channel publisher adapters

## 1. Goal (one sentence, no "and")
Implement the four channel publisher adapters (Telegram, X, Threads, Instagram) each conforming to a common async interface, with per-adapter retry logic, ToS enforcement, and credential validation.

## 2. In Scope
- `src/smm_autopilot/publishers/__init__.py`
- `src/smm_autopilot/publishers/base.py` (abstract `Publisher` interface: `async publish(post) -> PublishResult`)
- `src/smm_autopilot/publishers/telegram.py` (Telegram Bot API `sendMessage`/`sendPhoto` to channel)
- `src/smm_autopilot/publishers/x.py` (X API v2 `POST /2/tweets` with OAuth 2.0 PKCE, monthly quota tracking)
- `src/smm_autopilot/publishers/threads.py` (Meta Graph API two-phase publish: create container → publish, token refresh)
- `src/smm_autopilot/publishers/instagram.py` (Meta Graph API, disabled by default)
- `tests/test_publishers.py` (unit tests with mocked API responses for all 4 adapters)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- Scheduling logic (when to publish) — belongs to TKT-007@0.1.0
- Approval queue — belongs to TKT-005@0.1.0
- Draft generation — belongs to TKT-004@0.1.0
- Browser automation, unofficial APIs, or any ToS-violating publish path — explicitly forbidden

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.0 §3.6 ChannelPublishers (responsibility, inputs, outputs, failure modes per adapter, ToS enforcement)
- ARCH-001@0.1.0 §5 Data Model (`PublishJob`, `PublishLog`, `Channel` schemas)
- ARCH-001@0.1.0 §6 External Interfaces (all 4 platform APIs: protocol, auth, rate limits)
- ADR-001@0.1.0 (Python + httpx)
- TKT-001@0.1.0 outputs: `db.py`, `models.py`, `config.py`

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/publishers/__init__.py`
- [ ] `src/smm_autopilot/publishers/base.py`
- [ ] `src/smm_autopilot/publishers/telegram.py`
- [ ] `src/smm_autopilot/publishers/x.py`
- [ ] `src/smm_autopilot/publishers/threads.py`
- [ ] `src/smm_autopilot/publishers/instagram.py`
- [ ] `tests/test_publishers.py` (coverage ≥80% for publishers module)

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_publishers.py -v` passes
- [ ] Given a mocked Telegram API success response, when `TelegramPublisher.publish()` is called, then `PublishJob.status` is set to `published` and `platform_post_id` is set
- [ ] Given a mocked X API 429 response, when `XPublisher.publish()` is called, then it retries up to 3× with exponential backoff and respects `retry_after`
- [ ] Given the X monthly post count is ≥490, when `XPublisher.publish()` is called, then it refuses to publish and notifies the PO
- [ ] Given a mocked Threads API token expiry (401), when `ThreadsPublisher.publish()` is called, then it attempts token refresh; on refresh failure, the adapter disables itself
- [ ] Given `InstagramPublisher` credentials are not provisioned, when `publish()` is called, then it returns immediately with status `pending_credentials`
- [ ] Given any adapter, when no official API path exists for the requested action, then the adapter refuses and logs the specific ToS clause
- [ ] All publish attempts are logged to the `PublishLog` table with timestamps
- [ ] `ruff check src/smm_autopilot/publishers/ tests/test_publishers.py` clean
- [ ] `mypy src/smm_autopilot/publishers/ --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.0's `requirements.txt`
- Do NOT modify `db.py` or `models.py` — if schema changes are needed, return a question
- Do NOT implement any publish path that uses browser automation, scraping, or unofficial APIs
- Use `httpx.AsyncClient` for all HTTP requests to platform APIs
- OAuth tokens MUST be loaded from environment variables, never hardcoded
- X API monthly quota counter MUST be persisted in SQLite (not in-memory)
- All SQL parameterised (no f-string SQL)
- Codex-gpt-5.3 assigned because: this ticket involves OAuth 2.0 PKCE flows, Meta Graph API two-phase publishing, token refresh logic, and security-sensitive credential handling — algorithmically dense and security-critical work

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
