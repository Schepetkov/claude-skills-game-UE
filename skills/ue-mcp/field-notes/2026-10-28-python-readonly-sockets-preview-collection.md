---
symptom: from editor Python, "Property 'SocketName' / 'BoneName' ... is read-only" on SkeletalMeshSocket, "Property 'Skeleton' ... is read-only" on PreviewMeshCollection; set_properties over MCP also refuses Skeleton
engine: "5.8.1"
status: verified
date: 2026-10-28
source: Engine/Source/Runtime/Engine/Classes/Engine/PreviewMeshCollection.h (UPROPERTY(VisibleAnywhere) Skeleton); EditorToolset SkeletalMeshTools
---
- **Mesh sockets**: don't build `SkeletalMeshSocket` in Python. Use the MCP tools
  `editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools.add_socket {mesh, socket_name, bone_name}` and
  `set_socket_transform {mesh, socket_name, transform}`, then save the mesh (`EditorAssetLibrary.save_loaded_asset`).
- **PreviewMeshCollection**: `Skeleton` is `VisibleAnywhere` — not settable from Python or `ObjectTools.set_properties`,
  and `PreviewMeshCollectionFactory` does not expose its skeleton. A collection with no skeleton still works when it is
  set on the skeleton: `USkeleton.set_skeleton_additional_preview_meshes(collection)`, then close and reopen the
  animation editor. (The skeletal mesh editor ignores additional meshes — see ue-assets field note on weapon sockets.)
- `UAnimationAsset.set_preview_skeletal_mesh(mesh)` switches an animation's preview mesh; reopen its editor.
- Saving any of these while PIE runs returns False — stop PIE first.
