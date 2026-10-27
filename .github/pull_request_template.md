## What the agent will now do differently

<!-- One or two lines. "Checks X before Y", "knows that Z fails silently when ...". -->

## Where it came from

<!-- A retro (rounds, cause) or a find. Engine version. No project names, paths or ids. -->

## Kind

- [ ] Field note (`skills/<skill>/field-notes/YYYY-MM-DD-slug.md`) — `status: observed` or `verified`
- [ ] Change to a skill's `SKILL.md` / `references/` — every claim has a source
- [ ] New skill
- [ ] Code that runs on users' machines (`hooks/`, `scripts/`, `templates/`, `install.*`, `tools/`)

## Checklist

- [ ] `python tools/check_skills.py` passes locally
- [ ] Verified claims cite an engine path, an Epic doc URL or a measurement; the rest is a field note marked `observed`
- [ ] Searched the skill and its `field-notes/` — this is not a duplicate (if it extends a note, edit that note)
- [ ] No project names, character names, personal paths, ids, keys or tokens
- [ ] Code: does only what the description says, no network calls it doesn't need, standard library preferred
