---
symptom: an emissive opening or a point light inside a cavity looks right on one map and fills with a flat cream/white haze on another (bright, foggy) map
engine: "5.8.1"
status: observed
date: 2026-11-01
source: retro — the same creature and Level Sequence moved from a dark lava map to a bright map with volumetric height fog; frames compared with the emissive parameter set to 0, 0.8, 1.5, 3, 12
---
Two causes stacked, both invisible on the first (dark) map:

- **Point light in volumetric fog.** Inside a cavity the light lights the fog volume, not just the walls: the opening
  looks filled with glowing milk. Set `volumetric_scattering_intensity` on the light to 0–0.15 on any map with
  volumetric fog.
- **Emissive is exposure-relative.** An emissive strength tuned under a dark map's exposure is several times too strong
  where the scene is bright and auto exposure sits elsewhere; with bloom and fog in front it turns from orange to cream.
  Here 12 → 1.5.

Method that found it in two frames: override the parameter to 0 through a dynamic material instance in PIE and capture
the same frame — if the haze is gone, it is the emissive; then pick the value by a capture at two or three strengths.
Re-tune glow per map whenever an asset moves to a map with different fog or exposure.
