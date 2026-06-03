#!/usr/bin/env python3
"""Build a basic XivPlan .xivplan scene from a compact mechanic spec JSON."""

from __future__ import annotations

import argparse
import base64
import copy
import io
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
    "omega-o8s": {
        "shape": "circle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "radial", "angularDivs": 8, "radialDivs": 2},
        "backgroundStatus": "fallback",
        "sourceReason": "no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays",
        "arenaOverlays": [
            {"kind": "radial_ticks", "count": 16, "color": "#8aa0b8", "opacity": 42},
            {"kind": "axis", "axis": "AC", "label": "AC 轴", "color": "#5fb3ff", "opacity": 72},
            {"kind": "axis", "axis": "BD", "label": "BD 轴", "color": "#ffb650", "opacity": 72},
            {"kind": "half_mask", "side": "W", "label": "西半场", "color": "#5fb3ff", "opacity": 10},
            {"kind": "ring_label_band", "label": "O8S/Omega arena fallback: use axes, waymarks, and Boss target ring", "color": "#f7f7f7"},
        ],
    },
    "ultimate-yokai-star-dance": {
        "shape": "circle",
        "width": 600,
        "height": 600,
        "padding": 120,
        "grid": {"type": "radial", "angularDivs": 8, "radialDivs": 2},
        "backgroundImage": "/arena/udm-p1.png",
        "backgroundStatus": "local-asset",
        "sourceReason": "local UDM/Yokai arena asset `/arena/udm-p1.png` found; use it for Ultimate Yokai Star Dance P1 diagrams",
        "arenaOverlays": [
            {"kind": "radial_ticks", "count": 16, "color": "#8aa0b8", "opacity": 42},
            {"kind": "axis", "axis": "AC", "label": "AC 轴", "color": "#5fb3ff", "opacity": 66},
            {"kind": "axis", "axis": "BD", "label": "BD 轴", "color": "#ffb650", "opacity": 66},
        ],
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
    "o8s": "omega-o8s",
    "omega": "omega-o8s",
    "omega-o8s": "omega-o8s",
    "sigmascape": "omega-o8s",
    "kefka": "omega-o8s",
    "凯夫卡": "omega-o8s",
    "妖星乱舞": "omega-o8s",
    "ultimate-yokai-star-dance": "ultimate-yokai-star-dance",
    "ultimate yokai star dance": "ultimate-yokai-star-dance",
    "yokai-star-dance": "ultimate-yokai-star-dance",
    "udm": "ultimate-yokai-star-dance",
    "绝妖": "ultimate-yokai-star-dance",
    "绝妖星乱舞": "ultimate-yokai-star-dance",
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
ROLE_NUMBER_ICONS = {
    "MT": "/actor/tank1.png",
    "ST": "/actor/tank2.png",
    "H1": "/actor/healer1.png",
    "H2": "/actor/healer2.png",
    "D1": "/actor/dps1.png",
    "D2": "/actor/dps2.png",
    "D3": "/actor/dps3.png",
    "D4": "/actor/dps4.png",
}
DEFAULT_PARTY_JOBS = {
    "MT": {"job": "DRK", "jobName": "Dark Knight", "icon": "/actor/DRK.png"},
    "ST": {"job": "PLD", "jobName": "Paladin", "icon": "/actor/PLD.png"},
    "H1": {"job": "AST", "jobName": "Astrologian", "icon": "/actor/AST.png"},
    "H2": {"job": "SCH", "jobName": "Scholar", "icon": "/actor/SCH.png"},
    "D1": {"job": "SAM", "jobName": "Samurai", "icon": "/actor/SAM.png"},
    "D2": {"job": "DRG", "jobName": "Dragoon", "icon": "/actor/DRG.png"},
    "D3": {"job": "BRD", "jobName": "Bard", "icon": "/actor/BRD.png"},
    "D4": {"job": "PCT", "jobName": "Pictomancer", "icon": "/actor/PCT.png"},
}
MECHANIC_FLOW_TOKENS = {"mechanic_flow", "mechanic-flow", "mechanic", "main", "main_mechanic", "机制流程", "主机制流程"}
FLOW_EXAMPLE_TOKENS = {"flow_example", "flow-example", "example", "position_example", "timeline_example", "流程示例", "示例"}
ENEMY_SPEC_KINDS = {"boss", "enemy", "add", "clone", "shadow", "untargetable_source"}
ENEMY_KIND_DEFAULT_RADIUS = {
    "boss": 42,
    "enemy": 42,
    "add": 26,
    "clone": 28,
    "shadow": 28,
    "untargetable_source": 32,
}
FALLBACK_ENEMY_ICON_DATA_URLS = {
    "boss": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADimHc4AAAD/klEQVR4nO1dsZLTMBCVPFRHcfX1VPAVNIGKVv9Avif3D2pTQRq+4q66npqCa82YwRnjkWTZertaOftmbi6FI63e211pFUUxRqFQKBQKhUKhUCgUCoVCoVAobgHWNIT+eOxzn7WnUxNjs3shvFVB7J5Jb0EMeyukSxWjMzdMvoT+bUsDd99+/Mx91n/++NBCNFjJ5LsVhKME4RbBtk68f3y+d1/f/2pViDdGCPkO6O25/aTEGOzlEKFrmXz/+Hw//b8WS/1yTNDkEZAahGPy+hRGG2LRQB0JXavk+5nXb42CHHsoI6G7Vc+XIkLXIvk+4u2lUVBDBNZKWKrn17QTLkDMS1ohf8ledBR0rZHvF9IMIg1xikCeglrzfG77YQJwFC0+07uRUUA9XogAe8n7NVIRpMILGYIm30+9+tDH277Ya0W7ZpMuy4ZAtVxaJbNtxhXjkCA9+tyHOyMcXRO5/+XplfN9nOMnWQWh0o9/eXotJRHRBuWcJjYF+RRpkzyfm6qG9tw7eSnJSpx8fYz8FPGZQiBEQE7G1U9FZGMN+VuerwRxAviQ928lM/A+jomZNwV9OeEGdAikDYQnU7U74ny8Y09B1/x/PtJNbBcQSZTp6N/4ty5HMaugUQRkNEgHyPGgc0BR6X+YpQm0187by62sA0BuccDrgNE4jh1JbqD3lkhXQRTG1gTVeEgr4T1EgyN2JJY6oNVocAx2s+0FtRQNjtFh2Cth6dHgmO2rshsajIaLffhvaTi8Ri5FF5a5tRyj6l6QExINNe0Qsx3th2hg3gvaSvwut6PdQEaI7IKKlYJ8NMQIcAVSBOpd0D0J4JeWp2tFWHheynK4SIBQ3tvy9dBsLx1IXRIi9QzA+9Fng8R+KG/my9LSlCQs9ZCmoLVR4GPpYCCtlLhEG2vTECS60QKwfJ/2gvtMGI3mjyb6XC+ckpl5NjS3/5pLUjIBhnAlOx194c/nFOkHNgfEwpDK6BGD545/hhCxcSDSL2wS3mKML1iLz0kvEWGLHai5j3wOQKcilyCa4jMH6iiGLkOpU5HL9HJUSqJMPde2DAFyvrK0xksdU3qZ9sNBPvte0JZIcIXevOX91GmHXICUl+QOzgFXN2vaStlHUXSSVrHR85ILRxgd4bJyMSVFjhxSVfzk2whBESICOMaKNCpEQIBm7wsKGi+A/GR/M/uo97pYJuHkIM7HO9Ij7iks9M2x0ch/a+LUw87hwVN+wz46yc7s4ro1kVeA7+b33xeZHu8q3Bs6CmE/mbdmjwKMA5N8c24/sXP3l3f3le9urn2Bd/VTEbby7eXV+zfC0OvvB8hBr7+gIQv9Dn9DRqFQKBQKhUKhUCgUCoVCoVAYHvwBvlhymqjhOA0AAAAASUVORK5CYII=",
    "add": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADimHc4AAACbUlEQVR4nO2cMU7DQBBFbYueJjUNHQ2tqxxihZC4BX3q9NwCKUJzCKq0NO5oqNPkBEZ0UeQgJ5md+bP7X5kCr/+bmVgKnqYhhBBCCCGEEEIIIYQQQgghpGRaz4s/vI9jA8Lw0rpk0dYcOoIMswtFCN5DRNcYEDF8q3NnNRw1eMtuaD3DHz9WPw0I7dP6zkOCyQiaCl4rfHlbLdDO5N4Bp6pf+wblIPz0ut5ZdIR2F7SRw1/2j9+Hny3659toEkxGENKsRzt3F/GpR07Mfa3vA8v7zN4BOee+hYTcXeDyFHQpMjNcq06AEjDVlprVI2eGqilh6j60xlCoDiiREALkwmqOMIrgBciVIaJLgBYgSuEhS4AWUAOwAkS5alG7AFKAZAoLUQKcAMkcEpoEKAFiFA6SBCgBNQIjQIyrEqULIASIUxgIEtwFiHMI3tfvar55hHO4d0Dt3HhdeLfd7Jf9Zq/5N49/pD8X7R/1YTsAZfQgnMtFgPb/8EQ+F78Dav0O+Ju3cmXLH8/8z+3XfbSudO2ABDKKPM/hPoKSswTv67sL8AzBO3wYAR5hIIQPJaBWoAQko6pEqX44ARbhIIUPKSBnSGjhwwrIERZi+NACagFaQFKqWtTqhxegER5y+CEEXBMievhhBJSMmoCpd2fnvP6fq5o1q3/qPrTeFQ7VAWlmqBFGj5kAzS6YE67VygJIAVabptKJkK0qP9yqgtxVFPnc3JZS2raUOS8ya7/AnTI/8eQcsdyY5bwxizvjSt0ZV8ryviHzk11X8lbaCOfm5txaNueij6YhaJcSQgghhBBCCCGEEEIIIYSQ5n9+AR9+LrHgK8bcAAAAAElFTkSuQmCC",
    "generic": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADimHc4AAACeElEQVR4nO3csaoaQRTG8RnjJcTumiKFkEZbn8DnWbCwtbD2AXyAaXwDsfMNLHwCYatgFYIgSRBCkhuWEAjBe3M32TNnzuz/19gI7p5vz8wu64xzAAAAAAAAAAAAQM68M6Qsy4fnfnc0Gpk4N59Lwa0G4nMvfOpB+DYUPeUwOq6lxdf83d+pXgFlzQIURfHuud8NIby10A0+9eIXNYr+v2FohOBTLH7RQNH/NYzYIfiUil8IFr5OEDFD6LSx+H/7vZiTc6eNxU8phCit9tjJFEqFrzMkSQ9H4h1gofhPHY90J4gGYKX4miEk8STcZmIBWLv6tbpAJACrxdcIIdoQZKX4sY+XOUBZ4/e4t9q0iatpPB6/nE6n991u163X68t+v786peeDJp8Nus6I2Wx2v1wuP1yv14fVavUmVgCmhiDJ++XNZvPxdDp9vVwu33u9nqn3GKpzQFOT2W63+1x9DofDu+Px+MVlMhmbm4Qnk8mr7Xb7yWXCXACDweDucDhkMf5XfOp3P3/q9/svzufzNxeZ1N2QuQ5YLBavXUbMBTCfz9+7jJgLIDcEoIwAlBGAMgJQRgDKCEAZAeQSwK3H8rp/EU+V5EsZOkAZAeQegPVhKAgffye3RW8xNHmeDEHKGg8gp7uhIPyXlAodoCxaANa6IEQ6XpEAHmtTKyGEiKtlxDrAaggh8lIl5gBlogFY64KgsFBPvAOshBCUVkn6Nq8TTmHFfLQ54KmTCUrdoF386JNwSiGEBIpfYbeUtu2W8gv7Bf1kaqVJwY5ZaQSR0zuMJJ6ER0pF0C5+Rf0AbmHf0ESU7JybljLDvaMBAAAAAAAAAADgZP0Alow3hY1ayVoAAAAASUVORK5CYII=",
}

DEFAULT_SCENE_CONTRACT = {
    "require_full_party_each_step": False,
    "require_enemy_each_step": False,
    "require_waymarks_each_step": False,
    "allow_partial_observation": True,
}
SEMANTIC_OBJECT_FIELDS = (
    "damagePattern",
    "damagePatternKind",
    "movementRoute",
    "routeIntent",
    "source",
    "targets",
    "targetRoles",
    "resolveIndex",
    "resolveTiming",
    "aoeIntent",
    "fromRole",
    "fromObject",
    "fromMarker",
    "toRole",
    "toObject",
    "toMarker",
    "toZone",
    "startLabel",
    "endLabel",
    "snapToTarget",
    "baitSequence",
    "statusOverlay",
    "statusRole",
    "statusName",
    "statusKind",
    "decisionGroup",
    "durationLabel",
    "stackLabel",
    "priorityLabel",
    "anchorRole",
    "anchorPartyId",
    "visibleSteps",
    "assetStatus",
    "assetFallback",
)

STATUS_ICON_COLORS = {
    "red": ("#d13438", "#ffffff"),
    "blue": ("#0078d4", "#ffffff"),
    "green": ("#107c10", "#ffffff"),
    "yellow": ("#ffb900", "#101318"),
    "purple": ("#8764b8", "#ffffff"),
    "orange": ("#ff8c00", "#101318"),
    "short": ("#d13438", "#ffffff"),
    "long": ("#0078d4", "#ffffff"),
    "fire": ("#ff8c00", "#101318"),
    "ice": ("#2aa7ff", "#101318"),
    "light": ("#f7e36d", "#101318"),
    "dark": ("#3b2f66", "#ffffff"),
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
LABEL_BAND_POSITIONS = {
    "top": [(-220.0, 302.0), (0.0, 286.0), (220.0, 302.0)],
    "bottom": [(-220.0, -302.0), (0.0, -286.0), (220.0, -302.0)],
    "left": [(-302.0, 176.0), (-302.0, 0.0), (-302.0, -176.0)],
    "right": [(302.0, 176.0), (302.0, 0.0), (302.0, -176.0)],
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


def label_band_position(obj: dict[str, Any]) -> tuple[float, float] | None:
    raw_band = obj.get("labelBand", obj.get("label_band"))
    if not isinstance(raw_band, str) or not raw_band.strip():
        return None
    band = raw_band.strip().lower().replace("-", "_")
    positions = LABEL_BAND_POSITIONS.get(band)
    if not positions:
        return None
    raw_index = obj.get("labelBandIndex", obj.get("label_band_index", obj.get("bandIndex", 0)))
    try:
        index = int(raw_index)
    except (TypeError, ValueError):
        index = 0
    base = positions[index % len(positions)]
    cycle = index // len(positions)
    if cycle:
        if band in {"top", "bottom"}:
            step = -28.0 if band == "top" else 28.0
            base = (base[0], base[1] + cycle * step)
        else:
            step = 28.0 if band == "left" else -28.0
            base = (base[0] + cycle * step, base[1])
    return with_offset(base, obj.get("offset"))


def text_pos_from_obj(obj: dict[str, Any]) -> tuple[float, float]:
    if "pos" not in obj:
        band_pos = label_band_position(obj)
        if band_pos is not None:
            return band_pos
    x, y = pos_from_obj(obj)
    # Keep auto-generated labels inside the validator margin even when a large
    # mechanic such as a charge line pushes the preferred offset outward.
    return max(-330.0, min(330.0, x)), max(-330.0, min(330.0, y))


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
    for optional_key in (
        "backgroundImage",
        "backgroundOpacity",
        "backgroundStatus",
        "backgroundAsset",
        "fallbackBackground",
        "ticks",
        "preset",
        "source",
        "sourceReason",
        "arenaOverlays",
    ):
        if optional_key in arena:
            result[optional_key] = arena[optional_key]
    return result


def add_common(obj: dict[str, Any], spec_obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    obj["id"] = obj_id
    source_key = object_key(spec_obj)
    if source_key:
        obj["sourceKey"] = source_key
    for key in SEMANTIC_OBJECT_FIELDS:
        if key in spec_obj:
            obj[key] = copy.deepcopy(spec_obj[key])
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
    enemy_kind = enemy_kind_from_spec(obj)
    radius = int(obj.get("radius", default_enemy_radius(enemy_kind)))
    display_name = str(obj.get("displayName") or obj.get("name") or default_enemy_name(enemy_kind))
    ring = normalize_enemy_ring(obj, radius)
    rotation = int(obj.get("facing", obj.get("rotation", 180)))
    icon = str(obj.get("icon") or obj.get("image") or fallback_enemy_icon(enemy_kind))
    return add_common(
        {
            "type": "enemy",
            "name": display_name,
            "displayName": display_name,
            "enemyKind": enemy_kind,
            "icon": icon,
            "image": obj.get("image", icon),
            "assetId": obj.get("asset_id", obj.get("assetId")),
            "assetStatus": obj.get("asset_status", obj.get("assetStatus", "fallback")),
            "assetSource": obj.get("asset_source", obj.get("assetSource", "fallback")),
            "assetFallback": obj.get("asset_fallback", obj.get("assetFallback")),
            "iconWidth": int(obj.get("iconWidth", obj.get("icon_width", min(72, max(42, radius * 2))))),
            "iconHeight": int(obj.get("iconHeight", obj.get("icon_height", min(72, max(42, radius * 2))))),
            "x": x,
            "y": y,
            "radius": radius,
            "rotation": rotation,
            "facing": rotation,
            "ring": "dir" if ring.get("visible", True) else "none",
            "targetRing": ring,
            "color": obj.get("color", "#d13438"),
            "opacity": 100,
        },
        obj,
        obj_id,
    )


def is_enemy_spec(obj: dict[str, Any]) -> bool:
    obj_type = obj.get("type")
    kind = obj.get("kind")
    return obj_type == "enemy" or (isinstance(kind, str) and kind in ENEMY_SPEC_KINDS)


def enemy_kind_from_spec(obj: dict[str, Any]) -> str:
    explicit = obj.get("enemyKind") or obj.get("enemy_kind")
    if isinstance(explicit, str) and explicit:
        return explicit
    if obj.get("type") == "enemy":
        kind = obj.get("kind")
        return str(kind) if isinstance(kind, str) and kind else "boss"
    kind = obj.get("kind")
    if isinstance(kind, str) and kind in ENEMY_SPEC_KINDS:
        return "boss" if kind == "boss" else kind
    return "boss"


def default_enemy_name(enemy_kind: str) -> str:
    if enemy_kind == "add":
        return "Add"
    if enemy_kind in {"clone", "shadow"}:
        return "Clone"
    if enemy_kind == "untargetable_source":
        return "Source"
    return "Boss"


def default_enemy_radius(enemy_kind: str) -> int:
    if enemy_kind in {"boss", "enemy"}:
        return int(style_value("boss_radius", ENEMY_KIND_DEFAULT_RADIUS["boss"]))
    return ENEMY_KIND_DEFAULT_RADIUS.get(enemy_kind, 32)


def fallback_enemy_icon(enemy_kind: str) -> str:
    if enemy_kind in {"boss", "enemy", "clone", "shadow", "untargetable_source"}:
        return FALLBACK_ENEMY_ICON_DATA_URLS["boss"]
    if enemy_kind == "add":
        return FALLBACK_ENEMY_ICON_DATA_URLS["add"]
    return FALLBACK_ENEMY_ICON_DATA_URLS["generic"]


def normalize_enemy_ring(obj: dict[str, Any], radius: int) -> dict[str, Any]:
    raw = obj.get("ring")
    if isinstance(raw, dict):
        ring = copy.deepcopy(raw)
        ring.setdefault("visible", True)
        ring.setdefault("radius", radius)
        ring.setdefault("strokeWidth", 3)
        ring.setdefault("style", "target-ring")
        return ring
    if raw in {False, "none", "hidden"}:
        return {"visible": False, "radius": radius, "strokeWidth": 0, "style": "none"}
    return {"visible": True, "radius": int(obj.get("ringRadius", radius)), "strokeWidth": int(obj.get("ringStrokeWidth", 3)), "style": "target-ring"}


def enemy_suffix_from_position(obj: dict[str, Any], duplicate_index: int) -> str:
    pos = obj.get("pos")
    if isinstance(pos, str) and pos.upper() in DIRECTION_DEGREES:
        return pos.upper()
    if isinstance(pos, dict) and isinstance(pos.get("dir"), str) and pos["dir"].upper() in DIRECTION_DEGREES:
        return pos["dir"].upper()
    try:
        x, y = pos_from_obj(obj)
    except BuildError:
        return str(duplicate_index)
    if abs(x) > abs(y) and abs(x) > 16:
        return "E" if x > 0 else "W"
    if abs(y) > 16:
        return "N" if y > 0 else "S"
    return str(duplicate_index)


def normalize_enemy_spec(obj: dict[str, Any], duplicate_index: int | None = None) -> dict[str, Any]:
    normalized = copy.deepcopy(obj)
    enemy_kind = enemy_kind_from_spec(normalized)
    normalized["enemyKind"] = enemy_kind
    display_name = str(normalized.get("displayName") or normalized.get("name") or default_enemy_name(enemy_kind)).strip()
    if not display_name:
        display_name = default_enemy_name(enemy_kind)
    if duplicate_index is not None:
        suffix = enemy_suffix_from_position(normalized, duplicate_index)
        if not display_name.endswith(f" {suffix}"):
            display_name = f"{display_name} {suffix}"
    normalized["name"] = display_name
    normalized["displayName"] = display_name
    radius = int(normalized.get("radius", default_enemy_radius(enemy_kind)))
    normalized["radius"] = radius
    normalized["ring"] = normalize_enemy_ring(normalized, radius)
    normalized.setdefault("icon", fallback_enemy_icon(enemy_kind))
    normalized.setdefault("asset_status", "fallback")
    normalized.setdefault("asset_fallback", "generic-add-icon" if enemy_kind == "add" else "generic-boss-icon")
    normalized.setdefault("label", display_name)
    normalized.setdefault("labelPlacement", "auto")
    normalized.setdefault("labelDistance", radius + 96)
    normalized.setdefault("leaderLine", True)
    normalized.setdefault("labelAvoid", ["party", "enemy", "mechanic", "arrow", "text"])
    if "facing" in normalized and "rotation" not in normalized:
        normalized["rotation"] = normalized["facing"]
    return normalized


def normalize_enemy_specs(objects_spec: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names: dict[str, int] = {}
    for spec_obj in objects_spec:
        if not is_enemy_spec(spec_obj):
            continue
        enemy_kind = enemy_kind_from_spec(spec_obj)
        name = str(spec_obj.get("displayName") or spec_obj.get("name") or default_enemy_name(enemy_kind)).strip()
        names[name] = names.get(name, 0) + 1

    occurrences: dict[str, int] = {}
    normalized: list[dict[str, Any]] = []
    for spec_obj in objects_spec:
        if not is_enemy_spec(spec_obj):
            normalized.append(spec_obj)
            continue
        enemy_kind = enemy_kind_from_spec(spec_obj)
        base_name = str(spec_obj.get("displayName") or spec_obj.get("name") or default_enemy_name(enemy_kind)).strip()
        occurrences[base_name] = occurrences.get(base_name, 0) + 1
        duplicate_index = occurrences[base_name] if names.get(base_name, 0) > 1 else None
        normalized.append(normalize_enemy_spec(spec_obj, duplicate_index=duplicate_index))
    return normalized


def make_party(obj: dict[str, Any], obj_id: int) -> dict[str, Any]:
    role = str(obj.get("role") or obj.get("name") or "Player").upper()
    defaults = DEFAULT_PARTY_JOBS.get(role, {})
    job = str(obj.get("job") or defaults.get("job") or role)
    job_name = str(obj.get("jobName") or obj.get("job_name") or defaults.get("jobName") or job)
    display_style = explicit_party_display_style(obj.get("partyDisplayStyle")) or explicit_party_display_style(obj.get("party_display_style")) or "role-number-icon"
    if display_style == "role-number-icon":
        icon = str(ROLE_NUMBER_ICONS.get(role) or ROLE_IMAGES.get(role, "/actor/any.png"))
    else:
        icon = str(obj.get("icon") or defaults.get("icon") or ROLE_IMAGES.get(role, "/actor/any.png"))
    role_label = str(obj.get("roleLabel") or obj.get("role_label") or role)
    role_label_visible = obj.get("roleLabelVisible", obj.get("role_label_visible", display_style != "role-number-icon")) is not False
    icon_scale = float(obj.get("iconScale", obj.get("icon_scale", 1.0)) or 1.0)
    icon_scale = max(0.72, min(1.25, icon_scale))
    base_size = int(obj.get("width", style_value("player_size", DEFAULT_PLAYER_SIZE)))
    width = int(max(24, round(base_size * icon_scale)))
    height = int(max(24, round(int(obj.get("height", base_size)) * icon_scale)))
    x, y = pos_from_obj(obj)
    return add_common(
        {
            "type": "party",
            "name": role,
            "role": role,
            "job": job,
            "jobName": job_name,
            "jobDefault": "job" not in obj and role in DEFAULT_PARTY_JOBS,
            "roleLabel": role_label,
            "roleLabelPlacement": obj.get("roleLabelPlacement", obj.get("role_label_placement", "near-icon")),
            "roleLabelVisible": role_label_visible,
            "icon": icon,
            "image": icon if display_style == "role-number-icon" else obj.get("image", icon),
            "partyDisplayStyle": display_style,
            "guideSection": obj.get("guideSection", obj.get("guide_section", "mechanic_flow")),
            "iconScale": icon_scale,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "rotation": int(obj.get("rotation", 0)),
            "opacity": 100,
        },
        obj,
        obj_id,
    )


def party_role_label_position(spec_obj: dict[str, Any]) -> tuple[float, float]:
    x, y = pos_from_obj(spec_obj)
    role = str(spec_obj.get("role") or spec_obj.get("key") or "").upper()
    role_offsets = {
        "MT": (26.0, 0.0),
        "ST": (-26.0, 0.0),
        "H1": (0.0, -26.0),
        "H2": (0.0, 26.0),
        "D1": (24.0, -18.0),
        "D2": (-24.0, -18.0),
        "D3": (24.0, 18.0),
        "D4": (-24.0, 18.0),
    }
    if role in role_offsets:
        candidate = (x + role_offsets[role][0], y + role_offsets[role][1])
    else:
        radius = math.hypot(x, y)
        inward = (0.0, 1.0) if radius <= 24 else (-x / radius, -y / radius)
        distance = float(spec_obj.get("roleLabelDistance", spec_obj.get("role_label_distance", 26)))
        candidate = (x + inward[0] * distance, y + inward[1] * distance)
    offset = spec_obj.get("roleLabelOffset", spec_obj.get("role_label_offset"))
    return with_offset(candidate, offset)


def build_party_role_label_objects(spec_obj: dict[str, Any], next_id: int, anchor_id: int) -> tuple[list[dict[str, Any]], int]:
    display_style = explicit_party_display_style(spec_obj.get("partyDisplayStyle")) or explicit_party_display_style(spec_obj.get("party_display_style"))
    if display_style == "role-number-icon":
        return [], next_id
    visible = spec_obj.get("roleLabelVisible", spec_obj.get("role_label_visible", True)) is not False
    role_label = spec_obj.get("roleLabel", spec_obj.get("role_label", spec_obj.get("role")))
    if not visible or not role_label:
        return [], next_id
    label_pos = party_role_label_position(spec_obj)
    label_obj = {
        "kind": "text",
        "text": str(role_label),
        "pos": [round(label_pos[0], 3), round(label_pos[1], 3)],
        "fontSize": int(spec_obj.get("roleLabelFontSize", spec_obj.get("role_label_font_size", 11))),
        "labelKind": "party_role",
        "roleLabelAnchorId": anchor_id,
        "labelAnchorId": anchor_id,
        "labelAnchor": object_key(spec_obj),
        "leaderLine": False,
    }
    return [make_text(label_obj, next_id)], next_id + 1


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


def status_visible_on_step(assignment: dict[str, Any], step_index: int) -> bool:
    visible = assignment.get("visibleSteps", assignment.get("visible_steps"))
    if visible is None:
        return True
    if isinstance(visible, str):
        return visible.strip().lower() in {"all", "*", "normal"}
    if not isinstance(visible, list):
        return False
    for item in visible:
        if isinstance(item, int) and item == step_index:
            return True
        if isinstance(item, str) and item.strip().lower() in {"all", "*"}:
            return True
        if isinstance(item, list) and len(item) == 2 and all(isinstance(value, int) for value in item):
            start, end = item
            if start <= step_index <= end:
                return True
    return False


def status_badge_data_url(label: str, color: str = "#5b2b2b", text_color: str = "#ffffff") -> str:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return ""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=color, outline="#f7f7f7", width=4)
    draw.rounded_rectangle([9, 9, 55, 55], radius=9, outline="#101318", width=2)
    text = str(label or "?").strip()[:2] or "?"
    try:
        font = ImageFont.truetype("arial.ttf", 24 if len(text) == 1 else 20)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    x = 32 - (bbox[2] - bbox[0]) / 2
    y = 32 - (bbox[3] - bbox[1]) / 2 - 1
    draw.text((x, y), text, font=font, fill=text_color, stroke_width=1, stroke_fill="#101318")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def status_assignment_role(assignment: dict[str, Any]) -> str:
    value = assignment.get("role")
    if isinstance(value, str) and value.upper() in PARTY_ROLES:
        return value.upper()
    return ""


def status_assignment_icon(assignment: dict[str, Any]) -> tuple[str, str]:
    icon = assignment.get("statusIcon", assignment.get("status_icon", assignment.get("icon")))
    if isinstance(icon, str) and icon.strip():
        return icon.strip(), str(assignment.get("assetStatus", assignment.get("asset_status", "dedicated")))
    raw_token = str(
        assignment.get("iconToken")
        or assignment.get("icon_token")
        or assignment.get("statusName")
        or assignment.get("status_name")
        or assignment.get("kind")
        or "?"
    ).strip()
    token = raw_token.lower().replace(" ", "-").replace("_", "-")
    color, text_color = STATUS_ICON_COLORS.get(token, ("#5b2b2b", "#ffffff"))
    fallback_label = str(assignment.get("fallbackLabel", assignment.get("fallback_label", raw_token[:2] or "?")))
    return status_badge_data_url(fallback_label, color, text_color), "fallback"


def make_status_overlay(
    assignment: dict[str, Any],
    party_obj: dict[str, Any],
    obj_id: int,
    overlay_index: int,
) -> dict[str, Any]:
    role = status_assignment_role(assignment)
    party_width = float(party_obj.get("width", DEFAULT_PLAYER_SIZE))
    party_height = float(party_obj.get("height", DEFAULT_PLAYER_SIZE))
    raw_scale = assignment.get("iconScale", assignment.get("icon_scale", 0.42))
    try:
        scale = max(0.35, min(0.5, float(raw_scale)))
    except (TypeError, ValueError):
        scale = 0.42
    size = max(13, round(min(party_width, party_height) * scale))
    offset_step = size * 0.56
    x = float(party_obj.get("x", 0)) - party_width / 2 + size / 2 + overlay_index * offset_step
    y = float(party_obj.get("y", 0)) + party_height / 2 - size / 2 - overlay_index * 1.5
    icon, asset_status = status_assignment_icon(assignment)
    name = str(assignment.get("statusName", assignment.get("status_name", "Status"))).strip() or "Status"
    result = {
        "kind": "icon",
        "type": "icon",
        "name": f"{role} {name}",
        "image": icon,
        "x": round(x, 3),
        "y": round(y, 3),
        "width": size,
        "height": size,
        "rotation": 0,
        "opacity": int(assignment.get("opacity", 100)),
        "statusOverlay": True,
        "statusRole": role,
        "statusName": name,
        "statusKind": assignment.get("kind", assignment.get("statusKind", assignment.get("status_kind", "debuff"))),
        "decisionGroup": assignment.get("decisionGroup", assignment.get("decision_group", "")),
        "durationLabel": assignment.get("durationLabel", assignment.get("duration_label", "")),
        "stackLabel": assignment.get("stackLabel", assignment.get("stack_label", "")),
        "priorityLabel": assignment.get("priorityLabel", assignment.get("priority_label", "")),
        "anchorRole": role,
        "anchorPartyId": party_obj.get("id"),
        "assetStatus": asset_status,
        "assetFallback": assignment.get("assetFallback", assignment.get("asset_fallback", "status-icon-fallback" if asset_status == "fallback" else "")),
        "fallbackReason": assignment.get("fallbackReason", assignment.get("fallback_reason", "")),
        "visibleSteps": copy.deepcopy(assignment.get("visibleSteps", assignment.get("visible_steps", "all"))),
    }
    source = assignment.get("source")
    confidence = assignment.get("confidence")
    if source:
        result["source"] = source
    if confidence:
        result["confidence"] = confidence
    return add_common(result, assignment, obj_id)


def attach_status_overlays(
    objects: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
    next_id: int,
    step_index: int,
) -> tuple[list[dict[str, Any]], int]:
    if not assignments:
        return objects, next_id
    party_by_role = {
        str(obj.get("role") or obj.get("name") or "").upper(): obj
        for obj in objects
        if isinstance(obj, dict) and obj.get("type") == "party"
    }
    overlays_by_role: dict[str, int] = {}
    overlay_objects: list[dict[str, Any]] = []
    for assignment in assignments:
        if not isinstance(assignment, dict) or not status_visible_on_step(assignment, step_index):
            continue
        role = status_assignment_role(assignment)
        if not role or role not in party_by_role:
            continue
        overlay_index = overlays_by_role.get(role, 0)
        if overlay_index >= 3:
            continue
        overlay_objects.append(make_status_overlay(assignment, party_by_role[role], next_id, overlay_index))
        overlays_by_role[role] = overlay_index + 1
        next_id += 1
    return objects + overlay_objects, next_id


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
    x, y = text_pos_from_obj(obj)
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
    if "labelKind" in obj:
        result["labelKind"] = obj["labelKind"]
    if "labelRole" in obj:
        result["labelRole"] = obj["labelRole"]
    if "label_role" in obj:
        result["labelRole"] = obj["label_role"]
    if "labelBand" in obj:
        result["labelBand"] = obj["labelBand"]
    if "label_band" in obj:
        result["labelBand"] = obj["label_band"]
    if "labelBandIndex" in obj:
        result["labelBandIndex"] = obj["labelBandIndex"]
    if "label_band_index" in obj:
        result["labelBandIndex"] = obj["label_band_index"]
    if "roleLabelAnchorId" in obj:
        result["roleLabelAnchorId"] = obj["roleLabelAnchorId"]
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
    if is_enemy_spec(spec_obj):
        offset = spec_obj.get("labelOffset")
        if math.hypot(x, y) <= 24:
            return with_offset((238.0, 70.0), offset)
        if abs(x) >= abs(y):
            corner_y = 214.0 if y >= 0 else -214.0
            return with_offset((226.0 if x >= 0 else -226.0, corner_y), offset)
        corner_x = 214.0 if x >= 0 else -214.0
        return with_offset((corner_x, 226.0 if y >= 0 else -226.0), offset)
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


def semantic_value(spec_obj: dict[str, Any], nested: dict[str, Any], key: str, fallback: Any = None) -> Any:
    if key in nested:
        return nested[key]
    if key in spec_obj:
        return spec_obj[key]
    return fallback


def damage_pattern_metadata(spec_obj: dict[str, Any], pattern: dict[str, Any], pattern_kind: str) -> dict[str, Any]:
    return {
        "damagePattern": copy.deepcopy(pattern),
        "damagePatternKind": pattern_kind,
        "source": semantic_value(spec_obj, pattern, "source", "Boss"),
        "targets": semantic_value(spec_obj, pattern, "targets", []),
        "resolveIndex": semantic_value(spec_obj, pattern, "resolveIndex", 1),
        "resolveTiming": semantic_value(spec_obj, pattern, "resolveTiming", "cast_snapshot"),
        "aoeIntent": semantic_value(spec_obj, pattern, "aoeIntent", "damage"),
    }


def pattern_object(base: dict[str, Any], metadata: dict[str, Any], *, key: str, label: str | None = None) -> dict[str, Any]:
    result = {**base, **copy.deepcopy(metadata), "key": key}
    if label:
        result["label"] = label
        result.setdefault("labelFontSize", 13)
        result.setdefault("labelPlacement", "auto")
    return result


def expand_damage_pattern_spec(spec_obj: dict[str, Any]) -> list[dict[str, Any]]:
    raw_pattern = spec_obj.get("damagePattern")
    pattern = copy.deepcopy(raw_pattern) if isinstance(raw_pattern, dict) else copy.deepcopy(spec_obj)
    pattern_kind = str(pattern.get("kind") or spec_obj.get("patternKind") or spec_obj.get("pattern_kind") or "").strip()
    if not pattern_kind:
        raise BuildError("damagePattern requires a kind")
    prefix = object_key(spec_obj) or f"damage-{pattern_kind}"
    label = str(pattern.get("label") or spec_obj.get("label") or "").strip() or None
    render_label = pattern.get("renderLabel", spec_obj.get("renderLabel", True)) is not False
    metadata = damage_pattern_metadata(spec_obj, pattern, pattern_kind)
    pos = pattern.get("pos", spec_obj.get("pos", "center"))
    distance = pattern.get("distance", spec_obj.get("distance", DEFAULT_OBJECT_DISTANCE))
    radius = int(pattern.get("radius", spec_obj.get("radius", 240)))
    opacity = int(pattern.get("opacity", spec_obj.get("opacity", 24)))
    color = pattern.get("color", spec_obj.get("color"))

    if pattern_kind == "fan120":
        rotations = pattern.get("rotations", [90, 210, 330])
        return [
            pattern_object(
                {
                    "kind": "cone",
                    "pos": pos,
                    "distance": distance,
                    "radius": radius,
                    "coneAngle": int(pattern.get("angle", 120)),
                    "rotation": rotation,
                    "color": color or "#2aa7ff",
                    "opacity": opacity,
                },
                metadata,
                key=f"{prefix}-{index + 1}",
                label=label if render_label and index == 0 else None,
            )
            for index, rotation in enumerate(rotations)
        ]
    if pattern_kind == "shareFan90":
        return [
            pattern_object(
                {
                    "kind": "cone",
                    "pos": pos,
                    "distance": distance,
                    "radius": radius,
                    "coneAngle": int(pattern.get("angle", 90)),
                    "rotation": float(pattern.get("rotation", 90)),
                    "color": color or "#ff8c00",
                    "opacity": opacity,
                },
                metadata,
                key=prefix,
                label=label if render_label else None,
            )
        ]
    if pattern_kind == "baitTrail":
        points = pattern.get("points", [[-150, -110], [-75, -55], [0, 0], [75, 55], [150, 110]])
        return [
            pattern_object(
                {
                    "kind": "circle",
                    "pos": point,
                    "radius": int(pattern.get("circleRadius", 34)),
                    "color": color or "#d13438",
                    "opacity": opacity,
                    "baitSequence": index + 1,
                },
                metadata,
                key=f"{prefix}-{index + 1}",
                label=label if render_label and index == len(points) - 1 else None,
            )
            for index, point in enumerate(points)
        ]
    if pattern_kind == "towerResolve":
        positions = pattern.get("positions", ["N", "S", "E", "W"])
        return [
            pattern_object(
                {
                    "kind": "tower",
                    "pos": tower_pos,
                    "distance": pattern.get("distance", 190),
                    "radius": int(pattern.get("towerRadius", 42)),
                    "count": int(pattern.get("count", 2)),
                    "color": color or "#bae3ff",
                    "opacity": int(pattern.get("opacity", 62)),
                },
                metadata,
                key=f"{prefix}-{index + 1}",
                label=label if render_label and index == 0 else None,
            )
            for index, tower_pos in enumerate(positions)
        ]
    if pattern_kind == "chargeLine":
        return [
            pattern_object(
                {
                    "kind": "rect",
                    "pos": pos,
                    "distance": distance,
                    "width": int(pattern.get("width", 110)),
                    "height": int(pattern.get("height", 520)),
                    "rotation": float(pattern.get("rotation", 0)),
                    "color": color or "#d13438",
                    "opacity": opacity,
                },
                metadata,
                key=prefix,
                label=label if render_label else None,
            )
        ]
    if pattern_kind == "safeSector":
        safe_metadata = {**metadata, "aoeIntent": semantic_value(spec_obj, pattern, "aoeIntent", "safe")}
        return [
            pattern_object(
                {
                    "kind": "cone",
                    "pos": pos,
                    "distance": distance,
                    "radius": radius,
                    "coneAngle": int(pattern.get("angle", 90)),
                    "rotation": float(pattern.get("rotation", 90)),
                    "color": color or "#8fd14f",
                    "opacity": int(pattern.get("opacity", 18)),
                },
                safe_metadata,
                key=prefix,
                label=label if render_label else None,
            )
        ]
    if pattern_kind == "bossHitbox":
        hitbox_metadata = {**metadata, "aoeIntent": semantic_value(spec_obj, pattern, "aoeIntent", "reference_only")}
        return [
            pattern_object(
                {
                    "kind": "circle",
                    "pos": pos,
                    "distance": distance,
                    "radius": int(pattern.get("radius", 72)),
                    "color": color or "#ffb900",
                    "opacity": int(pattern.get("opacity", 18)),
                    "hollow": True,
                },
                hitbox_metadata,
                key=prefix,
                label=label if render_label else None,
            )
        ]
    raise BuildError(f"unsupported damagePattern kind: {pattern_kind!r}")


def expand_movement_route_spec(spec_obj: dict[str, Any]) -> dict[str, Any]:
    raw_route = spec_obj.get("movementRoute")
    route = copy.deepcopy(raw_route) if isinstance(raw_route, dict) else copy.deepcopy(spec_obj)
    result = copy.deepcopy(spec_obj)
    result["kind"] = str(route.get("kind") or route.get("routeKind") or "arrow")
    for key in ("from", "to", "waypoints", "curve", "distance", "startGap", "endGap", "allowDangerCrossing", "routeCheck"):
        if key in route:
            result[key] = copy.deepcopy(route[key])
    result["arrowStyle"] = route.get("arrowStyle", spec_obj.get("arrowStyle", "movement"))
    result["movementRoute"] = copy.deepcopy(route)
    result["routeIntent"] = route.get("intent", route.get("routeIntent", result["arrowStyle"]))
    for key in (
        "fromRole",
        "fromObject",
        "fromMarker",
        "toRole",
        "toObject",
        "toMarker",
        "toZone",
        "resolveIndex",
        "startLabel",
        "endLabel",
        "snapToTarget",
    ):
        if key in route:
            result[key] = copy.deepcopy(route[key])
    return result


def expand_phase_v_objects(objects_spec: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for spec_obj in objects_spec:
        if not isinstance(spec_obj, dict):
            expanded.append(spec_obj)
            continue
        kind = spec_obj.get("kind")
        if kind == "damagePattern":
            expanded.extend(expand_damage_pattern_spec(spec_obj))
            continue
        if kind == "movementRoute":
            expanded.append(expand_movement_route_spec(spec_obj))
            continue
        expanded.append(spec_obj)
    return expanded


def build_step(step: dict[str, Any], next_id: int) -> tuple[dict[str, Any], int]:
    if not isinstance(step, dict):
        raise BuildError("each step must be an object")
    objects_spec = step.get("objects", [])
    if not isinstance(objects_spec, list):
        raise BuildError("step.objects must be a list")
    objects_spec = normalize_enemy_specs(expand_phase_v_objects(objects_spec))

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

        if spec_obj.get("type") == "enemy" or kind in ENEMY_SPEC_KINDS:
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
        attached_objects: list[dict[str, Any]] = []
        attached_next_id = next_id + 1
        if kind == "party":
            party_labels, attached_next_id = build_party_role_label_objects(spec_obj, attached_next_id, next_id)
            attached_objects.extend(party_labels)
        if kind not in {"text", "label"}:
            label_objects, attached_next_id = build_attached_label_objects(spec_obj, attached_next_id, next_id)
            attached_objects.extend(label_objects)
        objects.extend(attached_objects)
        if attached_objects:
            next_id = attached_next_id - 1
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

    status_assignments = step.get("statusAssignments", step.get("status_assignments", []))
    if not isinstance(status_assignments, list):
        raise BuildError("step.statusAssignments must be a list")
    step_index = int(step.get("_step_index", 0) or 0)
    objects, next_id = attach_status_overlays(objects, status_assignments, next_id, step_index)

    if step.get("title"):
        title_text = step.get("page_title") or step["title"]
        objects.append(
            make_text(
                {
                    "text": title_text,
                    "pos": step.get("titlePos", "N"),
                    "distance": step.get("titleDistance", 322),
                    "fontSize": step.get("titleFontSize", style_value("title_font_size", 18)),
                    "labelRole": "page_title",
                    "labelBand": "top",
                    "labelKind": "mechanic",
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
        "teaching_question",
        "why_this_frame_exists",
        "changed_objects_only",
        "page_title",
        "annotation_callouts",
        "movement_required",
        "flow_kind",
        "guide_section",
        "party_cluster",
        "stack_group",
        "partial_observation",
        "partial",
        "local_view",
        "statusAssignments",
        "status_assignment_contract",
    ):
        if key in step:
            built_step[key] = step[key]
    built_step.pop("_step_index", None)
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


def normalize_guide_section(value: Any, default: str = "mechanic_flow") -> str:
    if not isinstance(value, str) or not value.strip():
        return default
    token = value.strip().lower().replace(" ", "_")
    if token in FLOW_EXAMPLE_TOKENS:
        return "flow_example"
    if token in MECHANIC_FLOW_TOKENS:
        return "mechanic_flow"
    return default


def guide_section_from_spec(spec: dict[str, Any]) -> str:
    for key in ("guide_section", "guideSection", "figure_type", "figureType", "diagram_type", "diagramType"):
        if key in spec:
            return normalize_guide_section(spec.get(key))
    metadata = spec.get("metadata")
    if isinstance(metadata, dict):
        for key in ("guide_section", "guideSection", "figure_type", "figureType", "diagram_type", "diagramType"):
            if key in metadata:
                return normalize_guide_section(metadata.get(key))
    return "mechanic_flow"


def party_display_style_for_section(section: str) -> str:
    return "job-icon" if section == "flow_example" else "role-number-icon"


def explicit_party_display_style(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    token = value.strip().lower().replace(" ", "-").replace("_", "-")
    if token in {"job", "job-icon", "job-icons", "job-default", "career-icon", "职业图标"}:
        return "job-icon"
    if token in {"role", "role-icon", "role-icons", "role-number", "role-number-icon", "role-number-icons", "numbered-role-icon", "职能图标", "编号职能图标"}:
        return "role-number-icon"
    return None


def apply_party_display_policy(objects: list[dict[str, Any]], section: str) -> None:
    style = party_display_style_for_section(section)
    for obj in objects:
        if spec_object_kind(obj) != "party":
            continue
        explicit = (
            explicit_party_display_style(obj.get("partyDisplayStyle"))
            or explicit_party_display_style(obj.get("party_display_style"))
            or explicit_party_display_style(obj.get("iconStyle"))
            or explicit_party_display_style(obj.get("icon_style"))
        )
        obj.setdefault("guideSection", section)
        obj.setdefault("partyDisplayStyle", explicit or style)


def is_partial_observation_step(step: dict[str, Any]) -> bool:
    return bool(step.get("partial_observation") or step.get("partial") or step.get("local_view"))


def default_party_objects(distance: int = 108) -> list[dict[str, Any]]:
    return [{"kind": "party", "key": role, "role": role, "pos": ROLE_DIR[role], "distance": distance} for role in PARTY_ROLES]


def default_enemy_object() -> dict[str, Any]:
    return {"kind": "boss", "key": "boss", "name": "Boss", "displayName": "Boss", "pos": "center", "radius": 42, "labelPlacement": "auto"}


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
    return any(is_enemy_spec(obj) for obj in objects)


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
    root_guide_section = guide_section_from_spec(spec)
    root_marker_presets = spec.get("markerPresets", [])
    if isinstance(root_marker_presets, str):
        root_marker_presets = [root_marker_presets]
    if not isinstance(root_marker_presets, list):
        raise BuildError("markerPresets must be a string or list")
    contract, contract_active = normalize_scene_contract(spec)
    root_status_assignments = spec.get("statusAssignments", spec.get("status_assignments", []))
    if root_status_assignments is None:
        root_status_assignments = []
    if not isinstance(root_status_assignments, list):
        raise BuildError("statusAssignments must be a list")

    for step_index, raw_step in enumerate(spec["steps"], start=1):
        step = copy.deepcopy(raw_step)
        step["_step_index"] = step_index
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
        step_guide_section = root_guide_section
        for key in ("guide_section", "guideSection", "figure_type", "figureType", "diagram_type", "diagramType"):
            if key in step:
                step_guide_section = normalize_guide_section(step.get(key), root_guide_section)
                break
        apply_party_display_policy(objects, step_guide_section)
        step_status_assignments = step.get("statusAssignments", step.get("status_assignments", []))
        if step_status_assignments is None:
            step_status_assignments = []
        if not isinstance(step_status_assignments, list):
            raise BuildError("step.statusAssignments must be a list")
        combined_status_assignments = copy.deepcopy(root_status_assignments) + copy.deepcopy(step_status_assignments)
        if combined_status_assignments:
            step["statusAssignments"] = combined_status_assignments
        step["objects"] = objects
        step["guide_section"] = step_guide_section
        for transient_key in ("inherit", "remove", "updates", "replace", "markerPresets", "focusRoles", "focus_roles", "guideSection", "figureType", "diagramType"):
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
    scene["guide_section"] = guide_section_from_spec(spec)
    scene["party_display_policy"] = party_display_style_for_section(scene["guide_section"])
    if spec.get("name"):
        scene["name"] = spec["name"]
    if spec.get("style"):
        scene["style"] = spec["style"]
    if isinstance(spec.get("scene_contract"), dict):
        scene["scene_contract"] = copy.deepcopy(spec["scene_contract"])
    if isinstance(spec.get("annotation_contract"), dict):
        scene["annotation_contract"] = copy.deepcopy(spec["annotation_contract"])
    if isinstance(spec.get("mechanic_semantics_contract"), dict):
        scene["mechanic_semantics_contract"] = copy.deepcopy(spec["mechanic_semantics_contract"])
    if isinstance(spec.get("status_assignment_contract"), dict):
        scene["status_assignment_contract"] = copy.deepcopy(spec["status_assignment_contract"])
    if isinstance(spec.get("statusAssignments"), list):
        scene["statusAssignments"] = copy.deepcopy(spec["statusAssignments"])
    elif isinstance(spec.get("status_assignments"), list):
        scene["statusAssignments"] = copy.deepcopy(spec["status_assignments"])
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
