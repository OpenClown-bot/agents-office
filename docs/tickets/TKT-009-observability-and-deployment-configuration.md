---
id: TKT-009
title: "Observability and deployment configuration"
version: 0.1.1
status: draft
arch_ref: ARCH-001@0.1.1
component: "all"
depends_on: [TKT-001]
blocks: []
estimate: S
assigned_executor: "glm-5.1"
created: 2026-04-24
updated: 2026-04-24
---

# TKT-009: Observability and deployment configuration

## 1. Goal (one sentence, no "and")
Configure structured JSON logging via structlog across all components, create the deploy script with pre-deploy DB backup, and set up the systemd slice for OS-level resource ceilings.

## 2. In Scope
- `src/smm_autopilot/logging.py` (structlog JSON configuration: timestamp, level, component, event, trace_id fields)
- `infra/deploy.sh` (deploy script: backup DB, git pull, docker compose down/up, health check)
- `infra/smm-autopilot.slice` (systemd slice: `CPUQuota=300%`, `MemoryMax=6G`)
- `infra/docker-compose.override.yml` (logging driver config: `max-size: 50m`, `max-file: 5`)
- `tests/test_logging.py` (unit test: verify structlog JSON output format)

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- Prometheus/Grafana setup — explicitly excluded per ARCH-001@0.1.1 §8 (no dev-ops rotation)
- Application business logic — belongs to TKT-002@0.1.1 through TKT-008@0.1.1 and the split approval-bot tickets
- `/stats` bot command implementation — belongs to TKT&#45;005c@0.1.0
- CI/CD pipeline — out of scope for MVP

## 4. Inputs (Executor MUST read before writing code)
- ARCH-001@0.1.1 §8 Observability (log format, metrics, alerting, tracing)
- ARCH-001@0.1.1 §9 Security (secrets management, no secrets in git)
- ARCH-001@0.1.1 §10 Deployment (rollback procedure, backup, systemd slice, Docker log rotation)
- TKT-001@0.1.1 outputs: `docker-compose.yml`, `db.py`

## 5. Outputs (deliverables)
- [ ] `src/smm_autopilot/logging.py`
- [ ] `infra/deploy.sh`
- [ ] `infra/smm-autopilot.slice`
- [ ] `infra/docker-compose.override.yml`
- [ ] `tests/test_logging.py`

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/test_logging.py -v` passes
- [ ] Given a log event, when emitted, then stdout contains a single JSON line with fields: `timestamp` (ISO 8601), `level`, `component`, `event`, `trace_id`
- [ ] `infra/deploy.sh` is executable (`chmod +x`) and contains: DB backup step, `docker compose down`, `docker compose up -d --build`, health check (`docker compose ps`)
- [ ] `infra/smm-autopilot.slice` contains `CPUQuota=300%` and `MemoryMax=6442450944` (6 GB in bytes)
- [ ] `infra/docker-compose.override.yml` configures logging driver with `max-size: 50m` and `max-file: "5"`
- [ ] `ruff check src/smm_autopilot/logging.py tests/test_logging.py` clean
- [ ] `mypy src/smm_autopilot/logging.py --strict` clean

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies beyond those in TKT-001@0.1.1's `requirements.txt` (structlog is already included)
- Do NOT create `.env` files — only reference `.env.example` from TKT-001@0.1.1
- Do NOT commit any secrets or real tokens
- `deploy.sh` MUST NOT use `docker compose push` or interact with a container registry — build is local
- All SQL parameterised (no f-string SQL)

## 8. Definition of Done
- [ ] All Acceptance Criteria pass
- [ ] PR opened with link to this TKT in description
- [ ] No TODO / FIXME left in code
- [ ] Executor filled §10 Execution Log

## 9. Questions (empty at creation; Executor appends here if blocked — do NOT start code)

## 10. Execution Log (Executor fills as work proceeds)

---

## Handoff Checklist (Architect ticks before setting status to `ready`)
- [x] Goal is one sentence, no conjunctions
- [x] NOT In Scope has ≥1 explicit item
- [x] Acceptance Criteria are machine-checkable (no "looks good")
- [x] Constraints explicitly list forbidden actions
- [x] All ArchSpec/ADR references are version-pinned
- [x] `depends_on` accurately reflects prerequisites
