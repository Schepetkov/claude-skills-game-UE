---
symptom: PIE measured over MCP while the editor window is not in front - `csvprofile frames=N` never finishes, the CSV stays locked and empty, frames come out at ~333 ms
engine: "5.8.1"
status: observed
date: 2026-10-31
source: measurement, editor PIE driven over MCP from a terminal in front; Editor/UnrealEd/Classes/Editor/EditorPerformanceSettings.h bThrottleCPUWhenNotForeground
---
An agent drives the editor from another window, so the editor is in the background and its "Use Less CPU when in
Background" throttle (`UEditorPerformanceSettings::bThrottleCPUWhenNotForeground`) holds PIE at ~3 fps. A
`csvprofile frames=120` then took minutes and `csvprofile stop` wrote a file with no rows; when it did finish, every
frame was 333 ms, and anything paced by a timer (a 15 Hz scene capture) ran on every frame - a per-frame cost that is
not the one the player sees. Bring the editor window to the front before measuring (Win32 `ShowWindow` +
`SetForegroundWindow` on the editor's main window), or turn the throttle off for the run, and compare only runs taken
in the same state. Frame counter of the log prefix (`[NNN]`, frame number mod 1000) between two console commands is a
quick fps check when the CSV fails.
