// UAgentConsoleToolset - an MCP tool that runs a console command in the PIE world (or the editor world when no
// PIE is up). UE 5.8's shipped toolsets have no console tool; this is how an agent reaches cvars, stat commands
// and the project's own commands such as Agent.SceneState.
//
// Template from the ue-mcp skill (references/scene-probe.md). It must live in an EDITOR module: UToolsetDefinition
// comes from the ToolsetRegistry plugin, which a game target does not see. Editor module Build.cs:
//     PrivateDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "UnrealEd", "ToolsetRegistry" });
// After a full build: ModelContextProtocol.RefreshTools, then call it through call_tool.

#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetDefinition.h"
#include "AgentConsoleToolset.generated.h"

UCLASS(BlueprintType, Hidden)
class UAgentConsoleToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/**
	 * Runs a console command in the play world when a PIE session is running, in the editor world otherwise, and
	 * returns what the command wrote to its output device. UE_LOG lines are NOT returned: commands that log (most
	 * project commands) must write a file instead - e.g. "Agent.SceneState all shot1" writes
	 * Saved/AgentRuns/shot1.json, which the agent then reads from disk.
	 * @param Command  The console command, e.g. "Agent.SceneState all intro_line3" or "stat unit".
	 */
	UFUNCTION(meta = (AICallable), Category = "Agent")
	static FString RunConsole(const FString& Command);
};
