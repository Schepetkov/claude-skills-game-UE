# Memory hygiene — the periodic pass

Claude Code auto-memory: an index file (`MEMORY.md`) that loads every session, plus one note file per topic that
loads on demand. Location: `~/.claude/projects/<project-key>/memory/`. The index is the expensive part — every
line costs context in every session.

## Kinds of note

| Kind | Example | Lifetime |
|---|---|---|
| **Rule** (how the human wants work done) | "commit only after the author has checked" | until the human changes it; then rewrite, keep the date |
| **State** (where a feature stands) | "menu redesign built, waiting for the author" | until accepted or dropped → facts to git/docs, note deleted |
| **Lesson** (how a tool/engine behaves) | "save_assets silently succeeds on read-only LFS files" | promote to a skill as soon as it holds beyond this project |
| **Pointer** (where things are) | "secrets live in X, build scripts in Y" | as long as true; verify on use |

## The pass (monthly, or when the index passes ~100 lines)

1. **State notes**: for each, check git (`git log -S`, `git status`). Accepted and committed → delete the note
   (the commit message and docs carry the facts). Abandoned → delete. Still open → one line in the index, date in it.
2. **Lessons**: anything engine/tool-generic → move into the matching skill (a symptom → cause row, a field note),
   delete from memory. Project-specific → the project's CLAUDE.md or project skill if every session needs it.
3. **Contradictions**: grep the notes for the same subject; merge into one note with the current rule and the date
   it changed ("since 2026-10-06: …"). Delete the others.
4. **Index**: one line per note — `[Title](file.md) — the hook in ≤ 15 words`. Group many state notes of one area
   under one line listing the files.
5. **Secrets**: a note never contains a token, password or key — only where it lives.

## Red flags

- An index line that is a paragraph.
- "Done" in a note, and the files are in `git status` as modified.
- Two notes whose titles differ but say opposite things.
- A lesson that has been copied into three projects' memory — it is a skill.
- A note nobody has needed in months — delete; git has the history.
