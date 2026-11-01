---
symptom: the human reports a hidden thing still "leaking" - its sound, its icon, its timing - right after you hid its visual
engine: "any"
status: observed
date: 2026-11-01
---
When one state visually replaces another (a stronger status supersedes a weaker one on the same target), list EVERY output of
the replaced state before calling it hidden: looping visual, start one-shot, start sound, UI icon/tooltip, pacing/pause it
adds, reaction animation it triggers. Fixing only the visual cost three more review rounds (sound, icon, extra flinch and
delay). Same for anything derived from an object: size a decal, a crack or a clearance relative to the object it belongs to,
not in absolute units - an absolute size looked right on the first test object and wrong on the next.
And check a "moment" (an effect landing) through the real action at normal speed and slowed, with sound, plus a frame a few
seconds later for leftovers - a debug command that toggles the end state never shows the moment.
