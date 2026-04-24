---
id: PRD-001
title: "SMM Autopilot MVP"
version: 0.1.0
status: draft            # draft | in_review | approved | superseded
owner: "@yourmomsenpai"
author_model: "claude-opus-4.7"
created: 2026-04-24
updated: 2026-04-24
supersedes: null
superseded_by: null
related: []
---

# PRD-001: SMM Autopilot MVP

## 1. Problem Statement

The Product Owner operates a Russian-language VPN service (Remnawave + Bedolaga bot + cabinet on a separate host; remnanode + omniroute on a shared Hetzner 4c/8GB VPS) whose primary audience is Russian-speaking users inside the Russian Federation who rely on the VPN to reach Instagram, Threads, X, and other blocked platforms. There is currently no social-media presence for the product: SMM baseline is zero posts per week, and the PO cannot personally sustain consistent brand output while also running the VPN infrastructure. The business consequence is missed demand generation in the exact channels the product's own users inhabit. The epic is worth doing now because (a) the product is operational and needs a growth loop, (b) there is idle capacity on the shared VPS that is cheaper than hiring SMM labor, and (c) free-tier LLMs available to the PO make content drafting effectively zero marginal cost. The bottleneck this epic removes is PO attention, not creative direction: the PO retains final editorial authority through a one-click approval queue, but no longer has to discover, read, draft, or schedule posts manually.

## 2. Goals (SMART)

- **G1 (PO time on SMM).** The PO spends **≤2 hours/week** on SMM operations (approval-queue review + oversight + source-list curation combined), measured as a 14-day rolling average starting **30 days after go-live**. Baseline: 0 hours/week (no SMM today), but baseline posting volume is also 0 — this goal replaces "the PO cannot sustain SMM" with "the PO sustains brand presence in ≤2 hours/week".
- **G2 (publication volume).** The system delivers **≥15 approved posts/week aggregated across active channels**, sustained for **2 consecutive weeks**, reached within **45 days of go-live**. Active channels = channels with provisioned credentials at the measurement window. If only Telegram is active, the target reduces pro-rata to the cadence ceiling (see §7); the goal is then recomputed against whatever channels are live.
- **G3 (draft quality).** Over any **14-day rolling window starting 30 days after go-live**, **≥80% of drafts reviewed by the PO are approved without PO edits** (edit = any textual change to the chosen variant before publish). Measured as (approved-without-edit) / (approved-total). Rejected drafts do not count in either numerator or denominator.

All three goals are Specific (each names a single metric), Measurable (numeric target, numeric window), Achievable within the Technical Envelope in §7, Relevant (G1 ties to US-4, G2 ties to US-3, G3 ties to US-2), and Time-bound (explicit deadlines).

## 3. Non-Goals (explicitly NOT in this epic)

- **NG1.** Autonomous publishing. Every post ships only after PO one-click approval from the queue.
- **NG2.** Publishing factually unverifiable content. Drafts that cannot be substantiated from a cited source are paraphrased with inline citation OR held flagged `UNVERIFIED`, never surfaced to the approval queue as "ready".
- **NG3.** Publishing via browser automation, screen scraping, unofficial APIs, or any means not sanctioned by the target platform's official Terms of Service. If a channel offers no compliant write path, that channel is not supported.
- **NG4.** Replying to DMs on any channel.
- **NG5.** Moderating or auto-responding to comments on posts the system publishes.
- **NG6.** Multi-step campaign scheduling (e.g. "Black Friday promo sequence across 5 posts over 10 days").
- **NG7.** Quantitative A/B testing based on post-publication metrics (reach, engagement, CTR). Qualitative A/B — the system generates two textual variants per tailored post and the PO picks one in the approval queue — is in scope; analytics-driven A/B is not.
- **NG8.** AI-generated images, AI-generated video, carousel posts, stories, reels, or any modality other than text-plus-optional-reused-source-image.
- **NG9.** Non-Russian-language content. All generated posts are in Russian.
- **NG10.** Targeting EU residents or otherwise bringing the system into GDPR scope. Audience is the Russian-speaking user base inside the Russian Federation.
- **NG11.** Auto-throttling or auto-adjusting cadence based on platform response signals. The PO sets the cadence; the system obeys it.

## 4. Target Users / Personas

- **P1 — Product Owner (primary user of the system).** Solo operator of the VPN service and of this agent stack. Runs infrastructure, product, growth, and customer contact. Motivation: maintain a consistent brand voice on social channels without becoming a full-time SMM manager. Risk profile: strongly risk-averse — will not ship factually false or ToS-risky content, even at the cost of missing a day. Primary interactions with the system: approval queue, cadence throttle, source-list curation, credential provisioning per channel.
- **P2 — Russian-speaking VPN end-user (audience for the published content).** Located primarily inside the Russian Federation; uses the product's VPN to access Instagram, Threads, X, and other blocked platforms. Speaks Russian as primary language; consumes content in Russian. Interested in: privacy, censorship-circumvention techniques, platform-policy changes (e.g. Telegram/Meta/X policy shifts that affect access), competitor moves, product launches adjacent to privacy/VPN, and practical "how to keep access" advice. Distribution: reachable on Telegram natively and on Threads / X / Instagram via the VPN itself. Does NOT interact with the system directly.

## 5. User Stories & Acceptance Criteria

### US-1: News ingestion & ranking
As the PO, I want the system to continuously monitor news sources relevant to the VPN audience and surface only items that are worth publishing, so that I never have to scan news feeds manually.
**Acceptance:**
- [ ] Given a PO-seeded list of news sources (RSS feeds, public Telegram channels, public accounts) plus rules-based autodiscovery of adjacent sources, when a new item appears in any source, then the system classifies it against a fixed taxonomy (privacy / circumvention / platform policy / competitors / product launches / other) and only items matching the first five categories enter the internal draft queue.
- [ ] Given a newly classified item, when the item is marked time-sensitive, then it reaches the PO's approval queue within the freshness SLA (soft ≤6 hours, hard ≤24 hours from source publication).
- [ ] Given a classified item flagged as politically sensitive (censorship law changes, named regimes, war/protest, activist content), when it is queued, then it lands in a separate "sensitive" sub-queue that requires an explicit PO action distinct from the normal approval action — there is no one-click path that mixes sensitive and non-sensitive items.
- [ ] Given an item cannot be substantiated from at least one citable source, when the system attempts to draft it, then the draft is either rewritten to paraphrase the source with an inline citation, OR held flagged `UNVERIFIED` — it is never surfaced as a normal approval-ready draft.

### US-2: Draft generation with qualitative A/B
As the PO, I want each selected news item turned into 1–3 short Russian-language posts (one tailored to each active channel for which the item is relevant), with two textual variants per post, so that I can pick the better draft in a single click without editing.
**Acceptance:**
- [ ] Given a ranked item and the set of currently-active channels (credentials provisioned + PO-enabled), when the system generates drafts, then it produces between 1 and 3 tailored posts (one per channel the item is relevant to), and for each tailored post it produces exactly two textual variants (A and B) in Russian.
- [ ] Given a tailored post, when generated, then it respects the channel's format constraints: character limits, no content modality other than text + optional reused source image (no AI-generated images, no video, no carousels), no prohibited content types per the channel's ToS.
- [ ] Given the PO opens an item in the approval queue, when they review it, then they can: (i) approve variant A, (ii) approve variant B, (iii) edit either variant and approve the edited version, (iv) reject the tailored post for that channel, or (v) defer the item for up to 24 hours.
- [ ] Given a drafted variant relies on a factual claim, when the claim is included, then it is attributable to the source item either by inline citation or by paraphrase that does not introduce unsourced new claims.

### US-3: Controlled-cadence publishing
As the PO, I want approved posts published to the selected channel on a cadence I can throttle globally and per-channel, so that the volume stays inside brand rhythm and inside platform free-tier limits.
**Acceptance:**
- [ ] Given an approved post (variant chosen), when the next scheduled publish window arrives for that channel (static best-practice time heuristics per channel; no analytics-driven personalization), then the system publishes to the channel within 5 minutes using only the platform's official sanctioned write API.
- [ ] Given the cadence ceiling for a channel is ≤1 post/day, when approval would cause more than 1 post/day on that channel, then surplus approved posts are held in a per-channel scheduled queue and released on subsequent days, never exceeding the ceiling.
- [ ] Given the PO changes the cadence throttle (global kill-switch, per-channel enable/disable, or per-channel cadence), when the change is saved, then subsequent scheduling respects the new throttle within one hour.
- [ ] Given the platform API returns an error or rate-limit response, when a publish attempt fails, then the post is re-queued with bounded retries; there is never a fallback to browser automation, unofficial APIs, or ToS-violating means.
- [ ] Given a channel's required credentials are not provisioned, when the system is asked to publish there, then the channel is marked "pending PO credentials" and no publish attempts are made; other channels are unaffected.

### US-4: One-click approval queue with time-boxed expiry
As the PO, I want every publish gated through a one-click approval queue, with time-boxed expiry on stale items, so that I keep editorial control without becoming the bottleneck on fresh news.
**Acceptance:**
- [ ] Given any drafted item (normal, sensitive, or `UNVERIFIED`), when drafting completes, then the item appears in the PO's approval queue (normal or sensitive sub-queue as appropriate) and waits for PO action.
- [ ] Given the PO takes no action on a time-sensitive item for longer than the freshness SLA (hard ≤24 hours from source publication), when the SLA elapses, then the item is auto-expired and marked as "missed" — the system never auto-publishes stale items.
- [ ] Given a PO approval action, when recorded, then the system publishes the selected variant to the designated channel within the latency budget (soft ≤1 minute, hard ≤5 minutes from approval).
- [ ] Given the PO has spent the G1 target of ≤2 hours/week on the queue, when measured over a 14-day rolling window starting 30 days after go-live, then that time includes all queue reviews, edits, and cadence adjustments combined.

### US-5: Hard failure-safety on factuality and platform ToS
As the PO, I want the system to refuse any action that would risk factually false content or a ToS violation, so that zero-tolerance rules are enforced by construction and not by vigilance.
**Acceptance:**
- [ ] Given any candidate draft, when the system cannot attribute every factual claim to a cited source, then the draft is either paraphrased with inline citation OR held `UNVERIFIED`; no path allows an unsubstantiated claim to reach the approval queue as "ready".
- [ ] Given a channel's published ToS prohibits an action the system would otherwise perform (e.g. automated posting without an app review, scraping-based publishing), when that action is required, then the action is refused at the pipeline level, the channel is disabled for that path, and the refusal is logged with the specific ToS clause referenced.
- [ ] Given the system would need to use a paid-tier API beyond the $30/month paid-LLM cap (see §7) OR a non-official API to operate a channel, when that need is detected, then the channel is disabled and the PO is notified; the system does not silently fall back to a non-compliant means.
- [ ] Given an audit of all published posts over any 30-day window, when reviewed by the PO, then **zero** posts are factually false or ToS-violating. This matches KPI 4 in §6.

## 6. Success Metrics / KPIs

| Metric | Baseline | Target | Measurement method |
|---|---|---|---|
| PO hours/week on SMM operations | 0 hrs/week (no SMM today) | ≤2 hrs/week, as 14-day rolling average, starting 30 days after go-live | PO self-reported time log; cross-checked against queue-activity timestamps |
| Approved-and-published posts/week, aggregated across active channels | 0 posts/week | ≥15 posts/week sustained for 2 consecutive weeks, within 45 days of go-live | Count of rows in the publish log with status `published`, grouped by ISO week |
| Draft approval-without-edit rate | 0% (no drafts today) | ≥80% over any 14-day rolling window starting 30 days after go-live | Ratio = (approvals with zero text diff) / (approvals total); rejections excluded from both numerator and denominator |
| Factually false OR ToS-violating posts published | 0 (never) | 0 (absolute, any window) | Manual audit + any user report + any platform warning/takedown; a single incident is a goal failure |
| Freshness SLA adherence on time-sensitive items | N/A | ≥95% of time-sensitive items reach the queue within 6 hours of source publication, ≥100% within 24 hours, measured monthly | Timestamp diff between source-publication timestamp and queue-arrival timestamp |

## 7. Technical Envelope (constraints Architect must respect)

- **Infra share.** Target VPS is a Hetzner 4c / 8 GB RAM host. Only remnanode + omniroute co-reside there (estimated combined steady-state footprint ≤1 GB RAM, <1 CPU core at peak, per PO). The Remnawave panel, the Bedolaga bot, and the cabinet are on a separate host and are NOT resource-relevant to this PRD. The SMM Autopilot stack may consume **up to 3 CPU cores (75% of total) and up to 6 GB RAM (75% of total) at peak**, but must leave ≥1 CPU core and ≥2 GB RAM free for the VPN data plane at all times. Hard resource ceiling enforced at the OS level is required.
- **Paid-LLM budget.** **Hard cap: US$30 / calendar month** on paid LLM spend, measured as out-of-pocket dollar cost to the PO for any commercial API invocation. Free-tier-at-session-start models (GLM 5.1, Kimi K2.6, Qwen 3.6 Plus) must carry ≥95% of LLM workload, measured by token count. If the Architect determines that any pipeline step requires a paid LLM to meet quality or latency, that step's cost must be amortized so that the monthly rolling spend never exceeds US$30. Exceeding the cap must surface to the PO and the relevant step must degrade (not silently upgrade).
- **Latency budget (end-to-end).**
  - Source publication → draft in queue: **soft ≤6 hours, hard ≤24 hours** for time-sensitive items.
  - PO approval → post live on channel: **soft ≤1 minute, hard ≤5 minutes**.
  - PO cadence-throttle change → scheduling obeys new throttle: **hard ≤1 hour**.
- **Cadence ceilings (hard, enforced).**
  - Telegram: ≤1 post/day per channel, target 3–5 posts/week.
  - Threads: ≤1 post/day per channel, target 2–4 posts/week.
  - X (Twitter): ≤1 post/day per channel, target 2–4 posts/week. Must stay within the X free-tier write quota (500 posts/month at PRD write time) net of retries.
  - Instagram (if activated): ≤1 post/day, target ≤3 posts/week.
- **Content-format constraints.** Text + optionally one reused image sourced from the originating news item (e.g. article OG image or equivalent, used under fair-use / source-attribution principles). No AI-generated images, no video, no carousels, no stories, no reels, no multi-image galleries. Russian language only.
- **Compliance floor.**
  - Russian Federation law applies, including applicable advertising and information statutes.
  - Each target platform's Terms of Service is a hard floor: any write path must be explicitly sanctioned by the platform's official terms.
  - GDPR is NOT in scope — audience is primarily inside the RF; the system must not deliberately target EU residents.
  - Two absolute rules: (a) no factually false content ever published, (b) no ToS-violating means of publication ever used.
- **External dependencies (per-channel go-live is blocked on PO credential provisioning; the PO explicitly accepts this per-channel gating).**
  - **Telegram Bot API.** Credentials ready at PRD write time; channel can go live first.
  - **X API write endpoint.** Free tier (500 writes/month) is assumed sufficient at the stated cadence. PO to provision account + app.
  - **Threads API** (subset of Meta Graph API). PO to provision Meta Developer app and Threads credentials.
  - **Instagram Business API** (Meta Graph API). Nice-to-have; PO to provision if/when prioritized.
  - **Source ingestion.** RSS, public Telegram channels (via Bot API), public web pages of platforms' own policy/news blogs, and any PO-seeded sources. No private-channel scraping. No paid news data providers in MVP (would break the paid-LLM cap's spirit and is not needed).
- **Operational envelope.**
  - The system must be operable by a single PO without a dev-ops rotation. Alerts must be actionable or silenced; the PO's baseline of 2 hrs/week (G1) must absorb any reasonable incident response.
  - Missing a single day on a single channel is acceptable. Silent corruption of content (e.g. posting last week's approved draft tomorrow) is not acceptable.

## 8. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Meta changes Threads or Instagram API terms mid-MVP and revokes the write path | Channel goes dark | Medium | Design each channel as an independently togglable adapter. Missing a channel-day is acceptable per quality-over-quantity principle. If Meta closes the write path entirely, the channel moves to `Out of Scope` and the PRD is re-versioned. |
| X moves free tier off the current 500-writes/month allowance, or closes the free write tier entirely | Channel over paid-LLM-adjacent budget or dark | Medium | Cadence ceiling of ≤1/day keeps monthly writes ≤31 regardless. If the free tier disappears, the system auto-throttles X to 0 and surfaces to PO for an explicit spend decision; X does not silently consume the $30/month LLM cap. |
| PO cannot provision credentials for X/Threads/IG in time → MVP ships Telegram-only | Reduced G2 attainment | Medium | G2 is pro-rated against active channels; Telegram-only MVP is explicitly acceptable. No implementation is blocked — only go-live per channel. |
| PO approves a factually false or ToS-risky draft by mistake under time pressure | Brand, legal, or platform-account damage | Low–Medium | Drafts carry inline citations; `UNVERIFIED` flag is prominent; sensitive items go to a separate sub-queue requiring a distinct action; every approval is logged for post-hoc audit. The final gate is human; the PRD cannot reduce this to zero, only to "known and logged". |
| SMM workload spikes exceed the 3-CPU / 6-GB envelope and degrade the VPN data plane | VPN users impacted | Low–Medium | Hard OS-level resource ceiling at ≤3 CPU / ≤6 GB RAM for SMM Autopilot; VPN data plane guaranteed ≥1 CPU / ≥2 GB RAM headroom. Architect is responsible for enforcing this. |
| Source list is narrow, producing echo-chamber/bland content | Low brand engagement; G3 (approval-without-edit rate) degrades | Medium | Seed list + rules-based autodiscovery of adjacent sources. PO-reviewed quarterly curation is out of MVP scope but flagged as an operational activity; G3 degradation is the leading indicator that the source mix needs refresh. |
| RF information/advertising law changes mid-MVP and renders existing drafts non-compliant | Content becomes illegal; potential takedown / fine | Low–Medium | Compliance classifier in the pipeline; PO decision required for policy-adjacent content. If RF law changes, affected categories are paused pending PO decision; no automated reinterpretation of legal boundaries. |
| PO time on approval queue exceeds the 2-hrs/week G1 target because draft quality is too low (G3 < 80%) | G1 and G3 both miss | Medium | G1, G2, G3 are measured independently; if G3 misses, that is the leading signal to improve generation quality before widening cadence. The PRD explicitly prefers missing G2 over degrading G3. |
| Telegram Bot API rate limits or anti-spam flags trip on a PO-approved burst | Channel temporarily throttled | Low | Hard cadence ceiling ≤1/day already well below Telegram's limits; publish retries use bounded backoff; no workaround paths exist by design (NG3). |

## 9. Open Questions (resolve BEFORE handoff to Architect)

None. All clarifying questions were resolved across two batched rounds with the Product Owner before this PRD was drafted. No `TBD` values remain in the document. Any future reversal by the PO (e.g. activating VK, re-opening Dzen, lifting Non-Goals) requires a version bump per CONTRIBUTING.md rule 3.

## 10. Out of Scope (explicitly deferred to follow-up PRDs)

- **Yandex Dzen publishing.** No public publishing API exists at PRD write time (verified at draft time: Dzen is "semi-automated only" — content generation is possible via third-party tooling but publication is manual through the Dzen UI). Autonomous publishing to Dzen therefore cannot satisfy NG3 (no ToS-violating means). Deferred; revisit if/when Dzen exposes an official publish API.
- **VK community posting.** Account not created by the PO at PRD write time. Deferred to a follow-up decision; not a Non-Goal because the PO may choose to activate it later.
- **Metrics / analytics ingestion from social platforms** (reach, impressions, engagement, CTR per post per channel). Scope of a follow-up PRD (to be filed by the PO). This PRD explicitly depends on the **absence** of platform metrics — G3 uses only the internal approval log, not platform feedback.
- **AI business / marketing advisor** that consumes platform metrics, VPN bot/panel metrics, and produces recommendations to the PO. Scope of a follow-up PRD.
- **Evergreen reposts from our own archive.** Requires "knowing what performed well", which requires metrics. Scope of a later PRD, downstream of the metrics-ingestion PRD.
- **Analytics-driven optimal-times posting** (per-channel per-audience personalized windows). MVP uses static best-practice time windows only. Scope of a later PRD, downstream of the metrics-ingestion PRD.
- **Autonomous source-list curation beyond rules-based heuristics** (e.g. reinforcement-learned source scoring based on approval-rate feedback). Scope of a later PRD that has access to approval-rate history ≥90 days.
- **Post modalities beyond text + reused source image** (AI-generated images, video, carousels, stories, reels). Separate PRD per modality if prioritized.

---

## Handoff Checklist (author ticks all before setting status to `approved`)
- [ ] All sections filled; no TODO / TBD
- [ ] Non-Goals explicitly listed (≥1)
- [ ] Each User Story has testable Acceptance Criteria
- [ ] KPIs are measurable (not "improve" — numeric target and window)
- [ ] Technical Envelope contains concrete numbers
- [ ] Open Questions are closed or explicitly escalated to PO
