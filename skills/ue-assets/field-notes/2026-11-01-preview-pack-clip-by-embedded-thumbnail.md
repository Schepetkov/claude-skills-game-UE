---
symptom: need to know what an animation in another project looks like (e.g. "is Q_Ability the shot into the sky?") without opening that project
engine: "UE 5.8"
status: observed
date: 2026-11-01
---
An asset saved by the editor usually carries its Content Browser thumbnail as a PNG inside the `.uasset`: read the bytes, take
`b[b.rfind(b'\x89PNG') : b.find(b'IEND', start) + 8]` and open it. For animation sequences it showed the pose clearly (a bow
raised overhead identified the "shoot up" clip among Q/R abilities). Cascade particle systems in the same pack had only a
"No Image" placeholder, and some PNGs are truncated (PIL "broken PNG file") - then fall back to exporting the clip to FBX
from a commandlet of that project (`AssetExportTask` + `AnimSequenceExporterFBX` works under `-nullrhi`).
