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
constexpr float TextDesignWidth = 1200.0f;
constexpr float TextDesignHeight = 640.0f;

// Trim the transparent padding of the current artwork in the brush.
const FBox2f BookFrameArtworkUV(FVector2f(0.055f, 0.033f), FVector2f(0.945f, 0.974f));
const FAnchors TitleAnchors(0.13f, 0.145f, 0.435f, 0.29f);
const FAnchors BodyAnchors(0.565f, 0.265f, 0.88f, 0.77f);
const FAnchors PageNumberAnchors(0.725f, 0.815f, 0.88f, 0.88f);
}

void SPatrolManualReadingWidget::Construct(const FArguments& Args)
{
    BookFrameBrush.DrawAs = ESlateBrushDrawType::Image;
    BookFrameBrush.SetResourceObject(Args._BookFrame);
    BookFrameBrush.SetUVRegion(BookFrameArtworkUV);

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
                SNew(SOverlay)
                + SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
                [
                    SNew(SImage).Image(&BookFrameBrush)
                ]
                + SOverlay::Slot()
                [
                    // Keep glyphs uniformly scaled while the text canvas fills the book on both axes.
                    SNew(SScaleBox)
                    .HAlign(HAlign_Fill).VAlign(VAlign_Fill)
                    .Stretch(EStretch::ScaleToFit)
                    [
                        SNew(SBox).WidthOverride(TextDesignWidth).HeightOverride(TextDesignHeight)
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
