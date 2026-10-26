# Retro — template and examples

## Template (fill in before telling the human the task is done)

```
Task:     <one line>
Rounds:   <N>  (times the human sent it back)
Causes:   1. <round 1 — why>   2. <round 2 — why> ...
Learned:  <what the skills / CLAUDE.md did not say and should have>
In the way: <tool, process, environment friction>
Changes:  <kind>:<target> <what>   (one per cause; "none" only when rounds = 0 and nothing got in the way)
Journal:  journal.py add ... (done)
```

Then one line to the human: *"3 rounds — mostly I didn't look at the shot myself; added a scene-state check after
every cut to the cinematics skill."*

## Cause → change mapping

| Cause, as written in the journal | Change that removes it | Kind |
|---|---|---|
| "didn't look at the result myself" | a tool that shows it (scene state JSON, screenshot, test) + a step "check before showing" in the skill | tool, skill |
| "didn't know API X behaves like Y" | a symptom → cause row in the skill, with the source path | skill |
| "the human wanted something else" | show a sketch / 2–3 options before building; write the agreed intent into the task | rule |
| "another session stopped my PIE / closed the editor" | a lock hook; never a "please be careful" note | hook |
| "the build ran on a dirty tree" | build from a clean worktree, scripted | tool |
| "memory said X was done, it wasn't" | delete the stale note; verify against git before trusting (memory hygiene) | memory |
| "the same fix was needed in three places" | fix the root once, then remove the patches | code |
| "waited for a slow step" | measure it; script or parallelize it; or batch it at the end | tool |

A cause that recurs in `journal.py stats` after a change was made means the change did not work — revisit it,
don't stack a second note on top.

## What does *not* count as a change

- "I will be more careful next time." There is no next-time memory of carefulness.
- A paragraph in chat. The next session never sees it.
- A memory note for a lesson that applies to any project — that belongs in a skill.
- A rule nobody enforces when a hook could (collisions, forbidden commands, required order of steps).

## Example 1 — cinematics, 4 rounds

```
Task:     dialogue scene before the first level
Rounds:   4
Causes:   1. speaker's head out of frame on line 3   2. camera crossed the 180° line on the reverse
          3. same — fixed one cut, broke another   4. character floating 8 cm above the floor
Learned:  the agent never looked at the frames; every defect was visible in a snapshot
In the way: no way to read "what is on screen" without a human screenshot
Changes:  tool:scene-probe (camera, cuts, heads on screen, floor gap, warnings)
          skill:ue-cinematics "check every cut by numbers before showing"
```

Next scene in the area: 1 round (a taste note on the lens). The journal shows it.

## Example 2 — parallel sessions, 2 incidents

```
Task:     two features in parallel on one editor
Rounds:   2 (not the human's — the sessions broke each other)
Causes:   1. session B closed the editor for a full build while session A was in PIE
          2. Live Coding from A patched B's half-written header; editor crashed
Changes:  hook:editor-lock (file lock on PIE/build/close/Live Coding, session_id from the hook)
          rule:"PIE running with the lock free is the human's — never stop it"
          skill:ue-mcp parallel sessions section
```
