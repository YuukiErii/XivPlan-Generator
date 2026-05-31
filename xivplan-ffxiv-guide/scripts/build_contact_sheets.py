#!/usr/bin/env python3
"""Build PNG contact sheets from visual-regression step exports."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "artifacts" / "phase-i-visual-regression"
DEFAULT_OUTPUT = ROOT / "artifacts" / "phase-m-visual-review" / "contact-sheets"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.strip().lower(), flags=re.UNICODE)
    return re.sub(r"-+", "-", cleaned).strip("-") or "case"


def discover_cases(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.iterdir() if path.is_dir() and (path / "manifest.json").exists())


def step_image_path(case_dir: Path, image_ref: str) -> Path:
    return case_dir / Path(image_ref.replace("/", "\\"))


def fit_image(image: Image.Image, size: int) -> Image.Image:
    image = image.convert("RGBA")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), "#111318")
    x = (size - image.width) // 2
    y = (size - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    return canvas


def draw_wrapped_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, max_width: int, face: ImageFont.ImageFont) -> None:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=face)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = xy
    for line in lines[:2]:
        draw.text((x, y), line, font=face, fill="#f5f7fb")
        y += 18


def build_contact_sheet(case_dir: Path, output_path: Path, columns: int, thumb_size: int) -> dict[str, Any]:
    manifest = read_json(case_dir / "manifest.json")
    steps = manifest.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{case_dir}: manifest has no steps")

    title_height = 48
    cell_gap = 18
    outer = 26
    rows = math.ceil(len(steps) / columns)
    cell_width = thumb_size
    cell_height = thumb_size + title_height
    width = outer * 2 + columns * cell_width + (columns - 1) * cell_gap
    height = outer * 2 + rows * cell_height + (rows - 1) * cell_gap + 42
    sheet = Image.new("RGBA", (width, height), "#0f1117")
    draw = ImageDraw.Draw(sheet)
    title_face = font(20)
    small_face = font(14)
    draw.text((outer, outer), case_dir.name, font=title_face, fill="#ffffff")

    checked_images: list[str] = []
    for idx, item in enumerate(steps):
        row = idx // columns
        col = idx % columns
        x = outer + col * (cell_width + cell_gap)
        y = outer + 42 + row * (cell_height + cell_gap)
        image_path = step_image_path(case_dir, str(item.get("image", "")))
        with Image.open(image_path) as source:
            thumb = fit_image(source, thumb_size)
        sheet.alpha_composite(thumb, (x, y + title_height))
        draw.rounded_rectangle([x, y, x + cell_width, y + title_height + thumb_size], radius=8, outline="#3f4758", width=2)
        label = f"{item.get('step', idx + 1):02d} {item.get('title', '')}"
        draw_wrapped_text(draw, (x + 8, y + 8), str(label), cell_width - 16, small_face)
        checked_images.append(str(image_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output_path)
    return {"case": case_dir.name, "steps": len(steps), "contact_sheet": str(output_path), "images": checked_images}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build contact-sheet PNGs for visual-regression cases.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--thumb-size", type=int, default=260)
    args = parser.parse_args()

    cases = discover_cases(args.input_dir)
    if not cases:
        print(f"ERROR: no cases with manifest.json under {args.input_dir}")
        return 2

    payload = []
    for case_dir in cases:
        output_path = args.output_dir / f"{slugify(case_dir.name)}.png"
        payload.append(build_contact_sheet(case_dir, output_path, args.columns, args.thumb_size))
        print(f"Wrote {output_path}")
    manifest_path = args.output_dir.parent / "contact-sheet-manifest.json"
    write_json(manifest_path, {"cases": payload})
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
