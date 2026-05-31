#!/usr/bin/env python3
"""Validate basic XivPlan .xivplan JSON structure."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from collections import Counter
from math import hypot
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
    "image",
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
    "marker": {"name", "image", "x", "y", "width", "height", "rotation", "shape", "color", "opacity"},
    "icon": {"name", "image", "x", "y", "width", "height", "rotation", "opacity"},
    "image": {"name", "image", "x", "y", "width", "height", "rotation", "opacity"},
    "enemy": {"name", "icon", "x", "y", "radius", "rotation", "ring", "color", "opacity"},
    "tower": {"x", "y", "radius", "count", "color", "opacity"},
    "stack": {"x", "y", "radius", "count", "color", "opacity"},
    "circle": {"x", "y", "radius", "color", "opacity"},
    "knockback": {"x", "y", "radius", "color", "opacity"},
    "eye": {"x", "y", "radius", "color", "opacity"},
    "donut": {"x", "y", "radius", "innerRadius", "color", "opacity"},
    "arc": {"x", "y", "radius", "innerRadius", "coneAngle", "rotation", "color", "opacity"},
    "line": {"x", "y", "length", "width", "rotation", "color", "opacity"},
    "cone": {"x", "y", "radius", "coneAngle", "rotation", "color", "opacity"},
    "rect": {"x", "y", "width", "height", "rotation", "color", "opacity"},
    "lineStack": {"x", "y", "width", "height", "rotation", "color", "opacity"},
    "lineKnockback": {"x", "y", "width", "height", "rotation", "color", "opacity"},
    "lineKnockAway": {"x", "y", "width", "height", "rotation", "color", "opacity"},
    "polygon": {"x", "y", "radius", "sides", "orient", "rotation", "color", "opacity"},
    "starburst": {"x", "y", "radius", "spokes", "spokeWidth", "rotation", "color", "opacity"},
    "exaflare": {"x", "y", "radius", "length", "spacing", "rotation", "color", "opacity"},
    "arrow": {"x", "y", "width", "height", "rotation", "color", "opacity"},
    "text": {"text", "x", "y", "rotation", "color", "stroke", "style", "fontSize", "align", "opacity"},
    "tether": {"startId", "endId", "tether", "width", "color", "opacity"},
}

IMAGE_TYPES = {"image", "icon", "party"}
TEXT_FIELD_LIMIT = 80
GUIDE_TEXT_LIMIT = 180
OBJECT_BOUND_MARGIN = 40
PARTY_OVERLAP_DISTANCE = 18
PARTY_ROLE_NAMES = {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"}
WAYMARK_NAMES = {"A", "B", "C", "D", "1", "2", "3", "4"}

DEFAULT_SCENE_CONTRACT = {
    "require_full_party_each_step": False,
    "require_enemy_each_step": False,
    "require_waymarks_each_step": False,
    "allow_partial_observation": True,
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def expect_number(errors: list[str], obj: dict[str, Any], key: str, where: str) -> None:
    if key in obj and not isinstance(obj[key], (int, float)):
        fail(errors, f"{where}: {key} must be a number")


def looks_like_observation_step(step: dict[str, Any]) -> bool:
    if step.get("partial_observation") is True or step.get("partial") is True or step.get("local_view") is True:
        return True
    text = " ".join(str(step.get(field, "")) for field in ("title", "purpose", "guide_text")).lower()
    return any(
        token in text
        for token in ("observe", "observation", "partial", "asset", "image2", "png", "smoke", "局部", "观察", "觀察", "素材", "预览")
    )


def explicitly_partial_observation(step: dict[str, Any]) -> bool:
    return bool(step.get("partial_observation") is True or step.get("partial") is True or step.get("local_view") is True)


def validate_data_url(errors: list[str], value: Any, where: str) -> None:
    if not isinstance(value, str):
        fail(errors, f"{where}.image must be a string")
        return
    if not value.startswith("data:"):
        return
    header, sep, payload = value.partition(",")
    if not sep or ";base64" not in header:
        fail(errors, f"{where}.image data URL must include a base64 payload")
        return
    media_type = header[5:].split(";", 1)[0]
    if media_type not in {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}:
        fail(errors, f"{where}.image data URL has unsupported media type {media_type!r}")
    try:
        decoded = base64.b64decode(payload, validate=True)
    except Exception as exc:  # noqa: BLE001 - report malformed payloads in CLI output.
        fail(errors, f"{where}.image data URL payload is not valid base64: {exc}")
        return
    if not decoded:
        fail(errors, f"{where}.image data URL payload is empty")


def object_extent(obj: dict[str, Any]) -> tuple[float, float, float, float]:
    x = float(obj.get("x", 0) or 0)
    y = float(obj.get("y", 0) or 0)
    x_radius = 0.0
    y_radius = 0.0
    radius = obj.get("radius")
    inner_radius = obj.get("innerRadius")
    for value in (radius, inner_radius):
        if isinstance(value, (int, float)):
            x_radius = max(x_radius, abs(float(value)))
            y_radius = max(y_radius, abs(float(value)))
    width = obj.get("width")
    height = obj.get("height")
    if isinstance(width, (int, float)):
        x_radius = max(x_radius, abs(float(width)) / 2)
    if isinstance(height, (int, float)):
        y_radius = max(y_radius, abs(float(height)) / 2)
    return x, y, x_radius, y_radius


def arena_bounds(scene: dict[str, Any]) -> tuple[float, float]:
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    width = arena.get("width", 600)
    height = arena.get("height", 600)
    if not isinstance(width, (int, float)):
        width = 600
    if not isinstance(height, (int, float)):
        height = 600
    return float(width) / 2 + OBJECT_BOUND_MARGIN, float(height) / 2 + OBJECT_BOUND_MARGIN


def object_role(obj: dict[str, Any]) -> str:
    for key in ("role", "name", "label"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip() in PARTY_ROLE_NAMES:
            return value.strip()
    return ""


def object_waymark(obj: dict[str, Any]) -> str:
    if obj.get("type") != "marker":
        return ""
    for key in ("marker", "name", "label"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip().upper() in WAYMARK_NAMES:
            return value.strip().upper()
    return ""


def normalize_scene_contract(scene: dict[str, Any]) -> tuple[dict[str, bool], bool]:
    raw_contract = scene.get("scene_contract")
    if raw_contract is None:
        return dict(DEFAULT_SCENE_CONTRACT), False
    if not isinstance(raw_contract, dict):
        return dict(DEFAULT_SCENE_CONTRACT), True
    contract = dict(DEFAULT_SCENE_CONTRACT)
    for key in contract:
        if key in raw_contract:
            contract[key] = bool(raw_contract[key])
    return contract, True


def partial_observation_has_reason(step: dict[str, Any]) -> bool:
    text = str(step.get("guide_text", "")).strip()
    if len(text) < 12:
        return False
    reason_tokens = ("because", "why", "partial", "observation", "局部", "观察", "觀察", "只展示", "用于", "因为", "原因", "素材")
    return any(token in text.lower() for token in reason_tokens)


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
    bound_x, bound_y = arena_bounds(scene)
    contract, contract_active = normalize_scene_contract(scene)
    if contract_active and not isinstance(scene.get("scene_contract"), dict):
        fail(errors, "root.scene_contract must be an object")

    for step_index, step in enumerate(steps):
        where_step = f"steps[{step_index}]"
        if not isinstance(step, dict):
            fail(errors, f"{where_step} must be an object")
            continue
        if not isinstance(step.get("title"), str) or not step.get("title", "").strip():
            fail(errors, f"{where_step}.title must be a non-empty string")
        elif len(step["title"]) > TEXT_FIELD_LIMIT:
            fail(errors, f"{where_step}.title is too long for a diagram label")
        if "title" in step and not isinstance(step["title"], str):
            fail(errors, f"{where_step}.title must be a string")
        if "purpose" in step and not isinstance(step["purpose"], str):
            fail(errors, f"{where_step}.purpose must be a string")
        if not isinstance(step.get("guide_text"), str) or not step.get("guide_text", "").strip():
            fail(errors, f"{where_step}.guide_text must be a non-empty string")
        elif len(step["guide_text"]) > GUIDE_TEXT_LIMIT:
            fail(errors, f"{where_step}.guide_text is too long; split the step or shorten on-figure prose")
        if "guide_text" in step and not isinstance(step["guide_text"], str):
            fail(errors, f"{where_step}.guide_text must be a string")
        if "checks" in step and not isinstance(step["checks"], list):
            fail(errors, f"{where_step}.checks must be a list")
        objects = step.get("objects")
        if not isinstance(objects, list):
            fail(errors, f"{where_step}.objects must be a list")
            continue
        party_objects: list[tuple[str, float, float, int]] = []
        step_type_counts: Counter[str] = Counter()
        step_waymarks: set[str] = set()
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
            step_type_counts[obj_type] += 1

            missing = REQUIRED_BY_TYPE.get(obj_type, set()) - obj.keys()
            if missing:
                fail(errors, f"{where} ({obj_type}) missing required fields: {', '.join(sorted(missing))}")

            if obj_type in IMAGE_TYPES and "image" in obj:
                validate_data_url(errors, obj.get("image"), where)
            for text_key in ("text", "label", "name"):
                text_value = obj.get(text_key)
                if isinstance(text_value, str) and len(text_value) > TEXT_FIELD_LIMIT:
                    fail(errors, f"{where}.{text_key} is too long for on-figure text")

            for key in (
                "x",
                "y",
                "width",
                "height",
                "radius",
                "innerRadius",
                "rotation",
                "opacity",
                "count",
                "coneAngle",
                "sides",
                "spokes",
                "spokeWidth",
                "length",
                "spacing",
            ):
                expect_number(errors, obj, key, where)
            if obj_type == "marker" and obj.get("shape") not in {"circle", "square"}:
                fail(errors, f"{where}.shape must be circle or square")
            if obj_type == "polygon" and obj.get("orient") not in {"point", "side"}:
                fail(errors, f"{where}.orient must be point or side")
            if isinstance(obj.get("x"), (int, float)) and isinstance(obj.get("y"), (int, float)):
                x, y, x_radius, y_radius = object_extent(obj)
                if abs(x) + x_radius > bound_x or abs(y) + y_radius > bound_y:
                    fail(errors, f"{where} ({obj_type}) is outside arena bounds")
            if obj_type == "party" and isinstance(obj.get("x"), (int, float)) and isinstance(obj.get("y"), (int, float)):
                party_objects.append((object_role(obj), float(obj["x"]), float(obj["y"]), int(obj_id) if isinstance(obj_id, int) else -1))
            waymark = object_waymark(obj)
            if waymark:
                step_waymarks.add(waymark)

        partial_observation = explicitly_partial_observation(step) if contract_active else looks_like_observation_step(step)
        if contract_active and partial_observation:
            if not contract["allow_partial_observation"]:
                fail(errors, f"{where_step} uses partial observation but scene_contract.allow_partial_observation is false")
            elif not partial_observation_has_reason(step):
                fail(errors, f"{where_step} partial_observation requires guide_text explaining why the step can omit full context")

        if len(party_objects) < 8 and not partial_observation:
            fail(errors, f"{where_step} has {len(party_objects)} party objects; use 8 players or mark the step as partial/observation")
        if contract_active and contract["require_full_party_each_step"] and not partial_observation:
            present_roles = {role for role, *_ in party_objects if role}
            missing_roles = sorted(PARTY_ROLE_NAMES - present_roles)
            if missing_roles:
                fail(errors, f"{where_step} missing required party roles: {', '.join(missing_roles)}")
        if contract_active and contract["require_enemy_each_step"] and not partial_observation and step_type_counts["enemy"] < 1:
            fail(errors, f"{where_step} is missing a Boss/enemy anchor")
        if contract_active and contract["require_waymarks_each_step"] and not partial_observation:
            missing_waymarks = sorted({"A", "B", "C", "D"} - step_waymarks)
            if missing_waymarks:
                fail(errors, f"{where_step} missing required waymarks: {', '.join(missing_waymarks)}")
        for left_index, left in enumerate(party_objects):
            for right in party_objects[left_index + 1 :]:
                if hypot(left[1] - right[1], left[2] - right[2]) < PARTY_OVERLAP_DISTANCE:
                    left_name = left[0] or f"id {left[3]}"
                    right_name = right[0] or f"id {right[3]}"
                    fail(errors, f"{where_step}: party objects {left_name} and {right_name} overlap")

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
