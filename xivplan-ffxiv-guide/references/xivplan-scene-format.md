# XivPlan Scene Format

This workspace has a local XivPlan checkout at `C:\Users\Mahiru\Desktop\FFXIV\XivPlan`.

## File Format

XivPlan `.xivplan` files are JSON scenes. The local app writes files with MIME type `application/vnd.xivplan.plan+json`; share links use compressed base64 text, but saved `.xivplan` files are plain JSON.

Root shape:

```json
{
  "nextId": 1,
  "arena": {},
  "steps": [
    { "objects": [] }
  ]
}
```

## Coordinates

- Scene center is `(0, 0)`.
- `x` positive is east/right.
- `y` positive is north/up.
- A common local FRU planning scale used previously is `1m = 15 XivPlan coordinate units`; use only when the user wants map-distance conversion.

Default arena from the app:

```json
{
  "shape": "rectangle",
  "width": 600,
  "height": 600,
  "padding": 120,
  "grid": { "type": "rectangle", "rows": 4, "columns": 4 }
}
```

Useful arena variants:

```json
{ "shape": "circle", "width": 600, "height": 600, "padding": 120, "grid": { "type": "radial", "angularDivs": 8, "radialDivs": 2 } }
```

## Object Types

Use scene-wide unique integer `id` values across all steps. Each object has `type` and `opacity`.

Each step may also carry a stable export title:

```json
{
  "title": "Initial positions",
  "objects": []
}
```

When the local XivPlan app exports all steps, the title is written to `manifest.json` and used in a stable PNG filename such as `step_01_initial_positions.png`. Older `.xivplan` files without step titles fall back to `Step 1`, `Step 2`, and so on.

### In-Scene Annotations

Generated Phase U scenes can declare:

```json
{
  "annotation_contract": {
    "require_in_scene_teaching": true,
    "min_callouts_per_step": 3,
    "max_callout_chars": 38,
    "prefer_axis_and_priority_labels": true,
    "convert_guide_text_to_footer": true
  }
}
```

Use `page_title` on a step to override the rendered page title derived from `title`, and use text object `labelRole` values such as `axis`, `priority`, `mechanic`, and `footer` for short guide callouts. Text objects may also set `labelBand: "top" | "bottom" | "left" | "right"` plus `labelBandIndex` to place dense annotations in stable outside-arena bands.

### Phase V Mechanic Semantics

Generated complex scenes declare:

```json
{
  "mechanic_semantics_contract": {
    "require_arrow_semantics": true,
    "require_range_semantics": true,
    "require_resolve_geometry": true,
    "require_danger_crossing_declaration": true
  }
}
```

Use `movementRoute` for required movement and reset arrows. Preserve a source (`fromRole`, `fromObject`, or `fromMarker`), a target (`toRole`, `toObject`, `toMarker`, or `toZone`), `resolveIndex`, route intent, and boolean `snapToTarget`.

Use `damagePattern` for judgment geometry. Supported kinds are `fan120`, `shareFan90`, `baitTrail`, `towerResolve`, `chargeLine`, `safeSector`, and `bossHitbox`. Every pattern keeps `label`, `source`, `targets`, `resolveIndex`, `resolveTiming`, and `aoeIntent`. Use `aoeIntent: "damage" | "safe" | "bait_history" | "future_resolve" | "reference_only"` to separate current danger from safe overlays and historical traces.

### Phase X Status Assignments

Buff/debuff or status-driven scenes declare:

```json
{
  "status_assignment_contract": {
    "require_status_overlays": true,
    "require_all_assigned_roles_visible": true,
    "require_status_icon_readability": true,
    "require_fallback_reason": true
  },
  "statusAssignments": [
    {
      "role": "MT",
      "statusName": "短红",
      "kind": "debuff",
      "statusIcon": "data:image/png;base64,...",
      "decisionGroup": "red-short",
      "visibleSteps": "all",
      "durationLabel": "短",
      "source": "user-screenshot",
      "confidence": "confirmed"
    }
  ]
}
```

When `statusIcon` is not available, use a traceable fallback badge instead of pretending a real buff icon was confirmed:

```json
{
  "role": "H1",
  "statusName": "短蓝",
  "kind": "debuff",
  "iconToken": "blue",
  "fallbackLabel": "短",
  "assetStatus": "fallback",
  "assetFallback": "status-icon-fallback",
  "fallbackReason": "No confirmed real status icon asset was provided."
}
```

The builder renders each visible assignment as an `icon` object with `statusOverlay: true`, `statusRole`, `statusName`, `decisionGroup`, `anchorRole`, `anchorPartyId`, `assetStatus`, and `fallbackReason`. It is anchored to the upper-left of the assigned party object, not to a generic group label. `audit_visual_quality.py` reports `status_assignment_score`; missing, tiny, wrongly anchored, or undocumented fallback overlays are severe in strict generated mode.

### Players

Specs and scenes can classify player rendering with `guide_section` / `figure_type`:

- `mechanic_flow` is the default. It renders numbered role icons such as `/actor/tank1.png`, `/actor/healer2.png`, and `/actor/dps4.png`; extra role-label text is normally hidden.
- `flow_example` preserves the older job-icon example style: `/actor/<JOB>.png` plus a nearby `roleLabel`.

```json
{
  "id": 1,
  "type": "party",
  "name": "MT",
  "role": "MT",
  "job": "DRK",
  "jobName": "Dark Knight",
  "partyDisplayStyle": "role-number-icon",
  "roleLabel": "MT",
  "roleLabelVisible": false,
  "icon": "/actor/tank1.png",
  "image": "/actor/tank1.png",
  "x": 0,
  "y": 180,
  "width": 32,
  "height": 32,
  "rotation": 0,
  "opacity": 100
}
```

Useful role or job images:

- `/actor/tank1.png`, `/actor/tank2.png`, `/actor/healer1.png`, `/actor/healer2.png`, `/actor/dps1.png`, `/actor/dps2.png`, `/actor/dps3.png`, `/actor/dps4.png`
- `/actor/DRK.png`, `/actor/PLD.png`, `/actor/AST.png`, `/actor/SCH.png`, `/actor/SAM.png`, `/actor/DRG.png`, `/actor/BRD.png`, `/actor/PCT.png`

Generated scenes keep a concrete data identity: MT=DRK, ST=PLD, H1=AST, H2=SCH, D1=SAM, D2=DRG, D3=BRD, D4=PCT unless the user overrides it. `mechanic_flow` displays official numbered role icons. `flow_example` displays XivPlan built-in `/actor/<JOB>.png` assets and visible `roleLabel` text in non-cluster frames. `job:*` tokens or text-only badges are invalid replacements.

### Custom Images

Local PNG imports are stored as portable data URLs on a generic image object:

```json
{
  "id": 2,
  "type": "image",
  "name": "Custom PNG",
  "image": "data:image/png;base64,...",
  "x": 40,
  "y": 20,
  "width": 64,
  "height": 64,
  "rotation": 0,
  "opacity": 100
}
```

The same `image` field on `party`, `marker`, and `icon` objects may also contain a `data:image/png;base64,...` URL when the local XivPlan PNG import button is used.

### Enemies

```json
{
  "id": 10,
  "type": "enemy",
  "name": "Fatebreaker",
  "displayName": "Fatebreaker",
  "enemyKind": "boss",
  "icon": "data:image/png;base64,...",
  "assetStatus": "dedicated",
  "assetFallback": "generic-boss-icon",
  "x": 0,
  "y": 0,
  "radius": 42,
  "rotation": 180,
  "facing": 180,
  "ring": "dir",
  "targetRing": {
    "visible": true,
    "radius": 42,
    "strokeWidth": 3,
    "style": "target-ring"
  },
  "color": "#d13438",
  "opacity": 100
}
```

`ring` may be `dir`, `omni`, or `none`; Phase P audits also read `targetRing`. Normal steps require a non-empty name/display name, a visible target ring, a radius or `targetRing.radius`, and a matching readable text label. Phase Q also requires an enemy icon: dedicated assets should be embedded as PNG data URLs, while uncertain assets use the explicit `generic-boss-icon` or `generic-add-icon` fallback. Compact specs may use `kind: "boss"`, `kind: "add"`, `kind: "clone"`, `kind: "shadow"`, or `kind: "untargetable_source"`; the builder normalizes them into `type: "enemy"` objects.

### Common Mechanic Objects

Tower:

```json
{ "id": 20, "type": "tower", "x": 0, "y": 220, "radius": 40, "count": 1, "color": "#bae3ff", "opacity": 70 }
```

Stack:

```json
{ "id": 21, "type": "stack", "x": 0, "y": 0, "radius": 70, "count": 4, "color": "#8fd14f", "opacity": 60 }
```

Circle or spread/danger zone:

```json
{ "id": 22, "type": "circle", "x": 120, "y": 120, "radius": 45, "color": "#ff8c00", "opacity": 45, "hollow": true }
```

Line AoE:

```json
{ "id": 23, "type": "line", "x": 0, "y": 0, "length": 500, "width": 80, "rotation": 0, "color": "#d13438", "opacity": 45 }
```

Cone AoE:

```json
{ "id": 24, "type": "cone", "x": 0, "y": 0, "radius": 280, "coneAngle": 90, "rotation": 0, "color": "#d13438", "opacity": 45 }
```

Arrow:

```json
{ "id": 25, "type": "arrow", "x": 0, "y": 0, "width": 160, "height": 20, "rotation": 90, "color": "#0078d4", "opacity": 100, "arrowEnd": true }
```

Text:

```json
{ "id": 26, "type": "text", "text": "MT/H1 北塔", "x": 0, "y": 260, "rotation": 0, "color": "#ffffff", "stroke": "#000000", "style": "outline", "fontSize": 18, "align": "center", "opacity": 100 }
```

Tether:

```json
{ "id": 27, "type": "tether", "startId": 1, "endId": 2, "tether": "line", "width": 4, "color": "#ffb900", "opacity": 100 }
```

Tether values include `line`, `close`, `far`, `--`, `+-`, and `++`.

## Layering

Object render layers are determined by XivPlan, but order the JSON and written instructions from background to foreground:

1. Arena and safe/danger zones.
2. AoE objects.
3. Boss/enemies and towers.
4. Player markers.
5. Tethers/arrows.
6. Text labels.

## Validation

After generating or editing `.xivplan`, run:

```bash
python scripts/validate_xivplan_scene.py path/to/file.xivplan
```

On this Windows machine, the reliable bundled Python is:

```text
C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

## Mechanic Spec Builder

Use `scripts/build_xivplan_scene.py` when the user wants an actual `.xivplan` draft from a mechanism. The builder consumes a compact spec JSON and outputs a valid XivPlan scene JSON.

Command:

```bash
python xivplan-ffxiv-guide/scripts/build_xivplan_scene.py xivplan-ffxiv-guide/assets/specs/tower-cardinals.spec.json -o artifacts/generated-xivplan/tower-cardinals.xivplan
python xivplan-ffxiv-guide/scripts/validate_xivplan_scene.py artifacts/generated-xivplan/tower-cardinals.xivplan
```

Spec root:

```json
{
  "name": "四塔分配",
  "style": "king-x-fru",
  "arena": { "preset": "fru-p1" },
  "markerPresets": "cardinals",
  "scene_contract": {
    "require_full_party_each_step": true,
    "require_enemy_each_step": true,
    "require_waymarks_each_step": true,
    "allow_partial_observation": false
  },
  "steps": [
    {
      "title": "四塔：T/H 南北，DPS 东西",
      "purpose": "展示四塔职责。",
      "guide_text": "T/H 处理南北塔，DPS 处理东西塔。",
      "checks": ["四座塔均为 2 人塔"],
      "objects": []
    }
  ]
}
```

Useful root presets:

- `style: "king-x-fru"`: applies KING X / FRU-like defaults for title text, label text, player size, Boss radius, safe/danger colors, and transparent area fills.
- `arena.preset: "default-circle"`: 600x600 radial circle.
- `arena.preset: "fru-p1"`: 600x600 circle with `/arena/e11.svg`.
- `arena.preset: "fru-p2"` or `"eden-light"`: 600x600 circle with `/arena/e8.svg`.
- `arena.preset: "omega-o8s"`: 600x600 radial fallback circle for O8S/Omega/Kefka/妖星乱舞 when no local O8S background is found; builder adds `backgroundStatus: "fallback"` plus radial tick, AC/BD axis, half-field, and fallback-note overlays.
- `arena.preset: "udm-p1"`: 600x600 circle with `/arena/udm-phase1.png`, radial ticks, and no grid for UDM / 绝妖 P1.
- `arena.preset: "udm-p2"`: 600x600 circle with `/arena/udm-phase2.png`, radial ticks, and no grid for UDM / 绝妖 P2.
- `arena.preset: "udm-p3"`: 600x600 circle with `/arena/udm-phase3.png`, radial ticks, and no grid for UDM / 绝妖 P3.
- `arena.preset: "udm-p4"`: 600x600 circle with `/arena/udm-p4.png` for UDM mahjong / 麻将-style special examples.
- `arena.preset: "ultimate-yokai-star-dance"`: generic UDM P1 fallback with `/arena/udm-phase1.png`; prefer phase-specific `udm-p1` / `udm-p2` / `udm-p3` when phase is known.
- `arena.arenaOverlays`: optional Phase W list rendered by the PNG exporter. Supported kinds are `radial_ticks`, `axis`, `half_mask`, and `ring_label_band`.
- `markerPresets: "cardinals"`: A/B/C/D at N/E/S/W.
- `markerPresets: "intercards"`: 1/2/3/4 at NE/SE/SW/NW.
- `markerPresets: "all-waymarks"`: both cardinal and intercardinal waymarks.
- `scene_contract`: when present, tells the builder and validator that normal steps must preserve full visual context.

Scene contract:

```json
{
  "scene_contract": {
    "require_full_party_each_step": true,
    "require_enemy_each_step": true,
    "require_waymarks_each_step": true,
    "allow_partial_observation": false
  }
}
```

- If a normal step omits `inherit`, the builder still fills missing party roles, a Boss/enemy anchor, and waymarks required by the contract.
- `focusRoles` may be set on a step to highlight active roles while leaving the other seven/eight party icons as `ghost` context.
- `partial_observation: true` is reserved for local observation or asset-preview frames. If the contract allows it, `guide_text` must explain why the step can omit full context.

Supported object `kind` values:

| kind | XivPlan type | Notes |
|---|---|---|
| `boss` | `enemy` | Boss/add marker |
| `party` | `party` | Use `role` such as MT/ST/H1/H2/D1-D4 |
| `marker` | `marker` | Use `marker` as A/B/C/D/1/2/3/4 or provide `image` |
| `icon` | `icon` | Status/mechanic icon with an image URL or data URL |
| `image` | `image` | Custom embedded PNG or image URL |
| `tower` | `tower` | Use `count` for soak count |
| `stack` | `stack` | Use `count` for stack size |
| `circle`, `danger_circle`, `safe_circle` | `circle` | Use `radius`, `color`, `opacity` |
| `knockback` | `knockback` | Circle-style knockback source |
| `line` | `line` | Rectangular AoE |
| `rect`, `rectangle` | `rect` | Free rectangular zone |
| `line_stack` | `lineStack` | Line stack marker |
| `line_knockback` | `lineKnockback` | Line knockback marker |
| `line_knockaway` | `lineKnockAway` | Line knock-away marker |
| `donut` | `donut` | Use `innerRadius` and `radius` |
| `cone` | `cone` | Cone AoE |
| `arc` | `arc` | Ring-sector AoE with `innerRadius` and `coneAngle` |
| `polygon` | `polygon` | Use `sides` and `orient` (`point` or `side`) |
| `starburst` | `starburst` | Use `spokes` and `spokeWidth` |
| `eye` | `eye` | Gaze marker; `invert` is supported |
| `exaflare` | `exaflare` | Repeating explosion line with `length` and `spacing` |
| `arrow` | `arrow` | Use `from` and `to` positions |
| `path`, `polyline` | `arrow` segments | Use `points` or `waypoints` for bent routes |
| `tether` | `tether` | Use `start` and `end` refs from same step |
| `label`, `text` | `text` | Text label |

Position values:

- `"center"`
- `"N"`, `"E"`, `"S"`, `"W"`, `"NE"`, `"SE"`, `"SW"`, `"NW"`
- `[x, y]`
- `{ "dir": "N", "distance": 220 }`

Optional fields:

- `distance`: radial distance for direction positions.
- `offset`: `[x, y]` added after resolving `pos`.
- `label`: auto-create a text label for a non-text object.
- `labelPos`, `labelDistance`, `labelOffset`: customize auto-label placement.
- `labelPlacement: "auto"`: place the label outside the object in an outward direction.
- `labelAvoid`: preferred collision-avoidance classes for the label audit, such as `["party", "enemy", "mechanic", "arrow", "text"]`.
- `labelAnchor`: emitted on generated text labels so audits can reason about anchor distance.
- `leaderLine: true`: draw a thin line from the object anchor to an auto-placed label.
- `arrowStyle`: one of `movement`, `preposition`, `micro`, `knockback`, `bait`, `forbidden`, or `reset`.
- `waypoints`: intermediate positions for a bent arrow route.
- `points` / `path`: full route point list for `kind: "path"` or `kind: "polyline"`.
- `curve`: simple curved-route shorthand; the builder approximates it as a two-segment bend.
- `startGap` / `endGap`: shorten a rendered arrow so the tail/head does not sit directly on a player or marker.
- `routeCheck: false`: exclude a route from crossing checks when it is intentionally not simultaneous.
- `allowDangerCrossing: true`: mark movement through a danger zone as mechanic-required.
- `key`: explicit reference name for tethers.

Step inheritance:

```json
{
  "title": "2 判定站位",
  "inherit": true,
  "updates": {
    "D1": { "pos": "NW", "distance": 220 }
  },
  "remove": ["initial-safe-zone"],
  "objects": [
    { "kind": "circle", "key": "d1-spread", "pos": "NW", "distance": 220, "radius": 48 }
  ]
}
```

- `inherit: true` copies the previous expanded step's spec objects before applying edits.
- `updates` patches inherited objects by `key`, `role`, or `name`.
- `remove` removes inherited objects by `key`, `role`, or `name`.
- `replace` removes the object with the same key and appends a replacement object.
- `guide_text`, `purpose`, `checks`, `visual_focus`, `required_roles`, `reset_state`, `storyboard_phase`, `teaching_question`, `why_this_frame_exists`, and `changed_objects_only` are preserved on the output step for guide assembly, export manifests, and storyboard audits.
- Phase O generated steps should use finer `storyboard_phase` values such as `observe_signal`, `assign_roles`, `preposition`, `first_move`, `first_resolve`, `second_move`, `second_resolve`, `reset`, and `next_read_setup`; the final scene should contain observation / assignment / movement / resolve / reset / next-read coverage and normally 6-16 steps, or 12-20 for long teaching flows.
- Contracted scenes are validated for complete MT/ST/H1/H2/D1/D2/D3/D4 role coverage, at least one named enemy anchor with visible target ring, and stable cardinal waymarks on every normal step.

Label layout audit:

```bash
python xivplan-ffxiv-guide/scripts/audit_label_layout.py artifacts/generated-xivplan/my-scene.xivplan --markdown-out artifacts/label-layout-report.md
python xivplan-ffxiv-guide/scripts/auto_place_labels.py artifacts/generated-xivplan/my-scene.xivplan -o artifacts/generated-xivplan/my-scene-labels.xivplan
```

- The audit estimates text, party, Boss, marker, mechanic, and arrow bounding boxes.
- Severe text overlap fails the label gate; review-level items are reported for manual polish.

Flow line audit:

```bash
python xivplan-ffxiv-guide/scripts/audit_flow_lines.py artifacts/generated-xivplan/my-scene.xivplan --markdown-out artifacts/flow-line-report.md
```

- The audit estimates arrow segments from `flowStart` / `flowEnd`, or from arrow center, width, and rotation.
- Severe issues include arrow crossings above the allowed threshold and arrowheads covering players, Bosses, markers, or text.
- Movement through high-opacity danger zones is reported as a review item unless the route sets `allowDangerCrossing: true`.

Visual quality audit:

```bash
python xivplan-ffxiv-guide/scripts/audit_visual_quality.py artifacts/generated-xivplan/my-scene.xivplan --json-out artifacts/visual-quality-results.json --markdown-out artifacts/visual-quality-report.md
python xivplan-ffxiv-guide/scripts/audit_visual_quality.py artifacts/phase8-e2e --json-out artifacts/phase-g/visual-quality-results.json --markdown-out artifacts/phase-g/visual-quality-report.md
```

- The audit combines context, density, label layout, flow lines, layer coverage, aesthetics, and step-story coverage into one report.
- Severe issues fail the gate; review items remain visible for human polish without blocking generated packages.
- Directory input prefers case-level `scene.xivplan` files before falling back to recursive `.xivplan` discovery.

Phase 5 regression sample:

```bash
python xivplan-ffxiv-guide/scripts/build_xivplan_scene.py xivplan-ffxiv-guide/assets/specs/phase5-multistep-style.spec.json -o artifacts/generated-xivplan/phase5-multistep-style.xivplan
python xivplan-ffxiv-guide/scripts/validate_xivplan_scene.py artifacts/generated-xivplan/phase5-multistep-style.xivplan
```

## Step PNG Export

The local XivPlan screenshot menu supports:

- Copy current step PNG to the clipboard.
- Save current step as a PNG file.
- Export every step as a ZIP file.
- Select `1X`, `2X`, or `4X` rendering scale.

The ZIP contains one PNG per step plus `manifest.json`:

```json
{
  "version": 1,
  "pixelRatio": 2,
  "stepCount": 2,
  "steps": [
    {
      "step": 1,
      "title": "Initial positions",
      "image": "step_01_initial_positions.png"
    }
  ]
}
```
