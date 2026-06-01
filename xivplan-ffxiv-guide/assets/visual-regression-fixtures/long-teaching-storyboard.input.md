# Phase O Long Teaching Storyboard Fixture

Build a FRU-style long-flow teaching storyboard with at least 14 frames.

The regression runner uses the deterministic semantic builder for this case so the fixture can check:

- every step has a distinct `teaching_question`;
- each frame keeps party, enemy, waymark, mechanic, and text context;
- long-flow density remains accepted without synthetic padding;
- the final frames include reset and next-read handoff context.
