---
symptom: a hood/helmet/hat on a character looks fine when the head faces forward, but when the head turns (look-at, dialogue head motion) the skull shows through, "the face turns inside the hood"; it happens in one scene and not another, even within one line
engine: "5.8.1"
status: verified
date: 2026-11-04
source: retro — a MetaHuman wearing a fitted hood, four rounds with the human before the real cause
---
- **A leader-pose follower with a relative offset on its component slides off the bone it rides.** The follower's
  bones are the leader's, but the offset is applied in the component (body) frame, not in the head's frame. Tuned with
  the head facing forward it looks right; any head rotation swings the hood around the head bone while the offset stays
  "back and down along the body" → gap at the temple, scalp poking out. How much depends on how far the head turns, so
  one scene (head toward the camera) looks fine and another (head toward a partner off to the side) does not.
- **Fix:** zero the component offset and bake the same translation into the mesh's reference-pose geometry. Rigid
  with the head bone it now follows the head. In Python: `GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh` →
  `GeometryScript_MeshTransforms.translate_mesh(offset)` → `copy_mesh_to_skeletal_mesh` (recompute normals/tangents
  off, original vertex order on) per LOD; then check the material slots are not empty and the bounds moved by exactly
  the offset.
- **Measure positions, not only rotations.** Comparing the head bone's axes between the face mesh and the hood gave
  0.00° every time and hid the problem; the head *location* differed by the offset (4.9 cm). Probe every skeletal
  component of the character: component relative transform, `get_socket_location("head")` vs the leader's. Any
  non-zero relative transform on a follower is a suspect.
- **MetaHuman audio-to-face clips carry head motion** (`HeadYaw/HeadPitch/HeadRoll`, `HeadTranslation*` curves). The
  face post-process applies them to the face mesh's head only, so anything worn on the body's head stays still while
  the face nods inside it. Take the curves off the face (zero them in the face anim graph) and add the rotation to the
  body's head bone (the body post-process that does the dialogue look-at); the face then follows the body.
- **Recompiling a Blueprint that a placed actor spawns as a child actor** can leave a twin in PIE (two copies of the
  child at the same spot) while the editor world looks clean. `ChildActorComponent.set_child_actor_class(None)` then
  back to the class in the editor world recreates the child; check the actor count in PIE before taking frames.
