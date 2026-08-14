# Replication Cookbook — UE 5.8

Copy-paste patterns. Verify every symbol against your engine's source before shipping advice built on it.

## Push-model property, done correctly

```cpp
// MyUnit.h
UCLASS()
class AMyUnit : public AActor
{
    GENERATED_BODY()
public:
    AMyUnit();
    void SetHealth(float NewHealth);
    float GetHealth() const { return Health; }

protected:
    UFUNCTION() void OnRep_Health(float OldHealth);
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    // private on purpose: the setter is the only legal write path
    UPROPERTY(ReplicatedUsing = OnRep_Health)
    float Health = 100.f;
};
```

```cpp
// MyUnit.cpp
#include "Net/UnrealNetwork.h"
#include "Net/Core/PushModel/PushModel.h"

AMyUnit::AMyUnit()
{
    bReplicates = true;
    bReplicateUsingRegisteredSubObjectList = true;
    SetNetUpdateFrequency(10.f);       // 5.5+: accessors, not the raw field
    SetMinNetUpdateFrequency(2.f);
}

void AMyUnit::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    FDoRepLifetimeParams Params;
    Params.bIsPushBased = true;
    Params.Condition = COND_None;
    Params.RepNotifyCondition = REPNOTIFY_OnChanged;
    DOREPLIFETIME_WITH_PARAMS_FAST(AMyUnit, Health, Params);
}

void AMyUnit::SetHealth(float NewHealth)
{
    check(HasAuthority());
    const float Old = Health;
    Health = NewHealth;
    MARK_PROPERTY_DIRTY_FROM_NAME(AMyUnit, Health, this);
    OnRep_Health(Old);                 // server runs its own cosmetics
}
```

`Build.cs` needs `NetCore` for the push-model macros:

```csharp
PublicDependencyModuleNames.AddRange(new string[] { "NetCore" });
```

## Replication conditions — free bandwidth

| Condition | Sends to |
|---|---|
| `COND_None` | everyone |
| `COND_OwnerOnly` | owning connection only — inventory, private state |
| `COND_SkipOwner` | everyone except owner — owner already predicted it |
| `COND_InitialOnly` | once, on first replication — spawn config |
| `COND_SimulatedOnly` | non-autonomous proxies |
| `COND_Custom` | gated by `DOREPLIFETIME_ACTIVE_OVERRIDE` |

`COND_InitialOnly` on spawn-time constants (team id, archetype, faction) is the single highest-value/lowest-risk change on most projects.

## Fast array — incremental list replication

```cpp
USTRUCT()
struct FUnitOrder : public FFastArraySerializerItem
{
    GENERATED_BODY()
    UPROPERTY() int32 UnitId = 0;
    UPROPERTY() FIntPoint TargetTile = FIntPoint::ZeroValue;

    void PostReplicatedAdd(const struct FUnitOrderArray& Serializer);
    void PostReplicatedChange(const struct FUnitOrderArray& Serializer);
    void PreReplicatedRemove(const struct FUnitOrderArray& Serializer);
};

USTRUCT()
struct FUnitOrderArray : public FFastArraySerializer
{
    GENERATED_BODY()
    UPROPERTY() TArray<FUnitOrder> Items;

    bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
    {
        return FFastArraySerializer::FastArrayDeltaSerialize<FUnitOrder, FUnitOrderArray>(Items, DeltaParms, *this);
    }
};

template<> struct TStructOpsTypeTraits<FUnitOrderArray> : public TStructOpsTypeTraitsBase2<FUnitOrderArray>
{
    enum { WithNetDeltaSerializer = true };
};
```

The server must call `MarkItemDirty(Item)` after mutating an item and `MarkArrayDirty()` after add/remove — same silent-failure class as push model.

## Dormancy

```cpp
// spawn dormant, wake only when something actually changes
Unit->SetNetDormancy(DORM_Initial);

// when the server changes it
Unit->FlushNetDormancy();     // pushes one update
Unit->SetNetDormancy(DORM_DormantAll);
```

`DORM_Initial` means the actor replicates its initial state then goes quiet without ever entering the active list. For actors that only change on discrete events (turn boundaries, interaction) this removes them from per-tick consideration entirely.

Gotcha: property changes on a dormant actor **do not replicate** until `FlushNetDormancy()`. Wrap it in the setter if you use dormancy widely.

## Validated server RPC

```cpp
UFUNCTION(Server, Reliable, WithValidation)
void Server_SubmitOrder(int32 TurnIndex, int32 UnitId, FIntPoint TargetTile);
```

```cpp
bool AMyPlayerController::Server_SubmitOrder_Validate(int32 TurnIndex, int32 UnitId, FIntPoint TargetTile)
{
    // cheap, side-effect-free sanity only. Returning false disconnects the client.
    return TargetTile.X >= 0 && TargetTile.Y >= 0 && UnitId >= 0;
}

void AMyPlayerController::Server_SubmitOrder_Implementation(int32 TurnIndex, int32 UnitId, FIntPoint TargetTile)
{
    AMyGameState* GS = GetWorld()->GetGameState<AMyGameState>();
    if (!GS || GS->GetTurnIndex() != TurnIndex) { return; }   // stale/replayed
    if (GS->GetActiveTurnPlayer() != PlayerState) { return; } // not your turn
    if (!GS->IsLegalMove(UnitId, TargetTile)) { return; }     // full rules check lives here
    GS->ApplyOrder(UnitId, TargetTile);
}
```

Rule: `_Validate` is for *impossible* input (out of range, malformed). Actual game-rule enforcement belongs in `_Implementation` and must **return quietly**, not disconnect — legitimate clients race the server all the time.

## Late-joiner-safe event delivery

Wrong:

```cpp
Multicast_PlayExplosion(Location);   // late joiners and out-of-relevancy clients never see it
```

Right:

```cpp
UPROPERTY(ReplicatedUsing = OnRep_LastResolvedTurn)
FTurnResult LastResolvedTurn;

void OnRep_LastResolvedTurn()
{
    PlayTurnCosmetics(LastResolvedTurn);   // deterministic from state
}
```

Multicast is acceptable only for cosmetics that are meaningless if missed (a hit spark), never for anything that changes what the player sees a second later.

## Component replication

```cpp
UMyComponent::UMyComponent()
{
    SetIsReplicatedByDefault(true);   // or SetIsReplicated(true) at runtime
}
```

Both the owning actor (`bReplicates = true`) and the component must opt in. Forgetting the component side is a top-5 bug.

## Testing matrix — run all four before "done"

| Config | Catches |
|---|---|
| Standalone | authority-gated cosmetics that never run |
| PIE, 2 clients, **Run Dedicated Server** on | ownership, `HasAuthority`, server-only assumptions |
| Dedicated server + `net.PktLag 120 net.PktLagVariance 40` | order-of-arrival, prediction, UI that assumes instant response |
| Client joining mid-match | multicast-as-state, `COND_InitialOnly` mistakes, null replicated pointers |

## Object pointer safety

```cpp
void AMyActor::OnRep_TargetUnit()
{
    if (!TargetUnit) { return; }   // reference may arrive before the object does
    // ...
}
```

A replicated `UObject*`/`AActor*` can legitimately arrive as `nullptr` and resolve on a later update. Every `OnRep_` on a pointer needs this guard, and any dependent logic must be re-runnable.
