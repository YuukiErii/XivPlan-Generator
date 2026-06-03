#!/usr/bin/env python3
"""Export each XivPlan step to a lightweight PNG preview plus manifest.json."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import sys
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps


CANVAS_SIZE = 720
CENTER = CANVAS_SIZE // 2
SCALE = 0.9
ROOT = Path(__file__).resolve().parents[2]
ROLE_COLORS = {
    "MT": "#3f7bdc",
    "ST": "#3f7bdc",
    "H1": "#49a86d",
    "H2": "#49a86d",
    "D1": "#d86b7d",
    "D2": "#d86b7d",
    "D3": "#b58a2a",
    "D4": "#8d6eea",
}


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


def data_url_image(value: Any) -> Image.Image | None:
    if not isinstance(value, str) or not value.startswith("data:image/"):
        return None
    header, sep, payload = value.partition(",")
    if not sep or ";base64" not in header:
        return None
    try:
        return Image.open(BytesIO(base64.b64decode(payload))).convert("RGBA")
    except Exception:
        return None


@lru_cache(maxsize=1)
def xivplan_public_dirs() -> tuple[Path, ...]:
    env_dir = os.environ.get("XIVPLAN_PUBLIC_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.extend(
        [
            ROOT.parent / "XivPlan" / "public",
            ROOT / "public",
            ROOT / "xivplan-ffxiv-guide" / "public",
        ]
    )
    return tuple(path.resolve() for path in candidates if path.exists())


@lru_cache(maxsize=128)
def local_asset_image(value: str) -> Image.Image | None:
    if not value.startswith("/"):
        return None
    relative = Path(value.lstrip("/").replace("/", "\\"))
    for public_dir in xivplan_public_dirs():
        candidate = (public_dir / relative).resolve()
        try:
            candidate.relative_to(public_dir)
        except ValueError:
            continue
        if candidate.is_file():
            try:
                if candidate.suffix.lower() == ".svg":
                    return svg_placeholder_image(candidate)
                return Image.open(candidate).convert("RGBA")
            except Exception:
                return None
    return None


def svg_placeholder_image(path: Path) -> Image.Image:
    """Draw a lightweight arena fallback when Pillow cannot rasterize SVG."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"pagecolor=\"(#[0-9a-fA-F]{6})\"", text)
    background = match.group(1) if match else "#40352c"
    image = Image.new("RGBA", (600, 600), background)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse([4, 4, 596, 596], outline=color_rgba("#8f7b66", 82), width=6)
    for index in range(8):
        angle = math.radians(index * 45)
        x = 300 + math.cos(angle) * 292
        y = 300 + math.sin(angle) * 292
        draw.line([(300, 300), (x, y)], fill=color_rgba("#6f5a48", 42), width=2)
    for radius_px in (150, 225):
        draw.ellipse([300 - radius_px, 300 - radius_px, 300 + radius_px, 300 + radius_px], outline=color_rgba("#6f5a48", 46), width=2)
    draw_centered_text(draw, (300, 300), path.stem.upper(), 22, fill="#f5efe7")
    return image


def reference_image(value: Any) -> Image.Image | None:
    source = data_url_image(value)
    if source is not None:
        return source
    if isinstance(value, str):
        return local_asset_image(value)
    return None


def arena_bounds() -> tuple[int, int, int, int]:
    return 60, 60, CANVAS_SIZE - 60, CANVAS_SIZE - 60


def arena_center_radius() -> tuple[tuple[int, int], int]:
    left, top, right, bottom = arena_bounds()
    return (CENTER, CENTER), (right - left) // 2


def paste_arena_background(canvas: Image.Image, source: Image.Image, opacity: Any, shape: str) -> None:
    left, top, right, bottom = arena_bounds()
    size = (right - left, bottom - top)
    background = ImageOps.fit(source.convert("RGBA"), size, method=Image.Resampling.LANCZOS)
    alpha_factor = max(0.0, min(1.0, float(opacity if opacity is not None else 100) / 100.0))
    if alpha_factor < 1.0:
        alpha = background.getchannel("A").point(lambda value: round(value * alpha_factor))
        background.putalpha(alpha)
    if shape == "circle":
        mask = Image.new("L", size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, size[0] - 1, size[1] - 1], fill=255)
        background.putalpha(Image.composite(background.getchannel("A"), Image.new("L", size, 0), mask))
    canvas.alpha_composite(background, (left, top))


def draw_grid(draw: ImageDraw.ImageDraw, arena: dict[str, Any]) -> None:
    center, outer = arena_center_radius()
    grid = arena.get("grid") if isinstance(arena.get("grid"), dict) else {}
    grid_type = grid.get("type")
    if arena.get("shape", "circle") == "rectangle" or grid_type == "rectangle":
        rows = int(grid.get("rows", 4) or 4)
        columns = int(grid.get("columns", 4) or 4)
        left, top, right, bottom = arena_bounds()
        for index in range(1, columns):
            x = left + (right - left) * index / columns
            draw.line([(x, top), (x, bottom)], fill=color_rgba("#3a414d", 50), width=1)
        for index in range(1, rows):
            y = top + (bottom - top) * index / rows
            draw.line([(left, y), (right, y)], fill=color_rgba("#3a414d", 50), width=1)
        return
    angular_divs = int(grid.get("angularDivs", 8) or 8)
    radial_divs = int(grid.get("radialDivs", 2) or 2)
    for index in range(angular_divs):
        angle = math.radians(index * 360 / angular_divs)
        end = (center[0] + math.cos(angle) * outer, center[1] + math.sin(angle) * outer)
        draw.line([center, end], fill=color_rgba("#3a414d", 44), width=1)
    for index in range(1, radial_divs + 1):
        r = outer * index / (radial_divs + 1)
        draw.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], outline=color_rgba("#3a414d", 42), width=1)


def draw_radial_ticks(draw: ImageDraw.ImageDraw, count: int, color: str, opacity: Any) -> None:
    center, outer = arena_center_radius()
    for index in range(max(1, count)):
        angle = math.radians(index * 360 / count)
        inner = outer - (18 if index % 2 == 0 else 11)
        start = (center[0] + math.cos(angle) * inner, center[1] + math.sin(angle) * inner)
        end = (center[0] + math.cos(angle) * outer, center[1] + math.sin(angle) * outer)
        draw.line([start, end], fill=color_rgba(color, opacity), width=2)


def draw_axis_overlay(draw: ImageDraw.ImageDraw, axis: str, label: str, color: str, opacity: Any) -> None:
    center, outer = arena_center_radius()
    if axis.upper() == "AC":
        points = [(center[0], center[1] - outer), (center[0], center[1] + outer)]
        label_pos = (center[0] - 34, center[1] - outer + 26)
    else:
        points = [(center[0] - outer, center[1]), (center[0] + outer, center[1])]
        label_pos = (center[0] + outer - 42, center[1] - 24)
    draw.line(points, fill=color_rgba(color, opacity), width=3)
    if label:
        draw_centered_text(draw, label_pos, label, 13, fill=color)


def draw_half_mask(canvas: Image.Image, side: str, color: str, opacity: Any, label: str) -> None:
    left, top, right, bottom = arena_bounds()
    overlay = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")
    side = side.upper()
    if side in {"W", "WEST"}:
        box = [left, top, CENTER, bottom]
        label_pos = (CENTER - 128, CENTER)
    elif side in {"E", "EAST"}:
        box = [CENTER, top, right, bottom]
        label_pos = (CENTER + 128, CENTER)
    elif side in {"N", "NORTH"}:
        box = [left, top, right, CENTER]
        label_pos = (CENTER, CENTER - 128)
    else:
        box = [left, CENTER, right, bottom]
        label_pos = (CENTER, CENTER + 128)
    overlay_draw.rectangle(box, fill=color_rgba(color, opacity))
    mask = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(arena_bounds(), fill=255)
    overlay.putalpha(Image.composite(overlay.getchannel("A"), Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0), mask))
    canvas.alpha_composite(overlay)
    if label:
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw_centered_text(draw, label_pos, label, 13, fill=color)


def draw_arena_overlays(image: Image.Image, draw: ImageDraw.ImageDraw, arena: dict[str, Any]) -> None:
    overlays = arena.get("arenaOverlays")
    if not isinstance(overlays, list):
        return
    for overlay in overlays:
        if not isinstance(overlay, dict):
            continue
        kind = str(overlay.get("kind", ""))
        if kind == "radial_ticks":
            draw_radial_ticks(draw, int(overlay.get("count", 16) or 16), str(overlay.get("color", "#8aa0b8")), overlay.get("opacity", 42))
        elif kind == "axis":
            draw_axis_overlay(draw, str(overlay.get("axis", "AC")), str(overlay.get("label", "")), str(overlay.get("color", "#f7f7f7")), overlay.get("opacity", 72))
        elif kind == "half_mask":
            draw_half_mask(image, str(overlay.get("side", "W")), str(overlay.get("color", "#5fb3ff")), overlay.get("opacity", 12), str(overlay.get("label", "")))
        elif kind == "ring_label_band":
            draw_centered_text(draw, (CENTER, 38), str(overlay.get("label", ""))[:78], 12, fill=str(overlay.get("color", "#f7f7f7")))


def draw_arena(image: Image.Image, scene: dict[str, Any]) -> None:
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    shape = str(arena.get("shape", "circle"))
    draw = ImageDraw.Draw(image, "RGBA")
    background = reference_image(arena.get("backgroundImage"))
    if background is not None:
        paste_arena_background(image, background, arena.get("backgroundOpacity", 88), shape)
    elif shape == "rectangle":
        draw.rectangle(arena_bounds(), fill="#242932", outline="#667085", width=3)
    else:
        draw.ellipse(arena_bounds(), fill="#242932", outline="#667085", width=3)
    draw_grid(draw, arena)
    draw_arena_overlays(image, draw, arena)
    if background is None and arena.get("backgroundImage"):
        draw_centered_text(draw, (CENTER, CANVAS_SIZE - 36), f"arena asset fallback: {arena.get('backgroundImage')}", 11, fill="#f7c873")
    if shape == "rectangle":
        draw.rectangle(arena_bounds(), outline="#667085", width=3)
    else:
        draw.ellipse(arena_bounds(), outline="#667085", width=3)


def paste_centered(canvas: Image.Image, source: Image.Image, center: tuple[float, float], size: tuple[float, float], opacity: Any = 100) -> None:
    width = max(1, round(size[0] * SCALE))
    height = max(1, round(size[1] * SCALE))
    icon = source.copy()
    icon.thumbnail((width, height), Image.Resampling.LANCZOS)
    if opacity is not None:
        alpha_factor = max(0.0, min(1.0, float(opacity) / 100.0))
        if alpha_factor < 1.0:
            alpha = icon.getchannel("A").point(lambda value: round(value * alpha_factor))
            icon.putalpha(alpha)
    x = round(center[0] - icon.width / 2)
    y = round(center[1] - icon.height / 2)
    canvas.alpha_composite(icon, (x, y))


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


def draw_job_badge(draw: ImageDraw.ImageDraw, obj: dict[str, Any], center: tuple[float, float], width: float, height: float) -> None:
    role = str(obj.get("role") or obj.get("name") or "")
    job = str(obj.get("job") or role)
    fill = color_rgba(ROLE_COLORS.get(role, "#20252d"), obj.get("opacity", 100))
    draw.rounded_rectangle([center[0] - width / 2, center[1] - height / 2, center[0] + width / 2, center[1] + height / 2], radius=6, fill=fill, outline="#f2f7ff", width=2)
    draw_centered_text(draw, center, job[:3], 10)


def draw_object(image: Image.Image, draw: ImageDraw.ImageDraw, obj: dict[str, Any]) -> None:
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
        ring = obj.get("targetRing")
        ring_width = 4
        if isinstance(ring, dict):
            r = radius(ring.get("radius", obj.get("radius", 44)))
            ring_width = max(2, round(float(ring.get("strokeWidth", 3)) * SCALE))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color_rgba("#5b2b2b", min(28, obj.get("opacity", 100))), outline="#ff6b6b", width=ring_width)
        icon = reference_image(obj.get("icon") or obj.get("image"))
        if icon is not None:
            paste_centered(image, icon, (cx, cy), (float(obj.get("iconWidth", r * 1.45)), float(obj.get("iconHeight", r * 1.45))), obj.get("opacity", 100))
        else:
            draw_centered_text(draw, (cx, cy), str(obj.get("name", "Boss"))[:4], 12)
    elif obj_type in {"party", "marker", "image", "icon"}:
        width = float(obj.get("width", 34)) * SCALE
        height = float(obj.get("height", 34)) * SCALE
        source = reference_image(obj.get("image") or obj.get("icon"))
        if source is not None:
            paste_centered(image, source, (cx, cy), (float(obj.get("width", 34)), float(obj.get("height", 34))), obj.get("opacity", 100))
        elif obj_type == "party":
            draw_job_badge(draw, obj, (cx, cy), width, height)
        else:
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
    draw_arena(image, scene)

    for obj in step.get("objects", []):
        if obj.get("type") not in {"party", "marker", "enemy", "text", "tether"}:
            draw_object(image, draw, obj)
    for obj in step.get("objects", []):
        if obj.get("type") in {"party", "marker", "enemy", "image", "icon", "arrow", "text"}:
            draw_object(image, draw, obj)

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
