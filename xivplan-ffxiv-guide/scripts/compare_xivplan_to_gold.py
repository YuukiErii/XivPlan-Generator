#!/usr/bin/env python3
"""Compare a generated XivPlan scene against a gold human reference."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PARTY_ROLES = {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"}
DEFAULT_PARTY_ICONS = {
    "MT": "/actor/DRK.png",
    "ST": "/actor/PLD.png",
    "H1": "/actor/AST.png",
    "H2": "/actor/SCH.png",
    "D1": "/actor/SAM.png",
    "D2": "/actor/DRG.png",
    "D3": "/actor/BRD.png",
    "D4": "/actor/PCT.png",
}
MECHANIC_ZONE_TYPES = {
    "arc",
    "circle",
    "cone",
    "donut",
    "exaflare",
    "eye",
    "knockback",
    "line",
    "lineKnockAway",
    "lineKnockback",
    "lineStack",
    "polygon",
    "proximity",
    "rect",
    "rightTriangle",
    "stack",
    "starburst",
    "tower",
    "triangle",
}
FLOW_SEMANTIC_KEYS = {
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
}
RANGE_SEMANTIC_KEYS = {"label", "source", "targets", "targetRoles", "resolveIndex", "resolveTiming", "aoeIntent", "damagePattern"}


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scene_steps(scene: dict[str, Any]) -> list[dict[str, Any]]:
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")
    return [step for step in steps if isinstance(step, dict)]


def step_objects(step: dict[str, Any]) -> list[dict[str, Any]]:
    return [obj for obj in step.get("objects", []) if isinstance(obj, dict)]


def all_objects(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [obj for step in steps for obj in step_objects(step)]


def average(values: list[int | float]) -> float:
    return round(float(statistics.fmean(values)), 2) if values else 0.0


def role_from_legacy_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    parts = value.strip().replace("/", " ").split()
    if parts and parts[0].upper() in PARTY_ROLES:
        return parts[0].upper()
    return ""


def job_from_legacy_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    parts = value.strip().replace("/", " ").split()
    if len(parts) >= 2 and parts[0].upper() in PARTY_ROLES:
        return parts[1].upper()
    return ""


def party_role(obj: dict[str, Any]) -> tuple[str, str]:
    for key in ("role", "name", "label", "roleLabel"):
        value = obj.get(key)
        if isinstance(value, str) and value.upper() in PARTY_ROLES:
            return value.upper(), "explicit"
    for key in ("name", "label", "roleLabel"):
        role = role_from_legacy_name(obj.get(key))
        if role:
            return role, "legacy-prefix"
    return "", "missing"


def party_job(obj: dict[str, Any]) -> str:
    value = obj.get("job") or obj.get("jobName") or obj.get("job_name")
    if isinstance(value, str) and value.strip():
        return value.strip()
    for key in ("name", "label"):
        job = job_from_legacy_name(obj.get(key))
        if job:
            return job
    icon = str(obj.get("icon") or obj.get("image") or "").replace("\\", "/")
    if icon.startswith("/actor/") and icon.endswith(".png"):
        return icon.rsplit("/", 1)[-1].split(".", 1)[0]
    return ""


def arena_descriptor(scene: dict[str, Any]) -> str:
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    if arena.get("backgroundImage"):
        return str(arena["backgroundImage"])
    if arena.get("preset"):
        return str(arena["preset"])
    if arena.get("shape"):
        return str(arena["shape"])
    return "none"


def arena_profile(scene: dict[str, Any], objects: list[dict[str, Any]]) -> dict[str, Any]:
    arena = scene.get("arena") if isinstance(scene.get("arena"), dict) else {}
    waymarks = sorted({str(obj.get("name") or obj.get("marker") or obj.get("label")).upper() for obj in objects if obj.get("type") == "marker" and str(obj.get("name") or obj.get("marker") or obj.get("label")).upper() in {"A", "B", "C", "D", "1", "2", "3", "4"}})
    axis_labels = [
        str(obj.get("text", "")).strip()
        for obj in objects
        if obj.get("type") == "text" and any(token in str(obj.get("text", "")) for token in ("轴", "axis", "AC", "BD"))
    ]
    return {
        "descriptor": arena_descriptor(scene),
        "backgroundImage": arena.get("backgroundImage"),
        "preset": arena.get("preset"),
        "shape": arena.get("shape"),
        "grid": arena.get("grid"),
        "ticks": arena.get("ticks"),
        "waymarks": waymarks,
        "axis_labels": axis_labels,
        "axis_label_count": len(axis_labels),
    }


def text_profile(steps: list[dict[str, Any]], objects: list[dict[str, Any]]) -> dict[str, Any]:
    text_objects = [obj for obj in objects if obj.get("type") == "text"]
    lengths = [len(str(obj.get("text", ""))) for obj in text_objects]
    guide_text_chars = sum(len(str(step.get("guide_text", ""))) for step in steps)
    in_scene_chars = sum(lengths)
    total_explanation_chars = in_scene_chars + guide_text_chars
    role_badge_texts = [
        str(obj.get("text", "")).strip()
        for obj in text_objects
        if str(obj.get("text", "")).strip().upper() in PARTY_ROLES
    ]
    return {
        "text_objects": len(text_objects),
        "in_scene_text_chars": in_scene_chars,
        "avg_text_chars": round(average(lengths), 2),
        "max_text_chars": max(lengths) if lengths else 0,
        "guide_text_chars": guide_text_chars,
        "in_scene_explanation_ratio": round(in_scene_chars / total_explanation_chars, 4) if total_explanation_chars else 0.0,
        "guide_text_migration_gap": round(guide_text_chars / total_explanation_chars, 4) if total_explanation_chars else 0.0,
        "role_badge_text_objects": len(role_badge_texts),
    }


def arrow_profile(objects: list[dict[str, Any]]) -> dict[str, Any]:
    arrows = [obj for obj in objects if obj.get("type") == "arrow"]
    semantic_counts = Counter()
    for obj in arrows:
        for key in FLOW_SEMANTIC_KEYS:
            if obj.get(key) not in (None, "", [], {}):
                semantic_counts[key] += 1
    return {
        "arrows": len(arrows),
        "styles": dict(sorted(Counter(str(obj.get("arrowStyle") or "default") for obj in arrows).items())),
        "with_flow_start_end": sum(1 for obj in arrows if isinstance(obj.get("flowStart"), list) and isinstance(obj.get("flowEnd"), list)),
        "with_from_to_semantics": sum(1 for obj in arrows if any(obj.get(key) not in (None, "", [], {}) for key in ("fromRole", "fromObject", "fromMarker")) and any(obj.get(key) not in (None, "", [], {}) for key in ("toRole", "toObject", "toMarker", "toZone"))),
        "with_resolve_index": sum(1 for obj in arrows if obj.get("resolveIndex") not in (None, "")),
        "semantic_fields": dict(sorted(semantic_counts.items())),
    }


def mechanic_profile(objects: list[dict[str, Any]]) -> dict[str, Any]:
    mechanics = [obj for obj in objects if obj.get("type") in MECHANIC_ZONE_TYPES]
    semantic_counts = Counter()
    for obj in mechanics:
        for key in RANGE_SEMANTIC_KEYS:
            if obj.get(key) not in (None, "", [], {}):
                semantic_counts[key] += 1
    return {
        "mechanic_range_zones": len(mechanics),
        "types": dict(sorted(Counter(str(obj.get("type")) for obj in mechanics).items())),
        "with_semantic_fields": sum(1 for obj in mechanics if any(obj.get(key) not in (None, "", [], {}) for key in RANGE_SEMANTIC_KEYS)),
        "semantic_fields": dict(sorted(semantic_counts.items())),
    }


def party_profile(objects: list[dict[str, Any]]) -> dict[str, Any]:
    party = [obj for obj in objects if obj.get("type") == "party"]
    roles: Counter[str] = Counter()
    role_sources: Counter[str] = Counter()
    jobs: Counter[str] = Counter()
    official_icons = 0
    for obj in party:
        role, source = party_role(obj)
        if role:
            roles[role] += 1
        role_sources[source] += 1
        job = party_job(obj)
        if job:
            jobs[job] += 1
        icon = str(obj.get("icon") or obj.get("image") or "").replace("\\", "/")
        if icon in DEFAULT_PARTY_ICONS.values():
            official_icons += 1
    return {
        "party_objects": len(party),
        "roles": dict(sorted(roles.items())),
        "role_sources": dict(sorted(role_sources.items())),
        "jobs": dict(sorted(jobs.items())),
        "official_job_icons": official_icons,
        "legacy_role_prefix_count": role_sources.get("legacy-prefix", 0),
        "compatible_role_set": sorted(roles),
        "full_party_compatible": PARTY_ROLES <= set(roles),
    }


def profile_scene(path: Path) -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene_steps(scene)
    objects = all_objects(steps)
    type_counts = Counter(str(obj.get("type")) for obj in objects if obj.get("type"))
    objects_per_step = [len(step_objects(step)) for step in steps]
    return {
        "path": str(path),
        "name": scene.get("name") or path.stem,
        "steps": len(steps),
        "objects": len(objects),
        "avg_objects_per_step": round(average(objects_per_step), 2),
        "type_counts": dict(sorted(type_counts.items())),
        "density": {
            "objects_per_step": objects_per_step,
            "min_objects_per_step": min(objects_per_step) if objects_per_step else 0,
            "max_objects_per_step": max(objects_per_step) if objects_per_step else 0,
        },
        "text": text_profile(steps, objects),
        "arrows": arrow_profile(objects),
        "mechanics": mechanic_profile(objects),
        "arena": arena_profile(scene, objects),
        "party": party_profile(objects),
    }


def ratio(generated: float, gold: float) -> float:
    return round(generated / gold, 4) if gold else 0.0


def compare_profiles(generated: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    return {
        "steps": {"generated": generated["steps"], "gold": gold["steps"], "ratio": ratio(generated["steps"], gold["steps"])},
        "objects": {"generated": generated["objects"], "gold": gold["objects"], "ratio": ratio(generated["objects"], gold["objects"])},
        "avg_objects_per_step": {"generated": generated["avg_objects_per_step"], "gold": gold["avg_objects_per_step"], "ratio": ratio(generated["avg_objects_per_step"], gold["avg_objects_per_step"])},
        "text_objects": {"generated": generated["text"]["text_objects"], "gold": gold["text"]["text_objects"], "ratio": ratio(generated["text"]["text_objects"], gold["text"]["text_objects"])},
        "in_scene_text_chars": {"generated": generated["text"]["in_scene_text_chars"], "gold": gold["text"]["in_scene_text_chars"], "ratio": ratio(generated["text"]["in_scene_text_chars"], gold["text"]["in_scene_text_chars"])},
        "mechanic_range_zones": {"generated": generated["mechanics"]["mechanic_range_zones"], "gold": gold["mechanics"]["mechanic_range_zones"], "ratio": ratio(generated["mechanics"]["mechanic_range_zones"], gold["mechanics"]["mechanic_range_zones"])},
        "arrows": {"generated": generated["arrows"]["arrows"], "gold": gold["arrows"]["arrows"], "ratio": ratio(generated["arrows"]["arrows"], gold["arrows"]["arrows"])},
        "arena": {"generated": generated["arena"]["descriptor"], "gold": gold["arena"]["descriptor"], "match": generated["arena"]["descriptor"] == gold["arena"]["descriptor"]},
    }


def add_gap(gaps: list[dict[str, Any]], dimension: str, generated: Any, gold: Any, message: str, suggestion: str, severity: str = "gap") -> None:
    gaps.append(
        {
            "dimension": dimension,
            "severity": severity,
            "generated": generated,
            "gold": gold,
            "message": message,
            "suggestion": suggestion,
        }
    )


def deficit_report(generated: dict[str, Any], gold: dict[str, Any], deltas: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if deltas["steps"]["ratio"] < 0.8:
        add_gap(gaps, "storyboard", generated["steps"], gold["steps"], "Generated scene has far fewer steps than the gold reference.", "Split complex mechanics into branch/read/move/resolve/reset frames.")
    if deltas["objects"]["ratio"] < 0.75:
        add_gap(gaps, "density", generated["objects"], gold["objects"], "Generated scene carries much less total visual information.", "Move more guide semantics into in-scene labels, ranges, and overlays.")
    if deltas["text_objects"]["ratio"] < 0.5 or deltas["in_scene_text_chars"]["ratio"] < 0.5:
        add_gap(gaps, "in_scene_text", generated["text"], gold["text"], "Generated explanation is still mostly outside the diagram surface.", "Convert teaching_question and guide_text into page titles, axis labels, priority labels, and short callouts.")
    if deltas["mechanic_range_zones"]["ratio"] < 0.5:
        add_gap(gaps, "mechanic_geometry", generated["mechanics"], gold["mechanics"], "Generated scene lacks the gold reference range/geometry density.", "Add cone/rect/target-ring/safe-sector semantics for actual damage timing and responsibility.")
    if generated["arrows"]["arrows"] and generated["arrows"]["with_from_to_semantics"] < generated["arrows"]["arrows"]:
        add_gap(gaps, "arrow_semantics", generated["arrows"], gold["arrows"], "Generated arrows exist but lack from/to/resolve metadata.", "Add movementRoute fields such as fromRole, toRole or toZone, resolveIndex, startLabel, endLabel, and snapToTarget.")
    if not deltas["arena"]["match"]:
        add_gap(gaps, "arena_context", generated["arena"]["descriptor"], gold["arena"]["descriptor"], "Generated arena/background differs from the gold reference.", "Scan available XivPlan arena assets, use the fight-specific background when present, or document fallback overlays.")
    if generated["party"]["legacy_role_prefix_count"] == 0 and gold["party"]["legacy_role_prefix_count"] > 0:
        add_gap(gaps, "party_compatibility", generated["party"], gold["party"], "Gold reference uses legacy role prefixes such as H1 AST.", "Keep strict generated role/job/icon contracts, but make reference analysis compatible with legacy names.")
    return gaps


def render_markdown(report: dict[str, Any]) -> str:
    generated = report["generated"]
    gold = report["gold"]
    deltas = report["deltas"]
    lines = [
        "# XivPlan Gold Comparison",
        "",
        f"- Generated: `{generated['path']}`",
        f"- Gold: `{gold['path']}`",
        "",
        "## Key Metrics",
        "",
        "| Metric | Generated | Gold | Ratio |",
        "|---|---:|---:|---:|",
        f"| Steps | {deltas['steps']['generated']} | {deltas['steps']['gold']} | {deltas['steps']['ratio']} |",
        f"| Objects | {deltas['objects']['generated']} | {deltas['objects']['gold']} | {deltas['objects']['ratio']} |",
        f"| Avg objects / step | {deltas['avg_objects_per_step']['generated']} | {deltas['avg_objects_per_step']['gold']} | {deltas['avg_objects_per_step']['ratio']} |",
        f"| Text objects | {deltas['text_objects']['generated']} | {deltas['text_objects']['gold']} | {deltas['text_objects']['ratio']} |",
        f"| In-scene text chars | {deltas['in_scene_text_chars']['generated']} | {deltas['in_scene_text_chars']['gold']} | {deltas['in_scene_text_chars']['ratio']} |",
        f"| Mechanic/range zones | {deltas['mechanic_range_zones']['generated']} | {deltas['mechanic_range_zones']['gold']} | {deltas['mechanic_range_zones']['ratio']} |",
        f"| Arrows | {deltas['arrows']['generated']} | {deltas['arrows']['gold']} | {deltas['arrows']['ratio']} |",
        "",
        "## Arena",
        "",
        f"- Generated arena: `{generated['arena']['descriptor']}`",
        f"- Gold arena: `{gold['arena']['descriptor']}`",
        f"- Gold ticks: `{bool(gold['arena']['ticks'])}`; generated ticks: `{bool(generated['arena']['ticks'])}`",
        "",
        "## Arrow Semantics",
        "",
        f"- Generated arrows: {generated['arrows']['arrows']}; with from/to semantics: {generated['arrows']['with_from_to_semantics']}; with resolveIndex: {generated['arrows']['with_resolve_index']}.",
        f"- Gold arrows: {gold['arrows']['arrows']}; with from/to semantics: {gold['arrows']['with_from_to_semantics']}; with resolveIndex: {gold['arrows']['with_resolve_index']}.",
        "",
        "## Party Compatibility",
        "",
        f"- Generated compatible roles: {', '.join(generated['party']['compatible_role_set']) or 'none'}; legacy prefixes: {generated['party']['legacy_role_prefix_count']}.",
        f"- Gold compatible roles: {', '.join(gold['party']['compatible_role_set']) or 'none'}; legacy prefixes: {gold['party']['legacy_role_prefix_count']}.",
        "",
        "## Gaps",
        "",
    ]
    if report["gaps"]:
        for gap in report["gaps"]:
            lines.append(f"- [{gap['dimension']}] {gap['message']} Suggestion: {gap['suggestion']}")
    else:
        lines.append("- No major generated-vs-gold gaps crossed the current thresholds.")
    return "\n".join(lines) + "\n"


def compare(generated_path: Path, gold_path: Path) -> dict[str, Any]:
    generated = profile_scene(generated_path)
    gold = profile_scene(gold_path)
    deltas = compare_profiles(generated, gold)
    return {
        "version": 1,
        "generated": generated,
        "gold": gold,
        "deltas": deltas,
        "gaps": deficit_report(generated, gold, deltas),
        "acceptance_reproduction": {
            "steps": f"{generated['steps']} vs {gold['steps']}",
            "objects": f"{generated['objects']} vs {gold['objects']}",
            "text_objects": f"{generated['text']['text_objects']} vs {gold['text']['text_objects']}",
            "in_scene_text_chars": f"{generated['text']['in_scene_text_chars']} vs {gold['text']['in_scene_text_chars']}",
            "mechanic_range_zones": f"{generated['mechanics']['mechanic_range_zones']} vs {gold['mechanics']['mechanic_range_zones']}",
            "arena": f"{generated['arena']['descriptor']} vs {gold['arena']['descriptor']}",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare a generated .xivplan file against a gold human reference.")
    parser.add_argument("generated", type=Path, help="Generated .xivplan scene")
    parser.add_argument("gold", type=Path, help="Gold reference .xivplan scene")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        report = compare(args.generated, args.gold)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(report), encoding="utf-8")

    reproduction = report["acceptance_reproduction"]
    print(
        "generated vs gold: steps={steps}; objects={objects}; text={text_objects}; chars={in_scene_text_chars}; ranges={mechanic_range_zones}; arena={arena}".format(
            **reproduction
        )
    )
    print(f"gaps={len(report['gaps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
