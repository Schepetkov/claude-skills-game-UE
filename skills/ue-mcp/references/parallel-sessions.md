# Parallel agent sessions on one editor

Several Claude Code sessions (and the human) can share one open editor over MCP. Most of the time that works.
It breaks on a small set of operations that change the editor for everyone — and when it breaks, it breaks
someone else's work: a stopped PIE, a closed editor with unsaved edits, a Live Coding patch that crashes the process.

## How MCP calls behave with several clients

- Every tool call runs on the **game thread**, one at a time. A long call (material recompile, capture, level load,
  Niagara system edit) stalls every other session's calls until it returns.
- A **modal dialog** (Save Content, Overwrite Existing Object, Blueprint Compilation Error) blocks the game thread:
  MCP hangs for everyone until a human clicks it.
- MCP requests carry **no caller identity** the editor could use to arbitrate. The server cannot tell sessions apart.
- The editor's **undo stack and dirty packages are shared**. A peer's `save_assets []` saves your dirty assets too.

## Exclusive vs lock-free operations

| Exclusive — take the lock | Why |
|---|---|
| Start / stop PIE | one PIE per editor; stopping someone's PIE kills their test (or the human's play session) |
| Live Coding compile | patches **every** source newer than the loaded DLL — including another session's half-written files — and can crash the editor for everyone |
| Load / open a level | swaps the editor world under every session |
| Build.bat / UBT / RunUAT | needs the editor closed for header changes; holds the Live Coding mutex otherwise |
| Closing or restarting the editor | takes everyone's MCP and unsaved in-memory edits with it |
| Commandlets (`UnrealEditor-Cmd -run=…`) | write packages the editor has loaded; run with the editor closed |

| Lock-free | Notes |
|---|---|
| Reading: list/describe actors, properties, assets, Slate tree, logs | the bulk of agent work |
| Editing **your own** assets | save right after each edit and check the bytes on disk; one owner per map/asset — ask the owner otherwise |
| Scene snapshots (`Agent.SceneState`, see [scene-probe.md](scene-probe.md)) | read-only, works in whoever's PIE is running |
| Screenshots / captures | serialised with everything else; keep them few |

## The rules

1. **A PIE running while the lock is free belongs to the human. Never stop it.** Wait, or work lock-free.
2. **No Live Coding while more than one session edits C++.** Take the lock and do a full build with the editor
   closed instead. Live Coding also keeps function-local statics of the old module and does not survive a restart.
3. **`-game` runs load the DLLs of the last full build** — they never see Live Coding patches. Verify a C++ change
   in `-game` only after a full build.
4. Denied by the lock → do lock-free work (read, plan, edit your own assets) or wait. Don't poll the lock in a loop.
5. Save in-editor edits right after making them. A peer closing the editor takes unsaved edits with it.

## Why a file + hook, not an MCP tool

- The exclusive operations that matter most — Build.bat, closing the editor, commandlets — happen **when the
  editor is down**, so a lock living in the editor (or behind its MCP server) does not exist exactly when needed.
- An MCP call carries no session identity; a Claude Code **hook event carries `session_id`**, `cwd`, the tool
  name and its full input. The hook can tell who is asking and deny with a reason the agent reads.
- A file in the project's `Saved/` survives editor restarts and is visible to every session on the machine.

## The hook

`hooks/editor-lock.py` in this skill (Python 3 stdlib). Modes: `pre` (PreToolUse), `post` (PostToolUse and
PostToolUseFailure), `status`, `release`.

- **pre**: classifies the call by regex (MCP: start/stop PIE, Live Coding, load level; shell: Build.bat/UBT/RunUAT,
  closing the editor, commandlets). Lock free or ours → take/extend it. Held by another live session → deny with
  "who, what, since when, how long left".
- **post**: release — except after a successful PIE start or editor close, which **hold** the lock until PIE stops
  or the project is rebuilt (or the TTL runs out). A failed PIE start releases at once. A build inside your own PIE
  does not drop the PIE hold.
- **TTL** per operation (PIE 20 min, build/close 30 min) — a crashed session's lock expires on its own;
  `python editor-lock.py release` drops it by hand.

Lock file: `UE_EDITOR_LOCK_FILE`, else `<dir of the .uproject>/Saved/AgentLock.json` (found under
`$CLAUDE_PROJECT_DIR` up to two levels deep, or `UE_PROJECT_DIR`), else `$CLAUDE_PROJECT_DIR/.claude/editor-lock.json`.
MCP tool prefix: `UE_MCP_TOOL_PREFIX` (default `mcp__unreal__` — the server key in `.mcp.json` is `unreal`).

### Install (opt-in, per project)

Copy the hook into the project so every teammate's session gets it:

```bash
mkdir -p .claude/hooks && cp ~/.claude/skills/ue-mcp/hooks/editor-lock.py .claude/hooks/
```

Add to the project's `.claude/settings.json` (merge with existing `hooks`):

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "mcp__unreal__call_tool|Bash|PowerShell",
        "hooks": [{ "type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/editor-lock.py\" pre", "timeout": 10 }] }
    ],
    "PostToolUse": [
      { "matcher": "mcp__unreal__call_tool|Bash|PowerShell",
        "hooks": [{ "type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/editor-lock.py\" post", "timeout": 10 }] }
    ],
    "PostToolUseFailure": [
      { "matcher": "mcp__unreal__call_tool|Bash|PowerShell",
        "hooks": [{ "type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/editor-lock.py\" post", "timeout": 10 }] }
    ]
  }
}
```

- `python` must resolve to Python 3 (`python3` on most Linux/macOS). On Windows, if your hooks run in PowerShell,
  add `"shell": "bash"` to each hook entry so `$CLAUDE_PROJECT_DIR` expands (Git Bash).
- With `bEnableToolSearch` off, tools are registered natively (`mcp__unreal__<tool>`): widen the matcher to `mcp__unreal__.*`.
- Add the lock to the project's CLAUDE.md in two lines: what is exclusive, and "PIE with the lock free = the human's".

### Tune it

- Edit `MCP_OPS` / `SHELL_OPS` at the top of the hook: your project's console tool may start PIE or open maps
  through other names (e.g. `RunConsole("open MyMap")` is not caught by the default `load-level` pattern).
- Classification is a regex over the call's text: a `grep Build.bat` also counts as a build. Harmless while the
  lock is free; denied while a peer holds it.
- Two hooks firing in the same millisecond can both see "free" — the file is replaced atomically, but there is no
  compare-and-swap. In practice the next exclusive call sees the winner.

### Pipe-test it

```bash
H=.claude/hooks/editor-lock.py
ev() { printf '{"session_id":"%s","hook_event_name":"%s","tool_name":"%s","tool_input":%s}' "$@"; }
ev A PreToolUse  mcp__unreal__call_tool '{"tool_name":"StartPIE"}' | python $H pre    # takes the lock
ev A PostToolUse mcp__unreal__call_tool '{"tool_name":"StartPIE"}' | python $H post   # PIE holds it
ev B PreToolUse  Bash '{"command":"Build.bat MyGameEditor Win64 Development"}' | python $H pre   # -> deny JSON
ev A PreToolUse  mcp__unreal__call_tool '{"tool_name":"StopPIE"}'  | python $H pre
ev A PostToolUse mcp__unreal__call_tool '{"tool_name":"StopPIE"}'  | python $H post   # released
ev B PreToolUse  Bash '{"command":"Build.bat MyGameEditor Win64 Development"}' | python $H pre   # allowed
python $H status; python $H release
```

## Running checks in parallel

- Verification runs are better as **`-game` processes** than as a second editor: `-game -windowed -ResX=1280 -ResY=720`,
  scalability Medium, a separate `-log=<name>.log`, and don't let them write the human's `GameUserSettings.ini`.
- The GPU is usually the bottleneck, not CPU: measure one process's VRAM before running several. One editor with a
  realtime viewport can hold most of a high-end card.
- A second editor on port 8001 works for MCP (see field notes) but writes the same packages — avoid for editing.
- Don't launch `-game` or commandlets while the human is actively working in the editor — they compete for the GPU
  and the shader/DDC caches.
