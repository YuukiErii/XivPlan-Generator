#!/usr/bin/env python3
"""Regression checks for the Phase 10 natural-language mechanic parser."""

from __future__ import annotations

import sys
from pathlib import Path

from parse_mechanic_request import parse_text


FIXTURES = Path(__file__).resolve().parents[1] / "assets" / "parser-fixtures"


def categories(parsed: dict) -> set[str]:
    return {item["category"] for item in parsed["candidate_categories"]}


def event_times(parsed: dict) -> list[str]:
    return [event["time"] for event in parsed["timeline_ir"]["events"] if event["time"]]


def assert_ordered_times(times: list[str]) -> None:
    numeric = [int(time.split(":")[0]) * 60 + int(time.split(":")[1]) for time in times]
    assert numeric == sorted(numeric), times


def parse_fixture(name: str) -> dict:
    path = FIXTURES / name
    return parse_text(path.read_text(encoding="utf-8"), encounter_name=name, phase="unknown", source="fixture")


def main() -> int:
    tower = parse_fixture("four-tower-spread-stack.input.md")
    assert {"tower", "spread", "stack"}.issubset(categories(tower)), categories(tower)
    assert_ordered_times(event_times(tower))

    light = parse_fixture("light-rampant-like.input.md")
    assert "light-rampant-like" in categories(light), categories(light)
    assert "tether" in categories(light), categories(light)
    assert "tower" in categories(light), categories(light)

    limit_cut = parse_fixture("hello-world-limit-cut.input.md")
    assert "hello-world-like" in categories(limit_cut), categories(limit_cut)
    assert "limit-cut-like" in categories(limit_cut), categories(limit_cut)
    assert "line-shape" in categories(limit_cut), categories(limit_cut)
    assert_ordered_times(event_times(limit_cut))

    fru = parse_fixture("fru-p1-rewrite.input.md")
    assert "cleave" in categories(fru), categories(fru)
    assert "spread" in categories(fru), categories(fru)
    assert "tankbuster" in categories(fru), categories(fru)

    animal = parse_fixture("image2-animal-asset.input.md")
    assert "debuff" in categories(animal), categories(animal)
    assert "spread" in categories(animal), categories(animal)
    assert "stack" in categories(animal), categories(animal)

    yokai = parse_fixture("ultimate-yokai-star-dance-p1-draft.input.md")
    yokai_unknowns = yokai["mechanic_ir"]["unknowns"]
    assert yokai_unknowns, "expected unknowns for draft yokai fixture"
    assert any(item["kind"] == "targeting_rule" for item in yokai_unknowns), yokai_unknowns
    assert yokai["mechanic_ir"]["party_constraints"]["melee_uptime"] == "prefer"
    assert yokai["mechanic_ir"]["party_constraints"]["caster_movement"] == "minimize"

    incomplete = parse_fixture("incomplete-unknowns.input.md")
    assert len(incomplete["mechanic_ir"]["unknowns"]) >= 3, incomplete["mechanic_ir"]["unknowns"]
    assert any(item["severity"] == "blocking" for item in incomplete["mechanic_ir"]["unknowns"])

    print("OK: mechanic parser recognizes categories, preserves timeline order, and emits unknowns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
