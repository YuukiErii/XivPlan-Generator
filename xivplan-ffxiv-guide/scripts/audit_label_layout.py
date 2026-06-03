#!/usr/bin/env python3
"""Audit text label placement in XivPlan scenes."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import sys
from pathlib import Path
from typing import Any


TEXT_TYPES = {"text"}
ANCHOR_TYPES = {"party", "enemy", "marker"}
MECHANIC_TYPES = {"arc", "circle", "cone", "donut", "exaflare", "eye", "knockback", "line", "lineStack", "polygon", "rect", "stack", "starburst", "tower"}
FLOW_TYPES = {"arrow", "tether"}
PARTY_ROLES = {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"}
SHORT_ROLE_TAGS = PARTY_ROLES | {str(index) for index in range(1, 9)}
MECHANIC_LABEL_HINTS = (
    "雷",
    "火",
    "冰",
    "光",
    "暗",
    "塔",
    "轴",
    "线",
    "圈",
    "分摊",
    "分散",
    "诱导",
    "优先",
    "倒数",
    "目标环",
    "安全",
    "危险",
    "左排",
    "右排",
)


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def text_width(text: str, font_size: float) -> float:
    width = 0.0
    for char in text:
        width += font_size if ord(char) > 127 else font_size * 0.58
    return max(width, font_size)


def label_text(obj: dict[str, Any]) -> str:
    return str(obj.get("text", "")).strip()


def is_short_role_or_marker_label(text: str) -> bool:
    value = text.strip()
    upper = value.upper()
    if upper in SHORT_ROLE_TAGS:
        return True
    if len(value) <= 6 and any(role in upper for role in PARTY_ROLES):
        return True
    if len(value) <= 5 and all(char.isdigit() or char in "/-" for char in value):
        return True
    if len(value) <= 5 and any(char.isdigit() for char in value) and any(hint in value for hint in ("雷", "火", "塔", "线")):
        return True
    return value in {"高后", "低右", "高前", "低左", "近", "远", "左", "右", "上", "下"}


def classify_label(obj: dict[str, Any]) -> str:
    if obj.get("type") != "text":
        return "notLabel"
    explicit = obj.get("labelRole") or obj.get("label_role")
    if isinstance(explicit, str) and explicit.strip():
        normalized = explicit.strip()
        if normalized in {"page_title", "axis", "priority", "mechanic", "footer"}:
            return "mechanicCallout"
        if normalized in {"role_badge", "party_role"}:
            return "roleBadge"
        return "attachedLabel"
    kind = obj.get("labelKind") or obj.get("label_kind")
    if isinstance(kind, str):
        if kind in {"party_role", "roleBadge", "role_badge"}:
            return "roleBadge"
        if kind in {"mechanic", "mechanicCallout", "callout"}:
            return "mechanicCallout"
        if kind in {"attachedLabel", "attached", "auto"}:
            return "attachedLabel"
    text = label_text(obj)
    if is_short_role_or_marker_label(text):
        return "roleBadge"
    if obj.get("labelAnchor") is not None or obj.get("labelAnchorId") is not None:
        return "attachedLabel"
    if any(hint in text for hint in MECHANIC_LABEL_HINTS):
        return "mechanicCallout"
    return "floatingText"


def bbox_for_object(obj: dict[str, Any], reference_mode: str = "strict") -> tuple[float, float, float, float] | None:
    if not isinstance(obj.get("x"), (int, float)) or not isinstance(obj.get("y"), (int, float)):
        return None
    x = float(obj["x"])
    y = float(obj["y"])
    obj_type = obj.get("type")
    if obj_type == "text":
        font_size = float(obj.get("fontSize", 14) or 14)
        text = str(obj.get("text", ""))
        label_class = classify_label(obj)
        width = text_width(text, font_size) + 10
        height = font_size * 1.35 + 6
        if label_class == "roleBadge":
            width = text_width(text, font_size) + 3
            height = font_size * 1.05 + 2
        elif reference_mode == "gold" and label_class in {"attachedLabel", "mechanicCallout"}:
            width = text_width(text, font_size) + 5
            height = font_size * 1.15 + 3
        return x - width / 2, y - height / 2, x + width / 2, y + height / 2
    if obj_type in {"party", "marker", "image", "icon"}:
        width = float(obj.get("width", 32) or 32)
        height = float(obj.get("height", 32) or 32)
        return x - width / 2, y - height / 2, x + width / 2, y + height / 2
    radius = obj.get("radius")
    if isinstance(radius, (int, float)):
        radius = float(radius)
        return x - radius, y - radius, x + radius, y + radius
    width = obj.get("width")
    height = obj.get("height")
    if isinstance(width, (int, float)) or isinstance(height, (int, float)):
        w = float(width if isinstance(width, (int, float)) else 8)
        h = float(height if isinstance(height, (int, float)) else 8)
        pad = 5 if obj_type in FLOW_TYPES else 0
        return x - w / 2 - pad, y - h / 2 - pad, x + w / 2 + pad, y + h / 2 + pad
    return None


def overlap_area(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> float:
    dx = min(left[2], right[2]) - max(left[0], right[0])
    dy = min(left[3], right[3]) - max(left[1], right[1])
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy


def bbox_area(box: tuple[float, float, float, float]) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def center(obj: dict[str, Any]) -> tuple[float, float]:
    return float(obj.get("x", 0) or 0), float(obj.get("y", 0) or 0)


def label_anchor_object(text_obj: dict[str, Any], objects: list[dict[str, Any]]) -> dict[str, Any] | None:
    anchor_id = text_obj.get("labelAnchorId")
    if isinstance(anchor_id, int):
        for obj in objects:
            if obj.get("id") == anchor_id:
                return obj
    anchor_key = text_obj.get("labelAnchor")
    if isinstance(anchor_key, str) and anchor_key:
        lowered = anchor_key.lower()
        for obj in objects:
            for key in ("key", "sourceKey", "name", "role"):
                value = obj.get(key)
                if isinstance(value, str) and value.lower() == lowered:
                    return obj
    return None


def max_anchor_distance(text_obj: dict[str, Any], anchor_obj: dict[str, Any] | None) -> float:
    threshold = 180.0 if text_obj.get("leaderLine") else 130.0
    if anchor_obj is not None and isinstance(anchor_obj.get("radius"), (int, float)):
        threshold = max(threshold, float(anchor_obj["radius"]) + 120.0)
    return threshold


def issue_severity(
    text_box: tuple[float, float, float, float],
    other_box: tuple[float, float, float, float],
    other_obj: dict[str, Any],
    *,
    text_obj: dict[str, Any],
    reference_mode: str = "strict",
) -> str:
    overlap = overlap_area(text_box, other_box)
    if overlap <= 0:
        return "none"
    other_type = str(other_obj.get("type", "unknown"))
    ratio = overlap / max(bbox_area(text_box), 1)
    label_class = classify_label(text_obj)
    if reference_mode == "gold":
        if other_type != "text":
            return "review" if ratio >= 0.6 else "none"
        other_label_class = classify_label(other_obj)
        if label_class == "floatingText" and other_label_class == "floatingText" and ratio >= 0.88:
            return "severe"
        if label_class == "roleBadge" and other_type in ANCHOR_TYPES | MECHANIC_TYPES | FLOW_TYPES:
            return "review" if ratio >= 0.72 else "none"
        if label_class in {"attachedLabel", "mechanicCallout"} and other_type in ANCHOR_TYPES | MECHANIC_TYPES | FLOW_TYPES:
            return "review" if ratio >= 0.58 else "none"
        if other_type == "text" and (label_class != "floatingText" or other_label_class != "floatingText"):
            return "review"
        return "review"
    if other_type in ANCHOR_TYPES and ratio >= 0.08:
        return "severe"
    if other_type in FLOW_TYPES and ratio >= 0.12:
        return "severe"
    if other_type in MECHANIC_TYPES and float(other_obj.get("opacity", 100) or 100) <= 20:
        return "none"
    if other_type in MECHANIC_TYPES and float(other_obj.get("opacity", 100) or 100) < 35:
        return "review"
    if ratio >= 0.2:
        return "severe"
    return "review"


def audit_step(step: dict[str, Any], step_index: int, reference_mode: str = "strict") -> dict[str, Any]:
    objects = [obj for obj in step.get("objects", []) if isinstance(obj, dict)]
    bboxes = [(index, obj, bbox_for_object(obj, reference_mode=reference_mode)) for index, obj in enumerate(objects)]
    text_items = [(index, obj, box) for index, obj, box in bboxes if box and obj.get("type") == "text"]
    issues: list[dict[str, Any]] = []
    label_classes = Counter(classify_label(obj) for _index, obj, _box in text_items)

    for left_i, left_obj, left_box in text_items:
        for right_i, right_obj, right_box in bboxes:
            if right_box is None or right_i == left_i:
                continue
            right_type = str(right_obj.get("type", "unknown"))
            if right_type == "text" and right_i < left_i:
                continue
            if left_obj.get("labelKind") == "party_role" or right_obj.get("labelKind") == "party_role":
                continue
            severity = issue_severity(left_box, right_box, right_obj, text_obj=left_obj, reference_mode=reference_mode)
            if severity == "none":
                continue
            overlap = round(overlap_area(left_box, right_box), 2)
            label_class = classify_label(left_obj)
            issue_kind = "text_overlap" if right_type == "text" else f"text_vs_{right_type}"
            if reference_mode == "gold" and severity == "review" and label_class in {"attachedLabel", "roleBadge", "mechanicCallout"}:
                issue_kind = f"dense_{label_class}"
            issues.append(
                {
                    "severity": severity,
                    "kind": issue_kind,
                    "text": str(left_obj.get("text", "")),
                    "text_id": left_obj.get("id"),
                    "other_id": right_obj.get("id"),
                    "other_type": right_type,
                    "label_class": label_class,
                    "overlap_area": overlap,
                }
            )

    for text_index, text_obj, _box in text_items:
        if text_obj.get("labelAnchor") is None and text_obj.get("labelAnchorId") is None:
            continue
        tx, ty = center(text_obj)
        anchor_obj = label_anchor_object(text_obj, objects)
        if anchor_obj is not None:
            nearest_distance = math.dist((tx, ty), center(anchor_obj))
        else:
            nearest_distance = min(
                (
                    math.dist((tx, ty), center(obj))
                    for index, obj, box in bboxes
                    if index != text_index and obj.get("type") in ANCHOR_TYPES | MECHANIC_TYPES
                ),
                default=0.0,
            )
        if nearest_distance > max_anchor_distance(text_obj, anchor_obj):
            issues.append(
                {
                    "severity": "review",
                    "kind": "label_far_from_anchor",
                    "text": str(text_obj.get("text", "")),
                    "text_id": text_obj.get("id"),
                    "distance": round(nearest_distance, 2),
                }
            )

    severe_count = sum(1 for issue in issues if issue["severity"] == "severe")
    review_count = sum(1 for issue in issues if issue["severity"] == "review")
    return {
        "step": step_index,
        "title": step.get("title", f"Step {step_index}"),
        "labels": len(text_items),
        "label_classes": dict(sorted(label_classes.items())),
        "severe_collisions": severe_count,
        "review_items": review_count,
        "issues": issues,
    }


def audit_scene(path: Path, reference_mode: str = "strict") -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")
    per_step = [audit_step(step, index, reference_mode=reference_mode) for index, step in enumerate(steps, start=1) if isinstance(step, dict)]
    severe = sum(item["severe_collisions"] for item in per_step)
    review = sum(item["review_items"] for item in per_step)
    label_classes: Counter[str] = Counter()
    for step in per_step:
        label_classes.update(step.get("label_classes", {}))
    return {
        "path": str(path),
        "reference_mode": reference_mode,
        "steps": len(per_step),
        "labels": sum(item["labels"] for item in per_step),
        "label_classes": dict(sorted(label_classes.items())),
        "severe_collisions": severe,
        "review_items": review,
        "ok": severe == 0,
        "per_step": per_step,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Label Layout Audit",
        "",
        "| Scene | Status | Steps | Labels | Severe | Review |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {Path(result['path']).name} | {'PASS' if result['ok'] else 'FAIL'} | {result['steps']} | {result['labels']} | {result['severe_collisions']} | {result['review_items']} |"
        )
    lines.extend(["", "## Issues", ""])
    for result in results:
        for step in result["per_step"]:
            for issue in step["issues"]:
                lines.append(
                    "- {scene} step {step}: [{severity}] {kind} `{text}` other={other}".format(
                        scene=Path(result["path"]).name,
                        step=step["step"],
                        severity=issue["severity"],
                        kind=issue["kind"],
                        text=issue.get("text", ""),
                        other=issue.get("other_id", issue.get("distance", "")),
                    )
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit text label collisions in XivPlan scenes.")
    parser.add_argument("paths", type=Path, nargs="+", help="One or more .xivplan files")
    parser.add_argument("--reference-mode", choices=("strict", "gold"), default="strict", help="Use gold to profile dense human reference scenes without treating attached labels as generator failures")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        results = [audit_scene(path, reference_mode=args.reference_mode) for path in args.paths]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(results), encoding="utf-8")

    for result in results:
        print(f"{result['path']}: {'PASS' if result['ok'] else 'FAIL'} severe={result['severe_collisions']} review={result['review_items']}")
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
