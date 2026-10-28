---
symptom: components added to a spawned Blueprint actor from editor Python end up attached to a component that no longer exists (null mesh, world location 0,0,0); or after killing the editor the next launch hangs - MCP calls time out, the log stops at "Engine is initialized"
engine: "5.8.1"
status: observed
date: 2026-10-28
source: one session, both reproduced
---
- `SubobjectDataSubsystem.add_new_subobject` on an actor INSTANCE re-runs its construction script: every component the
  script made (a MetaHuman BP's Body, Face...) is recreated. References taken before the add are stale - an attach or
  `set_leader_pose_component` on them silently goes nowhere. Add all components first, then fetch the components again
  and wire them; hidden/visibility changes made before the add are reset too.
- Killing the editor (`Stop-Process`) with a dirty map leaves `Saved/Autosaves/PackageRestoreData.json` listing it; the
  next launch opens a modal "Restore Packages" window that blocks the game thread, so MCP calls hang. Slate windows do
  not expose their buttons to UI Automation. If nothing in the list is wanted, close the editor, set the file to
  `{"RestoreEnabled": false, "Packages": []}` (keep a copy), relaunch. Better: before closing, check
  `EditorLoadingAndSavingUtils.get_dirty_map_packages()` / `get_dirty_content_packages()` and close only when clean.
- `EditorAssetLibrary.consolidate_assets(keep, [drop])` repoints the referencers but does NOT delete `drop`, and the
  asset registry in the same session still reports the old references - delete afterwards with
  `find_package_referencers_for_asset(p, True)` (loads to confirm) as the check, not `get_referencers`.
