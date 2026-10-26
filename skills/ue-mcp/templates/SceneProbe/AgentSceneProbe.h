// UAgentSceneProbe - what is on the screen right now, as JSON an agent can read.
//
// Template from the ue-mcp skill (references/scene-probe.md). Drop both files into your game module
// (e.g. Source/<Game>/Agent/), add "Json" to the module's dependencies, do a FULL build (a new UCLASS is not
// something Live Coding can add), then in PIE or -game:
//
//     Agent.SceneState [filter] [file]
//
// filter: all | camera | characters | visible  (comma separated; default all)
// file:   writes <Project>/Saved/AgentRuns/<file>.json. Always pass it when driving the probe over MCP:
//         a console-running tool returns what the command printed to its output device, not UE_LOG lines.
//
// Only engine types are used. Project state (match, dialogue, quest...) is added through OnDescribe from your
// own code - see the example at the bottom of AgentSceneProbe.cpp.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AgentSceneProbe.generated.h"

class FJsonObject;

/**
 * The world being described, the filter, the root object to add fields to, warnings to append to. Called on the game
 * thread during DescribeJson. Static, so with several PIE worlds every binding sees every world: compare the world.
 */
DECLARE_MULTICAST_DELEGATE_FourParams(FAgentSceneProbeDescribe, UWorld* /*World*/, const FString& /*Filter*/, FJsonObject& /*Root*/, TArray<FString>& /*Warnings*/);

// No <MODULE>_API on purpose: add it if another module calls GetSubsystem<UAgentSceneProbe>().
UCLASS()
class UAgentSceneProbe : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	/**
	 * The scene now, as JSON: world (map, time, dilation), camera (view target, location, rotation, FOV, cuts and
	 * seconds since the last one), characters (what the mesh plays, rendered, head on screen, gap to the floor,
	 * speed) and warnings. Warnings are hints, not errors: an empty anim, a character in the air with no montage,
	 * a character tagged AgentProbe.Focus that is not rendered.
	 */
	FString DescribeJson(const FString& Filter) const;

	/** Project fields and warnings. Bind once at module startup; unbind on shutdown. */
	static FAgentSceneProbeDescribe OnDescribe;

	/** Actor tags the probe understands. */
	static const FName FocusTag;   // warn when this actor is not rendered (the speaker of a line, the boss in a reveal)
	static const FName FloatsTag;  // floats by design: no "in the air" warning
	static const FName IgnoreTag;  // leave out of the snapshot

	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	/** The view a frame ago; a jump between two frames is a cut. */
	FVector LastViewAt = FVector::ZeroVector;
	FRotator LastViewRot = FRotator::ZeroRotator;
	TWeakObjectPtr<AActor> LastViewTarget;
	bool bHaveView = false;
	/** World seconds of the most recent cuts (newest last) and the total count. */
	TArray<double> RecentCuts;
	int32 Cuts = 0;
};
