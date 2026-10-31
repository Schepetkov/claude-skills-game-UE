---
symptom: a Niagara system edited through the MCP NiagaraToolset (copy of a fire system turned into body smoke) shows no effect, the wrong colour, particles floating far from the character, or a setting that "took" but reads back as the default
engine: "5.8.1"
status: observed
date: 2026-10-31
source: retro — a character aura built by copying an existing system and editing its stack over MCP (CreateNiagaraSystem, AddModule, SetStackInputData, SetRendererData); several hours of invisible or misplaced smoke traced to these traps
---
- **Enum inputs are set by internal name `<Enum>::NewEnumeratorN`, and N is not the display order.**
  `ENiagaraSkelSamplingModeFull`: Bones = 0, Sockets = 5, Bones and Sockets = 6, Surface (Triangles) = 7, Surface (Vertices) = 8.
  An unknown N is silently stored as 0. After every enum write, read the input back (`GetStackInputData`) and check
  `displayName`. Do not test the readback with a substring of the enum's own name — `ENiagara_AutomaticManual` contains
  "Manual" whatever the value is.
- **`AddModule` appends to the end of the stack.** A force module (`AccelerationForce`, `Drag`) added after
  `SolveForcesAndVelocity` does nothing. Remove the solver and add it again, so it is last.
- **Inputs hidden by a static switch refuse writes** ("input is hidden by static-switch / conditional logic") — set the
  switch first (e.g. SubUV `Define SubUV Setup Manually` = Manual, then `Manual SubImage Size`).
- **A copied system keeps the original's colour curve.** `Color` = ColorFromCurve with HDR orange keys times a small
  `Scale Color` is still red-brown. Replace the input with a constant `LinearColor`; disable the original's
  `DynamicMaterialParameters` if the new material does not read them (a fire erosion curve can hide smoke completely).
- **Skeletal-mesh sampling:** source mode `Default` takes the mesh the component is attached to — attach the system to
  the SkeletalMeshComponent itself (`SpawnSystemAttached` to the mesh, socket allowed). A preview helper that attaches to
  an intermediate scene component makes the sampler fall back to `PreviewMesh` at the wrong transform: smoke in columns a
  metre away. Judge such effects in PIE, not in an editor preview. `Surface (Triangles)` needs CPU access on the mesh;
  without it particles spawn at one point — `Skeleton (Bones)` needs nothing and covers a humanoid well.
- **There is no Python way to read particle positions** (`GetNiagaraParticlePositions_DebugOnly` is not exposed); verify
  with frames taken through the play view (`HighResShot` via the player controller), several seconds after spawn.
- **Black smoke on a dark scene does not read.** Carry the silhouette with a second, bright unlit emitter (colour > 1).
- Edits made while PIE runs are not saved; stop PIE, edit, `EditorAssetLibrary.save_loaded_asset`, start again.
