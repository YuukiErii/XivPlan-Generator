#!/usr/bin/env python3
"""Move XivPlan text labels to lower-collision nearby positions."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from audit_label_layout import bbox_area, bbox_for_object, overlap_area


CANDIDATE_OFFSETS = [
    (0, 0),
    (0, 34),
    (34, 0),
    (0, -34),
    (-34, 0),
    (42, 42),
    (42, -42),
    (-42, -42),
    (-42, 42),
    (0, 68),
    (68, 0),
    (0, -68),
    (-68, 0),
]


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_scene(path: Path, scene: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def moved_bbox(box: tuple[float, float, float, float], dx: float, dy: float) -> tuple[float, float, float, float]:
    return box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy


def score_box(candidate: tuple[float, float, float, float], other_boxes: list[tuple[float, float, float, float]], dx: float, dy: float) -> float:
    overlap_penalty = 0.0
    for other in other_boxes:
        overlap = overlap_area(candidate, other)
        if overlap:
            overlap_penalty += overlap / max(bbox_area(candidate), 1) * 1000
    movement_penalty = (abs(dx) + abs(dy)) * 0.05
    return overlap_penalty + movement_penalty


def place_step_labels(step: dict[str, Any]) -> int:
    objects = step.get("objects", [])
    if not isinstance(objects, list):
        return 0
    moved = 0

    for index, obj in enumerate(objects):
        if not isinstance(obj, dict) or obj.get("type") != "text":
            continue
        base_box = bbox_for_object(obj)
        if base_box is None:
            continue
        other_boxes = [
            box
            for other_index, other in enumerate(objects)
            if other_index != index and isinstance(other, dict) and (box := bbox_for_object(other)) is not None
        ]
        current_score = score_box(base_box, other_boxes, 0, 0)
        best_score = current_score
        best_offset = (0, 0)
        for dx, dy in CANDIDATE_OFFSETS[1:]:
            candidate_box = moved_bbox(base_box, dx, dy)
            candidate_score = score_box(candidate_box, other_boxes, dx, dy)
            if candidate_score < best_score:
                best_score = candidate_score
                best_offset = (dx, dy)
        if best_offset != (0, 0):
            obj["x"] = round(float(obj.get("x", 0) or 0) + best_offset[0], 3)
            obj["y"] = round(float(obj.get("y", 0) or 0) + best_offset[1], 3)
            moved += 1
    return moved


def auto_place(scene: dict[str, Any]) -> tuple[dict[str, Any], int]:
    updated = copy.deepcopy(scene)
    moved = 0
    steps = updated.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")
    for step in steps:
        if isinstance(step, dict):
            moved += place_step_labels(step)
    return updated, moved


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-place XivPlan text labels by minimizing nearby bbox collisions.")
    parser.add_argument("scene", type=Path, help="Input .xivplan file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .xivplan file")
    args = parser.parse_args()

    try:
        scene = read_scene(args.scene)
        updated, moved = auto_place(scene)
        write_scene(args.output, updated)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    print(f"labels moved: {moved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
