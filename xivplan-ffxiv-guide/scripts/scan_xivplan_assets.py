#!/usr/bin/env python3
"""Scan local XivPlan public assets and report arena availability."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUBDIRS = ("arena", "actor", "marker")

ARENA_MATCH_RULES = [
    {
        "preset": "fru-p1",
        "terms": ["fru", "fru p1", "fru-p1", "fatebreaker", "e11", "eden promise", "雷火", "雷火剑"],
        "asset_terms": ["e11"],
        "fallback_reason": "FRU P1 requires the built-in Eden Promise arena `/arena/e11.svg`.",
    },
    {
        "preset": "eden-light",
        "terms": ["eden light", "shiva", "light rampant", "e8", "光之暴走", "光暴", "冰镜"],
        "asset_terms": ["e8"],
        "fallback_reason": "Eden/Shiva-light diagrams use the built-in `/arena/e8.svg` asset.",
    },
    {
        "preset": "udm-p1",
        "terms": ["ultimate yokai", "yokai star", "udm p1", "udm-p1", "udm phase1", "udm-phase1", "绝妖 p1", "绝妖第一阶段", "绝妖一阶段"],
        "asset_terms": ["udm-phase1", "udm-p1"],
        "fallback_reason": "no built-in UDM P1 arena asset found; fallback to default-circle with explicit axis overlays",
    },
    {
        "preset": "udm-p2",
        "terms": ["udm p2", "udm-p2", "udm phase2", "udm-phase2", "绝妖 p2", "绝妖第二阶段", "绝妖二阶段"],
        "asset_terms": ["udm-phase2", "udm-p2"],
        "fallback_reason": "no built-in UDM P2 arena asset found; fallback to default-circle with explicit axis overlays",
    },
    {
        "preset": "udm-p3",
        "terms": ["udm p3", "udm-p3", "udm phase3", "udm-phase3", "绝妖 p3", "绝妖第三阶段", "绝妖三阶段"],
        "asset_terms": ["udm-phase3", "udm-p3"],
        "fallback_reason": "no built-in UDM P3 arena asset found; fallback to default-circle with explicit axis overlays",
    },
    {
        "preset": "ultimate-yokai-star-dance",
        "terms": ["ultimate yokai", "yokai star", "udm", "绝妖", "绝妖星乱舞"],
        "asset_terms": ["udm-phase1", "udm-p1", "udm"],
        "fallback_reason": "no built-in UDM/Yokai arena asset found; fallback to default-circle with explicit axis overlays",
    },
    {
        "preset": "omega-o8s",
        "terms": ["o8s", "omega", "sigmascape", "kefka", "凯夫卡", "妖星乱舞"],
        "asset_terms": ["o8", "omega", "kefka", "sigmascape"],
        "fallback_reason": "no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays",
    },
    {
        "preset": "tile-square",
        "terms": ["tile", "grid", "square", "格子", "方形", "平台"],
        "asset_terms": [],
        "fallback_reason": "tile-square uses a generated grid overlay rather than a raid background image",
    },
]


def slug(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text, flags=re.UNICODE)
    return re.sub(r"-+", "-", text).strip("-")


def public_dir_candidates(explicit: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    env_dir = os.environ.get("XIVPLAN_PUBLIC_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.extend(
        [
            ROOT.parent / "XivPlan" / "public",
            ROOT / "public",
            ROOT / "xivplan-ffxiv-guide" / "public",
        ]
    )
    seen: set[Path] = set()
    result: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def relative_asset_path(public_dir: Path, path: Path) -> str:
    return "/" + path.relative_to(public_dir).as_posix()


def file_entry(public_dir: Path, path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "name": path.name,
        "asset_path": relative_asset_path(public_dir, path),
        "extension": path.suffix.lower().lstrip("."),
        "bytes": stat.st_size,
        "modified": stat.st_mtime,
    }


def scan_public_dir(public_dir: Path) -> dict[str, list[dict[str, Any]]]:
    payload: dict[str, list[dict[str, Any]]] = {}
    for subdir in DEFAULT_SUBDIRS:
        target = public_dir / subdir
        if not target.is_dir():
            payload[subdir] = []
            continue
        payload[subdir] = [
            file_entry(public_dir, path)
            for path in sorted(target.iterdir())
            if path.is_file() and not path.name.startswith(".")
        ]
    return payload


def choose_asset(rule: dict[str, Any], arena_assets: list[dict[str, Any]]) -> dict[str, Any] | None:
    asset_terms = [slug(term) for term in rule.get("asset_terms", [])]
    if not asset_terms:
        return None
    for term in asset_terms:
        for asset in arena_assets:
            name_slug = slug(str(asset.get("name", "")))
            asset_slug = slug(str(asset.get("asset_path", "")))
            if term in name_slug or term in asset_slug:
                return asset
    return None


def encounter_matches(encounter: str, rule: dict[str, Any]) -> bool:
    haystack = encounter.lower()
    return any(term.lower() in haystack for term in rule.get("terms", []))


def build_arena_manifest(public_dir: Path, scanned: dict[str, list[dict[str, Any]]], encounter: str) -> dict[str, Any]:
    arena_assets = scanned.get("arena", [])
    rules: list[dict[str, Any]] = []
    for rule in ARENA_MATCH_RULES:
        asset = choose_asset(rule, arena_assets)
        matched = encounter_matches(encounter, rule) if encounter else False
        rules.append(
            {
                "preset": rule["preset"],
                "matched_encounter": matched,
                "available": asset is not None or rule["preset"] == "tile-square",
                "background": asset.get("asset_path") if asset else None,
                "asset_name": asset.get("name") if asset else None,
                "sourceReason": (
                    f"local asset `{asset.get('asset_path')}` found under {public_dir}"
                    if asset
                    else rule["fallback_reason"]
                ),
            }
        )
    matching = [item for item in rules if item["matched_encounter"]]
    return {
        "public_dir": str(public_dir),
        "arena_count": len(arena_assets),
        "actor_count": len(scanned.get("actor", [])),
        "marker_count": len(scanned.get("marker", [])),
        "rules": rules,
        "encounter": encounter,
        "encounter_matches": matching,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# XivPlan Asset Scan",
        "",
        f"- public_dir: `{payload['public_dir']}`",
        f"- arena assets: {payload['arena_count']}",
        f"- actor assets: {payload['actor_count']}",
        f"- marker assets: {payload['marker_count']}",
        f"- encounter query: {payload.get('encounter') or 'n/a'}",
        "",
        "## Arena Rules",
        "",
        "| Preset | Available | Background | Encounter Match | Source Reason |",
        "|---|---|---|---|---|",
    ]
    for item in payload.get("rules", []):
        lines.append(
            "| {preset} | {available} | {background} | {matched} | {reason} |".format(
                preset=item["preset"],
                available="yes" if item["available"] else "no",
                background=item.get("background") or "none",
                matched="yes" if item.get("matched_encounter") else "no",
                reason=str(item.get("sourceReason", "")).replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan local XivPlan public assets for Phase W arena/background evidence.")
    parser.add_argument("--public-dir", type=Path, help="Explicit XivPlan public directory")
    parser.add_argument("--encounter", default="", help="Encounter/mechanic query to match against known arena aliases")
    parser.add_argument("--json-out", type=Path, help="Optional JSON manifest output path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report output path")
    args = parser.parse_args()

    candidates = public_dir_candidates(args.public_dir)
    if not candidates:
        print("ERROR: no XivPlan public directory found", file=sys.stderr)
        return 2

    public_dir = candidates[0]
    scanned = scan_public_dir(public_dir)
    payload = build_arena_manifest(public_dir, scanned, args.encounter)
    payload["assets"] = scanned

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(payload), encoding="utf-8")

    print(f"public_dir: {public_dir}")
    print(f"arena assets: {payload['arena_count']}")
    if args.encounter:
        for item in payload["encounter_matches"]:
            print(f"- {item['preset']}: {'available' if item['available'] else 'fallback'} {item.get('background') or item['sourceReason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
