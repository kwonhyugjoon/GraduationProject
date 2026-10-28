using UnrealBuildTool;
using System.Collections.Generic;

public class MuseumStage1DemoEditorTarget : TargetRules
{
    public MuseumStage1DemoEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
        ExtraModuleNames.Add("MuseumStage1Demo");
    }
}
