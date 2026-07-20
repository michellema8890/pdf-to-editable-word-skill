# Contributing

Install development dependencies and run the tests before opening a pull request:

```bash
python -m pip install -e ".[dev]"
python scripts/sync_bundled_skill.py
python -m unittest discover -s tests -v
```

Use synthetic PDFs or documents with an explicit redistribution license for regression cases. Never commit confidential or copyrighted source documents. Include a regression test for bug fixes and describe Microsoft Word and LibreOffice behavior separately when rendering differs.

After changing `skills/pdf-to-editable-word`, run `scripts/sync_bundled_skill.py` so the wheel contains the same portable Skill. Regenerate demo artifacts with `scripts/generate_demo.py` and `scripts/build_demo_assets.py`; commit only synthetic, redistributable examples.
