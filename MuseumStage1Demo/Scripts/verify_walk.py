"""Drive the real CharacterMovement component through the generated level in PIE."""
import unreal,time,json,traceback,math,hashlib
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Validation';OUT.mkdir(parents=True,exist_ok=True)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level.load_level('/Game/Stage1/Maps/L_MuseumStage1')
route=[[350,-1400,100],[700,0,100],[1200,0,100],[1525,1220,100],[1525,-1220,100],
       [1200,0,100],[700,0,100],[700,-1350,100],
       [-740,-1200,100],[-740,-750,100],[-1620,-750,100],[-740,-750,100],
       [-740,750,100],[-1620,750,100],[-740,750,100],[-740,480,100],[0,520,100],
       [0,570,100],[0,1510,550],[-2690,1530,550],[-2690,0,550],
       [-2690,-1530,550],[2280,-1530,550],[2280,0,550],[2280,1530,550],[0,1510,550]]
route=[[-x,y,z] for x,y,z in route]
staff_route=[[-x,y,z] for x,y,z in [[2290,-1612.5,100],[2290,1612.5,100],[650,1612.5,100]]]
tyranno_route=[[-x,y,177] for x,y in [(-600,-900),(-600,-1490),(-2640,-1490),(-2640,1490),
                                      (-600,1490),(-600,450),(-600,0),(-2640,0),(-600,0),(-600,-900)]]
state={'start':time.monotonic(),'phase':'start','point':0,'reached':[],'last_progress':time.monotonic(),
       'max_z':0,'samples':[],'blocked':{},'staff_reached':[],'tyranno_reached':[],'pawn':None}
def finish(passed,error=None):
    result={k:v for k,v in state.items() if k not in ('pawn','start','last_progress')}
    result['map_source_sha256']=hashlib.sha256((ROOT/'Content/Stage1/Maps/L_MuseumStage1.umap').read_bytes()).hexdigest()
    result.update({'passed':passed,'error':error,'method':'Actual PIE character movement through the public route, followed by a resized 300cm-wide, 350cm-tall capsule through the ground-floor left circulation loop. Teleport sets up independent collision tests and the locked-corridor/proxy starting positions; route points are reached using CharacterMovement.',
                   'tyranno_proxy_limitation':'Capsule clearance only; no dinosaur mesh, animation, tail sweep or AI pathfinding is implemented.'})
    (OUT/'walk_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    state['phase']='shutdown';state['pawn']=None;state['quit_after']=time.monotonic()+3
    level.editor_request_end_play()
def tick(delta):
    try:
        now=time.monotonic()
        if state['phase']=='shutdown':
            if now>=state['quit_after']:
                unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if now-state['start']>360:finish(False,'Overall route timeout');return
        if state['phase']=='start':
            if now-state['start']<3:return
            level.editor_request_begin_play();state['phase']='wait';state['last_progress']=now;return
        world=unreal.EditorLevelLibrary.get_game_world()
        if not world:return
        pawn=unreal.GameplayStatics.get_player_character(world,0)
        if not pawn:return
        state['pawn']=pawn;p=pawn.get_actor_location()
        state['max_z']=max(state['max_z'],p.z)
        if state['phase']=='wait':
            if now-state['last_progress']<2:return
            state['pawn_class']=str(pawn.get_class().get_name())
            state['max_walk_speed']=pawn.get_component_by_class(unreal.CharacterMovementComponent).get_editor_property('max_walk_speed')
            state['initial_position']=[p.x,p.y,p.z]
            camera=unreal.GameplayStatics.get_player_camera_manager(world,0).get_camera_location()
            state['camera_height_above_pawn_cm']=camera.z-p.z
            state['first_person_camera_confirmed']=math.hypot(camera.x-p.x,camera.y-p.y)<32 and 40<camera.z-p.z<90
            state['phase']='route';state['last_progress']=now
        if state['phase']=='route':
            if state['point']>=len(route):
                pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
                pawn.set_actor_location(unreal.Vector(-740,-1612.5,105),False,True)
                state['phase']='staff';state['last_progress']=now;return
            target=route[state['point']];dx=target[0]-p.x;dy=target[1]-p.y;distance=math.hypot(dx,dy)
            if distance<65 and abs(p.z-target[2])<95:
                state['reached'].append({'index':state['point'],'position':[p.x,p.y,p.z]})
                state['point']+=1;state['last_progress']=now;return
            if now-state['last_progress']>22:
                finish(False,'Stuck at route point '+str(state['point'])+' '+str([p.x,p.y,p.z]));return
            pawn.add_movement_input(unreal.Vector(dx/max(distance,1),dy/max(distance,1),0),1.,True)
        elif state['phase']=='staff':
            pawn.add_movement_input(unreal.Vector(-1,0,0),1.,True)
            if now-state['last_progress']>2.5:
                state['blocked']['staff_door']={'passed':-900<p.x<-850,'position':[p.x,p.y,p.z]}
                pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
                pawn.set_actor_location(unreal.Vector(-1130,-1612.5,105),False,True)
                state['phase']='staff_route';state['staff_point']=0;state['last_progress']=now
        elif state['phase']=='staff_route':
            target=staff_route[state['staff_point']];dx=target[0]-p.x;dy=target[1]-p.y;distance=math.hypot(dx,dy)
            if distance<30 and abs(p.z-target[2])<95:
                state['staff_reached'].append({'index':state['staff_point'],'position':[p.x,p.y,p.z]})
                state['staff_point']+=1;state['last_progress']=now
            elif now-state['last_progress']>22:
                finish(False,'Stuck in staff corridor at '+str(state['staff_point'])+' '+str([p.x,p.y,p.z]));return
            else:pawn.add_movement_input(unreal.Vector(dx/max(distance,1),dy/max(distance,1),0),1.,True)
            if state['staff_point']>=len(staff_route):
                pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
                state['phase']='staff_exit';state['last_progress']=now
        elif state['phase']=='staff_exit':
            pawn.add_movement_input(unreal.Vector(0,-1,0),1.,True)
            if now-state['last_progress']>2.5:
                state['blocked']['other_staff_door']={'passed':1465<p.y<1480 and -710<p.x<-590,'position':[p.x,p.y,p.z]}
                pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
                pawn.set_actor_location(unreal.Vector(-2350,-600,105),False,True)
                state['phase']='outer';state['last_progress']=now
        elif state['phase']=='outer':
            pawn.add_movement_input(unreal.Vector(-1,0,0),1.,True)
            if now-state['last_progress']>2.5:
                state['blocked']['outer_wall']={'passed':-2470<p.x<-2355,'position':[p.x,p.y,p.z]}
                pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
                pawn.set_actor_location(unreal.Vector(2760,0,550),False,True)
                state['phase']='stage2';state['last_progress']=now
        elif state['phase']=='stage2':
            pawn.add_movement_input(unreal.Vector(1,0,0),1.,True)
            if now-state['last_progress']>2.5:
                state['blocked']['stage2_door']={'passed':2948<p.x<2965 and p.z>500,'position':[p.x,p.y,p.z]}
                pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
                pawn.set_actor_location(unreal.Vector(-2280,0,550),False,True)
                state['phase']='stage3';state['last_progress']=now
        elif state['phase']=='stage3':
            pawn.add_movement_input(unreal.Vector(-1,0,0),1.,True)
            if now-state['last_progress']>2.5:
                state['blocked']['stage3_door']={'passed':-2465<p.x<-2448 and p.z>500,'position':[p.x,p.y,p.z]}
                if not (state['first_person_camera_confirmed'] and state['max_z']>500 and all(v['passed'] for v in state['blocked'].values())):
                    finish(False,'Public route or door collision checks failed');return
                movement=pawn.get_component_by_class(unreal.CharacterMovementComponent)
                movement.stop_movement_immediately()
                capsule=pawn.get_component_by_class(unreal.CapsuleComponent)
                capsule.set_capsule_size(150.,175.,True)
                # The resized clearance proxy does not use player equipment or sprinting.
                pawn.get_component_by_class(unreal.PatrolEquipmentComponent).set_component_tick_enabled(False)
                movement.set_editor_property('max_walk_speed',180.)
                pawn.set_actor_location(unreal.Vector(600,-900,190),False,True)
                state['phase']='tyranno';state['tyranno_point']=0;state['last_progress']=now
                state['tyranno_proxy_dimensions_cm']=[2*capsule.get_scaled_capsule_radius(),2*capsule.get_scaled_capsule_half_height()]
        elif state['phase']=='tyranno':
            target=tyranno_route[state['tyranno_point']];dx=target[0]-p.x;dy=target[1]-p.y;distance=math.hypot(dx,dy)
            if distance<40 and abs(p.z-target[2])<45:
                state['tyranno_reached'].append({'index':state['tyranno_point'],'position':[p.x,p.y,p.z]})
                state['tyranno_point']+=1;state['last_progress']=now
            elif now-state['last_progress']>28:
                finish(False,'Tyranno proxy blocked at '+str(state['tyranno_point'])+' '+str([p.x,p.y,p.z]));return
            else:pawn.add_movement_input(unreal.Vector(dx/max(distance,1),dy/max(distance,1),0),1.,True)
            if state['tyranno_point']>=len(tyranno_route):
                finish(True)
    except Exception:finish(False,traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
