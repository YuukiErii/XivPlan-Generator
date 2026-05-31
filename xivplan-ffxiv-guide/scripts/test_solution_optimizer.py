#!/usr/bin/env python3
"""Regression checks for the Phase 4 solution optimizer."""

from __future__ import annotations

import sys
from pathlib import Path

from score_solution_candidates import read_json, score_bundle


SAMPLE = Path(__file__).resolve().parents[1] / "assets" / "optimization" / "spread-stack-candidates.json"


def main() -> int:
    report = score_bundle(read_json(SAMPLE))
    by_id = {candidate["id"]: candidate for candidate in report["candidates"]}

    assert report["recommended_candidate"] == "fixed-clocks", report["recommended_candidate"]
    assert by_id["fixed-clocks"]["recommendable"]
    assert by_id["caster-anchor"]["recommendable"]
    assert not by_id["crossing-shortcut"]["recommendable"]
    assert by_id["caster-anchor"]["components"]["caster_movement_score"] > by_id["fixed-clocks"]["components"][
        "caster_movement_score"
    ]
    assert by_id["fixed-clocks"]["components"]["memory_score"] > by_id["caster-anchor"]["components"]["memory_score"]
    assert by_id["crossing-shortcut"]["route_crossings"]

    print("OK: optimizer recommends fixed-clocks and rejects crossing-shortcut")
    return 0


if __name__ == "__main__":
    sys.exit(main())
