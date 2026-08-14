# Profiling reference — UE 5.8

## First capture, step by step

1. **Build Development (not editor).** Profiling output goes to `Saved/Profiling/`.
2. Launch standalone with tracing:
   ```
   YourGame.exe -game -trace=cpu,gpu,frame,loadtime,memory,counters -statnamedevents -log
   ```
   Add `net -NetTrace=1` for multiplayer, `WorldStreaming` for World Partition.
3. **Run the scenario twice.** Discard the first run — shader compilation and cold caches distort it.
4. `stat unit` on screen the whole time; note which thread is highest.
5. Open the `.utrace` from `Saved/Profiling/` in **Unreal Insights**.
6. In Insights: Frames panel → click the slowest frame → Timing view scoped to that frame. Work top-down from the widest bar.

`-statnamedevents` gives readable scope names instead of hashes. Without it a capture is much harder to read.

## stat command index

### Overview
| Command | Shows |
|---|---|
| `stat fps` | frame rate only |
| `stat unit` | Frame / Game / Draw / GPU / RHIT / DynRes. 5.8: + GPU VRAM usage & budget, frame number, UTC timestamp |
| `stat unitgraph` | the same over time — use this for spikes |
| `stats.UnitTimestamp 1` | enable timestamps in `stat unit` |
| `stat detailed` | unit + a breakdown |
| `stat none` | clear |

### Game thread
| Command | Shows |
|---|---|
| `stat game` | gameplay tick breakdown |
| `stat engine` | engine-level counters |
| `stat ai` | AI cost |
| `stat StateTree` | StateTree evaluation |
| `stat anim` | animation evaluation |
| `stat physics` | physics step |
| `stat levels` | level streaming state |
| `stat gc` | garbage collection |
| `stat object` / `stat objectcounts` | UObject counts by class |

### Render / GPU
| Command | Shows |
|---|---|
| `stat scenerendering` | draw calls, primitives, **ray tracing active instances** |
| `stat initviews` | visibility/culling cost — the commonly-missed render-thread cost |
| `stat rhi` | RHI resources and counters |
| `stat gpu` | per-pass GPU timing (Lumen passes broken out) |
| `stat nanite` | Nanite raster/cull stats |
| `ProfileGPU` (Ctrl+, in editor) | one-frame GPU breakdown → GPU Visualizer |
| `r.ProfileGPU.TableFormatting 1` | 5.8: compact text output |
| `stat PSOPrecache` | PSO precaching metrics |

### Memory / streaming
| Command | Shows |
|---|---|
| `memreport -full` | full breakdown written to `Saved/Profiling/` |
| `stat memory` | live memory counters |
| `stat streaming` | texture streaming pool |
| `ListTextures` | textures sorted by memory, with source asset |
| `obj list class=Texture2D` | object dump by class |

### Mobile
| Command | Shows |
|---|---|
| `stat thermals` | 5.8: Android/iOS thermal state. A throttling device invalidates all other measurements |

## Insights channels

| Channel | Gives you |
|---|---|
| `cpu` | CPU timing tree (needs `-statnamedevents` for names) |
| `gpu` | GPU Profiler 2.0 events |
| `frame` | frame boundaries — required for the Frames panel |
| `loadtime` | asset load timeline; finds synchronous loads |
| `memory` | allocation tracking (heavy) |
| `counters` | 5.8: includes the **UObject Count** counter |
| `net` (+ `-NetTrace=1`) | per-property/RPC bandwidth attribution |
| `WorldStreaming` | 5.8 **Spatial Profiler** tab — per-cell World Partition analysis |

Context for the Spatial Profiler: `wp.Editor.ExportMinimapForInsights` exports PNG + JSON so cells are visually identifiable.

## Snapshot hitches (5.8)

Catches hitches you can't reproduce on demand — captures a trace snapshot **and** a screenshot at the moment of the hitch.

```
stat default            # an active stat group is required
snapshothitches -start
...play...
snapshothitches -stop
```

Output lands in `Saved/`. This is the correct tool for "it stutters sometimes and I can't catch it".

## Bottleneck decision table

| `stat unit` pattern | Meaning | Next move |
|---|---|---|
| Game ≈ Frame | game-thread bound | `stat game`, Insights CPU timeline; audit ticks and Blueprints |
| Draw ≈ Frame | render-thread bound | `stat scenerendering`, `stat initviews`; cut draw calls / primitive count |
| GPU ≈ Frame | GPU bound | `ProfileGPU`, `stat GPU`; see `ue-lighting`. Set `r.Lumen.AsyncCompute 0` first |
| RHIT high | submission / driver / PSO | PSO precaching validation; check for excessive state changes |
| Frame ≫ every thread | stall | GC (`stat gc`), sync load (`loadtime` channel), PSO miss, or vsync/pacing |
| GPU high only at certain angles | overdraw/complexity | Quad Overdraw + Shader Complexity viewmodes |
| Periodic identical-size spikes | GC or streaming tick | `stat gc`; try incremental GC cvars |

## Editor viewmodes worth naming

| Viewmode | Finds |
|---|---|
| Shader Complexity | expensive materials |
| Quad Overdraw | overlapping translucency / foliage cards |
| Light Complexity | too many overlapping lights (pre-MegaLights path) |
| Lightmap Density | baked lighting waste (irrelevant on Lumen-only projects) |
| Virtual Shadow Map → Page Allocation / Invalidation | VSM cost, names the offending primitive |
| Lumen → Performance Overview | which pixels need reflection rays |
| Nanite → Clusters / Overdraw / Evaluate WPO | Nanite-specific cost |
| Collision | mis-authored collision doing work it shouldn't |

## Shader compile diagnostics (5.8)

```
recompileshaders listtypes      # now reports PermutationCount
```

Material Editor and Material Instance Editor show a **Total Shaders** viewport overlay. `UMaterialEditingLibrary::ListShaders` exposes the same to editor script — usable for an automated audit of the worst offenders.

5.8 cut permutations across volumetric fog, VSM, Substrate, MegaLights and Lumen, and reduced LTO link time on Clang. If compile times are still bad after upgrading, suspect DDC configuration before suspecting content.

## Automation

- Epic's **Automated Performance Tests** framework feeds a runtime-trends view in Horde analytics (improved in 5.8). That's the hook for tracking regressions in CI rather than re-measuring by hand.
- Insights annotations (5.8) persist to sidecar `.ini` files next to the trace — annotate a baseline capture once and reuse it as the reference.
