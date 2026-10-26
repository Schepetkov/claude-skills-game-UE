# Cinematic craft reference: staging, coverage, cutting, lenses, reveals

Compiled 2026-10-23. Every rule carries its source in [brackets]. Two tags mark how sure a rule is:
- `[synth]` = my own derivation from the cited rules plus camera geometry, not stated by any one source.
  Treat these as defaults to check in a frame, not as industry fact.
- `[engine]` = read from a UE 5.8.2 source tree (see `engine-api.md`).

Caveat on sources: the key game talks are GDC Vault videos (Witcher 3 2016, AC Odyssey 2019). Their full
contents could not be fetched, so the game-specific rules below come from published write-ups of those
talks. No public source gives AAA studios' lens defaults or shot-length statistics for game dialogue.
Wherever a number is missing, the film-craft number is used and labeled.

Source key (cited by short id below):
- W3a  https://www.gameanim.com/2016/03/23/cinematic-dialogue-witcher-3/ (write-up of Tomsinski, GDC 2016)
- W3b  https://www.tweaktown.com/news/51166/cdpr-reveals-science-behind-witcher-3s-dialogue-animations/index.html
- W3v  https://gdcvault.com/play/1022988/Behind-the-Scenes-of-Cinematic  (video: https://www.youtube.com/watch?v=chf3REzAjgI)
- ACO  https://www.gdcvault.com/play/1026381/Procedural-Generation-of-Cinematic-Dialogues (abstract only)
- DAO  http://www.datoolset.net/wiki/Conversation_cinematics_and_animation (BioWare Dragon Age toolset)
- DAI  https://www.gamesradar.com/games/dragon-age/dragon-age-the-veilguard-wont-suffer-from-inquisitions-weird-camera-issues-because-the-guy-who-made-it-is-creative-director-now-and-he-heard-the-feedback/
- DAI2 https://news.softpedia.com/news/Dragon-Age-Inquisition-Camera-System-Improves-Cut-Scenes-391837.shtml
- ME   https://www.techradar.com/features/how-mass-effect-invented-the-cinematic-rpg-sorry-jj-but-we-did-lens-flares-first
- GOW  https://www.cheatcc.com/articles/understanding-god-of-war-s-unbroken-camera-and-how-it-was-made/ ; https://www.dualshockers.com/god-of-war-podcast-no-cut-camera/
- HFW  https://gamedeveloper.com/gdc2023/designing-the-cinematic-theme-park-of-horizon-forbidden-west
- HAW  https://www.gamedeveloper.com/programming/creating-an-event-driven-cinematic-camera-part-one (Hawkins, procedural camera)
- BBC  https://www.gamedeveloper.com/art/how-to-build-a-better-cutscene
- R180 https://en.wikipedia.org/wiki/180-degree_rule
- R30  https://en.wikipedia.org/wiki/30-degree_rule
- MUR  https://nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch
- BOR  https://davidbordwell.net/blog/2007/05/27/intensified-continuity-revisited/
- OTS  https://www.soundstripe.com/blogs/over-the-shoulder-shot
- DEA  https://www.rogerdeakins.com/?p=220511 (Deakins / Mullen forum thread)
- HR   https://en.wikipedia.org/wiki/Headroom_(photographic_framing) ; https://www.videomaker.com/article/f5/9231-framing-good-shots
- NR   https://human.libretexts.org/Courses/City_College_of_San_Francisco/Video_Production_Handbook_I/08:_Video_Aesthetics/8.05:_Video_Composition
- EYE  https://www.masterclass.com/articles/film-101-what-are-eyelines-how-to-use-eyeline-match-to-tell-a-story-and-drive-a-narrative ; https://blog.frame.io/2023/03/20/eyeline-lessons-from-the-marvelous-mrs-maisel/
- LGT  https://www.redsharknews.com/production/item/4900-the-cinematic-way-to-light-dialogue-scenes ; https://neiloseman.com/introduction-short-key-lighting/
- XKEY https://nofilmschool.com/2018/10/cross-key-technique-lighting-2-interview-subjects-just-3-lights
- RAT  https://en.wikipedia.org/wiki/Lighting_ratio ; https://cloud.wikis.utexas.edu/wiki/spaces/rtf318/pages/80022816/Lighting+ratios
- PRX  https://en.wikipedia.org/wiki/Proxemics
- JL   https://www.adobe.com/creativecloud/video/discover/j-cut-and-l-cut
- JP   https://cinemontage.org/?p=7026 (Jurassic Park brachiosaurus reveal, editor's analysis)
- SPF  https://pixflow.net/blog/spielberg-reaction-shots-emotion/
- BOSS https://gamerant.com/best-monster-reveals-horror-games/ ; https://gamerant.com/dark-souls-best-boss-intro-cutscenes-ranked/ ; https://itch.io/devlog/9177/2021st-week-cutscene-system-new-monsters-art-improvement.amp
- UEDOF https://dev.epicgames.com/documentation/en-us/unreal-engine/cinematic-depth-of-field-in-unreal-engine
- UECUT https://dev.epicgames.com/documentation/en-us/unreal-engine/cinematic-camera-cut-track-in-unreal-engine
- WC3  https://wolfcrow.com/?p=60196 (180 rule with 3+ characters)

---

## 0. Units and camera maths the agent must use

0.1 The UE CineCamera default filmback is "16:9 Digital Film" at 23.76 x 13.365 mm, with a 35 mm lens at
    f/2.8 ("Universal Zoom" preset). This is NOT full frame. [engine: BaseEngine.ini lines 3609, 3621, 3631-3638]
0.2 Every mm value in film literature (and in this file) means full frame (36 x 24 mm stills, or the
    "16:9 DSLR" preset 36 x 20.25). Either set the filmback to "16:9 DSLR", or divide the full-frame mm by 1.515
    on the default filmback (50 mm FF = 33 mm on Digital Film). Pick one convention per project and write it
    into the sequence. [engine + synth]
0.3 Frame height at the subject = distance x sensorHeight / focalLength. On 16:9 DSLR: H = d x 20.25 / f.
    Example: a 50 mm lens at 1.5 m frames 0.61 m vertically, which is an MCU. Use this to place the camera from
    the wanted shot size instead of guessing. [synth, pinhole geometry]
0.4 Manual focus distance is in cm (UE units). Aperture does NOT change exposure in UE, so the f-stop is a
    pure DOF control. Focus Method None disables DOF entirely. [UEDOF]
0.5 Blade-shaped bokeh renders only at the Epic and Cinematic scalability levels. Lower levels draw round
    bokeh. Judge DOF frames at Cinematic. [UEDOF]
0.6 Camera Cut sections cannot leave gaps or overlap unless "Can Blend" is on. Blends interpolate
    transform, focal length and DOF. For long cinematics use one shot (sub-sequence) per camera. [UECUT]
0.7 A camera cut marks the frame as a cut (`SetGameCameraCutThisFrame` / `NotifyCameraCut`), which resets
    temporal history (TAA/TSR, motion blur). If one camera actor teleports between "shots" without a cut
    section, expect a smeared frame. Rule: one CineCameraActor per shot. [engine: MovieSceneCameraCutGameHandler.cpp ~335]

---

## 1. Third-party skills reviewed (what to keep, what is wrong or generic)

**quodsoler/unreal-engine-skills `ue-sequencer-cinematics`** (repo https://github.com/quodsoler/unreal-engine-skills,
raw file `skills/ue-sequencer-cinematics/SKILL.md`; listing https://claudemarketplaces.com/skills/quodsoler/unreal-engine-skills/ue-sequencer-cinematics)
- Useful: API only, and accurate in the parts checked. `GetSequencePlayer()` replaces the deprecated
  `SequencePlayer` property. Bind before `Play()`, because frame 0 evaluates the asset binding. Prefer tag
  bindings (`SetBindingByTag`) over GUIDs. Event endpoints must be UFUNCTIONs on a `ULevelSequenceDirector`
  with zero args or one object arg, and need `CallInEditor` to fire in preview. `OnFinished` fires only on a
  natural end; `Stop()` fires `OnStop`. Keep State needs a manual `SetViewTargetWithBlend` back to the
  player. Camera cuts are evaluated per client, so they do not replicate. `Jump` skips events; `PlayTo`
  fires them. Store the player in a UPROPERTY or GC eats it mid-scene.
- Missing: there is no craft at all. Nothing on lens, shot size, coverage, cutting or staging. Take the API
  gotchas; the craft half of `ue-cinematics` has to come from elsewhere.
**claudskills.com `unreal-sequencer`** (https://claudskills.com/skills/unreal-sequencer/) and **a5c-ai/babysitter
`unreal-sequencer`** (the playbooks.com page returned 404; the claudskills text has the same template shape)
- Generic. It targets UE 5.0 docs and lists capabilities ("camera cuts, rails, events"). Its "best practices"
  ("use master sequences, handle bindings carefully, profile playback") are untestable. Nothing to keep.
**tessl nolanx-ai `continuity-editing-axis-match`** (https://tessl.io/registry/skills/github/nolanx-ai/nolanx.ai/continuity-editing-axis-match)
- Keep: set an axis of action per scene; cross it only with a neutral (on-axis) shot, a camera move that
  wraps around, or a deliberate destabilizing choice; cut at the readable peak of a movement, not after it;
  keep the action vector and body orientation across the cut; the continuation can be tighter.
- Weak: no numbers and no check step (Tessl's own review says the same). It never mentions the 30-degree
  rule or eyeline matching.
**tessl nolanx-ai `shot-size-and-angle-language`** (https://tessl.io/registry/skills/github/nolanx-ai/nolanx.ai/shot-size-and-angle-language)
- Keep: the vocabulary (ECU, CU, MCU, MS, MFS, FS, WS, EWS). The size-to-purpose map: CU/ECU for realization,
  fear and micro-expression; MCU/MS for readable neutral dialogue; FS/WS for body, blocking and threat scale;
  EWS for geography and isolation. The angle meanings: low = power or threat, high = vulnerability, eye level
  = neutral, overhead = pattern or helplessness, canted = rupture. "Every change of size needs dramatic logic."
- Weak: these are vocabulary, not instructions. There are no lenses, distances or heights, and the angles
  are not quantified. The kit table in section 6 fills that gap.
**Verdict for our skill:** the API gotchas are covered (quodsoler) and the vocabulary is covered (nolanx).
What nobody publishes is a numbered, frame-checkable rule set. Sections 2-7 are written to be that.

---

## 2. How game studios build dialogue scenes

### 2.1 The Witcher 3 (CD Projekt Red, Tomsinski, GDC 2016)
- Scale: more than 35 h of dialogue, of which only 2.5 h are mocapped cutscenes. The other 1,463 are
  "systemic" dialogues built in a timeline editor from about 2,400 shared animations. Full mocap is kept for
  unique moments. [W3a]
- A generator makes the first pass of cameras, body animation, facial animation and look-ats. Its inputs are
  actor data, cinematic instructions, and data parsed from the voice-over. Camera-cut markers and an initial
  pass of idles and gestures come from parsing the VO audio. The generator obeys the 180 rule and adds
  establishing shots. Designers re-roll it with one button until the pass is good, then polish by hand. [W3a, W3b]
  -> Agent rule: derive cut points from the line timing first (line starts, pauses, emotion tags), then
     hand-tune. Never place cuts by eye on an empty timeline.
- Workflow, in order: empty timeline holding only the VO, then generate acting and cameras, then fix
  cameras/idles/gestures, then polish face and poses. A simple scene takes minutes. [W3a]
- "A gesture in close-up is better than a line of dialogue." Close-ups carry the emotion beats. [W3a]
- Idles: 35 variations per skeleton type (male, female, dwarf), plus sitting sets. They are grouped by
  emotional state and social status so the generator can choose by mood. [W3a]
- Gestures are additive over the idle, can override it, are bone-masked to body parts, and have a blend
  weight for variety. An additive gesture breaks when the underlying idle drifts far from the base pose it
  was authored on. [W3a]
  -> Check: author each additive gesture against the idle family it will play on.
- Look-ats come in three scopes (body, head only, eyes only). Pose-based look-ats handle special postures
  such as leaning or sitting, blending 3 poses so hands stay planted. [W3a]
- Pose keys fix clipping (arms through bulky bodies). Runtime facial controls enhance key close-ups. Props
  are attached in the editor, and camera framing hides hand-offs (the crossbow example). [W3a]
- Localization stretches the timeline by percentage: a 12 s English scene runs about 14 s in French.
  -> Agent rule: key cuts and gestures to line events, not to absolute seconds, so another language
     (17% longer here) does not break sync. [W3a + synth]
- Lighting: per-scene custom lights tied to the time of day, verified on 9 lighting-condition panels.
  "Deny Area" zones keep wandering NPCs out of the set. [W3a]

### 2.2 BioWare (Dragon Age toolset, DA:Inquisition, Mass Effect)
- Conversations in a known location use a "stage": a set object that fixes camera positions and actor
  blocking, like a theatre set. Conversations that can happen anywhere fall back to a generic
  over-the-shoulder setup. [DAO]
  -> Agent rule: author a stage (marks plus a camera set) for every scripted location, and keep a generic
     OTS rig as the fallback.
- Per line: one camera plus an optional 2nd camera with a "Delay" in seconds, i.e. at most one cut inside a
  line. Anything more becomes a full cutscene. [DAO]
- Per-line actor controls: body look snaps instantly; head look turns smoothly; pose; helmet off; weapons
  sheathed. [DAO]
  -> Check: force helmets off and weapons sheathed before any face shot.
- An emotion filter per line drives the gesture vigour and the facial pass (FaceFX lip sync plus a facial
  emotion layer). Gestures have Start Time (s into the line), Weight (vigour), Speed, and Blend In/Out. An
  animation longer than the VO is flagged red. [DAO]
- KOTOR had about 3 shots per conversation. Mass Effect had to solve camera moves and "fitting everyone in
  frame" across thousands of conversations, using partly automated direction that designers could
  override. [ME]
- Inquisition replaced pure OTS ping-pong on stages with "intelligent" cameras that react to the scene. [DAI2]
  Its zoomed-out camera for minor NPCs drew complaints because it did not favour the player character's
  good angles; Veilguard went back to traditional OTS. [DAI]
  -> Agent rule: a wide "fits both" framing as the default for minor talks reads as cheap. Default to OTS
     or MCU singles; use the wide only to establish.

### 2.3 Ubisoft, Assassin's Creed Odyssey (Paradis, GDC 2019)
- About 30 h of interactive cinematic dialogue. About 15% of scenes were fully procedural, and every scene
  had some procedural part. Staging, acting, editing, framing and lighting were all generated, then refined
  by cinematic designers. [ACO] The detailed rules are only in the members-only video.

### 2.4 Santa Monica, God of War (2018)
- The camera never cuts, cutscenes included. It is an OTS follow camera treated as "an additional character
  in the scene". Takes are stitched invisibly (about 100 long takes). The script was not allowed to say "cut
  to", and writers worked with the camera director (Dori Arazi) so they did not paint the camera into a
  corner. Only a handful of actual tricks; the rest is planning. [GOW]
  -> Agent rule: a one-shot scene needs blocking that moves actors to the camera, not the reverse, and every
     transition hidden behind a wipe (foreground object, body, whip-pan). It is a style choice for the whole
     game, not a fix for a single scene.

### 2.5 Guerrilla, Horizon Forbidden West (Auray, GDC 2023)
- Tiers by intensity: main quests get bespoke cameras and animation ("roller coasters"); small exchanges
  get cheaper systemic treatment ("teacups"). Scenes are blocked by scouting the real level in-engine with a
  debug camera. [HFW]
  -> Agent rule: scout and frame in the actual level map, never in an empty test map.

### 2.6 Procedural camera geometry (Hawkins, "Event-Driven Cinematic Camera")
- Line of action: for one actor, it is their facing; for two actors, it is the vector from the primary to
  the secondary actor. All cuts must respect the line as it stands at the moment of the cut. [HAW]
- Triangle system: the master/establishing camera sits at the apex, and the other cameras favour one actor.
  Four basic two-actor setups, with these horizontal angles in Hawkins' frame: standard -45°,
  over-the-shoulder 75°, POV -90°, profile 0°. [HAW]
- Emphasis: "full" puts the focus at frame centre; "two-thirds" puts it 1/3 across the frame; "one-half"
  puts it 1/4 across. [HAW] This matches the OTS convention of about 2/3 of the frame on the speaker.
- Shot sizes are defined by the head and body spheres: CU = head fills frame; MCU = 1/3 body; MS = 1/2 body;
  MFS = 3/4 body; FS = whole body; LS = body at half the screen. [HAW]
- Occlusion: cast rays from the camera to each actor's bounding sphere. If blocked, try the next shot on an
  ordered fallback list. [HAW]
  -> Check: every shot has at least one unobstructed ray to each framed head.
- Actors moving in opposite directions: cut to a new scene and a new line. Moving the camera to establish a
  new line inside a scene should be rare. [HAW]

### 2.7 Production lessons that apply to an agent [BBC]
- Lock camera, lens, size and move in layout before animating. Block the body roughly, but time the key
  marks (head turns, walk starts and stops, gestures) precisely.
- Give camera moves ease-in and ease-out and keep them to live-action rigs (dolly, crane, pan, tilt,
  handheld). Unmotivated "CG camera" moves disorient.
- Avoid ECUs on assets that cannot hold them (low-poly face, weak hair, weak lip sync). Hide hard actions
  off-screen with sound plus a reaction shot. Do not show feet on moving characters without proper walk
  cycles.
- Hide the gameplay-to-cutscene seam with a contrasting angle, an insert on a detail the player already
  saw, a cutaway, or a hand-off. Cut "shoe-leather" travel unless it builds tension.

---

## 3. Dialogue camera rules (frame-checkable)

### 3.1 Axis, eyelines, matching
D1. Before placing any camera, draw the axis between the two talkers' heads. Every camera in the exchange
    stays on one side of it. Check: speaker A is always screen-left and B always screen-right. [R180, HAW]
D2. Eyelines must meet. If A looks camera-left in A's single, B looks camera-right in B's reverse. [OTS, EYE]
D3. Reverse shots are matched pairs: the same lens, height, distance and size on both sides. Deviate only on
    purpose (see D9). [OTS, EYE, DEA]
D4. The eyeline sits a few degrees off the lens, on the side of the listener. Into the lens = direct address
    or fourth-wall break; use only on purpose. Tighter eyeline (closer to lens) = more intimacy. [EYE, DEA]
D5. In UE, aim the look-at target at the other actor's eye socket, not their actor origin. For a tight
    eyeline in a close single, offset the look-at target toward the lens by up to about 5° rather than
    moving the camera inside the listener's head. [synth from D4 and DEA "mark on the matte box"]
D6. OTS: the foreground shoulder takes about 1/3 of the frame and is out of focus. Focus is on the eye of
    the actor facing camera. Larger than 1/3 and it blocks the shot; a thin edge rebalances power toward the
    far actor. [OTS] Check by screen-space bounds.
D7. Leave enough distance between actors that the shoulder reads as foreground, not as part of the other
    head. [OTS] For human scale that is 1.2-2.0 m eye to eye (see section 5). [synth + PRX]
D8. Camera height for a neutral read = eye height of the actor facing camera. [OTS]
D9. Power: raise or lower the camera relative to that eye line to say who holds the upper hand. [OTS,
    nolanx] Testable default [synth]: low angle = lens 25-40 cm below eye line, tilted up 8-15°; high angle =
    the same amount above, tilted down. Keep it mirrored across the reverse pair (the dominant one shot from
    below, the other from above) only while the power relation holds.

### 3.2 Composition
C1. Eyes on the upper-third line (about 33% down the frame). Eyes at 28% already reads as too little
    headroom. A CU may crop the top of the head; it must still show neck or shoulder tops. [HR]
C2. Nose (look) room: more space in front of the face than behind. Profile needs the most; frontal needs the
    least. Put the eyes near a third-intersection, facing the open side. [NR, OTS]
C3. When cutting wide to close, re-check that headroom changes proportionally; zooming in means tilting up
    to keep the eyes on the third. [HR, NR]
C4. Speaker emphasis: speaker's face centre about 1/3 across the frame in OTS and singles; 1/2 or full
    centre only for confrontational, symmetric frontal shots. [HAW]

### 3.3 Lens and depth of field (full-frame mm)
L1. Normal range is roughly 35-70 mm (close to the human eye's view). Wider exaggerates depth and distance
    between people; longer flattens and compresses them together. [Columbia technical-camera module via search;
    https://smorgasbord.cdp.arch.columbia.edu/modules/40-rendering-with-blender/252-technical-camera]
L2. OTS: 50-85 mm full frame is the typical band. A longer OTS compresses the pair and keeps the shoulder
    from looming. [OTS, DEA (Mullen)]
L3. Deakins' own habit: OTS on 32-35 mm and the closer single on 40-50 mm, "closer to the human view". Wide
    close-ups (25-28 mm) force a tight eyeline onto the lens edge. [DEA]
    -> Two valid styles. "Intimate" = move the camera in with 35-50 mm. "Classic" = stay back with 75-100 mm.
       Pick one per scene and keep both sides of the reverse identical. [synth from DEA, OTS]
L4. Use the same lens on both reverses (D3). Between successive shots of the same subject, a lens change
    under 20 mm reads as a jump cut. [R30]
L5. Focus on the near eye of the subject. Focus Method Manual or Tracking. Smooth Focus Changes ON for pulls
    between speakers within one shot. [OTS, UEDOF]
L6. DOF starting points [synth; UEDOF only gives examples of f/1.4, 2.8, 5.6 at 4-10 m]:
    singles and OTS f/2.0-2.8; two-shots f/4 so both faces are sharp; wides and establishing f/5.6-8.
    Check: both faces sharp in any shot that contains two speaking faces.
L7. Do not leave the default f/2.8 on wides: at 35 mm it blurs the set you just built to establish. [synth]

### 3.4 Cutting dialogue
E1. Priority when choosing a cut (Murch's "rule of six"): emotion, then story, rhythm, eye-trace,
    2D screen plane (screen direction, 180), then 3D spatial continuity. Give up the lower ones first. [MUR]
E2. A new shot of the same subject needs either 30° or more of camera angle change, or a 20 mm or larger
    focal-length change (axial cut). Otherwise it is a jump cut. [R30]
E3. Shot size changes should be noticeable but not disorienting (Murch's example: full figure to ankles-up
    is enough). [R30] Default [synth]: step at least one size on the ladder (MS->MCU, MCU->CU).
E4. Do not cut on the exact syllable a line starts. Use L-cuts (the speaker's audio carries over onto the
    listener's face) and J-cuts (the next speaker is heard before seen). Overlap of about 0.5 s is usually
    enough; "feel it, don't see it". [JL]
E5. Reaction shots: give the listener the beat when a line lands (insult, reveal, decision). L-cut onto
    their face. Real people react before they respond. [JL, W3a "gesture in close-up"]
E6. Cut points come from line events: line start, end, internal pauses, emotion change. Not from a fixed
    timer. [W3a, W3b]
E7. Shot length reference (film, no game data published): modern Hollywood dialogue ASL 2-4 s; Ephron's
    1998 OTS/singles dialogue about 4.1-4.3 s per shot; Lubitsch's 1940 two-shot style held 21-82 s.
    Shorter = more intensity. [BOR]
    -> Game default [synth]: 3-6 s per shot, at most one cut inside a line (BioWare's cap, [DAO]), and no
       shot under 1.0 s except inserts and impacts.
E8. Build intensity by moving down the size ladder over the scene (WS -> MS -> MCU -> CU). Save the CU for
    the strongest exchange. [BOR on Lubitsch]
E9. Re-establish with a wide after big blocking changes, an entrance or exit, or more than about 30 s of
    singles. Witcher's generator always adds establishing shots. [W3a, synth for the 30 s]
E10. Avoid repetition: rotate within the matched pairs (OTS <-> single <-> two-shot) according to emotion,
     not at random. [nolanx shot-size skill: "don't vary shots randomly"]. Witcher re-rolls the generator
     until the pass reads well, then keeps it. [W3b]
E11. Match on action: cut during the readable peak of a motion (head turn, rise, draw), with matched
     direction and body orientation. Never cut after the motion has finished. [nolanx continuity]
E12. Inserts (a hand, a weapon, a portal rune) cut in on a detail the player already saw or that the line
     names. They are the safest way to hide a gameplay-to-cutscene seam. [BBC]

### 3.5 Crossing the line safely
X1. Allowed ways to cross: (a) the camera visibly arcs across during the shot; (b) a neutral shot on the axis
    (head-on or from behind) as a buffer; (c) an actor moves and redefines the line on screen; (d) a
    pre-lapped line of dialogue hides an accidental cross; (e) a deliberate cross to disorient (ambush,
    betrayal, possession). [R180, nolanx]
X2. Crossing harms spatial understanding but not story comprehension or enjoyment much. Accept it only if
    the gain is real. [R180]

### 3.6 Three or more characters
T1. Pick the axis between the two main talkers and keep everyone, the third included, on the same side
    of the camera. [WC3]
T2. When the speaker changes to the third character, the active axis moves to that pair. Before cutting on
    the new axis, show the change: a two-shot or wide where the speaker turns, or the speaker's head turn as a
    cut point (match on action). [indiefilmhustle via search https://indiefilmhustle.com/180-degree-rule/, E11]
T3. Default triangle stage [synth from HAW triangle]: actors on an equilateral-ish triangle with 1.5-2.5 m
    sides, open toward camera (a "V" open at the bottom). The master camera sits at the apex outside the
    open side. Singles are shot from inside the opposite edges so each actor's eyeline alternates sides.
T4. Mass Effect's problem statement: in a group shot, "fit everyone in frame". The fallback is a wider
    two-shot or group shot, not a jump across the axis. [ME]

### 3.7 Acting layer in dialogue
A1. Layer stack: mood idle (chosen by emotion and status) -> additive gestures (bone-masked, weighted) ->
    facial and lip sync -> look-at (eyes, head, body scopes). [W3a, DAO]
A2. Look-at: the body snaps or stays planted, and the head turns smoothly. [DAO] The eyes lead the head
    and the head leads the body; a blink placed in the middle of a large head turn hides the eye jump. Eyes
    moving alone look disconnected, so add a little head and chest drift. [animation practice via search;
    https://polycount.com/discussion/comment/2588194, Lynda "21 Foundations of Animation"]
A3. Flag every gesture that outlasts its line (BioWare marks them red). [DAO]
A4. The listener is never frozen: a listen idle with blinks and small nods on the speaker's emphasis
    points. Witcher grouped idles by emotion for exactly this. [W3a; nod-on-emphasis is synth]

---

## 4. Lighting a dialogue
G1. Short key: the key light sits on the far side of the eyeline from camera, so the camera-side cheek is
    in shadow. Near-side ("broad") key looks flatter. [LGT]
G2. Cross key / cross backlight: in a two-hander, each actor's key is also the other's backlight. With the
    180 rule respected, this keeps the camera-side of both faces in shadow from every camera position. 2-3
    lights cover the whole coverage. [LGT, XKEY]
G3. Shoot the master toward the key or backlight. Then the OTS and singles inherit a short key automatically.
    [LGT]
G4. Key-to-fill ratios: 2:1 (1 stop) soft and readable; 4:1 (2 stops) dramatic; 8:1 (3 stops) very low key.
    Rarely go past 8:1. [RAT]
    -> In UE [synth]: fill = sky or bounce or a low-intensity rect light; verify with the Pixel Inspector or
       an exposure-locked frame that the shadow-side cheek is 1-3 EV under the key side, matching the mood.
G5. Motivate the key from a practical source in the wide (a torch, a portal, a window), then cheat a
    larger, softer source in the same direction for the close singles. [LGT]
G6. Per-shot cheat lights [synth; Witcher used per-scene custom lights tied to time of day, W3a]: in UE,
    use lighting channels or light-function-free rect lights spawned in that shot's sub-sequence, so a CU
    eye light or rim light never contaminates the wide. Check: toggle the light; only the intended face
    changes.
G7. Lock exposure (manual, or narrow min/max EV) for the whole scene. Auto-exposure pumping on backlit
    shots is the "beginner problem" with backlight. [LGT; UE implementation is synth]
G8. Lighting must survive the actual level and time of day. Witcher validated 9 lighting-condition panels.
    [W3a]

---

## 5. Staging and spacing (marks)
S1. Proxemics (Hall): intimate under 0.46 m; personal 0.46-1.22 m; social 1.2-3.7 m; public beyond. Hall
    meant these as guides, not laws. [PRX]
S2. Dialogue mark defaults [synth from S1 and D7]: friends or conspirators 0.9-1.2 m eye to eye; neutral
    or formal 1.4-2.0 m; hostile standoff 2.5-4 m (shoot more singles; the OTS shoulder gets small). A
    creature 2x human height needs about 2x the distance for the same OTS geometry.
S3. Angle the talkers 10-30° open toward camera ("cheat out") rather than in pure profile, so the singles
    see three-quarter faces. [synth; standard stage practice, consistent with HAW "standard" -45° setup]
S4. Marks are fixed points per stage: one mark per actor per beat, and one camera set per mark layout.
    Changing marks mid-scene = a new beat = re-establish (E9). [DAO stages, synth]
S5. Clear the set of moving NPCs (Witcher's "Deny Area" around dialogues). [W3a]

---

## 6. Default dialogue camera kit (synthesized)

Full-frame mm on the "16:9 DSLR" filmback (36 x 20.25). On the default UE filmback divide mm by 1.515
(rule 0.2). The distance is camera-to-subject's-eyes, derived from H = d x 20.25 / f with an average
1.8 m human. Height is relative to the subject's eye line. "Offset" is the horizontal angle between the
camera's view direction and the A-B axis, measured on the camera's side of the line (0° = profile along
the line, 90° = perpendicular). Sources of the shape: lens bands [OTS, DEA, L1], sizes [HAW, nolanx],
angles [HAW triangle], usage [W3a, DAO, BOR]. All numbers are `[synth]` defaults to verify in a frame.

| Shot | Lens (FF mm) | Frame height at subject | Distance | Camera height | Offset from axis | When used |
|---|---|---|---|---|---|---|
| Establishing / master (EWS-WS) | 18-28 | 3-6 m | 5-10 m | eye level or +1-3 m (high = geography) | 80-100°, on the apex of the triangle | First shot of a scene; re-establish after blocking change, entrance, or about 30 s of singles |
| Two-shot (MFS-MS, both faces) | 28-35 | 1.0-1.4 m | 2.5-3.5 m | eye level | 60-90° | Neutral exchanges, a turn in power, someone moves, 3-person reset |
| OTS (dirty single), MS-MCU | 50-85 | 0.6-0.8 m | 1.6-3.0 m (from the far actor) | far actor's eye level | 15-30° (behind the listener's shoulder) | Workhorse of dialogue; keeps both people's relation; shoulder 1/3 of frame, soft |
| Clean single MCU | 50-65 | 0.5-0.6 m | 1.3-1.9 m | eye level (±25-40 cm for power) | 20-35° | Most lines once geography is set; listener reactions |
| Close-up CU | 75-100 | 0.30-0.38 m | 1.2-1.9 m | eye level | 25-40° | Emotional turn, decision, lie, threat; the scene's strongest beats |
| Extreme CU (eyes / mouth) | 100-135 | 0.12-0.18 m | 0.7-1.2 m | eye level | 30-45° | One beat per scene at most; only if the face, eyes and lip sync hold up [BBC] |
| Insert (hand, prop, rune) | 50-100 (macro feel) | 0.1-0.4 m | as needed | on the object | free, keep screen direction | Name the object the line mentions; hide a seam [BBC] |
| POV / subjective | 24-35 | n/a | at the viewer's eye | the viewer's eye height | on axis, 0° from the viewer | Only when the viewer's subjective state matters (terror, a reveal) |
| Low-angle hero/threat | 24-35 | FS-MS | 2-5 m | 0.3-1.0 m from ground, tilt up 10-25° | 30-60° | The dominant party, creature reveal (section 7) |
| High-angle exposure | 35-50 | MS-FS | 2-4 m | 0.5-1.5 m above eye, tilt down 10-20° | 30-60° | The diminished party, defeat, surveillance |

Kit rules:
K1. One matched pair per pairing: OTS-A/OTS-B and CU-A/CU-B share lens, distance and height. [D3]
K2. Any cut within the same subject respects E2 (30° or 20 mm). Check by comparing camera transforms.
K3. f-stop: f/2-2.8 on OTS, singles and CU; f/4 on two-shots; f/5.6-8 on wides. [L6]
K4. A minimal 2-person scene = 1 master + OTS pair + MCU pair (5 cameras). Add a CU pair for the emotional
    peak. This is the Witcher/BioWare "stage" set in spirit. [W3a, DAO, synth]

---

## 7. Creature reveal and boss arrival (e.g. a demon out of a portal)

Sourced techniques:
R1. Build tension before the reveal. One dev learned to use rooms or beats that escalate before the monster
    breaks through. [BOSS (itch devlog)]
R2. Sound first. Cleric Beast opens on a howl and rattling chains before it appears. In Jurassic Park the
    footfalls and guttural sound are held until about 1 s before the creature is seen. [BOSS, JP]
R3. Show the reaction before the creature (the "Spielberg face": eyes wide, looking slightly up, mouth a
    little open). Jurassic Park delays the brachiosaurus with a push-in on the jeep, Grant standing, and 3
    shots of Sattler before the reveal. A hand even turns her head toward it. [JP, SPF]
R4. Then the reveal: the camera moves behind the onlookers and rises as the creature fills the frame, so
    humans in the foreground give scale. [JP]
R5. Partial reveal: a single glowing eye in darkness (Super Metroid); the spider body first, the true form
    last (Quelaag); one brother speaks while the other stays in shadow (Lothric). Intimidation grows "as more
    of her frame appears". [BOSS]
R6. Tilt-up for scale: the ground trembles, then the camera tilts up to the giant (Shadow of the Colossus).
    A slow pan up a huge form while a storm rages, until the viewer realizes it is the creature (Malus, DA:I).
    [BOSS]
R7. Misdirection: set up one threat, then drop a second from above (Ornstein onto Smough). Arrivals from the
    ceiling or from above create dread. [BOSS]
R8. React on a face again after the reveal: Silent Hill 2 Remake holds on Angela's terror before the
    monster is seen clearly. [BOSS]

Synthesized reveal template for a portal entrance (`[synth]` from R1-R8, E7, section 6; check every number
in a frame):
P1. Beat 1, omen (2-4 s): wide of the place; light and sound change first (portal hum, a light flicker,
    dust). Do not show the creature yet. [R1, R2]
P2. Beat 2, reaction (1.5-3 s): MCU or CU of the witness, eyes slightly up toward the portal, with the key
    light shifting to portal colour on their face. Optional slow push-in of 5-10% frame height. [R3]
P3. Beat 3, partial (1-2 s per shot, 1-3 shots): inserts of the creature's parts in shadow, or a silhouette
    against the portal glow: a claw on the rim, a horn, an eye. [R5]
P4. Beat 4, full reveal (3-5 s, the longest shot of the sequence): low angle (lens 0.3-1.0 m above ground,
    tilt up 15-25°), 24-35 mm, with a human or a known object in the foreground or mid-ground for scale, OR
    a slow tilt or rise up the body ending on the face. Creature head in the upper third; give it headroom so
    it does not look cramped, or crop the top on purpose to read "too big for the frame". [R4, R6, C1]
P5. Beat 5, hold on reaction (1.5-3 s): back to the witness CU, matching the earlier reaction shot's lens
    and side, so the change in their face reads. [R3, R8]
P6. Beat 6, establish the new geography (2-3 s): a two-shot or wide with both creature and witness on the
    same axis that the dialogue will use. From here, section 3 rules apply with the creature as a talker:
    scale its marks (S2) and keep its CU from below and the human's from slightly above while it dominates.
    [E9, D9]
P7. Sound sync: the first creature sound at least 1 s before its first frame. Its loudest hit (roar, impact)
    lands on the cut to the full reveal, not before it. [R2; the cut alignment is synth]
P8. Do not reveal in the same frame as the first sound, and do not show the full body in the first creature
    shot. The full reveal is earned by at least 2 prior beats (omen plus reaction). [synth from R1-R5]

---

## 8. Agent checklist per shot (pass/fail)
1. Filmback convention stated; lens in FF mm matches the kit band for its size. (0.2, section 6)
2. Camera on the correct side of the active axis; speaker screen side unchanged since the last shot. (D1)
3. Eyeline toward the listener's side, a few degrees off lens; reverse matches. (D2, D4)
4. Eyes on the upper third (30-36% from top); look room on the facing side. (C1, C2)
5. OTS shoulder no more than 1/3 of the frame and out of focus; focus on the near eye. (D6, L5)
6. Change from the previous shot of the same subject: 30° or more, or 20 mm or more, plus a size step. (E2, E3)
7. Cut is on a line event or the peak of a motion, with an L/J overlap of about 0.5 s if dialogue spans it. (E4, E6, E11)
8. Shot length 1-6 s (inserts can be shorter); at most 1 cut inside a line. (E7)
9. No occluder on the ray to each framed head. (HAW)
10. Shadow-side cheek is toward camera (short key) unless the shot is meant to be flat. (G1)
11. One CineCameraActor per shot; cut sections without gaps; DOF Focus Method not None. (0.6, 0.7, 0.4)
12. Re-establishing wide present after any blocking change. (E9)
