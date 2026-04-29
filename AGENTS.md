# AGENTS.md

This repository is managed by a **multi-LLM pipeline** with strict role separation. If you are an AI agent, identify your role from the prompt you received and load the matching file:

- **Business Planner** → `docs/prompts/business-planner.md`
- **Technical Architect** → `docs/prompts/architect.md`
- **Code Executor** → `docs/prompts/executor.md`
- **Reviewer** → `docs/prompts/reviewer.md`

Follow the role file **exactly**. Do not cross role boundaries. See `CONTRIBUTING.md` for the full process rules and `docs/QA-PLAYBOOK.md` / `docs/OPERATIONAL-PLAYBOOK.md` for QA and change-management procedures.

If you are an **Orchestrator** session (helping the human PO coordinate the other roles), additionally read `docs/session-log/README.md` and follow the auto-handoff rule in `docs/OPERATIONAL-PLAYBOOK.md` §6.

Before making any change:
1. Read `README.md` and `CONTRIBUTING.md`.
2. Check your allowed write-zones in `CONTRIBUTING.md` — touching files outside your zone will be rejected.
3. Run `python scripts/validate_docs.py` before pushing.
