# Party Job Defaults

Phase R upgrades party rendering from eight generic role dots to official XivPlan job icons plus a short role label.

In this document, "job icon" means the built-in XivPlan official icon asset under `public/actor/<JOB>.png`. It does not mean an abstract token such as `job:samurai`, a colored role icon, or a text abbreviation drawn inside a badge.

## Default Comp

| Role | Default Job | Icon | Role Label | Notes |
|---|---|---|---|---|
| MT | DRK | `/actor/DRK.png` | `MT` | Main tank. |
| ST | PLD | `/actor/PLD.png` | `ST` | Off tank. |
| H1 | AST | `/actor/AST.png` | `H1` | Pure healer slot. |
| H2 | SCH | `/actor/SCH.png` | `H2` | Shield healer slot. |
| D1 | SAM | `/actor/SAM.png` | `D1` | Melee 1. |
| D2 | DRG | `/actor/DRG.png` | `D2` | Melee 2. |
| D3 | BRD | `/actor/BRD.png` | `D3` | Physical ranged. |
| D4 | PCT | `/actor/PCT.png` | `D4` | Caster slot. |

The default is intentionally concrete so generated diagrams can be audited without needing user-provided jobs. Users may override any job/icon assignment when a static has a specific comp.

## Party Object Grammar

```json
{
  "kind": "party",
  "role": "MT",
  "job": "DRK",
  "jobName": "Dark Knight",
  "roleLabel": "MT",
  "icon": "/actor/DRK.png",
  "image": "/actor/DRK.png",
  "iconScale": 1.0,
  "pos": "N",
  "distance": 108,
  "roleLabelPlacement": "near-icon"
}
```

Builder output keeps the same identity fields on the final `party` object:

- `role`: one of `MT/ST/H1/H2/D1/D2/D3/D4`.
- `job`: compact job code.
- `jobName`: readable job name.
- `icon`: official XivPlan job icon path such as `/actor/DRK.png`.
- `image`: same official icon path unless an explicit user-supplied image is intentionally used.
- `roleLabel`: short role text shown near the icon.
- `roleLabelVisible`: may be false only for cluster/stack frames.
- `iconScale`: clamped so the exported icon remains at least `24 px`.

## Label Rules

- Non-cluster frames must show both the official job icon and role label.
- Cluster or heavy-overlap frames may hide `roleLabel`, but must keep the official job icon readable.
- Movement and reset frames must preserve role/job/icon fields after position updates.
- `focusRoles` may lower opacity for non-focus players, but it must not remove job or role identity.
- Abstract `job:*` tokens, generic `/actor/tank.png`/`healer.png`/`dps.png` role icons, and text-only abbreviation badges do not satisfy Phase R/S default job-icon acceptance.

## Validation

`validate_xivplan_scene.py` and `audit_visual_quality.py` enforce:

- all eight roles appear exactly once in normal frames;
- each party object has job identity and the expected official XivPlan icon path;
- non-cluster frames keep a readable role label;
- cluster frames may omit role labels but not job icons;
- icons stay above the `24 px` readability floor.
