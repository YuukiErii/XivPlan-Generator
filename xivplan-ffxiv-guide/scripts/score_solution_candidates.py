#!/usr/bin/env python3
"""Score and compare FFXIV strategy candidates before drawing XivPlan scenes."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_ROLES = ("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4")
DEFAULT_BOSS = {"pos": [0, 0], "uptime_radius": 120, "targetable_duration": 12}
TIMING_MULTIPLIERS = {
    "downtime": 0.1,
    "free": 0.25,
    "preposition": 0.5,
    "resolution": 1.2,
    "cast": 1.5,
}
SCORE_FIELDS = (
    "caster_movement_score",
    "melee_uptime_score",
    "memory_score",
    "tolerance_score",
    "communication_score",
    "diagram_clarity_score",
    "fight_specific_fit_score",
)
SCORE_LABELS = {
    "caster_movement_score": "读条职业移动",
    "melee_uptime_score": "近战 uptime",
    "memory_score": "记忆成本",
    "tolerance_score": "容错",
    "communication_score": "沟通成本",
    "diagram_clarity_score": "图面清晰度",
    "fight_specific_fit_score": "副本适配",
}


class ScoreError(ValueError):
    """Candidate bundle cannot be scored."""


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def round_score(value: float) -> float:
    return round(value + 1e-9, 2)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_pos(value: Any) -> tuple[float, float]:
    if isinstance(value, list) and len(value) == 2 and all(isinstance(item, (int, float)) for item in value):
        return float(value[0]), float(value[1])
    if isinstance(value, dict) and isinstance(value.get("x"), (int, float)) and isinstance(value.get("y"), (int, float)):
        return float(value["x"]), float(value["y"])
    raise ScoreError(f"position must be [x, y] or {{x, y}}, got {value!r}")


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.dist(a, b)


def role_tags(role: str, party: dict[str, Any]) -> set[str]:
    tags = set(party.get(role, {}).get("tags", []))
    if role in {"MT", "ST"}:
        tags.update({"tank", "uptime"})
    elif role in {"H1", "H2"}:
        tags.update({"healer", "caster"})
    elif role in {"D1", "D2"}:
        tags.update({"melee", "uptime"})
    elif role == "D3":
        tags.add("mobile_ranged")
    elif role == "D4":
        tags.add("caster")
    return tags


def movement_role_weight(role: str, party: dict[str, Any]) -> float:
    tags = role_tags(role, party)
    if "caster" in tags:
        return 1.5
    if "healer" in tags:
        return 1.35
    if "uptime" in tags:
        return 1.1
    if "mobile_ranged" in tags:
        return 0.8
    return 1.0


def timing_multiplier(movement: dict[str, Any]) -> float:
    timing = str(movement.get("timing", "resolution"))
    if timing not in TIMING_MULTIPLIERS:
        raise ScoreError(f"unsupported movement timing: {timing!r}")
    multiplier = TIMING_MULTIPLIERS[timing]
    if movement.get("forced"):
        multiplier *= 0.75
    return multiplier


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if abs(value) < 1e-9:
        return 0
    return 1 if value > 0 else 2


def proper_segment_crossing(
    a1: tuple[float, float],
    a2: tuple[float, float],
    b1: tuple[float, float],
    b2: tuple[float, float],
) -> bool:
    # Shared endpoints are intentional stack/reset points, not route crossings.
    if any(distance(left, right) < 1e-9 for left in (a1, a2) for right in (b1, b2)):
        return False
    return orientation(a1, a2, b1) != orientation(a1, a2, b2) and orientation(b1, b2, a1) != orientation(
        b1, b2, a2
    )


def segment_outside_fraction(
    start: tuple[float, float],
    end: tuple[float, float],
    center: tuple[float, float],
    radius: float,
    samples: int = 40,
) -> float:
    outside = 0
    for index in range(samples):
        ratio = (index + 0.5) / samples
        point = (start[0] + (end[0] - start[0]) * ratio, start[1] + (end[1] - start[1]) * ratio)
        if distance(point, center) > radius:
            outside += 1
    return outside / samples


def count_route_crossings(movements: list[dict[str, Any]]) -> list[dict[str, str]]:
    crossings: list[dict[str, str]] = []
    by_beat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for movement in movements:
        if movement.get("route_check", True):
            by_beat[str(movement.get("beat", "default"))].append(movement)

    for beat, beat_movements in by_beat.items():
        for index, first in enumerate(beat_movements):
            for second in beat_movements[index + 1 :]:
                if first["role"] == second["role"]:
                    continue
                if proper_segment_crossing(
                    resolve_pos(first["from"]),
                    resolve_pos(first["to"]),
                    resolve_pos(second["from"]),
                    resolve_pos(second["to"]),
                ):
                    crossings.append({"beat": beat, "roles": f"{first['role']} / {second['role']}"})
    return crossings


def movement_scores(
    movements: list[dict[str, Any]],
    party: dict[str, Any],
    budgets: dict[str, float],
) -> tuple[float, float, dict[str, Any]]:
    weighted_total = 0.0
    caster_total = 0.0
    role_distances: dict[str, float] = defaultdict(float)
    role_weighted: dict[str, float] = defaultdict(float)

    for movement in movements:
        role = movement["role"]
        length = distance(resolve_pos(movement["from"]), resolve_pos(movement["to"]))
        base = length / 100 * timing_multiplier(movement)
        weighted = base * movement_role_weight(role, party)
        weighted_total += weighted
        role_distances[role] += length
        role_weighted[role] += weighted
        if "caster" in role_tags(role, party):
            caster_total += base * 1.5

    movement_budget = float(budgets.get("movement", 32))
    caster_budget = float(budgets.get("caster_movement", 12))
    if movement_budget <= 0 or caster_budget <= 0:
        raise ScoreError("movement budgets must be positive numbers")
    movement_score = 20 * (1 - weighted_total / movement_budget)
    caster_score = 20 * (1 - caster_total / caster_budget)
    details = {
        "weighted_movement_cost": round_score(weighted_total),
        "caster_movement_cost": round_score(caster_total),
        "role_distances": {role: round_score(value) for role, value in sorted(role_distances.items())},
        "role_weighted_costs": {role: round_score(value) for role, value in sorted(role_weighted.items())},
    }
    return round_score(clamp(movement_score, 0, 20)), round_score(clamp(caster_score, 0, 20)), details


def melee_uptime_score(
    movements: list[dict[str, Any]],
    party: dict[str, Any],
    boss: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    center = resolve_pos(boss.get("pos", DEFAULT_BOSS["pos"]))
    radius = float(boss.get("uptime_radius", DEFAULT_BOSS["uptime_radius"]))
    targetable_duration = float(boss.get("targetable_duration", DEFAULT_BOSS["targetable_duration"]))
    uptime_roles = sorted(role for role in party if "uptime" in role_tags(role, party))
    lost_by_role: dict[str, float] = defaultdict(float)

    for movement in movements:
        role = movement["role"]
        if role not in uptime_roles or not movement.get("boss_targetable", True):
            continue
        start = resolve_pos(movement["from"])
        end = resolve_pos(movement["to"])
        duration = float(movement.get("duration", 1))
        hold = float(movement.get("hold", 0))
        lost_by_role[role] += duration * segment_outside_fraction(start, end, center, radius)
        if distance(end, center) > radius:
            lost_by_role[role] += hold

    if not uptime_roles:
        return 20.0, {"uptime_roles": [], "lost_by_role": {}, "average_lost_duration": 0.0}

    average_loss = sum(lost_by_role.values()) / len(uptime_roles)
    score = 20 * (1 - average_loss / targetable_duration)
    details = {
        "uptime_roles": uptime_roles,
        "uptime_radius": radius,
        "targetable_duration": targetable_duration,
        "lost_by_role": {role: round_score(lost_by_role.get(role, 0.0)) for role in uptime_roles},
        "average_lost_duration": round_score(average_loss),
    }
    return round_score(clamp(score, 0, 20)), details


def memory_score(complexity: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    penalties = {
        "live_sorts": float(complexity.get("live_sorts", 0)) * 2.5,
        "role_swaps": float(complexity.get("role_swaps", 0)) * 1.5,
        "exceptions": float(complexity.get("exceptions", 0)) * 1.5,
        "simultaneous_attributes": max(float(complexity.get("simultaneous_attributes", 1)) - 1, 0) * 1.0,
    }
    bonuses = {
        "pattern_reuse": min(float(complexity.get("pattern_reuse", 0)) * 0.75, 3),
        "fixed_assignments": min(float(complexity.get("fixed_assignments", 0)) * 0.4, 2),
        "stable_meanings": min(float(complexity.get("stable_meanings", 0)) * 0.4, 2),
    }
    score = 20 - sum(penalties.values()) + sum(bonuses.values())
    return round_score(clamp(score, 0, 20)), {"penalties": penalties, "bonuses": bonuses}


def tolerance_score(tolerance: dict[str, Any], auto_crossings: int) -> tuple[float, dict[str, Any]]:
    margin = float(tolerance.get("min_margin", 30))
    penalties = {
        "small_margin": max(30 - margin, 0) / 3,
        "crossing_routes": (float(tolerance.get("crossing_routes", 0)) + auto_crossings) * 2,
        "simultaneous_swaps": float(tolerance.get("simultaneous_swaps", 0)) * 0.75,
        "last_second_adjustments": float(tolerance.get("last_second_adjustments", 0)) * 1.5,
    }
    return round_score(clamp(15 - sum(penalties.values()), 0, 15)), {"min_margin": margin, "penalties": penalties}


def communication_score(communication: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    penalties = {
        "long_callout": max(float(communication.get("callout_words", 0)) - 16, 0) * 0.15,
        "priority_rules": float(communication.get("priority_rules", 0)) * 0.8,
        "exception_rules": float(communication.get("exception_rules", 0)) * 1.0,
        "long_macro": max(float(communication.get("macro_lines", 0)) - 4, 0) * 0.5,
    }
    return round_score(clamp(10 - sum(penalties.values()), 0, 10)), {"penalties": penalties}


def diagram_score(diagram: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    penalties = {
        "too_many_steps": max(float(diagram.get("steps", 0)) - 6, 0) * 0.5,
        "arrows": float(diagram.get("arrows", 0)) * 0.1,
        "crossing_arrows": float(diagram.get("crossing_arrows", 0)) * 1.2,
        "dense_labels": max(float(diagram.get("labels", 0)) - 16, 0) * 0.15,
        "branches": float(diagram.get("branches", 0)) * 1.0,
        "dense_step": max(float(diagram.get("max_objects_per_step", 0)) - 30, 0) * 0.08,
    }
    return round_score(clamp(10 - sum(penalties.values()), 0, 10)), {"penalties": penalties}


def phase12_diagnostics(candidate: dict[str, Any], movements: list[dict[str, Any]]) -> dict[str, Any]:
    tolerance = candidate.get("tolerance", {})
    cast_window_cost = 0.0
    reset_cost = 0.0
    timeline_distance = 0.0
    for movement in movements:
        length = distance(resolve_pos(movement["from"]), resolve_pos(movement["to"]))
        timeline_distance += length
        if movement.get("timing") == "cast":
            cast_window_cost += length
        if str(movement.get("beat", "")).lower() in {"reset", "recenter", "return"}:
            reset_cost += length
    safe_area_ratio = float(tolerance.get("safe_area_ratio", 0.0))
    return {
        "timeline_movement_distance": round_score(timeline_distance),
        "cast_window_movement_distance": round_score(cast_window_cost),
        "reset_movement_distance": round_score(reset_cost),
        "safe_area_ratio": round_score(safe_area_ratio),
        "tower_players": int(tolerance.get("tower_players", 0)),
        "stack_players": int(tolerance.get("stack_players", 0)),
        "phase12_checks": [
            {
                "name": "timeline_movement_distance",
                "passed": timeline_distance <= float(candidate.get("budgets", {}).get("timeline_distance", 1200)),
                "details": f"{round_score(timeline_distance)} total coordinate units",
            },
            {
                "name": "cast_window_movement",
                "passed": cast_window_cost <= 260,
                "details": f"{round_score(cast_window_cost)} coordinate units during cast windows",
            },
            {
                "name": "reset_cost",
                "passed": reset_cost <= 360,
                "details": f"{round_score(reset_cost)} coordinate units marked as reset movement",
            },
            {
                "name": "safe_area",
                "passed": safe_area_ratio == 0 or safe_area_ratio >= 0.35,
                "details": f"{round_score(safe_area_ratio)} declared safe-area ratio",
            },
        ],
    }


def declared_safety_checks(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    checks = candidate.get("safety_checks", [])
    if not isinstance(checks, list):
        raise ScoreError("candidate.safety_checks must be a list")
    normalized = []
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("name"), str):
            raise ScoreError("each safety check must have a string name")
        normalized.append(
            {
                "name": check["name"],
                "passed": bool(check.get("passed")),
                "details": str(check.get("details", "")),
            }
        )
    return normalized


def score_candidate(bundle: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    party = bundle.get("party", {})
    if not isinstance(party, dict):
        raise ScoreError("party must be an object keyed by role")
    movements = candidate.get("movements", [])
    if not isinstance(movements, list):
        raise ScoreError("candidate.movements must be a list")
    for movement in movements:
        if not isinstance(movement, dict):
            raise ScoreError("each movement must be an object")
        role = movement.get("role")
        if role not in party:
            raise ScoreError(f"movement role must exist in party: {role!r}")
        resolve_pos(movement.get("from"))
        resolve_pos(movement.get("to"))

    checks = declared_safety_checks(candidate)
    phase12 = phase12_diagnostics(candidate, movements)
    checks.extend(phase12["phase12_checks"])
    missing_roles = sorted(role for role in DEFAULT_ROLES if role not in party)
    checks.append(
        {
            "name": "party_roles_present",
            "passed": not missing_roles,
            "details": "all eight default roles present" if not missing_roles else f"missing roles: {', '.join(missing_roles)}",
        }
    )

    crossings = count_route_crossings(movements)
    forbid_crossing = bool(bundle.get("constraints", {}).get("forbid_route_crossing", False))
    checks.append(
        {
            "name": "forbidden_route_crossing",
            "passed": not (forbid_crossing and crossings),
            "details": "none" if not crossings else "; ".join(f"{item['beat']}: {item['roles']}" for item in crossings),
        }
    )
    safety_gate = all(check["passed"] for check in checks)

    movement_score, caster_score, movement_details = movement_scores(
        movements,
        party,
        bundle.get("budgets", {}),
    )
    uptime_score, uptime_details = melee_uptime_score(movements, party, {**DEFAULT_BOSS, **bundle.get("boss", {})})
    memory, memory_details = memory_score(candidate.get("complexity", {}))
    tolerance, tolerance_details = tolerance_score(candidate.get("tolerance", {}), len(crossings))
    communication, communication_details = communication_score(candidate.get("communication", {}))
    diagram, diagram_details = diagram_score(candidate.get("diagram", {}))
    fight_specific_fit = round_score(clamp(float(candidate.get("fight_specific_fit", 0)), 0, 5))
    components = {
        "movement_score": movement_score,
        "caster_movement_score": caster_score,
        "melee_uptime_score": uptime_score,
        "memory_score": memory,
        "tolerance_score": tolerance,
        "communication_score": communication,
        "diagram_clarity_score": diagram,
        "fight_specific_fit_score": fight_specific_fit,
    }
    total = sum(components[field] for field in SCORE_FIELDS)

    return {
        "id": str(candidate.get("id", "")),
        "name": str(candidate.get("name", candidate.get("id", ""))),
        "summary": str(candidate.get("summary", "")),
        "tradeoffs": [str(item) for item in candidate.get("tradeoffs", [])],
        "safety_gate": safety_gate,
        "recommendable": safety_gate,
        "solution_score": round_score(total) if safety_gate else None,
        "components": components,
        "safety_checks": checks,
        "route_crossings": crossings,
        "details": {
            "movement": movement_details,
            "melee_uptime": uptime_details,
            "memory": memory_details,
            "tolerance": tolerance_details,
            "communication": communication_details,
            "diagram": diagram_details,
            "phase12": {key: value for key, value in phase12.items() if key != "phase12_checks"},
        },
    }


def recommendation_reason(results: list[dict[str, Any]]) -> list[str]:
    recommendable = [result for result in results if result["recommendable"]]
    if not recommendable:
        return ["没有候选方案通过安全门槛。"]
    best = recommendable[0]
    if len(recommendable) == 1:
        return ["这是唯一通过安全门槛的候选方案。"]
    runner_up = recommendable[1]
    deltas = []
    for field in SCORE_FIELDS:
        delta = best["components"][field] - runner_up["components"][field]
        if delta > 0:
            deltas.append((delta, SCORE_LABELS[field]))
    deltas.sort(reverse=True)
    if not deltas:
        return ["总分最高，且没有明显单项劣势。"]
    return [f"{label}比次选高 {round_score(delta)} 分。" for delta, label in deltas[:3]]


def score_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    candidates = bundle.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ScoreError("candidates must contain at least two strategy candidates")
    results = [score_candidate(bundle, candidate) for candidate in candidates]
    results.sort(key=lambda item: (item["recommendable"], item["solution_score"] or -1), reverse=True)
    recommendable = [result for result in results if result["recommendable"]]
    recommended = recommendable[0]["id"] if recommendable else None
    return {
        "version": 1,
        "mechanic": str(bundle.get("mechanic", "")),
        "description": str(bundle.get("description", "")),
        "recommended_candidate": recommended,
        "recommendation_reason": recommendation_reason(results),
        "candidates": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    by_id = {item["id"]: item for item in report["candidates"]}
    recommended = by_id.get(report["recommended_candidate"])
    lines = [
        f"# {report['mechanic']} 解法评分",
        "",
        report["description"],
        "",
        "## 候选总览",
        "",
        "| 候选 | 安全门槛 | 总分 | 读条移动 | 近战 uptime | 记忆 | 容错 | 沟通 | 图面 | 适配 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for candidate in report["candidates"]:
        components = candidate["components"]
        lines.append(
            "| {name} | {gate} | {total} | {caster} | {uptime} | {memory} | {tolerance} | {communication} | {diagram} | {fit} |".format(
                name=candidate["name"],
                gate="通过" if candidate["safety_gate"] else "淘汰",
                total=candidate["solution_score"] if candidate["solution_score"] is not None else "-",
                caster=components["caster_movement_score"],
                uptime=components["melee_uptime_score"],
                memory=components["memory_score"],
                tolerance=components["tolerance_score"],
                communication=components["communication_score"],
                diagram=components["diagram_clarity_score"],
                fit=components["fight_specific_fit_score"],
            )
        )

    lines.extend(["", "## 推荐方案", ""])
    if recommended:
        lines.append(f"推荐 `{recommended['name']}`。")
        lines.append("")
        for reason in report["recommendation_reason"]:
            lines.append(f"- {reason}")
        if recommended["tradeoffs"]:
            lines.append("- 牺牲点：" + "；".join(recommended["tradeoffs"]))
    else:
        lines.append("没有方案通过安全门槛。先修复硬性问题，再比较软评分。")

    lines.extend(["", "## 候选明细", ""])
    for candidate in report["candidates"]:
        lines.extend(
            [
                f"### {candidate['name']}",
                "",
                candidate["summary"],
                "",
                f"- 安全门槛：{'通过' if candidate['safety_gate'] else '淘汰'}",
                f"- 总移动成本：{candidate['details']['movement']['weighted_movement_cost']}",
                f"- 读条职业移动成本：{candidate['details']['movement']['caster_movement_cost']}",
                f"- 近战平均损失时长：{candidate['details']['melee_uptime']['average_lost_duration']}",
            ]
        )
        if candidate["tradeoffs"]:
            lines.append("- 牺牲点：" + "；".join(candidate["tradeoffs"]))
        failed = [check for check in candidate["safety_checks"] if not check["passed"]]
        if failed:
            lines.append("- 安全问题：" + "；".join(f"{check['name']} ({check['details']})" for check in failed))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Score FFXIV strategy candidates and recommend a safe solution.")
    parser.add_argument("bundle", type=Path, help="Path to candidate bundle JSON")
    parser.add_argument("--json-out", type=Path, help="Optional structured score report")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown comparison report")
    args = parser.parse_args()

    try:
        report = score_bundle(read_json(args.bundle))
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.json_out:
        write_json(args.json_out, report)
        print(f"Wrote {args.json_out}")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
        print(f"Wrote {args.markdown_out}")

    print(f"mechanic: {report['mechanic']}")
    print(f"candidates: {len(report['candidates'])}")
    print(f"recommended: {report['recommended_candidate'] or 'none'}")
    for candidate in report["candidates"]:
        total = candidate["solution_score"] if candidate["solution_score"] is not None else "REJECTED"
        print(f"- {candidate['id']}: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
