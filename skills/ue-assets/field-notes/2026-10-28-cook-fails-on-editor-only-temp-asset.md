---
symptom: cook fails "Failed to cook /<Plugin>/... It imports class /Script/<Module>.<Class>, which is in a module that is not available on the platform"; the asset registry shows no referencers
engine: "5.8.1"
status: observed
date: 2026-10-28
source: cook log (LogCook UnexpectedLoad line)
---
The failing package was an engine plugin's editor-only asset (a facial-animation solver config). Nothing referenced it
in the asset registry, so `get_referencers` was empty: it was loaded, not imported. The cook log names the culprit a few
hundred lines earlier: `UnexpectedLoad: TargetPackage <failing> was unexpectedly loaded during the cook of SourcePackage
<yours>`. Here `<yours>` was a leftover editor-only temp asset (a `*_Performance_Tmp` from a facial-animation bake),
committed into a folder listed in `DirectoriesToAlwaysCook`. Nothing used it: delete it (or keep such temps outside
always-cooked folders). Adding a whole folder to `DirectoriesToAlwaysCook` cooks every editor leftover in it — search the
folder for `*_Tmp*` / work assets before adding it.
