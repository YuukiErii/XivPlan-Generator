#!/usr/bin/env python3
"""Search local FFXIV mechanic knowledge cards for analogy candidates."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "xivplan-ffxiv-guide" / "references"
ALIASES = REFS / "mechanic-aliases.md"
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9'+-]*|\d+-\d+|\d+|[\u4e00-\u9fff]{1,6}")
KNOWN_CATEGORIES = {
    "raidwide",
    "tankbuster",
    "spread",
    "stack",
    "tower",
    "cleave",
    "in-out",
    "line-shape",
    "knockback",
    "gaze",
    "tether",
    "debuff",
    "bait",
    "pass",
    "rotation",
    "clone-memory",
    "sequence",
    "tile-platform",
    "adds-priority",
    "limit-cut-like",
    "hello-world-like",
    "light-rampant-like",
    "exaflare-like",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    extra: list[str] = []
    for token in tokens:
        if re.fullmatch(r"[\u4e00-\u9fff]{3,6}", token):
            extra.extend(token[index : index + 2] for index in range(len(token) - 1))
    return tokens + extra


def parse_aliases(path: Path = ALIASES) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in read_text(path).splitlines():
        if not line.startswith("|") or line.startswith("|---") or "Canonical" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        aliases = [item.strip() for item in cells[1].split(",") if item.strip()]
        categories = [item.strip() for item in cells[2].split(",") if item.strip()]
        load_first = [item.strip() for item in cells[3].split(";") if item.strip()]
        rows.append(
            {
                "canonical": cells[0],
                "aliases": aliases,
                "categories": categories,
                "load_first": load_first,
                "notes": cells[4],
            }
        )
    return rows


def alias_matches(query: str, aliases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lowered = query.lower()
    matches: list[dict[str, Any]] = []
    for entry in aliases:
        matched = [alias for alias in [entry["canonical"], *entry["aliases"]] if alias.lower() in lowered]
        if matched:
            item = dict(entry)
            item["matched_aliases"] = matched
            matches.append(item)
    return matches


def expand_query(query: str, matches: list[dict[str, Any]]) -> str:
    parts = [query]
    for match in matches:
        parts.append(match["canonical"])
        parts.extend(match["aliases"])
        parts.extend(match["categories"])
    return " ".join(parts)


def split_cards(path: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    cards: list[dict[str, Any]] = []
    current_title = path.stem
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                cards.append(make_card(path, current_title, "\n".join(current)))
            current_title = line[3:].strip()
            current = [line]
        else:
            current.append(line)
    if current:
        cards.append(make_card(path, current_title, "\n".join(current)))
    return cards


def make_card(path: Path, title: str, text: str) -> dict[str, Any]:
    rel = path.relative_to(ROOT).as_posix()
    categories = [item for item in re.findall(r"`([^`]+)`", text) if item in KNOWN_CATEGORIES]
    aliases = extract_field(text, "常见别名")
    transferable = extract_field(text, "可迁移")
    do_not_copy = extract_field(text, "不应照搬")
    unknowns = extract_field(text, "需要确认")
    principle = extract_field(text, "原理")
    confidence = extract_field(text, "置信度") or "unknown"
    return {
        "id": f"{rel}#{slugify(title)}",
        "title": title,
        "path": rel,
        "text": text,
        "categories": sorted(set(categories)),
        "aliases": aliases,
        "principle": principle,
        "transferable": transferable,
        "do_not_copy": do_not_copy,
        "unknowns": unknowns,
        "confidence_label": confidence.replace("`", "").strip(),
    }


def extract_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if field in line:
            _, _, tail = line.partition("：")
            return tail.strip(" -")
    return ""


def slugify(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "-", text.strip()).strip("-")
    return value.lower() or "card"


def load_corpus() -> list[dict[str, Any]]:
    paths = [
        REFS / "mechanic-taxonomy.md",
        REFS / "positioning-patterns.md",
    ]
    paths.extend(
        path
        for path in sorted((REFS / "encounters").glob("**/*.md"))
        if path.name not in {"index.md", "coverage-audit.md"}
    )
    cards: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        if path.name in {"mechanic-taxonomy.md", "positioning-patterns.md", "mechanic-aliases.md"}:
            cards.append(make_card(path, path.stem, read_text(path)))
        else:
            cards.extend(split_cards(path))
    return cards


def idf(corpus_tokens: list[Counter[str]]) -> dict[str, float]:
    documents = len(corpus_tokens)
    document_frequency: Counter[str] = Counter()
    for counts in corpus_tokens:
        document_frequency.update(counts.keys())
    return {token: math.log((documents + 1) / (df + 0.5)) + 1 for token, df in document_frequency.items()}


def score_card(card: dict[str, Any], query_tokens: Counter[str], idf_values: dict[str, float], preferred_paths: set[str]) -> tuple[float, list[str]]:
    text_tokens = Counter(tokenize(card["title"] + "\n" + card["text"]))
    score = 0.0
    matched: list[str] = []
    for token, q_count in query_tokens.items():
        count = text_tokens.get(token, 0)
        if not count:
            continue
        matched.append(token)
        score += (1 + math.log(count)) * idf_values.get(token, 1.0) * (1 + math.log(q_count))
    title_tokens = set(tokenize(card["title"]))
    score += sum(2.0 for token in query_tokens if token in title_tokens)
    if card["path"] in preferred_paths:
        score += 4.0
    if any(card["path"].endswith(path) for path in preferred_paths):
        score += 3.0
    confidence = card.get("confidence_label", "")
    if "local-verified" in confidence:
        score += 1.0
    elif "high" in confidence:
        score += 0.7
    return score, matched


def search(query: str, topn: int = 5) -> dict[str, Any]:
    aliases = parse_aliases()
    matches = alias_matches(query, aliases)
    expanded = expand_query(query, matches)
    corpus = load_corpus()
    corpus_tokens = [Counter(tokenize(card["title"] + "\n" + card["text"])) for card in corpus]
    idf_values = idf(corpus_tokens)
    query_tokens = Counter(tokenize(expanded))
    preferred_paths = {path for match in matches for path in match.get("load_first", [])}

    scored: list[dict[str, Any]] = []
    for card in corpus:
        score, matched_terms = score_card(card, query_tokens, idf_values, preferred_paths)
        if score <= 0:
            continue
        scored.append(
            {
                "id": card["id"],
                "title": card["title"],
                "path": card["path"],
                "score": round(score, 3),
                "matched_terms": sorted(set(matched_terms))[:20],
                "categories": card["categories"],
                "confidence_label": card["confidence_label"],
                "principle": card["principle"],
                "transferable": card["transferable"],
                "do_not_copy": card["do_not_copy"],
                "unknowns": card["unknowns"],
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query": query,
        "expanded_query": expanded,
        "alias_matches": [
            {
                "canonical": match["canonical"],
                "matched_aliases": match["matched_aliases"],
                "categories": match["categories"],
                "load_first": match["load_first"],
                "notes": match["notes"],
            }
            for match in matches
        ],
        "candidates": scored[:topn],
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Mechanic Knowledge Search",
        "",
        f"- query: {result['query']}",
        f"- alias matches: {', '.join(match['canonical'] for match in result['alias_matches']) or 'none'}",
        "",
        "## Candidates",
        "",
    ]
    if not result["candidates"]:
        lines.append("- No candidates found.")
        return "\n".join(lines) + "\n"
    for index, candidate in enumerate(result["candidates"], start=1):
        lines.extend(
            [
                f"### {index}. {candidate['title']}",
                "",
                f"- path: `{candidate['path']}`",
                f"- score: {candidate['score']}",
                f"- categories: {', '.join(candidate['categories']) or 'unknown'}",
                f"- confidence: {candidate['confidence_label'] or 'unknown'}",
                f"- matched terms: {', '.join(candidate['matched_terms'])}",
                f"- principle: {candidate['principle'] or 'n/a'}",
                f"- transferable: {candidate['transferable'] or 'n/a'}",
                f"- do not copy: {candidate['do_not_copy'] or 'n/a'}",
                f"- unknowns: {candidate['unknowns'] or 'n/a'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Search local mechanic knowledge cards.")
    parser.add_argument("query", nargs="?", help="Natural-language query")
    parser.add_argument("--input", type=Path, help="Read query from a file")
    parser.add_argument("--topn", type=int, default=5, help="Number of candidates")
    parser.add_argument("--json-out", type=Path, help="Write JSON search results")
    parser.add_argument("--markdown-out", type=Path, help="Write Markdown search report")
    args = parser.parse_args()

    if args.input:
        query = read_text(args.input)
    elif args.query:
        query = args.query
    else:
        print("ERROR: provide a query or --input", file=sys.stderr)
        return 2

    result = search(query, topn=args.topn)
    if args.json_out:
        write_json(args.json_out, result)
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(result), encoding="utf-8")
    print(f"candidates: {len(result['candidates'])}")
    for candidate in result["candidates"]:
        print(f"- {candidate['title']} [{candidate['score']}] {candidate['path']}")
    return 0 if result["candidates"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
