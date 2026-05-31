#!/usr/bin/env python3
"""Extract machine-readable style baselines from golden XivPlan scenes."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


MECHANIC_ZONE_TYPES = {
    "arc",
    "circle",
    "cone",
    "donut",
    "exaflare",
    "eye",
    "knockback",
    "line",
    "lineKnockAway",
    "lineKnockback",
    "lineStack",
    "polygon",
    "proximity",
    "rect",
    "rightTriangle",
    "stack",
    "starburst",
    "tower",
    "triangle",
}
LAYER_GROUPS = {
    "party": {"party"},
    "enemy": {"enemy"},
    "marker": {"marker"},
    "text": {"text"},
    "arrow": {"arrow", "tether"},
    "mechanic_zone": MECHANIC_ZONE_TYPES,
}
SIZE_KEYS = ("width", "height", "radius", "innerRadius", "fontSize", "opacity")
ROLE_NAMES = {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"}


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    pos = (len(ordered) - 1) * pct
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return round(ordered[lo], 3)
    weight = pos - lo
    return round(ordered[lo] * (1 - weight) + ordered[hi] * weight, 3)


def describe_numbers(values: Iterable[float]) -> dict[str, Any]:
    items = [float(value) for value in values]
    if not items:
        return {"count": 0}
    return {
        "count": len(items),
        "min": round(min(items), 3),
        "p25": percentile(items, 0.25),
        "median": percentile(items, 0.5),
        "p75": percentile(items, 0.75),
        "max": round(max(items), 3),
        "mean": round(statistics.fmean(items), 3),
    }


def top_counts(counter: Counter[Any], limit: int = 12) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common(limit)}


def layer_counts(objects: list[dict[str, Any]]) -> dict[str, int]:
    counts = {layer: 0 for layer in LAYER_GROUPS}
    for obj in objects:
        obj_type = obj.get("type")
        for layer, obj_types in LAYER_GROUPS.items():
            if obj_type in obj_types:
                counts[layer] += 1
                break
    return counts


def object_type_counts(objects: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(obj.get("type")) for obj in objects if isinstance(obj.get("type"), str))


def object_position(obj: dict[str, Any]) -> tuple[float, float] | None:
    x = numeric(obj.get("x"))
    y = numeric(obj.get("y"))
    if x is None or y is None:
        return None
    return x, y


def text_bucket(obj: dict[str, Any]) -> str:
    pos = object_position(obj)
    if pos is None:
        return "unknown"
    x, y = pos
    if abs(x) <= 75 and abs(y) <= 75:
        return "center"
    vertical = "north" if y > 75 else "south" if y < -75 else "mid"
    horizontal = "east" if x > 75 else "west" if x < -75 else "center"
    if vertical == "mid":
        return horizontal
    if horizontal == "center":
        return vertical
    return f"{vertical}-{horizontal}"


def role_name(obj: dict[str, Any]) -> str | None:
    for key in ("role", "name", "label", "text"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip() in ROLE_NAMES:
            return value.strip()
    return None


def distance_distribution(objects: list[dict[str, Any]], source_type: str, target_type: str) -> dict[str, Any]:
    sources = [object_position(obj) for obj in objects if obj.get("type") == source_type]
    targets = [object_position(obj) for obj in objects if obj.get("type") == target_type]
    sources = [pos for pos in sources if pos is not None]
    targets = [pos for pos in targets if pos is not None]
    distances: list[float] = []
    for sx, sy in sources:
        for tx, ty in targets:
            distances.append(math.hypot(sx - tx, sy - ty))
    return describe_numbers(distances)


def arrow_segment(obj: dict[str, Any]) -> tuple[tuple[float, float], tuple[float, float]] | None:
    pos = object_position(obj)
    height = numeric(obj.get("height"))
    rotation = numeric(obj.get("rotation")) or 0.0
    if pos is None or height is None:
        return None
    x, y = pos
    radians = math.radians(rotation)
    dx = math.sin(radians) * height / 2
    dy = math.cos(radians) * height / 2
    return (x - dx, y - dy), (x + dx, y + dy)


def ccw(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(
    first: tuple[tuple[float, float], tuple[float, float]],
    second: tuple[tuple[float, float], tuple[float, float]],
) -> bool:
    a, b = first
    c, d = second
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def arrow_analysis(objects: list[dict[str, Any]]) -> dict[str, Any]:
    arrows = [obj for obj in objects if obj.get("type") == "arrow"]
    lengths = [value for obj in arrows if (value := numeric(obj.get("height"))) is not None]
    widths = [value for obj in arrows if (value := numeric(obj.get("width"))) is not None]
    rotations = [value % 360 for obj in arrows if (value := numeric(obj.get("rotation"))) is not None]
    colors = Counter(str(obj.get("color")) for obj in arrows if obj.get("color"))
    segments = [segment for obj in arrows if (segment := arrow_segment(obj)) is not None]
    crossings = 0
    for index, segment in enumerate(segments):
        crossings += sum(1 for other in segments[index + 1 :] if segments_intersect(segment, other))
    return {
        "count": len(arrows),
        "length": describe_numbers(lengths),
        "width": describe_numbers(widths),
        "rotation_degrees": describe_numbers(rotations),
        "colors": top_counts(colors),
        "crossing_risk": {
            "segment_count": len(segments),
            "estimated_crossings": crossings,
            "risk": "high" if crossings >= 4 else "medium" if crossings else "low",
        },
    }


def text_analysis(objects: list[dict[str, Any]]) -> dict[str, Any]:
    texts = [obj for obj in objects if obj.get("type") == "text"]
    lengths = [len(str(obj.get("text", ""))) for obj in texts]
    font_sizes = [value for obj in texts if (value := numeric(obj.get("fontSize"))) is not None]
    x_values = [pos[0] for obj in texts if (pos := object_position(obj)) is not None]
    y_values = [pos[1] for obj in texts if (pos := object_position(obj)) is not None]
    return {
        "count": len(texts),
        "characters": describe_numbers(lengths),
        "font_size": describe_numbers(font_sizes),
        "colors": top_counts(Counter(str(obj.get("color")) for obj in texts if obj.get("color"))),
        "strokes": top_counts(Counter(str(obj.get("stroke")) for obj in texts if obj.get("stroke"))),
        "styles": top_counts(Counter(str(obj.get("style")) for obj in texts if obj.get("style"))),
        "align": top_counts(Counter(str(obj.get("align")) for obj in texts if obj.get("align"))),
        "position": {
            "x": describe_numbers(x_values),
            "y": describe_numbers(y_values),
            "buckets": top_counts(Counter(text_bucket(obj) for obj in texts), limit=16),
        },
    }


def size_analysis(objects: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obj in objects:
        obj_type = obj.get("type")
        if isinstance(obj_type, str):
            grouped[obj_type].append(obj)
    for obj_type, type_objects in sorted(grouped.items()):
        fields: dict[str, Any] = {}
        for key in SIZE_KEYS:
            values = [value for obj in type_objects if (value := numeric(obj.get(key))) is not None]
            if values:
                fields[key] = describe_numbers(values)
        if fields:
            by_type[obj_type] = fields
    return by_type


def common_arena(scene: dict[str, Any]) -> dict[str, Any]:
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    return {
        "shape": arena.get("shape"),
        "width": arena.get("width"),
        "height": arena.get("height"),
        "padding": arena.get("padding"),
        "backgroundImage": arena.get("backgroundImage"),
        "grid": arena.get("grid"),
        "ticks": arena.get("ticks"),
    }


def step_profile(step: dict[str, Any], index: int) -> dict[str, Any]:
    objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
    counts = object_type_counts(objects)
    party_roles = sorted({role for obj in objects if obj.get("type") == "party" and (role := role_name(obj))})
    return {
        "index": index,
        "title": step.get("title", f"Step {index}"),
        "purpose": step.get("purpose"),
        "guide_text_chars": len(str(step.get("guide_text", ""))),
        "object_count": len(objects),
        "type_counts": dict(sorted(counts.items())),
        "layer_counts": layer_counts(objects),
        "party_roles": party_roles,
        "complete_party": party_roles == sorted(ROLE_NAMES),
        "text": text_analysis(objects),
        "arrows": arrow_analysis(objects),
    }


def recommendations(scene_profile: dict[str, Any]) -> dict[str, Any]:
    step_counts = [step["object_count"] for step in scene_profile["steps"]]
    text_counts = [step["layer_counts"]["text"] for step in scene_profile["steps"]]
    font_sizes = scene_profile["aggregate"]["text"]["font_size"]
    size_by_type = scene_profile["aggregate"]["sizes_by_type"]
    return {
        "recommended_objects_per_step": {
            "normal_range": [
                percentile(step_counts, 0.25),
                percentile(step_counts, 0.75),
            ],
            "upper_review_threshold": percentile(step_counts, 0.9),
            "golden_average": describe_numbers(step_counts).get("mean"),
        },
        "text_density_limit": {
            "normal_text_objects_per_step": [
                percentile(text_counts, 0.25),
                percentile(text_counts, 0.75),
            ],
            "upper_review_threshold": percentile(text_counts, 0.9),
            "typical_font_size": font_sizes.get("median"),
        },
        "player_boss_marker_sizes": {
            "party": size_by_type.get("party", {}),
            "enemy": size_by_type.get("enemy", {}),
            "marker": size_by_type.get("marker", {}),
        },
    }


def analyze_scene(path: Path) -> dict[str, Any]:
    scene = read_scene(path)
    raw_steps = scene.get("steps")
    if not isinstance(raw_steps, list):
        raise ValueError(f"{path}: root.steps must be a list")
    steps = [step for step in raw_steps if isinstance(step, dict)]
    all_objects = [obj for step in steps for obj in step.get("objects", []) if isinstance(obj, dict)]
    counts = object_type_counts(all_objects)
    profile = {
        "path": str(path),
        "scene_name": path.stem,
        "arena": common_arena(scene),
        "nextId": scene.get("nextId"),
        "step_count": len(steps),
        "total_objects": len(all_objects),
        "objects_per_step": describe_numbers([len(step.get("objects", [])) for step in steps]),
        "type_counts": dict(sorted(counts.items())),
        "layer_counts": layer_counts(all_objects),
        "aggregate": {
            "text": text_analysis(all_objects),
            "arrows": arrow_analysis(all_objects),
            "sizes_by_type": size_analysis(all_objects),
            "distances": {
                "party_to_enemy": distance_distribution(all_objects, "party", "enemy"),
                "party_to_marker": distance_distribution(all_objects, "party", "marker"),
                "enemy_to_marker": distance_distribution(all_objects, "enemy", "marker"),
            },
        },
        "steps": [step_profile(step, index) for index, step in enumerate(steps, start=1)],
    }
    profile["recommendations"] = recommendations(profile)
    return profile


def combined_profile(scene_profiles: list[dict[str, Any]]) -> dict[str, Any]:
    total_counts: Counter[str] = Counter()
    all_step_counts: list[int] = []
    all_text_counts: list[int] = []
    backgrounds: Counter[str] = Counter()
    for profile in scene_profiles:
        total_counts.update(profile["type_counts"])
        all_step_counts.extend(step["object_count"] for step in profile["steps"])
        all_text_counts.extend(step["layer_counts"]["text"] for step in profile["steps"])
        background = profile["arena"].get("backgroundImage") or "none"
        backgrounds[str(background)] += 1
    return {
        "scene_count": len(scene_profiles),
        "step_count": sum(profile["step_count"] for profile in scene_profiles),
        "total_objects": sum(profile["total_objects"] for profile in scene_profiles),
        "objects_per_step": describe_numbers(all_step_counts),
        "text_objects_per_step": describe_numbers(all_text_counts),
        "type_counts": dict(sorted(total_counts.items())),
        "background_images": top_counts(backgrounds),
    }


def slugify(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "golden-xivplan"


def default_output_stem(paths: list[Path]) -> str:
    if len(paths) == 1:
        return f"{slugify(paths[0].stem)}-style-profile"
    return "golden-xivplan-style-profile"


def render_markdown(profile: dict[str, Any]) -> str:
    scenes = profile["scenes"]
    aggregate = profile["aggregate"]
    lines = [
        "# Golden XivPlan Style Profile",
        "",
        f"- Generated from {aggregate['scene_count']} scene(s).",
        f"- Total steps: {aggregate['step_count']}",
        f"- Total objects: {aggregate['total_objects']}",
        f"- Objects per step: median {aggregate['objects_per_step'].get('median')}, p25-p75 {aggregate['objects_per_step'].get('p25')} - {aggregate['objects_per_step'].get('p75')}",
        f"- Common backgrounds: {', '.join(f'{name} ({count})' for name, count in aggregate['background_images'].items()) or 'none'}",
        "",
        "## Scene Summary",
        "",
        "| Scene | Steps | Objects | Arena | Top Types |",
        "|---|---:|---:|---|---|",
    ]
    for scene in scenes:
        top_types = ", ".join(f"{name}:{count}" for name, count in Counter(scene["type_counts"]).most_common(8))
        arena = scene["arena"].get("backgroundImage") or scene["arena"].get("shape") or "unknown"
        lines.append(f"| {scene['scene_name']} | {scene['step_count']} | {scene['total_objects']} | `{arena}` | {top_types} |")
    lines.extend(["", "## Step Density", "", "| Scene | Step | Objects | Party | Enemy | Marker | Text | Arrow | Mechanic |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for scene in scenes:
        for step in scene["steps"]:
            layers = step["layer_counts"]
            lines.append(
                f"| {scene['scene_name']} | {step['index']} | {step['object_count']} | "
                f"{layers['party']} | {layers['enemy']} | {layers['marker']} | {layers['text']} | "
                f"{layers['arrow']} | {layers['mechanic_zone']} |"
            )
    lines.extend(["", "## Baseline Recommendations", ""])
    for scene in scenes:
        rec = scene["recommendations"]
        obj_range = rec["recommended_objects_per_step"]["normal_range"]
        text_range = rec["text_density_limit"]["normal_text_objects_per_step"]
        lines.extend(
            [
                f"### {scene['scene_name']}",
                "",
                f"- Recommended objects per step: {obj_range[0]} - {obj_range[1]} (review above {rec['recommended_objects_per_step']['upper_review_threshold']}).",
                f"- Text density: {text_range[0]} - {text_range[1]} text objects per step (review above {rec['text_density_limit']['upper_review_threshold']}).",
                f"- Typical text font size: {rec['text_density_limit']['typical_font_size']}.",
                f"- Arrow crossing risk: {scene['aggregate']['arrows']['crossing_risk']['risk']} ({scene['aggregate']['arrows']['crossing_risk']['estimated_crossings']} estimated crossings).",
                "",
            ]
        )
        for obj_type, fields in rec["player_boss_marker_sizes"].items():
            bits = []
            for field, stats in fields.items():
                if isinstance(stats, dict) and stats.get("median") is not None:
                    bits.append(f"{field} median {stats['median']}")
            if bits:
                lines.append(f"- {obj_type} size baseline: {', '.join(bits)}.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze golden .xivplan files into reusable style profiles.")
    parser.add_argument("paths", type=Path, nargs="+", help="One or more golden .xivplan files")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/style-analysis"), help="Directory for JSON and Markdown outputs")
    parser.add_argument("--name", help="Output basename without extension")
    parser.add_argument("--json-out", type=Path, help="Explicit JSON output path")
    parser.add_argument("--markdown-out", type=Path, help="Explicit Markdown output path")
    args = parser.parse_args()

    try:
        scene_profiles = [analyze_scene(path) for path in args.paths]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    profile = {
        "version": 1,
        "inputs": [str(path) for path in args.paths],
        "aggregate": combined_profile(scene_profiles),
        "scenes": scene_profiles,
    }

    output_stem = args.name or default_output_stem(args.paths)
    json_out = args.json_out or args.output_dir / f"{output_stem}.json"
    markdown_out = args.markdown_out or args.output_dir / f"{output_stem}.md"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(profile), encoding="utf-8")

    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
