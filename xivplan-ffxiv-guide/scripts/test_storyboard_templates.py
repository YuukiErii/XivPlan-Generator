#!/usr/bin/env python3
"""Regression checks for Phase F storyboard templates."""

from __future__ import annotations

import sys

from build_spec_from_solution import ROLES, build_spec
from build_xivplan_scene import build_scene
from validate_xivplan_scene import validate_scene


TARGETS = {
    "MT": [0, 115],
    "ST": [0, -115],
    "H1": [-150, 0],
    "H2": [150, 0],
    "D1": [-110, 110],
    "D2": [110, 110],
    "D3": [-125, -125],
    "D4": [125, -125],
}
REQUIRED_PHASES = {"observe", "move", "resolve", "reset"}
REQUIRED_FIELDS = ("purpose", "guide_text", "checks", "visual_focus", "required_roles", "reset_state", "storyboard_phase")


def bundle_for(categories: list[str]) -> dict:
    return {
        "mechanic": "storyboard-template-smoke",
        "planning_context": {
            "categories": categories,
            "unknowns": [],
            "arena_selection": {"preset": "default-circle", "source": "default-fallback", "reason": "test"},
        },
        "candidates": [
            {
                "id": "safe-prog",
                "mode": "test",
                "assumptions": [],
                "risks": [],
                "movements": [{"role": role, "to": TARGETS[role]} for role in ROLES],
                "step_plan": [{}, {"guide_text": "按职能固定预站。"}],
            }
        ],
    }


def assert_storyboard(categories: list[str]) -> None:
    spec = build_spec(bundle_for(categories), None, "safe-prog")
    steps = spec["steps"]
    assert 6 <= len(steps) <= 14, (categories, len(steps))
    phases = {step["storyboard_phase"] for step in steps}
    assert REQUIRED_PHASES <= phases, (categories, phases)
    for index, step in enumerate(steps, start=1):
        for field in REQUIRED_FIELDS:
            assert step.get(field), (categories, index, field)

    scene = build_scene(spec)
    errors, _counts, _objects = validate_scene(scene)
    assert not errors, (categories, errors[:5])
    for index, step in enumerate(scene["steps"], start=1):
        for field in REQUIRED_FIELDS:
            assert step.get(field), (categories, index, field)
        if step.get("movement_required"):
            assert any(obj.get("type") in {"arrow", "tether"} for obj in step.get("objects", [])), (categories, index, "missing flow")


def main() -> int:
    cases = [
        ["spread"],
        ["stack"],
        ["tower"],
        ["tether"],
        ["knockback"],
        ["sequence"],
        ["tile-platform"],
        ["tower", "stack", "spread", "tether", "sequence"],
    ]
    for categories in cases:
        assert_storyboard(categories)
    print(f"OK: Phase F storyboard templates covered {len(cases)} category sets")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
