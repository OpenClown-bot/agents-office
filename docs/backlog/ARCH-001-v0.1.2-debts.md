---
id: BACKLOG-ARCH-001-v0.1.2
title: "ARCH-001 v0.1.2 deferred items"
status: open
spec_ref: ARCH-001@0.1.1
created: 2026-04-25
owner: "@yourmomsenpai"
---

# ARCH-001 v0.1.2 backlog

Deferred items from ARCH-001@0.1.1 review cycle. To be addressed in the next ArchSpec bump (v0.1.2) after Executor phase begins surfacing real-world impact.

## 1. From RV-SPEC-001 (Kimi K2.6 SPEC review, verdict pass_with_changes)

### Medium
1. **Resource envelope ambiguity**: Docker stack limit `2 CPU / 4 GB` < PRD ceiling `3 CPU / 6 GB`. Reconcile narratively or pick one canonical limit.
2. **Queue backpressure undefined**: ARCH §6 internal task queue has no `max_queue_depth`, no circuit-breaker, no shed strategy. Fill in.
3. **No data-retention / purge policy** for SQLite growth: tables grow without bounds. Add policy (TTL or size-based) for RawItem, ClassifiedItem, Draft, PublishLog.
4. **Telegram admin privilege** is an unstated external-system assumption: who can press approve buttons in the bot. Specify.
5. **Admin privilege level undefined**: group admin vs owner vs allowlist by user_id from ENV. Pick one and document.
6. **TKT-009@0.1.1 telemetry budget may double-count CPU** when both prometheus exporter and node_exporter run.

### Low
- Semantic-drift tolerance `0.05%` lacks rationale.
- Deferred draft expiry not specified.
- `message_delivered` schema includes fields telemetry cannot collect.
- Channel capability split (static vs OAuth) is implicit in §3, not explicit.
- Semantic versioning guidance not yet applied to ticket frontmatter.

## 2. From Devin Review on PR#6 (informational findings)

9 additional findings visible at https://app.devin.ai/review/openclown-bot/agents-office/pull/6 — minor clarifications and style suggestions. Not enumerated here individually; triage and prioritize when opening v0.1.2 bump.

## 3. Process improvements

1. **Commit ordering on approval PRs**: in PR#6, status was flipped to `approved` (commit 513f26b) before the final content fix (c17c442). Per immutability gate, content fixes must precede status flips even within open PRs. Document this rule explicitly in CONTRIBUTING.md or QA-PLAYBOOK.md under "Approval workflow".

## 4. From RV-CODE-001 (Kimi K2.6 CODE review of TKT-001, verdict pass_with_changes)

### Low
- **F-S1** (`tests/test_db.py:145-151`): `test_metrics_composite_pk` checks column names but does not verify the composite PRIMARY KEY constraint on `(name, period, period_date)`. Add an explicit duplicate-INSERT test that should raise `IntegrityError`.
- **F-S2** (`tests/test_db.py:47-67`): `test_schema_tables_exist` verifies table names only, not column correctness for tables other than `metrics`. Extend test to introspect column lists for all 12 tables.
- **F-S3** (`Dockerfile:1-13`): Image runs as root. Add `RUN useradd -m -u 1000 smm` and `USER smm` for defense-in-depth.
- **F-S4** (`src/smm_autopilot/db.py:115-124`): `execute_read` acquires `self._write_lock`, but `_write_worker` never acquires the same lock. Under SQLite WAL mode this is technically safe (readers and writers do not block each other), yet the asymmetric locking is confusing. **Remediation**: either remove `_write_lock` from `execute_read` (documenting that WAL mode provides concurrency safety) or acquire it in `_write_worker` for clarity.

These can be addressed in TKT-002 test refactor or in a small follow-up TKT-001a hardening ticket.

## 5. From Devin Review on PR#8 (RV-CODE-001 template/role inconsistencies)

### Low
- Frontmatter `type: code_review` (from `TEMPLATE-code.md`) does not match `reviewer.md:144` contract which mandates `type: code` (matching `RV-SPEC-001` precedent of `type: spec`). Fix: align `docs/reviews/TEMPLATE-code.md` with the role file, OR amend the role file to allow `code_review`. Pick one source of truth.
- Findings grouped by `### Blocking` / `### Non-blocking` (template style) instead of `### High` / `### Medium` / `### Low` (`reviewer.md:145` mandate, matching `RV-SPEC-001` precedent). Same root cause: template diverges from role file. Fix in same place as above.


## Resolution

When ARCH-001 v0.1.2 is opened, the Architect MUST:
- Pull this file into the v0.1.2 ticket.
- Address each Medium item with either a fix in the spec or a justified deferral to v0.2.x with explicit owner and target date.
- Process improvements (§3) update CONTRIBUTING.md or QA-PLAYBOOK.md, not the ArchSpec itself.
