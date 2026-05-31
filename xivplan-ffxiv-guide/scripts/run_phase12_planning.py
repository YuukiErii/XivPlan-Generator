#!/usr/bin/env python3
"""Run Phase 12 planning cases from parsed IR to guide packages."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

from assemble_guide import assemble_guide
from build_spec_from_solution import build_spec
from build_xivplan_scene import build_scene, write_json
from export_xivplan_steps import export_steps
from plan_solution_candidates import plan_bundle, read_json
from score_solution_candidates import render_markdown, score_bundle
from validate_xivplan_scene import validate_scene


ROOT = Path(__file__).resolve().parents[2]
PARSED_ROOT = ROOT / "artifacts" / "parsed-mechanics"
KNOWLEDGE_ROOT = ROOT / "artifacts" / "knowledge-search"
OUT_ROOT = ROOT / "artifacts" / "solution-planning"
CASES = [
    "four-tower-spread-stack",
    "light-rampant-like",
    "hello-world-limit-cut",
    "fru-p1-rewrite",
    "image2-animal-asset",
    "ultimate-yokai-star-dance-p1-draft",
]
KNOWLEDGE_BY_CASE = {
    "light-rampant-like": "light-rampant-remix",
    "hello-world-limit-cut": "hello-world-limit-cut",
    "fru-p1-rewrite": "fru-p1-safe-side",
    "image2-animal-asset": "p12s-paradeigma-animal",
}


def maybe_read_knowledge(slug: str) -> dict[str, Any] | None:
    knowledge_slug = KNOWLEDGE_BY_CASE.get(slug)
    if not knowledge_slug:
        return None
    path = KNOWLEDGE_ROOT / knowledge_slug / "knowledge-search.json"
    return read_json(path) if path.exists() else None


def guide_for(case_dir: Path, bundle: dict[str, Any], scores: dict[str, Any], manifest: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    candidate_id = scores.get("recommended_candidate")
    by_id = {candidate.get("id"): candidate for candidate in bundle.get("candidates", [])}
    candidate = by_id.get(candidate_id, {})
    unknowns = bundle.get("planning_context", {}).get("unknowns", [])
    steps = spec["steps"]
    return {
        "title": f"Phase 12：{bundle['mechanic']}",
        "summary": bundle.get("description", ""),
        "recommended_solution": f"{candidate.get('name', candidate_id)}：{candidate.get('summary', '')}",
        "scene": "scene.xivplan",
        "spec": "spec.json",
        "figures": [
            {
                "step": item["step"],
                "title": steps[item["step"] - 1]["title"],
                "image": item["image"],
                "caption": f"图 {item['step']}：{steps[item['step'] - 1]['title']}",
                "guide_text": steps[item["step"] - 1]["guide_text"],
            }
            for item in manifest["steps"]
        ],
        "flow": [step["guide_text"] for step in steps],
        "role_assignments": [
            {"role": "MT/ST", "position": "南北或内圈坦克位", "task": "处理坦克职责、塔或复位。"},
            {"role": "H1/H2", "position": "东西或内圈治疗位", "task": "保证治疗覆盖，避免读条窗口长距离移动。"},
            {"role": "D1/D2", "position": "近战内圈或斜角", "task": "优先保 Boss uptime，按图处理散开/塔。"},
            {"role": "D3/D4", "position": "外圈或读条锚定位", "task": "D3 负责机动补位，D4 尽量少动。"},
        ],
        "common_mistakes": [
            "把未知点当成定稿规则，导致实战信息更新后图文不一致。",
            "为了少走路而让路线交叉。",
            "复位点没有提前约定，影响下一读条起手。",
        ],
        "short_callout": [
            "先观察，再预站。",
            "固定职能优先，未知点按保守版处理。",
            "判定后回中或回八方复位。",
        ],
        "mnemonic": "观察、预站、判定、移动、结算、复位。",
        "consistency_checks": [
            "已生成候选方案、评分、推荐理由、spec、.xivplan 和攻略包。",
            "每个 step 带 purpose、guide_text、checks。",
            "推荐方案保留风险与待验证点。",
        ],
        "unknowns": unknowns,
    }


def run_case(slug: str) -> dict[str, Any]:
    source_dir = PARSED_ROOT / slug
    if not source_dir.exists():
        raise FileNotFoundError(f"missing parsed case: {source_dir}")
    case_dir = OUT_ROOT / slug
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    bundle = plan_bundle(
        read_json(source_dir / "mechanic-ir.json"),
        read_json(source_dir / "timeline-ir.json"),
        maybe_read_knowledge(slug),
        {},
    )
    candidate_path = case_dir / "solution-candidates.json"
    write_json(candidate_path, bundle)

    scores = score_bundle(bundle)
    score_path = case_dir / "solution-scores.json"
    report_path = case_dir / "solution-report.md"
    write_json(score_path, scores)
    report_path.write_text(render_markdown(scores), encoding="utf-8")

    spec = build_spec(bundle, scores, None)
    spec_path = case_dir / "spec.json"
    scene_path = case_dir / "scene.xivplan"
    write_json(spec_path, spec)
    scene = build_scene(spec)
    write_json(scene_path, scene)
    errors, counts, object_count = validate_scene(scene)
    if errors:
        raise RuntimeError(f"{slug} invalid scene: {errors}")

    manifest = export_steps(scene_path, case_dir, scale_factor=1)
    guide = guide_for(case_dir, bundle, scores, manifest, spec)
    guide_path = case_dir / "guide.json"
    write_json(guide_path, guide)
    outputs = assemble_guide(guide_path, case_dir / "guide-package", strict_images=True)

    risk_path = case_dir / "risks-and-assumptions.md"
    risk_lines = ["# 风险与待验证点", ""]
    for item in guide["unknowns"] or ["暂无阻塞未知点；仍需实战确认范围和节奏。"]:
        risk_lines.append(f"- {item}")
    risk_path.write_text("\n".join(risk_lines) + "\n", encoding="utf-8")

    return {
        "slug": slug,
        "recommended": scores.get("recommended_candidate"),
        "candidate_count": len(bundle["candidates"]),
        "steps": len(scene["steps"]),
        "objects": object_count,
        "types": dict(sorted(counts.items())),
        "unknowns": len(guide["unknowns"]),
        "paths": {
            "candidates": str(candidate_path),
            "scores": str(score_path),
            "report": str(report_path),
            "risk_report": str(risk_path),
            "spec": str(spec_path),
            "scene": str(scene_path),
            "guide_package": str(case_dir / "guide-package"),
            "markdown": str(outputs["markdown"]),
            "docx": str(outputs["docx"]),
            "pdf": str(outputs["pdf"]),
        },
    }


def render_summary(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Phase 12 Solution Planning Report",
        "",
        "## Summary",
        "",
        f"- cases: {len(results)}",
        "- generated: solution-candidates.json, solution-scores.json, solution-report.md, risks-and-assumptions.md, spec.json, scene.xivplan, guide-package/",
        "",
        "## Case Matrix",
        "",
        "| Case | Candidates | Recommended | Steps | Objects | Unknowns |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result['slug']} | {result['candidate_count']} | {result['recommended']} | {result['steps']} | {result['objects']} | {result['unknowns']} |"
        )
    lines.extend(
        [
            "",
            "## Acceptance Notes",
            "",
            "- Phase 8 five cases all have IR -> candidates -> score -> recommended spec -> `.xivplan` -> guide package outputs.",
            "- `ultimate-yokai-star-dance-p1-draft` produces a v0.1 progression draft and preserves unknowns in guide and risk report.",
            "- Specs use six explicit steps: observation, preposition, first resolution, movement, final resolution, reset.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
        results = [run_case(slug) for slug in CASES]
        write_json(OUT_ROOT / "phase12-solution-planning-results.json", results)
        (OUT_ROOT / "phase12-solution-planning-report.md").write_text(render_summary(results), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - batch report should fail loudly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {OUT_ROOT / 'phase12-solution-planning-report.md'}")
    print(f"cases: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
