#!/usr/bin/env python3
"""Validate basic XivPlan .xivplan JSON structure."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


KNOWN_TYPES = {
    "arc",
    "arrow",
    "circle",
    "cone",
    "cursor",
    "donut",
    "draw",
    "enemy",
    "exaflare",
    "eye",
    "icon",
    "knockback",
    "line",
    "lineKnockAway",
    "lineKnockback",
    "lineStack",
    "marker",
    "party",
    "polygon",
    "proximity",
    "rect",
    "rightTriangle",
    "rotateCCW",
    "rotateCW",
    "stack",
    "starburst",
    "tether",
    "text",
    "tower",
    "triangle",
}

REQUIRED_BY_TYPE = {
    "party": {"name", "image", "x", "y", "width", "height", "rotation", "opacity"},
    "enemy": {"name", "icon", "x", "y", "radius", "rotation", "ring", "color", "opacity"},
    "tower": {"x", "y", "radius", "count", "color", "opacity"},
    "stack": {"x", "y", "radius", "count", "color", "opacity"},
    "circle": {"x", "y", "radius", "color", "opacity"},
    "knockback": {"x", "y", "radius", "color", "opacity"},
    "donut": {"x", "y", "radius", "innerRadius", "color", "opacity"},
    "line": {"x", "y", "length", "width", "rotation", "color", "opacity"},
    "cone": {"x", "y", "radius", "coneAngle", "rotation", "color", "opacity"},
    "arrow": {"x", "y", "width", "height", "rotation", "color", "opacity"},
    "text": {"text", "x", "y", "rotation", "color", "stroke", "style", "fontSize", "align", "opacity"},
    "tether": {"startId", "endId", "tether", "width", "color", "opacity"},
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def expect_number(errors: list[str], obj: dict[str, Any], key: str, where: str) -> None:
    if key in obj and not isinstance(obj[key], (int, float)):
        fail(errors, f"{where}: {key} must be a number")


def validate_scene(scene: Any) -> tuple[list[str], Counter[str], int]:
    errors: list[str] = []
    counts: Counter[str] = Counter()

    if not isinstance(scene, dict):
        return ["root must be a JSON object"], counts, 0

    if not isinstance(scene.get("nextId"), int):
        fail(errors, "root.nextId must be an integer")
    if not isinstance(scene.get("arena"), dict):
        fail(errors, "root.arena must be an object")
    steps = scene.get("steps")
    if not isinstance(steps, list) or not steps:
        fail(errors, "root.steps must be a non-empty list")
        return errors, counts, 0

    ids: set[int] = set()
    all_objects: list[dict[str, Any]] = []

    for step_index, step in enumerate(steps):
        where_step = f"steps[{step_index}]"
        if not isinstance(step, dict):
            fail(errors, f"{where_step} must be an object")
            continue
        objects = step.get("objects")
        if not isinstance(objects, list):
            fail(errors, f"{where_step}.objects must be a list")
            continue
        for object_index, obj in enumerate(objects):
            where = f"{where_step}.objects[{object_index}]"
            if not isinstance(obj, dict):
                fail(errors, f"{where} must be an object")
                continue
            all_objects.append(obj)
            obj_id = obj.get("id")
            obj_type = obj.get("type")
            if not isinstance(obj_id, int):
                fail(errors, f"{where}.id must be an integer")
            elif obj_id in ids:
                fail(errors, f"{where}.id duplicates scene-wide id {obj_id}")
            else:
                ids.add(obj_id)

            if not isinstance(obj_type, str) or obj_type not in KNOWN_TYPES:
                fail(errors, f"{where}.type is unknown: {obj_type!r}")
                continue
            counts[obj_type] += 1

            missing = REQUIRED_BY_TYPE.get(obj_type, set()) - obj.keys()
            if missing:
                fail(errors, f"{where} ({obj_type}) missing required fields: {', '.join(sorted(missing))}")

            for key in ("x", "y", "width", "height", "radius", "rotation", "opacity", "count"):
                expect_number(errors, obj, key, where)

    for obj in all_objects:
        if obj.get("type") != "tether":
            continue
        where = f"tether id {obj.get('id')}"
        for key in ("startId", "endId"):
            target_id = obj.get(key)
            if not isinstance(target_id, int):
                fail(errors, f"{where}: {key} must be an integer")
            elif target_id not in ids:
                fail(errors, f"{where}: {key} references missing id {target_id}")

    next_id = scene.get("nextId")
    if isinstance(next_id, int) and ids and next_id <= max(ids):
        fail(errors, f"root.nextId={next_id} must be greater than max object id {max(ids)}")

    return errors, counts, len(all_objects)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate basic XivPlan .xivplan JSON structure.")
    parser.add_argument("path", type=Path, help="Path to a .xivplan JSON file")
    args = parser.parse_args()

    try:
        scene = json.loads(args.path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should report parse errors clearly.
        print(f"ERROR: failed to read JSON: {exc}", file=sys.stderr)
        return 2

    errors, counts, object_count = validate_scene(scene)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    print(f"steps: {len(scene['steps'])}")
    print(f"objects: {object_count}")
    if counts:
        print("types:")
        for obj_type, count in sorted(counts.items()):
            print(f"- {obj_type}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
