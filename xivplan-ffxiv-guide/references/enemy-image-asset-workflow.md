# Enemy Image Asset Workflow

Phase Q makes every Boss, clone, add, and untargetable mechanic source visually identifiable beyond the target ring and name label.

## Policy

- Convert user-provided enemy appearance notes into an `asset_brief` before requesting or reusing an image.
- Prefer user screenshots, strategy screenshots, first-person captures, or public guide/video references when an encounter is known.
- If the appearance cannot be confirmed, use a guide-friendly generic Boss/add fallback icon and mark the asset as `fallback`.
- Do not copy official UI art, logos, watermarks, or original game artwork exactly. Generate or draw small original guide icons with a clean silhouette.
- Icons should have transparent background, no text, clear outline, and remain readable at `64-96 px`.
- Every enemy asset decision must be written to an enemy asset manifest and every final `.xivplan` should embed the icon as a data URL.

## Manifest Shape

```json
{
  "enemy_assets": [
    {
      "enemy_id": "fatebreaker",
      "name": "Fatebreaker",
      "kind": "boss",
      "source": "user-description",
      "asset_id": "boss-fatebreaker-icon",
      "path": "outputs/fatebreaker/assets/boss-fatebreaker-icon.png",
      "fallback": "generic-boss-icon",
      "display": {
        "width": 72,
        "height": 72,
        "anchor": "center"
      }
    }
  ]
}
```

`path` is optional only when a fallback is intentionally used. Fallback-only entries still need `enemy_id`, `name`, `kind`, `asset_id`, and `fallback`.

## Injection

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\inject_enemy_assets.py `
  artifacts\phase-q\spec.json `
  artifacts\phase-q\enemy-assets.json `
  -o artifacts\phase-q\spec.enemy-assets.json
```

The injector matches enemies by `enemy_id`, `asset_id`, `key`, `displayName`, or `name`, then writes:

- `icon`: embedded PNG data URL or generic fallback data URL.
- `asset_id`: manifest asset identifier.
- `asset_status`: `dedicated` or `fallback`.
- `asset_source`: user description, screenshot source, manifest path, or fallback.
- `asset_fallback`: fallback icon name when used.
- `iconWidth` / `iconHeight`: display size from manifest `display`.

If an enemy is present in the spec but absent from the manifest, the injector still writes a fallback icon so the target ring is never the only identity cue.

## Validation

```powershell
& $py xivplan-ffxiv-guide\scripts\validate_image_assets.py artifacts\phase-q\enemy-assets.json
& $py xivplan-ffxiv-guide\scripts\build_xivplan_scene.py artifacts\phase-q\spec.enemy-assets.json -o artifacts\phase-q\scene.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_xivplan_scene.py artifacts\phase-q\scene.xivplan
```

Acceptance criteria:

- Every normal step enemy has a non-empty `icon` or `image`.
- Dedicated PNG assets pass alpha, transparent-corner, subject-coverage, and size checks.
- Fallback-only manifest entries are explicit and reported.
- Generated `.xivplan` scenes preserve enemy name, target ring, icon, and asset status together.
