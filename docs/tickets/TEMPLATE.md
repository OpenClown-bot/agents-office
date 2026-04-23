---
id: TKT-XXX
title: ""
status: draft              # draft | ready | in_progress | in_review | done | blocked
arch_ref: ARCH-XXX@X.Y.Z
component: ""
depends_on: []
blocks: []
estimate: S                # S | M | L
assigned_executor: "glm-5.1"
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# TKT-XXX: <Title>

## 1. Goal (one sentence, no "and")
<What this ticket achieves, in one atomic sentence.>

## 2. In Scope
- <file or module to create>
- <config to add>
- <migration>
- <tests>

## 3. NOT In Scope (Executor must NOT touch these — returns for review)
- <explicitly excluded item>
- <belongs to another ticket — reference TKT-YYY>

## 4. Inputs (Executor MUST read before writing code)
- <ARCH-XXX @version §section>
- <ADR-XXX @version>
- <existing file: src/core/...>

## 5. Outputs (deliverables)
- [ ] `src/path/to/new_file.py` with class `ClassName`
- [ ] `config/...yaml`
- [ ] `migrations/NNN_....sql`
- [ ] `tests/path/test_...py` (coverage ≥80% for new module)
- [ ] Updated README section

## 6. Acceptance Criteria (machine-checkable)
- [ ] `pytest tests/path/test_...py` passes
- [ ] Manual smoke: `<command>` produces `<expected result>`
- [ ] `ruff check` clean
- [ ] `mypy <path>` clean
- [ ] Logs in required format

## 7. Constraints (hard rules for Executor)
- Do NOT add new dependencies except: <explicit allowlist>
- Do NOT modify schemas of other tables
- Do NOT touch `src/core/**` — return a question if you think you need to
- Use existing `<helper>` from `src/core/...`
- All SQL parameterised (no f-string SQL)

## 8. Definition of Done
- [ ] All Acceptance Criteria pass
- [ ] PR opened with link to this TKT in description
- [ ] No TODO / FIXME left in code
- [ ] Executor filled §10 Execution Log

## 9. Questions (empty at creation; Executor appends here if blocked — do NOT start code)
<!-- Q1 (YYYY-MM-DD, model-id): question text -->

## 10. Execution Log (Executor fills as work proceeds)
<!-- YYYY-MM-DD HH:MM model-id: started -->
<!-- YYYY-MM-DD HH:MM model-id: opened PR #NN -->

---

## Handoff Checklist (Architect ticks before setting status to `ready`)
- [ ] Goal is one sentence, no conjunctions
- [ ] NOT In Scope has ≥1 explicit item
- [ ] Acceptance Criteria are machine-checkable (no "looks good")
- [ ] Constraints explicitly list forbidden actions
- [ ] All ArchSpec/ADR references are version-pinned
- [ ] `depends_on` accurately reflects prerequisites
