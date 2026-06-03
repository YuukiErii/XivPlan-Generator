#!/usr/bin/env python3
"""Regression checks for the Phase G visual quality audit."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from audit_visual_quality import audit_scene
from build_spec_from_solution import build_spec
from build_xivplan_scene import DEFAULT_PARTY_JOBS, FALLBACK_ENEMY_ICON_DATA_URLS, ROLE_NUMBER_ICONS, build_scene
from run_visual_regression import build_semantic_long_flow_spec
from validate_xivplan_scene import validate_scene


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def good_scene() -> dict:
    roles = [
        ("MT", 0, 90),
        ("ST", 0, -90),
        ("H1", -90, 0),
        ("H2", 90, 0),
        ("D1", -70, 70),
        ("D2", 70, 70),
        ("D3", -70, -70),
        ("D4", 70, -70),
    ]
    party = [
        {
            "type": "party",
            "role": role,
            "name": role,
            "job": DEFAULT_PARTY_JOBS[role]["job"],
            "jobName": DEFAULT_PARTY_JOBS[role]["jobName"],
            "icon": DEFAULT_PARTY_JOBS[role]["icon"],
            "image": DEFAULT_PARTY_JOBS[role]["icon"],
            "roleLabel": role,
            "roleLabelVisible": True,
            "x": x,
            "y": y,
            "width": 30,
            "height": 30,
            "id": index,
        }
        for index, (role, x, y) in enumerate(roles, start=10)
    ]
    markers = [
        {"type": "marker", "name": "A", "x": 0, "y": 245, "width": 42, "height": 42, "id": 1},
        {"type": "marker", "name": "B", "x": 245, "y": 0, "width": 42, "height": 42, "id": 2},
        {"type": "marker", "name": "C", "x": 0, "y": -245, "width": 42, "height": 42, "id": 3},
        {"type": "marker", "name": "D", "x": -245, "y": 0, "width": 42, "height": 42, "id": 4},
    ]
    base = (
        markers
        + [
            {
                "type": "enemy",
                "name": "Boss",
                "displayName": "Boss",
                "icon": FALLBACK_ENEMY_ICON_DATA_URLS["boss"],
                "x": 0,
                "y": 0,
                "radius": 45,
                "ring": "dir",
                "targetRing": {"visible": True, "radius": 45, "strokeWidth": 3, "style": "target-ring"},
                "id": 5,
            },
            {"type": "text", "text": "Boss", "x": 0, "y": -190, "fontSize": 14, "id": 6},
        ]
        + party
    )
    return {
        "name": "visual quality smoke",
        "arena": {"shape": "circle", "width": 600, "height": 600, "padding": 120, "grid": {"type": "radial"}},
        "metadata": {"source": "visual-quality-smoke"},
        "steps": [
            {
                "title": "1 观察",
                "storyboard_phase": "observe",
                "purpose": "确认机制。",
                "guide_text": "先观察。",
                "checks": ["八人可见"],
                "visual_focus": "观察",
                "required_roles": [role for role, *_ in roles],
                "reset_state": "保持八方。",
                "objects": base + [{"type": "circle", "x": 0, "y": 0, "radius": 100, "opacity": 20, "id": 40}, {"type": "text", "text": "观察", "x": 0, "y": 185, "id": 41}],
            },
            {
                "title": "2 移动",
                "storyboard_phase": "move",
                "purpose": "显示路线。",
                "guide_text": "沿箭头移动。",
                "checks": ["路线不交叉"],
                "visual_focus": "移动",
                "required_roles": [role for role, *_ in roles],
                "reset_state": "进入判定。",
                "objects": base + [{"type": "arrow", "x": 0, "y": 145, "width": 90, "height": 14, "rotation": 90, "flowStart": [0, 90], "flowEnd": [0, 200], "id": 42}, {"type": "text", "text": "移动", "x": 84, "y": 205, "id": 43}],
            },
            {
                "title": "3 判定",
                "storyboard_phase": "resolve",
                "purpose": "显示判定。",
                "guide_text": "处理判定。",
                "checks": ["判定明确"],
                "visual_focus": "判定",
                "required_roles": [role for role, *_ in roles],
                "reset_state": "判定后回中。",
                "objects": base + [{"type": "stack", "x": 0, "y": 0, "radius": 70, "count": 8, "id": 44}, {"type": "text", "text": "判定", "x": 0, "y": 155, "id": 45}],
            },
            {
                "title": "4 复位",
                "storyboard_phase": "reset",
                "purpose": "回中复位。",
                "guide_text": "回中准备下一轮。",
                "checks": ["复位明确"],
                "visual_focus": "复位",
                "required_roles": [role for role, *_ in roles],
                "reset_state": "回中。",
                "objects": base
                + [
                    {"type": "stack", "x": 0, "y": 0, "radius": 60, "count": 8, "id": 46},
                    {
                        "type": "arrow",
                        "x": 182.5,
                        "y": -20,
                        "width": 75,
                        "height": 12,
                        "rotation": 180,
                        "arrowStyle": "reset",
                        "flowStart": [220, -20],
                        "flowEnd": [145, -20],
                        "id": 52,
                    },
                    {"type": "text", "text": "复位", "x": 0, "y": 145, "id": 47},
                ],
            },
            {
                "title": "5 下一轮起手",
                "storyboard_phase": "reset",
                "purpose": "下一轮起手。",
                "guide_text": "保持八方。",
                "checks": ["下一轮明确"],
                "visual_focus": "起手",
                "required_roles": [role for role, *_ in roles],
                "reset_state": "八方。",
                "objects": base
                + [
                    {"type": "circle", "x": 0, "y": 0, "radius": 80, "opacity": 20, "id": 48},
                    {
                        "type": "arrow",
                        "x": -182.5,
                        "y": 20,
                        "width": 75,
                        "height": 12,
                        "rotation": 0,
                        "arrowStyle": "reset",
                        "flowStart": [-220, 20],
                        "flowEnd": [-145, 20],
                        "id": 53,
                    },
                    {"type": "text", "text": "起手", "x": 0, "y": 160, "id": 49},
                ],
            },
            {
                "title": "6 结束",
                "storyboard_phase": "resolve",
                "purpose": "结束确认。",
                "guide_text": "确认无后续。",
                "checks": ["结束明确"],
                "visual_focus": "结束",
                "required_roles": [role for role, *_ in roles],
                "reset_state": "结束。",
                "objects": base + [{"type": "circle", "x": 0, "y": 0, "radius": 80, "opacity": 20, "id": 50}, {"type": "text", "text": "结束", "x": 0, "y": 160, "id": 51}],
            },
        ],
    }


def bad_scene() -> dict:
    scene = good_scene()
    scene["arena"] = {}
    scene["steps"][0]["objects"] = [obj for obj in scene["steps"][0]["objects"] if obj.get("type") != "party"]
    scene["steps"] = [step for step in scene["steps"] if step.get("storyboard_phase") != "reset"]
    return scene


def label_collision_scene() -> dict:
    scene = good_scene()
    scene["steps"][0]["objects"].append({"type": "text", "text": "A marker title", "x": 0, "y": 245, "fontSize": 20, "id": 200})
    return scene


def movement_without_arrow_scene() -> dict:
    scene = good_scene()
    scene["steps"][1]["movement_required"] = True
    scene["steps"][1]["objects"] = [obj for obj in scene["steps"][1]["objects"] if obj.get("type") != "arrow"]
    return scene


def party_identity_bad_scene() -> dict:
    scene = good_scene()
    for obj in scene["steps"][0]["objects"]:
        if obj.get("type") == "party" and obj.get("role") == "MT":
            obj.pop("job", None)
            obj.pop("jobName", None)
            obj.pop("icon", None)
            obj["image"] = ""
            obj["roleLabel"] = ""
            break
    return scene


def legacy_gold_reference_scene() -> dict:
    scene = json.loads(json.dumps(good_scene()))
    scene["arena"] = {
        "shape": "circle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "radial", "angularDivs": 8, "radialDivs": 1},
        "ticks": {"type": "radial", "majorCount": 8, "minorCount": 72},
        "backgroundImage": "/arena/e11.svg",
    }
    for step in scene["steps"]:
        step.pop("storyboard_phase", None)
        step.pop("reset_state", None)
        for obj in step["objects"]:
            if obj.get("type") == "party":
                role = obj["role"]
                obj["name"] = f"{role} {DEFAULT_PARTY_JOBS[role]['job']}"
                obj.pop("role", None)
                obj.pop("job", None)
                obj.pop("jobName", None)
                obj.pop("roleLabel", None)
                obj.pop("icon", None)
    scene["steps"][0]["objects"].extend(
        [
            {"type": "text", "text": "AC 雷轴", "x": 0, "y": 120, "fontSize": 13, "id": 300},
            {"type": "text", "text": "1/3雷", "x": -68, "y": 68, "fontSize": 12, "id": 301},
            {"type": "cone", "x": 0, "y": 0, "radius": 220, "angle": 120, "rotation": 0, "opacity": 36, "id": 302},
            {"type": "arrow", "x": 0, "y": 56, "width": 18, "height": 112, "rotation": 0, "id": 303},
        ]
    )
    return scene


def party_display_policy_spec(guide_section: str) -> dict:
    return {
        "name": f"party display policy {guide_section}",
        "style": "king-x-fru",
        "guide_section": guide_section,
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": {"preset": "default-circle", "source": "test"},
        "markerPresets": "cardinals",
        "steps": [
            {
                "title": "Display policy smoke",
                "storyboard_phase": "observe",
                "purpose": "Check party icon policy.",
                "guide_text": "Check party icon policy.",
                "checks": ["party identity"],
                "visual_focus": "party identity",
                "required_roles": ["MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"],
                "reset_state": "stable",
                "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center", "radius": 42}],
            }
        ],
    }


def party_object(scene: dict, role: str) -> dict:
    for obj in scene["steps"][0]["objects"]:
        if obj.get("type") == "party" and obj.get("role") == role:
            return obj
    raise AssertionError(f"missing party role {role}")


def phase_v_builder_spec() -> dict:
    spec = party_display_policy_spec("mechanic_flow")
    spec["name"] = "Phase V direct builder smoke"
    spec["mechanic_semantics_contract"] = {
        "require_arrow_semantics": True,
        "require_range_semantics": True,
        "require_resolve_geometry": True,
        "require_danger_crossing_declaration": True,
    }
    step = spec["steps"][0]
    step["storyboard_phase"] = "first_resolve"
    step["objects"].extend(
        [
            {
                "kind": "damagePattern",
                "key": "direct-fan",
                "damagePattern": {
                    "kind": "fan120",
                    "source": "Boss",
                    "targets": ["D1", "D2", "D3"],
                    "resolveIndex": 1,
                    "resolveTiming": "first_hit",
                    "aoeIntent": "damage",
                    "label": "direct thunder fan",
                    "renderLabel": False,
                    "radius": 180,
                },
            },
            {
                "kind": "movementRoute",
                "key": "direct-route",
                "movementRoute": {
                    "fromObject": "direct-origin",
                    "toZone": "direct-destination",
                    "from": [180, -160],
                    "to": [180, -80],
                    "resolveIndex": 1,
                    "arrowStyle": "movement",
                    "intent": "reposition",
                    "startLabel": "start",
                    "endLabel": "target",
                    "snapToTarget": False,
                },
            },
        ]
    )
    return spec


def phase_x_status_assignment_spec() -> dict:
    spec = party_display_policy_spec("mechanic_flow")
    spec["name"] = "Phase X status assignment smoke"
    spec["status_assignment_contract"] = {
        "require_status_overlays": True,
        "require_all_assigned_roles_visible": True,
        "require_status_icon_readability": True,
        "require_fallback_reason": True,
    }
    spec["statusAssignments"] = [
        {
            "role": role,
            "statusName": f"{role} status",
            "kind": "debuff",
            "iconToken": "blue" if index % 2 else "red",
            "fallbackLabel": str(index),
            "decisionGroup": f"group-{index % 2}",
            "visibleSteps": "all",
            "assetStatus": "fallback",
            "assetFallback": "status-icon-fallback",
            "fallbackReason": "Unit test uses deterministic fallback badges instead of real status icon assets.",
        }
        for index, role in enumerate(("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"), start=1)
    ]
    step = spec["steps"][0]
    step["storyboard_phase"] = "assign_roles"
    step["purpose"] = "Check per-player status assignment overlays."
    step["guide_text"] = "Each player keeps a readable status badge on the upper-left of their party icon."
    step["title"] = "1 Status read"
    step["teaching_question"] = "Which status belongs to each player?"
    step["objects"].append({"kind": "circle", "key": "status-read", "pos": "center", "radius": 118, "color": "#8fd14f", "opacity": 16})
    move_step = json.loads(json.dumps(step))
    move_step.update(
        {
            "title": "2 Status move",
            "storyboard_phase": "first_move",
            "purpose": "Move by status while badges stay attached.",
            "guide_text": "Status badges remain attached while players move to their assigned lanes.",
            "teaching_question": "Do status badges stay attached during movement?",
            "movement_required": True,
            "flow_kind": "movement",
            "objects": step["objects"]
            + [{"kind": "arrow", "key": "status-move-a", "from": [218, 118], "to": [260, 176], "arrowStyle": "movement", "endGap": 24}],
        }
    )
    resolve_step = json.loads(json.dumps(step))
    resolve_step.update(
        {
            "title": "3 Status resolve",
            "storyboard_phase": "first_resolve",
            "purpose": "Resolve by visible status group.",
            "guide_text": "The visible badges agree with the safe lane labels during resolution.",
            "teaching_question": "Which status resolves each lane?",
            "objects": step["objects"]
            + [{"kind": "rect", "key": "status-lane", "pos": "W", "distance": 120, "width": 180, "height": 520, "color": "#8fd14f", "opacity": 18}],
        }
    )
    reset_step = json.loads(json.dumps(step))
    reset_step.update(
        {
            "title": "4 Status reset",
            "storyboard_phase": "reset",
            "purpose": "Reset without losing status ownership.",
            "guide_text": "All roles reset and keep the same status overlay for the next read.",
            "teaching_question": "Can the party reset without losing status ownership?",
            "movement_required": True,
            "flow_kind": "reset",
            "objects": step["objects"]
            + [{"kind": "arrow", "key": "status-reset-a", "from": [-260, -176], "to": [-218, -118], "arrowStyle": "reset", "endGap": 24}],
        }
    )
    spec["steps"] = [step, move_step, resolve_step, reset_step]
    return spec


def enemy_identity_spec() -> dict:
    return {
        "name": "enemy identity builder smoke",
        "style": "king-x-fru",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": {"preset": "default-circle"},
        "markerPresets": "cardinals",
        "steps": [
            {
                "title": "1 多目标身份",
                "guide_text": "两个同名小怪必须自动加方向后缀。",
                "objects": [
                    {"kind": "add", "key": "orb-east", "name": "Orb", "pos": "E", "distance": 178},
                    {"kind": "add", "key": "orb-west", "name": "Orb", "pos": "W", "distance": 178},
                    {"kind": "boss", "key": "main-boss", "name": "Main Boss", "pos": "center", "radius": 42, "facing": 180},
                    {"kind": "circle", "key": "danger", "pos": "center", "radius": 110, "opacity": 18},
                ],
            }
        ],
    }


def phase_u_solution_bundle() -> dict:
    return {
        "mechanic": "Ultimate Yokai Star Dance Phase U",
        "planning_context": {
            "categories": ["tower", "stack", "spread", "cleave", "sequence"],
            "unknowns": ["点名规则暂不确定，按保守分支处理。"],
            "arena_selection": {"preset": "default-circle", "source": "test", "reason": "Phase U annotation smoke."},
        },
        "candidates": [
            {
                "id": "safe-prog",
                "name": "Phase U safe prog",
                "summary": "Fixed roles with branch pages and in-scene teaching labels.",
                "mode": "test",
                "assumptions": [],
                "risks": [],
                "step_plan": [
                    {"guide_text": "确认机制类别、分支和安全半场。"},
                    {"guide_text": "全员按固定八方预站，T/H 南北，DPS 东西。"},
                ],
                "movements": [
                    {"role": "MT", "to": [0, 115]},
                    {"role": "ST", "to": [0, -115]},
                    {"role": "H1", "to": [-150, 0]},
                    {"role": "H2", "to": [150, 0]},
                    {"role": "D1", "to": [-110, 110]},
                    {"role": "D2", "to": [110, 110]},
                    {"role": "D3", "to": [-125, -125]},
                    {"role": "D4", "to": [125, -125]},
                ],
            }
        ],
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        good = tmp_path / "good.xivplan"
        bad = tmp_path / "bad.xivplan"
        label_collision = tmp_path / "label-collision.xivplan"
        movement_without_arrow = tmp_path / "movement-without-arrow.xivplan"
        party_identity_bad = tmp_path / "party-identity-bad.xivplan"
        legacy_gold = tmp_path / "legacy-gold.xivplan"
        semantic_long_flow = tmp_path / "semantic-long-flow.xivplan"
        enemy_identity = tmp_path / "enemy-identity.xivplan"
        phase_u_annotation = tmp_path / "phase-u-annotation.xivplan"
        phase_v_semantics_bad = tmp_path / "phase-v-semantics-bad.xivplan"
        phase_x_status = tmp_path / "phase-x-status.xivplan"
        phase_x_status_bad = tmp_path / "phase-x-status-bad.xivplan"
        write_json(good, good_scene())
        write_json(bad, bad_scene())
        write_json(label_collision, label_collision_scene())
        write_json(movement_without_arrow, movement_without_arrow_scene())
        write_json(party_identity_bad, party_identity_bad_scene())
        write_json(legacy_gold, legacy_gold_reference_scene())
        write_json(semantic_long_flow, build_scene(build_semantic_long_flow_spec()))
        identity_scene = build_scene(enemy_identity_spec())
        identity_errors, _counts, _objects = validate_scene(identity_scene)
        assert not identity_errors, identity_errors[:5]
        phase_u_scene = build_scene(build_spec(phase_u_solution_bundle(), None, None))
        phase_u_errors, _counts, _objects = validate_scene(phase_u_scene)
        assert not phase_u_errors, phase_u_errors[:5]
        phase_v_bad_scene = json.loads(json.dumps(phase_u_scene))
        phase_v_bad_arrow = next(
            obj
            for step in phase_v_bad_scene["steps"]
            for obj in step["objects"]
            if obj.get("type") == "arrow"
        )
        for key in ("toRole", "toObject", "toMarker", "toZone"):
            phase_v_bad_arrow.pop(key, None)
        phase_v_bad_errors, _counts, _objects = validate_scene(phase_v_bad_scene)
        assert any("semantic route requires toRole" in error for error in phase_v_bad_errors), phase_v_bad_errors
        phase_v_builder_scene = build_scene(phase_v_builder_spec())
        phase_v_builder_errors, _counts, _objects = validate_scene(phase_v_builder_scene)
        assert not phase_v_builder_errors, phase_v_builder_errors
        phase_x_scene = build_scene(phase_x_status_assignment_spec())
        phase_x_errors, _counts, _objects = validate_scene(phase_x_scene)
        assert not phase_x_errors, phase_x_errors
        phase_x_bad_scene = json.loads(json.dumps(phase_x_scene))
        phase_x_bad_scene["steps"][0]["objects"] = [
            obj
            for obj in phase_x_bad_scene["steps"][0]["objects"]
            if not (obj.get("statusOverlay") is True and obj.get("statusRole") == "MT")
        ]
        phase_x_bad_errors, _counts, _objects = validate_scene(phase_x_bad_scene)
        assert any("missing visible status overlay for MT" in error for error in phase_x_bad_errors), phase_x_bad_errors
        mechanic_flow_scene = build_scene(party_display_policy_spec("mechanic_flow"))
        flow_example_scene = build_scene(party_display_policy_spec("flow_example"))
        mechanic_flow_errors, _counts, _objects = validate_scene(mechanic_flow_scene)
        flow_example_errors, _counts, _objects = validate_scene(flow_example_scene)
        assert not mechanic_flow_errors, mechanic_flow_errors[:5]
        assert not flow_example_errors, flow_example_errors[:5]
        write_json(enemy_identity, identity_scene)
        write_json(phase_u_annotation, phase_u_scene)
        write_json(phase_v_semantics_bad, phase_v_bad_scene)
        write_json(phase_x_status, phase_x_scene)
        write_json(phase_x_status_bad, phase_x_bad_scene)
        good_result = audit_scene(good)
        bad_result = audit_scene(bad)
        label_result = audit_scene(label_collision)
        movement_result = audit_scene(movement_without_arrow)
        party_identity_result = audit_scene(party_identity_bad)
        legacy_gold_strict_result = audit_scene(legacy_gold)
        legacy_gold_reference_result = audit_scene(legacy_gold, reference_mode="gold")
        long_flow_result = audit_scene(semantic_long_flow)
        identity_result = audit_scene(enemy_identity)
        phase_u_result = audit_scene(phase_u_annotation)
        phase_v_bad_result = audit_scene(phase_v_semantics_bad)
        phase_x_result = audit_scene(phase_x_status)
        phase_x_bad_result = audit_scene(phase_x_status_bad)
    assert party_object(mechanic_flow_scene, "MT")["icon"] == ROLE_NUMBER_ICONS["MT"], party_object(mechanic_flow_scene, "MT")
    assert party_object(mechanic_flow_scene, "MT")["partyDisplayStyle"] == "role-number-icon", party_object(mechanic_flow_scene, "MT")
    assert party_object(mechanic_flow_scene, "MT")["roleLabelVisible"] is False, party_object(mechanic_flow_scene, "MT")
    assert not [obj for obj in mechanic_flow_scene["steps"][0]["objects"] if obj.get("labelKind") == "party_role"], mechanic_flow_scene
    assert party_object(flow_example_scene, "MT")["icon"] == DEFAULT_PARTY_JOBS["MT"]["icon"], party_object(flow_example_scene, "MT")
    assert party_object(flow_example_scene, "MT")["partyDisplayStyle"] == "job-icon", party_object(flow_example_scene, "MT")
    assert party_object(flow_example_scene, "MT")["roleLabelVisible"] is True, party_object(flow_example_scene, "MT")
    flow_role_labels = {obj.get("text") for obj in flow_example_scene["steps"][0]["objects"] if obj.get("labelKind") == "party_role"}
    assert {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"} <= flow_role_labels, flow_role_labels
    assert good_result["ok"], good_result
    assert good_result["status"] in {"PASS", "REVIEW"}, good_result
    assert not bad_result["ok"], bad_result
    severe_kinds = {issue["kind"] for issue in bad_result["issues"] if issue["severity"] == "severe"}
    assert {"missing_arena_context", "missing_party_roles"} <= severe_kinds, severe_kinds
    label_kinds = {issue["kind"] for issue in label_result["issues"] if issue["severity"] == "severe"}
    assert "text_vs_marker" in label_kinds, label_kinds
    movement_kinds = {issue["kind"] for issue in movement_result["issues"] if issue["severity"] == "severe"}
    assert "step_missing_flow_layer" in movement_kinds, movement_kinds
    party_identity_kinds = {issue["kind"] for issue in party_identity_result["issues"] if issue["severity"] == "severe"}
    assert {"party_missing_job", "party_missing_job_icon", "party_missing_role_label"} <= party_identity_kinds, party_identity_kinds
    assert not legacy_gold_strict_result["ok"], legacy_gold_strict_result
    assert legacy_gold_reference_result["ok"], legacy_gold_reference_result
    assert legacy_gold_reference_result["status"] == "GOLD_PROFILE", legacy_gold_reference_result
    assert legacy_gold_reference_result["gold_style_score"] > 50, legacy_gold_reference_result
    assert long_flow_result["ok"], long_flow_result
    assert long_flow_result["severe_items"] == 0, long_flow_result
    density = long_flow_result["components"]["density"]
    assert density["long_flow_density_accepted"], density
    assert density["accepted_dense_steps"], density
    enemy_identity_issues = [issue for issue in identity_result["issues"] if issue["dimension"] == "enemy_identity"]
    assert not [issue for issue in enemy_identity_issues if issue["severity"] == "severe"], enemy_identity_issues
    phase_u_profile = phase_u_result["components"]["annotation_contract"]
    phase_v_profile = phase_u_result["components"]["mechanic_semantics"]
    assert phase_u_result["ok"], phase_u_result
    assert phase_u_profile["ok"], phase_u_profile
    assert 10 <= phase_u_profile["steps"] <= 14, phase_u_profile
    assert phase_u_profile["text_chars"] >= 900 or phase_u_profile["text_objects"] >= 140, phase_u_profile
    assert phase_v_profile["ok"], phase_v_profile
    assert phase_v_profile["range_semantics_score"] == 100.0, phase_v_profile
    assert phase_v_profile["arrow_semantics_score"] == 100.0, phase_v_profile
    assert phase_v_profile["declared_endpoint_snaps"] == phase_v_profile["arrows"], phase_v_profile
    assert {"baitTrail", "bossHitbox", "chargeLine", "fan120", "safeSector", "shareFan90", "towerResolve"} <= set(phase_v_profile["pattern_kinds"]), phase_v_profile
    assert not phase_v_bad_result["ok"], phase_v_bad_result
    phase_v_bad_kinds = {issue["kind"] for issue in phase_v_bad_result["issues"] if issue["severity"] == "severe"}
    assert {"arrow_missing_route_semantics", "arrow_semantics_incomplete"} <= phase_v_bad_kinds, phase_v_bad_kinds
    direct_cones = [obj for obj in phase_v_builder_scene["steps"][0]["objects"] if obj.get("damagePatternKind") == "fan120"]
    direct_arrows = [obj for obj in phase_v_builder_scene["steps"][0]["objects"] if obj.get("movementRoute")]
    assert len(direct_cones) == 3, direct_cones
    assert len(direct_arrows) == 1, direct_arrows
    assert direct_arrows[0]["fromObject"] == "direct-origin", direct_arrows[0]
    assert direct_arrows[0]["toZone"] == "direct-destination", direct_arrows[0]
    phase_x_profile = phase_x_result["components"]["status_assignment"]
    assert phase_x_result["ok"], phase_x_result
    assert phase_x_profile["status_assignment_score"] == 100.0, phase_x_profile
    assert phase_x_profile["visible_expected"] == 32, phase_x_profile
    assert phase_x_profile["visible_overlays"] == 32, phase_x_profile
    assert not phase_x_bad_result["ok"], phase_x_bad_result
    phase_x_bad_kinds = {issue["kind"] for issue in phase_x_bad_result["issues"] if issue["severity"] == "severe"}
    assert "status_overlay_missing" in phase_x_bad_kinds, phase_x_bad_kinds
    print("OK: visual quality audit covers severe failures, label/title avoidance, movement flow, semantic long-flow density, enemy identity, party identity, guide-section icon policy, gold reference mode, Phase U annotations, Phase V route/range hard gates, and Phase X status assignment overlays")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
