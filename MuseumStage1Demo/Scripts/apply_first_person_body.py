import unreal,sys,runpy
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());sys.path.insert(0,str(ROOT/'Scripts'))
runpy.run_path(str(ROOT/'Scripts/setup_first_person_body.py'))
from first_person_pawn import configure_first_person_pawn
configure_first_person_pawn(unreal.load_asset('/Game/Stage1/Blueprints/BP_Stage1_FirstPerson'))
unreal.log('FIRST_PERSON_PATROL_BODY_APPLIED')
