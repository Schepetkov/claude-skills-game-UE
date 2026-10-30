---
symptom: a portrait or icon filmed by a USceneCaptureComponent2D shows a different, coarse face or missing hair; correct only while the unit is selected / filmed by another camera; LOD in a capture
engine: "5.8.1"
status: observed
date: 2026-10-30
source: in-game captures of a modular character (outfit parts + head with their own LOD chains), PIE, before/after one change
---
A scene capture does not pick the LOD of a skeletal mesh for itself: the mesh keeps the LOD the **main view** chose.
A unit eighty metres from the game camera was filmed at its last LOD in a 192 px portrait. For most characters that
is invisible at that size (the far LOD is the same mesh, decimated); for a character assembled from parts with their
own LOD chains (a head and hair asset, pack outfit pieces) the far LOD looked like another person — no hair, a
different face.

It hid for weeks because a second portrait (the selected unit's panel) forced LOD0 on the unit it filmed, so the cell
portrait of the *selected* unit was right by accident.

- Every component a capture films that the main view sees from far away: `USkinnedMeshComponent::SetForcedLOD(1)`
  (1-based; 0 gives the choice back) for as long as the capture shows it, plus `PrestreamTextures` renewed per pass for
  the mips. Give the LOD back when the picture leaves the screen — and only if no other capture still films that unit
  (two owners of one flag: check both before clearing).
- Forcing the LOD only for the frame of the capture is cheaper for the main view, but the new LOD is picked up on the
  component's next update, so the capture of that frame may still use the old one — not tried here.
- The cost: those units are drawn at LOD0 in the main view too. Measure before shipping it to a handheld.
- Check a capture with the unit **not** selected / not filmed elsewhere — that is the state players see most.
