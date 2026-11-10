#include "PatrolEquipmentHUDSubsystem.h"

#include "../PatrolEquipmentComponent.h"
#include "Brushes/SlateColorBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Texture2D.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "PatrolEquipmentHUD"

namespace
{
enum EEquipmentHUDTexture : int32
{
    SlotNormal,
    SlotSelected,
    StatusOn,
    StatusOff,
    IconFlashlight,
    IconManual,
    IconArtifact,
    TextureCount
};

const TCHAR* const TextureNames[] = {
    TEXT("T_EquipmentSlot_Normal"),
    TEXT("T_EquipmentSlot_Selected"),
    TEXT("T_FlashlightStatus_On"),
    TEXT("T_FlashlightStatus_Off"),
    TEXT("T_EquipmentIcon_Flashlight"),
    TEXT("T_EquipmentIcon_Manual"),
    TEXT("T_EquipmentIcon_Artifact")
};
static_assert(UE_ARRAY_COUNT(TextureNames) == TextureCount);

constexpr float SlotSize = 132.0f;
constexpr float SelectedSlotSize = SlotSize * 1.12f;
constexpr float SlotGap = 8.0f;

const FLinearColor Gold = FLinearColor::FromSRGBColor(FColor(255, 195, 93));
const FLinearColor Brass = FLinearColor::FromSRGBColor(FColor(153, 119, 73));
const FLinearColor WarmWhite = FLinearColor::FromSRGBColor(FColor(255, 240, 209));
const FLinearColor MutedWhite = FLinearColor::FromSRGBColor(FColor(215, 204, 186));

class SPatrolEquipmentHUD final : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SPatrolEquipmentHUD) {}
        SLATE_ARGUMENT(APlayerController*, Controller)
        SLATE_ARGUMENT(TConstArrayView<TObjectPtr<UTexture2D>>, Textures)
    SLATE_END_ARGS()

    void Construct(const FArguments& Args)
    {
        Controller = Args._Controller;
        InitializeTextureBrushes(Args._Textures);

        const FText Names[] = {
            LOCTEXT("FlashlightSlot", "손전등"),
            LOCTEXT("NotebookSlot", "업무지침서"),
            LOCTEXT("RelicSlot", "유물")
        };
        constexpr EEquipmentHUDTexture Icons[] = { IconFlashlight, IconManual, IconArtifact };
        const TSharedRef<SHorizontalBox> Row = SNew(SHorizontalBox);
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(Slots); ++Index)
        {
            TSharedRef<SWidget> Column = CreateEquipmentSlot(
                Slots[Index], FText::AsNumber(Index + 1), Icons[Index], Names[Index]);
            if (Index == 0)
            {
                Column = SNew(SVerticalBox)
                    + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
                    [
                        CreateFlashlightStatus()
                    ]
                    + SVerticalBox::Slot().AutoHeight()
                    [
                        Column
                    ];
            }

            Row->AddSlot().AutoWidth().VAlign(VAlign_Bottom).Padding(Index == 0 ? 0.0f : SlotGap, 0, 0, 0)
            [
                Column
            ];
        }

        ChildSlot
        [
            SNew(SOverlay)
            + SOverlay::Slot().Padding(FMargin(24, 24, 38, 34))
            [
                SAssignNew(Panel, SScaleBox)
                .HAlign(HAlign_Right)
                .VAlign(VAlign_Bottom)
                .Stretch(EStretch::ScaleToFit)
                .StretchDirection(EStretchDirection::DownOnly)
                .Visibility(EVisibility::Collapsed)
                [
                    Row
                ]
            ]
        ];

        RefreshState();
    }

    virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override
    {
        RefreshState();
    }

private:
    struct FSlotWidgets
    {
        TSharedPtr<SBox> Size;
        TSharedPtr<SBorder> Frame;
        TSharedPtr<SBorder> KeyBadge;
        TSharedPtr<STextBlock> Name;
    };

    void InitializeTextureBrushes(TConstArrayView<TObjectPtr<UTexture2D>> Textures)
    {
        for (int32 Index = 0; Index < Textures.Num(); ++Index)
        {
            if (UTexture2D* Texture = Textures[Index].Get())
            {
                TextureBrushes[Index].SetResourceObject(Texture);
                TextureBrushes[Index].SetImageSize(FVector2f(Texture->GetSizeX(), Texture->GetSizeY()));
            }
        }

        // Trim transparent source margins without resizing or editing the textures.
        const FVector2f FrameSourceSize(1448, 1086);
        TextureBrushes[SlotNormal].SetUVRegion(FBox2f(
            FVector2f(212, 25) / FrameSourceSize, FVector2f(1232, 1045) / FrameSourceSize));
        TextureBrushes[SlotSelected].SetUVRegion(FBox2f(
            FVector2f(247, 55) / FrameSourceSize, FVector2f(1197, 1005) / FrameSourceSize));

        const FVector2f StatusSourceSize(2172, 724);
        const FBox2f StatusUV(FVector2f(250, 69) / StatusSourceSize, FVector2f(1922, 626) / StatusSourceSize);
        TextureBrushes[StatusOn].SetUVRegion(StatusUV);
        TextureBrushes[StatusOff].SetUVRegion(StatusUV);
    }

    const FSlateBrush* GetTextureBrush(EEquipmentHUDTexture Id, const FSlateBrush* Fallback = nullptr) const
    {
        const FSlateBrush& Brush = TextureBrushes[Id];
        return Brush.GetResourceObject() ? &Brush : Fallback;
    }

    TSharedRef<SWidget> CreateEquipmentSlot(FSlotWidgets& Slot, const FText& Key,
        EEquipmentHUDTexture Icon, const FText& Name)
    {
        static const FSlateColorBrush SolidBrush(FLinearColor::White);

        // Reserve the selected size so every card stays centered in its own cell.
        return SNew(SBox)
            .WidthOverride(SelectedSlotSize).HeightOverride(SelectedSlotSize)
            .HAlign(HAlign_Center).VAlign(VAlign_Bottom)
            [
                SAssignNew(Slot.Size, SBox)
                [
                    SAssignNew(Slot.Frame, SBorder)
                    .Padding(FMargin(15, 16, 15, 17))
                    [
                        SNew(SOverlay)
                        + SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top)
                        [
                            SAssignNew(Slot.KeyBadge, SBorder)
                            .BorderImage(&SolidBrush)
                            .Padding(0)
                            [
                                SNew(SBox).WidthOverride(26).HeightOverride(21)
                                .HAlign(HAlign_Center).VAlign(VAlign_Center)
                                [
                                    SNew(STextBlock).Text(Key)
                                    .Font(FCoreStyle::GetDefaultFontStyle("Bold", 14))
                                    .ColorAndOpacity(FLinearColor(0.025f, 0.016f, 0.008f))
                                ]
                            ]
                        ]
                        + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(0, 0, 0, 8)
                        [
                            SNew(SBox).WidthOverride(76).HeightOverride(76)
                            [
                                SNew(SScaleBox).Stretch(EStretch::ScaleToFit).HAlign(HAlign_Center).VAlign(VAlign_Center)
                                [
                                    SNew(SImage).Image(GetTextureBrush(Icon))
                                ]
                            ]
                        ]
                        + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom)
                        [
                            SAssignNew(Slot.Name, STextBlock).Text(Name)
                            .Font(FCoreStyle::GetDefaultFontStyle("Bold", 20))
                        ]
                    ]
                ]
            ];
    }

    void UpdateSlotVisual(FSlotWidgets& Slot, bool bSelected)
    {
        static const FSlateRoundedBoxBrush NormalFrame(
            FLinearColor::FromSRGBColor(FColor(22, 22, 23, 222)), 5.0f, Brass, 1.0f);
        static const FSlateRoundedBoxBrush SelectedFrame(
            FLinearColor::FromSRGBColor(FColor(79, 47, 19, 231)), 5.0f, Gold, 2.0f);

        const float Size = bSelected ? SelectedSlotSize : SlotSize;
        Slot.Size->SetWidthOverride(Size);
        Slot.Size->SetHeightOverride(Size);
        Slot.Frame->SetBorderImage(bSelected
            ? GetTextureBrush(SlotSelected, &SelectedFrame)
            : GetTextureBrush(SlotNormal, &NormalFrame));
        Slot.KeyBadge->SetBorderBackgroundColor(FSlateColor(bSelected ? Gold : Brass));
        Slot.Name->SetColorAndOpacity(FSlateColor(bSelected ? WarmWhite : MutedWhite));
    }

    TSharedRef<SWidget> CreateFlashlightStatus()
    {
        static const FSlateRoundedBoxBrush IndicatorBrush(FLinearColor::White, 5.0f, FVector2f(10, 10));
        constexpr float BottomGap = 6.0f;

        return SAssignNew(FlashlightStatus, SBox)
            .WidthOverride(SelectedSlotSize)
            .HeightOverride(SelectedSlotSize / 3.0f + BottomGap)
            .Padding(FMargin(0, 0, 0, BottomGap))
            .Visibility(EVisibility::Collapsed)
            [
                SAssignNew(FlashlightFrame, SBorder)
                .HAlign(HAlign_Center).VAlign(VAlign_Center)
                .Padding(0)
                [
                    SNew(SHorizontalBox)
                    + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
                    [
                        SAssignNew(FlashlightIndicator, SImage).Image(&IndicatorBrush)
                    ]
                    + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
                    [
                        SAssignNew(FlashlightText, STextBlock)
                        .Font(FCoreStyle::GetDefaultFontStyle("Bold", 14))
                    ]
                ]
            ];
    }

    void RefreshState()
    {
        const APlayerController* PC = Controller.Get();
        APawn* Pawn = PC ? PC->GetPawn().Get() : nullptr;
        if (Pawn != ObservedPawn.Get())
        {
            ObservedPawn = Pawn;
            Equipment = IsValid(Pawn) ? Pawn->FindComponentByClass<UPatrolEquipmentComponent>() : nullptr;
        }

        const UPatrolEquipmentComponent* CurrentEquipment = ObservedPawn.IsValid() ? Equipment.Get() : nullptr;
        const int32 Slot = CurrentEquipment ? CurrentEquipment->GetHandSlot() : 0;
        const bool bFlashlightOn = CurrentEquipment && CurrentEquipment->IsFlashlightOn();
        if (Slot == DisplayedSlot && bFlashlightOn == bDisplayedFlashlightOn) return;

        if (Slot != DisplayedSlot)
        {
            DisplayedSlot = Slot;
            Panel->SetVisibility(CurrentEquipment ? EVisibility::Visible : EVisibility::Collapsed);
            FlashlightStatus->SetVisibility(Slot == 1 ? EVisibility::Visible : EVisibility::Collapsed);

            for (int32 Index = 0; Index < UE_ARRAY_COUNT(Slots); ++Index)
            {
                UpdateSlotVisual(Slots[Index], Slot == Index + 1);
            }
        }

        static const FSlateRoundedBoxBrush StatusFallback(
            FLinearColor::FromSRGBColor(FColor(23, 20, 16, 230)), 4.0f, Brass, 1.0f);
        bDisplayedFlashlightOn = bFlashlightOn;
        FlashlightFrame->SetBorderImage(GetTextureBrush(bFlashlightOn ? StatusOn : StatusOff, &StatusFallback));
        FlashlightText->SetText(bFlashlightOn
            ? LOCTEXT("FlashlightOn", "손전등 ON")
            : LOCTEXT("FlashlightOff", "손전등 OFF"));
        FlashlightText->SetColorAndOpacity(FSlateColor(bFlashlightOn ? WarmWhite : MutedWhite));
        FlashlightIndicator->SetColorAndOpacity(FSlateColor(bFlashlightOn ? Gold : FLinearColor(0.22f, 0.22f, 0.22f)));
    }

    FSlateBrush TextureBrushes[TextureCount];
    TWeakObjectPtr<APlayerController> Controller;
    TWeakObjectPtr<APawn> ObservedPawn;
    TWeakObjectPtr<UPatrolEquipmentComponent> Equipment;
    TSharedPtr<SScaleBox> Panel;
    FSlotWidgets Slots[3];
    TSharedPtr<SBox> FlashlightStatus;
    TSharedPtr<SBorder> FlashlightFrame;
    TSharedPtr<SImage> FlashlightIndicator;
    TSharedPtr<STextBlock> FlashlightText;
    int32 DisplayedSlot = 0;
    bool bDisplayedFlashlightOn = false;
};
}

void UPatrolEquipmentHUDSubsystem::PlayerControllerChanged(APlayerController* NewPlayerController)
{
    Super::PlayerControllerChanged(NewPlayerController);
    RemoveHUD();

    ULocalPlayer* LocalPlayer = GetLocalPlayer();
    UGameViewportClient* Viewport = LocalPlayer ? LocalPlayer->ViewportClient.Get() : nullptr;
    if (!NewPlayerController || NewPlayerController->GetLocalPlayer() != LocalPlayer
        || !Viewport || !Viewport->GetGameLayerManager().IsValid()) return;

    LoadHUDTextures();
    HUD = SNew(SPatrolEquipmentHUD)
        .Controller(NewPlayerController)
        .Textures(HUDTextures)
        .Visibility(EVisibility::HitTestInvisible);
    HUDViewport = Viewport;
    Viewport->AddViewportWidgetForPlayer(LocalPlayer, HUD.ToSharedRef(), 0);
}

void UPatrolEquipmentHUDSubsystem::LoadHUDTextures()
{
    if (!HUDTextures.IsEmpty()) return;

    HUDTextures.Reserve(TextureCount);
    for (const TCHAR* Name : TextureNames)
    {
        const FString Path = FString::Printf(TEXT("/Game/UI/Equipment/%s.%s"), Name, Name);
        UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *Path);
        if (!Texture)
        {
            UE_LOG(LogTemp, Warning, TEXT("Patrol equipment HUD could not load Texture2D %s"), *Path);
        }
        HUDTextures.Add(Texture);
    }
}

void UPatrolEquipmentHUDSubsystem::Deinitialize()
{
    RemoveHUD();
    Super::Deinitialize();
}

void UPatrolEquipmentHUDSubsystem::RemoveHUD()
{
    if (UGameViewportClient* Viewport = HUDViewport.Get(); Viewport && HUD.IsValid())
    {
        Viewport->RemoveViewportWidgetForPlayer(GetLocalPlayer(), HUD.ToSharedRef());
    }
    HUD.Reset();
    HUDViewport.Reset();
}

#undef LOCTEXT_NAMESPACE
