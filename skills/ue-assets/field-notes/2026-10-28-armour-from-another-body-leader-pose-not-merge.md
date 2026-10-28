---
symptom: a modular armour/clothing pack made for one body (UE5 Manny/Quinn) has to go on another body (a MetaHuman) and keep its own materials and LODs; merging the pieces into one skeletal mesh skews them, baking them into one atlas ruins close shots
engine: "5.8.1"
status: observed
date: 2026-10-28
source: one hero rebuilt three ways in one session; the first two failed in the close-up review
---
Three ways to dress a hero in a pack's pieces, and what each cost:

1. **Bake everything into one mesh + one atlas** (one draw, one material - the cheapest on a board of many figures).
   Fine for a far camera; at a close-up the atlas density was ~5 px/cm at 2K, ~10 at 4K, and the decimated pieces
   showed facets. Raising the atlas to 4K and dropping the decimation barely changed the close shot: the ceiling was the
   source's own textures. Before upgrading the bake, check whether the source itself is good enough.
2. **`USkeletalMergingLibrary::MergeMeshes` / `FSkeletalMeshMerge`** keeps materials and LODs, but builds ONE reference
   skeleton: pieces skinned in another body's bind pose (Quinn) render skewed against a body in its own (MetaHuman).
3. **Leader-pose followers** (one `USkeletalMeshComponent` per piece, `SetLeaderPoseComponent(body)`): each piece keeps
   its own bind pose, materials and pack LODs; it only needs the body to have its bone names. This is the one that held
   the close shot. Cost: a skinned component per piece (no anim evaluation) and a draw per material slot.

Checks that saved rounds:
- Survey the packs by LOD count and texture size before picking (a commandlet over `SkeletalMesh` assets:
  `SkeletalMeshEditorSubsystem.get_lod_count`, the material instances' texture sizes) - in that library one pack had
  4 LODs and 4K maps on every piece, the other 1 LOD and 2K.
- Preview the fit first with the pieces led by the target body in the editor world, before any import work.
- Can the pieces be re-assigned to the target skeleton? Diff the bone names: the pack skeleton carried `ik_*`,
  `weapon_*`, `center_of_mass`, `interaction` the MetaHuman skeleton lacks - re-assigning would have meant editing a
  shared skeleton; leader pose needs none of that.
- Everything that copies the body mesh (a ghost/stealth material swap, an ice shell, a death dissolve shell) must also
  cover the followers, or the armour stays opaque / vanishes in one frame.
- Cap the pack's 4K maps at 2K for the game (`max_texture_size`), Character texture group: per piece 2K still beats a
  shared atlas.
