---
symptom: a world-space move arrow / path trail drawn over the units' heads looks too short or overshoots its target from a tilted top-down camera; a short (one-cell) arrow looks crooked; the trail passes through tall units
engine: "5.8.1"
status: observed
date: 2026-10-31
source: a tactics board game (8x8, 200 cm cells, board camera pitched 36-66 deg); three review rounds on one path trail
---
A trail drawn at a fixed height h over the floor (chevrons "just over the heads", ~2 m) is seen shifted along the camera's
view direction by **h / tan(pitch)** on screen-to-floor: 1.45 cells at 36 deg, 0.74 at 55 deg (200 cm cells). A move
toward the camera reads 1-2.5 cells short, away from it overshoots, sideways it hangs over the neighbouring row - so the
arrow "sometimes reaches, sometimes not".

What fixed it (accepted):

- **Land the end on the floor.** Keep the middle over the heads, ease the last stretch down (smootherstep, so both bends
  are soft and the last ~20 % lies flat) and put the arrow head's TIP on the floor - no height, no parallax. Stop the tip
  on a circle (~0.35-0.4 cell) round the destination's centre, not on the cell edge: a diagonal then ends inside the
  cell, not on the corner shared by four cells, and it never covers the unit / ghost standing in the centre.
- **Place the head along its chord.** On a bent line, a head centred on the curve with the curve's tangent points past
  the end point; take the direction from the point one head-length back to the end and put the tip exactly on the end.
- **Scale height and head with the move's length.** A one-cell move with a 2 m bridge is a 60-deg cliff with a head as
  long as the move. Height = clamp(0.4 x length, 35 cm, head height), head = clamp(0.45 x length, 45 cm, full),
  descent over up to the whole short move: a short move becomes a low step at the feet, a long one a bridge - one shape,
  no jump between lengths.
- **Clear bodies by measurement, not by a constant.** Collect, per cell, the top of each unit's and ghost's mesh bounds
  (`GetMesh()->Bounds.GetBox().Max.Z`, skip hidden ones) and keep the trail clearance-cm over every occupied cell it
  crosses; for an arc raise the apex in steps until the parabola clears each occupied cell over its whole width (a
  parabola's lowest point over a stretch is at one of the stretch's ends). Start a tall unit's trail over its own head.
- **Check a matrix, not one move.** Toward / away / sideways, 1 cell straight and diagonal, 2 cells, long, jump, blocked
  path, tall unit at the start and on the way - each as numbers in a pure geometry test (tip inside the cell and off its
  centre, no segment steeper than ~35 deg, z over each occupied cell) and one frame from the player's camera. Each of
  the three rounds was a case from this list that had not been looked at.
