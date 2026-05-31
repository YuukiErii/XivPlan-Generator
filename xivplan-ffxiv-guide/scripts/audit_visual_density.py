#!/usr/bin/env python3
"""Audit XivPlan visual density and layer coverage for guide diagrams."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


KEY_LAYER_GROUPS = {
    "marker": {"marker"},
    "party": {"party"},
    "enemy": {"enemy"},
    "text": {"text"},
    "mechanic_zone": {"arc", "circle", "cone", "donut", "exaflare", "eye", "knockback", "line", "lineStack", "polygon", "proximity", "rect", "stack", "starburst", "tower", "triangle"},
    "arrow": {"arrow", "tether"},
}
REQUIRED_LAYERS = {"marker", "party", "enemy", "text", "mechanic_zone"}


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def step_object_types(step: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for obj in step.get("objects", []):
        if isinstance(obj, dict) and isinstance(obj.get("type"), str):
            counts[obj["type"]] += 1
    return counts


def covered_layers(type_counts: Counter[str]) -> dict[str, bool]:
    return {
        layer: any(type_counts.get(obj_type, 0) > 0 for obj_type in obj_types)
        for layer, obj_types in KEY_LAYER_GROUPS.items()
    }


def primary_mechanic_count(type_counts: Counter[str]) -> int:
    baseline = {"marker", "party", "enemy", "text"}
    return sum(count for obj_type, count in type_counts.items() if obj_type not in baseline)


def audit_scene(path: Path) -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")

    per_step: list[dict[str, Any]] = []
    total_counts: Counter[str] = Counter()
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        counts = step_object_types(step)
        total_counts.update(counts)
        object_count = sum(counts.values())
        mechanics = primary_mechanic_count(counts)
        per_step.append(
            {
                "step": index,
                "title": step.get("title", f"Step {index}"),
                "objects": object_count,
                "types": dict(sorted(counts.items())),
                "primary_mechanics": mechanics,
                "single_step_focus": mechanics <= 16 and object_count <= 45,
            }
        )

    avg_objects = round(sum(item["objects"] for item in per_step) / len(per_step), 2) if per_step else 0
    layers = covered_layers(total_counts)
    missing_layers = [layer for layer, present in layers.items() if not present]
    missing_required_layers = [layer for layer in missing_layers if layer in REQUIRED_LAYERS]
    dense_steps = [item["step"] for item in per_step if not item["single_step_focus"]]
    summary = (
        "KING X-like density: good"
        if not missing_required_layers and avg_objects >= 12 and not dense_steps
        else "KING X-like density: review recommended"
    )
    return {
        "path": str(path),
        "steps": len(per_step),
        "objects": sum(total_counts.values()),
        "avg_objects_per_step": avg_objects,
        "types": dict(sorted(total_counts.items())),
        "layers": layers,
        "missing_layers": missing_layers,
        "missing_required_layers": missing_required_layers,
        "dense_steps": dense_steps,
        "per_step": per_step,
        "summary": summary,
        "ok": not missing_required_layers and not dense_steps and len(per_step) > 0,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Visual Density Audit",
        "",
        "| Scene | Steps | Objects | Avg / Step | Missing Layers | Dense Steps | Summary |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for result in results:
        lines.append(
            "| {scene} | {steps} | {objects} | {avg} | {missing} | {dense} | {summary} |".format(
                scene=Path(result["path"]).name,
                steps=result["steps"],
                objects=result["objects"],
                avg=result["avg_objects_per_step"],
                missing=", ".join(result["missing_layers"]) or "none",
                dense=", ".join(str(step) for step in result["dense_steps"]) or "none",
                summary=result["summary"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit XivPlan visual density and layer coverage.")
    parser.add_argument("paths", type=Path, nargs="+", help="One or more .xivplan files")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        results = [audit_scene(path) for path in args.paths]
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
        print(f"{result['path']}: {result['summary']}")
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
