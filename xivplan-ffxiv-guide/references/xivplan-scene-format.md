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

### Players

```json
{
  "id": 1,
  "type": "party",
  "name": "MT",
  "image": "/actor/tank.png",
  "x": 0,
  "y": 180,
  "width": 32,
  "height": 32,
  "rotation": 0,
  "opacity": 100
}
```

Useful role images:

- `/actor/tank.png`
- `/actor/healer.png`
- `/actor/dps.png`
- `/actor/melee.png`
- `/actor/ranged.png`
- `/actor/magic_ranged.png`

### Enemies

```json
{
  "id": 10,
  "type": "enemy",
  "name": "Boss",
  "icon": "/actor/enemy.png",
  "x": 0,
  "y": 0,
  "radius": 50,
  "rotation": 0,
  "ring": "dir",
  "color": "#d13438",
  "opacity": 100
}
```

`ring` may be `dir`, `omni`, or `none`.

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
  "arena": { "shape": "circle", "size": 600 },
  "steps": [
    {
      "title": "四塔：T/H 南北，DPS 东西",
      "objects": []
    }
  ]
}
```

Supported object `kind` values:

| kind | XivPlan type | Notes |
|---|---|---|
| `boss` | `enemy` | Boss/add marker |
| `party` | `party` | Use `role` such as MT/ST/H1/H2/D1-D4 |
| `tower` | `tower` | Use `count` for soak count |
| `stack` | `stack` | Use `count` for stack size |
| `circle`, `danger_circle`, `safe_circle` | `circle` | Use `radius`, `color`, `opacity` |
| `knockback` | `knockback` | Circle-style knockback source |
| `line` | `line` | Rectangular AoE |
| `cone` | `cone` | Cone AoE |
| `arrow` | `arrow` | Use `from` and `to` positions |
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
- `key`: explicit reference name for tethers.
