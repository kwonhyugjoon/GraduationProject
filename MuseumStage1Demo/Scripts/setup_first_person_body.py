"""Import the patrol body and retarget the template locomotion without rebuilding the map."""
import unreal,json
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());BASE='/Game/Stage1/FirstPerson/Patrol'
(ROOT/'Saved/Validation').mkdir(parents=True,exist_ok=True)
assets=unreal.AssetToolsHelpers.get_asset_tools()
unreal.SystemLibrary.execute_console_command(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
mesh_path=BASE+'/SK_PatrolBody'
existing=unreal.load_asset(mesh_path) if unreal.EditorAssetLibrary.does_asset_exist(mesh_path) else None
if existing is None or existing.get_editor_property('skeleton') is None or '-Stage1RefreshBodyMeshes' in unreal.SystemLibrary.get_command_line():
    options=unreal.FbxImportUI()
    options.set_editor_properties({'automated_import_should_detect_type':False,'import_as_skeletal':True,
        'mesh_type_to_import':unreal.FBXImportType.FBXIT_SKELETAL_MESH,'import_mesh':True,
        'original_import_type':unreal.FBXImportType.FBXIT_SKELETAL_MESH,
        'import_animations':False,'import_materials':False,'import_textures':False,'create_physics_asset':False})
    options.get_editor_property('skeletal_mesh_import_data').set_editor_properties({
        'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,
        'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS})
    task=unreal.AssetImportTask()
    task.set_editor_properties({'filename':str(ROOT/'References/FirstPersonBody/patrol_first_person_body.fbx'),
        'destination_path':BASE,'destination_name':'SK_PatrolBody','automated':True,'save':True,'replace_existing':True,
        'factory':unreal.FbxFactory(),'options':options})
    assets.import_asset_tasks([task])
target=unreal.load_asset(mesh_path)
assert isinstance(target,unreal.SkeletalMesh),'Patrol skeletal import failed'
assert target.get_editor_property('skeleton'),'The patrol body has no Skeleton asset'
assert unreal.EditorAssetLibrary.save_loaded_asset(target.get_editor_property('skeleton'),only_if_is_dirty=False)
slots=list(target.get_editor_property('materials'))
for i,slot in enumerate(slots):
    name=str(slot.get_editor_property('material_slot_name'))
    if name.endswith('_001'):name=name[:-4]
    mat=unreal.load_asset('/Game/Stage1/Materials/M_Patrol_'+name)
    assert mat,'Missing patrol material '+name
    mat.set_editor_property('used_with_skeletal_mesh',True)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False)
    slot.set_editor_property('material_interface',mat)
target.set_editor_property('materials',slots)
unreal.EditorAssetLibrary.save_loaded_asset(target)
world_path=BASE+'/SK_PatrolWorld'
existing_world=unreal.load_asset(world_path) if unreal.EditorAssetLibrary.does_asset_exist(world_path) else None
if existing_world is None or existing_world.get_editor_property('skeleton') is None or '-Stage1RefreshBodyMeshes' in unreal.SystemLibrary.get_command_line():
    options=unreal.FbxImportUI()
    options.set_editor_properties({'automated_import_should_detect_type':False,'import_as_skeletal':True,
        'mesh_type_to_import':unreal.FBXImportType.FBXIT_SKELETAL_MESH,'import_mesh':True,
        'original_import_type':unreal.FBXImportType.FBXIT_SKELETAL_MESH,
        'import_animations':False,'import_materials':False,'import_textures':False,'create_physics_asset':False,
        'skeleton':target.get_editor_property('skeleton')})
    options.get_editor_property('skeletal_mesh_import_data').set_editor_properties({
        'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,
        'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS})
    task=unreal.AssetImportTask()
    task.set_editor_properties({'filename':str(ROOT/'References/FirstPersonBody/patrol_world.fbx'),
        'destination_path':BASE,'destination_name':'SK_PatrolWorld','automated':True,'save':True,'replace_existing':True,
        'factory':unreal.FbxFactory(),'options':options})
    assets.import_asset_tasks([task])
world_mesh=unreal.load_asset(world_path);world_slots=list(world_mesh.get_editor_property('materials'))
assert 120<target.get_bounds().box_extent.z*2<150,'The body mesh must use centimetres: '+str(target.get_bounds())
assert 170<world_mesh.get_bounds().box_extent.z*2<180,'The world mesh must use centimetres: '+str(world_mesh.get_bounds())
assert world_mesh.get_editor_property('skeleton')==target.get_editor_property('skeleton'),'The display and world bodies must share their Skeleton'
for slot in world_slots:
    name=str(slot.get_editor_property('material_slot_name')).removesuffix('_001')
    mat=unreal.load_asset('/Game/Stage1/Materials/M_Patrol_'+name)
    assert mat,'Missing patrol material '+name
    mat.set_editor_property('used_with_skeletal_mesh',True)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False)
    slot.set_editor_property('material_interface',mat)
world_mesh.set_editor_property('materials',world_slots)
unreal.EditorAssetLibrary.save_loaded_asset(world_mesh)
source=unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple')
chains={'Spine':('spine_01','spine_05','spine_01','spine_03'),
        'Neck':('neck_01','neck_02','neck','neck'),'Head':('head','head','head','head'),
        'ClavicleL':('clavicle_l','clavicle_l','clavicle_l','clavicle_l'),
        'ClavicleR':('clavicle_r','clavicle_r','clavicle_r','clavicle_r'),
        'ArmL':('upperarm_l','hand_l','upperarm_l','hand_l'),
        'ArmR':('upperarm_r','hand_r','upperarm_r','hand_r'),
        'LegL':('thigh_l','foot_l','thigh_l','foot_l'),'LegR':('thigh_r','foot_r','thigh_r','foot_r')}
rigs=[]
for name,mesh,start in [('IK_Source',source,0),('IK_Patrol',target,2)]:
    path=BASE+'/'+name
    rig=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else assets.create_asset(name,BASE,unreal.IKRigDefinition,unreal.IKRigDefinitionFactory())
    controller=unreal.IKRigController.get_controller(rig)
    assert controller.set_skeletal_mesh(mesh)
    assert controller.set_retarget_root('pelvis')
    assert abs(controller.get_ref_pose_transform_of_bone('root').scale3d.x-1)<.01,'Animation rig root scale must be 1'
    existing={str(c.chain_name) for c in controller.get_retarget_chains()}
    for chain,bones in chains.items():
        if chain not in existing:controller.add_retarget_chain(chain,bones[start],bones[start+1],'None')
    unreal.EditorAssetLibrary.save_loaded_asset(rig);rigs.append(rig)
path=BASE+'/RTG_Patrol'
retarget=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else assets.create_asset('RTG_Patrol',BASE,unreal.IKRetargeter,unreal.IKRetargetFactory())
controller=unreal.IKRetargeterController.get_controller(retarget)
controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE,rigs[0])
controller.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET,rigs[1])
if controller.get_num_retarget_ops()==0:controller.add_default_ops()
controller.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE,rigs[0])
controller.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET,rigs[1])
controller.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE,source)
controller.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET,target)
controller.auto_map_chains(unreal.AutoMapChainType.EXACT,True)
for chain in chains:assert controller.set_source_chain(chain,chain),'Chain mapping failed '+chain
# FK preserves the custom short legs; this model has no mannequin IK helper bones.
for index in (2,3,4):assert controller.set_retarget_op_enabled(index,False)
controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
unreal.EditorAssetLibrary.save_loaded_asset(retarget)
bp_path=BASE+'/Animations/ABP_PatrolLocomotion'
if not unreal.EditorAssetLibrary.does_asset_exist(bp_path):
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for command in ('a.ForceEvalRawData 1','a.ParallelAnimEvaluation 0','a.ParallelAnimUpdate 0'):
        unreal.SystemLibrary.execute_console_command(world,command)
    # Preload source animation/import metadata before the native batch compiler.
    loaded=[]
    for path in unreal.EditorAssetLibrary.list_assets('/Game/Characters/Mannequins/Anims',recursive=True,include_folder=False):
        obj=unreal.load_asset(path);loaded.append(obj)
        if isinstance(obj,unreal.AnimSequence):obj.get_editor_property('asset_import_data')
    source_bp=unreal.EditorAssetLibrary.find_asset_data('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed')
    results=unreal.IKRetargetBatchOperation.duplicate_and_retarget([source_bp],source,target,retarget,
        prefix='Patrol_',include_referenced_assets=True,overwrite_existing_files=False)
    assert results,'Locomotion retarget returned no assets'
    renames=[]
    for item in results:
        obj=item.get_asset();name=obj.get_name()
        renames.append(unreal.AssetRenameData(obj,BASE+'/Animations',name))
    generated_bp=unreal.load_asset('/Game/Patrol_ABP_Unarmed')
    assert generated_bp,'The batch did not create the patrol animation Blueprint'
    renames.append(unreal.AssetRenameData(generated_bp,BASE+'/Animations','ABP_PatrolLocomotion'))
    assert assets.rename_assets(renames),'Unable to collect retargeted animations'
anim=unreal.load_asset(bp_path)
assert isinstance(anim,unreal.AnimBlueprint),'Retargeted animation Blueprint is missing'
for item in unreal.EditorAssetLibrary.list_assets(BASE+'/Animations',recursive=True,include_folder=False):
    sequence=unreal.load_asset(item)
    if isinstance(sequence,unreal.AnimSequence):
        if sequence.get_name().startswith('Patrol_MF_Unarmed_'):
            # These source clips contain travelling pelvis motion. CharacterMovement
            # handles travel, so remove the horizontal stride trend from the baked pose.
            frames=unreal.AnimationLibrary.get_num_frames(sequence)
            keys=[unreal.AnimationLibrary.get_bone_pose_for_frame(sequence,'pelvis',i,False) for i in range(frames+1)]
            start=keys[0].translation;end=keys[-1].translation
            positions=[unreal.Vector(k.translation.x-(end.x-start.x)*i/frames,
                k.translation.y,k.translation.z-(end.z-start.z)*i/frames) for i,k in enumerate(keys)]
            controller_data=sequence.get_editor_property('controller')
            assert controller_data.set_bone_track_keys('pelvis',positions,[k.rotation for k in keys],[k.scale3d for k in keys],False)
        sequence.set_editor_properties({'force_root_lock':True,'enable_root_motion':False,
            'root_motion_root_lock':unreal.RootMotionRootLock.REF_POSE})
        unreal.EditorAssetLibrary.save_loaded_asset(sequence)
# The template foot-placement rig targets mannequin bones; use the baked patrol pose.
rig_path=BASE+'/CR_LocomotionPassthrough'
pose_rig=unreal.load_asset(rig_path) if unreal.EditorAssetLibrary.does_asset_exist(rig_path) else unreal.ControlRigBlueprintFactory.create_new_control_rig_asset(rig_path)
if not pose_rig.get_member_variables():pose_rig.add_member_variable('ShouldDoIKTrace','bool',True,False,'False')
pose_rig.recompile_vm()
unreal.BlueprintEditorLibrary.compile_blueprint(pose_rig)
unreal.EditorAssetLibrary.save_loaded_asset(pose_rig)
for node in unreal.ObjectIterator(unreal.AnimGraphNode_ControlRig):
    if node.get_path_name().startswith(anim.get_path_name()+':'):
        data=node.get_editor_property('node')
        data.set_editor_properties({'control_rig_class':pose_rig.generated_class(),'alpha':0.,
            'alpha_scale_bias':unreal.InputScaleBias(scale=0.,bias=0.)})
        node.set_editor_property('node',data)
unreal.BlueprintEditorLibrary.compile_blueprint(anim)
unreal.EditorAssetLibrary.save_directory(BASE,only_if_is_dirty=False,recursive=True)
report={'body_mesh':mesh_path,'world_mesh':world_path,'animation_blueprint':bp_path,'retargeter':BASE+'/RTG_Patrol',
        'animation_assets':list(unreal.EditorAssetLibrary.list_assets(BASE+'/Animations',recursive=True,include_folder=False)),
        'ops':controller.get_num_retarget_ops(),'head_geometry_removed':True,'map_rebuilt':False,
        'root_scale':1,'template_foot_ik_disabled':True}
(ROOT/'Saved/Validation/first_person_setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.log('FIRST_PERSON_BODY_RETARGET_COMPLETE')
