#pragma once

#include "Styling/SlateBrush.h"
#include "Widgets/SCompoundWidget.h"

class UTexture2D;

class SPatrolManualReadingWidget final : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SPatrolManualReadingWidget) {}
        SLATE_ARGUMENT(UTexture2D*, BookFrame)
    SLATE_END_ARGS()

    void Construct(const FArguments& Args);

private:
    FSlateBrush BookFrameBrush;
};
