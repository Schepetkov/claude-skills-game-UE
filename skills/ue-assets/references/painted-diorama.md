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

## Painted cards around a 3D play area with a free camera (props, backdrop, sky — laid out per seed)

A diorama is one camera's picture. When the camera orbits freely (a tactics board, 360°, pitch −6…−66°), each painted
prop must hold up from every side on its own. Learned in six review rounds on UE 5.8; every row is a defect the human
caught.

| Wrong | What the human saw | Right |
|---|---|---|
| Lying pieces (fallen drum, slab, capital) stood up as camera-facing cards | "floating", "at an odd angle" | never a standing card: a flat decal drawn top-down, or leave it out |
| Cards leant back with the view's pitch (to not go edge-on from above) | columns and walls falling over | upright only, turn about the vertical; a steep view simply sees less |
| Wide or directed pieces (wall, arch, portico, statue) turning to the camera | cardboard; corners give it away | draw them as a **frontal elevation**, keep them still facing the play area's centre, and only beyond the camera's reach (pivot bound + arm): then the back is never seen |
| Props drawn from ~25° above | top faces visible from a low camera, bases read wrong | standing props drawn side-on at eye level with a flat bottom edge; low props from 30 cm |
| Random mirroring of instances | painted light flips between neighbours | off |
| Density-noise scatter (PCG rings) | ~700 cards "from nowhere", identical pieces side by side, walls by the board | a composed layout: rings (empty → low pieces → clusters of anchor + satellites + low → a continuous back wall of buildings and silhouettes → backdrop), footprints that never overlap, the same picture kept apart |
| Then the composer's minimum (35–60 cards) | "too empty" ×3: gaps between the mid ring and the back line, a flat plain before the backdrop | the human wanted ~350: clusters out to the back line, a group every ~10° in the back wall, no deliberately empty sector. **Look for gaps from a low camera in all directions**; from above they do not show |
| A mirrored panorama round the backdrop cylinder | a kaleidoscope (one temple twice, face to face) | crossfade the panorama's last ~20 % into its start and repeat it plainly |
| Full height fog over the painted props, an unfogged painted backdrop behind | mid-ground props pale as ghosts in front of a dark backdrop — air perspective reversed | thin the fog, tint it the backdrop's mist, cap `fog_max_opacity` (~0.35) |
| A lit ground plane running up to the backdrop | the plain ends against the picture with a seam | blend the ground into the backdrop's own bottom-mist colour as **emissive** past ~2/3 of the radius |
| A cloud band with hard top/bottom edges | a ceiling | fade the band's alpha to both edges; speed ≥ ~0.25°/s (0.08°/s reads as still) |
| Ground tiles the size of a play cell, full contrast | the board's cells disappear | stones a third of a cell, ink pulled halfway to a mean grey near the board |
| A dark flat decal (ash patch) | reads as a hole | light decals only (cracks, bones, broken tiles) |

Mechanics that worked:

- Card = static mesh, two sections: the quad (local XZ, pivot at the foot) and a ground contact blob (modulate).
  Material WPO turns the quad about the vertical through `ObjectPositionWS` (per instance in the vertex shader) using
  the pre-skinned local position, so the instance's yaw is irrelevant. A `Billboard` scalar switches it off for still
  pieces. Dither it out near the camera and partly when it stands between the camera and the play area's centre.
- Cards cast no shadow (a billboard's shadow turns with the camera) — the blob gives contact.
- Flying souls: translucent card, WPO drift on two summed sines per axis with a per-instance phase, opacity breathing.
- The width of a card for spacing: `GetBoundingBox()` is the **extended** box — subtract the bounds extension you gave
  it for the turn, or tall cards reject every neighbour.
- Sheets where pieces stand on one drawn ground line: open the mask with a tall vertical element before labelling,
  or the line glues neighbours into one piece.
- Translucent backdrop/cloud cylinders centred on the origin sort ambiguously against translucent props: give them
  negative translucency sort priority.

### When the camera comes close: what the second round of reviews taught

The rules above held for a camera at its usual distance. When the human flew the free camera into the clusters (10–30 m,
looking down 15–35°), seven more send-backs followed:

| Wrong | What the human saw | Right |
|---|---|---|
| A tall card near the camera, any contact blob or sinking into the floor | "everything hangs in the air" | a painting drawn side-on cannot stand on the floor seen from above. Anything the camera reaches that is tall (columns, pedestals, trees, graves) is a **3D mesh**; the same composed layout places it (scale the mesh to the card's height) |
| Low painted heaps and urns kept as cards | still "hanging" | **fold the card's foot onto the floor**: give the quad a few rows, and in WPO lay the vertices below a fold height (~20 % for low heaps, ~10 % for urns) on the ground toward the camera, standing the rest on the fold line. The drawn base then lies on the floor in perspective |
| A contact blob dark only at its centre | invisible: its centre is behind the card | dense core at the foot plus a wide soft ring |
| The human's "it hangs" answered by removing the pieces | "I asked you to fix it, not remove it" | a defect report means repair; remove only on an explicit "remove" |
| Pack meshes picked by name (rubble, ground stones, root patches) | "you can only look at them from one side, part is missing" | many pack meshes are open shells, modelled against a wall or flush with a sculpted ground. Before using one: **four copies turned 0/90/180/270° in one frame** — a shell vanishes or is cut on some. Counting open border edges does not tell: merged pieces and trees are "open" too |
| A flat 3D patch laid level on mounds / sunk to the lowest point under it | the ground pokes through it; a heap half-buried on a slope | low props tilt to the slope across their footprint and sit at their centre; upright ones stay plumb |
| A 2.9M-triangle hero prop reused as scatter | — (found by the triangle count) | check triangles before a mesh goes into a layout |
| The approved trial existed only in the running game; the session restarted it | "why did you roll it back?" | what the human praises goes on disk at once |
| Rules written in one skill, another agent session built a map on the same set | "did you not save the rules?" | enforce them in the builder (a validator that refuses a wrong table) and link them from every skill an agent arrives through |

