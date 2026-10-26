// UAgentSceneProbe - see AgentSceneProbe.h and the ue-mcp skill's references/scene-probe.md.

#include "AgentSceneProbe.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Policies/CondensedJsonPrintPolicy.h"

DEFINE_LOG_CATEGORY_STATIC(LogAgentSceneProbe, Log, All);

FAgentSceneProbeDescribe UAgentSceneProbe::OnDescribe;
const FName UAgentSceneProbe::FocusTag(TEXT("AgentProbe.Focus"));
const FName UAgentSceneProbe::FloatsTag(TEXT("AgentProbe.Floats"));
const FName UAgentSceneProbe::IgnoreTag(TEXT("AgentProbe.Ignore"));

namespace AgentSceneProbe
{
	/** A camera move bigger than this between two frames is a cut, not a dolly. Tune to your fastest camera move. */
	constexpr float CutJumpCm = 150.f;
	constexpr float CutTurnDeg = 20.f;
	/** Capsule bottom further than this above the floor with no montage playing: hanging in the air. */
	constexpr float AirGapCm = 5.f;
	/** Characters listed, nearest to the camera first; keeps the JSON small enough to read in one go. */
	constexpr int32 MaxCharacters = 48;
	constexpr int32 KeepCuts = 8;

	double Round2(double V) { return FMath::RoundToDouble(V * 100.0) / 100.0; }

	TArray<TSharedPtr<FJsonValue>> Vec(const FVector& V)
	{
		return { MakeShared<FJsonValueNumber>(FMath::RoundToInt(V.X)), MakeShared<FJsonValueNumber>(FMath::RoundToInt(V.Y)),
			MakeShared<FJsonValueNumber>(FMath::RoundToInt(V.Z)) };
	}

	TArray<TSharedPtr<FJsonValue>> Rot(const FRotator& R)
	{
		return { MakeShared<FJsonValueNumber>(FMath::RoundToInt(R.Pitch)), MakeShared<FJsonValueNumber>(FMath::RoundToInt(R.Yaw)),
			MakeShared<FJsonValueNumber>(FMath::RoundToInt(R.Roll)) };
	}

	/** Where the head is on screen, 0..1 each way (may be outside 0..1 when off-screen); false behind the camera. */
	bool HeadOnScreen(const APlayerController* PC, const USkeletalMeshComponent* Mesh, FVector2D& OutPos)
	{
		if (!PC || !Mesh) return false;
		static const FName HeadNames[] = { TEXT("head"), TEXT("Head"), TEXT("head_01") };
		FVector At = Mesh->Bounds.Origin + FVector(0, 0, Mesh->Bounds.BoxExtent.Z * 0.8f);
		for (const FName& Name : HeadNames)
		{
			if (Mesh->DoesSocketExist(Name)) { At = Mesh->GetSocketLocation(Name); break; }
		}
		int32 W = 0, H = 0;
		PC->GetViewportSize(W, H);
		FVector2D Px;
		if (W <= 0 || H <= 0 || !PC->ProjectWorldLocationToScreen(At, Px)) return false;
		OutPos = FVector2D(Px.X / W, Px.Y / H);
		return true;
	}

	/** Gap under the capsule down to whatever it would stand on (0 when nothing is within 3 m). */
	float GapToFloor(const ACharacter* C)
	{
		const UCapsuleComponent* Capsule = C->GetCapsuleComponent();
		UWorld* World = C->GetWorld();
		if (!Capsule || !World) return 0.f;
		const FVector Bottom = C->GetActorLocation() - FVector(0, 0, Capsule->GetScaledCapsuleHalfHeight());
		FHitResult Hit;
		FCollisionQueryParams Params(TEXT("AgentSceneProbeFloor"), false, C);
		if (!World->LineTraceSingleByChannel(Hit, Bottom + FVector(0, 0, 2), Bottom - FVector(0, 0, 300), ECC_Visibility, Params)) return 0.f;
		return FMath::Max(0.f, static_cast<float>(Bottom.Z - Hit.ImpactPoint.Z));
	}

	/** What the mesh plays: a montage with its position, a single clip with its time, or the anim graph's class. */
	FString PlayingOf(const USkeletalMeshComponent* Mesh, bool& bOutMontage, bool& bOutNothing)
	{
		bOutMontage = false;
		bOutNothing = false;
		const UAnimInstance* Anim = Mesh ? Mesh->GetAnimInstance() : nullptr;
		if (!Anim)
		{
			bOutNothing = true;
			return TEXT("-");
		}
		if (const UAnimMontage* Montage = Anim->GetCurrentActiveMontage())
		{
			bOutMontage = true;
			return FString::Printf(TEXT("montage %s %.2fs"), *Montage->GetName(), Anim->Montage_GetPosition(Montage));
		}
		if (const UAnimSingleNodeInstance* Single = Cast<UAnimSingleNodeInstance>(Anim))
		{
			const UAnimationAsset* Asset = Single->GetAnimationAsset();
			bOutNothing = !Asset;
			return Asset ? FString::Printf(TEXT("clip %s %.2fs"), *Asset->GetName(), Single->GetCurrentTime()) : TEXT("-");
		}
		return FString::Printf(TEXT("graph %s"), *Anim->GetClass()->GetName());
	}
}

FString UAgentSceneProbe::DescribeJson(const FString& Filter) const
{
	using namespace AgentSceneProbe;

	UWorld* World = GetWorld();
	TArray<FString> Parts;
	(Filter.IsEmpty() ? FString(TEXT("all")) : Filter).ParseIntoArray(Parts, TEXT(","));
	const auto Want = [&Parts](const TCHAR* Part) { return Parts.Contains(TEXT("all")) || Parts.Contains(Part); };

	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	TArray<FString> Warnings;
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
	const APlayerCameraManager* Cam = PC ? PC->PlayerCameraManager.Get() : nullptr;

	Root->SetStringField(TEXT("map"), World ? World->GetMapName() : TEXT("-"));
	Root->SetNumberField(TEXT("time"), World ? Round2(World->GetTimeSeconds()) : 0.0);
	if (World && World->GetWorldSettings()) Root->SetNumberField(TEXT("dilation"), Round2(World->GetWorldSettings()->GetEffectiveTimeDilation()));
	if (World && World->IsPaused()) Root->SetBoolField(TEXT("paused"), true);

	if (Want(TEXT("camera")) && Cam)
	{
		const TSharedRef<FJsonObject> C = MakeShared<FJsonObject>();
		C->SetStringField(TEXT("target"), GetNameSafe(Cam->GetViewTarget()));
		C->SetArrayField(TEXT("at"), Vec(Cam->GetCameraLocation()));
		C->SetArrayField(TEXT("rot"), Rot(Cam->GetCameraRotation()));
		C->SetNumberField(TEXT("fov"), Round2(Cam->GetFOVAngle()));
		C->SetNumberField(TEXT("cuts"), Cuts);
		C->SetNumberField(TEXT("sinceCut"), RecentCuts.Num() == 0 || !World ? -1.0 : Round2(World->GetTimeSeconds() - RecentCuts.Last()));
		TArray<TSharedPtr<FJsonValue>> CutTimes;
		for (const double T : RecentCuts) CutTimes.Add(MakeShared<FJsonValueNumber>(Round2(T)));
		C->SetArrayField(TEXT("cutTimes"), CutTimes);
		Root->SetObjectField(TEXT("camera"), C);
	}

	const bool bVisibleOnly = Parts.Contains(TEXT("visible"));
	if ((Want(TEXT("characters")) || bVisibleOnly) && World)
	{
		const FVector Eye = Cam ? Cam->GetCameraLocation() : FVector::ZeroVector;
		TArray<ACharacter*> All;
		for (TActorIterator<ACharacter> It(World); It; ++It)
		{
			if (!It->ActorHasTag(IgnoreTag)) All.Add(*It);
		}
		All.Sort([&Eye](const ACharacter& A, const ACharacter& B)
		{
			return FVector::DistSquared(A.GetActorLocation(), Eye) < FVector::DistSquared(B.GetActorLocation(), Eye);
		});

		TArray<TSharedPtr<FJsonValue>> List;
		int32 Skipped = 0;
		for (ACharacter* C : All)
		{
			USkeletalMeshComponent* Mesh = C->GetMesh();
			const bool bRendered = Mesh && Mesh->WasRecentlyRendered(0.5f);
			const bool bHidden = C->IsHidden();
			bool bMontage = false, bNothing = false;
			const FString Playing = PlayingOf(Mesh, bMontage, bNothing);
			const float Gap = GapToFloor(C);
			const UCharacterMovementComponent* Move = C->GetCharacterMovement();
			const bool bAirborneByDesign = Move && (Move->IsFalling() || Move->IsFlying());

			// Warnings are computed for everyone, listed or not.
			if (!bHidden)
			{
				if (bNothing) Warnings.Add(FString::Printf(TEXT("%s: no animation playing (T-pose?)"), *C->GetName()));
				if (Gap > AirGapCm && !bMontage && !C->ActorHasTag(FloatsTag) && !bAirborneByDesign)
				{
					Warnings.Add(FString::Printf(TEXT("%s: %d cm above the floor, no montage, not falling"), *C->GetName(), FMath::RoundToInt(Gap)));
				}
				if (C->ActorHasTag(FocusTag) && !bRendered) Warnings.Add(FString::Printf(TEXT("%s: focus actor not rendered"), *C->GetName()));
			}

			if ((bVisibleOnly && !bRendered) || List.Num() >= MaxCharacters)
			{
				++Skipped;
				continue;
			}
			const TSharedRef<FJsonObject> O = MakeShared<FJsonObject>();
			O->SetStringField(TEXT("name"), C->GetName());
			O->SetStringField(TEXT("class"), C->GetClass()->GetName());
			O->SetArrayField(TEXT("at"), Vec(C->GetActorLocation()));
			O->SetNumberField(TEXT("yaw"), FMath::RoundToInt(C->GetActorRotation().Yaw));
			O->SetNumberField(TEXT("dist"), FMath::RoundToInt(FVector::Dist(C->GetActorLocation(), Eye)));
			O->SetStringField(TEXT("playing"), Playing);
			O->SetBoolField(TEXT("rendered"), bRendered);
			FVector2D Head;
			if (bRendered && HeadOnScreen(PC, Mesh, Head))
			{
				O->SetArrayField(TEXT("head"), { MakeShared<FJsonValueNumber>(Round2(Head.X)), MakeShared<FJsonValueNumber>(Round2(Head.Y)) });
			}
			if (Gap > 0.5f) O->SetNumberField(TEXT("gap"), FMath::RoundToInt(Gap));
			const float Speed = static_cast<float>(C->GetVelocity().Size());
			if (Speed > 1.f) O->SetNumberField(TEXT("speed"), FMath::RoundToInt(Speed));
			if (bHidden) O->SetBoolField(TEXT("hidden"), true);
			if (C->ActorHasTag(FocusTag)) O->SetBoolField(TEXT("focus"), true);
			if (C->IsPlayerControlled()) O->SetBoolField(TEXT("player"), true);
			List.Add(MakeShared<FJsonValueObject>(O));
		}
		Root->SetArrayField(TEXT("characters"), List);
		if (Skipped > 0) Root->SetNumberField(TEXT("charactersNotListed"), Skipped);
	}

	// Project fields: match state, dialogue line and speaker, quest step...
	OnDescribe.Broadcast(World, Filter, Root.Get(), Warnings);

	TArray<TSharedPtr<FJsonValue>> WarningValues;
	for (const FString& W : Warnings) WarningValues.Add(MakeShared<FJsonValueString>(W));
	Root->SetArrayField(TEXT("warnings"), WarningValues);

	FString Out;
	const TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer = TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Out);
	FJsonSerializer::Serialize(Root, Writer);
	return Out;
}

void UAgentSceneProbe::Tick(float DeltaTime)
{
	// A cut: another view target, or the camera moved further in one frame than any camera move goes.
	UWorld* World = GetWorld();
	const APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
	const APlayerCameraManager* Cam = PC ? PC->PlayerCameraManager.Get() : nullptr;
	if (!Cam) return;
	const FVector At = Cam->GetCameraLocation();
	const FRotator Rot = Cam->GetCameraRotation();
	AActor* Target = Cam->GetViewTarget();
	if (bHaveView && (Target != LastViewTarget.Get() || FVector::Dist(At, LastViewAt) > AgentSceneProbe::CutJumpCm
		|| FMath::Abs(FRotator::NormalizeAxis(Rot.Yaw - LastViewRot.Yaw)) > AgentSceneProbe::CutTurnDeg
		|| FMath::Abs(FRotator::NormalizeAxis(Rot.Pitch - LastViewRot.Pitch)) > AgentSceneProbe::CutTurnDeg))
	{
		++Cuts;
		RecentCuts.Add(World->GetTimeSeconds());
		if (RecentCuts.Num() > AgentSceneProbe::KeepCuts) RecentCuts.RemoveAt(0);
	}
	LastViewAt = At;
	LastViewRot = Rot;
	LastViewTarget = Target;
	bHaveView = true;
}

TStatId UAgentSceneProbe::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UAgentSceneProbe, STATGROUP_Tickables);
}

bool UAgentSceneProbe::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

namespace AgentSceneProbe
{
	static FAutoConsoleCommandWithWorldAndArgs GStateCmd(
		TEXT("Agent.SceneState"),
		TEXT("The scene as JSON for an agent. Agent.SceneState [filter] [file]: filter all|camera|characters|visible, ")
		TEXT("comma separated; with a file name the JSON goes to Saved/AgentRuns/<file>.json (use this over MCP)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			const UAgentSceneProbe* Probe = World ? World->GetSubsystem<UAgentSceneProbe>() : nullptr;
			if (!Probe)
			{
				UE_LOG(LogAgentSceneProbe, Warning, TEXT("Agent.SceneState: no game or PIE world here"));
				return;
			}
			const FString Json = Probe->DescribeJson(Args.Num() > 0 ? Args[0] : FString());
			if (Args.Num() > 1)
			{
				const FString Path = FPaths::ProjectSavedDir() / TEXT("AgentRuns") / (FPaths::MakeValidFileName(Args[1]) + TEXT(".json"));
				const bool bSaved = FFileHelper::SaveStringToFile(Json, *Path, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
				UE_LOG(LogAgentSceneProbe, Display, TEXT("Agent.SceneState -> %s%s"), *FPaths::ConvertRelativePathToFull(Path), bSaved ? TEXT("") : TEXT(" (FAILED)"));
				return;
			}
			UE_LOG(LogAgentSceneProbe, Display, TEXT("Agent.SceneState %s"), *Json);
		}));
}

/*
 * Adding project state - in your own code, not in this file:
 *
 *     #include "AgentSceneProbe.h"
 *     #include "Dom/JsonObject.h"
 *
 *     void UMyMatchSubsystem::Initialize(FSubsystemCollectionBase& Collection)
 *     {
 *         Super::Initialize(Collection);
 *         ProbeHandle = UAgentSceneProbe::OnDescribe.AddWeakLambda(this,
 *             [this](UWorld* World, const FString& Filter, FJsonObject& Root, TArray<FString>& Warnings)
 *             {
 *                 if (World != GetWorld()) return;   // several PIE worlds share the static delegate
 *                 const TSharedRef<FJsonObject> M = MakeShared<FJsonObject>();
 *                 M->SetNumberField(TEXT("round"), Round);
 *                 M->SetStringField(TEXT("turn"), CurrentSideName());
 *                 Root.SetObjectField(TEXT("match"), M);
 *                 if (bWaitingForInput && TimeWaiting > 30.f) Warnings.Add(TEXT("match: waiting for input for 30 s"));
 *             });
 *     }
 *     void UMyMatchSubsystem::Deinitialize() { UAgentSceneProbe::OnDescribe.Remove(ProbeHandle); Super::Deinitialize(); }
 *
 * Good project fields: the phase of the scene (menu / gameplay / dialogue / cutscene), the dialogue line and WHO
 * says it (tag that actor AgentProbe.Focus while it speaks, and the probe warns when the speaker is off-screen),
 * game-rule state the human would otherwise read off the HUD. Warnings should carry the phase: a reaction shot
 * keeps the speaker off-screen on purpose, so it is a hint, not an error.
 */
