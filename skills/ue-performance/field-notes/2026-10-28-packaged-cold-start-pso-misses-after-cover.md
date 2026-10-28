---
symptom: packaged cold first launch — the loading screen waited for PSO precaches, yet the first second of the scene hitches 0.4-0.7 s and later 0.2 s every few seconds, log "PSOPrecacheState: Missed"
engine: "5.8.1"
status: observed
date: 2026-10-28
source: measurement, packaged Development build, -clearPSODriverCache, CSV per phase
---
Cold driver cache, packaged build: a logo intro gated on its own precaches played clean (one 81 ms frame), the held
still over the map change had no frame above 20 ms, but the scene behind it opened with 381 and 683 ms frames right
after the fade and ~200 ms frames every few seconds after (new shots, new effects). Not yet proven why the precache
missed them; the likely cause is that the scene opens on black and fades in, so its real view is first drawn after the
loading screen is gone. Next step to try: a recorded PSO cache of a play-through (`-logPSO`, bundled
`FShaderPipelineCache`), or keep the cover up over the scene's first lit frames. The warm launch had none of it
(the intro's black wait: 13.7 s cold → 0.19 s warm).
