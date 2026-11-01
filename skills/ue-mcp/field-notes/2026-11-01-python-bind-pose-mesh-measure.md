---
symptom: measuring a skinned mesh around a bone from editor Python fails - AttributeError on get_ref_pose, "takes at most 2 arguments" on get_all_vertex_positions, "'GeometryScriptVectorList' has no attribute 'list'", "Property 'Notifies' is protected"
engine: "UE 5.8.1"
status: observed
date: 2026-11-01
---
Working calls in 5.8.1 Python (editor or commandlet), to measure e.g. a limb's thickness at a socket in bind pose:
- Bind pose: `pose = unreal.AnimPoseExtensions.get_reference_pose(skeleton)` (may return a tuple - take the AnimPose),
  then `unreal.AnimPoseExtensions.get_ref_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD)`; socket position =
  that transform's `transform_location(socket.relative_location)` (`skeletal_mesh.find_socket(name)` finds skeleton sockets too).
- Vertices: `GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(sk, unreal.DynamicMesh(), GeometryScriptCopyMeshFromAssetOptions(),
  GeometryScriptMeshReadLOD())`, then `GeometryScript_MeshQueries.get_all_vertex_positions(mesh, False)` (two arguments). Both
  return tuples - pick the `DynamicMesh` / `GeometryScriptVectorList` by type; the list converts with the method
  `vector_list.convert_vector_list_to_array()` (there is no `GeometryScript_ListUtils` module).
- `AnimSequence.notifies` is protected: use `unreal.AnimationLibrary.get_animation_notify_events(seq)`.
- `AnimationLibrary.get_bone_pose_for_time` returns the bone's LOCAL transform - constant for a hand under an animated arm. For a
  path in mesh space use `AnimPoseExtensions.get_anim_pose_at_frame` + `get_bone_pose(..., AnimPoseSpaces.WORLD)`.
