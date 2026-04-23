---
id: ARCH-XXX
title: ""
version: 0.1.0
status: draft
prd_ref: PRD-XXX@X.Y.Z        # version-pinned
owner: "@your-github-handle"
author_model: "claude-opus-4.6-thinking"
created: YYYY-MM-DD
updated: YYYY-MM-DD
adrs: []
tickets: []
---

# ARCH-XXX: <Title>

## 1. Context
Implements: <PRD-XXX @version, sections>.
Does NOT implement: <PRD-XXX §Non-Goals>.

## 2. Architecture Overview
<Prose + diagram (Mermaid preferred).>

```mermaid
graph LR
  A[Component A] --> B[Component B]
```

## 3. Components
### 3.1 <Component name>
- Responsibility: ...
- Inputs: ...
- Outputs: ...
- LLM usage: none | <model, purpose>
- State: stateless | <where stored>

### 3.2 ...

## 4. Data Flow
<Step-by-step flow describing which data is produced where.>

## 5. Data Model / Schemas
```yaml
EntityName:
  id: uuid
  field: type
```

## 6. External Interfaces
| System | Protocol | Auth | Rate limit | Notes |
|---|---|---|---|---|

## 7. Tech Stack Decisions (linked ADRs)
- Language: <lang> (ADR-XXX)
- Queue: <choice> (ADR-XXX)
- Storage: <choice> (ADR-XXX)
- Agent framework: <choice> (ADR-XXX)

## 8. Observability
- Logs: ...
- Metrics: ...
- Tracing: ...

## 9. Security
- Secrets management: ...
- Network boundaries: ...
- LLM prompt-injection mitigations: ...

## 10. Deployment
- Runtime: ...
- Resource budget: <CPU/RAM — must fit PRD Technical Envelope>
- Rollback procedure: ...

## 11. Work Breakdown (tickets for Executor)
| ID | Title | Depends on | Assigned executor |
|---|---|---|---|
| TKT-XXX | ... | — | glm-5.1 |

## 12. Risks & Open Questions
- R1: ...
- Q_TO_BUSINESS: ... ← escalation upstream

---

## Handoff Checklist
- [ ] Each component has clear Input/Output
- [ ] All referenced ADRs exist and are `approved` or `draft` (not missing)
- [ ] Resource budget fits PRD Technical Envelope
- [ ] Work Breakdown lists independent tickets or explicit dependency graph
- [ ] Observability and Security sections non-empty
- [ ] All PRD references pin to a specific version (`@X.Y.Z`)
