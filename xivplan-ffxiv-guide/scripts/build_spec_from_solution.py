#!/usr/bin/env python3
"""Build a multi-step XivPlan spec from a recommended Phase 12 solution."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROLES = ("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4")
ROLE_DIR = {"MT": "N", "ST": "S", "H1": "W", "H2": "E", "D1": "NW", "D2": "NE", "D3": "SW", "D4": "SE"}
DIRECTION_DEGREES = {"E": 0, "NE": 45, "N": 90, "NW": 135, "W": 180, "SW": 225, "S": 270, "SE": 315}
ALL_ROLES = list(ROLES)
TH_ROLES = ["MT", "ST", "H1", "H2"]
DPS_ROLES = ["D1", "D2", "D3", "D4"]


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


def direction_point(direction: str, distance: float = 110) -> tuple[float, float]:
    radians = math.radians(DIRECTION_DEGREES[direction])
    return math.cos(radians) * distance, math.sin(radians) * distance


def movement_arrow(role: str, move: dict[str, Any]) -> dict[str, Any] | None:
    target = pos_to_spec(move.get("to"))
    start = direction_point(ROLE_DIR[role])
    end = (target["x"], target["y"])
    if math.dist(start, end) < 90:
        return None
    return {"kind": "arrow", "key": f"move-{role.lower()}", "from": ROLE_DIR[role], "to": target, "distance": 110, "arrowStyle": "movement", "endGap": 34}


def has_flow_object(objects: list[dict[str, Any]]) -> bool:
    return any(obj.get("kind") in {"arrow", "path", "polyline", "tether", "link"} for obj in objects if isinstance(obj, dict))


def default_flow_object(flow_kind: str) -> dict[str, Any]:
    if flow_kind == "reset":
        return {
            "kind": "arrow",
            "key": "auto-reset-flow",
            "from": [220, -20],
            "to": [145, -20],
            "arrowStyle": "reset",
            "flowLabel": "auto-reset",
        }
    if flow_kind == "knockback":
        return {
            "kind": "arrow",
            "key": "auto-knockback-flow",
            "from": "center",
            "to": "N",
            "distance": 220,
            "arrowStyle": "knockback",
            "allowDangerCrossing": True,
            "endGap": 58,
            "flowLabel": "auto-knockback",
        }
    if flow_kind == "bait":
        return {
            "kind": "arrow",
            "key": "auto-bait-flow",
            "from": [-210, 145],
            "to": [-135, 145],
            "arrowStyle": "bait",
            "flowLabel": "auto-bait",
        }
    if flow_kind == "forbidden":
        return {
            "kind": "arrow",
            "key": "auto-forbidden-flow",
            "from": [-170, 0],
            "to": [170, 0],
            "arrowStyle": "forbidden",
            "routeCheck": False,
            "flowLabel": "auto-forbidden",
        }
    return {
        "kind": "polyline",
        "key": "auto-movement-flow",
        "from": [-205, -150],
        "waypoints": [[-170, -95]],
        "to": [-128, -66],
        "arrowStyle": "movement",
        "flowLabel": "auto-movement",
    }


def infer_flow_kind(phase: str, objects: list[dict[str, Any]], explicit: str | None = None) -> str:
    if explicit:
        return explicit
    kinds = {str(obj.get("kind", "")).lower() for obj in objects if isinstance(obj, dict)}
    if "knockback" in kinds or "line_knockback" in kinds or "lineknockback" in kinds:
        return "knockback"
    if "tether" in kinds or "link" in kinds:
        return "bait"
    if "forbidden" in kinds:
        return "forbidden"
    if phase == "reset":
        return "reset"
    return "movement"


def requires_movement(phase: str, objects: list[dict[str, Any]], explicit: bool | None = None) -> bool:
    if explicit is not None:
        return explicit
    if phase in {"move", "reset"}:
        return True
    return any(str(obj.get("arrowStyle", "")).lower() in {"bait", "knockback", "forbidden"} for obj in objects if isinstance(obj, dict))


def find_candidate(bundle: dict[str, Any], score_report: dict[str, Any] | None, candidate_id: str | None) -> dict[str, Any]:
    selected = candidate_id or (score_report or {}).get("recommended_candidate")
    candidates = {candidate.get("id"): candidate for candidate in bundle.get("candidates", [])}
    if selected not in candidates:
        selected = next(iter(candidates), None)
    if not selected:
        raise ValueError("no candidate available")
    return candidates[selected]


def category_set(bundle: dict[str, Any]) -> set[str]:
    categories = {str(item) for item in bundle.get("planning_context", {}).get("categories", [])}
    if "light-rampant-like" in categories:
        categories.update({"tower", "tether", "spread"})
    if "tile-platform" in categories:
        categories.add("tile")
    if "sequence" in categories:
        categories.add("case-based")
    return categories


def step(
    title: str,
    phase: str,
    purpose: str,
    guide_text: str,
    checks: list[str],
    visual_focus: str,
    required_roles: list[str],
    reset_state: str,
    objects: list[dict[str, Any]] | None = None,
    *,
    focus_roles: list[str] | None = None,
    inherit: bool | None = None,
    updates: dict[str, Any] | None = None,
    remove: list[str] | None = None,
    movement_required: bool | None = None,
    flow_kind: str | None = None,
) -> dict[str, Any]:
    objects = objects or []
    inferred_flow_kind = infer_flow_kind(phase, objects, flow_kind)
    result: dict[str, Any] = {
        "title": title,
        "storyboard_phase": phase,
        "movement_required": requires_movement(phase, objects, movement_required),
        "flow_kind": inferred_flow_kind,
        "purpose": purpose,
        "guide_text": guide_text,
        "checks": checks,
        "visual_focus": visual_focus,
        "required_roles": required_roles,
        "reset_state": reset_state,
        "objects": objects,
    }
    if focus_roles:
        result["focusRoles"] = focus_roles
    if inherit is not None:
        result["inherit"] = inherit
    if updates:
        result["updates"] = updates
    if remove:
        result["remove"] = remove
    return result


def observation_step(unknowns: list[str]) -> dict[str, Any]:
    callout = "保守假设" if unknowns else "信息已知"
    return step(
        "1 观察与信息确认",
        "observe",
        "展示机制读条、未知点和全员默认站位。",
        "先确认机制类别、点名和安全半场；未知点按保守假设处理，不把草案当作最终打法。",
        ["未知点已列入攻略包", "八人、Boss、标点都可见"],
        "机制信息、Boss 中心、八人初始上下文",
        ALL_ROLES,
        "尚未移动，保持八方起手。",
        [
            {"kind": "circle", "key": "read-source-ring", "pos": "center", "radius": 104, "color": "#ffb900", "opacity": 18},
            {"kind": "label", "key": "info-state", "text": callout, "pos": [0, -210]},
        ],
    )


def preposition_step(candidate: dict[str, Any]) -> dict[str, Any]:
    guide_text = candidate.get("step_plan", [{}, {"guide_text": "按职能固定预站。"}])[1].get("guide_text", "按职能固定预站。")
    return step(
        "2 固定预站",
        "preposition",
        "固定八人初始职责，给后续模板提供稳定起点。",
        guide_text,
        ["八个职能都有初始站位", "读条职业优先少移动"],
        "职能八方、内圈安全锚点",
        ALL_ROLES,
        "预站完成后等待第一轮读条。",
        [{"kind": "circle", "key": "safe-center", "pos": "center", "radius": 128, "color": "#8fd14f", "opacity": 18, "label": "内圈"}],
    )


def tower_steps() -> list[dict[str, Any]]:
    towers = [
        {"kind": "tower", "key": "tower-n", "pos": "N", "distance": 190, "count": 2, "label": "T/H"},
        {"kind": "tower", "key": "tower-s", "pos": "S", "distance": 190, "count": 2, "label": "T/H"},
        {"kind": "tower", "key": "tower-e", "pos": "E", "distance": 190, "count": 2, "label": "DPS"},
        {"kind": "tower", "key": "tower-w", "pos": "W", "distance": 190, "count": 2, "label": "DPS"},
    ]
    return [
        step(
            "塔出现",
            "resolve",
            "把塔位和每塔人数单独展示，避免职责和移动混在一张图里。",
            "先读四座塔的位置和人数，按固定职能分桶处理。",
            ["塔位清楚", "每塔人数清楚"],
            "塔位、塔人数、职能分桶",
            ALL_ROLES,
            "读塔后不急动，等待入塔提示。",
            towers,
        ),
        step(
            "入塔职责",
            "move",
            "显示每组进入对应塔位的移动方向。",
            "T/H 处理南北塔，DPS 处理东西塔；移动路线短且不穿中心。",
            ["入塔路线不交叉", "每塔至少标明职责组"],
            "入塔路线和当前行动组",
            ALL_ROLES,
            "入塔后保持到判定结束。",
            towers
            + [
                {"kind": "arrow", "key": "tower-mt", "from": [0, 44], "to": [0, 190], "arrowStyle": "movement", "endGap": 44},
                {"kind": "arrow", "key": "tower-st", "from": [0, -44], "to": [0, -190], "arrowStyle": "movement", "endGap": 44},
                {"kind": "arrow", "key": "tower-d2", "from": [44, 0], "to": [190, 0], "arrowStyle": "movement", "endGap": 44},
                {"kind": "arrow", "key": "tower-d1", "from": [-44, 0], "to": [-190, 0], "arrowStyle": "movement", "endGap": 44},
            ],
            focus_roles=ALL_ROLES,
        ),
    ]


def stack_steps() -> list[dict[str, Any]]:
    return [
        step(
            "分摊目标确认",
            "resolve",
            "拆出分摊人数和分组，不和散开或塔判定混读。",
            "A/B 两组各自集合，若实际点名不同，以点名者为中心微调。",
            ["分摊人数明确", "分组边界明确"],
            "分摊圈、分组标签",
            ALL_ROLES,
            "分摊后准备散开或回中。",
            [
                {"kind": "stack", "key": "stack-a", "pos": "W", "distance": 95, "radius": 58, "count": 4, "label": "A组"},
                {"kind": "stack", "key": "stack-b", "pos": "E", "distance": 95, "radius": 58, "count": 4, "label": "B组"},
            ],
        )
    ]


def spread_circle_objects() -> list[dict[str, Any]]:
    label_pos = {
        "MT": [0, 188],
        "ST": [0, -188],
        "H1": [-188, 0],
        "H2": [188, 0],
        "D1": [-235, 222],
        "D2": [235, 222],
        "D3": [-235, -222],
        "D4": [235, -222],
    }
    return [
        {
            "kind": "circle",
            "key": f"spread-{role}",
            "pos": direction,
            "distance": 190 if role.startswith("D") else 135,
            "radius": 34,
            "label": role,
            "labelPos": label_pos[role],
            "labelFontSize": 14,
        }
        for role, direction in ROLE_DIR.items()
    ]


def spread_steps() -> list[dict[str, Any]]:
    return [
        step(
            "散开点名",
            "resolve",
            "把每个角色的散开落点从其他判定中拆出来。",
            "按八方或指定 clock 散开，DPS 外圈、T/H 内圈，保持最小间距。",
            ["八个散开点不重叠", "远近职责没有互抢位置"],
            "散开圈、角色标签",
            ALL_ROLES,
            "散开判定后立刻看复位箭头。",
            spread_circle_objects(),
        )
    ]


def tether_steps() -> list[dict[str, Any]]:
    return [
        step(
            "连线出现",
            "observe",
            "把连线方向和不能交叉的关系单独展示。",
            "先读连线端点，同半场拉开；不要横穿 Boss 圈。",
            ["连线端点清楚", "禁止交叉已说明"],
            "连线端点、半场边界",
            DPS_ROLES,
            "读线后等待拉线路线。",
            [
                {"kind": "circle", "key": "tether-source-ring", "pos": "center", "radius": 128, "color": "#ffb900", "opacity": 18},
                {"kind": "arrow", "key": "tether-nw", "from": "NW", "to": "N", "distance": 205, "arrowStyle": "bait", "endGap": 40},
                {"kind": "arrow", "key": "tether-se", "from": "SE", "to": "S", "distance": 205, "arrowStyle": "bait", "endGap": 40},
            ],
            focus_roles=DPS_ROLES,
        ),
        step(
            "拉线方向",
            "move",
            "显示拉线者的安全移动路径。",
            "拉线者沿同侧外圈移动，线不交叉；非拉线者保留上下文但降低存在感。",
            ["拉线方向与 guide_text 一致", "箭头头部不压玩家"],
            "拉线箭头、外圈移动方向",
            DPS_ROLES,
            "拉线完成后等判定，再回中。",
            [
                {"kind": "circle", "key": "tether-safe-ring", "pos": "center", "radius": 172, "color": "#8fd14f", "opacity": 14},
                {"kind": "polyline", "key": "tether-route-left", "from": "NW", "waypoints": [[-175, 45]], "to": "W", "distance": 190, "arrowStyle": "movement", "endGap": 42},
                {"kind": "polyline", "key": "tether-route-right", "from": "SE", "waypoints": [[175, -45]], "to": "E", "distance": 190, "arrowStyle": "movement", "endGap": 42},
            ],
            focus_roles=DPS_ROLES,
        ),
    ]


def knockback_steps() -> list[dict[str, Any]]:
    return [
        step(
            "击退源与预站",
            "preposition",
            "先画击退源和防击退/落点选择。",
            "以中心击退源为基准预站，确认是否开防击退；不开则对准安全落点。",
            ["击退源可见", "落点不在危险区"],
            "击退源、预站点、安全落点",
            ALL_ROLES,
            "预站后等击退结算。",
            [
                {"kind": "knockback", "key": "kb-source", "pos": "center", "radius": 82, "color": "#d13438", "opacity": 35, "label": "击退源"},
                {"kind": "safe_circle", "key": "kb-safe", "pos": "N", "distance": 220, "radius": 70, "label": "落点"},
            ],
        ),
        step(
            "击退落点",
            "move",
            "把强制位移方向和最终落点拆成独立画面。",
            "击退方向从源点指向安全区；被击退后先站稳，再处理下一判定。",
            ["击退箭头起点在机制源", "箭头终点不压玩家"],
            "宽击退箭头、落点安全区",
            ALL_ROLES,
            "落点稳定后进入结算或复位。",
            [{"kind": "arrow", "key": "kb-arrow", "from": "center", "to": "N", "distance": 220, "arrowStyle": "knockback", "allowDangerCrossing": True, "endGap": 58}],
        ),
    ]


def dance_steps() -> list[dict[str, Any]]:
    return [
        step(
            "Case 读取",
            "observe",
            "把分支条件作为独立读取画面，避免边读边移动。",
            "确认当前 case 后只执行对应路线；没有被点名者保持默认位。",
            ["case 标签清楚", "未确认分支不画成事实"],
            "case 标签、当前读法",
            ALL_ROLES,
            "读 case 后进入第一拍路线。",
            [{"kind": "label", "key": "case-label", "text": "Case A / B", "pos": [0, 205]}],
        ),
        step(
            "第一拍路线",
            "move",
            "显示舞蹈机制第一拍的路线，不和后续拍混在一起。",
            "当前行动者按箭头移动，其余人保留原位等待下一拍。",
            ["路线不交叉", "行动者明确"],
            "第一拍移动箭头",
            ["MT", "ST"],
            "第一拍结束后停在半场边缘。",
            [
                {"kind": "polyline", "key": "dance-mt", "from": "N", "waypoints": [[-75, 165]], "to": "NW", "distance": 135, "arrowStyle": "movement", "endGap": 42},
                {"kind": "polyline", "key": "dance-st", "from": "S", "waypoints": [[75, -165]], "to": "SE", "distance": 135, "arrowStyle": "movement", "endGap": 42},
            ],
            focus_roles=["MT", "ST"],
        ),
    ]


def tile_steps() -> list[dict[str, Any]]:
    return [
        step(
            "地板状态",
            "observe",
            "先展示哪些格子可用，避免路线图缺少场地状态。",
            "红色格子不可站，绿色格子为下一步安全路线。",
            ["可用格和危险格分色", "场地状态先于人物移动"],
            "安全格、危险格、平台边界",
            ALL_ROLES,
            "确认地板后再移动。",
            [
                {"kind": "rect", "key": "tile-danger", "pos": "E", "distance": 75, "width": 120, "height": 360, "color": "#d13438", "opacity": 26},
                {"kind": "rect", "key": "tile-safe", "pos": "W", "distance": 75, "width": 120, "height": 360, "color": "#8fd14f", "opacity": 28, "label": "安全格"},
            ],
        ),
        step(
            "格子移动",
            "move",
            "显示跨格移动路线，确保不穿过不可用地板。",
            "全员沿安全格一侧移动，避免穿越红色格。",
            ["路线绕过危险格", "终点在可用平台"],
            "跨格路线、安全格边界",
            ALL_ROLES,
            "抵达安全格后等待结算。",
            [{"kind": "polyline", "key": "tile-route", "from": "S", "waypoints": [[-105, -70], [-105, 70]], "to": "N", "distance": 165, "arrowStyle": "movement", "endGap": 48}],
        ),
    ]


def movement_step(candidate: dict[str, Any], movement_targets: dict[str, Any], movement_arrows: list[dict[str, Any]]) -> dict[str, Any]:
    focus_roles = [move.get("role") for move in candidate.get("movements", []) if move.get("role") in ROLES]
    return step(
        "主要移动",
        "move",
        "执行推荐候选的主要移动窗口。",
        "只移动需要处理当前职责的人；近战保持目标圈附近，D4 和治疗尽量在自然窗口移动。",
        ["读条职业移动窗口已标注", "近战离圈时间最短"],
        "当前行动者、主移动路线、目标落点",
        focus_roles or ALL_ROLES,
        "移动完成后进入结算画面。",
        party_objects(108, movement_targets)
        + [
            {"kind": "circle", "key": "movement-window", "pos": "center", "radius": 146, "color": "#8fd14f", "opacity": 14},
        ]
        + movement_arrows,
        focus_roles=focus_roles or None,
    )


def final_resolution_step(categories: set[str], movement_targets: dict[str, Any]) -> dict[str, Any]:
    return step(
        "最终判定",
        "resolve",
        "显示最后的安全站位和判定范围。",
        "完成散开、双分摊或安全半场判定；出错时优先保持不撞线、不抢塔。",
        ["散开距离足够", "安全区/危险区不冲突"],
        "最终站位、判定范围、安全/危险区",
        ALL_ROLES,
        "判定后立刻回中或回八方。",
        party_objects(108, movement_targets) + final_resolution_objects(categories),
    )


def reset_step() -> dict[str, Any]:
    return step(
        "复位与下一轮起手",
        "reset",
        "判定结束后统一回到下一机制起点。",
        "结算后回中或回八方，保持下一读条前的复位节奏。",
        ["复位点明确", "下一机制起手位置明确"],
        "复位集合点、下一轮起手方向",
        ALL_ROLES,
        "回中集合，准备下一机制。",
        party_objects(92)
        + [
            {"kind": "stack", "key": "reset", "pos": "center", "radius": 74, "count": 8, "label": "复位"},
            {"kind": "arrow", "key": "reset-east", "from": [220, -20], "to": [145, -20], "arrowStyle": "reset"},
            {"kind": "arrow", "key": "reset-west", "from": [-220, 20], "to": [-145, 20], "arrowStyle": "reset"},
        ],
        flow_kind="reset",
    )


def ensure_flow_objects(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in steps:
        objects = item.setdefault("objects", [])
        if not isinstance(objects, list):
            continue
        if item.get("movement_required") and not has_flow_object(objects):
            flow_kind = infer_flow_kind(str(item.get("storyboard_phase", "")), objects, str(item.get("flow_kind", "")) or None)
            objects.append(default_flow_object(flow_kind))
            item["flow_kind"] = flow_kind
    return steps


def storyboard_templates(categories: set[str]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    if "tile" in categories or "tile-platform" in categories:
        templates.extend(tile_steps())
    if "case-based" in categories or "sequence" in categories:
        templates.extend(dance_steps())
    if "knockback" in categories:
        templates.extend(knockback_steps())
    if "tower" in categories:
        templates.extend(tower_steps())
    if "tether" in categories:
        templates.extend(tether_steps())
    if "stack" in categories:
        templates.extend(stack_steps())
    if "spread" in categories:
        templates.extend(spread_steps())
    if not templates:
        templates.append(
            step(
                "机制判定",
                "resolve",
                "显示当前机制的主要判定范围。",
                "按图确认安全区和危险区，再进入移动或复位。",
                ["安全区可见", "危险区可见"],
                "主要判定范围",
                ALL_ROLES,
                "判定后进入复位。",
                [{"kind": "circle", "key": "resolve-a", "pos": "center", "radius": 120, "label": "判定"}],
            )
        )
    return templates


def cap_storyboard_steps(steps: list[dict[str, Any]], max_steps: int = 14) -> list[dict[str, Any]]:
    if len(steps) <= max_steps:
        return steps
    required_tail = steps[-2:]
    middle = steps[2:-2]
    keep_middle = middle[: max_steps - 4]
    return steps[:2] + keep_middle + required_tail


def renumber_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    renumbered = []
    for index, item in enumerate(steps, start=1):
        updated = dict(item)
        title = str(updated.get("title", f"Step {index}"))
        title = title.split(" ", 1)[1] if title[:2].strip().isdigit() and " " in title else title
        updated["title"] = f"{index} {title}"
        renumbered.append(updated)
    return renumbered


def build_steps(bundle: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    movement_targets = {move["role"]: pos_to_spec(move.get("to")) for move in candidate.get("movements", []) if move.get("role") in ROLES}
    movement_arrows = [
        arrow
        for role, move in ((m.get("role"), m) for m in candidate.get("movements", []))
        if role in ROLE_DIR
        for arrow in [movement_arrow(role, move)]
        if arrow is not None
    ]
    categories = category_set(bundle)
    unknowns = bundle.get("planning_context", {}).get("unknowns", [])
    steps = [observation_step(unknowns), preposition_step(candidate)]
    steps.extend(storyboard_templates(categories))
    steps.append(movement_step(candidate, movement_targets, movement_arrows))
    steps.append(final_resolution_step(categories, movement_targets))
    steps.append(reset_step())
    return renumber_steps(ensure_flow_objects(cap_storyboard_steps(steps)))


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
        objects.extend(
            [
                {"kind": "arrow", "from": "NW", "to": "N", "distance": 205, "arrowStyle": "bait", "endGap": 40},
                {"kind": "arrow", "from": "SE", "to": "S", "distance": 205, "arrowStyle": "bait", "endGap": 40},
            ]
        )
    if "stack" in categories:
        objects.append({"kind": "stack", "key": "stack-a", "pos": "W", "distance": 95, "radius": 58, "count": 4, "label": "A组"})
        objects.append({"kind": "stack", "key": "stack-b", "pos": "E", "distance": 95, "radius": 58, "count": 4, "label": "B组"})
    return objects or [{"kind": "circle", "key": "resolve-a", "pos": "center", "radius": 120, "label": "判定"}]


def final_resolution_objects(categories: set[str]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if "spread" in categories:
        objects.extend(spread_circle_objects())
    if "cleave" in categories:
        objects.append({"kind": "rect", "key": "danger-east", "pos": "E", "distance": 150, "width": 210, "height": 560, "color": "#d13438", "opacity": 24})
        objects.append({"kind": "polygon", "key": "safe-west", "pos": "W", "distance": 115, "radius": 125, "sides": 4, "color": "#8fd14f", "opacity": 28, "label": "安全"})
    if "stack" in categories and "spread" not in categories:
        objects.append({"kind": "stack", "key": "stack-final", "pos": "center", "radius": 74, "count": 8, "label": "八人"})
    return objects or [{"kind": "stack", "key": "resolve-final", "pos": "center", "radius": 74, "count": 8, "label": "结算"}]


def build_spec(bundle: dict[str, Any], score_report: dict[str, Any] | None, candidate_id: str | None) -> dict[str, Any]:
    candidate = find_candidate(bundle, score_report, candidate_id)
    arena_selection = bundle.get("planning_context", {}).get("arena_selection")
    if not isinstance(arena_selection, dict):
        arena_selection = {
            "preset": "default-circle",
            "source": "default-fallback",
            "reason": "No arena selection was carried by the solution bundle.",
        }
    arena = {
        "preset": arena_selection.get("preset", "default-circle"),
        "source": arena_selection.get("source", "default-fallback"),
        "sourceReason": arena_selection.get("reason", ""),
    }
    return {
        "name": f"Phase 12：{bundle.get('mechanic', 'generated solution')} - {candidate.get('id')}",
        "style": "king-x-fru",
        "scene_contract": {
            "require_full_party_each_step": True,
            "require_enemy_each_step": True,
            "require_waymarks_each_step": True,
            "allow_partial_observation": False,
        },
        "arena": arena,
        "markerPresets": "cardinals",
        "metadata": {
            "source": "build_spec_from_solution.py",
            "storyboard_generator": "phase-f-v2",
            "storyboard_policy": "category-template-chain",
            "arena_selection": arena_selection,
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
