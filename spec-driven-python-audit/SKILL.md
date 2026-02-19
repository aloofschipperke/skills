---
name: spec-driven-python-audit
description: Audit spec-driven Python projects for integrity issues. Use when user asks to "audit project", "check PRD sync", "verify PLAN", "find orphan tests", or "check test coverage". Detects PRD requirements not in PLAN, PLAN items without PRD backing, tests without requirement markers, always-pass or always-fail tests, and items marked complete without tests.
---

# Audit Project

Scan a spec-driven Python project to verify PRD, PLAN, and code are in sync.

## Checks Performed

1. **PRD → PLAN sync**: Requirements in PRD.md should be tracked in PLAN.md
2. **PLAN → PRD sync**: PLAN items should reference valid PRD requirements
3. **Test coverage**: Requirements should have tests with `@pytest.mark.requirement`
4. **Test integrity**: No always-pass (`assert True`) or always-fail patterns
5. **Completion honesty**: Items marked `[x]` should have corresponding tests

## Usage

Run the audit script on any spec-driven Python project. The script is located in this skill's directory:

```bash
python3 "${SKILL_DIR}/scripts/audit_project.py" /path/to/project
```

Where `${SKILL_DIR}` is the base directory provided when the skill is invoked (shown as "Base directory for this skill: ...").

**Example invocation:**
```bash
python3 /home/kjj/.claude/skills/spec-driven-python-audit/scripts/audit_project.py .
```

Options:
- `-o, --output FILE`: Write report to specific file (default: `AUDIT_REPORT.md`)
- `--stdout`: Print report to stdout instead of file

## Expected Project Structure

The project must have:
- `PRD.md` with requirements in one of these formats:
  - List: `- **FR-1**: Description text`
  - Table: `| FR-1 | Description | ... |`
  - Heading: `### FR-1: Description text`
- `PLAN.md` with items formatted as: `- [x] **FR-1**: Description text` or section headers like `### Phase N (FR-1, FR-2)`
- Tests using `@pytest.mark.requirement("FR-1")` decorator

## Requirement ID Prefixes

| Prefix | Meaning |
|--------|---------|
| FR-N | Functional requirement |
| NFR-N | Non-functional requirement |
| INV-N | Invariant (must always be true) |
| R-N | Risk |
| TD-N | Technical debt |

## Report Sections

The generated `AUDIT_REPORT.md` includes:

1. **Summary**: Counts of requirements, plan items, tests, and issues
2. **PRD Not in PLAN**: Requirements missing from PLAN tracking
3. **PLAN Without PRD**: Plan items referencing non-existent requirements
4. **No Test Coverage**: Requirements without `@pytest.mark.requirement` tests
5. **Suspect Tests**: Tests with integrity issues (always-pass, no assertions)
6. **Completion Issues**: Items marked complete but missing tests
7. **Coverage Matrix**: Table showing all requirements with status

## Workflow

1. Run audit: `python3 "${SKILL_DIR}/scripts/audit_project.py" .` (using the skill's base directory)
2. Review `AUDIT_REPORT.md`
3. Address issues:
   - Add missing PLAN items for untracked PRD requirements
   - Remove or fix PLAN items without PRD backing
   - Add `@pytest.mark.requirement` markers to tests
   - Fix or remove always-pass/always-fail tests
   - Uncheck `[x]` items that lack test coverage
4. Re-run audit to verify fixes
