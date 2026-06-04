# UDM / Ultimate Yokai Star Dance Gold Reference

Use this reference when generating Ultimate Yokai Star Dance / UDM `.xivplan`
files. The gold sources are the local P1/P2/P3 folders under:

`C:\Users\Mahiru\Desktop\FFXIV\KING X\UDM`

The current machine profile is recorded at
`artifacts/style-analysis/udm-golden-reference-profile.md`.

## Arena Routing

- UDM / 绝妖 with P1 context should use `arena.preset: "udm-p1"`, which expands
  to `/arena/udm-phase1.png`, `backgroundOpacity: 50`, radial ticks, and no grid.
- UDM / 绝妖 with P2 context should use `arena.preset: "udm-p2"`, which expands
  to `/arena/udm-phase2.png`, `backgroundOpacity: 40`, radial ticks, and no grid.
- UDM / 绝妖 with P3 context should use `arena.preset: "udm-p3"` and the local
  phase-three UDM arena. Mahjong / 麻将-style special examples may use
  `arena.preset: "udm-p4"`.
- `绝妖星乱舞` must be routed before generic `妖星乱舞`: UDM/绝妖 uses the local
  UDM arena presets, while plain O8S / Kefka / 妖星乱舞 still uses the `omega-o8s`
  fallback unless the user explicitly requests UDM.

## Density Baseline

- The UDM P1-P3 gold set currently profiles as 10 scenes, 84 steps, 1972
  objects, and a median of 23 objects per step.
- Normal UDM generated steps should target roughly 20-30 objects per step after
  full-party, waymark, Boss, range, route, and short-label layers are present.
- Long P2-style flows may use 9-19 steps. Do not compress a multi-branch
  assignment into one frame when the gold references split it into separate
  read, assignment, movement, resolve, and reset pages.
- P1 rotation / conveyor-style frames may carry many movement arrows. Use
  `movementRoute` metadata and bend routes with `polyline` waypoints instead of
  drawing ambiguous straight-line crossings.

## Object Language

- Keep generated `.xivplan` files lightweight. Prefer XivPlan resource paths
  such as `/arena/udm-phase2.png`, `/actor/...`, and `/marker/...` over copying
  the gold files' large embedded data-URL images.
- Use `party`, `marker`, `enemy`, `circle`, `donut`, `cone`, `rect`, `tower`,
  `stack`, `arrow`, `polyline`, `icon`, and `statusOverlay` objects as the
  normalized generation vocabulary, even when `.xivplancn` references use
  names such as `waymark`, `indicatorMarker`, `fan`, or `target`.
- For status or head-marker ownership, use the Phase X `statusAssignments`
  contract. The gold folders contain buff/head-marker PNGs, but generated files
  should use traceable overlays or fallback badges rather than silently embedding
  many megabytes of copied PNGs.
- `.xivplancn` P2 references show dense short Chinese instruction labels: around
  4-10 labels and 38-87 text characters per step. Prefer compact in-scene labels
  plus route/range semantics, with longer explanation kept in `guide_text`.

## Output Policy

The user-facing skill path should generate only `.xivplan` by default. Step PNG,
SVG, contact sheets, Markdown, DOCX, or PDF are QA/release artifacts and should
only be produced by explicit full-package or regression commands.
