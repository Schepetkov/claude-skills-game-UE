---
symptom: dust/smoke from an earlier beat still hangs in the last shot; a code camera shake leaves the camera pointing at the floor; a borrowed impact effect draws a flat coloured disc
engine: "5.8.1"
status: observed
date: 2026-10-28
source: frame-by-frame review of a runtime-scripted impact and take-off (Cascade emitters, a CameraActor shot)
---
Three things that slipped through a scripted beat (all fixed, all invisible until the frames were taken):

- **Spawned emitters outlive the action.** Fire-and-forget `SpawnEmitterAtLocation` dust from the blow, the take-off
  and a shake-off was still drifting in the closing shot. Keep the returned components; `Deactivate()` when the action
  ends (no new particles), `DeactivateImmediate()` before the next shot that must be clean. Check the LAST shot too.
- **A shake added with AddActorLocalRotation accumulates.** Each frame's jolt stacks on the last; in slow motion
  (review at low time dilation = many frames) the camera drifted to the floor. Keep the shot's aim in a separate
  value, set aim + jolt every frame, and put the aim back at the end.
- **Ability effects from game packs carry gameplay indicators.** A hero's leap-smash system drew its area-of-effect
  disc - a flat yellow half-circle on the ground. Look at a borrowed effect in the shot before keeping it; a plain
  ground-dust system is usually the better impact layer.
