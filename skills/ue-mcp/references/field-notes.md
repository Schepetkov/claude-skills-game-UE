# Unreal MCP — field notes (UE 5.8.x, verified in a live project)

Things the tool schemas do not tell you. Each one cost at least one lost cycle in production use.

## Calling tools

- `call_tool` takes the full dotted `toolset_name` (from `list_toolsets`) and the `tool_name` **without** the prefix.
- Object refs are full object paths (`/Game/X/A.A`, `/Game/Map.Map:PersistentLevel.Actor_0`); a package path is rejected.
- `ObjectTools.set_properties`: `values` is a **JSON string**, not an object (an object silently returns False). Keys are
  lowerCamelCase (`list_properties` gives the schema). Several keys may apply only partly and still return true — read back.
  `FLinearColor` = `{"r","g","b","a"}`; enums by name; a `SizeBox` override needs `bOverride_WidthOverride: true` too.
- `get/set_properties` on a **Blueprint asset path operates on its CDO** (`Default__X_C`); the `UBlueprint` object itself
  (bindings, animations) is not reachable from shipped toolsets — write a project tool.
- A `TMap` in a DataAsset is written **whole**: a partial map does not add keys.
- Over a raw JSON-RPC client every parameter is required, defaults included (`CaptureViewport` wants `captureTransform`,
  all six `annotations` fields and `bShowUI`). Session id = `Mcp-Session-Id` header of `initialize`.
- Tool names and args: grep `def ` in `Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/*.py`.
- Python toolsets (`scene`, `asset`, `actor`, `object`, `material`…) appear only with `PythonScriptPlugin` enabled.
  Transforms there are `location` / `rotation{pitch,yaw,roll}` / `scale`; a quaternion is accepted and ignored;
  `set_actor_transform` with one field resets the others.

## Saving

- During PIE, `AssetTools.save_assets` / `is_dirty` answer **"Asset does not exist"** — StopPIE first.
- An explicit path of a new or freshly moved asset may also answer "does not exist"; `save_assets []` saves everything
  dirty — including a dirty map (check `git status` after).
- **Git LFS `lockable` files are read-only after commit**: `save_assets` silently "succeeds" and writes nothing.
  `git lfs lock` (or `chmod u+w`) first, then verify the bytes on disk (timestamp, a string you wrote).
- In a shared editor, save right after a recompile — a peer closing the editor takes in-memory edits with it.
- `AssetTools.delete` on a loaded asset drops it from the registry but the file stays locked on disk until the editor exits.
- `TextureTools.import_file` onto an existing name answers "already exists" but **does** reimport the file; the live
  texture shows old pixels until an editor restart. `StaticMeshTools.import_file` onto an existing name returns the old asset.
- `AssetTools.duplicate` returns False for engine materials (and sometimes your own): use a commandlet
  `EditorAssetLibrary.duplicate_asset`, or a parameter with a neutral default in the shared material.
- Creating an asset during PIE pops a modal "Overwrite Existing Object" and freezes the game thread.

## Materials

- `MaterialTools.delete_expression` asserts `!IsRooted()` and kills the editor — disconnect, never delete nodes.
- Custom node `Inputs`: resize first with N copies of the default element (as `get_properties` returns it), then a
  second call with the real names. `auto` is a reserved word as an input name (material falls back to default, black).
- Run `recompile` as its own call: a Custom-node recompile can pass the client timeout and orphan a half-applied script.
- New material for skeletal meshes / Niagara: set `bUsedWithSkeletalMesh` / `bUsedWithNiagara*` at creation, otherwise
  "missing usage flag — Default Material will be used in game".

## Niagara toolset

- Every `NiagaraToolset_System.*` call builds a system view model and never frees it (~50 MB per call). Save after
  each emitter, restart the editor between batches of 2–3 systems, watch the process working set.
- The Cascade converter can leave every emitter disabled (`bIsEnabled: false`) — check `GetEmitterSummary` right away.
- `AssetTools.get_dependencies` takes `asset_path` (with `path` the output is empty and looks "clean").
- A component that cached the system by id keeps playing the old one after you swap it in data — restart PIE.
- New system from an existing one: `CreateNiagaraSystem {templateSystem}` copies it (the original stays untouched).
  Script names in stack refs are `ENiagaraScriptUsage` values: `ParticleSpawnScript`, `ParticleUpdateScript`,
  `EmitterUpdateScript`; a dynamic input's child is `inputNameStack: ["Sprite Size", "Value", "Minimum"]`.
  `GetDynamicInputChain` shows the real numbers hidden behind RandomRange / Multiply inputs.
- A GPU emitter with `CalculateBoundsMode: Dynamic` has no real bounds; for a small ambient effect set `CPUSim` +
  `Fixed` bounds. Renderer `MinCameraDistance` (often 300 in templates) culls everything closer than 3 m.
- **Niagara does not simulate in the editor world** (game time stays 0, a capture there shows nothing or frozen spawn
  positions). Judge particles only in PIE.
- Material for Niagara sprites: `ParticleColor`'s main output is float3 — alpha comes from its `A` pin. `PC.a` in a
  Custom node fails to compile and the renderer silently uses the default lit material (black squares in an unlit
  scene). After a material edit grep the log for `Failed to compile Material`.

## Editor process and capture

- `Start-Process UnrealEditor.exe` opens the window minimized or larger than the work area: `ShowWindow(h, 3)` (maximize)
  and compare `GetWindowRect` with the screen. Before any Slate screenshot check `IsIconic` — a capture of a minimized
  window returned an empty PNG, the second one crashed the render thread (`RHIReadSurfaceData`).
- `CaptureViewport` always renders the **editor** world (no PIE actors, no Niagara). `CaptureEditorImage` caps at 1280 px.
  Full resolution: `SlateInspectorToolset.Screenshot {ref:""}` (or `Observe` + `{ref:"w1"}`); the base64 is inside
  `result.content[].text` as escaped JSON. A Message Log tab or Content Drawer over the viewport ends up in the frame —
  close it via `SlateInspectorToolset.Windows close` / click the level tab.
- `SlateInspectorToolset.Click` by ref works only in the first PIE session of an editor run; drive UI by keyboard focus
  (`PressKey Up/Enter`) instead. `Hover` keeps working.
- After a crash the next launch blocks on an invisible "restore packages" dialog: move `Saved/Autosaves` aside.
- A modal "Save Content" / "Check Out" dialog on `CloseMainWindow` hangs MCP for everyone; save first, then close.
- Port 8000 may belong to another project's editor: check the process **command line** before trusting it. Second editor:
  `-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:ServerPortNumber=8001`.
  After an editor exits, 8000 frees with a delay — "HttpListener unable to bind" means wait for it.
- Any running editor of the same engine holds the Live Coding mutex: `Build.bat … -NoHotReloadFromIDE`.
- **Live Coding:** touching any `.h` (UCLASS or not) → full build with the editor closed. Live Coding patches every source
  newer than the DLL, including other sessions' headers; it keeps function-local statics of the old module; static
  `FAutoConsoleCommand`s in a patched `.cpp` can re-register onto the wrong lambdas. Patches do not survive a restart.
- After an editor restart Claude Code's MCP client stays "session expired" until `/mcp` → Reconnect. A raw JSON-RPC
  client technically works, but it bypasses the editor-lock hooks (they watch MCP tool calls) and the harness may
  deny it as a bypass — ask the human for `/mcp` instead of working around it.
- **Preview video of a game world (PIE):** put a dormant `SceneCapture2D` (tagged) into the level beforehand — Python
  cannot spawn into the PIE world (`GameplayStatics` has no deferred spawn there), but finds the PIE copy with
  `get_all_actors_with_tag`. Drive it from a `register_slate_post_tick_callback`, timestamp frames with the game
  time and resample to a fixed fps. A background (unfocused) editor throttles PIE to ~3 fps;
  `bThrottleCPUWhenNotForeground` is not reachable from Python — expect choppy previews or ask for focus.
- Saving an asset while PIE runs reports success but writes nothing (`The Editor is currently in a play mode`) — save
  after `StopPIE` and check the file on disk.

## Console and Python

- No shipped tool executes console commands. Pattern: a project C++ tool (e.g. `RunConsole(Command)`), which also runs
  Python in the live editor via `py "<file>" <args>`. Exec functions of a PlayerController do not arrive through it —
  call `unreal.SystemLibrary.execute_console_command(world, cmd, pc)` from Python.
- `slomo` through such a tool is unknown in PIE; use `GameplayStatics.set_global_time_dilation` from Python.
- Debug cvars live across PIE sessions until the editor closes — reset them in the same command.
- Python gotchas: `duplicate_asset` a map + `load_level` = fatal "World Memory Leaks" (use
  `LevelEditorSubsystem.new_level_from_template`); `unreal.Rotator(a,b,c)` is (roll, pitch, yaw); positional
  `unreal.Color(...)` is not RGB — use keywords; unary minus on `unreal.Vector` mutates in place; `set_editor_property(None)`
  does not clear a `TSoftClassPtr`; PowerShell `Set-Content -Encoding utf8` writes a BOM → SyntaxError.
- A live CDO write reaches the next PIE only for `Config` properties; header defaults need a rebuild.
  `UUserWidget::TickFrequency` has no C++ setter — set it on the WBP CDO.

## Shots without the editor

- `-game -csvCaptureFrames=N -ExitAfterCsvProfiling "-csvExecCmds=10:cmd a,450:HighResShot 1"`: commands by frame
  number, comma-separated, arguments with spaces in quotes (`+` is sent literally). `-ExecCmds` fire on frame 1, before
  Nanite/GI settle. `HighResShot` has no UI — `Screenshot showui <name>`. A window capture uses `PrintWindow`, never a
  screen grab (other people's windows).
- Shots in another project's editor: `-ExecCmds="py <script>"` (not `-ExecutePythonScript`, it quits) with
  `bThrottleCPUWhenNotForeground=False`; step a `register_slate_post_tick_callback` state machine only when
  `get_frame_count()` moved.
- Asset thumbnails without an engine: the package embeds a PNG/JPEG (`\x89PNG…IEND`, `FFD8…FFD9` from the end), BGR.

## Building a WBP over UMGToolSet

- `UMGToolSet.CreateWidgetBlueprint {folderPath, assetName, parentClass:{refPath:"/Script/<Module>.<Class>"}}` gives an
  **empty tree**: add the root (CanvasPanel/Overlay) with `AddWidget` without `parentWidget`; `BindWidget` fields of the
  C++ parent show up in `GetWidgets` as `bInherited` with `widget: "None"` until added.
- `AddWidget {widgetBlueprint, widgetClass:{refPath}, widgetDisplayName, parentWidget?, childIndex}` returns refPaths of
  widget, slot and parent (the root's slot/parent are the string `"None"`). Canvas slots take
  `LayoutData {offsets, anchors, alignment}` + `bAutoSize` as one JSON. A Button holds one child.
- Brush JSON: `{"drawAs":"RoundedBox","tintColor":{...},"outlineSettings":{cornerRadii,color,width,roundingType}}`;
  font: `{"fontObject":{"refPath":"…Font.Font"},"typefaceFontName":"Default","size":N}`.
- `CompileWidgetBlueprint`, then `save_assets []`. Build the C++ parent first: a rebuilt WBP over an unbuilt parent plus
  someone's `StartPIE` pops a modal "Blueprint Asset Compilation Error" that hangs the game thread and MCP for everyone.
- `DataTableTools.set_rows`: a nested struct is written whole — omitted fields reset to defaults (FTextBlockStyle becomes magenta).
