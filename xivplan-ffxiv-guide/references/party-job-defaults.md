# Party Display Defaults

Party rendering now has two guide-section modes:

- `mechanic_flow`: main mechanism diagrams. Use official XivPlan numbered role icons as the visual identity, and omit extra `MT/ST/H1...` text labels by default.
- `flow_example`: illustrative flow/timeline/position examples. Keep the Phase R/S default job-icon style: official job icon plus a nearby role label.

Use `guide_section`, `guideSection`, `figure_type`, or `figureType` on the spec root or step. If omitted, the builder assumes `mechanic_flow`.

## Mechanic Flow Icons

For main mechanic diagrams, the icon already carries the official role slot:

| Role | Icon | Notes |
|---|---|---|
| MT | `/actor/tank1.png` | Tank slot 1. |
| ST | `/actor/tank2.png` | Tank slot 2. |
| H1 | `/actor/healer1.png` | Healer slot 1. |
| H2 | `/actor/healer2.png` | Healer slot 2. |
| D1 | `/actor/dps1.png` | DPS slot 1. |
| D2 | `/actor/dps2.png` | DPS slot 2. |
| D3 | `/actor/dps3.png` | DPS slot 3. |
| D4 | `/actor/dps4.png` | DPS slot 4. |

Builder output keeps `role`, `job`, and `jobName` for data consistency, but sets `partyDisplayStyle: "role-number-icon"` and normally sets `roleLabelVisible: false`.

## Flow Example Default Comp

For `flow_example`, "job icon" means the built-in XivPlan official icon asset under `public/actor/<JOB>.png`. It does not mean an abstract token such as `job:samurai`, a colored role icon, or a text abbreviation drawn inside a badge.

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

Users may override any job/icon assignment when a static has a specific comp, but generated examples must still use official XivPlan `/actor/<JOB>.png` assets.

## Party Object Grammar

Main mechanism diagram:

```json
{
  "guide_section": "mechanic_flow",
  "kind": "party",
  "role": "MT",
  "job": "DRK",
  "jobName": "Dark Knight",
  "partyDisplayStyle": "role-number-icon",
  "icon": "/actor/tank1.png",
  "image": "/actor/tank1.png",
  "roleLabelVisible": false,
  "pos": "N",
  "distance": 108
}
```

Flow example:

```json
{
  "guide_section": "flow_example",
  "kind": "party",
  "role": "MT",
  "job": "DRK",
  "jobName": "Dark Knight",
  "partyDisplayStyle": "job-icon",
  "roleLabel": "MT",
  "roleLabelVisible": true,
  "roleLabelPlacement": "near-icon",
  "icon": "/actor/DRK.png",
  "image": "/actor/DRK.png",
  "iconScale": 1.0,
  "pos": "N",
  "distance": 108
}
```

Builder output keeps the same identity fields on the final `party` object:

- `role`: one of `MT/ST/H1/H2/D1/D2/D3/D4`.
- `job`: compact job code.
- `jobName`: readable job name.
- `partyDisplayStyle`: `role-number-icon` for `mechanic_flow`, `job-icon` for `flow_example`, unless explicitly overridden.
- `icon` / `image`: the section-appropriate official XivPlan actor path.
- `roleLabel`: short role text, required for `flow_example` non-cluster frames.
- `roleLabelVisible`: false by default for `mechanic_flow`; may be false in `flow_example` only for cluster/stack frames.
- `iconScale`: clamped so the exported icon remains at least `24 px`.

## Label Rules

- `mechanic_flow` frames do not need extra `MT/ST/H1...` role-label text when numbered role icons are visible.
- `flow_example` non-cluster frames must show both the official job icon and role label.
- Cluster or heavy-overlap `flow_example` frames may hide `roleLabel`, but must keep the official job icon readable.
- Movement and reset frames must preserve role/job/icon fields after position updates.
- `focusRoles` may lower opacity for non-focus players, but it must not remove party identity.
- Abstract `job:*` tokens, generic `/actor/tank.png`/`healer.png`/`dps.png` icons as a replacement for numbered role slots, and text-only abbreviation badges do not satisfy acceptance.

## Validation

`validate_xivplan_scene.py` and `audit_visual_quality.py` enforce:

- all eight roles appear exactly once in normal frames;
- `mechanic_flow` party objects use numbered role icons;
- `flow_example` default party objects use the expected official XivPlan job icon paths;
- `flow_example` non-cluster frames keep a readable role label;
- cluster frames may omit role labels but not the required party icon;
- icons stay above the `24 px` readability floor.
