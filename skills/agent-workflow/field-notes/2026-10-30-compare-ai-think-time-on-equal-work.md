---
symptom: an AI change looks much slower (or faster) per turn than it is; the before/after numbers move when the run length changes
engine: "any (turn-based game AI measured by a self-play tool)"
status: observed
date: 2026-10-30
source: measurement (self-play tool, 12 games, single thread)
---
Total time / turns played compared two AI variants over the same seeds, but the variants play different games: the new
AI ended games sooner (690 vs 936 turns in 12 games), and early turns with a full board cost far more than late ones -
the average said +37 %. Capping both runs to the same early window (first 12 rounds of 16 games, 384 turns each, one
thread, both variants running side by side on the same machine load) gave +21 %, and +16 % after the fix.
Rule: compare per-turn cost only on equal work - same seeds, same round window that every game reaches, same turn
count, run both variants concurrently so machine load is shared; report the window with the number.
