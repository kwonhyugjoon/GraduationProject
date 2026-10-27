"""Find exposed coplanar faces; subtract occlusion by boxes at the tested surface.

Uses convex polygon clipping in centimetres, without external dependencies.
Cubes and ceiling panels are exact; cylinder caps use 32-sided polygons.
Curved surfaces are checked for exact duplicate instances separately.
"""
import math,json,argparse,importlib.util
from pathlib import Path
from collections import defaultdict,Counter

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def area(poly):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))/2 if len(poly)>2 else 0
def clip(poly,fn):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da,db=fn(a),fn(b)
        if da>=-1e-8:out.append(a)
        if (da>0 and db<0) or (da<0 and db>0):
            t=da/(da-db);out.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(2)))
    return out
def ccw(poly):
    if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))<0:poly=poly[::-1]
    return poly
def edges(poly):
    for a,b in zip(poly,poly[1:]+poly[:1]):
        yield lambda p,a=a,b=b:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def intersect(poly,other):
    for fn in edges(ccw(other)):
        poly=clip(poly,fn)
        if not poly:break
    return poly
def subtract(poly,other):
    pieces=[]
    for fn in edges(ccw(other)):
        outer=clip(poly,lambda p: -fn(p))
        if area(outer)>.0001:pieces.append(outer)
        poly=clip(poly,fn)
        if area(poly)<.0001:break
    return pieces
def basis(rot):
    p,y,r=map(math.radians,rot);sp,cp,sy,cy,sr,cr=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    return [(cp*cy,cp*sy,sp),(sr*sp*cy-cr*sy,sr*sp*sy+cr*cy,-sr*cp),(-cr*sp*cy-sr*sy,-cr*sp*sy+sr*cy,cr*cp)]
def audit(layout):
    objects=[];faces=defaultdict(list);duplicates=[];seen={}
    for (mesh,mat,solid),items in layout['groups'].items():
        for index,item in enumerate(items):
            identity=(mesh,tuple(round(v,5) for k in ('p','s','r') for v in item[k]))
            name=f'{mesh}_{mat}_{"Solid" if solid else "Detail"}[{index}]'
            if identity in seen:duplicates.append([seen[identity],name])
            seen[identity]=name
            axes=basis(item['r']);half=[v*50 for v in item['s']];p=item['p']
            extent=[sum(abs(axes[j][i])*half[j] for j in range(3)) for i in range(3)]
            obj={'name':name,'mesh':mesh,'mat':mat,'p':p,'axes':axes,'half':half,
                 'lo':[p[i]-extent[i] for i in range(3)],'hi':[p[i]+extent[i] for i in range(3)]}
            oid=len(objects);objects.append(obj)
            specs=[]
            if mesh=='Cube':
                for axis in range(3):
                    other=[i for i in range(3) if i!=axis]
                    for sign in (-1,1):
                        normal=tuple(sign*v for v in axes[axis]);center=[p[i]+normal[i]*half[axis] for i in range(3)]
                        points=[tuple(center[i]+a*half[other[0]]*axes[other[0]][i]+b*half[other[1]]*axes[other[1]][i] for i in range(3)) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
                        specs.append((normal,points))
            elif mesh=='Plane':
                specs.append((axes[2],[tuple(p[i]+a*half[0]*axes[0][i]+b*half[1]*axes[1][i] for i in range(3)) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]))
            elif mesh=='Cylinder':
                for sign in (-1,1):
                    normal=tuple(sign*v for v in axes[2])
                    points=[tuple(p[i]+normal[i]*half[2]+math.cos(t*math.tau/32)*half[0]*axes[0][i]+math.sin(t*math.tau/32)*half[1]*axes[1][i] for i in range(3)) for t in range(32)]
                    specs.append((normal,points))
            for normal,points in specs:
                d=dot(normal,points[0]);drop=max(range(3),key=lambda i:abs(normal[i]));uv=[i for i in range(3) if i!=drop]
                poly=ccw([tuple(pt[i] for i in uv) for pt in points])
                key=tuple(round(v,6) for v in normal)+(round(d,3),)
                faces[key].append({'oid':oid,'n':normal,'d':d,'drop':drop,'uv':uv,'poly':poly,
                    'min':[min(p[i] for p in poly) for i in range(2)],'max':[max(p[i] for p in poly) for i in range(2)]})
    findings=[];raw=0;buried=0
    for group in faces.values():
        group.sort(key=lambda f:f['min'][0])
        for i,a in enumerate(group):
            for b in group[i+1:]:
                if b['min'][0]>=a['max'][0]-.0001:break
                if min(a['max'][1],b['max'][1])-max(a['min'][1],b['min'][1])<=.0001:continue
                poly=intersect(a['poly'],b['poly'])
                if area(poly)<.01:continue
                raw+=1;n=a['n'];uv=a['uv'];drop=a['drop']
                def world(pt):
                    p=[0.,0.,0.];p[uv[0]],p[uv[1]]=pt
                    p[drop]=(a['d']-n[uv[0]]*pt[0]-n[uv[1]]*pt[1])/n[drop]
                    return [p[i]+n[i]*.02 for i in range(3)]
                points=[world(pt) for pt in poly];lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
                visible=[poly]
                for oid,obj in enumerate(objects):
                    if oid in (a['oid'],b['oid']) or obj['mesh']!='Cube':continue
                    if any(hi[i]<obj['lo'][i] or lo[i]>obj['hi'][i] for i in range(3)):continue
                    cover=poly
                    for axis,h in zip(obj['axes'],obj['half']):
                        for sign in (-1,1):
                            cover=clip(cover,lambda pt,axis=axis,h=h,sign=sign:h-sign*dot([world(pt)[i]-obj['p'][i] for i in range(3)],axis))
                            if not cover:break
                        if not cover:break
                    if area(cover)<.0001:continue
                    visible=[part for piece in visible for part in subtract(piece,cover)]
                    if not visible:break
                exposed=sum(area(p) for p in visible)/abs(n[drop])
                if exposed<.05:buried+=1;continue
                left,right=objects[a['oid']],objects[b['oid']]
                findings.append({'a':left['name'],'b':right['name'],'materials':[left['mat'],right['mat']],
                    'exposed_area_cm2':round(exposed,3),'normal':[round(v,5) for v in n],
                    'near':[round(sum(p[i] for p in points)/len(points),3) for i in range(3)]})
    return {'instances':len(objects),'planar_faces':sum(map(len,faces.values())),
        'raw_coplanar_pairs':raw,'fully_buried_pairs':buried,'exposed_coplanar_pairs':len(findings),
        'different_material_pairs':sum(f['materials'][0]!=f['materials'][1] for f in findings),
        'duplicate_instances':duplicates,'findings':findings,
        'method':'Same-facing plane overlap with convex clipping; subtract third-box occlusion 0.2 mm above each face. Cylinder caps approximated with 32 vertices. Curved side faces excluded; exact duplicate transforms checked for all primitive types.'}

if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('--layout',default=str(Path(__file__).with_name('stage1_layout.py')));args.add_argument('--out',required=True);opt=args.parse_args()
    spec=importlib.util.spec_from_file_location('audit_layout',opt.layout);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=audit(module.make_layout());Path(opt.out).write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='findings'},indent=2))
    print('Material pairs:',Counter(tuple(sorted(f['materials'])) for f in result['findings']))
    for item in result['findings'][:25]:print(item)
