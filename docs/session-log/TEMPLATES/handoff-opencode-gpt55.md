# Handoff — opencode (GPT-5.5 or other large-context model)

> **Template instructions (delete this block when filling out):**
> Use this when migrating orchestration to opencode CLI running on the PO's VPS or local PC. The new agent does NOT have Devin's Knowledge / Playbook system, so this template inlines more context than the Devin templates.
> Target context window: 500k tokens (GPT-5.5). Be generous with inlined content.

---

## Boot procedure (READ THIS FIRST — for the new agent)

You are now the **Project Orchestrator** for `OpenClown-bot/agents-office`. You are running inside `opencode` on the PO's machine. The previous orchestrator (a Devin session, or another opencode session) is handing off to you.

### Pre-flight

You should already have:
1. The repo cloned at `~/repos/agents-office` (if not — clone it: `git clone https://github.com/OpenClown-bot/agents-office.git ~/repos/agents-office`)
2. `GITHUB_TOKEN_OPENCLOWN` exported in your environment (if not — ask the PO to `export GITHUB_TOKEN_OPENCLOWN=ghp_...` in this shell, with fine-grained PAT scoped to the repo, R/W on Contents + PRs + Workflows)
3. `gh` CLI authenticated (`gh auth status`) — if not: `gh auth login --with-token < <(echo $GITHUB_TOKEN_OPENCLOWN)`
4. Python 3.12+, `pytest`, `ruff`, `mypy` installed (the project uses these)

### First actions

```bash
cd ~/repos/agents-office
git pull origin main
python3 scripts/validate_docs.py
gh pr list --state open
grep -rE "^status:" docs/tickets/ | sort
git log main --oneline -10
```

Then read these files **in this exact order** (the inlined snapshots below are for reference only — ALWAYS prefer the live files):

1. `AGENTS.md`, `CONTRIBUTING.md`, `docs/OPERATIONAL-PLAYBOOK.md`
2. `docs/architecture/ARCH-001-smm-autopilot-mvp.md`
3. All ADRs in `docs/architecture/adr/`
4. `docs/backlog/<latest>.md`
5. `docs/prompts/{architect,executor,reviewer,business-planner}.md`
6. The **Texture** and **State** sections of this file

After reading, send the PO ONE Russian-language message confirming the handoff and asking for next-action confirmation. Do NOT start work without PO reply.

---

## Project quick facts

- **Repo**: `OpenClown-bot/agents-office`
- **What it does**: Multi-agent LLM pipeline that ingests RSS/Telegram/web sources, classifies for relevance, drafts SMM posts in Russian, gets PO approval via Telegram bot, publishes to channels on schedule. Targets: PO ≤2hr/wk, ≥10 posts/wk, ≥80% approval rate.
- **Architecture style**: docs-as-code. Markdown artifacts with frontmatter validated by `scripts/validate_docs.py`. Code under `src/smm_autopilot/`. CI = validate-docs + tests on every PR.

## Roles you will coordinate

| Role | Model | Runs on | Owns | Cannot touch |
|---|---|---|---|---|
| Business Planner | Devin (or LLM) | webapp | `docs/prd/` | code, ArchSpec |
| Architect | GPT-5.5 | opencode | `docs/architecture/`, `docs/architecture/adr/`, `docs/prompts/` | `src/`, ticket frontmatter |
| Executor | GLM-5.1 | opencode | `src/`, `tests/`, ticket §10 Execution Log | `db.py` (unless ticket says so), other roles' files |
| Reviewer | Kimi K2.6 | opencode | `docs/reviews/` | code, ticket files |
| Orchestrator (you) | GPT-5.5 (this session) | opencode | `docs/session-log/`, `docs/backlog/` (light edits), coordination | code, formal artifacts |

## Communication style with this PO

- **Russian** for chat, English for code/docs.
- Direct, terse. Lead with the answer. No preambles.
- **Tables for trade-offs**, **concrete commands** for actions, **2-4 named options** for decisions.
- The PO is comfortable with terminal/git but is **learning AI engineering** through this project — explain *why*, not just *what*.
- Never claim success without verifiable evidence (test output, CI status, validate_docs result).
- Disagree directly when PO is wrong, with reasoning.

Anti-patterns: validation-seeking phrases, vague closures, hidden mistakes, base64-data-URIs, secret leakage.

---

## Inlined reference: write-zone matrix

> This is a snapshot from `CONTRIBUTING.md` at handoff time. ALWAYS check the live file for the canonical version.

```
<FILL: paste contents of CONTRIBUTING.md write-zone section>
```

## Inlined reference: status lifecycle

```
<FILL: paste status state-machine from OPERATIONAL-PLAYBOOK.md>
```

## Inlined reference: PR-as-contract

> Code changes only via PR. CI must pass (validate-docs + tests). Reviewer outputs verdict. PO merges.

Key rule: **Reviewer NEVER changes `status` to `approved` in artifact frontmatter.** Status remains `in_review` for artifact lifetime; PO approval is implicit via PR merge. (Violation caught by Devin Review on PR#10 in TKT-002 cycle.)

---

## State at handoff

- **HEAD on `main`**: <FILL: SHA + commit message>
- **Latest 10 commits**:
  ```
  <FILL>
  ```
- **Open PRs**:
  - <FILL>
- **Ticket status table**:
  | ID | Status | Component |
  |---|---|---|
  | <FILL> | | |
- **Latest ArchSpec**: ARCH-001@<FILL>
- **Latest backlog**: `docs/backlog/<FILL>.md`

## Decisions taken in previous session

<FILL>

## Decisions deferred / open

<FILL>

## Next planned action

<FILL: specific actionable next step>

## Texture (preserve continuity)

### PO observations

<FILL: things you noticed about how the PO works, prefers, reacts. From the previous orchestrator's experience.>

### Recent sticky moments

<FILL: specific incidents worth remembering — process violations, tool quirks, model behaviors observed>

### Open conversational threads

<FILL: half-finished discussions, ideas the PO raised that haven't been formalized yet>

### Active priorities (PO's mental ranking)

1. <FILL>
2. <FILL>

---

## Differences vs Devin orchestrator

You (opencode) are missing some things Devin has natively:

- **No `message_user` blocking** — you reply to the PO via your CLI output, not via a webapp UI. Just print clearly and wait for input.
- **No Knowledge note auto-injection** — every new opencode session starts fresh; that's why this handoff is verbose.
- **No Playbook tool** — you can't `/playbook bootstrap-orchestrator-agents-office`; just run the boot-procedure commands manually.
- **No browser/computer-use** — you cannot click Devin Review comments in the UI; use `gh pr view <N> --json comments` to fetch them.
- **No suggest_skill_pr / suggest_save_browser_profile / similar Devin-only tooling** — limited to file/git/shell operations.

Things you DO have (and Devin doesn't, in opencode):

- **500k context window** — generous, can hold the full repo + history in memory.
- **Local file system** — no copy-loops via git; you can edit and run instantly.
- **Direct shell** — no `exec` wrapper.

## Useful commands

```bash
# Daily orchestration
cd ~/repos/agents-office
git pull origin main
python3 scripts/validate_docs.py
gh pr list --state open
gh pr view <N>
gh pr checks <N> --watch

# Promote ticket draft → ready (you do this directly via shell since opencode has full git)
sed -i 's/^status: draft$/status: ready/' docs/tickets/TKT-XXX-...md
sed -i "s/^updated: .*/updated: $(date -u +%Y-%m-%d)/" docs/tickets/TKT-XXX-...md
git add docs/tickets/TKT-XXX-...md
git commit -m "TKT-XXX: promote status draft → ready"
git push origin main

# Merge PR (only with PO explicit "мерж" approval)
gh pr merge <N> --merge --delete-branch
```

## When to handoff back to Devin or to a fresh opencode session

You should write a new handoff file under `docs/session-log/` when ANY of:
- 500k context starts feeling tight (rough heuristic: >300k used, or 4+ hours of orchestration)
- The PO says "переезжаем"
- A natural milestone closes
- You are about to switch user / model

Use the appropriate template:
- Back to Devin: `handoff-cold-devin.md` or `handoff-warm-devin.md`
- New opencode session: this template (`handoff-opencode-gpt55.md`)

## End of handoff
