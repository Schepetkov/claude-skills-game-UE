---
symptom: fusing a new part into a character with signed distance fields (Blender + OpenVDB) gives an empty or blocky volume, a melted face, a staircase or a shading seam at the junction, or the part comes out truncated
engine: "Blender 5.2 (bundled openvdb Python module)"
status: observed
date: 2026-10-31
source: one prototype session; every item below was seen in a render and fixed
---
- `FloatGrid.createLevelSetFromPolygons` needs a **closed** mesh with consistent winding. A head with an open mouth
  and neck gave an empty interior; "sign from the nearest face normal" was blocky (flipped faces). Fill holes and
  recalc normals first.
- Do **not** remesh the whole region: far from the part the smooth union equals the original skin, so keep the
  original mesh and replace only the part plus a narrow fillet "collar". Remeshing the whole head and decimating
  9x melted the face.
- Give the collar the body's own atlas UVs (nearest point on the original surface + barycentric UV) and the body
  material — no rebake, full resolution. Copy the original custom normals onto the collar (Data Transfer,
  `CUSTOM_NORMAL`, weight 1 on skin fading into the part), or identical UVs still read as "broken tiles".
- Split skin/part along the iso-line `d_part − d_body = 0` (trilinear sampling, `bmesh.utils.edge_split` +
  `connect_verts`, smooth the line back onto the surface); assigning whole faces leaves a staircase.
- Write smooth-min as `min(a, b) − h²·k/4`, `h = max(k − |a − b|, 0)/k`. The mix form `b + (a − b)·h` in float32 with a
  1e9 "far" sentinel destroyed the field and truncated the part.
- `image.pixels` of an sRGB texture are display values; convert to linear before feeding a shader colour.
Even done right, a procedural part may still look toy-like — see the note on generated parts with a sunk base.
