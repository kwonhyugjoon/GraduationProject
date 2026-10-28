"""Exercise real PIE input, movement, equipment visibility and wall clearance."""
import unreal,time,json,traceback,sys,math
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());sys.path.insert(0,str(ROOT/'Scripts'))
OUT=ROOT/'Saved/Review';OUT.mkdir(parents=True,exist_ok=True)
REPORT=ROOT/'Saved/Validation/patrol_equipment.json';REPORT.parent.mkdir(parents=True,exist_ok=True)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level('/Game/Stage1/Maps/L_MuseumStage1')
state={'start':time.monotonic(),'phase':'start','index':0,'results':[]}
steps=['torch_wrist_up','torch_on','torch_off','notebook','book_down85','book_down89','book_down25','book_down45','book_down60','book_down70','book_down_sprint','book_down_jump','book_wall','notebook_click','empty','restore_off','restore_on','walk','sprint','release_shift','jump','wall']
held=set()
def key(world,pc,name,down):
    unreal.SystemLibrary.execute_console_command(world,'Patrol.TestKey '+name+(' down' if down else ' up'),pc)
    if down:held.add(name)
    else:held.discard(name)
def finish(error=None):
    REPORT.write_text(json.dumps({'passed':error is None,'error':error,'results':state['results'],
        'method':'Editor-only console bridge dispatches PC InputKey events into the actual PIE input pipeline. Screenshots use the player camera; movement samples come from CharacterMovement.'},indent=2),encoding='utf8')
    state.update(phase='shutdown',changed=time.monotonic());level.editor_request_end_play()
def tick(delta):
    try:
        now=time.monotonic()
        if state['phase']=='shutdown':
            if now-state['changed']>3:
                unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if now-state['start']>150:finish('Equipment test timeout');return
        if state['phase']=='start':
            if now-state['start']<4:return
            level.editor_request_begin_play();state.update(phase='wait',changed=now);return
        world=unreal.EditorLevelLibrary.get_game_world()
        if not world:return
        pawn=unreal.GameplayStatics.get_player_character(world,0)
        if not pawn:return
        pc=unreal.GameplayStatics.get_player_controller(world,0)
        move=pawn.get_component_by_class(unreal.CharacterMovementComponent)
        equipment=pawn.get_component_by_class(unreal.PatrolEquipmentComponent)
        if not equipment:raise AssertionError('Equipment component is absent')
        views={m.get_name():m for m in pawn.get_components_by_class(unreal.StaticMeshComponent)}
        torch=views['HeldFlashlight'];book=views['HeldNotebook']
        beam=next(m for m in pawn.get_components_by_class(unreal.SpotLightComponent) if m.get_name()=='PatrolFlashlightBeam')
        root=next(m for m in pawn.get_components_by_class(unreal.SceneComponent) if m.get_name()=='PatrolViewRoot')
        if state['phase']=='wait':
            if now-state['changed']<9:return
            unreal.SystemLibrary.execute_console_command(world,'t.MaxFPS 60',pc)
            pawn.set_actor_location(unreal.Vector(650,-1400,92.15),False,True)
            pc.set_control_rotation(unreal.Rotator(pitch=-6,yaw=90,roll=0))
            state.update(phase='setup')
        name=steps[state['index']]
        if state['phase']=='setup':
            for k in list(held):key(world,pc,k,False)
            state.update(phase='test',changed=now,shot=False,released=False,peak_z=-1e9)
            if name=='notebook_click':
                pawn.set_actor_location(unreal.Vector(650,-1400,92.15),False,True);pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0))
            if name=='torch_wrist_up':pc.set_control_rotation(unreal.Rotator(pitch=30,yaw=90,roll=0))
            elif name=='torch_on':pc.set_control_rotation(unreal.Rotator(pitch=-6,yaw=90,roll=0))
            elif name in ('torch_off','notebook_click','restore_on'):key(world,pc,'LeftMouseButton',True)
            elif name=='notebook':key(world,pc,'Two',True)
            elif name.startswith('book_down'):
                pitch=-int(name[9:]) if name[9:].isdigit() else -85
                pawn.set_actor_location(unreal.Vector(650,-1400,92.15),False,True);move.stop_movement_immediately()
                pc.set_control_rotation(unreal.Rotator(pitch=pitch,yaw=90,roll=0))
                if name in ('book_down_sprint','book_down_jump'):
                    key(world,pc,'W',True);key(world,pc,'LeftShift',True)
                    if name=='book_down_jump':key(world,pc,'SpaceBar',True)
            elif name=='book_wall':
                pawn.set_actor_location(unreal.Vector(1600,1320,92.15),False,True)
                pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0));key(world,pc,'W',True)
            elif name=='empty':
                key(world,pc,'Three',True);pc.set_control_rotation(unreal.Rotator(pitch=-70,yaw=90,roll=0))
            elif name=='restore_off':
                key(world,pc,'One',True);pc.set_control_rotation(unreal.Rotator(pitch=-6,yaw=90,roll=0))
            elif name in ('walk','sprint','release_shift','jump'):
                pawn.set_actor_location(unreal.Vector(650,-1400,92.15),False,True);move.stop_movement_immediately()
                pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0))
                key(world,pc,'W',True)
                if name in ('sprint','release_shift','jump'):key(world,pc,'LeftShift',True)
                if name=='jump':key(world,pc,'SpaceBar',True)
                state['position_start']=[650,-1400,92.15]
            elif name=='wall':
                pawn.set_actor_location(unreal.Vector(1600,1320,92.15),False,True)
                pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0))
                key(world,pc,'W',True)
            return
        elapsed=now-state['changed']
        if name not in ('walk','sprint','release_shift','jump','wall','book_down_sprint','book_down_jump','book_wall') and not state['released'] and elapsed>.18:
            for k in list(held):key(world,pc,k,False)
            state['released']=True
        if name=='release_shift' and not state['released'] and elapsed>.4:
            key(world,pc,'LeftShift',False);state['released']=True
        pos=pawn.get_actor_location();state['peak_z']=max(state['peak_z'],pos.z)
        if name in ('jump','book_down_jump') and elapsed>.18 and 'SpaceBar' in held:key(world,pc,'SpaceBar',False)
        screenshot=name.startswith('book_') or name in ('torch_wrist_up','torch_on','torch_off','notebook','empty','restore_on','wall')
        wait=2.8 if screenshot else 1.2
        if screenshot and not state['shot'] and elapsed>1.0:
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1600x900 filename="'+str(OUT/('equipment_'+name+'.png'))+'"',pc)
            state['shot']=True
        if elapsed<wait:return
        result={'name':name,'slot':equipment.get_editor_property('hand_slot'),'switch_on':equipment.get_editor_property('flashlight_on'),
            'torch_visible':torch.get_editor_property('visible'),'book_visible':book.get_editor_property('visible'),
            'beam_visible':beam.get_editor_property('visible'),'max_walk_speed':move.get_editor_property('max_walk_speed'),
            'speed':pawn.get_velocity().length(),'location':[pos.x,pos.y,pos.z]}
        if result['slot']==1:
            camera=pawn.get_component_by_class(unreal.CameraComponent)
            relative=unreal.MathLibrary.normalized_delta_rotator(beam.get_world_rotation(),camera.get_world_rotation())
            result['beam_pitch_above_view']=relative.pitch
            assert abs(relative.pitch-10)<.1,'Beam did not follow the raised torch: '+str(result)
        if name in ('torch_wrist_up','torch_on','restore_on'):assert result['slot']==1 and result['torch_visible'] and result['beam_visible'],result
        if name in ('torch_off','restore_off'):assert result['slot']==1 and result['torch_visible'] and not result['beam_visible'] and not result['switch_on'],result
        if name in ('notebook','notebook_click'):assert result['slot']==2 and result['book_visible'] and not result['torch_visible'] and not result['beam_visible'] and not result['switch_on'],result
        if name.startswith('book_down'):
            rotation=book.get_world_rotation();camera=pawn.get_component_by_class(unreal.CameraComponent)
            result['camera_pitch']=(camera.get_world_rotation().pitch+180)%360-180
            result['book_pitch']=(rotation.pitch+180)%360-180
            assert -25.05<=result['book_pitch']<=-24.95,result
            forward=pawn.get_actor_forward_vector();origin=pawn.get_actor_location()
            transform=book.get_world_transform()
            corners=[unreal.Vector(x,y,z) for x in (44.5,48.0) for y in (-11.4,11.4) for z in (-25.0,-1.0)]
            depths=[(transform.transform_location(c)-origin).dot(forward) for c in corners]
            result['book_front_clearance_cm']=min(depths)
            assert result['book_visible'] and min(depths)>35,'Book entered the body envelope: '+str(result)
            original_depths=[(camera.get_world_transform().transform_location(c)-origin).dot(forward) for c in corners]
            result['unlimited_pose_front_clearance_cm']=min(original_depths)
            if name in ('book_down70','book_down85'):assert min(original_depths)<35,'Original pose no longer reproduces body penetration'
        if name in ('book_down60','book_down70','book_down85','book_down89'):
            # Test the real sleeve cap, including its rim, against the player camera frustum.
            camera_transform=camera.get_world_transform();half_width=math.tan(math.radians(camera.get_editor_property('field_of_view')/2));half_height=half_width*9/16
            result['sleeve_cap_screen_bounds']=[]
            for sign in (-1,1):
                start=unreal.Vector(7,sign*25,-29);tangent=unreal.Vector(15,-sign*12.3,12).normal()
                u=tangent.cross(unreal.Vector(0,0,1)).normal();v=tangent.cross(u).normal()
                points=[start]+[start+(u*math.cos(i*2*math.pi/32)+v*math.sin(i*2*math.pi/32))*5.2 for i in range(32)]
                projected=[]
                for point in points:
                    local=camera_transform.inverse_transform_location(transform.transform_location(point))
                    assert local.x>0,'Sleeve cap crossed behind the camera'
                    projected.append((.5+local.y/(2*local.x*half_width),.5-local.z/(2*local.x*half_height)))
                lo=[min(p[a] for p in projected) for a in (0,1)];hi=[max(p[a] for p in projected) for a in (0,1)]
                result['sleeve_cap_screen_bounds'].append([lo,hi])
                assert hi[0]<0 or lo[0]>1 or hi[1]<0 or lo[1]>1,'Sleeve cut end entered the view: '+str(result)
        if name=='book_wall':assert not result['book_visible'],'Book retracted through the chest near a wall'
        if name=='empty':assert result['slot']==3 and not result['book_visible'] and not result['torch_visible'] and not result['beam_visible'],result
        if name in ('walk','release_shift'):assert 285<result['speed']<315 and result['max_walk_speed']==300,result
        if name=='sprint':assert 505<result['speed']<535 and result['max_walk_speed']==520,result
        if name=='jump':
            result['jump_height_cm']=state['peak_z']-92.15;assert result['jump_height_cm']>40,result
        if name=='wall':
            offset=root.get_editor_property('relative_location');result['wall_retract_cm']=-offset.x
            assert offset.x<-8,result
            camera=pawn.get_component_by_class(unreal.CameraComponent)
            assert unreal.SystemLibrary.line_trace_single(world,camera.get_world_location(),beam.get_world_location(),unreal.TraceTypeQuery.TRACE_TYPE_QUERY2,False,[pawn],unreal.DrawDebugTrace.NONE,True) is None,'Flashlight origin crossed a wall'
        if screenshot:assert (OUT/('equipment_'+name+'.png')).is_file(),'Missing screenshot: '+name
        state['results'].append(result)
        for k in list(held):key(world,pc,k,False)
        move.stop_movement_immediately()
        state['index']+=1
        if state['index']==len(steps):finish();return
        state['phase']='setup'
    except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
