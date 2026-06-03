#!/usr/bin/env python3
"""Search FF14 Huiji wiki for Boss appearance references without local proxy leakage."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_URL = "https://ff14.huijiwiki.com/api.php"
WIKI_HOST = "ff14.huijiwiki.com"
PROXY_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
USER_AGENT = "Codex-XivPlan-PhaseW/1.0 (appearance verification; no-proxy)"


def unique_terms(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in result:
            result.append(text)
    return result


def no_proxy_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def wiki_get_json(opener: urllib.request.OpenerDirector, params: dict[str, Any], timeout: float) -> tuple[dict[str, Any] | list[Any] | None, dict[str, Any]]:
    query = urllib.parse.urlencode(params)
    url = f"{API_URL}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8", errors="replace")), {
                "url": url,
                "status": getattr(response, "status", None),
                "ok": True,
                "time_utc": started,
            }
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return None, {
            "url": url,
            "status": None,
            "ok": False,
            "error": str(exc),
            "time_utc": started,
        }


def opensearch(opener: urllib.request.OpenerDirector, term: str, limit: int, timeout: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data, attempt = wiki_get_json(
        opener,
        {
            "action": "opensearch",
            "search": term,
            "limit": str(limit),
            "namespace": "0",
            "format": "json",
        },
        timeout,
    )
    attempts = [{**attempt, "method": "opensearch", "term": term}]
    if not isinstance(data, list) or len(data) < 4:
        return [], attempts
    titles = data[1] if isinstance(data[1], list) else []
    descriptions = data[2] if isinstance(data[2], list) else []
    urls = data[3] if isinstance(data[3], list) else []
    candidates = []
    for index, title in enumerate(titles):
        candidates.append(
            {
                "term": term,
                "title": str(title),
                "description": str(descriptions[index]) if index < len(descriptions) else "",
                "url": str(urls[index]) if index < len(urls) else "",
            }
        )
    return candidates, attempts


def enrich_candidate(opener: urllib.request.OpenerDirector, candidate: dict[str, Any], timeout: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    title = candidate.get("title")
    data, attempt = wiki_get_json(
        opener,
        {
            "action": "query",
            "format": "json",
            "prop": "pageimages|extracts",
            "piprop": "thumbnail|original",
            "pithumbsize": "360",
            "exintro": "1",
            "explaintext": "1",
            "titles": str(title or ""),
        },
        timeout,
    )
    attempts = [{**attempt, "method": "pageimages", "term": str(title or "")}]
    enriched = dict(candidate)
    pages = data.get("query", {}).get("pages", {}) if isinstance(data, dict) else {}
    if isinstance(pages, dict):
        for page in pages.values():
            if not isinstance(page, dict):
                continue
            enriched["pageid"] = page.get("pageid")
            enriched["source_page_title"] = page.get("title") or title
            enriched["extract"] = str(page.get("extract", ""))[:600]
            thumb = page.get("thumbnail") if isinstance(page.get("thumbnail"), dict) else {}
            original = page.get("original") if isinstance(page.get("original"), dict) else {}
            enriched["image_url"] = thumb.get("source") or original.get("source")
            break
    return enriched, attempts


def build_icon_brief(candidate: dict[str, Any], traits: list[str]) -> str:
    name = candidate.get("source_page_title") or candidate.get("title") or "Boss"
    trait_text = ", ".join(traits) if traits else "verified silhouette and color traits"
    return f"original transparent-background raid-guide icon for {name}, simplified from {trait_text}, no text, readable at 72 px"


def search(terms: list[str], max_results: int, timeout: float, visual_traits: list[str]) -> dict[str, Any]:
    previous_proxy_env = {key: os.environ.get(key) for key in PROXY_ENV_KEYS if os.environ.get(key)}
    opener = no_proxy_opener()
    attempts: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for term in terms:
        found, found_attempts = opensearch(opener, term, max_results, timeout)
        attempts.extend(found_attempts)
        for candidate in found:
            enriched, enrich_attempts = enrich_candidate(opener, candidate, timeout)
            attempts.extend(enrich_attempts)
            candidates.append(enriched)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.get("url") or candidate.get("title"))
        if key in seen:
            continue
        seen.add(key)
        candidate["source"] = "ff14-huijiwiki"
        candidate["source_url"] = candidate.get("url")
        candidate["visual_traits"] = visual_traits
        candidate["icon_brief"] = build_icon_brief(candidate, visual_traits)
        candidate["license_note"] = "Use as visual reference only; final guide icon must be original simplified artwork, not a copied wiki/game image."
        deduped.append(candidate)

    any_attempt_ok = any(attempt.get("ok") for attempt in attempts)
    if deduped:
        status = "found"
    elif any_attempt_ok:
        status = "no-candidate"
    else:
        status = "wiki-search-blocked-fallback"

    return {
        "status": status,
        "queried_terms": terms,
        "proxy_bypass": {
            "host": WIKI_HOST,
            "proxy_handler": "empty ProxyHandler",
            "ignored_proxy_env": previous_proxy_env,
            "no_proxy_recommendation": "NO_PROXY=ff14.huijiwiki.com,.huijiwiki.com",
        },
        "access_attempts": attempts,
        "candidates": deduped,
        "fallback_policy": "If status is wiki-search-blocked-fallback or no-candidate, use browser search, user screenshots, or public guide screenshots before finalizing a fallback icon.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Boss Appearance Search",
        "",
        f"- status: {payload['status']}",
        "- queried terms: " + ", ".join(payload.get("queried_terms", [])),
        f"- proxy bypass: {payload.get('proxy_bypass', {}).get('proxy_handler')}",
        "",
        "## Candidates",
        "",
    ]
    if not payload.get("candidates"):
        lines.append("- none")
    for candidate in payload.get("candidates", []):
        lines.extend(
            [
                f"- title: {candidate.get('source_page_title') or candidate.get('title')}",
                f"  source_url: {candidate.get('source_url') or candidate.get('url')}",
                f"  image_url: {candidate.get('image_url') or 'n/a'}",
                f"  icon_brief: {candidate.get('icon_brief')}",
                f"  license_note: {candidate.get('license_note')}",
            ]
        )
    lines.extend(["", "## Access Attempts", ""])
    for attempt in payload.get("access_attempts", []):
        lines.append(
            "- {method} `{term}` ok={ok} status={status}".format(
                method=attempt.get("method"),
                term=attempt.get("term"),
                ok=attempt.get("ok"),
                status=attempt.get("status") or attempt.get("error", "n/a"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Huiji wiki for a Boss appearance reference with no-proxy access.")
    parser.add_argument("--name", default="", help="Primary Boss name")
    parser.add_argument("--boss-cn", default="", help="Chinese Boss name")
    parser.add_argument("--boss-en", default="", help="English Boss name")
    parser.add_argument("--encounter", default="", help="Encounter or duty name")
    parser.add_argument("--phase", default="", help="Encounter phase")
    parser.add_argument("--alias", action="append", default=[], help="Additional search alias; repeatable")
    parser.add_argument("--visual-trait", action="append", default=[], help="Known visual trait to carry into icon brief")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path, help="Optional JSON output path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report output path")
    args = parser.parse_args()

    terms = unique_terms([args.name, args.boss_cn, args.boss_en, args.encounter, args.phase, *args.alias])
    if not terms:
        print("ERROR: provide at least one Boss name, encounter, phase, or alias", file=sys.stderr)
        return 2

    payload = search(terms, args.max_results, args.timeout, list(args.visual_trait))

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(payload), encoding="utf-8")

    print(f"status: {payload['status']}")
    print(f"candidates: {len(payload.get('candidates', []))}")
    for candidate in payload.get("candidates", [])[:3]:
        print(f"- {candidate.get('source_page_title') or candidate.get('title')}: {candidate.get('source_url') or candidate.get('url')}")
    return 0 if payload["status"] in {"found", "no-candidate", "wiki-search-blocked-fallback"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
