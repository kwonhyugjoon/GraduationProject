"""Shared equipment defaults and night-light levels for the patrol prototype."""
import unreal
LIGHT_SCALE=.28
SKY_INTENSITY=.04
MOON_INTENSITY=.03
EQUIPMENT='/Game/Stage1/Equipment'

def configure_equipment(pawn):
    subsystem=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles=subsystem.k2_gather_subobject_data_for_blueprint(pawn)
    def obj(handle):
        return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(subsystem.k2_find_subobject_data_from_handle(handle),pawn)
    component=next((obj(h) for h in handles if isinstance(obj(h),unreal.PatrolEquipmentComponent)),None)
    if component is None:
        handle,reason=subsystem.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0],new_class=unreal.PatrolEquipmentComponent,blueprint_context=pawn))
        component=obj(handle);assert component,reason
        subsystem.rename_subobject(handle,unreal.Text('PatrolEquipment'))
    component.set_editor_properties({'flashlight_view_mesh':unreal.load_asset(EQUIPMENT+'/SM_PatrolFlashlightView'),
        'notebook_view_mesh':unreal.load_asset(EQUIPMENT+'/SM_PatrolNotebookView'),'walk_speed':300.,'sprint_speed':520.})
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert unreal.EditorAssetLibrary.save_loaded_asset(pawn)

def apply_night_lighting():
    from stage1_layout import make_layout
    lights=make_layout()['lights']
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        name=actor.get_actor_label()
        if name.startswith('Museum_Warm_Light_'):
            actor.get_component_by_class(unreal.PointLightComponent).set_intensity(lights[int(name.rsplit('_',1)[1])]['power']*LIGHT_SCALE)
        elif name=='Museum_Soft_Key_Light':actor.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(MOON_INTENSITY)
        elif name=='Museum_Ambient_Light':actor.get_component_by_class(unreal.SkyLightComponent).set_intensity(SKY_INTENSITY)
