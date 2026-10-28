---
symptom: a sword/axe/staff baked into a character's skinned mesh sits wrong in the fist (too far, crossguard through the fingers, unnatural angle) and every adjustment is a DCC edit + re-import; the person reviewing cannot tweak it themselves
engine: "5.8.1"
status: verified
date: 2026-10-28
source: Engine/Source/Editor/Persona/Private/PersonaToolkit.cpp (bAllowOverrideMesh / SetAllowAdditionalMeshes); Engine/Source/Runtime/Engine/Classes/Engine/PreviewMeshCollection.h (Skeleton is VisibleAnywhere); one weapon placed after two hours of vertex edits
---
**Do not bake a rigid weapon into a skinned mesh.** Put it on a **mesh socket** and attach a static mesh component to it
(`SetupAttachment(Body, SocketName)`, relative transform identity). Then the placement is one transform, editable by
the person who judges it, with no re-import.

Making the socket editable by eye:
- The **Skeletal Mesh editor never shows Additional Meshes**: `PersonaToolkit.cpp` sets
  `bAllowOverrideMesh = GetContext() != USkeletalMesh` and `SetAllowAdditionalMeshes(bAllowOverrideMesh)`. If the
  mesh with the socket is only a head/face (the body is separate outfit meshes), the hand is invisible there.
- Use the **Animation editor** of an idle clip: Preview Mesh = the mesh that owns the socket, Additional Meshes = a
  `PreviewMeshCollection` with the body/gloves. Mesh sockets show in its Skeleton Tree ("Mesh Only") and are
  editable there; right-click the socket → Add Preview Asset → the weapon. The fist is closed in the clip pose,
  unlike the reference pose. Save the **mesh** afterwards (sockets live in it).
- Measure "forward" from the body (clavicle_l → clavicle_r, cross with up), not from the actor: a figure turned by
  its mesh is off from `GetActorForwardVector` (27° in the case seen).
- A fresh import of the mesh (delete + import) drops its sockets: put them back with the same transform.
- After the human says "done", check the asset's file date: an edit in the editor is not on disk until saved.

Cutting the weapon out of an already-baked mesh: copy the skeletal mesh LOD0 to a DynamicMesh
(`GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh`), delete the other triangles
(`GeometryScript_MeshEdits.delete_triangles_from_mesh` + `GeometryScript_List.convert_array_to_index_list`), move it
into a weapon frame (`inverse_transform_mesh`; origin at the guard = widest slice along the PCA axis, X to the tip),
`GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh`; the socket's transform = frame × inverse(bone
reference pose).
