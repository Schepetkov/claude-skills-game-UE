# Contributing

The whole point of this repo is that its claims are **checkable**. A PR that adds plausible-sounding UE advice makes it worse, not better — that content is already freely available from any chatbot.

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

## Reporting an error

If a skill states something wrong, an issue with the correction **and its source** is as valuable as a PR. Include the engine version you checked against — the answer may be right for 5.8 and wrong for 5.9, which is itself worth recording.
