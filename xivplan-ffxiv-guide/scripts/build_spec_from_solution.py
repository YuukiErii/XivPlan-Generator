#!/usr/bin/env python3
"""Build a multi-step XivPlan spec from a recommended Phase 12 solution."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROLES = ("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4")
ROLE_DIR = {"MT": "N", "ST": "S", "H1": "W", "H2": "E", "D1": "NW", "D2": "NE", "D3": "SW", "D4": "SE"}
DIRECTION_DEGREES = {"E": 0, "NE": 45, "N": 90, "NW": 135, "W": 180, "SW": 225, "S": 270, "SE": 315}
ALL_ROLES = list(ROLES)
TH_ROLES = ["MT", "ST", "H1", "H2"]
DPS_ROLES = ["D1", "D2", "D3", "D4"]
DEFAULT_PARTY_JOBS = {
    "MT": {"job": "DRK", "jobName": "Dark Knight", "icon": "/actor/DRK.png"},
    "ST": {"job": "PLD", "jobName": "Paladin", "icon": "/actor/PLD.png"},
    "H1": {"job": "AST", "jobName": "Astrologian", "icon": "/actor/AST.png"},
    "H2": {"job": "SCH", "jobName": "Scholar", "icon": "/actor/SCH.png"},
    "D1": {"job": "SAM", "jobName": "Samurai", "icon": "/actor/SAM.png"},
    "D2": {"job": "DRG", "jobName": "Dragoon", "icon": "/actor/DRG.png"},
    "D3": {"job": "BRD", "jobName": "Bard", "icon": "/actor/BRD.png"},
    "D4": {"job": "PCT", "jobName": "Pictomancer", "icon": "/actor/PCT.png"},
}
ANNOTATION_CONTRACT = {
    "require_in_scene_teaching": True,
    "min_callouts_per_step": 3,
    "max_callout_chars": 38,
    "prefer_axis_and_priority_labels": True,
    "convert_guide_text_to_footer": True,
}
MECHANIC_SEMANTICS_CONTRACT = {
    "require_arrow_semantics": True,
    "require_range_semantics": True,
    "require_resolve_geometry": True,
    "require_danger_crossing_declaration": True,
}
STATUS_ASSIGNMENT_CONTRACT = {
    "require_status_overlays": True,
    "require_all_assigned_roles_visible": True,
    "require_status_icon_readability": True,
    "require_fallback_reason": True,
}
STATUS_DRIVEN_CATEGORIES = {"debuff", "hello-world-like", "relativity-like", "high-concept-like", "status-assignment"}
CALLOUT_SLOTS = (
    ("top", 0),
    ("top", 2),
    ("left", 0),
    ("right", 0),
    ("left", 2),
    ("right", 2),
    ("bottom", 0),
    ("bottom", 2),
)
PHASE_CALLOUTS = {
    "observe_signal": "只读当前信号",
    "assign_roles": "先分组再移动",
    "assignment": "先分组再移动",
    "preposition": "预站后等读条",
    "first_move": "移动前先读完",
    "second_move": "只动当前职责",
    "between_resolves": "两判定间不抢跑",
    "move": "沿箭头短路线",
    "first_resolve": "判定后看复位",
    "second_resolve": "吃完立刻回稳",
    "resolve": "先判定再复位",
    "reset": "回中准备下一轮",
    "next_read_setup": "八方重开读条",
}
PHASE_TITLE_HINTS = {
    "observe_signal": "读法",
    "assign_roles": "分工",
    "assignment": "分工",
    "preposition": "预站",
    "first_move": "第一动",
    "second_move": "主要移动",
    "between_resolves": "中间处理",
    "move": "移动",
    "first_resolve": "第一判定",
    "second_resolve": "最终判定",
    "resolve": "判定",
    "reset": "复位",
    "next_read_setup": "下一读条",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact_phrase(value: Any, max_chars: int = 14) -> str:
    text = str(value or "").strip()
    for token in ("？", "?", "。", ".", "；", ";"):
        text = text.replace(token, "")
    text = " ".join(text.replace("，", " ").replace(",", " ").split())
    if len(text) <= max_chars:
        return text
    for separator in ("：", ":", "、", "/", " "):
        parts = [part.strip() for part in text.split(separator) if part.strip()]
        for part in parts:
            if 4 <= len(part) <= max_chars:
                return part
    return text[:max_chars]


def split_short_callouts(text: str, max_chars: int = 14) -> list[str]:
    normalized = str(text or "").replace("\n", " ")
    for separator in ("；", ";", "。", ".", "，", ","):
        normalized = normalized.replace(separator, "|")
    phrases = []
    for part in normalized.split("|"):
        phrase = compact_phrase(part, max_chars=max_chars)
        if 4 <= len(phrase) <= max_chars:
            phrases.append(phrase)
    return phrases


def axis_label(categories: set[str]) -> str:
    if "tower" in categories:
        return "南北 T/H 东西 DPS"
    if "cleave" in categories:
        return "先看 Boss 面向"
    if "tile" in categories or "tile-platform" in categories:
        return "按格子轴线走"
    return "AC/BD 轴线固定"


def priority_label(categories: set[str], step_phase: str) -> str:
    if "stack" in categories and "spread" in categories:
        return "先分摊后散开"
    if "tower" in categories:
        return "T/H 南北优先"
    if step_phase in {"first_move", "second_move", "move"}:
        return "读条职业少动"
    return "固定职责优先"


def mechanic_label(categories: set[str], step_phase: str) -> str:
    if "tower" in categories and step_phase in {"observe_signal", "assign_roles", "first_move"}:
        return "塔人数先确认"
    if "stack" in categories and step_phase in {"first_resolve", "second_resolve", "resolve"}:
        return "分摊人数别漏"
    if "spread" in categories:
        return "远近间距拉开"
    if "cleave" in categories:
        return "安全半场先定"
    return "机制范围先读"


def page_title_for_step(index: int, item: dict[str, Any]) -> str:
    question = compact_phrase(item.get("teaching_question"), max_chars=12)
    if not question:
        question = compact_phrase(item.get("title"), max_chars=12)
    phase_hint = PHASE_TITLE_HINTS.get(str(item.get("storyboard_phase", "")), "")
    if phase_hint and phase_hint not in question:
        title = f"{phase_hint}：{question}"
    else:
        title = question
    title = compact_phrase(title, max_chars=15)
    return f"{index} {title}"


def annotation_objects_for_step(index: int, item: dict[str, Any], categories: set[str], unknowns: list[str]) -> list[dict[str, Any]]:
    phase = str(item.get("storyboard_phase", ""))
    callout_texts = [
        axis_label(categories),
        priority_label(categories, phase),
        mechanic_label(categories, phase),
    ]
    callout_texts.extend(split_short_callouts(str(item.get("guide_text", "")), max_chars=14)[:2])
    callout_texts.append(compact_phrase(item.get("purpose"), max_chars=14))
    callout_texts.append(compact_phrase(item.get("visual_focus"), max_chars=14))
    callout_texts.append(PHASE_CALLOUTS.get(phase, "只回答本页问题"))
    if unknowns:
        callout_texts.append("未知点保守处理")
    else:
        callout_texts.append(compact_phrase(item.get("reset_state"), max_chars=14) or "错位先回安全区")

    deduped: list[str] = []
    for text in callout_texts:
        text = compact_phrase(text, max_chars=14)
        if text and text not in deduped:
            deduped.append(text)
    while len(deduped) < len(CALLOUT_SLOTS):
        deduped.append(("先观察", "再移动", "后判定", "判定后复位", "下一读条")[len(deduped) % 5])

    roles = ("axis", "priority", "mechanic", "mechanic", "mechanic", "mechanic", "footer", "footer")
    objects: list[dict[str, Any]] = []
    for callout_index, text in enumerate(deduped[: len(CALLOUT_SLOTS)]):
        band, band_index = CALLOUT_SLOTS[callout_index]
        objects.append(
            {
                "kind": "text",
                "key": f"phase-u-{index:02d}-callout-{callout_index + 1}",
                "text": text,
                "labelRole": roles[callout_index],
                "labelBand": band,
                "labelBandIndex": band_index,
                "fontSize": 12 if callout_index >= 3 else 13,
                "color": "#f7f7f7",
                "stroke": "#101820",
            }
        )
    return objects


def apply_in_scene_annotations(steps: list[dict[str, Any]], categories: set[str], unknowns: list[str]) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for index, item in enumerate(steps, start=1):
        updated = dict(item)
        updated["page_title"] = page_title_for_step(index, updated)
        callouts = annotation_objects_for_step(index, updated, categories, unknowns)
        updated["annotation_callouts"] = [obj["text"] for obj in callouts]
        objects = list(updated.get("objects", []))
        objects.extend(callouts)
        updated["objects"] = objects
        annotated.append(updated)
    return annotated


def resolve_index_for_phase(phase: str) -> int:
    if phase in {"first_move", "first_resolve", "preposition"}:
        return 1
    if phase in {"second_move", "second_resolve", "between_resolves"}:
        return 2
    if phase in {"reset", "next_read_setup"}:
        return 3
    return 0


def role_from_object_key(value: Any) -> str | None:
    tokens = str(value or "").lower().replace("_", "-").split("-")
    for role in ROLES:
        if role.lower() in tokens:
            return role
    return None


def decorate_movement_route(obj: dict[str, Any], step_index: int, phase: str) -> dict[str, Any]:
    updated = dict(obj)
    key = str(updated.get("key") or f"phase-v-route-{step_index}")
    from_role = role_from_object_key(key)
    resolve_index = resolve_index_for_phase(phase)
    route = {
        "fromRole": from_role,
        "fromObject": None if from_role else f"{key}-origin",
        "toZone": f"{key}-destination",
        "resolveIndex": resolve_index,
        "arrowStyle": str(updated.get("arrowStyle", "movement")),
        "intent": "reset" if phase in {"reset", "next_read_setup"} else "reposition",
        "startLabel": "起点",
        "endLabel": "目标点",
        "snapToTarget": bool(updated.get("snapToTarget", False)),
    }
    updated["movementRoute"] = route
    updated["routeIntent"] = route["intent"]
    for field in ("fromRole", "fromObject", "toZone", "resolveIndex", "startLabel", "endLabel", "snapToTarget"):
        if route.get(field) is not None:
            updated[field] = route[field]
    return updated


def damage_pattern(
    key: str,
    kind: str,
    *,
    source: str,
    targets: list[str],
    resolve_index: int,
    resolve_timing: str,
    aoe_intent: str,
    label: str,
    **kwargs: Any,
) -> dict[str, Any]:
    pattern = {
        "kind": kind,
        "source": source,
        "targets": targets,
        "resolveIndex": resolve_index,
        "resolveTiming": resolve_timing,
        "aoeIntent": aoe_intent,
        "label": label,
        "renderLabel": kwargs.pop("renderLabel", False),
        **kwargs,
    }
    return {"kind": "damagePattern", "key": key, "damagePattern": pattern}


def phase_v_damage_patterns(step_index: int, item: dict[str, Any], categories: set[str]) -> list[dict[str, Any]]:
    phase = str(item.get("storyboard_phase", ""))
    prefix = f"phase-v-{step_index:02d}"
    patterns: list[dict[str, Any]] = []
    if step_index == 1:
        patterns.append(
            damage_pattern(
                f"{prefix}-boss-hitbox",
                "bossHitbox",
                source="Boss",
                targets=[],
                resolve_index=0,
                resolve_timing="preposition",
                aoe_intent="reference_only",
                label="Boss 目标圈",
                radius=72,
            )
        )
    if "cleave" in categories and phase in {"assignment", "assign_roles", "preposition"}:
        patterns.append(
            damage_pattern(
                f"{prefix}-safe-sector",
                "safeSector",
                source="Boss",
                targets=ALL_ROLES,
                resolve_index=1,
                resolve_timing="cast_snapshot",
                aoe_intent="safe",
                label="安全扇区",
                angle=90,
                rotation=180,
                radius=250,
            )
        )
    if ("sequence" in categories or "bait" in categories) and phase in {"first_move", "second_move"}:
        patterns.append(
            damage_pattern(
                f"{prefix}-bait-trail",
                "baitTrail",
                source="D3/D4",
                targets=["D3", "D4"],
                resolve_index=1 if phase == "first_move" else 2,
                resolve_timing="cast_snapshot",
                aoe_intent="bait_history",
                label="诱导轨迹",
                points=[[-156, -112], [-82, -58], [0, 0], [82, 58], [156, 112]],
                circleRadius=30,
            )
        )
    if "stack" in categories and phase in {"first_resolve", "second_resolve"}:
        patterns.append(
            damage_pattern(
                f"{prefix}-share-fan",
                "shareFan90",
                source="Boss",
                targets=["H1", "H2", "D3", "D4"],
                resolve_index=1 if phase == "first_resolve" else 2,
                resolve_timing="first_hit" if phase == "first_resolve" else "second_hit",
                aoe_intent="damage",
                label="火：四人分摊90度",
                angle=90,
                rotation=90,
                radius=250,
            )
        )
    if "spread" in categories and phase == "second_resolve":
        patterns.append(
            damage_pattern(
                f"{prefix}-fan-spread",
                "fan120",
                source="Boss",
                targets=["D1", "D2", "D3"],
                resolve_index=2,
                resolve_timing="second_hit",
                aoe_intent="damage",
                label="雷：三人分散120度",
                angle=120,
                radius=260,
                rotations=[90, 210, 330],
            )
        )
    if "cleave" in categories and phase == "second_resolve":
        patterns.append(
            damage_pattern(
                f"{prefix}-charge-line",
                "chargeLine",
                source="Boss",
                targets=ALL_ROLES,
                resolve_index=2,
                resolve_timing="second_hit",
                aoe_intent="damage",
                label="残影冲锋线",
                width=104,
                height=540,
                rotation=90,
            )
        )
    if phase in {"first_resolve", "second_resolve", "resolve"} and not patterns:
        patterns.append(
            damage_pattern(
                f"{prefix}-safe-sector",
                "safeSector",
                source="Boss",
                targets=ALL_ROLES,
                resolve_index=max(resolve_index_for_phase(phase), 1),
                resolve_timing="first_hit" if phase == "first_resolve" else "second_hit",
                aoe_intent="safe",
                label="安全扇区",
                angle=90,
                radius=240,
            )
        )
    return patterns


def apply_phase_v_semantics(steps: list[dict[str, Any]], categories: set[str]) -> list[dict[str, Any]]:
    semantic_steps: list[dict[str, Any]] = []
    for step_index, item in enumerate(steps, start=1):
        updated = dict(item)
        phase = str(updated.get("storyboard_phase", ""))
        objects: list[dict[str, Any]] = []
        for obj in updated.get("objects", []):
            if isinstance(obj, dict) and obj.get("kind") in {"arrow", "path", "polyline"}:
                objects.append(decorate_movement_route(obj, step_index, phase))
            elif isinstance(obj, dict) and obj.get("kind") == "tower" and "tower" in categories and phase in {"first_move", "first_resolve"}:
                tower = dict(obj)
                tower["damagePattern"] = {
                    "kind": "towerResolve",
                    "source": "arena",
                    "targets": ALL_ROLES,
                    "resolveIndex": 1,
                    "resolveTiming": "first_hit",
                    "aoeIntent": "damage",
                    "label": str(tower.get("label") or "四塔判定"),
                    "renderLabel": False,
                }
                objects.append(tower)
            else:
                objects.append(obj)
        objects.extend(phase_v_damage_patterns(step_index, updated, categories))
        updated["objects"] = objects
        semantic_steps.append(updated)
    return semantic_steps


def party_objects(distance: int = 108, positions: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    objects = []
    for role in ROLES:
        defaults = DEFAULT_PARTY_JOBS[role]
        obj: dict[str, Any] = {
            "kind": "party",
            "key": role,
            "role": role,
            "job": defaults["job"],
            "jobName": defaults["jobName"],
            "icon": defaults["icon"],
            "roleLabel": role,
            "roleLabelPlacement": "near-icon",
            "pos": ROLE_DIR[role],
            "distance": distance,
        }
        if positions and role in positions:
            obj["pos"] = positions[role]
        objects.append(obj)
    return objects


def pos_to_spec(value: Any) -> dict[str, float]:
    if not isinstance(value, list) or len(value) != 2:
        return {"x": 0, "y": 0}
    return {"x": float(value[0]), "y": float(value[1])}


def direction_point(direction: str, distance: float = 110) -> tuple[float, float]:
    radians = math.radians(DIRECTION_DEGREES[direction])
    return math.cos(radians) * distance, math.sin(radians) * distance


def movement_arrow(role: str, move: dict[str, Any]) -> dict[str, Any] | None:
    target = pos_to_spec(move.get("to"))
    start = direction_point(ROLE_DIR[role])
    end = (target["x"], target["y"])
    if math.dist(start, end) < 90:
        return None
    return {"kind": "arrow", "key": f"move-{role.lower()}", "from": ROLE_DIR[role], "to": target, "distance": 110, "arrowStyle": "movement", "endGap": 34}


def has_flow_object(objects: list[dict[str, Any]]) -> bool:
    return any(obj.get("kind") in {"arrow", "path", "polyline", "tether", "link"} for obj in objects if isinstance(obj, dict))


def default_flow_object(flow_kind: str) -> dict[str, Any]:
    if flow_kind == "reset":
        return {
            "kind": "arrow",
            "key": "auto-reset-flow",
            "from": [220, -20],
            "to": [145, -20],
            "arrowStyle": "reset",
            "flowLabel": "auto-reset",
        }
    if flow_kind == "knockback":
        return {
            "kind": "arrow",
            "key": "auto-knockback-flow",
            "from": "center",
            "to": "N",
            "distance": 220,
            "arrowStyle": "knockback",
            "allowDangerCrossing": True,
            "endGap": 58,
            "flowLabel": "auto-knockback",
        }
    if flow_kind == "bait":
        return {
            "kind": "arrow",
            "key": "auto-bait-flow",
            "from": [-210, 145],
            "to": [-135, 145],
            "arrowStyle": "bait",
            "flowLabel": "auto-bait",
        }
    if flow_kind == "forbidden":
        return {
            "kind": "arrow",
            "key": "auto-forbidden-flow",
            "from": [-170, 0],
            "to": [170, 0],
            "arrowStyle": "forbidden",
            "routeCheck": False,
            "flowLabel": "auto-forbidden",
        }
    return {
        "kind": "polyline",
        "key": "auto-movement-flow",
        "from": [-205, -150],
        "waypoints": [[-170, -95]],
        "to": [-128, -66],
        "arrowStyle": "movement",
        "flowLabel": "auto-movement",
    }


def infer_flow_kind(phase: str, objects: list[dict[str, Any]], explicit: str | None = None) -> str:
    if explicit:
        return explicit
    kinds = {str(obj.get("kind", "")).lower() for obj in objects if isinstance(obj, dict)}
    if "knockback" in kinds or "line_knockback" in kinds or "lineknockback" in kinds:
        return "knockback"
    if "tether" in kinds or "link" in kinds:
        return "bait"
    if "forbidden" in kinds:
        return "forbidden"
    if phase == "reset":
        return "reset"
    return "movement"


def requires_movement(phase: str, objects: list[dict[str, Any]], explicit: bool | None = None) -> bool:
    if explicit is not None:
        return explicit
    if phase in {"move", "first_move", "second_move", "between_resolves", "reset", "next_read_setup"}:
        return True
    return any(str(obj.get("arrowStyle", "")).lower() in {"bait", "knockback", "forbidden"} for obj in objects if isinstance(obj, dict))


def find_candidate(bundle: dict[str, Any], score_report: dict[str, Any] | None, candidate_id: str | None) -> dict[str, Any]:
    selected = candidate_id or (score_report or {}).get("recommended_candidate")
    candidates = {candidate.get("id"): candidate for candidate in bundle.get("candidates", [])}
    if selected not in candidates:
        selected = next(iter(candidates), None)
    if not selected:
        raise ValueError("no candidate available")
    return candidates[selected]


def category_set(bundle: dict[str, Any]) -> set[str]:
    categories = {str(item) for item in bundle.get("planning_context", {}).get("categories", [])}
    if "light-rampant-like" in categories:
        categories.update({"tower", "tether", "spread"})
    if "tile-platform" in categories:
        categories.add("tile")
    if "sequence" in categories:
        categories.add("case-based")
    return categories


def is_status_driven(bundle: dict[str, Any], categories: set[str]) -> bool:
    if categories & STATUS_DRIVEN_CATEGORIES:
        return True
    planning_context = bundle.get("planning_context", {})
    text = " ".join(
        str(value)
        for value in (
            bundle.get("mechanic", ""),
            planning_context.get("summary", "") if isinstance(planning_context, dict) else "",
            " ".join(str(item) for item in planning_context.get("unknowns", [])) if isinstance(planning_context, dict) else "",
        )
    ).lower()
    triggers = (
        "buff",
        "debuff",
        "status",
        "hello world",
        "relativity",
        "high concept",
        "状态",
        "点名",
        "颜色",
        "倒计时",
        "延时",
        "短时",
        "长时",
        "世界第一",
        "世界第二",
    )
    return any(trigger in text for trigger in triggers)


def default_status_assignments() -> list[dict[str, Any]]:
    templates = [
        ("MT", "短红", "short", "短", "red-short"),
        ("ST", "长红", "red", "长", "red-long"),
        ("H1", "短蓝", "blue", "短", "blue-short"),
        ("H2", "长蓝", "long", "长", "blue-long"),
        ("D1", "一组红", "fire", "1", "group-red-1"),
        ("D2", "一组蓝", "ice", "1", "group-blue-1"),
        ("D3", "二组红", "orange", "2", "group-red-2"),
        ("D4", "二组蓝", "purple", "2", "group-blue-2"),
    ]
    return [
        {
            "role": role,
            "statusName": name,
            "kind": "debuff",
            "iconToken": token,
            "fallbackLabel": label,
            "decisionGroup": group,
            "visibleSteps": "all",
            "source": "generated-status-assignment-fallback",
            "confidence": "low",
            "assetStatus": "fallback",
            "assetFallback": "status-icon-fallback",
            "fallbackReason": "No confirmed real status icon asset was provided; use a readable text badge until user/screenshot/source confirms the exact buff icon.",
        }
        for role, name, token, label, group in templates
    ]


def step(
    title: str,
    phase: str,
    purpose: str,
    guide_text: str,
    checks: list[str],
    visual_focus: str,
    required_roles: list[str],
    reset_state: str,
    objects: list[dict[str, Any]] | None = None,
    *,
    focus_roles: list[str] | None = None,
    inherit: bool | None = None,
    updates: dict[str, Any] | None = None,
    remove: list[str] | None = None,
    movement_required: bool | None = None,
    flow_kind: str | None = None,
    teaching_question: str | None = None,
    why_this_frame_exists: str | None = None,
    changed_objects_only: str | None = None,
) -> dict[str, Any]:
    objects = objects or []
    inferred_flow_kind = infer_flow_kind(phase, objects, flow_kind)
    result: dict[str, Any] = {
        "title": title,
        "storyboard_phase": phase,
        "movement_required": requires_movement(phase, objects, movement_required),
        "flow_kind": inferred_flow_kind,
        "teaching_question": teaching_question or f"{purpose.rstrip('。.')}？",
        "why_this_frame_exists": why_this_frame_exists or purpose,
        "changed_objects_only": changed_objects_only or visual_focus,
        "purpose": purpose,
        "guide_text": guide_text,
        "checks": checks,
        "visual_focus": visual_focus,
        "required_roles": required_roles,
        "reset_state": reset_state,
        "objects": objects,
    }
    if focus_roles:
        result["focusRoles"] = focus_roles
    if inherit is not None:
        result["inherit"] = inherit
    if updates:
        result["updates"] = updates
    if remove:
        result["remove"] = remove
    return result


def observation_step(unknowns: list[str]) -> dict[str, Any]:
    callout = "保守假设" if unknowns else "信息已知"
    return step(
        "1 观察与信息确认",
        "observe_signal",
        "展示机制读条、未知点和全员默认站位。",
        "先确认机制类别、点名和安全半场；未知点按保守假设处理，不把草案当作最终打法。",
        ["未知点已列入攻略包", "八人、Boss、标点都可见"],
        "机制信息、Boss 中心、八人初始上下文",
        ALL_ROLES,
        "尚未移动，保持八方起手。",
        [
            {"kind": "circle", "key": "read-source-ring", "pos": "center", "radius": 104, "color": "#ffb900", "opacity": 18},
            {"kind": "label", "key": "info-state", "text": callout, "pos": [0, -210]},
        ],
        teaching_question="这一步要先读到什么机制信息？",
        why_this_frame_exists="先冻结读条、未知点和全员上下文，避免后续移动没有判断来源。",
        changed_objects_only="读条提示、未知点状态和机制源提示。",
    )


def preposition_step(candidate: dict[str, Any]) -> dict[str, Any]:
    guide_text = candidate.get("step_plan", [{}, {"guide_text": "按职能固定预站。"}])[1].get("guide_text", "按职能固定预站。")
    return step(
        "2 固定预站",
        "assign_roles",
        "固定八人初始职责，给后续模板提供稳定起点。",
        guide_text,
        ["八个职能都有初始站位", "读条职业优先少移动"],
        "职能八方、内圈安全锚点",
        ALL_ROLES,
        "预站完成后等待第一轮读条。",
        [{"kind": "circle", "key": "safe-center", "pos": "center", "radius": 128, "color": "#8fd14f", "opacity": 18, "label": "内圈"}],
        teaching_question="每个职责的默认起点在哪里？",
        why_this_frame_exists="把职责分配从移动和判定中拆出来，保证队员先知道自己属于哪一组。",
        changed_objects_only="八方职责锚点和内圈安全参考。",
    )


def tower_steps() -> list[dict[str, Any]]:
    towers = [
        {"kind": "tower", "key": "tower-n", "pos": "N", "distance": 190, "count": 2, "label": "T/H"},
        {"kind": "tower", "key": "tower-s", "pos": "S", "distance": 190, "count": 2, "label": "T/H"},
        {"kind": "tower", "key": "tower-e", "pos": "E", "distance": 190, "count": 2, "label": "DPS"},
        {"kind": "tower", "key": "tower-w", "pos": "W", "distance": 190, "count": 2, "label": "DPS"},
    ]
    return [
        step(
            "塔出现",
            "observe_signal",
            "把塔位和每塔人数单独展示，避免职责和移动混在一张图里。",
            "先读四座塔的位置和人数，按固定职能分桶处理。",
            ["塔位清楚", "每塔人数清楚"],
            "塔位、塔人数、职能分桶",
            ALL_ROLES,
            "读塔后不急动，等待入塔提示。",
            towers,
            teaching_question="塔刷在哪里、每座塔需要几个人？",
            why_this_frame_exists="先看塔位和人数，避免把读塔和入塔路线挤在同一帧。",
            changed_objects_only="四座塔和人数标签出现。",
        ),
        step(
            "入塔职责",
            "first_move",
            "显示每组进入对应塔位的移动方向。",
            "T/H 处理南北塔，DPS 处理东西塔；移动路线短且不穿中心。",
            ["入塔路线不交叉", "每塔至少标明职责组"],
            "入塔路线和当前行动组",
            ALL_ROLES,
            "入塔后保持到判定结束。",
            towers
            + [
                {"kind": "arrow", "key": "tower-mt", "from": [0, 44], "to": [0, 190], "arrowStyle": "movement", "endGap": 44},
                {"kind": "arrow", "key": "tower-st", "from": [0, -44], "to": [0, -190], "arrowStyle": "movement", "endGap": 44},
                {"kind": "arrow", "key": "tower-d2", "from": [44, 0], "to": [190, 0], "arrowStyle": "movement", "endGap": 44},
                {"kind": "arrow", "key": "tower-d1", "from": [-44, 0], "to": [-190, 0], "arrowStyle": "movement", "endGap": 44},
            ],
            focus_roles=ALL_ROLES,
            teaching_question="每组从哪里进到哪座塔？",
            why_this_frame_exists="把入塔路线单独画出，队员不用同时读塔位和移动方向。",
            changed_objects_only="入塔箭头和当前行动组。",
        ),
    ]


def stack_steps() -> list[dict[str, Any]]:
    return [
        step(
            "分摊目标确认",
            "first_resolve",
            "拆出分摊人数和分组，不和散开或塔判定混读。",
            "A/B 两组各自集合，若实际点名不同，以点名者为中心微调。",
            ["分摊人数明确", "分组边界明确"],
            "分摊圈、分组标签",
            ALL_ROLES,
            "分摊后准备散开或回中。",
            [
                {"kind": "stack", "key": "stack-a", "pos": "W", "distance": 95, "radius": 58, "count": 4, "label": "A组"},
                {"kind": "stack", "key": "stack-b", "pos": "E", "distance": 95, "radius": 58, "count": 4, "label": "B组"},
            ],
            teaching_question="哪两组要分别吃分摊？",
            why_this_frame_exists="让分摊目标和人数成为独立判断，不和后续散开或入塔混在一起。",
            changed_objects_only="A/B 分摊圈与人数标签。",
        )
    ]


def spread_circle_objects() -> list[dict[str, Any]]:
    label_pos = {
        "MT": [0, 188],
        "ST": [0, -188],
        "H1": [-188, 0],
        "H2": [188, 0],
        "D1": [-235, 222],
        "D2": [235, 222],
        "D3": [-235, -222],
        "D4": [235, -222],
    }
    return [
        {
            "kind": "circle",
            "key": f"spread-{role}",
            "pos": direction,
            "distance": 190 if role.startswith("D") else 135,
            "radius": 34,
            "label": role,
            "labelPos": label_pos[role],
            "labelFontSize": 14,
        }
        for role, direction in ROLE_DIR.items()
    ]


def spread_steps() -> list[dict[str, Any]]:
    return [
        step(
            "散开点名",
            "first_resolve",
            "把每个角色的散开落点从其他判定中拆出来。",
            "按八方或指定 clock 散开，DPS 外圈、T/H 内圈，保持最小间距。",
            ["八个散开点不重叠", "远近职责没有互抢位置"],
            "散开圈、角色标签",
            ALL_ROLES,
            "散开判定后立刻看复位箭头。",
            spread_circle_objects(),
            teaching_question="每个职责最终散开落点在哪里？",
            why_this_frame_exists="单独展示八方散开，避免和移动或其他判定压成一帧。",
            changed_objects_only="八个散开圈和职责标签。",
        )
    ]


def tether_steps() -> list[dict[str, Any]]:
    return [
        step(
            "连线出现",
            "observe_signal",
            "把连线方向和不能交叉的关系单独展示。",
            "先读连线端点，同半场拉开；不要横穿 Boss 圈。",
            ["连线端点清楚", "禁止交叉已说明"],
            "连线端点、半场边界",
            DPS_ROLES,
            "读线后等待拉线路线。",
            [
                {"kind": "circle", "key": "tether-source-ring", "pos": "center", "radius": 128, "color": "#ffb900", "opacity": 18},
                {"kind": "arrow", "key": "tether-nw", "from": "NW", "to": "N", "distance": 205, "arrowStyle": "bait", "endGap": 40},
                {"kind": "arrow", "key": "tether-se", "from": "SE", "to": "S", "distance": 205, "arrowStyle": "bait", "endGap": 40},
            ],
            focus_roles=DPS_ROLES,
            teaching_question="先看哪些端点被连线？",
            why_this_frame_exists="连线端点是后续拉线方向的前置判断，必须先单独读清楚。",
            changed_objects_only="连线端点、半场边界和禁止交叉提示。",
        ),
        step(
            "拉线方向",
            "first_move",
            "显示拉线者的安全移动路径。",
            "拉线者沿同侧外圈移动，线不交叉；非拉线者保留上下文但降低存在感。",
            ["拉线方向与 guide_text 一致", "箭头头部不压玩家"],
            "拉线箭头、外圈移动方向",
            DPS_ROLES,
            "拉线完成后等判定，再回中。",
            [
                {"kind": "circle", "key": "tether-safe-ring", "pos": "center", "radius": 172, "color": "#8fd14f", "opacity": 14},
                {"kind": "polyline", "key": "tether-route-left", "from": "NW", "waypoints": [[-175, 45]], "to": "W", "distance": 190, "arrowStyle": "movement", "endGap": 42},
                {"kind": "polyline", "key": "tether-route-right", "from": "SE", "waypoints": [[175, -45]], "to": "E", "distance": 190, "arrowStyle": "movement", "endGap": 42},
            ],
            focus_roles=DPS_ROLES,
            teaching_question="拉线者沿哪条路线拉开？",
            why_this_frame_exists="把拉线移动从连线观察中拆出来，降低路线交叉误读。",
            changed_objects_only="外圈移动路线和拉线者高亮。",
        ),
    ]


def knockback_steps() -> list[dict[str, Any]]:
    return [
        step(
            "击退源与预站",
            "preposition",
            "先画击退源和防击退/落点选择。",
            "以中心击退源为基准预站，确认是否开防击退；不开则对准安全落点。",
            ["击退源可见", "落点不在危险区"],
            "击退源、预站点、安全落点",
            ALL_ROLES,
            "预站后等击退结算。",
            [
                {"kind": "knockback", "key": "kb-source", "pos": "center", "radius": 82, "color": "#d13438", "opacity": 35, "label": "击退源"},
                {"kind": "safe_circle", "key": "kb-safe", "pos": "N", "distance": 220, "radius": 70, "label": "落点"},
            ],
            teaching_question="击退源在哪里、预站要对准哪一侧？",
            why_this_frame_exists="击退前先确认源点和安全落点，避免直接跳到位移结果。",
            changed_objects_only="击退源、预站提示和安全落点。",
        ),
        step(
            "击退落点",
            "first_move",
            "把强制位移方向和最终落点拆成独立画面。",
            "击退方向从源点指向安全区；被击退后先站稳，再处理下一判定。",
            ["击退箭头起点在机制源", "箭头终点不压玩家"],
            "宽击退箭头、落点安全区",
            ALL_ROLES,
            "落点稳定后进入结算或复位。",
            [{"kind": "arrow", "key": "kb-arrow", "from": "center", "to": "N", "distance": 220, "arrowStyle": "knockback", "allowDangerCrossing": True, "endGap": 58}],
            teaching_question="击退会把人推到哪里？",
            why_this_frame_exists="强制位移方向需要独立展示，和预站判断分开读。",
            changed_objects_only="击退箭头和最终落点方向。",
        ),
    ]


def dance_steps() -> list[dict[str, Any]]:
    return [
        step(
            "Case 读取",
            "observe_signal",
            "把分支条件作为独立读取画面，避免边读边移动。",
            "确认当前 case 后只执行对应路线；没有被点名者保持默认位。",
            ["case 标签清楚", "未确认分支不画成事实"],
            "case 标签、当前读法",
            ALL_ROLES,
            "读 case 后进入第一拍路线。",
            [{"kind": "label", "key": "case-label", "text": "Case A / B", "pos": [0, 205]}],
            teaching_question="当前是哪一个 case？",
            why_this_frame_exists="分支条件决定后续路线，必须先确认 case 再移动。",
            changed_objects_only="case 标签和当前读法提示。",
        ),
        step(
            "分支 A 示例",
            "assignment",
            "单独展示第一种读法的职责换算，不把多个 case 压进同一张图。",
            "Case A 先按北侧安全处理，T/H 保南北锚点，DPS 按东西补位；若实战点名不同，只替换本页分支。",
            ["分支名清楚", "职责换算不和移动箭头混读"],
            "Case A 分支、职责换算、优先级",
            ALL_ROLES,
            "读完分支 A 后进入对应第一拍路线。",
            [
                {"kind": "rect", "key": "case-a-safe-band", "pos": "N", "distance": 110, "width": 430, "height": 92, "color": "#8fd14f", "opacity": 18, "label": "A分支安全"},
                {"kind": "label", "key": "case-a-priority", "text": "北优先 / 南补位", "pos": [-132, 198], "fontSize": 13, "labelRole": "priority"},
            ],
            teaching_question="Case A 的职责优先级怎么换算？",
            why_this_frame_exists="组合机制需要分支页，队员才能只读当前条件下的优先级。",
            changed_objects_only="Case A 安全带、职责优先级和补位提示。",
        ),
        step(
            "分支 B 示例",
            "assignment",
            "单独展示第二种读法，把镜像分支从通用流程里拆出来。",
            "Case B 以东西安全为主，D3/D4 负责最远诱导，T/H 保持 Boss 目标圈附近，避免和 Case A 互相污染。",
            ["镜像分支和 A 分支可区分", "例外提醒进入图内"],
            "Case B 分支、诱导职责、例外提醒",
            ALL_ROLES,
            "读完分支 B 后进入对应第一拍路线。",
            [
                {"kind": "rect", "key": "case-b-safe-band", "pos": "E", "distance": 110, "width": 92, "height": 430, "color": "#2aa7ff", "opacity": 18, "label": "B分支安全"},
                {"kind": "label", "key": "case-b-priority", "text": "D3/D4 最远诱导", "pos": [132, 198], "fontSize": 13, "labelRole": "priority"},
            ],
            teaching_question="Case B 哪些职责负责诱导和补位？",
            why_this_frame_exists="把镜像或例外分支独立成页，防止同一张图同时讲两套规则。",
            changed_objects_only="Case B 安全带、最远诱导职责和例外提醒。",
        ),
        step(
            "第一拍路线",
            "first_move",
            "显示舞蹈机制第一拍的路线，不和后续拍混在一起。",
            "当前行动者按箭头移动，其余人保留原位等待下一拍。",
            ["路线不交叉", "行动者明确"],
            "第一拍移动箭头",
            ["MT", "ST"],
            "第一拍结束后停在半场边缘。",
            [
                {"kind": "polyline", "key": "dance-mt", "from": "N", "waypoints": [[-75, 165]], "to": "NW", "distance": 135, "arrowStyle": "movement", "endGap": 42},
                {"kind": "polyline", "key": "dance-st", "from": "S", "waypoints": [[75, -165]], "to": "SE", "distance": 135, "arrowStyle": "movement", "endGap": 42},
            ],
            focus_roles=["MT", "ST"],
            teaching_question="第一拍由谁先动、动到哪里？",
            why_this_frame_exists="第一拍路线和后续拍分开，避免舞蹈机制被压缩成摘要图。",
            changed_objects_only="MT/ST 第一拍路线和行动者高亮。",
        ),
    ]


def tile_steps() -> list[dict[str, Any]]:
    return [
        step(
            "地板状态",
            "observe_signal",
            "先展示哪些格子可用，避免路线图缺少场地状态。",
            "红色格子不可站，绿色格子为下一步安全路线。",
            ["可用格和危险格分色", "场地状态先于人物移动"],
            "安全格、危险格、平台边界",
            ALL_ROLES,
            "确认地板后再移动。",
            [
                {"kind": "rect", "key": "tile-danger", "pos": "E", "distance": 75, "width": 120, "height": 360, "color": "#d13438", "opacity": 26},
                {"kind": "rect", "key": "tile-safe", "pos": "W", "distance": 75, "width": 120, "height": 360, "color": "#8fd14f", "opacity": 28, "label": "安全格"},
            ],
            teaching_question="哪些地板能站、哪些地板不能站？",
            why_this_frame_exists="先读地板状态，再画路线，避免队员不知道为什么绕行。",
            changed_objects_only="安全格、危险格和平台边界。",
        ),
        step(
            "格子移动",
            "first_move",
            "显示跨格移动路线，确保不穿过不可用地板。",
            "全员沿安全格一侧移动，避免穿越红色格。",
            ["路线绕过危险格", "终点在可用平台"],
            "跨格路线、安全格边界",
            ALL_ROLES,
            "抵达安全格后等待结算。",
            [{"kind": "polyline", "key": "tile-route", "from": "S", "waypoints": [[-105, -70], [-105, 70]], "to": "N", "distance": 165, "arrowStyle": "movement", "endGap": 48}],
            teaching_question="全员沿哪条格子路线移动？",
            why_this_frame_exists="把路线放在地板读法之后，明确移动不穿过危险格。",
            changed_objects_only="跨格移动路线和终点。",
        ),
    ]


def movement_step(candidate: dict[str, Any], movement_targets: dict[str, Any], movement_arrows: list[dict[str, Any]]) -> dict[str, Any]:
    focus_roles = [move.get("role") for move in candidate.get("movements", []) if move.get("role") in ROLES]
    return step(
        "主要移动",
        "second_move",
        "执行推荐候选的主要移动窗口。",
        "只移动需要处理当前职责的人；近战保持目标圈附近，D4 和治疗尽量在自然窗口移动。",
        ["读条职业移动窗口已标注", "近战离圈时间最短"],
        "当前行动者、主移动路线、目标落点",
        focus_roles or ALL_ROLES,
        "移动完成后进入结算画面。",
        party_objects(108, movement_targets)
        + [
            {"kind": "circle", "key": "movement-window", "pos": "center", "radius": 146, "color": "#8fd14f", "opacity": 14},
        ]
        + movement_arrows,
        focus_roles=focus_roles or None,
        teaching_question="当前候选打法里真正需要移动的是谁？",
        why_this_frame_exists="把推荐方案的主移动窗口从职责分配和判定结果中拆出来。",
        changed_objects_only="行动者、主移动箭头和目标落点。",
    )


def final_resolution_step(categories: set[str], movement_targets: dict[str, Any]) -> dict[str, Any]:
    return step(
        "最终判定",
        "second_resolve",
        "显示最后的安全站位和判定范围。",
        "完成散开、双分摊或安全半场判定；出错时优先保持不撞线、不抢塔。",
        ["散开距离足够", "安全区/危险区不冲突"],
        "最终站位、判定范围、安全/危险区",
        ALL_ROLES,
        "判定后立刻回中或回八方。",
        party_objects(108, movement_targets) + final_resolution_objects(categories),
        teaching_question="移动后最终在哪里吃判定？",
        why_this_frame_exists="把最终站位和判定范围作为单独结果帧，方便复盘是否撞线或抢塔。",
        changed_objects_only="最终站位、判定范围和安全/危险区。",
    )


def reset_step() -> dict[str, Any]:
    return step(
        "复位与下一轮起手",
        "reset",
        "判定结束后统一回到下一机制起点。",
        "结算后回中或回八方，保持下一读条前的复位节奏。",
        ["复位点明确", "下一机制起手位置明确"],
        "复位集合点、下一轮起手方向",
        ALL_ROLES,
        "回中集合，准备下一机制。",
        party_objects(92)
        + [
            {"kind": "stack", "key": "reset", "pos": "center", "radius": 74, "count": 8, "label": "复位"},
            {"kind": "arrow", "key": "reset-east", "from": [220, -20], "to": [145, -20], "arrowStyle": "reset"},
            {"kind": "arrow", "key": "reset-west", "from": [-220, 20], "to": [-145, 20], "arrowStyle": "reset"},
        ],
        flow_kind="reset",
        teaching_question="判定后队伍如何回到可控位置？",
        why_this_frame_exists="结算后需要统一复位，避免下一机制从混乱站位开始。",
        changed_objects_only="复位集合点和回中箭头。",
    )


def next_read_setup_step() -> dict[str, Any]:
    return step(
        "下一读条准备",
        "next_read_setup",
        "重新展开到下一读条可用的八方起手。",
        "复位完成后按八方重新展开，Boss 居中，下一轮读条从同一语法继续。",
        ["八方职责已恢复", "下一读条起点明确"],
        "下一读条八方起手、Boss 中心、稳定标点",
        ALL_ROLES,
        "八方起手已恢复，等待下一机制。",
        party_objects(108)
        + [
            {
                "kind": "circle",
                "key": "next-read-ring",
                "pos": "center",
                "radius": 154,
                "color": "#8fd14f",
                "opacity": 14,
                "label": "下一读条",
                "labelPlacement": "fixed",
                "labelPos": [0, -210],
                "leaderLine": False,
            },
            {"kind": "arrow", "key": "next-read-reset-a", "from": [220, -20], "to": [160, -20], "arrowStyle": "reset", "endGap": 28},
            {"kind": "arrow", "key": "next-read-reset-b", "from": [-220, 20], "to": [-160, 20], "arrowStyle": "reset", "endGap": 28},
        ],
        movement_required=True,
        flow_kind="reset",
        teaching_question="下一轮从什么阵型重新开始？",
        why_this_frame_exists="把复位结果和下一读条起手分开，保证长机制有明确衔接帧。",
        changed_objects_only="八方重新展开和下一读条准备圈。",
    )


def ensure_flow_objects(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in steps:
        objects = item.setdefault("objects", [])
        if not isinstance(objects, list):
            continue
        if item.get("movement_required") and not has_flow_object(objects):
            flow_kind = infer_flow_kind(str(item.get("storyboard_phase", "")), objects, str(item.get("flow_kind", "")) or None)
            objects.append(default_flow_object(flow_kind))
            item["flow_kind"] = flow_kind
    return steps


def storyboard_templates(categories: set[str]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    if "tile" in categories or "tile-platform" in categories:
        templates.extend(tile_steps())
    if "case-based" in categories or "sequence" in categories:
        templates.extend(dance_steps())
    if "knockback" in categories:
        templates.extend(knockback_steps())
    if "tower" in categories:
        templates.extend(tower_steps())
    if "tether" in categories:
        templates.extend(tether_steps())
    if "stack" in categories:
        templates.extend(stack_steps())
    if "spread" in categories:
        templates.extend(spread_steps())
    if not templates:
        templates.append(
            step(
                "机制判定",
                "resolve",
                "显示当前机制的主要判定范围。",
                "按图确认安全区和危险区，再进入移动或复位。",
                ["安全区可见", "危险区可见"],
                "主要判定范围",
                ALL_ROLES,
                "判定后进入复位。",
                [{"kind": "circle", "key": "resolve-a", "pos": "center", "radius": 120, "label": "判定"}],
            )
        )
    return templates


def cap_storyboard_steps(steps: list[dict[str, Any]], max_steps: int = 16) -> list[dict[str, Any]]:
    if len(steps) <= max_steps:
        return steps
    required_tail = steps[-2:]
    middle = steps[2:-2]
    keep_middle = middle[: max_steps - 4]
    return steps[:2] + keep_middle + required_tail


def renumber_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    renumbered = []
    for index, item in enumerate(steps, start=1):
        updated = dict(item)
        title = str(updated.get("title", f"Step {index}"))
        title = title.split(" ", 1)[1] if title[:2].strip().isdigit() and " " in title else title
        updated["title"] = f"{index} {title}"
        renumbered.append(updated)
    return renumbered


def build_steps(bundle: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    movement_targets = {move["role"]: pos_to_spec(move.get("to")) for move in candidate.get("movements", []) if move.get("role") in ROLES}
    movement_arrows = [
        arrow
        for role, move in ((m.get("role"), m) for m in candidate.get("movements", []))
        if role in ROLE_DIR
        for arrow in [movement_arrow(role, move)]
        if arrow is not None
    ]
    categories = category_set(bundle)
    unknowns = bundle.get("planning_context", {}).get("unknowns", [])
    steps = [observation_step(unknowns), preposition_step(candidate)]
    steps.extend(storyboard_templates(categories))
    steps.append(movement_step(candidate, movement_targets, movement_arrows))
    steps.append(final_resolution_step(categories, movement_targets))
    steps.append(reset_step())
    steps.append(next_read_setup_step())
    steps = renumber_steps(ensure_flow_objects(cap_storyboard_steps(steps)))
    steps = apply_phase_v_semantics(steps, categories)
    return apply_in_scene_annotations(steps, categories, unknowns)


def first_resolution_objects(categories: set[str]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if "tower" in categories:
        objects.extend(
            [
                {"kind": "tower", "key": "tower-n", "pos": "N", "distance": 190, "count": 2, "label": "T/H"},
                {"kind": "tower", "key": "tower-s", "pos": "S", "distance": 190, "count": 2, "label": "T/H"},
                {"kind": "tower", "key": "tower-e", "pos": "E", "distance": 190, "count": 2, "label": "DPS"},
                {"kind": "tower", "key": "tower-w", "pos": "W", "distance": 190, "count": 2, "label": "DPS"},
            ]
        )
    if "tether" in categories:
        objects.extend(
            [
                {"kind": "arrow", "from": "NW", "to": "N", "distance": 205, "arrowStyle": "bait", "endGap": 40},
                {"kind": "arrow", "from": "SE", "to": "S", "distance": 205, "arrowStyle": "bait", "endGap": 40},
            ]
        )
    if "stack" in categories:
        objects.append({"kind": "stack", "key": "stack-a", "pos": "W", "distance": 95, "radius": 58, "count": 4, "label": "A组"})
        objects.append({"kind": "stack", "key": "stack-b", "pos": "E", "distance": 95, "radius": 58, "count": 4, "label": "B组"})
    return objects or [{"kind": "circle", "key": "resolve-a", "pos": "center", "radius": 120, "label": "判定"}]


def final_resolution_objects(categories: set[str]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if "spread" in categories:
        objects.extend(spread_circle_objects())
    if "cleave" in categories:
        objects.append({"kind": "rect", "key": "danger-east", "pos": "E", "distance": 150, "width": 210, "height": 560, "color": "#d13438", "opacity": 24})
        objects.append({"kind": "polygon", "key": "safe-west", "pos": "W", "distance": 115, "radius": 125, "sides": 4, "color": "#8fd14f", "opacity": 28, "label": "安全"})
    if "stack" in categories and "spread" not in categories:
        objects.append({"kind": "stack", "key": "stack-final", "pos": "center", "radius": 74, "count": 8, "label": "八人"})
    return objects or [{"kind": "stack", "key": "resolve-final", "pos": "center", "radius": 74, "count": 8, "label": "结算"}]


def build_spec(bundle: dict[str, Any], score_report: dict[str, Any] | None, candidate_id: str | None) -> dict[str, Any]:
    candidate = find_candidate(bundle, score_report, candidate_id)
    categories = category_set(bundle)
    arena_selection = bundle.get("planning_context", {}).get("arena_selection")
    if not isinstance(arena_selection, dict):
        arena_selection = {
            "preset": "default-circle",
            "source": "default-fallback",
            "reason": "No arena selection was carried by the solution bundle.",
        }
    arena = {
        "preset": arena_selection.get("preset", "default-circle"),
        "source": arena_selection.get("source", "default-fallback"),
        "sourceReason": arena_selection.get("reason", ""),
    }
    spec = {
        "name": f"Phase 12：{bundle.get('mechanic', 'generated solution')} - {candidate.get('id')}",
        "style": "king-x-fru",
        "guide_section": "mechanic_flow",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "annotation_contract": dict(ANNOTATION_CONTRACT),
        "mechanic_semantics_contract": dict(MECHANIC_SEMANTICS_CONTRACT),
        "arena": arena,
        "markerPresets": "cardinals",
        "metadata": {
            "source": "build_spec_from_solution.py",
            "storyboard_generator": "phase-o-v3",
            "storyboard_policy": "teaching-question-template-chain",
            "annotation_generator": "phase-u-in-scene-v1",
            "annotation_policy": "page-title-and-eight-callout-bands",
            "mechanic_semantics_generator": "phase-v-routes-and-ranges-v1",
            "mechanic_semantics_policy": "movement-route-and-damage-pattern-hard-gate",
            "party_defaults": "phase-r-defaults",
            "arena_selection": arena_selection,
            "recommended_candidate": candidate.get("id"),
            "mode": candidate.get("mode"),
            "assumptions": candidate.get("assumptions", []),
            "risks": candidate.get("risks", []),
        },
        "steps": build_steps(bundle, candidate),
    }
    if is_status_driven(bundle, categories):
        spec["status_assignment_contract"] = dict(STATUS_ASSIGNMENT_CONTRACT)
        spec["statusAssignments"] = default_status_assignments()
        metadata = spec.setdefault("metadata", {})
        metadata["status_assignment_generator"] = "phase-x-status-overlays-v1"
        metadata["status_assignment_policy"] = "role-bound-upper-left-overlay-hard-gate"
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a recommended Phase 12 solution candidate into scene spec JSON.")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--scores", type=Path)
    parser.add_argument("--candidate-id")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        bundle = read_json(args.bundle)
        scores = read_json(args.scores) if args.scores else None
        spec = build_spec(bundle, scores, args.candidate_id)
        write_json(args.output, spec)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    print(f"steps: {len(spec['steps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
