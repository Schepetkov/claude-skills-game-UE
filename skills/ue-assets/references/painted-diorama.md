# Painted 2.5D diorama (one illustration → a scene a camera can move in)

A menu backdrop or a level-select map built from flat painted layers (AI-generated or hand-painted), with real depth
of field, particles and a camera that sways and dives in. Learned on a UE 5.8 project, ten review rounds; every row
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
| Walls nearly parallel to the rays (oval's far left/right) | the ends shear and "slide" with **any** camera offset (stretch ∝ 1/cos of the wall's angle to the ray) — shrinking the sway only shrinks it | drop the strips within ~15° of each end and stand a **flat card facing the camera** at the end's depth there (front and back halves of the texture as two cards on one plane), overlapping the neighbouring strips by another ~20° so no slit opens. Plus a modest sway (≈15 cm at a 5 m focus) |
| An AI-generated 3D mesh of the slab (image-to-3D) fitted to the painted silhouette and camera-mapped | holes where its top was carved away to keep the props' floor flat, smeared texture on every surface the rest camera does not see — the human called it worse than the strips | do not camera-map a generated mesh onto the painting; keep the flat proxies + end cards. A real 3D slab needs its own texture, i.e. a different art pipeline |

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

## Animating painted (ink line) art

- **Never move the pixels of line art.** A shader that resamples the sprite (e.g. a funnel "rotating" by warping UVs
  around a cylinder) smears thin ink lines into horizontal streaks — invisible in thumbnails, obvious at screen size.
- What reads as motion and keeps the drawing crisp: light/shade bands running across the shape (a function of the
  cylinder angle and time, multiplying the colour), WPO sway of the card (top more than base), flicker/flashes, and
  real particles around it.
- A per-row profile (middle and half-width of the shape, baked from its alpha into a 1×N linear texture) lets the
  shader treat each row as the front of a cylinder without guessing the silhouette.
- **A creature with moving parts (heads, tail, breathing belly)** — move the geometry, not the texture: put the card
  on a subdivided grid mesh (64×64 is plenty; WPO on a 2-triangle quad can only shear the whole card) and in WPO
  rotate each part rigidly about its pivot (neck root, tail root) with a weight `1 − smoothstep(0.6R, 1.3R, dist)`
  from the part's centre; breathing = a small scale about the belly centre. Each vertex keeps its UV, so ink lines
  stay crisp. Per part: centre, pivot, radius, angle, rate, phase — two summed sines with different rates read as
  alive, one sine as a metronome. Eyes: a mask from saturated red pixels, pulsed emissive. Observed: UE 5.8.1.
- **Puddles/water on a painted floor:** take the mask from the art itself (bluish, mid-value pixels inside the floor;
  morphology open/close, keep components above an area threshold and with a compact fill ratio, drop those near the
  floor edge — rim rocks and the front lip read as false puddles), project it like the floor. Rain ripples drawn
  procedurally per cell **need a random on/off gate per cycle** (`hash(cell, cycle) < density`): with every cell
  firing, the rings form a static honeycomb that reads as a pattern, not rain.

## Several scenes in one map

- A scene whose floor/ring is **projected from a rest camera at the origin cannot be moved**: streamed as a sublevel
  with an offset transform, the projected parts vanish (props hang in the air). Stream every scene at the origin, keep
  one visible (`ULevelStreaming::SetShouldBeVisible` from C++; wait for `IsLevelVisible()`), and travel between them
  by taking the camera into thick cloud cards above/below the rest frame, swapping under the thickest cloud and coming
  out at the next scene from the other side — reads as one continuous descent. Keep the clouds out of the rest frame
  (start them beyond ±tan(vfov/2)·depth) or they haze every scene's sky. Observed: UE 5.8.1.
- That descent is not an overview: "all scenes together in one picture" needs a different view (renders of each
  scene as flat cards composed into one image). Ask which one is meant before building.

## An overview of all scenes (cards of their rest frames) with a seamless zoom into each

Worked first time with the human once these were in place (UE 5.8.1, measured):

- **Sketch first.** Cut each scene out (below), compose 2–3 layout variants as flat 2D images in Python, show them,
  build only the chosen one. The human picked from the sketches at once.
- **Capture each scene from its rest camera** with a `SceneCapture2D` copying the camera's lens and post:
  - the **whole frame** with `SCS_FinalColorHDR` and the show flag `Tonemapper` off → scene-linear values (emissive
    1.0 comes out 1.0). A card showing it through a camera with the same post is then tonemapped once, like the live
    scene. Captured with the tonemapper on, it gets tonemapped twice and comes out washed out.
  - the **cut-out** (the slab and what stands on it, no backdrop) twice, over an unlit black and an unlit white matte
    plane far behind, bloom off: `alpha = 1 − (W − B)/(white − black)`, `colour = B / alpha`. This is exact for
    half-transparent ghosts and smoke, which a chroma key is not.
  - at the **screen's exact aspect** (16:9 → 2752×1548). At 2752×1536 the zoomed-in card leaves 4 px bars top and bottom.
  - with **everything the live view has**, other levels' haze included. A part hidden for the capture shows as a
    brightness jump at the seam.
- **Layout:** the cards stand at different depths for parallax, all facing the overview camera exactly as each rest
  camera faces its scene. The camera only translates. Zoom pose = card centre − forward · W / (2·tan(hfov/2)), where
  W is the card's width. Pan first (across and down), dolly later.
- **Closed or future scenes:** take one real slab's cut-out, desaturate it to luminance and multiply by the scene's
  colour, then veil it in fog. A flat tint reads as a coloured smear, not a slab.
- **The seam:**
  - Put the scene's camera at its exact rest pose first (blend any menu offset or sway to zero).
  - Do not hard-cut. Dissolve over ~0.5 s through a full-frame card placed in front of the live camera **at its focus
    distance** with **depth test off**. Anything living in time (drifting ghosts, a turning funnel, particles) is at
    another phase than in the capture.
  - The card's actor must be **Movable**: a spawned StaticMeshActor is Static and ignores `SetActorLocation` in play.
  - The full-frame texture needs **no mips**. Shown at ~0.7 of its size it samples mip 1 and softens the ink against
    the live scene.
  - Reveal the full frame (sky, backdrop) **from the middle out with soft edges** that shrink to none at full frame,
    overlapped with the fade of the other cards. A hard rectangle reads as a framed picture; a fade before the reveal
    leaves a dark gap.
  - Measured across the camera switch in PIE: mean 0.3–0.6 of 255 per pixel; the static parts match at 1:1.

## Building more scenes of the same kind

- Re-render art at a higher resolution with an image-edit endpoint ("re-render this exact image, move nothing")
  at the model's native size: geometry stays pixel-exact (IoU ≈ 0.99), so every hand-tuned mask and spot carries
  over ×2. Tile-upscaled sizes (4K on some models) bring seams and mushy patches.
- Pale opaque subjects on a "transparent" background mode come back half-transparent — generate on a flat chroma
  green and key it yourself.
- The next variant (another level/circle) = an image edit of the base asset ("same shape, other theme"): same
  silhouette → the whole layout (floor, ring masks, end cards) is reused; only content and props are new.
- Shared parent materials across scenes: a rebuild script must not delete and recreate them — every other scene's
  instances lose their parent. Build them once; rebuild only on purpose, then rebuild all scenes.

## Particles in such a scene

- Do not borrow a weather/snow system for embers: velocity-aligned motion-blur sprites read as sharp angular streaks.
  Own sprite material: hot pale core + coloured halo + per-particle flicker (`ParticleRandom`), `Unaligned`, sizes
  in the miniature's units (millimetres to ~2 cm at a 5 m focus), curl noise, `MinCameraDistance` 0.
- `ParticleColor`'s main output is **float3** — take alpha from its `A` pin, or the shader fails and the sprite
  silently falls back to the default lit material (black squares in an unlit scene).
- **Rain/hail over a painted storm:** weather packs that kill drops on collision (scene depth or ray-traced
  collision, splash on hit, user parameters for area) do nothing useful over unlit cards — build a plain system:
  spawn box over the scene, lifetime ≈ fall height / speed, velocity-aligned thin streaks for rain, small unaligned
  dots with curl noise for hail, a separate tiny short-lived burst on the floor for splashes. If the background art
  already has painted rain, live streaks must be **brighter than the sky** behind them; on a still they still read
  weakly — judge rain in motion (a preview video), not in a single frame.
- Particles do **not** simulate in the editor world (game time stays 0): judge them only in PIE (see `ue-mcp`
  field notes for capturing a PIE preview).

## Verification before showing

1. Shots from the **rest camera and from the edges of the allowed camera range** (sway extremes, higher, the dive
   path) — never only the rest frame. Most "floating" and "cut" defects are invisible from the rest pose.
2. Particles and anything time-driven: in a game world (PIE), not the editor world.
3. Look at the shots yourself **at the human's screen size, crops 1:1** (bases, floor edge, side rocks, anything
   animated) before the human does — thumbnails hid both the end shear and the smeared line art.
4. Particle density: compare against the art at that size; the first tune was invisible (a tiny puff at the base),
   the second a blizzard over the drawing — aim for sparse specks that never cover the painted subject.
