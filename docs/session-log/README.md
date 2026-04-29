# Session Log

Free-form per-session handoff documents. **NOT formal artifacts** — no frontmatter validation, no version pinning, no Reviewer cycle. Their purpose is to allow any orchestrator agent (a fresh Devin session, an opencode instance, even a different LLM model) to pick up exactly where the previous session stopped — including the **emotional texture** of the work, not just the formal state.

## Why this exists

Devin / opencode / any LLM session has a finite context window. Once it fills up (or once the human runs out of daily credits and switches accounts), continuity is lost. This directory stores **structured handoffs** so that the project itself becomes the long-term memory, not the chat session.

The repo is the source of truth for **formal state** (tickets, ArchSpec, ADRs, reviews, backlog). The session log is the source of truth for **conversational state** — what the previous agent and PO were thinking about, what tone was being used, what was almost-decided but not yet committed.

## Filename convention

```
docs/session-log/YYYY-MM-DD-session-N.md
```

- `YYYY-MM-DD` — date the session was *closed* (UTC)
- `N` — sequential index for that day, starting from 1

Example: `2026-04-28-session-1.md`, `2026-04-28-session-2.md`, `2026-05-02-session-1.md`.

## When to write a handoff

### Cold handoff — auto-generated, no PO request needed

The orchestrator MUST automatically write a `handoff-cold-devin.md`-based file under `docs/session-log/` after **every closed TKT cycle**. "Closed cycle" means: code PR + review PR are both merged into `main`, the ticket's status is `in_review` (artifact-immutable / PO-implicit-approved). This rule lives in `docs/OPERATIONAL-PLAYBOOK.md` §6 and is non-negotiable.

This ensures a recent cold snapshot is always present in the repo, so if the PO suddenly runs out of Devin credits or the session crashes, they can open the latest `docs/session-log/*.md` file and migrate without any prep work.

The orchestrator may ALSO write a cold handoff voluntarily when:

- Devin context-summarization has happened ≥2 times in the current session
- 4+ hours of active orchestration work have accumulated without a TKT-cycle close
- The orchestrator notices itself drifting (forgetting earlier decisions, repeating questions)

### Warm handoff — on PO request only

The orchestrator writes a `handoff-warm-devin.md`-based file ONLY when the PO explicitly asks. Trigger phrases:

- "переезжаем" / "переезжаем в новую сессию"
- "запиши всё что знаешь обо мне" / "warm handoff"
- "save everything" / "сохрани контекст полностью"

When triggered, the orchestrator drops everything else, writes the warm handoff (~1.5–2× the size of cold), and presents the file content to the PO in chat for copy-paste into the new session.

### opencode handoff — on PO request only

The orchestrator writes a `handoff-opencode-gpt55.md`-based file when the PO says "переезжаем в opencode" or similar. This is a fallback for when Devin credits are exhausted across all accounts.

## Templates

Three templates are provided in `docs/session-log/TEMPLATES/`. Pick the one that matches the migration target:

| Template | When to use | Length |
|---|---|---|
| `handoff-cold-devin.md` | New Devin session, possibly different account / different GitHub linked, no prior context with this project. Routine handoff. | ~600 lines max |
| `handoff-warm-devin.md` | Same as cold, but the PO explicitly asked to preserve emotional texture, communication style, and in-flight thoughts. Use when PO says "переезжаем" / "save everything". | ~1200 lines max |
| `handoff-opencode-gpt55.md` | Migration to opencode CLI running GPT-5.5 (or any large-context model) on the PO's local machine or VPS. Includes more inline content because the new agent has no Devin Knowledge / Playbook system. | ~2500 lines, with full role-prompt inlines |

Copy the template, fill it in, save under `docs/session-log/YYYY-MM-DD-session-N.md`, push to main.

## How to use a handoff (PO's perspective)

### 1. New Devin session (any account, any linked GitHub)

1. Open the latest `docs/session-log/*.md` on github.com — copy its raw content.
2. In the new Devin session, paste that content as the first message.
3. Devin will read its own boot-procedure section and ask you for:
   - The repo URL (already in the file)
   - A **GitHub PAT (fine-grained, scoped to this repo)** to put into a session secret named `GITHUB_TOKEN_OPENCLOWN`
   - Confirmation to proceed with the suggested next action
4. Once you provide the token, Devin runs `git clone`, syncs state, and continues from where the previous session left off.

### 2. New opencode session on PO's machine or VPS

1. Open the latest `docs/session-log/*.md` — copy raw content.
2. Start a fresh opencode session with GPT-5.5 (or similar large-context model).
3. Paste content as first message, prefixed by: "Read this handoff. Then begin orchestration."
4. opencode reads the file, asks for repo path / token if not already in env, then continues.

### 3. Pre-planned migration ("переезжаем")

When the PO knows in advance that the current session is winding down:

1. PO says: "переезжаем в новую Devin сессию" (or "in opencode") to current orchestrator.
2. Current orchestrator drops everything else, writes a **warm** handoff (or opencode handoff if requested), pushes to main, AND posts the file content into the chat for the PO to copy directly.
3. PO copies file content from chat (or from the GitHub raw view), opens new session, pastes as first message.
4. New session runs its boot self-check (auto-detects missing repo / token, asks PO only for what's missing), reads the file, sends a confirmation message reflecting 1–2 details from the Texture section, then waits for PO go-ahead.

### 4. Unplanned migration — credits ran out unexpectedly

1. PO opens the latest `docs/session-log/*.md` file on github.com (raw view) — should be a cold handoff if the previous session followed the auto-rule.
2. PO copies content, opens new Devin session in another account, pastes, provides token if asked.
3. New session boots, syncs, asks confirmation question. PO continues.

No warm texture is preserved in this case — the cold handoff has all formal state but lacks PO-observation / texture sections. This is the trade-off of unplanned migration.

## What the handoff MUST contain

Each handoff file is a self-contained document. Even if the new agent has zero context about this project, reading just this file should be enough to:

1. Know what this project is (`OpenClown-bot/agents-office`, multi-agent LLM pipeline for SMM Autopilot)
2. Know the agent's role (PO orchestrator)
3. Know what was just accomplished
4. Know what is pending and which files describe it
5. Know how to communicate with the PO (language, tone, preferred output formats)
6. Know what the immediate next action should be

The templates enforce this via mandatory sections.

## What the handoff should NOT contain

- Secrets (tokens, passwords, API keys) — only secret *names*
- Speculative architectural decisions — those go to ADRs
- New code — code goes through Executor → Reviewer → PR cycle
- Anything that should be in a formal artifact (PRD/ARCH/ADR/TKT/RV) — write the artifact instead

## Lifecycle

- Files in `docs/session-log/` are **append-only**. Never edit a past session log file.
- Files older than 60 days *may* be moved to `docs/session-log/archive/YYYY-MM/` to reduce noise (manual decision by PO).
- The latest file is always the canonical "where are we now" snapshot.
