#!/usr/bin/env python3
"""Regression checks for Phase 11 mechanic knowledge retrieval."""

from __future__ import annotations

import sys
from pathlib import Path

from adapt_similar_mechanic import adapt
from search_mechanic_knowledge import search


FIXTURES = Path(__file__).resolve().parents[1] / "assets" / "knowledge-fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def titles(result: dict) -> str:
    return " | ".join(candidate["title"] for candidate in result["candidates"])


def assert_finds(query_name: str, expected: list[str]) -> dict:
    result = search(read_fixture(query_name), topn=5)
    title_blob = titles(result).lower()
    for item in expected:
        assert item.lower() in title_blob, (query_name, item, title_blob)
    assert len(result["candidates"]) >= 3, (query_name, result["candidates"])
    return result


def main() -> int:
    light = assert_finds("light-rampant-remix.input.md", ["Light Rampant"])
    assert light["alias_matches"][0]["canonical"] == "Light Rampant"

    hello = assert_finds("hello-world-limit-cut.input.md", ["Hello World"])
    assert any(match["canonical"] == "Hello World" for match in hello["alias_matches"])
    assert any(match["canonical"] == "Limit Cut" for match in hello["alias_matches"])

    paradeigma = assert_finds("p12s-paradeigma-animal.input.md", ["Paradeigma"])
    assert any(match["canonical"] == "Paradeigma" for match in paradeigma["alias_matches"])
    assert any(match["canonical"] == "Animals" for match in paradeigma["alias_matches"])

    fru = assert_finds("fru-p1-safe-side.input.md", ["Cyclonic Break", "Powder Mark"])
    assert any(match["canonical"] == "FRU P1 Safe Side" for match in fru["alias_matches"])

    report = adapt(read_fixture("light-rampant-remix.input.md"), topn=5)["report"]
    for section in ("我理解你指的是哪类机制", "可迁移部分", "不能照搬部分", "当前缺失信息", "推荐改写方向"):
        assert section in report, section

    print("OK: mechanic knowledge search finds analogy cards and writes required report sections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
