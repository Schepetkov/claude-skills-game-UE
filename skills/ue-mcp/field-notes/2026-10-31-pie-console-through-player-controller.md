---
symptom: a console command sent to a running PIE does nothing ("unknown command") or HighResShot saves the editor viewport instead of the game; a frame series of a short effect is impossible with one screenshot tool; a Python script cannot spawn an actor into the play world
engine: "5.8.1"
status: observed
date: 2026-10-31
source: retro — staging and checking an ability effect (a spirit hanging over a unit on threads, flying in and out) on a test map in PIE
---
- **A project tool that runs a console command "in the play world" at world level (`GEngine->Exec(World, ...)`)
  does not reach the player controller's exec handlers.** Cheat/debug commands (`ToggleDebugCamera`, `BugItGo`) answer
  "unknown command", and `HighResShot` there captures the **editor's level viewport**, not the game view. From Python,
  run them through the controller:
  `unreal.SystemLibrary.execute_console_command(world, cmd, unreal.GameplayStatics.get_player_controller(world, 0))`
  with `world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()`. The editor's `py "<file>"
  arg ...` command passes `sys.argv`, so one script can take a `;`-separated batch of commands.
- **Frames of a short effect:** slow the game (a time-scale cvar), register `unreal.register_slate_post_tick_callback`
  and issue `HighResShot WxH filename=<path>_NN.png` through the controller every N ticks, then unregister. A
  backgrounded editor ticks only a few times a second, so N = 2 already gives frames ~0.3–0.6 s apart; drop
  near-identical frames by image difference before tiling a contact sheet.
- **`BugItGo` does not move the debug camera** (only its rotation took effect); a close-up of the game view is easier
  with a project console command that sets the game camera's pivot, arm length and angles directly.
- **`unreal.GameplayStatics.begin_deferred_actor_spawn_from_class` is not exposed to Python** (AttributeError), and
  `EditorActorSubsystem` / `EditorLevelLibrary` spawn into the editor world — a Python script cannot add a camera
  actor to PIE; reuse an existing actor or add a console command in C++.
- **A Material edited and saved from Python while PIE runs is not written to disk** (the save returns success). Redo
  the edit after stopping PIE and check the file's modification time.
