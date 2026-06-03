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
DEFAULT_JOB_BY_ICON = {icon: icon.rsplit("/", 1)[-1].split(".", 1)[0] for icon in DEFAULT_PARTY_ICONS.values()}
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
SCORE_DIMENSIONS = (
    "context",
    "density",
    "label",
    "flow",
    "layer",
    "aesthetic",
    "step_story",
    "enemy_identity",
    "party_identity",
    "status_assignment",
    "range_semantics",
    "arrow_semantics",
)
ANNOTATION_CALLOUT_ROLES = {"axis", "priority", "mechanic", "footer"}
RANGE_SEMANTIC_TYPES = {"circle", "cone", "rect", "tower", "stack"}
REAL_RESOLVE_GEOMETRY_TYPES = {"cone", "rect", "tower", "stack"}
RANGE_REQUIRED_FIELDS = ("kind", "label", "source", "targets", "resolveIndex", "resolveTiming", "aoeIntent")
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


def legacy_role_from_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    parts = value.strip().replace("/", " ").split()
    if parts and parts[0].upper() in PARTY_ROLES:
        return parts[0].upper()
    return ""


def legacy_job_from_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    parts = value.strip().replace("/", " ").split()
    if len(parts) >= 2 and parts[0].upper() in PARTY_ROLES:
        return parts[1].upper()
    return ""


def object_role(obj: dict[str, Any], allow_legacy_role_prefix: bool = False) -> str:
    if obj.get("type") != "party":
        return ""
    for key in ("role", "name", "label"):
        value = obj.get(key)
        if isinstance(value, str) and value.upper() in PARTY_ROLES:
            return value.upper()
    if allow_legacy_role_prefix:
        for key in ("name", "label", "roleLabel", "role_label"):
            role = legacy_role_from_text(obj.get(key))
            if role:
                return role
    return ""


def party_job(obj: dict[str, Any], allow_legacy_role_prefix: bool = False) -> str:
    if obj.get("type") != "party":
        return ""
    value = obj.get("job") or obj.get("jobName") or obj.get("job_name")
    if isinstance(value, str) and value.strip():
        return str(value).strip()
    if allow_legacy_role_prefix:
        for key in ("name", "label"):
            job = legacy_job_from_text(obj.get(key))
            if job:
                return job
        icon = normalized_icon(party_icon(obj))
        if icon in DEFAULT_JOB_BY_ICON:
            return DEFAULT_JOB_BY_ICON[icon]
    return ""


def party_icon(obj: dict[str, Any]) -> str:
    if obj.get("type") != "party":
        return ""
    value = obj.get("icon") or obj.get("image")
    return str(value).strip() if isinstance(value, str) and value.strip() else ""


def normalized_icon(value: str) -> str:
    return value.replace("\\", "/")


def party_role_label(obj: dict[str, Any], allow_legacy_role_prefix: bool = False) -> str:
    if obj.get("type") != "party":
        return ""
    value = obj.get("roleLabel") or obj.get("role_label")
    if isinstance(value, str) and value.strip():
        return str(value).strip()
    if allow_legacy_role_prefix:
        for key in ("name", "label"):
            role = legacy_role_from_text(obj.get(key))
            if role:
                return role
    return ""


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
    policy = scene.get("party_display_policy")
    if isinstance(policy, str) and policy.strip():
        normalized = policy.strip().lower().replace("_", "-")
        if normalized in {"role-number", "role-number-icon", "role-number-icons", "numbered-role-icon"}:
            return "role-number-icon"
        if normalized in {"job", "job-icon", "job-icons", "job-default"}:
            return "job-icon"
    return "role-number-icon" if scene.get("guide_section") == "mechanic_flow" else "job-icon"


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


def arena_overlay_kinds(arena: dict[str, Any]) -> list[str]:
    overlays = arena.get("arenaOverlays")
    if not isinstance(overlays, list):
        return []
    return sorted(
        {
            str(overlay.get("kind"))
            for overlay in overlays
            if isinstance(overlay, dict) and overlay.get("kind")
        }
    )


def arena_context_profile(scene: dict[str, Any]) -> dict[str, Any]:
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    return {
        "preset": arena.get("preset"),
        "backgroundImage": arena.get("backgroundImage"),
        "backgroundStatus": arena.get("backgroundStatus"),
        "source": arena.get("source"),
        "sourceReason": arena.get("sourceReason"),
        "overlay_kinds": arena_overlay_kinds(arena),
        "overlay_count": len(arena.get("arenaOverlays", [])) if isinstance(arena.get("arenaOverlays"), list) else 0,
    }


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


def scene_context_issues(scene: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    if not has_arena_context(scene):
        add_issue(
            issues,
            dimension="context",
            severity="review" if reference_mode == "gold" else "severe",
            kind="missing_arena_context",
            message="Scene root has no arena background, preset, shape, or grid context.",
            suggestion="Set `arena.preset`, `arena.shape`, or `arena.backgroundImage` before generating the scene.",
        )
    if reference_mode != "gold":
        preset = str(arena.get("preset") or "")
        background_status = str(arena.get("backgroundStatus") or "")
        fallback_reason = str(arena.get("sourceReason") or "")
        overlay_kinds = set(arena_overlay_kinds(arena))
        if preset == "omega-o8s" or background_status == "fallback":
            if not fallback_reason:
                add_issue(
                    issues,
                    dimension="context",
                    severity="review",
                    kind="arena_fallback_reason_missing",
                    message="Arena fallback is active but `sourceReason` is empty.",
                    suggestion="Record why no dedicated arena background was used and how overlays compensate.",
                )
            if not {"axis", "radial_ticks"} <= overlay_kinds:
                add_issue(
                    issues,
                    dimension="context",
                    severity="severe",
                    kind="arena_fallback_overlay_missing",
                    message="Fallback arena does not provide both axis and radial tick overlays.",
                    suggestion="Add `arenaOverlays` with AC/BD axis lines and radial ticks for O8S/Omega fallback scenes.",
                )

    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict) or is_partial_step(step):
            continue
        objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
        roles = {role for obj in objects if (role := object_role(obj, allow_legacy_role_prefix=reference_mode == "gold"))}
        missing_roles = sorted(PARTY_ROLES - roles)
        if missing_roles:
            add_issue(
                issues,
                dimension="context",
                severity="review" if reference_mode == "gold" else "severe",
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
                severity="review" if reference_mode == "gold" else "severe",
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


def label_issues(label_layout: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    for step in label_layout.get("per_step", []):
        for item in step.get("issues", []):
            severity = str(item.get("severity", "review"))
            kind = str(item.get("kind", "label_issue"))
            if reference_mode == "gold" and severity == "severe":
                severity = "review"
                kind = f"gold_dense_{kind}"
            add_issue(
                issues,
                dimension="label",
                severity=severity,
                kind=kind,
                step=int(step.get("step", 0) or 0),
                title=step.get("title"),
                object_id=item.get("text_id"),
                other_id=item.get("other_id"),
                message=f"Label `{item.get('text', '')}` has a {item.get('kind', 'layout')} issue.",
                suggestion="Treat as gold-reference dense annotation for human review." if reference_mode == "gold" else "Move the label outward, enable `labelPlacement: \"auto\"`, or add a leader line.",
            )


def flow_issues(flow_lines: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    for step in flow_lines.get("per_step", []):
        for item in step.get("issues", []):
            severity = str(item.get("severity", "review"))
            kind = str(item.get("kind", "flow_issue"))
            if reference_mode == "gold" and severity == "severe":
                severity = "review"
                if kind.startswith("arrow_head_vs_"):
                    kind = f"gold_endpoint_snap_{kind.removeprefix('arrow_head_vs_')}"
                else:
                    kind = f"gold_dense_{kind}"
            add_issue(
                issues,
                dimension="flow",
                severity=severity,
                kind=kind,
                step=int(step.get("step", 0) or 0),
                title=step.get("title"),
                object_id=item.get("arrow_id"),
                other_id=item.get("other_id"),
                message=f"Arrow has a {item.get('kind', 'flow')} issue.",
                suggestion="Treat as an intentional gold-reference endpoint/contact pattern unless manual review says it hides the target." if reference_mode == "gold" else "Use `waypoints`, `curve`, `startGap` / `endGap`, or split simultaneous movement into another step.",
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


def enemy_identity_issues(scene: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    hard_severity = "review" if reference_mode == "gold" else "severe"
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
                severity=hard_severity,
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
                    severity=hard_severity,
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
                    severity=hard_severity,
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
                    severity=hard_severity,
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
                    severity=hard_severity,
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
                    severity=hard_severity,
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
                        severity=hard_severity,
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


def party_identity_issues(scene: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    allow_legacy = reference_mode == "gold"
    hard_severity = "review" if allow_legacy else "severe"
    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict) or is_partial_step(step):
            continue
        party = [obj for obj in step.get("objects", []) if isinstance(obj, dict) and obj.get("type") == "party"]
        roles = [object_role(obj, allow_legacy_role_prefix=allow_legacy) for obj in party]
        missing = sorted(PARTY_ROLES - set(role for role in roles if role))
        duplicates = sorted(role for role, count in Counter(role for role in roles if role).items() if count > 1)
        if missing:
            add_issue(
                issues,
                dimension="party_identity",
                severity=hard_severity,
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
                severity=hard_severity,
                kind="party_duplicate_roles",
                step=step_index,
                title=step.get("title"),
                message=f"Step repeats role identities: {', '.join(duplicates)}.",
                suggestion="Each normal frame should contain each role exactly once.",
            )
        cluster_step = is_cluster_step(step, party)
        for obj in party:
            role = object_role(obj, allow_legacy_role_prefix=allow_legacy) or str(obj.get("name", "party"))
            display_style = party_display_style(obj, scene)
            if not party_job(obj, allow_legacy_role_prefix=allow_legacy):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity=hard_severity,
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
                    severity=hard_severity,
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
                    severity=hard_severity,
                    kind="party_abstract_job_icon",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` uses abstract icon token `{party_icon(obj)}` instead of a XivPlan job PNG.",
                    suggestion="Use the built-in XivPlan official job icon path, for example `/actor/DRK.png`.",
                )
            elif display_style == "role-number-icon" and normalized_icon(party_icon(obj)) != ROLE_NUMBER_PARTY_ICONS.get(role):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity=hard_severity,
                    kind="party_role_number_icon_mismatch",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` mechanism-flow icon should be `{ROLE_NUMBER_PARTY_ICONS.get(role)}`, got `{party_icon(obj)}`.",
                    suggestion="Use XivPlan numbered role icons such as `/actor/tank1.png`, `/actor/healer2.png`, or `/actor/dps4.png` for mechanism-flow diagrams.",
                )
            elif display_style == "job-icon" and obj.get("jobDefault") is True and normalized_icon(party_icon(obj)) != DEFAULT_PARTY_ICONS.get(role):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity=hard_severity,
                    kind="party_default_job_icon_mismatch",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` default icon should be `{DEFAULT_PARTY_ICONS.get(role)}`, got `{party_icon(obj)}`.",
                    suggestion="Keep default comp icons aligned with XivPlan `public/actor/<JOB>.png` assets.",
                )
            if display_style == "job-icon" and not cluster_step and not party_role_label(obj, allow_legacy_role_prefix=allow_legacy):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity=hard_severity,
                    kind="party_missing_role_label",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` has no readable roleLabel.",
                    suggestion="Place `MT/ST/H1/H2/D1/D2/D3/D4` near the job icon outside cluster/stack frames.",
                )
            if display_style == "job-icon" and not cluster_step and not role_label_visible(obj):
                add_issue(
                    issues,
                    dimension="party_identity",
                    severity=hard_severity,
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
                    severity=hard_severity,
                    kind="party_icon_too_small",
                    step=step_index,
                    title=step.get("title"),
                    object_id=obj.get("id"),
                    message=f"Party role `{role}` job icon is below the 24 px readability floor.",
                    suggestion="Use `iconScale >= 0.72` or a larger base player icon size.",
                )


def status_assignment_role(assignment: dict[str, Any]) -> str:
    value = assignment.get("role")
    if isinstance(value, str) and value.upper() in PARTY_ROLES:
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


def audit_status_assignments(scene: dict[str, Any]) -> dict[str, Any]:
    contract = scene.get("status_assignment_contract") if isinstance(scene.get("status_assignment_contract"), dict) else {}
    applicable = bool(contract.get("require_status_overlays") or scene.get("statusAssignments"))
    per_step: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    visible_expected = 0
    visible_overlays = 0
    assigned_roles: set[str] = set()
    covered_roles: set[str] = set()
    fallback_count = 0
    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict) or is_partial_step(step):
            continue
        assignments = step.get("statusAssignments", step.get("status_assignments", []))
        if assignments is None:
            assignments = []
        if not isinstance(assignments, list):
            issues.append({"severity": "severe", "kind": "status_assignments_not_list", "step": step_index})
            continue
        objects = step.get("objects", []) if isinstance(step.get("objects"), list) else []
        party_by_role = {
            object_role(obj): obj
            for obj in objects
            if isinstance(obj, dict) and obj.get("type") == "party" and object_role(obj)
        }
        overlays_by_role: dict[str, list[dict[str, Any]]] = {}
        for obj in objects:
            if not isinstance(obj, dict) or obj.get("statusOverlay") is not True:
                continue
            role = str(obj.get("statusRole") or obj.get("anchorRole") or "").upper()
            if role:
                overlays_by_role.setdefault(role, []).append(obj)
                covered_roles.add(role)
            if obj.get("assetStatus") == "fallback":
                fallback_count += 1
                if contract.get("require_fallback_reason") and not str(obj.get("fallbackReason", "")).strip():
                    issues.append({"severity": "severe", "kind": "status_fallback_missing_reason", "step": step_index, "role": role, "object_id": obj.get("id")})
            width = obj.get("width")
            height = obj.get("height")
            if contract.get("require_status_icon_readability") and (not isinstance(width, (int, float)) or not isinstance(height, (int, float)) or min(width, height) < 13):
                issues.append({"severity": "severe", "kind": "status_icon_too_small", "step": step_index, "role": role, "object_id": obj.get("id")})
        expected_roles: list[str] = []
        for assignment in assignments:
            if not isinstance(assignment, dict):
                issues.append({"severity": "severe", "kind": "status_assignment_not_object", "step": step_index})
                continue
            role = status_assignment_role(assignment)
            if not role:
                issues.append({"severity": "severe", "kind": "status_assignment_missing_role", "step": step_index})
                continue
            assigned_roles.add(role)
            if not str(assignment.get("statusName", assignment.get("status_name", ""))).strip():
                issues.append({"severity": "severe", "kind": "status_assignment_missing_name", "step": step_index, "role": role})
            if status_visible_on_step(assignment, step_index):
                expected_roles.append(role)
                visible_expected += 1
                role_overlays = overlays_by_role.get(role, [])
                if not role_overlays:
                    issues.append({"severity": "severe", "kind": "status_overlay_missing", "step": step_index, "role": role})
                    continue
                visible_overlays += 1
                party_id = party_by_role.get(role, {}).get("id")
                if party_id is not None and not any(overlay.get("anchorPartyId") == party_id for overlay in role_overlays):
                    issues.append({"severity": "severe", "kind": "status_overlay_wrong_anchor", "step": step_index, "role": role, "party_id": party_id})
        per_step.append(
            {
                "step": step_index,
                "expected_roles": expected_roles,
                "overlay_roles": sorted(overlays_by_role),
                "missing_roles": sorted(role for role in expected_roles if role not in overlays_by_role),
            }
        )
    if contract.get("require_status_overlays") and visible_expected == 0:
        issues.append({"severity": "severe", "kind": "status_contract_without_visible_assignments"})
    score = round((visible_overlays / visible_expected) * 100, 2) if visible_expected else (100.0 if not contract.get("require_status_overlays") else 0.0)
    severe_items = sum(1 for issue in issues if issue["severity"] == "severe")
    return {
        "applicable": applicable,
        "ok": severe_items == 0,
        "status_assignment_score": score,
        "visible_expected": visible_expected,
        "visible_overlays": visible_overlays,
        "assigned_roles": sorted(assigned_roles),
        "covered_roles": sorted(covered_roles),
        "fallback_count": fallback_count,
        "severe_items": severe_items,
        "issues": issues,
        "per_step": per_step,
    }


def status_assignment_issues(profile: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    hard_severity = "review" if reference_mode == "gold" else "severe"
    for item in profile.get("issues", []):
        kind = str(item.get("kind", "status_assignment_issue"))
        role = item.get("role")
        add_issue(
            issues,
            dimension="status_assignment",
            severity="review" if reference_mode == "gold" and item.get("severity") == "severe" else str(item.get("severity", hard_severity)),
            kind=kind,
            step=item.get("step"),
            object_id=item.get("object_id"),
            message=f"Status assignment issue{f' for {role}' if role else ''}: {kind}.",
            suggestion="Render a readable status overlay on the assigned player's upper-left icon area, or document a traceable fallback badge.",
        )


def story_issues(scene: dict[str, Any], storyboard: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    hard_severity = "review" if reference_mode == "gold" else "severe"
    if storyboard.get("applicable"):
        for item in storyboard.get("issues", []):
            add_issue(
                issues,
                dimension="step_story",
                severity="review" if reference_mode == "gold" and str(item.get("severity", "severe")) == "severe" else str(item.get("severity", "severe")),
                kind=str(item.get("kind", "storyboard_issue")),
                message=str(item.get("kind", "Storyboard issue")),
                suggestion="Add the missing storyboard phase or required step metadata.",
            )
        for step in storyboard.get("per_step", []):
            for item in step.get("issues", []):
                add_issue(
                    issues,
                    dimension="step_story",
                    severity="review" if reference_mode == "gold" and str(item.get("severity", "severe")) == "severe" else str(item.get("severity", "severe")),
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
        severity=hard_severity,
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


def all_step_objects(scene: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        obj
        for step in scene.get("steps", [])
        if isinstance(step, dict)
        for obj in step.get("objects", [])
        if isinstance(obj, dict)
    ]


def text_label_role(obj: dict[str, Any]) -> str:
    value = obj.get("labelRole", obj.get("label_role"))
    return str(value).strip() if isinstance(value, str) else ""


def audit_annotation_contract(scene: dict[str, Any]) -> dict[str, Any]:
    contract = scene.get("annotation_contract") if isinstance(scene.get("annotation_contract"), dict) else {}
    applicable = bool(contract.get("require_in_scene_teaching"))
    min_callouts = int(contract.get("min_callouts_per_step", 3) or 3)
    max_callout_chars = int(contract.get("max_callout_chars", 38) or 38)
    prefer_axis_priority = bool(contract.get("prefer_axis_and_priority_labels", False))
    require_footer = bool(contract.get("convert_guide_text_to_footer", False))
    per_step: list[dict[str, Any]] = []
    total_text_objects = 0
    total_text_chars = 0
    total_callouts = 0
    total_guide_chars = 0

    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict):
            continue
        objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
        texts = [obj for obj in objects if obj.get("type") == "text" and isinstance(obj.get("text"), str)]
        text_chars = sum(len(str(obj.get("text", ""))) for obj in texts)
        guide_chars = len(str(step.get("guide_text", "")))
        roles = Counter(text_label_role(obj) for obj in texts if text_label_role(obj))
        callouts = [obj for obj in texts if text_label_role(obj) in ANNOTATION_CALLOUT_ROLES]
        issues: list[dict[str, Any]] = []
        if applicable and not is_partial_step(step):
            if roles.get("page_title", 0) < 1:
                issues.append({"severity": "severe", "kind": "missing_page_title", "field": "labelRole"})
            if len(callouts) < min_callouts:
                issues.append({"severity": "severe", "kind": "too_few_in_scene_callouts", "count": len(callouts), "expected": min_callouts})
            if prefer_axis_priority and roles.get("axis", 0) < 1:
                issues.append({"severity": "severe", "kind": "missing_axis_callout", "field": "labelRole"})
            if prefer_axis_priority and roles.get("priority", 0) < 1:
                issues.append({"severity": "severe", "kind": "missing_priority_callout", "field": "labelRole"})
            if roles.get("mechanic", 0) < 1:
                issues.append({"severity": "severe", "kind": "missing_mechanic_callout", "field": "labelRole"})
            if require_footer and roles.get("footer", 0) < 1:
                issues.append({"severity": "severe", "kind": "missing_footer_callout", "field": "labelRole"})
            for obj in callouts:
                length = len(str(obj.get("text", "")))
                if length > max_callout_chars:
                    issues.append(
                        {
                            "severity": "severe",
                            "kind": "callout_too_long",
                            "object_id": obj.get("id"),
                            "length": length,
                            "expected": max_callout_chars,
                        }
                    )
        total_text_objects += len(texts)
        total_text_chars += text_chars
        total_callouts += len(callouts)
        total_guide_chars += guide_chars
        per_step.append(
            {
                "step": step_index,
                "title": step.get("title"),
                "text_objects": len(texts),
                "text_chars": text_chars,
                "guide_text_chars": guide_chars,
                "callouts": len(callouts),
                "label_roles": dict(sorted(roles.items())),
                "issues": issues,
                "severe_items": sum(1 for issue in issues if issue["severity"] == "severe"),
            }
        )

    step_count = len([step for step in scene.get("steps", []) if isinstance(step, dict)])
    average_text_chars = round(total_text_chars / total_text_objects, 2) if total_text_objects else 0.0
    complex_mechanic = applicable and step_count >= 10
    text_richness_ok = (total_text_objects >= 140 or total_text_chars >= 900) if complex_mechanic else True
    average_length_ok = not total_text_objects or 4 <= average_text_chars <= 14
    severe = sum(item["severe_items"] for item in per_step)
    if complex_mechanic and not text_richness_ok:
        severe += 1
    return {
        "applicable": applicable,
        "ok": severe == 0,
        "steps": step_count,
        "text_objects": total_text_objects,
        "text_chars": total_text_chars,
        "guide_text_chars": total_guide_chars,
        "callouts": total_callouts,
        "average_text_chars": average_text_chars,
        "complex_mechanic": complex_mechanic,
        "text_richness_ok": text_richness_ok,
        "average_length_ok": average_length_ok,
        "min_callouts_per_step": min_callouts,
        "max_callout_chars": max_callout_chars,
        "severe_items": severe,
        "per_step": per_step,
    }


def annotation_contract_issues(profile: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    if reference_mode == "gold" or not profile.get("applicable"):
        return
    for step in profile.get("per_step", []):
        for item in step.get("issues", []):
            add_issue(
                issues,
                dimension="step_story",
                severity=str(item.get("severity", "severe")),
                kind=str(item.get("kind", "annotation_contract_issue")),
                step=int(step.get("step", 0) or 0),
                title=step.get("title"),
                object_id=item.get("object_id"),
                message="In-scene annotation contract is not satisfied.",
                suggestion="Add page title, axis, priority, mechanic, and footer callouts using `labelRole` and the top/bottom/left/right bands.",
            )
    if profile.get("complex_mechanic") and not profile.get("text_richness_ok"):
        add_issue(
            issues,
            dimension="step_story",
            severity="severe",
            kind="complex_mechanic_in_scene_text_too_sparse",
            message=(
                "Complex annotated mechanic has too little in-scene text "
                f"({profile.get('text_objects')} text objects, {profile.get('text_chars')} chars)."
            ),
            suggestion="For O8S/Yokai-like mechanics, target 140+ text objects or 900+ in-scene text chars.",
        )
    if profile.get("complex_mechanic") and not profile.get("average_length_ok"):
        add_issue(
            issues,
            dimension="aesthetic",
            severity="review",
            kind="annotation_average_label_length_out_of_range",
            message=f"Average in-scene text length is {profile.get('average_text_chars')} chars.",
            suggestion="Keep most labels in the 4-14 character scan range; move long prose back to guide text.",
        )


def damage_pattern(obj: dict[str, Any]) -> dict[str, Any]:
    value = obj.get("damagePattern")
    return value if isinstance(value, dict) else {}


def pattern_value(obj: dict[str, Any], key: str) -> Any:
    pattern = damage_pattern(obj)
    return pattern[key] if key in pattern else obj.get(key)


def audit_mechanic_semantics(scene: dict[str, Any], flow_lines: dict[str, Any]) -> dict[str, Any]:
    contract = scene.get("mechanic_semantics_contract") if isinstance(scene.get("mechanic_semantics_contract"), dict) else {}
    applicable = any(
        bool(contract.get(key))
        for key in (
            "require_arrow_semantics",
            "require_range_semantics",
            "require_resolve_geometry",
            "require_danger_crossing_declaration",
        )
    )
    per_step: list[dict[str, Any]] = []
    range_objects = 0
    semantic_ranges = 0
    complete_semantic_ranges = 0
    pattern_kinds: Counter[str] = Counter()
    true_geometry = 0
    issues: list[dict[str, Any]] = []

    for step_index, step in enumerate(scene.get("steps", []), start=1):
        if not isinstance(step, dict):
            continue
        step_issues: list[dict[str, Any]] = []
        step_ranges = [
            obj
            for obj in step.get("objects", [])
            if isinstance(obj, dict) and obj.get("type") in RANGE_SEMANTIC_TYPES
        ]
        semantic_step_ranges = [obj for obj in step_ranges if damage_pattern(obj)]
        complete_step_ranges: list[dict[str, Any]] = []
        for obj in semantic_step_ranges:
            pattern_kind = str(pattern_value(obj, "kind") or "")
            if pattern_kind:
                pattern_kinds[pattern_kind] += 1
            missing = [key for key in RANGE_REQUIRED_FIELDS if pattern_value(obj, key) in (None, "")]
            if not isinstance(pattern_value(obj, "targets"), list):
                missing.append("targets:list")
            if not isinstance(pattern_value(obj, "resolveIndex"), int):
                missing.append("resolveIndex:int")
            if missing:
                if contract.get("require_range_semantics"):
                    step_issues.append(
                        {
                            "severity": "severe",
                            "kind": "range_missing_semantics",
                            "object_id": obj.get("id"),
                            "missing": sorted(set(missing)),
                        }
                    )
                continue
            complete_step_ranges.append(obj)
            if obj.get("type") in REAL_RESOLVE_GEOMETRY_TYPES and pattern_value(obj, "aoeIntent") != "reference_only":
                true_geometry += 1

        if contract.get("require_resolve_geometry") and step_phase(step) == "resolve":
            resolve_geometry = [
                obj
                for obj in complete_step_ranges
                if obj.get("type") in REAL_RESOLVE_GEOMETRY_TYPES
                and pattern_value(obj, "aoeIntent") != "reference_only"
            ]
            if not resolve_geometry:
                step_issues.append({"severity": "severe", "kind": "resolve_step_missing_semantic_geometry"})

        range_objects += len(step_ranges)
        semantic_ranges += len(semantic_step_ranges)
        complete_semantic_ranges += len(complete_step_ranges)
        issues.extend({"step": step_index, "title": step.get("title"), **issue} for issue in step_issues)
        per_step.append(
            {
                "step": step_index,
                "title": step.get("title"),
                "phase": step_phase(step),
                "range_objects": len(step_ranges),
                "semantic_ranges": len(semantic_step_ranges),
                "complete_semantic_ranges": len(complete_step_ranges),
                "issues": step_issues,
            }
        )

    if contract.get("require_range_semantics") and semantic_ranges == 0:
        issues.append({"severity": "severe", "kind": "scene_missing_semantic_ranges"})
    if contract.get("require_resolve_geometry") and true_geometry == 0:
        issues.append({"severity": "severe", "kind": "scene_missing_real_resolve_geometry"})
    arrow_semantics_score = float(flow_lines.get("arrow_semantics_score", 100.0 if not contract.get("require_arrow_semantics") else 0.0))
    if contract.get("require_arrow_semantics") and arrow_semantics_score < 100.0:
        issues.append(
            {
                "severity": "severe",
                "kind": "arrow_semantics_incomplete",
                "score": arrow_semantics_score,
            }
        )
    range_semantics_score = round(complete_semantic_ranges / semantic_ranges * 100, 2) if semantic_ranges else (100.0 if not contract.get("require_range_semantics") else 0.0)
    return {
        "applicable": applicable,
        "contract": contract,
        "ok": not any(issue["severity"] == "severe" for issue in issues),
        "range_objects": range_objects,
        "semantic_ranges": semantic_ranges,
        "complete_semantic_ranges": complete_semantic_ranges,
        "range_semantics_score": range_semantics_score,
        "semantic_range_coverage": round(semantic_ranges / range_objects * 100, 2) if range_objects else 0.0,
        "true_resolve_geometry": true_geometry,
        "pattern_kinds": dict(sorted(pattern_kinds.items())),
        "arrows": int(flow_lines.get("arrows", 0) or 0),
        "semantic_arrows": int(flow_lines.get("semantic_arrows", 0) or 0),
        "arrow_semantics_score": arrow_semantics_score,
        "declared_endpoint_snaps": int(flow_lines.get("declared_endpoint_snaps", 0) or 0),
        "endpoint_snaps": int(flow_lines.get("endpoint_snaps", 0) or 0),
        "issues": issues,
        "per_step": per_step,
    }


def mechanic_semantics_issues(profile: dict[str, Any], issues: list[dict[str, Any]], reference_mode: str = "strict") -> None:
    if reference_mode == "gold" or not profile.get("applicable"):
        return
    for item in profile.get("issues", []):
        kind = str(item.get("kind", "mechanic_semantics_issue"))
        dimension = "arrow_semantics" if kind.startswith("arrow_") else "range_semantics"
        add_issue(
            issues,
            dimension=dimension,
            severity=str(item.get("severity", "severe")),
            kind=kind,
            step=int(item.get("step", 0) or 0) or None,
            title=item.get("title"),
            object_id=item.get("object_id"),
            message="Phase V mechanic semantics contract is not satisfied.",
            suggestion="Add movementRoute endpoints and snap declaration, or add damagePattern label/source/targets/resolve timing metadata with real resolve geometry.",
        )


def bounded_ratio(value: float, target: float) -> float:
    if target <= 0:
        return 100.0
    return round(max(0.0, min(100.0, value / target * 100.0)), 2)


def gold_style_profile(scene: dict[str, Any], density: dict[str, Any], label_layout: dict[str, Any], flow_lines: dict[str, Any]) -> dict[str, Any]:
    objects = all_step_objects(scene)
    type_counts = Counter(str(obj.get("type")) for obj in objects if obj.get("type"))
    text_objects = [obj for obj in objects if obj.get("type") == "text"]
    text_chars = sum(len(str(obj.get("text", ""))) for obj in text_objects)
    mechanic_zones = sum(type_counts.get(obj_type, 0) for obj_type in MECHANIC_TYPES)
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    party = [obj for obj in objects if obj.get("type") == "party"]
    compatible_roles = {role for obj in party if (role := object_role(obj, allow_legacy_role_prefix=True))}
    waymarks = {mark for obj in objects if (mark := object_waymark(obj))}
    step_count = len([step for step in scene.get("steps", []) if isinstance(step, dict)])
    avg_objects = float(density.get("avg_objects_per_step", 0) or 0)
    arrow_count = int(flow_lines.get("arrows", 0) or type_counts.get("arrow", 0))
    scores = {
        "step_richness_score": 100.0 if 10 <= step_count <= 20 else bounded_ratio(step_count, 10),
        "object_density_score": 100.0 if 35 <= avg_objects <= 65 else bounded_ratio(avg_objects, 35),
        "text_richness_score": round((bounded_ratio(len(text_objects), 140) + bounded_ratio(text_chars, 900)) / 2, 2),
        "mechanic_range_score": bounded_ratio(mechanic_zones, 100),
        "flow_presence_score": bounded_ratio(arrow_count, 10),
        "arena_context_score": round(
            (
                (100.0 if arena.get("backgroundImage") else 55.0 if arena.get("preset") or arena.get("shape") else 0.0)
                + (100.0 if arena.get("ticks") else 65.0 if arena.get("grid") else 0.0)
                + bounded_ratio(len(waymarks), 4)
            )
            / 3,
            2,
        ),
        "legacy_party_compat_score": bounded_ratio(len(compatible_roles), 8),
    }
    gold_style_score = round(sum(scores.values()) / len(scores), 2)
    return {
        "gold_style_score": gold_style_score,
        "scores": scores,
        "summary": "reference style dense; readability requires human confirmation" if label_layout.get("review_items", 0) else "reference style clean",
        "metrics": {
            "steps": step_count,
            "objects": len(objects),
            "avg_objects_per_step": avg_objects,
            "text_objects": len(text_objects),
            "in_scene_text_chars": text_chars,
            "mechanic_zones": mechanic_zones,
            "arrows": arrow_count,
            "waymarks": sorted(waymarks),
            "compatible_party_roles": sorted(compatible_roles),
            "backgroundImage": arena.get("backgroundImage"),
            "ticks": bool(arena.get("ticks")),
            "label_classes": label_layout.get("label_classes", {}),
        },
    }


def normalize_reference_issues(issues: list[dict[str, Any]], reference_mode: str) -> None:
    if reference_mode != "gold":
        return
    for issue in issues:
        if issue.get("severity") == "severe":
            issue["reference_original_severity"] = "severe"
            issue["severity"] = "review"
            issue["message"] = f"{issue['message']} Gold reference mode records this as profile evidence, not a generator-contract failure."


def audit_scene(path: Path, reference_mode: str = "strict") -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")

    density = audit_density_scene(path)
    label_layout = audit_label_scene(path, reference_mode=reference_mode)
    flow_lines = audit_flow_scene(path)
    storyboard = audit_storyboard_scene(path)
    annotation_contract = audit_annotation_contract(scene)
    mechanic_semantics = audit_mechanic_semantics(scene, flow_lines)
    status_assignment = audit_status_assignments(scene)
    arena_context = arena_context_profile(scene)

    issues: list[dict[str, Any]] = []
    scene_context_issues(scene, issues, reference_mode=reference_mode)
    density_issues(density, issues)
    label_issues(label_layout, issues, reference_mode=reference_mode)
    flow_issues(flow_lines, issues, reference_mode=reference_mode)
    layer_and_aesthetic_issues(scene, issues)
    story_issues(scene, storyboard, issues, reference_mode=reference_mode)
    annotation_contract_issues(annotation_contract, issues, reference_mode=reference_mode)
    mechanic_semantics_issues(mechanic_semantics, issues, reference_mode=reference_mode)
    enemy_identity_issues(scene, issues, reference_mode=reference_mode)
    party_identity_issues(scene, issues, reference_mode=reference_mode)
    status_assignment_issues(status_assignment, issues, reference_mode=reference_mode)
    normalize_reference_issues(issues, reference_mode)

    scores = {f"{dimension}_score": score_dimension(issues, dimension) for dimension in SCORE_DIMENSIONS}
    overall_score = round(sum(scores.values()) / len(scores), 2)
    severe = sum(1 for issue in issues if issue["severity"] == "severe")
    review = sum(1 for issue in issues if issue["severity"] == "review")
    status = "GOLD_PROFILE" if reference_mode == "gold" else ("FAIL" if severe else ("REVIEW" if review else "PASS"))
    result = {
        "path": str(path),
        "reference_mode": reference_mode,
        "ok": severe == 0,
        "status": status,
        "overall_score": overall_score,
        "scores": scores,
        "range_semantics_score": mechanic_semantics["range_semantics_score"],
        "arrow_semantics_score": mechanic_semantics["arrow_semantics_score"],
        "status_assignment_score": status_assignment["status_assignment_score"],
        "severe_items": severe,
        "review_items": review,
        "steps": len(steps),
        "issues": issues,
        "components": {
            "arena_context": arena_context,
            "density": density,
            "label_layout": label_layout,
            "flow_lines": flow_lines,
            "storyboard": storyboard,
            "annotation_contract": annotation_contract,
            "mechanic_semantics": mechanic_semantics,
            "status_assignment": status_assignment,
        },
    }
    if reference_mode == "gold":
        gold_profile = gold_style_profile(scene, density, label_layout, flow_lines)
        result["gold_style_score"] = gold_profile["gold_style_score"]
        result["gold_style_profile"] = gold_profile
    return result


def render_markdown(results: list[dict[str, Any]]) -> str:
    gold_mode = any(result.get("reference_mode") == "gold" for result in results)
    lines = ["# Visual Quality Audit", ""]
    if gold_mode:
        lines.extend(
            [
                "| Scene | Mode | Status | Gold Style | Contract Score | Context | Density | Label | Flow | Layer | Aesthetic | Story | Enemy | Party | Status | Range Sem | Arrow Sem | Severe | Review |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
    else:
        lines.extend(
            [
                "| Scene | Status | Score | Context | Density | Label | Flow | Layer | Aesthetic | Story | Enemy | Party | Status | Range Sem | Arrow Sem | Severe | Review |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
    for result in results:
        scores = result["scores"]
        scene = scene_label(result["path"])
        if gold_mode:
            lines.append(
                "| {scene} | {mode} | {status} | {gold} | {overall} | {context} | {density} | {label} | {flow} | {layer} | {aesthetic} | {story} | {enemy} | {party} | {status_assignment} | {range_semantics} | {arrow_semantics} | {severe} | {review} |".format(
                    scene=scene,
                    mode=result.get("reference_mode", "strict"),
                    status=result["status"],
                    gold=result.get("gold_style_score", ""),
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
                    status_assignment=scores["status_assignment_score"],
                    range_semantics=result["range_semantics_score"],
                    arrow_semantics=result["arrow_semantics_score"],
                    severe=result["severe_items"],
                    review=result["review_items"],
                )
            )
        else:
            lines.append(
                "| {scene} | {status} | {overall} | {context} | {density} | {label} | {flow} | {layer} | {aesthetic} | {story} | {enemy} | {party} | {status_assignment} | {range_semantics} | {arrow_semantics} | {severe} | {review} |".format(
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
                    status_assignment=scores["status_assignment_score"],
                    range_semantics=result["range_semantics_score"],
                    arrow_semantics=result["arrow_semantics_score"],
                    severe=result["severe_items"],
                    review=result["review_items"],
                )
            )
    lines.extend(["", "## Arena Context", ""])
    lines.extend(
        [
            "| Scene | Preset | Background | Status | Source | Overlays | Source Reason |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for result in results:
        arena = result.get("components", {}).get("arena_context", {})
        lines.append(
            "| {scene} | {preset} | {background} | {status} | {source} | {overlays} | {reason} |".format(
                scene=scene_label(result["path"]),
                preset=arena.get("preset") or "none",
                background=arena.get("backgroundImage") or "none",
                status=arena.get("backgroundStatus") or "n/a",
                source=arena.get("source") or "n/a",
                overlays=", ".join(arena.get("overlay_kinds", [])) or "none",
                reason=str(arena.get("sourceReason") or "").replace("|", "\\|"),
            )
        )
    lines.extend(["", "## Status Assignment", ""])
    lines.extend(
        [
            "| Scene | Applicable | Score | Expected | Visible | Assigned Roles | Covered Roles | Fallbacks |",
            "|---|---|---:|---:|---:|---|---|---:|",
        ]
    )
    for result in results:
        status_profile = result.get("components", {}).get("status_assignment", {})
        lines.append(
            "| {scene} | {applicable} | {score} | {expected} | {visible} | {assigned} | {covered} | {fallbacks} |".format(
                scene=scene_label(result["path"]),
                applicable="yes" if status_profile.get("applicable") else "no",
                score=status_profile.get("status_assignment_score", 100.0),
                expected=status_profile.get("visible_expected", 0),
                visible=status_profile.get("visible_overlays", 0),
                assigned=", ".join(status_profile.get("assigned_roles", [])) or "none",
                covered=", ".join(status_profile.get("covered_roles", [])) or "none",
                fallbacks=status_profile.get("fallback_count", 0),
            )
        )
    if gold_mode:
        lines.extend(["", "## Gold Profile", ""])
        for result in results:
            profile = result.get("gold_style_profile")
            if not isinstance(profile, dict):
                continue
            metrics = profile.get("metrics", {})
            lines.append(
                "- {scene}: {summary}; steps={steps}, objects={objects}, text={text}, chars={chars}, mechanic_zones={zones}, arrows={arrows}, background={background}".format(
                    scene=scene_label(result["path"]),
                    summary=profile.get("summary", "gold profile"),
                    steps=metrics.get("steps"),
                    objects=metrics.get("objects"),
                    text=metrics.get("text_objects"),
                    chars=metrics.get("in_scene_text_chars"),
                    zones=metrics.get("mechanic_zones"),
                    arrows=metrics.get("arrows"),
                    background=metrics.get("backgroundImage") or "none",
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
    parser.add_argument("--reference-mode", choices=("strict", "gold"), default="strict", help="Use gold to profile dense human reference scenes without applying the generator contract as a failure gate")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        scene_paths = expand_input_paths(args.paths)
        if not scene_paths:
            raise ValueError("no .xivplan files found")
        results = [audit_scene(path, reference_mode=args.reference_mode) for path in scene_paths]
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
        if result.get("reference_mode") == "gold":
            print(
                f"{result['path']}: {result['status']} gold_style_score={result.get('gold_style_score')} contract_score={result['overall_score']} severe={result['severe_items']} review={result['review_items']}"
            )
        else:
            print(
                f"{result['path']}: {result['status']} score={result['overall_score']} severe={result['severe_items']} review={result['review_items']}"
            )
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
