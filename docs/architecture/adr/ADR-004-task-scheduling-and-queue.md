---
id: ADR-004
title: "Task Scheduling and Queue"
status: proposed
arch_ref: ARCH-001@0.1.0
author_model: "claude-opus-4.6-thinking"
created: 2026-04-24
updated: 2026-04-24
superseded_by: null
---

# ADR-004: Task Scheduling and Queue

## Context

ARCH-001@0.1.0 requires periodic task execution for: source ingestion (every 15 min), classification (triggered after ingestion), draft generation (triggered after classification), publish job execution (at scheduled times), freshness SLA expiry checks (periodic), and source autodiscovery (periodic). The architecture is a single-process async Python application (per ADR-001@0.1.0 and ADR-002@0.1.0). No inter-process communication is needed. PRD-001@0.1.0 §7 requires the system to be operable by a single PO without a dev-ops rotation, so operational complexity must be minimal.

## Options Considered

### Option A: APScheduler 3.x (in-process async scheduler)
- **Pros:**
  - Pure Python, in-process. No external broker, no additional Docker service.
  - Supports cron-like schedules, interval-based triggers, and one-shot deferred jobs.
  - AsyncIO executor available for non-blocking job execution.
  - Lightweight: ~2 MB installed, ~5 MB RAM at runtime.
  - Mature: 10+ years of production use, stable API (v3 series).
  - Job persistence to SQLite via `SQLAlchemyJobStore` — survives restarts.
  - Single dependency: `apscheduler` (+ `sqlalchemy` for job store, which is lightweight).
- **Cons:**
  - In-process: if the process crashes, all scheduled jobs stop. Mitigated by Docker `restart: unless-stopped`.
  - No distributed scheduling (irrelevant: single-process architecture).
  - v4.x is a major rewrite with breaking changes; pinning to v3.x avoids this.

### Option B: Celery + Redis/RabbitMQ
- **Pros:**
  - Industry-standard distributed task queue. Supports retries, chaining, rate limiting.
  - Battle-tested at scale.
  - Rich monitoring (Flower dashboard).
- **Cons:**
  - Requires an external broker (Redis or RabbitMQ): additional Docker service, ~50–100 MB RAM for Redis, ~100–200 MB for RabbitMQ.
  - Celery worker processes: each worker ~100–150 MB RAM. Even one worker + broker = ~200–300 MB additional memory on the 4 GB ceiling.
  - Operational complexity: broker configuration, worker management, Flower dashboard.
  - Overkill: we have ~6 periodic tasks running at intervals of 5–15 minutes. Celery's distributed task routing is entirely unused.
  - Celery's async support is experimental and poorly documented (source: Celery docs "Async support is still in preview").

### Option C: asyncio.create_task + custom cron loop
- **Pros:**
  - Zero dependencies: pure stdlib.
  - Full control over scheduling logic.
  - No abstraction overhead.
- **Cons:**
  - No job persistence: if the process restarts, scheduled one-shot jobs (e.g., a deferred publish at a specific time) are lost. Must re-derive all pending jobs from DB state on startup — significant implementation burden.
  - No built-in cron-like expression parsing; must implement manually.
  - No retry/misfire handling; must implement manually.
  - Error handling in long-running `create_task` coroutines requires careful exception propagation.
  - Reimplements what APScheduler provides out of the box.

## Decision

We will use **APScheduler 3.x** (pinned to `APScheduler>=3.10,<4.0`) with `AsyncIOScheduler` and `SQLAlchemyJobStore` backed by the same SQLite database.

APScheduler provides exactly the scheduling primitives we need (interval triggers for ingestion/classification/expiry, cron triggers for publish windows, deferred one-shot jobs for scheduled publishes) with zero external infrastructure. The SQLAlchemy job store persists pending jobs to SQLite, so scheduled publishes survive process restarts. Celery is a 200 MB RAM overhead for a problem that APScheduler solves in 5 MB.

## Consequences

- **Positive:** Zero additional Docker services. ~5 MB RAM overhead. Job persistence via SQLite. Cron expressions for publish windows.
- **Negative:** In-process only (acceptable: single-process architecture). Must pin to v3.x to avoid v4 breaking changes. `SQLAlchemyJobStore` requires the `sqlalchemy` package, but this is not permission to use SQLAlchemy ORM for application data access; application tables remain raw SQL through aiosqlite per ADR-002@0.1.0 and ARCH-001@0.1.1 §7.
- **Follow-up:** Configure scheduler in TKT-007@0.1.1. Jobs: `ingest_sources` (interval 15min), `run_classifier` (interval 5min), `run_draft_generator` (interval 5min), `check_expiry` (interval 10min), `execute_publish_jobs` (interval 1min), `run_source_discovery` (interval 60min).

## Compatibility Note for ARCH-001@0.1.1

ADR-004@0.1.0 keeps the APScheduler + `SQLAlchemyJobStore` decision. TKT-001@0.1.1 allows `sqlalchemy` only for APScheduler job-store persistence and continues to forbid SQLAlchemy ORM for SMM Autopilot application tables.

## References

- APScheduler docs: https://apscheduler.readthedocs.io/en/3.x/
- APScheduler AsyncIOScheduler: https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/asyncio.html
- Celery async limitations: https://docs.celeryq.dev/en/stable/userguide/concurrency/eventlet.html
- Redis memory consumption: https://redis.io/docs/management/optimization/memory-optimization/
