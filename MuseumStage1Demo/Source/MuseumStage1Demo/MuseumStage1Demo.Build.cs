using UnrealBuildTool;

public class MuseumStage1Demo : ModuleRules
{
    public MuseumStage1Demo(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        if (Target.bBuildEditor) PrivateDependencyModuleNames.Add("ApplicationCore");
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore" });
    }
}
