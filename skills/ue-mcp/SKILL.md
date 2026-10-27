---
name: ue-mcp
description: Unreal Engine 5.8's built-in MCP server (Unreal MCP plugin) — enabling it, connecting Claude Code/Cursor/Codex to a running editor, the toolset registry and tool-search model, writing custom tools in C++/Python, and the safety rules for letting an agent drive the editor. Use when setting up or debugging the Unreal MCP connection, deciding which toolsets to enable, adding project-specific MCP tools, running several agent sessions on one editor (PIE/Live Coding/build collisions, the editor-lock hook), letting the agent check a scene itself (scene-state JSON probe), or when a task would be better done by inspecting the live editor than by reading files.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---

# Unreal MCP (UE 5.8)

UE 5.8 ships a **first-party MCP server that runs inside the editor process**. An agent connected to it can spawn actors, edit levels and materials, inspect Blueprints and Slate widgets, run automation tests, and read live editor state — instead of guessing from source files.

Plugin location in the engine: `Engine/Plugins/Experimental/ModelContextProtocol`.

**Status: Experimental.** The `.uplugin` sets `"IsExperimentalVersion": true`, `"EnabledByDefault": false`, `"NoRedist": true`. Epic's docs warn the feature is incomplete in places and that APIs and data formats may change. Treat it as a power tool, not infrastructure.

## Ground truth rule

Everything below was read out of a UE 5.8.1 source tree. Verify against your own engine before quoting:

```bash
cat  Engine/Plugins/Experimental/ModelContextProtocol/ModelContextProtocol.uplugin
cat  Engine/Plugins/Experimental/ModelContextProtocol/Source/ModelContextProtocolEngine/Public/ModelContextProtocolSettings.h
ls   Engine/Plugins/Experimental/Toolsets/
grep -rhoE '"ModelContextProtocol\.[A-Za-z]+"' Engine/Plugins/Experimental/ModelContextProtocol/Source/ | sort -u
```

## Setup

**1. Enable two plugins** — Edit → Plugins:

| Plugin | Why |
|---|---|
| **Unreal MCP** (`ModelContextProtocol`) | the server itself |
| **All Toolsets** (`AllToolsets`) | the actual tools. Without it the server runs and exposes nothing useful |

`ToolsetRegistry` and `EngineAssetDefinitions` are pulled in automatically as plugin dependencies. Restart the editor.

⚠️ **`AllToolsets` is not all toolsets.** In 5.8.1 there are 26 toolset plugins on disk and the aggregator depends on only **21**. These five must be enabled by hand if you want them:

```
ChaosClothAssetToolset, LiveCodingToolset, MetaHumanGenerator,
MVVMToolset, SequencerAnimMixerToolset
```

Verify for your engine — the list will drift:

```bash
ls Engine/Plugins/Experimental/Toolsets/          # what exists
grep '"Name"' Engine/Plugins/Experimental/Toolsets/AllToolsets/AllToolsets.uplugin
```

`AllToolsets` itself has no `Modules` — it is a pure aggregator, so it has no binaries and never needs building.

**2. Start the server.** It does **not** auto-start — `bAutoStartServer` defaults to `false`:

```
ModelContextProtocol.StartServer
```

Default endpoint: `http://127.0.0.1:8000/mcp`

**3. Generate the client config:**

```
ModelContextProtocol.GenerateClientConfig ClaudeCode
```

Accepts `ClaudeCode`, `Cursor`, `VSCode`, `Gemini`, `Codex`, or `All`. Writes `.mcp.json` to the project root. Launch the agent CLI **from that directory** so it picks the config up.

**4. Verify** — `/mcp` in Claude Code should list the Unreal server as connected. If not, the editor isn't running, the server wasn't started, or you launched from the wrong directory.

## Settings

`UModelContextProtocolSettings` — Edit → Editor Preferences → General → **Model Context Protocol**.

Config file is `EditorPerProjectUserSettings`, so the ini section is:

```ini
; Config/DefaultEditorPerProjectUserSettings.ini
[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]
bAutoStartServer=True
ServerPortNumber=8000
ServerUrlPath=/mcp
bEnableToolSearch=True
```

| Setting | Default | Meaning |
|---|---|---|
| `ServerUrlPath` | `/mcp` | URL base path. Invalid paths are silently replaced with the default and logged |
| `ServerPortNumber` | `8000` | change it if 8000 is taken — two editors cannot share a port |
| `bAutoStartServer` | **`False`** | start the server on module startup instead of by console command |
| `bEnableToolSearch` | **`True`** | see below — this one materially changes agent behaviour |

### `bEnableToolSearch` — leave it on

With it **on** (default), `tools/list` returns only three tools: `list_toolsets`, `describe_toolset`, `call_tool`. The agent discovers what exists on demand and dispatches through `call_tool`.

With it **off**, every tool from every enabled toolset is registered natively at startup. With `AllToolsets` enabled that is a very large tool list injected into context on every request.

Turn it off only when debugging a specific tool's schema.

## Console commands (verified in 5.8.1)

| Command | Use |
|---|---|
| `ModelContextProtocol.StartServer [port]` | start on demand; optional port override |
| `ModelContextProtocol.StopServer` | stop it — do this before a long PIE/profiling session you don't want touched |
| `ModelContextProtocol.GenerateClientConfig <Client>` | write `.mcp.json` for ClaudeCode / Cursor / VSCode / Gemini / Codex / All |
| `ModelContextProtocol.RefreshTools` | reload the tool registry after authoring or editing tools |
| `ModelContextProtocol.ToolCall` | invoke a tool from the console — the way to test a tool without an agent |
| `ModelContextProtocol.SessionStart` / `.SessionEnd` | session lifecycle |
| `ModelContextProtocol.PaginationPageSize` | page size for paginated results — lower it if responses blow up context |
| `ModelContextProtocol.ProgressIntervalSeconds` | progress notification cadence for long tools |
| `ModelContextProtocol.EnableAnalytics` | analytics toggle |
| `ModelContextProtocol.WrapPODToolResultsInObject` | result shape for plain-data returns |
| `ModelContextProtocol.AudioResultOggFormat` | audio result encoding |

## Security — read before enabling

- **No authentication.** None. Anything that can reach the port can drive the editor.
- **Loopback only by default.** The listener binds per `[HTTPServer.Listeners] DefaultBindAddress` (default `localhost`), and the server rejects non-loopback `Origin` headers.
- **Do not expose it beyond localhost.** Epic states it is not designed for remote use. Binding it to `0.0.0.0` hands your editor — and by extension your machine — to the network.
- **Transports:** HTTP and Server-Sent Events only. No stdio, no WebSocket.
- The agent is operating on **your live project**. Destructive edits are real edits.

Practical rules when working over MCP:

1. **Commit or stash before an agent-driven editing session.** git is the undo you can trust; the editor's undo stack is not.
2. **Read-only first.** Inspect state, report findings, propose a plan — then make changes on approval.
3. **Stop the server** during profiling runs and long PIE sessions. Tool calls perturb what you're measuring.
4. Never enable auto-start on a shared or build machine.

## What this changes about how to work

With MCP connected, prefer **asking the editor** over inferring from files:

| Task | Without MCP | With MCP |
|---|---|---|
| "Why is this widget laid out wrong?" | read the Blueprint asset blind | inspect the live Slate tree (`SlateInspectorToolset`) |
| "Is this actor's setting right?" | grep the .uasset — impossible | read the property off the live actor |
| "Does this change work?" | ask the user to test | run the automation test (`AutomationTestToolset`) |
| "What's in this level?" | guess from names | enumerate actors |

That said: MCP is not a profiler and not a substitute for measurement. `stat unit`, Unreal Insights, and `ProfileGPU` still own performance work — see the `ue-performance` skill. Use MCP to *set up* and *inspect*, not to claim a frame-time result.

## Toolsets

26 toolset plugins ship in `Engine/Plugins/Experimental/Toolsets/` (5.8.1). `AllToolsets` enables 21 of them — see the warning in Setup; you can also enable individual ones to keep the surface small.

Highest-value ones, and which of the other skills they pair with:

| Toolset | Pairs with |
|---|---|
| `EditorToolset` | everything — actors, levels, assets |
| `SlateInspectorToolset`, `UMGToolSet`, `MVVMToolset` | `ue-ui` |
| `AutomationTestToolset` | `ue-performance`, verification of any change |
| `StateTreeToolset`, `AIModuleToolset`, `WorldConditionsToolset` | AI/behaviour work |
| `NiagaraToolsets`, `PCGToolset`, `PhysicsToolsets`, `ChaosClothAssetToolset` | VFX, procedural content, sim |
| `GASToolsets` | Gameplay Ability System |
| `ConfigSettingsToolset` | reading/writing project settings — including the cvars the other skills discuss |
| `SemanticSearchToolset` | finding assets by meaning rather than name |
| `LiveCodingToolset` | C++ iteration without restarting the editor |

Full list with notes: [references/toolsets.md](references/toolsets.md).

## Custom tools

**Python (fastest path).** Drop a module in `Content/Python/`:

```python
import unreal

@unreal.uclass()
class MyProjectToolset(unreal.ToolsetDefinition):
    pass

@toolset_registry.tool_call
def get_unit_grid_state(level_name: str) -> str:
    """Return the current grid occupancy for a level.

    Args:
        level_name: Name of the level to inspect.
    """
    ...
```

Type hints and Google-style docstrings become the tool schema — they are not documentation, they are the interface the agent sees. Vague docstrings produce a tool the agent misuses.

**C++:**

```cpp
UCLASS(BlueprintType, Hidden)
class UMyProjectToolset : public UToolsetDefinition
{
    GENERATED_BODY()
public:
    /** Return the current grid occupancy for a level.
     *  @param LevelName Name of the level to inspect.
     */
    UFUNCTION(meta = (AICallable))
    static FString GetUnitGridState(const FString& LevelName);
};
```

Doc comments drive schema reflection here too.

After authoring either kind:

```
ModelContextProtocol.RefreshTools
```

Test with `ModelContextProtocol.ToolCall` before involving an agent — that isolates tool bugs from prompting problems.

**When a custom tool is worth writing:** when the agent repeatedly needs a project-specific fact that no generic toolset exposes (turn state, grid occupancy, a custom subsystem's status). Do not wrap things `EditorToolset` already does.

## Parallel sessions on one editor

Several agent sessions (and the human) can share one editor. Calls are serialised on the game thread, and a few
operations change the editor for everyone:

| Exclusive (lock) | Lock-free |
|---|---|
| start/stop PIE, Live Coding, load level, Build.bat/UBT, closing the editor, commandlets | reading anything, editing **your own** assets with an immediate save, scene snapshots, captures |

- **A PIE running while the lock is free is the human's — never stop it.**
- **Live Coding patches every source newer than the DLL** — a peer's half-written header too — and can crash the
  editor for everyone. With several sessions editing C++: take the lock, full build with the editor closed.
- **`-game` runs load the last full build**, never Live Coding patches.
- The lock is a **file + Claude Code hook**, not an MCP tool: the exclusive ops (build, close, commandlets) happen
  while the editor is down, and MCP calls carry no session identity — hook events carry `session_id`.
  Opt-in hook: [`hooks/editor-lock.py`](hooks/editor-lock.py); settings snippet, tuning and a pipe test in
  [references/parallel-sessions.md](references/parallel-sessions.md).

## Seeing the scene — scene probe

The agent cannot see the viewport. Give it numbers: [`templates/SceneProbe/`](templates/SceneProbe/) is a
`UTickableWorldSubsystem` (Game + PIE) plus an `Agent.SceneState [filter] [file]` command that writes
`Saved/AgentRuns/<file>.json`: camera and cuts (detected by view jumps), every character's anim state,
`WasRecentlyRendered`, head position on screen, gap to the floor, and warnings (T-pose, floating, focus actor
off-screen). An optional `RunConsole` MCP tool (editor module) runs it from the agent.

- **Write a file, always.** A console-running tool returns the command's output device, not `UE_LOG` text.
- **Two snapshots seconds apart** reveal a frozen clip; one never can.
- New `UCLASS` → **full build**, not Live Coding.
- Check scenes yourself before showing the human. Details and recipes: [references/scene-probe.md](references/scene-probe.md).

## Troubleshooting

| Symptom | Cause |
|---|---|
| Server listed but no useful tools | `AllToolsets` (or specific toolsets) not enabled |
| Client can't connect | server not started (`bAutoStartServer` is `False` by default) |
| Connects from one directory, not another | `.mcp.json` is per-directory; launch the CLI from the project root |
| Port in use | second editor instance — change `ServerPortNumber` |
| Custom tool doesn't appear | `ModelContextProtocol.RefreshTools` not run, or the Python module isn't under `Content/Python/` |
| Tool called with wrong arguments | the docstring/doc comment is the schema — make it precise |
| Huge responses eating context | lower `ModelContextProtocol.PaginationPageSize`; confirm `bEnableToolSearch` is on |
| Connection refused from another machine | working as designed — loopback only, non-loopback `Origin` rejected |
| Save "succeeds" but nothing on disk; "Asset does not exist" | PIE running, or Git LFS read-only file — see [references/field-notes.md](references/field-notes.md) |
| Need console/cvars or Python from the agent | no shipped tool — add a project `RunConsole` tool; details in field-notes |
| Another session stopped your PIE / closed the editor | no editor lock — install the hook ([references/parallel-sessions.md](references/parallel-sessions.md)) |
| `RunConsole` returns "no output" for a command that logs | `UE_LOG` is not captured — make the command write a file (scene probe does) |

## Related

- **`ue-performance`** — MCP does not replace `stat unit` / Insights / `ProfileGPU`
- **`ue-ui`** — `SlateInspectorToolset` beats reading widget Blueprints blind
- **`ue-assets`** — inspect imported meshes' live settings instead of inferring
- [references/toolsets.md](references/toolsets.md) — the full 27-toolset list
- [references/field-notes.md](references/field-notes.md) — verified pitfalls: calling, saving, materials, Niagara, capture, Live Coding, Python
- [references/parallel-sessions.md](references/parallel-sessions.md) — several sessions on one editor, the lock hook
- [references/scene-probe.md](references/scene-probe.md) — scene-state JSON for the agent, template usage, recipes
- **`agent-workflow`** — the retro loop that produced the lock and the probe

## Field notes from other projects

`field-notes/` next to this file (when present) holds lessons from other agents' retros, one per file. Before
debugging a symptom, `grep -ril "<symptom words>" field-notes/`. `status: observed` means seen in practice but not
yet checked against source — verify before relying on it; once checked, promote it into the tables above.
