// Editor-only input injection for end-to-end PIE checks; absent from packaged games.
#if WITH_EDITOR
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "InputKeyEventArgs.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"

static FAutoConsoleCommandWithWorldAndArgs PatrolValidationKey(
    TEXT("Patrol.TestKey"), TEXT("Inject a key press/release into the PIE player's normal input pipeline."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
    {
        if (!World || Args.Num() != 2 || !World->IsGameWorld()) return;
        if (APlayerController* PC = World->GetFirstPlayerController())
        {
            const bool bPressed = Args[1] == TEXT("down");
            PC->InputKey(FInputKeyEventArgs::CreateSimulated(FKey(*Args[0]), bPressed ? IE_Pressed : IE_Released, bPressed ? 1.f : 0.f, -1,
                IPlatformInputDeviceMapper::Get().GetPrimaryInputDeviceForUser(PC->GetPlatformUserId())));
        }
    }));
#endif
