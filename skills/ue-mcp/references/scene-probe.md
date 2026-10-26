# Scene probe — let the agent see the scene

The most expensive loop with a human author is "agent changes a scene → human looks → speaker off-screen / T-pose /
floating / wrong camera → again". Every one of those defects is visible in numbers. The scene probe is a
world subsystem that writes **what is on screen now** as JSON, so the agent checks its own work before anyone looks.

Template: [`templates/SceneProbe/`](../templates/SceneProbe/) — engine types only.

| File | Module | What |
|---|---|---|
| `AgentSceneProbe.h/.cpp` | your game module | `UAgentSceneProbe` (`UTickableWorldSubsystem`, Game + PIE worlds) and the `Agent.SceneState` console command |
| `Editor/AgentConsoleToolset.h/.cpp` | an editor module | `RunConsole` MCP tool — the shipped toolsets have no console. Skip if your project already has one |

## Install

1. Copy `AgentSceneProbe.*` into the game module (`Source/<Game>/Agent/`). Add `"Json"` to its `Build.cs`
   dependencies. Copy `Editor/AgentConsoleToolset.*` into an editor module (deps: `UnrealEd`, `ToolsetRegistry`)
   — UHT of a game target cannot see `UToolsetDefinition`.
2. **Full build with the editor closed.** A new `UCLASS` (and any header change) is not something Live Coding can
   add; a patched-in subsystem class half-exists until the next restart.
3. `ModelContextProtocol.RefreshTools`, then check the tool is listed (`describe_toolset`).

## Use from an agent

```
call_tool  <your toolset>  RunConsole  {"Command": "Agent.SceneState all intro_line3"}
→ read <Project>/Saved/AgentRuns/intro_line3.json from disk
```

- **Always pass a file name.** `RunConsole` returns what the command wrote to its output device; `UE_LOG` lines go
  to `GLog` and never come back through MCP. Without a file the JSON is only in the editor's log.
- Filter: `all` (default), `camera`, `characters`, `visible` (only characters rendered in the last 0.5 s).
- In `-game` (no editor, no MCP): `-ExecCmds="Agent.SceneState all boot"` fires on frame 1 — too early; prefer
  `"-csvExecCmds=300:Agent.SceneState all at300,900:Agent.SceneState all at900"` with `-csvCaptureFrames=N
  -ExitAfterCsvProfiling` (see `ue-performance`, measuring without a console). Better still, give the probe its own
  flags: start recording in `OnWorldBeginPlay` when `-AgentRun=<label>` is on the command line, and after
  `-AgentRunSeconds=N` stop, write the summary and `FPlatformMisc::RequestExit(false)` — a check run that needs
  nobody to close it, so an agent can launch several in parallel.
- `-game` check runs, lessons from a real project:
  - add `-unattended`: a missing map otherwise opens a modal dialog and the run silently falls back to the default map;
  - from Git Bash, `/Game/...` arguments get rewritten to `C:/Program Files/Git/Game/...` — set `MSYS_NO_PATHCONV=1`,
    and then pass the `.uproject` as a Windows path (`pwd -W`), since `/c/...` is no longer converted either;
  - `-game` loads the last full build; Live Coding patches are not in it;
  - budget: a 1280×720 `-game` run cost ~2–3 GB of VRAM on top of an idle editor (RTX 4090, mid-size scene); a PIE in
    the editor costs more. Measure yours with `nvidia-smi` sampled while the run lives;
  - in `-game`, `FScreenshotRequest` with UI shows the game window with its subtitles; in PIE, with UI it is the whole
    editor window — take the game view only (`bShowUI = !GIsEditor`).
- A second snapshot run often confirms a bug is real and not editor-only: if both PIE and `-game` show the frozen
  clip, it is in the content.
- Works in whoever's PIE is running — it is read-only and needs no editor lock (see [parallel-sessions.md](parallel-sessions.md)).

## What's in the JSON

```json
{"map":"UEDPIE_0_L_Intro","time":12.4,"dilation":1,
 "camera":{"target":"CineCam_Reverse","at":[120,-340,170],"rot":[-4,62,0],"fov":40,"cuts":5,"sinceCut":0.82,
           "cutTimes":[3.1,5.6,8.0,10.2,11.58]},
 "characters":[
   {"name":"BP_Hero_C_0","class":"BP_Hero_C","at":[300,0,92],"yaw":-170,"dist":410,
    "playing":"montage AM_Talk_Gesture 1.24s","rendered":true,"head":[0.36,0.31],"focus":true},
   {"name":"BP_Guard_C_2","class":"BP_Guard_C","at":[640,90,100],"yaw":180,"dist":820,
    "playing":"graph ABP_Guard_C","rendered":false,"gap":8}],
 "warnings":["BP_Guard_C_2: 8 cm above the floor, no montage, not falling"]}
```

| Field | Read it as |
|---|---|
| `camera.cuts`, `cutTimes`, `sinceCut` | a cut = view target changed, or the camera jumped > 150 cm / turned > 20° in one frame (tune the constants to your fastest legit move) |
| `playing` | `montage <name> <pos>`, `clip <name> <time>` (single-node), `graph <AnimBP class>`, `-` = nothing → T-pose warning |
| `rendered` | `WasRecentlyRendered(0.5)` — on screen (or in a shadow pass) in the last half second |
| `head` | head socket projected to the viewport, 0..1 each way; values outside 0..1 = off-frame. Rule-of-thirds heads sit near y ≈ 0.33 |
| `gap` | capsule bottom to the floor trace, cm. Warning only with no montage and not falling/flying |
| `dist`, `speed` | from the camera; velocity |
| `focus` | the actor carries tag `AgentProbe.Focus` — warn when not rendered |

Actor tags: `AgentProbe.Focus` (must be on screen — set it on the speaker while a line plays), `AgentProbe.Floats`
(ghosts, flyers: no air warning), `AgentProbe.Ignore` (leave out).

## Recipes

- **Frozen clip**: two snapshots a few seconds apart. A `clip`/`montage` whose time did not move while world
  `time` did is frozen (paused instance, zero play rate, a tick-disabled mesh). One snapshot can never show this.
- **Dialogue check**: on each line, snapshot → the speaker is `rendered` with `head` inside the frame (or the shot
  is a deliberate reaction shot — say so). Check `sinceCut` is small after each line change if cuts are line-driven.
- **Crossing the line**: from two consecutive snapshots of a reverse pair, both cameras should sit on the same side
  of the line between the two characters' `at` (sign of the 2D cross product).
- **Floating / sinking after a teleport or spawn**: `gap` > 5 with no montage; negative cases show as clipping
  through the floor — compare the capsule bottom to the floor yourself if needed.
- **Too many characters**: the list is nearest-first and capped (48); `charactersNotListed` says how many were cut.
  Filter `visible` to read only what the camera sees.

## Extending with project state

`UAgentSceneProbe::OnDescribe` is a static multicast delegate `(UWorld*, Filter, FJsonObject& Root, TArray<FString>&
Warnings)`. Bind it from your own subsystems — game rules state, dialogue line and its speaker, quest step, the
scene phase (menu / gameplay / dialogue / cutscene). Example at the bottom of `AgentSceneProbe.cpp`.

Warnings are **hints with context**, not errors: a reaction shot keeps the speaker off-screen on purpose; an
outro crane passes through empty frames. Put the scene phase into the warning text so the agent can judge.
Don't add warnings that fire on legitimate shots (empty frame, occlusion by a trace) — false alarms train the
agent to ignore the list.

## Beyond snapshots (when you need it)

- A **run recorder**: the same JSON twice a second plus events (cut, line change, warnings, Warning/Error log
  lines) into `Saved/AgentRuns/<label>/timeline.jsonl`, and a screenshot (`FScreenshotRequest::RequestScreenshot`)
  ~0.15 s after each cut. The agent then reviews a whole scene from one run instead of polling.
- Rewind Debugger / Gameplay Insights record far more, but into binary `.utrace` meant for eyes — the probe's job
  is a small, text-first answer an agent can diff.
