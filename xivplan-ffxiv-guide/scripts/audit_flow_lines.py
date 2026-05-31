#!/usr/bin/env python3
"""Audit XivPlan arrow and flow-line readability."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from audit_label_layout import bbox_for_object, overlap_area


HEAD_BLOCKING_TYPES = {"party", "enemy", "marker", "text"}
MECHANIC_TYPES = {"arc", "circle", "cone", "donut", "exaflare", "eye", "knockback", "line", "lineStack", "polygon", "rect", "stack", "starburst", "tower"}
DANGER_COLORS = ("#d13438", "#ff8c00", "#8764b8", "#b146c2", "#ff4f64")


Point = tuple[float, float]
Segment = tuple[Point, Point]


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def point_from_list(value: Any) -> Point | None:
    if isinstance(value, list) and len(value) == 2 and all(isinstance(item, (int, float)) for item in value):
        return float(value[0]), float(value[1])
    return None


def arrow_segment(obj: dict[str, Any]) -> Segment | None:
    start = point_from_list(obj.get("flowStart"))
    end = point_from_list(obj.get("flowEnd"))
    if start and end:
        return start, end
    if not isinstance(obj.get("x"), (int, float)) or not isinstance(obj.get("y"), (int, float)):
        return None
    length = obj.get("width")
    if not isinstance(length, (int, float)):
        return None
    rotation = math.radians(float(obj.get("rotation", 0) or 0))
    dx = math.cos(rotation) * float(length) / 2
    dy = -math.sin(rotation) * float(length) / 2
    x = float(obj["x"])
    y = float(obj["y"])
    return (x - dx, y - dy), (x + dx, y + dy)


def orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def near_same_point(left: Point, right: Point, tolerance: float = 4.0) -> bool:
    return math.dist(left, right) <= tolerance


def segments_share_endpoint(first: Segment, second: Segment) -> bool:
    return any(near_same_point(a, b) for a in first for b in second)


def segments_intersect(first: Segment, second: Segment) -> bool:
    if segments_share_endpoint(first, second):
        return False
    a, b = first
    c, d = second
    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def point_in_box(point: Point, box: tuple[float, float, float, float]) -> bool:
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def segment_intersects_box(segment: Segment, box: tuple[float, float, float, float]) -> bool:
    if point_in_box(segment[0], box) or point_in_box(segment[1], box):
        return True
    left, top, right, bottom = box
    edges = [
        ((left, top), (right, top)),
        ((right, top), (right, bottom)),
        ((right, bottom), (left, bottom)),
        ((left, bottom), (left, top)),
    ]
    return any(segments_intersect(segment, edge) for edge in edges)


def arrow_head_box(segment: Segment, arrow: dict[str, Any]) -> tuple[float, float, float, float]:
    _start, end = segment
    size = max(float(arrow.get("height", 14) or 14) * 1.4, 18.0)
    return end[0] - size / 2, end[1] - size / 2, end[0] + size / 2, end[1] + size / 2


def is_danger_zone(obj: dict[str, Any]) -> bool:
    if obj.get("type") not in MECHANIC_TYPES:
        return False
    if obj.get("type") in {"tower", "stack"}:
        return False
    opacity = float(obj.get("opacity", 100) or 100)
    if opacity < 24:
        return False
    color = str(obj.get("color", "")).lower()
    return any(color.startswith(prefix) for prefix in DANGER_COLORS)


def route_check_enabled(obj: dict[str, Any]) -> bool:
    return obj.get("routeCheck", obj.get("route_check", True)) is not False


def audit_step(step: dict[str, Any], step_index: int, max_crossings_per_step: int) -> dict[str, Any]:
    objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
    arrow_items = [(index, obj, segment) for index, obj in enumerate(objects) if obj.get("type") == "arrow" and (segment := arrow_segment(obj))]
    issues: list[dict[str, Any]] = []

    crossings = 0
    for left_index, left_obj, left_segment in arrow_items:
        if not route_check_enabled(left_obj):
            continue
        for right_index, right_obj, right_segment in arrow_items:
            if right_index <= left_index or not route_check_enabled(right_obj):
                continue
            if left_obj.get("pathKey") and left_obj.get("pathKey") == right_obj.get("pathKey"):
                continue
            if segments_intersect(left_segment, right_segment):
                crossings += 1
                issues.append(
                    {
                        "severity": "severe" if crossings > max_crossings_per_step else "review",
                        "kind": "arrow_crossing",
                        "arrow_id": left_obj.get("id"),
                        "other_id": right_obj.get("id"),
                    }
                )

    for _index, arrow, segment in arrow_items:
        if not arrow.get("arrowEnd", True):
            continue
        head_box = arrow_head_box(segment, arrow)
        for obj in objects:
            if obj is arrow or obj.get("type") not in HEAD_BLOCKING_TYPES:
                continue
            box = bbox_for_object(obj)
            if box and overlap_area(head_box, box) > 0:
                issues.append(
                    {
                        "severity": "severe",
                        "kind": f"arrow_head_vs_{obj.get('type')}",
                        "arrow_id": arrow.get("id"),
                        "other_id": obj.get("id"),
                    }
                )

    for _index, arrow, segment in arrow_items:
        if arrow.get("allowDangerCrossing") or arrow.get("arrowStyle") == "forbidden":
            continue
        for obj in objects:
            if not is_danger_zone(obj):
                continue
            box = bbox_for_object(obj)
            if box and segment_intersects_box(segment, box):
                issues.append(
                    {
                        "severity": "review",
                        "kind": "arrow_through_danger_zone",
                        "arrow_id": arrow.get("id"),
                        "other_id": obj.get("id"),
                    }
                )

    severe_count = sum(1 for issue in issues if issue["severity"] == "severe")
    review_count = sum(1 for issue in issues if issue["severity"] == "review")
    return {
        "step": step_index,
        "title": step.get("title", f"Step {step_index}"),
        "arrows": len(arrow_items),
        "crossings": crossings,
        "severe_items": severe_count,
        "review_items": review_count,
        "issues": issues,
    }


def audit_scene(path: Path, max_crossings_per_step: int = 0) -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")
    per_step = [audit_step(step, index, max_crossings_per_step) for index, step in enumerate(steps, start=1) if isinstance(step, dict)]
    severe = sum(item["severe_items"] for item in per_step)
    review = sum(item["review_items"] for item in per_step)
    crossings = sum(item["crossings"] for item in per_step)
    return {
        "path": str(path),
        "steps": len(per_step),
        "arrows": sum(item["arrows"] for item in per_step),
        "crossings": crossings,
        "severe_items": severe,
        "review_items": review,
        "ok": severe == 0,
        "per_step": per_step,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Flow Line Audit",
        "",
        "| Scene | Status | Steps | Arrows | Crossings | Severe | Review |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {Path(result['path']).name} | {'PASS' if result['ok'] else 'FAIL'} | {result['steps']} | {result['arrows']} | {result['crossings']} | {result['severe_items']} | {result['review_items']} |"
        )
    lines.extend(["", "## Issues", ""])
    for result in results:
        for step in result["per_step"]:
            for issue in step["issues"]:
                lines.append(
                    "- {scene} step {step}: [{severity}] {kind} arrow={arrow} other={other}".format(
                        scene=Path(result["path"]).name,
                        step=step["step"],
                        severity=issue["severity"],
                        kind=issue["kind"],
                        arrow=issue.get("arrow_id", ""),
                        other=issue.get("other_id", ""),
                    )
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit arrow crossings, arrow heads, and movement path clarity in XivPlan scenes.")
    parser.add_argument("paths", type=Path, nargs="+", help="One or more .xivplan files")
    parser.add_argument("--max-crossings-per-step", type=int, default=0, help="Allowed arrow crossings before a step fails")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        results = [audit_scene(path, args.max_crossings_per_step) for path in args.paths]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(results), encoding="utf-8")

    for result in results:
        print(f"{result['path']}: {'PASS' if result['ok'] else 'FAIL'} crossings={result['crossings']} severe={result['severe_items']} review={result['review_items']}")
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
