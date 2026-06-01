#!/usr/bin/env python3
"""Comprehensive Phase G visual quality audit for XivPlan scenes."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from audit_flow_lines import audit_scene as audit_flow_scene
from audit_label_layout import audit_scene as audit_label_scene
from audit_storyboard_steps import audit_scene as audit_storyboard_scene
from audit_visual_density import audit_scene as audit_density_scene


PARTY_ROLES = {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"}
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
WAYMARKS = {"A", "B", "C", "D"}
MECHANIC_TYPES = {
    "arc",
    "circle",
    "cone",
    "donut",
    "exaflare",
    "eye",
    "knockback",
    "line",
    "lineStack",
    "polygon",
    "proximity",
    "rect",
    "stack",
    "starburst",
    "tower",
    "triangle",
}
FLOW_TYPES = {"arrow", "tether"}
TEXT_PHASE_HINTS = {
    "observe": ("observe", "观察", "读取", "确认", "初始", "预站"),
    "move": ("move", "移动", "路线", "入塔", "拉线", "击退", "散开"),
    "resolve": ("resolve", "判定", "结算", "分摊", "塔", "安全"),
    "reset": ("reset", "复位", "回中", "下一", "起手"),
}
SCORE_DIMENSIONS = ("context", "density", "label", "flow", "layer", "aesthetic", "step_story", "enemy_identity", "party_identity")
PHASE_BUCKETS = {
    "observe_signal": "observe",
    "assign_roles": "observe",
    "preposition": "move",
    "first_move": "move",
    "second_move": "move",
    "between_resolves": "move",
    "first_resolve": "resolve",
    "second_resolve": "resolve",
    "next_read_setup": "reset",
}


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def text_for_step(step: dict[str, Any]) -> str:
    return " ".join(str(step.get(key, "")) for key in ("title", "purpose", "guide_text", "reset_state")).lower()


def step_phase(step: dict[str, Any]) -> str:
    explicit = step.get("storyboard_phase")
    if isinstance(explicit, str) and explicit:
        return PHASE_BUCKETS.get(explicit, explicit)
    text = text_for_step(step)
    if any(hint in text for hint in TEXT_PHASE_HINTS["reset"]):
        return "reset"
    for phase, hints in TEXT_PHASE_HINTS.items():
        if phase == "reset":
            continue
        if any(hint in text for hint in hints):
            return phase
    return "unknown"


def step_requires_flow(step: dict[str, Any]) -> tuple[bool, bool]:
    explicit = step.get("movement_required")
    if explicit is True:
        return True, True
    if explicit is False:
        return False, False
    phase = step_phase(step)
    if phase in {"move", "reset"}:
        return True, False
    return False, False


def is_partial_step(step: dict[str, Any]) -> bool:
    return bool(step.get("partial_observation") or step.get("partial") or step.get("local_view"))


def object_role(obj: dict[str, Any]) -> str:
    if obj.get("type") != "party":
        return ""
    for key in ("role", "name", "label"):
        value = obj.get(key)
        if isinstance(value, str) and value.upper() in PARTY_ROLES:
            return value.upper()
    return ""


def party_job(obj: dict[str, Any]) -> str:
    if obj.get("type") != "party":
        return ""
    value = obj.get("job") or obj.get("jobName") or obj.get("job_name")
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def party_icon(obj: dict[str, Any]) -> str:
    if obj.get("type") != "party":
        return ""
    value = obj.get("icon") or obj.get("image")
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def normalized_icon(value: str) -> str:
    return value.replace("\\", "/")


def party_role_label(obj: dict[str, Any]) -> str:
    if obj.get("type") != "party":
        return ""
    value = obj.get("roleLabel") or obj.get("role_label")
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def role_label_visible(obj: dict[str, Any]) -> bool:
    return obj.get("roleLabelVisible", obj.get("role_label_visible", True)) is not False


def is_cluster_step(step: dict[str, Any], party: list[dict[str, Any]]) -> bool:
    if step.get("party_cluster") or step.get("stack_group"):
        return True
    for left_index, left in enumerate(party):
        for right in party[left_index + 1 :]:
            if not all(isinstance(item.get(key), (int, float)) for item in (left, right) for key in ("x", "y")):
                continue
            if ((float(left["x"]) - float(right["x"])) ** 2 + (float(left["y"]) - float(right["y"])) ** 2) ** 0.5 < 42:
                return True
    return False


def object_waymark(obj: dict[str, Any]) -> str:
    if obj.get("type") != "marker":
        return ""
    for key in ("name", "marker", "label"):
        value = obj.get(key)
        if isinstance(value, str) and value.upper() in WAYMARKS:
            return value.upper()
    return ""


def enemy_name(obj: dict[str, Any]) -> str:
    if obj.get("type") != "enemy":
        return ""
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


def object_box(obj: dict[str, Any], fallback_radius: float = 0.0) -> tuple[float, float, float, float]:
    x = float(obj.get("x", 0) or 0)
    y = float(obj.get("y", 0) or 0)
    half_w = fallback_radius
    half_h = fallback_radius
    radius = obj.get("radius")
    if isinstance(radius, (int, float)):
        half_w = max(half_w, abs(float(radius)))
        half_h = max(half_h, abs(float(radius)))
    width = obj.get("width")
    height = obj.get("height")
    if isinstance(width, (int, float)):
        half_w = max(half_w, abs(float(width)) / 2)
    if isinstance(height, (int, float)):
        half_h = max(half_h, abs(float(height)) / 2)
    if obj.get("type") == "text":
        text = str(obj.get("text", ""))
        font_size = float(obj.get("fontSize", 16) or 16)
        half_w = max(half_w, max(18.0, len(text) * font_size * 0.28))
        half_h = max(half_h, font_size * 0.7)
    return x - half_w, y - half_h, x + half_w, y + half_h


def boxes_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], padding: float = 0.0) -> bool:
    return not (a[2] + padding < b[0] or b[2] + padding < a[0] or a[3] + padding < b[1] or b[3] + padding < a[1])


def has_arena_context(scene: dict[str, Any]) -> bool:
    arena = scene.get("arena")
    if not isinstance(arena, dict):
        return False
    return any(arena.get(key) for key in ("backgroundImage", "preset", "shape", "grid"))


def add_issue(
    issues: list[dict[str, Any]],
    *,
    dimension: str,
    severity: str,
    kind: str,
    message: str,
    suggestion: str,
    step: int | None = None,
    title: str | None = None,
    object_id: Any = None,
    other_id: Any = None,
) -> None:
    issue: dict[str, Any] = {
        "dimension": dimension,
        "severity": severity,
        "kind": kind,
        "message": message,
        "suggestion": suggestion,
    }
    if step is not None:
        issue["step"] = step
    if title:
        issue["title"] = title
    if object_id is not None:
        issue["object_id"] = object_id
    if other_id is not None:
        issue["other_id"] = other_id
    issues.append(issue)


def score_from_counts(severe: int, review: int) -> int:
    return max(0, min(100, 100 - severe * 38 - review * 7))


def score_dimension(issues: list[dict[str, Any]], dimension: str) -> int:
    severe = sum(1 for issue in issues if issue["dimension"] == dimension and issue["severity"] == "severe")
    review = sum(1 for issue in issues if issue["dimension"] == dimension and issue["severity"] == "review")
    return score_from_counts(severe, review)


def scene_context_issues(scene: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if not has_arena_context(scene):
        add_issue(
            issues,
            dimension="context",
            severity="severe",
            kind="missing_arena_context",
            message="Scene root has no arena background, preset, shape, or grid context.",
            suggestion="Set `arena.preset`, `arena.shape`, or `arena.backgroundImage` before generating the scene.",
        )

    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict) or is_partial_step(step):
            continue
        objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
        roles = {role for obj in objects if (role := object_role(obj))}
        missing_roles = sorted(PARTY_ROLES - roles)
        if missing_roles:
            add_issue(
                issues,
                dimension="context",
                severity="severe",
                kind="missing_party_roles",
                step=step_index,
                title=step.get("title"),
                message=f"Step is missing party roles: {', '.join(missing_roles)}.",
                suggestion="Keep all eight role icons visible, using ghosted opacity for non-active roles.",
            )
        if not any(obj.get("type") == "enemy" for obj in objects):
            add_issue(
                issues,
                dimension="context",
                severity="severe",
                kind="missing_enemy_anchor",
                step=step_index,
                title=step.get("title"),
                message="Step has no Boss/enemy anchor.",
                suggestion="Add a Boss/enemy object or enable the scene contract enemy requirement.",
            )
        waymarks = {mark for obj in objects if (mark := object_waymark(obj))}
        missing_marks = sorted(WAYMARKS - waymarks)
        if missing_marks:
            add_issue(
                issues,
                dimension="context",
                severity="review",
                kind="missing_cardinal_waymarks",
                step=step_index,
                title=step.get("title"),
                message=f"Step is missing cardinal waymarks: {', '.join(missing_marks)}.",
                suggestion="Use `markerPresets: \"cardinals\"` or keep stable A/B/C/D waymarks across normal steps.",
            )


def density_issues(density: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if not density.get("ok", False):
        for step in density.get("dense_steps", []):
            add_issue(
                issues,
                dimension="density",
                severity="review",
                kind="dense_step",
                step=int(step),
                message="Step is denser than the current single-step focus threshold.",
                suggestion="Split this step or move long explanations into guide text.",
            )
        for layer in density.get("missing_required_layers", []):
            severity = "severe" if layer in {"party", "enemy", "mechanic_zone"} else "review"
            add_issue(
                issues,
                dimension="layer",
                severity=severity,
                kind="missing_required_layer",
                message=f"Scene is missing required visual layer: {layer}.",
                suggestion="Add the missing layer or confirm the scene is intentionally partial.",
            )
    avg = float(density.get("avg_objects_per_step", 0) or 0)
    if avg < 10:
        add_issue(
            issues,
            dimension="density",
            severity="review",
            kind="low_visual_density",
            message=f"Average objects per step is low ({avg}).",
            suggestion="Add stable context objects, mechanic source, labels, or transition arrows.",
        )


def label_issues(label_layout: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    for step in label_layout.get("per_step", []):
        for item in step.get("issues", []):
            severity = str(item.get("severity", "review"))
            add_issue(
                issues,
                dimension="label",
                severity=severity,
                kind=str(item.get("kind", "label_issue")),
                step=int(step.get("step", 0) or 0),
                title=step.get("title"),
                object_id=item.get("text_id"),
                other_id=item.get("other_id"),
                message=f"Label `{item.get('text', '')}` has a {item.get('kind', 'layout')} issue.",
                suggestion="Move the label outward, enable `labelPlacement: \"auto\"`, or add a leader line.",
            )


def flow_issues(flow_lines: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    for step in flow_lines.get("per_step", []):
        for item in step.get("issues", []):
            severity = str(item.get("severity", "review"))
            add_issue(
                issues,
                dimension="flow",
                severity=severity,
                kind=str(item.get("kind", "flow_issue")),
                step=int(step.get("step", 0) or 0),
                title=step.get("title"),
                object_id=item.get("arrow_id"),
                other_id=item.get("other_id"),
                message=f"Arrow has a {item.get('kind', 'flow')} issue.",
                suggestion="Use `waypoints`, `curve`, `startGap` / `endGap`, or split simultaneous movement into another step.",
            )


def layer_and_aesthetic_issues(scene: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    type_counts: Counter[str] = Counter()
    opacities: list[float] = []
    flow_required_steps = 0
    flow_required_missing = 0
    explicit_flow_missing = False
    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict):
            continue
        objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
        step_types = {str(obj.get("type")) for obj in objects}
        requires_flow, explicit_flow = step_requires_flow(step)
        if requires_flow:
            flow_required_steps += 1
            if FLOW_TYPES.isdisjoint(step_types):
                flow_required_missing += 1
                explicit_flow_missing = explicit_flow_missing or explicit_flow
                add_issue(
                    issues,
                    dimension="flow",
                    severity="severe" if explicit_flow or step_phase(step) in {"move", "reset"} else "review",
                    kind="step_missing_flow_layer",
                    step=step_index,
                    title=step.get("title"),
                    message="Movement/reset step has no explicit flow arrow or tether.",
                    suggestion="Add `arrowStyle` movement, reset, bait, knockback, or forbidden-route flow objects.",
                )
        type_counts.update(str(obj.get("type")) for obj in objects if obj.get("type"))
        if not any(obj.get("type") in MECHANIC_TYPES for obj in objects):
            add_issue(
                issues,
                dimension="layer",
                severity="review",
                kind="step_missing_mechanic_layer",
                step=step_index,
                title=step.get("title"),
                message="Step has context but no explicit mechanic/safety layer.",
                suggestion="Add the current AoE, tower, stack, safe zone, or mechanic source.",
            )
        if "text" not in step_types:
            add_issue(
                issues,
                dimension="layer",
                severity="review",
                kind="step_missing_text_layer",
                step=step_index,
                title=step.get("title"),
                message="Step has no text label layer.",
                suggestion="Add a short title/callout label, keeping long wording in guide text.",
            )
        for obj in objects:
            obj_type = obj.get("type")
            opacity = obj.get("opacity")
            if obj_type in MECHANIC_TYPES and isinstance(opacity, (int, float)):
                opacities.append(float(opacity))
                if float(opacity) > 75 and obj_type not in {"tower", "stack", "starburst"}:
                    add_issue(
                        issues,
                        dimension="aesthetic",
                        severity="review",
                        kind="high_opacity_mechanic",
                        step=step_index,
                        title=step.get("title"),
                        object_id=obj.get("id"),
                        message=f"{obj_type} opacity is high ({opacity}).",
                        suggestion="Use translucent fills for AoE/safe-zone shapes so players and labels remain readable.",
                    )
            if obj_type == "text" and len(str(obj.get("text", ""))) > 18:
                add_issue(
                    issues,
                    dimension="aesthetic",
                    severity="review",
                    kind="long_in_scene_label",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message="In-scene label is long and may be harder to scan.",
                    suggestion="Shorten the label and keep the explanation in `guide_text`.",
                )
    if FLOW_TYPES.isdisjoint(type_counts) and len(scene.get("steps", [])) >= 4:
        severity = "severe" if flow_required_steps and explicit_flow_missing else "review"
        add_issue(
            issues,
            dimension="layer",
            severity=severity,
            kind="scene_missing_flow_layer",
            message="Multi-step scene has no movement/flow arrows.",
            suggestion="Add movement, reset, bait, knockback, or forbidden-route arrows where players change position.",
        )
    if opacities:
        average_opacity = statistics.mean(opacities)
        if average_opacity < 12:
            add_issue(
                issues,
                dimension="aesthetic",
                severity="review",
                kind="very_low_average_mechanic_opacity",
                message=f"Average mechanic opacity is low ({round(average_opacity, 1)}).",
                suggestion="Increase opacity enough that safety/danger regions are visible in exported PNGs.",
            )


def enemy_identity_issues(scene: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict) or is_partial_step(step):
            continue
        objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
        enemies = [obj for obj in objects if obj.get("type") == "enemy"]
        labels = [obj for obj in objects if obj.get("type") == "text"]
        enemy_names = [enemy_name(enemy) for enemy in enemies]
        duplicates = sorted(name for name, count in Counter(enemy_names).items() if name and count > 1)
        for duplicate in duplicates:
            add_issue(
                issues,
                dimension="enemy_identity",
                severity="severe",
                kind="duplicate_enemy_name",
                step=step_index,
                title=step.get("title"),
                message=f"Multiple enemies share the indistinguishable name `{duplicate}`.",
                suggestion="Append a direction or index, such as Add N / Add E / Add 1.",
            )
        for enemy in enemies:
            name = enemy_name(enemy)
            enemy_id = enemy.get("id")
            if not name:
                add_issue(
                    issues,
                    dimension="enemy_identity",
                    severity="severe",
                    kind="enemy_missing_name",
                    step=step_index,
                    title=step.get("title"),
                    object_id=enemy_id,
                    message="Enemy has no readable name/displayName.",
                    suggestion="Set `name` or `displayName` for every Boss, add, clone, or source.",
                )
                continue
            if not enemy_ring_visible(enemy):
                add_issue(
                    issues,
                    dimension="enemy_identity",
                    severity="severe",
                    kind="enemy_missing_target_ring",
                    step=step_index,
                    title=step.get("title"),
                    object_id=enemy_id,
                    message=f"Enemy `{name}` has no visible target ring.",
                    suggestion="Set `ring.visible: true` or use the default target-ring contract.",
                )
            icon = enemy.get("icon") or enemy.get("image")
            if not isinstance(icon, str) or not icon.strip():
                add_issue(
                    issues,
                    dimension="enemy_identity",
                    severity="severe",
                    kind="enemy_missing_icon",
                    step=step_index,
                    title=step.get("title"),
                    object_id=enemy_id,
                    message=f"Enemy `{name}` has no dedicated or fallback icon.",
                    suggestion="Run `inject_enemy_assets.py` or let the builder attach the generic Boss/add fallback icon.",
                )
            if not isinstance(enemy.get("radius"), (int, float)):
                add_issue(
                    issues,
                    dimension="enemy_identity",
                    severity="severe",
                    kind="enemy_missing_radius",
                    step=step_index,
                    title=step.get("title"),
                    object_id=enemy_id,
                    message=f"Enemy `{name}` has no radius.",
                    suggestion="Set `radius` or `ring.radius` so the target ring is auditable.",
                )
            matching_labels = [label for label in labels if str(label.get("text", "")).strip() == name]
            if not matching_labels:
                add_issue(
                    issues,
                    dimension="enemy_identity",
                    severity="severe",
                    kind="enemy_missing_name_label",
                    step=step_index,
                    title=step.get("title"),
                    object_id=enemy_id,
                    message=f"Enemy `{name}` has no matching text label.",
                    suggestion="Let the builder create an attached auto label or add a short label outside the target ring.",
                )
            enemy_box = object_box(enemy, float(enemy.get("radius", 36) or 36))
            for label in labels:
                if label in matching_labels:
                    continue
                if label.get("labelKind") == "party_role":
                    continue
                if boxes_overlap(enemy_box, object_box(label), padding=4):
                    add_issue(
                        issues,
                        dimension="enemy_identity",
                        severity="severe",
                        kind="enemy_ring_text_obstruction",
                        step=step_index,
                        title=step.get("title"),
                        object_id=enemy_id,
                        other_id=label.get("id"),
                        message=f"Enemy `{name}` target ring is obstructed by a text label.",
                        suggestion="Move the label outward or add a leader line.",
                    )
            for mechanic in objects:
                if mechanic.get("type") not in MECHANIC_TYPES:
                    continue
                opacity = mechanic.get("opacity")
                if isinstance(opacity, (int, float)) and opacity >= 70 and boxes_overlap(enemy_box, object_box(mechanic), padding=0):
                    add_issue(
                        issues,
                        dimension="enemy_identity",
                        severity="review",
                        kind="enemy_ring_high_opacity_overlap",
                        step=step_index,
                        title=step.get("title"),
                        object_id=enemy_id,
                        other_id=mechanic.get("id"),
                        message=f"Enemy `{name}` target ring overlaps a high-opacity mechanic layer.",
                        suggestion="Lower mechanic opacity or split the mechanic source and damage layer into separate frames.",
                    )


def party_identity_issues(scene: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict) or is_partial_step(step):
            continue
        party = [obj for obj in step.get("objects", []) if isinstance(obj, dict) and obj.get("type") == "party"]
        roles = [object_role(obj) for obj in party]
        missing = sorted(PARTY_ROLES - set(role for role in roles if role))
        duplicates = sorted(role for role, count in Counter(role for role in roles if role).items() if count > 1)
        if missing:
            add_issue(
                issues,
                dimension="party_identity",
                severity="severe",
                kind="party_missing_roles",
                step=step_index,
                title=step.get("title"),
                message=f"Step is missing role identities: {', '.join(missing)}.",
                suggestion="Keep all MT/ST/H1/H2/D1/D2/D3/D4 party objects through movement and reset frames.",
            )
        if duplicates:
            add_issue(
                issues,
                dimension="party_identity",
                severity="severe",
                kind="party_duplicate_roles",
                step=step_index,
                title=step.get("title"),
                message=f"Step repeats role identities: {', '.join(duplicates)}.",
                suggestion="Each normal frame should contain each role exactly once.",
            )
        cluster_step = is_cluster_step(step, party)
        for obj in party:
            role = object_role(obj) or str(obj.get("name", "party"))
            if not party_job(obj):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity="severe",
                    kind="party_missing_job",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` has no job identity.",
                    suggestion="Set `job` and `icon` using the Phase R default party configuration or a user override.",
                )
            if not party_icon(obj):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity="severe",
                    kind="party_missing_job_icon",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` has no job icon or fallback image.",
                    suggestion="Keep a job icon on every party object, even when role labels are hidden in a cluster frame.",
                )
            elif normalized_icon(party_icon(obj)).startswith("job:"):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity="severe",
                    kind="party_abstract_job_icon",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` uses abstract icon token `{party_icon(obj)}` instead of a XivPlan job PNG.",
                    suggestion="Use the built-in XivPlan official job icon path, for example `/actor/DRK.png`.",
                )
            elif obj.get("jobDefault") is True and normalized_icon(party_icon(obj)) != DEFAULT_PARTY_ICONS.get(role):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity="severe",
                    kind="party_default_job_icon_mismatch",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` default icon should be `{DEFAULT_PARTY_ICONS.get(role)}`, got `{party_icon(obj)}`.",
                    suggestion="Keep default comp icons aligned with XivPlan `public/actor/<JOB>.png` assets.",
                )
            if not cluster_step and not party_role_label(obj):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity="severe",
                    kind="party_missing_role_label",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` has no readable roleLabel.",
                    suggestion="Place `MT/ST/H1/H2/D1/D2/D3/D4` near the job icon outside cluster/stack frames.",
                )
            if not cluster_step and not role_label_visible(obj):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity="severe",
                    kind="party_role_label_hidden",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` hides its role label outside a stack/cluster frame.",
                    suggestion="Only hide role labels when icons overlap heavily; keep the job icon visible.",
                )
            width = obj.get("width")
            height = obj.get("height")
            if isinstance(width, (int, float)) and isinstance(height, (int, float)) and min(width, height) < 24:
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity="severe",
                    kind="party_icon_too_small",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` job icon is below the 24 px readability floor.",
                    suggestion="Use `iconScale >= 0.72` or a larger base player icon size.",
                )


def story_issues(scene: dict[str, Any], storyboard: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if storyboard.get("applicable"):
        for item in storyboard.get("issues", []):
            add_issue(
                issues,
                dimension="step_story",
                severity=str(item.get("severity", "severe")),
                kind=str(item.get("kind", "storyboard_issue")),
                message=str(item.get("kind", "Storyboard issue")),
                suggestion="Add the missing storyboard phase or required step metadata.",
            )
        for step in storyboard.get("per_step", []):
            for item in step.get("issues", []):
                add_issue(
                    issues,
                    dimension="step_story",
                    severity=str(item.get("severity", "severe")),
                    kind=str(item.get("kind", "storyboard_step_issue")),
                    step=int(step.get("step", 0) or 0),
                    title=step.get("title"),
                    message=f"Storyboard metadata issue on field `{item.get('field', '')}`.",
                    suggestion="Populate storyboard metadata including `teaching_question`, `purpose`, `guide_text`, `checks`, `visual_focus`, `required_roles`, `reset_state`, and `storyboard_phase`.",
                )
        return

    phases = {step_phase(step) for step in scene.get("steps", []) if isinstance(step, dict)}
    if "reset" not in phases:
        add_issue(
            issues,
            dimension="step_story",
            severity="severe",
            kind="missing_reset_step",
            message="Scene has no reset / return-to-start / next-mechanic step.",
            suggestion="Add a final reset step such as `回中复位` or `下一机制起手`.",
        )
    for phase in ("observe", "move", "resolve"):
        if phase not in phases:
            add_issue(
                issues,
                dimension="step_story",
                severity="review",
                kind="missing_story_phase",
                message=f"Scene may be missing a `{phase}` story phase.",
                suggestion="Split the diagram into observe, movement, resolution, and reset steps when the mechanic is complex.",
            )


def audit_scene(path: Path) -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")

    density = audit_density_scene(path)
    label_layout = audit_label_scene(path)
    flow_lines = audit_flow_scene(path)
    storyboard = audit_storyboard_scene(path)

    issues: list[dict[str, Any]] = []
    scene_context_issues(scene, issues)
    density_issues(density, issues)
    label_issues(label_layout, issues)
    flow_issues(flow_lines, issues)
    layer_and_aesthetic_issues(scene, issues)
    story_issues(scene, storyboard, issues)
    enemy_identity_issues(scene, issues)
    party_identity_issues(scene, issues)

    scores = {f"{dimension}_score": score_dimension(issues, dimension) for dimension in SCORE_DIMENSIONS}
    overall_score = round(sum(scores.values()) / len(scores), 2)
    severe = sum(1 for issue in issues if issue["severity"] == "severe")
    review = sum(1 for issue in issues if issue["severity"] == "review")
    status = "FAIL" if severe else ("REVIEW" if review else "PASS")
    return {
        "path": str(path),
        "ok": severe == 0,
        "status": status,
        "overall_score": overall_score,
        "scores": scores,
        "severe_items": severe,
        "review_items": review,
        "steps": len(steps),
        "issues": issues,
        "components": {
            "density": density,
            "label_layout": label_layout,
            "flow_lines": flow_lines,
            "storyboard": storyboard,
        },
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Visual Quality Audit",
        "",
        "| Scene | Status | Score | Context | Density | Label | Flow | Layer | Aesthetic | Story | Enemy | Party | Severe | Review |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        scores = result["scores"]
        scene = scene_label(result["path"])
        lines.append(
            "| {scene} | {status} | {overall} | {context} | {density} | {label} | {flow} | {layer} | {aesthetic} | {story} | {enemy} | {party} | {severe} | {review} |".format(
                scene=scene,
                status=result["status"],
                overall=result["overall_score"],
                context=scores["context_score"],
                density=scores["density_score"],
                label=scores["label_score"],
                flow=scores["flow_score"],
                layer=scores["layer_score"],
                aesthetic=scores["aesthetic_score"],
                story=scores["step_story_score"],
                enemy=scores["enemy_identity_score"],
                party=scores["party_identity_score"],
                severe=result["severe_items"],
                review=result["review_items"],
            )
        )
    lines.extend(["", "## Issues", ""])
    for result in results:
        if not result["issues"]:
            lines.append(f"- {scene_label(result['path'])}: no issues")
            continue
        scene = scene_label(result["path"])
        for issue in result["issues"]:
            location = f" step {issue['step']}" if "step" in issue else ""
            obj = f" object={issue.get('object_id')}" if "object_id" in issue else ""
            other = f" other={issue.get('other_id')}" if "other_id" in issue else ""
            lines.append(
                "- {scene}{location}: [{severity}] {dimension}/{kind}{obj}{other} - {message} Fix: {suggestion}".format(
                    scene=scene,
                    location=location,
                    severity=issue["severity"],
                    dimension=issue["dimension"],
                    kind=issue["kind"],
                    obj=obj,
                    other=other,
                    message=issue["message"],
                    suggestion=issue["suggestion"],
                )
            )
    return "\n".join(lines) + "\n"


def expand_input_paths(paths: list[Path]) -> list[Path]:
    scene_paths: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path.is_dir():
            direct_files = sorted(path.glob("*.xivplan"))
            case_scenes = sorted(
                child / "scene.xivplan"
                for child in path.iterdir()
                if child.is_dir() and (child / "scene.xivplan").exists()
            )
            candidates = direct_files or case_scenes or sorted(path.rglob("*.xivplan"))
        else:
            candidates = [path]
        for candidate in candidates:
            normalized = candidate.resolve()
            if normalized in seen:
                continue
            seen.add(normalized)
            scene_paths.append(candidate)
    return scene_paths


def scene_label(path: str) -> str:
    scene_path = Path(path)
    if scene_path.name == "scene.xivplan" and scene_path.parent.name:
        return f"{scene_path.parent.name}/{scene_path.name}"
    return scene_path.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit visual quality with Phase G scoring.")
    parser.add_argument("paths", type=Path, nargs="+", help="One or more .xivplan files or directories")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        scene_paths = expand_input_paths(args.paths)
        if not scene_paths:
            raise ValueError("no .xivplan files found")
        results = [audit_scene(path) for path in scene_paths]
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
        print(
            f"{result['path']}: {result['status']} score={result['overall_score']} severe={result['severe_items']} review={result['review_items']}"
        )
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
