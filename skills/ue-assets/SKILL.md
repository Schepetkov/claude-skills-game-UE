---
name: ue-assets
description: Unreal Engine 5.8 3D asset pipeline — mesh import (Interchange/FBX/glTF), Nanite (static, skeletal, foliage, assemblies), LODs and fallbacks, collision, UVs and lightmaps, materials and texture budgets, virtual textures, instancing, HLOD/World Partition streaming. Use when importing or authoring meshes, deciding Nanite vs LOD, fixing bad collision/UVs/scale/pivots, cutting mesh or texture memory, or bringing AI-generated meshes into a project.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---

# UE 5.8 Asset & Geometry Pipeline

## Ground truth rule (read first)

Grep the engine source before quoting cvars or settings — the published docs trail the source (confirmed drift on the MegaLights and Iris pages in 5.8). See [Finding the engine source](#finding-the-engine-source) at the bottom.

```bash
grep -rn 'TEXT("r\.Nanite' Engine/Source/Runtime/Renderer/Private/Nanite/
grep -rn 'FallbackRelativeError\|PositionPrecision' Engine/Source/Runtime/Engine/Classes/Engine/StaticMesh.h
```

## Decision 1: Nanite or traditional LODs?

Default in 5.8 is **Nanite for almost all opaque/masked geometry**. Use LODs when Nanite can't apply.

**Nanite works on:** static meshes, skeletal meshes, geometry collections; static mesh / skeletal mesh / instanced static mesh / spline mesh / HISM components, foliage painter, landscape grass.

**Nanite does not support:**

| Not supported | Consequence |
|---|---|
| Translucent / additive blend modes | falls back to default material + warning in log |
| Morph targets | any morph-driven mesh stays non-Nanite |
| Forward renderer, VR stereo, MSAA | project-wide blocker |
| Lighting channels | can't isolate lights per mesh |
| Native ray tracing (default) | RT uses fallback/proxy meshes; `r.RayTracing.Nanite.Mode 1` is experimental native |
| Custom expressions / derivative-dependent material nodes | may produce artifacts |

**Hard limit:** 16 million Nanite instances per scene (streamed-in included). Not a soft budget — it's clamped.

Requirements: DX12 + Shader Model 6, current desktop/console GPU, and an SSD (Nanite streams mesh pages on demand; on HDD you get visible pop-in that no setting fixes).

**Nanite is not "free detail."** It costs a fixed per-frame raster/cull overhead and increases on-disk + streaming footprint. On a stylized low-poly project, Nanite on a 400-tri prop is a net loss. Check actual triangle counts before enabling it wholesale.

## Decision 2: fallback quality

Every Nanite mesh keeps a fallback mesh used for ray tracing, complex collision, and non-Nanite paths.

- **Fallback Relative Error** — higher = coarser fallback = less memory, worse RT shadows/reflections and less accurate traces. Tune per asset class, not globally.
- **Position Precision** — quantization of vertex positions. Auto is usually right; forcing high precision on a small prop wastes memory.
- **Preserve Area** — keeps thin features from vanishing during simplification. Turn on for foliage cards, railings, wires.

If RT shadows look wrong only on detailed meshes, the fallback is the suspect before the shadow settings are.

## 5.8 Nanite additions worth knowing

- **Nanite Foliage** — instancing + skinned meshes + voxelization + bone-based wind. ~0.1 ms GPU for 100k updating bones in Epic's tests. Animation auto-stops below a screen-size threshold; wind still reaches distant trees.
- **Nanite Assemblies** — micro-instancing of repeated sub-parts (branches, fronds, bolts). Works for static and skeletal. This is how you get a detailed tree without paying for unique geometry per branch.
- **Nanite skeletal meshes** — use *animation* LODs, not geometry LODs. One draw call per mesh; VSM support; voxel LODs.
- **Nanite Pixel Programmable Distance** (foliage property) — distance past which pixel-programmable (masked/WPO) material work is skipped. Big win on dense foliage.
- **Skinned mesh WPO Disable Distance** and WPO evaluation controls — set these; WPO is the leading cause of VSM invalidation storms.
- Significantly improved raster + culling on handhelds.
- **Mesh Terrain** — new **experimental** terrain workflow in 5.8. Treat as experimental: do not migrate a landscape to it without an explicit decision from the user.

## Import pipeline

**Interchange** is the modern import framework (FBX, glTF, OBJ, USD). Prefer it over the legacy FBX importer for new pipelines — it's scriptable and has per-format pipeline assets you can version in the repo.

Checklist for every imported mesh:

1. **Units and scale** — UE is centimetres. Blender's default export is metres; a 100× scale error is the single most common import bug. Verify in the Static Mesh editor bounds, not by eye in the viewport.
2. **Pivot / origin** — set at export. Fixing pivots in-engine means an offset in every placement.
3. **Axis** — UE is Z-up, left-handed. glTF/Blender are Y-up/Z-up right-handed; Interchange converts, but check a directional asset (a chair, not a sphere).
4. **Build Nanite** — enable at import when the mesh qualifies (see decision 1).
5. **Generate Lightmap UVs** — **disable** if the project has no baked lighting. A Lumen-only project pays memory for lightmap UVs it never reads.
6. **Collision** — auto-generated collision is almost always wrong. See below.
7. **Material slots** — one slot per material is a draw call on non-Nanite paths. Merge slots at authoring time.
8. **Texture sRGB flags** — basecolor sRGB on; normal/roughness/metallic/AO sRGB **off**. Wrong flags here produce washed-out or crunchy shading that people then "fix" in the material, compounding the error.

## Collision — the part everyone gets wrong

- **Simple collision** drives physics and most queries. Author it: `UCX_` prefixed convex hulls in the source file, or the Static Mesh editor's convex decomposition. Auto-box is fine only for actual boxes.
- **Complex collision** (per-triangle) is for traces only, never for simulated physics. `Use Complex as Simple` on a dense mesh is a performance trap.
- **Nanite meshes use the fallback mesh for complex collision.** A very coarse fallback = wrong traces. If line traces miss geometry that's clearly there, check Fallback Relative Error.
- Grid/tile-based games: prefer **grid-space logic over physics queries** entirely. Collision should serve selection and cursor picking, not movement rules.

Debug: `show Collision` in viewport, `pxvis collision` at runtime, and the **Collision** viewmode.

## Textures & memory

Order of impact:

1. **Resolution.** A 4K texture on a prop that's 40 px on screen is 16× waste. Set **Maximum Texture Size** per asset or use LOD Bias in a Texture LOD Group.
2. **Texture Groups** — assign correctly (`World`, `Character`, `UI`, `Effects`). Group-level LOD bias is how you cut memory per platform without touching assets.
3. **Compression** — normal maps `TC_Normalmap`, masks/packed data `TC_Masks` (no sRGB), UI `UserInterface2D`. BC7 for quality-critical basecolor, default DXT elsewhere.
4. **Channel packing** — roughness/metallic/AO into one RGB texture. Three greyscale textures where one packed texture would do is a 3× memory bug.
5. **Virtual Textures** — for very large or very numerous textures. Enables streaming at tile granularity, but adds indirection cost; not a default-on win for small assets.
6. 5.8: `r.Material.StripUnusedDefaultTextures` removes unused default textures at runtime — free memory, enable it.

Measure, don't guess:

```
stat streaming            # streaming texture pool usage
ListTextures              # sorted by memory, with source asset names
memreport -full           # full memory breakdown to a file
obj list class=Texture2D
```

## Instancing & draw calls

- **ISM / HISM** for repeated static geometry. HISM adds per-instance culling+LOD; ISM is cheaper when everything is always visible.
- Nanite already batches heavily — do not hand-merge Nanite meshes into one giant mesh, it defeats per-cluster culling.
- **HLOD + World Partition** for open areas. 5.8 made HLOD visibility updates dramatically faster (139× on Epic's CitySample) and added an SSIM-based perceptual diff so unchanged HLODs aren't rebuilt.
- `wp.Runtime.HLOD.ForceDisableShadows` is now toggleable at any time (5.8) — a quick A/B when shadows from HLOD proxies look wrong.

## Working with AI-generated meshes

Generated meshes (Meshy, Tripo, Rodin, photogrammetry output) need a fixed cleanup pass before entering `Content/`:

1. Inspect triangle count and topology. Generated meshes are often uniformly dense with no edge flow — fine for Nanite props, bad for anything that deforms.
2. **Never rig/animate a raw generated mesh** without retopology; skinning artifacts on dense triangle soup are unfixable downstream.
3. Rescale to centimetres and set the pivot before import.
4. Author collision manually — convex decomposition on organic generated shapes produces dozens of hulls; cap the hull count.
5. Bake/reduce textures to the project's budget; generated PBR sets frequently ship at 4K for a prop that needs 512.
6. Enable Nanite only if the tri count justifies it.
7. Keep them under a clear root (e.g. `Content/Generated/`) so they're distinguishable in audits.

If the `meshy-3d-generation` skill is installed, it handles the generation side; this skill governs everything after the file lands on disk.

## Symptom → cause

| Symptom | Cause |
|---|---|
| Mesh is 100× too big/small | export units (metres vs cm) |
| Mesh renders black / flat | missing or wrongly-flagged normal map (sRGB left on) |
| Nanite mesh renders as default grey material | translucent/unsupported blend mode — check the log for the Nanite material warning |
| Traces pass through visible geometry | Nanite fallback too coarse, or complex collision missing |
| Shadows shimmer on foliage | WPO with no disable distance → VSM invalidation. Set WPO Disable Distance + Nanite Pixel Programmable Distance |
| Textures pop in late | streaming pool too small (`stat streaming`), or Maximum Texture Size unset on huge assets |
| Editor slow to open a level, huge memory | 5.8 memory-maps asset registry tag data — if you still see GBs, suspect a stale registry or unversioned redirectors |
| Instances silently missing in a big scene | approaching the 16M Nanite instance ceiling |

## Finding the engine source

| Engine type | Where the source lives |
|---|---|
| **Source build** | The `EngineAssociation` GUID in the `.uproject` maps to a path under `HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds` (Windows) or `~/.config/Epic/UnrealEngine/Install.ini` (Linux). |
| **Launcher install** | `EngineAssociation` is a version string (`"5.8"`). Path under `HKLM:\SOFTWARE\EpicGames\Unreal Engine\<version>` → `InstalledDirectory`. Public headers only — no `Private/` sources. |

With only a Launcher install, confirm cvar names at runtime: the console autocompletes them, and `DumpConsoleCommands` writes the full list.

## Related

- [references/nanite.md](references/nanite.md) — Nanite settings, cvars, visualization modes, and the fallback/RT interaction in detail

## Field notes from other projects

`field-notes/` next to this file (when present) holds lessons from other agents' retros, one per file. Before
debugging a symptom, `grep -ril "<symptom words>" field-notes/`. `status: observed` means seen in practice but not
yet checked against source — verify before relying on it; once checked, promote it into the tables above.
