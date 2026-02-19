# Rules for AI Coding Agents

## Mandatory Workflow

1. Never write implementation until failing tests exist
2. If behavior changes, update PRD.md first
3. Each PLAN item must reference a PRD requirement ID and tests
4. Commit messages must start with `[SPEC-ID]`

## Separation of Concerns

- **PRD.md** = immutable contract (what to build)
- **PLAN.md** = mutable tracker (how we're building it)
- Do not edit PRD.md during implementation unless behavior genuinely changes

## Before Every Commit

- All tests pass (`uv run pytest`)
- Security checks pass (`uv run bandit -r src/`)
- PLAN items reference valid PRD IDs
- Commit message includes SPEC-ID

## Requirement IDs

| Prefix | Type |
|--------|------|
| FR-N | Functional requirements |
| NFR-N | Non-functional requirements |
| INV-N | Invariants |
| R-N | Risks |
| TD-N | Technical debt |

## Test Requirements

Every test must:
- Be marked with `@pytest.mark.requirement("FR-X")`
- Have docstring explaining what it tests
- Follow arrange/act/assert structure
- Be deterministic (no flaky tests)
- Be isolated (no shared state)

## Commit Message Format

```
[FR-3] Short description

Detailed explanation
- Key changes
- Tests added/modified

Closes: FR-3
Related: FR-1
```
