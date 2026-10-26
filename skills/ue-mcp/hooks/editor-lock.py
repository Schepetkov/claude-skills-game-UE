#!/usr/bin/env python3
"""Editor lock for several Claude Code sessions sharing one Unreal editor.

Why a file and a hook, not an MCP tool: the exclusive operations (closing the editor, Build.bat, commandlets)
happen exactly when the editor - and its MCP server - is gone, and an MCP call carries no session identity,
while every hook event carries `session_id`.

  pre       PreToolUse: an exclusive operation takes the lock for this session, or is denied while another
            live session holds it.
  post      PostToolUse / PostToolUseFailure: the operation is over - release, except a started PIE and a closed
            editor, which hold the lock until PIE is stopped / the project is rebuilt, or the TTL runs out.
  status    print the lock (by hand).
  release   drop the lock whoever holds it (by hand, after a crashed session).

A PIE that runs while nobody holds the lock is the human's own - never stop it.

Where the lock lives (first that applies):
  UE_EDITOR_LOCK_FILE   full path of the lock file
  UE_PROJECT_DIR        directory holding the .uproject -> <dir>/Saved/AgentLock.json
  otherwise             the first *.uproject found under $CLAUDE_PROJECT_DIR (or cwd), up to 2 levels deep
                        -> <its dir>/Saved/AgentLock.json; no .uproject -> $CLAUDE_PROJECT_DIR/.claude/editor-lock.json
UE_MCP_TOOL_PREFIX      tool-name prefix of the Unreal MCP server (default mcp__unreal__ - the server key in .mcp.json)

Python 3 standard library only. Edit OPS below to match your project's tool names.
"""

import json
import os
import re
import sys
import time

MCP_PREFIX = os.environ.get("UE_MCP_TOOL_PREFIX", "mcp__unreal__")
SHELL_TOOLS = ("Bash", "PowerShell")

# (operation, regex over the tool input, lock seconds, holds after the call, the held operation it ends)
# MCP patterns are matched against the JSON of call_tool's input (toolset, tool name, arguments).
MCP_OPS = [
    ("pie-start", r"(start|begin|request|launch)_?(pie|play)|play_?in_?editor", 1200, True, None),
    ("pie-stop", r"(stop|end)_?(pie|play)", 60, False, "pie-start"),
    ("live-coding", r"live_?coding|compile_?live", 600, False, None),
    ("load-level", r"(load|open)_?(level|map)", 300, False, None),
]
SHELL_OPS = [
    ("build", r"\bBuild(Editor)?\.(bat|sh)\b|RunUAT|UnrealBuildTool", 1800, False, "close-editor"),
    ("close-editor", r"CloseMainWindow|(Stop-Process|taskkill|pkill|killall)[^\n]*Unreal", 1800, True, None),
    ("commandlet", r"UnrealEditor-Cmd|UnrealEditor(\.exe)?\"?[^\n]*\s-run=", 1800, False, None),
]

SKIP_DIRS = {".git", ".claude", "Content", "Binaries", "Intermediate", "Saved", "DerivedDataCache", "Plugins",
             "node_modules", "Build", ".vs", ".idea"}


def project_root():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def find_uproject_dir(root, depth=2):
    try:
        entries = sorted(os.scandir(root), key=lambda e: e.name)
    except OSError:
        return None
    if any(e.is_file() and e.name.endswith(".uproject") for e in entries):
        return root
    if depth == 0:
        return None
    for e in entries:
        if e.is_dir() and e.name not in SKIP_DIRS and not e.name.startswith("."):
            found = find_uproject_dir(e.path, depth - 1)
            if found:
                return found
    return None


def lock_path():
    explicit = os.environ.get("UE_EDITOR_LOCK_FILE")
    if explicit:
        return explicit
    uproject_dir = os.environ.get("UE_PROJECT_DIR") or find_uproject_dir(project_root())
    if uproject_dir:
        return os.path.join(uproject_dir, "Saved", "AgentLock.json")
    return os.path.join(project_root(), ".claude", "editor-lock.json")


def now():
    return int(time.time())


def read_lock(path):
    try:
        with open(path, encoding="utf-8") as f:
            lock = json.load(f)
        return lock if lock.get("expires", 0) > now() else None
    except (OSError, ValueError):
        return None


def write_lock(path, lock):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def drop_lock(path):
    try:
        os.remove(path)
    except OSError:
        pass


def classify(event):
    tool = event.get("tool_name", "")
    if tool.startswith(MCP_PREFIX):
        ops = MCP_OPS
    elif tool in SHELL_TOOLS:
        ops = SHELL_OPS
    else:
        return None
    text = json.dumps(event.get("tool_input", {}), ensure_ascii=False)
    for op in ops:
        if re.search(op[1], text, re.IGNORECASE):
            return op
    return None


def describe(lock):
    left = max(0, lock["expires"] - now())
    since = time.strftime("%H:%M:%S", time.localtime(lock["since"]))
    held = f', holding {lock["held"]}' if lock.get("held") and lock["held"] != lock["reason"] else ""
    return (f'{lock["reason"]}{held} by session {lock["owner"][:8]} ({lock.get("cwd") or "?"}) since {since}, '
            f'{left // 60} min {left % 60} s left')


def pre(event):
    op = classify(event)
    if not op:
        return
    name, _, ttl, keep, _ = op
    session = event.get("session_id", "?")
    path = lock_path()
    lock = read_lock(path)
    if lock and lock["owner"] != session:
        reason = (f"Unreal editor is locked: {describe(lock)}. Do work that needs no exclusive editor access "
                  f"(reading, your own assets saved right away) or wait; never stop a PIE you did not start. "
                  f'Crashed holder: python "{os.path.abspath(__file__)}" release')
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
        return
    held = lock.get("held") if lock else None
    if keep:
        held = name
    write_lock(path, {
        "owner": session,
        "reason": name,
        "held": held,
        "since": lock["since"] if lock else now(),
        "expires": max(lock["expires"] if lock else 0, now() + ttl),
        "cwd": event.get("cwd", ""),
    })


def post(event):
    op = classify(event)
    if not op:
        return
    name, _, _, keep, ends = op
    path = lock_path()
    lock = read_lock(path)
    if not lock or lock["owner"] != event.get("session_id"):
        return
    failed = event.get("hook_event_name") == "PostToolUseFailure"
    held = lock.get("held")
    if failed and keep and held == name:
        held = None          # PIE did not start / the editor did not close
    elif not failed and ends and held == ends:
        held = None          # PIE stopped / project rebuilt after closing the editor
    if held:
        lock.update(reason=held, held=held)
        write_lock(path, lock)
    else:
        drop_lock(path)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "status":
        lock = read_lock(lock_path())
        print(f"{lock_path()}: " + (describe(lock) if lock else "free"))
        return
    if mode == "release":
        drop_lock(lock_path())
        print("released")
        return
    if mode not in ("pre", "post"):
        print("usage: editor-lock.py pre|post|status|release", file=sys.stderr)
        sys.exit(1)
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return  # never block a tool call over a malformed event
    (pre if mode == "pre" else post)(event)


if __name__ == "__main__":
    main()
