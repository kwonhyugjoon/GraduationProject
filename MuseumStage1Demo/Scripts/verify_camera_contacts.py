"""Press the actual PIE pawn against fixtures and test its near-plane rays."""
import unreal,time,json,math,traceback,hashlib,sys,re
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir());sys.path.insert(0,str(ROOT/'Scripts'))
(ROOT/'Saved/Validation').mkdir(parents=True,exist_ok=True)
from camera_contact_cases import CASES
before='-CameraContactBefore' in unreal.SystemLibrary.get_command_line()
suffix='before' if before else 'after';OUT=ROOT/'Saved/Review';OUT.mkdir(exist_ok=True)
config=(ROOT/'Config/DefaultEngine.ini').read_text(encoding='utf8')
match=re.search(r'(?m)^NearClipPlane\s*=\s*([\d.]+)',config);NEAR=float(match.group(1)) if match else 10.
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level('/Game/Stage1/Maps/L_MuseumStage1')
state={'start':time.monotonic(),'phase':'start','case':0,'angle':0,'results':[],'screenshots':[]}
angles=[(0,0),(-35,-35),(35,35),(0,-60),(0,60)]
shots={'north_staff_button','south_staff_button','upper_left_window','stage2_button'}
def finish(error=None):
    total=sum(s['near_plane_hits']+s['camera_overlap'] for c in state['results'] for s in c['samples'])
    report={'passed':error is None and (total>0 if before else total==0),'mode':suffix,'error':error,
        'near_clip_cm':NEAR,'fixture_count':len(state['results']),'pose_count':sum(len(c['samples']) for c in state['results']),
        'obstructed_samples':total,'cases':state['results'],'screenshots':state['screenshots'],
        'method':'Actual PIE pawn driven into 20 fixtures; five yaw/pitch poses each. Nine rays test the perspective near plane; a 2mm sphere checks the camera point. Actor setup uses teleport, approach uses CharacterMovement.',
        'map_source_sha256':hashlib.sha256((ROOT/'Content/Stage1/Maps/L_MuseumStage1.umap').read_bytes()).hexdigest(),
        'pawn_source_sha256':hashlib.sha256((ROOT/'Content/Stage1/Blueprints/BP_Stage1_FirstPerson.uasset').read_bytes()).hexdigest()}
    (ROOT/f'Saved/Validation/camera_contacts_{suffix}.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    state.update(phase='shutdown',changed=time.monotonic());level.editor_request_end_play()
def trace(world,a,b,pawn):
    return unreal.SystemLibrary.line_trace_single(world,a,b,unreal.TraceTypeQuery.TRACE_TYPE_QUERY2,False,[pawn],unreal.DrawDebugTrace.NONE,True)
def tick(delta):
    try:
        now=time.monotonic()
        if state['phase']=='shutdown':
            if now-state['changed']>3:
                unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if now-state['start']>155:finish('Camera contact verification timeout');return
        if state['phase']=='start':
            if now-state['start']<3:return
            level.editor_request_begin_play();state.update(phase='wait',changed=now);return
        world=unreal.EditorLevelLibrary.get_game_world()
        if not world:return
        pawn=unreal.GameplayStatics.get_player_character(world,0)
        if not pawn:return
        pc=unreal.GameplayStatics.get_player_controller(world,0)
        move=pawn.get_component_by_class(unreal.CharacterMovementComponent)
        capsule=pawn.get_component_by_class(unreal.CapsuleComponent)
        radius=capsule.get_scaled_capsule_radius();half=capsule.get_scaled_capsule_half_height()
        if state['phase']=='wait':
            if now-state['changed']<5:return
            if not before:
                for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
                    if not actor.get_actor_label().endswith('_Detail'):continue
                    component=actor.get_component_by_class(unreal.InstancedStaticMeshComponent)
                    if not component:continue
                    assert component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA)==unreal.CollisionResponseType.ECR_BLOCK
                    assert component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)==unreal.CollisionResponseType.ECR_IGNORE
            state['phase']='setup'
        name,point,normal,floor=CASES[state['case']]
        n=unreal.Vector(-normal[0],normal[1],0);direction=n*-1
        yaw=math.degrees(math.atan2(direction.y,direction.x))
        if state['phase']=='setup':
            move.stop_movement_immediately()
            pawn.set_actor_location(unreal.Vector(-point[0]+n.x*(radius+90),point[1]+n.y*(radius+90),floor+half+2.15),False,True)
            pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0))
            state['results'].append({'name':name,'samples':[]})
            state.update(phase='approach',changed=now,angle=0,sampled=False);return
        if state['phase']=='approach':
            pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0));pawn.add_movement_input(direction,1,True)
            if now-state['changed']>1.1:state.update(phase='angles',changed=now)
            return
        if state['phase']=='angles':
            dy,pitch=angles[state['angle']]
            pc.set_control_rotation(unreal.Rotator(pitch=pitch,yaw=yaw+dy,roll=0));pawn.add_movement_input(direction,1,True)
            if now-state['changed']<.2:return
            if not state['sampled']:
                camera=unreal.GameplayStatics.get_player_camera_manager(world,0)
                pos=camera.get_camera_location();rot=camera.get_camera_rotation()
                p,y=map(math.radians,(rot.pitch,rot.yaw));forward=unreal.Vector(math.cos(p)*math.cos(y),math.cos(p)*math.sin(y),math.sin(p))
                right=unreal.Vector(-math.sin(y),math.cos(y),0);up=unreal.Vector(-math.sin(p)*math.cos(y),-math.sin(p)*math.sin(y),math.cos(p))
                width=NEAR*math.tan(math.radians(85/2));height=width/(16/9)
                hits=sum(trace(world,pos,pos+forward*NEAR+right*(x*width)+up*(z*height),pawn) is not None for x in (-1,0,1) for z in (-1,0,1))
                overlap=unreal.SystemLibrary.sphere_trace_single(world,pos,pos+forward*.01,.2,unreal.TraceTypeQuery.TRACE_TYPE_QUERY2,False,[pawn],unreal.DrawDebugTrace.NONE,True) is not None
                actor=pawn.get_actor_location()
                state['results'][-1]['samples'].append({'yaw':rot.yaw,'pitch':rot.pitch,'near_plane_hits':hits,'camera_overlap':int(overlap),
                    'camera':[pos.x,pos.y,pos.z],'pawn':[actor.x,actor.y,actor.z],'camera_offset_cm':math.hypot(pos.x-actor.x,pos.y-actor.y)})
                state.update(sampled=True,sampled_at=now,shot=False)
                if name in shots and state['angle']==0:
                    path=OUT/f'camera_{name}_{suffix}.png'
                    unreal.SystemLibrary.execute_console_command(world,f'HighResShot 1600x900 filename="{path}"',pc)
                    state['screenshots'].append(path.name);state['shot']=True
            if now-state['sampled_at']<(.8 if state['shot'] else .08):return
            state['angle']+=1;state.update(sampled=False,changed=now)
            if state['angle']==len(angles):
                state['case']+=1
                if state['case']==len(CASES):finish();return
                state['phase']='setup'
    except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
