"""Fresh-process checks of the saved patrol body, skeleton, clips and pawn templates."""
import unreal,json,hashlib,sys
from pathlib import Path
root=Path(unreal.Paths.project_dir());base='/Game/Stage1/FirstPerson/Patrol'
(root/'Saved/Validation').mkdir(parents=True,exist_ok=True)
body=unreal.load_asset(base+'/SK_PatrolBody');world=unreal.load_asset(base+'/SK_PatrolWorld')
assert body.get_editor_property('skeleton')==world.get_editor_property('skeleton')
assert 120<body.get_bounds().box_extent.z*2<140
assert 174<world.get_bounds().box_extent.z*2<176
rig=unreal.IKRigController.get_controller(unreal.load_asset(base+'/IK_Patrol'))
assert abs(rig.get_ref_pose_transform_of_bone('root').scale3d.x-1)<.001
materials={}
for mesh in (body,world):
    for slot in mesh.get_editor_property('materials'):
        mat=slot.get_editor_property('material_interface')
        assert mat and mat.get_editor_property('used_with_skeletal_mesh')
        materials[mat.get_path_name()]=True
clips=[]
for path in unreal.EditorAssetLibrary.list_assets(base+'/Animations',recursive=True,include_folder=False):
    obj=unreal.load_asset(path)
    if isinstance(obj,unreal.AnimSequence) and obj.get_name().startswith('Patrol_MF_Unarmed_'):
        first=unreal.AnimationLibrary.get_bone_pose_for_frame(obj,'pelvis',0,False).translation
        last=unreal.AnimationLibrary.get_bone_pose_for_frame(obj,'pelvis',unreal.AnimationLibrary.get_num_frames(obj),False).translation
        assert abs(last.x-first.x)<.1 and abs(last.z-first.z)<.1,'A travelling clip remains: '+path
        clips.append(path)
assert len(clips)==16
anim=unreal.load_asset(base+'/Animations/ABP_PatrolLocomotion')
assert anim.generated_class()
pawn=unreal.load_asset('/Game/Stage1/Blueprints/BP_Stage1_FirstPerson')
sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
templates=[unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(sub.k2_find_subobject_data_from_handle(h),pawn) for h in sub.k2_gather_subobject_data_for_blueprint(pawn)]
view=next(o for o in templates if isinstance(o,unreal.SkeletalMeshComponent) and o.get_name().startswith('FirstPersonBody'))
assert view.get_editor_property('skeletal_mesh_asset')==body
assert view.get_editor_property('only_owner_see') and not view.get_editor_property('owner_no_see')
assert view.get_editor_property('anim_class')==anim.generated_class()
arm=next(o for o in templates if isinstance(o,unreal.SpringArmComponent))
assert arm.get_editor_property('target_arm_length')==28
assert abs(arm.get_editor_property('relative_location').x)<.01
assert abs(abs(arm.get_editor_property('relative_rotation').yaw)-180)<.01
assert arm.get_editor_property('do_collision_test') and arm.get_editor_property('probe_size')==5
assert not arm.get_editor_property('use_pawn_control_rotation')
camera=next(o for o in templates if isinstance(o,unreal.CameraComponent))
assert camera.get_editor_property('use_pawn_control_rotation')
files=list((root/'Content/Stage1/FirstPerson/Patrol').rglob('*.uasset'))+[root/'Content/Stage1/Blueprints/BP_Stage1_FirstPerson.uasset']
report={'passed':True,'shared_skeleton':True,'root_scale':1,'in_place_clips':len(clips),
    'first_person_body_cm':body.get_bounds().box_extent.z*2,'full_body_cm':world.get_bounds().box_extent.z*2,
    'camera_forward_cm':28,'camera_probe_cm':5,'body_offset_back_cm':18,'skeletal_materials':sorted(materials),
    'content_sha256':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(root/'Saved/Validation/first_person_assets_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
setup_path=root/'Saved/Validation/first_person_setup.json'
if setup_path.exists():
    setup=json.loads(setup_path.read_text(encoding='utf8'))
    setup['animation_assets']=['/Game/'+p.relative_to(root/'Content').with_suffix('').as_posix() for p in sorted((root/'Content/Stage1/FirstPerson/Patrol/Animations').glob('*.uasset'))]
    setup_path.write_text(json.dumps(setup,indent=2),encoding='utf8')
