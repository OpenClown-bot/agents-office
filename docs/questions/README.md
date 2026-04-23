# Questions

When an **Executor** encounters ambiguity or a contradiction between the Ticket and the ArchSpec, they MUST stop and create a question here rather than guess.

- Filename: `Q-TKT-NNN-NN.md` (NN = question number within that ticket).
- Scaffold: `python scripts/new_artifact.py question "TKT-001 rss dedup strategy"`.
- Executor fills `Context`, `Question`, and `What I assumed`.
- Architect fills `Architect's answer` and sets `status: answered`.
- Only after the question is answered may the Executor resume the ticket.
