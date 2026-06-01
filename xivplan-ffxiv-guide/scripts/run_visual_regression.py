#!/usr/bin/env python3
"""Run Phase I visual regression fixtures through the guide pipeline."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from assemble_guide import assemble_guide
from build_xivplan_scene import DEFAULT_PARTY_JOBS, build_scene
from export_xivplan_steps import export_steps
from inject_enemy_assets import inject_enemy_assets
from run_quality_gate import aggregate, case_result, render_markdown
from validate_xivplan_scene import validate_scene


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "xivplan-ffxiv-guide"
DEFAULT_FIXTURES = SKILL_DIR / "assets" / "visual-regression-fixtures"
DEFAULT_OUTPUT = ROOT / "artifacts" / "phase-i-visual-regression"

FIXTURE_META = {
    "fru-p1-thunder-fire-swords-like": {
        "encounter": "FRU P1 Visual Regression",
        "phase": "P1",
        "version": "phase-i-long-flow",
        "semantic_long_flow": True,
        "custom_builder": "semantic_long_flow",
    },
    "tankbuster-tower-like": {
        "encounter": "Tankbuster Tower Visual Regression",
        "phase": "P1",
        "version": "phase-i",
    },
    "light-rampant-like": {
        "encounter": "Light Rampant Visual Regression",
        "phase": "P1",
        "version": "phase-i",
    },
    "limit-cut-dance": {
        "encounter": "Limit Cut Dance Visual Regression",
        "phase": "P1",
        "version": "phase-i",
    },
    "tile-arena-transition": {
        "encounter": "Tile Arena Visual Regression",
        "phase": "P1",
        "version": "phase-i",
    },
    "long-teaching-storyboard": {
        "encounter": "Phase O Teaching Storyboard Regression",
        "phase": "P1",
        "version": "phase-o",
        "custom_builder": "semantic_long_flow",
        "semantic_long_flow": True,
    },
    "multi-boss-add-identity": {
        "encounter": "Phase P Enemy Identity Regression",
        "phase": "P1",
        "version": "phase-p",
        "custom_builder": "enemy_identity",
    },
    "known-encounter-boss-asset": {
        "encounter": "Phase S Known Boss Asset Regression",
        "phase": "P1",
        "version": "phase-s",
        "custom_builder": "known_enemy_asset",
    },
    "job-specific-positioning": {
        "encounter": "Phase S Job Identity Regression",
        "phase": "P1",
        "version": "phase-s",
        "custom_builder": "party_job_identity",
    },
    "party-stack-label-omission": {
        "encounter": "Phase S Party Stack Identity Regression",
        "phase": "P1",
        "version": "phase-s",
        "custom_builder": "party_stack_identity",
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copytree_clean(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    if source.exists():
        shutil.copytree(source, target)


def sync_case_surface(case_dir: Path) -> None:
    shutil.copy2(case_dir / "generated-specs" / "spec.json", case_dir / "spec.json")
    shutil.copy2(case_dir / "generated-xivplan" / "scene.xivplan", case_dir / "scene.xivplan")
    shutil.copy2(case_dir / "generated-xivplan" / "manifest.json", case_dir / "manifest.json")
    copytree_clean(case_dir / "generated-xivplan" / "images", case_dir / "images")


ROLES = ("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4")
DEFAULT_POSITIONS = {
    "MT": [0, 112],
    "ST": [0, -112],
    "H1": [-112, 0],
    "H2": [112, 0],
    "D1": [-96, 96],
    "D2": [96, 96],
    "D3": [-96, -96],
    "D4": [96, -96],
}
WEST_SAFE_POSITIONS = {
    "MT": [-75, 140],
    "ST": [-75, -140],
    "H1": [-172, 48],
    "H2": [-22, 48],
    "D1": [-172, 142],
    "D2": [-22, 142],
    "D3": [-172, -142],
    "D4": [-22, -142],
}
EAST_SAFE_POSITIONS = {role: [-value[0], value[1]] for role, value in WEST_SAFE_POSITIONS.items()}
NEAR_FAR_POSITIONS = {
    "MT": [-52, 92],
    "ST": [52, -92],
    "H1": [-142, 8],
    "H2": [142, -8],
    "D1": [-196, 152],
    "D2": [196, 152],
    "D3": [-196, -152],
    "D4": [196, -152],
}
TANK_OUT_POSITIONS = {
    **DEFAULT_POSITIONS,
    "MT": [0, 228],
    "ST": [0, -228],
}
RESET_POSITIONS = {role: [round(x * 0.78, 2), round(y * 0.78, 2)] for role, (x, y) in DEFAULT_POSITIONS.items()}
THUNDER_ROLES = {"MT", "H1", "D2", "D3"}
FIRE_ROLES = set(ROLES) - THUNDER_ROLES


def party_objects(positions: dict[str, list[float]]) -> list[dict[str, Any]]:
    return [{"kind": "party", "key": role, "role": role, "pos": positions[role]} for role in ROLES]


def text_obj(key: str, text: str, pos: list[float], size: int = 16) -> dict[str, Any]:
    if pos[1] <= -220:
        pos = [pos[0], -302]
    elif pos[1] >= 220:
        pos = [pos[0], 302]
    return {"kind": "text", "key": key, "text": text, "pos": pos, "fontSize": size}


def sword_tell_pips(prefix: str, step_index: int, count: int = 16) -> list[dict[str, Any]]:
    colors = ("#d13438", "#ffb900", "#2aa7ff", "#8764b8")
    objects = []
    for index in range(count):
        angle = (2 * math.pi * index / count) + (step_index * 0.055)
        radius = 214 + (index % 2) * 28
        objects.append(
            {
                "kind": "circle",
                "key": f"{prefix}-sword-tell-{index}",
                "pos": [round(math.cos(angle) * radius, 2), round(math.sin(angle) * radius, 2)],
                "radius": 7 + (index % 3) * 2,
                "color": colors[(index + step_index) % len(colors)],
                "opacity": 22,
            }
        )
    return objects


def role_halos(prefix: str, positions: dict[str, list[float]]) -> list[dict[str, Any]]:
    objects = []
    for role in ROLES:
        objects.append(
            {
                "kind": "circle",
                "key": f"{prefix}-halo-{role.lower()}",
                "pos": positions[role],
                "radius": 25 if role in THUNDER_ROLES else 21,
                "color": "#2aa7ff" if role in THUNDER_ROLES else "#ff8c00",
                "opacity": 30,
                "hollow": False,
            }
        )
    return objects


def clone_pair(prefix: str, east_label: str = "E clone", west_label: str = "W clone") -> list[dict[str, Any]]:
    return [
        {"kind": "clone", "key": f"{prefix}-east-clone", "name": east_label, "pos": "E", "distance": 205, "radius": 24, "opacity": 78},
        {"kind": "clone", "key": f"{prefix}-west-clone", "name": west_label, "pos": "W", "distance": 205, "radius": 24, "opacity": 78},
    ]


def half_field(prefix: str, safe_side: str) -> list[dict[str, Any]]:
    safe_x = -150 if safe_side == "W" else 150
    danger_x = -safe_x
    return [
        {"kind": "rect", "key": f"{prefix}-safe-half", "pos": [safe_x, 0], "width": 290, "height": 540, "color": "#8fd14f", "opacity": 18},
        {"kind": "rect", "key": f"{prefix}-danger-half", "pos": [danger_x, 0], "width": 290, "height": 540, "color": "#d13438", "opacity": 22},
    ]


def blade_lanes(prefix: str, safe_side: str) -> list[dict[str, Any]]:
    lane_x = -88 if safe_side == "W" else 88
    color = "#d13438" if safe_side == "W" else "#2aa7ff"
    objects = []
    for index, y in enumerate((-210, -140, -70, 70, 140, 210)):
        objects.append(
            {
                "kind": "rect",
                "key": f"{prefix}-lane-{index}",
                "pos": [lane_x, y],
                "width": 220,
                "height": 18,
                "rotation": 10 if index % 2 else -10,
                "color": color,
                "opacity": 20,
            }
        )
    return objects


def center_context(prefix: str) -> list[dict[str, Any]]:
    return [
        {"kind": "circle", "key": f"{prefix}-boss-ring", "pos": "center", "radius": 72, "color": "#d13438", "opacity": 20},
        {"kind": "circle", "key": f"{prefix}-inner-safe", "pos": "center", "radius": 132, "color": "#8fd14f", "opacity": 13},
        {"kind": "donut", "key": f"{prefix}-outer-read-ring", "pos": "center", "radius": 246, "innerRadius": 206, "color": "#ffb900", "opacity": 16},
    ]


def movement_arrows(prefix: str, routes: list[tuple[list[float], list[list[float]], list[float], str]]) -> list[dict[str, Any]]:
    objects = []
    for index, (start, waypoints, end, style) in enumerate(routes):
        obj: dict[str, Any] = {
            "kind": "polyline" if waypoints else "arrow",
            "key": f"{prefix}-route-{index}",
            "from": start,
            "to": end,
            "arrowStyle": style,
            "endGap": 62,
            "allowDangerCrossing": True,
        }
        if waypoints:
            obj["waypoints"] = waypoints
        objects.append(obj)
    return objects


def long_flow_step(
    index: int,
    title: str,
    phase: str,
    purpose: str,
    guide_text: str,
    positions: dict[str, list[float]],
    objects: list[dict[str, Any]],
    *,
    focus_roles: list[str] | None = None,
    movement_required: bool = False,
    flow_kind: str | None = None,
    reset_state: str = "Maintain context for the next read.",
    teaching_question: str | None = None,
    changed_objects_only: str | None = None,
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "title": f"{index} {title}",
        "storyboard_phase": phase,
        "movement_required": movement_required,
        "teaching_question": teaching_question or f"{purpose.rstrip('.')}?",
        "why_this_frame_exists": purpose,
        "changed_objects_only": changed_objects_only or purpose,
        "purpose": purpose,
        "guide_text": guide_text,
        "checks": ["full party visible", "boss anchor visible", "mechanic layer visible"],
        "visual_focus": purpose,
        "required_roles": list(ROLES),
        "reset_state": reset_state,
        "objects": party_objects(positions) + sword_tell_pips(f"lf{index}", index) + role_halos(f"lf{index}", positions) + center_context(f"lf{index}") + objects,
    }
    if focus_roles:
        step["focusRoles"] = focus_roles
    if flow_kind:
        step["flow_kind"] = flow_kind
    return step


def build_semantic_long_flow_spec() -> dict[str, Any]:
    steps = [
        long_flow_step(
            1,
            "Start clocks",
            "observe",
            "Show stable eight-player clocks before FRU-style reads begin.",
            "Begin from fixed clocks; keep boss, waymarks, and edge sword tells visible.",
            DEFAULT_POSITIONS,
            clone_pair("lf1") + [text_obj("lf1-call", "Start clocks", [0, -222])],
        ),
        long_flow_step(
            2,
            "East west read",
            "observe",
            "Compare east and west clone tells before choosing the first safe half.",
            "Read both side clones first; do not move until the safe half is decided.",
            DEFAULT_POSITIONS,
            clone_pair("lf2", "Fire side", "Thunder side") + half_field("lf2", "W") + blade_lanes("lf2", "W") + [text_obj("lf2-call", "W safe", [-174, -222])],
        ),
        long_flow_step(
            3,
            "Debuff split",
            "observe",
            "Separate thunder and fire responsibilities without moving the party yet.",
            "Blue rings track thunder roles; orange rings track fire roles for later swaps.",
            DEFAULT_POSITIONS,
            clone_pair("lf3") + [
                {"kind": "stack", "key": "lf3-fire-stack", "pos": "E", "distance": 108, "radius": 54, "count": 4, "color": "#ff8c00", "opacity": 44},
                {"kind": "tower", "key": "lf3-thunder-tower", "pos": "W", "distance": 108, "radius": 48, "count": 4, "color": "#2aa7ff", "opacity": 54},
                text_obj("lf3-call", "Thunder / fire", [0, -222]),
            ],
        ),
        long_flow_step(
            4,
            "First half move",
            "move",
            "Move the raid into the first safe half while preserving role lanes.",
            "Group shifts west through two lanes; arrows show the actual safe-half move.",
            WEST_SAFE_POSITIONS,
            half_field("lf4", "W")
            + blade_lanes("lf4", "W")
            + movement_arrows(
                "lf4",
                [
                    ([85, 70], [[20, 76]], [-164, 76], "movement"),
                    ([85, -70], [[20, -76]], [-164, -76], "movement"),
                    ([0, 0], [[-56, 0]], [-132, 0], "preposition"),
                ],
            )
            + [text_obj("lf4-call", "Move W", [-176, 222])],
            movement_required=True,
            flow_kind="movement",
            reset_state="Hold west lanes for the first hit.",
        ),
        long_flow_step(
            5,
            "Near far set",
            "preposition",
            "Refine near and far lanes before the first thunder/fire resolution.",
            "Near players step inside; far players stay on the outer lane for spacing.",
            NEAR_FAR_POSITIONS,
            half_field("lf5", "W")
            + [
                {"kind": "circle", "key": "lf5-near", "pos": "center", "radius": 112, "color": "#8fd14f", "opacity": 20},
                {"kind": "donut", "key": "lf5-far", "pos": "center", "radius": 234, "innerRadius": 174, "color": "#2aa7ff", "opacity": 18},
                text_obj("lf5-call", "Near / far", [0, -222]),
            ],
        ),
        long_flow_step(
            6,
            "First resolve",
            "resolve",
            "Resolve the first safe-half and debuff set in one readable frame.",
            "Resolve west-side safe half; keep near/far lanes and debuff colors visible.",
            NEAR_FAR_POSITIONS,
            half_field("lf6", "W")
            + blade_lanes("lf6", "W")
            + [
                {"kind": "cone", "key": "lf6-east-cleave", "pos": "E", "distance": 90, "radius": 220, "coneAngle": 58, "rotation": 180, "color": "#d13438", "opacity": 24},
                {"kind": "stack", "key": "lf6-fire-stack", "pos": "SW", "distance": 132, "radius": 48, "count": 4, "color": "#ff8c00", "opacity": 48},
                {"kind": "tower", "key": "lf6-thunder-tower", "pos": "NW", "distance": 132, "radius": 42, "count": 4, "color": "#2aa7ff", "opacity": 58},
                text_obj("lf6-call", "1st hit", [-172, -222]),
            ],
        ),
        long_flow_step(
            7,
            "Tankbusters out",
            "move",
            "Pull tank hits outside while the party keeps the safe-half context.",
            "Tanks leave north and south; non-tanks stay readable in the west half.",
            TANK_OUT_POSITIONS,
            half_field("lf7", "W")
            + [
                {"kind": "line_stack", "key": "lf7-mt-buster", "pos": "N", "distance": 158, "width": 58, "height": 270, "rotation": 0, "color": "#d13438", "opacity": 32},
                {"kind": "line_stack", "key": "lf7-st-buster", "pos": "S", "distance": 158, "width": 58, "height": 270, "rotation": 180, "color": "#d13438", "opacity": 32},
            ]
            + movement_arrows("lf7", [([0, 112], [], [0, 218], "bait"), ([0, -112], [], [0, -218], "bait")])
            + [text_obj("lf7-call", "Tanks out", [216, 222])],
            focus_roles=["MT", "ST"],
            movement_required=True,
            flow_kind="bait",
            reset_state="Tanks resolve outside, party holds west lanes.",
        ),
        long_flow_step(
            8,
            "Second side read",
            "observe",
            "Show the second clone read and make the side swap explicit.",
            "Second read flips the safe side; prepare to cross through the clean lanes.",
            WEST_SAFE_POSITIONS,
            clone_pair("lf8", "Thunder side", "Fire side") + half_field("lf8", "E") + blade_lanes("lf8", "E") + [text_obj("lf8-call", "Now E safe", [172, -222])],
        ),
        long_flow_step(
            9,
            "Swap route",
            "move",
            "Route the party from west lanes into the second safe half.",
            "Move around the boss, not through the center; the two group arrows avoid crossing.",
            EAST_SAFE_POSITIONS,
            half_field("lf9", "E")
            + blade_lanes("lf9", "E")
            + movement_arrows(
                "lf9",
                [
                    ([-162, 132], [[-90, 202], [80, 202]], [162, 132], "movement"),
                    ([-162, -132], [[-90, -202], [80, -202]], [162, -132], "movement"),
                    ([-42, 40], [[20, 82]], [92, 86], "micro"),
                ],
            )
            + [text_obj("lf9-call", "Swap E", [174, 222])],
            movement_required=True,
            flow_kind="movement",
            reset_state="Arrive east before the second hit.",
        ),
        long_flow_step(
            10,
            "Second resolve",
            "resolve",
            "Resolve the mirrored thunder/fire set after the side swap.",
            "Resolve east-side safe half; mirrored colors confirm the second order.",
            EAST_SAFE_POSITIONS,
            half_field("lf10", "E")
            + blade_lanes("lf10", "E")
            + [
                {"kind": "cone", "key": "lf10-west-cleave", "pos": "W", "distance": 90, "radius": 220, "coneAngle": 58, "rotation": 0, "color": "#d13438", "opacity": 24},
                {"kind": "stack", "key": "lf10-fire-stack", "pos": "SE", "distance": 132, "radius": 48, "count": 4, "color": "#ff8c00", "opacity": 48},
                {"kind": "tower", "key": "lf10-thunder-tower", "pos": "NE", "distance": 132, "radius": 42, "count": 4, "color": "#2aa7ff", "opacity": 58},
                text_obj("lf10-call", "2nd hit", [172, -222]),
            ],
        ),
        long_flow_step(
            11,
            "Reset center",
            "reset",
            "Return to a compact center setup after both thunder/fire hits.",
            "After the second hit, collapse toward center while preserving clock order.",
            RESET_POSITIONS,
            [
                {"kind": "stack", "key": "lf11-reset-stack", "pos": "center", "radius": 76, "count": 8, "color": "#8fd14f", "opacity": 40},
                {"kind": "circle", "key": "lf11-reset-ring", "pos": "center", "radius": 152, "color": "#8fd14f", "opacity": 14},
            ]
            + movement_arrows("lf11", [([176, 132], [[116, 82]], [-20, 36], "reset"), ([176, -132], [[116, -82]], [-20, -36], "reset")])
            + [text_obj("lf11-call", "Reset", [0, -222])],
            movement_required=True,
            flow_kind="reset",
            reset_state="Center reset complete.",
        ),
        long_flow_step(
            12,
            "Next cast ready",
            "reset",
            "Reopen into normal clocks so the next cast starts from a known state.",
            "Spread back to clocks, boss recenters, and the next read can reuse the same grammar.",
            DEFAULT_POSITIONS,
            clone_pair("lf12")
            + [
                {"kind": "circle", "key": "lf12-ready-ring", "pos": "center", "radius": 172, "color": "#8fd14f", "opacity": 16},
                {"kind": "donut", "key": "lf12-next-read", "pos": "center", "radius": 250, "innerRadius": 210, "color": "#ffb900", "opacity": 14},
            ]
            + movement_arrows("lf12", [([74, 72], [[40, 112]], [-110, 112], "reset"), ([74, -72], [[40, -112]], [-110, -112], "reset")])
            + [text_obj("lf12-call", "Next read", [0, -222])],
            movement_required=True,
            flow_kind="reset",
            reset_state="Ready for the next mechanic read.",
            teaching_question="How does the party reopen into clocks for the next cast?",
            changed_objects_only="Party spreads back to clocks and the next-read ring appears.",
        ),
        long_flow_step(
            13,
            "Next tell appears",
            "observe",
            "Show the next tell without moving so the long flow ends on a readable handoff.",
            "Hold clocks and read the next clone/tell pair before anyone pre-moves.",
            DEFAULT_POSITIONS,
            clone_pair("lf13", "Next fire", "Next thunder")
            + [
                {"kind": "donut", "key": "lf13-next-ring", "pos": "center", "radius": 250, "innerRadius": 214, "color": "#ffb900", "opacity": 15},
                {"kind": "circle", "key": "lf13-read-anchor", "pos": "center", "radius": 96, "color": "#2aa7ff", "opacity": 18},
                text_obj("lf13-call", "Read next", [0, -222]),
            ],
            teaching_question="What should the party read before the next movement?",
            changed_objects_only="Next clone/tell pair and read anchor.",
        ),
        long_flow_step(
            14,
            "Handoff frame",
            "reset",
            "Confirm the stable state and stop before the next mechanic's first movement.",
            "This is the handoff frame: clocks are restored, boss is centered, and the next read is isolated.",
            DEFAULT_POSITIONS,
            clone_pair("lf14")
            + [
                {"kind": "circle", "key": "lf14-handoff-safe", "pos": "center", "radius": 146, "color": "#8fd14f", "opacity": 16},
                {"kind": "stack", "key": "lf14-soft-center", "pos": "center", "radius": 58, "count": 8, "color": "#8fd14f", "opacity": 32},
                text_obj("lf14-call", "Handoff", [0, 180]),
            ],
            teaching_question="Where does this storyboard hand off to the next mechanic?",
            changed_objects_only="Stable handoff ring and final context confirmation.",
        ),
    ]
    return {
        "name": "FRU P1 semantic thunder/fire swords long-flow fixture",
        "style": "king-x-fru",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": {"preset": "fru-p1", "source": "fixture-semantic", "sourceReason": "Phase L semantic long-flow regression fixture."},
        "markerPresets": "cardinals",
        "metadata": {
            "source": "run_visual_regression.py",
            "storyboard_generator": "phase-l-semantic-long-flow",
            "storyboard_policy": "semantic-fru-p1-thunder-fire-sequence",
            "phase_o_teaching_questions": True,
            "density_policy": "semantic sword tells, debuff halos, safe-half fields, clone reads, and movement routes",
        },
        "steps": steps,
    }


def write_semantic_long_flow(case_dir: Path) -> dict[str, Any]:
    spec = build_semantic_long_flow_spec()
    scene = build_scene(spec)
    errors, _, object_count = validate_scene(scene)
    if errors:
        raise RuntimeError(f"semantic long-flow scene invalid: {errors}")

    spec_paths = (case_dir / "spec.json", case_dir / "generated-specs" / "spec.json")
    scene_paths = (case_dir / "scene.xivplan", case_dir / "generated-xivplan" / "scene.xivplan")
    for path in spec_paths:
        write_json(path, spec)
    for path in scene_paths:
        write_json(path, scene)

    if (case_dir / "images").exists():
        shutil.rmtree(case_dir / "images")
    manifest = export_steps(case_dir / "scene.xivplan", case_dir, scale_factor=1)
    write_json(case_dir / "manifest.json", manifest)
    write_json(case_dir / "generated-xivplan" / "manifest.json", manifest)
    copytree_clean(case_dir / "images", case_dir / "generated-xivplan" / "images")

    guide = {
        "title": "FRU P1 semantic visual regression long flow",
        "summary": "Phase O keeps the semantic long-flow readable while requiring 14 teaching-focused frames.",
        "recommended_solution": "Read side clones, split thunder/fire roles, resolve west, pull tanks out, swap east, resolve again, then reset.",
        "scene": "scene.xivplan",
        "spec": "spec.json",
        "figures": [
            {
                "step": item["step"],
                "title": scene["steps"][item["step"] - 1]["title"],
                "image": item["image"],
                "caption": f"Figure {item['step']}: {scene['steps'][item['step'] - 1]['title']}",
                "guide_text": scene["steps"][item["step"] - 1]["guide_text"],
            }
            for item in manifest["steps"]
        ],
        "flow": [step["guide_text"] for step in scene["steps"]],
        "role_assignments": [
            {"role": "MT/ST", "position": "tank out lanes", "task": "pull busters north and south, then reset"},
            {"role": "H1/H2", "position": "west/east anchors", "task": "hold party anchors through side swaps"},
            {"role": "D1-D4", "position": "intercard lanes", "task": "track thunder/fire color and near/far spacing"},
        ],
        "common_mistakes": ["Moving before the side read", "Crossing through center on the side swap", "Forgetting tank out before the second read"],
        "short_callout": ["clocks", "west safe", "near/far", "tanks out", "swap east", "reset"],
        "mnemonic": "Read side, color split, resolve, tank out, swap, resolve, reset.",
        "consistency_checks": ["14 semantic teaching steps", "500+ objects", "full context in every normal frame"],
        "unknowns": [],
    }
    guide_path = case_dir / "guide.json"
    write_json(guide_path, guide)
    assemble_guide(guide_path, case_dir / "guide-package", strict_images=True)
    return {"steps": len(scene["steps"]), "objects": object_count, "mode": "semantic-storyboard"}


def build_enemy_identity_spec() -> dict[str, Any]:
    base_enemies = [
        {"kind": "boss", "key": "main-boss", "name": "Main Boss", "pos": "center", "radius": 44, "facing": 180, "labelPlacement": "fixed", "labelPos": [238, -110]},
        {"kind": "add", "key": "orb-east", "name": "Orb", "pos": "E", "distance": 188, "radius": 26, "facing": 270, "labelPlacement": "fixed", "labelPos": [248, 158]},
        {"kind": "add", "key": "orb-west", "name": "Orb", "pos": "W", "distance": 188, "radius": 26, "facing": 90, "labelPlacement": "fixed", "labelPos": [-248, 158]},
        {"kind": "clone", "key": "north-clone", "name": "Mirror Clone", "pos": "N", "distance": 202, "radius": 28, "facing": 180, "labelPlacement": "fixed", "labelPos": [-178, 258]},
    ]

    def p_step(index: int, title: str, phase: str, question: str, objects: list[dict[str, Any]], guide_text: str) -> dict[str, Any]:
        return {
            "title": f"{index} {title}",
            "storyboard_phase": phase,
            "teaching_question": question,
            "why_this_frame_exists": question,
            "changed_objects_only": title,
            "purpose": question,
            "guide_text": guide_text,
            "checks": ["enemy names visible", "target rings visible", "duplicate adds distinguishable"],
            "visual_focus": title,
            "required_roles": list(ROLES),
            "reset_state": "Keep all enemy anchors visible for identity validation.",
            "objects": base_enemies + objects,
        }

    return {
        "name": "Phase P enemy identity regression fixture",
        "style": "king-x-fru",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": {"preset": "default-circle", "source": "fixture-phase-p", "sourceReason": "Multi enemy identity regression fixture."},
        "markerPresets": "cardinals",
        "metadata": {
            "source": "run_visual_regression.py",
            "storyboard_generator": "phase-o-v3",
            "storyboard_policy": "phase-p-enemy-identity-contract",
        },
        "steps": [
            p_step(
                1,
                "Enemy roster",
                "observe_signal",
                "Which Boss, clone, and adds must be distinguished first?",
                [{"kind": "circle", "key": "identity-read", "pos": "center", "radius": 118, "color": "#ffb900", "opacity": 16, "label": "读敌人", "labelPlacement": "fixed", "labelPos": [0, -210], "leaderLine": False}],
                "先读 Main Boss、Mirror Clone 和两只 Orb；同名 Orb 必须带方向后缀。",
            ),
            p_step(
                2,
                "Role assignment",
                "assign_roles",
                "Which side add belongs to which half party?",
                [
                    {"kind": "circle", "key": "east-add-zone", "pos": "E", "distance": 188, "radius": 54, "color": "#2aa7ff", "opacity": 18, "label": "东 add"},
                    {"kind": "circle", "key": "west-add-zone", "pos": "W", "distance": 188, "radius": 54, "color": "#ff8c00", "opacity": 18, "label": "西 add"},
                ],
                "东半队读 Orb E，西半队读 Orb W；Boss 和北分身仍保留目标环。",
            ),
            p_step(
                3,
                "Add movement",
                "first_move",
                "Where do tanks drag the named adds?",
                [
                    {"kind": "arrow", "key": "east-add-route", "from": "E", "to": "NE", "distance": 188, "arrowStyle": "bait", "endGap": 48},
                    {"kind": "arrow", "key": "west-add-route", "from": "W", "to": "NW", "distance": 188, "arrowStyle": "bait", "endGap": 48},
                ],
                "坦克把两只 Orb 分别拉向东北和西北；名字必须能区分方向。",
            ),
            p_step(
                4,
                "First resolve",
                "first_resolve",
                "Which named enemy resolves each AoE?",
                [
                    {"kind": "cone", "key": "boss-cleave", "pos": "center", "radius": 210, "coneAngle": 70, "rotation": 180, "color": "#d13438", "opacity": 22},
                    {"kind": "circle", "key": "east-add-hit", "pos": "NE", "distance": 188, "radius": 52, "color": "#d13438", "opacity": 20},
                    {"kind": "circle", "key": "west-add-hit", "pos": "NW", "distance": 188, "radius": 52, "color": "#d13438", "opacity": 20},
                ],
                "Boss 顺劈和两只 Orb 的爆炸分开判定，所有敌人名字仍可读。",
            ),
            p_step(
                5,
                "Between resolves",
                "observe_signal",
                "What stays visible while the party waits for the second hit?",
                [
                    {"kind": "donut", "key": "between-ring", "pos": "center", "radius": 242, "innerRadius": 174, "color": "#ffb900", "opacity": 14},
                    {"kind": "text", "key": "hold-label", "text": "Hold names", "pos": [0, -210], "fontSize": 14},
                ],
                "中间帧不移动，只确认敌人目标环和名字没有被大范围 AoE 盖住。",
            ),
            p_step(
                6,
                "Reset identity",
                "next_read_setup",
                "Where are the named enemies before the next read?",
                [
                    {"kind": "circle", "key": "reset-center", "pos": "center", "radius": 142, "color": "#8fd14f", "opacity": 14, "label": "下一读条", "labelPlacement": "fixed", "labelPos": [0, -210], "leaderLine": False},
                    {"kind": "arrow", "key": "reset-arrow", "from": [160, -120], "to": [104, -78], "arrowStyle": "reset", "endGap": 34},
                ],
                "复位帧继续保留 Main Boss、Mirror Clone、Orb E 和 Orb W 的身份合同。",
            ),
        ],
    }


def write_enemy_identity_case(case_dir: Path) -> dict[str, Any]:
    spec = build_enemy_identity_spec()
    scene = build_scene(spec)
    errors, _, object_count = validate_scene(scene)
    if errors:
        raise RuntimeError(f"enemy identity scene invalid: {errors}")

    for path in (case_dir / "spec.json", case_dir / "generated-specs" / "spec.json"):
        write_json(path, spec)
    for path in (case_dir / "scene.xivplan", case_dir / "generated-xivplan" / "scene.xivplan"):
        write_json(path, scene)

    if (case_dir / "images").exists():
        shutil.rmtree(case_dir / "images")
    manifest = export_steps(case_dir / "scene.xivplan", case_dir, scale_factor=1)
    write_json(case_dir / "manifest.json", manifest)
    write_json(case_dir / "generated-xivplan" / "manifest.json", manifest)
    copytree_clean(case_dir / "images", case_dir / "generated-xivplan" / "images")

    guide = {
        "title": "Phase P enemy identity regression",
        "summary": "Multi Boss/add fixture for target rings, names, duplicate add suffixes, and readable labels.",
        "recommended_solution": "Read all enemy names first, assign side adds, resolve named AoEs, then reset with identities preserved.",
        "scene": "scene.xivplan",
        "spec": "spec.json",
        "figures": [
            {
                "step": item["step"],
                "title": scene["steps"][item["step"] - 1]["title"],
                "image": item["image"],
                "caption": f"Figure {item['step']}: {scene['steps'][item['step'] - 1]['title']}",
                "guide_text": scene["steps"][item["step"] - 1]["guide_text"],
            }
            for item in manifest["steps"]
        ],
        "flow": [step["guide_text"] for step in scene["steps"]],
        "role_assignments": [
            {"role": "MT/ST", "position": "side adds", "task": "separate Orb E and Orb W"},
            {"role": "H1/H2", "position": "center support", "task": "hold party anchors while enemy identities are read"},
            {"role": "D1-D4", "position": "clock spots", "task": "resolve named AoEs after tanks separate the adds"},
        ],
        "common_mistakes": ["Treating same-name adds as interchangeable", "Covering enemy names with AoE labels"],
        "short_callout": ["read enemies", "split adds", "drag sides", "resolve", "hold names", "reset"],
        "mnemonic": "Name, ring, direction, resolve.",
        "consistency_checks": ["enemy_identity_score available", "duplicate adds distinguished", "target rings visible"],
        "unknowns": [],
    }
    guide_path = case_dir / "guide.json"
    write_json(guide_path, guide)
    assemble_guide(guide_path, case_dir / "guide-package", strict_images=True)
    return {"steps": len(scene["steps"]), "objects": object_count, "mode": "enemy-identity"}


CASTER_ANCHOR_POSITIONS = {
    "MT": [0, 132],
    "ST": [0, -132],
    "H1": [-76, 24],
    "H2": [76, 24],
    "D1": [-144, 116],
    "D2": [144, 116],
    "D3": [-172, -72],
    "D4": [92, -42],
}
JOB_RESOLVE_POSITIONS = {
    "MT": [-38, 142],
    "ST": [38, -142],
    "H1": [-126, 34],
    "H2": [126, 34],
    "D1": [-204, 146],
    "D2": [204, 146],
    "D3": [-204, -136],
    "D4": [128, -86],
}
STACK_CLUSTER_POSITIONS = {
    "MT": [0, 34],
    "ST": [0, -34],
    "H1": [-34, 0],
    "H2": [34, 0],
    "D1": [-24, 24],
    "D2": [24, 24],
    "D3": [-24, -24],
    "D4": [24, -24],
}
SPREAD_AFTER_STACK_POSITIONS = {
    "MT": [0, 118],
    "ST": [0, -118],
    "H1": [-118, 0],
    "H2": [118, 0],
    "D1": [-94, 94],
    "D2": [94, 94],
    "D3": [-94, -94],
    "D4": [94, -94],
}


def phase_s_step(
    index: int,
    title: str,
    phase: str,
    question: str,
    guide_text: str,
    objects: list[dict[str, Any]],
    *,
    movement_required: bool = False,
    flow_kind: str | None = None,
    party_cluster: bool = False,
    stack_group: bool = False,
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "title": f"{index} {title}",
        "storyboard_phase": phase,
        "teaching_question": question,
        "why_this_frame_exists": question,
        "changed_objects_only": title,
        "purpose": question,
        "guide_text": guide_text,
        "checks": ["full party identity visible", "enemy identity visible", "waymarks stable"],
        "visual_focus": title,
        "required_roles": list(ROLES),
        "reset_state": "Keep role/job identity through the next frame.",
        "movement_required": movement_required,
        "objects": objects,
    }
    if flow_kind:
        step["flow_kind"] = flow_kind
    if party_cluster:
        step["party_cluster"] = True
    if stack_group:
        step["stack_group"] = True
    return step


def role_assignments() -> list[dict[str, str]]:
    return [
        {"role": "MT/ST", "position": "tank anchors", "task": "keep boss/add positioning stable"},
        {"role": "H1/H2", "position": "healer anchors", "task": "hold recovery lanes and stack timing"},
        {"role": "D1-D4", "position": "DPS lanes", "task": "resolve spread, stack, and reset calls by role"},
    ]


def phase_s_arrows(prefix: str, routes: list[tuple[list[float], list[list[float]], list[float], str]]) -> list[dict[str, Any]]:
    arrows = movement_arrows(prefix, routes)
    for arrow in arrows:
        arrow["arrowEnd"] = False
        arrow["endGap"] = max(int(arrow.get("endGap", 0)), 82)
    return arrows


def write_job_identity_report(scene: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    expected_jobs = {role: values["job"] for role, values in DEFAULT_PARTY_JOBS.items()}
    expected_icons = {role: values["icon"] for role, values in DEFAULT_PARTY_JOBS.items()}
    steps: list[dict[str, Any]] = []
    ok = True
    for step_index, step in enumerate(scene.get("steps", []), start=1):
        party = [obj for obj in step.get("objects", []) if isinstance(obj, dict) and obj.get("type") == "party"]
        rows = []
        for obj in sorted(party, key=lambda item: ROLES.index(item.get("role")) if item.get("role") in ROLES else 99):
            role = str(obj.get("role", ""))
            row = {
                "role": role,
                "job": obj.get("job"),
                "jobName": obj.get("jobName"),
                "icon": obj.get("icon"),
                "roleLabel": obj.get("roleLabel"),
                "roleLabelVisible": obj.get("roleLabelVisible", True),
                "iconScale": obj.get("iconScale"),
                "width": obj.get("width"),
                "height": obj.get("height"),
            }
            rows.append(row)
            ok = ok and role in expected_jobs and row["job"] == expected_jobs[role] and row["icon"] == expected_icons[role]
            if not step.get("party_cluster") and not step.get("stack_group"):
                ok = ok and bool(row["roleLabel"]) and row["roleLabelVisible"] is not False
        steps.append(
            {
                "step": step_index,
                "title": step.get("title"),
                "party_cluster": bool(step.get("party_cluster") or step.get("stack_group")),
                "roles": rows,
            }
        )

    payload = {"ok": ok, "expected_default_jobs": expected_jobs, "expected_default_icons": expected_icons, "steps": steps}
    write_json(output_dir / "job-identity-report.json", payload)
    lines = [
        "# Job Identity Report",
        "",
        f"- status: {'PASS' if ok else 'FAIL'}",
        "- expected defaults: " + ", ".join(f"{role}={job}" for role, job in expected_jobs.items()),
        "- expected official XivPlan icons: " + ", ".join(f"{role}={icon}" for role, icon in expected_icons.items()),
        "",
        "| Step | Cluster | Roles |",
        "|---:|---|---|",
    ]
    for step in steps:
        roles = ", ".join(
            "{role}={job} @ {icon}{label}".format(
                role=row["role"],
                job=row["job"],
                icon=row["icon"],
                label="" if row["roleLabelVisible"] is not False else " label-hidden",
            )
            for row in step["roles"]
        )
        lines.append(f"| {step['step']} | {step['party_cluster']} | {roles} |")
    (output_dir / "job-identity-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def write_custom_case(case_dir: Path, spec: dict[str, Any], guide: dict[str, Any], mode: str) -> dict[str, Any]:
    scene = build_scene(spec)
    errors, _, object_count = validate_scene(scene)
    if errors:
        raise RuntimeError(f"{mode} scene invalid: {errors}")

    for path in (case_dir / "spec.json", case_dir / "generated-specs" / "spec.json"):
        write_json(path, spec)
    for path in (case_dir / "scene.xivplan", case_dir / "generated-xivplan" / "scene.xivplan"):
        write_json(path, scene)

    if (case_dir / "images").exists():
        shutil.rmtree(case_dir / "images")
    manifest = export_steps(case_dir / "scene.xivplan", case_dir, scale_factor=1)
    write_json(case_dir / "manifest.json", manifest)
    write_json(case_dir / "generated-xivplan" / "manifest.json", manifest)
    copytree_clean(case_dir / "images", case_dir / "generated-xivplan" / "images")
    write_job_identity_report(scene, case_dir)

    full_guide = {
        "title": guide["title"],
        "summary": guide["summary"],
        "recommended_solution": guide["recommended_solution"],
        "scene": "scene.xivplan",
        "spec": "spec.json",
        "figures": [
            {
                "step": item["step"],
                "title": scene["steps"][item["step"] - 1]["title"],
                "image": item["image"],
                "caption": f"Figure {item['step']}: {scene['steps'][item['step'] - 1]['title']}",
                "guide_text": scene["steps"][item["step"] - 1]["guide_text"],
            }
            for item in manifest["steps"]
        ],
        "flow": [step["guide_text"] for step in scene["steps"]],
        "role_assignments": role_assignments(),
        "common_mistakes": guide.get("common_mistakes", []),
        "short_callout": guide.get("short_callout", []),
        "mnemonic": guide.get("mnemonic", ""),
        "consistency_checks": guide.get("consistency_checks", []),
        "unknowns": guide.get("unknowns", []),
    }
    guide_path = case_dir / "guide.json"
    write_json(guide_path, full_guide)
    assemble_guide(guide_path, case_dir / "guide-package", strict_images=True)
    return {"steps": len(scene["steps"]), "objects": object_count, "mode": mode}


def build_known_enemy_asset_spec() -> dict[str, Any]:
    boss = {"kind": "boss", "key": "main-boss", "enemy_id": "main-boss", "name": "Fatebreaker", "pos": "center", "radius": 44, "facing": 180}
    add = {"kind": "add", "key": "orb-east", "enemy_id": "orb-east", "name": "Asset Add", "pos": "E", "distance": 178, "radius": 26, "facing": 270}
    return {
        "name": "Phase S known encounter enemy asset fixture",
        "style": "king-x-fru",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": {"preset": "fru-p1", "source": "fixture-phase-s", "sourceReason": "Known encounter Boss asset and fallback add icon regression."},
        "markerPresets": "cardinals",
        "metadata": {"source": "run_visual_regression.py", "storyboard_generator": "phase-o-v3", "phase_s_fixture": "known-encounter-boss-asset"},
        "steps": [
            phase_s_step(1, "Asset read", "observe_signal", "Which enemy has the dedicated asset?", "Boss uses a copied sample PNG; add keeps fallback icon.", [boss, add, {"kind": "circle", "key": "asset-read", "pos": "center", "radius": 116, "color": "#ffb900", "opacity": 16}]),
            phase_s_step(2, "Assign sides", "assign_roles", "Which roles watch the Boss and add?", "Tanks keep Boss center; east group watches the add fallback icon.", [boss, add, {"kind": "tower", "key": "east-check", "pos": "E", "distance": 128, "radius": 42, "count": 4, "color": "#2aa7ff", "opacity": 52, "label": "east add"}]),
            phase_s_step(3, "Drag add", "first_move", "Where does the add move without losing its icon?", "Add icon remains visible while the route moves it northeast.", [boss, add, {"kind": "arrow", "key": "add-route", "from": [178, 0], "to": [132, 132], "arrowStyle": "bait", "endGap": 82, "arrowEnd": False}], movement_required=True, flow_kind="bait"),
            phase_s_step(4, "Resolve named hits", "first_resolve", "Which named enemies resolve damage?", "Resolve Boss cleave and add burst with both icons still readable.", [boss, add, {"kind": "cone", "key": "boss-cleave", "pos": "center", "radius": 210, "coneAngle": 62, "rotation": 180, "color": "#d13438", "opacity": 24}, {"kind": "circle", "key": "add-burst", "pos": "NE", "distance": 132, "radius": 52, "color": "#d13438", "opacity": 22}]),
            phase_s_step(5, "Reset assets", "reset", "Do enemy icons survive the reset frame?", "Reset to center while retaining dedicated Boss and fallback add icons.", [boss, add, {"kind": "stack", "key": "reset-stack", "pos": "center", "radius": 66, "count": 8, "color": "#8fd14f", "opacity": 40}, {"kind": "arrow", "key": "reset-arrow", "from": [120, 120], "to": [54, 54], "arrowStyle": "reset", "endGap": 82, "arrowEnd": False}], movement_required=True, flow_kind="reset"),
            phase_s_step(6, "Next read", "next_read_setup", "What is ready for the next asset read?", "Boss and add names, target rings, and icons remain visible.", [boss, add, {"kind": "circle", "key": "next-ring", "pos": "center", "radius": 146, "color": "#8fd14f", "opacity": 15}]),
        ],
    }


def write_known_enemy_asset_case(case_dir: Path) -> dict[str, Any]:
    asset_dir = case_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    sample = SKILL_DIR / "assets" / "image-assets" / "samples" / "m6s-animal-icon-256.png"
    copied_asset = asset_dir / "fatebreaker-guide-icon.png"
    shutil.copy2(sample, copied_asset)
    manifest = {
        "enemy_assets": [
            {
                "enemy_id": "main-boss",
                "name": "Fatebreaker",
                "kind": "boss",
                "source": "fixture-copied-sample-png",
                "asset_id": "fatebreaker-guide-icon",
                "path": "assets/fatebreaker-guide-icon.png",
                "fallback": "generic-boss-icon",
                "display": {"width": 72, "height": 72, "anchor": "center"},
            },
            {
                "enemy_id": "orb-east",
                "name": "Asset Add",
                "kind": "add",
                "source": "fallback",
                "asset_id": "asset-add-fallback",
                "fallback": "generic-add-icon",
                "display": {"width": 56, "height": 56, "anchor": "center"},
            },
        ]
    }
    manifest_path = case_dir / "enemy-assets.json"
    write_json(manifest_path, manifest)
    subprocess.run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "validate_image_assets.py"),
            str(manifest_path),
            "--json-out",
            str(case_dir / "enemy-asset-validation.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    base_spec = build_known_enemy_asset_spec()
    write_json(case_dir / "base-spec.json", base_spec)
    spec = inject_enemy_assets(base_spec, manifest, manifest_path)
    return write_custom_case(
        case_dir,
        spec,
        {
            "title": "Phase S known encounter Boss asset regression",
            "summary": "Dedicated Boss PNG injection plus explicit add fallback icon.",
            "recommended_solution": "Read asset-backed Boss, assign side add, resolve, then reset with icons preserved.",
            "common_mistakes": ["Treating fallback add icons as missing assets", "Letting cleave labels cover enemy target rings"],
            "short_callout": ["asset read", "assign east add", "drag", "resolve", "reset", "next"],
            "mnemonic": "Dedicated Boss, fallback add, both stay visible.",
            "consistency_checks": ["enemy asset manifest exists", "asset validation passes", "enemy_identity_score stays 100"],
        },
        "known-enemy-asset",
    )


def build_job_specific_positioning_spec() -> dict[str, Any]:
    boss = {"kind": "boss", "key": "boss", "name": "Boss", "pos": "center", "radius": 42, "facing": 180}
    return {
        "name": "Phase S job-specific positioning fixture",
        "style": "king-x-fru",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": {"preset": "default-circle", "source": "fixture-phase-s", "sourceReason": "Default job identity and movement preservation regression."},
        "markerPresets": "cardinals",
        "metadata": {"source": "run_visual_regression.py", "storyboard_generator": "phase-o-v3", "phase_s_fixture": "job-specific-positioning"},
        "steps": [
            phase_s_step(1, "Default job clocks", "observe_signal", "Which default job belongs to each role?", "Default official XivPlan job icons are visible: MT DRK, ST PLD, H1 AST, H2 SCH, D1 SAM, D2 DRG, D3 BRD, D4 PCT.", [boss] + party_objects(DEFAULT_POSITIONS) + [{"kind": "circle", "key": "clock-ring", "pos": "center", "radius": 136, "color": "#8fd14f", "opacity": 14}]),
            phase_s_step(2, "Caster anchor assign", "assign_roles", "Which jobs get shorter movement lanes?", "D4 PCT and healers anchor inside while melee keep uptime lanes.", [boss] + party_objects(CASTER_ANCHOR_POSITIONS) + [{"kind": "tower", "key": "caster-anchor", "pos": "SE", "distance": 94, "radius": 40, "count": 3, "color": "#2aa7ff", "opacity": 48, "label": "caster side"}]),
            phase_s_step(3, "Move by job", "first_move", "Do job icons survive movement?", "All eight players move by job-sensitive lanes while icons and role labels stay attached.", [boss] + party_objects(JOB_RESOLVE_POSITIONS) + phase_s_arrows("job3", [([0, 112], [], [-38, 142], "movement"), ([96, -96], [[118, -72]], [128, -86], "micro"), ([-96, 96], [[-144, 128]], [-204, 146], "movement")]), movement_required=True, flow_kind="movement"),
            phase_s_step(4, "Resolve job lanes", "first_resolve", "Which job lanes resolve the mechanic?", "Melee resolve outer lanes; D4 PCT remains near the caster anchor.", [boss] + party_objects(JOB_RESOLVE_POSITIONS) + [{"kind": "cone", "key": "lane-cleave", "pos": "center", "radius": 212, "coneAngle": 58, "rotation": 0, "color": "#d13438", "opacity": 22}, {"kind": "stack", "key": "caster-stack", "pos": "SE", "distance": 94, "radius": 48, "count": 4, "color": "#8fd14f", "opacity": 42, "label": "D4 anchor"}]),
            phase_s_step(5, "Reset identity", "reset", "Does the default comp persist after reset?", "Return to center lanes without losing job icons or role labels.", [boss] + party_objects(RESET_POSITIONS) + phase_s_arrows("job5", [([128, -86], [[82, -46]], [60, -36], "reset"), ([-204, 146], [[-116, 78]], [-74, 72], "reset")]) + [{"kind": "stack", "key": "reset-stack", "pos": "center", "radius": 66, "count": 8, "color": "#8fd14f", "opacity": 36}], movement_required=True, flow_kind="reset"),
            phase_s_step(6, "Next job read", "next_read_setup", "What identity state starts the next mechanic?", "Everyone reopens to default job clocks with role labels visible.", [boss] + party_objects(DEFAULT_POSITIONS) + [{"kind": "circle", "key": "next-clock-ring", "pos": "center", "radius": 132, "color": "#8fd14f", "opacity": 14}]),
        ],
    }


def write_job_specific_positioning_case(case_dir: Path) -> dict[str, Any]:
    return write_custom_case(
        case_dir,
        build_job_specific_positioning_spec(),
        {
            "title": "Phase S job-specific positioning regression",
            "summary": "Default eight-player job comp, nearby role labels, and identity preservation through movement/reset.",
            "recommended_solution": "Start clocks, anchor caster/healers, move by job lanes, resolve, reset, and reopen with the same default comp.",
            "common_mistakes": ["Dropping job icon tokens during movement updates", "Hiding role labels outside stack frames"],
            "short_callout": ["job clocks", "caster anchor", "move lanes", "resolve", "reset", "reopen"],
            "mnemonic": "DRK PLD AST SCH SAM DRG BRD PCT, labels stay near official icons.",
            "consistency_checks": ["default comp report passes", "party_identity_score stays 100", "role labels visible outside cluster frames"],
        },
        "party-job-identity",
    )


def clustered_party_objects(positions: dict[str, list[float]]) -> list[dict[str, Any]]:
    return [
        {
            "kind": "party",
            "key": role,
            "role": role,
            "pos": positions[role],
            "roleLabelVisible": False,
            "iconScale": 0.78,
        }
        for role in ROLES
    ]


def build_party_stack_label_omission_spec() -> dict[str, Any]:
    boss = {"kind": "boss", "key": "boss", "name": "Boss", "pos": "center", "radius": 42, "facing": 180}
    return {
        "name": "Phase S party stack role-label omission fixture",
        "style": "king-x-fru",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": {"preset": "default-circle", "source": "fixture-phase-s", "sourceReason": "Cluster/stack party identity crop-sheet regression."},
        "markerPresets": "cardinals",
        "metadata": {"source": "run_visual_regression.py", "storyboard_generator": "phase-o-v3", "phase_s_fixture": "party-stack-label-omission"},
        "steps": [
            phase_s_step(1, "Normal labels", "observe_signal", "Can non-cluster frames show both job and role?", "Open on normal clocks where every job icon has a nearby role label.", [boss] + party_objects(DEFAULT_POSITIONS) + [{"kind": "circle", "key": "open-ring", "pos": "center", "radius": 130, "color": "#8fd14f", "opacity": 14}]),
            phase_s_step(2, "Stack assignment", "assign_roles", "Which roles will compress into the stack?", "All eight prepare to compress; labels are still visible before the stack.", [boss] + party_objects(SPREAD_AFTER_STACK_POSITIONS) + [{"kind": "stack", "key": "stack-preview", "pos": "center", "radius": 74, "count": 8, "color": "#8fd14f", "opacity": 34, "label": "prepare stack"}]),
            phase_s_step(3, "Collapse route", "first_move", "How does the party collapse without losing icons?", "Players collapse into the stack; arrows show the compression route.", [boss] + clustered_party_objects(STACK_CLUSTER_POSITIONS) + phase_s_arrows("stk3", [([94, 94], [[58, 58]], [24, 24], "movement"), ([-94, -94], [[-58, -58]], [-24, -24], "movement"), ([0, 118], [[0, 72]], [0, 34], "movement")]), movement_required=True, flow_kind="movement", party_cluster=True, stack_group=True),
            phase_s_step(4, "Cluster resolve", "first_resolve", "Are reduced job icons readable when role labels are hidden?", "Cluster frame hides role labels, but each job icon remains visible and above the readability floor.", [boss] + clustered_party_objects(STACK_CLUSTER_POSITIONS) + [{"kind": "stack", "key": "cluster-stack", "pos": "center", "radius": 76, "count": 8, "color": "#8fd14f", "opacity": 42, "label": "8 stack"}], party_cluster=True, stack_group=True),
            phase_s_step(5, "Spread out reset", "reset", "Can role labels return after the stack?", "After stack resolution, players spread out and role labels return.", [boss] + party_objects(SPREAD_AFTER_STACK_POSITIONS) + phase_s_arrows("stk5", [([24, 24], [[58, 58]], [94, 94], "reset"), ([-24, -24], [[-58, -58]], [-94, -94], "reset")]) + [{"kind": "circle", "key": "reset-ring", "pos": "center", "radius": 122, "color": "#8fd14f", "opacity": 14}], movement_required=True, flow_kind="reset"),
            phase_s_step(6, "Next spread", "next_read_setup", "What identity state starts the next spread?", "Everyone is back on spread positions with full job and role identity.", [boss] + party_objects(DEFAULT_POSITIONS) + [{"kind": "donut", "key": "next-spread", "pos": "center", "radius": 236, "innerRadius": 172, "color": "#ffb900", "opacity": 14}]),
        ],
    }


def write_party_stack_label_omission_case(case_dir: Path) -> dict[str, Any]:
    return write_custom_case(
        case_dir,
        build_party_stack_label_omission_spec(),
        {
            "title": "Phase S party stack label omission regression",
            "summary": "Normal frames show job icons plus role labels; stack frames hide labels while preserving readable job icons.",
            "recommended_solution": "Show full labels before compression, hide role labels only for the stack frame, then restore labels on reset.",
            "common_mistakes": ["Removing job icons when hiding role labels", "Keeping labels visible in a dense stack until they overlap"],
            "short_callout": ["labels visible", "prepare stack", "collapse", "icons only", "spread reset", "next"],
            "mnemonic": "Hide labels only in the stack; never hide jobs.",
            "consistency_checks": ["cluster frame keeps job icons", "non-cluster labels return", "party_identity_score stays 100"],
        },
        "party-stack-identity",
    )


def run_pipeline(input_path: Path, case_dir: Path, meta: dict[str, Any], force: bool) -> None:
    command = [
        sys.executable,
        str(SKILL_DIR / "scripts" / "run_full_guide_pipeline.py"),
        str(input_path),
        "--encounter-name",
        meta["encounter"],
        "--phase",
        meta["phase"],
        "--version",
        meta["version"],
        "--output-dir",
        str(case_dir),
    ]
    if force:
        command.append("--force")
    subprocess.run(command, cwd=ROOT, check=True)


def render_phase_i_report(
    quality_summary: dict[str, Any],
    quality_results: list[dict[str, Any]],
    fixture_outputs: list[dict[str, Any]],
    acceptance: dict[str, Any],
) -> str:
    lines = [
        "# Phase I Visual Regression Report",
        "",
        "## Acceptance",
        "",
        f"- status: {'PASS' if acceptance['ok'] else 'FAIL'}",
        f"- fixtures: {len(fixture_outputs)}",
        f"- quality gate: {'PASS' if quality_summary['ok'] else 'FAIL'} ({quality_summary['passed']}/{quality_summary['cases']})",
        f"- Phase S fixtures present: {'PASS' if not acceptance.get('missing_phase_s_fixtures') else 'FAIL'}",
        f"- Phase S fixture count: {acceptance.get('fixture_count', len(fixture_outputs))}",
        f"- long-flow fixture: {acceptance['long_flow_slug']}",
        f"- long-flow steps: {acceptance['long_flow_steps']}",
        f"- long-flow objects: {acceptance['long_flow_objects']}",
        "",
        "## Fixture Outputs",
        "",
        "| Fixture | Status | Steps | Objects | Visual Quality | Identity / Asset Evidence | Output |",
        "|---|---|---:|---:|---|---|---|",
    ]
    by_slug = {result["slug"]: result for result in quality_results}
    for item in fixture_outputs:
        result = by_slug[item["slug"]]
        visual_quality = result.get("visual_quality", {})
        evidence = []
        case_dir = Path(item["output_dir"])
        if (case_dir / "job-identity-report.json").exists():
            evidence.append("job report")
        if (case_dir / "enemy-assets.json").exists():
            evidence.append("enemy manifest")
        if (case_dir / "enemy-asset-validation.json").exists():
            evidence.append("asset validation")
        lines.append(
            "| {slug} | {status} | {steps} | {objects} | {vq} {score} | {evidence} | `{path}` |".format(
                slug=item["slug"],
                status="PASS" if result["ok"] else "FAIL",
                steps=result["scene"]["steps"],
                objects=result["scene"]["objects"],
                vq=visual_quality.get("status", "n/a"),
                score=visual_quality.get("overall_score", "n/a"),
                evidence=", ".join(evidence) or "n/a",
                path=item["output_dir"],
            )
        )
    lines.extend(["", "## Quality Gate Detail", "", render_markdown(quality_summary, quality_results).strip()])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase I visual regression fixtures.")
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="Overwrite existing fixture outputs")
    args = parser.parse_args()

    fixtures = sorted(args.fixtures_dir.glob("*.input.md"))
    if not fixtures:
        print(f"ERROR: no visual regression fixtures found under {args.fixtures_dir}", file=sys.stderr)
        return 2

    if args.output_dir.exists() and args.force:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fixture_outputs: list[dict[str, Any]] = []
    for input_path in fixtures:
        slug = input_path.name.removesuffix(".input.md")
        meta = FIXTURE_META.get(slug, {"encounter": slug.replace("-", " ").title(), "phase": "P1", "version": "phase-i"})
        case_dir = args.output_dir / slug
        long_flow = None
        custom_builder = meta.get("custom_builder")
        if custom_builder == "semantic_long_flow":
            long_flow = write_semantic_long_flow(case_dir)
        elif custom_builder == "enemy_identity":
            long_flow = write_enemy_identity_case(case_dir)
        elif custom_builder == "known_enemy_asset":
            long_flow = write_known_enemy_asset_case(case_dir)
        elif custom_builder == "party_job_identity":
            long_flow = write_job_specific_positioning_case(case_dir)
        elif custom_builder == "party_stack_identity":
            long_flow = write_party_stack_label_omission_case(case_dir)
        else:
            run_pipeline(input_path, case_dir, meta, args.force)
            sync_case_surface(case_dir)
            if meta.get("semantic_long_flow"):
                long_flow = write_semantic_long_flow(case_dir)
        fixture_outputs.append(
            {
                "slug": slug,
                "input": str(input_path),
                "output_dir": str(case_dir),
                "semantic_long_flow": bool(meta.get("semantic_long_flow")),
                "long_flow": long_flow,
            }
        )

    quality_results = [case_result(args.output_dir / item["slug"]) for item in fixture_outputs]
    quality_summary = aggregate(quality_results)
    long_result = next((result for result in quality_results if result["slug"] == "fru-p1-thunder-fire-swords-like"), None)
    long_steps = int(long_result["scene"]["steps"]) if long_result else 0
    long_objects = int(long_result["scene"]["objects"]) if long_result else 0
    phase_s_required = {
        "multi-boss-add-identity",
        "known-encounter-boss-asset",
        "job-specific-positioning",
        "party-stack-label-omission",
        "long-teaching-storyboard",
    }
    present_slugs = {item["slug"] for item in fixture_outputs}
    missing_phase_s = sorted(phase_s_required - present_slugs)
    acceptance = {
        "ok": quality_summary["ok"] and not missing_phase_s and len(fixture_outputs) >= 10 and long_steps >= 10 and long_objects >= 500,
        "fixture_count": len(fixture_outputs),
        "phase_s_required_fixtures": sorted(phase_s_required),
        "missing_phase_s_fixtures": missing_phase_s,
        "long_flow_slug": long_result["slug"] if long_result else "missing",
        "long_flow_steps": long_steps,
        "long_flow_objects": long_objects,
    }

    payload = {
        "summary": quality_summary,
        "acceptance": acceptance,
        "fixtures": fixture_outputs,
        "results": quality_results,
    }
    write_json(args.output_dir / "visual-regression-results.json", payload)
    (args.output_dir / "visual-regression-report.md").write_text(
        render_phase_i_report(quality_summary, quality_results, fixture_outputs, acceptance),
        encoding="utf-8",
    )

    print(f"Wrote {args.output_dir / 'visual-regression-report.md'}")
    print(f"Wrote {args.output_dir / 'visual-regression-results.json'}")
    print(f"status: {'PASS' if acceptance['ok'] else 'FAIL'} ({quality_summary['passed']}/{quality_summary['cases']} cases)")
    print(f"long-flow: {long_steps} steps, {long_objects} objects")
    return 0 if acceptance["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
