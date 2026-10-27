"""Derive a skinned first-person body while preserving the approved source."""
import bpy,json
from mathutils import Matrix
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'Assets/Player/night_patrol_v15/night_patrol_v15_uv.blend'
OUT=ROOT/'References/FirstPersonBody'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
collection=bpy.data.collections['NightPatrol_Character']
rig=next(o for o in collection.objects if o.type=='ARMATURE')
if rig.animation_data:rig.animation_data_clear()
meshes=[o for o in collection.objects if o.type=='MESH']
# Author in centimetres with applied object scale so animation roots stay at scale 1.
worlds={o:o.matrix_world.copy() for o in [rig]+meshes}
for obj,matrix in worlds.items():obj.matrix_world=Matrix.Scale(100,4)@matrix
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes+[rig]:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=.01
rig.name='Armature'
bpy.context.view_layer.update()
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
height=max(p.z for p in points)-min(p.z for p in points)
assert 174<height<176,'The derived model must be 175 cm tall: '+str(height)
def export(name,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(OUT/name),use_selection=True,
        object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,
        axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE')
export('patrol_world.fbx',meshes+[rig])
removed=[];kept=[]
for obj in meshes:
    group_names={g.index:g.name for g in obj.vertex_groups}
    head_vertices=sum(any(group_names[g.group]=='head' and g.weight>.5 for g in v.groups) for v in obj.data.vertices)
    if head_vertices>len(obj.data.vertices)*.5 or obj.name=='Neck_Visible':
        removed.append(obj.name);bpy.data.objects.remove(obj,do_unlink=True)
    else:kept.append(obj)
assert removed and len(kept)>5,'Head/body separation failed'
export('patrol_first_person_body.fbx',kept+[rig])
report={'source':SOURCE.relative_to(ROOT.parent).as_posix(),'removed_head_meshes':removed,'body_meshes':[o.name for o in kept],
    'bones':[{ 'name':b.name,'parent':b.parent.name if b.parent else None,
               'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones],
    'original_source_unchanged':True}
(OUT/'body_source.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
