---
name: ue-performance
description: Unreal Engine 5.8 performance and optimization — profiling methodology (stat unit, Unreal Insights, GPU Visualizer), finding the real bottleneck (Game/Draw/GPU/RHIT), hitch and shader-stutter elimination via PSO precaching, tick and Blueprint cost, GC and memory, streaming and World Partition. Use when something is slow, stuttery, or memory-heavy, when setting a frame budget, or before claiming any optimization worked.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---

# UE 5.8 Performance

## Ground truth rule (read first)

Grep the engine source before quoting any cvar or default — published docs lag the source (confirmed drift on `r.MegaLights.Allow` → `r.MegaLights.Allowed`, and on the non-existent `bUseIris` Target.cs flag). See [Finding the engine source](#finding-the-engine-source) at the bottom.

## The rule that matters more than any cvar

**Measure → isolate → fix → re-measure.** Never propose an optimization without a number attached, and never report one as done without a before/after.

Corollaries that are violated constantly:
- **Never profile in the editor** for anything but a first sniff. Editor overhead, PIE, and unbuilt shaders distort everything. Profile a **Development** or **Test** build, standalone, on target hardware.
- **Never profile the first run** after a content change — shader compilation and cold DDC dominate. Run twice, measure the second.
- `r.Lumen.AsyncCompute 0` before attributing GPU cost to Lumen, or the work hides in async and you'll "prove" a false conclusion.
- One change at a time. Two changes and one measurement tells you nothing.

## Step 1: which thread is the bottleneck?

```
stat unit
```

Reads out **Frame / Game / Draw / GPU / RHIT / DynRes**. In 5.8 it also shows GPU VRAM usage and budget, frame numbers, and UTC timestamps (`stats.UnitTimestamp 1`).

Interpretation:

| Highest number | Bottleneck | Go to |
|---|---|---|
| **Game** ≈ Frame | game thread: ticks, Blueprints, AI, gameplay code | Step 3 |
| **Draw** ≈ Frame | render thread: draw calls, state changes, primitive count | Step 4 |
| **GPU** ≈ Frame | shading, lighting, overdraw, resolution | `ue-lighting` skill + Step 4 |
| **RHIT** high | RHI thread: submission cost, PSO creation, driver | Step 5 |
| Frame ≫ all of them | vsync, frame pacing, or a stall (GC, streaming, PSO) | Step 6 |

`stat unitgraph` shows the same over time — essential for spikes, which averages hide.

Mobile only: `stat thermals` (new in 5.8) reports Android/iOS thermal state. A device that's throttling makes every other measurement meaningless.

## Step 2: capture a trace

```
YourGame.exe -game -trace=cpu,gpu,frame,loadtime,memory,counters -statnamedevents
```

Add `net` + `-NetTrace=1` for multiplayer, `WorldStreaming` for World Partition.

Open in **Unreal Insights**. 5.8 additions:

| Feature | Use |
|---|---|
| **UObject Count** trace counter (via `counters` channel) | catches runaway object creation |
| Annotation system (time / range / event based, saved to sidecar `.ini`) | mark up a capture and re-open it later with notes intact |
| **Snapshot hitches** — `snapshothitches -start` / `-stop` | auto-captures trace + screenshot on a hitch. Requires an active stat group (`stat default`). The fastest way to catch a hitch you can't reproduce on demand |
| **Spatial Profiler** tab (World Partition Insights, `WorldStreaming` channel) | per-cell streaming analysis. `wp.Editor.ExportMinimapForInsights` exports a PNG+JSON minimap so cells have visual context |
| GPU Profiler 2.0 (since 5.6) | correlate GPU events with game-thread spikes in one capture |

`-statnamedevents` is what gives you readable scope names instead of hashes — without it, a capture is far harder to read.

## Step 3: game thread

Order of suspicion:

1. **Tick.** Count what ticks. Most actors don't need to.
   - `PrimaryActorTick.bCanEverTick = false` is the default answer.
   - Tick groups and `TickInterval` for things that need to tick, but not at 60 Hz.
   - Blueprint Event Tick is the worst offender — roughly an order of magnitude more expensive than equivalent C++.
2. **Blueprint hot paths.** `stat game`, then the Insights CPU timeline filtered to Blueprint. Move measured hot Blueprint logic to C++ — never "for cleanliness", only with a measurement.
3. **AI / Behaviour Tree / StateTree / EQS.** EQS queries are expensive; check query frequency and item counts. `stat AI`, `stat StateTree`.
4. **Component overhead.** Every `USceneComponent` costs transform propagation. Deep attachment hierarchies are silent game-thread cost.
5. **Garbage collection.** See Step 6.

Useful stats: `stat game`, `stat engine`, `stat ai`, `stat anim`, `stat physics`, `stat levels`.

## Step 4: render thread & GPU

```
stat scenerendering       # draw call counts, primitive counts, RT instance count
stat rhi                  # RHI-level resource stats
stat initviews            # visibility/culling cost — often the hidden render-thread cost
ProfileGPU                # Ctrl+, in editor; opens GPU Visualizer
r.ProfileGPU.TableFormatting 1     # 5.8: compact text output
```

5.8: `ProfileGPU` now also reports **graphics pipe wait times** — that's how you tell "GPU is busy" from "GPU is waiting".

Render-thread cost drivers, in order:
1. **Draw calls / primitive count** — merge material slots, use ISM/HISM, let Nanite batch (don't hand-merge Nanite meshes).
2. **`stat initviews`** — culling cost scales with primitive count even when nothing is drawn. Huge numbers of tiny actors are expensive before a single triangle is rasterized.
3. **Dynamic shadow casters** — each one is extra passes. Audit "Cast Shadow" on small props.
4. **Translucency and overdraw** — the Shader Complexity and Quad Overdraw viewmodes. Particles and foliage are the usual suspects.
5. **Resolution / upscaling** — TSR settings and `r.ScreenPercentage` move GPU cost more than any material tweak.

For Lumen/MegaLights/VSM specifics use the **`ue-lighting`** skill.

## Step 5: hitches and shader stutter (PSO precaching)

Shader/PSO stutter is the #1 cause of "runs at 120 fps but feels awful". 5.8 defaults to **PSO precaching** (automatic collection + async compilation), which supersedes the old bundled-cache workflow that required playing through a build to record PSOs.

| Cvar | Default | Purpose |
|---|---|---|
| `r.PSOPrecaching` | on | master toggle |
| `r.PSOPrecache.Components` | on | precache component PSOs |
| `r.PSOPrecache.Resources` | off | precache resource PSOs (meshes) |
| `r.PSOPrecache.GlobalShaders` | on | precache global compute/graphics at startup |
| `r.PSOPrecache.ProxyCreationWhenPSOReady` | on | delay proxy creation until the PSO compiled |
| `r.PSOPrecache.ProxyCreationDelayStrategy` | — | `0` skip the draw until ready · `1` draw with default material |
| `r.pso.PrecompileThreadPoolPercentOfHardwareThreads` | 75 | compile parallelism |
| `r.pso.PrecompileThreadPoolSize` / `...SizeMin` / `...SizeMax` | 0 / 2 / INT_MAX | explicit thread counts |

Diagnose remaining hitches:

```
r.PSOPrecache.Validation 1     # lightweight tracking
r.PSOPrecache.Validation 2     # detailed, logs every miss
stat PSOPrecache               # collected metrics
```

On a miss the log reports Type, PSOPrecachingState, Material, VertexFactoryType, MeshPassName, and shader hashes — that identifies the exact material/pass to fix. In Insights, watch the **`PSOPrecache: Missed`** and **`PSOPrecache: Too Late`** timers.

Break into the debugger on a specific case: `r.PSOPrecache.BreakOnMaterialName`, `r.PSOPrecache.BreakOnPassName`, `r.PSOPrecache.BreakOnShaderHash`. Disable `r.PSOPrecache.UseBackgroundThreadForCollection` to make that debuggable.

Other hitch sources, in order of frequency: synchronous asset loads, GC, level streaming, and the first spawn of any actor type.

## Step 6: memory, GC, streaming

**Memory:**

```
memreport -full           # writes a full breakdown to Saved/Profiling/
stat memory
stat streaming            # texture streaming pool
ListTextures              # textures by memory, with asset names
obj list class=<Class>
```

5.8 memory changes worth knowing:
- **MallocBinned3 is the default allocator on Windows**; max small bin is now 14 KB.
- **Asset registry tag data is memory-mapped** — "reduces RAM by GBs in large projects". If a large project still shows huge registry memory, suspect a stale/unbuilt registry.
- D3D12 buffer allocators support async pool pre-allocation on background threads.

**Garbage collection** — GC spikes show as a Frame ≫ Game/Draw/GPU stall:

```
stat gc
gc.TimeBetweenPurgingPendingKillObjects
gc.MaxObjectsInGame                 # raise only with evidence; it costs memory
```

5.8 added actor-aware incremental GC options:
- `s.ContinuouslyIncrementalGCWhileActorsPendingPurge`
- `s.LevelStreamingLowMemoryActorsPendingPurgeCount`
- `wp.Runtime.LevelStreamingContinuouslyIncrementalGCWhileActorsPendingPurgeForWP` (World Partition variant)

**Cooked-only GC crash — UObject cache on a native CDO.** Native CDOs (and objects created during module load) sit in
the disregard-for-GC set in cooked builds (closed in `PreInitPostStartupScreen`), so the GC never walks their
`UPROPERTY` references: a `TMap<…, TObjectPtr<UTexture2D>>` cache on a CDO lets the texture die and the next GC crashes
on a dangling pointer. PIE has no disregard set and never shows it. Cache with `TStrongObjectPtr` / `AddToRoot` instead;
subsystems are created after the set closes and may use `UPROPERTY`. Without a debugger: dbghelp via ctypes on the
minidump + `dumpbin /disasm`; a crash in `FlushQueuedReferences` points at the owner of the bad field.
These smooth GC across frames instead of paying it in one spike — the right first move when you see periodic identical-size hitches.

**Streaming (5.8):**
- Streamable Manager just-in-time async loading: opt in with `UE_ENABLE_STREAMABLE_JIT_ASYNC_LOADING=1` + `bUseJustInTimeAsyncLoader=true`; tune with `s.StreamableJITAsyncLoadingInitialBatchingFactor` (default `0.25`).
- HLOD visibility updates are ~139× faster (Epic's CitySample number), with SSIM perceptual diff avoiding needless rebuilds.
- PCG runtime generation scheduler cut game-thread cost up to 30%; `pcg.RuntimeGeneration.TimeBetweenRuntimeGenSchedulerTicks` reduces scheduling overhead further.

## Measuring without a console (standalone run)

When the agent cannot type `stat unit`: put a `CameraActor` with `AutoActivateForPlayer=Player0` in the map, launch
`UnrealEditor.exe <uproject> <map> -game -windowed -ResX= -ResY= -csvCaptureFrames=900 -ExitAfterCsvProfiling`. The CSV lands
in **`<Engine>/Saved/Profiling/CSV/`** with `FrameTime`, `GameThreadTime`, `RenderThreadTime`, `GPUTime`, `RHI/DrawCalls`.
- `csv.field_size_limit(10**9)` — a metadata field exceeds the default. The header may grow during the run
  (`[HasHeaderRowAtEnd]`): read by the last header, take `rows[-2]`.
- A backgrounded window is frame-capped by the game's own setting (e.g. 30 fps) — pass an `-ini:GameUserSettings:` override.
- The first run compiles shaders: take the median of three. Another editor of the same machine open = numbers up to 2× worse.
- Commands at a frame: `"-csvExecCmds=400:<cmd> <arg>,450:HighResShot 1"` (comma-separated, args with spaces).
## Frame budget: state it before optimizing

At 60 fps you have **16.6 ms**; at 30 fps, 33.3 ms. Split it explicitly, e.g. for 60 fps:

| Bucket | Budget |
|---|---|
| Game thread | 6 ms |
| Render thread (Draw) | 5 ms |
| GPU | 14 ms (parallel, but must fit the frame) |
| Headroom | remainder |

Without a stated budget, "optimization" has no finish line. Write the budget down, then measure against it.

5.8's quality tiers were designed around explicit targets, and you should reuse them: **High = 60 fps console**, **Epic = 30 fps console**, **Medium (Lumen Lite) = 60 fps on PS5/handhelds**.

## Reporting results

When reporting an optimization, always give:
1. the build config and hardware measured on,
2. before/after for the specific stat, not just "frame time",
3. what was changed — exactly one thing,
4. what got worse (there is almost always a trade).

If a change didn't measurably help, say so and revert it. An unmeasured "optimization" left in the codebase is a liability.

## Finding the engine source

| Engine type | Where the source lives |
|---|---|
| **Source build** | The `EngineAssociation` GUID in the `.uproject` maps to a path under `HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds` (Windows) or `~/.config/Epic/UnrealEngine/Install.ini` (Linux). |
| **Launcher install** | `EngineAssociation` is a version string (`"5.8"`). Path under `HKLM:\SOFTWARE\EpicGames\Unreal Engine\<version>` → `InstalledDirectory`. Public headers only. |

With only a Launcher install, confirm cvar names at runtime: the console autocompletes them, and `DumpConsoleCommands` writes the full list.

## Related

- **`ue-lighting`** — GPU-side lighting cost, Lumen/MegaLights/VSM cvars, scalability tiers
- **`ue-assets`** — mesh/texture memory, Nanite cost, instancing, HLOD
- **`ue-ui`** — Slate/UMG cost, invalidation, widget tick
- **`ue-networking`** — server frame time, bandwidth, `-NetTrace=1`
- [references/profiling.md](references/profiling.md) — command reference and a step-by-step first-capture walkthrough

## Field notes from other projects

`field-notes/` next to this file (when present) holds lessons from other agents' retros, one per file. Before
debugging a symptom, `grep -ril "<symptom words>" field-notes/`. `status: observed` means seen in practice but not
yet checked against source — verify before relying on it; once checked, promote it into the tables above.
