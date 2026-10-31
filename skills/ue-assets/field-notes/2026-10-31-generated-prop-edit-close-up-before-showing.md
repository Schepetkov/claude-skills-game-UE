---
symptom: a generated prop (image-to-3D) looks fine at board distance but the human sends it back for "squares" up close, ragged cuts where a part was removed, or see-through holes in a second pose built from the same mesh
engine: "any (Blender bmesh + UE import)"
status: observed
date: 2026-10-31
source: five review rounds on one prop; every defect was visible in a close-up render nobody took before showing
---
Decimating a 330k-triangle generated mesh to 10k for a board prop read as faceted the moment the camera zoomed in;
40k with smooth shading, 2K maps and engine LODs (1 / 0.35 / 0.15) was accepted. Weld vertices before decimating, or
the importer's UV-seam splits tear open. Removing a part (a chain) with a plane cut "by coordinate" sliced through the
neighbouring hinge and left an open hole: cut on the neighbouring part's outer face (`bmesh.ops.bisect_plane`
with `clear_outer`), cap with `holes_fill`, and give the cap UVs from a dark, flat texel of that part, not from an
arbitrary neighbour (it can be a highlight). A second pose made by bending one region smoothly away from a fixed one
(trap jaws shutting off their hinge posts) twisted the band into see-through loops; split the moving part
(`bmesh.ops.split`) and rotate it rigidly about the real pivot, deleting only the bits that would poke out.
Rule: before showing any mesh edit, render a close-up of every cut, seam and deformed joint (an orthographic view with
a grid to read part coordinates, a perspective close-up per joint), then a gameplay-camera frame in the engine.
