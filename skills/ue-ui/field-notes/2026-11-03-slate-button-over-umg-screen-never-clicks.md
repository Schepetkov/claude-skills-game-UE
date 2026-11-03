---
symptom: a plain Slate SButton added with GameViewportClient::AddViewportWidgetContent over a full-screen UMG screen gets the mouse down (it is under the pointer, it is the hit path's leaf) but OnClicked never fires; the same button works on a map without that screen
engine: "5.8.1"
status: observed
date: 2026-11-03
source: a tactics game's developer tool strip (Slate) shown over a level editor screen (UMG, full-screen drop zone + drag-detect on mouse down); checked with SlateInspectorToolset Click and the game's own mouse-down log
---
The press reached the button (a mouse-down preprocessor logged the hit path ending in `STextBlock < SButton`), the default
`EButtonClickMethod::DownAndUp` waits for the release, and the release never turned into a click while the full-screen
UMG screen was in the viewport. On a map without that screen the same strip clicked normally. The cause was not traced
(candidates: the screen's drag detection / mouse capture taking the release; hover lost because the click tool sends no
mouse move).

What fixed it: `SButton::ClickMethod(EButtonClickMethod::MouseDown)` - the button clicks on the press. Fine for tool
buttons (no drag-off-to-cancel needed). Also set `IsFocusable(false)` so a click does not take the keyboard from the game.

Checking a button from an agent without touching the human's mouse: `SlateInspectorToolset.Snapshot` (refs, physical
pixel rects) -> `Click {ref}`; log a line in OnClicked to see that it fired - `Click` returns true either way.
