---
id: ADR-001
title: "Application Language and Runtime"
status: proposed
arch_ref: ARCH-001@0.1.0
author_model: "claude-opus-4.6-thinking"
created: 2026-04-24
updated: 2026-04-24
superseded_by: null
---

# ADR-001: Application Language and Runtime

## Context

ARCH-001@0.1.0 requires a language and runtime for the SMM Autopilot MVP. The system runs on a shared Hetzner VPS (4c/8GB) with a hard resource ceiling of 3 CPU / 6 GB RAM. It must support: async HTTP calls to multiple APIs (Telegram, X, Meta, LLM providers), RSS parsing, HTML scraping, SQLite access, and a Telegram bot with inline keyboards. The PO operates solo with no dev-ops rotation, so operational complexity must be minimal. The executor models (GLM-5.1, Qwen-3.6-Plus) must be proficient in the chosen language.

## Options Considered

### Option A: Python 3.12 + asyncio
- **Pros:**
  - Mature async ecosystem: `httpx`, `aiohttp`, `aiosqlite`, `python-telegram-bot` (async v21+).
  - Excellent library coverage for RSS (`feedparser`), HTML parsing (`beautifulsoup4`+`lxml`), and LLM API clients.
  - GLM-5.1, Qwen-3.6-Plus, and Codex GPT-5.3 all have strong Python proficiency (most-trained language in all three models' corpora).
  - Low memory footprint for async workloads (~50–100 MB base).
  - Single-file deployment feasible; Docker image ~150 MB (slim).
  - PO familiarity: Python is the most common scripting language for VPS operators.
- **Cons:**
  - GIL limits true CPU parallelism (mitigated: workload is I/O-bound, not CPU-bound).
  - Type safety is opt-in (`mypy`); runtime type errors possible.
  - Startup time ~1s (acceptable for a long-running service).

### Option B: TypeScript (Node.js 22 + Bun/Deno)
- **Pros:**
  - Native async/await with event loop. Good HTTP client ecosystem (`undici`, `node-fetch`).
  - Strong typing with TypeScript.
  - `telegraf` or `grammy` for Telegram bots.
  - Fast V8 execution.
- **Cons:**
  - RSS parsing ecosystem weaker (no `feedparser` equivalent; `rss-parser` is less battle-tested).
  - LLM API client libraries are JS-first but less mature for Chinese LLM providers (GLM, Qwen) — would require raw HTTP calls anyway.
  - Node.js memory footprint higher than Python for equivalent async workloads (~80–150 MB base + V8 heap overhead).
  - Executor model proficiency: GLM-5.1 and Qwen-3.6-Plus are less extensively trained on TypeScript than Python (source: model cards and community benchmarks on HumanEval variants).
  - Bun/Deno add operational complexity and immaturity risk.

### Option C: Go 1.22
- **Pros:**
  - Goroutines provide true concurrency without GIL concerns. Tiny binary, fast startup, low memory.
  - Strong standard library for HTTP.
  - Excellent for long-running services.
- **Cons:**
  - No mature Telegram bot library with inline-keyboard support comparable to `python-telegram-bot` (go-telegram-bot-api exists but is less feature-rich).
  - No `feedparser` equivalent; RSS parsing requires manual implementation or less-maintained libraries.
  - No equivalent of `beautifulsoup4` for HTML scraping; `goquery` exists but HTML parsing ecosystem is thinner.
  - Executor model proficiency: GLM-5.1 and Qwen-3.6-Plus have significantly lower Go proficiency than Python (source: HumanEval benchmarks show ~15–20% lower pass rates for Go vs Python across these models).
  - Higher development time for an MVP that is fundamentally I/O-bound glue code.

## Decision

We will use **Python 3.12 + asyncio**.

Python is the clear winner for this I/O-bound, API-glue, Telegram-bot-centric workload. The ecosystem coverage (feedparser, beautifulsoup4, python-telegram-bot, aiosqlite, httpx) is unmatched. All three executor models are most proficient in Python, reducing ticket execution time and error rates. The GIL is irrelevant for an I/O-bound workload running on ≤2 CPU cores.

## Consequences

- **Positive:** Fastest time-to-MVP. Best library coverage. Highest executor model accuracy. Lowest operational burden.
- **Negative:** No compile-time type safety (mitigated by `mypy --strict` in CI). GIL prevents CPU parallelism (irrelevant for this workload).
- **Follow-up:** Pin Python 3.12.x in Dockerfile. Pin all dependencies in `requirements.txt` with exact versions. Configure `mypy --strict` and `ruff` in CI.

## References

- python-telegram-bot v21 async docs: https://docs.python-telegram-bot.org/
- httpx docs: https://www.python-httpx.org/
- aiosqlite docs: https://aiosqlite.omnilib.dev/
- feedparser docs: https://feedparser.readthedocs.io/
- HumanEval benchmark methodology: https://arxiv.org/abs/2107.03374
