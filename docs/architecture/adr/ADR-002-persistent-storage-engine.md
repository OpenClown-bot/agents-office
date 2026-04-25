---
id: ADR-002
title: "Persistent Storage Engine"
status: accepted
arch_ref: ARCH-001@0.1.0
author_model: "claude-opus-4.6-thinking"
created: 2026-04-24
updated: 2026-04-24
superseded_by: null
---

# ADR-002: Persistent Storage Engine

## Context

ARCH-001@0.1.0 requires persistent storage for source configuration, raw items, classified items, drafts, publish jobs, and operational metrics. The system runs on a shared Hetzner VPS with a hard memory ceiling of 4 GB for the SMM stack. Write throughput is low: at peak, ~50 items/hour ingested, ~20 drafts/hour generated, ~5 publish jobs/hour. The PO operates solo with no DBA or dev-ops rotation, so operational complexity must be near-zero. No inter-service communication is needed (single-process architecture per ARCH-001@0.1.0 §2).

## Options Considered

### Option A: SQLite (via aiosqlite)
- **Pros:**
  - Zero operational overhead: no server process, no port, no auth configuration. A single file on disk.
  - WAL mode supports concurrent reads with a single writer — sufficient for the single-process async architecture.
  - `aiosqlite` provides async Python access without blocking the event loop.
  - Backup = copy a single file. Trivial scripted backup before deploy.
  - Memory footprint: ~5–20 MB for the expected dataset size (tens of thousands of rows over months).
  - Battle-tested in production for workloads far exceeding this one (source: SQLite docs claim "any site that gets fewer than 100K hits/day").
- **Cons:**
  - Single-writer limitation: concurrent writes serialize. Mitigated by async write queue (single-writer pattern in ARCH-001@0.1.0 §12 R2).
  - No built-in replication. Acceptable: single-VPS deployment, PO accepts this per PRD-001@0.1.0 §7.
  - No network access for external tools. Acceptable: PO interacts via bot commands, not SQL.

### Option B: PostgreSQL (via asyncpg)
- **Pros:**
  - Full MVCC concurrency: multiple concurrent writers without contention.
  - Rich query capabilities: JSONB, full-text search, window functions.
  - `asyncpg` is the fastest Python async PostgreSQL driver.
  - Proven at any scale.
- **Cons:**
  - Operational overhead: separate server process consuming ~100–200 MB RAM at idle (source: PostgreSQL docs default `shared_buffers=128MB`). On a 4 GB ceiling, this is 2.5–5% of available memory for no throughput benefit.
  - Requires configuration: `pg_hba.conf`, user management, connection strings.
  - Backup requires `pg_dump` or WAL archiving — more complex than file copy.
  - Adds a Docker service, increasing compose complexity.
  - Overkill: the workload is ~50 writes/hour with <100K rows total. PostgreSQL's concurrency advantages are wasted.

### Option C: Redis (as primary store via redis-om-python)
- **Pros:**
  - In-memory speed: sub-millisecond reads.
  - Pub/sub could serve as a lightweight event bus.
  - Simple key-value data model.
- **Cons:**
  - Not a relational store: complex queries (e.g., "all drafts for channel X with status=ready, ordered by relevance_score") require manual indexing or secondary indices via `redis-om`.
  - Memory-first: entire dataset in RAM. Even with RDB persistence, RAM usage scales linearly with data. For months of items, this wastes hundreds of MB of the 4 GB ceiling.
  - Durability risk: RDB snapshots can lose up to 5 minutes of data. AOF mitigates but adds disk I/O.
  - Adds a Docker service.
  - Not a natural fit for the relational data model in ARCH-001@0.1.0 §5.

## Decision

We will use **SQLite via aiosqlite** with WAL mode enabled.

SQLite is the only option that adds zero operational overhead, zero additional memory, and zero additional Docker services. The workload (~50 writes/hour, single-writer async pattern) is well within SQLite's design envelope. The single-file backup model is ideal for a solo PO with no DBA. PostgreSQL and Redis are engineering overhead for a problem that doesn't exist at this scale.

## Consequences

- **Positive:** Zero-ops storage. Trivial backup. Minimal memory. No additional Docker services.
- **Negative:** Single-writer serialization (mitigated by async write queue). No replication (accepted per PRD-001@0.1.0). No network access for external tools (PO uses bot commands).
- **Follow-up:** Enable WAL mode on DB init (`PRAGMA journal_mode=WAL`). Implement async write queue in TKT-001@0.1.0. Pin `aiosqlite>=0.20.0` in requirements.

## References

- SQLite "Appropriate Uses" page: https://www.sqlite.org/whentouse.html
- SQLite WAL mode: https://www.sqlite.org/wal.html
- aiosqlite library: https://github.com/omnilib/aiosqlite
- PostgreSQL memory consumption: https://www.postgresql.org/docs/current/runtime-config-resource.html
