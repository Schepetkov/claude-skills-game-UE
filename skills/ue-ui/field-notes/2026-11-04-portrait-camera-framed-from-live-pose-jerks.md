---
symptom: a live 3D portrait (scene capture of a character's head) jerks or jumps at one moment of the idle loop, while the same idle on the character in the world plays smoothly; portrait camera twitches; head framing pops
engine: "5.8.1"
status: observed
date: 2026-11-04
source: measurement — per-frame camera position of a USceneCaptureComponent2D portrait vs the head bone, PIE, before/after one change
---
The portrait camera was framed every frame from the **animated** pose: it walked up the head bone's parents and took
the first one more than N cm below the head as "the neck", then put the camera relative to it. In one creature's idle
the drop between head and its parent crossed N for a few frames, the chosen "neck" switched to another bone, and the
camera jumped. The idle clip itself was clean (the seam measured 0.01 cm), so fixing the clip changed nothing — the
human saw the jerk only in the portrait.

- Anything that **chooses** bones or thresholds for framing should read the **reference pose**, once per asset:
  `FAnimationRuntime::GetComponentSpaceTransformRefPose(RefSkeleton, BoneIndex)` (AnimationRuntime.h), rotated by the
  component's quat, cached per mesh. Follow the live bone only for the smooth part (the head's position).
- A jerk reported "in the preview / portrait / icon" — check the capture path first, not the clip: record the capture
  component's location per frame next to the bone's and look for a step the bone does not have.
