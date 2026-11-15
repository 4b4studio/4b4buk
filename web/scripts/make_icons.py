#!/usr/bin/env python3
"""Render the placeholder app icons (requires Pillow and the DejaVu Sans Bold font).

The icon is a provisional placeholder until the owner approves a final mark.
Usage: python web/scripts/make_icons.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "public" / "icons"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG, FG, ACCENT = (15, 61, 46), (236, 244, 239), (95, 211, 141)

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="4b4buk">
  <rect width="512" height="512" rx="112" fill="#0f3d2e"/>
  <circle cx="256" cy="256" r="176" fill="none" stroke="#5fd38d" stroke-width="18"/>
  <text x="256" y="226" text-anchor="middle" font-family="DejaVu Sans, Verdana, sans-serif" font-weight="700" font-size="92" fill="#ecf4ef">4b4</text>
  <text x="256" y="336" text-anchor="middle" font-family="DejaVu Sans, Verdana, sans-serif" font-weight="700" font-size="104" fill="#5fd38d">buk</text>
</svg>
"""


def render(size: int, padding: float, rounded: bool) -> Image.Image:
    image = Image.new("RGBA", (size, size), BG + (255,) if not rounded else (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if rounded:
        draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * 0.22), fill=BG)
    inner = size * (1 - 2 * padding)
    centre = size / 2
    radius = inner * 0.344
    width = max(2, int(size * 0.035))
    draw.ellipse((centre - radius, centre - radius, centre + radius, centre + radius), outline=ACCENT, width=width)
    top = ImageFont.truetype(FONT, int(inner * 0.18))
    bottom = ImageFont.truetype(FONT, int(inner * 0.2))
    draw.text((centre, centre - inner * 0.06), "4b4", font=top, fill=FG, anchor="ms")
    draw.text((centre, centre + inner * 0.16), "buk", font=bottom, fill=ACCENT, anchor="ms")
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "icon.svg").write_text(SVG, encoding="utf-8")
    render(192, 0.0, True).save(OUT / "icon-192.png")
    render(512, 0.0, True).save(OUT / "icon-512.png")
    render(512, 0.1, False).save(OUT / "icon-maskable-512.png")  # full-bleed, content in the safe zone
    render(180, 0.0, False).convert("RGB").save(OUT / "apple-touch-icon.png")


if __name__ == "__main__":
    main()
