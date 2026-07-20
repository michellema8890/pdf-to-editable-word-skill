from __future__ import annotations

import hashlib
import html
import json
import os
import posixpath
import shutil
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

import pdfplumber
from PIL import Image, ImageDraw


TWIPS_PER_PT = 20


@dataclass(frozen=True)
class WordBox:
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    size: float
    color: str
    bold: bool
    font: str


def clean_text(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\u3000", " ")
    if not text.strip():
        return ""
    compact = text.replace(" ", "")
    if compact and len(compact) % 2 == 0:
        half = len(compact) // 2
        if compact[:half] == compact[half:]:
            return compact[:half]
    return text


def _is_light_color(color: object) -> bool:
    if color is None:
        return False
    try:
        vals = tuple(float(value) for value in color)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    if len(vals) >= 4:
        c, m, y, k = vals[:4]
        if k > 0.45:
            return False
        r = 1 - min(1, c + k)
        g = 1 - min(1, m + k)
        b = 1 - min(1, y + k)
    else:
        r, g, b = (vals + (0.0, 0.0, 0.0))[:3]
    return (r + g + b) / 3 > 0.68


def _word_color(color: object) -> str:
    return "FFFFFF" if _is_light_color(color) else "000000"


def _font_name(fontname: str | None, bold: bool) -> str:
    if not fontname:
        return "SimSun"
    name = fontname.split("+")[-1].strip()
    lowered = name.lower()
    if "hei" in lowered:
        return "SimHei"
    if "song" in lowered or "simsun" in lowered:
        return "SimSun"
    if "kai" in lowered:
        return "KaiTi"
    if "fang" in lowered:
        return "FangSong"
    return name[:80] or ("Arial" if bold else "SimSun")


def normalize_page_words(page, x_tolerance: float = 2.0, y_tolerance: float = 3.0) -> list[WordBox]:
    words = page.extract_words(
        keep_blank_chars=True,
        x_tolerance=x_tolerance,
        y_tolerance=y_tolerance,
        use_text_flow=False,
        extra_attrs=["fontname", "size", "non_stroking_color"],
    )
    boxes: list[WordBox] = []
    seen: set[tuple] = set()
    for word in words:
        text = clean_text(word.get("text", ""))
        if not text:
            continue
        x0, top, x1, bottom = (float(word[key]) for key in ("x0", "top", "x1", "bottom"))
        size = float(word.get("size") or max(8.0, bottom - top))
        font_source = str(word.get("fontname") or "")
        bold = "bold" in font_source.lower()
        key = (text, round(x0, 2), round(top, 2), round(x1, 2), round(bottom, 2), round(size, 2))
        if key in seen:
            continue
        seen.add(key)
        boxes.append(
            WordBox(
                text=text,
                x0=x0,
                top=top,
                x1=x1,
                bottom=bottom,
                size=size,
                color=_word_color(word.get("non_stroking_color")),
                bold=bold,
                font=_font_name(font_source, bold),
            )
        )
    return boxes


def inspect_pdf(pdf_path: Path) -> dict:
    pdf_path = pdf_path.resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    sizes: list[list[float]] = []
    text_layer_pages = 0
    character_count = 0
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            sizes.append([round(float(page.width), 2), round(float(page.height), 2)])
            count = len(page.chars)
            character_count += count
            if count:
                text_layer_pages += 1
    unique_sizes = sorted({tuple(size) for size in sizes})
    pages_without_text = len(sizes) - text_layer_pages
    return {
        "path": str(pdf_path),
        "pages": len(sizes),
        "text_layer_pages": text_layer_pages,
        "pages_without_text": pages_without_text,
        "characters": character_count,
        "page_sizes_pt": [list(size) for size in unique_sizes],
        "mixed_page_sizes": len(unique_sizes) > 1,
        "conversion_ready": bool(sizes) and text_layer_pages > 0 and len(unique_sizes) == 1,
        "all_pages_have_editable_text": pages_without_text == 0,
    }


def find_pdftoppm(explicit: Path | None = None) -> Path:
    candidates: list[str] = []
    if explicit:
        candidates.append(str(explicit))
    if os.environ.get("PDFTOPPM"):
        candidates.append(os.environ["PDFTOPPM"])
    discovered = shutil.which("pdftoppm")
    if discovered:
        candidates.append(discovered)
    for candidate in candidates:
        path = Path(candidate).expanduser().resolve()
        if path.is_file():
            return path
    raise FileNotFoundError(
        "pdftoppm was not found. Install Poppler, add pdftoppm to PATH, "
        "set PDFTOPPM, or pass --pdftoppm."
    )


def _render_page(
    pdf_path: Path,
    page_index: int,
    dpi: int,
    scratch_dir: Path,
    pdftoppm: Path,
    retries: int = 3,
) -> Image.Image:
    scratch_dir.mkdir(parents=True, exist_ok=True)
    prefix = scratch_dir / f"render_{page_index + 1:05d}"
    out_png = prefix.with_suffix(".png")
    out_png.unlink(missing_ok=True)
    command = [
        str(pdftoppm),
        "-r",
        str(dpi),
        "-png",
        "-singlefile",
        "-f",
        str(page_index + 1),
        "-l",
        str(page_index + 1),
        str(pdf_path),
        str(prefix),
    ]
    last_error = ""
    for attempt in range(1, retries + 1):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0 and out_png.is_file() and out_png.stat().st_size:
            with Image.open(out_png) as source:
                image = source.convert("RGB")
                image.load()
            out_png.unlink(missing_ok=True)
            return image
        last_error = (result.stderr or result.stdout or f"exit code {result.returncode}").strip()
        out_png.unlink(missing_ok=True)
        if attempt < retries:
            time.sleep(0.25 * attempt)
    raise RuntimeError(f"Poppler failed on page {page_index + 1}: {last_error}")


def _render_textless_background(
    pdf_path: Path,
    page_index: int,
    boxes: Iterable[WordBox],
    png_path: Path,
    dpi: int,
    scratch_dir: Path,
    pdftoppm: Path,
) -> None:
    scale = dpi / 72.0
    image = _render_page(pdf_path, page_index, dpi, scratch_dir, pdftoppm)
    try:
        draw = ImageDraw.Draw(image)
        for box in boxes:
            pad = max(1, int(round(box.size * scale * 0.12)))
            bounds = (
                int(round(box.x0 * scale)) - pad,
                int(round(box.top * scale)) - pad,
                int(round(box.x1 * scale)) + pad,
                int(round(box.bottom * scale)) + pad,
            )
            fill = (0, 0, 0) if box.color == "FFFFFF" else (255, 255, 255)
            draw.rectangle(bounds, fill=fill)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(png_path, optimize=True)
    finally:
        image.close()


def _esc_attr(value: str) -> str:
    return html.escape(value, quote=True)


def _esc_text(value: str) -> str:
    return html.escape(value, quote=False)


def _pt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _twips(value: float) -> int:
    return int(round(value * TWIPS_PER_PT))


def _background_shape(page_no: int, rel_id: str, width_pt: float, height_pt: float) -> str:
    return (
        f'<w:r><w:pict><v:shape id="bg{page_no}" type="#_x0000_t75" '
        f'style="position:absolute;margin-left:0pt;margin-top:0pt;width:{_pt(width_pt)}pt;'
        f'height:{_pt(height_pt)}pt;z-index:-251654144;mso-position-horizontal-relative:page;'
        f'mso-position-vertical-relative:page" o:allowincell="f" stroked="f">'
        f'<v:imagedata r:id="{rel_id}" o:title="page{page_no:04d}"/>'
        f'</v:shape></w:pict></w:r>'
    )


def _textbox_shape(page_no: int, box_no: int, box: WordBox) -> str:
    box_width = box.x1 - box.x0
    box_height = box.bottom - box.top
    font_size = max(4.0, box.size)
    if box_height > 0 and font_size > box_height * 1.35:
        font_size = box_height * 1.12
    align = "center" if box.color == "FFFFFF" or len(box.text) <= 1 else "left"
    estimated_width = sum(font_size * (0.58 if ord(char) < 128 else 1.02) for char in box.text)
    if align == "center":
        width = max(box_width + font_size * 0.35, estimated_width + font_size * 0.95)
        left = (box.x0 + box.x1 - width) / 2.0
    else:
        width = max(box_width + font_size * 2.2, estimated_width + font_size * 2.2)
        left = box.x0 - 0.2
    height = max(box_height + font_size * 0.35, font_size * 1.35)
    top = box.top - max(0.5, font_size * 0.10)
    bold_tag = "<w:b/>" if box.bold else ""
    xml_space = ' xml:space="preserve"' if box.text.startswith(" ") or box.text.endswith(" ") else ""
    half_points = max(2, int(round(font_size * 2)))
    line_height = max(1, _twips(font_size * 1.03))
    return (
        f'<w:r><w:pict><v:shape id="tb{page_no}_{box_no}" type="#_x0000_t202" '
        f'style="position:absolute;margin-left:{_pt(left)}pt;margin-top:{_pt(top)}pt;'
        f'width:{_pt(width)}pt;height:{_pt(height)}pt;z-index:251657216;'
        f'mso-position-horizontal-relative:page;mso-position-vertical-relative:page" '
        f'filled="f" stroked="f" o:allowincell="f"><v:textbox inset="0,0,0,0" '
        f'style="mso-fit-shape-to-text:t"><w:txbxContent><w:p><w:pPr>'
        f'<w:spacing w:before="0" w:after="0" w:line="{line_height}" w:lineRule="exact"/>'
        f'<w:ind w:left="0" w:right="0" w:firstLine="0"/><w:jc w:val="{align}"/>'
        f'</w:pPr><w:r><w:rPr><w:rFonts w:ascii="{_esc_attr(box.font)}" '
        f'w:hAnsi="{_esc_attr(box.font)}" w:eastAsia="{_esc_attr(box.font)}" '
        f'w:cs="{_esc_attr(box.font)}"/>{bold_tag}<w:color w:val="{box.color}"/>'
        f'<w:sz w:val="{half_points}"/><w:szCs w:val="{half_points}"/>'
        f'</w:rPr><w:t{xml_space}>{_esc_text(box.text)}</w:t></w:r></w:p></w:txbxContent>'
        f'</v:textbox></v:shape></w:pict></w:r>'
    )


def _page_paragraph(
    page_no: int,
    rel_id: str,
    width_pt: float,
    height_pt: float,
    boxes: list[WordBox],
    break_after: bool,
) -> str:
    runs = [_background_shape(page_no, rel_id, width_pt, height_pt)]
    runs.extend(_textbox_shape(page_no, index, box) for index, box in enumerate(boxes, 1))
    if break_after:
        runs.append('<w:r><w:br w:type="page"/></w:r>')
    return (
        '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="1" w:lineRule="exact"/>'
        '<w:ind w:left="0" w:right="0" w:firstLine="0"/></w:pPr>'
        + "".join(runs)
        + "</w:p>"
    )


def _content_types() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="png" ContentType="image/png"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        '</Types>'
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )


def _document_rels(image_names: list[str]) -> str:
    items = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for index, name in enumerate(image_names, 1):
        items.append(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="media/{_esc_attr(name)}"/>'
        )
    items.append("</Relationships>")
    return "".join(items)


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr><w:rPr>'
        '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="SimSun" w:cs="Arial"/><w:sz w:val="24"/>'
        '</w:rPr></w:style></w:styles>'
    )


def _settings_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:zoom w:percent="100"/><w:displayBackgroundShape/></w:settings>'
    )


def _document_header() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:xml="http://www.w3.org/XML/1998/namespace"><w:body>'
    )


def _document_footer(width_pt: float, height_pt: float) -> str:
    orientation = ' w:orient="landscape"' if width_pt > height_pt else ""
    return (
        f'<w:sectPr><w:pgSz w:w="{_twips(width_pt)}" w:h="{_twips(height_pt)}"{orientation}/>'
        '<w:pgMar w:top="0" w:right="0" w:bottom="0" w:left="0" w:header="0" w:footer="0" w:gutter="0"/>'
        '<w:cols w:space="0"/><w:docGrid w:linePitch="360"/></w:sectPr></w:body></w:document>'
    )


def _fingerprint(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = path.stat()
    return {"sha256": digest.hexdigest(), "size": stat.st_size}


def _prepare_cache(
    pdf_path: Path,
    work_dir: Path,
    dpi: int,
    selected_pages: list[int],
    resume: bool,
) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    images_dir = work_dir / "media"
    manifest_path = work_dir / "manifest.json"
    manifest = {
        "version": 1,
        "source": _fingerprint(pdf_path),
        "dpi": dpi,
        "pages": selected_pages,
    }
    if resume and manifest_path.is_file():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise RuntimeError("The work directory manifest does not match this PDF or conversion range.")
    elif resume and images_dir.exists() and any(images_dir.iterdir()):
        raise RuntimeError("The work directory contains cached pages but no trustworthy manifest.")
    else:
        if images_dir.exists():
            shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return images_dir


def convert_pdf(
    pdf_path: Path,
    out_docx: Path,
    *,
    work_dir: Path,
    dpi: int = 144,
    start: int = 0,
    end: int | None = None,
    resume: bool = False,
    pdftoppm: Path | None = None,
) -> dict:
    pdf_path = pdf_path.expanduser().resolve()
    out_docx = out_docx.expanduser().resolve()
    work_dir = work_dir.expanduser().resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    if dpi < 72 or dpi > 600:
        raise ValueError("dpi must be between 72 and 600")
    poppler = find_pdftoppm(pdftoppm)

    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)
        end_page = page_count if end is None else min(end, page_count)
        selected = list(range(max(0, start), end_page))
        if not selected:
            raise ValueError("No pages selected")
        sizes = {(round(float(pdf.pages[index].width), 2), round(float(pdf.pages[index].height), 2)) for index in selected}
        if len(sizes) != 1:
            raise ValueError("Mixed page sizes are not supported in v0.1")
        width_pt, height_pt = next(iter(sizes))
        images_dir = _prepare_cache(pdf_path, work_dir, dpi, selected, resume)
        body_path = work_dir / "document_body.xml"
        image_names: list[str] = []
        total_boxes = 0
        with body_path.open("w", encoding="utf-8", newline="") as body:
            for output_index, page_index in enumerate(selected, 1):
                page = pdf.pages[page_index]
                boxes = normalize_page_words(page)
                image_name = f"page_{page_index + 1:05d}.png"
                image_path = images_dir / image_name
                if resume and image_path.is_file() and image_path.stat().st_size:
                    cache_status = "reused"
                else:
                    _render_textless_background(
                        pdf_path,
                        page_index,
                        boxes,
                        image_path,
                        dpi,
                        work_dir / "scratch",
                        poppler,
                    )
                    cache_status = "rendered"
                image_names.append(image_name)
                total_boxes += len(boxes)
                body.write(
                    _page_paragraph(
                        output_index,
                        f"rId{output_index}",
                        width_pt,
                        height_pt,
                        boxes,
                        break_after=output_index != len(selected),
                    )
                )
                print(
                    f"page {page_index + 1}/{page_count}: {len(boxes)} editable text boxes ({cache_status})",
                    flush=True,
                )

    if total_boxes == 0:
        raise ValueError("The selected pages contain no extractable text; OCR is not available in v0.1")

    out_docx.parent.mkdir(parents=True, exist_ok=True)
    out_docx.unlink(missing_ok=True)
    with zipfile.ZipFile(out_docx, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("[Content_Types].xml", _content_types())
        archive.writestr("_rels/.rels", _root_rels())
        with archive.open("word/document.xml", "w") as document:
            document.write(_document_header().encode("utf-8"))
            with body_path.open("rb") as body:
                shutil.copyfileobj(body, document)
            document.write(_document_footer(width_pt, height_pt).encode("utf-8"))
        archive.writestr("word/styles.xml", _styles_xml())
        archive.writestr("word/settings.xml", _settings_xml())
        archive.writestr("word/_rels/document.xml.rels", _document_rels(image_names))
        for image_name in image_names:
            archive.write(images_dir / image_name, posixpath.join("word/media", image_name))

    validation = validate_docx(out_docx)
    if not validation["valid"]:
        raise RuntimeError(f"Generated DOCX failed validation: {validation}")
    return {
        "output": str(out_docx),
        "pages": len(selected),
        "editable_text_boxes": total_boxes,
        "background_images": len(image_names),
        "work_dir": str(work_dir),
    }


def validate_docx(docx_path: Path, pdf_path: Path | None = None) -> dict:
    docx_path = docx_path.expanduser().resolve()
    if not docx_path.is_file():
        raise FileNotFoundError(docx_path)
    required = {
        "[Content_Types].xml",
        "_rels/.rels",
        "word/document.xml",
        "word/_rels/document.xml.rels",
    }
    with zipfile.ZipFile(docx_path) as archive:
        names = set(archive.namelist())
        missing = sorted(required - names)
        if missing:
            return {"valid": False, "missing_parts": missing}
        root = ET.fromstring(archive.read("word/document.xml"))
        shape_tag = "{urn:schemas-microsoft-com:vml}shape"
        text_tag = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
        shape_ids = [element.attrib.get("id", "") for element in root.iter(shape_tag)]
        background_count = sum(shape_id.startswith("bg") for shape_id in shape_ids)
        text_box_count = sum(shape_id.startswith("tb") for shape_id in shape_ids)
        text = "".join((element.text or "") for element in root.iter(text_tag))
        media_count = sum(name.startswith("word/media/") and name.lower().endswith(".png") for name in names)
    result = {
        "valid": background_count > 0 and background_count == media_count and text_box_count > 0,
        "pages": background_count,
        "background_images": media_count,
        "editable_text_boxes": text_box_count,
        "editable_characters": len(text),
        "file_size": docx_path.stat().st_size,
    }
    if pdf_path is not None:
        source = inspect_pdf(pdf_path)
        result["source_pages"] = source["pages"]
        result["page_count_matches_source"] = source["pages"] == background_count
        result["valid"] = result["valid"] and result["page_count_matches_source"]
    return result
