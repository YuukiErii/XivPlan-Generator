#!/usr/bin/env python3
"""Build focused enemy and party identity crop sheets from visual regression exports."""

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
DEFAULT_OUTPUT = ROOT / "artifacts" / "phase-s-release-gate" / "identity-crop-sheets"
CANVAS_SIZE = 720
CENTER = CANVAS_SIZE // 2
SCALE = 0.9
ENEMY_CASES = {"multi-boss-add-identity", "known-encounter-boss-asset"}
PARTY_CASES = {"job-specific-positioning", "party-stack-label-omission"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def font(size: int) -> ImageFont.ImageFont:
    for candidate in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.strip().lower(), flags=re.UNICODE)
    return re.sub(r"-+", "-", cleaned).strip("-") or "case"


def image_path(case_dir: Path, image_ref: str) -> Path:
    return case_dir / Path(image_ref.replace("/", "\\"))


def scene_xy(obj: dict[str, Any], scale: int = 1) -> tuple[float, float]:
    return (CENTER + float(obj.get("x", 0)) * SCALE) * scale, (CENTER - float(obj.get("y", 0)) * SCALE) * scale


def object_box(obj: dict[str, Any], scale: int = 1, pad: int = 30) -> tuple[int, int, int, int]:
    cx, cy = scene_xy(obj, scale)
    radius = obj.get("radius")
    half_w = float(radius if isinstance(radius, (int, float)) else 28) * SCALE * scale
    half_h = half_w
    if isinstance(obj.get("width"), (int, float)):
        half_w = max(half_w, float(obj["width"]) * SCALE * scale / 2)
    if isinstance(obj.get("height"), (int, float)):
        half_h = max(half_h, float(obj["height"]) * SCALE * scale / 2)
    if obj.get("type") == "text":
        text = str(obj.get("text", ""))
        font_size = float(obj.get("fontSize", 14) or 14)
        half_w = max(half_w, len(text) * font_size * 0.32 * scale)
        half_h = max(half_h, font_size * 0.85 * scale)
    return round(cx - half_w - pad), round(cy - half_h - pad), round(cx + half_w + pad), round(cy + half_h + pad)


def union_box(boxes: list[tuple[int, int, int, int]], image_size: tuple[int, int]) -> tuple[int, int, int, int]:
    if not boxes:
        return 0, 0, image_size[0], image_size[1]
    left = max(0, min(box[0] for box in boxes))
    top = max(0, min(box[1] for box in boxes))
    right = min(image_size[0], max(box[2] for box in boxes))
    bottom = min(image_size[1], max(box[3] for box in boxes))
    if right - left < 120:
        extra = (120 - (right - left)) // 2
        left = max(0, left - extra)
        right = min(image_size[0], right + extra)
    if bottom - top < 120:
        extra = (120 - (bottom - top)) // 2
        top = max(0, top - extra)
        bottom = min(image_size[1], bottom + extra)
    return left, top, right, bottom


def fit_crop(source: Image.Image, box: tuple[int, int, int, int], size: int) -> Image.Image:
    crop = source.crop(box).convert("RGBA")
    crop.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), "#111318")
    canvas.alpha_composite(crop, ((size - crop.width) // 2, (size - crop.height) // 2))
    return canvas


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, max_width: int, face: ImageFont.ImageFont) -> None:
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
    for line in lines[:3]:
        draw.text((x, y), line, font=face, fill="#f5f7fb")
        y += 17


def build_sheet(crops: list[dict[str, Any]], output_path: Path, title: str, columns: int = 4, crop_size: int = 180) -> dict[str, Any]:
    if not crops:
        return {"path": str(output_path), "crops": 0, "skipped": True}
    title_height = 46
    cell_gap = 16
    outer = 24
    label_height = 62
    rows = math.ceil(len(crops) / columns)
    width = outer * 2 + columns * crop_size + (columns - 1) * cell_gap
    height = outer * 2 + 38 + rows * (title_height + crop_size + label_height) + (rows - 1) * cell_gap
    sheet = Image.new("RGBA", (width, height), "#0f1117")
    draw = ImageDraw.Draw(sheet)
    title_face = font(20)
    label_face = font(13)
    draw.text((outer, outer), title, font=title_face, fill="#ffffff")

    for idx, item in enumerate(crops):
        row = idx // columns
        col = idx % columns
        x = outer + col * (crop_size + cell_gap)
        y = outer + 38 + row * (title_height + crop_size + label_height + cell_gap)
        sheet.alpha_composite(item["image"], (x, y + title_height))
        draw.rounded_rectangle([x, y, x + crop_size, y + title_height + crop_size + label_height], radius=8, outline="#3f4758", width=2)
        draw_wrapped(draw, (x + 8, y + 8), str(item["label"]), crop_size - 16, label_face)
        draw_wrapped(draw, (x + 8, y + title_height + crop_size + 8), str(item.get("note", "")), crop_size - 16, label_face)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output_path)
    return {"path": str(output_path), "crops": len(crops), "skipped": False}


def enemy_crops(case_dir: Path, crop_size: int) -> list[dict[str, Any]]:
    scene = read_json(case_dir / "scene.xivplan")
    manifest = read_json(case_dir / "manifest.json")
    steps = manifest.get("steps", [])
    crops: list[dict[str, Any]] = []
    for index, step in enumerate(scene.get("steps", []), start=1):
        if index > len(steps):
            continue
        with Image.open(image_path(case_dir, str(steps[index - 1].get("image", "")))) as source:
            image = source.convert("RGBA")
            scale = max(1, round(image.width / CANVAS_SIZE))
            enemies = [obj for obj in step.get("objects", []) if isinstance(obj, dict) and obj.get("type") == "enemy"]
            labels = [obj for obj in step.get("objects", []) if isinstance(obj, dict) and obj.get("type") == "text"]
            for enemy in enemies:
                name = str(enemy.get("displayName") or enemy.get("name") or "Enemy")
                boxes = [object_box(enemy, scale, pad=52)]
                boxes.extend(object_box(label, scale, pad=18) for label in labels if str(label.get("text", "")).strip() == name)
                crops.append(
                    {
                        "image": fit_crop(image, union_box(boxes, image.size), crop_size),
                        "label": f"Step {index}: {name}",
                        "note": f"{enemy.get('enemyKind', 'enemy')} / {enemy.get('assetStatus', 'asset')}",
                    }
                )
    return crops


def party_crops(case_dir: Path, crop_size: int) -> list[dict[str, Any]]:
    scene = read_json(case_dir / "scene.xivplan")
    manifest = read_json(case_dir / "manifest.json")
    crops: list[dict[str, Any]] = []
    for index, step in enumerate(scene.get("steps", []), start=1):
        if index > len(manifest.get("steps", [])):
            continue
        party = [obj for obj in step.get("objects", []) if isinstance(obj, dict) and obj.get("type") == "party"]
        labels = [obj for obj in step.get("objects", []) if isinstance(obj, dict) and obj.get("labelKind") == "party_role"]
        if not party:
            continue
        with Image.open(image_path(case_dir, str(manifest["steps"][index - 1].get("image", "")))) as source:
            image = source.convert("RGBA")
            scale = max(1, round(image.width / CANVAS_SIZE))
            boxes = [object_box(obj, scale, pad=34) for obj in party]
            boxes.extend(object_box(label, scale, pad=12) for label in labels)
            cluster = bool(step.get("party_cluster") or step.get("stack_group"))
            jobs = ", ".join(f"{obj.get('role')}={obj.get('job')}" for obj in party)
            crops.append(
                {
                    "image": fit_crop(image, union_box(boxes, image.size), crop_size),
                    "label": f"Step {index}: {'cluster icons' if cluster else 'job labels'}",
                    "note": jobs,
                }
            )
    return crops


def discover_cases(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.iterdir() if path.is_dir() and (path / "scene.xivplan").exists() and (path / "manifest.json").exists())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build focused identity crop sheets for Phase S visual review.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--crop-size", type=int, default=190)
    args = parser.parse_args()

    cases = discover_cases(args.input_dir)
    if not cases:
        print(f"ERROR: no visual-regression cases found under {args.input_dir}")
        return 2

    manifest: dict[str, Any] = {"enemy_crop_sheets": [], "party_identity_crop_sheets": []}
    for case_dir in cases:
        if case_dir.name in ENEMY_CASES:
            output = args.output_dir / "enemy" / f"{slugify(case_dir.name)}-enemy.png"
            result = build_sheet(enemy_crops(case_dir, args.crop_size), output, f"{case_dir.name} enemy identity")
            result["case"] = case_dir.name
            manifest["enemy_crop_sheets"].append(result)
            print(f"Wrote {output}")
        if case_dir.name in PARTY_CASES:
            output = args.output_dir / "party" / f"{slugify(case_dir.name)}-party.png"
            result = build_sheet(party_crops(case_dir, args.crop_size), output, f"{case_dir.name} party identity")
            result["case"] = case_dir.name
            manifest["party_identity_crop_sheets"].append(result)
            print(f"Wrote {output}")

    write_json(args.output_dir / "identity-crop-sheet-manifest.json", manifest)
    print(f"Wrote {args.output_dir / 'identity-crop-sheet-manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

