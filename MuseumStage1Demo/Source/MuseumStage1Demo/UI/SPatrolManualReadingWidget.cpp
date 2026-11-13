#include "SPatrolManualReadingWidget.h"

#include "Brushes/SlateColorBrush.h"
#include "Engine/Texture2D.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SConstraintCanvas.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "PatrolManualReading"

namespace
{
constexpr float DimAlpha = 0.52f;
constexpr float ViewportMargin = 0.10f;
constexpr float BookDesignWidth = 1200.0f;

// Crop the dark outer margins of the 1671×941 image, leaving the teal outline intact.
const FVector2f BookSourceSize(1671.0f, 941.0f);
const FVector2f BookArtworkMin(96.0f, 15.0f);
const FVector2f BookArtworkMax(1576.0f, 926.0f);

const FAnchors TitleAnchors(0.083f, 0.105f, 0.455f, 0.20f);
const FAnchors DescriptionAnchors(0.066f, 0.265f, 0.455f, 0.84f);
const FAnchors CloseHintAnchors(0.132f, 0.902f, 0.455f, 0.95f);
const FAnchors ChapterAnchors(0.545f, 0.12f, 0.895f, 0.20f);
const FAnchors BodyAnchors(0.545f, 0.265f, 0.933f, 0.84f);
const FAnchors PageNumberAnchors(0.78f, 0.902f, 0.933f, 0.95f);
}

void SPatrolManualReadingWidget::Construct(const FArguments& Args)
{
    const FVector2f ArtworkSize = BookArtworkMax - BookArtworkMin;
    const float BookDesignHeight = BookDesignWidth * ArtworkSize.Y / ArtworkSize.X;
    BookFrameBrush.DrawAs = ESlateBrushDrawType::Image;
    BookFrameBrush.SetResourceObject(Args._BookFrame);
    BookFrameBrush.SetUVRegion(FBox2f(BookArtworkMin / BookSourceSize, BookArtworkMax / BookSourceSize));

    const FLinearColor Ink = FLinearColor::FromSRGBColor(FColor(58, 32, 18));
    static const FSlateColorBrush DimBrush(FLinearColor(0.0f, 0.0f, 0.0f, DimAlpha));

    ChildSlot
    [
        SNew(SOverlay)
        + SOverlay::Slot()
        [
            SNew(SImage).Image(&DimBrush)
        ]
        + SOverlay::Slot()
        [
            SNew(SConstraintCanvas)
            + SConstraintCanvas::Slot()
            .Anchors(FAnchors(ViewportMargin, ViewportMargin, 1.0f - ViewportMargin, 1.0f - ViewportMargin))
            .Offset(FMargin(0))
            [
                SNew(SScaleBox)
                .HAlign(HAlign_Center).VAlign(VAlign_Center)
                .Stretch(EStretch::ScaleToFit)
                [
                    SNew(SBox).WidthOverride(BookDesignWidth).HeightOverride(BookDesignHeight)
                    [
                        SNew(SOverlay)
                        + SOverlay::Slot()
                        [
                            SNew(SImage).Image(&BookFrameBrush)
                        ]
                        + SOverlay::Slot()
                        [
                            SNew(SConstraintCanvas)
                            + SConstraintCanvas::Slot()
                            .Anchors(TitleAnchors).Offset(FMargin(0))
                            [
                                SNew(STextBlock).Text(LOCTEXT("Title", "업무지침서"))
                                .Font(FCoreStyle::GetDefaultFontStyle("Bold", 42))
                                .ColorAndOpacity(Ink)
                                .Clipping(EWidgetClipping::ClipToBounds)
                            ]
                            + SConstraintCanvas::Slot()
                            .Anchors(DescriptionAnchors).Offset(FMargin(0))
                            [
                                SNew(STextBlock).Text(LOCTEXT("Description", "박물관 야간 순찰\n기본 장비 사용 안내"))
                                .Font(FCoreStyle::GetDefaultFontStyle("Regular", 27))
                                .ColorAndOpacity(Ink)
                                .AutoWrapText(true)
                                .Clipping(EWidgetClipping::ClipToBounds)
                            ]
                            + SConstraintCanvas::Slot()
                            .Anchors(CloseHintAnchors).Offset(FMargin(0))
                            [
                                SNew(STextBlock).Text(LOCTEXT("CloseHint", "좌클릭 닫기"))
                                .Font(FCoreStyle::GetDefaultFontStyle("Regular", 21))
                                .ColorAndOpacity(Ink)
                                .Clipping(EWidgetClipping::ClipToBounds)
                            ]
                            + SConstraintCanvas::Slot()
                            .Anchors(ChapterAnchors).Offset(FMargin(0))
                            [
                                SNew(STextBlock).Text(LOCTEXT("ChapterTitle", "01 기본 장비"))
                                .Font(FCoreStyle::GetDefaultFontStyle("Bold", 32))
                                .ColorAndOpacity(Ink)
                                .Clipping(EWidgetClipping::ClipToBounds)
                            ]
                            + SConstraintCanvas::Slot()
                            .Anchors(BodyAnchors).Offset(FMargin(0))
                            [
                                SNew(STextBlock).Text(LOCTEXT("Placeholder", "업무 내용은 추후 연결"))
                                .Font(FCoreStyle::GetDefaultFontStyle("Regular", 27))
                                .ColorAndOpacity(Ink)
                                .AutoWrapText(true)
                                .Clipping(EWidgetClipping::ClipToBounds)
                            ]
                            + SConstraintCanvas::Slot()
                            .Anchors(PageNumberAnchors).Offset(FMargin(0))
                            [
                                SNew(STextBlock).Text(FText::Format(LOCTEXT("PageNumber", "{0} / {1}"), 1, 1))
                                .Font(FCoreStyle::GetDefaultFontStyle("Regular", 21))
                                .ColorAndOpacity(Ink)
                                .Justification(ETextJustify::Right)
                                .Clipping(EWidgetClipping::ClipToBounds)
                            ]
                        ]
                    ]
                ]
            ]
        ]
    ];
}

#undef LOCTEXT_NAMESPACE
