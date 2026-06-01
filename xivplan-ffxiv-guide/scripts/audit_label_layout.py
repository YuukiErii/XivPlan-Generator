#!/usr/bin/env python3
"""Audit text label placement in XivPlan scenes."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


TEXT_TYPES = {"text"}
ANCHOR_TYPES = {"party", "enemy", "marker"}
MECHANIC_TYPES = {"arc", "circle", "cone", "donut", "exaflare", "eye", "knockback", "line", "lineStack", "polygon", "rect", "stack", "starburst", "tower"}
FLOW_TYPES = {"arrow", "tether"}


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def text_width(text: str, font_size: float) -> float:
    width = 0.0
    for char in text:
        width += font_size if ord(char) > 127 else font_size * 0.58
    return max(width, font_size)


def bbox_for_object(obj: dict[str, Any]) -> tuple[float, float, float, float] | None:
    if not isinstance(obj.get("x"), (int, float)) or not isinstance(obj.get("y"), (int, float)):
        return None
    x = float(obj["x"])
    y = float(obj["y"])
    obj_type = obj.get("type")
    if obj_type == "text":
        font_size = float(obj.get("fontSize", 14) or 14)
        width = text_width(str(obj.get("text", "")), font_size) + 10
        height = font_size * 1.35 + 6
        return x - width / 2, y - height / 2, x + width / 2, y + height / 2
    if obj_type in {"party", "marker", "image", "icon"}:
        width = float(obj.get("width", 32) or 32)
        height = float(obj.get("height", 32) or 32)
        return x - width / 2, y - height / 2, x + width / 2, y + height / 2
    radius = obj.get("radius")
    if isinstance(radius, (int, float)):
        radius = float(radius)
        return x - radius, y - radius, x + radius, y + radius
    width = obj.get("width")
    height = obj.get("height")
    if isinstance(width, (int, float)) or isinstance(height, (int, float)):
        w = float(width if isinstance(width, (int, float)) else 8)
        h = float(height if isinstance(height, (int, float)) else 8)
        pad = 5 if obj_type in FLOW_TYPES else 0
        return x - w / 2 - pad, y - h / 2 - pad, x + w / 2 + pad, y + h / 2 + pad
    return None


def overlap_area(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> float:
    dx = min(left[2], right[2]) - max(left[0], right[0])
    dy = min(left[3], right[3]) - max(left[1], right[1])
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def bbox_area(box: tuple[float, float, float, float]) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def center(obj: dict[str, Any]) -> tuple[float, float]:
    return float(obj.get("x", 0) or 0), float(obj.get("y", 0) or 0)


def label_anchor_object(text_obj: dict[str, Any], objects: list[dict[str, Any]]) -> dict[str, Any] | None:
    anchor_id = text_obj.get("labelAnchorId")
    if isinstance(anchor_id, int):
        for obj in objects:
            if obj.get("id") == anchor_id:
                return obj
    anchor_key = text_obj.get("labelAnchor")
    if isinstance(anchor_key, str) and anchor_key:
        lowered = anchor_key.lower()
        for obj in objects:
            for key in ("key", "sourceKey", "name", "role"):
                value = obj.get(key)
                if isinstance(value, str) and value.lower() == lowered:
                    return obj
    return None


def max_anchor_distance(text_obj: dict[str, Any], anchor_obj: dict[str, Any] | None) -> float:
    threshold = 180.0 if text_obj.get("leaderLine") else 130.0
    if anchor_obj is not None and isinstance(anchor_obj.get("radius"), (int, float)):
        threshold = max(threshold, float(anchor_obj["radius"]) + 120.0)
    return threshold


def issue_severity(text_box: tuple[float, float, float, float], other_box: tuple[float, float, float, float], other_obj: dict[str, Any]) -> str:
    overlap = overlap_area(text_box, other_box)
    if overlap <= 0:
        return "none"
    other_type = str(other_obj.get("type", "unknown"))
    ratio = overlap / max(bbox_area(text_box), 1)
    if other_type in ANCHOR_TYPES and ratio >= 0.08:
        return "severe"
    if other_type in FLOW_TYPES and ratio >= 0.12:
        return "severe"
    if other_type in MECHANIC_TYPES and float(other_obj.get("opacity", 100) or 100) <= 20:
        return "none"
    if other_type in MECHANIC_TYPES and float(other_obj.get("opacity", 100) or 100) < 35:
        return "review"
    if ratio >= 0.2:
        return "severe"
    return "review"


def audit_step(step: dict[str, Any], step_index: int) -> dict[str, Any]:
    objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
    bboxes = [(index, obj, bbox_for_object(obj)) for index, obj in enumerate(objects)]
    text_items = [(index, obj, box) for index, obj, box in bboxes if box and obj.get("type") == "text"]
    issues: list[dict[str, Any]] = []

    for left_i, left_obj, left_box in text_items:
        for right_i, right_obj, right_box in bboxes:
            if right_box is None or right_i == left_i:
                continue
            right_type = str(right_obj.get("type", "unknown"))
            if right_type == "text" and right_i < left_i:
                continue
            if left_obj.get("labelKind") == "party_role" or right_obj.get("labelKind") == "party_role":
                continue
            severity = issue_severity(left_box, right_box, right_obj)
            if severity == "none":
                continue
            overlap = round(overlap_area(left_box, right_box), 2)
            issues.append(
                {
                    "severity": severity,
                    "kind": "text_overlap" if right_type == "text" else f"text_vs_{right_type}",
                    "text": str(left_obj.get("text", "")),
                    "text_id": left_obj.get("id"),
                    "other_id": right_obj.get("id"),
                    "other_type": right_type,
                    "overlap_area": overlap,
                }
            )

    for text_index, text_obj, _box in text_items:
        if text_obj.get("labelAnchor") is None and text_obj.get("labelAnchorId") is None:
            continue
        tx, ty = center(text_obj)
        anchor_obj = label_anchor_object(text_obj, objects)
        if anchor_obj is not None:
            nearest_distance = math.dist((tx, ty), center(anchor_obj))
        else:
            nearest_distance = min(
                (
                    math.dist((tx, ty), center(obj))
                    for index, obj, box in bboxes
                    if index != text_index and obj.get("type") in ANCHOR_TYPES | MECHANIC_TYPES
                ),
                default=0.0,
            )
        if nearest_distance > max_anchor_distance(text_obj, anchor_obj):
            issues.append(
                {
                    "severity": "review",
                    "kind": "label_far_from_anchor",
                    "text": str(text_obj.get("text", "")),
                    "text_id": text_obj.get("id"),
                    "distance": round(nearest_distance, 2),
                }
            )

    severe_count = sum(1 for issue in issues if issue["severity"] == "severe")
    review_count = sum(1 for issue in issues if issue["severity"] == "review")
    return {
        "step": step_index,
        "title": step.get("title", f"Step {step_index}"),
        "labels": len(text_items),
        "severe_collisions": severe_count,
        "review_items": review_count,
        "issues": issues,
    }


def audit_scene(path: Path) -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")
    per_step = [audit_step(step, index) for index, step in enumerate(steps, start=1) if isinstance(step, dict)]
    severe = sum(item["severe_collisions"] for item in per_step)
    review = sum(item["review_items"] for item in per_step)
    return {
        "path": str(path),
        "steps": len(per_step),
        "labels": sum(item["labels"] for item in per_step),
        "severe_collisions": severe,
        "review_items": review,
        "ok": severe == 0,
        "per_step": per_step,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Label Layout Audit",
        "",
        "| Scene | Status | Steps | Labels | Severe | Review |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {Path(result['path']).name} | {'PASS' if result['ok'] else 'FAIL'} | {result['steps']} | {result['labels']} | {result['severe_collisions']} | {result['review_items']} |"
        )
    lines.extend(["", "## Issues", ""])
    for result in results:
        for step in result["per_step"]:
            for issue in step["issues"]:
                lines.append(
                    "- {scene} step {step}: [{severity}] {kind} `{text}` other={other}".format(
                        scene=Path(result["path"]).name,
                        step=step["step"],
                        severity=issue["severity"],
                        kind=issue["kind"],
                        text=issue.get("text", ""),
                        other=issue.get("other_id", issue.get("distance", "")),
                    )
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit text label collisions in XivPlan scenes.")
    parser.add_argument("paths", type=Path, nargs="+", help="One or more .xivplan files")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        results = [audit_scene(path) for path in args.paths]
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
        print(f"{result['path']}: {'PASS' if result['ok'] else 'FAIL'} severe={result['severe_collisions']} review={result['review_items']}")
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
