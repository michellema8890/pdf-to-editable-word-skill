from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / "demo"
ASSETS = ROOT / "assets"
CANVAS = (1400, 820)
PAGE_SIZE = (430, 556)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def fit_page(path: Path) -> Image.Image:
    with Image.open(path) as source:
        page = source.convert("RGB")
        page.thumbnail(PAGE_SIZE, Image.Resampling.LANCZOS)
        return page.copy()


def page_panel(canvas: Image.Image, page: Image.Image, x: int, y: int, label: str, accent: tuple[int, int, int]) -> tuple[int, int, int, int]:
    draw = ImageDraw.Draw(canvas)
    label_font = load_font(17, bold=True)
    shadow = (x + 7, y + 45 + 9, x + page.width + 7, y + 45 + page.height + 9)
    draw.rounded_rectangle(shadow, radius=5, fill=(218, 223, 227))
    draw.rounded_rectangle((x, y, x + page.width, y + 34), radius=5, fill=accent)
    draw.rectangle((x, y + 25, x + page.width, y + 34), fill=accent)
    label_box = draw.textbbox((0, 0), label, font=label_font)
    label_width = label_box[2] - label_box[0]
    draw.text((x + (page.width - label_width) / 2, y + 6), label, fill="white", font=label_font)
    canvas.paste(page, (x, y + 34))
    draw.rectangle((x, y + 34, x + page.width - 1, y + 34 + page.height - 1), outline=(205, 211, 216), width=1)
    return (x, y + 34, x + page.width, y + 34 + page.height)


def build_frame(source: Image.Image, target: Image.Image, edited: bool) -> Image.Image:
    frame = Image.new("RGB", CANVAS, (246, 248, 249))
    draw = ImageDraw.Draw(frame)
    title_font = load_font(34, bold=True)
    body_font = load_font(18)
    small_font = load_font(15)
    green = (22, 133, 91)
    blue = (40, 120, 181)
    ink = (23, 33, 43)
    muted = (94, 106, 117)

    title = "PDF TO EDITABLE WORD - PORTABLE AGENT SKILL"
    title_box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((CANVAS[0] - (title_box[2] - title_box[0])) / 2, 28), title, fill=ink, font=title_font)
    subtitle = "Layout preserved" if not edited else "Text edited in Word: Q2 -> Q3 and 48 -> 24 hours"
    subtitle_box = draw.textbbox((0, 0), subtitle, font=body_font)
    draw.text(((CANVAS[0] - (subtitle_box[2] - subtitle_box[0])) / 2, 76), subtitle, fill=green if edited else muted, font=body_font)

    left_bounds = page_panel(frame, source, 185, 120, "SOURCE PDF", (38, 50, 61))
    right_label = "EDITED DOCX" if edited else "EDITABLE DOCX"
    right_bounds = page_panel(frame, target, 785, 120, right_label, green)

    arrow_y = 410
    draw.line((652, arrow_y, 744, arrow_y), fill=blue, width=7)
    draw.polygon(((744, arrow_y), (723, arrow_y - 15), (723, arrow_y + 15)), fill=blue)

    if edited:
        right_x, right_y, right_edge, _ = right_bounds
        page_width = right_edge - right_x
        scale = page_width / 1020
        draw.rounded_rectangle(
            (right_x + int(72 * scale), right_y + int(70 * scale), right_x + int(770 * scale), right_y + int(115 * scale)),
            radius=4,
            outline=(255, 178, 36),
            width=5,
        )
        draw.rounded_rectangle(
            (right_x + int(660 * scale), right_y + int(205 * scale), right_x + int(885 * scale), right_y + int(265 * scale)),
            radius=4,
            outline=(255, 178, 36),
            width=5,
        )

    footer = "LOCAL & PRIVATE  |  CODEX  |  CLAUDE CODE  |  AGENT SKILLS"
    footer_box = draw.textbbox((0, 0), footer, font=small_font)
    draw.text(((CANVAS[0] - (footer_box[2] - footer_box[0])) / 2, 780), footer, fill=muted, font=small_font)
    return frame


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    source = fit_page(TMP / "source.png")
    output = fit_page(TMP / "output.png")
    edited = fit_page(TMP / "edited.png")
    layout_frame = build_frame(source, output, edited=False)
    edited_frame = build_frame(source, edited, edited=True)
    layout_frame.save(ASSETS / "demo-preview.png", optimize=True)
    layout_frame.save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=[edited_frame],
        duration=[1800, 2200],
        loop=0,
        optimize=True,
    )
    print(f"Created {ASSETS / 'demo-preview.png'}")
    print(f"Created {ASSETS / 'demo.gif'}")


if __name__ == "__main__":
    main()
