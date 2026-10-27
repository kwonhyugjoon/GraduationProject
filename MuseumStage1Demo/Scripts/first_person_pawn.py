"""Persistent first-person patrol body settings, shared by setup and map generation."""
import unreal
BASE='/Game/Stage1/FirstPerson/Patrol'

def configure_first_person_pawn(pawn):
    sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles=sub.k2_gather_subobject_data_for_blueprint(pawn)
    def obj(handle):
        return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(sub.k2_find_subobject_data_from_handle(handle),pawn)
    templates=[(h,obj(h)) for h in handles]
    root_handle=next(h for h,o in templates if isinstance(o,unreal.CapsuleComponent))
    primary=next(o for h,o in templates if isinstance(o,unreal.SkeletalMeshComponent) and o.get_name()=='CharacterMesh0')
    view=next((o for h,o in templates if isinstance(o,unreal.SkeletalMeshComponent) and o.get_name().startswith('FirstPersonBody')),None)
    if view is None:
        handle,reason=sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root_handle,
            new_class=unreal.SkeletalMeshComponent,blueprint_context=pawn))
        view=obj(handle);assert view,'Unable to add first-person body: '+str(reason)
        sub.rename_subobject(handle,unreal.Text('FirstPersonBody'))
    anim=unreal.load_asset(BASE+'/Animations/ABP_PatrolLocomotion')
    for component,mesh in [(primary,unreal.load_asset(BASE+'/SK_PatrolWorld')),(view,unreal.load_asset(BASE+'/SK_PatrolBody'))]:
        assert mesh and anim,'First-person body assets are not prepared'
        component.set_skeletal_mesh_asset(mesh)
        component.set_editor_properties({'anim_class':anim.generated_class(),
            'visible':True,'hidden_in_game':False,'render_in_main_pass':True,
            'animation_mode':unreal.AnimationMode.ANIMATION_BLUEPRINT,
            'relative_location':unreal.Vector(-18,0,-90),
            'relative_rotation':unreal.Rotator(pitch=0,yaw=270,roll=0),
            'visibility_based_anim_tick_option':unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES})
        component.set_collision_profile_name('NoCollision')
    primary.set_editor_properties({'owner_no_see':True,'only_owner_see':False,'cast_shadow':True,'cast_hidden_shadow':True})
    view.set_editor_properties({'owner_no_see':False,'only_owner_see':True,'cast_shadow':False})
    for h,o in templates:
        if isinstance(o,unreal.SpringArmComponent):
            # A reversed short boom keeps the eye 28 cm forward and sweeps that path.
            o.set_editor_properties({'target_arm_length':28.,'relative_location':unreal.Vector(0,0,65),
                'relative_rotation':unreal.Rotator(pitch=0,yaw=180,roll=0),
                'use_pawn_control_rotation':False,'inherit_pitch':False,'inherit_yaw':True,'inherit_roll':False,
                'do_collision_test':True,'probe_size':5.,'enable_camera_lag':False,'enable_camera_rotation_lag':False})
        if isinstance(o,unreal.CameraComponent):
            o.set_field_of_view(85.)
            o.set_editor_property('use_pawn_control_rotation',True)
    cdo=unreal.get_default_object(pawn.generated_class())
    cdo.set_editor_properties({'use_controller_rotation_yaw':True,'use_controller_rotation_pitch':False,'use_controller_rotation_roll':False})
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn),'Unable to save first-person character'
