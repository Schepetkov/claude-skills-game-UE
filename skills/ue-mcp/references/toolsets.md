# Unreal MCP toolsets — UE 5.8

The 27 toolset plugins that ship in `Engine/Plugins/Experimental/Toolsets/`. `AllToolsets` enables all of them; enabling individual ones keeps the surface smaller.

Re-derive the list for your engine:

```bash
ls Engine/Plugins/Experimental/Toolsets/
```

Then inspect what a specific toolset actually exposes:

```bash
grep -rn "AICallable" Engine/Plugins/Experimental/Toolsets/<Name>/Source/
```

`meta = (AICallable)` on a `UFUNCTION` is what makes a function a tool — grepping for it gives the real, current tool list for any toolset, which no doc page will.

## The list

### Core editor
| Toolset | What it's for |
|---|---|
| `AllToolsets` | umbrella plugin that enables everything below. Start here, narrow later |
| `EditorToolset` | actors, levels, assets, selection, transforms — the workhorse |
| `ConfigSettingsToolset` | read/write project and editor settings, including the cvars the other skills discuss |
| `PluginToolset` | plugin enumeration and state |
| `SemanticSearchToolset` | find assets by meaning rather than exact name |
| `LiveCodingToolset` | trigger Live Coding — C++ iteration without an editor restart |

### UI
| Toolset | What it's for |
|---|---|
| `SlateInspectorToolset` | inspect the **live** Slate widget tree. The single most useful tool for UI debugging — see `ue-ui` |
| `UMGToolSet` | UMG widget assets |
| `MVVMToolset` | ViewModel bindings |

### Gameplay & AI
| Toolset | What it's for |
|---|---|
| `AIModuleToolset` | AI controllers, perception, navigation |
| `StateTreeToolset` | StateTree assets and evaluation |
| `WorldConditionsToolset` | world condition assets |
| `GASToolsets` | Gameplay Ability System — abilities, effects, attributes |
| `GameplayTagsToolset` | tag hierarchy read/write |
| `GameFeaturesToolset` | Game Features plugins and actions |
| `ConversationToolset` | conversation/dialogue assets |
| `DataRegistryToolset` | Data Registry lookups |

### Content & simulation
| Toolset | What it's for |
|---|---|
| `NiagaraToolsets` | Niagara systems and emitters |
| `PCGToolset` | Procedural Content Generation graphs |
| `PhysicsToolsets` | physics assets, constraints, simulation |
| `ChaosClothAssetToolset` | Chaos cloth |
| `DataflowAgent` | Dataflow graphs |
| `AnimationAssistantToolset` | animation assets and blueprints |
| `SequencerAnimMixerToolset` | Sequencer anim mixing |
| `MetaHumanGenerator` | MetaHuman generation |

### Testing & meta
| Toolset | What it's for |
|---|---|
| `AutomationTestToolset` | run automation tests and read results. The way an agent verifies its own change |
| `MCPClientToolset` | lets the editor act as an MCP *client* toward other servers |

## Choosing a set

`AllToolsets` is the right default for exploratory work. Narrow when:

- **The tool list is noisy** — though with `bEnableToolSearch=True` (the default) only `list_toolsets` / `describe_toolset` / `call_tool` are registered natively, so this matters much less than it would otherwise.
- **You want a safety boundary.** Not enabling `PhysicsToolsets` or `MetaHumanGenerator` means an agent cannot touch them at all. Plugin enablement is a blunter and more reliable guardrail than instructions in a prompt.
- **Editor startup time matters** on a large project.

A reasonable minimal set for gameplay-focused C++ work:

```
EditorToolset, ConfigSettingsToolset, AutomationTestToolset,
SlateInspectorToolset, UMGToolSet, StateTreeToolset, AIModuleToolset
```

## Verifying what a toolset can actually do

Do not trust a summary — including this file. Ask the running editor:

```
ModelContextProtocol.RefreshTools
```

then, from the agent side, `list_toolsets` followed by `describe_toolset <name>`. That returns the live schema for the engine version and plugin set you actually have.

From the console, `ModelContextProtocol.ToolCall` invokes a tool directly — the fastest way to check a tool's behaviour without an agent in the loop.
