# Enemy Image Asset Workflow

Phase Q makes every Boss, clone, add, and untargetable mechanic source visually identifiable beyond the target ring and name label.

## Policy

- Convert user-provided enemy appearance notes into an `asset_brief` before requesting or reusing an image.
- Prefer user screenshots, strategy screenshots, first-person captures, FF14 Chinese wiki references, or public guide/video references when an encounter is known.
- If the appearance cannot be confirmed, use a guide-friendly generic Boss/add fallback icon and mark the asset as `fallback`.
- Do not copy official UI art, logos, watermarks, or original game artwork exactly. Generate or draw small original guide icons with a clean silhouette.
- Icons should have transparent background, no text, clear outline, and remain readable at `64-96 px`.
- Every enemy asset decision must be written to an enemy asset manifest and every final `.xivplan` should embed the icon as a data URL.

## Known Boss Sourcing

When the encounter or Boss name is known, search the FF14 Chinese wiki first:

- Primary site: `https://ff14.huijiwiki.com/wiki/首页`.
- Access Huiji wiki without the local proxy. On this machine proxy environment variables may point to `127.0.0.1:7890`; Boss-search scripts must either set `NO_PROXY=ff14.huijiwiki.com,.huijiwiki.com` and clear `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` for the request, or create an HTTP client that ignores inherited proxy environment variables. Do not treat a proxy-routed 403/connection error as proof that Huiji wiki is unavailable.
- Search by Chinese name, English name, raid name, and alias. For example, search both `凯夫卡` and `Kefka` when the notes mention O8S / Sigmascape.
- Prefer the Boss page, duty page, or enemy/NPC page that contains a clear body screenshot, portrait, infobox image, or gallery image.
- Record the page URL, page title, image URL or screenshot source, and the visual traits used in `asset_brief`: silhouette, head/weapon shape, dominant colors, wings/horns/mask/armor, and any phase-specific difference.
- If direct wiki search or API access is blocked after a no-proxy retry, use a normal browser search constrained to `ff14.huijiwiki.com`, then fall back to user screenshots or public guide screenshots. Mark the source as `wiki-search-blocked-fallback` only after the no-proxy attempt is recorded.
- Never paste a downloaded official/wiki image directly into the final guide icon unless the user explicitly wants a copied reference. The default workflow is to create an original, simplified, guide-friendly icon inspired by the verified traits.

Phase W provides a helper for the no-proxy search and report step:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\search_boss_appearance.py `
  --boss-cn "凯夫卡" `
  --boss-en "Kefka" `
  --encounter "O8S" `
  --alias "妖星乱舞" `
  --json-out artifacts\phase-w-product-gate\boss-appearance-kefka.json `
  --markdown-out artifacts\phase-w-product-gate\boss-appearance-kefka.md
```

The report records the queried terms, proxy-bypass method, Huiji API/page
attempts, candidate URLs, image references, and a draft `icon_brief`. A blocked
wiki/API path should be recorded as `wiki-search-blocked-fallback` before using
browser search, user screenshots, or public guide screenshots.

Asset brief minimum fields:

```json
{
  "enemy_id": "kefka",
  "name": "Kefka",
  "source": "ff14-huijiwiki",
  "source_url": "https://ff14.huijiwiki.com/wiki/...",
  "source_page_title": "凯夫卡",
  "visual_traits": ["pale clown-like face", "purple/yellow costume", "high collar"],
  "icon_brief": "transparent-background chibi raid-guide boss icon, clean silhouette, readable at 72 px, no text",
  "generated_icon_path": "outputs/o8s/assets/kefka-guide-icon.png",
  "license_note": "Use wiki/game art only as reference; final icon is original simplified guide art."
}
```

Use the brief to generate or draw an original PNG icon, then validate and inject it as usual.

## Manifest Shape

```json
{
  "enemy_assets": [
    {
      "enemy_id": "fatebreaker",
      "name": "Fatebreaker",
      "kind": "boss",
      "source": "user-description",
      "source_url": "https://ff14.huijiwiki.com/wiki/...",
      "source_page_title": "Fatebreaker",
      "visual_traits": ["metallic armor", "large sword", "blue lightning accents"],
      "icon_brief": "original transparent-background Fatebreaker guide icon with sword silhouette and blue lightning accents",
      "generated_icon_path": "outputs/fatebreaker/assets/boss-fatebreaker-icon.png",
      "license_note": "Original simplified guide icon; do not copy wiki/game art directly.",
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
