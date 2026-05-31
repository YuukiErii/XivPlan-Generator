# Positioning Patterns

## Purpose

Use these reusable layouts after classifying the mechanic with `mechanic-taxonomy.md`. Patterns are defaults, not fight facts. User macros, static conventions, and encounter-specific anchors always win.

## Default Role Map

| Role | Default clock | Common responsibility |
|---|---|---|
| MT | 北 | boss facing, north tank bait |
| ST | 南 | off-tank bait, south tank bait |
| H1 | 西 | west healer lane |
| H2 | 东 | east healer lane |
| D1 | 西北 | west melee lane |
| D2 | 东北 | east melee lane |
| D3 | 西南 | west ranged lane |
| D4 | 东南 | east caster lane |

Default field markers are `A` north, `B` east, `C` south, `D` west, with `1/2/3/4` on intercards. If a local strategy uses another numbering order, state the override once and draw the marker map.

## Pattern Cards

### Eight-Way Clocks

- Use for: fixed spreads, repeated bait circles, personal towers.
- Default: one player per clock based on the role map.
- Optimize: keep MT, ST, D1, and D2 closer when the mechanic radius allows; move ranged and healers outward first.
- Confirm: spread radius, whether boss-facing changes the anchor, and whether cardinals/intercards are swapped.
- Draw: initial clocks, danger-circle resolution, reset.

### Light Parties

- Use for: two four-player stacks, mirrored tower sets, left/right platform handling.
- Default: `MT H1 D1 D3` and `ST H2 D2 D4`.
- Optimize: keep each melee on the boss-facing side of its group where possible.
- Confirm: north/south or west/east split, healer assignment, stack size, and whether roles must swap.
- Draw: split line, two group labels, destination arrows.

### Pairs

- Use for: four two-player stacks, partner towers, repeated short tether mechanics.
- Default: `MT+D1`, `ST+D2`, `H1+D3`, `H2+D4`.
- Optimize: preserve the same partners across the guide unless a mechanic forces reassignment.
- Confirm: pair composition, pair lane, and whether each pair needs one support plus one DPS.
- Draw: four pair labels, pair destinations, reset point.

### Cardinal Towers

- Use for: four towers at `N/E/S/W`.
- Default if only roles are given: `MT/H1` north, `ST/H2` south, `D2/D4` east, `D1/D3` west.
- Optimize: make the assignment macro-readable and preserve melee access if tower radii allow.
- Confirm: soak count, eligibility, and post-tower movement.
- Draw: tower count labels and assigned players inside each tower.

### Two-Lane Priority

- Use for: fill mechanics where a subset is randomly selected and the rest adjust.
- Default: define one ordered list or two mirrored lists, then fill the first legal slot.
- Optimize: prefer a deterministic macro over live visual sorting when both solve the mechanic.
- Confirm: whether the sort is global, role-based, left/right, or debuff-specific.
- Draw: priority list beside the arena and one example assignment.

### Relative North

- Use for: clone-relative, boss-relative, add-relative, or safe-lane-relative mechanics.
- Default: label the anchor as `新北` and state when the anchor locks.
- Optimize: turn all later instructions into anchor-relative directions once the anchor is known.
- Confirm: whether players may pre-position before the anchor appears.
- Draw: observation step, anchor arrow, transformed marker map.

### Near/Far Baits

- Use for: closest/farthest cones, lines, jumps, or tankbusters.
- Default: separate baiters and non-baiters into distinct radii.
- Optimize: leave a visible buffer between bait radii so small movement does not steal targeting.
- Confirm: lock timing, number of targets, and whether baiters rotate.
- Draw: concentric bands, bait labels, line/cone result.

### Knockback Landing

- Use for: center knockbacks, tower-side knockbacks, platform landings.
- Default: draw source, pre-position, travel arrow, and landing zone.
- Optimize: offer anti-knockback and manual landing routes only if both are legal.
- Confirm: exact distance, immunity rules, walls, and follow-up spread/stack.
- Draw: before knockback, landing, follow-up resolution.

### Tether Lanes

- Use for: pull-apart lines, breakable chains, cardinal tether baits.
- Default: assign endpoints to non-crossing lanes.
- Optimize: shorten travel while leaving enough length margin.
- Confirm: pass/break threshold, endpoint identity, crossing restriction, and return timing.
- Draw: tether graph first, then movement arrows, then resolved lanes.

### Timeline Buckets

- Use for: relativity, Hello World-like debuffs, long dances.
- Default: group players by debuff family and duration, then build a beat table.
- Optimize: reuse waiting spots and reset points; keep each diagram to one beat.
- Confirm: durations, expiration order, movement locks, and whether debuffs pass on contact.
- Draw: timeline table plus 4-10 small steps.

### Tiles And Platforms

- Use for: changing arena floor, bridge routes, safe tiles, fall-risk mechanics.
- Default: draw arena state explicitly in every step.
- Optimize: keep each role in a stable lane across transitions.
- Confirm: which tiles are legal, whether movement is forced, and where melee can retain uptime.
- Draw: arena-state snapshot, route, landing/stack.

## Pattern Selection Rules

1. Start from mechanic safety and eligibility.
2. Preserve fixed partners, light parties, or priorities across consecutive mechanics when possible.
3. Prefer stable lanes over last-second crossing.
4. Keep casters and healers on waiting spots that resolve multiple beats when legal.
5. Keep melee inside the target ring when legal, but never trade away safety margin without saying so.
6. Split observation, movement, resolution, and reset into separate XivPlan steps.

## Pattern Output Template

```markdown
## Positioning Pattern

- Base pattern:
- Anchor:
- Fixed assignments:
- Random adjustments:
- Melee uptime note:
- Caster movement note:
- Reset point:
- Needs confirmation:
```
