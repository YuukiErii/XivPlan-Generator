# Phase P Multi Boss / Add Identity Fixture

Build a deterministic multi-enemy scene with one main Boss, one clone, and two same-name adds.

The regression runner uses the Phase P enemy identity builder for this case so the fixture can check:

- every enemy has a non-empty name and visible target ring;
- same-name adds are automatically distinguishable by direction or index;
- enemy labels stay readable enough to avoid severe obstruction;
- `enemy_identity_score` is present in the visual quality report.
