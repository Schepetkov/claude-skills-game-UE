---
symptom: need frames of a Level Sequence playing in PIE at exact frame numbers (with live Niagara) from Python; AttributeError get_sequence_player; "'position' is an invalid keyword"; Slate screenshot shows a docked Content Browser instead of the viewport
engine: "5.8.1"
status: observed
date: 2026-11-01
source: retro — reviewing a boss birth sequence (25 fps, auto-play LevelSequenceActor) frame by frame over MCP
---
- The player: `lsa.get_editor_property("sequence_player")` (no `get_sequence_player()` in Python).
- Position: build `unreal.MovieSceneSequencePlaybackParams()` empty, then `set_editor_property("frame", FrameTime(FrameNumber(n)))`
  and `("update_method", UpdatePositionMethod.JUMP|SCRUB)`; constructor keywords fail and there is no `time_unit` property
  (frames are display-rate). `set_playback_position(params)`, then `pause()`.
- **Scrubbing to a frame leaves Niagara empty** (systems do not simulate the skipped time). For a frame with particles,
  jump ~12 frames earlier, `play()`, then pause with a second call.
- The two MCP round trips cost ~20 frames at 25 fps; measure the overshoot once (`get_current_time()`) and request
  `target − overshoot` — after that frames land exactly.
- When the human has a tab docked over the level viewport, a Slate window screenshot captures that tab. `HighResShot
  1920x1080 filename=<abs path>` through `execute_console_command(game_world, …)` renders the PIE camera regardless
  (no Slate overlay — fine for checking the picture). Delete the PNGs after reading.
