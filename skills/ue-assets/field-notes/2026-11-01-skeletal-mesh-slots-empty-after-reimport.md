---
symptom: an imported skeletal mesh renders as flat clay / "the body has no material" although the material asset exists and compiles; the mesh's slot shows None
engine: "5.8.1"
status: observed
date: 2026-11-01
source: retro — meshes deleted and imported again from Python (legacy FBX, AssetImportTask) in a live editor; the human spotted it on the first in-game frame
---
After a delete-and-import cycle the new skeletal meshes came in with their slots set to `None`; the script that assigned
the materials had run against the previous assets. In a lit frame the mesh reads as untextured clay, which is easy to
mistake for "fog / lighting washes the colour out".

- **After every import, assert the slots**: `[s.material_interface for s in mesh.get_editor_property("materials")]` must
  contain no `None`. Do it in the import script, not by eye on a frame.
- **Assigning from Python**: changing an element of the list returned by `get_editor_property("materials")` does not
  stick. Build new structs and set the whole list:
  ```python
  slots = []
  for old in mesh.get_editor_property("materials"):
      s = unreal.SkeletalMaterial()
      s.set_editor_property("material_interface", mat)
      s.set_editor_property("material_slot_name", old.get_editor_property("material_slot_name"))
      slots.append(s)
  mesh.set_editor_property("materials", slots)
  unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
  ```
  `imported_material_slot_name` is read-only on the struct — leave it out.
