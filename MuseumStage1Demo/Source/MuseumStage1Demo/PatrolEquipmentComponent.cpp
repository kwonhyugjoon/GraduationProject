#include "PatrolEquipmentComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"

namespace
{
constexpr float UnequipDuration = .15f;
constexpr float EquipDuration = .20f;
const FVector LoweredViewOffset(-16.f, 0.f, -35.f);
constexpr float LoweredPitch = -15.f;
constexpr double MaxWallRetraction = 36.0;
constexpr double MinHeldItemDepth = 14.0;
constexpr double WallInterpSpeed = 18.0;
constexpr double BookChestClearance = 35.0;
const FVector BookCenter(46.2, 0.0, -13.0);
const FVector BookExtent(1.8, 11.4, 12.0);

struct FEquipmentClearance
{
    FVector TowardCamera = FVector::ZeroVector;
    double Budget = 0.0;
    double Required = 0.0;
    bool bHasRoom = false;
};
}

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
        View->SetVisibility(false);
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
    FlashlightBeam->SetVisibility(false);
    FlashlightBeam->RegisterComponent();
    DisplayedHandSlot = HandSlot;
    RefreshEquipment();
}

void UPatrolEquipmentComponent::SelectHandSlot(int32 Slot)
{
    if (Slot < 1 || Slot > 3 || Slot == HandSlot) return;
    HandSlot = Slot;
    RefreshFlashlight();
}

void UPatrolEquipmentComponent::ToggleFlashlight()
{
    if (HandSlot != 1) return;
    bFlashlightOn = !bFlashlightOn;
    RefreshFlashlight();
}

void UPatrolEquipmentComponent::UpdateEquipmentTransition(float DeltaTime)
{
    if (DisplayedHandSlot != HandSlot)
    {
        if (DisplayedHandSlot == 3) SwitchDisplayedEquipment();
        else TransitionState = EEquipmentTransition::Unequipping;
    }
    else if (TransitionState == EEquipmentTransition::Unequipping)
    {
        // Reselecting the outgoing item reverses from its current pose.
        TransitionState = EEquipmentTransition::Equipping;
    }

    if (TransitionState == EEquipmentTransition::Unequipping)
    {
        const float TimeToLower = (1.f - LowerProgress) * UnequipDuration;
        if (DeltaTime < TimeToLower)
        {
            LowerProgress += DeltaTime / UnequipDuration;
            return;
        }

        DeltaTime -= TimeToLower;
        SwitchDisplayedEquipment();
    }

    if (TransitionState == EEquipmentTransition::Equipping)
    {
        LowerProgress = FMath::Max(0.f, LowerProgress - DeltaTime / EquipDuration);
        if (LowerProgress == 0.f) TransitionState = EEquipmentTransition::Idle;
    }
}

void UPatrolEquipmentComponent::SwitchDisplayedEquipment()
{
    DisplayedHandSlot = HandSlot;
    const bool bHasHeldItem = DisplayedHandSlot != 3;
    LowerProgress = bHasHeldItem ? 1.f : 0.f;
    TransitionState = bHasHeldItem ? EEquipmentTransition::Equipping : EEquipmentTransition::Idle;
    RefreshEquipment();
}

void UPatrolEquipmentComponent::RefreshEquipment()
{
    if (!FlashlightView || !NotebookView) return;
    // The active mesh is shown after its new pose has passed clearance.
    FlashlightView->SetVisibility(false);
    NotebookView->SetVisibility(false);
    RefreshFlashlight();
    if (Body)
    {
        if (DisplayedHandSlot == 1 || DisplayedHandSlot == 2) Body->HideBoneByName(TEXT("upperarm_r"), EPhysBodyOp::PBO_None);
        else Body->UnHideBoneByName(TEXT("upperarm_r"));
        if (DisplayedHandSlot == 2) Body->HideBoneByName(TEXT("upperarm_l"), EPhysBodyOp::PBO_None);
        else Body->UnHideBoneByName(TEXT("upperarm_l"));
    }
}

void UPatrolEquipmentComponent::RefreshFlashlight()
{
    if (!FlashlightView || !FlashlightBeam) return;
    const bool bWantsLight = WantsFlashlightBeam();
    // Only the view update enables the beam, after setting its swept origin.
    if (!bWantsLight) FlashlightBeam->SetVisibility(false);
    FlashlightView->SetScalarParameterValueOnMaterials(TEXT("LampGlow"), bWantsLight ? 1.f : 0.f);
}

bool UPatrolEquipmentComponent::WantsFlashlightBeam() const
{
    return HandSlot == 1 && DisplayedHandSlot == 1 && bFlashlightOn;
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
    UpdateEquipmentTransition(DeltaTime);
    UpdateEquipmentView(DeltaTime);
}

void UPatrolEquipmentComponent::UpdateEquipmentView(float DeltaTime)
{
    BobPhase += DeltaTime * (bSprinting ? 12.f : 8.f);
    if (DisplayedHandSlot == 3 && TransitionState == EEquipmentTransition::Idle)
    {
        WallRetraction = 0.0;
        WallProximity = 0.0;
        return;
    }

    const bool bShowingNotebook = DisplayedHandSlot == 2;
    UStaticMeshComponent* HeldView = bShowingNotebook ? NotebookView.Get() : FlashlightView.Get();
    UStaticMesh* HeldMesh = HeldView->GetStaticMesh();
    if (!HeldMesh)
    {
        HeldView->SetVisibility(false);
        FlashlightBeam->SetVisibility(false);
        return;
    }

    UWorld* World = GetWorld();
    const FTransform CameraTransform = Camera->GetComponentTransform();
    const FVector CameraLocation = CameraTransform.GetLocation();
    const FVector CameraForward = CameraTransform.GetUnitAxis(EAxis::X);
    const FRotator CameraRotation = CameraTransform.Rotator();
    FRotator HeldRotation = CameraRotation;
    // Keep the book in front of the chest while the camera can still look at the feet.
    if (bShowingNotebook) HeldRotation.Pitch = FMath::Max(FRotator::NormalizeAxis(HeldRotation.Pitch), -25.f);
    const double LookDown = bShowingNotebook ? FMath::Clamp((-FRotator::NormalizeAxis(CameraRotation.Pitch) - 25.0) / 60.0, 0.0, 1.0) : 0.0;
    const double NotebookBlend = FMath::SmoothStep(0.0, 1.0, LookDown);
    const double Amount = FMath::Clamp(Character->GetVelocity().Size2D() / SprintSpeed, 0.0, 1.0);
    const FVector BobOffset(0.0, FMath::Sin(BobPhase) * .45 * Amount, FMath::Cos(BobPhase * 2.f) * .5 * Amount);
    const FVector HeldLocation = CameraTransform.TransformPosition(BobOffset)
        + HeldRotation.RotateVector(FVector(-14.0, 0.0, -20.0) * NotebookBlend);
    FTransform HeldPose(HeldRotation, HeldLocation);

    const FBoxSphereBounds Bounds = HeldMesh->GetBounds();
    const FCollisionShape Shape = FCollisionShape::MakeBox(Bounds.BoxExtent + FVector(.5));
    const FVector ItemAnchor = bShowingNotebook ? BookCenter : FVector(42.0, 14.0, -14.0);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(PatrolEquipmentClearance), false, Character);
    Query.bFindInitialOverlaps = true;

    auto SweepPose = [&](const FTransform& Pose)
    {
        FEquipmentClearance Clearance;
        const FVector Anchor = Pose.TransformPosition(ItemAnchor);
        const FVector EyeToItem = Anchor - CameraLocation;
        // Retract along the viewing ray to keep the item in roughly the same screen position.
        Clearance.TowardCamera = -EyeToItem.GetSafeNormal();
        const double Depth = FVector::DotProduct(EyeToItem, CameraForward);
        const double DepthPerCm = FVector::DotProduct(-Clearance.TowardCamera, CameraForward);
        if (DepthPerCm > UE_SMALL_NUMBER)
        {
            Clearance.Budget = FMath::Clamp((Depth - MinHeldItemDepth) / DepthPerCm, 0.0, MaxWallRetraction);
        }

        const FQuat Rotation = Pose.GetRotation();
        if (bShowingNotebook)
        {
            const FVector BodyForward = Character->GetActorForwardVector();
            const double BookDepth = FVector::DotProduct(Anchor - Character->GetActorLocation(), BodyForward)
                - FMath::Abs(FVector::DotProduct(Rotation.GetAxisX(), BodyForward)) * BookExtent.X
                - FMath::Abs(FVector::DotProduct(Rotation.GetAxisY(), BodyForward)) * BookExtent.Y
                - FMath::Abs(FVector::DotProduct(Rotation.GetAxisZ(), BodyForward)) * BookExtent.Z;
            // At steep camera pitch even the lowering motion can take the book through the chest.
            if (BookDepth < BookChestClearance) return FEquipmentClearance{};

            const double TowardChest = -FVector::DotProduct(Clearance.TowardCamera, BodyForward);
            if (TowardChest > UE_SMALL_NUMBER)
            {
                Clearance.Budget = FMath::Min(Clearance.Budget, (BookDepth - BookChestClearance) / TowardChest);
            }
        }

        const FVector DesiredCenter = Pose.TransformPosition(Bounds.Origin);
        if (Clearance.Budget <= UE_KINDA_SMALL_NUMBER)
        {
            Clearance.bHasRoom = !World->OverlapBlockingTestByChannel(DesiredCenter, Rotation, ECC_Camera, Shape, Query);
            return Clearance;
        }

        const FVector TuckedCenter = DesiredCenter + Clearance.TowardCamera * Clearance.Budget;
        FHitResult Hit;
        const bool bBlocked = World->SweepSingleByChannel(Hit, TuckedCenter, DesiredCenter, Rotation, ECC_Camera, Shape, Query);
        Clearance.bHasRoom = !bBlocked || !Hit.bStartPenetrating;
        Clearance.Required = bBlocked ? Clearance.Budget * (1.0 - Hit.Time) : 0.0;
        return Clearance;
    };

    FEquipmentClearance Clearance = SweepPose(HeldPose);
    const double ProximityTarget = !Clearance.bHasRoom ? 1.0
        : Clearance.Budget > UE_KINDA_SMALL_NUMBER ? Clearance.Required / Clearance.Budget : 0.0;
    WallProximity = FMath::FInterpTo(WallProximity, ProximityTarget, DeltaTime, WallInterpSpeed);

    const float LowerAmount = FMath::Square(LowerProgress);
    if (LowerAmount > 0.f)
    {
        FVector TransitionOffset = LoweredViewOffset * LowerAmount;
        TransitionOffset.X *= 1.0 - FMath::SmoothStep(0.0, 1.0, WallProximity);
        HeldPose.AddToTranslation(CameraTransform.TransformVectorNoScale(TransitionOffset));
        HeldPose.ConcatenateRotation(FRotator(LoweredPitch * LowerAmount, 0.f, 0.f).Quaternion());
        Clearance = SweepPose(HeldPose);
    }

    // Obstructions clamp immediately. Releasing the retraction can be smoothed inside the safe path.
    WallRetraction = FMath::Clamp(FMath::FInterpTo(WallRetraction, Clearance.Required, DeltaTime, WallInterpSpeed),
        Clearance.Required, Clearance.Budget);
    ViewRoot->SetWorldLocationAndRotation(HeldPose.GetLocation() + Clearance.TowardCamera * WallRetraction, HeldPose.GetRotation());
    HeldView->SetVisibility(Clearance.bHasRoom);

    if (!HeldView->IsVisible() || !WantsFlashlightBeam())
    {
        FlashlightBeam->SetVisibility(false);
        return;
    }

    const FVector IntendedLight = ViewRoot->GetComponentTransform().TransformPosition(FVector(55.14f, 14.f, -12.48f));
    FHitResult BeamHit;
    const bool bBeamBlocked = World->SweepSingleByChannel(BeamHit, CameraLocation, IntendedLight, FQuat::Identity, ECC_Camera,
        FCollisionShape::MakeSphere(3.f), Query);
    if (bBeamBlocked && BeamHit.bStartPenetrating)
    {
        FlashlightBeam->SetVisibility(false);
        return;
    }

    FlashlightBeam->SetWorldLocationAndRotation(bBeamBlocked ? FVector(BeamHit.Location) : IntendedLight,
        CameraTransform.GetRotation() * FRotator(10.f, 0.f, 0.f).Quaternion());
    FlashlightBeam->SetVisibility(true);
}
