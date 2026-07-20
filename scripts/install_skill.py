from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from pdf_to_editable_word.installer import install_skill  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the portable Agent Skill.")
    parser.add_argument("--agent", choices=["codex", "claude"], default="codex")
    parser.add_argument("--scope", choices=["user", "project"], default="user")
    parser.add_argument("--destination", type=Path, help="Custom parent skills directory")
    args = parser.parse_args()
    target = install_skill(
        agent=args.agent,
        scope=args.scope,
        destination=args.destination,
        source=REPOSITORY_ROOT / "skills" / "pdf-to-editable-word",
    )
    print(f"Installed pdf-to-editable-word to {target}")


if __name__ == "__main__":
    main()
