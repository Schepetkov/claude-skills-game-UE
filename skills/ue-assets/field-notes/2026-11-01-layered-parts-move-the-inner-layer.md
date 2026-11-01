---
symptom: in a modular character kit, hair (or ears) pokes through helmets and hoods; an automatic fix that pushes the helmet outward over the hair makes things worse - a multi-piece helmet comes apart, a two-layer mail hood blows into a spike
engine: "5.8.1"
status: observed
date: 2026-11-01
source: one modular soldier pool, three review rounds on the same defect class
---
Pieces of a modular pack interpenetrate already in the source (the pack's "hat" hair morph does not fit its own helmets),
and per-part decimation and per-part engine LODs pull the layers further apart. What held, and what did not:

- **Move the inner layer, never the outer shell.** Pushing helmet vertices outward (a smoothed radial field from the skull
  centre) passed every numeric check and still broke two assets: a helmet made of separate pieces (dome, band, mask, mail
  curtain) - each piece moved by a different amount, the dome lifted off the band and the mask off the face; a mail hood
  with an outer and an inner shell - the push pulled one shell into a long spike. The outer layer is what the camera sees;
  leave it exactly as authored.
- **Inner layer rules that worked:** press under-helmet hair radially to just under the tightest covering shell, never
  below the scalp; where the shell is tighter than the scalp, sink the hair under the skin (it is invisible there anyway);
  frontal hair left in a face opening sinks too. A beard that reaches through a given helmet is kept out of that helmet
  (a tag pair the kit picker checks) instead of being fitted.
- **Not every head cover is a helmet.** Some torsos carry their own hood. Find covers by geometry (a ray straight up from
  the skull centre hits the part) rather than by category, and give such a kit no hair at all - "just hide the hair under
  the mail" was the accepted answer.
- **Make your own LODs for the layered parts** and fit each LOD: the engine reduces every part alone and the layers
  drift again. 10 % of a 1.3k-triangle helmet shattered; 20 % held.
- **Check by numbers AND by close-up frames of every cover**, from the front and the back, at the LOD the low settings
  use. The ray metric said zero; only a close frame showed the split helmet.
- Ray metric pitfalls: a skull centre at the head bone sits at the nape (rays graze the back of the helmet) - use the
  head part's box, below the top; a helmet surface buried in the skull (an inner plate) is invisible - skip hits deeper
  than ~1 cm inside the head; the neck stump below the chin is under the torso - cut it from the check.
