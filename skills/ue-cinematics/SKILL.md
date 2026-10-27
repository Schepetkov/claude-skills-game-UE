---
name: ue-cinematics
description: Unreal Engine 5.8 cinematics and in-engine dialogue direction — breaking a scene into beats, blocking actors on marks, camera coverage (axis/180, OTS, singles, reverse pairs), lenses and depth of field on CineCamera, cutting dialogue, creature/boss reveals, choosing and editing animation (FK Control Rig additive layers, bake to AnimSequence), Level Sequences built over MCP, runtime playback from C++, and reviewing shots by frames and numbers. Use when staging a cutscene or dialogue scene, placing or cutting cameras, fixing "flat"/"amateur" cinematics, picking or tweaking animation for a scene, or driving Sequencer from an agent.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---

# UE 5.8 Cinematics — direction, cameras, animation

The agent works as director, layout artist and editor at once: it reads the scene, decides what the
audience must feel at every beat, blocks the actors, places cameras, cuts, casts animation, builds it in
Sequencer over MCP and reviews the result frame by frame.

Two references carry the detail — load the one you need:
- [references/craft.md](references/craft.md) — sourced, numbered craft rules (axis, eyelines, lenses, cutting,
  lighting, proxemics, reveal template, per-shot checklist). Every rule has a source URL or a `[synth]` tag.
- [references/engine-api.md](references/engine-api.md) — engine-verified API: all 339 animation MCP tools, Python
  library names, runtime C++, CineCamera defaults, frame rendering. Items not provable from source are marked UNVERIFIED.

## Ground truth rule (read first)

Grep the engine source before quoting an API. The Sequencer Python surface moved a lot between 5.4 and 5.8
(custom bindings, deprecated `SequencePlayer`, `AddSpawnableFrom*` moved to a subsystem). See
[Finding the engine source](#finding-the-engine-source).

```bash
grep -n "static.*(" Engine/Plugins/Animation/ControlRig/Source/ControlRigEditor/Public/ControlRigSequencerEditorLibrary.h
grep -rn "tool_call" Engine/Plugins/Experimental/Toolsets/AnimationAssistantToolset/Content/Python/animation_toolset/toolsets/ | wc -l
sed -n '3600,3640p' Engine/Config/BaseEngine.ini     # CineCamera filmback/lens presets and defaults
```

## Be honest about quality before starting

| Work | What an agent does well | Where it is weak |
|---|---|---|
| Blocking, marks, facing, spacing | geometry — checkable by numbers | — |
| Camera placement, lens, DOF, coverage | derivable from shot size and axis; checkable in frames | taste on the edge cases — show frames |
| Cutting dialogue | line events give cut points; rules are explicit | comic/musical timing |
| Editing an existing clip (pose fix, retime, hold, mirror, aim, foot plant) | additive FK layer, measurable | — |
| Hand-keyed new body performance from zero | — | **poor**: no weight, overlap, timing. Do not promise it |
| Faces / lip sync | use the project's face pipeline | not by hand keys |

So the animation rule is a **casting ladder**: (1) an existing clip that already fits → (2) the closest clip
from any pack, retargeted, adjusted by an additive FK layer → (3) two clips blended or spliced → (4) mocap
(suit or video-to-mocap) → (5) hand keys only for small things (head turn, hand raise, hold pose). Tell the
user which rung each beat lands on.

## Decision 1: how the scene is delivered

| Delivery | Use for | Notes |
|---|---|---|
| **Level Sequence** (authored cameras, baked animation) | key moments: arrivals, deaths, reveals, set pieces, anything with camera moves | full control; costs authoring per scene; drive with tag bindings at runtime |
| **Runtime dialogue camera system** (rule-driven cuts from line events) | the bulk of conversations | Witcher 3 / BioWare model: generator does the first pass from line timing, a human polishes the important ones. Rules from craft.md §3 go into the system, not into each scene |
| **One-shot follow camera** (no cuts) | a whole-game style choice | needs blocking that brings actors to the camera; not a fix for one scene |

Hybrid is normal: rule-driven dialogue, with a Level Sequence for the arrival, matching its last frame to the
first dialogue shot so the hand-off is invisible.

## The director workflow (do it in this order)

1. **Read the scene.** Who wants what from whom; who holds power and when it shifts; the one feeling the
   player must leave with. Write it as one sentence per beat.
2. **Beats.** Split at every change of intent, power or information (a new line by a new speaker is not
   automatically a beat). Each beat gets: purpose, dominant character, shot-size target on the ladder
   (WS → MS → MCU → CU — intensity grows down the ladder; save the CU for the peak).
3. **Blocking.** Place marks in the real level, never an empty test map. Spacing by relationship
   (hostile 2.5–4 m, neutral 1.4–2 m, intimate 0.9–1.2 m; a creature twice human height needs twice the
   distance). Cheat bodies 10–30° open to camera. Three or more: a triangle open toward the master camera.
   Clear occluders between camera positions and faces; move set dressing, not the axis.
4. **Axis.** Draw the line between the two main talkers' heads. Pick the side (the side with the better
   background and the key light behind the listener). Every camera of the exchange stays on it. When the
   active pair changes, show the change (a two-shot or a head turn cut on the action) before using the new axis.
5. **Coverage plan.** Minimum per pairing: master + OTS pair + MCU pair; CU pair for the peak; inserts for
   objects the lines name; reaction singles for every line that lands. Matched pairs share lens, distance and
   height (kit table below).
6. **Cut list.** Cut points come from line events (start, end, pauses, emotion change), never a fixed timer.
   J/L overlaps ~0.5 s. Shots 1–6 s, at most one cut inside a line, nothing under 1 s except inserts/impacts.
   A new shot of the same subject needs ≥30° of angle change or ≥20 mm of lens change plus a size step.
   Re-establish after any blocking change or ~30 s of singles.
7. **Cast animation** per beat by the ladder above. List: beat → clip → source pack → change needed.
8. **Build** (recipes below), **review frames**, run the checklist, fix, repeat. Show the user a contact sheet
   per pass, not a description.

## Units — the trap that breaks every lens number

The default CineCamera filmback is **"16:9 Digital Film" (23.76 × 13.365 mm), 35 mm at f/2.8**, not full frame.
Film literature (and craft.md) quotes full-frame mm. Either set the filmback to **"16:9 DSLR" (36 × 20.25)** on
every camera (`SetFilmbackPresetByName`), or divide full-frame mm by **1.515**. State the convention in the
sequence.

Default focus is **Manual at 100 000 cm** — DOF is effectively off until you set a distance or Tracking.

Place a camera from the wanted shot size, not by eye: frame height at the subject `H = d × 20.25 / f`
(16:9 DSLR, `d` and `H` in the same unit). 50 mm at 150 cm frames 61 cm = MCU.

## Dialogue camera kit (full-frame mm on 16:9 DSLR)

| Shot | Lens | Frame height | Distance | Height | Off axis | Use |
|---|---|---|---|---|---|---|
| Master / establishing | 18–28 | 3–6 m | 5–10 m | eye or +1–3 m | 80–100° (apex) | first shot; re-establish |
| Two-shot | 28–35 | 1.0–1.4 m | 2.5–3.5 m | eye | 60–90° | neutral exchange, power turn, 3-person reset |
| OTS | 50–85 | 0.6–0.8 m | 1.6–3.0 m | far actor's eye | 15–30° | workhorse; shoulder ≤ 1/3 of frame, soft |
| Clean single MCU | 50–65 | 0.5–0.6 m | 1.3–1.9 m | eye ±25–40 cm | 20–35° | most lines; reactions |
| CU | 75–100 | 0.30–0.38 m | 1.2–1.9 m | eye | 25–40° | the scene's strongest beats |
| Low-angle threat | 24–35 | FS–MS | 2–5 m | 0.3–1.0 m off ground, tilt up 10–25° | 30–60° | dominant party, creature reveal |
| High-angle exposure | 35–50 | MS–FS | 2–4 m | 0.5–1.5 m above eye, tilt down 10–20° | 30–60° | the diminished party |

f-stop: f/2–2.8 singles/OTS/CU, f/4 two-shots (both faces sharp), f/5.6–8 wides. Focus on the near eye.
Eyes on the upper third (30–36 % from top), look room on the facing side, speaker ~1/3 across the frame.
Power: the dominant one shot from below, the other from slightly above, mirrored, only while it holds.
All numbers are starting points — the frame decides. Full rule set and sources: craft.md §3–§6.

## Creature / boss arrival template

Sound first (≥1 s before the first creature frame) → witness reaction (eyes up toward the source) → partial
reveal (silhouette, a claw, an eye; 1–3 short shots) → **full reveal**: the longest shot, low angle 24–35 mm
with a human in the foreground for scale, or a tilt up the body ending on the face; the loudest hit lands on
this cut → hold on the witness again (same lens and side as before) → two-shot/wide on the axis the dialogue
will use. Never reveal in the same frame as the first sound; never the full body in the first creature shot.
Detail and timings: craft.md §7.

## Building it in Sequencer over MCP

Toolsets (in `AllToolsets` via `AnimationAssistantToolset`): `SequencerTools`, `SequencerKeyframingTools`,
`SequencerControlRigTools`, `ControlRigTools`, `SequencerOutlinerTools`, `SequencerImportExportTools`,
`SequencerCustomBindingTools`, `SequencerConditionTools`. `SequencerAnimMixerToolset` is **not** in
AllToolsets and needs the Experimental `MovieSceneAnimMixer` plugin.

Gotchas that cost hours (all verified in source — engine-api.md §1.10):
- **All frames are display-rate frames.** Never call `set_tick_resolution` on a sequence with keys.
- **Open the sequence first** (`open_sequence`) — playback, camera, selection and layer tools act on the focused one.
- **One CineCameraActor per shot**, each with its own camera-cut section. Teleporting one camera between shots
  without a cut smears the frame (temporal history is only reset on a cut).
- `create_camera` spawns at the current viewport pose, **locks the viewport to it**, and auto-creates a cut
  section only for the first camera. Add later cuts by hand; eject the pilot lock before deleting a camera.
- `add_actors` already adds a transform track; a second transform track cannot be keyed — find, don't add.
- **`bake_to_control_rig` is destructive**: deletes every Control Rig track on the binding and disables the
  animation track. It replaces the clip with editable keys; it is not a layer.
- **Additive editing of a clip** = native FK Control Rig in layered mode. The MCP track tool only takes a
  Control Rig *asset*, so call the library directly:
  `unreal.ControlRigSequencerLibrary.find_or_create_control_rig_track(world, seq, unreal.FKControlRig, binding, is_layered_control_rig=True)`.
  The value/key tools then find it with `control_rig_asset_path="FKControlRig"`.
- **Bake** the result with `SequencerTools.export_anim_sequence` (new AnimSequence on the same skeleton);
  for spawnables that exist only in the open Sequencer use `ControlRigSequencerLibrary.export_anim_sequence_from_sequencer`.
- **MetaHuman:** never switch the body mesh to `ANIMATION_SINGLE_NODE` to hold a pose — the face follows the body only on
  the normal anim path and the head detaches. To review a pose, place a `LevelSequenceActor` with
  `playback_settings.auto_play=True` and a low `play_rate` (auto-play lives in `playback_settings`, not on the actor).
- A clip pose does not evaluate in the **editor** world (components do not tick) — measure bones in PIE; and use
  `set_animation_mode()`, not `set_editor_property("animation_mode")`. Bone world positions of a clip:
  `AnimationLibrary.find_bone_path_to_root` + `get_bone_pose_for_time` along the chain.
- No paired "offer/take hand" clips exist in Paragon packs; build from single clips + a layered FK rig, solving the arm
  numerically (coordinate descent on upperarm/lowerarm controls toward the target hand).
- Tool errors do not raise: a failed tool returns the type default (`False`, `None`). Check every return.
- **`set_camera_cut_binding` fails in 5.8.2** (`unreal.Guid(str)` takes no arguments). Set the section property
  instead: `ObjectTools.set_properties(section, {"CameraBindingID": {"guid": "<binding guid>", "sequenceId": 0,
  "resolveParentIndex": -1}})`, then read it back.
- **A spawnable CineCamera already owns three keyed tracks** on its component binding (focal length, aperture,
  manual focus distance). Edit those (remove the key, set the default); adding your own duplicates makes Sequencer
  average them. `set_properties` on the spawned instance keeps `Filmback` but loses `CurrentFocalLength` on respawn.
- Limit each camera's **spawn track section to its own shot**, so the other cameras' editor meshes never appear in
  review frames.
- `CaptureViewport` ignores Game View and needs `captureTransform`; pass the shot camera's transform — the FOV comes
  from the camera the viewport is locked to. Editor sprites still show; good enough for layout, not for final look.
- **Editor-crashing calls (assert, not exception):** `unreal.SequencerTools.get_bound_objects(..., SequencerScriptingRange())`
  with the default open range; `Exporter.run_asset_export_task` with a `None` object. Find spawned actors in the world
  instead, and guard every export. Save the sequence after each step — a crash takes all unsaved tracks.
- **Niagara in a sequence:** spawn a temp `NiagaraActor` from the system asset, `add_spawnable_from_instance`, destroy
  the temp, `seq.add_possessable(spawned.niagara_component)` for the child binding, add `MovieSceneNiagaraSystemTrack`
  and set the section to `NiagaraAgeUpdateMode.DESIRED_AGE`, so frame-by-frame renders do not run the effect fast.
- **Retargeting onto a non-standard skeleton** (HumanIK `Character1_*`, Mixamo, custom): `apply_auto_generated_retarget_definition`
  returns False — add the chains by hand with the *same chain names* as the source rig, then `AutoMapChains(EXACT)`,
  `AutoAlignAllBones(TARGET)` and `IKRetargetBatchOperation.run_batch_retarget` (`DuplicateAndRetarget` is deprecated in 5.8).

## Final render without Movie Render Queue

MRQ is off by default, and enabling it by command line fails if its binaries are older than the editor. Without it:
lock the viewport to the camera cut, then drive a Slate post-tick state machine — per frame: `set_global_position`,
`force_update`, wait 2–3 ticks, `AutomationLibrary.take_high_res_screenshot(w, h, file, None, False, False, LOW, '', 0.0,
True)` (last arg = force Game View, so no editor sprites), wait for the task, next frame. ~0.5 s/frame warm at 1080p.
Export VO with `SoundExporterWAV`, mix by line start times in ffmpeg, mux with the PNG sequence. Runtime-generated
decor (PCG "generate on demand") is absent in the editor world: call `PCGComponent.generate(True)` before rendering and
never save the map afterwards.

Recipes (skeletal clip + FK additive layer + bake; camera + cut + lens/focus keys): engine-api.md §1.11–1.12.

## Playing it at runtime (C++)

Modules: `LevelSequence`, `MovieScene`, `MovieSceneTracks`, `CinematicCamera`.
`ULevelSequencePlayer::CreateLevelSequencePlayer(World, Seq, Settings, OutActor)`; bind runtime actors with
`SetBindingByTag` **before** `Play()`; keep the player in a `UPROPERTY`. `ALevelSequenceActor::SequencePlayer`
is deprecated since 5.4 — `GetSequencePlayer()`. There is no `bRestoreState`: use
`FinishCompletionStateOverride`. `OnFinished` fires only on a natural end (`Stop()` fires `OnStop`). Camera cuts
are evaluated per client and do not replicate. Detail: engine-api.md §2.

## Reviewing — frames and numbers, not adjectives

- **Frames without PIE:** `set_lock_camera_cut_to_viewport(True)`, set the playhead, `force_update()`, take a
  viewport screenshot on a later tick; tile frames into one contact sheet per pass. Movie Render Queue is off
  by default and its legacy executor starts PIE — avoid it in a shared editor.
- **Numbers per shot** (log them, compare to the kit): camera side of the axis
  (sign of `cross(B−A, Cam−A).Z` constant across the exchange), angle and lens delta to the previous shot of
  the same subject (≥30° or ≥20 mm), frame height at the subject from the formula, eye height in frame,
  an unobstructed line trace from camera to each framed head.
- Then the per-shot checklist (craft.md §8). Show the contact sheet to the user and name what changed.

## Finding the engine source

| Engine type | Where the source lives |
|---|---|
| **Source build** | The `EngineAssociation` GUID in the `.uproject` maps to a path under `HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds` (Windows) or `~/.config/Epic/UnrealEngine/Install.ini` (Linux). |
| **Launcher install** | `EngineAssociation` is a version string (`"5.8"`). Path under `HKLM:\SOFTWARE\EpicGames\Unreal Engine\<version>` → `InstalledDirectory`. Plugin Python (the MCP toolsets) ships with it; C++ private sources do not. |

## Related

- **`ue-mcp`** — connecting to the editor; the toolsets this skill drives.
- **`ue-lighting`** — per-shot cheat lights, exposure lock, Lumen in close-ups.
- **`ue-performance`** — cinematic scalability and shot cost; measure, don't guess.
- **`ue-assets`** — retargeting pack animation, skeleton compatibility.

## Field notes from other projects

`field-notes/` next to this file (when present) holds lessons from other agents' retros, one per file. Before
debugging a symptom, `grep -ril "<symptom words>" field-notes/`. `status: observed` means seen in practice but not
yet checked against source — verify before relying on it; once checked, promote it into the tables above.
