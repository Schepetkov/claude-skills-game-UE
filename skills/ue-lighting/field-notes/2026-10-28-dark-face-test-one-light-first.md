---
symptom: a character's face is dark grey in a close-up while its armour/clothes look fine and another character's face in the same shot looks right
engine: "5.8.1"
status: observed
date: 2026-10-28
source: three wrong fixes shipped before the right one; the measurement that found it took minutes
---
Measure before theorising. What found it:

1. Crop the face region of a frame and read its mean value (the dark face was ~49/255, the good one ~176).
2. Put a small point light 50 cm in front of the dark face (same channel the face is in) and capture again. If the face
   lights up, the face is fine and the lighting is missing; if it does not, look at the material.
3. Then compare the dark character's setup with the good one's: here the good one carried its own face fill light (a
   dialogue-character class), the dark one was a different actor class that wore the same kind of face without it. The
   armour looked bright only because metal reflects the bright sky; skin has nothing to reflect.

Traps on the way:
- A directional fill hung on the gameplay camera does nothing for a cinematic camera that has taken the view (it lit
  the backs, and at 200 lux changed nothing visible in the shot) - check a fill at an extreme value before relying on it.
- Change one thing per capture and undo the test change: a lighting-channel experiment left the face out of the very
  channel the next test light used, and that test read as "light has no effect".
- Hidden sections of a host mesh and their shadows/ray-traced presence were not the cause (measured: 47 → 49).
