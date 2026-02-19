# {{PROJECT_NAME}}

{{DESCRIPTION}}

## Development Workflow

This project uses spec-driven development:

1. **PRD.md** - Product requirements (what to build) - immutable contract
2. **PLAN.md** - Implementation plan (how we're building) - mutable tracker
3. **Tests** - Proof that requirements are met
4. **Git commits** - Track requirement completion

### Workflow Loop

1. Update PRD.md (add requirement with ID like FR-1)
2. Update PLAN.md (add checklist item referencing requirement)
3. Write failing tests (mark with `@pytest.mark.requirement("FR-1")`)
4. Implement minimal code to pass tests
5. Commit with `[FR-1] Description` format
6. Mark PLAN item complete `[✓]`

### Setup

```bash
uv pip install -e ".[dev]"
uv run pytest
uv run bandit -r src/
```

## Never

- ❌ Write code before tests
- ❌ Mark PLAN items done with failing tests
- ❌ Edit PRD during implementation
- ❌ Implement features not in PRD
