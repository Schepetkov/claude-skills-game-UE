#!/usr/bin/env python3
"""Claude Code SessionStart hook: keep the shared skills current in every session.

  1. `git pull --ff-only` in the skills repo (main is protected: only reviewed PRs land there)
  2. names the files that run code (hooks/, scripts/, templates/, install.*) if the pull changed any,
     so the agent shows them to the human before running them
  3. lists skills that are in the repo but not linked into ~/.claude/skills
  4. prints the result as additionalContext for the session

Settings (user ~/.claude/settings.json or project .claude/settings.json):

  "hooks": { "SessionStart": [ { "hooks": [ { "type": "command",
      "command": "python \"$HOME/.claude/skills/agent-workflow/hooks/session-start-skills.py\"" } ] } ] }

Env: SKILLS_REPO (default ~/Documents/GitHub/claude-skills-game-UE, else the repo this file lives in),
     SKILLS_DIR (default ~/.claude/skills). Standard library only; never fails the session.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

EXECUTABLE = ("/hooks/", "/scripts/", "/templates/", "tools/", "install.")


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "git failed")
    return r.stdout.strip()


def find_repo() -> Path | None:
    env = os.environ.get("SKILLS_REPO")
    candidates = [Path(env).expanduser()] if env else []
    candidates.append(Path.home() / "Documents" / "GitHub" / "claude-skills-game-UE")
    # this file -> agent-workflow/hooks -> skills -> repo (resolves through the install link)
    candidates.append(Path(__file__).resolve().parents[3])
    return next((c for c in candidates if (c / ".git").exists() and (c / "skills").is_dir()), None)


def main() -> None:
    lines: list[str] = []
    repo = find_repo()
    if repo is None:
        lines.append("Shared skills repo not found - set SKILLS_REPO. Using whatever is in ~/.claude/skills.")
    else:
        try:
            before = git(repo, "rev-parse", "--short", "HEAD")
            try:
                git(repo, "pull", "--ff-only", "--quiet")
                after = git(repo, "rev-parse", "--short", "HEAD")
                if before == after:
                    lines.append(f"Shared skills: up to date at {after}.")
                else:
                    log = git(repo, "log", "--format=  %h %s", f"{before}..{after}")
                    lines.append(f"Shared skills: updated {before} -> {after}. New lessons from other agents:")
                    lines.append(log)
                    changed = git(repo, "diff", "--name-only", f"{before}..{after}").splitlines()
                    code = [f for f in changed if any(m in f for m in EXECUTABLE)]
                    if code:
                        lines.append("Files that RUN CODE changed: " + ", ".join(code)
                                     + ". Show the human the diff before running any of them"
                                     + f" (git -C {repo.as_posix()} diff {before}..{after} -- <file>).")
            except RuntimeError:
                lines.append(f"Shared skills: offline or local changes, using local copy at {before}.")
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as e:
            lines.append(f"Shared skills: git unavailable ({e}).")

        dst = Path(os.environ.get("SKILLS_DIR", Path.home() / ".claude" / "skills")).expanduser()
        missing = [p.name for p in sorted((repo / "skills").iterdir())
                   if p.is_dir() and not (dst / p.name / "SKILL.md").exists()]
        if missing:
            lines.append("Skills not installed: " + ", ".join(missing)
                         + f" - tell the human to rerun install from {repo.as_posix()}.")

    lines.append("At the end of a significant task the human types /retro; lessons that help any project "
                 "go back to the shared repo as a pull request (see the retro skill).")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": "\n".join(lines)},
                      "suppressOutput": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # a broken hook must never block a session
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                 "additionalContext": f"Shared skills hook failed: {e}"}}))
