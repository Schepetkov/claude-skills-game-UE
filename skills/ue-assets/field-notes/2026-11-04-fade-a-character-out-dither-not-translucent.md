---
symptom: pieces/characters that must recede (out of focus, "not part of this hint") are swapped to one grey material on every slot and look broken - fur/hair cards turn into grey squares ("there is no material"); a translucent grey version stacks into bright blobs where cards and limbs overlap
engine: "5.8.1"
status: verified
date: 2026-11-04
source: one board game, three rounds with the reviewer; frames in PIE before/after each variant
---
**Swapping every slot to one material drops the original opacity masks.** Fur, hair and foliage cards are masked by
their own textures; a flat replacement draws the whole card quad. Two looks that work:

- **Grey but solid, keep the detail**: leave the materials alone, write a custom depth stencil value on the meshes and
  desaturate/darken those pixels in a post-process blendable on the camera (`SceneTexture:CustomStencil`, compare
  `CustomDepth <= SceneDepth` so a piece standing in front is not greyed through). Texture, masks and shadows stay.
- **Almost gone (grey and see-through)**: replace the slots with an **unlit Masked material whose opacity mask is
  `DitherTemporalAA(Opacity)`** (function `/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA`,
  input `Alpha Threshold`), not a Translucent one. Each pixel is drawn or not, so overlapping cards and limbs do not
  add up; TSR smooths the pattern in motion (a single HighResShot frame shows it as sparse dots). Opacity ~0.3 + a
  Fresnel term reads as a faint silhouette; the dithered shadow mostly disappears too.

Also hide the piece's attached effects (Niagara loops, props on sockets) while faded - otherwise fire and auras stay
in full colour on an invisible body.
