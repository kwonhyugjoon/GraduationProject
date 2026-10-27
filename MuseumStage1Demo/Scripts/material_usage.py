"""Repair only ISM usage flags, then verify persisted flags in a fresh editor."""
import unreal,sys,json,hashlib
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir())
baseline={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'Content').rglob('*') if p.is_file()}
sys.path.insert(0,str(ROOT/'Scripts'))
from stage1_layout import make_layout
OUT=ROOT/'Saved/Validation'
OUT.mkdir(parents=True,exist_ok=True)
repair='-Stage1RepairMaterialUsage' in unreal.SystemLibrary.get_command_line()
names={key[1] for key in make_layout()['groups']}
paths=sorted('/Game/Stage1/Materials/'+('M_GalleryFloor' if name=='gallery_floor' else 'M_'+name) for name in names)
materials=[]
for path in paths:
    mat=unreal.load_asset(path)
    assert isinstance(mat,unreal.Material),'Expected a project material: '+path
    before=mat.get_editor_property('used_with_instanced_static_meshes')
    if repair:
        mat.set_editor_property('used_with_instanced_static_meshes',True)
        unreal.MaterialEditingLibrary.recompile_material(mat)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False),'Material save failed: '+path
    enabled=mat.get_editor_property('used_with_instanced_static_meshes')
    disk=ROOT/'Content'/Path(path.removeprefix('/Game/')+'.uasset')
    materials.append({'asset':path,'before':before,'enabled':enabled,
        'file':disk.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(disk.read_bytes()).hexdigest()})
assert all(m['enabled'] for m in materials),'An instanced-mesh material is missing its usage flag'
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Stage1/Maps/L_MuseumStage1')
actual=set()
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        for i in range(comp.get_num_materials()):
            mat=comp.get_material(i)
            assert isinstance(mat,unreal.Material),'Unexpected material type on '+actor.get_actor_label()
            actual.add(str(mat.get_path_name()).split('.')[0])
            assert mat.get_editor_property('used_with_instanced_static_meshes'),'Map material flag is missing: '+str(mat.get_path_name())
assert actual==set(paths),'Map material inventory differs from the generator'
changed=[p for p,sha in baseline.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=sha]
assert all(p.startswith('Content/Stage1/Materials/') for p in changed),'The repair changed unrelated content'
report={'passed':True,'mode':'repair' if repair else 'fresh_process_verification',
    'material_count':len(materials),'actual_map_materials':sorted(actual),'materials':materials,
    'changed_content':changed,'map_unchanged':True,'map_source_sha256':hashlib.sha256((ROOT/'Content/Stage1/Maps/L_MuseumStage1.umap').read_bytes()).hexdigest(),
    'baseline_file':'in_process_content_snapshot',
    'scope':'Saved ISM usage flags on the existing map materials; read-only verification unless repair was requested.'}
(OUT/('material_usage_repair.json' if repair else 'material_usage_validation.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.log('STAGE1_MATERIAL_USAGE_'+('REPAIR' if repair else 'VERIFIED')+' '+str(len(materials)))
