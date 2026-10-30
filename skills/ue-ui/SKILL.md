---
name: ue-ui
description: Unreal Engine 5.8 UI/UX — UMG and Slate, CommonUI, the 5.8 Unified Input System (Enhanced Input + Common Input merged), gamepad/cardinal navigation and focus, DPI scaling and safe zones, widget performance (invalidation, retainer, volatile, bindings), and UI debugging. Use when building or reviewing HUD/menus/tooltips, wiring gamepad or multi-platform input for UI, fixing focus/navigation/layout/scaling issues, or when UI is costing frame time.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---

# UE 5.8 UI & UX

## Ground truth rule (read first)

**Grep the engine source before quoting a cvar.** Epic's docs lag the source, and the UMG optimization doc page in particular lists **no** cvars at all while the engine declares dozens. See [Finding the engine source](#finding-the-engine-source) at the bottom.

```bash
grep -rhoE 'TEXT\("Slate\.[A-Za-z.]+"\)' \
  Engine/Source/Runtime/SlateCore/ Engine/Source/Runtime/Slate/ Engine/Source/Runtime/UMG/ | sort -u
```

## Decision 1: CommonUI or plain UMG?

Use **CommonUI** if any of these are true:
- gamepad support (this is the big one — cardinal navigation, focus, and back-handling are the parts everyone rebuilds badly),
- more than one input device or platform,
- layered UI (menus over HUD over modals) needing a real stack,
- platform-specific button glyphs.

Use plain UMG only for a small, mouse-only, single-layer HUD.

CommonUI gives you: a widget library of common game functionality, **style data assets** that separate styling from widgets (share one style across many UIs), an **Input Routing** system for selective widget interactivity, platform-specific button icons, and **cardinal navigation management for gamepads**.

Enable the `CommonUI` and `EnhancedInput` plugins, then **Project Settings → Game → Common Input Settings**.

## Decision 2: 5.8 changed input — use the unified path

5.8's headline UI change: **Enhanced Input and Common Input/UI are unified**. Consequences:

- No more duplicate data assets between gameplay input and UI input — this was the most annoying part of pre-5.8 CommonUI setups.
- Cross-platform input handling is simplified; one set of mappings drives both.
- New **Input Debugger for Enhanced Input UI** — use it instead of guessing why a binding doesn't fire.
- More reliable event processing, better widget binding behaviour, expanded virtual key support, trigger edge-case fixes.

For CommonUI + Enhanced Input: **Project Settings → Game → Common Input Settings → Enable Enhanced Input Support = true**.

Pre-5.8 tutorials describing parallel Common Input + Enhanced Input data assets are now obsolete — say so rather than following them.

## Architecture rules

1. **Widgets render state; they never own it.** Game state lives in GameState/PlayerState/components. A widget that owns authoritative data is a bug waiting for a multiplayer or save/load feature.
2. **Event-driven, never polled.** See the performance section — this is also an architecture rule, because it dictates that gameplay classes expose delegates.
3. **One widget class, one responsibility.** A 3000-node "MainHUD" Blueprint is unmaintainable and invalidates as a unit.
4. **C++ base + Blueprint derived.** Logic, bindings and delegates in a `UUserWidget` subclass; visual tree and styling in the Blueprint child. `BindWidget` gives compile-time-checked references:
   ```cpp
   UPROPERTY(meta = (BindWidget))
   TObjectPtr<UProgressBar> HealthBar;
   ```
   A missing/renamed widget then fails at Blueprint compile, not at runtime.
5. **Never `CreateWidget` in Tick or on hover.** Pool widgets; `SetVisibility` is orders of magnitude cheaper than construct/destruct.

## Performance: the rules that actually matter

Ranked by real-world impact.

### 1. Kill property bindings
A bound attribute is **polled every frame** for every widget that uses it. This is the number-one UMG cost.

Replace with event dispatchers/delegates:

```cpp
HealthComponent->OnHealthChanged.AddDynamic(this, &UMyHUD::HandleHealthChanged);
```

Rule for reviews: any `Bind` on a UMG property is a finding unless it's provably cold.

### 2. Minimize Tick and Paint
`NativeTick` / Event Tick on a widget is a per-frame cost multiplied by widget count. `SetDesiredTickFrequency(EWidgetTickFrequency::Never)` on widgets that don't need it.

### 3. Invalidation and caching
- **Invalidation Box** caches child widget draw/layout information and watches for changes.
- **Global Invalidation** (`Slate.EnableGlobalInvalidation`) applies caching to the whole `SWindow`. Big win for mostly-static UI; audit carefully — badly-marked widgets go stale.
- **Retainer Panel** flattens children into a single texture before painting. Use for expensive static subtrees, and to apply a material effect to a whole subtree. Costs a render target.
- Mark widgets that change **every frame** as **Volatile** — volatile widgets skip caching, which is *cheaper* than invalidating a cache constantly.

The mistake: wrapping frequently-changing widgets in an Invalidation Box. That's worse than not caching at all.

Relevant cvars (present in 5.8.1 source):
`Slate.EnableGlobalInvalidation`, `Slate.EnableInvalidationPanels`, `Slate.EnableRetainedRendering`, `Slate.AlwaysInvalidate` (diagnostic — forces worst case), `Slate.DynamicInvalidation.Options`, `Slate.DeferRetainedRenderingRenderThread`.

### 4. Animation cost, cheapest first
1. **Material-only animations — zero CPU cost**, GPU handles them. Correct choice for looping glows, scrolling backgrounds, pulses.
2. Blueprint-scripted animation — low startup cost.
3. Sequencer animation — higher initialization overhead. Non-transform changes (e.g. colour) force a redraw but **do not** invalidate layout.
4. Layout-changing animation — most expensive. Mark the widget Volatile.

### 5. Layout hygiene
- Don't nest Canvas Panels deeply — use Horizontal/Vertical/Grid boxes. Canvas is the most expensive panel.
- **Never combine Scale Box with Size Box** — creates an infinite update loop.
- Use **Spacer**, not Size Box, for spacing.
- Restrict **Rich Text** — prefer standard Text with a custom font. Rich Text parses markup and builds a more complex widget tree.
- Delete unused widgets. They cost memory and construction time even while invisible.

### 6. Visibility semantics
`Collapsed` removes the widget from layout **and** hit-testing (cheapest). `Hidden` keeps its layout slot. `SelfHitTestInvisible`/`HitTestInvisible` remove hit-testing cost from decorative widgets — apply liberally to backgrounds and non-interactive text.

### 7. Load in tiers
Split complex UI by priority: always-visible (load with the level), frequently-needed (preload in background), rarely-used (async load on demand). A settings menu should not be resident during gameplay.

## Debugging

| Tool | Use |
|---|---|
| **Widget Reflector** (Tools → Debug → Widget Reflector) | pick any on-screen widget, see the full Slate tree, source widget, and why it's laid out that way. First stop for every layout bug |
| `Slate.Debug.LogAllWidgets` | dump the widget set |
| `Slate.DumpUpdateList` | what's being updated each frame — finds the widget defeating your invalidation |
| `Slate.AlwaysInvalidate 1` | force worst-case invalidation; if perf barely changes, your caching wasn't working anyway |
| `Slate.Debug.TraceNavigationConfig` | trace gamepad/cardinal navigation decisions — the tool for "focus goes to the wrong button" |
| `Slate.EnableSlateWidgetTracker` | widget lifetime tracking |
| `Slate.DumpFontCacheStats` | font atlas pressure — a real cause of UI hitches with many distinct glyph sizes |
| **Input Debugger for Enhanced Input UI** (5.8) | why a UI input binding didn't fire |
| `stat slate`, `stat UI` | Slate CPU cost per frame |
| Unreal Insights, CPU channel | Slate ticks/paints in the timeline |

## Gamepad, focus & navigation

The part that always ships broken. Checklist:

1. Every interactive screen has a **defined initial focus target** — `SetFocus()` on open. Without it the first gamepad press does nothing.
2. Navigation rules set explicitly (`SetNavigationRule`) where auto cardinal navigation guesses wrong — long lists, grids, and wrapping.
3. **Back/cancel** handled at the stack level, not per-widget. CommonUI's activatable widget stack does this; hand-rolled stacks always leak a screen eventually.
4. Focus **visible**: a focus style distinct from hover. Mouse hover ≠ gamepad focus.
5. Input mode set correctly on transitions: `SetInputModeUIOnly` / `GameAndUI` / `GameOnly`, with the mouse cursor state matching.
6. Test the whole flow with the **mouse unplugged**. If any screen becomes unreachable, it's broken.

If the game world itself is an interactive surface (a grid, a map, a build area), decide explicitly whether it participates in UI focus or is a separate game-input context. Mixing them is where "the cursor jumped to the menu mid-action" bugs come from.

## Scaling, DPI & safe zones

- **DPI Curve** in Project Settings → User Interface. Default scales by shortest side; verify at 1280×720, 1920×1080 and 3840×2160 before shipping any menu.
- Anchor to edges/corners, not to absolute positions. Everything anchored to the centre breaks at ultrawide.
- **Safe zones** matter on console/TV — use `SSafeZone`/CommonUI's safe-zone support, and test with the debug safe-zone overlay. Text at the literal screen edge is a certification failure, not a taste issue.
- Fonts: pre-set the sizes you actually use. Every distinct size is a separate glyph atlas entry — `Slate.DumpFontCacheStats` shows the damage.
- Aspect ratio: test 16:9, 16:10, 21:9. HUD elements pinned to corners are fine; full-screen backgrounds need explicit handling.

## UX rules

General, but especially load-bearing for strategy/simulation UIs:

- **Never use engine message dialogs or OS-native popups for gameplay decisions.** Build an in-game modal styled to the project's design system: dismissable with Escape/B, initial focus on Cancel, and the confirm button labelled with the actual action ("End turn", "Delete save"), never "OK".
- **Show the current state at all times** — whose turn, which phase, what mode. Ambiguity here is the most common complaint about strategy UIs.
- **Preview before commit.** Movement range, attack range, outcome estimates on hover/focus, with an explicit confirm step for irreversible actions.
- **Undo for anything not yet committed.** If the design forbids undo, the confirm step becomes mandatory.
- **Information density is a feature** for strategy players. Provide full numeric breakdowns in tooltips — and make them keyboard/gamepad reachable, not hover-only.
- **Give a readable log of what happened** after AI or opponent actions. Drive it from replicated result state (see `ue-networking`), not from fire-and-forget events.

## Symptom → cause

| Symptom | Cause |
|---|---|
| UI eats frame time with nothing moving | property bindings polling every frame |
| Invalidation Box made it slower | a frequently-changing child inside it — mark Volatile or move it out |
| Layout stutters / infinite update | Scale Box wrapping a Size Box |
| Gamepad focus goes nowhere on open | no initial `SetFocus()` |
| Focus jumps to the wrong element | auto cardinal navigation guessing — set explicit navigation rules; trace with `Slate.Debug.TraceNavigationConfig` |
| Menu unreachable without a mouse | screen never received focus; test mouse-unplugged |
| Text clipped on TV / console | no safe zone |
| UI tiny or huge on a different monitor | DPI curve untested at that resolution |
| Hitch when a menu first opens | widget constructed on demand + font atlas build. Preload and pool |
| `BindWidget` failure at runtime | widget renamed in the Blueprint — check the property is `meta = (BindWidget)` and the names match |
| `NativeTick` never called on a CommonUI screen | `UCommonActivatableWidget` descendants carry `DisableNativeTick` — drive animation from a ticker/timer or hover/focus events |
| Editor builds, Shipping does not | `UPanelWidget::ReplaceChild/ReplaceChildAt` and `GetDisplayLabel` are `WITH_EDITOR` — write your own child swap |
| Widget added with `SetPositionInViewport` flies off-screen | 5.8 `SetPositionInViewport`/`SetDesiredSizeInViewport` reset anchors to (0,0) — call `SetAnchorsInViewport` last, or position inside the widget |
| Box/9-slice frame drawn as a thin line, "fixed" by touching the texture | margins use the texture proxy's size, created once on first paint while the texture was still compiling. `FTextureCompilingManager::FinishCompilation` + `ReleaseDynamicResource(Brush)` before use |
| 9-slice corners the wrong size | corner on screen = **texture** width × Margin; `ImageSize` does not matter — size the texture for the screen |
| UI texture blurry / grey box in PIE | texture in World group with mips/streaming — UI group, `NoMipmaps` or NeverStream |
| Icon drawn much smaller than its texture looks jagged / "pixelated" (a 400 px star at 30 px) | `NoMipmaps` + minification: Slate samples the full image, every screen pixel hits one texel. Non-power-of-two textures get no mips at all — pad to a POT square, `TMGS_SimpleAverage`, or ship the texture at the drawn size |
| `FSlateDrawElement::MakeBox` ignores the brush tint | it tints with the argument colour — pass `Brush.TintColor * InWidgetStyle` |
| RoundedBox not drawn | corner radius larger than half the height |
| Border with collapsed content vanishes | a `UBorder` sizes to its content; keep an empty SizeBox instead of collapsing |
| Outlined text sits lower than unoutlined | `OutlineSize` offsets the glyphs by the outline — compensate, do glows with separate shapes |
| `UImage::SetDesiredSizeOverride` has no effect | set `Brush.ImageSize` or wrap in a SizeBox |
| Pooled children stretch in a HorizontalBox | slot default is Fill — set Automatic from C++ |
| Overlay row gets height 0 | `SOverlay` clamps a child to the overlay minus padding — the overlay must hold all rows |
| Gamepad A clicks an invisible cursor and switches input to mouse | `CommonUI.ShouldVirtualAcceptSimulateMouseButton` (default true) — set false |
| UHT error on a UFUNCTION parameter | a parameter named `Navigation` shadows `UWidget::Navigation` |
| Nested WBP instance keeps old values | the parent WBP's template holds them — recompile the parent; CDO edits of the child show only after an editor restart |
| PIE instance thrown out of the viewport during work | `CompileWidgetBlueprint` of a live WBP while PIE runs — check `IsPIERunning` first |
| Unlit widget materials blown out on a dark map | widget emissive is multiplied by scene exposure — run the colour through `EyeAdaptationInverse` |
| World-space widget smeared over animated meshes | translucent quad without depth before TSR — `TranslucencyPass = MTP_AfterMotionBlur` |
| Full-screen widget added with `AddWidget` to an Overlay is 0×0 / clicks and drops go straight to the viewport | `UOverlaySlot` defaults to `HAlign_Left` / `VAlign_Top` (OverlaySlot.cpp) — set both to Fill explicitly |
| During a UMG drag-drop the board/world under the pointer is the wrong cell or none; drop lands nowhere | Slate sends `OnDragOver`, not `OnMouseMove`, so `FSceneViewport` keeps a stale mouse: `GetHitResultUnderCursor` / `GetMousePosition` lie. Trace from the event: `USlateBlueprintLibrary::AbsoluteToViewport(Event.GetScreenSpacePosition())` → `GetHitResultAtScreenPosition`, in `NativeOnDragOver` and `NativeOnDrop` |
| A transparent full-screen drop zone blocks the game's own "is the pointer over UI" check | the zone is the deepest hit-testable widget — let that check recognise it (compare the hit path's last widget with the zone's `GetCachedWidget()`), or keep the zone Collapsed outside the editing mode |

## Finding the engine source

| Engine type | Where the source lives |
|---|---|
| **Source build** | The `EngineAssociation` GUID in the `.uproject` maps to a path under `HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds` (Windows) or `~/.config/Epic/UnrealEngine/Install.ini` (Linux). |
| **Launcher install** | `EngineAssociation` is a version string (`"5.8"`). Path under `HKLM:\SOFTWARE\EpicGames\Unreal Engine\<version>` → `InstalledDirectory`. Public headers only. |

With only a Launcher install, confirm cvar names at runtime: the console autocompletes them, and `DumpConsoleCommands` writes the full list.

## External reference

[YawLighthouse/UMG-Slate-Compendium](https://github.com/YawLighthouse/UMG-Slate-Compendium) — the most complete community reference for UMG/Slate internals (widget catalogue, invalidation, attributes, focus system, input routing, debug tools, engine file map). Covers UE4 and UE5; cross-check anything version-specific against your engine source before acting on it.

## Related

- **`ue-performance`** — frame budget and how UI cost shows up in `stat unit`
- [references/umg-optimization.md](references/umg-optimization.md) — the full optimization checklist with cvars

## Field notes from other projects

`field-notes/` next to this file (when present) holds lessons from other agents' retros, one per file. Before
debugging a symptom, `grep -ril "<symptom words>" field-notes/`. `status: observed` means seen in practice but not
yet checked against source — verify before relying on it; once checked, promote it into the tables above.
