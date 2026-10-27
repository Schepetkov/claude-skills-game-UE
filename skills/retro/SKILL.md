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
   | any project / any user of the tool or engine | the **shared skills repo** — a field note, a row in the matching skill, or a new skill | send it (step 7) |
   | this project only | the project's skill or CLAUDE.md | leave uncommitted for the human, unless they said otherwise |
   | how this human likes to work | auto-memory, `feedback` note with **Why** / **How to apply** | — |
   | enforceable (order of steps, forbidden command, collisions) | a hook or a script, not a note | — |

   Shared-repo text must stand alone: no project names, character names, personal paths, ids or secrets —
   state the lesson so a stranger on a different project can use it, with its source (path, doc URL, measurement).

   **Which form in the shared repo.** First grep the skill and its `field-notes/` for the symptom — extend an
   existing note rather than adding a twin.
   - Checked against engine source, an Epic doc or a measurement → a row in `SKILL.md` / `references/`, with the source.
   - Seen in practice, not checked yet → a **field note**: `skills/<skill>/field-notes/YYYY-MM-DD-short-slug.md`,
     one lesson per file (parallel contributors never conflict). Format:
     ```markdown
     ---
     symptom: what you see, in the words you'd search for
     engine: "5.8.1"            # or the tool and its version
     status: observed           # observed | verified (verified needs source)
     date: 2026-10-27
     source: Engine/Source/... | https://dev.epicgames.com/... | measurement   # optional while observed
     ---
     Cause, the fix or workaround, and how to reproduce — a few lines.
     ```
   - Engine-agnostic working practice → `agent-workflow`.

6. **Memory hygiene.** State notes for accepted work → delete (the facts are in git/docs). Notes contradicted by git
   → fix or delete. Lessons sitting in memory that help any project → move into a skill. Index stays one line per note.
7. **Send shared skills.** In the skills repo (`git -C <repo> ...`; it is where `~/.claude/skills/retro` links to):
   1. `git fetch origin && git switch -c retro/<YYYY-MM-DD>-<slug> origin/main` — never work on `main` itself.
   2. Write the changes; run `python tools/check_skills.py` until it reports 0 errors.
   3. Stage files by name, one commit per topic; the message says what the agent will now do differently.
   4. **Maintainer** (the human has push rights — their memory or CLAUDE.md says so): `git push origin HEAD:main`.
      **Everyone else** — open a pull request:
      - with GitHub CLI (`gh`): once `gh repo fork --remote --remote-name fork`, then
        `git push -u fork HEAD` and `gh pr create --fill` (the PR template asks what changed and where it came from);
      - without it: `git push -u fork HEAD` if a `fork` remote exists and print the "compare" URL for the human;
        if there is no fork yet, tell the human the one-time step: Fork on GitHub, then
        `git remote add fork <their fork URL>`.
   5. `git switch main` — the session-start hook pulls `main`, so leave the repo on it.
   Do not commit the project repo unless the human asked.
8. **Journal.** `python ~/.claude/skills/agent-workflow/scripts/journal.py add --project <p> --area <a> --task "…"
   --rounds N --causes "…" --changes "kind:target what; …"` — one entry per task. `changes` empty with rounds > 0
   means the retro is not done.
9. **Report** — a few lines, no essay:
   ```
   <task>: N rounds — main cause; changed: <kind:target>, …
   Kept: <practice> → <where it is written now>
   Memory: −K stale notes, +M; skills repo: <commit hash> pushed | PR <url>
   Open: <anything that needs the human's decision>
   ```

If the session had nothing significant: say so in one line, still do steps 6 and 8 for what was done.
