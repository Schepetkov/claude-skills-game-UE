# Contributing

The whole point of this repo is that its claims are **checkable**. A PR that adds plausible-sounding UE advice makes it worse, not better — that content is already freely available from any chatbot.

Most contributions here are expected to come from agents: you work on your project, type `/retro` at the end of a task, and your agent opens a pull request with what it learned. Everything below applies to those PRs exactly as to hand-written ones.

## How a lesson gets in

```
your session ──/retro──▶ branch retro/<date>-<slug> ──▶ pull request ──▶ CI check ──▶ maintainer review ──▶ main
                                                                                                          │
                     every installed agent pulls main at session start (skills/agent-workflow/hooks) ◀────┘
```

- `main` is protected: nothing lands without a pull request, a green `check` job and a maintainer's approval.
  Whatever reaches `main` becomes instructions for every agent that installed these skills — that is why.
- The `retro` skill does the branch, the check and the PR for you. By hand: fork, branch from `main`,
  `python tools/check_skills.py`, push, open a PR — the template asks the right questions.
- One lesson per PR is easiest to review. Several field notes from one retro may share a PR.

## Two kinds of contribution

| | Verified claim | Field note |
|---|---|---|
| What | A cvar, API, default, cost, decision rule | Something seen in practice: a pitfall, a workaround, a symptom → cause |
| Where | A row in `SKILL.md` or `references/*.md` | `skills/<skill>/field-notes/YYYY-MM-DD-short-slug.md`, one lesson per file |
| Bar | A source (below) — no exceptions | Engine/tool version, how it was seen, how to reproduce. `status: observed` until someone checks it |
| Becomes | — | Verified: a maintainer or contributor checks it against source, moves it into the skill's tables, deletes the note |

Field-note frontmatter (`tools/check_skills.py` enforces it):

```markdown
---
symptom: what you see, in the words you'd search for
engine: "5.8.1"
status: observed            # observed | verified — verified needs source
date: 2026-10-27
source: Engine/Source/...   # or an Epic doc URL, or "measurement: <hardware, before → after>"
---
Cause, then the fix or workaround, then how to reproduce. A few lines; no story of the project.
```

One file per lesson means two contributors never edit the same lines. Before writing one, grep the skill and its `field-notes/` for the symptom; extend an existing note instead of adding a twin.

## What gets a PR rejected

- A project name, character or map name, a personal path (`C:\Users\<name>`), an id, a key or a token. CI catches the common forms; reviewers catch the rest. Write the lesson so a stranger on another project can use it.
- A verified-style claim with no source. Make it a field note instead.
- Code (`hooks/`, `scripts/`, `templates/`, `install.*`, `tools/`) that does more than its description says, calls the network without need, or pulls dependencies when the standard library would do. This code runs on other people's machines; it is read line by line.
- A duplicate of an existing row or note.

## Maintainers

Maintainers merge PRs and, every so often, **consolidate**: verified field notes move into the skill tables, duplicates merge, notes that turned out wrong are deleted, and a `SKILL.md` over ~250 lines sheds tables into `references/`. A maintainer's own agent may push to `main` directly; everyone else goes through a PR.

## The one hard rule

**Every factual claim needs a source.** One of:

1. **A path in the engine source** — `Engine/Source/Runtime/Renderer/Private/Lumen/Lumen.cpp` and the symbol you found there.
2. **An Epic documentation URL** — and if it contradicts the source, the source wins and the contradiction is worth documenting (see the `r.MegaLights.Allow` / `r.MegaLights.Allowed` example in the README).
3. **A measurement** — build config, hardware, before/after numbers.

"I'm pretty sure it's called that", "this is standard practice", and "the AI said so" are not sources. Neither is a blog post that doesn't cite one of the above — that's how `bUseIris = true;` propagated into half the internet despite never existing.

## Verifying a cvar

```bash
# from the engine root
grep -rn -A6 'TEXT("r\.Your\.Cvar")' Engine/Source/Runtime/Renderer/Private/
```

The `FAutoConsoleVariableRef` declaration gives you three things: the real name, the backing variable's initializer (the true default — not what a doc page claims), and the help text. Quote from that.

If you only have a Launcher install, `DumpConsoleCommands` in-game writes the full list to `Saved/`. Say in the PR which method you used.

## Style

These skills are read by an agent, not a human browsing docs. Optimise accordingly:

- **Lead with the decision.** Tables and decision trees, not prose surveys. If there's a right answer, say which one it is.
- **Order by impact.** "Cheapest fix first" beats an alphabetical cvar dump. Say what each option trades away.
- **Symptom → cause tables** are the highest-value format in this repo. Add to them.
- **Mark maturity.** Experimental is experimental. Deprecated is deprecated. Note the version something changed in.
- **Name the failure mode.** "This fails silently" is more useful than "be careful".
- Keep `SKILL.md` under ~200 lines. Deep tables and cookbooks go in `references/`, which load only when needed.
- No filler. If a section doesn't change what the agent does, delete it.

## Skill structure

```
skills/<skill-name>/
├── SKILL.md              # required — frontmatter + the decision content
├── references/           # optional — loaded on demand
│   └── <topic>.md
├── field-notes/          # optional — contributed lessons, one per file, YYYY-MM-DD-slug.md
├── scripts/              # optional — tools the skill runs (Python 3 stdlib preferred)
├── hooks/                # optional — Claude Code hooks; opt-in, documented with a settings snippet and a pipe test
└── templates/            # optional — code to copy into a project; say which engine version it targets
```

`SKILL.md` frontmatter:

```yaml
---
name: ue-something                  # must match the directory name
description: >-
  What it covers — then "Use when ..." with concrete triggers.
  This is the only text the agent sees when deciding whether to load
  the skill, so make the triggers specific.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---
```

The `description` is doing more work than anything else in the file. Write it as trigger conditions, not as a topic label.

## Adding a new skill

Gaps worth filling: animation & control rig, audio & MetaSounds, physics & Chaos, Gameplay Ability System, build/packaging & CI, World Partition authoring, mobile/Switch targets.

Before opening a PR:

- [ ] Every cvar / API / ini key verified by one of the three methods above
- [ ] Engine version stated; version-specific items marked
- [ ] Experimental and deprecated features flagged as such
- [ ] No hardcoded personal paths, project names, or credentials
- [ ] `SKILL.md` has a `## Ground truth rule` section pointing at source verification
- [ ] Tested in Claude Code — the skill actually loads on its stated triggers
- [ ] `python tools/check_skills.py` reports 0 errors

## Reporting an error

If a skill states something wrong, an issue with the correction **and its source** is as valuable as a PR. Include the engine version you checked against — the answer may be right for 5.8 and wrong for 5.9, which is itself worth recording.
