---
symptom: a character jerks when a status loop (stun, dizzy, channel) starts or ends, "at some random moment"; head snaps, feet slide when a looping slot montage stops
engine: "5.8.1"
status: observed
date: 2026-11-04
source: measurement — peak bone speeds (head, hand, foot) per frame around PlaySlotAnimationAsDynamicMontage / Montage_Stop, PIE
---
A status loop played as a dynamic slot montage (`PlaySlotAnimationAsDynamicMontage(Loop, Slot, In, Out, 1, 10000)`,
ended with `Montage_Stop(Out)`) reused the short blends of a hit cue (0.1 s in / 0.15 s out). A hit starts and ends
near the idle; a long "look around" loop does not — it drifted up to 25 cm from the idle (head turned 22 cm away, feet
planted elsewhere). Where in the loop the status ended decided how far the 0.15 s blend had to throw the body: head
peaked at 3.4 m/s, feet slid 10 cm. Hence "sometimes it jerks".

- Give long loops their own blend times: 0.4 s in / 0.5 s out cut the exit peaks to head 1.2 m/s, hand 1.3, foot
  0.5 (from 3.4 / 3.75 / 1.4). Expose them as properties so a human can tune by eye.
- Measure before choosing: sample head / hand / foot socket locations every frame through the blend, take the peak
  speed; also measure how far the loop wanders from the idle over its whole length, not just its first frame.
- The feet still slide during the blend if the loop stands them elsewhere — only a clip that keeps the feet fixes that.
