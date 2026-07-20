# Contributing

Install development dependencies and run the tests before opening a pull request:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

Use synthetic PDFs or documents with an explicit redistribution license for regression cases. Never commit confidential or copyrighted source documents. Include a regression test for bug fixes and describe Microsoft Word and LibreOffice behavior separately when rendering differs.
