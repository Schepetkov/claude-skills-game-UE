---
symptom: a MetaHuman face worn on a non-MetaHuman body looks into the corners of its eyes in dialogue - eyes look red, look apart
engine: "5.8.1"
status: observed
date: 2026-10-28
source: CTRL_expressions_eyeLook* curves read from the face anim instance in PIE (get_curve_value) - right 0.99, up 0.73
---
A MetaHuman face rides a body that follows another character's pose (game pieces "wearing" a face for a scene). The
dialogue system turns the HEAD toward the partner in the body's post-process - but this body is driven by a
pose-follow anim instance, so the head never turns. The face's gaze logic (target angle / max eye angle, clamped to 1)
then gives the eyes the whole angle: 45 degrees aside and 18 up against a 30/25 degree range saturated the curves,
the eyeballs rolled into the corners and the camera saw the red inner lids.

Check by number, not by eye: read `CTRL_expressions_eyeLook{Left,Right,Up,Down}{L,R}` from the face's anim instance.
Values near 1 mean the head is not taking its share. Fix one of:
- turn the head (a look-at on the body that actually drives the face), or
- for faces whose head cannot turn, widen the gaze range (here 75/60 degrees: the same angle moves the eyes a little
  over half way) - a subclass of the face anim class, so characters whose head does turn keep the tight range.
