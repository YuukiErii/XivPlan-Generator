# Arena Presets

Use this reference when selecting a XivPlan arena background from user text,
encounter context, or mechanic category.

## Presets

| Preset | Background | Use When |
|---|---|---|
| `fru-p1` | `/arena/e11.svg` | FRU P1, Fatebreaker, thunder/fire swords, east-west safe-side reads, Cyclonic Break, death sentence or tankbuster diagrams in the FRU P1 visual language. |
| `fru-p2` | `/arena/e8.svg` | FRU P2 or Eden/Shiva-light style diagrams when the user explicitly names FRU P2. |
| `eden-light` | `/arena/e8.svg` | Shiva, Light Rampant, light orb, mirror, hexagram, or Eden light-themed mechanics. |
| `omega-o8s` | none | O8S, Omega, Sigmascape, Kefka, or 妖星乱舞-style mechanics when no dedicated O8S arena asset is present locally. Use default circle plus explicit AC/BD axis, radial tick, half-field, waymark, and Boss target-ring overlays. |
| `ultimate-yokai-star-dance` | `/arena/udm-p1.png` when available | Ultimate Yokai Star Dance / UDM progression diagrams when the local XivPlan public assets contain `udm-*` arena PNGs. |
| `tile-square` | none | Square, platform, grid, floor-tile, or transition diagrams where the arena shape matters more than a raid background image. |
| `default-circle` | none | Fallback for generic mechanics or when no explicit encounter/category evidence exists. |

## Alias Map

- `fru`, `fru-p1`, `fatebreaker`, `e11`, `eden-promise` -> `fru-p1`
- `fru-p2` -> `fru-p2`
- `shiva`, `light-rampant`, `eden-light`, `e8` -> `eden-light`
- `o8s`, `omega`, `sigmascape`, `kefka`, `凯夫卡`, `妖星乱舞` -> `omega-o8s`
- `ultimate-yokai-star-dance`, `yokai-star-dance`, `udm`, `绝妖`, `绝妖星乱舞` -> `ultimate-yokai-star-dance`
- `tile`, `tile-square`, `square`, `grid arena` -> `tile-square`
- `default`, `circle`, `default-circle` -> `default-circle`

## Selection Priority

1. User-specified background wins. Examples: "background use FRU P1",
   "use e11", "Light Rampant background", "square arena".
2. Encounter and phase context comes next. Example: `encounter_name=FRU`
   and `phase=P1` selects `fru-p1`.
3. Mechanic category inference comes next. `light-rampant-like` selects
   `eden-light`; `tile-platform` selects `tile-square`.
4. Fall back to `default-circle`.

## Quality Report Wording

When reporting or auditing a generated scene, preserve the selection source:

- `user-specified`: the user directly requested a background or arena family.
- `mechanic-inferred`: encounter, phase, or detected category implied the arena.
- `default-fallback`: no strong signal was available.

Generated specs should carry:

```json
{
  "arena": {
    "preset": "fru-p1",
    "source": "user-specified",
    "sourceReason": "FRU P1 / Fatebreaker context uses the Eden Promise background."
  }
}
```

For Phase W asset-sensitive cases, run the local asset scan before assuming a
background exists:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\scan_xivplan_assets.py `
  --encounter "O8S 妖星乱舞" `
  --json-out artifacts\phase-w-product-gate\arena-assets.json `
  --markdown-out artifacts\phase-w-product-gate\arena-assets.md
```

If O8S/Omega has no local background, use:

```json
{
  "arena": {
    "preset": "omega-o8s",
    "source": "mechanic-inferred",
    "sourceReason": "no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays"
  }
}
```

The builder expands `omega-o8s` into radial ticks, AC/BD axes, a half-field
overlay, and a short fallback note so exported PNG/contact sheets show the
compensating arena language rather than a plain anonymous circle.
