---
name: retro
description: Close a work session or an accepted task with a retro — count the rounds of corrections, name a cause for each, turn every cause into a change (skill row, rule, hook, tool), keep what worked as a written practice, clean expired memory, log the task in the journal, commit shared-skill changes, and report in one line. Invoked by the human as /retro [task or note]; it runs the retro procedure of the agent-workflow skill.
license: MIT
disable-model-invocation: true
argument-hint: "[task or what to focus on]"
metadata:
  scope: "engine-agnostic; any long-running project with a human author"
---

# /retro — close the session so the next one starts smarter

The human typed `/retro`. Focus, if given: **$ARGUMENTS**. Otherwise cover every significant task of this session
(more than one round, touched a pipeline, or the human was surprised).

Load the `agent-workflow` skill first and follow its Retro section; this file is the checklist and the order.

## Steps — do them, don't describe them

1. **Facts first.** `git status --short`, `git log --oneline` for the session — what actually landed, what is still
   uncommitted, what was abandoned. Memory and chat are claims; git is the record.
2. **Rounds.** For each task: how many times the human sent the work back. Quote their words, not your summary.
3. **One cause per round**, classed: didn't check the result myself · missing knowledge · misread intent ·
   tool in the way · process collision. "I should be more careful" is not a cause.
4. **What worked.** Approaches that landed on the first try or that the human praised. A practice that is not
   written down is lost — it gets the same treatment as a mistake.
5. **Make the changes now**, one per cause and one per kept practice:

   | Lesson applies to | Goes into | Then |
   |---|---|---|
   | any project / any user of the tool or engine | the **shared skills repo** — a row in the matching skill, or a new skill | commit and push it (step 7) |
   | this project only | the project's skill or CLAUDE.md | leave uncommitted for the human, unless they said otherwise |
   | how this human likes to work | auto-memory, `feedback` note with **Why** / **How to apply** | — |
   | enforceable (order of steps, forbidden command, collisions) | a hook or a script, not a note | — |

   Shared-repo text must stand alone: no project names, character names, personal paths, ids or secrets —
   state the lesson so a stranger on a different project can use it, with its source (path, doc URL, measurement).

6. **Memory hygiene.** State notes for accepted work → delete (the facts are in git/docs). Notes contradicted by git
   → fix or delete. Lessons sitting in memory that help any project → move into a skill. Index stays one line per note.
7. **Commit shared skills.** In the skills repo: stage the changed files by name, one commit per topic, message says
   what the agent will now do differently; push. Do not commit the project repo unless the human asked.
8. **Journal.** `python ~/.claude/skills/agent-workflow/scripts/journal.py add --project <p> --area <a> --task "…"
   --rounds N --causes "…" --changes "kind:target what; …"` — one entry per task. `changes` empty with rounds > 0
   means the retro is not done.
9. **Report** — a few lines, no essay:
   ```
   <task>: N rounds — main cause; changed: <kind:target>, …
   Kept: <practice> → <where it is written now>
   Memory: −K stale notes, +M; skills repo: <commit hash> pushed
   Open: <anything that needs the human's decision>
   ```

If the session had nothing significant: say so in one line, still do steps 6 and 8 for what was done.
