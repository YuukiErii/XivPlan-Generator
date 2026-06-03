# Visual Flow Language

Use this reference when drawing movement, knockback, bait, reset, and forbidden routes in XivPlan scenes.

## Arrow Styles

| `arrowStyle` | Meaning | Visual Default | Use |
|---|---|---|---|
| `movement` | Main required movement | thick blue arrow | Role movement that must be followed now. |
| `preposition` | Early setup / minor pre-position | thin cyan arrow | Small adjustment before the main resolution. |
| `micro` | Fine adjustment | very thin pale cyan arrow | Tiny boss-circle or clock-position correction. |
| `knockback` | Forced knockback / push direction | wide white-blue arrow | Start at the knockback source and end at the landing zone. |
| `bait` | Bait path or bait handoff | amber arrow | Show where a bait target should drag the hit. |
| `forbidden` | Do-not-take route | translucent red line without arrowhead | Mark unsafe routes separately from actual movement. |
| `reset` | Return / next-mechanic setup | green arrow | Return to center, clock, light party, or the next read start. |

## Path Rules

- Prefer short, segmentable arrows over one long diagonal line that crosses the entire arena.
- Use `waypoints` or `kind: "path"` / `kind: "polyline"` when a route should bend around a tower, marker, party group, or danger zone.
- Use `curve` for a simple two-segment bend when exact waypoints are not important.
- Only the final segment of a multi-segment route should have an arrowhead unless every segment is a separate action.
- If routes still cross after bending, split the diagram into another step.

## Phase V Route Semantics

Generated complex scenes should declare `mechanic_semantics_contract.require_arrow_semantics: true`. Required movement and reset routes use `movementRoute`:

```json
{
  "kind": "movementRoute",
  "key": "d3-north-tower",
  "movementRoute": {
    "fromRole": "D3",
    "toZone": "north-tower",
    "resolveIndex": 2,
    "arrowStyle": "movement",
    "intent": "reposition",
    "startLabel": "诱导后",
    "endLabel": "进北塔",
    "snapToTarget": true
  }
}
```

Use `snapToTarget: true` only when the arrowhead is intentionally allowed to touch a declared `toRole`, `toMarker`, `toObject`, or `toZone`. Keep `snapToTarget: false` when the route stops short of the target. Declare `allowDangerCrossing: true` only when the mechanic really requires passing through the currently active danger region.

## Spec Examples

Single styled movement:

```json
{ "kind": "arrow", "key": "d1-move", "from": "NW", "to": [-45, 45], "distance": 205, "arrowStyle": "movement" }
```

Bent route with waypoints:

```json
{
  "kind": "polyline",
  "key": "d4-safe-route",
  "from": "SE",
  "waypoints": [[160, -40]],
  "to": [55, 55],
  "distance": 205,
  "arrowStyle": "movement"
}
```

Reset arrow:

```json
{ "kind": "arrow", "key": "reset-center", "from": "E", "to": "center", "distance": 180, "arrowStyle": "reset" }
```

Forbidden route:

```json
{ "kind": "arrow", "key": "bad-cross", "from": "W", "to": "E", "distance": 220, "arrowStyle": "forbidden", "routeCheck": false }
```

## Audit Expectations

- `scripts/audit_flow_lines.py` should report zero severe issues for new generated scenes.
- Arrow crossings default to zero. If a crossing is intentional and not simultaneous, set `routeCheck: false` and explain it in `guide_text`.
- Arrowheads should not cover player icons, Boss anchors, markers, or text.
- Movement arrows that pass through red/orange/purple current-danger zones are severe under the Phase V contract unless `allowDangerCrossing: true` is set for a mechanic-required route.
- `aoeIntent: "bait_history" | "safe" | "future_resolve" | "reference_only"` zones are not current-danger crossing failures.
- Phase V generated routes should report `arrow_semantics_score=100.0`; missing start, endpoint, intent, resolve round, or boolean endpoint-snap declaration blocks release.
