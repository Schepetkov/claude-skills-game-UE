---
symptom: character sinks into the floor on landing, crouches too deep after a jump attack, feet float during a scripted jump
engine: "5.8.1"
status: observed
date: 2026-10-27
source: measurement (component-space foot/pelvis heights of Paragon-style Jump_Start / Jump_Melee / Jump_Recovery clips)
---
In-place jump clips (no root motion, root at 0) still move the feet a lot relative to the root: a jump start reaches
the feet 20-30 cm *below* the root in the crouch, an air-attack clip tucks the feet 25-60 cm *above* it, the recovery
clip puts them back on the ground. A scripted beat that drives the actor's height by hand (a fixed arc plus a fixed
"landing drop") is right for one clip and wrong for the next: a -16 cm drop that put the tucked feet on the ground
at the hit kept the recovery's feet 16 cm under the floor and the pelvis 40 cm too low.

Fix: on ground phases set the actor height from the lowest foot bone of the last evaluated pose —
`ActorZ = FloorZ + AnkleHeight - (min(foot_l.Z, foot_r.Z) - ActorZ)`, interpolated (speed ~18-20) to hide the one-frame
lag; in the air take `max(arc, that height)` so the feet never pass through the floor. Start the landing clip from
its first frame (its own give), not from its deepest frame. Measure the clips first: sample root/pelvis/feet in
component space every 1/30 s (AnimationLibrary.get_bone_poses_for_time along the bone path) and read the numbers.
