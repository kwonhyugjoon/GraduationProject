"""Capture actual editor views after shaders settle; no image generation."""
import unreal,time,json,traceback,hashlib,sys
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Review';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'Scripts'))
from surface_review_views import VIEWS
before='-Stage1SurfaceBefore' in unreal.SystemLibrary.get_command_line()
if before:OUT=ROOT/'Saved/SurfaceBefore';OUT.mkdir(parents=True,exist_ok=True)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level.load_level('/Game/Stage1/Maps/L_MuseumStage1')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors=actors.get_all_level_actors()
camera_by_label={a.get_actor_label():a for a in all_actors if isinstance(a,unreal.CameraActor)}
floor_actor=next(a for a in all_actors if a.get_actor_label()=='Cube_gallery_floor_Solid')
assert hasattr(floor_actor,'set_is_temporarily_hidden_in_editor'),'Temporary editor visibility API is unavailable'
names=['Overview','Entrance','UpperGallery','Exterior','StaffCorridor','UpperPatrol','GalleryPatrol','Stage2Door','Stage3Door','DummyFront','DummyBack','NorthStaffDoor','GallerySign','StaffLayout']
for name,(position,target) in VIEWS.items():
    camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*position),unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*position),unreal.Vector(*target)))
    camera.get_component_by_class(unreal.CameraComponent).set_field_of_view(85.)
    camera_by_label['Preview_'+name]=camera
names=list(VIEWS) if before else names+list(VIEWS)
state={'start':time.monotonic(),'index':0,'task':None,'last':0,'done':[],'cutaway':False}
(OUT/'screenshot_api.txt').write_text(unreal.AutomationLibrary.take_high_res_screenshot.__doc__,encoding='utf-8')
def tick(delta):
    global floor_actor
    try:
        elapsed=time.monotonic()-state['start']
        if elapsed<35:return
        if state['task'] is not None:
            if not state['task'].is_task_done():return
            name=names[state['index']]
            if name=='StaffLayout':floor_actor.set_is_temporarily_hidden_in_editor(False)
            state['done'].append(name);state['index']+=1;state['task']=None;state['last']=elapsed
        if elapsed-state['last']<3:return
        if state['index']>=len(names):
            (OUT/'capture_report.json').write_text(json.dumps({'views':state['done'],'engine_rendered':True,
                'map_source_sha256':hashlib.sha256((ROOT/'Content/Stage1/Maps/L_MuseumStage1.umap').read_bytes()).hexdigest(),
                'staff_layout_cutaway':'Only upper floor slabs temporarily hidden for this review; restored after screenshot. Map not saved.'},indent=2),encoding='utf-8')
            unreal.unregister_slate_post_tick_callback(handle)
            camera_by_label.clear();all_actors.clear();floor_actor=None
            unreal.SystemLibrary.quit_editor();return
        name=names[state['index']]
        if name=='StaffLayout' and not state['cutaway']:
            floor_actor.set_is_temporarily_hidden_in_editor(True)
            state['cutaway']=True;state['last']=elapsed;return
        state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(OUT/(name.lower()+'.png')),camera=camera_by_label['Preview_'+name])
    except Exception:
        if floor_actor is not None:floor_actor.set_is_temporarily_hidden_in_editor(False)
        (OUT/'capture_error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
