# Changelog

## v0.1.0 - 2026-07-20

First public release of the portable PDF to Editable Word Agent Skill.

### Included

- Layout-preserving PDF-to-DOCX conversion with editable, searchable text boxes.
- Portable Agent Skill for Codex, Claude Code, and custom Agent Skills directories.
- Standalone `pdf2word` CLI with `inspect`, `convert`, `validate`, `doctor`, and `skill install` commands.
- Safe resumable rendering with source fingerprint and settings validation.
- Structural DOCX validation for pages, background images, text boxes, and editable characters.
- Synthetic, redistributable PDF/DOCX examples and an actual Microsoft Word-rendered demo GIF.
- Cross-platform Poppler discovery, standard PDF font mapping, tests, and GitHub Actions.

### Known limitations

- Scanned PDFs require an OCR stage that is not included yet.
- Non-text content remains in the page background rather than becoming semantic Word objects.
- Mixed page sizes are rejected in v0.1.0.
- Microsoft Word is the primary rendering target; LibreOffice may handle VML text boxes differently.
