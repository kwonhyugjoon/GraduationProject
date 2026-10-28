"""Check project package references in a fresh Unreal Python commandlet."""
import json
from pathlib import Path
import unreal

root=Path(unreal.Paths.project_dir())
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
options=unreal.AssetRegistryDependencyOptions()
options.set_editor_properties({'include_hard_package_references':True,'include_soft_package_references':True})
entries=registry.get_assets_by_path('/Game',recursive=True)
missing=[]
for entry in entries:
    for dependency in registry.get_dependencies(entry.package_name,options):
        path=str(dependency)
        if path.startswith('/Game/') and not unreal.EditorAssetLibrary.does_asset_exist(path):
            missing.append({'asset':str(entry.package_name),'missing':path})
report={'passed':not missing,'project_assets':len(entries),'missing_dependencies':missing}
out=root/'Saved/Validation';out.mkdir(parents=True,exist_ok=True)
(out/'project_assets_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
assert not missing,'Missing project dependencies: '+json.dumps(missing)
