---
symptom: an added organic part (horn, spike, growth) on an existing character looks toy-like or shows a seam where it meets the skin, however the junction is blended
engine: "any (Blender 5.2 + image-to-3D generator + UE import)"
status: observed
date: 2026-10-31
source: six review rounds adding horns to a game creature; the human accepted only the generated part seated like the creature's existing spikes
---
What failed, in order: a tube horn stuck into the skull (visible cut); a whole-head SDF remesh (the face melted into a
helmet after decimation); a fused skin "collar" with a rebaked 1K skin texture (blurry band); a procedural lumpy ring
over the seam ("low quality, not a demon horn"). Procedural geometry fixes the topology but not the look — organic
detail at a close-up needs an artist or a generator.

What was accepted: generate the part **with its own flared base** (image of the single part → image-to-3D with
texture), then seat it the way the model's existing spikes are seated: base point on the skin by ray-cast, rotate so
the part grows along the skin normal (blended with the intended direction) and its chord points where the concept
says, scale by the chord, **sink the base part-way into the skin** — the knobby base itself hides the intersection,
no blending needed. Mirror for the pair, parent to the head bone, decimate to budget.

Pitfalls: a glTF import splits vertices along UV seams, so "fill holes" sees thousands of open edges and spawns junk
faces — weld by distance first (UVs live on loops and survive), then cap the one real hole in the base. A generated
base is often wider than the target body (two bases met on a small skull): narrow it radially about the part axis
with a smooth falloff instead of shrinking the whole part. Check every seat from above-front and above-back — a
curved skull exposes the hollow base on one side.
