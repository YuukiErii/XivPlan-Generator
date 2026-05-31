#!/usr/bin/env python3
"""Summarize visual-regression review items into a burndown report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def visual_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results", [])
    if not isinstance(results, list):
        raise ValueError("visual-regression results must contain a list field named `results`")
    return [result for result in results if isinstance(result, dict)]


def iter_issues(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        slug = str(result.get("slug", "unknown"))
        visual_quality = result.get("visual_quality", {})
        issues = visual_quality.get("issues", []) if isinstance(visual_quality, dict) else []
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            rows.append(
                {
                    "fixture": slug,
                    "severity": str(issue.get("severity", "review")),
                    "kind": str(issue.get("kind", "unknown")),
                    "dimension": str(issue.get("dimension", "unknown")),
                    "step": issue.get("step", "-"),
                    "title": issue.get("title", ""),
                }
            )
    return rows


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    rows = iter_issues(visual_results(payload))
    review_rows = [row for row in rows if row["severity"] == "review"]
    severe_rows = [row for row in rows if row["severity"] == "severe"]
    by_kind = Counter(row["kind"] for row in review_rows)
    by_fixture = Counter(row["fixture"] for row in review_rows)
    by_fixture_step: dict[str, Counter[tuple[Any, str]]] = defaultdict(Counter)
    for row in review_rows:
        by_fixture_step[row["fixture"]][(row["step"], row["kind"])] += 1
    return {
        "source_summary": payload.get("summary", {}),
        "acceptance": payload.get("acceptance", {}),
        "review_items": len(review_rows),
        "severe_items": len(severe_rows),
        "by_kind": dict(by_kind.most_common()),
        "by_fixture": dict(by_fixture.most_common()),
        "by_fixture_step": {
            fixture: [
                {"step": step, "kind": kind, "count": count}
                for (step, kind), count in counter.most_common()
            ]
            for fixture, counter in sorted(by_fixture_step.items())
        },
    }


def render_markdown(source: Path, summary: dict[str, Any]) -> str:
    lines = [
        "# Visual Review Burndown",
        "",
        f"- source: `{source}`",
        f"- review items: {summary['review_items']}",
        f"- severe items in source: {summary['severe_items']}",
        "",
        "## Review Items By Kind",
        "",
        "| Kind | Count |",
        "|---|---:|",
    ]
    for kind, count in summary["by_kind"].items():
        lines.append(f"| `{kind}` | {count} |")
    if not summary["by_kind"]:
        lines.append("| none | 0 |")

    lines.extend(["", "## Review Items By Fixture", "", "| Fixture | Count |", "|---|---:|"])
    for fixture, count in summary["by_fixture"].items():
        lines.append(f"| `{fixture}` | {count} |")
    if not summary["by_fixture"]:
        lines.append("| none | 0 |")

    lines.extend(["", "## Fixture / Step Detail", ""])
    for fixture, items in summary["by_fixture_step"].items():
        lines.extend([f"### {fixture}", "", "| Step | Kind | Count |", "|---:|---|---:|"])
        for item in items:
            lines.append(f"| {item['step']} | `{item['kind']}` | {item['count']} |")
        lines.append("")
    if not summary["by_fixture_step"]:
        lines.append("No review items remain.")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize review items from visual-regression-results.json.")
    parser.add_argument("results_json", type=Path, help="Path to visual-regression-results.json")
    parser.add_argument("--json-out", type=Path, help="Optional JSON summary path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown burndown path")
    args = parser.parse_args()

    try:
        payload = read_json(args.results_json)
        if not isinstance(payload, dict):
            raise ValueError("input JSON root must be an object")
        summary = summarize(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        write_json(args.json_out, summary)
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(args.results_json, summary), encoding="utf-8")

    print(f"review_items={summary['review_items']} severe_items={summary['severe_items']}")
    return 0 if summary["severe_items"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
