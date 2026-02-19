---
name: spec-driven-python-init
description: Initialize a spec-driven Python development project with PRD.md, PLAN.md, and pytest test infrastructure. Use when setting up a new Python project, creating PRD/PLAN structure for Python code, initializing spec-driven workflow for Python, or when user mentions "spec-driven Python", "Python PRD", "pytest-based setup", or wants to scaffold a Python project with requirements tracking and test-first development.
---

# Spec-Driven Project Initialization

Initialize projects with a requirements-first, test-driven structure.

## Quick Start

```bash
# Run the init script
python /path/to/skill/scripts/init_project.py --name "project-name" --description "Brief description"
```

Or manually create files using templates in `templates/`.

## Before Creating Files, Ask:

1. Project name? (or confirm from directory name)
2. Brief description?
3. Python version? (default: 3.11)
4. Additional dependencies?
5. Any initial requirements for PRD, or use placeholders?

## Files Created

| File | Purpose |
|------|---------|
| `PRD.md` | Immutable requirements contract (FR-1, NFR-1, INV-1 format) |
| `PLAN.md` | Mutable implementation checklist linking to PRD IDs |
| `pyproject.toml` | uv + pytest + bandit configuration |
| `docs/AGENT_RULES.md` | Rules for AI coding agents |
| `tests/test_example.py` | Template showing `@pytest.mark.requirement` pattern |

## Directory Structure

```
project/
├── src/__init__.py
├── tests/__init__.py
├── tests/test_example.py
├── docs/AGENT_RULES.md
├── PRD.md
├── PLAN.md
├── README.md
├── pyproject.toml
└── .gitignore
```

## After Initialization

Commit with: `[PROJECT] Initialize spec-driven development structure`

Then use the `spec-driven-python-workflow` skill for ongoing development.
