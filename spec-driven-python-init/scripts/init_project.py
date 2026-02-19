#!/usr/bin/env python3
"""Initialize a spec-driven development project."""
import argparse
import os
from datetime import date
from pathlib import Path


def get_skill_dir() -> Path:
    """Get the skill directory (parent of scripts/)."""
    return Path(__file__).parent.parent


def read_template(name: str) -> str:
    """Read a template file from the templates directory."""
    template_path = get_skill_dir() / "templates" / name
    return template_path.read_text()


def substitute(content: str, substitutions: dict[str, str]) -> str:
    """Replace {{KEY}} placeholders with values."""
    for key, value in substitutions.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def init_project(
    target_dir: Path,
    name: str,
    description: str,
    python_version: str = "3.11",
) -> None:
    """Initialize project structure with all files."""
    target_dir = Path(target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    subs = {
        "PROJECT_NAME": name,
        "DESCRIPTION": description,
        "PYTHON_VERSION": python_version,
        "DATE": date.today().isoformat(),
    }

    # Create directories
    (target_dir / "src").mkdir(exist_ok=True)
    (target_dir / "tests").mkdir(exist_ok=True)
    (target_dir / "docs" / "decisions").mkdir(parents=True, exist_ok=True)

    # Create __init__.py files
    (target_dir / "src" / "__init__.py").touch()
    (target_dir / "tests" / "__init__.py").touch()
    (target_dir / "docs" / "decisions" / ".gitkeep").touch()

    # Create files from templates
    files = {
        "PRD.md": "PRD.md",
        "PLAN.md": "PLAN.md",
        "pyproject.toml": "pyproject.toml",
        "README.md": "README.md",
        ".gitignore": ".gitignore",
        "docs/AGENT_RULES.md": "AGENT_RULES.md",
        "tests/test_example.py": "test_example.py",
    }

    for dest, template in files.items():
        content = read_template(template)
        content = substitute(content, subs)
        (target_dir / dest).write_text(content)

    print(f"✓ Initialized spec-driven project: {name}")
    print(f"  Location: {target_dir}")
    print("\nNext steps:")
    print("  1. cd", target_dir)
    print("  2. git init && git add -A")
    print('  3. git commit -m "[PROJECT] Initialize spec-driven development structure"')
    print("  4. uv venv")
    print("  5. uv pip install -e '.[dev]'")


def main():
    parser = argparse.ArgumentParser(description="Initialize a spec-driven project")
    parser.add_argument("--name", "-n", required=True, help="Project name")
    parser.add_argument("--description", "-d", default="", help="Project description")
    parser.add_argument("--python", "-p", default="3.11", help="Python version")
    parser.add_argument(
        "--path",
        default=".",
        help="Target directory (default: current directory)",
    )

    args = parser.parse_args()
    init_project(
        target_dir=args.path,
        name=args.name,
        description=args.description,
        python_version=args.python,
    )


if __name__ == "__main__":
    main()
