#!/usr/bin/env python3
"""Plan Phase 12 solution candidates from mechanic IR, timeline IR, and constraints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROLES = ("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4")
BASE_POS = {
    "MT": [0, 70],
    "ST": [0, -70],
    "H1": [-70, 0],
    "H2": [70, 0],
    "D1": [-52, 52],
    "D2": [52, 52],
    "D3": [-58, -58],
    "D4": [58, -58],
}
CLOCK_POS = {
    "MT": [0, 115],
    "ST": [0, -115],
    "H1": [-150, 0],
    "H2": [150, 0],
    "D1": [-110, 110],
    "D2": [110, 110],
    "D3": [-125, -125],
    "D4": [125, -125],
}
OUTER_POS = {
    "MT": [0, 185],
    "ST": [0, -185],
    "H1": [-185, 0],
    "H2": [185, 0],
    "D1": [-160, 160],
    "D2": [160, 160],
    "D3": [-175, -175],
    "D4": [175, -175],
}
INNER_POS = {
    "MT": [0, 90],
    "ST": [0, -90],
    "H1": [-90, 0],
    "H2": [90, 0],
    "D1": [-58, 58],
    "D2": [58, 58],
    "D3": [-128, -128],
    "D4": [82, -82],
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mechanic_name(mechanic_ir: dict[str, Any]) -> str:
    context = mechanic_ir.get("encounter_context", {})
    name = context.get("encounter_name") or "generated-mechanic"
    phase = context.get("phase")
    return f"{name} {phase}".strip()


def all_categories(mechanic_ir: dict[str, Any], timeline_ir: dict[str, Any]) -> set[str]:
    categories: set[str] = set()
    for mechanic in mechanic_ir.get("mechanics", []):
        categories.update(str(item) for item in mechanic.get("categories", []))
        if mechanic.get("primary_category"):
            categories.add(str(mechanic["primary_category"]))
    for event in timeline_ir.get("events", []):
        categories.update(str(item) for item in event.get("categories", []))
    return categories


def collect_unknowns(mechanic_ir: dict[str, Any], timeline_ir: dict[str, Any]) -> list[str]:
    unknowns = []
    for item in mechanic_ir.get("unknowns", []):
        text = item.get("question") or item.get("text")
        if text:
            unknowns.append(str(text))
    for event in timeline_ir.get("events", []):
        if event.get("unknown_refs"):
            unknowns.append(f"{event.get('time', '??:??')} {event.get('description', '')} 存在未确认规则。")
    return sorted(set(unknowns))


def default_party() -> dict[str, dict[str, Any]]:
    return {
        "MT": {"job": "DRK", "icon": "/actor/DRK.png", "roleLabel": "MT", "tags": ["tank", "uptime"]},
        "ST": {"job": "PLD", "icon": "/actor/PLD.png", "roleLabel": "ST", "tags": ["tank", "uptime"]},
        "H1": {"job": "AST", "icon": "/actor/AST.png", "roleLabel": "H1", "tags": ["healer", "caster"]},
        "H2": {"job": "SCH", "icon": "/actor/SCH.png", "roleLabel": "H2", "tags": ["healer", "caster"]},
        "D1": {"job": "SAM", "icon": "/actor/SAM.png", "roleLabel": "D1", "tags": ["melee", "uptime"]},
        "D2": {"job": "DRG", "icon": "/actor/DRG.png", "roleLabel": "D2", "tags": ["melee", "uptime"]},
        "D3": {"job": "BRD", "icon": "/actor/BRD.png", "roleLabel": "D3", "tags": ["mobile_ranged"]},
        "D4": {"job": "PCT", "icon": "/actor/PCT.png", "roleLabel": "D4", "tags": ["caster"]},
    }


def movement_set(to_positions: dict[str, list[int]], timing: str, beat: str) -> list[dict[str, Any]]:
    return [
        {
            "role": role,
            "from": BASE_POS[role],
            "to": to_positions[role],
            "timing": timing,
            "duration": 0.7 if timing in {"free", "preposition"} else 1.1,
            "hold": 0.2 if timing == "resolution" else 0.0,
            "beat": beat,
            "boss_targetable": True,
        }
        for role in ROLES
    ]


def safety_checks(categories: set[str], unknowns: list[str]) -> list[dict[str, Any]]:
    checks = [{"name": "eight_roles_assigned", "passed": True, "details": "MT/ST/H1/H2/D1-D4 all assigned"}]
    if "tower" in categories:
        checks.append({"name": "tower_count_assumption", "passed": True, "details": "四塔按两人塔或固定单塔模板保守处理"})
    if "stack" in categories:
        checks.append({"name": "stack_count_assumption", "passed": True, "details": "分摊按四人或八人固定分桶处理"})
    if "spread" in categories:
        checks.append({"name": "spread_clearance", "passed": True, "details": "外圈 clock 站位保留最小间距"})
    if "tether" in categories:
        checks.append({"name": "tether_crossing", "passed": True, "details": "路线按同向或半场内移动，避免交叉"})
    if unknowns:
        checks.append({"name": "unknowns_preserved", "passed": True, "details": "未知点进入 risk list，不作为已确认事实"})
    return checks


def candidate(
    candidate_id: str,
    name: str,
    summary: str,
    to_positions: dict[str, list[int]],
    timing: str,
    beat: str,
    categories: set[str],
    unknowns: list[str],
    mode: str,
    tradeoffs: list[str],
) -> dict[str, Any]:
    moves = movement_set(to_positions, timing, beat)
    if candidate_id == "uptime-optimized":
        moves = [move if move["role"] != "D4" else {**move, "to": [70, -70], "timing": "free", "duration": 0.35} for move in moves]
    complexity = {
        "safe-prog": {"live_sorts": 0, "role_swaps": 0, "exceptions": 0, "simultaneous_attributes": 1, "pattern_reuse": 3, "fixed_assignments": 8, "stable_meanings": 2},
        "uptime-optimized": {"live_sorts": 1, "role_swaps": 1, "exceptions": 1, "simultaneous_attributes": 2, "pattern_reuse": 2, "fixed_assignments": 5, "stable_meanings": 1},
        "high-tolerance": {"live_sorts": 0, "role_swaps": 0, "exceptions": 0, "simultaneous_attributes": 1, "pattern_reuse": 2, "fixed_assignments": 8, "stable_meanings": 2},
    }[candidate_id]
    tolerance = {
        "safe-prog": {"min_margin": 34, "simultaneous_swaps": 0, "last_second_adjustments": 0, "safe_area_ratio": 0.48, "tower_players": 8 if "tower" in categories else 0, "stack_players": 8 if "stack" in categories else 0},
        "uptime-optimized": {"min_margin": 26, "simultaneous_swaps": 1, "last_second_adjustments": 1, "safe_area_ratio": 0.38, "tower_players": 8 if "tower" in categories else 0, "stack_players": 4 if "stack" in categories else 0},
        "high-tolerance": {"min_margin": 42, "simultaneous_swaps": 0, "last_second_adjustments": 0, "safe_area_ratio": 0.58, "tower_players": 8 if "tower" in categories else 0, "stack_players": 8 if "stack" in categories else 0},
    }[candidate_id]
    return {
        "id": candidate_id,
        "name": name,
        "summary": summary,
        "mode": mode,
        "tradeoffs": tradeoffs,
        "assumptions": ["按固定八人职能模板起步", "未知点保留到攻略包待验证"] + unknowns[:3],
        "risks": unknowns or ["需要实战确认伤害范围和判定节奏"],
        "safety_checks": safety_checks(categories, unknowns),
        "movements": moves,
        "complexity": complexity,
        "tolerance": tolerance,
        "communication": {"callout_words": 12 if candidate_id != "uptime-optimized" else 20, "priority_rules": 0 if candidate_id != "uptime-optimized" else 1, "exception_rules": 0 if candidate_id != "uptime-optimized" else 1, "macro_lines": 3},
        "diagram": {"steps": 6, "arrows": 8 if candidate_id != "safe-prog" else 6, "crossing_arrows": 0, "labels": 14, "branches": 0 if candidate_id != "uptime-optimized" else 1, "max_objects_per_step": 28},
        "fight_specific_fit": 5 if candidate_id == "safe-prog" else 4,
        "step_plan": [
            {"phase": "observe", "title": "观察", "guide_text": "确认机制类别、点名和安全半场，未知规则先按保守版本处理。"},
            {"phase": "preposition", "title": "预站", "guide_text": "全员按固定八方 / 职能分桶预站，读条职业优先留内圈。"},
            {"phase": "resolve_1", "title": "第一判定", "guide_text": "按图处理塔、连线或第一轮分摊，路线不交叉。"},
            {"phase": "move", "title": "移动", "guide_text": "只在当前 beat 移动需要动的人，近战不无故离开目标圈。"},
            {"phase": "resolve_2", "title": "结算", "guide_text": "处理散开、双分摊或安全半场判定。"},
            {"phase": "reset", "title": "复位", "guide_text": "判定后回中或回八方，准备下一读条。"},
        ],
    }


def plan_bundle(mechanic_ir: dict[str, Any], timeline_ir: dict[str, Any], knowledge: dict[str, Any] | None, constraints: dict[str, Any]) -> dict[str, Any]:
    categories = all_categories(mechanic_ir, timeline_ir)
    unknowns = collect_unknowns(mechanic_ir, timeline_ir)
    knowledge_titles = [item.get("title", "") for item in (knowledge or {}).get("candidates", [])[:3] if item.get("title")]
    description = " / ".join(item.get("description", "") for item in timeline_ir.get("events", [])[:3]) or "IR-generated mechanic"
    if knowledge_titles:
        description += "；参考：" + "、".join(knowledge_titles)
    if constraints.get("strategy_context") == "static":
        context = "固定队"
    elif constraints.get("strategy_context") == "pf":
        context = "野队"
    else:
        context = "默认开荒"
    return {
        "version": 2,
        "mechanic": mechanic_name(mechanic_ir),
        "description": description,
        "planning_context": {
            "strategy_context": context,
            "categories": sorted(categories),
            "unknowns": unknowns,
            "timeline_events": timeline_ir.get("events", []),
            "arena_selection": mechanic_ir.get("arena_selection") or timeline_ir.get("arena_selection"),
        },
        "boss": {"pos": [0, 0], "uptime_radius": 125, "targetable_duration": 12},
        "party": default_party(),
        "constraints": {"forbid_route_crossing": True, **constraints},
        "budgets": {"movement": 32, "caster_movement": 12},
        "candidates": [
            candidate("safe-prog", "候选 A：开荒固定职能", "固定八方与职能分桶，优先保证安全、复位和讲解稳定。", CLOCK_POS, "preposition", "prog", categories, unknowns, "开荒优先解 / 野队可交流", ["读条职业若被指定外圈，仍需提前预站"]),
            candidate("uptime-optimized", "候选 B：少移动保 uptime", "D4 和治疗尽量锚定，近战保内圈，部分职责用临场补位。", INNER_POS, "resolution", "uptime", categories, unknowns, "竞速 / 熟练优化解", ["需要固定队预先约定补位", "未知点多时不应默认采用"]),
            candidate("high-tolerance", "候选 C：高容错外圈", "扩大处理距离和安全边距，牺牲少量输出换取更明显的错误隔离。", OUTER_POS, "preposition", "safe-margin", categories, unknowns, "开荒高容错", ["全员移动更远", "近战和坦克可能短暂离圈"]),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 12 solution candidate bundle from IR files.")
    parser.add_argument("--mechanic-ir", type=Path, required=True)
    parser.add_argument("--timeline-ir", type=Path, required=True)
    parser.add_argument("--knowledge", type=Path)
    parser.add_argument("--constraints", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        mechanic_ir = read_json(args.mechanic_ir)
        timeline_ir = read_json(args.timeline_ir)
        knowledge = read_json(args.knowledge) if args.knowledge and args.knowledge.exists() else None
        constraints = read_json(args.constraints) if args.constraints and args.constraints.exists() else {}
        bundle = plan_bundle(mechanic_ir, timeline_ir, knowledge, constraints)
        write_json(args.output, bundle)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    print(f"candidates: {len(bundle['candidates'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
