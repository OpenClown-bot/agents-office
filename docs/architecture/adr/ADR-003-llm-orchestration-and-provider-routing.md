---
id: ADR-003
title: "LLM Orchestration and Provider Routing"
status: proposed
arch_ref: ARCH-001@0.1.0
author_model: "claude-opus-4.6-thinking"
created: 2026-04-24
updated: 2026-04-24
superseded_by: null
---

# ADR-003: LLM Orchestration and Provider Routing

## Context

ARCH-001@0.1.0 §3.2 (Classifier) and §3.3 (DraftGenerator) require LLM calls for content classification and draft generation. PRD-001@0.1.0 §7 mandates: free-tier LLMs carry ≥95% of token workload; hard cap $30/month on paid LLM spend; degradation (not silent upgrade) if cap is exceeded. The system must route between multiple free-tier providers (GLM-4-Flash, Qwen-Turbo) with fallback logic, track token usage, and enforce the monthly budget. Expected volume: ~200–500 LLM calls/day at ~500 tokens/call avg.

## Options Considered

### Option A: Direct HTTP calls via httpx with custom routing logic
- **Pros:**
  - Zero additional dependencies. `httpx` is already required for API calls (Telegram, X, Meta).
  - Full control over provider routing, retry logic, fallback chains, and token tracking.
  - No framework abstraction to learn or maintain.
  - Minimal memory footprint: no framework runtime.
  - Simple to implement: each provider is a ~50-line async function wrapping an HTTP POST with JSON parsing.
  - Token counting is trivially extracted from API response `usage` fields.
- **Cons:**
  - No automatic prompt templating (but templates are static strings — no need for a framework).
  - No built-in structured output parsing (but we validate against a JSON schema manually — ~10 lines).
  - If adding more providers in the future, each requires a new wrapper function.

### Option B: LangChain (Python)
- **Pros:**
  - Rich ecosystem: prompt templates, output parsers, chains, agent framework.
  - Built-in support for many LLM providers including OpenAI-compatible endpoints.
  - Community momentum and extensive docs.
- **Cons:**
  - Massive dependency tree: `langchain-core` alone pulls ~20 transitive dependencies. Full `langchain` pulls ~50+. Increases Docker image size by ~100–200 MB.
  - Memory overhead: ~50–100 MB additional runtime memory for framework initialization (source: community benchmarks on LangChain memory usage).
  - Abstraction complexity: for our use case (2 LLM calls: classify and generate), LangChain's chains/agents/tools/memory abstractions are entirely unused overhead.
  - GLM-4-Flash and Qwen-Turbo require custom LLM wrappers in LangChain (not in the default provider set); this negates the "built-in support" advantage.
  - Version churn: LangChain has broken backward compatibility across major versions frequently (source: LangChain changelog, v0.1→v0.2 migration guide).
  - Overkill: we have exactly 2 prompt templates and 2 JSON output schemas. A framework designed for complex agent workflows adds no value.

### Option C: LiteLLM (proxy mode or library mode)
- **Pros:**
  - Unified interface to 100+ LLM providers, including GLM and Qwen via OpenAI-compatible endpoint routing.
  - Built-in token tracking and budget management.
  - Library mode (no proxy server) adds moderate dependency footprint.
  - Fallback logic built-in.
- **Cons:**
  - Dependency: `litellm` pulls `openai`, `tiktoken`, `tokenizers`, and others (~30 transitive deps). Docker image +100 MB.
  - Memory: `tiktoken` + `tokenizers` models loaded at runtime add ~50–80 MB RAM.
  - Proxy mode would add a separate HTTP server process — unacceptable on the shared VPS.
  - Library mode still has significant import-time overhead (~2–3s, source: community issue reports).
  - Budget management is per-key, not per-calendar-month — would still need custom logic for the $30/month PRD constraint.
  - For 2 providers with well-documented OpenAI-compatible APIs, LiteLLM's 100-provider abstraction is unused overhead.

## Decision

We will use **direct HTTP calls via httpx with custom routing logic** (Option A).

The system has exactly 2 LLM providers, 2 prompt templates, and 2 JSON output schemas. The entire LLM integration layer is ~200 lines of Python. Adding a framework (LangChain or LiteLLM) would contribute 20–50× more dependency code than application code, consume 50–100 MB of additional RAM on a constrained VPS, and provide zero features we actually use. The custom routing logic (primary → fallback → keyword-only degradation) is ~30 lines and trivially testable.

Token tracking is implemented by extracting `usage.total_tokens` from each API response and accumulating in a SQLite counter. Monthly budget enforcement checks this counter before each call and degrades to keyword-only classification if exceeded.

## Consequences

- **Positive:** Minimal dependencies. Minimal memory. Full control over retry/fallback/budget logic. No framework version churn risk.
- **Negative:** Adding a 3rd provider requires writing a new ~50-line wrapper (acceptable; unlikely in MVP scope). No automatic prompt versioning (mitigated: prompts are version-controlled in git as Python constants).
- **Follow-up:** Implement `LLMClient` class in TKT-003@0.1.0 and TKT-004@0.1.0 with methods `classify(text) -> Category` and `generate_drafts(item, channels) -> list[Draft]`. Track tokens per call in SQLite `llm_usage` table.

## References

- httpx docs: https://www.python-httpx.org/
- GLM-4-Flash API (BigModel/ZhipuAI): https://open.bigmodel.cn/dev/api
- Qwen-Turbo API (Alibaba Cloud): https://help.aliyun.com/zh/model-studio/
- LangChain dependency analysis: https://github.com/langchain-ai/langchain/blob/master/libs/core/pyproject.toml
- LiteLLM GitHub: https://github.com/BerriAI/litellm
