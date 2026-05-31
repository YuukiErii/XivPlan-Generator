# FFXIV Mechanic Icon Prompt Template

Use case: stylized-concept
Asset type: transparent PNG icon for an FFXIV / FF14 raid guide diagram
Primary request: Create a guide-friendly original icon for `{{subject}}`.
Subject: `{{subject}}`, represented as a clear fantasy raid mechanic object, not copied from official game UI art.
Style/medium: clean semi-flat digital illustration, crisp silhouette, high contrast, readable at 64 px.
Composition/framing: centered single object, square icon composition, generous padding, no cropped edges.
Backdrop: perfectly flat solid `{{chroma_key}}` chroma-key background for background removal.
Lighting/mood: simple soft lighting, no cast shadow, no floor contact shadow.
Color palette: `{{palette}}`; avoid using the chroma-key color in the subject.
Text: none.
Constraints: no text, no watermark, no logos, no exact reproduction of copyrighted FF14 UI icons, no background scene, no extra characters.
Avoid: gradients or texture in the chroma-key background, shadows touching the background, tiny details that disappear at 64 px.

Default values:

- `{{chroma_key}}`: `#00ff00`
- `{{palette}}`: "mechanic-appropriate colors with a bright rim and dark readable silhouette"

Post-processing:

1. Remove the chroma-key background locally.
2. Save as transparent PNG.
3. Validate with `scripts/validate_image_assets.py`.
4. Inject with `scripts/inject_image_assets.py`.
