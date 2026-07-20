from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .converter import convert_pdf, inspect_pdf, validate_docx
from .doctor import run_doctor
from .installer import install_skill


def _print_result(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    for key, value in result.items():
        print(f"{key}: {value}")


def _print_doctor(result: dict, as_json: bool) -> None:
    if as_json:
        _print_result(result, True)
        return
    for check in result["checks"]:
        marker = "INFO" if not check["required"] else ("OK" if check["ok"] else "FAIL")
        print(f"[{marker}] {check['name']}: {check['detail']}")
    print("\nReady to convert PDFs." if result["ready"] else "\nMissing a required dependency.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf2word",
        description="Convert text-based PDFs to layout-preserving DOCX files with editable text.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = commands.add_parser("inspect", help="Inspect a PDF before conversion")
    inspect_cmd.add_argument("pdf", type=Path)
    inspect_cmd.add_argument("--json", action="store_true")

    convert_cmd = commands.add_parser("convert", help="Convert a PDF to DOCX")
    convert_cmd.add_argument("pdf", type=Path)
    convert_cmd.add_argument("out_docx", type=Path)
    convert_cmd.add_argument("--work-dir", type=Path)
    convert_cmd.add_argument("--dpi", type=int, default=144)
    convert_cmd.add_argument("--start", type=int, default=0, help="Zero-based inclusive page index")
    convert_cmd.add_argument("--end", type=int, default=None, help="Zero-based exclusive page index")
    convert_cmd.add_argument("--resume", action="store_true")
    convert_cmd.add_argument("--pdftoppm", type=Path)

    validate_cmd = commands.add_parser("validate", help="Validate a generated DOCX")
    validate_cmd.add_argument("docx", type=Path)
    validate_cmd.add_argument("--pdf", type=Path)
    validate_cmd.add_argument("--json", action="store_true")

    doctor_cmd = commands.add_parser("doctor", help="Check conversion dependencies")
    doctor_cmd.add_argument("--pdftoppm", type=Path)
    doctor_cmd.add_argument("--json", action="store_true")

    skill_cmd = commands.add_parser("skill", help="Manage the portable Agent Skill")
    skill_actions = skill_cmd.add_subparsers(dest="skill_command", required=True)
    install_cmd = skill_actions.add_parser("install", help="Install the Agent Skill")
    install_cmd.add_argument("--agent", choices=["codex", "claude"], default="codex")
    install_cmd.add_argument("--scope", choices=["user", "project"], default="user")
    install_cmd.add_argument("--destination", type=Path, help="Custom parent skills directory")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "inspect":
        _print_result(inspect_pdf(args.pdf), args.json)
        return 0
    if args.command == "convert":
        work_dir = args.work_dir or args.out_docx.parent / f".{args.out_docx.stem}.pdf2word-work"
        result = convert_pdf(
            args.pdf,
            args.out_docx,
            work_dir=work_dir,
            dpi=args.dpi,
            start=args.start,
            end=args.end,
            resume=args.resume,
            pdftoppm=args.pdftoppm,
        )
        _print_result(result, False)
        return 0
    if args.command == "validate":
        result = validate_docx(args.docx, args.pdf)
        _print_result(result, args.json)
        return 0 if result["valid"] else 1
    if args.command == "doctor":
        result = run_doctor(args.pdftoppm)
        _print_doctor(result, args.json)
        return 0 if result["ready"] else 1
    if args.command == "skill" and args.skill_command == "install":
        target = install_skill(agent=args.agent, scope=args.scope, destination=args.destination)
        print(f"Installed pdf-to-editable-word to {target}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
