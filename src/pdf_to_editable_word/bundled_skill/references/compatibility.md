# Compatibility

## Source PDFs

- Require extractable text on at least one selected page. Pages without text are preserved as background-only pages.
- Reject mixed page sizes in v0.1 rather than generating incorrect sections.
- Treat password-protected, damaged, and malformed PDFs as unsupported input.
- Expect white or black backgrounds behind most text. Erasure on textured or colored areas may be visible.

## DOCX rendering

- Optimize output for desktop Microsoft Word.
- Use VML text boxes because they preserve absolute positioning in Word.
- Expect LibreOffice and browser previews to reposition or omit some text boxes.
- Expect font substitution when source fonts are unavailable on the viewing system.

## Editability

Text is stored in editable text boxes. Page borders, table lines, photographs, diagrams, signatures, QR codes, and other non-text content remain in a raster page background.

## Failure handling

Use a fresh work directory after changing the source PDF, DPI, or page range. Use `--resume` only with an unchanged manifest. Preserve the work directory until validation succeeds.
