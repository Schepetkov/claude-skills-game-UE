---
name: ue-networking
description: Unreal Engine 5.8 multiplayer — replication (legacy + Iris), Push Model, RPCs, subobjects, relevancy/dormancy, bandwidth budgeting, lag/jitter simulation, and network profiling. Use when writing or debugging any replicated actor/component/property, choosing between Iris and the generic replication system, diagnosing desync/rubber-banding/"it works in PIE but not on a dedicated server", or tuning net bandwidth.
license: MIT
metadata:
  engine: "Unreal Engine 5.8"
---

# UE 5.8 Networking

## Ground truth rule (read first)

**Never quote a cvar, ini key, or engine API from memory or from a web doc without verifying it against the engine build you are actually targeting.** Epic's published documentation lags the source, sometimes by a full rename.

Two verified examples as of 5.8.1: the MegaLights doc page says `r.MegaLights.Allow` while the source declares `r.MegaLights.Allowed`; and `bUseIris = true` in `*.Target.cs` — repeated across blogs and AI answers — **does not exist** in 5.8's UnrealBuildTool at all.

Locate the engine source (see [Finding the engine source](#finding-the-engine-source) at the bottom), then:

```bash
# a cvar's real name + default + help text
grep -rn 'TEXT("net\.' Engine/Source/Runtime/Net/ Engine/Source/Runtime/Engine/Private/ | grep -i <topic>
# an API
grep -rn "SetNetDormancy" Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h
```

## Decision 1: Iris or generic replication?

In 5.8 Iris is **production-ready** (it was Experimental through 5.7). It is still **opt-in**; the generic system remains the default.

| Concurrent replicated actors | Recommendation |
|---|---|
| < ~100 | Stay on generic. Iris migration cost will not pay back. |
| ~100–300 | Evaluate. Measure first (`stat net`, Network Insights) before migrating. |
| 300+, or heavy per-connection relevancy work | Iris. Its filtering/prioritization scales where `AActor::IsNetRelevantFor` fan-out does not. |

Low-actor-count games — co-op, arena, turn-based — should stay on generic replication. Do not propose an Iris migration unless the user asks or profiling shows server replication cost dominating.

Hard blocker: **Replication Graph and Iris cannot coexist on the same net driver.** Iris has no node-based control; you express the same intent with filters and prioritizers.

Full migration details: [references/iris.md](references/iris.md).

## Decision 2: Push Model — adopt regardless

Push Model (dirty-tracking instead of per-property comparison) works with **both** systems and is where 5.7/5.8 are steering the engine. Adopt it on hot-path properties now; it is the prerequisite for any later Iris move and costs nothing to do early.

```cpp
// Header
UPROPERTY(ReplicatedUsing = OnRep_Health)
float Health = 100.f;

// GetLifetimeReplicatedProps
FDoRepLifetimeParams Params;
Params.bIsPushBased = true;
Params.Condition = COND_None;
DOREPLIFETIME_WITH_PARAMS_FAST(AMyActor, Health, Params);

// Every write site — no exceptions
void AMyActor::SetHealth(float NewHealth)
{
    Health = NewHealth;
    MARK_PROPERTY_DIRTY_FROM_NAME(AMyActor, Health, this);
}
```

**The failure mode:** a write that skips `MARK_PROPERTY_DIRTY_FROM_NAME` never replicates, and it fails *silently*. Enforce this by making the property private with a single setter. When reviewing code, treat any direct assignment to a push-based property outside its setter as a bug.

Enable in `Config/DefaultEngine.ini`:

```ini
[SystemSettings]
net.IsPushModelEnabled=1
```

The macros live in the `NetCore` module — add it to the consuming module's `Build.cs`.

## Server authority checklist

Before writing any gameplay-affecting code, answer these:

1. **Who owns the decision?** Server. Clients send intent (`Server_` RPC), never results.
2. **Is the RPC validated?** Use `WithValidation` and actually implement `_Validate` — return `false` on impossible input; it disconnects the cheater.
3. **Is state replicated or RPC'd?** Replicate *state*; RPC *events*. State survives joins and relevancy changes; multicast RPCs do not.
4. **Does a late joiner see the right thing?** If the answer relies on a multicast that already fired, it's a bug — move it to replicated state + `OnRep_`.
5. **Does it run in standalone?** `HasAuthority()` is true in standalone, so authority-gated code must still do the local cosmetic work. Common pattern: server mutates state, `OnRep_` plays cosmetics, and the server calls `OnRep_` itself.

## RPC rules that bite

- `Server` RPCs require the calling client to **own** the actor (`SetOwner` to the `PlayerController`, or be a Pawn possessed by it). Silent no-op otherwise — check the log for `No owning connection`.
- `NetMulticast` is unreliable-by-default and **drops for non-relevant clients**. Never carry state in it.
- `Reliable` RPCs share a per-connection queue. Spamming them **overflows the reliable buffer and disconnects the client**. Never call a reliable RPC from `Tick`.
- RPC parameters are serialized per-call. Passing a big `TArray` in a multicast every frame is the #1 bandwidth bug.

## Subobject replication (5.8 default path)

The registered-subobject list replaced `ReplicateSubObjects()`:

```cpp
AMyActor::AMyActor()
{
    bReplicates = true;
    bReplicateUsingRegisteredSubObjectList = true;
}

// when the subobject is created (server side)
AddReplicatedSubObject(MyComponentOrObject);
// when destroyed
RemoveReplicatedSubObject(MyComponentOrObject);
```

Iris **requires** this path. The legacy `ReplicateSubObjects()` override is deprecated — if you find it in touched code, convert it rather than extending it.

## Bandwidth and update-rate tuning

`NetUpdateFrequency` and `MinNetUpdateFrequency` became private in 5.5 — **use the accessors**, direct access is a deprecation error:

```cpp
SetNetUpdateFrequency(10.f);
SetMinNetUpdateFrequency(2.f);
```

Other levers, in the order to try them:

1. `SetNetUpdateFrequency` down. Most actors do not need 100 Hz.
2. `NetCullDistanceSquared` — cheapest possible relevancy win.
3. `SetNetDormancy(DORM_Initial / DORM_DormantAll)` for actors that change rarely; `FlushNetDormancy()` on change.
4. `COND_*` replication conditions (`COND_OwnerOnly`, `COND_SkipOwner`, `COND_InitialOnly`) — free bandwidth, no logic change.
5. `FFastArraySerializer` for lists that change incrementally instead of replicating the whole `TArray`.
6. Quantize. A `float` position that could be an `int16` in grid space is a 2× waste. Grid-based games should replicate **grid coordinates**, not world transforms.

## Debugging workflow

Always reproduce on a **dedicated server**, not Listen/PIE-single-process — ownership and authority bugs hide in PIE:

```
PIE settings: Net Mode = Play As Client, Number of Players = 2+, Run Dedicated Server = on
```

Console commands and switches (grep each in source before relying on it):

| Command | Use |
|---|---|
| `stat net` | Ping, in/out packets, bandwidth per second — the first look |
| `net.PktLag 120`, `net.PktLagVariance 40`, `net.PktLoss 5` | Simulate a real connection. **Run this before calling anything "done".** |
| `net.DebugDraw 1` | Visualize replicated actors/relevancy in world |
| `-NetTrace=1` + Unreal Insights | Per-property bandwidth attribution — the only way to find *which* property is eating the pipe |
| `Log LogNetTraffic Verbose` | Per-call RPC tracing |

Insights: launch with `-trace=cpu,gpu,frame,net -NetTrace=1`, then the **Networking** tab attributes bytes to properties and RPCs by name.

## Common bugs, ranked by how often they appear

1. Push-model property written without `MARK_PROPERTY_DIRTY_FROM_NAME` → silent non-replication.
2. Reliable RPC in `Tick` → reliable buffer overflow → client disconnect under load.
3. Multicast used to deliver state → late joiners and out-of-relevancy clients desync.
4. `Server_` RPC on a non-owned actor → silently dropped.
5. `OnRep_` never called on the server → cosmetics only work for clients. Call it explicitly from the setter on authority.
6. Component replication forgotten: `SetIsReplicated(true)` on the component, in addition to the actor replicating.
7. Property added to `GetLifetimeReplicatedProps` with the wrong class argument in the `DOREPLIFETIME` macro.
8. Object pointer replicated to a client that has not loaded/received that object → arrives as `nullptr`. Guard every replicated `UObject*` in `OnRep_`.

## Genre note: turn-based / grid games

Turn-based designs invert the usual real-time assumptions — apply these instead:

- Replicate **the authoritative turn state machine**, not per-frame interpolated transforms. One `FTurnState` struct with a turn index is cheaper and desync-proof.
- Use a monotonically increasing `TurnIndex`/`CommandIndex` so clients can reject stale or replayed input. The server rejects any command whose index isn't current.
- Actions are **commands**, not continuous input: `Server_SubmitOrder(FOrder)` validated against the current turn owner. Never trust a client's claim that it is their turn.
- Animation/VFX of a resolved turn is cosmetic: replicate the *result*, let each client play it locally from `OnRep_`. Do not multicast per-step animation events.
- Dormancy is nearly free here: units sit at `DORM_DormantAll` between turns, `FlushNetDormancy()` on resolution.

## Finding the engine source

| Engine type | Where the source lives |
|---|---|
| **Source build** | The `EngineAssociation` GUID in the `.uproject` maps to a path under `HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds` (Windows) or `~/.config/Epic/UnrealEngine/Install.ini` (Linux). Full `Engine/Source/` tree — everything in this skill is greppable. |
| **Launcher install** | `EngineAssociation` is a version string (`"5.8"`). Path under `HKLM:\SOFTWARE\EpicGames\Unreal Engine\<version>` → `InstalledDirectory`. Ships public headers but **not** the `Private/` sources where most cvars are declared. |

With only a Launcher install, confirm cvar names at runtime instead: the console autocompletes them, and `DumpConsoleCommands` writes the full list. Say explicitly which method you used when quoting a name.

## Related

- [references/iris.md](references/iris.md) — Iris enable steps verified against 5.8.1 source, filtering/prioritization, what breaks
- [references/replication-cookbook.md](references/replication-cookbook.md) — copy-paste patterns: conditions, fast arrays, dormancy, RPC validation
