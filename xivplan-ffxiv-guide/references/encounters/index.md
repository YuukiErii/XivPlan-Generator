# Encounter Mechanic Index

## Purpose

Use this index when a user names an encounter mechanic or asks for a strategy "类似某机制". These files are retrieval cards for mechanic principles and drawing plans. They are not complete timelines and they do not override a user-provided macro, raidplan, or static convention.

## Retrieval Procedure

1. Match fight, phase, mechanic name, common alias, or mechanic family.
2. Load the relevant encounter file and `../mechanic-taxonomy.md`.
3. State the matched principle in one sentence.
4. Separate `可迁移部分` from `不应照搬`.
5. Ask only for unresolved details that materially affect the drawing.
6. Select a pattern from `../positioning-patterns.md`.

## Coverage

| Series | File | Starter coverage |
|---|---|---|
| UCOB | [ultimates/ucob.md](ultimates/ucob.md) | Twintania, Nael, Bahamut Trios, adds, Golden Bahamut |
| UWU | [ultimates/uwu.md](ultimates/uwu.md) | Garuda, Ifrit, Titan, Predation, Annihilation, Suppression, endgame |
| TEA | [ultimates/tea.md](ultimates/tea.md) | Limit Cut, Nisi/Gavel, Wormhole, Fate Calibration |
| DSR / DSU | [ultimates/dsr.md](ultimates/dsr.md) | Playstation chains, Sanctity, Dive from Grace, Death of the Heavens, Wroth Flames |
| TOP | [ultimates/top.md](ultimates/top.md) | Pantokrator, Party Synergy, Hello World, Run: Dynamis |
| FRU | [ultimates/fru.md](ultimates/fru.md) | P1-P5 representative mechanics, with local XivPlan evidence |
| UDM / Ultimate Yokai Star Dance | [ultimates/udm.md](ultimates/udm.md) | P1-P3 gold-reference arena routing, object density, and XivPlan-only output policy |
| Omega Savage | [savage/omega.md](savage/omega.md) | O1S-O12S floor-indexed; extra cards for Grand Cross, Forsaken, and Hello World |
| Eden Savage | [savage/eden.md](savage/eden.md) | E1S-E12S floor-indexed; extra cards for Light Rampant and Relativity |
| Pandaemonium Savage | [savage/pandaemonium.md](savage/pandaemonium.md) | P1S-P12S floor-indexed; extra cards for High Concept and P12S |
| Arcadion Savage | [savage/arcadion.md](savage/arcadion.md) | M1S-M12S floor-indexed; refresh live Heavyweight cards before concrete use |

See [coverage-audit.md](coverage-audit.md) for the floor-by-floor audit and scope boundary.

## Alias Map

| User phrase | Load first | Mechanic family |
|---|---|---|
| 光暴、光之失控、Light Rampant | `savage/eden.md`, then `ultimates/fru.md` | tether + tower + orb/AoE |
| HW、Hello World | `savage/omega.md`, then `ultimates/top.md` | debuff + timer + pass/bait |
| 限制切、Limit Cut、麻将数字 | `ultimates/tea.md` | numbered ordered resolution |
| 虫洞、Wormhole | `ultimates/tea.md` | limit-cut sequence + bait + puddle |
| 石牢、Gaols | `ultimates/uwu.md` | ordered random-player placement + chain explosion |
| 八龙、Grand Octet | `ultimates/ucob.md` | dynamic anchor + ordered divebomb loop |
| 相对论、Relativity | `savage/eden.md`, then `ultimates/fru.md` | timed debuff dance |
| PlayStation、PS 线 | `ultimates/dsr.md`, then `ultimates/top.md` | symbol pairs + tether distance |
| 龙诗、Darklit Dragonsong | `ultimates/fru.md` | line/tether + tower + light-party dance |
| Classical、概念、形状 | `savage/pandaemonium.md` | pair tether + shape interception |
| 热量、火风、Caloric | `savage/pandaemonium.md` | movement budget + debuff pairing |
| 糖画、小怪、动物、M6S | `savage/arcadion.md` | custom assets + adds priority + arena state |
| Sunrise、日出 | `savage/arcadion.md` | polarity + duration + cannon/tower |

## Response Contract For Analogies

```markdown
## 类比机制定位

- 我理解你指的是：
- 核心原理：
- 可迁移部分：
- 不应照搬：
- 推荐站位模板：
- 需要确认的点：
```

## Known Gaps

Phase 3 now has floor-indexed coverage for the requested Savage series. Future expansions should add:

- Region-specific CN party-finder macro variants.
- Additional per-floor cards when a less-common mechanic is requested.
- Concrete XivPlan examples for each combined mechanic family.
