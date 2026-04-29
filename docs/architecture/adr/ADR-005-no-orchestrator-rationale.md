---
id: ADR-005
title: "No OpenClaw Orchestrator for SMM Autopilot MVP"
status: proposed
arch_ref: ARCH-001@0.1.2
author_model: "claude-opus-4.6-thinking"
created: 2026-04-28
updated: 2026-04-28
superseded_by: null
---

# ADR-005: No OpenClaw Orchestrator for SMM Autopilot MVP

## Context

ARCH-001@0.1.2 re-evaluates whether SMM Autopilot should adopt OpenClaw as a top-level orchestrator, gateway, cron scheduler, Telegram surface, and skill runtime. PRD-001@0.1.0 requires a small, deterministic, official-API-only SMM pipeline with PO approval, factuality gating, Russian-language drafting, cadence enforcement, and operation on a shared 4c / 8 GB VPS.

OpenClaw's own documentation describes it as a self-hosted multi-channel Gateway for a personal AI assistant, where one long-lived Gateway owns messaging surfaces and bridges them to AI agents (https://docs.openclaw.ai, https://docs.openclaw.ai/concepts/architecture). Its GitHub README likewise frames OpenClaw as a personal AI assistant with many messaging channels and a Node 24 / Node 22.14+ runtime (https://github.com/openclaw/openclaw). This makes it a plausible operator gateway, but not a direct replacement for the existing Python SourceIngester -> Classifier -> DraftGenerator -> ApprovalBot -> Scheduler -> ChannelPublishers pipeline.

OpenClaw supports Telegram via grammY with long polling by default, pairing / allowlist controls, inline buttons, and message actions (https://docs.openclaw.ai/channels/telegram). It also has built-in cron inside the Gateway with persistent jobs at `~/.openclaw/cron/jobs.json` (https://docs.openclaw.ai/automation/cron-jobs). Skills are AgentSkills-compatible folders loaded by precedence and allowlists, and OpenClaw explicitly warns to treat third-party skills as untrusted code (https://docs.openclaw.ai/tools/skills). Plugins can add channels, tools, providers, hooks, skills, and background services, but native plugins run in-process with the Gateway and require Gateway restarts for runtime-code changes (https://docs.openclaw.ai/tools/plugin). OpenClaw security guidance assumes a one-operator personal-assistant trust boundary, not hostile multi-tenant isolation (https://docs.openclaw.ai/gateway/security).

The relevant skills marketplace is broad but supply-chain-sensitive. VoltAgent's Awesome OpenClaw Skills list says it curates thousands of ClawHub skills, not audits them, and warns that skills can include prompt injections, tool poisoning, hidden malware payloads, or unsafe data handling (https://github.com/VoltAgent/awesome-openclaw-skills). The Aaron SEO/GEO bundle is a comparatively structured example: ClawHub lists `aaron-seo-geo` v9.9.5 as a source-linked bundle with scan metadata and 20 SEO/GEO skills (https://clawhub.ai/plugins/aaron-seo-geo), while the source README states it is zero-dependency markdown for SEO/GEO workflows and does not guarantee rankings, legal compliance, or business outcomes (https://github.com/aaron-he-zhu/seo-geo-claude-skills). It is useful prior art for content-quality checklists, not a replacement for PRD-001@0.1.0's SMM runtime.

## Options Considered

### Option A: Keep the bespoke Python pipeline; do not run OpenClaw in MVP
- **Pros:**
  - Preserves ADR-001@0.1.0 through ADR-004@0.1.0: Python 3.12, SQLite, direct HTTP LLM routing, and APScheduler.
  - Keeps one application process and one SQLite state model; no second Gateway runtime, no second scheduler state store, and no extra Node process on the shared VPS.
  - Keeps official platform API publishing explicit in ChannelPublishers, which directly supports PRD-001@0.1.0 NG3 and US-5.
  - Avoids third-party skill supply-chain risk in the publish path.
  - Keeps the approval queue implementation testable with deterministic Telegram Bot API behavior.
- **Cons:**
  - Does not reuse OpenClaw's mature multi-channel gateway or Telegram pairing UX.
  - Natural-language skill discovery, plugin ecosystem, and OpenClaw Control UI are unavailable in MVP.
  - Future multi-channel operator inbox work will require a fresh integration decision.

### Option B: Make OpenClaw the top-level OrchestratorAgent
- **Pros:**
  - Reuses OpenClaw Gateway, Telegram support, channel routing, cron, skills, plugins, and Control UI.
  - Could expose future operator commands through OpenClaw channels without building each from scratch.
  - Skill allowlists and plugin hooks provide a generalized extension surface.
- **Cons:**
  - Adds Node 24 / Node 22.14+ runtime and a long-lived Gateway process in addition to the Python pipeline, increasing operational burden on the shared VPS.
  - Requires mapping durable SMM state from SQLite into OpenClaw sessions, cron jobs, tools, or plugins; this creates two state authorities instead of one.
  - OpenClaw cron persists outside the application DB, while ARCH-001@0.1.2 uses SQLite for auditability and migrations.
  - OpenClaw's security model is one trusted operator boundary; it does not remove prompt-injection or delegated-tool risks for external source content.
  - A top-level LLM agent deciding pipeline steps would weaken deterministic PRD safeguards around factuality, ToS refusal, cadence, and no-autonomous-publishing.

### Option C: Hybrid integration: OpenClaw for ApprovalBot / operator UI only
- **Pros:**
  - Could reuse Telegram allowlists, inline buttons, DMs, and future multi-channel operator messages.
  - Keeps the Python ingestion/classification/drafting/publishing pipeline intact.
  - Creates a migration path if the PO later wants Slack/Discord/WhatsApp operator control.
- **Cons:**
  - Still adds a second long-lived Gateway and config/secrets store only to replace a narrow ApprovalBot component.
  - Approval latency would depend on Python <-> OpenClaw integration glue and channel action semantics.
  - Inline approval callbacks must still be checked against the SMM SQLite draft state, so the Python bot logic remains necessary or becomes a custom plugin.
  - No MVP PRD goal requires multi-channel operator control; Telegram-only approval is accepted risk in ARCH-001@0.1.2.

### Option D: Install selected OpenClaw / Awesome skills into the SMM runtime
- **Pros:**
  - Existing skills cover social posting, RSS digestion, SEO/GEO content, source research, safety gates, cron, backups, and notifications.
  - Aaron SEO/GEO skills provide useful content-quality and entity-optimization checklists for future prompt design.
  - Skill ecosystem could accelerate later non-MVP workflows.
- **Cons:**
  - Skills are instructions/tool wrappers, not versioned application components with the SMM Autopilot data model, acceptance tests, or rollback plan.
  - Many social-posting candidates depend on third-party schedulers, browser automation, cookies, MTProto/user APIs, or unofficial scraping paths that conflict with PRD-001@0.1.0 NG3.
  - Marketplace curation is not an audit; installing skills into the runtime expands the trusted code/prompt surface.
  - Skills do not supply the specific PRD logic: Russian language only, source-span factuality validation, sensitive sub-queue, exact per-channel cadence ceilings, and official API refusal paths.

## Relevant Skill Inventory

The Phase 0 scan iterated the Awesome OpenClaw Skills categories most relevant to PRD-001@0.1.0: Marketing & Sales, Productivity & Tasks, Communication, Search & Research, Browser & Automation, Calendar & Scheduling, Self-Hosted & Automation, Security & Passwords, Data & Analytics, Clawdbot Tools, and high-signal Web & Frontend entries.

| Area | Relevant candidates | Fit for PRD-001@0.1.0 | Decision |
|---|---|---|---|
| Social scheduling / publishing | `adaptlypost`, `postfast`, `postiz`, `publora`, `publora-telegram`, `publora-threads`, `publora-twitter`, `simplified-social-media`, `social-media-manager`, `x-agent`, `x-oauth-api`, `opentweet-x-poster`, `baoyu-post-to-x`, `x-cli`, `bird`, `bluesky`, `facebook`, `facebook-page-manager`, `ghost-cms` | Some can post or schedule, but most introduce third-party platforms, broad channel sets, cookie/API ambiguity, or missing PRD-specific approval/factuality controls. | Do not install. Keep custom ChannelPublishers over official APIs only. |
| Browser / unofficial automation | `agent-browser`, `super-browser`, `actionbook`, `camoufox`, `b0tresch-stealth-browser`, `x-automation`, `instagram-scraper`, `weibo-manager`, `2captcha` | Browser automation and anti-detection tooling directly conflict with PRD-001@0.1.0 NG3 for publishing paths. | Explicitly reject for MVP publish or ingestion paths. |
| Source ingestion / research | `freshrss-reader`, `rss-skill`, `feed-to-md`, `rss-digest`, `feed-digest`, `ak-rss-24h-brief`, `hfnews`, `daily-news`, `fund-news-summary`, `search-cluster`, `openclaw-free-web-search`, `web-search-pro`, `desearch-ai-search`, `x-monitor`, `x-actionbook-recap`, `x-tweet-fetcher`, `readx`, `social-intelligence`, `telegram-history`, `tg-mtproto-cli`, `sergei-mikhailov-tg-channel-reader` | RSS skills overlap with SourceIngester but do not own SMM DB state. X/Twitter and Telegram history skills often rely on third-party indexes, MTProto, user sessions, or scraping-like behavior. | Use as future inspiration only. MVP keeps RSS/public web/Bot API ingestion in Python. |
| Drafting / content quality | `brand-voice-profile`, `content-creator`, `content-generation`, `blogburst`, `content-research`, `content-remix-studio`, `content-repurposer-pro`, `sovereign-brand-voice-writer`, `seo-content-writer`, `geo-content-optimizer`, `meta-tags-optimizer`, `content-quality-auditor`, `domain-authority-auditor`, `entity-optimizer`, Aaron SEO/GEO bundle | Useful prompt/checklist prior art, especially quality and entity-audit concepts. They do not enforce Russian-only posts, citations, source-span validation, or PRD channel constraints by construction. | Do not install in runtime. Reference concepts only if future prompt-ticket revisions need them. |
| Approval / human-in-the-loop | `agentgate`, `postwall`, `personal-data-hub`, `workcrm`, `questions-form`, `sanctifai` | Confirms that human approval patterns exist, but they target generic data/API/email workflows rather than SMM draft state and Telegram inline callbacks. | Keep custom ApprovalBot. |
| Security / audit / policy | `aegis-shield`, `pipelock`, `authensor-gateway`, `agent-audit-trail`, `clauditor`, `skillguard-audit`, `skill-provenance`, `pyx-scan`, `domain-trust-check`, `facticity-ai`, `glin-profanity`, `compliance-officer` | Useful as security vocabulary. Runtime adoption would expand supply-chain surface and still need custom SMM policy tests. | Keep deterministic escaping, schema validation, attribution checks, and logs in Python. |
| Scheduling / ops / notifications | `casual-cron`, `cron-backup`, `cron-retry`, `job-execution-monitor`, `gotify`, `rho-telegram-alerts`, `telegram-todolist`, `todo-boss`, `n8n`, `n8n-workflow-automation` | Overlaps with APScheduler, backup retention, and Telegram alerts but adds external workflow/config surfaces. | Keep APScheduler, Docker restart policy, SQLite backup, and ApprovalBot alerts. |
| OpenClaw ecosystem / connectors | `agent-builder`, `agents-manager`, `claw-sync`, `provider-sync`, `clawdbot-security-check`, `mcp-client`, `pipedream-connect`, `zapier-mcp`, Composio references | Useful if SMM Autopilot becomes an OpenClaw-native product later. Not needed for current PRD goals. | Defer to a future PRD/ADR. |

## Decision

We will use **Option A: keep the bespoke Python pipeline and do not run OpenClaw as an orchestrator, gateway, cron scheduler, or skill runtime in the MVP**.

OpenClaw is a strong personal-assistant gateway, but SMM Autopilot MVP is a constrained, deterministic automation service. The MVP's hard requirements are official API publishing, exact cadence enforcement, source-grounded Russian drafts, PO approval from Telegram, and a single SQLite audit trail. OpenClaw would add a second runtime and a broad extension surface without replacing the core domain logic.

OpenClaw and selected skills remain architecture inputs, not runtime dependencies. Future work may revisit OpenClaw if a new PRD requires multi-channel operator control, OpenClaw-native skills as first-class product extension points, or a personal-assistant experience beyond the Telegram approval queue.

## Consequences

- **Positive:** MVP remains within the existing Python / SQLite / APScheduler resource and operational envelope.
- **Positive:** The trusted code and prompt surface stays small; no third-party skills are installed into production.
- **Positive:** ChannelPublishers remain explicit official-API adapters with deterministic refusal behavior.
- **Negative:** The MVP does not get OpenClaw's Control UI, pairing UX, multi-channel operator surface, or skill marketplace.
- **Negative:** If the PO later wants an OpenClaw-native operator assistant, integration will require a new PRD/ADR and migration plan.
- **Follow-up:** If revisited, require exact version/commit pinning for every OpenClaw plugin/skill, `openclaw security audit --deep`, sandboxed tool policy, a single source-of-truth decision for scheduler state, and proof that every write path still satisfies PRD-001@0.1.0 NG3.

## References

- OpenClaw docs home: https://docs.openclaw.ai
- OpenClaw Gateway architecture: https://docs.openclaw.ai/concepts/architecture
- OpenClaw Telegram channel docs: https://docs.openclaw.ai/channels/telegram
- OpenClaw skills docs: https://docs.openclaw.ai/tools/skills
- OpenClaw plugins docs: https://docs.openclaw.ai/tools/plugin
- OpenClaw cron docs: https://docs.openclaw.ai/automation/cron-jobs
- OpenClaw security docs: https://docs.openclaw.ai/gateway/security
- OpenClaw GitHub repository: https://github.com/openclaw/openclaw
- Awesome OpenClaw Skills: https://github.com/VoltAgent/awesome-openclaw-skills
- Aaron SEO/GEO ClawHub bundle: https://clawhub.ai/plugins/aaron-seo-geo
- Aaron SEO/GEO source repository: https://github.com/aaron-he-zhu/seo-geo-claude-skills
