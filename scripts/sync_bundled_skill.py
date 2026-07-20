from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "pdf-to-editable-word"
TARGET = ROOT / "src" / "pdf_to_editable_word" / "bundled_skill"


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"Synced {SOURCE} -> {TARGET}")


if __name__ == "__main__":
    main()
