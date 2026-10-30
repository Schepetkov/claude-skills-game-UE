---
symptom: a rule change is accepted in the core and tests, then the human finds an ability or a preview that still behaves by the old rule
engine: "any (game rules engine with data-driven abilities and several clients)"
status: observed
date: 2026-10-29
source: practice (one round lost on a turn-based tactics project)
---
The change removed a primitive from a piece's rules ("forward" for a pawn-like piece). Movement, attack and aura were
updated and tested, but an ability of the same piece ("charge forward 2 cells") kept the removed primitive - in the
resolver's default, in a wire fallback that fills a missing target, and in three client previews that re-derived the
path themselves. The human saw it on the first look.
Rule: when a rule primitive changes or disappears, grep for every consumer of its OLD meaning before reporting done -
ability payloads and descriptions, resolver defaults, request fallbacks, client-side previews and replays, scripted
tutorials - and list each with "changed / unchanged on purpose / question for the designer". The open ones are asked in
the same report, not discovered by the human.

Second case (2026-10-30, same kind of project, caught before the human): a ranged piece was switched to another
piece's MOVE pattern. The rules engine, a client and two tools recognised "which piece this is" by that move pattern -
castling partners, the piece icon, the editor palette group, the balance calculator's role curve. Nothing failed in a
test; the archer had silently become a castling rook. Rule: when a content change moves a unit onto another unit's
pattern, grep every consumer of the pattern NAME (not only of the movement code) and separate "how it moves" from
"what it is" with an explicit identity field before shipping.
