# Arena Selection Template

Use this before writing coordinates or spec objects.

## Input Signals

- User request:
- Encounter name:
- Phase:
- Mechanic category:
- Similar-mechanic evidence:
- Screenshot or XivPlan source:

## Decision

- Selected preset:
- Background:
- Selection source: `user-specified` / `mechanic-inferred` / `default-fallback`
- Source reason:
- Fallback risk:

## Preset Rules

| Preset | Use when | Background |
|---|---|---|
| `fru-p1` | FRU P1, Fatebreaker, E11, thunder/fire swords, FRU-style death sentence or east-west safe-side reads | `/arena/e11.svg` |
| `fru-p2` | FRU P2 explicitly named | `/arena/e8.svg` |
| `eden-light` | Shiva, Light Rampant, mirror, light orb, Eden light-themed mechanic | `/arena/e8.svg` |
| `udm-p1` | UDM / 绝妖 P1 | `/arena/udm-phase1.png` |
| `udm-p2` | UDM / 绝妖 P2 | `/arena/udm-phase2.png` |
| `udm-p3` | UDM / 绝妖 P3 | `/arena/udm-phase3.png` |
| `omega-o8s` | Plain O8S / Omega / Kefka / 妖星乱舞 when no local O8S background exists | fallback overlays |
| `tile-square` | Square platform, grid, floor tile, transition platform | none |
| `default-circle` | No stronger arena signal exists | none |

## Spec Snippet

```json
{
  "arena": {
    "preset": "fru-p1",
    "source": "mechanic-inferred",
    "sourceReason": "FRU P1 / Fatebreaker context uses the Eden Promise background."
  },
  "markerPresets": "cardinals"
}
```

## Checklist

- [ ] User-specified arena was honored when present.
- [ ] `绝妖星乱舞` / UDM was resolved before plain `妖星乱舞` / O8S fallback.
- [ ] Encounter/phase inference was checked before category fallback.
- [ ] Fallback choice is labeled as `default-fallback`.
- [ ] Normal steps retain arena context for the visual quality gate.
- [ ] Waymarks are stable across steps unless the mechanic explicitly moves the reference frame.
