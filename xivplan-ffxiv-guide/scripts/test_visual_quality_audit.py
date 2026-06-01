#!/usr/bin/env python3
"""Regression checks for the Phase G visual quality audit."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from audit_visual_quality import audit_scene
from build_xivplan_scene import DEFAULT_PARTY_JOBS, FALLBACK_ENEMY_ICON_DATA_URLS, build_scene
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


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        good = tmp_path / "good.xivplan"
        bad = tmp_path / "bad.xivplan"
        label_collision = tmp_path / "label-collision.xivplan"
        movement_without_arrow = tmp_path / "movement-without-arrow.xivplan"
        party_identity_bad = tmp_path / "party-identity-bad.xivplan"
        semantic_long_flow = tmp_path / "semantic-long-flow.xivplan"
        enemy_identity = tmp_path / "enemy-identity.xivplan"
        write_json(good, good_scene())
        write_json(bad, bad_scene())
        write_json(label_collision, label_collision_scene())
        write_json(movement_without_arrow, movement_without_arrow_scene())
        write_json(party_identity_bad, party_identity_bad_scene())
        write_json(semantic_long_flow, build_scene(build_semantic_long_flow_spec()))
        identity_scene = build_scene(enemy_identity_spec())
        identity_errors, _counts, _objects = validate_scene(identity_scene)
        assert not identity_errors, identity_errors[:5]
        write_json(enemy_identity, identity_scene)
        good_result = audit_scene(good)
        bad_result = audit_scene(bad)
        label_result = audit_scene(label_collision)
        movement_result = audit_scene(movement_without_arrow)
        party_identity_result = audit_scene(party_identity_bad)
        long_flow_result = audit_scene(semantic_long_flow)
        identity_result = audit_scene(enemy_identity)
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
    assert long_flow_result["ok"], long_flow_result
    assert long_flow_result["severe_items"] == 0, long_flow_result
    density = long_flow_result["components"]["density"]
    assert density["long_flow_density_accepted"], density
    assert density["accepted_dense_steps"], density
    enemy_identity_issues = [issue for issue in identity_result["issues"] if issue["dimension"] == "enemy_identity"]
    assert not [issue for issue in enemy_identity_issues if issue["severity"] == "severe"], enemy_identity_issues
    print("OK: visual quality audit covers severe failures, label/title avoidance, movement flow, semantic long-flow density, enemy identity, and party identity")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
