---
symptom: a measurement tool rebuilt after a source change gives numbers that disagree with the tests; a reference snapshot taken from it does not match the product built from the same source
engine: "any (CMake/Ninja or any build wrapper)"
status: observed
date: 2026-10-29
source: measurement (binary timestamp vs. source edit)
---
A small wrapper script took several build targets but forwarded only the first one to the build tool. The test binary
was rebuilt on every change; the auto-battler and the replay tool silently stayed from an hour earlier, so a
determinism reference and a balance run came from a binary without the latest core change. It surfaced only because
the product (built separately) wrote a different status order than the "reference".
Rule: before trusting a number or snapshot from a rebuilt tool, compare the tool binary's modified time with the newest
source edit it must contain (and re-run the measurement if it is older). When a wrapper takes a list of targets, make
it pass all of them (`--target a b c`) and print what it built.
