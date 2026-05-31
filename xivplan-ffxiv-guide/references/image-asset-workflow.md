# Image Asset Workflow

Phase 7 handles custom raster assets for XivPlan diagrams: animals, masks, heads, adds, crystals, encounter-specific icons, and other objects that are not already available in XivPlan.

The guiding rule is portability: every asset used by a generated `.xivplan` should be embedded as a `data:image/png;base64,...` URL so the plan still renders after moving the file.

## Workflow

1. Identify the missing asset.
   - Name the subject: "鬼头", "动物", "光水晶", "特殊分身".
   - Decide diagram role: enemy/add, mechanic icon, safe/danger marker, decorative terrain, or status icon.
   - Decide target display size, usually `32-96 px`.
2. Draft an image2 prompt from `assets/image-prompts/`.
   - Prefer a clean opaque icon on a flat chroma-key background for transparent cutout.
   - Avoid copyrighted UI art, exact game logos, watermarks, and text.
3. Generate PNG with image2 / Codex image generation.
   - For built-in image generation, request a perfectly flat chroma-key background, then remove the background locally.
   - If a true native transparent image path is unavailable, use the chroma-key removal path from the `imagegen` skill.
4. Save final PNG under a mechanism-local asset folder.
   - For sample fixtures: `xivplan-ffxiv-guide/assets/image-assets/samples/`.
   - For generated guide outputs: `outputs/<mechanic>/assets/`.
5. Validate the asset:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\validate_image_assets.py xivplan-ffxiv-guide\assets\image-assets\samples\m6s-animal-icon.png
```

6. Write an asset manifest:

```json
{
  "assets": [
    {
      "asset_id": "m6s-animal",
      "name": "M6S animal icon",
      "path": "../image-assets/samples/m6s-animal-icon.png",
      "width": 78,
      "height": 78,
      "placements": [
        {
          "step": 2,
          "key": "animal-north",
          "pos": "N",
          "distance": 150,
          "label": "动物"
        }
      ]
    }
  ]
}
```

7. Inject the asset into a compact XivPlan spec:

```powershell
& $py xivplan-ffxiv-guide\scripts\inject_image_assets.py `
  xivplan-ffxiv-guide\assets\specs\image-asset-base.spec.json `
  xivplan-ffxiv-guide\assets\image-assets\sample-asset-manifest.json `
  -o artifacts\generated-specs\image-asset-injected.spec.json `
  --replace
```

8. Build the final `.xivplan`:

```powershell
& $py xivplan-ffxiv-guide\scripts\build_xivplan_scene.py `
  artifacts\generated-specs\image-asset-injected.spec.json `
  -o artifacts\generated-xivplan\image-asset-injected.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_xivplan_scene.py artifacts\generated-xivplan\image-asset-injected.xivplan
```

## Asset Standards

| Requirement | Standard |
|---|---|
| Format | PNG |
| Background | Transparent alpha preferred |
| Padding | Transparent corners and enough padding for 32-96 px display |
| Readability | Clear silhouette at small size |
| Text | No text unless specifically needed |
| Copyright | Do not copy official game art exactly; make a guide-friendly original icon |
| Portability | Embed as data URL in generated `.xivplan` |

## Prompt Pattern

Use `assets/image-prompts/ffxiv-mechanic-icon.prompt.md` as the default source. Keep prompts asset-focused:

- Subject and role.
- Transparent/chroma-key requirement.
- Icon scale and silhouette.
- Color family if it communicates mechanic logic.
- No text, no watermark, no exact game UI reproduction.

## Review Checklist

- [ ] PNG opens locally.
- [ ] Alpha channel exists.
- [ ] Corners are transparent.
- [ ] Subject is not blank and not edge-to-edge.
- [ ] Subject remains readable when downscaled to 64 px.
- [ ] Manifest placements match the intended steps.
- [ ] Injected spec builds into a valid `.xivplan`.
