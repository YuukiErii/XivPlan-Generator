#!/usr/bin/env python3
"""Build a basic XivPlan .xivplan scene from a compact mechanic spec JSON."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_SIZE = 600
DEFAULT_PADDING = 120
DEFAULT_OBJECT_DISTANCE = 220
DEFAULT_PLAYER_SIZE = 32

ROLE_IMAGES = {
    "MT": "/actor/tank.png",
    "ST": "/actor/tank.png",
    "H1": "/actor/healer.png",
    "H2": "/actor/healer.png",
    "D1": "/actor/dps.png",
    "D2": "/actor/dps.png",
    "D3": "/actor/dps.png",
    "D4": "/actor/dps.png",
    "T": "/actor/tank.png",
    "H": "/actor/healer.png",
    "DPS": "/actor/dps.png",
}

DIRECTION_DEGREES = {
    "E": 0,
    "NE": 45,
    "N": 90,
    "NW": 135,
    "W": 180,
    "SW": 225,
    "S": 270,
    "SE": 315,
}


class BuildError(ValueError):
    """Spec cannot be converted into a XivPlan scene."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_number(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)):
        raise BuildError(f"{name} must be a number")
    return float(value)


def resolve_pos(value: Any, distance: float = DEFAULT_OBJECT_DISTANCE) -> tuple[float, float]:
    if value is None or value == "center":
        return 0.0, 0.0
    if isinstance(value, list) and len(value) == 2:
        return as_number(value[0], "position x"), as_number(value[1], "position y")
    if isinstance(value, dict):
        if "x" in value and "y" in value:
            return as_number(value["x"], "position x"), as_number(value["y"], "position y")
        if "dir" in value:
            return resolve_pos(value["dir"], as_number(value.get("distance", distance), "distance"))
    if isinstance(value, str):
        key = value.upper()
        if key in DIRECTION_DEGREES:
            radians = math.radians(DIRECTION_DEGREES[key])
            return round(math.cos(radians) * distance, 3), round(math.sin(radians) * distance, 3)
    raise BuildError(f"unsupported position: {value!r}")


def with_offset(pos: tuple[float, float], offset: Any) -> tuple[float, float]:
    if offset is None:
        return pos
    if not isinstance(offset, list) or len(offset) != 2:
        raise BuildError("offset must be [x, y]")
    return pos[0] + as_number(offset[0], "offset x"), pos[1] + as_number(offset[1], "offset y")


def pos_from_obj(obj: dict[str, Any]) -> tuple[float, float]:
    distance = as_number(obj.get("distance", DEFAULT_OBJECT_DISTANCE), "distance")
    return with_offset(resolve_pos(obj.get("pos", "center"), distance), obj.get("offset"))


def rotation_from_vector(start: tuple[float, float], end: tuple[float, float]) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    # XivPlan scene y points north, while canvas y points down. This keeps north-bound arrows visually upward.
    return round(math.degrees(math.atan2(-dy, dx)), 3)


def base_arena(spec: dict[str, Any]) -> dict[str, Any]:
    arena = spec.get("arena", {})
    if not isinstance(arena, dict):
        raise BuildError("arena must be an object")

    shape = arena.get("shape", "circle")
    size = int(arena.get("size", arena.get("width", DEFAULT_SIZE)))
    width = int(arena.get("width", size))
    height = int(arena.get("height", size))

    if shape == "circle":
        grid = arena.get("grid", {"type": "radial", "angularDivs": 8, "radialDivs": 2})
    elif shape == "rectangle":
        grid = arena.get("grid", {"type": "rectangle", "rows": 4, "columns": 4})
    else:
        grid = arena.get("grid", {"type": "none"})

    return {
        "shape": shape,
        "width": width,
        "height": height,
        "padding": int(arena.get("padding", DEFAULT_PADDING)),
        "grid": grid,
    }


def add_common(obj: dict[str, Any], spec_obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    obj["id"] = obj_id
    obj["opacity"] = int(spec_obj.get("opacity", obj.get("opacity", 100)))
    if spec_obj.get("hide"):
        obj["hide"] = True
    return obj


def make_boss(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "enemy",
            "name": obj.get("name", "Boss"),
            "icon": obj.get("icon", "/actor/enemy.png"),
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 52)),
            "rotation": int(obj.get("rotation", 180)),
            "ring": obj.get("ring", "dir"),
            "color": obj.get("color", "#d13438"),
            "opacity": 100,
        },
        obj,
        obj_id,
    )


def make_party(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    role = obj.get("role") or obj.get("name") or "Player"
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "party",
            "name": role,
            "image": obj.get("image", ROLE_IMAGES.get(str(role).upper(), "/actor/any.png")),
            "x": x,
            "y": y,
            "width": int(obj.get("width", DEFAULT_PLAYER_SIZE)),
            "height": int(obj.get("height", DEFAULT_PLAYER_SIZE)),
            "rotation": int(obj.get("rotation", 0)),
            "opacity": 100,
        },
        obj,
        obj_id,
    )


def make_tower(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "tower",
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 42)),
            "count": int(obj.get("count", 1)),
            "color": obj.get("color", "#bae3ff"),
            "opacity": 70,
        },
        obj,
        obj_id,
    )


def make_circle(obj: dict[str, Any], obj_id: int, obj_type: str = "circle") -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    color = obj.get("color", "#d13438" if obj.get("kind") in {"danger", "danger_circle"} else "#ffb900")
    result = {
        "type": obj_type,
        "x": x,
        "y": y,
        "radius": int(obj.get("radius", 60)),
        "color": color,
        "opacity": int(obj.get("opacity", 45)),
    }
    if obj.get("hollow", True):
        result["hollow"] = True
    return add_common(result, obj, obj_id)


def make_stack(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "stack",
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 70)),
            "count": int(obj.get("count", 4)),
            "color": obj.get("color", "#8fd14f"),
            "opacity": 55,
        },
        obj,
        obj_id,
    )


def make_text(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "text",
            "text": obj.get("text", obj.get("label", "")),
            "x": x,
            "y": y,
            "rotation": int(obj.get("rotation", 0)),
            "color": obj.get("color", "#ffffff"),
            "stroke": obj.get("stroke", "#000000"),
            "style": obj.get("style", "outline"),
            "fontSize": int(obj.get("fontSize", 18)),
            "align": obj.get("align", "center"),
            "opacity": 100,
        },
        obj,
        obj_id,
    )


def make_line(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "line",
            "x": x,
            "y": y,
            "length": int(obj.get("length", 500)),
            "width": int(obj.get("width", 80)),
            "rotation": float(obj.get("rotation", 0)),
            "color": obj.get("color", "#d13438"),
            "opacity": int(obj.get("opacity", 45)),
        },
        obj,
        obj_id,
    )


def make_cone(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "cone",
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 280)),
            "coneAngle": int(obj.get("coneAngle", 90)),
            "rotation": float(obj.get("rotation", 0)),
            "color": obj.get("color", "#d13438"),
            "opacity": int(obj.get("opacity", 45)),
        },
        obj,
        obj_id,
    )


def make_arrow(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    start = resolve_pos(obj.get("from", obj.get("start", "center")), as_number(obj.get("distance", DEFAULT_OBJECT_DISTANCE), "distance"))
    end = resolve_pos(obj.get("to", obj.get("end", "N")), as_number(obj.get("distance", DEFAULT_OBJECT_DISTANCE), "distance"))
    start = with_offset(start, obj.get("startOffset"))
    end = with_offset(end, obj.get("endOffset"))
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    length = math.dist(start, end)
    return add_common(
        {
            "type": "arrow",
            "x": round(mid[0], 3),
            "y": round(mid[1], 3),
            "width": int(obj.get("width", max(length, 1))),
            "height": int(obj.get("height", 20)),
            "rotation": float(obj.get("rotation", rotation_from_vector(start, end))),
            "color": obj.get("color", "#0078d4"),
            "opacity": 100,
            "arrowEnd": obj.get("arrowEnd", True),
        },
        obj,
        obj_id,
    )


def object_key(spec_obj: dict[str, Any]) -> str | None:
    for key in ("key", "role", "name"):
        value = spec_obj.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def build_step(step: dict[str, Any], next_id: int) -> tuple[dict[str, Any], int]:
    if not isinstance(step, dict):
        raise BuildError("each step must be an object")
    objects_spec = step.get("objects", [])
    if not isinstance(objects_spec, list):
        raise BuildError("step.objects must be a list")

    objects: list[dict[str, Any]] = []
    refs: dict[str, int] = {}
    deferred_tethers: list[dict[str, Any]] = []

    for spec_obj in objects_spec:
        if not isinstance(spec_obj, dict):
            raise BuildError("each object spec must be an object")
        kind = spec_obj.get("kind")
        if kind in {"tether", "link"}:
            deferred_tethers.append(spec_obj)
            continue

        if kind == "boss":
            built = make_boss(spec_obj, next_id)
        elif kind == "party":
            built = make_party(spec_obj, next_id)
        elif kind == "tower":
            built = make_tower(spec_obj, next_id)
        elif kind in {"stack", "spread_stack"}:
            built = make_stack(spec_obj, next_id)
        elif kind in {"circle", "danger", "danger_circle", "safe", "safe_circle"}:
            built = make_circle(spec_obj, next_id)
        elif kind == "knockback":
            built = make_circle(spec_obj, next_id, "knockback")
        elif kind in {"text", "label"}:
            built = make_text(spec_obj, next_id)
        elif kind == "line":
            built = make_line(spec_obj, next_id)
        elif kind == "cone":
            built = make_cone(spec_obj, next_id)
        elif kind == "arrow":
            built = make_arrow(spec_obj, next_id)
        else:
            raise BuildError(f"unsupported object kind: {kind!r}")

        objects.append(built)
        ref = object_key(spec_obj)
        if ref:
            refs[ref] = next_id
        if spec_obj.get("label") and kind not in {"text", "label"}:
            label_obj = {
                "kind": "text",
                "text": spec_obj["label"],
                "pos": spec_obj.get("labelPos", spec_obj.get("pos", "center")),
                "distance": spec_obj.get("labelDistance", spec_obj.get("distance", DEFAULT_OBJECT_DISTANCE + 48)),
                "offset": spec_obj.get("labelOffset"),
                "fontSize": spec_obj.get("labelFontSize", 16),
            }
            objects.append(make_text(label_obj, next_id + 1))
            next_id += 1
        next_id += 1

    for spec_obj in deferred_tethers:
        start = spec_obj.get("start")
        end = spec_obj.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            raise BuildError("tether requires string start and end refs")
        if start not in refs or end not in refs:
            raise BuildError(f"tether references must exist in the same step: {start!r}, {end!r}")
        objects.append(
            add_common(
                {
                    "type": "tether",
                    "startId": refs[start],
                    "endId": refs[end],
                    "tether": spec_obj.get("tether", "line"),
                    "width": int(spec_obj.get("width", 4)),
                    "color": spec_obj.get("color", "#ffb900"),
                    "opacity": 100,
                },
                spec_obj,
                next_id,
            )
        )
        next_id += 1

    if step.get("title"):
        objects.append(
            make_text(
                {
                    "text": step["title"],
                    "pos": step.get("titlePos", "N"),
                    "distance": step.get("titleDistance", 285),
                    "fontSize": step.get("titleFontSize", 18),
                },
                next_id,
            )
        )
        next_id += 1

    return {"objects": objects}, next_id


def build_scene(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise BuildError("spec root must be an object")
    steps_spec = spec.get("steps")
    if not isinstance(steps_spec, list) or not steps_spec:
        raise BuildError("spec.steps must be a non-empty list")

    next_id = 1
    steps = []
    for step in steps_spec:
        built_step, next_id = build_step(step, next_id)
        steps.append(built_step)

    return {
        "nextId": next_id,
        "arena": base_arena(spec),
        "steps": steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a XivPlan .xivplan file from a mechanic spec JSON.")
    parser.add_argument("spec", type=Path, help="Path to mechanic spec JSON")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .xivplan path")
    args = parser.parse_args()

    try:
        scene = build_scene(read_json(args.spec))
    except (OSError, json.JSONDecodeError, BuildError) as exc:
        print(f"ERROR: {exc}")
        return 1

    write_json(args.output, scene)
    print(f"Wrote {args.output}")
    print(f"steps: {len(scene['steps'])}")
    print(f"objects: {sum(len(step['objects']) for step in scene['steps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
