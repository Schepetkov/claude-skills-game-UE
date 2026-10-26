<!-- markdownlint-disable MD033 -->
# Game Dev Skills for Claude Code — Unreal Engine 5.8

Agent Skills that make [Claude Code](https://claude.com/claude-code) genuinely useful on an Unreal Engine project instead of confidently wrong about it.

Nine skills: eight covering networking, lighting, assets, performance, UI, cinematics, the engine's new built-in MCP server, and AI 3D-asset generation — written against **UE 5.8** and verified against a 5.8.1 source tree, not recalled from training data — plus one engine-agnostic skill for how the agent itself works on a long project: retros, a task journal, memory hygiene, independent review.

And tooling for running several agent sessions on one live editor: an editor-lock hook so they don't stop each other's PIE or crash each other with Live Coding, and a scene probe that lets the agent read what is on screen instead of asking you to look.

[Русская версия](README.ru.md)

---

## Why this exists

Ask any LLM about an Unreal cvar and you get a plausible name that may or may not exist. Two examples found while writing these skills:

| What the model / doc says | What UE 5.8.1 actually has |
|---|---|
| `r.MegaLights.Allow` (Epic's own doc page) | `r.MegaLights.Allowed`, plus `r.MegaLights.EnableForProject` and `r.MegaLights.Supported`, which the doc never mentions |
| `bUseIris = true;` in `*.Target.cs` (repeated across blogs and AI answers) | **does not exist** in 5.8's UnrealBuildTool. Iris is enabled via `net.Iris.UseIrisReplication` + `FIrisNetDriverConfig` |

So every skill here opens with the same rule: **verify against the engine source you are actually building against, before quoting anything.** Each skill ships the exact `grep` commands to do it, plus instructions for locating the engine source from your `.uproject`.

The rest is what the docs don't put in one place: decision trees, cost orderings, symptom→cause tables, and the failure modes that actually eat weeks.

---

## The skills

| Skill | Covers | Reach for it when |
|---|---|---|
| **`ue-networking`** | Replication (generic + Iris), Push Model, RPCs, subobjects, relevancy/dormancy, bandwidth, `-NetTrace` | Any replicated property. "Works in PIE, broken on dedicated server." Choosing Iris vs generic |
| **`ue-lighting`** | Lumen + **Lumen Lite**, MegaLights, Virtual Shadow Maps, Substrate, ray tracing scene, scalability tiers | Scene lighting setup, GPU budget, noise/leaking/flicker/ghosting, per-platform quality |
| **`ue-assets`** | Import (Interchange/FBX/glTF), Nanite (static/skeletal/foliage/assemblies), collision, UVs, textures, instancing, HLOD | Importing meshes, Nanite vs LOD, bad collision or scale, cutting mesh/texture memory |
| **`ue-performance`** | `stat unit` → bottleneck, Unreal Insights, GPU Visualizer, PSO precaching, tick/Blueprint cost, GC, streaming | Anything slow or stuttery. Setting a frame budget. Before claiming an optimization worked |
| **`ue-ui`** | UMG + Slate, CommonUI, the 5.8 **Unified Input System**, gamepad focus/navigation, DPI & safe zones, widget perf | HUD/menus, gamepad UI, focus bugs, UI eating frame time |
| **`ue-cinematics`** | Directing in-engine cutscenes and dialogue: beats, blocking, axis/180, coverage kit with lenses, cutting on line events, creature reveals, Sequencer over MCP (339 tools), FK Control Rig additive layers and baking, runtime playback | Staging a cutscene or conversation. "Our cinematics look flat." Editing a clip for a scene |
| **`ue-mcp`** | UE 5.8's built-in **Unreal MCP** server — setup, the 26 toolsets (and which 5 `AllToolsets` silently skips), tool search, custom tools in C++/Python, safety, field notes. **Parallel sessions** on one editor with an opt-in lock hook; a **scene probe** C++ template (scene state as JSON) and a `RunConsole` tool | Connecting an agent to a live editor. Writing project-specific MCP tools. Several sessions on one editor. Letting the agent check a scene itself |
| **`meshy-3d-generation`** | [Meshy AI](https://meshy.ai) API — text/image→3D, texturing, rigging, animation | Generating 3D assets. Pairs with `ue-assets` for the cleanup pass before import |
| **`agent-workflow`** | Engine-agnostic working discipline: a retro after every significant task whose output is a change (skill, rule, hook, tool), a sqlite task journal with rounds-per-area stats, auto-memory hygiene, speaking up, review by a second model, measured skill optimization | A task took several rounds of corrections. Memory feels stale. Before committing to a spec. "Why does this keep happening?" |

`ue-mcp` is the one that changes the others: with the editor connected, the agent can inspect the live Slate tree, read actor properties, and run automation tests instead of inferring from `.uasset` files it cannot read.

Each UE skill is a `SKILL.md` plus reference files that load only when needed — cvar tables, cookbooks, checklists.

### The agent workflow

The UE skills make the agent right about the engine. `agent-workflow` and the `ue-mcp` tooling make it cheaper to work with over months:

- **Retro → change.** After each significant task the agent counts the rounds of corrections, names the cause of each, and makes a change that removes it — a skill row, a rule, a hook, a tool — then logs it in `journal.py`. `journal.py stats` shows rounds per area over time and which changes preceded fewer rounds.
- **The agent checks its own scene.** `Agent.SceneState` writes camera, cuts, characters' animation state, on-screen head positions, floor gaps and warnings to JSON — the agent reads it over MCP before showing you anything.
- **Parallel sessions don't collide.** A file lock taken by a Claude Code hook guards PIE, Live Coding, level loads, builds and editor restarts; a PIE running without the lock is yours and is never stopped.
- **Memory stays honest.** State notes expire once accepted, lessons move into skills, claims are checked against git.

### What 5.8 specifically changed

These skills are current on the 5.8 deltas, not 5.3-era advice:

- **Built-in MCP server** — `Engine/Plugins/Experimental/ModelContextProtocol`, first-party, experimental, off by default. Agents can drive the editor over `http://127.0.0.1:8000/mcp`
- **Iris is production-ready** (Experimental through 5.7) — with the real enable path, not the blog version
- **Lumen Lite** — new Medium GI tier, ~2× faster than high quality, targets 60 fps on PS5/handhelds. **SSGI is deprecated** in its favour
- **MegaLights production-ready** — much lower noise, early cull by light power
- **Unified Input System** — Enhanced Input and Common Input/UI merged; no more duplicate data assets
- **Nanite Foliage / Assemblies**, Nanite Pixel Programmable Distance, skinned-mesh WPO controls
- **Snapshot hitches**, Spatial Profiler, UObject Count counter in Insights
- MallocBinned3 default on Windows, memory-mapped asset registry, actor-aware incremental GC
- Mobile: multi-pass deferred by default

---

## Install

**Requires:** [Claude Code](https://claude.com/claude-code). The UE skills need no other dependencies. `meshy-3d-generation` needs Python 3 with `requests` and a Meshy API key. The journal (`agent-workflow/scripts/journal.py`) and the editor-lock hook need Python 3, standard library only.

### Option A — user level (available in every project)

```powershell
# Windows
git clone https://github.com/Schepetkov/claude-skills-game-UE.git
cd claude-skills-game-UE
.\install.ps1
```

```bash
# macOS / Linux
git clone https://github.com/Schepetkov/claude-skills-game-UE.git
cd claude-skills-game-UE
./install.sh
```

Links each skill into `~/.claude/skills/`. On Windows it uses directory junctions (no admin rights needed), on POSIX symlinks — so `git pull` in this repo updates the skills everywhere. Pass `-Copy` / `--copy` if you'd rather have independent copies.

### Option B — one project only

```bash
# from your UE project root
cp -r /path/to/claude-skills-game-UE/skills/ue-lighting .claude/skills/
```

### Option C — pick individual skills

```powershell
.\install.ps1 -Skills ue-networking,ue-performance
```

```bash
./install.sh ue-networking ue-performance
```

Verify with `/skills` in Claude Code — the installed skills should be listed.

### Optional — the editor-lock hook (per project)

Skills install themselves; hooks don't. If more than one agent session (or you and an agent) will use one editor, opt in per project:

```bash
# from your UE project root
mkdir -p .claude/hooks
cp ~/.claude/skills/ue-mcp/hooks/editor-lock.py .claude/hooks/
```

Then add `PreToolUse`, `PostToolUse` and `PostToolUseFailure` hooks on `mcp__unreal__call_tool|Bash|PowerShell` to `.claude/settings.json`, calling `python "$CLAUDE_PROJECT_DIR/.claude/hooks/editor-lock.py" pre` / `post`. The full snippet, the env vars, how to tune the patterns and a pipe test are in [`skills/ue-mcp/references/parallel-sessions.md`](skills/ue-mcp/references/parallel-sessions.md). The lock file goes to `<your .uproject dir>/Saved/AgentLock.json`; `python .claude/hooks/editor-lock.py status|release` inspects or clears it.

The scene probe is C++ you add to your project: copy [`skills/ue-mcp/templates/SceneProbe/`](skills/ue-mcp/templates/SceneProbe/) into your modules and do a full build — see [`scene-probe.md`](skills/ue-mcp/references/scene-probe.md).

---

## Usage

Skills load automatically when the conversation matches their description. You can also invoke one by name:

```
/ue-performance the turn transition hitches, find out why
```

Typical prompts that trigger them:

- *"Why does this replicated property never update on the client?"* → `ue-networking`
- *"Lumen is eating 8 ms, what do I cut first?"* → `ue-lighting`
- *"Should this mesh be Nanite?"* → `ue-assets`
- *"The game stutters when a new enemy type first spawns"* → `ue-performance` (PSO precaching)
- *"Gamepad can't reach the settings menu"* → `ue-ui`
- *"Two of us are on the same editor and my PIE keeps getting stopped"* → `ue-mcp` (editor lock)
- *"That took four rounds, do the retro"* → `agent-workflow`

---

## What these skills will and won't do

**Will:**
- Tell you to measure before optimizing, and refuse to call something fixed without a before/after
- Give a decision tree with an explicit recommendation, not a survey of options
- Name the cheapest fix first and say what each one trades away
- Flag experimental features as experimental (Mesh Terrain, native Nanite RT, prefiltered distant VSM)
- Point at the engine source rather than assert a cvar from memory

**Won't:**
- Guarantee a cvar name without you having an engine source tree to check against. With a Launcher-only install, the skills fall back to runtime verification (`DumpConsoleCommands`, console autocomplete) and say which method they used
- Cover Blueprint-only workflows in depth — the bias is C++ with Blueprint at the leaves
- Cover audio, physics, or animation beyond what cinematics needs. Contributions welcome
- Compile the C++ templates for you — `SceneProbe` is written against 5.8 engine APIs but must be built in your project

---

## Engine version

Written and verified against **UE 5.8 / 5.8.1**.

Most content holds for 5.5+, but 5.8-specific items are marked as such. Anything Epic renames will drift — which is exactly why every skill leads with "grep the source first" rather than asking you to trust the table.

If you're on a different version, the skills still work: the methodology, decision trees, and symptom tables are version-independent. Only the cvar names need checking, and the skills tell the agent to check them.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: every factual claim needs a source — an engine-source path, an Epic doc URL, or a measurement. "I think it's called that" is not a source, and is exactly the failure mode this repo exists to fix.

## Licence

MIT — see [LICENSE](LICENSE).

`meshy-3d-generation` is included from [meshy-dev/meshy-3d-agent](https://github.com/meshy-dev/meshy-3d-agent) (MIT). Unreal Engine is a trademark of Epic Games, Inc.; this project is not affiliated with or endorsed by Epic Games.
