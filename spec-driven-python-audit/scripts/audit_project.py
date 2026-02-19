#!/usr/bin/env python3
"""
Audit a spec-driven Python project for integrity issues.

Checks:
1. PRD ↔ PLAN sync: Requirements in PRD should be tracked in PLAN
2. PLAN ↔ PRD sync: PLAN items should reference valid PRD requirements
3. Test coverage: Requirements should have corresponding tests
4. Test integrity: No always-pass or always-fail tests
5. Completion honesty: Items marked [x] should have passing tests
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Requirement:
    """A requirement from PRD.md."""
    id: str
    text: str
    line_number: int


@dataclass
class PlanItem:
    """A tracked item from PLAN.md."""
    id: str
    text: str
    completed: bool
    line_number: int
    test_refs: list[str] = field(default_factory=list)


@dataclass
class TestInfo:
    """Information about a test function."""
    name: str
    file: Path
    line_number: int
    requirement_ids: list[str]
    issues: list[str] = field(default_factory=list)


@dataclass
class AuditResult:
    """Results of the audit."""
    requirements: dict[str, Requirement] = field(default_factory=dict)
    plan_items: dict[str, PlanItem] = field(default_factory=dict)
    tests: list[TestInfo] = field(default_factory=list)

    # Issues found
    prd_not_in_plan: list[str] = field(default_factory=list)
    plan_not_in_prd: list[str] = field(default_factory=list)
    no_test_coverage: list[str] = field(default_factory=list)
    suspect_tests: list[TestInfo] = field(default_factory=list)
    completion_issues: list[tuple[str, str]] = field(default_factory=list)


# Requirement ID core pattern (without word boundaries)
REQ_ID_CORE = r'(?:FR|NFR|INV|R|TD)-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*'

# Requirement ID pattern with word boundaries for general matching
REQ_ID_PATTERN = re.compile(r'\b(' + REQ_ID_CORE + r')\b')

# PRD requirement definition pattern: - **FR-1**: Description text
PRD_REQ_PATTERN = re.compile(r'^\s*[-*]\s*\*\*(' + REQ_ID_CORE + r')\*\*:\s*(.*)')

# PRD requirement definition pattern (Table): | FR-1 | Description text | ... |
PRD_TABLE_REQ_PATTERN = re.compile(r'^\s*\|\s*(' + REQ_ID_CORE + r')\s*\|\s*(.*?)\s*\|.*')

# PRD requirement definition pattern (Heading): ### FR-1: Description text
PRD_HEADING_PATTERN = re.compile(r'^#+\s*(' + REQ_ID_CORE + r'):\s*(.*)')

# PLAN item pattern (with checkbox): - [x] **FR-1**: Description text
PLAN_ITEM_PATTERN = re.compile(r'^\s*[-*]\s*\[([ xX~])\]\s*\*\*(' + REQ_ID_CORE + r')\*\*:\s*(.*)')

# Loose PLAN item pattern: - [x] Description (FR-1)
TASK_PATTERN = re.compile(r'^\s*[-*]\s*\[([ xX~])\]\s*(.*)')
# Pattern to find (FR-XX, FR-YY) inside a string
REQ_REF_PATTERN = re.compile(r'\((' + REQ_ID_CORE + r'(?:,\s*' + REQ_ID_CORE + r')*)\)')
# Header pattern: ### Section Title (FR-1)
HEADER_PATTERN = re.compile(r'^#+\s+(.*)')

# Test reference pattern in PLAN
TEST_REF_PATTERN = re.compile(r'Tests?:\s*`([^`]+)`')

# PLAN table pattern: | FR-1 | Done | ... | (requirement ID in first column)
PLAN_TABLE_PATTERN = re.compile(r'^\s*\|\s*(' + REQ_ID_CORE + r')\s*\|\s*(Done|Pending|In Progress|Complete|Incomplete|Yes|No|-)\s*\|', re.IGNORECASE)

def parse_prd(prd_path: Path) -> dict[str, Requirement]:
    """Parse PRD.md and extract requirements."""
    requirements = {}
    content = prd_path.read_text()
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # Try list format
        match = PRD_REQ_PATTERN.match(line)
        if match:
            req_id = match.group(1)
            req_text = match.group(2).strip()
            requirements[req_id] = Requirement(
                id=req_id,
                text=req_text,
                line_number=i
            )
            continue

        # Try table format
        match = PRD_TABLE_REQ_PATTERN.match(line)
        if match:
            req_id = match.group(1)
            req_text = match.group(2).strip()
            requirements[req_id] = Requirement(
                id=req_id,
                text=req_text,
                line_number=i
            )
            continue

        # Try heading format: ### FR-1: Description
        match = PRD_HEADING_PATTERN.match(line)
        if match:
            req_id = match.group(1)
            req_text = match.group(2).strip()
            requirements[req_id] = Requirement(
                id=req_id,
                text=req_text,
                line_number=i
            )

    return requirements


def parse_plan(plan_path: Path) -> dict[str, PlanItem]:
    """Parse PLAN.md and extract tracked items."""
    plan_items = {}
    content = plan_path.read_text()
    lines = content.split('\n')

    current_section_reqs = []

    for i, line in enumerate(lines, 1):
        # Check for Header first
        header_match = HEADER_PATTERN.match(line)
        if header_match:
            text = header_match.group(1).strip()
            ids = REQ_ID_PATTERN.findall(text)

            if ids:
                current_section_reqs = []
                for req_id in ids:
                    # Optimistically mark complete, will be unset if incomplete tasks follow
                    plan_items[req_id] = PlanItem(
                        id=req_id,
                        text=f"Section: {text}",
                        completed=True,
                        line_number=i
                    )
                    current_section_reqs.append(req_id)
            else:
                # New section with no requirements, clear context
                current_section_reqs = []

            # Continue to next line (headers aren't tasks)
            continue

        # Try strict format first: - [x] **FR-1**: Description
        match = PLAN_ITEM_PATTERN.match(line)
        if match:
            status = match.group(1)
            req_id = match.group(2)
            text = match.group(3).strip()

            # If this task is incomplete, it might also affect the section requirements
            if status.lower() != 'x':
                 for section_req in current_section_reqs:
                     if section_req in plan_items:
                         plan_items[section_req].completed = False

            # Look for test references
            test_refs = []
            context = '\n'.join(lines[max(0, i-1):min(len(lines), i+5)])
            test_match = TEST_REF_PATTERN.search(context)
            if test_match:
                test_refs = [t.strip() for t in test_match.group(1).split(',')]

            plan_items[req_id] = PlanItem(
                id=req_id,
                text=text,
                completed=(status.lower() == 'x'),
                line_number=i,
                test_refs=test_refs
            )
            continue

        # Try loose format: - [x] Description (FR-1, FR-2)
        match = TASK_PATTERN.match(line)
        if match:
            status = match.group(1)
            text = match.group(2).strip()

            # If this task is incomplete, mark section requirements as incomplete
            if status.lower() != 'x':
                 for section_req in current_section_reqs:
                     if section_req in plan_items:
                         plan_items[section_req].completed = False

            # Find all requirement references anywhere in the text
            ids = REQ_ID_PATTERN.findall(text)
            for req_id in ids:
                # Look for test references
                test_refs = []
                context = '\n'.join(lines[max(0, i-1):min(len(lines), i+5)])
                test_match = TEST_REF_PATTERN.search(context)
                if test_match:
                    test_refs = [t.strip() for t in test_match.group(1).split(',')]

                plan_items[req_id] = PlanItem(
                    id=req_id,
                    text=text,
                    completed=(status.lower() == 'x'),
                    line_number=i,
                    test_refs=test_refs
                )
            continue

        # Try table format: | FR-1 | Done | ... |
        match = PLAN_TABLE_PATTERN.match(line)
        if match:
            req_id = match.group(1)
            status_text = match.group(2).lower()
            completed = status_text in ('done', 'complete', 'yes')

            # Only add if not already tracked (avoid overwriting more specific entries)
            if req_id not in plan_items:
                plan_items[req_id] = PlanItem(
                    id=req_id,
                    text=f"Table entry: {line.strip()}",
                    completed=completed,
                    line_number=i,
                    test_refs=[]
                )

    return plan_items


def find_test_files(project_root: Path) -> list[Path]:
    """Find all Python test files in the project."""
    test_files = []

    # Directories to skip
    skip_dirs = {'.venv', 'venv', 'node_modules', '.git', '__pycache__',
                 '.tox', '.nox', 'build', 'dist', '.eggs', '*.egg-info'}

    def should_skip(path: Path) -> bool:
        for part in path.parts:
            if part in skip_dirs or part.endswith('.egg-info'):
                return True
        return False

    for pattern in ['tests/**/test_*.py', 'test_*.py', '**/test_*.py']:
        for f in project_root.glob(pattern):
            if not should_skip(f.relative_to(project_root)):
                test_files.append(f)

    return list(set(test_files))


def analyze_test_file(test_path: Path) -> list[TestInfo]:
    """Analyze a test file for requirement markers and suspicious patterns.

    Only analyzes top-level test functions and test methods in classes,
    not nested functions within tests (which may have names like test_handler).
    """
    tests = []
    content = test_path.read_text()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return tests

    lines = content.split('\n')

    def process_test_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Process a single test function."""
        if not node.name.startswith('test_'):
            return

        test_info = TestInfo(
            name=node.name,
            file=test_path,
            line_number=node.lineno,
            requirement_ids=[]
        )

        # Look for @pytest.mark.requirement decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                # Handle @pytest.mark.requirement("FR-1")
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == 'requirement':
                        for arg in decorator.args:
                            if isinstance(arg, ast.Constant):
                                test_info.requirement_ids.append(arg.value)

        # Check for suspicious patterns in the function body
        issues = check_test_integrity(node, lines)
        test_info.issues = issues

        tests.append(test_info)

    # Only look at top-level functions and methods in classes (not nested functions)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Top-level test function
            process_test_function(node)
        elif isinstance(node, ast.ClassDef):
            # Test class - look for test methods
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    process_test_function(item)

    return tests


def check_test_integrity(func_node: ast.FunctionDef | ast.AsyncFunctionDef, lines: list[str]) -> list[str]:
    """Check a test function for integrity issues using AST analysis.

    This uses AST-based analysis to avoid false positives from:
    - `pass` in nested functions/classes
    - `pass` in string literals (test data)
    - `pass` in exception handlers
    """
    issues = []

    # Get direct children of the function body (excluding nested defs)
    body = func_node.body

    # Skip docstring if present
    body_without_docstring = body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        if isinstance(body[0].value.value, str):
            body_without_docstring = body[1:]

    # Check if test is just a placeholder (only pass statement)
    if len(body_without_docstring) == 1 and isinstance(body_without_docstring[0], ast.Pass):
        issues.append("Placeholder test (only pass statement)")
        return issues  # No point checking further

    # Check for always-pass assertions at top level
    for node in body_without_docstring:
        if isinstance(node, ast.Assert):
            test = node.test
            # Check for `assert True`
            if isinstance(test, ast.Constant) and test.value is True:
                issues.append("Always-pass pattern: assert True")
            # Check for `assert 1` (truthy constant)
            elif isinstance(test, ast.Constant) and test.value == 1:
                issues.append("Always-pass pattern: assert 1")
            # Check for `assert 1 == 1`
            elif isinstance(test, ast.Compare):
                if (isinstance(test.left, ast.Constant) and
                    len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq) and
                    len(test.comparators) == 1 and isinstance(test.comparators[0], ast.Constant)):
                    if test.left.value == test.comparators[0].value:
                        issues.append("Always-pass pattern: trivial comparison")

    # Check if function has any assertions (using AST, more accurate than text matching)
    has_assertion = False

    class AssertionFinder(ast.NodeVisitor):
        def __init__(self):
            self.found = False

        def visit_Assert(self, node):
            self.found = True

        def visit_Call(self, node):
            # Check for pytest.raises, pytest.warns, mock assertions
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if attr in ('raises', 'warns', 'assert_called', 'assert_called_once',
                           'assert_called_with', 'assert_called_once_with',
                           'assert_not_called', 'assert_has_calls'):
                    self.found = True
            self.generic_visit(node)

        def visit_With(self, node):
            # Check for `with pytest.raises(...):` context managers
            for item in node.items:
                if isinstance(item.context_expr, ast.Call):
                    call = item.context_expr
                    if isinstance(call.func, ast.Attribute):
                        if call.func.attr in ('raises', 'warns'):
                            self.found = True
            self.generic_visit(node)

        # Don't recurse into nested function definitions
        def visit_FunctionDef(self, node):
            pass

        def visit_AsyncFunctionDef(self, node):
            pass

        def visit_ClassDef(self, node):
            pass

    finder = AssertionFinder()
    for node in body:
        finder.visit(node)
    has_assertion = finder.found

    # Only flag as placeholder if no assertions found AND function body is trivial
    if not has_assertion:
        # Check if body only contains non-assertion statements
        non_trivial = False
        for node in body_without_docstring:
            if not isinstance(node, (ast.Pass, ast.Expr)):
                non_trivial = True
                break
            # Check if Expr contains something meaningful (not just a string)
            if isinstance(node, ast.Expr):
                if not isinstance(node.value, ast.Constant):
                    non_trivial = True
                    break

        if not non_trivial:
            issues.append("No assertions found (placeholder test)")

    return issues


def run_audit(project_root: Path) -> AuditResult:
    """Run the full audit on a project."""
    result = AuditResult()

    # Parse PRD
    prd_path = project_root / 'PRD.md'
    if prd_path.exists():
        result.requirements = parse_prd(prd_path)
        if not result.requirements:
            print(f"Warning: No requirements found in {prd_path}. Check file format.", file=sys.stderr)

    # Parse PLAN
    plan_path = project_root / 'PLAN.md'
    if plan_path.exists():
        result.plan_items = parse_plan(plan_path)

    # Find and analyze tests
    test_files = find_test_files(project_root)
    for test_file in test_files:
        result.tests.extend(analyze_test_file(test_file))

    # Build test coverage map
    tested_requirements = set()
    for test in result.tests:
        tested_requirements.update(test.requirement_ids)

    # Check PRD → PLAN sync
    for req_id in result.requirements:
        if req_id not in result.plan_items:
            result.prd_not_in_plan.append(req_id)

    # Check PLAN → PRD sync
    for plan_id in result.plan_items:
        if plan_id not in result.requirements:
            result.plan_not_in_prd.append(plan_id)

    # Check test coverage
    for req_id in result.requirements:
        if req_id not in tested_requirements:
            result.no_test_coverage.append(req_id)

    # Check test integrity
    for test in result.tests:
        if test.issues:
            result.suspect_tests.append(test)

    # Check completion honesty
    for plan_id, plan_item in result.plan_items.items():
        if plan_item.completed:
            # Check if there are tests for this requirement
            has_tests = any(plan_id in t.requirement_ids for t in result.tests)
            if not has_tests and plan_id in result.requirements:
                result.completion_issues.append(
                    (plan_id, "Marked complete but no tests found")
                )

    return result


def generate_report(result: AuditResult, project_root: Path) -> str:
    """Generate a markdown audit report."""
    lines = [
        "# Project Audit Report",
        "",
        f"**Project**: {project_root.name}",
        f"**Audited**: {project_root.absolute()}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Requirements in PRD**: {len(result.requirements)}",
        f"- **Items in PLAN**: {len(result.plan_items)}",
        f"- **Test functions found**: {len(result.tests)}",
        "",
    ]

    # Calculate issue counts
    total_issues = (
        len(result.prd_not_in_plan) +
        len(result.plan_not_in_prd) +
        len(result.no_test_coverage) +
        len(result.suspect_tests) +
        len(result.completion_issues)
    )

    if total_issues == 0:
        lines.append("**No issues found.**")
    else:
        lines.append(f"**Total issues found: {total_issues}**")

    lines.extend(["", "---", ""])

    # PRD not in PLAN
    lines.append("## PRD Requirements Not in PLAN")
    lines.append("")
    if result.prd_not_in_plan:
        lines.append("These requirements are defined in PRD.md but not tracked in PLAN.md:")
        lines.append("")
        for req_id in sorted(result.prd_not_in_plan):
            req = result.requirements[req_id]
            lines.append(f"- **{req_id}**: {req.text} (PRD.md:{req.line_number})")
    else:
        lines.append("*None*")
    lines.extend(["", "---", ""])

    # PLAN not in PRD
    lines.append("## PLAN Items Without PRD Backing")
    lines.append("")
    if result.plan_not_in_prd:
        lines.append("These items are in PLAN.md but not defined in PRD.md:")
        lines.append("")
        for plan_id in sorted(result.plan_not_in_prd):
            item = result.plan_items[plan_id]
            lines.append(f"- **{plan_id}**: {item.text} (PLAN.md:{item.line_number})")
    else:
        lines.append("*None*")
    lines.extend(["", "---", ""])

    # No test coverage
    lines.append("## Requirements Without Test Coverage")
    lines.append("")
    if result.no_test_coverage:
        lines.append("These requirements have no tests with `@pytest.mark.requirement` marker:")
        lines.append("")
        for req_id in sorted(result.no_test_coverage):
            req = result.requirements[req_id]
            lines.append(f"- **{req_id}**: {req.text}")
    else:
        lines.append("*All requirements have test coverage*")
    lines.extend(["", "---", ""])

    # Suspect tests
    lines.append("## Suspect Tests")
    lines.append("")
    if result.suspect_tests:
        lines.append("These tests have integrity issues:")
        lines.append("")
        for test in result.suspect_tests:
            rel_path = test.file.relative_to(project_root) if project_root in test.file.parents else test.file
            lines.append(f"### `{test.name}` ({rel_path}:{test.line_number})")
            lines.append("")
            if test.requirement_ids:
                lines.append(f"**Requirements**: {', '.join(test.requirement_ids)}")
            lines.append("")
            lines.append("**Issues**:")
            for issue in test.issues:
                lines.append(f"- {issue}")
            lines.append("")
    else:
        lines.append("*No suspect tests found*")
    lines.extend(["", "---", ""])

    # Completion issues
    lines.append("## Completion Honesty Issues")
    lines.append("")
    if result.completion_issues:
        lines.append("These items are marked complete but have issues:")
        lines.append("")
        for req_id, issue in result.completion_issues:
            item = result.plan_items[req_id]
            lines.append(f"- **{req_id}**: {issue} (PLAN.md:{item.line_number})")
    else:
        lines.append("*No completion issues found*")
    lines.extend(["", "---", ""])

    # Test coverage matrix
    lines.append("## Test Coverage Matrix")
    lines.append("")
    lines.append("| Requirement | In PLAN | Has Tests | Status |")
    lines.append("|-------------|---------|-----------|--------|")

    for req_id in sorted(result.requirements.keys()):
        in_plan = "Yes" if req_id in result.plan_items else "No"
        has_tests = "Yes" if any(req_id in t.requirement_ids for t in result.tests) else "No"

        if req_id in result.plan_items:
            item = result.plan_items[req_id]
            status = "Complete" if item.completed else "Pending"
        else:
            status = "Not tracked"

        lines.append(f"| {req_id} | {in_plan} | {has_tests} | {status} |")

    lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Audit a spec-driven Python project for integrity issues"
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to project root (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: AUDIT_REPORT.md in project root)"
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print report to stdout instead of file"
    )

    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    # Validate project structure
    prd_path = project_root / 'PRD.md'
    plan_path = project_root / 'PLAN.md'

    if not prd_path.exists():
        print(f"Error: PRD.md not found in {project_root}", file=sys.stderr)
        sys.exit(1)

    if not plan_path.exists():
        print(f"Error: PLAN.md not found in {project_root}", file=sys.stderr)
        sys.exit(1)

    # Run audit
    result = run_audit(project_root)

    # Generate report
    report = generate_report(result, project_root)

    if args.stdout:
        print(report)
    else:
        output_path = Path(args.output) if args.output else project_root / 'AUDIT_REPORT.md'
        output_path.write_text(report)
        print(f"Audit report written to: {output_path}")

    # Exit with error code if issues found
    total_issues = (
        len(result.prd_not_in_plan) +
        len(result.plan_not_in_prd) +
        len(result.suspect_tests) +
        len(result.completion_issues)
    )

    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
