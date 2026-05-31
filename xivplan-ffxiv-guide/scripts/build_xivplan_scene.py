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

ARROW_STYLE_PRESETS = {
    "movement": {"color": "#2aa7ff", "height": 18, "opacity": 100, "arrowEnd": True},
    "preposition": {"color": "#36d7d9", "height": 12, "opacity": 88, "arrowEnd": True},
    "micro": {"color": "#7fd8ff", "height": 10, "opacity": 82, "arrowEnd": True},
    "knockback": {"color": "#f3fbff", "height": 26, "opacity": 96, "arrowEnd": True},
    "bait": {"color": "#ffb900", "height": 14, "opacity": 92, "arrowEnd": True},
    "forbidden": {"color": "#d13438", "height": 12, "opacity": 62, "arrowEnd": False},
    "reset": {"color": "#8fd14f", "height": 12, "opacity": 86, "arrowEnd": True},
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
    "tile-square": {
        "shape": "rectangle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "rectangle", "rows": 4, "columns": 4},
    },
}

ARENA_ALIASES = {
    "circle": "default-circle",
    "default": "default-circle",
    "default_circle": "default-circle",
    "e11": "fru-p1",
    "eden-promise": "fru-p1",
    "fatebreaker": "fru-p1",
    "fru": "fru-p1",
    "fru-p1": "fru-p1",
    "p1": "fru-p1",
    "e8": "eden-light",
    "eden-light": "eden-light",
    "fru-p2": "fru-p2",
    "light-rampant": "eden-light",
    "shiva": "eden-light",
    "square": "tile-square",
    "tile": "tile-square",
    "tile-square": "tile-square",
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

PARTY_ROLES = ("MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4")
ROLE_DIR = {"MT": "N", "ST": "S", "H1": "W", "H2": "E", "D1": "NW", "D2": "NE", "D3": "SW", "D4": "SE"}

DEFAULT_SCENE_CONTRACT = {
    "require_full_party_each_step": False,
    "require_enemy_each_step": False,
    "require_waymarks_each_step": False,
    "allow_partial_observation": True,
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
        preset_name = ARENA_ALIASES.get(str(preset_name).lower(), str(preset_name))
        if preset_name not in ARENA_PRESETS:
            raise BuildError(f"unknown arena preset: {preset_name!r}")
        merged = copy.deepcopy(ARENA_PRESETS[preset_name])
        merged.update({key: value for key, value in arena.items() if key != "preset"})
        merged["preset"] = preset_name
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
    for optional_key in ("backgroundImage", "backgroundOpacity", "ticks", "preset", "source", "sourceReason"):
        if optional_key in arena:
            result[optional_key] = arena[optional_key]
    return result


def add_common(obj: dict[str, Any], spec_obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    obj["id"] = obj_id
    if spec_obj.get("ghost") and "opacity" not in spec_obj:
        obj["opacity"] = 35
    obj["opacity"] = int(spec_obj.get("opacity", obj.get("opacity", 100)))
    if spec_obj.get("ghost"):
        obj["ghost"] = True
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
    result = {
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
    }
    if "labelAnchor" in obj:
        result["labelAnchor"] = obj["labelAnchor"]
    if "labelAnchorId" in obj:
        result["labelAnchorId"] = obj["labelAnchorId"]
    if "leaderLine" in obj:
        result["leaderLine"] = bool(obj["leaderLine"])
    if "labelAvoid" in obj:
        result["labelAvoid"] = obj["labelAvoid"]
    return add_common(
        result,
        obj,
        obj_id,
    )


def make_leader_line(start: tuple[float, float], end: tuple[float, float], obj_id: int) -> dict[str, Any]:
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    length = max(math.dist(start, end), 1)
    return add_common(
        {
            "type": "line",
            "x": round(mid[0], 3),
            "y": round(mid[1], 3),
            "length": int(round(length)),
            "width": 3,
            "rotation": rotation_from_vector(start, end),
            "color": "#ffffff",
            "opacity": 65,
        },
        {},
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
    style_name = str(obj.get("arrowStyle", obj.get("style", "movement")))
    style = ARROW_STYLE_PRESETS.get(style_name, ARROW_STYLE_PRESETS["movement"])
    start = obj.get("_segmentStart")
    end = obj.get("_segmentEnd")
    if start is None:
        start = resolve_pos(obj.get("from", obj.get("start", "center")), as_number(obj.get("distance", DEFAULT_OBJECT_DISTANCE), "distance"))
    if end is None:
        end = resolve_pos(obj.get("to", obj.get("end", "N")), as_number(obj.get("distance", DEFAULT_OBJECT_DISTANCE), "distance"))
    start = with_offset(start, obj.get("startOffset"))
    end = with_offset(end, obj.get("endOffset"))
    start, end = trim_arrow_segment(start, end, obj.get("startGap", 0), obj.get("endGap", 0))
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    length = math.dist(start, end)
    result = {
        "type": "arrow",
        "x": round(mid[0], 3),
        "y": round(mid[1], 3),
        "width": int(obj.get("width", max(length, 1))),
        "height": int(obj.get("height", style["height"])),
        "rotation": float(obj.get("rotation", rotation_from_vector(start, end))),
        "color": obj.get("color", style["color"]),
        "opacity": int(obj.get("opacity", style["opacity"])),
        "arrowEnd": obj.get("arrowEnd", style["arrowEnd"]),
        "arrowStyle": style_name,
        "flowStart": [round(start[0], 3), round(start[1], 3)],
        "flowEnd": [round(end[0], 3), round(end[1], 3)],
    }
    for optional_key in ("pathKey", "flowSegment", "routeCheck", "allowDangerCrossing", "flowLabel"):
        if optional_key in obj:
            result[optional_key] = obj[optional_key]
    return add_common(result, obj, obj_id)


def trim_arrow_segment(start: tuple[float, float], end: tuple[float, float], start_gap: Any, end_gap: Any) -> tuple[tuple[float, float], tuple[float, float]]:
    sx, sy = start
    ex, ey = end
    length = math.dist(start, end)
    if length <= 1:
        return start, end
    dx = (ex - sx) / length
    dy = (ey - sy) / length
    max_gap = max(length / 2 - 1, 0)
    if isinstance(start_gap, (int, float)) and start_gap > 0 and max_gap > 0:
        gap = min(float(start_gap), max_gap)
        sx += dx * gap
        sy += dy * gap
    if isinstance(end_gap, (int, float)) and end_gap > 0 and max_gap > 0:
        gap = min(float(end_gap), max_gap)
        ex -= dx * gap
        ey -= dy * gap
    return (sx, sy), (ex, ey)


def resolve_flow_point(value: Any, distance: float) -> tuple[float, float]:
    return resolve_pos(value, distance)


def curved_midpoint(start: tuple[float, float], end: tuple[float, float], curve: Any) -> tuple[float, float]:
    amount = 52.0
    if isinstance(curve, (int, float)):
        amount = float(curve)
    elif isinstance(curve, str):
        lowered = curve.lower()
        if lowered in {"left", "ccw"}:
            amount = 52.0
        elif lowered in {"right", "cw"}:
            amount = -52.0
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max(math.hypot(dx, dy), 1.0)
    normal = (-dy / length, dx / length)
    return (start[0] + dx / 2 + normal[0] * amount, start[1] + dy / 2 + normal[1] * amount)


def arrow_points(obj: dict[str, Any]) -> list[tuple[float, float]]:
    distance = as_number(obj.get("distance", DEFAULT_OBJECT_DISTANCE), "distance")
    raw_points = obj.get("points", obj.get("path"))
    if raw_points is not None:
        if not isinstance(raw_points, list) or len(raw_points) < 2:
            raise BuildError("arrow path/points must contain at least two positions")
        return [resolve_flow_point(point, distance) for point in raw_points]

    start = resolve_flow_point(obj.get("from", obj.get("start", "center")), distance)
    end = resolve_flow_point(obj.get("to", obj.get("end", "N")), distance)
    waypoints = obj.get("waypoints", [])
    if waypoints is None:
        waypoints = []
    if not isinstance(waypoints, list):
        raise BuildError("arrow.waypoints must be a list")
    points = [start] + [resolve_flow_point(point, distance) for point in waypoints] + [end]
    if obj.get("curve") and not waypoints:
        points = [start, curved_midpoint(start, end, obj.get("curve")), end]
    return points


def make_arrow_objects(obj: dict[str, Any], obj_id: int) -> list[dict[str, Any]]:
    points = arrow_points(obj)
    path_key = object_key(obj) or f"arrow-{obj_id}"
    objects: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(zip(points, points[1:]), start=1):
        if math.dist(start, end) < 1:
            continue
        segment_spec = copy.deepcopy(obj)
        segment_spec["_segmentStart"] = start
        segment_spec["_segmentEnd"] = end
        segment_spec["pathKey"] = path_key
        segment_spec["flowSegment"] = index
        if index < len(points) - 1 and "arrowEnd" not in segment_spec:
            segment_spec["arrowEnd"] = False
        objects.append(make_arrow(segment_spec, obj_id + len(objects)))
    if not objects:
        raise BuildError("arrow path must include at least one non-zero segment")
    return objects


def label_clearance(spec_obj: dict[str, Any]) -> float:
    radius = spec_obj.get("radius")
    if isinstance(radius, (int, float)):
        return float(radius) + 58
    kind = spec_obj.get("kind")
    if kind == "tower":
        return 100
    if kind in {"stack", "spread_stack"}:
        return float(spec_obj.get("radius", 70)) + 58
    if kind in {"circle", "danger", "danger_circle", "safe", "safe_circle", "knockback"}:
        return float(spec_obj.get("radius", 60)) + 58
    width = spec_obj.get("width")
    height = spec_obj.get("height")
    if isinstance(width, (int, float)) or isinstance(height, (int, float)):
        return max(float(width if isinstance(width, (int, float)) else 0), float(height if isinstance(height, (int, float)) else 0)) / 2 + 42
    return 64


def auto_label_position(anchor: tuple[float, float], spec_obj: dict[str, Any]) -> tuple[float, float]:
    x, y = anchor
    radius = max(1.0, math.hypot(x, y))
    outward = (x / radius, y / radius) if radius > 24 else (0.0, 1.0)
    distance = float(spec_obj.get("labelDistance", label_clearance(spec_obj)))
    if radius <= 24 and "labelDistance" not in spec_obj:
        obj_radius = spec_obj.get("radius")
        if isinstance(obj_radius, (int, float)) and obj_radius >= 100:
            return with_offset((170.0, 0.0), spec_obj.get("labelOffset"))
        distance += 36
    candidate = (x + outward[0] * distance, y + outward[1] * distance)
    if max(abs(candidate[0]), abs(candidate[1])) > 210:
        if abs(x) >= abs(y):
            outward = (0.0, 1.0 if y >= 0 else -1.0)
        else:
            outward = (1.0 if x >= 0 else -1.0, 0.0)
        candidate = (x + outward[0] * distance, y + outward[1] * distance)
    offset = spec_obj.get("labelOffset")
    return with_offset(candidate, offset)


def build_attached_label_objects(spec_obj: dict[str, Any], next_id: int, anchor_id: int) -> tuple[list[dict[str, Any]], int]:
    if not spec_obj.get("label"):
        return [], next_id

    anchor = pos_from_obj(spec_obj)
    placement = str(spec_obj.get("labelPlacement", "")).lower()
    if placement == "auto" or "labelPos" not in spec_obj:
        label_pos = auto_label_position(anchor, spec_obj)
        leader_line = bool(spec_obj.get("leaderLine", True))
    else:
        label_pos = resolve_pos(
            spec_obj.get("labelPos", spec_obj.get("pos", "center")),
            as_number(spec_obj.get("labelDistance", spec_obj.get("distance", DEFAULT_OBJECT_DISTANCE + 48)), "labelDistance"),
        )
        label_pos = with_offset(label_pos, spec_obj.get("labelOffset"))
        leader_line = False

    label_obj = {
        "kind": "text",
        "text": spec_obj["label"],
        "pos": [round(label_pos[0], 3), round(label_pos[1], 3)],
        "fontSize": spec_obj.get("labelFontSize", 16),
        "labelAnchor": object_key(spec_obj),
        "labelAnchorId": anchor_id,
        "leaderLine": leader_line,
        "labelAvoid": spec_obj.get("labelAvoid", ["party", "enemy", "mechanic", "arrow", "text"]),
    }
    built_objects: list[dict[str, Any]] = []
    if leader_line and math.dist(anchor, label_pos) >= 24:
        built_objects.append(make_leader_line(anchor, label_pos, next_id))
        next_id += 1
    built_objects.append(make_text(label_obj, next_id))
    next_id += 1
    return built_objects, next_id


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
        elif kind in {"arrow", "path", "polyline"}:
            built_arrows = make_arrow_objects(spec_obj, next_id)
            objects.extend(built_arrows)
            ref = object_key(spec_obj)
            if ref:
                refs[ref] = built_arrows[0]["id"]
            next_id += len(built_arrows)
            continue
        else:
            raise BuildError(f"unsupported object kind: {kind!r}")

        objects.append(built)
        ref = object_key(spec_obj)
        if ref:
            refs[ref] = next_id
        if kind not in {"text", "label"}:
            label_objects, next_id = build_attached_label_objects(spec_obj, next_id + 1, next_id)
            objects.extend(label_objects)
            if label_objects:
                next_id -= 1
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
                    "distance": step.get("titleDistance", 322),
                    "fontSize": step.get("titleFontSize", style_value("title_font_size", 18)),
                },
                next_id,
            )
        )
        next_id += 1

    built_step = {"objects": objects}
    for key in (
        "title",
        "purpose",
        "guide_text",
        "checks",
        "visual_focus",
        "required_roles",
        "reset_state",
        "storyboard_phase",
        "movement_required",
        "flow_kind",
        "partial_observation",
        "partial",
        "local_view",
    ):
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


def normalize_scene_contract(spec: dict[str, Any]) -> tuple[dict[str, bool], bool]:
    raw_contract = spec.get("scene_contract")
    if raw_contract is None:
        return copy.deepcopy(DEFAULT_SCENE_CONTRACT), False
    if not isinstance(raw_contract, dict):
        raise BuildError("scene_contract must be an object")
    contract = copy.deepcopy(DEFAULT_SCENE_CONTRACT)
    for key in contract:
        if key in raw_contract:
            contract[key] = bool(raw_contract[key])
    return contract, True


def is_partial_observation_step(step: dict[str, Any]) -> bool:
    return bool(step.get("partial_observation") or step.get("partial") or step.get("local_view"))


def default_party_objects(distance: int = 108) -> list[dict[str, Any]]:
    return [{"kind": "party", "key": role, "role": role, "pos": ROLE_DIR[role], "distance": distance} for role in PARTY_ROLES]


def default_enemy_object() -> dict[str, Any]:
    return {"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}


def default_waymark_objects(root_marker_presets: list[str]) -> list[dict[str, Any]]:
    presets = root_marker_presets or ["all-waymarks"]
    objects: list[dict[str, Any]] = []
    for preset_name in presets:
        objects.extend(expand_marker_preset(str(preset_name)))
    return objects


def spec_object_kind(spec_obj: dict[str, Any]) -> str:
    kind = spec_obj.get("kind", spec_obj.get("type", ""))
    return str(kind)


def party_role_from_spec(spec_obj: dict[str, Any]) -> str:
    if spec_object_kind(spec_obj) != "party":
        return ""
    for key in ("role", "name", "key"):
        value = spec_obj.get(key)
        if isinstance(value, str) and value.upper() in PARTY_ROLES:
            return value.upper()
    return ""


def marker_name_from_spec(spec_obj: dict[str, Any]) -> str:
    if spec_object_kind(spec_obj) != "marker":
        return ""
    for key in ("marker", "name", "key"):
        value = spec_obj.get(key)
        if isinstance(value, str) and value.upper() in MARKER_ICONS:
            return value.upper()
    return ""


def has_enemy_anchor(objects: list[dict[str, Any]]) -> bool:
    return any(spec_object_kind(obj) in {"boss", "enemy"} for obj in objects)


def apply_scene_contract(
    step: dict[str, Any],
    objects: list[dict[str, Any]],
    contract: dict[str, bool],
    contract_active: bool,
    root_marker_presets: list[str],
) -> list[dict[str, Any]]:
    if not contract_active:
        return objects
    if is_partial_observation_step(step) and contract["allow_partial_observation"]:
        return objects

    completed = list(objects)
    if contract["require_enemy_each_step"] and not has_enemy_anchor(completed):
        completed.insert(0, default_enemy_object())

    if contract["require_full_party_each_step"]:
        present_roles = {party_role_from_spec(obj) for obj in completed}
        for party_obj in default_party_objects():
            role = party_obj["role"]
            if role not in present_roles:
                completed.append(party_obj)

    if contract["require_waymarks_each_step"]:
        present_markers = {marker_name_from_spec(obj) for obj in completed}
        for marker_obj in default_waymark_objects(root_marker_presets):
            marker = marker_name_from_spec(marker_obj)
            if marker and marker not in present_markers:
                completed.insert(0, marker_obj)

    return completed


def apply_focus_roles(step: dict[str, Any], objects: list[dict[str, Any]]) -> None:
    raw_roles = step.get("focusRoles")
    if raw_roles is None:
        raw_roles = step.get("focus_roles")
    if raw_roles is None:
        return
    if isinstance(raw_roles, str):
        focus_roles = {raw_roles.upper()}
    elif isinstance(raw_roles, list):
        focus_roles = {str(role).upper() for role in raw_roles}
    else:
        raise BuildError("step.focusRoles must be a string or list")

    for obj in objects:
        role = party_role_from_spec(obj)
        if not role:
            continue
        if role in focus_roles:
            obj.setdefault("opacity", 100)
            continue
        if "opacity" not in obj:
            obj["opacity"] = 35
        obj["ghost"] = True


def expand_step_specs(spec: dict[str, Any]) -> list[dict[str, Any]]:
    expanded_steps: list[dict[str, Any]] = []
    previous_objects: list[dict[str, Any]] = []
    root_marker_presets = spec.get("markerPresets", [])
    if isinstance(root_marker_presets, str):
        root_marker_presets = [root_marker_presets]
    if not isinstance(root_marker_presets, list):
        raise BuildError("markerPresets must be a string or list")
    contract, contract_active = normalize_scene_contract(spec)

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
        objects = apply_scene_contract(step, objects, contract, contract_active, root_marker_presets)
        apply_focus_roles(step, objects)
        step["objects"] = objects
        for transient_key in ("inherit", "remove", "updates", "replace", "markerPresets", "focusRoles", "focus_roles"):
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
    if isinstance(spec.get("scene_contract"), dict):
        scene["scene_contract"] = copy.deepcopy(spec["scene_contract"])
    if isinstance(spec.get("metadata"), dict):
        scene["metadata"] = copy.deepcopy(spec["metadata"])
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
