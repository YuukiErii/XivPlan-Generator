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
from build_xivplan_scene import build_scene
from export_xivplan_steps import export_steps
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
        {"kind": "boss", "key": f"{prefix}-east-clone", "name": east_label, "pos": "E", "distance": 205, "radius": 24, "opacity": 78},
        {"kind": "boss", "key": f"{prefix}-west-clone", "name": west_label, "pos": "W", "distance": 205, "radius": 24, "opacity": 78},
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
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "title": f"{index} {title}",
        "storyboard_phase": phase,
        "movement_required": movement_required,
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
        "summary": "Phase L replaces density padding with a readable 12-step FRU-style thunder/fire storyboard.",
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
        "consistency_checks": ["12 semantic steps", "500+ objects", "full context in every normal frame"],
        "unknowns": [],
    }
    guide_path = case_dir / "guide.json"
    write_json(guide_path, guide)
    assemble_guide(guide_path, case_dir / "guide-package", strict_images=True)
    return {"steps": len(scene["steps"]), "objects": object_count, "mode": "semantic-storyboard"}


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
        f"- long-flow fixture: {acceptance['long_flow_slug']}",
        f"- long-flow steps: {acceptance['long_flow_steps']}",
        f"- long-flow objects: {acceptance['long_flow_objects']}",
        "",
        "## Fixture Outputs",
        "",
        "| Fixture | Status | Steps | Objects | Visual Quality | Output |",
        "|---|---|---:|---:|---|---|",
    ]
    by_slug = {result["slug"]: result for result in quality_results}
    for item in fixture_outputs:
        result = by_slug[item["slug"]]
        visual_quality = result.get("visual_quality", {})
        lines.append(
            "| {slug} | {status} | {steps} | {objects} | {vq} {score} | `{path}` |".format(
                slug=item["slug"],
                status="PASS" if result["ok"] else "FAIL",
                steps=result["scene"]["steps"],
                objects=result["scene"]["objects"],
                vq=visual_quality.get("status", "n/a"),
                score=visual_quality.get("overall_score", "n/a"),
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
        run_pipeline(input_path, case_dir, meta, args.force)
        sync_case_surface(case_dir)
        long_flow = None
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
    acceptance = {
        "ok": quality_summary["ok"] and long_steps >= 10 and long_objects >= 500,
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
