# Handoff — Devin (warm)

> **Template instructions (delete this block when filling out):**
> Use this when the PO explicitly asked to migrate ("переезжаем"), or when significant emotional/conversational texture has accumulated in the session that the next agent needs to preserve continuity.
> **Generated on demand only** — the orchestrator does NOT auto-write warm handoffs (cold version is auto-written after each TKT cycle per OPERATIONAL-PLAYBOOK §9). Warm version is the PO's explicit request: "переезжаем", "save everything", "запиши всё что знаешь обо мне".
> Includes everything from `handoff-cold-devin.md` PLUS texture sections.

---

## Boot procedure (READ THIS FIRST — for the new agent)

You are the new **Project Orchestrator** for `OpenClown-bot/agents-office`. The previous Devin session is winding down (credits exhausted, context full, or PO-initiated migration) and is handing the project to you with full conversational continuity.

### Self-check (run these BEFORE asking the PO anything)

Verify all three preconditions yourself, ask only for what is missing.

#### 1. Repo access — local clone

```bash
ls ~/repos/agents-office/.git >/dev/null 2>&1 && echo "REPO_OK" || echo "REPO_MISSING"
```

If `REPO_MISSING`:
```bash
git clone https://github.com/OpenClown-bot/agents-office.git ~/repos/agents-office 2>&1
```
If clone fails with 403 / not authorized → continue to step 2 (token), then retry with token (step 3).

#### 2. GitHub PAT

```bash
[[ -n "$GITHUB_TOKEN_OPENCLOWN" ]] && echo "TOKEN_OK" || echo "TOKEN_MISSING"
```

If `TOKEN_MISSING`:
- `secrets` tool: `action="request"`, `secret_name="GITHUB_TOKEN_OPENCLOWN"`, `type="plain"`, `should_save=true`, `save_scope="user"`, `note="Fine-grained PAT for OpenClown-bot/agents-office. Permissions: Contents R/W, Pull requests R/W, Workflows R/W, Metadata R."`
- If PO doesn't have a PAT, link to: https://github.com/settings/personal-access-tokens/new

#### 3. Repo access via PAT (only if step 1 failed)

```bash
git clone https://x-access-token:${GITHUB_TOKEN_OPENCLOWN}@github.com/OpenClown-bot/agents-office.git ~/repos/agents-office
```

If still fails — token lacks repo access; ask PO to fix permissions.

#### 4. Sync + sanity check

```bash
cd ~/repos/agents-office
git pull origin main
python3 scripts/validate_docs.py | tail -3
git log main --oneline -10
```

Must report `0 failed`. If not, STOP and surface to PO.

### Never tell the PO "make sure X is set up before pasting this"

They pasted this file precisely because they want YOU to handle bootstrap. Self-check first; ask only for what's missing.

### After self-check passes

Read in this order:
1. `AGENTS.md`, `CONTRIBUTING.md`, `docs/OPERATIONAL-PLAYBOOK.md`, `docs/QA-PLAYBOOK.md`
2. `docs/architecture/ARCH-001-smm-autopilot-mvp.md` (latest version)
3. All ADRs in `docs/architecture/adr/` (5 files, short)
4. `docs/backlog/<latest>.md`
5. `docs/prompts/{architect,executor,reviewer,business-planner}.md`
6. **This file (the rest)** — read every section, especially "Texture" and "PO observations"

After reading, send the PO ONE Russian-language message:
- Confirm self-check passed (one line: "Repo synced, validate-docs clean.")
- **Reflect back to PO 1-2 specific things from the Texture section** (proves you actually read it; this is the PO's sanity check)
- Ask the suggested "Next action" question

Then WAIT for PO reply.

---

## Project quick facts

- **Repo**: `OpenClown-bot/agents-office`
- **What it does**: Multi-agent LLM pipeline that ingests RSS / Telegram / web sources, classifies for relevance + sensitivity, drafts SMM posts in Russian, gets PO approval via Telegram bot, publishes to channels on schedule. Targets: PO ≤2hr/wk, ≥10 posts/wk, ≥80% approval rate.
- **Architecture**: docs-as-code; markdown artifacts validated by `scripts/validate_docs.py`. Code under `src/smm_autopilot/`. CI = validate-docs + tests on every PR.
- **MVP runs on**: 4c / 8GB shared VPS. Python 3.12 + SQLite + APScheduler + httpx. No Node, no extra runtimes (per ADR-005).

## Roles

| Role | Model | Runs on | Owns | Cannot touch |
|---|---|---|---|---|
| Business Planner | Devin (separate session) | webapp | `docs/prd/` | code, ArchSpec |
| Architect | GPT-5.5 | opencode on PO's VPS | `docs/architecture/`, `docs/architecture/adr/`, `docs/tickets/` | `docs/prd/`, `src/`, `docs/prompts/`, ticket frontmatter on `status: approved` |
| Executor | GLM-5.1 | opencode on PO's VPS | `src/`, `tests/`, ticket §10 Execution Log | other roles' files |
| Reviewer | Kimi K2.6 | opencode on PO's VPS | `docs/reviews/` | code, ticket files, NEVER `status: approved` |
| **Orchestrator (you)** | Devin | webapp | Coordination + `docs/session-log/` + `docs/backlog/` (light edits / new entries) + ticket frontmatter promotions (`status`, `arch_ref`, `version`, `updated`) + light reference-pinning in ticket body | code, formal artifact bodies (PRD/ARCH/ADR/RV), `docs/prompts/` |

## Communication style with this PO

The PO is Russian-speaking, comfortable with terminal/git/Markdown, but **explicitly learning AI engineering and orchestration through this project**. Treat every interaction as efficient orchestration AND a teaching opportunity.

**Patterns that work for this PO**:
- Tables for trade-offs (Pro/Con; Option A/B/C)
- Concrete commands, not vague suggestions
- 2-4 named options when asking for decisions
- Honest "I don't know" rather than confident guesses
- Short paragraphs — no walls of text
- Direct disagreement when PO is wrong, with reasoning
- Use `<ref_file file="..." />` and `<ref_snippet file="..." lines="..." />` for code/doc citations
- Send screenshots as attachments via `message_user`, not as base64

**Anti-patterns to avoid**:
- Validation-seeking phrases ("отличный вопрос!", "хорошая идея!")
- Vague closures ("давай попробуем", "может сработать")
- Hidden mistakes — surface them immediately, root-cause, fix
- Apologetic preambles
- Never claim success without verifiable evidence

## Texture from the previous session

> Fill in observations the human cares about — these enable conversational continuity.

### Observations about the PO

- <FILL: e.g. "PO has multiple Devin accounts, rotates them to extend daily credits.">
- <FILL: e.g. "PO works in evening sessions, prefers compact responses after 22:00 UTC.">
- <FILL: e.g. "PO is sensitive to over-promising — prefers 'we'll see' to 'definitely'.">
- <FILL: e.g. "PO appreciates initiative with the GitHub token (e.g. promoting tickets, merging approved PRs) over asking for every click.">

### Specific recent moments worth carrying forward

- <FILL: e.g. "Devin Review caught a process violation (Reviewer set status: approved). PO appreciated that I owned the mistake — turned out my prompt to Reviewer was wrong.">
- <FILL: e.g. "We had to nudge Kimi K2.6 because she over-deliberated for 25min on RV-CODE-003 — lesson is 20-min mark for pinpoint.">
- <FILL: any other sticky moments>

### Open conversational threads

- <FILL: e.g. "PO wants Aaron-SEO checklists referenced in TKT-004 DraftGenerator §4 Inputs as inspiration source.">
- <FILL: any unfinished thoughts the PO raised>

### Active priorities (PO's mental ranking)

1. <FILL: top priority>
2. <FILL: second>
3. <FILL: ...>

## State at handoff (formal)

- **HEAD on `main`**: <FILL: SHA + commit message>
- **Latest 10 commits**:
  ```
  <FILL>
  ```
- **Open PRs**: <FILL: #N + title + branch, or "none">
- **Ticket status table**:
  | ID | Status | Component | Notes |
  |---|---|---|---|
  | <FILL> | | | |
- **Latest ArchSpec**: ARCH-001@<FILL>
- **Latest backlog file** + key open items: <FILL>
- **Latest review verdicts** (last 3): <FILL>

## Decisions taken in the previous session

<FILL: ordered list of merged PRs, merged ADRs, key process decisions, with one-line rationale each>

## Decisions deferred / open with PO

<FILL: things the previous session did not resolve, with context for each>

## Next planned action

<FILL: specific, actionable, e.g. "Promote TKT-004 status draft → ready, add Aaron-SEO inspiration ref to §4 Inputs, send Executor prompt to GLM-5.1.">

## Pitfalls / lessons from the previous session

<FILL: process gotchas, tool quirks, things-to-not-repeat>

## Useful commands cheatsheet

```bash
python3 scripts/validate_docs.py
curl -s -H "Authorization: Bearer $GITHUB_TOKEN_OPENCLOWN" \
  "https://api.github.com/repos/OpenClown-bot/agents-office/pulls?state=open" | jq '.[] | {n:.number,t:.title,b:.head.ref}'
git log main --oneline -10
grep -rE "^status:" docs/tickets/ | sort
```

## Models in active use

| Role | Model | Where it runs | Notes |
|---|---|---|---|
| Architect | GPT-5.5 | opencode on PO's VPS | Solid, large output. Sometimes truncates large docs into multiple commits. |
| Executor | GLM-5.1 | opencode on PO's VPS | Fast, follows tickets literally. Sometimes misses subtle ArchSpec contract clauses (e.g. metric counter semantics). |
| Reviewer | Kimi K2.6 | opencode on PO's VPS | Excellent depth, but over-deliberates. Pinpoint at 20-min mark if no commit yet. |
| Business Planner | Devin (separate session) | webapp | Optional; only run when PRD needs new vision/scope work. |
| Orchestrator (you) | Devin | webapp | This is you. |

## End of handoff
