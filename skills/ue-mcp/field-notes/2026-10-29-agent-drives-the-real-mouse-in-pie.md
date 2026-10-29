---
symptom: an agent needs to prove a mouse-only interaction (UMG drag-and-drop onto the 3D world) in PIE; console commands and tool clicks do not exercise it
engine: "5.8.1"
status: observed
date: 2026-10-29
source: one session verifying a drag-and-drop board editor; every step below was hit once
---
- **Where widgets are:** `SlateInspectorToolset.Snapshot` (`ref: ""`, deep `maxDepth`) lists widgets with `pos`/`size` in
  **physical** desktop pixels (a 150 % monitor did not need scaling). From editor Python in PIE,
  `widget.get_cached_geometry()` / `get_paint_space_geometry()` came back zero — do not build coordinates on it.
- **Where world points are:** `GameplayStatics.project_world_to_screen` gives viewport pixels. Find the viewport's
  offset once: put the OS cursor at a known point, read `PlayerController.get_mouse_position()` a second later
  (one frame of lag otherwise), offset = cursor − mouse.
- **Driving it:** PowerShell with `SetProcessDPIAware`, `SetForegroundWindow` on the editor, `SetCursorPos` +
  `mouse_event` down, 20 small `SetCursorPos` steps, up. `SlateInspectorToolset.Drag` needs a widget as the end ref —
  useless for dropping onto the 3D world.
- **The human may be in the same PIE.** All agent sessions idle and the PIE state changing on its own = the human is
  playing; a scripted click undid their action. Check before every scripted input, and stop driving the mouse then.
