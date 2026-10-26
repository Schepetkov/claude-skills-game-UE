// UAgentConsoleToolset - see AgentConsoleToolset.h.

#include "AgentConsoleToolset.h"
#include "Editor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Misc/StringOutputDevice.h"

FString UAgentConsoleToolset::RunConsole(const FString& Command)
{
	if (Command.IsEmpty()) return TEXT("no command");
	UWorld* World = GEditor ? GEditor->PlayWorld.Get() : nullptr;
	const TCHAR* Where = TEXT("play world");
	if (!World)
	{
		World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		Where = TEXT("editor world");
	}
	if (!World || !GEngine) return TEXT("no world");

	FStringOutputDevice Output;
	Output.SetAutoEmitLineTerminator(true);
	const bool bHandled = GEngine->Exec(World, *Command, Output);
	return FString::Printf(TEXT("%s (%s): %s"), bHandled ? TEXT("ran") : TEXT("unknown command"), Where,
		Output.IsEmpty() ? TEXT("no output (UE_LOG text is not captured - write a file)") : *Output);
}
