---
symptom: a pack's own materials and normal maps put on its meshes after a round trip through another tool (engine export -> Blender -> FBX import) render the armour and faces almost black under a key/fill light, while BaseColor is fine and other packs' parts on the same merged mesh are lit correctly
engine: "5.8.1"
status: observed
date: 2026-11-01
source: a full-quality soldier kit rebuilt from the pack's source geometry; first reported as "the fill light broke"
---
- The light was fine (lighting channels on the component were right); the WorldNormal buffer showed the faces pointing
  away from the camera. The normal maps were being read with the green channel the other way round for the re-exported
  meshes - the tangent basis of the round-tripped mesh is mirrored relative to the one the maps were baked for.
- **Fast proof without guessing:** in PIE, give one character dynamic material instances with every normal-map parameter
  set to `/Engine/EngineMaterials/FlatNormal`. If the light comes back, the normal maps (or the tangents) are the cause;
  then toggle `flip_green_channel` on the maps (in memory, not saved) and look again.
- It was per pack, not per mesh path: one pack's maps needed the flip, another pack's on the same pipeline did not.
  Set the flag in the import step for the packs that need it, so a re-run does not bring the defect back.
- Do not judge texture quality from a `SceneCapture2D` in the editor world: it does not drive texture streaming and shows
  low mips. Judge it from a game-view screenshot in PIE / `-game`.
- Right after a texture setting change (flip, max size) the editor rebuilds the textures in the background; frames taken
  in that window show white or grey placeholders that look like broken materials. Re-check after the rebuild.
