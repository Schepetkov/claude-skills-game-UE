---
symptom: editor crashes "Old world ... not cleaned up by garbage collection while loading new map" / Fatal error EditorServer.cpp after copying a map from Python; or the SOURCE .umap shows modified after a "copy"
engine: "5.8.1"
status: verified
date: 2026-10-27
source: two failed attempts in one session (crash log + git status of the source map)
---
Copying a level from an editor Python script, then working in the copy:

- `EditorAssetLibrary.duplicate_asset(src_map, dst_map)` followed by `LevelEditorSubsystem.load_level(dst_map)` in the
  same call crashes the editor: the duplicate stays in memory as a standalone `UWorld`, and loading its package as the
  editor world hits the "old world not cleaned up" fatal check. The copy is not on disk yet, so it is lost too.
- `EditorLoadingAndSavingUtils.save_map(open_world, dst_map)` as a "save as" writes the copy, but it also re-saved the
  open source map (a 2-line binary diff in git). Restore the source from version control afterwards, or copy the
  `.umap` file on disk while the source is not loaded.
- `EditorAssetLibrary.does_asset_exist(dst_map)` returned False for an existing map while a PIE session was running —
  a script that copies "if missing" then copies again. Check the file on disk, and refuse to touch the editor world
  while `UnrealEditorSubsystem.get_game_world()` is not None (`get_editor_world()` is None then anyway).

Safe recipe: copy once, by hand or with the file copy of the closed package, check `git status` of the source; every
later run only loads the copy.
