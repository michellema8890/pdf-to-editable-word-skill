from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from pdf_to_editable_word.converter import convert_pdf, find_pdftoppm, inspect_pdf, validate_docx


def make_pdf(path: Path, pages: int = 2) -> None:
    document = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    for page_number in range(1, pages + 1):
        document.setLineWidth(1)
        document.rect(36, 36, width - 72, height - 72)
        document.setFont("Helvetica-Bold", 18)
        document.drawString(72, height - 90, f"Editable document page {page_number}")
        document.setFont("Helvetica", 11)
        document.drawString(72, height - 120, "This text should remain searchable and editable in Word.")
        document.drawString(72, height - 140, "The border remains in the rendered page background.")
        document.showPage()
    document.save()


class ConversionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_inspect_text_pdf(self) -> None:
        pdf = self.root / "sample.pdf"
        make_pdf(pdf)
        result = inspect_pdf(pdf)
        self.assertEqual(result["pages"], 2)
        self.assertEqual(result["text_layer_pages"], 2)
        self.assertTrue(result["conversion_ready"])
        self.assertFalse(result["mixed_page_sizes"])

    def test_convert_and_validate(self) -> None:
        try:
            poppler = find_pdftoppm()
        except FileNotFoundError:
            self.skipTest("pdftoppm is not installed")
        pdf = self.root / "sample.pdf"
        docx = self.root / "sample.docx"
        make_pdf(pdf)
        conversion = convert_pdf(pdf, docx, work_dir=self.root / "work", pdftoppm=poppler)
        result = validate_docx(docx, pdf)
        self.assertEqual(conversion["pages"], 2)
        self.assertTrue(result["valid"])
        self.assertEqual(result["pages"], 2)
        self.assertEqual(result["background_images"], 2)
        self.assertGreaterEqual(result["editable_text_boxes"], 6)
        self.assertGreater(result["editable_characters"], 100)

    def test_custom_skill_install(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        destination = self.root / "agent-skills"
        subprocess.run(
            [sys.executable, str(repository / "scripts" / "install_skill.py"), "--destination", str(destination)],
            cwd=repository,
            check=True,
        )
        installed = destination / "pdf-to-editable-word"
        self.assertTrue((installed / "SKILL.md").is_file())
        self.assertTrue((installed / "scripts" / "pdf2word.py").is_file())


if __name__ == "__main__":
    unittest.main()
