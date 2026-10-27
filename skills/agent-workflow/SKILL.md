---
name: agent-workflow
description: Working discipline for a coding agent on a long project with a human author — the retro after every significant task (rounds of corrections, causes, and the skill/rule/hook/tool change that prevents them), the task journal (scripts/journal.py, sqlite) with rounds-per-area statistics, Claude Code auto-memory hygiene (small index, expiring state notes, lessons promoted into skills, claims checked against git), speaking up about broken process, independent review by a second model, and measured skill optimization. Use when a significant task is finished or accepted, when the human sent work back more than once, when memory or CLAUDE.md feels stale or contradictory, before committing to a spec or architecture, or when asked "why does this keep happening / how do we work faster".
license: MIT
metadata:
  scope: "engine-agnostic; any long-running project with a human author"
---

# Agent workflow — learn from every task, keep memory honest

The expensive loop on a long project is **agent does it → human looks → "not that" → again**. Each round costs the
human's attention, the scarcest resource on the project. This skill turns every round into a change that removes
the next one: a skill row, a rule, a hook, a tool. Talking about it in chat changes nothing.

## Ground truth rule

Memory, notes and CLAUDE.md are claims, not facts. Before acting on "X is done / X is broken / we decided Y":

```bash
git log --oneline -20 -- <path>        # did it land, and when
git status --short                     # is it still uncommitted (someone else's work?)
git log -S'<symbol>' --oneline          # when a name appeared or vanished
```

The code and git history win over a note. A note that disagrees with git is fixed or deleted in the same turn.

## 1. Retro — after every significant task

Significant = took more than one round, touched a pipeline, or the human was surprised. Run it when the human
accepts the work (or abandons it), not later.

1. **Count the rounds** — times the human sent the work back. 0 is the target.
2. **For each round, one cause** in plain words. Classify:

| Cause class | Typical fix |
|---|---|
| Didn't check the result myself (no screenshot, no test, no scene state) | a tool or a verification step in the skill. Check through **the same entry point the human will use** (press Play on that map, run the shipped command) — a capture script that sets the scene up itself proves the script, not the deliverable |
| Missing knowledge (engine API, project convention) | a row in the skill's table / a reference file |
| Misread the request (taste, intent) | ask earlier: show a sketch or 2–3 options before building |
| Tool got in the way (crash, lock, slow build) | a hook, a script, a field note |
| Process collision (another session, dirty tree) | a rule + enforcement (hook), not a reminder |

3. **Keep what worked.** An approach that landed first try or that the human praised is written down the same
   way as a mistake — otherwise the next session rediscovers it by luck.
4. **Make the change now** — edit the skill, add the rule, write the hook, or file the tool task. A lesson that
   applies beyond this project goes into a **shared skill** — written so a stranger can use it (no project names,
   personal paths, ids), with its source — and is **sent to the skills repo right away** (pushed by a maintainer,
   a pull request from everyone else; unverified lessons as field notes — the `retro` skill has the steps); a
   project-only one goes into the project's CLAUDE.md or skill.
5. **Record it** in the journal (below). `changes` empty with rounds > 0 = the retro is not done.
6. Tell the human in **a few lines**: rounds, main cause, what changed, what was kept. Not a report.

The human can trigger the whole procedure with **`/retro`** (the `retro` skill in this repo).
Template and worked examples: [references/retro.md](references/retro.md).

## 2. Task journal

`scripts/journal.py` — Python 3 stdlib, sqlite at `~/.claude/agent-journal.sqlite` (override `AGENT_JOURNAL_DB`).
One DB across projects, so lessons are comparable.

```bash
J=~/.claude/skills/agent-workflow/scripts/journal.py
python "$J" add --project mygame --area cinematics --task "Intro dialogue" --rounds 3 \
  --causes "speaker off-screen; crossed the axis" \
  --changes "skill:ue-cinematics axis check before every cut; tool:scene snapshot after each cut"
python "$J" list --project mygame --area cinematics
python "$J" stats [--project mygame] [--by week]
```

`stats` prints mean rounds per area per month/week, the most frequent causes, and for each recorded change the
area's mean rounds before vs after it. Small numbers — read it as "keep / revisit", not as proof. Areas are
free text; keep a stable short set per project (`ui`, `cinematics`, `build`, `networking`, `docs`…).

## 3. Memory hygiene (Claude Code auto-memory)

| Rule | Why |
|---|---|
| Index (`MEMORY.md`) = **one line per note**, a title and a hook, no content | the index loads every session; a fat index crowds out the task |
| **State notes expire.** "Built, waiting for the author" lives until accepted; then the facts go to git (commit message) or project docs and the note is deleted | stale state is the main source of confidently wrong starts |
| **Reusable lessons move into skills.** A note that would help on another project is a skill row, not memory | memory is per-project and per-machine; skills travel |
| **Contradictions resolve into one rule.** Two notes that disagree → one note with the current rule and the date it changed | the agent otherwise picks whichever it read last |
| **Verify before trusting** (Ground truth rule) | notes describe intent; git describes what happened |
| Grouped state notes (one per feature) get one index line for the group | keeps the index scannable |

Periodic pass (when the index passes ~100 lines, or monthly): delete accepted state, promote lessons, merge
duplicates. Checklist: [references/memory-hygiene.md](references/memory-hygiene.md).

## 4. Speak up — and decide

- When the process, a tool or memory is going wrong (repeated crash, a rule everyone works around, two sessions
  colliding, a note that is wrong), say so in **one or two lines with a proposal**: "X broke 3 times this week
  because Y — I suggest a hook that Z. Do it?" Silence is how a workaround becomes permanent.
- **Decide technical matters yourself**: API choice, file layout, which test, how to measure. Asking the human to
  pick between two equivalent implementations wastes their attention.
- **Ask the human only for what only they know**: taste, design intent, priorities, what "done" looks like,
  anything irreversible or outward-facing (publishing, deleting, spending money).
- When asking, offer a recommendation and the alternatives in one message — never an open "what do you want?".

## 5. Independent review

Before committing to a spec, an architecture or a risky refactor, get a read that is not anchored on yours:

- Use a **different model** (e.g. a subagent with another `model`), or at least a fresh agent with no history.
- Give it **the problem and the code/spec**, not your conclusion. Ask **"what is wrong with this, what will break,
  what is missing"** — never "confirm this is good". An agent handed a hypothesis tends to return it confirmed.
- Treat the answer as input: accept, reject with a reason, or test. Record what changed in the spec.

Prompt shapes and what to give the reviewer: [references/review-and-optimization.md](references/review-and-optimization.md).

## 6. Measured improvement — later, with data

Once the journal shows an area with steady rounds and the work has an **automatic check** (a test, a scene-state
assertion, a lint, a measured number), the skill for that area can be optimized against it: run the task set,
score, edit the skill, re-run. Reflective prompt optimizers such as **GEPA** (an LLM reads failed traces and
proposes prompt edits, keeping a Pareto set of variants) automate that loop. Do this only when:

- the journal has enough tasks in the area to tell a change from noise (dozens, not three);
- the score is automatic — an optimizer against human taste overfits to the reviewer's last mood;
- the skill is narrow (one pipeline), not a whole-project philosophy.

Until then the retro is the optimizer.

## Related

- **`ue-mcp`** — the editor lock hook and the scene probe are retro outputs of exactly this loop: "the agent
  didn't look at the scene" became a tool, "sessions collided" became a hook
- [references/retro.md](references/retro.md) — retro template, examples, cause → change mapping
- [references/memory-hygiene.md](references/memory-hygiene.md) — the periodic memory pass
- [references/review-and-optimization.md](references/review-and-optimization.md) — reviewer prompts, GEPA notes
