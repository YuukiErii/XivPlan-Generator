#!/usr/bin/env python3
"""Inject enemy icon assets into compact XivPlan specs."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
from pathlib import Path
from typing import Any

from build_xivplan_scene import ENEMY_SPEC_KINDS, fallback_enemy_icon


class EnemyAssetError(ValueError):
    """Enemy asset manifest cannot be applied."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text, flags=re.UNICODE)
    return re.sub(r"-+", "-", text).strip("-")


def is_enemy_spec(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    kind = obj.get("kind")
    return obj.get("type") == "enemy" or (isinstance(kind, str) and kind in ENEMY_SPEC_KINDS)


def enemy_kind(obj: dict[str, Any]) -> str:
    kind = obj.get("enemyKind") or obj.get("enemy_kind") or obj.get("kind") or "boss"
    if kind == "enemy":
        return "boss"
    return str(kind)


def data_url(path: Path) -> str:
    if not path.exists():
        raise EnemyAssetError(f"asset file does not exist: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    if mime_type != "image/png":
        raise EnemyAssetError(f"enemy icons must be PNG files: {path}")
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def manifest_assets(manifest: dict[str, Any], manifest_path: Path) -> dict[str, dict[str, Any]]:
    raw_assets = manifest.get("enemy_assets")
    if raw_assets is None:
        raw_assets = manifest.get("assets", [])
    if not isinstance(raw_assets, list):
        raise EnemyAssetError("manifest.enemy_assets must be a list")

    assets: dict[str, dict[str, Any]] = {}
    for index, asset in enumerate(raw_assets):
        if not isinstance(asset, dict):
            raise EnemyAssetError(f"enemy_assets[{index}] must be an object")
        enemy_id = slug(asset.get("enemy_id") or asset.get("asset_id") or asset.get("name"))
        if not enemy_id:
            raise EnemyAssetError(f"enemy_assets[{index}] needs enemy_id, asset_id, or name")
        path_value = asset.get("path")
        if isinstance(path_value, str) and path_value:
            icon = data_url((manifest_path.parent / path_value).resolve())
            status = "dedicated"
            source = asset.get("source", "manifest-path")
        else:
            icon = fallback_enemy_icon(str(asset.get("kind") or "boss"))
            status = "fallback"
            source = asset.get("source", "fallback")
        normalized = dict(asset)
        normalized["enemy_id"] = enemy_id
        normalized["icon"] = icon
        normalized["asset_status"] = status
        normalized["asset_source"] = source
        normalized.setdefault("asset_id", enemy_id)
        normalized.setdefault("fallback", "generic-add-icon" if str(asset.get("kind", "")).lower() == "add" else "generic-boss-icon")
        assets[enemy_id] = normalized
    return assets


def match_asset(enemy: dict[str, Any], assets: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        enemy.get("enemy_id"),
        enemy.get("asset_id"),
        enemy.get("assetId"),
        enemy.get("key"),
        enemy.get("displayName"),
        enemy.get("name"),
    ]
    for candidate in candidates:
        key = slug(candidate)
        if key in assets:
            return assets[key]
    return None


def apply_asset(enemy: dict[str, Any], asset: dict[str, Any] | None) -> None:
    kind = enemy_kind(enemy)
    if asset is None:
        enemy["icon"] = fallback_enemy_icon(kind)
        enemy.setdefault("asset_id", f"{slug(enemy.get('key') or enemy.get('name') or kind)}-fallback")
        enemy["asset_status"] = "fallback"
        enemy["asset_source"] = "fallback"
        enemy["asset_fallback"] = "generic-add-icon" if kind == "add" else "generic-boss-icon"
        return

    display = asset.get("display") if isinstance(asset.get("display"), dict) else {}
    enemy["icon"] = asset["icon"]
    enemy["asset_id"] = asset.get("asset_id")
    enemy["asset_status"] = asset.get("asset_status", "dedicated")
    enemy["asset_source"] = asset.get("asset_source", asset.get("source", "manifest"))
    enemy["asset_fallback"] = asset.get("fallback")
    if "width" in display:
        enemy["iconWidth"] = display["width"]
    elif "width" in asset:
        enemy["iconWidth"] = asset["width"]
    if "height" in display:
        enemy["iconHeight"] = display["height"]
    elif "height" in asset:
        enemy["iconHeight"] = asset["height"]


def inject_enemy_assets(spec: dict[str, Any], manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        raise EnemyAssetError("spec.steps must be a non-empty list")
    assets = manifest_assets(manifest, manifest_path)
    injected = 0
    fallback = 0
    for step_index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise EnemyAssetError(f"spec.steps[{step_index}] must be an object")
        objects = step.get("objects", [])
        if not isinstance(objects, list):
            raise EnemyAssetError(f"spec.steps[{step_index}].objects must be a list")
        for obj in objects:
            if not is_enemy_spec(obj):
                continue
            asset = match_asset(obj, assets)
            apply_asset(obj, asset)
            if asset is None or obj.get("asset_status") == "fallback":
                fallback += 1
            else:
                injected += 1
    metadata = spec.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata["enemy_asset_manifest"] = {
            "source": str(manifest_path),
            "assets": len(assets),
            "dedicated_injections": injected,
            "fallback_injections": fallback,
        }
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject enemy icon data URLs from an enemy asset manifest into a compact XivPlan spec.")
    parser.add_argument("spec", type=Path, help="Input compact scene spec JSON")
    parser.add_argument("manifest", type=Path, help="Enemy asset manifest JSON")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output spec JSON")
    args = parser.parse_args()

    try:
        spec = read_json(args.spec)
        manifest = read_json(args.manifest)
        if not isinstance(spec, dict) or not isinstance(manifest, dict):
            raise EnemyAssetError("spec and manifest roots must be JSON objects")
        write_json(args.output, inject_enemy_assets(spec, manifest, args.manifest))
    except (OSError, json.JSONDecodeError, EnemyAssetError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
