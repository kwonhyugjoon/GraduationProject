#include "PatrolEquipmentHUDSubsystem.h"
#include "SPatrolManualReadingWidget.h"

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

constexpr float SlotSize = 142.0f;
constexpr float SelectedSlotSize = SlotSize * 1.12f;
constexpr float SlotGap = 8.0f;
constexpr float StatusWidth = 159.0f;
constexpr float StatusHeight = StatusWidth / 6.0f;
constexpr float StatusGap = 6.0f;
constexpr float EmptyHandIconOpacity = 0.30f;

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
        SLATE_ARGUMENT(UTexture2D*, ManualBookFrame)
    SLATE_END_ARGS()

    void Construct(const FArguments& Args)
    {
        Controller = Args._Controller;
        InitializeTextureBrushes(Args._Textures);

        const FText Names[] = {
            LOCTEXT("FlashlightSlot", "손전등"),
            LOCTEXT("NotebookSlot", "업무지침서"),
            LOCTEXT("EmptyHandSlot", "빈손")
        };
        const FSlateBrush* const Icons[] = {
            GetTextureBrush(IconFlashlight), GetTextureBrush(IconManual), GetTextureBrush(IconArtifact)
        };
        const TSharedRef<SHorizontalBox> Row = SNew(SHorizontalBox);
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(Slots); ++Index)
        {
            TSharedRef<SWidget> Column = CreateEquipmentSlot(
                Slots[Index], FText::AsNumber(Index + 1), Icons[Index], Names[Index],
                Index == 2 ? EmptyHandIconOpacity : 1.0f);
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

        const TSharedRef<SOverlay> Overlay = SNew(SOverlay);
        if (Args._ManualBookFrame)
        {
            Overlay->AddSlot()
            [
                SAssignNew(ManualReading, SPatrolManualReadingWidget)
                .BookFrame(Args._ManualBookFrame)
                .Visibility(EVisibility::Collapsed)
            ];
        }

        Overlay->AddSlot().Padding(FMargin(24, 24, 38, 34))
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
        ];

        ChildSlot[Overlay];
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
        const auto SetArtworkRegion = [this](EEquipmentHUDTexture Id, FVector2f SourceSize,
            FVector2f Min, FVector2f Max, float IconHeight = 0.0f)
        {
            FSlateBrush& Brush = TextureBrushes[Id];
            Brush.SetUVRegion(FBox2f(Min / SourceSize, Max / SourceSize));
            if (IconHeight > 0.0f)
            {
                const FVector2f ArtworkSize = Max - Min;
                Brush.SetImageSize(ArtworkSize * (IconHeight / ArtworkSize.Y));
            }
        };

        const FVector2f SquareSource(1254, 1254);
        SetArtworkRegion(SlotNormal, SquareSource, {271, 276}, {984, 977});
        SetArtworkRegion(SlotSelected, SquareSource, {248, 246}, {1004, 1008});
        SetArtworkRegion(IconFlashlight, SquareSource, {337, 292}, {868, 945}, 64.0f);
        SetArtworkRegion(IconManual, SquareSource, {352, 349}, {905, 949}, 60.0f);
        SetArtworkRegion(IconArtifact, SquareSource, {346, 298}, {908, 962}, 62.0f);

        const FVector2f StatusSource(2172, 724);
        SetArtworkRegion(StatusOn, StatusSource, {289, 217}, {1883, 505});
        SetArtworkRegion(StatusOff, StatusSource, {405, 248}, {1767, 476});
    }

    const FSlateBrush* GetTextureBrush(EEquipmentHUDTexture Id, const FSlateBrush* Fallback = nullptr) const
    {
        const FSlateBrush& Brush = TextureBrushes[Id];
        return Brush.GetResourceObject() ? &Brush : Fallback;
    }

    TSharedRef<SWidget> CreateEquipmentSlot(FSlotWidgets& Slot, const FText& Key,
        const FSlateBrush* Icon, const FText& Name, float IconOpacity)
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
                    .Padding(FMargin(10, 14, 10, 15))
                    [
                        SNew(SOverlay)
                        + SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top).Padding(4, 0, 0, 0)
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
                        + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(0, 0, 0, 18)
                        [
                            SNew(SBox).WidthOverride(68).HeightOverride(64)
                            [
                                SNew(SScaleBox).Stretch(EStretch::ScaleToFit).HAlign(HAlign_Center).VAlign(VAlign_Center)
                                [
                                    SNew(SImage).Image(Icon)
                                    .ColorAndOpacity(FLinearColor(1.0f, 1.0f, 1.0f, IconOpacity))
                                    .Visibility(Icon ? EVisibility::Visible : EVisibility::Hidden)
                                ]
                            ]
                        ]
                        + SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Bottom)
                        [
                            SNew(SScaleBox)
                            .HAlign(HAlign_Center).VAlign(VAlign_Center)
                            .Stretch(EStretch::ScaleToFitX).StretchDirection(EStretchDirection::DownOnly)
                            [
                                SAssignNew(Slot.Name, STextBlock).Text(Name)
                                .Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
                            ]
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
        static const FSlateRoundedBoxBrush IndicatorBrush(FLinearColor::White, 1.5f, FVector2f(3, 10));

        return SNew(SBox)
            .WidthOverride(StatusWidth).HeightOverride(StatusHeight + StatusGap)
            .Padding(FMargin(0, 0, 0, StatusGap))
            [
                SAssignNew(FlashlightStatus, SBox).Visibility(EVisibility::Collapsed)
                [
                    SAssignNew(FlashlightFrame, SBorder).Padding(0)
                    [
                        SNew(SOverlay)
                        + SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(9, 0, 0, 0)
                        [
                            SAssignNew(FlashlightIndicator, SImage).Image(&IndicatorBrush)
                        ]
                        + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
                        [
                            SAssignNew(FlashlightText, STextBlock)
                            .Font(FCoreStyle::GetDefaultFontStyle("Bold", 14))
                        ]
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
        const bool bShowManual = ManualReading.IsValid() && CurrentEquipment && CurrentEquipment->IsManualReadingReady();
        if (ManualReading.IsValid())
        {
            const EVisibility ManualVisibility = bShowManual ? EVisibility::HitTestInvisible : EVisibility::Collapsed;
            if (ManualReading->GetVisibility() != ManualVisibility) ManualReading->SetVisibility(ManualVisibility);
        }

        const EVisibility EquipmentVisibility = CurrentEquipment && !bShowManual
            ? EVisibility::Visible : EVisibility::Collapsed;
        if (Panel->GetVisibility() != EquipmentVisibility) Panel->SetVisibility(EquipmentVisibility);

        const int32 Slot = CurrentEquipment ? CurrentEquipment->GetHandSlot() : 0;
        const bool bFlashlightOn = CurrentEquipment && CurrentEquipment->IsFlashlightOn();
        if (Slot == DisplayedSlot && bFlashlightOn == bDisplayedFlashlightOn) return;

        if (Slot != DisplayedSlot)
        {
            DisplayedSlot = Slot;
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
    TSharedPtr<SPatrolManualReadingWidget> ManualReading;
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
        .ManualBookFrame(ManualBookFrame.Get())
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

    static constexpr TCHAR ManualBookFramePath[] = TEXT("/Game/UI/Manual/T_Manual_BookFrame.T_Manual_BookFrame");
    ManualBookFrame = LoadObject<UTexture2D>(nullptr, ManualBookFramePath);
    if (!ManualBookFrame || ManualBookFrame->GetSizeX() <= 0 || ManualBookFrame->GetSizeY() <= 0)
    {
        ManualBookFrame = nullptr;
        UE_LOG(LogTemp, Warning, TEXT("Patrol manual HUD could not load a usable Texture2D %s"), ManualBookFramePath);
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
