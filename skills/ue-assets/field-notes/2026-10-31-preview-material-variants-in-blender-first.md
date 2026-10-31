---
symptom: material look variants for a character (glow, fire, emissive cracks) need the human's pick, but the shared editor is busy (another session's PIE, a held lock) and every round through the engine is slow
engine: "UE 5.8, Blender 5.2"
status: observed
date: 2026-10-31
source: retro (variant pick accepted on the first showing)
---
Build the same node graph that will go into the engine in Blender (same maps, same parameters per variant), put the
copies of the figure side by side with labels, animate noise offsets and flicker with drivers on `frame` (Space plays
it), Eevee + bloom, pack all images, open the file through the camera in Rendered shading. The human picks there; only
the chosen graph is built in the engine. The editor is not needed for this step at all.

Pitfalls met on the way (Blender 5 Python):
- The compositor is no longer `scene.node_tree`: create a `CompositorNodeTree` node group with an output socket, assign
  it to `scene.compositing_node_group`, finish with `NodeGroupOutput`.
- Copying a rigged figure: an action on the armature object can key the object's own transform, so setting the copy's
  location does nothing - offset each copy through a parent empty instead.
- `obj.parent = other` from Python resets `matrix_parent_inverse`; for bone-parented parts (horns on the head bone)
  copy it back from the source object, or the parts end up metres away.

Mask for emissive cracks painted into the base colour: derive it from the base colour's chroma (`R - max(G, B)`, grey
skin gives 0) rather than from an older emissive map, which may cover only part of what is painted.
