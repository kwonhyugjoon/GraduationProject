"""Museum layout in centimetres; all generated geometry is original primitive work."""
import math
from collections import defaultdict

def make_layout():
    groups=defaultdict(list)
    lights=[];signs=[]
    def shape(mesh,mat,p,size,rot=(0,0,0),solid=False):
        groups[(mesh,mat,solid)].append({'p':list(p),'s':[v/100 for v in size],'r':list(rot)})
    def box(mat,p,size,rot=(0,0,0),solid=True):shape('Cube',mat,p,size,rot,solid)
    def cylinder(mat,p,r,h,solid=False):shape('Cylinder',mat,p,(r*2,r*2,h),solid=solid)
    def sphere(mat,p,size):shape('Sphere',mat,p,size)
    def beam(mat,a,b,r=6,solid=False):
        d=[b[i]-a[i] for i in range(3)];length=sum(v*v for v in d)**.5
        yaw=math.degrees(math.atan2(d[1],d[0]));pitch=-math.degrees(math.atan2(math.hypot(d[0],d[1]),d[2]))
        shape('Cylinder',mat,[(a[i]+b[i])/2 for i in range(3)],(2*r,2*r,length),(pitch,yaw,0),solid)
    def rail(a,b):
        for h,r in [(100,4),(27,3)]:beam('brass',(a[0],a[1],a[2]+h),(b[0],b[1],b[2]+h),r,True)
        sloped=abs(a[2]-b[2])>=1
        count=round((b[1]-a[1])/30) if sloped else max(1,int(math.dist(a,b)/36))
        samples=[(i+.5)/count for i in range(count)] if sloped else [i/count for i in range(count+1)]
        for t in samples:
            p=[a[j]+(b[j]-a[j])*t for j in range(3)]
            base=p[2] if abs(a[2]-b[2])<1 else min(450,(math.floor((p[1]-650)/30)+1)*18)
            top=p[2]+100
            cylinder('brass',(p[0],p[1],(base-1+top)/2),2.8,top-base+1,True)
            cylinder('brass',(p[0],p[1],base+2),7,4,True)
    def column(x,y,height=800):
        box('stone_dark',(x,y,20),(120,120,40))
        box('stone',(x,y,48),(104,104,18))
        cylinder('stone',(x,y,height/2),43,height-100,True)
        for i in range(12):
            t=math.tau*i/12
            cylinder('stone_light',(x+41*math.cos(t),y+41*math.sin(t),height/2),3,height-145)
        box('stone_light',(x,y,height-35),(108,108,25))
        box('stone',(x,y,height-12),(125,125,20))
        for z in ([170,600] if height>=700 else [170]):
            sphere('lamp',(x,y-50,z),(19,19,29))
            cylinder('brass',(x,y-50,z-22),13,8)
            lights.append({'p':[x,y-65,z],'power':260 if z==600 else 180,'radius':650 if z==600 else 390,'color':[255,186,112]})
    def plant(x,y):
        cylinder('brass',(x,y,32),42,64,True)
        cylinder('soil',(x,y,65),36,4)
        beam('wood_dark',(x,y,65),(x+8,y,165),9)
        for i in range(9):
            t=math.tau*i/9
            sphere('leaf',(x+55*math.cos(t),y+55*math.sin(t),154+(i%3)*14),(95,35,25))
    def bench(x,y,yaw=0):
        box('wood_dark',(x,y,49),(180,52,13),(0,yaw,0))
        t=math.radians(yaw)
        for dx in [-65,65]:
            px=x+dx*math.cos(t);py=y+dx*math.sin(t)
            box('bronze',(px,py,24),(13,43,43),(0,yaw,0))
        back=(x-24*math.sin(t),y+24*math.cos(t),92.25)
        box('wood_dark',back,(180,10,73.5),(0,yaw,0))
    def plaque(x,y,z,text,yaw=-90,size=26,width=None,height=None):
        # The supplied plane is the support surface; text sits 2mm off its inset.
        width=width or max(100,len(text)*size*.62+24);height=height or size*1.6+8
        nx,ny=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
        box('brass',(x+nx*2,y+ny*2,z),(4,width,height),(0,yaw,0),False)
        box('door',(x+nx*4.5,y+ny*4.5,z),(1,width-4,height-4),(0,yaw,0),False)
        signs.append({'p':[x+nx*5.2,y+ny*5.2,z],'text':text,'yaw':yaw,'size':size,
                      'mounted':True,'support':[x,y,z],'panel_size':[width,height]})
    def door(x,y,z=0,width=220,text='STAFF ONLY'):
        box('door',(x,y,z+125),(width,18,250))
        for dx in [-width/2,width/2]:box('stone_dark',(x+dx,y,z+131.25),(24,44,262.5))
        box('stone_dark',(x,y,z+275),(width+44,44,25))
        box('brass',(x+width*.31,y-13,z+123),(8,6,42),solid=False)
        sphere('red',(x+width/2+28,y-25,z+158),(10,7,14))
        plaque(x,y-9,z+205,text,-90,18,width=width-40,height=38)
    def room(name,x0,x1,y0,y1,entry='south'):
        width=x1-x0;depth=y1-y0;cx=(x0+x1)/2;cy=(y0+y1)/2
        # The parquet lives in the material; a room has one continuous floor surface.
        box('room_floor',(cx,cy,1.75),(width,depth,3.5),solid=False)
        door_width=280
        for side,axis,fixed,lo,hi in [('west','y',x0,y0,y1),('east','y',x1,y0,y1),
                                     ('south','x',y0,x0,x1),('north','x',y1,x0,x1)]:
            middle=(lo+hi)/2
            # Full horizontal runs and shortened vertical runs meet at butt joints.
            for mat,z,h,d in [('stone',140,280,28),('stone_dark',28,55,36),('brass',262,20,36)]:
                a0,b0=(lo-d/2,hi+d/2) if axis=='x' else (lo+d/2,hi-d/2)
                opening=door_width if mat=='stone' else door_width-.6
                spans=[(a0,middle-opening/2),(middle+opening/2,b0)] if side==entry else [(a0,b0)]
                for a,b in spans:
                    x,y=((a+b)/2,fixed) if axis=='x' else (fixed,(a+b)/2)
                    box(mat,(x,y,z),(b-a,d,h) if axis=='x' else (d,b-a,h))
            if side==entry:
                x,y=(middle,fixed) if axis=='x' else (fixed,middle)
                box('stone',(x,y,263),(door_width,28,34) if axis=='x' else (28,door_width,34))
        if entry=='west':plaque(x0-14,cy,263,name,180,17,220,30)
        elif entry=='east':plaque(x1+14,cy,263,name,0,17,220,30)
        else:plaque(cx,y0-14,263,name,-90,17,220,30)
        for x in [x0+65,x1-65]:
            for y in [y0+70,y1-70]:
                box('stone_dark',(x,y,125),(45,45,250))
                box('brass',(x,y,247),(65,65,15))
                sphere('lamp',(x,y,265),(22,22,26))
                lights.append({'p':[x,y,225],'power':180,'radius':550,'color':[255,189,125]})
    # The visitor floor and a restrained checker marble pattern.
    box('stone_dark',(-250,0,-28),(5600,3700,56))
    for ix in range(35):
        for iy in range(23):
            x=-2980+ix*160;y=-1760+iy*160
            box('marble_a' if (ix+iy)%2 else 'marble_b',(x,y,.2),(158.5,158.5,.4),solid=False)
    # Tall museum enclosure, entry portal, classical cornice and window bays.
    for x in [-3000,2500]:
        for a,b in [(-1767.5,-170),(170,1767.5)]:box('stone',(x,(a+b)/2,440),(65,b-a,880))
        box('stone',(x,0,225),(65,340,450))
        box('stone',(x,0,817),(65,340,126))
    box('stone',(-250,1800,440),(5565,65,880))
    for a,b in [(-3032.5,-300),(300,2532.5)]:box('stone',((a+b)/2,-1800,440),(b-a,65,880))
    box('stone',(0,-1800,640),(600,65,480))
    for z,h,d,mat in [(55,80,89,'stone_dark'),(440,42,90,'brass'),(825,38,120,'stone_light'),(870,35,155,'stone_dark')]:
        left=min(-3042,-2990-d/2);right=max(2542,2490+d/2)
        for y in [-1790,1790]:box(mat,((left+right)/2,y,z),(right-left,d,h))
        for x in [left+d/2,right-d/2]:
            inner=1790-d/2
            for a,b in ([(-inner,-171),(171,inner)] if z==440 else [(-inner,inner)]):
                box(mat,(x,(a+b)/2,z),(d,b-a,h))
    # Restore a walkable entrance opening through the low decorative band.
    door(0,-1780,0,550,'NIGHT MUSEUM')
    for x in [-2980,2480]:
        for y in [-1500,-750,0,750,1500]:column(x,y,416 if y==0 else 800)
    for y in [-1780,1780]:
        for x in [-2650,-2000,-1300,-650,650,1300,2000]:column(x,y)
    for x in [-380,380]:column(x,-1860,865)
    plaque(0,-1864,750,'NIGHT MUSEUM',-90,65,820,115)
    for side in [-1,1]:
        for y in [-1125,-375,375,1125]:
            x=(-3000 if side<0 else 2500)-side*42
            box('window',(x,y,590),(6,325,365),solid=False)
            for yy in [y-175,y+175]:box('stone_dark',(x,yy,590),(25,22,395),solid=False)
            for z in [395,590,785]:box('brass',(x,y,z),(27,365,12),solid=False)
            box('stone_dark',(x,y,590),(25,10,380),solid=False)
    for x in [-2325,-1650,-950,950,1650]:
        box('window',(x,1758,590),(325,6,365),solid=False)
        for dx in [-175,175]:box('stone_dark',(x+dx,1753,590),(22,25,395),solid=False)
        for z in [395,590,785]:box('brass',(x,1753,z),(365,27,12),solid=False)
    # Exterior window reveals and a stone forecourt complete the building frontage.
    for y,face in [(-1840,-1),(1840,1)]:
        for x in [-2325,-1650,-950,950,1650]:
            box('window',(x,y,590),(325,8,365),solid=False)
            for dx in [-175,175]:box('stone_dark',(x+dx,y+face*5,590),(22,25,395),solid=False)
            for z in [395,590,785]:box('brass',(x,y+face*8,z),(365,16,12),solid=False)
    for side in [-1,1]:
        for y in [-1125,-375,375,1125]:
            x=(-3000 if side<0 else 2500)+side*40
            box('window',(x,y,590),(8,325,365),solid=False)
            for dy in [-175,175]:box('stone_dark',(x+side*5,y+dy,590),(25,22,395),solid=False)
            for z in [395,590,785]:box('brass',(x+side*8,y,z),(16,365,12),solid=False)
    box('stone_dark',(0,-1855,750),(820,18,115),solid=False)
    box('window',(0,-1792,335),(548,18,125))
    box('brass',(0,-1793,126),(10,25,250))
    box('stone_dark',(-250,-2600,-52),(6500,1600,48))
    for a,b,top in [(-2030,-1980,-20),(-1980,-1930,-10),(-1930,-1850,0)]:
        box('stone_light',(0,(a+b)/2,(-28+top)/2),(1000,b-a,top+28))
    for x in [-1150,1150]:plant(x,-2200)
    # A down-facing atrium roof reads as a ceiling inside, but remains a cutaway above.
    shape('Plane','ceiling',(-250,0,895),(5500,3600,100),(180,0,0))
    for x in [-2600,-1900,-950,0,950,1900]:shape('Plane','stone_light',(x,0,880),(25,3570,100),(180,0,0))
    for y in [-1200,-400,400,1200]:
        start=-2975
        for x in [-2600,-1900,-950,0,950,1900]:
            shape('Plane','stone_light',((start+x-12.5)/2,y,880),(x-12.5-start,25,100),(180,0,0))
            start=x+12.5
        shape('Plane','stone_light',((start+2475)/2,y,880),(2475-start,25,100),(180,0,0))
    # A rectangular visitor gallery covers the reverse-C staff passage below.
    for p,s in [((-2695,0,432),(530,2880,36)),((-230,1610,432),(5460,340,36)),
                ((-230,-1610,432),(5460,340,36)),((2305,0,432),(390,2880,36))]:box('gallery_floor',p,s)
    rail((-2450,-1460,450),(-2450,1460,450))
    rail((-2450,-1460,450),(2130,-1460,450))
    rail((-2450,1460,450),(-340,1460,450))
    rail((340,1460,450),(2130,1460,450))
    rail((2130,-1460,450),(2130,1460,450))
    # The main stair is fully traversable, with eighteen-centimetre risers.
    for i in range(25):
        h=(i+1)*18;y=650+(i+.5)*30
        box('stone_light',(0,y,h/2),(600,30,h))
        box('brass',(0,y-14.5,h-1.7),(598,2,4),solid=False)
    box('gallery_floor',(0,1420,432),(680,40,36))
    # Close the unused bay behind the stair all the way to the rear wall/soffit.
    box('stone_light',(0,1583.75,207),(600,367.5,414))
    rail((-285,650,0),(-285,1400,450));rail((285,650,0),(285,1400,450))
    for side in (-1,1):
        beam('brass',(side*285,650,100),(side*340,635,100),4,True)
        beam('brass',(side*285,1400,550),(side*340,1420,550),4,True)
    for x in [-340,340]:
        for y,z in [(635,0),(1420,450)]:
            box('stone_dark',(x,y,z+63),(70,70,126))
            sphere('lamp',(x,y,z+145),(35,35,45))
            lights.append({'p':[x,y,z+160],'power':280,'radius':550,'color':[255,185,108]})
    # Three roofless exhibition rooms on the ground floor.
    room('GALLERY A',-2390,-850,250,1250,entry='east')
    room('GALLERY B',-2390,-850,-1250,-250,entry='east')
    room('GALLERY C',950,2100,-1410,1410,entry='west')
    # Closed future-stage entrances sit in real openings at the side-wall centres.
    for side,stage in [(-1,2),(1,3)]:
        x=-3000 if side<0 else 2500;face=0 if side<0 else 180
        box('stone_dark',(x-side*10,0,452),(110,340,4))
        box('door',(x,0,589),(18,280,270))
        for y in [-155,155]:box('stone_light',(x-side*10,y,589),(110,30,270))
        box('stone_light',(x-side*10,0,739),(110,340,30))
        box('brass',(x-side*10,0,589),(6,8,270),solid=False)
        for y in [-42,42]:box('brass',(x-side*12,y,585),(8,8,40),solid=False)
        plaque(x-side*33,0,779,'STAGE '+str(stage),face,28,340,44)
        sphere('red',(x-side*70,155,600),(8,12,16))
        lights.append({'p':[x-side*110,0,730],'power':200,'radius':520,'color':[255,189,125]})
    # The longer north arm reaches the stair; its entrance faces south into the hall.
    # The museum exterior walls enclose its upper and lower arms.
    box('stone',(2110,0,207),(30,2820,414))
    box('stone_dark',(2125,0,25),(35,2845,50))
    box('stone',(1522,-1425,207),(1206,30,414))
    box('stone_dark',(1530,-1440,25),(1225,35,50))
    for a,b in [(300,540),(760,2125)]:
        box('stone',((a+b)/2,1425,207),(b-a,30,414))
        trim_a=a-.3;trim_b=2142.5 if b==2125 else b+.3
        box('stone_dark',((trim_a+trim_b)/2,1440,25),(trim_b-trim_a,35,50))
    box('stone',(650,1425,332),(220,30,164))
    box('stone',(300,1612.5,207),(32,375,414))
    door(650,1425,width=220)
    plaque(650,1410,308,'ACCESS LOCKED',-90,18,240,38)
    for lower,upper in [(-1800,-1425)]:
        middle=(lower+upper)/2
        for a,b in [(lower,middle-110),(middle+110,upper)]:
            b=min(b,-1440)
            box('stone',(935,(a+b)/2,207),(32,b-a,414))
        box('stone',(935,middle,332),(32,220,164))
        box('door',(935,middle,125),(18,220,250))
        for dy in [-110,110]:box('stone_dark',(935,middle+dy,131.25),(44,24,262.5))
        box('stone_dark',(935,middle,275),(44,264,25))
        box('brass',(922,middle+68,123),(6,8,42),solid=False)
        sphere('red',(910,middle+138,158),(7,10,14))
        plaque(926,middle,205,'STAFF ONLY',180,18,180,38)
        plaque(919,middle,308,'ACCESS LOCKED',180,18,240,38)
    for x,y in [(2285,-1200),(2285,-400),(2285,400),(2285,1200),
                (1250,-1612.5),(1850,-1612.5),(700,1612.5),(1250,1612.5),(1850,1612.5)]:
        box('lamp',(x,y,410),(55,24,6),solid=False)
        lights.append({'p':[x,y,310],'power':120,'radius':450,'color':[143,170,190]})
    # Empty central display platform reserved for the separately authored fossil.
    shape('Cylinder','stone_dark',(0,0,35),(720,620,70),solid=True)
    shape('Cylinder','wood',(0,0,73),(670,570,10))
    for i in range(40):
        t0=math.tau*i/40;t1=math.tau*(i+1)/40
        a=(360*math.cos(t0),310*math.sin(t0),0);b=(360*math.cos(t1),310*math.sin(t1),0)
        beam('brass',(a[0],a[1],104),(b[0],b[1],104),3,True)
        cylinder('brass',(a[0],a[1],70),3,68,True)
    # Reception island, benches and plants maintain clear visitor routes.
    cylinder('stone_dark',(0,-950,20),155,40,True)
    cylinder('wood_dark',(0,-950,72),146,100,True)
    cylinder('brass',(0,-950,124),153,10)
    cylinder('linen',(0,-950,131),138,5)
    plaque(0,-1103,91,'NIGHT WATCH',-90,18,180,38)
    # A single stationary v15 preview stands beside reception, clear of the left loop.
    cylinder('stone_dark',(340,-650,8),90,16,True)
    cylinder('brass',(340,-650,17),91,2)
    plaque(340,-740,9,'PATROL MODEL',-90,7,105,14)
    lights.append({'p':[340,-850,230],'power':650,'radius':360,'color':[255,220,182]})
    lights.append({'p':[340,-450,210],'power':400,'radius':320,'color':[217,228,255]})
    lights.append({'p':[530,-650,200],'power':150,'radius':300,'color':[255,220,182]})
    for x,y,yaw in [(-2905,-1100,90),(-2905,0,90),(-2905,1100,90),(-2905,-800,90),(550,-1690,0),(-2905,800,90)]:bench(x,y,yaw)
    for p in [(-2910,-1250),(-2910,1250),(500,-1480),(-2910,-450),(-2910,450)]:plant(*p)
    for x in [-2500,-1500,-500,500,1500]:
        for y in [-1200,-100,1050]:lights.append({'p':[x,y,700],'power':600,'radius':1100,'color':[255,214,162]})
    # UE's +Y-facing camera has screen-right along -X. Preserve the supplied image's
    # left/right room arrangement with positive scales and mirrored orientations.
    for instances in groups.values():
        for item in instances:
            item['p'][0]=-item['p'][0]
            item['r'][1]=180-item['r'][1]
    # Shared railing endpoints must not leave identical surfaces on top of each other.
    for key,instances in groups.items():
        unique={}
        for item in instances:
            identity=tuple(round(v,6) for field in ('p','s','r') for v in item[field])
            unique.setdefault(identity,item)
        groups[key]=list(unique.values())
    for item in lights:item['p'][0]=-item['p'][0]
    for item in signs:
        item['p'][0]=-item['p'][0];item['support'][0]=-item['support'][0];item['yaw']=180-item['yaw']
    return {'groups':groups,'lights':lights,'signs':signs,
            'rooms':[{'name':'A','bounds':[-2390,-850,250,1250]},{'name':'B','bounds':[-2390,-850,-1250,-250]},
                     {'name':'C','bounds':[950,2100,-1410,1410]}],
            'dimensions_cm':[5500,3600],'bounds_plan_cm':[-3000,2500,-1800,1800],
            'upper_floor_cm':450,'upper_gallery_inner_bounds':[-2430,2110,-1430,1430],'stair_width_cm':600,
            'gallery_rail_bounds':[-2450,2130,-1460,1460],'gallery_rail_setback_cm':20,
            'rail_posts_grounded':True,'rail_baseplate_radius_cm':7,
            'stair_rear_bay_filled':True,'stair_rear_fill_bounds_cm':[-300,300,1400,1767.5,0,414],
            'upper_gallery_inward_extensions':False,
            'staff_corridor_floor':1,'staff_corridor_shape':'reverse_C_open_to_hall',
            'staff_corridor_segments':[{'side':'lower','bounds':[951,2467.5,-1767.5,-1440]},
                                       {'side':'right','bounds':[2125,2467.5,-1767.5,1767.5]},
                                       {'side':'upper','bounds':[316,2467.5,1440,1767.5]}],
            'staff_entry_centres':[[935,-1612.5],[650,1425]],
            'staff_entry_facings':['west','south'],'north_staff_arm_extension_cm':635,
            'gallery_c_entry_side':'west',
            'gallery_entries':[{'room':'A','position':[-850,750,0],'side':'east'},
                               {'room':'B','position':[-850,-750,0],'side':'east'},
                               {'room':'C','position':[950,0,0],'side':'west'}],
            'stage_doors':[{'stage':2,'side':'left','position':[-3000,0,450],'connected':False},
                           {'stage':3,'side':'right','position':[2500,0,450],'connected':False}],
            'door_locations':5,'open_gallery_entries':3,
            'tyranno_proxy_dimensions_cm':[300,350],'left_route_target_clear_width_cm':450,
            'staff_ceiling_is_upper_gallery_slab':True,'staff_ceiling_underside_cm':414,
            'temporary_exhibit_count':0,
            'patrol_dummy':{'count':1,'position_plan':[340,-650,18],'height_cm':175,'pose':'A','animated':False},
            'signage_style':'brass_framed_surface_mounted_panels',
            'lighting_style':'readable_night_patrol','upper_floor_finish':'world_aligned_stone_tiles_with_inlay',
            'room_floor_finish':'single_surface_basketweave_parquet',
            'player_start':[0,-1470,105],
            'route':[[350,-1400,100],[-740,-1200,100],[-740,-780,100],[-1460,-780,100],[-740,-780,100],
                     [-740,780,100],[-1460,780,100],[-740,780,100],[-740,480,100],[0,520,100],
                     [0,570,100],[0,1510,550],[-2280,1530,550],[-2280,0,550],
                     [-2280,-1530,550],[2280,-1530,550],[2280,0,550],[2280,1530,550],[0,1510,550]]}
