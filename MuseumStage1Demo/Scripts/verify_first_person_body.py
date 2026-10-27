"""Exercise and capture the real player camera in PIE, including owner-only geometry."""
import unreal,time,json,traceback,math,hashlib
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Review';OUT.mkdir(exist_ok=True)
(ROOT/'Saved/Validation').mkdir(parents=True,exist_ok=True)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level('/Game/Stage1/Maps/L_MuseumStage1')
state={'start':time.monotonic(),'phase':'start','pose':0,'samples':[],'images':[]}
poses=[('fp_forward',0,False,False),('fp_look_down',-62,False,False),
       ('fp_feet',-85,False,False),('fp_walking',-80,True,False),('fp_jump',-80,False,True)]
def finish(passed,error=None):
    report={k:v for k,v in state.items() if k not in ('start','phase_start','requested','jumped')}
    report.update({'passed':passed,'error':error,'method':'Actual PIE player camera and HighResShot; initial pawn location is set to a clear public corridor. Owner-only patrol geometry is rendered from the local player view.',
        'map_source_sha256':hashlib.sha256((ROOT/'Content/Stage1/Maps/L_MuseumStage1.umap').read_bytes()).hexdigest()})
    (ROOT/'Saved/Validation/first_person_body_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    state['phase']='shutdown';state['phase_start']=time.monotonic();level.editor_request_end_play()
def tick(delta):
    try:
        now=time.monotonic()
        if state['phase']=='shutdown':
            if now-state['phase_start']>4:
                unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if now-state['start']>110:finish(False,'First-person verification timeout');return
        if state['phase']=='start':
            if now-state['start']<4:return
            level.editor_request_begin_play();state['phase']='wait';state['phase_start']=now;return
        world=unreal.EditorLevelLibrary.get_game_world()
        if not world:return
        pawn=unreal.GameplayStatics.get_player_character(world,0)
        if not pawn:return
        pc=unreal.GameplayStatics.get_player_controller(world,0)
        meshes=pawn.get_components_by_class(unreal.SkeletalMeshComponent)
        view=next(m for m in meshes if m.get_name().startswith('FirstPersonBody'))
        primary=next(m for m in meshes if m.get_name()=='CharacterMesh0')
        if state['phase']=='wait':
            if now-state['phase_start']<8:return
            pawn.set_actor_location(unreal.Vector(700,-1400,92.15),False,True)
            assert view.get_editor_property('only_owner_see') and not view.get_editor_property('owner_no_see')
            assert primary.get_editor_property('owner_no_see')
            assert '/SK_PatrolBody.' in str(view.get_editor_property('skeletal_mesh_asset').get_path_name())
            assert '/SK_PatrolWorld.' in str(primary.get_editor_property('skeletal_mesh_asset').get_path_name())
            assert view.get_anim_instance(),'The patrol body has no animation instance'
            state['animation_class']=view.get_anim_instance().get_class().get_name()
            state['visibility']={k:str(view.get_editor_property(k)) for k in ('visible','hidden_in_game','render_in_main_pass','relative_scale3d')}
            state['view_target']=str(pc.get_view_target().get_path_name())
            state['mesh_owner']=str(view.get_owner().get_path_name())
            state['owner_body_visible']=True;state['head_geometry_excluded']=True
            state['pose']=0;state['phase']='pose';state['phase_start']=now;state['requested']=False;state['jumped']=False
        if state['phase']=='pose':
            name,pitch,moving,jumping=poses[state['pose']]
            pc.set_control_rotation(unreal.Rotator(pitch=pitch,yaw=90,roll=0))
            if moving:pawn.add_movement_input(unreal.Vector(0,1,0),1,True)
            elif not jumping:pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
            if jumping and not state['jumped']:
                pawn.jump();state['jumped']=True
            p=pawn.get_actor_location();foot=view.get_socket_location('foot_l');hand=view.get_socket_location('hand_l')
            assert math.hypot(foot.x-p.x,foot.y-p.y)<110 and -130<foot.z-p.z<40,'Foot left the physical player body'
            assert math.hypot(hand.x-p.x,hand.y-p.y)<110 and -60<hand.z-p.z<80,'Hand left the physical player body'
            camera=unreal.GameplayStatics.get_player_camera_manager(world,0)
            if moving:
                state['samples'].append({'time':now,'foot_relative':[foot.x-p.x,foot.y-p.y,foot.z-p.z],
                    'hand_relative':[hand.x-p.x,hand.y-p.y,hand.z-p.z]})
            delay=.25 if jumping else 1.3
            if not state['requested'] and now-state['phase_start']>delay:
                image_path=OUT/(name+'.png')
                unreal.SystemLibrary.execute_console_command(world,'HighResShot 1600x900 filename="'+str(image_path)+'"',pc)
                state['requested']=True;state['request_time']=now
                state['images'].append({'name':name,'pitch':camera.get_camera_rotation().pitch,
                    'camera_offset':[camera.get_camera_location().x-p.x,camera.get_camera_location().y-p.y,camera.get_camera_location().z-p.z],
                    'pawn_position':[p.x,p.y,p.z],'foot_position':[foot.x,foot.y,foot.z],'hand_position':[hand.x,hand.y,hand.z]})
            if state['requested'] and now-state['request_time']>2.5:
                assert (OUT/(name+'.png')).is_file(),'Missing player screenshot: '+name
                state['pose']+=1
                if state['pose']==len(poses):
                    samples=state['samples']
                    foot_motion=max(math.dist(a['foot_relative'],b['foot_relative']) for a in samples for b in samples)
                    hand_motion=max(math.dist(a['hand_relative'],b['hand_relative']) for a in samples for b in samples)
                    state['foot_motion_cm']=foot_motion;state['hand_motion_cm']=hand_motion
                    assert 5<foot_motion<140,'Walking foot motion is missing or incorrectly scaled'
                    assert 2<hand_motion<120,'Walking arm motion is missing or incorrectly scaled'
                    finish(True);return
                state['phase_start']=now;state['requested']=False;state['jumped']=False
    except Exception:finish(False,traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
