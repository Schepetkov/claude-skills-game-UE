# UMG / Slate optimization checklist — UE 5.8

Work top-down. Everything above the fold is worth more than everything below it.

## Tier 1 — do these first

| # | Rule | Why |
|---|---|---|
| 1 | **Remove every property binding.** Replace with event dispatchers / delegates | bound attributes are polled **every frame, per widget**. The single largest UMG cost in practice |
| 2 | **No Event Tick / `NativeTick`** unless proven necessary. Use `SetDesiredTickFrequency(EWidgetTickFrequency::Never)` | per-frame cost × widget count |
| 3 | **Delete unused widgets** from the tree | they cost memory and construction time even when invisible |
| 4 | **`Collapsed`, not `Hidden`**, for things out of play | `Collapsed` leaves layout *and* hit-testing; `Hidden` still occupies a layout slot |
| 5 | **`SelfHitTestInvisible` / `HitTestInvisible`** on all decorative widgets | removes them from hit-test traversal entirely |
| 6 | **Never construct widgets at runtime in hot paths.** Pool + `SetVisibility` | `CreateWidget` is expensive; a per-frame construct is a guaranteed hitch |

## Tier 2 — caching, done correctly

| Mechanism | Use it for | Do not use it for |
|---|---|---|
| **Invalidation Box** | subtrees that change rarely | anything that changes every frame — you pay the invalidation cost repeatedly |
| **Global Invalidation** (`Slate.EnableGlobalInvalidation`) | mostly-static, whole-window UI | projects with lots of ad-hoc widget mutation; stale-widget bugs are subtle |
| **Retainer Panel** | expensive static subtrees; applying a material effect to a whole subtree | small/simple subtrees — it costs a render target |
| **Volatile flag** | widgets that genuinely change every frame | everything else — volatile skips caching entirely |

Diagnostic: set `Slate.AlwaysInvalidate 1`. If frame time barely moves, your caching was not doing anything and you can delete the complexity.

Related cvars present in 5.8.1:
`Slate.EnableGlobalInvalidation`, `Slate.EnableInvalidationPanels`, `Slate.EnableRetainedRendering`, `Slate.EnableRetainedRenderingHittestRemap`, `Slate.DeferRetainedRenderingRenderThread`, `Slate.DynamicInvalidation.Options`, `Slate.AlwaysInvalidate`, `Slate.EnableDesignerRetainedRendering`.

## Tier 3 — animation

Cost order, cheapest first:

1. **Material-only animation** — *zero CPU cost*, entirely GPU. The correct choice for glows, scrolling backgrounds, pulses, shimmer, any looping decorative effect.
2. **Blueprint-scripted animation** — low startup cost.
3. **Sequencer animation** — higher initialization overhead. Changing non-transform attributes (e.g. colour) forces a **redraw** but does **not** invalidate layout.
4. **Layout-changing animation** — most expensive. Mark the animated widget **Volatile**.

Practical rule: if the animation could be expressed as a material parameter, it should be.

## Tier 4 — layout hygiene

- **Canvas Panel is the most expensive panel.** Don't nest them. Prefer Horizontal Box / Vertical Box / Grid Panel / Uniform Grid.
- **Scale Box + Size Box together creates an infinite update loop.** Never combine them.
- **Spacer**, not Size Box, for spacing.
- **Rich Text is expensive** (markup parsing + a more complex widget tree). Use standard Text with a custom font unless inline markup is genuinely required.
- Deep widget hierarchies cost layout traversal. Flatten where possible.

## Tier 5 — loading strategy

| Tier | Example | Strategy |
|---|---|---|
| Always visible | HUD, state indicator | load with the level, keep resident |
| Frequently needed | unit info panel, action bar | preload in background, pool, toggle visibility |
| Rarely used | settings, credits, full codex | async load on demand, destroy after |

A settings menu resident during gameplay is pure waste.

## Fonts

Every distinct font **size** creates glyph atlas entries. Many arbitrary sizes → atlas pressure → hitches when new glyphs are rasterized.

- Define a small fixed type scale and stick to it.
- Pre-cache glyphs for languages you ship.
- Measure: `Slate.DumpFontCacheStats`.
- Related: `Slate.EnableFontAntiAliasing`, `Slate.EnableLegacyFontHinting`, `Slate.DefaultTextShapingMethod`.

## Debug command index (verified in 5.8.1 source)

| Command | Use |
|---|---|
| `Slate.Debug.LogAllWidgets` | dump all widgets |
| `Slate.DumpUpdateList` | what updates each frame — finds the widget defeating invalidation |
| `Slate.AlwaysInvalidate` | force worst case; A/B your caching |
| `Slate.Debug.TraceNavigationConfig` | trace gamepad/cardinal navigation decisions |
| `Slate.EnableSlateWidgetTracker` | widget lifetime tracking |
| `Slate.DumpFontCacheStats` | font atlas pressure |
| `Slate.DebugCulling` | visualize Slate culling |
| `Slate.CullingSlackFillPercent` | culling tuning |
| `Slate.AllowSlateToSleep` | Slate idle behaviour — check this before blaming your UI for constant CPU use |
| `Slate.Commands.ListAll` / `Slate.Commands.ListBound` | command bindings |
| `Slate.AllowBackgroundBlurWidgets`, `Slate.BackgroundBlurDownsample`, `Slate.BackgroundBlurMaxKernelSize` | background blur is a **real** GPU cost — downsample it or disable on low-end |
| `stat slate`, `stat UI` | per-frame Slate CPU cost |

**Widget Reflector** (Tools → Debug → Widget Reflector) is the primary tool: pick any on-screen widget and inspect the live Slate tree, the owning UMG widget, and the layout chain. Use it before reading any code for a layout bug.

Re-derive the full list any time:

```bash
grep -rhoE 'TEXT\("Slate\.[A-Za-z.]+"\)' \
  Engine/Source/Runtime/SlateCore/ Engine/Source/Runtime/Slate/ Engine/Source/Runtime/UMG/ | sort -u
```

## Background blur — special mention

Background blur widgets are one of the few UMG features with meaningful **GPU** cost, and they multiply with layered menus. If a menu drops frame time on GPU rather than game thread, blur is the first suspect. Levers: `Slate.BackgroundBlurDownsample`, `Slate.BackgroundBlurMaxKernelSize`, or `Slate.AllowBackgroundBlurWidgets 0` in a low scalability tier.

## Review checklist

When reviewing a UMG Blueprint or `UUserWidget`, flag:

- [ ] any property binding
- [ ] Event Tick with logic in it
- [ ] `CreateWidget` outside construction/pooling
- [ ] nested Canvas Panels
- [ ] Scale Box wrapping a Size Box
- [ ] decorative widgets left hit-testable
- [ ] `Hidden` where `Collapsed` was meant
- [ ] Rich Text used for plain text
- [ ] widget references fetched by name/cast instead of `meta = (BindWidget)`
- [ ] state owned by the widget instead of a gameplay class
- [ ] no initial focus set on an interactive screen
- [ ] hover-only information with no gamepad/keyboard path
- [ ] engine/OS dialogs used for gameplay confirmations
