---
symptom: a custom-depth stencil outline set to a dark colour shows nothing; the stencil is written (render custom depth on, value right) but no line appears
engine: "UE 5.8 (marketplace post-process outline material, stencil groups)"
status: observed
date: 2026-11-03
source: measurement (stencil read back in PIE, then the same group set to saturated magenta)
---
A dark "ink" outline for enemy pieces was set on a free stencil group of a marketplace outline post-process material.
The meshes had `RenderCustomDepth` on and the right stencil value, yet the frame showed no outline. Setting the group's
colour to bright magenta drew it at once: the material adds the outline colour on top of the scene (colour ×
brightness), so a near-black colour adds nothing.
Rule: before designing an outline colour, test the group with a saturated colour to prove the stencil → group mapping,
and read how the material composites. If it adds light, outlines can only be lighter than what they surround — use a
light rim colour (or change the material to lerp) instead of a dark one.
Also seen the same day: a Fresnel rim (`1 - |N·V|`) on a low-poly flat-shaded mesh (a 12-triangle arrow head) lights
whole faces and reads as stair-steps; a flat tone looked clean.
