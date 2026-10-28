---
symptom: after re-importing a skeletal mesh over the existing asset from Python, the mesh has 4, 6, 8... material slots (each pair duplicated); trimming the "extra" ones makes the face black and props render with the default grey grid material
engine: "5.8.1"
status: observed
date: 2026-10-28
source: AssetImportTask(replace_existing=True, FbxFactory, legacy FBX importer) run four times on one mesh in a live editor
---
Each import over the existing asset appended the file's material slots again and moved the sections onto the NEW
slots (2 → 4 → 6 → 8 → 10). The old slots look unused but are not removable by index: `materials[:2]` left the
sections pointing past the array → default material (grainy grey at distance — it is NOT shaders still compiling;
compare with the previous frame). Material IDs from `copy_mesh_from_skeletal_mesh` are not section slot indices.

Fix: a **fresh import** — close the editor, delete the `.uasset`, import with a commandlet, re-assign materials by slot
name, re-apply the LOD settings, re-add sockets. While the editor must stay open, leaving the duplicate slots all on the
same material renders correctly; never trim them.
