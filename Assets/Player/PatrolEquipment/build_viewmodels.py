"""Author sealed camera-space grips with the approved v15 palette; original stays untouched."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent
REPORTS=ROOT.parents[2]/'MuseumStage1Demo/Saved/EquipmentSource'
REPORTS.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT.parent/'night_patrol_v15/night_patrol_v15_uv.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
skin_color=tuple(bpy.data.objects['Hand_Continuous_r'].active_material.diffuse_color[:3])
shirt_color=tuple(bpy.data.objects['Upper_Continuous'].active_material.diffuse_color[:3])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
materials={}
def mat(name,color,rough=.65,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    materials[name]={'color':list(color),'roughness':rough,'metallic':metal}
    return m
skin=mat('Equipment_Skin',skin_color);shirt=mat('Equipment_Shirt',shirt_color)
rubber=mat('Equipment_Rubber',(.018,.025,.030),.82)
metal=mat('Equipment_Metal',(.10,.13,.15),.32,.75)
brass=mat('Equipment_Brass',(.45,.30,.10),.35,.6)
lens=mat('Equipment_Lens',(.8,.85,.77),.25)
cover=mat('Equipment_Cover',(.035,.075,.09),.7)
paper=mat('Equipment_Paper',(.62,.57,.43),.95)
label=mat('Equipment_Label',(.73,.65,.44),.65)
def point(p):return Vector((p[0],-p[1],p[2]))
groups={}
def finish(o,name,material,group):
    o.name=name;o.data.materials.append(material);groups.setdefault(group,[]).append(o)
    return o
def box(name,center,size,material,group,bevel=.3):
    bpy.ops.mesh.primitive_cube_add(size=1,location=point(center));o=bpy.context.object
    o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bevel;mod.segments=3
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(o,name,material,group)
def tube(name,a,b,r1,r2,material,group):
    a,b=point(a),point(b);d=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r1,radius2=r2,depth=d.length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return finish(o,name,material,group)
def sphere(name,center,radii,group):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=point(center))
    o=bpy.context.object;o.scale=radii
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,skin,group)

def capsule(name,a,b,radius,group):
    tube(name,a,b,radius,radius,skin,group)
    sphere(name+' start',a,(radius,)*3,group);sphere(name+' end',b,(radius,)*3,group)

def sleeve(side,wrist,group):
    sign=1 if side=='r' else -1
    c=point(wrist)
    hand_axis=Vector((6,-3.4,.7)).normalized()*12 if group=='Flashlight' else Vector((12,0,0))
    a=point((7,sign*25,-29));b=point(Vector(wrist)-hand_axis)
    vertices=[];faces=[];count=32;rings=17
    for j in range(rings):
        t=j/(rings-1);center=(1-t)**2*a+2*(1-t)*t*b+t*t*c
        tangent=(2*(1-t)*(b-a)+2*t*(c-b)).normalized()
        u=tangent.cross(Vector((0,0,1))).normalized();v=tangent.cross(u).normalized()
        radius=5.2*(1-t)+3.65*t
        if t>.87:radius+=.25*math.sin((t-.87)/.13*math.pi)
        for i in range(count):
            angle=i*2*math.pi/count;vertices.append(center+radius*(math.cos(angle)*u+math.sin(angle)*v))
    for j in range(rings-1):
        for i in range(count):
            n=(i+1)%count;faces.append((j*count+i,j*count+n,(j+1)*count+n,(j+1)*count+i))
    faces.extend([tuple(reversed(range(count))),tuple((rings-1)*count+i for i in range(count))])
    mesh=bpy.data.meshes.new('Closed sleeve');mesh.from_pydata(vertices,[],faces);mesh.update()
    o=bpy.data.objects.new('Continuous sleeve '+side,mesh);scene.collection.objects.link(o)
    for f in mesh.polygons:f.use_smooth=len(f.vertices)==4
    finish(o,o.name,shirt,group)

def hand(side,wrist,group):
    start=len(groups.get(group,[]));sign=1 if side=='r' else -1
    axis=Vector((6,-3.4,.7)).normalized() if group=='Flashlight' else Vector((1,0,0))
    capsule('Closed aligned wrist',Vector(wrist)-axis*4,Vector(wrist)+axis*4,3.1,group)
    center=Vector(wrist)+axis*(7 if group=='Flashlight' else 8)
    palm=sphere('Rounded palm grip',center,(4.9,4.1,4.1),group)
    palm.rotation_euler=point(axis).to_track_quat('X','Z').to_euler()
    parts=groups[group][start:];bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object
    o.name='Sealed grip '+side
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    remesh=o.modifiers.new('Solid palm finger and wrist union','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.28;remesh.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth=o.modifiers.new('Palm transitions','SMOOTH');smooth.factor=.6;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
    decimate=o.modifiers.new('Grip topology budget','DECIMATE');decimate.ratio=.5;bpy.ops.object.modifier_apply(modifier=decimate.name)
    for f in o.data.polygons:f.use_smooth=True
    groups[group]=groups[group][:start]+[o]
    sleeve(side,wrist,group)
hand('r',(32,21.4,-14.2),'Flashlight')
torch_parts_start=len(groups['Flashlight'])

tube('Torch grip',(30,14,-12),(46,14,-12),3.3,3.3,rubber,'Flashlight')
tube('Rear cap',(28,14,-12),(31,14,-12),3.6,3.6,metal,'Flashlight')
tube('Reflector housing',(45,14,-12),(52,14,-12),3.8,5,metal,'Flashlight')
tube('Lens bezel',(52,14,-12),(55,14,-12),5,5,brass,'Flashlight')
tube('Lens',(55,14,-12),(55.4,14,-12),4.4,4.4,lens,'Flashlight')
box('Power switch',(41,14,-8.4),(3,2.3,1.4),rubber,'Flashlight',.5)
for i in range(5):tube('Grip ridge %d'%i,(32+i*2.2,14,-12),(32.5+i*2.2,14,-12),3.55,3.55,metal,'Flashlight')

# Tilt only the torch; the wrist and palm keep their relaxed alignment.
torch_pose=Matrix.Translation(point((38,14,-15.5)))@Matrix.Rotation(math.radians(-10),4,'Y')@Matrix.Translation(-point((38,14,-12)))
for part in groups['Flashlight'][torch_parts_start:]:part.matrix_world=torch_pose@part.matrix_world

hand('r',(34,12.7,-17),'Notebook');hand('l',(34,-12.7,-17),'Notebook')
book_parts_start=len(groups['Notebook'])
box('Book cover',(46,0,-18),(2.4,28,29),cover,'Notebook',.7)
box('Page block',(46.6,0,-18),(1.6,26.5,27.5),paper,'Notebook',.25)
box('Front cover',(44.6,0,-18),(.45,28,29),cover,'Notebook',.25)
box('Book spine',(45.5,-13.8,-18),(3,1.2,29),brass,'Notebook',.4)
box('Cover label',(44.28,0,-14),(.15,23,14),paper,'Notebook',.15)
font=bpy.data.fonts.load('C:/Windows/Fonts/malgun.ttf')
for text,z,size in [('인수인계',-12,3.7),('노트',-17,3.7),('NIGHT PATROL',-26,1.55)]:
    curve=bpy.data.curves.new('Book lettering','FONT');curve.body=text;curve.font=font;curve.align_x='CENTER';curve.size=size;curve.extrude=.08;curve.resolution_u=4
    o=bpy.data.objects.new('Book '+text,curve);scene.collection.objects.link(o);o.location=point((44.13,0,z))
    o.rotation_euler=Matrix(((0,0,-1),(-1,0,0),(0,1,0))).to_euler();o.data.materials.append(cover if z>-20 else label)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');groups['Notebook'].append(bpy.context.object);o.select_set(False)

# Keep the smaller book close to the chest; both wrists remain parallel to the forearms.
book_transform=Matrix.Translation((46.5,0,-13))@Matrix.Diagonal((1,22/28,24/29,1))@Matrix.Translation((-46,0,18))
for part in groups['Notebook'][book_parts_start:]:part.matrix_world=book_transform@part.matrix_world

def finish_triangles(mesh):
    mesh.calc_loop_triangles()
    coords=[v.co for v in mesh.vertices]
    if all((coords[t.vertices[1]]-coords[t.vertices[0]]).cross(coords[t.vertices[2]]-coords[t.vertices[0]]).length*.5>=1e-12 for t in mesh.loop_triangles):return
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='EAR_CLIP')
    for iteration in range(5):
        bad=[f for f in bm.faces if (f.verts[1].co-f.verts[0].co).cross(f.verts[2].co-f.verts[0].co).length*.5<1e-12]
        if not bad:break
        bmesh.ops.beautify_fill(bm,faces=list(bm.faces),edges=list({e for f in bad for e in f.edges}),use_restrict_tag=False,method='AREA')
    assert all((f.verts[1].co-f.verts[0].co).cross(f.verts[2].co-f.verts[0].co).length*.5>=1e-12 for f in bm.faces),'Degenerate triangles remain'
    assert all(e.is_manifold for e in bm.edges),'Triangle cleanup opened the mesh'
    bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update()

report={}
for group,objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    for part in objects:
        bm=bmesh.new();bm.from_mesh(part.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not edge.is_manifold for edge in bm.edges)
        print('PART_TOPOLOGY',part.name,bad);assert bad==0,(part.name,bad)
        bm.to_mesh(part.data);bm.free()
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='SM_Patrol'+group+'View'
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    finish_triangles(o.data)
    for old_uv in list(o.data.uv_layers):o.data.uv_layers.remove(old_uv)
    uv=o.data.uv_layers.new(name='EquipmentUV')
    for face in o.data.polygons:
        drop=max(range(3),key=lambda i:abs(face.normal[i]));axes=[i for i in range(3) if i!=drop]
        for loop in face.loop_indices:
            v=o.data.vertices[o.data.loops[loop].vertex_index].co
            uv.data[loop].uv=(v[axes[0]]*.5,v[axes[1]]*.5)
    bpy.ops.export_scene.fbx(filepath=str(ROOT/(o.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='X',axis_up='Z',apply_unit_scale=True,bake_anim=False,mesh_smooth_type='FACE')
    original_transform=o.matrix_world.copy();o.matrix_world=Matrix.Scale(.01,4)@original_transform
    bpy.ops.export_scene.gltf(filepath=str(REPORTS/(o.name+'.glb')),use_selection=True,export_format='GLB')
    o.matrix_world=original_transform
    bm=bmesh.new();bm.from_mesh(o.data)
    bad_edges=sum(not e.is_manifold for e in bm.edges);bm.free()
    assert bad_edges==0,(group,bad_edges)
    o.data.calc_loop_triangles();report[group]={'triangles':len(o.data.loop_triangles),'materials':[m.name for m in o.data.materials],'open_or_nonmanifold_edges':bad_edges}
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'PatrolEquipment.blend'))
(ROOT/'materials.json').write_text(json.dumps(materials,indent=2),encoding='utf8')
(REPORTS/'mesh_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
