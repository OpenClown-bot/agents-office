---
id: RV-SPEC-001
type: spec
target_ref: ARCH-001@0.1.1
status: in_review
reviewer_model: "kimi-k2.6"
created: 2026-04-24
---

# Spec Review — ARCH-001@0.1.1

## Summary

Architecture is internally consistent and PRD-traceable, but contains six medium-severity gaps in schema alignment, operational semantics, and platform API assumptions that should be patched before Executor handoff. No high-severity blockers.

## Verdict

- [ ] approve
- [x] approve with minor comments
- [ ] request changes (blocking)

Justification: Verdict is `pass_with_changes` — multiple medium-severity findings (schema drift, missing expiry rule, misleading Telegram ingestion description, absent quota schema, inconsistent backup semantics) must be resolved in a follow-up patch bump; zero high-severity defects block approval.

## Findings

### Medium

- **M1 — Telegram source ingestion omits admin-privilege requirement.**
  ArchSpec §3.1 and §6 describe ingestion from "public Telegram channels via Bot API `getUpdates` on a read-only bot or channel forwarding". A Telegram bot **cannot** read channel posts via `getUpdates` unless it is an **administrator** of that channel. The phrase "read-only bot" is misleading and risks an Executor implementation that silently fails to ingest Telegram sources.
  Fix: Architect to add a sentence in §3.1 and §6 stating: "The ingestion bot token must be added as an administrator (with read-only privileges acceptable) to every Telegram source channel; alternatively, channel owners must forward posts to a dedicated ingestion chat."
  Role: Architect.

- **M2 — `Draft` image URL schema mismatch between §3.3 and §5.**
  §3.3 (DraftGenerator outputs) lists `variant_a_image_url` and `variant_b_image_url`, but §5 Data Model defines `Draft.image_url` as a single nullable column. The Executor cannot know whether to implement one or two image columns.
  Fix: Architect to align §3.3 with §5 (single `image_url` per draft, because A/B variants differ only in text and share the same source image) or update §5 to add `variant_a_image_url` / `variant_b_image_url`.
  Role: Architect.

- **M3 — No transaction semantics stated for SourceIngester batch persistence.**
  §3.1 says "persist raw items to the database" without specifying whether a batch of items from one poll is atomic. Deduplication by `(source_id, external_id)` prevents duplicates on crash+restart, but the Executor needs to know the intended isolation boundary (single-item insert vs. batch transaction).
  Fix: Add one sentence to §3.1: "Each item is inserted independently; deduplication by `(source_id, external_id)` handles any partial-batch restart."
  Role: Architect.

- **M4 — Deferred draft expiry behavior is undefined.**
  PRD-001@0.1.0 §5 US-2 allows the PO to defer an item "for up to 24 hours". ArchSpec §3.5 (Scheduler) auto-expires time-sensitive items after 24h, but does not state what happens to `deferred` non-time-sensitive drafts after 24h, or whether deferred items are ever automatically re-queued.
  Fix: Architect to add a rule in §3.5 or §4 step 7: "Deferred drafts are re-surfaced in the approval queue after 24 hours; if the PO takes no action for a further 24 hours, the draft is marked `expired`."
  Role: Architect.

- **M5 — X API monthly quota counter lacks a schema definition.**
  TKT-006@0.1.1 §6 Acceptance Criteria requires "X API monthly quota counter MUST be persisted in SQLite (not in-memory)", but no table or column in ArchSpec §5 tracks per-channel monthly post counts. `PublishLog` could be used to derive this, but the Ticket explicitly mandates a persisted counter.
  Fix: Architect to add a `channel_monthly_posts` integer column to the `Channel` table (or a dedicated `QuotaCounter` table) in §5 Data Model.
  Role: Architect.

- **M6 — SQLite backup procedure may produce inconsistent copies under active writes.**
  ArchSpec §10 says "SQLite DB copied to `backups/` directory before each deploy". If writes are in progress during the file copy, the backup may be corrupted or inconsistent. WAL mode reduces but does not eliminate this risk.
  Fix: Specify in §10 that `deploy.sh` must run `docker compose down` (or use `sqlite3 .backup`) before copying the DB file.
  Role: Architect.

### Low

- **L1 — ADR frontmatter `arch_ref` pins to `ARCH-001@0.1.0` on the `ARCH-001@0.1.1` branch.**
  ADR-001@0.1.0 through ADR-004@0.1.0 all list `arch_ref: ARCH-001@0.1.0`. ADR-004@0.1.0 added a compatibility note for `ARCH-001@0.1.1` but did not update its own `arch_ref`. This is cosmetic but reduces traceability.
  Fix: Bump `arch_ref` to `ARCH-001@0.1.1` in all four ADRs, or add a frontmatter `note: created against ARCH-001@0.1.0; compatible with 0.1.1`.
  Role: Architect.

- **L2 — TKT-009@0.1.1 mandates `MemoryMax=6442450944` while ArchSpec uses `6G` suffix.**
  ArchSpec §10 says `MemoryMax=6G`; TKT-009@0.1.1 §6 AC says `MemoryMax=6442450944` (bytes). systemd accepts both, but the inconsistency is unnecessary.
  Fix: Align both documents on one representation (the `6G` suffix is more readable).
  Role: Architect.

- **L3 — `CadenceConfig` table name is misleading.**
  The table only contains `global_kill_switch` and `updated_at`. All per-channel cadence lives in the `Channel` table. The name implies a broader cadence configuration scope than exists.
  Fix: Rename to `GlobalKillSwitch` or add a comment in §5 explaining the table's narrow purpose.
  Role: Architect.

- **L4 — PO time-tracking mechanism for G1 is absent from the data model.**
  PRD-001@0.1.0 §2 G1 requires measuring "PO spends ≤2 hrs/week on SMM operations". ArchSpec §8 states "PO self-reported time log; cross-checked against queue-activity timestamps" but provides no schema, bot command, or automated heuristic.
  Fix: Either add a `po_time_log` table and a `/time start/stop` command to TKT&#45;005b@0.1.0, or replace the metric with an automated proxy (e.g., total duration of queue-interaction sessions derived from `callback_query` timestamps).
  Role: Architect.

- **L5 — `trace_id` correlation is not reflected in the data model.**
  ArchSpec §8 says "Each item carries a `trace_id` (UUID) from ingestion through publish", but no schema in §5 includes a `trace_id` column. The intent appears to be log-only, but the phrasing "carries" suggests a data-model field.
  Fix: Clarify in §8 that `trace_id` is log-context only, or add `trace_id` to `RawItem`, `ClassifiedItem`, `Draft`, and `PublishJob`.
  Role: Architect.

## Cross-reference check

| Check | Result | Notes |
|---|---|---|
| All PRD sections claimed as "implemented" are actually covered | ✅ | Trace Matrix in §1 covers all Goals G1–G3 and User Stories US-1–US-5. |
| All Non-Goals from PRD are respected | ✅ | No component implements NG1–NG11. Browser automation, DMs, comment moderation, multi-step campaigns, analytics A/B, AI images, non-Russian content, GDPR targeting, and auto-throttling are all absent. |
| Resource budget fits Technical Envelope | ✅ | Docker limit 2 CPU / 4 GB < PRD ceiling 3 CPU / 6 GB; systemd backstop 3 CPU / 6 GB matches PRD. |
| Every Ticket in Work Breakdown is atomic | ✅ | TKT-005@0.1.0 was correctly split into TKT&#45;005a@0.1.0 / TKT&#45;005b@0.1.0 / TKT&#45;005c@0.1.0. Each remaining ticket has a single-sentence goal. |
| No hidden assumptions about external systems | ⚠️ | M1: Telegram admin privilege is an unstated external-system assumption. |

## Specific weak points probed (reviewer red-team)

1. **Component crash mid-flow:** SourceIngester crash during a poll leaves a partial batch; deduplication handles restart. Scheduler crash loses in-memory APScheduler state but SQLAlchemyJobStore recovers scheduled jobs. DraftGenerator crash marks `generation_failed` and retries later. No unrecoverable silent data loss.
2. **10× expected load:** SQLite single-writer lock would serialize writes but the async write queue mitigates. LLM free-tier rate limits would trigger fallback/Qwen-Turbo, then keyword-only degradation. No component would exceed the 3 CPU / 6 GB envelope under stated peak (~800 MB, ~1.5 cores for <30s).
3. **Prompt-injection vectors:** Classifier and DraftGenerator both use XML-escaped delimiters + JSON schema output validation. Post-generation attribution check adds a second deterministic barrier. The adversarial test suites in TKT-003@0.1.1 and TKT-004@0.1.1 cover nested delimiters, role-play, homoglyphs, multi-turn leakage, and closing-tag injection. Surface is well-mitigated.
4. **Data-retention story:** No explicit retention policy is defined. SQLite file grows with every ingested item, draft, and publish job. On a 4 GB ceiling, months of operation at 50 writes/hour (~1.2 MB/month estimated) is negligible, but an explicit retention rule (e.g., archive items older than 90 days) is missing. Classified as low follow-up.

## Questions for Architect

- **Q1:** Does the PO intend to seed an initial `SensitivityKeyword` list at deployment, or will the classifier run with zero sensitivity keywords until the PO manually adds them via `/sensitivity add`?
- **Q2:** Should deferred drafts expire, or should they remain in the queue indefinitely until the PO acts?
- **Q3:** Is the single `Draft.image_url` field the correct schema (implying both A/B variants share the same image), or do you need separate `variant_a_image_url` / `variant_b_image_url` columns?
