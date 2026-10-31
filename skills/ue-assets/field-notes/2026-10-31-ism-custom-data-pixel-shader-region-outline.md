---
symptom: an ISM material that reads PerInstanceCustomData draws as if every value were 0 (edges never light, only the uniform fill shows)
engine: "5.8.1"
status: observed
date: 2026-10-31
source: retro — board "region of light" overlay (range and area-of-effect frame) built as an ISM of tile planes
---
- **Per-instance custom data used in the pixel shader: route it through a `VertexInterpolator`.** Wired straight into
  a Custom node that feeds Emissive/Opacity it read 0 on a translucent unlit ISM; the same data through
  `MaterialExpressionVertexInterpolator` worked at once. CPU side was right all along
  (`per_instance_sm_custom_data` showed the expected values) — check both ends before blaming the data.
- **Outline of an arbitrary set of grid cells without a mesh rebuild:** one ISM plane per cell, custom data 0 = an
  8-bit mask of which of the eight neighbours lie outside the region (N/E/S/W + diagonals). The shader decodes the bits
  (`fmod(f, 2)`, `floor(f / 2)`), takes the distance to each flagged side and to inner corners only where both
  orthogonal neighbours are inside, and lights `1 - smoothstep(w/2, w, d)` as the line plus `exp(-d / glow)` as the
  halo. Concave notches (a hole where the caster stands) and board-edge clipping come out right with no geometry
  work. Map the bits to UV with the mesh's real UV layout — `/Engine/BasicShapes/Plane` is u = (x+50)/100,
  v = (y+50)/100 — read it once from the mesh description rather than guessing.
- Emissive above 1 on the line (and a whiter core than the halo) is what makes it read as light under bloom rather
  than as a painted stripe; keep the inner fill alpha low (~0.05) or the region reads as a coloured carpet.
