# vpn-agents

Monorepo for the VPN-service SMM & analytics agent platform, built using a multi-LLM **Orchestrator → Worker** pipeline.

This repo is also the **source of truth** for the development process itself. Documents (PRDs, architecture specs, tickets, reviews) live in `docs/` and are versioned in git alongside the code they describe (docs-as-code).

## Pipeline at a glance

```
[You / Product Owner]
        │
        ▼
┌─────────────────────┐
│ 1. Business Planner │  → docs/prd/PRD-XXX.md
│    (Opus 4.7, web)  │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ 2. Tech Architect   │  → docs/architecture/ARCH-XXX.md
│    (Opus 4.6 Think.)│     docs/architecture/adr/ADR-XXX.md
└─────────────────────┘     docs/tickets/TKT-XXX.md
        │
        ▼
┌─────────────────────┐
│ 3. Reviewer (Spec)  │  → docs/reviews/RV-SPEC-*.md
│    (Kimi K2.6)      │
└─────────────────────┘
        │ approved
        ▼
┌─────────────────────┐
│ 4. Code Executor    │  → src/**, tests/**  (PR)
│    (GLM 5.1 primary)│
│    Qwen / Codex alt │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ 3'. Reviewer (Code) │  → docs/reviews/RV-CODE-*.md
│    (Kimi K2.6)      │
└─────────────────────┘
        │
        ▼
   [You: merge]
```

## Directory layout

```
vpn-agents/
├── docs/
│   ├── prd/               # Product Requirements Documents (Business Planner)
│   ├── architecture/      # System architecture specs (Architect)
│   │   └── adr/           # Architecture Decision Records
│   ├── tickets/           # Task Tickets for Executors
│   ├── reviews/           # Spec reviews and code reviews
│   └── questions/         # Questions raised by Executor back to Architect
├── src/                   # Production code (written by Executors)
├── tests/                 # Tests
├── infra/                 # docker-compose, deploy scripts, configs
├── scripts/               # Dev tooling (docs validator, artifact scaffolder)
└── .github/workflows/     # CI (docs validation, lint, tests)
```

## Artifact IDs and lifecycle

Every artifact has a stable, monotonically-increasing ID:

- `PRD-001`, `PRD-002`, …
- `ARCH-001`, `ARCH-002`, …
- `ADR-001`, `ADR-002`, …
- `TKT-001`, `TKT-002`, …
- `RV-SPEC-ARCH-001`, `RV-CODE-PR-42`, …

Status lifecycle: `draft → in_review → approved → superseded`.  
Never delete an artifact. When superseded, keep the file and set `superseded_by:`.

## Quick start

```bash
# 1. Clone to your workstation and VPS
git clone git@github.com:<you>/vpn-agents.git
cd vpn-agents

# 2. Create a new PRD
python scripts/new_artifact.py prd "SMM Autopilot"
# → creates docs/prd/PRD-001-smm-autopilot.md from template

# 3. Validate all docs locally
python scripts/validate_docs.py
```

## Contributing / process rules

See [CONTRIBUTING.md](CONTRIBUTING.md) for hard rules about who writes what and the handoff contracts.
