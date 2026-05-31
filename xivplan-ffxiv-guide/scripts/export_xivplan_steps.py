#!/usr/bin/env python3
"""Export each XivPlan step to a lightweight PNG preview plus manifest.json."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageColor, ImageDraw, ImageFont


CANVAS_SIZE = 720
CENTER = CANVAS_SIZE // 2
SCALE = 0.9


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.strip().lower(), flags=re.UNICODE)
    return re.sub(r"-+", "-", cleaned).strip("-") or "step"


def color_rgba(value: Any, opacity: Any = 100) -> tuple[int, int, int, int]:
    try:
        rgb = ImageColor.getrgb(str(value or "#ffffff"))
    except ValueError:
        rgb = (255, 255, 255)
    alpha = max(0, min(255, round(float(opacity if opacity is not None else 100) * 2.55)))
    return rgb[0], rgb[1], rgb[2], alpha


def xy(obj: dict[str, Any]) -> tuple[float, float]:
    return CENTER + float(obj.get("x", 0)) * SCALE, CENTER - float(obj.get("y", 0)) * SCALE


def radius(value: Any) -> float:
    return float(value or 0) * SCALE


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


def draw_centered_text(draw: ImageDraw.ImageDraw, center: tuple[float, float], text: str, size: int, fill: str = "#ffffff") -> None:
    face = font(size)
    bbox = draw.textbbox((0, 0), text, font=face, stroke_width=2)
    x = center[0] - (bbox[2] - bbox[0]) / 2
    y = center[1] - (bbox[3] - bbox[1]) / 2
    draw.text((x, y), text, font=face, fill=fill, stroke_width=2, stroke_fill="#101318")


def polygon_points(cx: float, cy: float, r: float, sides: int, rotation: float) -> list[tuple[float, float]]:
    return [
        (
            cx + math.cos(math.radians(rotation + i * 360 / sides)) * r,
            cy - math.sin(math.radians(rotation + i * 360 / sides)) * r,
        )
        for i in range(sides)
    ]


def rotated_rect(cx: float, cy: float, width: float, height: float, rotation: float) -> list[tuple[float, float]]:
    angle = math.radians(rotation)
    points = [(-width / 2, -height / 2), (width / 2, -height / 2), (width / 2, height / 2), (-width / 2, height / 2)]
    return [
        (
            cx + x * math.cos(angle) - y * math.sin(angle),
            cy + x * math.sin(angle) + y * math.cos(angle),
        )
        for x, y in points
    ]


def draw_arrow(draw: ImageDraw.ImageDraw, obj: dict[str, Any]) -> None:
    cx, cy = xy(obj)
    length = float(obj.get("width", 80)) * SCALE
    rotation = math.radians(float(obj.get("rotation", 0)))
    dx = math.cos(rotation) * length / 2
    dy = math.sin(rotation) * length / 2
    start = (cx - dx, cy - dy)
    end = (cx + dx, cy + dy)
    fill = color_rgba(obj.get("color", "#2aa7ff"), obj.get("opacity", 100))
    draw.line([start, end], fill=fill, width=max(3, round(float(obj.get("height", 14)) * SCALE / 2)))
    head = 12
    for angle in (rotation + math.radians(150), rotation - math.radians(150)):
        point = (end[0] + math.cos(angle) * head, end[1] + math.sin(angle) * head)
        draw.line([end, point], fill=fill, width=3)


def draw_object(draw: ImageDraw.ImageDraw, obj: dict[str, Any]) -> None:
    obj_type = obj.get("type")
    cx, cy = xy(obj)
    fill = color_rgba(obj.get("color", "#ffffff"), obj.get("opacity", 100))

    if obj_type in {"circle", "tower", "stack", "knockback", "eye"}:
        r = radius(obj.get("radius", 40))
        box = [cx - r, cy - r, cx + r, cy + r]
        if obj.get("hollow") or obj_type == "tower":
            draw.ellipse(box, outline=fill, width=4)
        else:
            draw.ellipse(box, fill=fill, outline=fill)
        if obj_type == "tower":
            draw_centered_text(draw, (cx, cy), str(obj.get("count", "")), 18)
        if obj_type == "stack":
            draw_centered_text(draw, (cx, cy), str(obj.get("count", "")), 18)
    elif obj_type == "donut":
        outer = radius(obj.get("radius", 180))
        inner = radius(obj.get("innerRadius", 80))
        draw.ellipse([cx - outer, cy - outer, cx + outer, cy + outer], outline=fill, width=8)
        draw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], outline=(255, 255, 255, 90), width=3)
    elif obj_type in {"rect", "line", "lineStack", "lineKnockback", "lineKnockAway"}:
        width = float(obj.get("width", obj.get("length", 100))) * SCALE
        height = float(obj.get("height", obj.get("width", 40))) * SCALE
        points = rotated_rect(cx, cy, width, height, float(obj.get("rotation", 0)))
        draw.polygon(points, fill=fill)
    elif obj_type == "cone":
        r = radius(obj.get("radius", 220))
        angle = float(obj.get("coneAngle", 90))
        rot = float(obj.get("rotation", 0))
        points = [(cx, cy)]
        points.extend(polygon_points(cx, cy, r, 18, rot - angle / 2)[:1])
        for i in range(19):
            a = math.radians(rot - angle / 2 + angle * i / 18)
            points.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        draw.polygon(points, fill=fill)
    elif obj_type == "polygon":
        draw.polygon(polygon_points(cx, cy, radius(obj.get("radius", 120)), int(obj.get("sides", 6)), float(obj.get("rotation", 0))), fill=fill)
    elif obj_type == "starburst":
        for i in range(int(obj.get("spokes", 8))):
            rot = float(obj.get("rotation", 0)) + i * 360 / int(obj.get("spokes", 8))
            points = rotated_rect(cx, cy, radius(obj.get("spokeWidth", 18)), radius(obj.get("radius", 120)), rot)
            draw.polygon(points, fill=fill)
    elif obj_type == "exaflare":
        rot = math.radians(float(obj.get("rotation", 0)))
        spacing = float(obj.get("spacing", 58)) * SCALE
        r = radius(obj.get("radius", 32))
        for i in range(int(obj.get("length", 5))):
            px = cx + math.cos(rot) * spacing * i
            py = cy + math.sin(rot) * spacing * i
            draw.ellipse([px - r, py - r, px + r, py + r], outline=fill, width=3)
    elif obj_type == "arrow":
        draw_arrow(draw, obj)
    elif obj_type == "enemy":
        r = radius(obj.get("radius", 44))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color_rgba("#5b2b2b", obj.get("opacity", 100)), outline="#ff6b6b", width=4)
        draw_centered_text(draw, (cx, cy), str(obj.get("name", "Boss")), 14)
    elif obj_type in {"party", "marker", "image", "icon"}:
        width = float(obj.get("width", 34)) * SCALE
        height = float(obj.get("height", 34)) * SCALE
        draw.rounded_rectangle([cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2], radius=6, fill=color_rgba("#20252d", obj.get("opacity", 100)), outline="#d7e3f5", width=2)
        label = str(obj.get("name", obj.get("type", "")))
        if obj_type == "marker":
            label = str(obj.get("name", "M"))
        draw_centered_text(draw, (cx, cy), label[:4], 12)
    elif obj_type == "text":
        draw_centered_text(draw, (cx, cy), str(obj.get("text", "")), int(obj.get("fontSize", 16)))


def render_step(scene: dict[str, Any], step: dict[str, Any], output_path: Path, scale_factor: int) -> None:
    size = CANVAS_SIZE * scale_factor
    image = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), "#15171ccc")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse([60, 60, CANVAS_SIZE - 60, CANVAS_SIZE - 60], fill="#242932", outline="#667085", width=3)
    draw.line([(CENTER, 70), (CENTER, CANVAS_SIZE - 70)], fill="#3a414d", width=1)
    draw.line([(70, CENTER), (CANVAS_SIZE - 70, CENTER)], fill="#3a414d", width=1)

    for obj in step.get("objects", []):
        if obj.get("type") not in {"party", "marker", "enemy", "text", "tether"}:
            draw_object(draw, obj)
    for obj in step.get("objects", []):
        if obj.get("type") in {"party", "marker", "enemy", "image", "icon", "arrow", "text"}:
            draw_object(draw, obj)

    if scale_factor != 1:
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def export_steps(scene_path: Path, output_dir: Path, scale_factor: int = 1) -> dict[str, Any]:
    scene = read_json(scene_path)
    if not isinstance(scene, dict) or not isinstance(scene.get("steps"), list):
        raise ValueError("scene must contain a steps list")
    images_dir = output_dir / "images"
    manifest = {"scene": str(scene_path), "scale": scale_factor, "steps": []}
    for index, step in enumerate(scene["steps"], start=1):
        title = str(step.get("title", f"step {index}"))
        filename = f"step_{index:02d}_{slugify(title)}.png"
        render_step(scene, step, images_dir / filename, scale_factor)
        manifest["steps"].append({"step": index, "title": title, "image": f"images/{filename}"})
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Export XivPlan step previews to PNG files.")
    parser.add_argument("scene", type=Path, help="Path to .xivplan JSON")
    parser.add_argument("-o", "--output-dir", type=Path, required=True, help="Output directory")
    parser.add_argument("--scale", type=int, choices=[1, 2, 4], default=1, help="PNG scale factor")
    args = parser.parse_args()
    try:
        manifest = export_steps(args.scene, args.output_dir, args.scale)
    except Exception as exc:  # noqa: BLE001 - CLI should report export failures clearly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output_dir}")
    print(f"steps: {len(manifest['steps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
