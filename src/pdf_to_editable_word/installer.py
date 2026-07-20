from __future__ import annotations

import os
import shutil
from importlib.resources import files
from pathlib import Path


SKILL_NAME = "pdf-to-editable-word"


def bundled_skill_path() -> Path:
    return Path(str(files("pdf_to_editable_word").joinpath("bundled_skill")))


def default_skill_root(agent: str, scope: str, project_dir: Path | None = None) -> Path:
    if scope == "project":
        root = (project_dir or Path.cwd()).resolve()
        return root / (".claude" if agent == "claude" else ".codex") / "skills"
    if agent == "claude":
        return Path.home() / ".claude" / "skills"
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills"


def install_skill(
    *,
    agent: str = "codex",
    scope: str = "user",
    destination: Path | None = None,
    source: Path | None = None,
    project_dir: Path | None = None,
) -> Path:
    source_path = (source or bundled_skill_path()).resolve()
    if not (source_path / "SKILL.md").is_file():
        raise FileNotFoundError(f"Bundled Agent Skill is incomplete: {source_path}")
    skill_root = destination.expanduser().resolve() if destination else default_skill_root(agent, scope, project_dir)
    target = skill_root / SKILL_NAME
    skill_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_path, target, dirs_exist_ok=True)
    return target
