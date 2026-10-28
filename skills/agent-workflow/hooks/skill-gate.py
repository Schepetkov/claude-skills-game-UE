#!/usr/bin/env python3
"""Claude Code hook: the skills that match a task are loaded BEFORE any work on it.

Why: an agent that answers from memory instead of loading the project's skills improvises one-off scripts where the
skill already has a tool and a recipe; "load the skill first" written in CLAUDE.md was not enough - a gate is.

  prompt  (UserPromptSubmit): routes the human's words to skills (routes file) and adds them to the session's
          required set; injects the list into the context.
  pre     (PreToolUse, matcher "*"): denies every tool except the exempt ones while a required skill is not loaded;
          a Skill call marks its skill loaded.

Routes file: $CLAUDE_PROJECT_DIR/.claude/skill-routes.json (or SKILL_ROUTES=<path>):
  {"routes":  {"<skill>": ["stem", "=wholeword", ...]},   # lowercase; a stem matches at a word start
   "implies": {"<skill>": ["<also required>"]},            # e.g. asset work also needs the editor-tools skill
   "exempt":  ["Skill", "ToolSearch", "AskUserQuestion"]}  # tools never gated
Settings:
  "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python \".../skill-gate.py\" prompt"}]}],
  "PreToolUse":       [{"matcher": "*", "hooks": [{"type": "command", "command": "python \".../skill-gate.py\" pre"}]}]
State: <tmp>/skill-gate/<session_id>.json. Standard library only. Subagent calls (agent_id set) are not gated.
Pipe test:  echo '{"session_id":"t","prompt":"the sword is far from the hand"}' | python skill-gate.py prompt
"""
import json, os, re, sys, tempfile

STATE_DIR = os.path.join(tempfile.gettempdir(), "skill-gate")
DEFAULT_EXEMPT = ["Skill", "ToolSearch", "AskUserQuestion", "TodoWrite"]


def config():
    path = os.environ.get("SKILL_ROUTES") or os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "skill-routes.json")
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except Exception:
        c = {}
    return c.get("routes", {}), c.get("implies", {}), set(c.get("exempt", DEFAULT_EXEMPT))


def state_path(sid):
    return os.path.join(STATE_DIR, re.sub(r"[^A-Za-z0-9_-]", "_", sid or "nosession") + ".json")


def load(sid):
    try:
        with open(state_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"required": [], "loaded": []}


def save(sid, st):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(state_path(sid), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False)


def bare(name):
    name = (name or "").strip().lstrip("/")
    return name.split(":")[-1].split()[0] if name else ""


def hits(stem, t):
    if stem.startswith("="):
        return re.search(r"(?<!\w)" + re.escape(stem[1:]) + r"(?!\w)", t) is not None
    return re.search(r"(?<!\w)" + re.escape(stem), t) is not None


def route(text, routes, implies):
    t = text.lower()
    hit = [s for s, stems in routes.items() if any(hits(st, t) for st in stems)]
    for s in list(hit):
        for extra in implies.get(s, []):
            if extra not in hit:
                hit.insert(0, extra)
    return hit


def on_prompt(data):
    routes, implies, _ = config()
    sid, text = data.get("session_id"), data.get("prompt") or ""
    st = load(sid)
    m = re.match(r"\s*/([\w:-]+)", text)                     # the human typed /skill - it is being loaded
    if m:
        st["loaded"] = sorted(set(st["loaded"]) | {bare(m.group(1))})
    st["required"] += [s for s in route(text, routes, implies) if s not in st["required"]]
    save(sid, st)
    missing = [s for s in st["required"] if s not in st["loaded"]]
    msg = ("SKILL GATE: first action of this turn = load these skills with the Skill tool, before any other tool: "
           + ", ".join(missing) + ". Other tools are denied until they are loaded; then use their tools and recipes."
           if missing else
           "SKILL GATE: no new skill matched. If the task touches a skill's area, load it before working; if none fits, say so.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}, ensure_ascii=False))


def on_pre(data):
    _, _, exempt = config()
    sid, tool = data.get("session_id"), data.get("tool_name") or ""
    st = load(sid)
    if tool == "Skill":
        name = bare((data.get("tool_input") or {}).get("skill"))
        if name:
            st["loaded"] = sorted(set(st["loaded"]) | {name})
            save(sid, st)
        return
    if tool in exempt or data.get("agent_id"):
        return
    missing = [s for s in st["required"] if s not in st["loaded"]]
    if missing:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": "SKILL GATE: load the skills for this task first (Skill tool): " + ", ".join(missing)}},
            ensure_ascii=False))


if __name__ == "__main__":
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except Exception:
        payload = {}
    {"prompt": on_prompt, "pre": on_pre}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda d: None)(payload)
