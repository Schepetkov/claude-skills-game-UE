---
symptom: an effect spawned from a template vanishes a second later; a loop that should follow a moving component stays where it first appeared; a region "is not drawn" in one capture and drawn in the next; the editor dies running a material script
engine: "5.8.1"
status: observed
date: 2026-10-31
source: retro — a board aim overlay (ISM regions + a ghost Niagara loop) and a ground-sigil zone effect, three rounds with the human plus one editor crash
---
- **Niagara systems made with `CreateNiagaraSystem` from `/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst`
  carry `SystemState` Loop Behavior = Once, duration 1 s.** A loop built on it plays for a second and deactivates; a
  capture taken right after spawning looks fine. Set `SystemUpdateScript/SystemState/Loop Behavior` to Infinite for a
  loop, and probe the component (`is_active()`, `is_visible()`) a few seconds later, not in the spawn frame.
- **A single immortal particle does not follow its component in world space.** Moving the component
  (`SetWorldLocation`) moves new spawns only; set the emitter's `bLocalSpace` true (`SetEmitterData`, field
  `bLocalSpace`) for anything that glides after the cursor.
- **Template emitters come with `FixedBounds` ±100.** A 6 m ground decal-plane emitter is culled as soon as its
  centre leaves the screen. Set bounds to the real size (`FixedBounds` in `SetEmitterData`; the param name is
  `emitter`, not `emitterRef`, for the setters).
- **`MaterialEditingLibrary.delete_all_material_expressions` on a material a class default object holds asserts
  (`!IsRooted`) and kills the editor.** To change a Custom node, edit it in place:
  `unreal.find_object(None, '<path>.<name>:MaterialExpressionCustom_0').set_editor_property('code', ...)`, same for
  `MaterialExpressionScalarParameter_N` defaults, then `recompile_material`. Or delete the `.uasset` with the editor
  closed and create it fresh.
- **One capture cannot show flicker.** When the numbers say a thing is on and the frame shows it off (or the reverse),
  sample per frame for a couple of seconds with `unreal.register_slate_post_tick_callback` writing the values to a
  file. Seen: a fade "step toward the target" (`v += (want > v ? s : -s)`) overshot at the background editor's
  8 fps and blinked 0↔1 every frame; `FMath::FInterpConstantTo` stops at the target.
