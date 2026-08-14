# Iris Replication — UE 5.8

Status in 5.8: **production-ready**, still **opt-in**. 5.8 added protocol-mismatch handling, serialization refinements, cull-distance management, Scene Graph integration, RemoteObjects RPC routing, and **parallel network handlers (on by default)**.

All identifiers below were read out of a UE **5.8.1** source tree. Re-grep against your own engine before quoting them — Epic moves these between releases.

## Enabling Iris — the actual mechanism

Widely-repeated advice says `bUseIris = true;` in `*.Target.cs`. **That flag does not exist in 5.8's UnrealBuildTool.** `grep -rn "bUseIris" Engine/Source/Programs/UnrealBuildTool/` returns nothing.

The real chain, from `UEngine::WillNetDriverUseIris` in `Runtime/Engine/Private/UnrealEngine.cpp`:

**1. Plugin enabled** — the `IrisCore` module must be loaded, or Iris hard-ensures:

```json
// YourProject.uproject
{ "Name": "Iris", "Enabled": true }
```

**2. Module support** — in the consuming module's `*.Build.cs`:

```csharp
SetupIrisSupport(Target);            // ModuleRules.cs
// optionally: SetupIrisSupport(Target, bAddAsPublicDependency: true);
```

Iris-specific code is guarded with `#if UE_WITH_IRIS`.

**3. Engine cvar** — declared in `Runtime/Net/Iris/Private/Iris/IrisConfig.cpp`:

```ini
[SystemSettings]
net.Iris.UseIrisReplication=1
net.IsPushModelEnabled=1
net.SubObjects.DefaultUseSubObjectReplicationList=1
```

**4. Per-net-driver config** — `FIrisNetDriverConfig` (`Runtime/Engine/Classes/Engine/Engine.h`), collected in `UEngine::IrisNetDriverConfigs`:

```ini
[/Script/Engine.Engine]
+IrisNetDriverConfigs=(NetDriverDefinition="GameNetDriver",bCanUseIris=true,PreferredReplicationSystem=Iris)
```

Fields: `NetDriverDefinition`, `NetDriverName`, `NetDriverWildcardName`, `bCanUseIris`, `PreferredReplicationSystem` (`Default` / `Generic` / `Iris`).

**Resolution order** (later wins):
1. `bCanUseIris && net.Iris.UseIrisReplication` → default preference
2. `PreferredReplicationSystem` on the matching config
3. `UGameInstance::GetDesiredReplicationSystem(NetDriverDefinition)` — override this to decide per-session in code
4. In PIE, clients follow the dedicated-server instance's choice
5. `-UseIrisReplication=0|1` on the command line — **overrides everything**

Note the asymmetry: the cmdline and GameInstance can only *force Iris on* when `bCanUseIris` is true, but can force it *off* unconditionally. The safest A/B test is therefore to ship with `bCanUseIris=true` and flip via cmdline.

## Verify it actually took

```
Log LogNet Log
```

Look for `is forcing NetDriver ... to use the Iris replication system` / `... Generic replication system`, and the ensure `%s is not using Iris because the IrisCore module isn't loaded`. If neither line appears, the net driver silently stayed on generic.

## Required code changes

### Subobjects (mandatory)

```cpp
AMyActor::AMyActor()
{
    bReplicateUsingRegisteredSubObjectList = true;
}
```

For subobjects that are **not** `AActor`/`UActorComponent`:

```cpp
#include "Iris/ReplicationSystem/ReplicationFragmentUtil.h"

#if UE_WITH_IRIS
void UMyObject::RegisterReplicationFragments(
    UE::Net::FFragmentRegistrationContext& Context,
    UE::Net::EFragmentRegistrationFlags RegistrationFlags)
{
    UE::Net::FReplicationFragmentUtil::CreateAndRegisterFragmentsForObject(this, Context, RegistrationFlags);
}
#endif
```

### Structs with custom `NetSerialize`

Iris needs to be told a struct's hand-rolled serializer is safe to use:

```ini
[/Script/IrisCore.ReplicationStateDescriptorConfig]
+SupportsStructNetSerializerList=(StructName=MyCustomStruct)
```

Without this you get a descriptor-build warning at startup and the struct falls back or errors. Prefer writing a real `FNetSerializer` for anything hot.

### Unchanged

Property replication syntax, RPC declaration and execution, dormancy, and fast-array replication all behave the same.

## What Iris does not have

- **Replication Graph** — mutually exclusive, cannot share a net driver. Replace graph nodes with:
  - **Filters** — decide *whether* an object replicates to a connection (spatial, group, owner-based). This is the Replication Graph node equivalent.
  - **Prioritizers** — decide *ordering* when bandwidth is scarce.
- Node-based custom routing. Express it as a filter class instead.

## Architecture map (for reading engine code)

| Concept | Meaning |
|---|---|
| `UReplicationSystem` | Top-level owner of state, filtering, prioritization, serialization |
| Replication Bridge | Gameplay ↔ replication translation layer (`EngineReplicationBridge`) |
| Net Object | Iris's internal handle for a replicated object |
| Replication State | The struct holding replicated data |
| Replication Protocol | Describes what/how an object replicates |
| Replication Fragment | Carries a state between gameplay object and replication system |
| Net Handle | Unique id for a replicated object |
| Net Token Data Stream | Synchronizes object paths / interned strings |
| Replication Data Stream | Schedules and serializes dirty state |

Source roots: `Engine/Source/Runtime/Net/Iris/`, and the engine-side bridge in `Runtime/Engine/Public/Net/Iris/`.

## Migration order that minimizes risk

1. Push Model everywhere first, on generic replication. Ship it. Verify no regressions.
2. Convert all subobject replication to the registered list. Ship it.
3. Register custom `NetSerialize` structs. Ship it.
4. Only then flip `net.Iris.UseIrisReplication=1` behind a cmdline switch and A/B on a real dedicated server with `net.PktLag`/`net.PktLoss` active.
5. Compare `stat net` and Insights `-NetTrace=1` captures before/after. If bytes/sec and server frame time did not improve materially, revert — the migration has ongoing maintenance cost.
