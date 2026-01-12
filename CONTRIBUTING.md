# Contributing Guidelines

Thank you for contributing to this project. The goal of these guidelines is to
keep collaboration clear, efficient, and reproducible while we work through the
capstone as a team.

These practices are intentionally lightweight and are meant to support learning
and teamwork—not create unnecessary overhead.

---

## General Principles
- Keep work **scoped and focused**
- Prefer **clarity over cleverness**
- Make assumptions explicit
- Prioritize reproducibility
- Communicate early if blocked

---

## Workflow Overview
This project follows an **Agile sprint-based workflow** using GitHub Issues and
Projects.

- All work should be tracked via an issue (ticket)
- Each ticket should have a clear owner
- Tickets define scope and a “Definition of Done”
- Commits should reference the relevant ticket when possible

---

## Writing Tickets
When creating or drafting a ticket, aim to answer three questions clearly:

1. What problem does this ticket solve?
2. What does “done” look like?
3. What is explicitly out of scope?

Early in the project, tickets may be drafted collaboratively or refined during
sprint planning. Over time, team members are encouraged to write their own
tickets prior to planning meetings.

---

## Branching & Commits
- Work on small, focused changes
- Use clear, descriptive commit messages
- Example commit messages:
  - `feat: add initial ingestion script`
  - `docs: update README with workflow details`
  - `fix: handle missing values in sentiment data`

If unsure, prioritize clarity over brevity.

---

## Data Handling
- **Do not commit generated data artifacts**
- Raw and processed datasets are reproducible from scripts
- Only code, documentation, and configuration files should be committed

This keeps the repository lightweight and reproducible for all contributors.

---

## Notebooks
- Notebooks are intended for exploration and analysis
- Avoid using notebooks as the only place where logic exists
- If analysis becomes reusable or important, migrate it into scripts or modules

---

## Communication & Blockers
- Raise blockers during daily scrums
- If blocked outside of meetings, communicate early
- Questions and clarification are encouraged—especially around assumptions

---

## Reviews & Collaboration
- Be respectful and constructive when reviewing work
- Focus feedback on clarity, correctness, and scope
- Remember that this is a learning-focused team project

---

## Final Note
These guidelines may evolve as the project progresses. The goal is to support
effective collaboration while keeping the process simple and transparent.


