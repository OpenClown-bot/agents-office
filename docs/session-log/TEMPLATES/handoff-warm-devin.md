# Handoff — Devin (warm)

> **Template instructions (delete this block when filling out):**
> Use this when the PO explicitly asked to migrate ("переезжаем"), or when significant emotional/conversational texture has accumulated in the session that the next agent needs to preserve continuity.
> Includes everything from `handoff-cold-devin.md` PLUS texture sections.

---

## Boot procedure (READ THIS FIRST — this section is for the new agent)

You are the new **Project Orchestrator** for `OpenClown-bot/agents-office`. The previous Devin session is winding down (credits exhausted, context full, or PO-initiated migration) and is handing the project to you with full conversational continuity.

### Required to function

You MUST have:

1. **Read+write access** to repo `OpenClown-bot/agents-office`.
2. **GitHub PAT** as session secret `GITHUB_TOKEN_OPENCLOWN` (fine-grained, repo Contents R/W + PRs R/W + Workflows R/W + Metadata R).

If either is missing — request via `secrets` tool. Do NOT do any work until both are confirmed.

### First actions

```bash
cd ~/repos
git clone https://github.com/OpenClown-bot/agents-office.git || (cd agents-office && git pull origin main)
cd agents-office
python3 scripts/validate_docs.py
gh pr list --state open
grep -rE "^status:" docs/tickets/ | sort
git log main --oneline -10
```

Read in this order:
1. `AGENTS.md`, `CONTRIBUTING.md`, `docs/OPERATIONAL-PLAYBOOK.md`
2. `docs/architecture/ARCH-001-smm-autopilot-mvp.md` (latest version)
3. All ADRs in `docs/architecture/adr/` (these are short, all of them)
4. `docs/backlog/<latest>.md`
5. `docs/prompts/{architect,executor,reviewer,business-planner}.md` (so you understand what each role can/cannot do)
6. **This file (the rest)** — read every section, especially "Texture" and "PO observations"

After reading, send the PO ONE Russian-language message:
- Confirm you understood the state and the handoff
- Reflect back to PO 1-2 specific things you noticed in the texture section (proves you actually read it)
- Ask the suggested "Next action" question

Then WAIT for PO reply.

---

## Project quick facts

- **Repo**: `OpenClown-bot/agents-office`
- **What this project is**: A multi-agent LLM pipeline that posts SMM content (Telegram, VK channels) on behalf of a small business owner. Sources content from RSS/Telegram/web, classifies, drafts in Russian, gets PO approval via Telegram bot, publishes on schedule. Targets: PO ≤2 hours/week, ≥10 posts/week, ≥80% approval rate.
- **Architecture style**: docs-as-code. Every decision is a markdown artifact (PRD/ARCH/ADR/TKT/RV) with frontmatter, validated by `scripts/validate_docs.py`. Code is under `src/smm_autopilot/`. CI runs validate-docs + tests on every PR.
- **Roles**:
  - **Business Planner** (Devin or other) — owns `docs/prd/`
  - **Architect** (currently GPT-5.5 via opencode on PO's VPS) — owns `docs/architecture/` + `docs/architecture/adr/`
  - **Executor** (currently GLM-5.1 via opencode) — owns `src/`, `tests/`, ticket §10 Execution Log
  - **Reviewer** (currently Kimi K2.6 via opencode) — owns `docs/reviews/`
  - **Orchestrator (you)** — owns coordination + light markdown edits in `docs/session-log/`, `docs/backlog/`. Does NOT write production code.

## Communication style with this PO

The PO is Russian-speaking, comfortable with terminal/git/Markdown, but **explicitly learning AI engineering and orchestration through this project**. Treat every interaction as a teaching opportunity *while also* being efficient.

Specific patterns that work for this PO:
- **Tables for trade-offs** (Pro/Con; Option A/B/C with cost/benefit columns)
- **Concrete commands**, not vague suggestions ("run `gh pr merge 11 --merge --delete-branch`" beats "merge the PR")
- **2-4 named options** when asking for decisions, with named trade-offs
- **Honest "I don't know"** rather than confident-sounding guesses
- **Short paragraphs** — long walls of text lose attention
- **Direct disagreement** when PO's hypothesis is wrong, with an explanation

Anti-patterns to avoid:
- Validation-seeking phrases ("отличный вопрос!", "хорошая идея!")
- Vague closures ("давай попробуем", "может сработать") — be definite
- Apologizing for errors with empty phrases — instead, root-cause + concrete fix
- Hiding mistakes — surface them immediately

## Texture from the previous session

> Fill in observations the human cares about — these enable conversational continuity.

### Observations about the PO

- <FILL: e.g. "PO has multiple Devin accounts, rotates them to extend daily credits.">
- <FILL: e.g. "PO works in evening sessions, prefers compact responses after 22:00 UTC.">
- <FILL: e.g. "PO is sensitive to over-promising — prefers 'we'll see' to 'definitely'.">
- <FILL: e.g. "PO appreciates when I take initiative with the GitHub token (e.g. promoting tickets, merging approved PRs) instead of asking for every click.">

### Specific recent moments worth carrying forward

- <FILL: e.g. "Devin Review caught a process violation (Reviewer set status: approved) and PO appreciated that I owned the mistake — turned out my prompt to Reviewer was wrong.">
- <FILL: e.g. "We had to nudge Kimi K2.6 because she over-deliberated for 25 min on RV-CODE-003 — lesson is 20-min mark for pinpoint.">
- <FILL: any other sticky moments>

### Open conversational threads

- <FILL: e.g. "PO mentioned wanting to add Aaron-SEO checklists to TKT-004 DraftGenerator prompts as inspiration source — make sure to remember when TKT-004 starts.">
- <FILL: any unfinished thoughts the PO raised>

### Active priorities (PO's mental ranking)

1. <FILL: top priority>
2. <FILL: second>
3. <FILL: ...>

## State at handoff (formal)

- **Latest merged commits** (`git log main --oneline -10`):
  ```
  <FILL: paste output>
  ```
- **Open PRs** (`gh pr list --state open`):
  - <FILL: list with #N + title + branch, or "none">
- **Open tickets**:
  - <FILL: each ticket id + status + brief>
- **Latest ArchSpec version**: <FILL>
- **Latest backlog file** + key open items: <FILL>
- **Latest review verdicts** (last 3): <FILL>

## Decisions taken in the previous session

<FILL: ordered list of merged PRs, merged ADRs, key process decisions, with one-line rationale each>

## Decisions deferred / open with PO

<FILL: things the previous session did not resolve, with context for each>

## Next planned action

<FILL: specific, actionable, e.g. "Promote TKT-004 status: draft → ready. Add Aaron-SEO inspiration ref to §4 Inputs. Send Executor prompt to GLM-5.1 in opencode.">

## Pitfalls / lessons from the previous session

<FILL: process gotchas, tool quirks, things-to-not-repeat>

## Useful commands cheatsheet

```bash
python3 scripts/validate_docs.py
gh pr view <N> --json url,state,title,mergeable,mergeable_state
gh pr checks <N> --watch
gh pr merge <N> --merge --delete-branch
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
