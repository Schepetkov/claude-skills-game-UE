---
symptom: a character rotated by code (spin, shake-off, twirl) reads as "a strange shake" or a wobble instead of a clean spin; a jump of yaw at the end of the move
engine: "5.8.1"
status: observed
date: 2026-10-28
source: review of a runtime take-off beat; the clip's pelvis yaw measured with AnimationLibrary.get_bone_pose_for_time
---
The take-off clip (a Paragon hero's "LevelStart") already turned the body about -330 degrees while it rose; a
procedural turn plus a shudder was added to the mesh in the same second. The two rotations fought - the reviewer saw
"a strange shake up there".

Before rotating a body in code, measure what the clip does: compose the local poses from the root down to the pelvis
(`AnimationLibrary.find_bone_path_to_root` + `get_bone_pose_for_time`, in the editor, no PIE needed) every 0.1 s and
print the unwrapped yaw and height. Then:
- if the clip already turns, add turns **on top of it, the same way and in the same window**;
- add **whole turns** (360 x n), so the body ends where the clip ends - a partial extra turn snaps back when the
  procedural rotation is removed;
- drive the angle as the integral of a trapezoid speed (fast ramp up, full speed, fast ramp down) - "sharp" but never
  a jump; no noise on top.

The same measurement also answers "is there a cool spin clip in the pack": three of ten candidate clips were checked
in seconds, and the one already in use turned out to contain the spin.
