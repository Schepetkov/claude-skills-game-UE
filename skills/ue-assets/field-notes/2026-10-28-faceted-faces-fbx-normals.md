---
symptom: a character's face (or any smooth surface) shows flat triangles and dark blotches in a close-up, only on meshes that went through Blender; the same mesh looks fine in Blender
engine: "5.8.1"
status: observed
date: 2026-10-28
source: two hero meshes fixed and measured in one session; 150+ figure meshes found with the same import setting
---
Blender's FBX export with `mesh_smooth_type="OFF"` writes the per-corner normals but no smoothing groups. The legacy FBX
importer's default `normal_import_method = FBXNIM_COMPUTE_NORMALS` throws the file's normals away and, with no smoothing
groups, computes faceted ones; the tangent-space normal map baked against smooth normals then shows as dark patches.

- Import with `FbxImportUI.skeletal_mesh_import_data.normal_import_method = FBXNIM_IMPORT_NORMALS` (and the static mesh one).
- Check what an asset got: `asset_import_data.normal_import_method` (legacy FBX data) - a census over a folder is cheap.
- Fixing an existing asset: a re-import (an `AssetImportTask` with `replace_existing` over it) keeps the asset's STORED
  import settings and can reshuffle material slots (19 became 34). Record slot -> material and the LOD setup, delete the
  `.uasset` with the editor closed, import fresh at the same path (references by path survive), put the materials and LODs
  back. If the FBX goes to Interchange instead of the legacy importer, `Interchange.FeatureFlags.Import.FBX 0` for the run.
