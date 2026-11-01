---
symptom: a thin static mesh with a translucent material (ribbon, banner, shield FX) renders with far fewer triangles than authored and a sawtooth silhouette; the material looks right, the shape does not
engine: "UE 5.8"
status: observed
date: 2026-11-01
source: one FX session; vertex counts compared against Blender before and after the fix
---
- A project whose import default enables Nanite builds Nanite data for every imported static mesh. A translucent
  material cannot draw through Nanite, so the renderer uses the **Nanite fallback mesh** — a reduced copy
  (768 → 252 triangles on a ribbon), with no log line that points at the cause.
- Setting the `nanite_settings` property from Python (`set_editor_property`) does not rebuild the render data.
  Use `StaticMeshEditorSubsystem.set_nanite_settings(mesh, settings, apply_changes=True)` with `enabled = False`.
- Check it by numbers, not by eye: `StaticMeshEditorSubsystem.get_number_verts(mesh, 0)` should match the source
  file's vertex count.
- If the mesh is re-imported every iteration from a script, turn Nanite off after every import — the import resets it.
