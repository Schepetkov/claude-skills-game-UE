---
symptom: a material built from Python renders flat and still in game ("the material fell off, no animation"); a Custom node reports "missing input N" although every connect call returned True; a reimported mesh lost its UVs and vertex colours; an imported blue texture became a normal map; the editor froze deleting a material
engine: "5.8.1"
status: observed
date: 2026-10-31
source: retro — effect props generated in Meshy, assembled in Blender, materials and Niagara built from Python over MCP; four rounds with the human traced to these traps
---
- **Check the compile log, not the frame.** A material that fails to compile is drawn with a fallback: flat colour, no
  texture, no World Position Offset. In a capture that reads as "the texture is missing and the animation does not play",
  and you will chase the mesh instead. After every scripted material: grep `Saved/Logs/<Project>.log` from the line where
  the script started for `<MaterialName>.*Failed to compile` and the line after it (the reason).
- **One output feeding two inputs is unreliable.** `MaterialEditingLibrary.connect_material_expressions` returned True,
  yet the second Custom node (or the second input of the same Custom node, e.g. a `VertexColor` wired to `VC` and its `A`
  pin to `VA`; a `TextureCoordinate` wired to a sample's `UVs` and to a Custom input) compiled with
  `Custom material Custom missing input N`. Give every connection its own source node (a second TextureSample, a second
  TextureCoordinate, a second Time) — cheap, and it compiles.
- **`VertexColor` through pin `''` is float3 (RGB).** `VC.a` inside the Custom code is "vector swizzle 'a' is out of
  bounds". Wire the `A` pin separately — or better, keep data you need in R, G, B.
- **A texture that looks blue is imported as a normal map** (compression guessed from the pixels). Ice and water base
  colours hit this; the material then fails with "Sampler type is Color, should be Normal". Set
  `compression_settings` (`TC_DEFAULT`) and `srgb` explicitly on every imported texture.
- **Re-importing an FBX over an existing static mesh** (`AssetImportTask.replace_existing`) reused the asset's stored
  settings and dropped UVs and vertex colours (`EditorStaticMeshLibrary.get_num_uv_channels` → 0, `has_vertex_colors`
  → False). Import under a new asset name, check both numbers, then remove the old asset with the editor closed.
- **Blender join matches UV maps by name.** Parts with differently named UV maps (a generated disk `UV0`, imported glTF
  `UVMap`) end up as two layers; dropping "extra" layers after the join throws away the second part's UVs. Rename every
  part's single UV map to one name before joining.
- **`EditorAssetLibrary.delete_asset` on a material created in the same session** hit an ensure ("Failed to unload all
  packages during ForceDeleteObjects") with native references from the shader map and left a modal that froze the
  editor and the MCP server. Rebuild a material in place with `delete_all_material_expressions` (not on a material a
  class default object holds — see the 2026-10-31 Niagara note) instead of deleting and recreating it.
