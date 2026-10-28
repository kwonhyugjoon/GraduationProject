#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PatrolEquipmentComponent.generated.h"

class ACharacter;
class UCameraComponent;
class USceneComponent;
class USkeletalMeshComponent;
class UStaticMesh;
class UStaticMeshComponent;
class USpotLightComponent;
class UPointLightComponent;

UCLASS(ClassGroup=(Patrol), meta=(BlueprintSpawnableComponent))
class MUSEUMSTAGE1DEMO_API UPatrolEquipmentComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPatrolEquipmentComponent();
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Patrol")
    TObjectPtr<UStaticMesh> FlashlightViewMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Patrol")
    TObjectPtr<UStaticMesh> NotebookViewMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Patrol", meta=(ClampMin="1"))
    float WalkSpeed = 300.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Patrol", meta=(ClampMin="1"))
    float SprintSpeed = 520.f;

    UPROPERTY(BlueprintReadOnly, Category="Patrol")
    int32 HandSlot = 1;

    UPROPERTY(BlueprintReadOnly, Category="Patrol")
    bool bFlashlightOn = true;

    UPROPERTY(BlueprintReadOnly, Category="Patrol")
    bool bSprinting = false;

    UFUNCTION(BlueprintCallable, Category="Patrol")
    void SelectHandSlot(int32 Slot);

    UFUNCTION(BlueprintCallable, Category="Patrol")
    void ToggleFlashlight();

private:
    void RefreshEquipment();
    UPROPERTY(Transient) TObjectPtr<ACharacter> Character;
    UPROPERTY(Transient) TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> Body;
    UPROPERTY(Transient) TObjectPtr<USceneComponent> ViewRoot;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> FlashlightView;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> NotebookView;
    UPROPERTY(Transient) TObjectPtr<USpotLightComponent> FlashlightBeam;
    UPROPERTY(Transient) TObjectPtr<UPointLightComponent> HandFill;
    float BobPhase = 0.f;
    float WallOffset = 0.f;
};
