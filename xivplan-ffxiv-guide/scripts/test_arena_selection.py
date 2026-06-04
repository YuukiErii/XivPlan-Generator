#!/usr/bin/env python3
"""Regression checks for arena preset selection and propagation."""

from __future__ import annotations

import sys

from build_spec_from_solution import build_spec
from build_xivplan_scene import build_scene
from parse_mechanic_request import parse_text
from plan_solution_candidates import plan_bundle


def minimal_timeline(parsed: dict) -> dict:
    return parsed["timeline_ir"]


def assert_arena(parsed: dict, preset: str, source: str) -> None:
    selection = parsed["mechanic_ir"]["arena_selection"]
    assert selection["preset"] == preset, selection
    assert selection["source"] == source, selection


def main() -> int:
    explicit = parse_text("Background use FRU P1. Thunder fire swords safe-side read.", encounter_name="unknown", phase="unknown")
    assert_arena(explicit, "fru-p1", "user-specified")

    light = parse_text("Mechanic is similar to Light Rampant with tether towers.", encounter_name="unknown", phase="unknown")
    assert_arena(light, "eden-light", "user-specified")

    udm_phase = parse_text("绝妖星乱舞 P2 一运，盗火分组后踩塔。", encounter_name="unknown", phase="unknown")
    assert_arena(udm_phase, "udm-p2", "user-specified")

    o8s_fallback = parse_text("妖星乱舞 / O8S style branch dance.", encounter_name="unknown", phase="unknown")
    assert_arena(o8s_fallback, "omega-o8s", "user-specified")

    inferred = parse_text("Simple spread then stack.", encounter_name="FRU", phase="P1")
    assert_arena(inferred, "fru-p1", "mechanic-inferred")

    fallback = parse_text("Generic spread then stack.", encounter_name="unknown", phase="unknown")
    assert_arena(fallback, "default-circle", "default-fallback")

    bundle = plan_bundle(explicit["mechanic_ir"], minimal_timeline(explicit), None, {"strategy_context": "prog"})
    spec = build_spec(bundle, None, "safe-prog")
    assert spec["arena"]["preset"] == "fru-p1", spec["arena"]
    assert spec["metadata"]["arena_selection"]["source"] == "user-specified", spec["metadata"]

    scene = build_scene(
        {
            "name": "arena alias smoke",
            "arena": {"preset": "light-rampant", "source": "user-specified"},
            "steps": [{"title": "1", "guide_text": "smoke", "objects": [{"kind": "boss"}]}],
        }
    )
    assert scene["arena"]["preset"] == "eden-light", scene["arena"]
    assert scene["arena"]["backgroundImage"] == "/arena/e8.svg", scene["arena"]
    assert scene["arena"]["source"] == "user-specified", scene["arena"]

    udm_scene = build_scene(
        {
            "name": "udm arena alias smoke",
            "arena": {"preset": "udm-p2", "source": "user-specified"},
            "steps": [{"title": "1", "guide_text": "smoke", "objects": [{"kind": "boss"}]}],
        }
    )
    assert udm_scene["arena"]["preset"] == "udm-p2", udm_scene["arena"]
    assert udm_scene["arena"]["backgroundImage"] == "/arena/udm-phase2.png", udm_scene["arena"]
    assert udm_scene["arena"]["backgroundOpacity"] == 40, udm_scene["arena"]

    print("OK: arena selection detects, propagates, and resolves aliases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
