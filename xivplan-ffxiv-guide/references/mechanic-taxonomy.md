# Mechanic Taxonomy

## Purpose

Use this file to classify a written FFXIV mechanic before selecting a positioning pattern or searching encounter examples. A mechanic description may contain several categories at once. Preserve the resolution order instead of collapsing a layered mechanic into one label.

## Retrieval Contract

For every mechanic, extract:

```yaml
mechanic_id:
  cn_names: []
  en_names: []
  category: []
  required_inputs: []
  common_solutions: []
  diagram_patterns: []
  failure_modes: []
  optimization_hooks: []
  unknowns: []
```

When the user says "类似某机制", return:

1. The matched encounter mechanic and why it matches.
2. The invariant principle that transfers.
3. The details that must be re-confirmed.
4. The positioning pattern that can be reused.
5. The parts of the original strategy that must not be copied blindly.

## Core Categories

| Category | CN terms | Required inputs | Common solution shape | XivPlan diagram pattern | Typical failure mode |
|---|---|---|---|---|---|
| `raidwide` | 全屏 AoE、AOE、转场伤害 | hit count, damage type, mitigation window | plan mitigation and healing reset | boss + short text label | mitigation timing hidden inside prose |
| `tankbuster` | 死刑、换 T、双 T 分摊、无敌 | target rule, hit count, cleave radius, vuln | invuln, shared soak, swap, separate tanks | boss + tank circles + arrows | party stands inside the buster radius |
| `spread` | 散开、八方、时钟位、近远散开 | target count, radius, timing, fixed or random | clocks, role spread, priority spread | party markers + danger circles | unmarked players occupy marked safe spots |
| `stack` | 分摊、四人分摊、双分摊、小队分摊 | target count, stack size, vuln rules | full party, pairs, light parties | stack circles + participant labels | diagram omits who joins each stack |
| `tower` | 塔、踩塔、职能塔、颜色塔 | tower count, soak count, eligibility, follow-up | fixed assignments or priority fill | tower objects + role labels | tower count and assigned players disagree |
| `cleave` | 顺劈、扇形、左右刀、前后刀 | origin, facing, angle, safe side | stay behind, rotate, alternate sides | cone/line + safe highlight | boss-facing direction is ambiguous |
| `in-out` | 钢铁、月环、靠近、远离 | center, radius, order | in then out, out then in | circle/donut + numbered arrows | order is described but not drawn |
| `line-shape` | 直线、十字、X 字、井字、地火 | origin, width, travel direction, delay | pre-position, cross gaps, follow trail | line/rect/polygon + arrows | safe lane is too narrow or mislabeled |
| `knockback` | 击退、拉入、防击退 | source, distance, immunity allowed, wall risk | anti-knockback or landing pre-position | knockback source + landing zone | only the start point is drawn |
| `gaze` | 背对、看向、眼睛、视线 | gaze source, facing check timing, line-of-sight blocker | face away, face toward, hide | eye icon + facing arrows | diagram uses arena north instead of player facing |
| `tether` | 连线、远近线、拉线、传线 | endpoints, length condition, crossing rule, pass rule | pull cardinals, pair lanes, timed pass | tether + endpoint labels + arrows | routes cross or return too early |
| `debuff` | 颜色、数字、倒计时、正负极、易伤 | assignment, duration, expiration effect, incompatibilities | sort, pair, pass, clock resolve | text badges + timers + groups | color or duration is treated as cosmetic |
| `bait` | 诱导、最近、最远、仇恨、放圈 | target rule, bait count, lock timing, puddle persistence | fixed bait spots, rotate, edge drop | circles/lines + bait arrows | non-bait players steal closest/farthest targeting |
| `pass` | 传毒、传火、交换、交接 | legal receiver, contact rule, timing, max stacks | fixed relay order | tether/debuff labels + ordered arrows | pass path intersects another debuff holder |
| `rotation` | 顺时针、逆时针、旋转、转场 | anchor, direction, step count, relative orientation | fixed rotation lanes | numbered arrows around arena | absolute north is used when anchor-relative north is required |
| `clone-memory` | 分身、镜像、延迟、记忆判定 | spawn order, copied action, delay, safe inversion | observe, store, replay | clone objects + numbered snapshots | observation and execution are combined in one picture |
| `sequence` | 跳舞、大运动会、多轮处理 | timeline, checkpoints, reset points | split into atomic beats | one step per observation or resolution | one image tries to show the entire dance |
| `tile-platform` | 地板、平台、桥、格子、落脚点 | valid tiles, transition rule, fall/death wall | pre-assign lanes and landing tiles | arena polygons + tile labels | guide omits how the arena changes |
| `adds-priority` | 小怪、转火、打断、拉怪 | spawn order, kill priority, tank split, interrupt order | assign tanks and target priority | enemy objects + order labels | diagram looks correct but omits target priority |

## Common Combined Shapes

| Combined shape | Typical ingredients | What to extract first |
|---|---|---|
| Light Rampant-like | tether + tower + orb/AoE + spread | tether graph, free players, tower eligibility, final explosion order |
| Hello World-like | debuff + timer + pass + bait | debuff family, duration buckets, pass order, reset point |
| Limit Cut-like | number + ordered bait/charge + tower/puddle | number assignment, pair grouping, resolve order, safe waiting lane |
| Relativity-like | debuff + timer + clone-memory + movement sequence | timeline table first, then role lanes and reset |
| Exaflare-like | line-shape + delayed repeat + movement | origin, repeat spacing, follow or cross rule |
| Playstation-like | symbol pair + tether length + spread | pair identity, near/far condition, lane assignment |
| Tower-and-line | tower + bait/tether + line AoE | eligibility, line direction, whether tower players can move |
| Tile transition | tile-platform + knockback/bait + stack/spread | arena state before and after each transition |

## Unknowns Checklist

Before drawing a concrete strategy, ask or infer with an explicit assumption:

- How many players are targeted?
- Are assignments fixed, random, role-based, color-based, duration-based, or priority-based?
- What is the exact resolution order?
- Is arena north fixed, boss-relative, clone-relative, or anchor-relative?
- Are anti-knockback, invulnerability, and tank swaps allowed?
- Is melee uptime a hard requirement or a preference?
- Does the strategy need CN party-finder compatibility or static-specific optimization?
- Which external source or user-provided strategy is authoritative?

## Confidence Labels

Use one of these labels in encounter cards:

- `high`: the mechanic principle and transferable structure are stable.
- `medium`: the principle is stable, but common solutions vary by region or party.
- `local-verified`: this workspace contains a concrete local XivPlan or guide artifact.
- `refresh-before-use`: the encounter is current enough that the concrete strategy should be checked against an up-to-date guide or user macro before drawing.
