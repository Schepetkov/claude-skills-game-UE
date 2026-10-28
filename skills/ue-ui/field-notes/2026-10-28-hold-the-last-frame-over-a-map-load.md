---
symptom: loading screen should show the last game frame frozen over OpenLevel; ReadPixels ensure InRHITexture; crash in the overlay's OnPaint after the map change; packaged-only crash in a screenshot delegate
engine: "5.8.1"
status: observed
date: 2026-10-28
source: Engine/Source/Runtime/Engine/Private/GameViewportClient.cpp (UGameViewportClient::ProcessScreenShots); crashes reproduced in -game and a packaged Development build
---
Holding the last frame of an intro still under a blocking map load (a viewport overlay outlives `UEngine::LoadMap`):

- **Read the frame inside the viewport's draw.** `FViewport::ReadPixels` called from game code in a `-game` run hit
  `ensure(InRHITexture)` (1.5 s stall) and returned nothing: outside the draw the back buffer is not bound. Use
  `FScreenshotRequest::RequestScreenshot(false)` + `UGameViewportClient::OnScreenshotCaptured()`: the delegate fires
  from `ProcessScreenShots` on the next draw with the pixels (alpha already 255) and no file is written while it is bound.
  Copy into `UTexture2D::CreateTransient(W, H, PF_B8G8R8A8)`, `SRGB = true`, `UpdateResource()`. Keep a fallback timer
  (leave on black if the frame never comes).
- **Never unbind the handler from inside itself.** `Remove(Handle)` destroys the lambda that is running, captures
  included; the next line read freed memory. In the editor's `-game` it survived by luck, the packaged build crashed
  (`EXCEPTION_ACCESS_VIOLATION` in the lambda). Set a "done" flag in the handler, remove the binding on the next tick.
- **The texture must be visible to the GC.** The options struct holding it lived in a subsystem field without
  `UPROPERTY`; `LoadMap`'s garbage collection freed the transient texture and the overlay crashed in `OnPaint`
  (`Index >= 0` in UObjectArray). Every struct on the path from request to paint: `UPROPERTY`.
- Preloading the next map with `LoadPackageAsync` under the intro: hold the **asset** (`UPackage::FindAssetInPackage()`
  → the `UWorld`) in a `UPROPERTY` across the map change — a held `UPackage` does not keep its inner objects alive.
  `OpenLevel` then finds the world in memory (measured: map load 3.77 s → 0.59 s uncooked, 0.34 s packaged).
