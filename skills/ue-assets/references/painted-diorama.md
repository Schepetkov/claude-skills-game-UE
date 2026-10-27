# Painted 2.5D diorama (one illustration → a scene a camera can move in)

A menu backdrop or a level-select map built from flat painted layers (AI-generated or hand-painted), with real depth
of field, particles and a camera that sways and dives in. Learned on a UE 5.8 project, six review rounds; every row
below is a defect a human actually caught.

## The core rule: everything that touches the ground stands on a real ground

| Wrong | What the human sees | Right |
|---|---|---|
| Floor painted on the same vertical card as the cliff; props on cards at their own depths | props "float" as soon as the camera moves (parallax between prop and painted floor) | floor = a real (tilted) plane; the painting is **projected onto it from the rest camera**; each prop's base = the ray through its painted spot intersected with that plane |
| Prop spots picked by eye on the painting | half of them sit on the rim or outside the floor | keep spots ≥ ~2 % of the floor size inside the floor mask; move them toward the centre automatically |
| Prop sprites cut with padding under the base, or with a neighbour's debris inside | "floating" again; foreign chips | cut each sprite from its own connected component, no air below the base |
| A vertical fog card in front of the props | the fog hides the bases → props look like they hover | fog as thin layers **lying on the floor plane** (3–4 at different heights, each drifting its own way); brighter than the floor, or it is invisible on a pale floor |
| No contact | props look pasted on | a soft dark ellipse on the floor plane under each prop |
| Empty space "reserved" for something that is not in this scene | "why is the middle empty?" | fill the whole area unless the empty space is part of this scene's purpose |

## Projection proxies (cliff, rim, sides)

Project the painting from the rest camera onto simple proxy geometry: a tilted plane for the floor, a ring of
vertical strips for the slab's sides (strips placed on an oval traced from the painted silhouette).

| Pitfall | Fix |
|---|---|
| A ray from the rest camera crosses the ring twice (front wall, back wall): **the nearer wall takes the pixel** — back-rim rocks land on the front wall and cut through props | split the texture by ownership: the front half gets only pixels below the oval's middle row (cliff), the back half only pixels above (rim); the far left/right columns go to both |
| A flat card for the side rock clusters at one depth | it slides off the ring off-axis: vertical cuts, a rock hanging apart from the island | put the ring on the oval through the **outer silhouette** (side rocks included) instead of separate cards |
| Ring on a larger oval than the floor | a thin gap at the front edge, background glow shines through | extend the floor texture to the ring's oval on the front half |
| Floor mask from a brightness threshold | shaded parts of the floor fall out, stepped edges | close + fill the contour, unite with a fitted ellipse, blur the mask edge (no stair steps) |
| Walls nearly parallel to the rays (oval's far left/right) | at 20–30° off-axis the projection smears into black bands | this is the method's limit — state the camera range (e.g. sway ≤ 8°, the dive path) and check exactly that range; free orbit needs real 3D rocks |

## Rendering

- **Opaque-ish cards: Masked + dithered opacity**, not Translucent — masked writes depth, so cinematic DoF blurs
  each card by its own distance. Translucent cards are blurred by whatever opaque depth is behind them.
- Unlit emissive with manual exposure and `apply_physical_camera_exposure = false` (otherwise unlit art is black).
- **Miniature scale** sells the diorama: with focus ~5 m a 35 mm f/2 lens already blurs the foreground rocks and the
  far background (tilt-shift look). At real-world scale (50 m) the same lens barely blurs anything.
- Lava/glow in the painting: an emissive boost on saturated orange pixels with a slow flicker — no mask needed.
- Ghost figures: translucent card material, opacity "breathing", drift by World Position Offset (no code).
- A camera looking along +Y has screen-right = **world −X**: everything placed from screen coordinates comes out
  mirrored unless you negate X. Self-consistent if every layer uses the same mapping; just remember it when placing
  background cards by screen position.

## Particles in such a scene

- Do not borrow a weather/snow system for embers: velocity-aligned motion-blur sprites read as sharp angular streaks.
  Own sprite material: hot pale core + coloured halo + per-particle flicker (`ParticleRandom`), `Unaligned`, sizes
  in the miniature's units (millimetres to ~2 cm at a 5 m focus), curl noise, `MinCameraDistance` 0.
- `ParticleColor`'s main output is **float3** — take alpha from its `A` pin, or the shader fails and the sprite
  silently falls back to the default lit material (black squares in an unlit scene).
- Particles do **not** simulate in the editor world (game time stays 0): judge them only in PIE (see `ue-mcp`
  field notes for capturing a PIE preview).

## Verification before showing

1. Shots from the **rest camera and from the edges of the allowed camera range** (sway extremes, higher, the dive
   path) — never only the rest frame. Most "floating" and "cut" defects are invisible from the rest pose.
2. Particles and anything time-driven: in a game world (PIE), not the editor world.
3. Look at the shots yourself at full size (crops of the bases, the floor edge, the side rocks) before the human does.
