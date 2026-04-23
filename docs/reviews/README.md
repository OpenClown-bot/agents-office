# Reviews

Owner: **Reviewer** (Kimi K2.6). MUST be a different model family from the Architect (to avoid in-family bias).

## Two modes

1. **Spec Review** — runs before any code is written. Target: an ArchSpec PR.
   Template: `TEMPLATE-spec.md`. Scaffold: `python scripts/new_artifact.py review-spec "ARCH-001 review"`.

2. **Code Review** — runs on a PR produced by an Executor. Target: a GitHub PR implementing one TKT.
   Template: `TEMPLATE-code.md`. Scaffold: `python scripts/new_artifact.py review-code "PR-42"`.

## What a review MUST include

- Explicit verdict (approve / request changes).
- Contract compliance (did the PR touch only `In Scope`?).
- At least 3 red-team probes (what if X fails, what about concurrency, what's the blast radius?).
