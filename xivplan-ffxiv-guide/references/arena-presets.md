# Arena Presets

Use this reference when selecting a XivPlan arena background from user text,
encounter context, or mechanic category.

## Presets

| Preset | Background | Use When |
|---|---|---|
| `fru-p1` | `/arena/e11.svg` | FRU P1, Fatebreaker, thunder/fire swords, east-west safe-side reads, Cyclonic Break, death sentence or tankbuster diagrams in the FRU P1 visual language. |
| `fru-p2` | `/arena/e8.svg` | FRU P2 or Eden/Shiva-light style diagrams when the user explicitly names FRU P2. |
| `eden-light` | `/arena/e8.svg` | Shiva, Light Rampant, light orb, mirror, hexagram, or Eden light-themed mechanics. |
| `tile-square` | none | Square, platform, grid, floor-tile, or transition diagrams where the arena shape matters more than a raid background image. |
| `default-circle` | none | Fallback for generic mechanics or when no explicit encounter/category evidence exists. |

## Alias Map

- `fru`, `fru-p1`, `fatebreaker`, `e11`, `eden-promise` -> `fru-p1`
- `fru-p2` -> `fru-p2`
- `shiva`, `light-rampant`, `eden-light`, `e8` -> `eden-light`
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
