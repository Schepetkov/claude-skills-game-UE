# Engine API reference: Sequencer, Control Rig, CineCamera, runtime playback (UE 5.8.2 source)

All paths are relative to the engine root `Engine/` (see "Finding the engine source" in SKILL.md).
Everything here was read from source on 2026-10-23. Items marked **UNVERIFIED** were not proven from source.
Abbreviations: `AAT=Plugins/Experimental/Toolsets/AnimationAssistantToolset/Content/Python/animation_toolset`.

---

## 1. MCP animation toolsets

### 1.0 Plugins, enabling, AllToolsets

- `AnimationAssistantToolset` (Experimental, EditorOnly, has C++ module + Python). Depends on plugins
  `ControlRig`, `ToolsetRegistry`, `LevelSequenceEditor`, `SequencerScripting`.
  Evidence: `Plugins/Experimental/Toolsets/AnimationAssistantToolset/AnimationAssistantToolset.uplugin`.
- It registers 8 toolset classes (Python `unreal.ToolsetDefinition` subclasses):
  `ControlRigTools, SequencerTools, SequencerKeyframingTools, SequencerControlRigTools,
  SequencerOutlinerTools, SequencerConditionTools, SequencerCustomBindingTools, SequencerImportExportTools`.
  Evidence: `$AAT/toolsets/__init__.py` (`Registration([...])`), `$AAT/../init_unreal.py` calls `toolsets._registration.register()`.
- `SequencerAnimMixerToolset` (Experimental, `EnabledByDefault: false`, Python-only, no Modules) depends on
  `ToolsetRegistry` + `MovieSceneAnimMixer`. Registers `SequencerAnimMixerTools`.
  Evidence: `Plugins/Experimental/Toolsets/SequencerAnimMixerToolset/SequencerAnimMixerToolset.uplugin`,
  `.../Content/Python/sequencer_animmixer_toolset/toolsets/mixer.py` docstring: "separate plugin ... because the
  MovieSceneAnimMixer plugin is not enabled by default".
- `MovieSceneAnimMixer` ("Sequencer Anim Mixer") is Experimental, `EnabledByDefault: false`.
  Evidence: `Plugins/Experimental/MovieSceneAnimMixer/MovieSceneAnimMixer.uplugin`.
- **AllToolsets includes AnimationAssistantToolset but NOT SequencerAnimMixerToolset** (must be enabled by hand,
  and it drags in MovieSceneAnimMixer).
  Proof: `grep -n "AnimationAssistantToolset\|SequencerAnimMixer" Plugins/Experimental/Toolsets/AllToolsets/AllToolsets.uplugin`
  -> only `AnimationAssistantToolset` matches.
- Tools are static UFunctions with meta `AICallable`; Python exceptions are converted to script errors and the tool
  returns the type's default value (e.g. `False`, `None`) instead of raising.
  Evidence: `Plugins/Experimental/ToolsetRegistry/Content/Python/toolset_registry/tool_call_impl.py` (`def tool_call`,
  `unreal.SystemLibrary.raise_script_error`, `_get_default_value_for_type`).
- UObject params over the wire are `{"refPath": "<object path name>"}`.
  Evidence: `.../toolset_registry/tests/test_execute_tool.py:104`. Struct params (e.g. `SequencerBindingProxy`
  = `FMovieSceneBindingProxy{BindingID: FGuid, Sequence: UMovieSceneSequence*}`, `Source/Runtime/MovieScene/Public/MovieSceneBindingProxy.h:52-56`)
  are presumably passed as JSON objects with those fields — **UNVERIFIED** exact JSON shape; check with `describe_toolset`.
- Automation tests are registered as `AI.Toolsets.AnimationToolset.{ControlRig,Sequencer,SequencerKeyframing,
  SequencerControlRig,SequencerOutliner,SequencerConditions,SequencerCustomBindings,SequencerImportExport}` and
  `AI.Toolsets.SequencerAnimMixerToolset`. Evidence: both `init_unreal.py` files. Tests need a mannequin mesh
  (`/Game/Animation/ControlRig/Metahuman/SK_Mannequin_MH`, `/Game/Characters/UEFN_Mannequin/...`, `/MoverExamples/...`)
  and skip otherwise (`$AAT/tests/_sequencer_test_base.py`).

Tool listing below was extracted with an AST script over each file (functions decorated `@toolset_registry.tool_call`):
`python -I extract_tools.py $AAT/toolsets/*.py .../mixer.py`.

### 1.1 SequencerTools (`$AAT/toolsets/sequencer.py`, 140 tools)
Lifecycle: `create_level_sequence(package_path, asset_name)` (DELETES an existing asset at that path to avoid a modal),
`get_current_sequence()`, `get_focused_sequence()` (sub-sequence aware), `open_sequence(sequence)`, `close_sequence()`, `refresh_sequence()`.
Playback: `play`, `pause`, `is_playing`, `set_playhead_frame(frame)`, `get_playhead_frame`, `play_to(frame)`,
`set_playback_speed(speed)`, `get_playback_speed`, `set_loop_mode(loop)`, `get_loop_mode`, `force_evaluate`.
Sequence props: `get/set_display_rate(sequence, numerator, denominator=1)`, `get/set_playback_range(sequence, start_frame, end_frame)`,
`get/set_view_range(seq, start_seconds, end_seconds)`, `get/set_work_range(...seconds)`, `get/set_tick_resolution(seq, num, den=1)`,
`get/set_evaluation_type(seq, eval_type)`, `get/set_clock_source(seq, clock_source)`, `is_playback_range_locked`, `set_playback_range_locked`,
marked frames: `add_marked_frame`, `get_marked_frames`, `delete_marked_frame(index)`, `delete_all_marked_frames`, `find_marked_frame_by_label`.
Bindings: `add_actors(actors)`, `add_actors_by_name(actor_names)`, `add_spawnable_from_instance(sequence, obj)`,
`add_spawnable_from_class(sequence, actor_class_path)` (e.g. `/Script/CinematicCamera.CineCameraActor`), `create_camera(spawnable=True)`,
`get_bindings`, `find_binding_by_name`, `get/set_binding_name`, `remove_binding`, `get_bound_objects`, `get_child_possessables`,
`get_binding_id(sequence, binding)`, `add_actors_to_binding`, `replace_binding_with_actors`, `remove_actors_from_binding`,
`remove_all_bindings`, `remove_invalid_bindings`, `rebind_component(component_bindings, component_name)`, `fix_actor_references`,
tags: `find_binding_by_tag`, `find_bindings_by_tag`, `get_all_binding_tags`, `get_binding_tags`, `tag_binding(binding, tag_name)`, `untag_binding`, `remove_binding_tag`.
Tracks: `add_track_to_binding(binding, track_type: Class)`, `add_track_to_sequence(sequence, track_type)` (master tracks, e.g. camera cut),
`get_tracks_on_binding`, `get_tracks_on_sequence`, `find_tracks_by_type`, `remove_track`, `remove_track_from_sequence`,
`get/set_track_display_name`, `set_property_name_and_path(track, display_name, property_path)`, `set_byte_track_enum`.
Sections: `add_section(track)`, `get_sections`, `remove_section`, `set/get_section_range(section, start_frame, end_frame)`,
`has_section_start_frame/end_frame`, `set_section_start_bounded/end_bounded`, `set_section_ease_in/out(section, duration)`,
`get_section_ease_in/out`, `set/get_section_blend_type` ('Absolute'|'Additive'|'Relative'|'Override'),
`set/get_section_completion_mode`, `get_section_properties`, `set/get_section_pre_roll_frames`, `set/get_section_post_roll_frames`,
`get_section_to_key(track)`, `set_section_animation(section: MovieSceneSkeletalAnimationSection, anim_sequence_path)`,
`set_camera_cut_binding(section: MovieSceneCameraCutSection, camera_binding_id: str)`.
Events: `add_event_trigger_section(track)`, `add_event_repeater_section(track)`.
Selection/UI: `get_selected_tracks/sections/bindings/folders`, `select_tracks/sections/bindings/folders`, `empty_selection`,
`get/set_selection_range`, `set_camera_lock(lock)`, `is_camera_cut_locked`, track filters (`get_track_filter_names`,
`is_track_filter_active`, `set_track_filter_active`), lock (`is_sequence_locked`, `set_sequence_locked`, `get_sequence_lock_state`).
Folders: `add_root_folder`, `get_root_folders`, `remove_root_folder`, `add_track_to_folder`, `add_binding_to_folder`, `get_folder_contents`.
Sub-sequences: `focus_sub_sequence(sub_section)`, `focus_parent_sequence`, `get_sub_sequence_hierarchy`.
Clipboard: `copy/paste_bindings`, `copy/paste_tracks`, `copy/paste_sections`, `copy/paste_folders` (paste takes a token from copy).
Bake: `bake_transform(bindings)` -> `LevelSequenceEditorSubsystem.bake_transform_with_settings(bindings, BakingAnimationKeySettings())`.

### 1.2 SequencerKeyframingTools (`$AAT/toolsets/keyframing.py`, 22 tools)
`get_channel_names(section)`, `add_key_float(section, channel_name, frame, value, interpolation="")`
('' = SmartAuto; 'auto','user','linear','constant','break'; 'cubic' is an alias for AUTO), `add_key_bool`, `add_key_integer`,
`add_key_string`, `get_keys(section, channel_name)` (JSON), `get_keys_by_index`, `remove_key_at_frame`, `set/get_default_value`,
`get_selected_channels`, `select_channels`, `open/close_curve_editor`, `is_curve_editor_open`, `get_selected_key_channels`,
`get_curve_editor_selected_keys`, `curve_editor_select_keys`, `curve_editor_empty_selection`, `show_curve`, `is_curve_shown`,
`bake_channel_keys(section, channel_name, start_frame, end_frame)`. Channel names look like `'Location.X'` (docstring).

### 1.3 ControlRigTools (`$AAT/toolsets/controlrig.py`, 44 tools) — authoring Control Rig ASSETS (graph, hierarchy)
`create(path)`, `import_bones_from_asset(control_rig, skeletal_mesh)`, hierarchy: `get_elements`, `get_all_bones/nulls/controls`,
`add_element`, `add_bone`, `add_null`, `add_control(control_rig, name, parent=None, settings=None)`,
`get/set_global_transform`, `get/set_local_transform`, `get_parent`, `get_children`;
graphs: `get_graph`, `list_graphs`, `add_graph`, `get_forward_solve_graph`, `get_backward_solve_graph`, `get_interaction_graph`,
`get_event_graph`, `add_event_graph`, `add_backward_solve_graph`, `add_interaction_graph`;
nodes/pins: `create_node(control_rig, graph, node_type, position=None, node_name)`, `list_nodes`, `delete_node`,
`get/set_node_position`, `add_event_node`, `add_variable_node`, `list_pins`, `get/set_pin_value`, `connect_pins`,
`disconnect_pins`, `get_connected_pins`; variables: `add_variable`, `list_variables`, `get_variable`, `change_variable_type`, `remove_variable`.

### 1.4 SequencerControlRigTools (`$AAT/toolsets/controlrig_sequencer.py`, 72 tools) — Control Rig inside Sequencer
Value get/set (all take `sequence, control_rig_asset_path, control_name, frame`, setters have `set_key=True`):
`get/set_float`, `get/set_bool`, `get/set_int`, `get/set_vector2d(x,y)`, `get/set_position(x,y,z)`, `get/set_rotator(pitch,yaw,roll)`,
`get/set_scale`, `get/set_euler_transform(9 floats)`, `get/set_transform(loc+rot)`, `get/set_world_transform(loc+rot)`,
`get_actor_transform_at_frame(sequence, actor_name, frame)`.
Keying: `key_controls(section, control_names)` (at CURRENT Sequencer time), `key_controls_at_frames(section, control_names, frames)`.
Baking: `bake_to_control_rig(sequence, binding, control_rig_asset_path, reduce_keys=False, tolerance=0.001, reset_controls=True)`,
`load_anim_into_rig(cr_section, anim_sequence_path, start_frame=0, reset_controls=True, key_reduce=False, tolerance=0.001)`,
`collapse_anim_layers(sequence, control_rig_asset_path, reduce_keys, tolerance)`.
Masking: `get/set_controls_mask`, `show_all_controls`, `hide_all_controls`.
Layering/priority: `is_layered_control_rig`, `set_layered_mode(sequence, path, is_layered)`, `get/set_priority_order`, `is_fk_control_rig`.
Spaces: `set_space(seq, path, control, space_type, frame, space_target)`, `move_space`, `delete_space`, `bake_space`.
Tools: `tween_control_rig`, `blend_values_on_selected(sequence, operation, blend_value)`, `snap_control_rig(...)`,
`select_mirrored_controls`, `mirror_selected_controls`, `zero_transforms(selection_only, include_channels)`.
Anim layers (editor Anim Layers panel): `get_anim_layers`, `add_layer_from_selection`, `delete_anim_layer(index)`,
`duplicate_anim_layer`, `reorder_anim_layers`, `merge_anim_layers(indices)`.
Selection: `get_selected_controls`, `select_control`, `clear_selection`, `frame_selection`.
FBX: `export_fbx_from_rig(sequence, path, export_file_path, ascii)`, `import_fbx_to_rig(sequence, path, import_file_path, selected_controls)`.
Track: `find_or_create_track(sequence, binding, control_rig_asset_path, is_layered=False)` -> JSON `{track, control_rig}`,
`get_control_rigs(sequence)`, `get_controls_info(sequence, path)` (JSON list of `{name, type...}`).
Animation-mode UI: `get/set_anim_mode_gizmo_scale`, `..._hierarchy`, `..._nulls`, `..._hide_manips`, `..._only_rig_sel`, `..._local_spaces`.

### 1.5 SequencerOutlinerTools (`outliner.py`, 18 tools)
`get_outliner_tree`, `get_outliner_children(node, type_filter=None)`, `get/set_outliner_selection`, `get_node_label`,
`set_node_expanded`/`is_node_expanded`, `set_node_muted`/`get_muted_nodes`, `set_node_solo`/`get_soloed_nodes`,
`set_node_deactivated`/`get_deactivated_nodes`, `set_node_locked`/`get_locked_nodes`, `set_node_pinned`/`get_pinned_nodes`,
`get_sections_for_nodes`. Nodes are `SequencerViewModelScriptingStruct`.

### 1.6 SequencerImportExportTools (`import_export.py`, 6 tools)
`export_fbx(world, sequence, bindings, fbx_file_path, override_options=None)`, `import_fbx(world, sequence, bindings, import_settings, fbx_file_path)`,
`export_anim_sequence(world, sequence, anim_sequence, binding, create_link=False)` -> `unreal.SequencerTools.export_anim_sequence(world, seq, anim, unreal.AnimSeqExportOption(), binding, create_link)`
(default export options, no way to pass custom ones via the tool), `link_anim_sequence`, `get_linked_anim_sequences(sequence)`, `get_linked_level_sequence(anim_sequence)`.

### 1.7 SequencerCustomBindingTools (`custom_bindings.py`, 8 tools)
`convert_to_spawnable(binding)` (returns list), `convert_to_possessable`, `convert_to_custom_binding(binding, binding_type_class)`,
`get_custom_binding_type`, `get_custom_binding_objects`, `get_custom_bindings_of_type`, `change_actor_template_class(binding, actor_class)`,
`save_default_spawnable_state(binding)`.

### 1.8 SequencerConditionTools (`conditions.py`, 9 tools)
`get/set/clear_section_condition(section[, condition_class])`, `get/set/clear_track_condition`, `get/set/clear_track_row_condition(track, row_index[, cls])`.

### 1.9 SequencerAnimMixerTools (`.../sequencer_animmixer_toolset/toolsets/mixer.py`, 20 tools)
`get_mixer_layers(track: MovieSceneAnimationMixerTrack)`, `get_mixer_layer_count`, `add_mixer_layer`, `insert_mixer_layer(track, index)`,
`add_animation_to_mixer(track, layer_index, start_frame, anim_sequence)`, `add_child_track_to_layer(track, binding, track_class, layer_index)`
(e.g. Control Rig on a mixer layer), `get/set_layer_name`, `get_layer_sections`, `get_layer_index`, `is_layer_empty`,
transitions: `get_transitions_for_section`, `get_transition_between`, `get_transition_info`, `change_transition_type`, `get_transition_name`,
decorations: `get_compatible_decorations`, `get_decorations`, `find_decoration`, `add_decoration`, `remove_decoration`.
The mixer track is added with `SequencerTools.add_track_to_binding(binding, unreal.MovieSceneAnimationMixerTrack.static_class())`
(`.../tests/test_mixer_toolset.py:60`).

### 1.10 Gotchas visible in code
- **Frames are DISPLAY-RATE frames everywhere** in these tools, not tick-resolution ticks:
  `set_playhead_frame` -> `LevelSequenceEditorBlueprintLibrary.set_global_position(params)` whose `TimeUnit` defaults to `DisplayRate`
  (`Plugins/MovieScene/LevelSequenceEditor/Source/LevelSequenceEditor/Public/LevelSequenceEditorBlueprintLibrary.h:108`);
  `set_section_range` -> `MovieSceneSectionExtensions::SetRange`, which converts from display rate to tick resolution
  (`Plugins/MovieScene/SequencerScripting/Source/SequencerScripting/Private/ExtensionLibraries/MovieSceneSectionExtensions.cpp:271-290`);
  channel `add_key` defaults `EMovieSceneTimeUnit::DisplayRate` (`.../Private/KeysAndChannels/MovieSceneScriptingFloat.h:376`);
  all `ControlRigSequencerLibrary` get/set default `TimeUnit = DisplayRate` (`ControlRigSequencerEditorLibrary.h:610-640`).
  `set_tick_resolution` migrates frame times (`MovieSceneSequenceExtensions.h:118-125`) — avoid changing it.
- **Most tools need a sequence OPEN in Sequencer**: playback/selection/camera/layer tools go through
  `LevelSequenceEditorBlueprintLibrary`/`LevelSequenceEditorSubsystem`, which act on the open (focused) sequence
  (`create_camera` uses `Sequencer->GetFocusedMovieSceneSequence()`, `Source/Editor/Sequencer/Private/SequencerUtilities.cpp:1063`).
  Tests always call `open_level_sequence(seq)` right after creating (`$AAT/tests/_sequencer_test_base.py`).
- `create_camera(spawnable)`: spawns a CineCameraActor at the **current viewport camera** pose, converts the binding to a custom
  binding (`UMovieSceneSpawnableActorBinding` if spawnable, else **`UMovieSceneReplaceableActorBinding`** — not a plain possessable),
  then **locks the viewport to the camera** and **creates a Camera Cut track/section only if none exists yet and there is no
  Cinematic Shot track** (`SequencerUtilities.cpp:1063-1157`, `NewCameraAdded` at :959-973,
  `Source/Editor/MovieSceneTools/Private/MovieSceneToolHelpers.cpp:1424-1454`). Second and later cameras need manual camera-cut sections.
- Viewport pilot lock left on a destroyed spawnable can assert in `UTypedElementRegistry`; tests eject it
  (`LevelEditorSubsystem.eject_pilot_level_actor()` + `set_lock_camera_cut_to_viewport(False)`) before closing (`_sequencer_test_base.py: _release_viewport_actor_lock`).
- `add_actors` auto-creates a 3D transform track; adding a second transform track to the same binding cannot be keyed
  (`_sequencer_test_base.py:_make_transform_section` comment). Reuse via `find_tracks_by_type`.
- `set_camera_cut_binding` takes a **GUID string** and builds `MovieSceneObjectBindingID` with only `Guid` set (sequence-local).
  Use `str(binding.binding_id)` (proxy field `BindingID`). Native alternative: `section.set_camera_binding_id(sequence.get_binding_id(binding))`
  (`Source/Runtime/MovieSceneTracks/Public/Sections/MovieSceneCameraCutSection.h:47-52`, `MovieSceneSequenceExtensions.h:457`).
  Exact str format accepted by `unreal.Guid(str)` — **UNVERIFIED** (likely 32-hex from `Guid.to_string()`).
- `add_spawnable_from_instance` tool calls the **deprecated (5.5)** `sequence.add_spawnable_from_instance`; prefer
  `LevelSequenceEditorSubsystem.add_spawnable_from_instance` (`MovieSceneSequenceExtensions.h:421-434`).
  `add_spawnable_from_class` already uses the subsystem.
- `find_or_create_track` / `bake_to_control_rig` require a **Control Rig ASSET path** (`unreal.load_asset(path).get_control_rig_class()`),
  so the native **FK Control Rig cannot be added through these tools**. Call the library directly:
  `unreal.ControlRigSequencerLibrary.find_or_create_control_rig_track(world, seq, unreal.FKControlRig, binding, is_layered_control_rig=True)`.
  The value tools find the rig by **substring match on the rig class path** (`_find_rig`), so `control_rig_asset_path="FKControlRig"`
  matches `/Script/ControlRig.FKControlRig` for the get/set/key tools.
- `bake_to_control_rig` (library `BakeToControlRig`) **removes every existing Control Rig track on that binding** and **disables the
  Skeletal Animation track** (`Plugins/Animation/ControlRig/Source/ControlRigEditor/Private/ControlRigSequencerEditorLibrary.cpp:1445-1449, 1526-1532`).
  It is "replace the anim with editable keys", not an additive layer.
- A **layered (additive) Control Rig** requires the rig to have a Backwards Solve (InverseExecution) event, **except FK Control Rig**,
  which is switched to `EControlRigFKRigExecuteMode::Additive` (`ControlRigSequencerEditorLibrary.cpp:235-263`).
- `key_controls` keys at the current playhead; use `key_controls_at_frames` for explicit frames.
- After `find_or_create_track`, tests set the CR section range and force construction:
  `rigs[0].track.get_section_to_key().set_range(0,120)`, `control_rig.request_construction()`, `LevelSequenceEditorBlueprintLibrary.force_update()`
  (`$AAT/tests/test_sequencer_control_rig.py:95-110`).
- Anim-layer tools log `No Anim Layers on Level Sequence` when none exist; space tools log `Can not find Space Channel` on rigs without
  space channels (tests mark these as expected errors).

### 1.11 Recipe A — skeletal anim + FK additive Control Rig layer + bake to new AnimSequence
Assembled from `_sequencer_test_base.py`, `test_sequencer_control_rig.py`, `test_sequencer_import_export.py`, `test_sequencer_toolset.py:592-606`.
Mixed tool/Python; every step is either a listed tool or the library call it wraps.
```python
seq = SequencerTools.create_level_sequence('/Game/Cine', 'LS_Test')            # tool
unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)              # = open_sequence tool
SequencerTools.set_playback_range(seq, 0, 120)                                    # display-rate frames
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
actor.get_editor_property('skeletal_mesh_component').set_skeletal_mesh_asset(mesh)
binding = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem).add_actors([actor])[0]   # = add_actors tool
# (spawnable instead: SequencerCustomBindingTools.convert_to_spawnable(binding)[0])
trk = SequencerTools.add_track_to_binding(binding, unreal.MovieSceneSkeletalAnimationTrack.static_class())
sec = SequencerTools.add_section(trk); SequencerTools.set_section_range(sec, 0, 120)
SequencerTools.set_section_animation(sec, '/Game/Anims/A_Idle')                  # sets section.params.animation
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cr_trk = unreal.ControlRigSequencerLibrary.find_or_create_control_rig_track(
    world, seq, unreal.FKControlRig, binding, is_layered_control_rig=True)       # FK rig, Additive apply mode
cr_trk.get_section_to_key().set_range(0, 120)
rig = [p.control_rig for p in unreal.ControlRigSequencerLibrary.get_control_rigs(seq) if p.track == cr_trk][0]
# FK control names: get_controls_info(seq, 'FKControlRig')  (FK rig controls are named after bones; exact suffix UNVERIFIED)
SequencerControlRigTools.set_rotator(seq, 'FKControlRig', '<control>', 30, pitch=0, yaw=0, roll=20)  # keyed (set_key=True)
anim = unreal.AssetToolsHelpers.get_asset_tools().create_asset('A_Idle_Edited', '/Game/Anims', unreal.AnimSequence,
        (lambda f: (f.set_editor_property('target_skeleton', mesh.skeleton), f)[1])(unreal.AnimSequenceFactory()))
SequencerImportExportTools.export_anim_sequence(world, seq, anim, binding, create_link=False)  # bakes evaluated pose
```
Export options when calling the library directly: `UAnimSeqExportOption` fields incl. `bExportTransforms, bExportMorphTargets,
bExportAttributeCurves, bRecordInWorldSpace, bEvaluateAllSkeletalMeshComponents, Interpolation, CurveInterpolation, WarmUpFrames,
DelayBeforeStart, bUseCustomTimeRange, CustomStartFrame, CustomEndFrame, CustomDisplayRate, bUseCustomFrameRate, CustomFrameRate`
(`Source/Editor/UnrealEd/Classes/Exporters/AnimSeqExportOption.h`). Export uses the sequence display range and display rate unless overridden.
`SequencerTools.export_anim_sequence` spins up its own `ULevelSequencePlayer` (works without open Sequencer; use
`ControlRigSequencerLibrary.export_anim_sequence_from_sequencer(anim, opts, binding, create_link)` when the binding is a spawnable that
only exists in the open Sequencer) (`SequencerScriptingEditor/Public/SequencerTools.h:176-190`, `SequencerTools.cpp:388-440`,
`ControlRigSequencerEditorLibrary.h:166-178`).

### 1.12 Recipe B — CineCamera, camera cut, lens/focus/transform keys
```python
cam_binding = SequencerTools.create_camera(spawnable=True)      # camera at viewport pose; auto camera-cut if first camera
# or: SequencerTools.add_spawnable_from_class(seq, '/Script/CinematicCamera.CineCameraActor')
#     cut = SequencerTools.add_track_to_sequence(seq, unreal.MovieSceneCameraCutTrack.static_class())
#     cs  = SequencerTools.add_section(cut); SequencerTools.set_section_range(cs, 0, 120)
#     cs.set_camera_binding_id(seq.get_binding_id(cam_binding))
comp = SequencerTools.get_child_possessables(cam_binding)        # CameraComponent binding (or seq.add_possessable(cam.get_cine_camera_component()))
fl = SequencerTools.add_track_to_binding(comp[0], unreal.MovieSceneFloatTrack.static_class())
SequencerTools.set_property_name_and_path(fl, 'CurrentFocalLength', 'CurrentFocalLength')
s = SequencerTools.add_section(fl); SequencerTools.set_section_range(s, 0, 120)
ch = SequencerKeyframingTools.get_channel_names(s)[0]
SequencerKeyframingTools.add_key_float(s, ch, 0, 35.0); SequencerKeyframingTools.add_key_float(s, ch, 60, 85.0)
# focus: property path 'FocusSettings.ManualFocusDistance' (cm); aperture: 'CurrentAperture'
tr = SequencerTools.find_tracks_by_type(cam_binding, unreal.MovieScene3DTransformTrack.static_class())  # add if missing
# keys on channels named like 'Location.X', 'Rotation.Z' ...
```
- Property names are real UPROPERTYs: `CurrentFocalLength`, `CurrentAperture`, `CurrentFocusDistance`, `FocusSettings`
  (`Source/Runtime/CinematicCamera/Public/CineCameraComponent.h`). Nested path `FocusSettings.ManualFocusDistance` and whether
  `get_child_possessables` returns the component for a freshly created camera — **UNVERIFIED** (test only asserts a list).
  The Sequencer FBX camera import itself names the track `CurrentFocalLength` (`MovieSceneToolHelpers.cpp:3429`).

---

## 2. Runtime playback from C++

- Build.cs modules (all exist under `Source/Runtime/`): `LevelSequence`, `MovieScene`, `MovieSceneTracks`, `CinematicCamera`
  (`ls -d Source/Runtime/{LevelSequence,MovieScene,MovieSceneTracks,CinematicCamera}`).
- Create: `static ULevelSequencePlayer* ULevelSequencePlayer::CreateLevelSequencePlayer(UObject* WorldContextObject, ULevelSequence*,
  FMovieSceneSequencePlaybackSettings Settings, ALevelSequenceActor*& OutActor)` (`Source/Runtime/LevelSequence/Public/LevelSequencePlayer.h:106`).
- Camera cut event: `FOnLevelSequencePlayerCameraCutEvent OnCameraCut` (dynamic multicast, param `UCameraComponent*`);
  `UCameraComponent* GetActiveCameraComponent()` (`LevelSequencePlayer.h:27,109-114`).
- Base player `UMovieSceneSequencePlayer` (`Source/Runtime/MovieScene/Public/MovieSceneSequencePlayer.h`): `Play, PlayReverse, PlayLooping(NumLoops=-1),
  Pause, Stop, StopAtCurrentTime, GoToEndAndStop, PlayTo(PlaybackParams, PlayToParams), SetPlaybackPosition(PlaybackParams), RestoreState,
  SetCompletionModeOverride, IsPlaying, IsPaused, SetPlayRate, SetHideHud, SetDisableCameraCuts, GetCurrentTime, GetDuration, SetFrameRange,
  SetTimeRange, GetBoundObjects(FMovieSceneObjectBindingID), GetObjectBindings(UObject*)`.
  Events (dynamic, `FOnMovieSceneSequencePlayerEvent`): `OnPlay, OnPlayReverse, OnStop, OnPause, OnFinished` ("finishes naturally (without
  explicitly calling stop)"); native `FOnMovieSceneSequencePlayerNativeEvent OnNativeFinished`; native `OnSequenceUpdated()` (:405-430).
- `FMovieSceneSequencePlaybackParams`: `Frame (FFrameTime)`, `Time (s)`, `MarkedFrame (FString)`, `Timecode`, `PositionType`
  (`Frame|Time|MarkedFrame|Timecode`), `UpdateMethod (EUpdatePositionMethod)`, `bHasJumped`. Frame is display-rate
  (MarkedFrame is converted tick->display, `MovieSceneSequencePlayer.cpp:121`).
- `FMovieSceneSequencePlaybackSettings` fields (`Source/Runtime/MovieScene/Public/MovieSceneSequencePlaybackSettings.h:49-130`):
  `bAutoPlay(false)`, `LoopCount (FMovieSceneSequenceLoopCount.Value; -1 infinite)`, `TickInterval`, `PlayRate(1)`, `StartTime(0, s)`,
  `bRandomStartTime`, `bDisableMovementInput`, `bDisableLookAtInput`, `bHidePlayer`, `bHideHud`, `bDisableCameraCuts`,
  `FinishCompletionStateOverride (None|ForceKeepState|ForceRestoreState)`, `bPauseAtEnd`, `bInheritTickIntervalFromOwner(true)`, `bDynamicWeighting`.
  **There is no `bRestoreState`** in 5.8 — use `FinishCompletionStateOverride` or per-section completion mode
  (`grep -n bRestoreState .../MovieSceneSequencePlaybackSettings.h` -> no match).
- `ALevelSequenceActor` (`Source/Runtime/LevelSequence/Public/LevelSequenceActor.h`):
  `PlaybackSettings` (:84), **`SequencePlayer` is `UE_DEPRECATED(5.4, "Direct access to SequencePlayer will be removed. Please use GetSequencePlayer()")`** (:86-88),
  use `ULevelSequencePlayer* GetSequencePlayer() const` (:153); `LevelSequenceAsset`, `SetSequence(ULevelSequence*)`, `CameraSettings`
  (`FLevelSequenceCameraSettings{bOverrideAspectRatioAxisConstraint, AspectRatioAxisConstraint}`), `BindingOverrides`, `bOverrideInstanceData`,
  `bReplicatePlayback`.
- Binding overrides on the actor: `SetBinding(FMovieSceneObjectBindingID, const TArray<AActor*>&, bool bAllowBindingsFromAsset=false)`,
  `SetBindingByTag(FName, const TArray<AActor*>&, bool bAllowBindingsFromAsset=false)`, `AddBinding`, `AddBindingByTag(FName, AActor*, bool)`,
  `RemoveBinding`, `RemoveBindingByTag`, `ResetBinding`, `ResetBindings`, `FindNamedBinding(FName)` ("Find Binding by Tag"), `FindNamedBindings` (:177-253).
  Doc: with `bAllowBindingsFromAsset=false` the override **replaces** the asset binding and **spawnables will not spawn**; `true` adds to them.
  Tags are authored in Sequencer (RMB binding -> Tags...) or via `tag_binding` tool.
- Minimal C++ (composed from the signatures above):
```cpp
FMovieSceneSequencePlaybackSettings S; S.bDisableMovementInput = S.bDisableLookAtInput = S.bHideHud = true;
S.FinishCompletionStateOverride = EMovieSceneCompletionModeOverride::ForceRestoreState;
ALevelSequenceActor* SeqActor = nullptr;
ULevelSequencePlayer* P = ULevelSequencePlayer::CreateLevelSequencePlayer(this, Seq, S, SeqActor);
SeqActor->SetBindingByTag(TEXT("Hero"), { HeroActor });      // before Play
P->OnFinished.AddDynamic(this, &UMyCine::HandleFinished);    // UFUNCTION handler
P->Play();
```

---

## 3. CineCamera

- `UCineCameraComponent` props: `Filmback (FCameraFilmbackSettings)`, `LensSettings`, `FocusSettings`, `CropSettings`, `CurrentFocalLength`,
  `CurrentAperture`, `CurrentFocusDistance`, `ExposureMethod`, `CustomNearClippingPlane`, `CurrentHorizontalFOV`; functions `SetFilmback,
  SetLensSettings, SetFocusSettings, SetCropSettings, SetCurrentAperture, SetCurrentFocalLength, SetFilmbackPresetByName, SetLensPresetByName,
  SetCropPresetByName, GetHorizontal/VerticalFieldOfView, static GetFilmbackPresetsCopy/GetLensPresetsCopy` (`Source/Runtime/CinematicCamera/Public/CineCameraComponent.h`).
- Presets live in config `[/Script/CinematicCamera.CineCameraSettings]` (`Config/BaseEngine.ini:3607`):
  filmbacks `16:9 Film, 16:9 Digital Film (23.76x13.365), 16:9 DSLR, Super 8mm, Super 16mm, Super 35mm, 35mm Academy, 35mm Full Aperture,
  35mm VistaVision, IMAX 70mm, APS-C (Canon), Full Frame DSLR (36x24), Micro Four Thirds`; **DefaultFilmbackPreset="16:9 Digital Film"**.
  Lenses `12mm Prime f/2.8, 30mm Prime f/1.4, 50mm Prime f/1.8, 85mm Prime f/1.8, 105mm Prime f/2, 200mm Prime f/2, 24-70mm Zoom f/2.8,
  70-200mm Zoom f/2.8, Universal Zoom (4-1000mm)`; **DefaultLensPresetName="Universal Zoom"**, **DefaultLensFocalLength=35**, **DefaultLensFStop=2.8**;
  crops `No Crop, 1.33 (4:3), 1.77 (16:9), 2.39`. Constructor applies these and sets `bConstrainAspectRatio=true` (`CineCameraComponent.cpp:45-57`).
- `FCameraFocusSettings` defaults: **`FocusMethod=Manual`, `ManualFocusDistance=100000` (1 km — effectively background in focus)**,
  `bSmoothFocusChanges=false`, `FocusSmoothingInterpSpeed=8`, `FocusOffset=0` (`CineCameraSettings.h:272-283`).
  `ECameraFocusMethod {DoNotOverride, Manual, Tracking, Disable}` (:191-205).
  Tracking: `FCameraTrackingFocusSettings{ActorToTrack (TSoftObjectPtr<AActor>), RelativeOffset, bDrawDebugTrackingFocusPoint}` (Interp props, keyable).
- `ACineCameraActor::LookatTrackingSettings (FCameraLookatTrackingSettings)`: `bEnableLookAtTracking, LookAtTrackingInterpSpeed, ActorToTrack,
  RelativeOffset, bAllowRoll, bDrawDebugLookAtTrackingPosition` (`CineCameraActor.h:23-86`).
- `ACameraRig_Rail` and `ACameraRig_Crane` still exist (`Source/Runtime/CinematicCamera/Public/CameraRig_Rail.h:19`, `CameraRig_Crane.h:18`).
  Sequencer also has `FSequencerUtilities::CreateCameraWithRig` (attaches a new CineCamera to a rig actor, `SequencerUtilities.cpp:1160-1242`).
- Dialogue focal lengths: the engine ships 30/50/85/105 mm primes but no dialogue defaults. Conventional shot/reverse-shot
  ~35-50 mm mediums, 85 mm close-ups at f/1.8-2.8 with tracking focus on the speaker's head — **UNVERIFIED (craft convention, not engine data)**.

---

## 4. Control Rig for an arbitrary skeleton

- `UFKControlRig : UControlRig`, `UCLASS(NotBlueprintable, DisplayName="FK Control Rig")` — native, no asset, works on any skeleton
  (`Plugins/Animation/ControlRig/Source/ControlRig/Public/Rigs/FKControlRig.h:40-41`). Python class `unreal.FKControlRig`.
  `EControlRigFKRigExecuteMode {Replace, Additive, Direct}` (:24-37). Library: `get_fk_control_rig_apply_mode(rig)`,
  `set_control_rig_apply_mode(rig, mode)`, `is_fk_control_rig(rig)` (`ControlRigSequencerEditorLibrary.h:1387, ~1415-1423`).
- Sequencer UI: Add Track menu on a binding has "FK Control Rig" ("Adds the FK Control Rig") and an FK bone-selection dialog
  ("Select Bones You Want To Be Active On The FK Control Rig") (`ControlRigEditor/Private/Sequencer/ControlRigParameterTrackEditor.cpp:2021-2022, 6756, 6916`).
- Content Browser AnimSequence context menu "Edit With FK Control Rig" -> `EditWithFKControlRig` -> `BakeToControlRig(UFKControlRig::StaticClass(), ...)`,
  which creates a new Level Sequence `Driving_<AnimName>` next to the anim, baked to an FK rig (`ControlRigEditorModule.cpp:1068, 1162, 1232-1290`).
  Also "Bake To Control Rig" submenu (`ControlRigEditorModule.cpp:1175`, `BakeToControlRigHelper.cpp:351`).
- Skeletal animation track menu items (`Source/Editor/MovieSceneTools/Private/TrackEditors/CommonAnimationTrackEditor.cpp`):
  **"Bake Animation Sequence"** (tooltip: bake for this skeletal mesh using Sequencer display range and display rate),
  "Create Linked Animation Sequence" (:2824), "Open/Delete Linked Animation Sequence", "Import Anim Sequence Into This Section",
  "Add AutoBake"/"Remove AutoBake" (:2787-2801).
- Python (`unreal.ControlRigSequencerLibrary`, ScriptName of `UControlRigSequencerEditorLibrary`, `ControlRigSequencerEditorLibrary.h:121`), verified names:
  `get_visible_control_rigs`, `get_control_rigs(seq)` -> `[ControlRigSequencerBindingProxy{control_rig, track}]`,
  `find_or_create_control_rig_track(world, seq, cr_class, binding, is_layered_control_rig=False)`,
  `find_or_create_control_rig_component_track`, `bake_to_control_rig(world, seq, cr_class, export_options, reduce_keys, tolerance, binding, reset_controls=True)`,
  `load_anim_sequence_into_control_rig_section_with_range(section, anim, skel_comp, start_frame, use_custom_anim_range, anim_start, anim_end, time_unit, key_reduce, tolerance, interpolation, reset_controls, onto_selected_controls)`
  (old `load_anim_sequence_into_control_rig_section` deprecated 5.6), `export_anim_sequence_from_sequencer(anim, opts, binding, create_link)`,
  `get_linked_anim_track`, `get_or_create_linked_anim_track`, `add_auto_bake(bindings)`, `isolate_linked_anim_track(s)`, `delete_linked_anim_sequence/track`,
  `smart_reduce(params, section)`, `key_controls`, `key_controls_at_frames`, `get/set_local_control_rig_{float,bool,int,vector2d,position,rotator,scale,euler_transform,transform_no_scale,transform}` (+ plural batch forms),
  `get/set_control_rig_world_transform(s)`, `batch_get/set_control_transforms`, `get_control_values`, `collapse_control_rig_anim_layers(seq, track, key_reduce, tolerance)`,
  `collapse_control_rig_anim_layers_with_settings`, `set_control_rig_layered_mode(track, is_layered)`, `is_layered_control_rig`, `set/get_control_rig_priority_order`,
  `get_anim_layers`, `add_anim_layer_from_selection`, `delete/duplicate/reorder/merge_anim_layers`, `merge_anim_layers_with_settings`,
  space: `set_control_rig_space`, `bake_control_rig_space`, `delete/move_control_rig_space`, `get_space_channel`; constraints: `add_constraint`, `bake_constraint(s)`;
  `tween_control_rig`, `snap_control_rig`, `import_fbx_to_control_rig_track`, `export_fbx_from_control_rig_section`, `replace_control_rig`,
  `recreate_control_rig_with_new_settings`, `bake_time_warp`, `delete_time_warp`.
  Proof: `grep -n "static.*(" Plugins/Animation/ControlRig/Source/ControlRigEditor/Public/ControlRigSequencerEditorLibrary.h`.
- `unreal.SequencerTools` (ScriptName of `USequencerToolsFunctionLibrary`): `render_movie`, `cancel_movie_render`, `get_bound_objects(world, seq, bindings, range)`,
  `get_object_bindings`, `export_level_sequence_fbx(params)`, `export_anim_sequence(world, seq, anim, opts, binding, create_link)`,
  `export_anim_sequence_wait_for_delegate`, `link_anim_sequence`, `clear_linked_anim_sequences`, `get_level_sequence_link_from_anim_sequence`,
  `get_anim_sequence_link_from_level_sequence`, `import_level_sequence_fbx`, `create_event`, `create_quick_binding`,
  `import_fbx_to_control_rig`, `export_fbx_from_control_rig` (`Plugins/MovieScene/SequencerScripting/Source/SequencerScriptingEditor/Public/SequencerTools.h:130-296`).
- Animation layers: editor class `UAnimLayer`/`UAnimLayers` (`ControlRigEditor/Private/Sequencer/AnimLayers/AnimLayers.h:229-234`), driven
  by the layer functions above; collapse/merge bakes layers into one section.
- Modular Rig: `UModularRig : UControlRig` present (`ControlRig/Public/ModularRig.h:167-168`). Module library plugin `ControlRigModules`
  ("Control Rig Modules") is **Beta, EnabledByDefault true**, content folders `Modules`, `Modules56`, `Modules58` with
  `Spine, Neck, Arm, Leg, Foot, Finger, Shoulder, Chain, Tail, AnimalSpine, AnimalNeck, HindLeg, Hinge, Piston, Wheel, ...`
  (`Plugins/Animation/ControlRigModules/ControlRigModules.uplugin`, `ls .../Content/Modules`). ControlRig itself `EnabledByDefault: true`.
- `AnimatorKit` plugin: "Utilities for Animating in Unreal with Sequencer", Beta, EnabledByDefault true (`Plugins/Animation/AnimatorKit/AnimatorKit.uplugin`).
  Contents not inspected — **UNVERIFIED** what it adds.

---

## 5. Rendering frames for review

- Movie Render Queue plugin `Plugins/MovieScene/MovieRenderPipeline` ("Movie Render Queue", `EnabledByDefault: false`, not Beta). Includes
  Movie Render Graph (`MovieRenderPipelineCore/Public/Graph/...`). Python examples ship in `.../MovieRenderPipeline/Content/Python/`:
  `MovieGraphQuickRenderExample.py`, `MoviePipelineEditorExample.py`, `MovieGraphCreateConfigExample.py`, `mrq_stills.py`, etc.
- **Quick Render (5.6+ graph)** minimal: `unreal.get_editor_subsystem(unreal.MovieGraphQuickRenderSubsystem).begin_quick_render(mode, settings)` with
  `settings = unreal.MovieGraphQuickRenderModeSettings()`; `mode` from `EMovieGraphQuickRenderMode {CurrentSequence, UseViewportCameraInSequence,
  CurrentViewport (Still), SelectedCameras (Still)}`; `settings.level_sequence_override`, `frame_range_type = CUSTOM`, `custom_start_frame/custom_end_frame`,
  `post_render_behavior`, `graph_preset` (defaults to `/MovieRenderPipeline/DefaultQuickRenderGraph`)
  (`MovieGraphQuickRenderExample.py`, `MovieRenderPipelineCore/Public/Graph/MovieGraphQuickRenderSettings.h:28-44,145-147`,
  `.../Private/Graph/MovieGraphQuickRenderSettings.cpp:110`).
- Legacy MRQ: `subsystem = get_editor_subsystem(MoviePipelineQueueSubsystem)`, `job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)`,
  `job.sequence`/`job.map` (SoftObjectPath, `MoviePipelineQueue.h:692-696`), `job.get_configuration().find_or_add_setting_by_class(MoviePipelineOutputSetting /
  MoviePipelineDeferredPassBase / MoviePipelineImageSequenceOutput_PNG)`, then `subsystem.render_queue_with_executor_instance(unreal.MoviePipelinePIEExecutor(subsystem))`
  (`MoviePipelineEditorExample.py:127-187`). **PIE executor starts a PIE session** — conflicts with a shared editor.
- Lighter path (no MRQ, no PIE): `LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)`, set playhead
  (`set_global_position(MovieSceneSequencePlaybackParams(frame=FrameTime(FrameNumber(n))))` = `set_playhead_frame`), `force_update()`, then a viewport capture,
  e.g. `unreal.AutomationLibrary.take_high_res_screenshot(res_x, res_y, filename, camera=None, ...)`
  (`Source/Developer/FunctionalTesting/Public/AutomationBlueprintFunctionLibrary.h:143`). `SetCurrentTime(int)`/`SetCurrentLocalTime(int)` are
  deprecated since 5.4 (`LevelSequenceEditorBlueprintLibrary.h:88-101`). Whether the screenshot waits a frame for the lock to apply — **UNVERIFIED**;
  issue it on a later tick.

---

## 6. New / notable in 5.7-5.8 (verified only)

- **Sequencer Anim Mixer** (`MovieSceneAnimMixer`, Experimental, off by default): `MovieSceneAnimationMixerTrack` with layers, transitions
  (`MovieSceneAnimTransitionSectionBase`) and decorations; Control Rig can live on a mixer layer (`add_child_track_to_layer`). The MovieSceneTools
  editor has `IMovieSceneAnimMixerBakeProvider.h` (`Source/Editor/MovieSceneTools/Public/`) for baking mixer output. Toolset: `SequencerAnimMixerTools`.
- **Custom bindings** are now the model for spawnables/replaceables: `UMovieSceneSpawnableActorBinding`, `UMovieSceneReplaceableActorBinding`
  (used by `create_camera`); scripting `AddSpawnableFrom*` on the sequence deprecated 5.5 in favour of `LevelSequenceEditorSubsystem`.
- **Section/track conditions** exposed to scripting (`MovieSceneConditionExtensions.h`, `SequencerConditionTools`).
- **GameplayCameras** (`Plugins/Cameras/GameplayCameras`, "modular and data-driven camera system", **Experimental but EnabledByDefault true**):
  has Sequencer integration — `FGameplayCameraComponentTrackEditor` (tracks for `UGameplayCameraComponentBase` parameters) and a
  `MovieSceneCameraFramingZoneTrack/Section` (`GameplayCameras/Public/MovieScene/`, `GameplayCamerasEditor/Private/Sequencer/`). Camera directors:
  Single, PriorityQueue, StateTree, Blueprint (`GameplayCameras/Public/Directors/`). Whether a camera-cut can target a GameplayCameraComponent — **UNVERIFIED**.
- **CameraCalibration** (`Plugins/VirtualProduction/CameraCalibration*`): lens distortion/calibration for virtual production; not needed for game cinematics.
- Control Rig: `LoadAnimSequenceIntoControlRigSectionWithRange` (5.6), time-warp bake/delete on CR sections, `SmartReduce`, `MergeAnimLayersWithSettings`.
