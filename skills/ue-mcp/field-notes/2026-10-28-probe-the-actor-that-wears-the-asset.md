---
symptom: a correction measured in PIE makes things worse (offset grows from 7.75 to 12.8 cm); a fit between DCC and engine coordinates moves the part the wrong way
engine: "5.8.1"
status: observed
date: 2026-10-28
source: retro — fitting a baked weapon into a character's fist, three re-imports
---
- **Probe the actor that wears the asset, not the first one of its gameplay type.** Menus, lobbies and test maps often
  spawn several actors of the same class/form with different looks. Filter by the asset itself
  (`get_skeletal_mesh_asset().get_name() == "<Mesh>"`), and when the scene that shows the look is not the default map,
  open that scene first. A probe that silently picks `[0]` measures someone else's hand.
- **DCC ↔ engine mapping: check the direction with one known move before trusting it.** A rotation fitted (Kabsch/SVD)
  on a handful of nearly coplanar points (finger knuckles of one hand) can come out mirrored with a small residual —
  the residual does not catch it. For FBX round trips, Blender armature space is usually Unreal component space with
  Y negated; move by a test vector, re-measure, confirm the sign, then apply.
- **Iterate to a threshold**: measure → apply → re-measure on the same actor and pose, until the residual is below
  the tolerance (e.g. 1 cm). Report the before/after number, not "should be fixed".
- Better still: anything the author may want to nudge (a held weapon, a prop) belongs on a socket they can move
  themselves — see the ue-assets note on rigid weapons — so no measurement loop is needed.
