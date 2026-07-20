from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


SKILL_NAME = "pdf-to-editable-word"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY_ROOT / "skills" / SKILL_NAME


def default_skill_root(agent: str, scope: str) -> Path:
    if scope == "project":
        return Path.cwd() / (".claude" if agent == "claude" else ".codex") / "skills"
    if agent == "claude":
        return Path.home() / ".claude" / "skills"
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills"


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the portable Agent Skill.")
    parser.add_argument("--agent", choices=["codex", "claude"], default="codex")
    parser.add_argument("--scope", choices=["user", "project"], default="user")
    parser.add_argument("--destination", type=Path, help="Custom parent skills directory")
    args = parser.parse_args()

    root = args.destination.expanduser().resolve() if args.destination else default_skill_root(args.agent, args.scope)
    target = root / SKILL_NAME
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, target, dirs_exist_ok=True)
    print(f"Installed {SKILL_NAME} to {target}")
    print("Install the Python package with `python -m pip install .` before invoking the skill.")


if __name__ == "__main__":
    main()
