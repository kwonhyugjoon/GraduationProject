#pragma once

#include "Subsystems/LocalPlayerSubsystem.h"
#include "PatrolEquipmentHUDSubsystem.generated.h"

class SWidget;
class UGameViewportClient;
class UTexture2D;

UCLASS()
class UPatrolEquipmentHUDSubsystem : public ULocalPlayerSubsystem
{
    GENERATED_BODY()

public:
    virtual void PlayerControllerChanged(APlayerController* NewPlayerController) override;
    virtual void Deinitialize() override;

private:
    void LoadHUDTextures();
    void RemoveHUD();

    UPROPERTY(Transient)
    TArray<TObjectPtr<UTexture2D>> HUDTextures;

    TSharedPtr<SWidget> HUD;
    TWeakObjectPtr<UGameViewportClient> HUDViewport;
};
