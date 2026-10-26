# Independent review and measured optimization

## Why a second model

An agent reviewing its own plan finds the problems it already thought of. A reviewer handed the author's
conclusion tends to agree with it. What works: a reviewer with **different priors** (another model, or a fresh
context) given **the raw material**, asked to **attack**.

## What to hand the reviewer

| Give | Don't give |
|---|---|
| the problem in the human's words and the constraints | your conclusion or "I think X is best" |
| the spec / diff / relevant files (paths it can read) | a summary of the code instead of the code |
| what is already ruled out and why, in one line each | the conversation history |
| the question: "what is wrong, what breaks, what is missing, what is over-built" | "please confirm", "is this good?" |

## Prompt shape

```
Problem: <2-4 lines, the human's goal and hard constraints>
Material: <files to read>, <spec path>
Already ruled out: <option> — <reason>
Review this as a skeptical senior engineer. List, most severe first:
  1. what will break or not work as described (with the line / section)
  2. what is missing for it to work in practice
  3. what is over-built and can be cut
Do not summarize what it does. Do not praise. If something is fine, skip it.
```

In Claude Code: spawn a subagent with a `model` different from the main session's for specs and architecture;
a fresh same-model agent is the fallback. One reviewer per document; a panel adds tokens faster than insight.

## Using the answer

- Each point: **accept** (edit the spec), **reject** (one-line reason in the spec), or **test** (cheapest experiment).
- Record in the spec's status line: "reviewed by <model> <date>: <what changed>".
- Don't loop the reviewer until it agrees — that is asking for confirmation by attrition.

## Measured skill optimization (later)

Reflective prompt optimization treats a skill as a prompt to be tuned against a score:

1. A task set from the journal for one area (real tasks, with their accepted outcomes).
2. An automatic scorer: a test passes, a scene-state assertion holds (no warnings, speaker on screen on every
   line), a measured frame time, a lint.
3. Run → score → an LLM reads the failing traces and proposes edits to the skill → keep variants that improve
   any task without regressing others → repeat. **GEPA** (Genetic-Pareto, reflective prompt evolution) is one
   published optimizer of this kind; DSPy ships an implementation.

Preconditions — skip it until all hold:

- dozens of journal entries in the area, not a handful;
- a scorer that needs no human (otherwise you optimize toward one person's last comment);
- a narrow skill (one pipeline); a broad skill gets edits that help one task and quietly hurt another;
- a held-out set of tasks the optimizer never saw, checked before adopting a variant.
