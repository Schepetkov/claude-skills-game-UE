---
symptom: editor/game crashes (EXCEPTION_ACCESS_VIOLATION, address 0 or 0xffffffffffffffff) in UMaterialInstanceDynamic::SetTextureParameterValue / UMaterialInterface::GetTextureParameterValue a while after a widget swapped an image's material and later put the old brush back
engine: "5.8.1"
status: observed
date: 2026-10-31
source: two crash minidumps, stack UImage brush restore -> GetDynamicMaterial -> SetTextureParameterValue on a freed MID
---
A widget replaced an `UImage`'s brush with a new dynamic material (a "plate" look) and saved the previous brush in a
plain C++ member `FSlateBrush DesignBrush;` to restore it later. The previous brush's resource was the image's own
`UMaterialInstanceDynamic` (created by `GetDynamicMaterial()`). Once the image's brush no longer pointed at it, nothing
the GC can see referenced it: `FSlateBrush::ResourceObject` is a `UPROPERTY` inside the struct, but a struct member that
is not itself a `UPROPERTY` is invisible to the garbage collector. The GC freed the MID; the next restore put a dangling
pointer back on the image, `GetDynamicMaterial()` returned it as "already dynamic" and `SetTextureParameterValue` crashed.
In play it looked random (two crashes within minutes, both on hovering a card), because it needs a GC pass between
the swap and the restore.

Fix: `UPROPERTY() FSlateBrush SavedBrush;` (or `TObjectPtr`/`TStrongObjectPtr` to the material). Same rule for any
cached `UObject*` inside a struct member: brushes, `FSlateFontInfo::FontObject`, `FButtonStyle`.

Self-check that would have caught it: after any code that swaps a widget's material, run the swap/restore path with
`obj gc` between the steps (e.g. hover A → `obj gc` → hover B → `obj gc` → hover A). A screenshot of the new look
proves nothing about lifetime.
