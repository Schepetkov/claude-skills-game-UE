---
symptom: the editor (and the MCP server) froze for minutes after a Python asset script; an imported static mesh came in 100x too big; a pack's hit effect drew a huge grey ball; a pack's weapon trail drew a giant dark sheet across the map; a Python probe found no runtime-spawned component on an actor; a material reference looked missing in the .uasset bytes
engine: "5.8.1"
status: observed
date: 2026-10-31
source: retro — a status-loop prop (Meshy → Blender → import) and a claw trail built over MCP; one return from the human plus one editor freeze traced to these traps
---
- **`AssetTools.create_asset` over an existing name opens a modal "Overwrite Existing Object" dialog** and the game
  thread waits on it — the editor and every MCP call hang until a human clicks. During PIE,
  `EditorAssetLibrary.does_asset_exist` returned False for an asset that existed, so a "create if missing" guard walked
  straight into it. In scripts you re-run, only `unreal.load_asset(path)` and stop if it returns None; create assets in a
  separate one-time script, never in the edit script.
- **Blender FBX export with `global_scale=100` + legacy FBX import = 100x mesh.** The legacy importer converts units
  itself; a 1.9 m prop arrived 190 m wide (check `get_bounding_box()` after every import). `source_models` / build scale
  of a `StaticMesh` is not reachable from Python ("Failed to find property"), so the fix is delete the fresh asset and
  import again with `FbxImportUI.static_mesh_import_data.import_uniform_scale = 0.01` (or export at scale 1).
- **A pack's hit effect drew an opaque grey sphere for two frames**: its mesh emitter used a material that failed to
  compile ("Texture Sample> Missing input texture" — an earlier cleanup had dropped the texture reference), so the mesh
  got the default material. The `Failed to compile Material` line in the log names it; the fallback hides it in captures
  as "some grey thing". Check the log for every material of every system an ability plays, not only your own.
- **A texture "missing" from a material's byte-grep may be present under a numeric suffix.** `grep -a -o "/Game/..."`
  over a `.uasset` shows `T_Cave_Noise` while the asset is `T_Cave_Noise_14`: an FName's trailing number is stored as a
  separate integer. Compare against the source pack's asset list before re-importing anything.
- **Sword trails from packs that take `User.Start` / `User.End` vectors** (set by the pack's own Blueprint each tick)
  draw a ribbon from the world origin when spawned plainly on a socket — a giant dark sheet. `GetSystemSummary` lists
  such `User.*` vector parameters; for a trail that follows a socket use a plain ribbon emitter (spawn rate, sim-position
  initialisation, width scaled by `1 - NormalizedAge`).
- **A pooled ribbon component's first frame can sit at its previous location**, drawing one long streak from there to
  the socket. A loop delay of ~0.05 s on the emitter (EmitterState `UseLoopDelay`, `Loop Delay`) lets the attachment
  settle before the first particle.
- **Probing runtime-spawned components from Python**: `actor.get_components_by_class(StaticMeshComponent)` did not
  return a component created at runtime with `NewObject` + `RegisterComponent`; iterate
  `unreal.ObjectIterator(unreal.StaticMeshComponent)` and filter by `c.get_world() == world`. Read transforms with
  `c.get_editor_property('relative_scale3d')` — `get_relative_scale3d` does not exist in Python. Destroyed components stay
  visible to the iterator until GC, so a "duplicate" right after a respawn is usually the dead one.
