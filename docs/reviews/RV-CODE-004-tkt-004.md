---
id: RV-CODE-004
type: code_review
target_pr: "https://github.com/OpenClown-bot/agents-office/pull/17"
ticket_ref: TKT-004@0.1.3
status: in_review
reviewer_model: "kimi-k2.6"
created: 2026-04-30
updated: 2026-04-30
verdict: pass_with_changes
---

# Code Review — PR #17 (TKT-004@0.1.3 Draft generation service)

## Summary

The PR implements the DraftGenerator component with 36 passing tests, 94% coverage, ruff-clean and mypy-strict-clean code. However, a critical runtime bug causes `generation_retry_count` to over-increment per active channel, exhausting retries prematurely and permanently failing classified items (Devin Review F-1). A secondary moderate bug causes a `TypeError` when `channel.char_limit` is NULL (Devin Review F-2). Additional medium-severity findings include per-variant attribution validation weakness and a TOCTOU race condition in draft deduplication. The verdict is **fail** — the critical bug must be fixed before merge.

## Verdict

- [ ] approve
- [ ] approve with minor comments
- [x] request changes (blocking)

Justification: Critical bug F-1 violates the ArchSpec retry contract (ARCH-001@0.1.2 §3.3) by incrementing `generation_retry_count` N times for N active channels in a single cycle, causing items to be permanently failed after one LLM outage.

## Contract compliance

- [x] PR modifies ONLY files listed in TKT-004@0.1.2 `Outputs` (`src/smm_autopilot/drafting/*`, `tests/test_drafting.py`, `docs/tickets/TKT-004@0.1.2-draft-generation-service.md` frontmatter)
- [x] No changes to `NOT In Scope` items (`llm/client.py`, `llm/providers.py` untouched)
- [x] No new dependencies beyond TKT-001@0.1.1 `requirements.txt`
- [ ] All Acceptance Criteria pass (CI green) — AC5 test is weak (covers 1 channel only, misses F-1); AC6 test is structural only (misses F-6)
- [x] Definition of Done complete (Executor filled §10 Execution Log)

## Acceptance Criteria verification

| AC | Test reference | Status | Notes |
|---|---|---|---|
| AC1: `pytest tests/test_drafting.py -v` passes | All 36 tests pass | **Verified** | 94% coverage |
| AC2: 2 channels → 2 Draft rows, Russian non-empty variants | `test_generate_drafts_two_channels_two_draft_rows`, `test_generate_drafts_russian_variants` | **Verified** | |
| AC3: `char_limit=280` → both variants ≤280 | `test_char_limit_280_enforced` | **Verified** | Does not cover NULL `char_limit` (F-2) |
| AC4: Missing citation/source-span → `status=unverified` | `test_missing_citation_marks_unverified` | **Verified** | Does not cover per-variant citation bypass (F-3) |
| AC5: Timeout retry 2× → `generation_failed` + counters | `test_timeout_retry_marks_generation_failed` | **Weak** | Only 1 channel; misses multi-channel over-increment (F-1) |
| AC6: ≥5 adversarial injection cases → valid JSON, no instruction followed | `test_prompt_injection_mitigation` (5 cases) | **Weak** | Tests prompt structure only, not LLM output behavior (F-5, F-6) |
| AC7: `ruff check` clean | Verified locally | **Verified** | |
| AC8: `mypy --strict` clean | Verified locally | **Verified** | |

## Findings

### Blocking (high)

- **F-1 (CRITICAL) — `_mark_generation_failed` over-increments `generation_retry_count` per active channel.**  
  `service.py:98-100` iterates `for item in items: for channel in channels: await self._generate_draft_for_channel(item, channel)`. Each channel failure independently calls `_mark_generation_failed` at `service.py:162`, which executes `generation_retry_count = generation_retry_count + 1` (`service.py:223`). With N active channels all failing for the same item in one generation cycle, the retry count is incremented N times instead of once. Per ARCH-001@0.1.2 §3.3, the Scheduler retries `generation_failed` items until `generation_retry_count=3`; with 3 channels, a single LLM outage cycle exhausts all retries and permanently fails the item.  
  **Responsible:** Executor.  
  **Remediation:** Restructure `generate_drafts` to collect channel failures per item and call `_mark_generation_failed` at most once per item per cycle. For example, have `_generate_draft_for_channel` return a success/failure boolean, and only mark the item failed after the inner channel loop completes if any channel failed and no recovery path exists.

### Non-blocking (medium)

- **F-2 (MODERATE) — `int(None)` TypeError when `channel.char_limit` is NULL.**  
  `service.py:111`: `char_limit: int = int(channel.get("char_limit", 0)) or 0`. Because the SELECT at `service.py:90` includes `char_limit`, the dict key always exists; when the DB column is NULL the value is `None`. `int(None)` raises `TypeError` before `or 0` is evaluated. The schema (`db.py:75`) defines `char_limit INTEGER` with no `NOT NULL` constraint, so NULL is valid.  
  *Devin Review finding — concur.*  
  **Responsible:** Executor.  
  **Remediation:** Change to `int(channel.get("char_limit") or 0)`.

- **F-3 (MEDIUM) — Attribution validation allows one variant to be unattributed if the other contains a citation URL.**  
  `validation.py:48-51`: `has_cite = _has_citation(combined, citations)` checks whether any citation URL appears in the **combined** text of both variants. If variant A contains a URL but variant B makes a completely unrelated factual claim (e.g. "Mars is a planet" with no source support), the draft is still marked `ready`. ARCH-001@0.1.2 §3.3 states: "Every factual claim must be attributable to the source. If a claim cannot be attributed, paraphrase with inline citation or flag the draft as UNVERIFIED." The current logic weakens G3 (≥80% approval-without-edit).  
  **Responsible:** Executor.  
  **Remediation:** Change `_has_citation` to require each variant to independently contain a citation URL or `_source_span_overlap`, OR split the check so that `has_cite` is evaluated per-variant and both variants must pass.

- **F-4 (MEDIUM) — TOCTOU race condition allows duplicate draft rows under concurrent `generate_drafts()` calls.**  
  `service.py:99-104` performs a separate `SELECT` read to check for existing drafts, then later queues an `INSERT` write. No `UNIQUE(classified_item_id, channel_id)` constraint exists on the `draft` table (`db.py:80-96`). Because the Database class serializes writes via an async queue but does not hold the write lock across the read-check → write-insert gap, two concurrent tasks can both observe no existing draft and both insert.  
  **Responsible:** Executor (with Architect follow-up for schema).  
  **Remediation:** Add `UNIQUE(classified_item_id, channel_id)` to `draft` table schema (requires TKT-001@0.1.1 hardening ticket or PO approval) and change the insert in `service.py:167-180` to `INSERT OR IGNORE` or wrap check+insert in a single atomic transaction.

### Non-blocking (low)

- **F-5 (LOW) — Prompt-injection adversarial test only verifies prompt structure, not LLM behavioral resilience.**  
  `tests/test_drafting.py:test_prompt_injection_mitigation` builds the escaped prompt and asserts line structure, then parses a hardcoded JSON string. It never submits the adversarial prompt to an LLM and never verifies that the LLM output would be valid draft JSON or that injected instructions are ignored. The AC claims "no injected instruction is followed" but the test only proves escaping mechanics.  
  **Responsible:** Executor.  
  **Remediation:** Add an integration-level test (or mocked LLMClient test) that asserts the LLM response parser rejects non-JSON output or output containing the injected instruction text. If real LLM calls are unavailable, document the limitation in the test docstring.

- **F-6 (LOW) — Fullwidth Unicode homoglyphs (`\uff1c`, `\uff1e`) are not escaped by `xml.sax.saxutils.escape`.**  
  `prompts.py:24`: `xml.sax.saxutils.escape` only escapes ASCII `&`, `<`, `>`. The test case `\uff1c/source_text\uff1e` passes because string comparison does not match the fullwidth characters, but the LLM still receives what looks like a delimiter-like structure inside the `<source_text>` block. This leaves a residual prompt-injection surface for models that normalize or visually interpret fullwidth punctuation.  
  **Responsible:** Executor.  
  **Remediation:** Extend `xml_escape_source` to also replace fullwidth less-than `\uff1c` and fullwidth greater-than `\uff1e` with their escaped ASCII equivalents, or explicitly blacklist them in the system prompt.

- **F-7 (LOW) — PR body omits rollback procedure.**  
  Per reviewer.md §B.11, the PR body should state a rollback command/procedure. The body lists files and AC mapping but does not include rollback steps.  
  **Responsible:** Executor.  
  **Remediation:** Add a "Rollback" section to the PR body referencing `git revert` or `git checkout` of the previous tag + `docker compose up -d --build` per ARCH-001@0.1.2 §10.

- **F-8 (LOW) — `generate_drafts` does not implement queue backpressure limits from ARCH-001@0.1.2 §4.1.**  
  `service.py:84` fetches all `classified` items without checking whether the `drafts` table backlog exceeds 500 rows. The ArchSpec states DraftGenerator should "pause non-time-sensitive generation and alerts PO" when `drafts(status=ready|unverified|deferred) >= 500`. This is not an AC but is a contract divergence.  
  **Responsible:** Executor / Architect.  
  **Remediation:** Add a pre-flight count query against the `draft` table; if non-time-sensitive items exceed the threshold, skip generation and log a warning with `structlog`.

## Red-team probes

- **Error paths:** LLM timeout and unparseable responses are handled with 2× retry + `generation_failed` fallback. DB write failures are not caught inside `_generate_draft_for_channel` — an exception would bubble up and stop the entire `generate_drafts` cycle for all remaining items/channels. Consider wrapping the inner loop body in a try/except to continue with other items.
- **Concurrency:** Two concurrent `generate_drafts()` calls can race on the existing-draft check (F-4). The `Database` write queue serializes writes but not the read-write interleaving.
- **Input validation:** `_parse_draft_response` strips markdown code blocks and validates JSON schema, which is reasonable. No upper bound on parsed string length — a malicious LLM response could return multi-megabyte strings causing memory pressure.
- **Observability:** Logs use `structlog` with `classified_item_id` and `channel_id`, which is good. No `trace_id` is carried from ingestion (ARCH-001@0.1.2 §8 mentions trace_id but it is absent from the DB schema and code). Log levels seem appropriate: warnings for failures, info for cycle completion.

## Verdict justification

**fail** — Blocking critical bug F-1 (generation_retry_count over-increment per channel) violates the ArchSpec retry contract and would permanently fail classified items after a single LLM outage when multiple channels are active. Moderate bug F-2 (`TypeError` on NULL `char_limit`) is a straightforward runtime crash. Both must be fixed. Medium findings F-3 and F-4 should be addressed or explicitly deferred with follow-up tickets.

---

## Addendum: Re-review after fix iterations (2026-04-30)

Original verdict: fail. After Architect mini-cycle (PR #20 → TKT-004@0.1.3) and three Executor fix iterations, all findings are addressed:

- F-1: ✅ verified — `_generate_draft_for_channel` returns success/failure; `_mark_generation_failed` is called at most once per item per cycle, only when all channels fail. Test `test_multi_channel_failure_increments_once` at `tests/test_drafting.py:611` confirms.
- F-2: ✅ verified — `int(channel.get("char_limit") or 0)` handles NULL safely. Test `test_null_char_limit_falls_back_to_zero` at `tests/test_drafting.py:669` confirms.
- F-3: ✅ verified — per-variant attribution check in `validation.py`. Test `test_per_variant_attribution_one_unattributed_marks_unverified` at `tests/test_drafting.py:692` confirms.
- F-4: ✅ verified — `UNIQUE(classified_item_id, channel_id)` added to draft table per TKT-004@0.1.3 §7 authorisation; `INSERT OR IGNORE` used in `service.py`. AC9 test `test_concurrent_generate_drafts_no_duplicate_rows` at `tests/test_drafting.py:704` passes.
- F-5: ⏭ deferred to backlog per orchestrator PR #19 (merged). LOW.
- F-6: ✅ verified — fullwidth Unicode `\uff1c` `\uff1e` escaped in `xml_escape_source`.
- F-7: ✅ verified — PR #17 body now has `## Rollback` section per reviewer.md §B.11, references ARCH-001@0.1.2 §10 Deployment Workflow.
- F-8: ⏭ deferred to backlog per orchestrator PR #19 (merged). LOW.
- (New, surfaced by Devin Review on iter1) F-9: ✅ verified — early-skip in `_generate_draft_for_channel` prevents metrics inflation and wasted LLM calls. Tests `test_generate_drafts_skips_items_with_existing_drafts` at `tests/test_drafting.py:733` and `test_generate_drafts_partial_coverage_processes_remaining_channels` at `tests/test_drafting.py:770` confirm.
- (New, surfaced by Devin Review on iter2) Write-zone violation: ✅ verified — §8 Definition of Done checkboxes reverted to `[ ]`.
- (New, surfaced by Devin Review on iter2) Test helper bug: ✅ verified — `_make_draft_response` uses explicit `None`-check (`citations if citations is not None else [...]`).

### Re-review verdict: pass_with_changes

Two LOW-severity findings (F-5, F-8) remain deferred to backlog (PR #19, merged) per PO decision; all blocking and medium findings are resolved.

All Acceptance Criteria from TKT-004@0.1.3 §6 (including AC9) are independently verified. All §7 Constraints honoured. ARCH-001@0.1.2 §3.3 retry contract correctly implemented.
