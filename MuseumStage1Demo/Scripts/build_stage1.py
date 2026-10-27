"""Build the reviewable stage in Unreal using only project-local assets."""
import unreal,sys,json,math,traceback
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir())
sys.path.insert(0,str(ROOT/'Scripts'))
from stage1_layout import make_layout
from camera_collision import configure_architecture_collision
ASSET_ROOT='/Game/Stage1'
MAP=ASSET_ROOT+'/Maps/L_MuseumStage1'
def rotation(values):
    return unreal.Rotator(pitch=values[0],yaw=values[1],roll=values[2])
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assets=unreal.AssetToolsHelpers.get_asset_tools()
subobjects=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(['/Game'],force_rescan=True)
unreal.EditorAssetLibrary.make_directory(ASSET_ROOT+'/Maps')
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    assert levels.load_level(MAP),'Unable to load generated stage map'
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path()).startswith('Stage1/'):
            actors.destroy_actor(actor)
else:
    assert levels.new_level(MAP),'Unable to create stage map'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
layout=make_layout()
instanced_material_names={key[1] for key in layout['groups']}
report={'layout':{k:v for k,v in layout.items() if k!='groups'},'batches':[],'blueprints':[]}

PALETTE={
 'stone':((.53,.44,.31),.7,0), 'stone_light':((.68,.61,.47),.6,0),
 'stone_dark':((.105,.12,.13),.65,0),'brass':((.47,.29,.09),.28,.72),
 'bronze':((.12,.10,.065),.4,.65),'wood_dark':((.075,.037,.018),.5,0),
 'wood':((.24,.105,.04),.52,0),'wood_alt':((.31,.15,.06),.52,0),
 'marble_a':((.57,.55,.47),.28,.05),'marble_b':((.44,.43,.38),.32,.05),
 'linen':((.43,.34,.22),.9,0),'fossil':((.72,.60,.40),.68,.02),
 'pottery':((.40,.17,.055),.45,0),'soil':((.025,.018,.011),1,0),
 'leaf':((.035,.15,.055),.68,0),'door':((.07,.10,.105),.36,.35),
 'cavity':((.012,.01,.009),.9,0),'ceiling':((.34,.31,.25),.8,0),
 'window':((.025,.075,.12),.12,.35),'glass':((.31,.48,.55),.1,.05),
 'lamp':((1,.43,.075),.25,0),'red':((.55,.035,.015),.3,0)}
patrol_sources=json.loads((ROOT.parent/'Assets/Player/night_patrol_v15/materials.json').read_text(encoding='utf-8'))
for source in patrol_sources:
    pbr=source['pbrMetallicRoughness']
    PALETTE['Patrol_'+source['name']]=(tuple(pbr['baseColorFactor'][:3]),pbr['roughnessFactor'],pbr['metallicFactor'])
materials={}
for name,(color,roughness,metallic) in PALETTE.items():
    path=ASSET_ROOT+'/Materials/M_'+name
    mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else assets.create_asset('M_'+name,ASSET_ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    if name in instanced_material_names:mat.set_editor_property('used_with_instanced_static_meshes',True)
    if name.startswith('Patrol_') and unreal.EditorAssetLibrary.does_asset_exist(ASSET_ROOT+'/FirstPerson/Patrol/SK_PatrolBody'):
        mat.set_editor_property('used_with_skeletal_mesh',True)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    base=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,0)
    base.set_editor_property('constant',unreal.LinearColor(*color,1))
    unreal.MaterialEditingLibrary.connect_material_property(base,'',unreal.MaterialProperty.MP_BASE_COLOR)
    for value,prop,yy in [(roughness,unreal.MaterialProperty.MP_ROUGHNESS,100),(metallic,unreal.MaterialProperty.MP_METALLIC,180)]:
        node=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,yy)
        node.set_editor_property('r',value);unreal.MaterialEditingLibrary.connect_material_property(node,'',prop)
    if name in ('lamp','red','window'):
        emission=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,260)
        strength=2.2 if name=='lamp' else .8 if name=='red' else .08
        emission.set_editor_property('constant',unreal.LinearColor(*(v*strength for v in color),1))
        unreal.MaterialEditingLibrary.connect_material_property(emission,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if name=='glass':
        mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property('two_sided',True)
        opacity=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,260)
        opacity.set_editor_property('r',.14)
        unreal.MaterialEditingLibrary.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    materials[name]=mat

# World-aligned PBR stone: metre tiles, narrow joints, veins and perimeter inlay.
floor_path=ASSET_ROOT+'/Materials/M_GalleryFloor'
floor_mat=unreal.load_asset(floor_path) if unreal.EditorAssetLibrary.does_asset_exist(floor_path) else assets.create_asset('M_GalleryFloor',ASSET_ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
unreal.MaterialEditingLibrary.delete_all_material_expressions(floor_mat)
floor_mat.set_editor_property('used_with_instanced_static_meshes',True)
position=unreal.MaterialEditingLibrary.create_material_expression(floor_mat,unreal.MaterialExpressionWorldPosition,-650,0)
pattern=unreal.MaterialEditingLibrary.create_material_expression(floor_mat,unreal.MaterialExpressionCustom,-400,0)
pin=unreal.CustomInput();pin.set_editor_property('input_name','WorldPos')
pattern.set_editor_property('inputs',[pin])
pattern.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT4)
pattern.set_editor_property('code',(ROOT/'Scripts/gallery_floor.hlsl').read_text(encoding='utf-8'))
assert unreal.MaterialEditingLibrary.connect_material_expressions(position,'',pattern,'WorldPos'),'Floor world-position connection failed'
for prop,channels,y in [(unreal.MaterialProperty.MP_BASE_COLOR,(True,True,True,False),0),
                        (unreal.MaterialProperty.MP_ROUGHNESS,(False,False,False,True),180)]:
    mask=unreal.MaterialEditingLibrary.create_material_expression(floor_mat,unreal.MaterialExpressionComponentMask,-100,y)
    mask.set_editor_properties(dict(zip(('r','g','b','a'),channels)))
    assert unreal.MaterialEditingLibrary.connect_material_expressions(pattern,'',mask,''),'Floor channel-mask connection failed'
    assert unreal.MaterialEditingLibrary.connect_material_property(mask,'',prop),'Floor material output connection failed'
unreal.MaterialEditingLibrary.recompile_material(floor_mat)
unreal.EditorAssetLibrary.save_loaded_asset(floor_mat)
materials['gallery_floor']=floor_mat
from room_floor import ensure_room_floor
materials['room_floor']=ensure_room_floor()

# Preserve the engine font atlas while keeping signs readable under night exposure.
text_path=ASSET_ROOT+'/Materials/M_MuseumSignage'
if unreal.EditorAssetLibrary.does_asset_exist(text_path):
    text_material=unreal.load_asset(text_path)
else:
    text_material=assets.duplicate_asset('M_MuseumSignage',ASSET_ROOT+'/Materials',unreal.load_asset('/Engine/EngineMaterials/DefaultTextMaterialOpaque'))
    font_output=unreal.MaterialEditingLibrary.get_material_property_input_node(text_material,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if font_output is None:
        font_output=unreal.MaterialEditingLibrary.get_material_property_input_node(text_material,unreal.MaterialProperty.MP_BASE_COLOR)
    assert font_output,'The engine text material has no font color output'
    text_material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    gain=unreal.MaterialEditingLibrary.create_material_expression(text_material,unreal.MaterialExpressionMultiply,0,250)
    gain.set_editor_property('const_b',12.)
    unreal.MaterialEditingLibrary.connect_material_expressions(font_output,'',gain,'A')
    unreal.MaterialEditingLibrary.connect_material_property(gain,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(text_material)
    unreal.EditorAssetLibrary.save_loaded_asset(text_material)

def component_template(bp,handle):
    data=subobjects.k2_find_subobject_data_from_handle(handle)
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data,bp)

def blueprint(name):
    path=ASSET_ROOT+'/Geometry/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):return unreal.load_asset(path)
    factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',unreal.Actor)
    bp=assets.create_asset(name,ASSET_ROOT+'/Geometry',unreal.Blueprint,factory)
    assert bp,'Blueprint factory failed: '+name
    return bp

for (mesh_name,material_name,solid),instances in layout['groups'].items():
    name=f'BP_Geo_{mesh_name}_{material_name}_'+('Solid' if solid else 'Detail')
    bp=blueprint(name)
    handles=subobjects.k2_gather_subobject_data_for_blueprint(bp)
    comp=None;handle=None
    for h in handles:
        obj=component_template(bp,h)
        if isinstance(obj,unreal.SceneComponent):obj.set_mobility(unreal.ComponentMobility.STATIC)
        if isinstance(obj,unreal.InstancedStaticMeshComponent):comp=obj;handle=h
    if comp is None:
        params=unreal.AddNewSubobjectParams(parent_handle=handles[0],new_class=unreal.InstancedStaticMeshComponent,blueprint_context=bp)
        handle,reason=subobjects.add_new_subobject(params)
        comp=component_template(bp,handle)
        if comp and material_name=='room_floor':
            assert subobjects.make_new_scene_root(handles[0],handle,bp),'Unable to root the room-floor batch'
    reason='' if comp else 'No component created'
    assert comp,'Unable to add geometry batch: '+str(reason)
    subobjects.rename_subobject(handle,unreal.Text('MuseumGeometry'))
    mesh=unreal.load_asset('/Engine/BasicShapes/'+mesh_name)
    assert mesh,'Missing engine shape: '+mesh_name
    comp.set_static_mesh(mesh);comp.set_material(0,materials[material_name])
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    configure_architecture_collision(comp,solid)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    actor=actors.spawn_actor_from_class(bp.generated_class(),unreal.Vector(0,0,0))
    actor.set_actor_label(name.replace('BP_Geo_',''))
    actor.set_folder_path('Stage1/Architecture')
    actor.set_editor_property('tags',[unreal.Name('Stage1Generated')])
    component=actor.get_component_by_class(unreal.InstancedStaticMeshComponent)
    transforms=[unreal.Transform(location=unreal.Vector(*item['p']),rotation=rotation(item['r']),scale=unreal.Vector(*item['s'])) for item in instances]
    component.modify();component.add_instances(transforms,False,False,False)
    report['batches'].append({'asset':str(bp.get_path_name()),'instances':len(instances),'solid':solid})
    unreal.log('STAGE1_BATCH '+name+' '+str(len(instances)))

# Import the approved A-pose as one stationary display, retaining all eight slots.
dummy_path=ASSET_ROOT+'/Characters/SM_PatrolV15_Dummy'
if not unreal.EditorAssetLibrary.does_asset_exist(dummy_path):
    options=unreal.FbxImportUI()
    options.set_editor_properties({'automated_import_should_detect_type':False,
        'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,
        'import_mesh':True,'import_animations':False,'import_materials':False,'import_textures':False})
    data=options.get_editor_property('static_mesh_import_data')
    data.set_editor_properties({'combine_meshes':True,'transform_vertex_to_absolute':True,
        'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':True,
        'auto_generate_collision':False,'generate_lightmap_u_vs':False,
        'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS})
    task=unreal.AssetImportTask()
    task.set_editor_properties({'filename':str(ROOT.parent/'Assets/Player/night_patrol_v15/night_patrol_v15_uv.fbx'),
        'destination_path':ASSET_ROOT+'/Characters','destination_name':'SM_PatrolV15_Dummy',
        'automated':True,'save':True,'replace_existing':False,'factory':unreal.FbxFactory(),'options':options})
    assets.import_asset_tasks([task])
    assert unreal.EditorAssetLibrary.does_asset_exist(dummy_path),'Patrol dummy import failed: '+str(task.imported_object_paths)
dummy_mesh=unreal.load_asset(dummy_path)
assert isinstance(dummy_mesh,unreal.StaticMesh),'Patrol display must be a static mesh'
dummy_slots=[]
for i,slot in enumerate(dummy_mesh.get_editor_property('static_materials')):
    name=str(slot.get_editor_property('material_slot_name'))
    if name.endswith('_001'):name=name[:-4]
    assert 'Patrol_'+name in materials,'Unexpected patrol material slot: '+name
    dummy_mesh.set_material(i,materials['Patrol_'+name]);dummy_slots.append(name)
assert len(dummy_slots)==8,'The patrol display lost a source material slot'
bounds=dummy_mesh.get_bounds();height=bounds.box_extent.z*2
assert 174<height<176,'Unexpected patrol dummy import scale: '+str(height)
dummy=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(-340,-650,18-(bounds.origin.z-bounds.box_extent.z)),rotation((0,-90,0)))
dummy.set_actor_label('Patrol_v15_Display_Dummy');dummy.set_folder_path('Stage1/CharacterPreview')
dummy_component=dummy.get_component_by_class(unreal.StaticMeshComponent)
dummy_component.set_static_mesh(dummy_mesh);dummy_component.set_collision_profile_name('NoCollision')
unreal.EditorAssetLibrary.save_loaded_asset(dummy_mesh)
report['patrol_dummy']={'asset':dummy_path,'count':1,'height_cm':height,'materials':dummy_slots,
    'source':'../Assets/Player/night_patrol_v15/night_patrol_v15_uv.fbx','animated':False,
    'location_world':[dummy.get_actor_location().x,dummy.get_actor_location().y,dummy.get_actor_location().z]}

for i,entry in enumerate(layout['lights']):
    actor=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(*entry['p']))
    actor.set_actor_label('Museum_Warm_Light_%02d'%i);actor.set_folder_path('Stage1/Lighting')
    light=actor.get_component_by_class(unreal.PointLightComponent)
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_intensity(entry['power']);light.set_attenuation_radius(entry['radius'])
    light.set_light_color(unreal.LinearColor(*(v/255 for v in entry['color']),1))
    light.set_cast_shadows(False)
    light.set_editor_property('source_radius',18)

sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,1200),rotation((-45,-25,0)))
sun.set_actor_label('Museum_Soft_Key_Light');sun.set_folder_path('Stage1/Lighting')
sunlight=sun.get_component_by_class(unreal.DirectionalLightComponent)
sunlight.set_mobility(unreal.ComponentMobility.MOVABLE);sunlight.set_intensity(.20)
sunlight.set_light_color(unreal.LinearColor(.48,.60,.85,1));sunlight.set_cast_shadows(True)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,1000))
sky.set_actor_label('Museum_Ambient_Light');sky.set_folder_path('Stage1/Lighting')
skycomp=sky.get_component_by_class(unreal.SkyLightComponent);skycomp.set_mobility(unreal.ComponentMobility.MOVABLE)
cube=unreal.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap')
if cube:
    skycomp.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    skycomp.set_editor_property('cubemap',cube)
skycomp.set_intensity(.22)
fog=actors.spawn_actor_from_class(unreal.ExponentialHeightFog,unreal.Vector(0,0,-300))
fog.set_folder_path('Stage1/Lighting')
fogcomp=fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
fogcomp.set_editor_property('fog_density',.002)
fogcomp.set_editor_property('fog_inscattering_luminance',unreal.LinearColor(.035,.045,.065,1))
post=actors.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector(0,0,200))
post.set_actor_label('Museum_Exposure');post.set_folder_path('Stage1/Lighting')
post.set_editor_property('unbound',True)
settings=post.get_editor_property('settings')
settings.set_editor_property('override_auto_exposure_method',True)
settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
settings.set_editor_property('override_auto_exposure_bias',True)
settings.set_editor_property('auto_exposure_bias',-4.)
settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
settings.set_editor_property('override_bloom_intensity',True)
settings.set_editor_property('bloom_intensity',.20)
post.set_editor_property('settings',settings)

for entry in layout['signs']:
    actor=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(*entry['p']),rotation((0,entry['yaw'],0)))
    actor.set_actor_label('Sign_'+entry['text'].replace(' ','_'));actor.set_folder_path('Stage1/Signs')
    comp=actor.get_component_by_class(unreal.TextRenderComponent)
    comp.set_text(unreal.Text(entry['text']));comp.set_world_size(entry['size'])
    comp.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    comp.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    comp.set_text_render_color(unreal.Color(233,207,147,255))
    comp.set_text_material(text_material)

start=actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(*layout['player_start']),rotation((0,90,0)))
start.set_actor_label('Museum_Visitor_Entrance');start.set_folder_path('Stage1/Player')

# Project-local copies of Epic's tested movement Blueprint remain editable.
original=unreal.load_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter')
base_mode=unreal.load_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode')
pawn_path=ASSET_ROOT+'/Blueprints/BP_Stage1_FirstPerson'
pawn=unreal.load_asset(pawn_path) if unreal.EditorAssetLibrary.does_asset_exist(pawn_path) else assets.duplicate_asset('BP_Stage1_FirstPerson',ASSET_ROOT+'/Blueprints',original)
cdo=unreal.get_default_object(pawn.generated_class())
cdo.get_component_by_class(unreal.CharacterMovementComponent).set_editor_properties({'max_walk_speed':300.,'jump_z_velocity':420.,'gravity_scale':1.2,'max_step_height':35.,'orient_rotation_to_movement':False})
cdo.set_editor_property('use_controller_rotation_yaw',True)
for h in subobjects.k2_gather_subobject_data_for_blueprint(pawn):
    comp=component_template(pawn,h)
    if isinstance(comp,unreal.SpringArmComponent):
        comp.set_editor_property('target_arm_length',0.)
        comp.set_editor_property('relative_location',unreal.Vector(0,0,65))
    if isinstance(comp,unreal.SkeletalMeshComponent):comp.set_owner_no_see(True)
    if isinstance(comp,unreal.CameraComponent):comp.set_field_of_view(85.)
unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
unreal.EditorAssetLibrary.save_loaded_asset(pawn)
if unreal.EditorAssetLibrary.does_asset_exist(ASSET_ROOT+'/FirstPerson/Patrol/SK_PatrolWorld'):
    from first_person_pawn import configure_first_person_pawn
    configure_first_person_pawn(pawn)
mode_path=ASSET_ROOT+'/Blueprints/BP_Stage1Mode_FirstPerson'
mode=unreal.load_asset(mode_path) if unreal.EditorAssetLibrary.does_asset_exist(mode_path) else assets.duplicate_asset('BP_Stage1Mode_FirstPerson',ASSET_ROOT+'/Blueprints',base_mode)
unreal.get_default_object(mode.generated_class()).set_editor_property('default_pawn_class',pawn.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(mode)
unreal.EditorAssetLibrary.save_loaded_asset(mode)
report['blueprints'].append(str(pawn.get_path_name()))
retired=[ASSET_ROOT+'/Blueprints/BP_Stage1Mode_ThirdPerson',ASSET_ROOT+'/Blueprints/BP_Stage1_ThirdPerson']
for path in retired:
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        referencers=unreal.EditorAssetLibrary.find_package_referencers_for_asset(path,False)
        assert not [r for r in referencers if str(r) not in retired], 'Unexpected reference to retired third-person asset: '+path
        assert unreal.EditorAssetLibrary.delete_asset(path),'Unable to remove retired mode: '+path
report['perspective']='first_person_only'

for label,p,r,ortho in [('Overview',(250,-1250,6500),(-78,90,0),0),
                       ('StaffLayout',(250,-1250,6500),(-78,90,0),0),
                       ('Entrance',(0,-1410,165),(0,90,0),0),
                       ('UpperGallery',(2650,-900,615),(-15,150,0),0),
                       ('UpperPatrol',(2680,-1050,615),(-8,90,0),0),
                       ('GalleryPatrol',(1620,400,165),(-5,90,0),0),
                       ('Stage2Door',(2500,0,645),(0,0,0),0),
                       ('Stage3Door',(-2000,0,645),(0,180,0),0),
                       ('DummyFront',(-340,-1000,155),(-8,90,0),0),
                       ('DummyBack',(-340,-300,155),(-8,-90,0),0),
                       ('NorthStaffDoor',(-650,650,185),(4.5,90,0),0),
                       ('GallerySign',(510,750,165),(9,0,0),0),
                       ('StaffCorridor',(-2285,-950,165),(0,90,0),0),
                       ('Exterior',(0,-5000,1000),(-7,90,0),0)]:
    actor=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*p),rotation(r))
    actor.set_actor_label('Preview_'+label);actor.set_folder_path('Stage1/ReviewCameras')
    cam=actor.get_component_by_class(unreal.CameraComponent)
    cam.set_editor_property('aspect_ratio',16/9)
    if ortho:
        cam.set_editor_property('projection_mode',unreal.CameraProjectionMode.ORTHOGRAPHIC)
        cam.set_editor_property('ortho_width',ortho)
    else:cam.set_field_of_view(60. if label in ('Overview','StaffLayout') else 110. if label in ('Stage2Door','Stage3Door') else 80.)

assert levels.save_current_level(),'Map save failed'
unreal.EditorAssetLibrary.save_directory(ASSET_ROOT,only_if_is_dirty=False,recursive=True)
report['map']=MAP
report['geometry_instances']=sum(len(v) for v in layout['groups'].values())
report['temporary_exhibit_instances']=sum(len(v) for (mesh,mat,solid),v in layout['groups'].items() if mat in ('fossil','pottery','glass','cavity'))
assert report['temporary_exhibit_instances']==0,'Temporary exhibits remain in the generated map'
report['partition_height_cm']=280
report['staff_on_second_floor']=False
report['night_lighting']={'skylight':.22,'moonlight':.20,'exposure_bias':-4.,'bloom':.20}
report['generation_completed']=True
(ROOT/'Saved/stage1_build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.log('STAGE1_BUILD_COMPLETE '+str(report['geometry_instances']))
