from __future__ import annotations

import os
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_to_editable_word.converter import convert_pdf  # noqa: E402


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def draw_demo_pdf(path: Path) -> None:
    page = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    ink = HexColor("#17212B")
    muted = HexColor("#66727F")
    green = HexColor("#16855B")
    blue = HexColor("#2878B5")
    line = HexColor("#D7DDE3")

    page.setFillColor(green)
    page.rect(0, height - 12, width, 12, fill=1, stroke=0)
    page.setFillColor(ink)
    page.setFont("Helvetica-Bold", 22)
    page.drawString(48, height - 64, "Quarterly Operations Review - Q2 2026")
    page.setFillColor(muted)
    page.setFont("Helvetica", 10)
    page.drawString(48, height - 84, "Synthetic demo document | Safe to redistribute | Generated locally")

    metrics = [
        ("DOCUMENTS", "1,284", "+18%"),
        ("SUCCESS RATE", "98.7%", "+1.4 pts"),
        ("REVIEW TIME", "48 hours", "-31%"),
    ]
    card_y = height - 170
    card_w = 160
    for index, (label, value, delta) in enumerate(metrics):
        x = 48 + index * 174
        page.setStrokeColor(line)
        page.roundRect(x, card_y, card_w, 64, 4, fill=0, stroke=1)
        page.setFillColor(muted)
        page.setFont("Helvetica-Bold", 8)
        page.drawString(x + 12, card_y + 45, label)
        page.setFillColor(ink)
        page.setFont("Helvetica-Bold", 18)
        page.drawString(x + 12, card_y + 20, value)
        page.setFillColor(green)
        page.setFont("Helvetica", 8)
        page.drawRightString(x + card_w - 12, card_y + 24, delta)

    page.setFillColor(ink)
    page.setFont("Helvetica-Bold", 12)
    page.drawString(48, height - 224, "Conversion quality")
    page.setStrokeColor(line)
    page.line(48, height - 234, width - 48, height - 234)

    rows = [
        ("Layout fidelity", "Validated", "Page geometry and visual structure retained"),
        ("Editable text", "Validated", "Searchable Word text boxes created"),
        ("Privacy", "Local", "No document upload or cloud conversion"),
        ("Agent support", "Portable", "Codex, Claude Code, and Agent Skills"),
    ]
    columns = [48, 210, 310, width - 48]
    row_top = height - 260
    page.setFont("Helvetica-Bold", 8)
    page.setFillColor(muted)
    page.drawString(columns[0], row_top, "CHECK")
    page.drawString(columns[1], row_top, "RESULT")
    page.drawString(columns[2], row_top, "DETAIL")
    page.setStrokeColor(line)
    page.line(columns[0], row_top - 8, columns[-1], row_top - 8)
    for index, (check, result, detail) in enumerate(rows):
        y = row_top - 34 - index * 38
        page.setFillColor(ink)
        page.setFont("Helvetica-Bold", 9)
        page.drawString(columns[0], y, check)
        page.setFillColor(green if result in {"Validated", "Local"} else blue)
        page.setFont("Helvetica-Bold", 9)
        page.drawString(columns[1], y, result)
        page.setFillColor(ink)
        page.setFont("Helvetica", 9)
        page.drawString(columns[2], y, detail)
        page.setStrokeColor(line)
        page.line(columns[0], y - 12, columns[-1], y - 12)

    chart_x, chart_y, chart_w, chart_h = 48, 126, 370, 145
    page.setFillColor(ink)
    page.setFont("Helvetica-Bold", 12)
    page.drawString(chart_x, chart_y + chart_h + 20, "Documents processed")
    page.setStrokeColor(line)
    for step in range(4):
        y = chart_y + step * chart_h / 3
        page.line(chart_x, y, chart_x + chart_w, y)
    values = [38, 52, 61, 78, 91, 112]
    points: list[tuple[float, float]] = []
    for index, value in enumerate(values):
        x = chart_x + index * chart_w / (len(values) - 1)
        y = chart_y + (value / 120) * chart_h
        points.append((x, y))
    page.setStrokeColor(blue)
    page.setLineWidth(2)
    for first, second in zip(points, points[1:]):
        page.line(first[0], first[1], second[0], second[1])
    page.setFillColor(blue)
    for x, y in points:
        page.circle(x, y, 3, fill=1, stroke=0)
    page.setFillColor(muted)
    page.setFont("Helvetica", 8)
    for index, month in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun")):
        x = chart_x + index * chart_w / 5
        page.drawCentredString(x, chart_y - 14, month)

    qr_x, qr_y, cell = 462, 142, 5
    pattern = (
        "1111111010101",
        "1000001011101",
        "1011101010001",
        "1011101010111",
        "1011101010101",
        "1000001011101",
        "1111111010101",
        "0000000010000",
        "1010111110101",
        "0111010011110",
        "1010111010101",
        "1101000111010",
        "1011111010111",
    )
    page.setFillColor(ink)
    for row, bits in enumerate(pattern):
        for column, bit in enumerate(bits):
            if bit == "1":
                page.rect(qr_x + column * cell, qr_y + (len(pattern) - row) * cell, cell, cell, fill=1, stroke=0)
    page.setFont("Helvetica-Bold", 8)
    page.drawCentredString(qr_x + 32, qr_y - 2, "LOCAL ONLY")

    page.setStrokeColor(line)
    page.line(48, 70, width - 48, 70)
    page.setFillColor(muted)
    page.setFont("Helvetica", 8)
    page.drawString(48, 52, "Generated by pdf-to-editable-word-skill | github.com/longligooo/pdf-to-editable-word-skill")
    page.drawRightString(width - 48, 52, "1 / 1")
    page.save()


def edit_docx(source: Path, target: Path) -> None:
    replacements = {"Q2 2026": "Q3 2026", "48 hours": "24 hours"}
    with zipfile.ZipFile(source) as input_docx, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as output_docx:
        for item in input_docx.infolist():
            data = input_docx.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                for text_node in root.iter(f"{W}t"):
                    value = text_node.text or ""
                    for old, new in replacements.items():
                        value = value.replace(old, new)
                    text_node.text = value
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            output_docx.writestr(item, data)


def main() -> None:
    examples = ROOT / "examples"
    examples.mkdir(parents=True, exist_ok=True)
    source_pdf = examples / "demo-source.pdf"
    output_docx = examples / "demo-output.docx"
    edited_docx = examples / "demo-edited.docx"
    draw_demo_pdf(source_pdf)
    with tempfile.TemporaryDirectory(prefix="pdf2word-demo-") as work:
        convert_pdf(
            source_pdf,
            output_docx,
            work_dir=Path(work),
            dpi=144,
            pdftoppm=Path(os.environ["PDFTOPPM"]) if os.environ.get("PDFTOPPM") else None,
        )
    edit_docx(output_docx, edited_docx)
    print(f"Created {source_pdf}")
    print(f"Created {output_docx}")
    print(f"Created {edited_docx}")


if __name__ == "__main__":
    main()
