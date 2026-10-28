#include "PatrolEquipmentComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"

UPatrolEquipmentComponent::UPatrolEquipmentComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UPatrolEquipmentComponent::BeginPlay()
{
    Super::BeginPlay();
    Character = Cast<ACharacter>(GetOwner());
    if (!Character) return;
    Camera = Character->FindComponentByClass<UCameraComponent>();
    TArray<USkeletalMeshComponent*> Meshes;
    Character->GetComponents(Meshes);
    for (USkeletalMeshComponent* Mesh : Meshes)
    {
        if (Mesh->GetName().StartsWith(TEXT("FirstPersonBody"))) Body = Mesh;
    }
    if (!Camera) return;
    ViewRoot = NewObject<USceneComponent>(Character, TEXT("PatrolViewRoot"));
    ViewRoot->SetupAttachment(Camera);
    ViewRoot->RegisterComponent();
    auto MakeView = [this](const FName Name, UStaticMesh* Mesh)
    {
        UStaticMeshComponent* View = NewObject<UStaticMeshComponent>(Character, Name);
        View->SetupAttachment(ViewRoot);
        View->SetStaticMesh(Mesh);
        View->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        View->SetOnlyOwnerSee(true);
        View->SetCastShadow(false);
        View->SetLightingChannels(true, true, false);
        View->RegisterComponent();
        for (int32 Index = 0; Index < View->GetNumMaterials(); ++Index) View->CreateDynamicMaterialInstance(Index);
        return View;
    };
    FlashlightView = MakeView(TEXT("HeldFlashlight"), FlashlightViewMesh);
    NotebookView = MakeView(TEXT("HeldNotebook"), NotebookViewMesh);
    HandFill = NewObject<UPointLightComponent>(Character, TEXT("PatrolHandFill"));
    HandFill->SetupAttachment(Camera);
    HandFill->SetIntensityUnits(ELightUnits::Candelas);
    HandFill->SetIntensity(18.f);
    HandFill->SetAttenuationRadius(100.f);
    HandFill->SetLightingChannels(false, true, false);
    HandFill->SetCastShadows(false);
    HandFill->RegisterComponent();
    FlashlightBeam = NewObject<USpotLightComponent>(Character, TEXT("PatrolFlashlightBeam"));
    FlashlightBeam->SetupAttachment(Camera);
    FlashlightBeam->SetIntensityUnits(ELightUnits::Candelas);
    FlashlightBeam->SetIntensity(3500.f);
    FlashlightBeam->SetAttenuationRadius(2200.f);
    FlashlightBeam->SetInnerConeAngle(16.f);
    FlashlightBeam->SetOuterConeAngle(28.f);
    FlashlightBeam->SetLightColor(FLinearColor(1.f, .94f, .80f));
    FlashlightBeam->SetCastShadows(true);
    FlashlightBeam->SetRelativeLocation(FVector(55.14f, 14.f, -12.48f));
    FlashlightBeam->SetRelativeRotation(FRotator(10.f, 0.f, 0.f));
    FlashlightBeam->RegisterComponent();
    RefreshEquipment();
}

void UPatrolEquipmentComponent::SelectHandSlot(int32 Slot)
{
    if (Slot < 1 || Slot > 3) return;
    HandSlot = Slot;
    RefreshEquipment();
}

void UPatrolEquipmentComponent::ToggleFlashlight()
{
    if (HandSlot != 1) return;
    bFlashlightOn = !bFlashlightOn;
    RefreshEquipment();
}

void UPatrolEquipmentComponent::RefreshEquipment()
{
    if (!FlashlightView || !NotebookView || !FlashlightBeam) return;
    FlashlightView->SetVisibility(HandSlot == 1);
    NotebookView->SetVisibility(HandSlot == 2);
    FlashlightBeam->SetVisibility(HandSlot == 1 && bFlashlightOn);
    FlashlightView->SetScalarParameterValueOnMaterials(TEXT("LampGlow"), HandSlot == 1 && bFlashlightOn ? 1.f : 0.f);
    if (Body)
    {
        if (HandSlot == 1 || HandSlot == 2) Body->HideBoneByName(TEXT("upperarm_r"), EPhysBodyOp::PBO_None);
        else Body->UnHideBoneByName(TEXT("upperarm_r"));
        if (HandSlot == 2) Body->HideBoneByName(TEXT("upperarm_l"), EPhysBodyOp::PBO_None);
        else Body->UnHideBoneByName(TEXT("upperarm_l"));
    }
}

void UPatrolEquipmentComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!Character || !Character->IsLocallyControlled() || !Camera || !ViewRoot) return;
    APlayerController* PC = Cast<APlayerController>(Character->GetController());
    if (!PC) return;
    if (PC->WasInputKeyJustPressed(EKeys::One)) SelectHandSlot(1);
    if (PC->WasInputKeyJustPressed(EKeys::Two)) SelectHandSlot(2);
    if (PC->WasInputKeyJustPressed(EKeys::Three)) SelectHandSlot(3);
    if (PC->WasInputKeyJustPressed(EKeys::LeftMouseButton)) ToggleFlashlight();
    bSprinting = PC->IsInputKeyDown(EKeys::LeftShift);
    Character->GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;

    const FTransform CameraTransform = Camera->GetComponentTransform();
    FRotator HeldRotation = CameraTransform.Rotator();
    // Keep the book in front of the chest while the camera can still look at the feet.
    if (HandSlot == 2) HeldRotation.Pitch = FMath::Max(FRotator::NormalizeAxis(HeldRotation.Pitch), -25.f);
    const float LookDown = HandSlot == 2 ? FMath::Clamp((-FRotator::NormalizeAxis(CameraTransform.Rotator().Pitch) - 25.f) / 60.f, 0.f, 1.f) : 0.f;
    const float NotebookBlend = LookDown * LookDown * (3.f - 2.f * LookDown);
    const FTransform HeldTransform(HeldRotation, CameraTransform.GetLocation());
    ViewRoot->SetWorldRotation(HeldRotation);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(PatrolEquipmentClearance), false, Character);
    FHitResult Hit;
    const FVector Start = CameraTransform.GetLocation();
    const FVector End = HeldTransform.TransformPosition(FVector(90.f, 0.f, -10.f));
    const bool bWall = GetWorld()->SweepSingleByChannel(Hit, Start, End, FQuat::Identity, ECC_Camera,
        FCollisionShape::MakeSphere(6.f), Query);
    const float TargetOffset = bWall ? FMath::Clamp(Hit.Distance - 90.f, -80.f, 0.f) : 0.f;
    WallOffset = FMath::FInterpTo(WallOffset, TargetOffset, DeltaTime, 18.f);
    NotebookView->SetVisibility(HandSlot == 2 && WallOffset > FMath::Lerp(-8.f, -1.f, NotebookBlend));
    const float Speed = Character->GetVelocity().Size2D();
    BobPhase += DeltaTime * (bSprinting ? 12.f : 8.f);
    const float Amount = FMath::Clamp(Speed / SprintSpeed, 0.f, 1.f);
    const FVector ViewOffset(WallOffset, FMath::Sin(BobPhase) * .45f * Amount,
        WallOffset * .35f + FMath::Cos(BobPhase * 2.f) * .5f * Amount);
    ViewRoot->SetWorldLocation(CameraTransform.TransformPosition(ViewOffset)
        + HeldRotation.RotateVector(FVector(-14.f, 0.f, -20.f) * NotebookBlend));
    const FVector IntendedLight = CameraTransform.TransformPosition(ViewRoot->GetRelativeLocation() + FVector(55.14f, 14.f, -12.48f));
    if (GetWorld()->SweepSingleByChannel(Hit, Start, IntendedLight, FQuat::Identity, ECC_Camera,
        FCollisionShape::MakeSphere(3.f), Query)) FlashlightBeam->SetWorldLocation(Hit.Location);
    else FlashlightBeam->SetWorldLocation(IntendedLight);
    FlashlightBeam->SetWorldRotation((CameraTransform.GetRotation() * FRotator(10.f, 0.f, 0.f).Quaternion()).Rotator());
}
