---
symptom: a screenshot series from a Python Slate tick callback writes only the last file (40 requests -> 1 PNG), or far fewer files than requested
engine: "5.8.1"
status: verified
date: 2026-11-01
source: a PIE frame-series script (HighResShot through the player controller every N Slate ticks); before/after file counts
---
`HighResShot ... filename=<path>` issued from `unreal.register_slate_post_tick_callback` is a request served on a later
rendered frame. When the editor window is focused, Slate can tick several times per rendered frame; a new request issued
before the previous one was written replaces it — with "every 2 ticks" one run of 40 requests left a single file (the
last name), and "every 3 ticks" left 24 of 45. A backgrounded editor ticks slowly and hides the problem.

Fix: before issuing the next shot, check that the previous file exists on disk and skip the tick otherwise
(`if last and not os.path.exists(last): return`). Six shots then land in ~10 s at "every 1 tick", none lost.
Reduce the request interval only after that guard is in place.
