# Enemy Identity Style Guide

Use this reference whenever a diagram contains a Boss, add, clone, shadow, or untargetable mechanic source.

## Contract

Every normal step must keep each enemy distinguishable:

- `name` or `displayName`: required and non-empty.
- `enemyKind`: `boss`, `add`, `clone`, `shadow`, or `untargetable_source`.
- `radius` or `targetRing.radius`: required for target-ring sizing.
- `targetRing.visible`: required unless the step is explicitly partial observation.
- `facing`: required when cleaves, positional reads, or relative direction matter.
- A matching short text label: required so screenshots remain readable even if the renderer style changes.

## Defaults

| Kind | Radius | Label |
|---|---:|---|
| `boss` | `32-45` | Boss name, not just `Boss`, when known. |
| `add` | `20-32` | Name plus direction or index when duplicated. |
| `clone` / `shadow` | `24-32` | Must differ from the original Boss name, such as `Boss Clone N` or `East Clone`. |
| `untargetable_source` | `28-36` | Use a named source marker with a translucent or dashed-feeling ring. |

If several enemies start with the same name, the builder should append a direction or index, for example `Add N`, `Add E`, or `Add 1`.

## Spec Example

```json
{
  "kind": "add",
  "key": "orb-east",
  "name": "Orb",
  "pos": "E",
  "distance": 188,
  "radius": 26,
  "facing": 270,
  "labelPlacement": "fixed",
  "labelPos": [248, 158]
}
```

The builder normalizes this into an `enemy` object with a visible target ring, `displayName`, `enemyKind`, `targetRing`, and an attached text label.

## Validation

`validate_xivplan_scene.py` fails if an enemy has no name, no radius / target-ring radius, hidden target ring, missing matching label, or an indistinguishable duplicate name.

`audit_visual_quality.py` reports `enemy_identity_score` and fails severe cases where enemy labels or target rings are obstructed by text, arrows, or high-opacity mechanics.
