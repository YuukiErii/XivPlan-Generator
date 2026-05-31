#!/usr/bin/env python3
"""Build a multi-step XivPlan spec from a recommended Phase 12 solution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROLES = ("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4")
ROLE_DIR = {"MT": "N", "ST": "S", "H1": "W", "H2": "E", "D1": "NW", "D2": "NE", "D3": "SW", "D4": "SE"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def party_objects(distance: int = 108, positions: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    objects = []
    for role in ROLES:
        obj: dict[str, Any] = {"kind": "party", "key": role, "role": role, "pos": ROLE_DIR[role], "distance": distance}
        if positions and role in positions:
            obj["pos"] = positions[role]
        objects.append(obj)
    return objects


def pos_to_spec(value: Any) -> dict[str, float]:
    if not isinstance(value, list) or len(value) != 2:
        return {"x": 0, "y": 0}
    return {"x": float(value[0]), "y": float(value[1])}


def find_candidate(bundle: dict[str, Any], score_report: dict[str, Any] | None, candidate_id: str | None) -> dict[str, Any]:
    selected = candidate_id or (score_report or {}).get("recommended_candidate")
    candidates = {candidate.get("id"): candidate for candidate in bundle.get("candidates", [])}
    if selected not in candidates:
        selected = next(iter(candidates), None)
    if not selected:
        raise ValueError("no candidate available")
    return candidates[selected]


def build_steps(bundle: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    movement_targets = {move["role"]: pos_to_spec(move.get("to")) for move in candidate.get("movements", []) if move.get("role") in ROLES}
    categories = set(bundle.get("planning_context", {}).get("categories", []))
    unknowns = bundle.get("planning_context", {}).get("unknowns", [])
    steps: list[dict[str, Any]] = [
        {
            "title": "1 观察",
            "purpose": "展示机制信息和未知点。",
            "guide_text": "先确认机制读条、点名和安全半场；未知点按保守假设处理。",
            "checks": ["未知点已列入攻略包", "不要把 v0.1 草案当作最终打法"],
            "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}]
            + party_objects(108)
            + [{"kind": "label", "text": "保守假设" if unknowns else "信息已知", "pos": "N", "distance": 272}],
        },
        {
            "title": "2 预站",
            "purpose": "固定八人初始职责。",
            "guide_text": candidate.get("step_plan", [{}, {"guide_text": "按职能固定预站。"}])[1].get("guide_text", "按职能固定预站。"),
            "checks": ["八个职能都有初始站位", "读条职业优先少移动"],
            "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}]
            + party_objects(108)
            + [{"kind": "circle", "key": "safe-center", "pos": "center", "radius": 130, "color": "#8fd14f", "opacity": 18, "label": "内圈"}],
        },
        {
            "title": "3 第一判定",
            "purpose": "处理塔、连线或第一轮分摊。",
            "guide_text": "按固定分桶处理第一轮判定；路线不交叉，塔和分摊人数按图示确认。",
            "checks": ["路线不交叉", "塔/分摊人数与假设一致"],
            "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}] + party_objects(108) + first_resolution_objects(categories),
        },
        {
            "title": "4 移动",
            "purpose": "执行推荐候选的主要移动。",
            "guide_text": "只移动需要处理当前职责的人；近战保持目标圈附近，D4 和治疗尽量在自然窗口移动。",
            "checks": ["读条职业移动窗口已标注", "近战离圈时间最短"],
            "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}]
            + party_objects(108, movement_targets)
            + [
                {"kind": "arrow", "from": ROLE_DIR[role], "to": pos_to_spec(move.get("to")), "distance": 110, "height": 12}
                for role, move in ((m.get("role"), m) for m in candidate.get("movements", []))
                if role in ROLE_DIR
            ],
        },
        {
            "title": "5 结算",
            "purpose": "显示最终安全站位和判定范围。",
            "guide_text": "完成散开、双分摊或安全半场判定；出错时优先保持不撞线、不抢塔。",
            "checks": ["散开距离足够", "安全区/危险区不冲突"],
            "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}]
            + party_objects(108, movement_targets)
            + final_resolution_objects(categories),
        },
        {
            "title": "6 复位",
            "purpose": "判定结束后统一回到下一机制起点。",
            "guide_text": "结算后回中或回八方，保持下一读条前的复位节奏。",
            "checks": ["复位点明确", "下一机制起手位置明确"],
            "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}]
            + party_objects(92)
            + [{"kind": "stack", "key": "reset", "pos": "center", "radius": 74, "count": 8, "label": "复位"}],
        },
    ]
    return steps


def first_resolution_objects(categories: set[str]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if "tower" in categories:
        objects.extend(
            [
                {"kind": "tower", "key": "tower-n", "pos": "N", "distance": 190, "count": 2, "label": "T/H"},
                {"kind": "tower", "key": "tower-s", "pos": "S", "distance": 190, "count": 2, "label": "T/H"},
                {"kind": "tower", "key": "tower-e", "pos": "E", "distance": 190, "count": 2, "label": "DPS"},
                {"kind": "tower", "key": "tower-w", "pos": "W", "distance": 190, "count": 2, "label": "DPS"},
            ]
        )
    if "tether" in categories:
        objects.extend([{"kind": "arrow", "from": "NW", "to": "N", "distance": 205}, {"kind": "arrow", "from": "SE", "to": "S", "distance": 205}])
    if "stack" in categories:
        objects.append({"kind": "stack", "key": "stack-a", "pos": "W", "distance": 95, "radius": 58, "count": 4, "label": "A组"})
        objects.append({"kind": "stack", "key": "stack-b", "pos": "E", "distance": 95, "radius": 58, "count": 4, "label": "B组"})
    return objects or [{"kind": "circle", "key": "resolve-a", "pos": "center", "radius": 120, "label": "判定"}]


def final_resolution_objects(categories: set[str]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if "spread" in categories:
        for role, direction in ROLE_DIR.items():
            objects.append({"kind": "circle", "key": f"spread-{role}", "pos": direction, "distance": 190 if role.startswith("D") else 135, "radius": 34, "label": role})
    if "cleave" in categories:
        objects.append({"kind": "rect", "key": "danger-east", "pos": "E", "distance": 150, "width": 210, "height": 560, "color": "#d13438", "opacity": 24})
        objects.append({"kind": "polygon", "key": "safe-west", "pos": "W", "distance": 115, "radius": 125, "sides": 4, "color": "#8fd14f", "opacity": 28, "label": "安全"})
    if "stack" in categories and "spread" not in categories:
        objects.append({"kind": "stack", "key": "stack-final", "pos": "center", "radius": 74, "count": 8, "label": "八人"})
    return objects or [{"kind": "stack", "key": "resolve-final", "pos": "center", "radius": 74, "count": 8, "label": "结算"}]


def build_spec(bundle: dict[str, Any], score_report: dict[str, Any] | None, candidate_id: str | None) -> dict[str, Any]:
    candidate = find_candidate(bundle, score_report, candidate_id)
    return {
        "name": f"Phase 12：{bundle.get('mechanic', 'generated solution')} - {candidate.get('id')}",
        "style": "king-x-fru",
        "arena": {"preset": "default-circle"},
        "markerPresets": "cardinals",
        "metadata": {
            "source": "build_spec_from_solution.py",
            "recommended_candidate": candidate.get("id"),
            "mode": candidate.get("mode"),
            "assumptions": candidate.get("assumptions", []),
            "risks": candidate.get("risks", []),
        },
        "steps": build_steps(bundle, candidate),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a recommended Phase 12 solution candidate into scene spec JSON.")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--scores", type=Path)
    parser.add_argument("--candidate-id")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        bundle = read_json(args.bundle)
        scores = read_json(args.scores) if args.scores else None
        spec = build_spec(bundle, scores, args.candidate_id)
        write_json(args.output, spec)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    print(f"steps: {len(spec['steps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
