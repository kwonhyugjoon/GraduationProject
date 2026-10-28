"""Import locally authored held props, equip the pawn and dim existing museum lights."""
import unreal,json,sys
from pathlib import Path
root=Path(unreal.Paths.project_dir());sys.path.insert(0,str(root/'Scripts'))
from patrol_equipment import configure_equipment,apply_night_lighting,EQUIPMENT
source=root.parent/'Assets/Player/PatrolEquipment'
assets=unreal.AssetToolsHelpers.get_asset_tools()
unreal.EditorAssetLibrary.make_directory(EQUIPMENT)
palette=json.loads((source/'materials.json').read_text(encoding='utf8'))
materials={}
for name,data in palette.items():
    path=EQUIPMENT+'/M_'+name
    mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else assets.create_asset('M_'+name,EQUIPMENT,unreal.Material,unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    color=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-300,0)
    color.set_editor_property('constant',unreal.LinearColor(*data['color'],1))
    unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    for prop,key,y in [(unreal.MaterialProperty.MP_ROUGHNESS,'roughness',120),(unreal.MaterialProperty.MP_METALLIC,'metallic',220)]:
        value=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-300,y)
        value.set_editor_property('r',data[key]);unreal.MaterialEditingLibrary.connect_material_property(value,'',prop)
    if name=='Equipment_Lens':
        param=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-300,320)
        param.set_editor_properties({'parameter_name':'LampGlow','default_value':1.})
        mul=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionMultiply,-100,320)
        unreal.MaterialEditingLibrary.connect_material_expressions(color,'',mul,'A')
        unreal.MaterialEditingLibrary.connect_material_expressions(param,'',mul,'B')
        unreal.MaterialEditingLibrary.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat);assert unreal.EditorAssetLibrary.save_loaded_asset(mat)
    materials[name]=mat
unreal.SystemLibrary.execute_console_command(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
mesh_info={}
for name in ('SM_PatrolFlashlightView','SM_PatrolNotebookView'):
    options=unreal.FbxImportUI();options.set_editor_properties({'automated_import_should_detect_type':False,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_mesh':True,'import_animations':False,'import_materials':False,'import_textures':False})
    options.get_editor_property('static_mesh_import_data').set_editor_properties({'combine_meshes':True,'transform_vertex_to_absolute':True,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':True,'import_rotation':unreal.Rotator(pitch=0,yaw=90,roll=0),'auto_generate_collision':False,'generate_lightmap_u_vs':False,'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS})
    task=unreal.AssetImportTask();task.set_editor_properties({'filename':str(source/(name+'.fbx')),'destination_path':EQUIPMENT,'destination_name':name,'automated':True,'save':True,'replace_existing':True,'factory':unreal.FbxFactory(),'options':options})
    assets.import_asset_tasks([task]);mesh=unreal.load_asset(EQUIPMENT+'/'+name);assert isinstance(mesh,unreal.StaticMesh)
    for index,slot in enumerate(mesh.get_editor_property('static_materials')):
        material=str(slot.get_editor_property('material_slot_name'));assert material in materials,material
        mesh.set_material(index,materials[material])
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    bounds=mesh.get_bounds();mesh_info[name]={'center':[bounds.origin.x,bounds.origin.y,bounds.origin.z],'extent':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z]}
configure_equipment(unreal.load_asset('/Game/Stage1/Blueprints/BP_Stage1_FirstPerson'))
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert level.load_level('/Game/Stage1/Maps/L_MuseumStage1')
apply_night_lighting();assert level.save_current_level()
(root/'Saved/Validation').mkdir(parents=True,exist_ok=True)
(root/'Saved/Validation/equipment_setup.json').write_text(json.dumps({'passed':True,'meshes':mesh_info},indent=2),encoding='utf8')
unreal.log('PATROL_EQUIPMENT_SAVED '+json.dumps(mesh_info))
