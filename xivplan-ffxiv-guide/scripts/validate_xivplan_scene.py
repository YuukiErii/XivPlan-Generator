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
PARTY_CLUSTER_DISTANCE = 42
PARTY_ROLE_NAMES = {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"}
WAYMARK_NAMES = {"A", "B", "C", "D", "1", "2", "3", "4"}
DEFAULT_PARTY_JOBS = {
    "MT": {"DRK", "DK", "DARK KNIGHT"},
    "ST": {"PLD", "PALADIN"},
    "H1": {"AST", "ASTROLOGIAN"},
    "H2": {"SCH", "SCHOLAR"},
    "D1": {"SAM", "SAMURAI"},
    "D2": {"DRG", "DRAGOON"},
    "D3": {"BRD", "BARD"},
    "D4": {"PCT", "PICTOMANCER"},
}
DEFAULT_PARTY_ICONS = {
    "MT": "/actor/DRK.png",
    "ST": "/actor/PLD.png",
    "H1": "/actor/AST.png",
    "H2": "/actor/SCH.png",
    "D1": "/actor/SAM.png",
    "D2": "/actor/DRG.png",
    "D3": "/actor/BRD.png",
    "D4": "/actor/PCT.png",
}
ROLE_NUMBER_PARTY_ICONS = {
    "MT": "/actor/tank1.png",
    "ST": "/actor/tank2.png",
    "H1": "/actor/healer1.png",
    "H2": "/actor/healer2.png",
    "D1": "/actor/dps1.png",
    "D2": "/actor/dps2.png",
    "D3": "/actor/dps3.png",
    "D4": "/actor/dps4.png",
}

DEFAULT_SCENE_CONTRACT = {
    "require_full_party_each_step": False,
    "require_enemy_each_step": False,
    "require_waymarks_each_step": False,
    "allow_partial_observation": True,
}
ANNOTATION_CONTRACT_BOOL_FIELDS = {
    "require_in_scene_teaching",
    "prefer_axis_and_priority_labels",
    "convert_guide_text_to_footer",
}
ANNOTATION_CONTRACT_INT_FIELDS = {"min_callouts_per_step", "max_callout_chars"}
MECHANIC_SEMANTICS_CONTRACT_BOOL_FIELDS = {
    "require_arrow_semantics",
    "require_range_semantics",
    "require_resolve_geometry",
    "require_danger_crossing_declaration",
}
STATUS_ASSIGNMENT_CONTRACT_BOOL_FIELDS = {
    "require_status_overlays",
    "require_all_assigned_roles_visible",
    "require_status_icon_readability",
    "require_fallback_reason",
}
ROUTE_SOURCE_KEYS = ("fromRole", "fromObject", "fromMarker")
ROUTE_TARGET_KEYS = ("toRole", "toObject", "toMarker", "toZone")
RANGE_SEMANTIC_TYPES = {"circle", "cone", "rect", "tower", "stack"}
REAL_RESOLVE_GEOMETRY_TYPES = {"cone", "rect", "tower", "stack"}


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


def validate_data_url(errors: list[str], value: Any, where: str, field: str = "image") -> None:
    if not isinstance(value, str):
        fail(errors, f"{where}.{field} must be a string")
        return
    if not value.startswith("data:"):
        return
    header, sep, payload = value.partition(",")
    if not sep or ";base64" not in header:
        fail(errors, f"{where}.{field} data URL must include a base64 payload")
        return
    media_type = header[5:].split(";", 1)[0]
    if media_type not in {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}:
        fail(errors, f"{where}.{field} data URL has unsupported media type {media_type!r}")
    try:
        decoded = base64.b64decode(payload, validate=True)
    except Exception as exc:  # noqa: BLE001 - report malformed payloads in CLI output.
        fail(errors, f"{where}.{field} data URL payload is not valid base64: {exc}")
        return
    if not decoded:
        fail(errors, f"{where}.{field} data URL payload is empty")


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


def party_job(obj: dict[str, Any]) -> str:
    value = obj.get("job") or obj.get("jobName") or obj.get("job_name")
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def party_icon(obj: dict[str, Any]) -> str:
    value = obj.get("icon") or obj.get("image")
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def normalized_icon(value: str) -> str:
    return value.replace("\\", "/")


def party_role_label(obj: dict[str, Any]) -> str:
    value = obj.get("roleLabel") or obj.get("role_label")
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def role_label_visible(obj: dict[str, Any]) -> bool:
    return obj.get("roleLabelVisible", obj.get("role_label_visible", True)) is not False


def party_display_style(obj: dict[str, Any], scene: dict[str, Any]) -> str:
    value = obj.get("partyDisplayStyle") or obj.get("party_display_style")
    if isinstance(value, str) and value.strip():
        normalized = value.strip().lower().replace("_", "-")
        if normalized in {"role-number", "role-number-icon", "role-number-icons", "numbered-role-icon"}:
            return "role-number-icon"
        if normalized in {"job", "job-icon", "job-icons", "job-default"}:
            return "job-icon"
    scene_policy = scene.get("party_display_policy")
    if isinstance(scene_policy, str) and scene_policy.strip():
        normalized = scene_policy.strip().lower().replace("_", "-")
        if normalized in {"role-number", "role-number-icon", "role-number-icons", "numbered-role-icon"}:
            return "role-number-icon"
        if normalized in {"job", "job-icon", "job-icons", "job-default"}:
            return "job-icon"
    return "role-number-icon" if scene.get("guide_section") == "mechanic_flow" else "job-icon"


def object_waymark(obj: dict[str, Any]) -> str:
    if obj.get("type") != "marker":
        return ""
    for key in ("marker", "name", "label"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip().upper() in WAYMARK_NAMES:
            return value.strip().upper()
    return ""


def enemy_display_name(obj: dict[str, Any]) -> str:
    for key in ("displayName", "name"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def enemy_ring_visible(obj: dict[str, Any]) -> bool:
    ring = obj.get("targetRing", obj.get("ring"))
    if isinstance(ring, dict):
        return ring.get("visible", True) is not False and isinstance(ring.get("radius", obj.get("radius")), (int, float))
    if isinstance(ring, str):
        return ring.strip().lower() not in {"", "none", "hidden", "false"}
    return bool(ring)


def party_cluster_step(step: dict[str, Any], party_objects: list[dict[str, Any]]) -> bool:
    if step.get("party_cluster") or step.get("stack_group"):
        return True
    for left_index, left in enumerate(party_objects):
        if not isinstance(left.get("x"), (int, float)) or not isinstance(left.get("y"), (int, float)):
            continue
        for right in party_objects[left_index + 1 :]:
            if not isinstance(right.get("x"), (int, float)) or not isinstance(right.get("y"), (int, float)):
                continue
            if hypot(float(left["x"]) - float(right["x"]), float(left["y"]) - float(right["y"])) < PARTY_CLUSTER_DISTANCE:
                return True
    return False


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


def mechanic_semantics_contract(scene: dict[str, Any]) -> dict[str, bool]:
    raw_contract = scene.get("mechanic_semantics_contract")
    if not isinstance(raw_contract, dict):
        return {}
    return {key: bool(raw_contract.get(key)) for key in MECHANIC_SEMANTICS_CONTRACT_BOOL_FIELDS}


def status_assignment_contract(scene: dict[str, Any]) -> dict[str, bool]:
    raw_contract = scene.get("status_assignment_contract")
    if not isinstance(raw_contract, dict):
        return {}
    return {key: bool(raw_contract.get(key)) for key in STATUS_ASSIGNMENT_CONTRACT_BOOL_FIELDS}


def status_assignment_role(assignment: dict[str, Any]) -> str:
    value = assignment.get("role")
    if isinstance(value, str) and value.upper() in PARTY_ROLE_NAMES:
        return value.upper()
    return ""


def status_visible_on_step(assignment: dict[str, Any], step_index: int) -> bool:
    visible = assignment.get("visibleSteps", assignment.get("visible_steps"))
    if visible is None:
        return True
    if isinstance(visible, str):
        return visible.strip().lower() in {"all", "*", "normal"}
    if not isinstance(visible, list):
        return False
    for item in visible:
        if isinstance(item, int) and item == step_index:
            return True
        if isinstance(item, str) and item.strip().lower() in {"all", "*"}:
            return True
        if isinstance(item, list) and len(item) == 2 and all(isinstance(value, int) for value in item):
            start, end = item
            if start <= step_index <= end:
                return True
    return False


def has_semantic_value(obj: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(obj.get(key) not in (None, "", [], {}) for key in keys)


def step_requires_semantic_routes(step: dict[str, Any]) -> bool:
    if step.get("movement_required") is True:
        return True
    return str(step.get("storyboard_phase", "")) in {"first_move", "second_move", "move", "reset", "next_read_setup"}


def is_resolve_step(step: dict[str, Any]) -> bool:
    return str(step.get("storyboard_phase", "")) in {"first_resolve", "second_resolve", "resolve"}


def damage_pattern(obj: dict[str, Any]) -> dict[str, Any]:
    value = obj.get("damagePattern")
    return value if isinstance(value, dict) else {}


def pattern_value(obj: dict[str, Any], key: str) -> Any:
    pattern = damage_pattern(obj)
    return pattern[key] if key in pattern else obj.get(key)


def validate_arrow_semantics(errors: list[str], arrow: dict[str, Any], where: str) -> None:
    if not has_semantic_value(arrow, ROUTE_SOURCE_KEYS):
        fail(errors, f"{where} semantic route requires fromRole, fromObject, or fromMarker")
    if not has_semantic_value(arrow, ROUTE_TARGET_KEYS):
        fail(errors, f"{where} semantic route requires toRole, toObject, toMarker, or toZone")
    if not isinstance(arrow.get("routeIntent"), str) or not arrow.get("routeIntent", "").strip():
        fail(errors, f"{where} semantic route requires routeIntent")
    if not isinstance(arrow.get("resolveIndex"), int):
        fail(errors, f"{where} semantic route requires integer resolveIndex")
    if not isinstance(arrow.get("snapToTarget"), bool):
        fail(errors, f"{where} semantic route requires boolean snapToTarget")


def validate_range_semantics(errors: list[str], obj: dict[str, Any], where: str) -> None:
    pattern = damage_pattern(obj)
    if not pattern:
        return
    required = ("kind", "label", "source", "targets", "resolveIndex", "resolveTiming", "aoeIntent")
    missing = [key for key in required if pattern_value(obj, key) in (None, "")]
    if missing:
        fail(errors, f"{where} semantic range is missing: {', '.join(missing)}")
    targets = pattern_value(obj, "targets")
    if not isinstance(targets, list):
        fail(errors, f"{where} semantic range targets must be a list")
    if not isinstance(pattern_value(obj, "resolveIndex"), int):
        fail(errors, f"{where} semantic range resolveIndex must be an integer")


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
    annotation_contract = scene.get("annotation_contract")
    if annotation_contract is not None:
        if not isinstance(annotation_contract, dict):
            fail(errors, "root.annotation_contract must be an object")
        else:
            for key in ANNOTATION_CONTRACT_BOOL_FIELDS:
                if key in annotation_contract and not isinstance(annotation_contract[key], bool):
                    fail(errors, f"root.annotation_contract.{key} must be a boolean")
            for key in ANNOTATION_CONTRACT_INT_FIELDS:
                if key in annotation_contract and not isinstance(annotation_contract[key], int):
                    fail(errors, f"root.annotation_contract.{key} must be an integer")
    semantics_contract = scene.get("mechanic_semantics_contract")
    if semantics_contract is not None:
        if not isinstance(semantics_contract, dict):
            fail(errors, "root.mechanic_semantics_contract must be an object")
        else:
            for key in MECHANIC_SEMANTICS_CONTRACT_BOOL_FIELDS:
                if key in semantics_contract and not isinstance(semantics_contract[key], bool):
                    fail(errors, f"root.mechanic_semantics_contract.{key} must be a boolean")
    semantics_policy = mechanic_semantics_contract(scene)
    status_contract = scene.get("status_assignment_contract")
    if status_contract is not None:
        if not isinstance(status_contract, dict):
            fail(errors, "root.status_assignment_contract must be an object")
        else:
            for key in STATUS_ASSIGNMENT_CONTRACT_BOOL_FIELDS:
                if key in status_contract and not isinstance(status_contract[key], bool):
                    fail(errors, f"root.status_assignment_contract.{key} must be a boolean")
    status_policy = status_assignment_contract(scene)
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
        party_full_objects: list[dict[str, Any]] = []
        enemy_objects: list[dict[str, Any]] = []
        text_labels: list[str] = []
        arrow_objects: list[tuple[str, dict[str, Any]]] = []
        semantic_range_objects: list[tuple[str, dict[str, Any]]] = []
        status_overlays: list[dict[str, Any]] = []
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
            if obj_type == "enemy" and "icon" in obj:
                validate_data_url(errors, obj.get("icon"), where, "icon")
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
                party_full_objects.append(obj)
            if obj_type == "enemy":
                enemy_objects.append(obj)
            if obj_type == "text" and isinstance(obj.get("text"), str):
                text_labels.append(obj["text"].strip())
            if obj_type == "arrow":
                arrow_objects.append((where, obj))
            if obj_type in RANGE_SEMANTIC_TYPES and damage_pattern(obj):
                semantic_range_objects.append((where, obj))
            if obj.get("statusOverlay") is True:
                status_overlays.append(obj)
                status_role = obj.get("statusRole") or obj.get("anchorRole")
                if not isinstance(status_role, str) or status_role.upper() not in PARTY_ROLE_NAMES:
                    fail(errors, f"{where} status overlay must carry statusRole/anchorRole MT/ST/H1/H2/D1/D2/D3/D4")
                if not isinstance(obj.get("statusName"), str) or not obj.get("statusName", "").strip():
                    fail(errors, f"{where} status overlay must carry statusName")
                if status_policy.get("require_status_icon_readability"):
                    width = obj.get("width")
                    height = obj.get("height")
                    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)) or min(width, height) < 13:
                        fail(errors, f"{where} status overlay icon is below the 13 px readability floor")
                if status_policy.get("require_fallback_reason") and obj.get("assetStatus") == "fallback" and not str(obj.get("fallbackReason", "")).strip():
                    fail(errors, f"{where} fallback status icon must record fallbackReason")
            waymark = object_waymark(obj)
            if waymark:
                step_waymarks.add(waymark)

        partial_observation = explicitly_partial_observation(step) if contract_active else looks_like_observation_step(step)
        if semantics_policy.get("require_arrow_semantics") and step_requires_semantic_routes(step):
            if not arrow_objects:
                fail(errors, f"{where_step} movement/reset step requires a semantic route arrow")
            for where_arrow, arrow in arrow_objects:
                validate_arrow_semantics(errors, arrow, where_arrow)
        if semantics_policy.get("require_range_semantics"):
            for where_range, range_obj in semantic_range_objects:
                validate_range_semantics(errors, range_obj, where_range)
        if semantics_policy.get("require_resolve_geometry") and is_resolve_step(step):
            resolve_ranges = [
                obj
                for _where_range, obj in semantic_range_objects
                if obj.get("type") in REAL_RESOLVE_GEOMETRY_TYPES
                and pattern_value(obj, "aoeIntent") != "reference_only"
            ]
            if not resolve_ranges:
                fail(errors, f"{where_step} resolve step requires semantic AoE geometry")
        if contract_active and partial_observation:
            if not contract["allow_partial_observation"]:
                fail(errors, f"{where_step} uses partial observation but scene_contract.allow_partial_observation is false")
            elif not partial_observation_has_reason(step):
                fail(errors, f"{where_step} partial_observation requires guide_text explaining why the step can omit full context")
        assignments = step.get("statusAssignments", step.get("status_assignments", []))
        if status_policy.get("require_status_overlays"):
            if not isinstance(assignments, list) or not assignments:
                fail(errors, f"{where_step} status_assignment_contract requires statusAssignments")
            else:
                overlay_roles = {
                    str(obj.get("statusRole") or obj.get("anchorRole") or "").upper()
                    for obj in status_overlays
                    if isinstance(obj.get("statusRole") or obj.get("anchorRole"), str)
                }
                party_ids_by_role = {role: obj_id for role, _x, _y, obj_id in party_objects if role}
                for assignment in assignments:
                    if not isinstance(assignment, dict):
                        fail(errors, f"{where_step}.statusAssignments entries must be objects")
                        continue
                    role = status_assignment_role(assignment)
                    if not role:
                        fail(errors, f"{where_step}.statusAssignments entry must have role MT/ST/H1/H2/D1/D2/D3/D4")
                        continue
                    if not isinstance(assignment.get("statusName", assignment.get("status_name")), str):
                        fail(errors, f"{where_step}.statusAssignments[{role}] must have statusName")
                    if status_visible_on_step(assignment, step_index + 1):
                        role_overlays = [
                            obj
                            for obj in status_overlays
                            if str(obj.get("statusRole") or obj.get("anchorRole") or "").upper() == role
                        ]
                        if not role_overlays:
                            fail(errors, f"{where_step} missing visible status overlay for {role}")
                        for overlay in role_overlays:
                            if overlay.get("anchorPartyId") != party_ids_by_role.get(role):
                                fail(errors, f"{where_step} status overlay for {role} is not anchored to that party object")
                if status_policy.get("require_all_assigned_roles_visible"):
                    visible_roles = {
                        status_assignment_role(item)
                        for item in assignments
                        if isinstance(item, dict) and status_visible_on_step(item, step_index + 1)
                    }
                    missing_visible = sorted(role for role in visible_roles if role and role not in overlay_roles)
                    if missing_visible:
                        fail(errors, f"{where_step} missing status overlays for assigned roles: {', '.join(missing_visible)}")

        if len(party_objects) < 8 and not partial_observation:
            fail(errors, f"{where_step} has {len(party_objects)} party objects; use 8 players or mark the step as partial/observation")
        if contract_active and contract["require_full_party_each_step"] and not partial_observation:
            present_roles = {role for role, *_ in party_objects if role}
            missing_roles = sorted(PARTY_ROLE_NAMES - present_roles)
            if missing_roles:
                fail(errors, f"{where_step} missing required party roles: {', '.join(missing_roles)}")
            duplicate_roles = sorted(role for role, count in Counter(role for role, *_ in party_objects if role).items() if count > 1)
            if duplicate_roles:
                fail(errors, f"{where_step} has duplicate party roles: {', '.join(duplicate_roles)}")
            cluster_step = party_cluster_step(step, party_full_objects)
            for party_index, party in enumerate(party_full_objects):
                role = object_role(party)
                where_party = f"{where_step}.party[{party_index}]"
                if not role:
                    fail(errors, f"{where_party} must have one MT/ST/H1/H2/D1/D2/D3/D4 role")
                    continue
                job = party_job(party)
                icon = party_icon(party)
                if not job:
                    fail(errors, f"{where_party} ({role}) must have a job for Phase R identity")
                if not icon:
                    fail(errors, f"{where_party} ({role}) must have a job icon or fallback image")
                if party.get("jobDefault") is True and job.upper() not in DEFAULT_PARTY_JOBS.get(role, set()):
                    fail(errors, f"{where_party} ({role}) default job mismatch: {job}")
                display_style = party_display_style(party, scene)
                if display_style == "role-number-icon":
                    expected_icon = ROLE_NUMBER_PARTY_ICONS.get(role)
                    if normalized_icon(icon) != expected_icon:
                        fail(errors, f"{where_party} ({role}) must use official numbered role icon {expected_icon}, got {icon}")
                elif party.get("jobDefault") is True and normalized_icon(icon) != DEFAULT_PARTY_ICONS.get(role):
                    fail(errors, f"{where_party} ({role}) must use official XivPlan job icon {DEFAULT_PARTY_ICONS.get(role)}, got {icon}")
                if normalized_icon(icon).startswith("job:"):
                    fail(errors, f"{where_party} ({role}) uses abstract job token {icon}; use a XivPlan /actor/<JOB>.png icon")
                if display_style == "job-icon" and not cluster_step and not role_label_visible(party):
                    fail(errors, f"{where_party} ({role}) hides roleLabel outside a cluster/stack frame")
                if display_style == "job-icon" and not cluster_step and not party_role_label(party):
                    fail(errors, f"{where_party} ({role}) must have roleLabel near the job icon")
        if contract_active and contract["require_enemy_each_step"] and not partial_observation and step_type_counts["enemy"] < 1:
            fail(errors, f"{where_step} is missing a Boss/enemy anchor")
        if not partial_observation:
            enemy_names = [enemy_display_name(obj) for obj in enemy_objects]
            for enemy_index, enemy in enumerate(enemy_objects):
                where_enemy = f"{where_step}.enemy[{enemy_index}]"
                name = enemy_display_name(enemy)
                if not name:
                    fail(errors, f"{where_enemy} must have a non-empty name/displayName")
                if not isinstance(enemy.get("radius"), (int, float)):
                    target_ring = enemy.get("targetRing")
                    ring_radius = target_ring.get("radius") if isinstance(target_ring, dict) else None
                    if not isinstance(ring_radius, (int, float)):
                        fail(errors, f"{where_enemy} must have radius or targetRing.radius")
                if not enemy_ring_visible(enemy):
                    fail(errors, f"{where_enemy} target ring must be visible")
                icon = enemy.get("icon") or enemy.get("image")
                if not isinstance(icon, str) or not icon.strip():
                    fail(errors, f"{where_enemy} must have an icon or fallback icon")
                if name and name not in text_labels:
                    fail(errors, f"{where_enemy} name label is missing from text layer: {name}")
            duplicate_enemy_names = sorted(name for name, count in Counter(enemy_names).items() if name and count > 1)
            if duplicate_enemy_names:
                fail(errors, f"{where_step} has indistinguishable duplicate enemy names: {', '.join(duplicate_enemy_names)}")
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
