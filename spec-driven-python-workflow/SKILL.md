---
name: spec-driven-python-workflow
description: Guide spec-driven Python development workflow with pytest-based test-first implementation, requirement tracking, and proper commit practices. Use when implementing Python features, adding requirements, updating PLAN.md, writing pytest tests linked to PRD IDs, or when user mentions "implement FR-", "add requirement", "update plan", "write test for", or needs help following spec-driven practices in Python projects.
---

# Spec-Driven Python Development Workflow

## Core Loop

```
PRD.md (add req) → PLAN.md (add item) → Write test → Implement → Commit → Mark done
```

## Adding a New Requirement

1. **Update PRD.md** with new requirement ID:
   ```markdown
   - **FR-2**: Users can export data as CSV
   ```

2. **Update PLAN.md** with implementation item:
   ```markdown
   - [ ] **FR-2**: Export data as CSV
     - Tests: `tests/test_export.py::test_csv_export`
     - Done when: CSV downloads with correct headers
   ```

3. **Write failing test first**:
   ```python
   @pytest.mark.requirement("FR-2")
   def test_csv_export():
       """Given data, when exported, then valid CSV with headers."""
       # Arrange / Act / Assert
   ```

4. **Implement** minimal code to pass

5. **Commit**:
   ```
   [FR-2] Add CSV export functionality

   - Implemented export_csv() function
   - Tests: test_export.py::test_csv_export

   Closes: FR-2
   ```

6. **Mark done** in PLAN.md: `- [x] **FR-2**: ...`

## Requirement ID Reference

| Prefix | Use for | Example |
|--------|---------|---------|
| FR-N | User-facing features | FR-1: Login with email |
| NFR-N | Performance, security | NFR-1: Response < 200ms |
| INV-N | Must always be true | INV-1: Passwords hashed |
| R-N | Known risks | R-1: API rate limits |
| TD-N | Intentional shortcuts | TD-1: Hardcoded config |

## Test Pattern

```python
@pytest.mark.requirement("FR-N")
def test_descriptive_name():
    """
    Given: [precondition]
    When: [action]
    Then: [expected result]
    """
    # Arrange
    # Act
    # Assert
```

## Commit Format

```
[FR-N] Short imperative description

- What changed
- Tests added/modified

Closes: FR-N (if complete)
Related: FR-X (if affected)
```

## Rules

| Do | Don't |
|----|-------|
| Write test before code | Implement without tests |
| One requirement per commit | Bundle unrelated changes |
| Update PRD for behavior changes | Edit PRD during implementation |
| Reference PRD IDs in tests | Write orphan tests |
| Mark PLAN items when tests pass | Mark done with failing tests |

## Verification Commands

```bash
uv run pytest                    # All tests pass
uv run pytest -m "requirement"   # Only requirement-linked tests
uv run bandit -r src/           # Security check
```
