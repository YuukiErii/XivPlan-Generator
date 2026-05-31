#!/usr/bin/env python3
"""Create an analogy adaptation report from a user request and search results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from search_mechanic_knowledge import search, write_json


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_understanding(query: str, result: dict[str, Any]) -> str:
    aliases = result.get("alias_matches", [])
    if aliases:
        names = "、".join(match["canonical"] for match in aliases)
        return f"我理解你指的是 `{names}` 这一类机制的变体，而不是要求照搬原副本站位。"
    if result.get("candidates"):
        titles = "、".join(candidate["title"] for candidate in result["candidates"][:2])
        return f"我理解你在描述一个与 `{titles}` 相近的组合机制，需要先确认可迁移原则。"
    return "我暂时只能识别为未定类比机制，需要补充机制名、类别或参考副本。"


def merge_field(candidates: list[dict[str, Any]], field: str, fallback: str) -> list[str]:
    values: list[str] = []
    for candidate in candidates:
        value = str(candidate.get(field, "")).strip()
        if value and value != "n/a" and value not in values:
            values.append(value)
    return values or [fallback]


def categories(candidates: list[dict[str, Any]], aliases: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for alias in aliases:
        for category in alias.get("categories", []):
            if category not in values:
                values.append(category)
    for candidate in candidates:
        for category in candidate.get("categories", []):
            if category not in values:
                values.append(category)
    return values


def recommended_direction(query: str, result: dict[str, Any]) -> list[str]:
    cats = set(categories(result.get("candidates", []), result.get("alias_matches", [])))
    directions = []
    if {"tether", "tower"} & cats:
        directions.append("先画连线/塔的资格与图形，再单独画移动、判定和复位。")
    if "debuff" in cats or "pass" in cats:
        directions.append("先做状态/时间 bucket 表，再逐 beat 画等待点、交接点和清除点。")
    if "line-shape" in cats or "exaflare-like" in cats:
        directions.append("先确认起点、方向、线宽和间隔，再画主路线，避免把所有可能分支塞进一张图。")
    if "clone-memory" in cats:
        directions.append("把观察图和执行图拆开，保留对象映射规则，而不是只画最终安全区。")
    if "spread" in cats or "stack" in cats:
        directions.append("明确点名/分摊人数、半径和易伤规则，再决定 clocks、light parties 或 pairs。")
    if "cleave" in cats:
        directions.append("用 boss-relative 或 anchor-relative 标注安全侧，避免把绝对东西南北误当作机制事实。")
    if not directions:
        directions.append("先把机制拆成观察、预站、判定、移动、复位五类信息，再进入 XivPlan spec。")
    if any(term in query for term in ("暂不确定", "不确定", "未知", "待确认", "?")):
        directions.append("当前输入含未知信息，应输出草案并在最终图前确认阻塞项。")
    return directions


def render_report(query: str, result: dict[str, Any]) -> str:
    all_candidates = result.get("candidates", [])
    encounter_candidates = [candidate for candidate in all_candidates if "/references/encounters/" in candidate.get("path", "").replace("\\", "/")]
    candidates = (encounter_candidates or all_candidates)[:3]
    alias_names = [match["canonical"] for match in result.get("alias_matches", [])]
    lines = [
        "# Similar Mechanic Adaptation Report",
        "",
        "## 我理解你指的是哪类机制",
        "",
        summarize_understanding(query, result),
        "",
        "- 原始输入：",
        "",
        f"> {query.strip().replace(chr(10), ' ')}",
        "",
        f"- 命中的别名族：{', '.join(alias_names) or 'none'}",
        f"- 候选类别：{', '.join(categories(candidates, result.get('alias_matches', []))) or 'unknown'}",
        "",
        "## 候选机制",
        "",
    ]
    if candidates:
        for index, candidate in enumerate(candidates, start=1):
            lines.extend(
                [
                    f"{index}. `{candidate['title']}`",
                    f"   - 来源：`{candidate['path']}`",
                    f"   - 分数：{candidate['score']}",
                    f"   - 匹配词：{', '.join(candidate['matched_terms'])}",
                ]
            )
    else:
        lines.append("- 未找到足够候选。")
    lines.extend(["", "## 可迁移部分", ""])
    for item in merge_field(candidates, "transferable", "只能迁移机制类别和拆图原则，不能直接定站位。"):
        lines.append(f"- {item}")
    lines.extend(["", "## 不能照搬部分", ""])
    for item in merge_field(candidates, "do_not_copy", "原副本的具体坐标、人数、时间轴和站位不能直接照搬。"):
        lines.append(f"- {item}")
    lines.extend(["", "## 当前缺失信息", ""])
    for item in merge_field(candidates, "unknowns", "需要确认点名规则、人数、顺序、方向锚点和队伍宏。"):
        lines.append(f"- {item}")
    lines.extend(["", "## 推荐改写方向", ""])
    for item in recommended_direction(query, result):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 将输入先过 `parse_mechanic_request.py` 生成 mechanic/timeline IR。",
            "- 把本报告中的可迁移原则写入候选解法，不把原机制具体站位当作事实。",
            "- 若存在 blocking unknowns，先标为草案图或请求确认。",
        ]
    )
    return "\n".join(lines) + "\n"


def adapt(query: str, topn: int = 5, search_result: dict[str, Any] | None = None) -> dict[str, Any]:
    result = search_result or search(query, topn=topn)
    return {
        "query": query,
        "search": result,
        "report": render_report(query, result),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write an analogy adaptation report for a similar mechanic request.")
    parser.add_argument("query", nargs="?", help="Natural-language request")
    parser.add_argument("--input", type=Path, help="Read request from file")
    parser.add_argument("--search-json", type=Path, help="Use existing search result JSON")
    parser.add_argument("--topn", type=int, default=5)
    parser.add_argument("-o", "--output-dir", type=Path, required=True, help="Output directory")
    args = parser.parse_args()

    if args.input:
        query = read_text(args.input)
    elif args.query:
        query = args.query
    elif args.search_json:
        data = load_json(args.search_json)
        query = data.get("query", "")
    else:
        print("ERROR: provide query, --input, or --search-json", file=sys.stderr)
        return 2

    search_result = load_json(args.search_json) if args.search_json else None
    result = adapt(query, topn=args.topn, search_result=search_result)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "knowledge-search.json", result["search"])
    (args.output_dir / "similarity-report.md").write_text(result["report"], encoding="utf-8")
    print(f"Wrote {args.output_dir / 'similarity-report.md'}")
    print(f"candidates: {len(result['search'].get('candidates', []))}")
    return 0 if result["search"].get("candidates") else 1


if __name__ == "__main__":
    raise SystemExit(main())
