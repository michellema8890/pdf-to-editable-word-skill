# PDF to Editable Word

Convert text-based PDFs into Microsoft Word documents that preserve the page appearance while keeping text editable. Everything runs locally; documents are never uploaded.

> Alpha software. The current output is optimized for Microsoft Word and for PDFs that already contain a text layer. See [Known limitations](#known-limitations).

## Why this approach

Most converters choose between editable text and visual fidelity. This project uses a hybrid representation:

1. Extract words, positions, font sizes, and colors from the PDF text layer.
2. Render each source page and remove the original glyph areas from the page image.
3. Rebuild the DOCX with the cleaned page as a background and editable, absolutely positioned text boxes above it.
4. Validate the generated DOCX structure before delivery.

Non-text graphics remain visually faithful because they stay in the page background. Text remains searchable and editable in Word.

## Quick start

Requirements:

- Python 3.10+
- Poppler (`pdftoppm` on `PATH`)
- Microsoft Word for the best rendering compatibility

```bash
git clone https://github.com/longligooo/pdf-to-editable-word.git
cd pdf-to-editable-word
python -m pip install -e .

pdf2word inspect input.pdf
pdf2word convert input.pdf output.docx
pdf2word validate output.docx --pdf input.pdf
```

On Windows, install Poppler and either add `pdftoppm.exe` to `PATH` or set `PDFTOPPM` to its full path. On Debian or Ubuntu:

```bash
sudo apt-get install poppler-utils
```

Conversion can resume after an interruption:

```bash
pdf2word convert input.pdf output.docx --work-dir .pdf2word-work/input --resume
```

The work directory contains a source fingerprint and conversion parameters. Cached pages are reused only when the manifest matches.

## Agent installation

The repository includes one portable `SKILL.md` shared by Codex, Claude Code, and agents that implement the Agent Skills convention.

```bash
# Codex user skill
python scripts/install_skill.py --agent codex

# Claude Code user skill
python scripts/install_skill.py --agent claude

# Project-local Claude Code skill
python scripts/install_skill.py --agent claude --scope project

# Any agent-specific skill directory
python scripts/install_skill.py --destination /path/to/agent/skills
```

Agents without Skill support can invoke the `pdf2word` CLI directly. An asynchronous MCP adapter is planned after the conversion job API is stable.

## Commands

```text
pdf2word inspect INPUT.pdf [--json]
pdf2word convert INPUT.pdf OUTPUT.docx [--dpi 144] [--resume]
pdf2word validate OUTPUT.docx [--pdf INPUT.pdf] [--json]
```

Use `--pdftoppm PATH` when Poppler is not on `PATH`. Use `--start` and `--end` for a zero-based page range.

## Known limitations

- PDFs without a text layer require OCR, which is not included in v0.1.
- Text is editable; tables, diagrams, images, and other page graphics remain part of the background image.
- Colored or textured backgrounds behind text may show erased regions.
- Mixed page sizes are detected and rejected instead of silently producing incorrect output.
- The DOCX uses VML text boxes for broad Microsoft Word support. LibreOffice may reposition or omit them.
- Font substitution can change line width when the source fonts are unavailable.

## Development

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

Tests generate synthetic PDFs at runtime; no copyrighted sample documents are committed.

## Roadmap

- Visual diff reports rendered through Microsoft Word
- Optional OCR backends for scanned documents
- Better background reconstruction for colored pages
- Mixed-size and mixed-orientation documents
- Asynchronous MCP server for long-running conversions
- Reproducible benchmark corpus and quality dashboard

## License

MIT. Poppler is an external runtime dependency and is not distributed by this repository.
