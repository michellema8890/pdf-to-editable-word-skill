from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from .converter import find_pdftoppm


def _word_detail() -> str | None:
    if sys.platform != "win32":
        return None
    try:
        import winreg

        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE"
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    value, _ = winreg.QueryValueEx(key, None)
                    path = Path(value)
                    if path.is_file():
                        return str(path)
            except OSError:
                continue
    except ImportError:
        pass
    try:
        import ctypes

        class Guid(ctypes.Structure):
            _fields_ = [
                ("data1", ctypes.c_ulong),
                ("data2", ctypes.c_ushort),
                ("data3", ctypes.c_ushort),
                ("data4", ctypes.c_ubyte * 8),
            ]

        clsid = Guid()
        if ctypes.windll.ole32.CLSIDFromProgID("Word.Application", ctypes.byref(clsid)) == 0:
            return "Microsoft Word COM registration found"
    except (AttributeError, OSError):
        pass
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "$type=[type]::GetTypeFromProgID('Word.Application'); if ($null -ne $type) { exit 0 } else { exit 1 }",
            ],
            capture_output=True,
            check=False,
            timeout=10,
        )
        if result.returncode == 0:
            return "Microsoft Word COM registration found"
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return None


def run_doctor(pdftoppm: Path | None = None) -> dict:
    checks: list[dict] = [
        {
            "name": "python",
            "required": True,
            "ok": sys.version_info >= (3, 10),
            "detail": f"{platform.python_implementation()} {platform.python_version()}",
        }
    ]
    try:
        poppler = find_pdftoppm(pdftoppm)
        result = subprocess.run(
            [str(poppler), "-v"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        version_text = (result.stderr or result.stdout).splitlines()
        checks.append(
            {
                "name": "poppler",
                "required": True,
                "ok": result.returncode == 0,
                "detail": version_text[0].strip() if version_text else str(poppler),
                "path": str(poppler),
            }
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
        checks.append({"name": "poppler", "required": True, "ok": False, "detail": str(exc)})

    word = _word_detail()
    checks.append(
        {
            "name": "microsoft_word",
            "required": False,
            "ok": word is not None,
            "detail": word or "Optional; recommended for final visual review",
        }
    )
    ready = all(check["ok"] for check in checks if check["required"])
    return {"ready": ready, "checks": checks}
