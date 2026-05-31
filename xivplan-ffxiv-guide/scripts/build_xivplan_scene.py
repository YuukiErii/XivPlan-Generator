#!/usr/bin/env python3
"""Build a basic XivPlan .xivplan scene from a compact mechanic spec JSON."""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_SIZE = 600
DEFAULT_PADDING = 120
DEFAULT_OBJECT_DISTANCE = 220
DEFAULT_PLAYER_SIZE = 32
DEFAULT_MARKER_SIZE = 42

STYLE_PRESETS = {
    "king-x-fru": {
        "title_font_size": 24,
        "label_font_size": 14,
        "text_stroke": "#101318",
        "danger_color": "#d13438",
        "warning_color": "#ff8c00",
        "safe_color": "#8fd14f",
        "movement_color": "#2aa7ff",
        "tower_color": "#bae3ff",
        "stack_color": "#8fd14f",
        "zone_opacity": 42,
        "safe_opacity": 32,
        "tower_opacity": 70,
        "stack_opacity": 55,
        "player_size": 34,
        "boss_radius": 36,
        "marker_size": 42,
    },
}

ARENA_PRESETS = {
    "default-circle": {
        "shape": "circle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "radial", "angularDivs": 8, "radialDivs": 2},
    },
    "fru-p1": {
        "shape": "circle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "radial", "angularDivs": 8, "radialDivs": 2},
        "backgroundImage": "/arena/e11.svg",
    },
    "fru-p2": {
        "shape": "circle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "radial", "angularDivs": 8, "radialDivs": 2},
        "backgroundImage": "/arena/e8.svg",
    },
    "eden-light": {
        "shape": "circle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "radial", "angularDivs": 8, "radialDivs": 2},
        "backgroundImage": "/arena/e8.svg",
    },
}

MARKER_PRESETS = {
    "cardinals": [
        {"kind": "marker", "key": "A", "name": "A", "marker": "A", "pos": "N", "distance": 245},
        {"kind": "marker", "key": "B", "name": "B", "marker": "B", "pos": "E", "distance": 245},
        {"kind": "marker", "key": "C", "name": "C", "marker": "C", "pos": "S", "distance": 245},
        {"kind": "marker", "key": "D", "name": "D", "marker": "D", "pos": "W", "distance": 245},
    ],
    "intercards": [
        {"kind": "marker", "key": "1", "name": "1", "marker": "1", "pos": "NE", "distance": 220},
        {"kind": "marker", "key": "2", "name": "2", "marker": "2", "pos": "SE", "distance": 220},
        {"kind": "marker", "key": "3", "name": "3", "marker": "3", "pos": "SW", "distance": 220},
        {"kind": "marker", "key": "4", "name": "4", "marker": "4", "pos": "NW", "distance": 220},
    ],
    "all-waymarks": [],
}
MARKER_PRESETS["all-waymarks"] = MARKER_PRESETS["cardinals"] + MARKER_PRESETS["intercards"]

MARKER_ICONS = {
    "A": ("/marker/waymark_a.png", "circle", "#d13438"),
    "B": ("/marker/waymark_b.png", "circle", "#ffb900"),
    "C": ("/marker/waymark_c.png", "circle", "#0078d4"),
    "D": ("/marker/waymark_d.png", "circle", "#8764b8"),
    "1": ("/marker/waymark_1.png", "square", "#d13438"),
    "2": ("/marker/waymark_2.png", "square", "#ffb900"),
    "3": ("/marker/waymark_3.png", "square", "#0078d4"),
    "4": ("/marker/waymark_4.png", "square", "#8764b8"),
}

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

_STYLE: dict[str, Any] = {}


class BuildError(ValueError):
    """Spec cannot be converted into a XivPlan scene."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def style_value(key: str, fallback: Any) -> Any:
    return _STYLE.get(key, fallback)


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
    preset_name = arena.get("preset") or spec.get("arenaPreset")
    if preset_name:
        if preset_name not in ARENA_PRESETS:
            raise BuildError(f"unknown arena preset: {preset_name!r}")
        merged = copy.deepcopy(ARENA_PRESETS[preset_name])
        merged.update({key: value for key, value in arena.items() if key != "preset"})
        arena = merged

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

    result = {
        "shape": shape,
        "width": width,
        "height": height,
        "padding": int(arena.get("padding", DEFAULT_PADDING)),
        "grid": grid,
    }
    for optional_key in ("backgroundImage", "backgroundOpacity", "ticks"):
        if optional_key in arena:
            result[optional_key] = arena[optional_key]
    return result


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
            "radius": int(obj.get("radius", style_value("boss_radius", 52))),
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
            "width": int(obj.get("width", style_value("player_size", DEFAULT_PLAYER_SIZE))),
            "height": int(obj.get("height", style_value("player_size", DEFAULT_PLAYER_SIZE))),
            "rotation": int(obj.get("rotation", 0)),
            "opacity": 100,
        },
        obj,
        obj_id,
    )


def make_image(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "image",
            "name": obj.get("name", "Image"),
            "image": obj.get("image", ""),
            "x": x,
            "y": y,
            "width": int(obj.get("width", 96)),
            "height": int(obj.get("height", 96)),
            "rotation": int(obj.get("rotation", 0)),
            "opacity": int(obj.get("opacity", 100)),
        },
        obj,
        obj_id,
    )


def make_marker(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    marker = str(obj.get("marker", obj.get("name", "A"))).upper()
    icon, shape, color = MARKER_ICONS.get(marker, (obj.get("image", ""), obj.get("shape", "circle"), obj.get("color", "#ffffff")))
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "marker",
            "name": obj.get("name", marker),
            "image": obj.get("image", icon),
            "x": x,
            "y": y,
            "width": int(obj.get("width", style_value("marker_size", DEFAULT_MARKER_SIZE))),
            "height": int(obj.get("height", style_value("marker_size", DEFAULT_MARKER_SIZE))),
            "rotation": int(obj.get("rotation", 0)),
            "shape": obj.get("shape", shape),
            "color": obj.get("color", color),
            "opacity": int(obj.get("opacity", 100)),
        },
        obj,
        obj_id,
    )


def make_icon(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "icon",
            "name": obj.get("name", "Icon"),
            "image": obj.get("image", obj.get("icon", "")),
            "x": x,
            "y": y,
            "width": int(obj.get("width", 32)),
            "height": int(obj.get("height", 32)),
            "rotation": int(obj.get("rotation", 0)),
            "opacity": int(obj.get("opacity", 100)),
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
            "color": obj.get("color", style_value("tower_color", "#bae3ff")),
            "opacity": int(obj.get("opacity", style_value("tower_opacity", 70))),
        },
        obj,
        obj_id,
    )


def make_circle(obj: dict[str, Any], obj_id: int, obj_type: str = "circle") -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    kind = obj.get("kind")
    if kind in {"safe", "safe_circle"}:
        default_color = style_value("safe_color", "#8fd14f")
        default_opacity = style_value("safe_opacity", 35)
    elif kind in {"danger", "danger_circle"}:
        default_color = style_value("danger_color", "#d13438")
        default_opacity = style_value("zone_opacity", 45)
    else:
        default_color = style_value("warning_color", "#ffb900")
        default_opacity = style_value("zone_opacity", 45)
    color = obj.get("color", default_color)
    result = {
        "type": obj_type,
        "x": x,
        "y": y,
        "radius": int(obj.get("radius", 60)),
        "color": color,
        "opacity": int(obj.get("opacity", default_opacity)),
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
            "color": obj.get("color", style_value("stack_color", "#8fd14f")),
            "opacity": int(obj.get("opacity", style_value("stack_opacity", 55))),
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
            "stroke": obj.get("stroke", style_value("text_stroke", "#000000")),
            "style": obj.get("style", "outline"),
            "fontSize": int(obj.get("fontSize", style_value("label_font_size", 18))),
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


def make_rect(obj: dict[str, Any], obj_id: int, obj_type: str = "rect") -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    result = {
        "type": obj_type,
        "x": x,
        "y": y,
        "width": int(obj.get("width", 120)),
        "height": int(obj.get("height", 80)),
        "rotation": float(obj.get("rotation", 0)),
        "color": obj.get("color", style_value("danger_color", "#d13438")),
        "opacity": int(obj.get("opacity", style_value("zone_opacity", 45))),
    }
    if obj.get("hollow", False):
        result["hollow"] = True
    return add_common(result, obj, obj_id)


def make_donut(obj: dict[str, Any], obj_id: int, obj_type: str = "donut") -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": obj_type,
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 220)),
            "innerRadius": int(obj.get("innerRadius", 80)),
            "color": obj.get("color", style_value("danger_color", "#d13438")),
            "opacity": int(obj.get("opacity", style_value("zone_opacity", 45))),
        },
        obj,
        obj_id,
    )


def make_arc(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "arc",
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 240)),
            "innerRadius": int(obj.get("innerRadius", 120)),
            "coneAngle": int(obj.get("coneAngle", 90)),
            "rotation": float(obj.get("rotation", 0)),
            "color": obj.get("color", style_value("danger_color", "#d13438")),
            "opacity": int(obj.get("opacity", style_value("zone_opacity", 45))),
        },
        obj,
        obj_id,
    )


def make_polygon(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    result = {
        "type": "polygon",
        "x": x,
        "y": y,
        "radius": int(obj.get("radius", 160)),
        "sides": int(obj.get("sides", 6)),
        "orient": obj.get("orient", "point"),
        "rotation": float(obj.get("rotation", 0)),
        "color": obj.get("color", style_value("safe_color", "#8fd14f")),
        "opacity": int(obj.get("opacity", style_value("safe_opacity", 35))),
    }
    if obj.get("hollow", False):
        result["hollow"] = True
    return add_common(result, obj, obj_id)


def make_starburst(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "starburst",
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 130)),
            "spokes": int(obj.get("spokes", 8)),
            "spokeWidth": int(obj.get("spokeWidth", 24)),
            "rotation": float(obj.get("rotation", 0)),
            "color": obj.get("color", style_value("danger_color", "#d13438")),
            "opacity": int(obj.get("opacity", style_value("zone_opacity", 45))),
        },
        obj,
        obj_id,
    )


def make_eye(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    result = {
        "type": "eye",
        "x": x,
        "y": y,
        "radius": int(obj.get("radius", 80)),
        "color": obj.get("color", style_value("danger_color", "#d13438")),
        "opacity": int(obj.get("opacity", style_value("zone_opacity", 45))),
    }
    if obj.get("invert"):
        result["invert"] = True
    if obj.get("hollow", True):
        result["hollow"] = True
    return add_common(result, obj, obj_id)


def make_exaflare(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "exaflare",
            "x": x,
            "y": y,
            "radius": int(obj.get("radius", 36)),
            "length": int(obj.get("length", 5)),
            "spacing": int(obj.get("spacing", 58)),
            "rotation": float(obj.get("rotation", 0)),
            "color": obj.get("color", style_value("danger_color", "#d13438")),
            "opacity": int(obj.get("opacity", style_value("zone_opacity", 45))),
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
            "color": obj.get("color", style_value("movement_color", "#0078d4")),
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
        elif kind == "marker":
            built = make_marker(spec_obj, next_id)
        elif kind == "icon":
            built = make_icon(spec_obj, next_id)
        elif kind == "image":
            built = make_image(spec_obj, next_id)
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
        elif kind in {"rect", "rectangle"}:
            built = make_rect(spec_obj, next_id)
        elif kind in {"line_stack", "lineStack"}:
            built = make_rect(spec_obj, next_id, "lineStack")
        elif kind in {"line_knockback", "lineKnockback"}:
            built = make_rect(spec_obj, next_id, "lineKnockback")
        elif kind in {"line_knockaway", "lineKnockAway"}:
            built = make_rect(spec_obj, next_id, "lineKnockAway")
        elif kind == "donut":
            built = make_donut(spec_obj, next_id)
        elif kind == "arc":
            built = make_arc(spec_obj, next_id)
        elif kind == "polygon":
            built = make_polygon(spec_obj, next_id)
        elif kind == "starburst":
            built = make_starburst(spec_obj, next_id)
        elif kind == "eye":
            built = make_eye(spec_obj, next_id)
        elif kind == "exaflare":
            built = make_exaflare(spec_obj, next_id)
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
                    "fontSize": step.get("titleFontSize", style_value("title_font_size", 18)),
                },
                next_id,
            )
        )
        next_id += 1

    built_step = {"objects": objects}
    for key in ("title", "purpose", "guide_text", "checks"):
        if key in step:
            built_step[key] = step[key]
    if "guide_text" not in built_step:
        built_step["guide_text"] = step.get("purpose") or step.get("title") or "See diagram."

    return built_step, next_id


def expand_marker_preset(name: str) -> list[dict[str, Any]]:
    if name not in MARKER_PRESETS:
        raise BuildError(f"unknown marker preset: {name!r}")
    return copy.deepcopy(MARKER_PRESETS[name])


def step_object_key(spec_obj: dict[str, Any]) -> str | None:
    return object_key(spec_obj)


def expand_step_specs(spec: dict[str, Any]) -> list[dict[str, Any]]:
    expanded_steps: list[dict[str, Any]] = []
    previous_objects: list[dict[str, Any]] = []
    root_marker_presets = spec.get("markerPresets", [])
    if isinstance(root_marker_presets, str):
        root_marker_presets = [root_marker_presets]
    if not isinstance(root_marker_presets, list):
        raise BuildError("markerPresets must be a string or list")

    for raw_step in spec["steps"]:
        step = copy.deepcopy(raw_step)
        objects: list[dict[str, Any]] = copy.deepcopy(previous_objects) if step.get("inherit") else []

        remove_keys = step.get("remove", [])
        if isinstance(remove_keys, str):
            remove_keys = [remove_keys]
        if not isinstance(remove_keys, list):
            raise BuildError("step.remove must be a string or list")
        remove_set = {str(key) for key in remove_keys}
        if remove_set:
            objects = [obj for obj in objects if step_object_key(obj) not in remove_set]

        updates = step.get("updates", {})
        if not isinstance(updates, dict):
            raise BuildError("step.updates must be an object keyed by object key")
        if updates:
            by_key = {step_object_key(obj): obj for obj in objects if step_object_key(obj)}
            for key, patch in updates.items():
                if key not in by_key:
                    raise BuildError(f"step update references missing inherited object: {key!r}")
                if not isinstance(patch, dict):
                    raise BuildError(f"step update for {key!r} must be an object")
                by_key[key].update(patch)

        replace = step.get("replace", [])
        if not isinstance(replace, list):
            raise BuildError("step.replace must be a list")
        for replacement in replace:
            if not isinstance(replacement, dict):
                raise BuildError("step.replace entries must be objects")
            key = step_object_key(replacement)
            if not key:
                raise BuildError("step.replace entries require key, role, or name")
            objects = [obj for obj in objects if step_object_key(obj) != key]
            objects.append(replacement)

        marker_presets = list(root_marker_presets)
        step_marker_presets = step.get("markerPresets", [])
        if isinstance(step_marker_presets, str):
            step_marker_presets = [step_marker_presets]
        if not isinstance(step_marker_presets, list):
            raise BuildError("step.markerPresets must be a string or list")
        marker_presets.extend(step_marker_presets)

        preset_objects: list[dict[str, Any]] = []
        for preset_name in marker_presets:
            preset_objects.extend(expand_marker_preset(str(preset_name)))
        if preset_objects and not step.get("inherit"):
            objects = preset_objects + objects

        own_objects = step.get("objects", [])
        if not isinstance(own_objects, list):
            raise BuildError("step.objects must be a list")
        objects.extend(own_objects)
        step["objects"] = objects
        for transient_key in ("inherit", "remove", "updates", "replace", "markerPresets"):
            step.pop(transient_key, None)
        expanded_steps.append(step)
        previous_objects = copy.deepcopy(objects)

    return expanded_steps


def build_scene(spec: dict[str, Any]) -> dict[str, Any]:
    global _STYLE
    if not isinstance(spec, dict):
        raise BuildError("spec root must be an object")
    steps_spec = spec.get("steps")
    if not isinstance(steps_spec, list) or not steps_spec:
        raise BuildError("spec.steps must be a non-empty list")
    style_name = spec.get("style")
    _STYLE = {}
    if style_name:
        if style_name not in STYLE_PRESETS:
            raise BuildError(f"unknown style preset: {style_name!r}")
        _STYLE = STYLE_PRESETS[style_name]

    next_id = 1
    steps = []
    for step in expand_step_specs(spec):
        built_step, next_id = build_step(step, next_id)
        steps.append(built_step)

    scene = {
        "nextId": next_id,
        "arena": base_arena(spec),
        "steps": steps,
    }
    if spec.get("name"):
        scene["name"] = spec["name"]
    if spec.get("style"):
        scene["style"] = spec["style"]
    return scene


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
