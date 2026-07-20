from __future__ import annotations

import shutil
import subprocess
import sys


def main() -> int:
    executable = shutil.which("pdf2word")
    if executable:
        return subprocess.call([executable, *sys.argv[1:]])
    try:
        from pdf_to_editable_word.cli import main as cli_main
    except ImportError:
        print(
            "pdf-to-editable-word is not installed. Install the repository with "
            "`python -m pip install .` first.",
            file=sys.stderr,
        )
        return 2
    cli_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
