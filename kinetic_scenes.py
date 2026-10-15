"""Physical scene actions: hinges, engraving, interpretation and fracture.

All geometry is evaluated from the song clock, including the debris. Seeking
to a frame therefore produces exactly the same state as continuous playback.
Playback uses only the Python standard library. Reference video pixels are
never used as materials.
"""
from __future__ import annotations
import math

TAU=math.tau

def clamp(v):return max(0.,min(1.,v))
def smooth(v):
    v=clamp(v);return v*v*(3-2*v)
def rnd(i,j=0):
    n=(int(i)*374761393+int(j)*668265263+97531)&0xffffffff
    n=((n^(n>>13))*1274126177)&0xffffffff
    return ((n^(n>>16))&65535)/65535
def mix(a,b,q):return tuple(x+(y-x)*q for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def spin(v,ax=0.,ay=0.,az=0.):
    x,y,z=v
    y,z=y*math.cos(ax)-z*math.sin(ax),y*math.sin(ax)+z*math.cos(ax)
    x,z=x*math.cos(ay)+z*math.sin(ay),-x*math.sin(ay)+z*math.cos(ay)
    return x*math.cos(az)-y*math.sin(az),x*math.sin(az)+y*math.cos(az),z
def project(c,v):
    x,y,z=v;f=3.6/max(1.3,3.6+z)
    return c.w*(.5+x*.5*f),c.h*(.5+y*.85*f)
def line3(c,a,b,col=4,ch=None):
    c.line(*project(c,a),*project(c,b),ch,col)
def loop3(c,vertices,col=4,ch=None):
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):line3(c,a,b,col,ch)
def ring3(c,cx,cy,z,rx,ry,col=4,angle=0,tilt=0,portion=1):
    pts=[]
    for k in range(81):
        a=k/80*TAU*portion+angle
        pts.append(add((cx,cy,z),spin((math.cos(a)*rx,math.sin(a)*ry,0),tilt)))
    for a,b in zip(pts,pts[1:]):line3(c,a,b,col)

def face(c,vertices,col=42,edge=4,seed=0,material='.:/+=',fill=True):
    """Rasterize a planar convex piece; the outline follows its actual edges."""
    pts=[project(c,v) for v in vertices]
    if fill:
        for i in range(1,len(pts)-1):
            a,b,d=pts[0],pts[i],pts[i+1]
            den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1])
            if abs(den)<.3:continue
            y0=max(0,math.floor(min(a[1],b[1],d[1])));y1=min(c.h-1,math.ceil(max(a[1],b[1],d[1])))
            x0=max(0,math.floor(min(a[0],b[0],d[0])));x1=min(c.w-1,math.ceil(max(a[0],b[0],d[0])))
            for y in range(y0,y1+1):
                for x in range(x0,x1+1):
                    u=((b[1]-d[1])*(x-d[0])+(d[0]-b[0])*(y-d[1]))/den
                    v=((d[1]-a[1])*(x-d[0])+(a[0]-d[0])*(y-d[1]))/den
                    if min(u,v,1-u-v)>=-.005:
                        c.put(x,y,material[(x*3+y*5+seed)%len(material)],col)
    if edge is not None:loop3(c,vertices,edge)

def backdrop(c,t,rose=False):
    c.backgrounds=[34 if rose else 31]*c.h
    # A chamber considerably larger than the terminal, with depth and buttresses.
    for depth in range(5,0,-1):
        z=depth*.65;col=35 if rose else 32
        for s in [-1,1]:
            line3(c,(s*1.22,-.9,z),(s*1.22,.9,z),col)
            line3(c,(s*1.22,-.9,z),(0,-1.2,z),col)
            for k in range(5):
                yy=(k-2)*.25
                line3(c,(s*1.22,yy,z),(s*1.05,yy-.1,z),col)
    for i in range(14):
        x=(i-6.5)*.22
        line3(c,(x,.6,0),(x*.25,.12,3),35 if rose else 42)
    for i in range(60):
        x=rnd(i,2)*2.6-1.3;y=rnd(i,7)*1.5-.75;z=rnd(i,8)*2
        c.put(*project(c,(x,y+math.sin(t*.8+i)*.006,z)),'.',35 if rose else 42)

# Stroke inscriptions, rather than words translated into decorative pixels.
STROKES=[(-.4,-.4,.4,.4),(.4,-.4,-.4,.4),(-.45,0,.45,0),
         (0,-.5,0,.5),(-.4,-.45,.4,-.45),(-.4,.45,.4,.45),
         (-.4,-.45,-.4,.45),(.4,-.45,.4,.45),(-.4,.2,.1,-.3)]

def sign3(c,center,sx,sy,index,col=4,ax=0,ay=0,az=0,unravel=0):
    for j,(a,b,d,e) in enumerate(STROKES):
        if rnd(index,j)<.36:continue
        move=unravel*(.25+rnd(index+j,12))
        offset=((rnd(index,j+20)-.5)*move,move*(rnd(j,index)-.5),-move*.3)
        a3=add(center,add(spin((a*sx,b*sy,0),ax,ay,az),offset))
        b3=add(center,add(spin((d*sx,e*sy,0),ax,ay,az+unravel*.8),offset))
        line3(c,a3,b3,col)

def flakes(c,p,count=80,seed=2,col=4,gravity=1):
    """Ballistic sparks with different launch times; no wrapped coordinates."""
    for i in range(count):
        age=max(0,p-rnd(i,seed)*.45)
        if age<=0:continue
        a=rnd(i,seed+1)*TAU;v=.3+rnd(i,seed+2)*2
        center=(math.cos(a)*age*v,math.sin(a)*age*v*.7+age*age*gravity,-age*rnd(i,seed+3)*1.8)
        x,y=project(c,center)
        tail=project(c,(center[0]-math.cos(a)*age*.10,center[1]-math.sin(a)*age*.06,center[2]))
        c.line(*tail,x,y,'.' if i%4 else '*',col if i%3 else 7)

def festival(c,t,local,p,features):
    """A ceremonial wheel splits at its hub, then breaks into solid shards."""
    backdrop(c,t,True)
    w,h=c.w,c.h
    charge=smooth(p/.25);fracture=smooth((p-.22)/.25)
    # The ritual has an altar, suspension cables, a hub and radial stained glass.
    for s in [-1,1]:
        for j in range(3):
            x=s*(.82+j*.09)
            a=(x,-.8,.3);b=(s*.68,-.23,.1)
            snap=smooth((p-.62-j*.04)/.17)
            if not snap:line3(c,a,b,43)
            else:
                mid=mix(a,b,.50)
                line3(c,a,(mid[0]+s*snap*.15,mid[1]-snap*.08,mid[2]),37)
                line3(c,(mid[0]-s*snap*.11,mid[1]+snap*.15,mid[2]),
                      (b[0]+s*snap*.2,b[1]+snap*snap*.5,b[2]-snap*.3),43)
        for k in range(6):
            ring3(c,s*.96,.46,.15,.15+k*.006,.022,36)
    for k in range(6):
        size=.40+k*.105;y=.39+k*.044
        for j in range(8):
            left=-size+j*size/4;right=left+size/4
            verts=[(left,y,.4),(right,y,.4),(right+.015,y+.038,.1),(left-.015,y+.038,.1)]
            age=max(0,(p-.55-k*.027-rnd(j,k)*.045)*3)
            if age:
                center=((left+right)/2,y+.019,.25)
                shift=(center[0]*age*.5,age*age*.50,-age*.85)
                verts=[add(add(center,shift),spin(tuple(v[d]-center[d] for d in range(3)),age*(2+j*.1),age*(j-3)*.5)) for v in verts]
            face(c,verts,35,37 if age else 43,k,'_:=')
    # Small floor witnesses are dwarfed by the wheel.
    for x in [-.65,0,.65]:
        xx,yy=project(c,(x,.43,-.1));c.text(xx-1,yy-2,'o',37)
        c.text(xx-1,yy-1,'/|',43);c.text(xx-1,yy,'/\\',43)
    shards=[]
    for band in range(3):
        r0=.36+band*.27;r1=r0+.27
        for k in range(20):
            a=k*TAU/20-.5*math.pi;b=(k+1)*TAU/20-.5*math.pi
            verts=[(math.cos(a)*r0,math.sin(a)*r0*.62-.08,.12),
                   (math.cos(a)*r1,math.sin(a)*r1*.62-.08,.12),
                   (math.cos(b)*r1,math.sin(b)*r1*.62-.08,.12),
                   (math.cos(b)*r0,math.sin(b)*r0*.62-.08,.12)]
            center=tuple(sum(v[j] for v in verts)/4 for j in range(3))
            # Cracks travel outward, before each individual piece is released.
            release=.33+band*.075+rnd(k,band)*.055
            age=max(0,(p-release)*2.5)
            drift=(math.cos((a+b)/2)*age*(.40+rnd(k,9)),
                   math.sin((a+b)/2)*age*.36+age*age*.73,
                   -age*(.45+rnd(k,band+70)*1.10))
            rot=(age*(rnd(k,13)-.5)*8,age*(rnd(k,15)-.5)*9,age*(rnd(k,17)-.5)*6)
            moved=[add(add(center,drift),spin(tuple(v[j]-center[j] for j in range(3)),*rot)) for v in verts]
            edge=4 if release-.13<p<release else 37 if k%3==0 or age>.12 else 36
            material=44 if k%5 else 43 if band==1 else 35
            shards.append((sum(v[2] for v in moved)/4,moved,material,edge,k))
    # Painter order means the pieces can tumble past each other, not as rows.
    for _,verts,col,edge,k in sorted(shards,key=lambda item:item[0],reverse=True):
        face(c,verts,col,edge,k,':/X=')
        mid=tuple(sum(v[j] for v in verts)/4 for j in range(3))
        if p<.45:sign3(c,mid,.08,.12,k+31,37)
    # A recognizable mechanical effigy is being regenerated inside the crown.
    # Head, breastplate, limbs and feet break before the wheel around them.
    body=[
        [(-.055,-.29,0),(.055,-.29,0),(.07,-.20,0),(0,-.17,0),(-.07,-.20,0)],
        [(-.075,-.16,0),(.075,-.16,0),(.06,-.035,0),(-.06,-.035,0)],
        [(-.055,-.03,0),(.055,-.03,0),(.045,.025,0),(-.045,.025,0)],
        [(-.085,-.15,0),(-.13,-.13,0),(-.19,-.035,0),(-.15,-.025,0)],
        [(.085,-.15,0),(.13,-.13,0),(.19,-.035,0),(.15,-.025,0)],
        [(-.05,.02,0),(-.005,.02,0),(-.03,.105,0),(-.075,.105,0)],
        [(.005,.02,0),(.05,.02,0),(.075,.105,0),(.03,.105,0)],
        [(-.08,.11,0),(-.025,.11,0),(-.025,.145,0),(-.09,.145,0)],
        [(.025,.11,0),(.08,.11,0),(.09,.145,0),(.025,.145,0)],
    ]
    for i,verts in enumerate(body):
        center=tuple(sum(v[j] for v in verts)/len(verts) for j in range(3))
        age=max(0,(p-.31-i*.009)*2.8)
        shift=((rnd(i,29)-.5)*age*.8,-age*.24+age*age*.72,-.16-age*1.4)
        moved=[add(add(center,shift),spin(tuple(v[j]-center[j] for j in range(3)),age*(i-3),age*3,age*(rnd(i,3)-.5)*7)) for v in verts]
        face(c,moved,33 if i==0 else 38,4 if age<.08 else 37,i,'@#' if i==0 else '/=')
    if p<.33:
        line3(c,(-.044,-.24,-.19),(.044,-.24,-.19),3,'=')
        line3(c,(0,-.14,-.19),(0,-.04,-.19),6,'|')
    if p<.48:
        ring3(c,0,-.08,-.02,.29*(1+charge*.07),.235,4)
        for k in range(8):
            a=k*TAU/8+local*1.1
            line3(c,(math.cos(a)*.27,-.08+math.sin(a)*.22,-.05),
                  (math.cos(a)*.33,-.08+math.sin(a)*.26,-.05),4)
    if fracture:
        # Forked, nonuniform cracks reach the frame edges, then become debris.
        for k in range(9):
            a=k*TAU/9+.1
            end=(math.cos(a)*fracture*1.18,-.08+math.sin(a)*fracture*.75,-.08)
            if p<.59:
                mid=mix((0,-.08,-.08),end,.54)
                mid=(mid[0]+.05*math.sin(k*3),mid[1]-.04,mid[2])
                line3(c,(0,-.08,-.08),mid,4);line3(c,mid,end,7)
        flakes(c,max(0,p-.32)*1.9,105,41,37)
        for i in range(36):
            age=max(0,(p-.40-rnd(i,32)*.24)*2)
            if not age:continue
            a=i*2.399
            center=(math.cos(a)*(.23+age*.73),-.08+math.sin(a)*age*.63+age*age*.26,-age*(.5+rnd(i,12)))
            vertices=[add(center,spin(v,age*6,age*(i%5),age*4)) for v in [(-.025,-.032,0),(.043,-.012,0),(.0,.043,0)]]
            face(c,vertices,36,4,i,'/')
    if .35<p<.46:
        c.center(h*.10,'R E B I R T H   /   R I T E   B R O K E N',37)

def rebirth(c,t,local,p,features):
    """The second rite tries rebuilding; its bridge and sanctuary buckle inward."""
    backdrop(c,t,False)
    # Segmented bridge tiles rise to reconnect, then buckle from its far end.
    pieces=[]
    for row in range(11):
        z=row*.24;wide=.44+row*.035;y=.35
        for side in [-1,1]:
            x=side*wide*.5
            verts=[(x-wide*.48,y,z),(x+wide*.48,y,z),
                   (x+wide*.48,y,z+.22),(x-wide*.48,y,z+.22)]
            build=1-smooth((p-row*.013)/.19)
            fail=max(0,(p-(.30+(10-row)*.025+(.04 if side<0 else 0)))*2.9)
            center=(x,y,z+.11)
            shift=(side*fail*.13,build*.55+fail*fail*.8,-fail*.3)
            moved=[add(add(center,shift),spin(tuple(v[i]-center[i] for i in range(3)),fail*(3+row*.18),side*fail*2,side*fail*.5)) for v in verts]
            pieces.append((sum(v[2] for v in moved)/4,moved,42,4 if fail==0 else 43,row))
    # A spatial rib vault breaks at the keystones; ribs have real joints.
    for rib in range(8):
        z=rib*.37
        for side in [-1,1]:
            for seg in range(5):
                a=side*(math.pi*.15+seg*math.pi*.07)
                b=a+side*math.pi*.066
                verts=[(math.sin(a)*1.15,-math.cos(a)*.73,z),
                       (math.sin(b)*1.15,-math.cos(b)*.73,z),
                       (math.sin(b)*1.22,-math.cos(b)*.78,z+.10),
                       (math.sin(a)*1.22,-math.cos(a)*.78,z+.10)]
                center=tuple(sum(v[j] for v in verts)/4 for j in range(3))
                age=max(0,(p-.34-rib*.027-seg*.018)*2.7)
                shift=(-center[0]*age*.40,age*age*.60,-age*.45)
                moved=[add(add(center,shift),spin(tuple(v[j]-center[j] for j in range(3)),side*age*2,age*3,side*age*2.5)) for v in verts]
                pieces.append((sum(v[2] for v in moved)/4,moved,32,3 if age==0 else 7,seg))
    for _,verts,col,edge,k in sorted(pieces,key=lambda item:item[0],reverse=True):face(c,verts,col,edge,k,'/=+')
    # The attempted regeneration has a physical, continuously shrinking return.
    for k in range(8):
        q=smooth((p-.1-k*.015)/.40)
        ring3(c,0,-.2,2-k*.08,.28*(1-q)+.015,.20*(1-q)+.01,9 if p<.38 else 7,local)
    flakes(c,max(0,p-.40)*1.7,90,89,3)

def inscription(c,t,local,p,features):
    c.backgrounds=[15]*c.h
    # An enormous engraved slab tilts toward the reader. A radial scanner
    # captures each sign; strokes escape in depth instead of sliding as bands.
    tilt=-.22+.30*smooth(p)
    def slab(v):return spin(v,.08,tilt,-.035)
    face(c,[slab(v) for v in [(-1.18,-.63,.16),(1.18,-.63,.16),(1.18,.63,.16),(-1.18,.63,.16)]],22,23,3,':   .')
    for row in range(4):
        for col in range(13):
            idx=row*13+col;cx=(col-6)*.183;cy=(row-1.5)*.29
            detect=clamp(p*1.8-(col/13)*.50-row*.08)
            center=slab((cx,cy,.10))
            sign3(c,center,.115,.20,idx+5,4 if detect<.15 else 28,
                  ay=tilt+detect*1.6,az=detect*(rnd(idx,9)-.5)*2,
                  unravel=max(0,detect-.26)*.65)
            if .08<detect<.32:
                x,y=project(c,center);c.box(x-c.w*.036,y-c.h*.09,c.w*.072,c.h*.18,7)
    for s in [-1,1]:
        a=(s*1.25,-.8,-.10);b=(0,.56-p*1.12,-.12)
        line3(c,a,b,5);line3(c,a,(b[0]+s*.25,b[1],b[2]),23)
    c.center(c.h*.95,'OPTICAL READ / GLYPH ESCAPES CAPTURE',23)

def palimpsest(c,t,local,p,features):
    c.backgrounds=[31]*c.h
    # Three thick leaves, hinged along different edges, reveal different writing.
    for layer in range(2,-1,-1):
        q=0 if layer==2 else smooth((p-layer*.20)/.50)
        hinge=(-1.02,-.60,layer*.10)
        angle=-q*2.35
        def tx(v):
            v=(v[0]-hinge[0],v[1]-hinge[1],v[2]-hinge[2])
            return add(hinge,spin(v,angle if layer%2 else 0,angle if layer%2==0 else 0,0))
        verts=[tx(v) for v in [(-1.02,-.60,layer*.10),(1.12,-.60,layer*.10),(1.12,.65,layer*.10),(-1.02,.65,layer*.10)]]
        face(c,verts,[42,22,35][layer],[4,28,36][layer],layer,'::|/=')
        for row in range(4):
            for col in range(11):
                x=(col-5)*.185;y=(row-1.5)*.26
                for j,(a,b,d,e) in enumerate(STROKES):
                    if rnd(row*11+col+layer*33,j)<.4:continue
                    ink=max(0,p-.62)*2 if layer==2 else 0
                    axis=(row*11+col)*.37
                    left=add((x,y,layer*.10-.012),spin((a*.13,b*.18,0),0,ink*1.6,math.sin(axis)*ink))
                    right=add((x,y,layer*.10-.012),spin((d*.13,e*.18,0),0,ink*1.6,math.sin(axis)*ink))
                    line3(c,tx(left),tx(right),[33,28,37][layer])
        # Severed binding threads recoil and curl away from the opening leaf.
        for j in range(12):
            start=tx((-1.03,j*.102-.55,layer*.10))
            end=(-1.15-q*.10,j*.102-.55+math.sin(local*7+j)*q*.05,.20)
            line3(c,start,end,38 if layer<2 else 43)

def city_decode(c,t,local,p,features):
    c.backgrounds=[0]*c.h
    # Isometric buildings physically feed an optical reader through data cables.
    end=(.43,0,-.15);powered=smooth(p/.62)
    for row in range(4):
        for col in range(6):
            idx=row*6+col;x=-1.10+col*.19;y=.26-row*.12;z=row*.38
            height=.13+rnd(idx,2)*.43
            pts=[(x,y,z),(x+.13,y,z),(x+.13,y-height,z),(x,y-height,z)]
            face(c,pts,42,38,idx,'|:=')
            face(c,[pts[1],add(pts[1],(.06,-.03,.13)),add(pts[2],(.06,-.03,.13)),pts[2]],32,3,idx,'|:')
            lead=(x+.06,y-height,z)
            if powered>idx/35:
                bend=(end[0]-.2,lead[1]*.3,lead[2]*.5)
                line3(c,lead,bend,42);line3(c,bend,end,38)
                packet=(p*3-idx*.08)%1
                c.put(*project(c,mix(lead,end,packet)),'*',4)
    # Gimbals cannot lock onto the alien glyph; the rejected form rotates away.
    for k in range(5):
        ring3(c,.48,0,-.10+k*.07,.31+k*.045,.41+k*.04,3 if k%2 else 5,local*.5,math.sin(local*2+k)*.6)
    sign3(c,(.49,0,-.25),.35,.55,177,4,ay=local*2.3,az=local*.7)
    for i in range(5):
        x,y=project(c,(.95,.24-i*.12,0))
        c.text(x,y,'[ ]' if p<.45+i*.07 else '[/]',7 if p>.45 else 8)
    line3(c,(-1.2,.49,0),(1.2,.49,0),8)

def decode_failure(c,t,local,p,features):
    c.backgrounds=[15]*c.h
    nodes=[]
    for i in range(9):
        a=i*TAU/9-math.pi*.5
        release=clamp((p-i*.068-.18)*3)
        center=(math.cos(a)*(.65+release*.22),math.sin(a)*(.41+release*.18),-.1-release*.25)
        nodes.append(center)
        verts=[add(center,spin(v,release*2,release*3,(i-4)*release*.3)) for v in [(-.17,-.10,0),(.17,-.10,0),(.17,.10,0),(-.17,.10,0)]]
        face(c,verts,22,7 if release else 3,i,'01/')
        if not release:sign3(c,center,.17,.12,i+11,4)
    for i in range(9):
        a,b=nodes[i],nodes[(i+1)%9]
        cut=smooth((p-i*.068-.08)/.18)
        line3(c,a,mix(a,b,.5-cut*.45),38)
        line3(c,mix(a,b,.5+cut*.45),b,38)
        if cut:
            m=mix(a,b,.5)
            for k in range(6):
                ang=k*TAU/6+local*3
                line3(c,m,mix(m,(m[0]+math.cos(ang)*.15,m[1]+math.sin(ang)*.10,m[2]-.1),cut),7)
    sign3(c,(0,0,-.25),.6,.65,204,7,ay=p*math.pi,unravel=p*.5)

def civil_grid(c,t,local,p,features):
    c.backgrounds=[31]*c.h
    # A mechanical press crushes a recognizable city into the circuit die.
    crush=smooth((p-.15)/.67)
    for row in range(5,0,-1):
        z=row*.28
        for col in range(11):
            x=(col-5)*.2;top=.29-(.2+rnd(col,row)*.45)*(1-crush*.95)
            face(c,[(x-.065,.32,z),(x+.065,.32,z),(x+.065,top,z),(x-.065,top,z)],32,38,col,'|:')
            if crush>.6:
                line3(c,(x,.30,z),(x,.29,z-.15),7)
    yy=-.83+crush*1.06
    for side in [-1,1]:
        line3(c,(side*1.05,-.9,0),(side*1.05,.55,0),4)
        for k in range(9):
            y=-.8+k*.14
            line3(c,(side*1.12,y,0),(side*1.00,y,0),43)
    face(c,[(-1.02,yy,0),(1.02,yy,0),(1.02,yy+.09,.35),(-1.02,yy+.09,.35)],42,4,3,'#=|')
    face(c,[(-1.1,.38,0),(1.1,.38,0),(1.1,.38,2),(-1.1,.38,2)],32,3,4,'+:.')
    if crush>.63:flakes(c,(crush-.63)*1.8,65,59,6,.4)

def overload(c,t,local,p,features):
    c.backgrounds=[39]*c.h
    # Optical feedback branches from an input to recursive receivers, whose
    # physical diaphragms rupture in order from the centre to the perimeter.
    for depth in range(4,-1,-1):
        count=2**depth
        for i in range(count):
            x=(i+.5)*2.40/count-1.20;y=-.51+depth*.26
            parent=((i//2+.5)*2.40/max(1,count//2)-1.20,y-.26,.15)
            center=(x,y,.15)
            delay=depth*.11
            if p<delay:continue
            if depth:line3(c,parent,center,7 if p>delay+.3 else 3)
            fail=clamp((p-delay-.25)*3)
            radius=.17/(1+depth*.24)
            ring3(c,x,y,.12,radius,radius*.7,7 if fail else 4)
            for k in range(5):
                a=k*TAU/5+fail*2
                start=(x+math.cos(a)*radius*.5,y+math.sin(a)*radius*.4,.08)
                tip=(x+math.cos(a)*radius*(1.2+fail*3),y+math.sin(a)*radius*(.8+fail*2),.02-fail*.4)
                line3(c,start,tip,7 if fail else 38)
    flakes(c,max(0,p-.55)*1.7,120,73,7,.15)

def strata(c,t,local,p,features):
    c.backgrounds=[15]*c.h
    # Excavation into an oblique block of strata, with a boring head and spoil.
    for layer in range(7,-1,-1):
        y=-.55+layer*.15;excavate=smooth((p-layer*.065)/.45)
        verts=[(-1.05,y,0),(1.05,y,0),(1.21,y+.045,.45),(-.89,y+.045,.45)]
        face(c,verts,22 if layer%2 else 25,23,layer,'/::=')
        for col in range(13):
            x=(col-6)*.15
            if abs(x)<excavate*.78:continue
            sign3(c,(x,y-.03,-.015),.11,.09,col+layer*19,28 if layer%2 else 37)
        # Sections fracture and tilt down along the widening excavation.
        for side in [-1,1]:
            age=max(0,(p-layer*.065-.2)*2)
            center=(side*excavate*.72,y,.05)
            poly=[(-.10,-.04,0),(.12,-.04,0),(.15,.07,.1),(-.09,.08,.15)]
            if age:
                moved=[add(add(center,(side*age*.23,age*age*.17,-age*.4)),spin(v,age*3,side*age*2)) for v in poly]
                face(c,moved,25,28,layer,'#/:')
    head=(0,-.61+p*1.10,-.22)
    for k in range(3):ring3(c,*head,.12+k*.035,.03+k*.018,4,local*9,tilt=.6)
    for side in [-1,1]:line3(c,(side*.07,-.9,-.24),(head[0]+side*.07,head[1],head[2]),38)
    flakes(c,p*.7,70,31,28,.8)

def collision(c,t,local,p,features):
    c.backgrounds=[0]*c.h
    converge=smooth(p/.57);broken=max(0,(p-.48)*2)
    # Competing interpretations inhabit perpendicular, tangible glyph cages.
    for side in [-1,1]:
        center=(side*(1.05-.91*converge),0,.05)
        angle=side*(.6+converge*.8+broken*2)
        for j in range(7):
            x=(j-3)*.13
            v=add(center,spin((x,0,0),.18,angle,side*.12))
            sign3(c,v,.12,.75,33+j+side*9,3 if side<0 else 7,ay=angle,az=side*.12,unravel=broken*.7)
        verts=[add(center,spin(v,.18,angle,side*.12)) for v in [(-.53,-.48,0),(.53,-.48,0),(.53,.48,0),(-.53,.48,0)]]
        if broken<.4:loop3(c,verts,38 if side<0 else 36)
    if broken:
        for k in range(16):
            a=k*TAU/16
            r=broken*(.3+rnd(k,9))
            poly=[(-.07,-.06,0),(.09,-.04,0),(.01,.09,.02)]
            center=(math.cos(a)*r,math.sin(a)*r*.7,-broken*rnd(k,2))
            face(c,[add(center,spin(v,broken*k*.4,broken*3,broken*k*.2)) for v in poly],42 if k%2 else 35,4,k,'/X')
        ring3(c,0,0,0,broken*1.35,broken*.85,4)
        flakes(c,broken,70,91,4,.2)

def flay(c,t,local,p,features):
    c.backgrounds=[15]*c.h
    # The language membrane is unzipped from the bottom; strips curl in depth
    # and detach, revealing a continuous empty substrate.
    face(c,[(-1.2,-.7,.3),(1.2,-.7,.3),(1.2,.7,.3),(-1.2,.7,.3)],22,23,1,' . ')
    for col in range(17):
        x=(col-8)*.145;openq=smooth((p-.025*(col%5))/.79)
        edge=.66-openq*1.38
        for j in range(14):
            y=-.68+j*.1
            if y>edge:continue
            sign3(c,(x,y,.2),.115,.09,col*14+j,4)
        # Five articulated segments form the curled, engraved strip.
        start=(x,edge,.2)
        for k in range(5):
            a=k/5*openq*3.7
            dest=(x+.025*math.sin(col),edge+math.sin(a)*openq*.36,-.05-(1-math.cos(a))*openq*.36)
            if k:
                face(c,[(start[0]-.061,start[1],start[2]),(start[0]+.061,start[1],start[2]),
                        (dest[0]+.061,dest[1],dest[2]),(dest[0]-.061,dest[1],dest[2])],25,28,col+k,'/01')
            start=dest
        if openq>.68:
            q=(openq-.68)*2
            sign3(c,(x+q*math.sin(col)*.16,edge+q*q*.6,-q*.7),.12,.16,col+33,28,ax=q*3,az=q*col)

def cut_fantasy(c,t,local,p,features):
    c.backgrounds=[31]*c.h
    # A mirrored shell is cut along a branching diagonal and opens like teeth.
    for row in range(5):
        for col in range(10):
            x=-1.2+col*.24;y=-.69+row*.27
            q=smooth((p-.10-rnd(col,row)*.16)/.65)
            side=-1 if col<5 else 1
            center=(x+.12,y+.135,.12)
            rot=side*q*(1.4+.2*(row%2))
            pts=[(-.12,-.135,0),(.12,-.135,0),(.12,.135,0),(-.12,.135,0)]
            moved=[add(add(center,(side*q*.13,q*q*.14,-q*.18)),spin(v,q*.3,rot,q*(row-2)*.1)) for v in pts]
            face(c,moved,32 if (col+row)%2 else 42,4,col,'/:=')
            if q<.7:sign3(c,center,.18,.19,col+row*10,3,ay=rot)
    for k in range(15):
        y=-.7+k*.1;x=math.sin(k*.8)*.13
        if k/15<p*1.3:line3(c,(x-.03,y,-.1),(x+.07,y+.1,-.1),6)
    if p>.65:sign3(c,(0,0,-.4),.42,.8,81,7,unravel=(p-.65)*.6)

def veil(c,t,local,p,features):
    c.backgrounds=[39]*c.h
    # A woven canopy tears from its central eye; each thread stays attached at
    # an edge and whips back around its own anchor, exposing another dark veil.
    for j in range(20):
        y=(j-9.5)*.072
        for side in [-1,1]:
            release=smooth((p-abs(j-9.5)*.018)/.62)
            anchor=(side*1.28,y,.13)
            tip=(side*(.02+release*1.11),y+math.sin(local*10+j)*release*.15,-release*.6)
            prev=anchor
            for k in range(1,15):
                q=k/14
                v=mix(anchor,tip,q)
                v=(v[0],v[1]+math.sin(q*math.pi)*release*.19*math.sin(local*7+j),v[2])
                line3(c,prev,v,36 if j%3 else 37);prev=v
    for i in range(17):
        x=(i-8)*.14
        line3(c,(x,-.8,.4),(x,.8,.4),35)
        for row in range(6):
            if abs(x)<p*.9:sign3(c,(x,(row-2.5)*.20,.38),.10,.15,i+row*9,44)

def fold(c,t,local,p,features):
    c.backgrounds=[31]*c.h
    # A hinged map closes around a small city; actual perspective foreshortening.
    for col in range(12):
        x=(col-5.5)*.095;height=.12+rnd(col,7)*.22
        face(c,[(x-.03,.20,.3),(x+.03,.20,.3),(x+.03,.20-height,.3),(x-.03,.20-height,.3)],42,3,col,'|:')
    angle=smooth(p)*2.5
    for side in [-1,1]:
        def tx(v):return spin(v,0,side*angle*.5,-side*.015)
        pts=[tx(v) for v in [(0,-.69,0),(side*1.24,-.69,0),(side*1.24,.69,0),(0,.69,0)]]
        face(c,pts,25,28,5,'/::')
        for row in range(5):
            for col in range(6):
                center=tx((side*(.10+col*.2),(row-2)*.25,-.01))
                sign3(c,center,.15,.18,col+row*19,4,ay=side*angle*.5)
    line3(c,(0,-.69,-.02),(0,.69,-.02),6)

def slices(c,t,local,p,features):
    c.backgrounds=[0]*c.h
    # Nine slabs of one volumetric city rotate about separate pivots. They have
    # thickness and visible section faces, rather than displaced screen rows.
    for i in range(8,-1,-1):
        z=(i-4)*.14
        q=smooth((p-i*.018)/.8)
        angle=q*(i-4)*.25
        center=(0,0,z)
        def tx(v):return add((math.sin(i*2)*q*.10,math.cos(i)*q*.09,z),spin(v,.12+q*.3,angle,(i-4)*q*.035))
        for col in range(12):
            x=(col-5.5)*.18;top=.34-(.17+rnd(col,7)*.40)
            pts=[(x-.07,.34,0),(x+.07,.34,0),(x+.07,top,0),(x-.07,top,0)]
            face(c,[tx(v) for v in pts],32 if i%2 else 22,38 if i%2 else 28,col,'|:=')
            face(c,[tx(pts[1]),tx(add(pts[1],(0,0,.08))),tx(add(pts[2],(0,0,.08))),tx(pts[2])],42,4,col,'/')
        loop3(c,[tx(v) for v in [(-1.20,-.60,0),(1.20,-.60,0),(1.20,.50,0),(-1.20,.50,0)]],3 if i%2 else 5)

def spiral(c,t,local,p,features):
    c.backgrounds=[15]*c.h
    # A continuous manuscript curls into a funnel around its observer. Its
    # curvature and width change; a glyph cannot be followed to an outside.
    for j in range(100,0,-1):
        q=j/100;a=q*TAU*3+local*.55
        radius=.12+q*(1.1-.35*p);z=q*1.3
        center=(math.cos(a)*radius,math.sin(a)*radius*.63,z)
        nxt=(math.cos(a+.15)*radius,math.sin(a+.15)*radius*.63,z)
        face(c,[(center[0],center[1]-.07,z),(nxt[0],nxt[1]-.07,z),
                (nxt[0],nxt[1]+.07,z),(center[0],center[1]+.07,z)],25,28,j,'/=')
        if j%3==0:sign3(c,center,.10,.12,j+3,4,ay=a*.25,az=a)
    ring3(c,0,0,-.1,.10,.13,6)

def swap(c,t,local,p,features):
    c.backgrounds=[31]*c.h
    # Two opposed rooms revolve on a common axle, exchange front/back, then
    # change their material. No full-frame reversal or alternating copy.
    angle=smooth(p)*math.pi
    for side in [1,-1]:
        a=angle+(0 if side==1 else math.pi)
        center=(math.cos(a)*.55,math.sin(a)*.15,math.sin(a)*.75)
        color=3 if side==1 else 36
        def tx(v):return add(center,spin(v,0,a))
        for z in [.0,.30]:
            loop3(c,[tx(v) for v in [(-.48,-.50,z),(.48,-.50,z),(.48,.50,z),(-.48,.50,z)]],color)
        for x in [-.48,.48]:
            for y in [-.50,.50]:line3(c,tx((x,y,0)),tx((x,y,.3)),38)
        for col in range(8):
            x=(col-3.5)*.10;top=.25-(.15+rnd(col,2 if side==1 else 11)*.40)
            face(c,[tx(v) for v in [(x-.035,.25,0),(x+.035,.25,0),(x+.035,top,0),(x-.035,top,0)]],42 if side==1 else 35,color,col,'01' if p<.5 else '/X')
    line3(c,(0,-.9,0),(0,.9,0),4)
    ring3(c,0,0,0,.85,.12,6,angle,tilt=.8)

def stutter(c,t,local,p,features):
    c.backgrounds=[39]*c.h
    # A question is caught in the teeth of a printing mechanism. Each aborted
    # impression becomes a separate hinged card, then a shower of k fragments.
    for side in [-1,1]:
        cx=side*.92
        ring3(c,cx,0,.16,.29,.43,43,local*1.2)
        for i in range(12):
            a=i*TAU/12+local*1.2*side
            line3(c,(cx+math.cos(a)*.20,math.sin(a)*.30,.1),(cx+math.cos(a)*.32,math.sin(a)*.46,.1),37)
    for i in range(11):
        birth=i*.063;age=max(0,p-birth)
        if p<birth:continue
        center=((rnd(i,9)-.5)*age*.7,-.40+age*1.3, .3-age*.8)
        angle=age*(rnd(i,11)-.5)*5
        verts=[add(center,spin(v,age*3,angle,angle*.4)) for v in [(-.38,-.13,0),(.38,-.13,0),(.38,.13,0),(-.38,.13,0)]]
        face(c,verts,35,37,i,'k /')
        sign3(c,center,.32,.18,39,4,ax=age*3,ay=angle)
    for i in range(70):
        age=max(0,p-.38-rnd(i,7)*.40)
        if age:
            pos=((rnd(i,13)-.5)*age*3,-.10+age*age*2,-age*.7)
            c.put(*project(c,pos),'k',6 if i%3 else 7)

def heaven(c,t,local,p,features,invert=False):
    c.backgrounds=[39 if invert else 15]*c.h
    # Articulated vault ribs and attached mosaics; the first night grows along
    # its branches, while the second vault hinges down and loses its keystones.
    for rib in range(7,-1,-1):
        z=rib*.38
        for side in [-1,1]:
            for k in range(9):
                a=side*(k/8*math.pi*.55)
                b=side*((k+.86)/8*math.pi*.55)
                r=1.22
                vertices=[(math.sin(a)*r,-math.cos(a)*.72,z),
                          (math.sin(b)*r,-math.cos(b)*.72,z),
                          (math.sin(b)*(r+.08),-math.cos(b)*.78,z+.09),
                          (math.sin(a)*(r+.08),-math.cos(a)*.78,z+.09)]
                invasion=clamp(p*1.7-rib*.07-k*.045)
                if invert:
                    age=max(0,(p-rib*.04-k*.012-.08)*1.6)
                    pivot=(side*1.22,.10,z)
                    vertices=[add(add(pivot,(0,age*age*.3,-age*.26)),spin(tuple(v[j]-pivot[j] for j in range(3)),age*.4,0,-side*age*2)) for v in vertices]
                face(c,vertices,22 if invasion<.25 else 29,37 if invasion<.25 else 5,rib+k,'/|=')
                if invasion and not invert:
                    mid=tuple(sum(v[j] for v in vertices)/4 for j in range(3))
                    for branch in range(3):
                        end=(mid[0]+math.sin(k+branch)*invasion*.18,mid[1]+invasion*.15,mid[2]-.02)
                        line3(c,mid,end,5)
    for i in range(9):
        z=i*.32;y=.42
        if invert:y+=max(0,p-.3-i*.035)**2*2
        face(c,[(-.43,y,z),(.43,y,z),(.43,y,z+.20),(-.43,y,z+.20)],22,23,i,'_:.')
    if invert:flakes(c,p*.9,95,14,28,.9)

def geometry(c,t,local,p,features):
    c.backgrounds=[0]*c.h
    # A Cartesian lattice has individual welded joints. Cracks propagate in
    # three axes; cells fold inside out and eventually lose all shared edges.
    verts={}
    for z in range(5):
        for y in range(6):
            for x in range(9):
                idx=x+9*y+54*z;delay=rnd(idx,7)*.26+(x+y+z)*.01
                q=smooth((p-delay)/.67)
                base=((x-4)*.30,(y-2.5)*.25,z*.34)
                stretch=spin(base,q*(rnd(z,11)-.5)*2.4,q*(rnd(y,13)-.5)*2.5,q*(rnd(x,9)-.5)*2.2)
                verts[x,y,z]=(stretch[0]+(rnd(idx,8)-.5)*q*.25,
                               stretch[1]+q*q*(rnd(idx,10)-.2)*.42,
                               stretch[2]-q*(rnd(idx,3)*.5))
    for (x,y,z),a in sorted(verts.items(),key=lambda item:item[1][2],reverse=True):
        idx=x+9*y+54*z
        for axis in [(1,0,0),(0,1,0),(0,0,1)]:
            key=(x+axis[0],y+axis[1],z+axis[2]);b=verts.get(key)
            if b is None:continue
            breakq=smooth((p-.25-rnd(idx,sum(axis)+11)*.4)/.25)
            line3(c,a,mix(a,b,.5-breakq*.44),3 if z%2 else 5)
            line3(c,mix(a,b,.5+breakq*.44),b,3 if z%2 else 5)
        c.put(*project(c,a),'+' if p<.5 else '*' if idx%3 else 'X',4 if p<.5 else 7)
    flakes(c,max(0,p-.45)*1.5,90,121,4,.1)

def optic_nerve(c,x,y,dx,dy,depth,t,color):
    if depth<=0:return
    x1=x+dx;y1=y+dy
    c.line(x,y,x1,y1,color=color)
    c.put(x1,y1,'+' if depth>1 else '.',37)
    turn=math.sin(t+depth)*.18
    optic_nerve(c,x1,y1,dx*.65-dy*(.5+turn),dy*.55+dx*.10,depth-1,t+.8,color)
    optic_nerve(c,x1,y1,dx*.7+dy*.42,dy*.44-dx*.13,depth-1,t-.5,color)

def suspend(c,t,local,p,features):
    w,h=c.w,c.h
    energy,bass,high,onset=features
    c.backgrounds=[34]*h
    cx=w*.52;cy=h*.49
    # A nervous cathedral and a deep optic replace numerical progress entirely.
    for y in range(h):
        for x in range(w):
            dx=(x-cx)/(w*.55);dy=(y-cy)/(h*.73)
            r=math.hypot(dx,dy);a=math.atan2(dy,dx)
            fold=math.sin(r*39-a*5+t*1.2)+math.cos(a*19-r*12)
            if r>.25:
                glyph='/\\|=+'[int(abs(fold)*4)%5]
                col=36 if fold>1.7 else 44 if fold>.9 else 35
                c.put(x,y,glyph,col)
            elif rnd(x,y+7)>.7:
                c.put(x,y,'+' if fold>1 else '.',36)
    for ring in range(7):
        rx=w*(.18+ring*.055);ry=h*(.24+ring*.073)
        c.ellipse(cx,cy,rx,ry,36 if ring%2 else 43,phase=.025*math.sin(local+ring),char='/',steps=240)
    c.ellipse(cx,cy,w*.24,h*.34,4,char=':',steps=320)
    c.ellipse(cx,cy,w*.235,h*.33,36,char='/',steps=280)
    for side in [-1,1]:
        xx=w*(.5+side*.43)
        for rib in range(5):
            x=xx+side*rib*w*.012
            c.line(x,-1,x,h,'|',36 if rib==0 else 43 if rib==4 else 35)
            for level in range(7):
                y=h*(level+.5)/7
                c.line(x,y,x-side*w*.025,y,'=',36)
    for branch in range(11):
        x=w*(branch+.5)/11
        optic_nerve(c,x,-1,(cx-x)*.18,h*.11,4,t+branch,36)
    for ray in range(40):
        a=ray*TAU/40+local*.12
        c.line(cx+math.cos(a)*w*.04,cy+math.sin(a)*h*.055,
               cx+math.cos(a)*w*.16,cy+math.sin(a)*h*.22,'/',4 if ray%3 else 36)
    # Signs remain anchored in the aperture. The scanner rotates and examines
    # each one; individual strokes hinge, recoil and regrow incompatible forms.
    for row in range(3):
        for col in range(13):
            idx=col+row*13;x=(col-6)*.176;y=(row-1)*.26
            phase=local*.53-idx*.071
            q=.5+.5*math.sin(phase*TAU)
            unravel=smooth((q-.35)/.65)*(.1+.22*p)
            sign3(c,(x,y,-.30),.13,.20,idx+29,4 if q>.64 else 36,
                  ax=math.sin(phase)*.25,ay=unravel*4,az=math.sin(phase*2)*unravel,
                  unravel=unravel)
    for ray in range(4):
        a=local*.7+ray*math.pi*.5
        line3(c,(.06,0,.4),(.06+math.cos(a)*1.20,math.sin(a)*.8,-.40),4)
    if p>.6:flakes(c,(p-.6)*1.5,75,18,36,0)

SCENES={
    'flay_language':flay,'peel_fantasy':cut_fantasy,'veil_cut':veil,
    'fiction_fold':fold,'k_stutter':stutter,'reality_slice':slices,
    'fiction_spiral':spiral,'reality_swap':swap,'inscription_scan':inscription,
    'decoder_city':city_decode,'decode_failure':decode_failure,
    'palimpsest':palimpsest,'civilization_grid':civil_grid,'overload':overload,
    'festival_rupture':festival,'strata_text':strata,'semantic_collision':collision,
    'civil_suspend':suspend,'rebirth_shear':rebirth,
    'heaven_crawl':heaven,'heaven_invert':lambda c,t,l,p,f:heaven(c,t,l,p,f,True),
    'geometry_break':geometry,
}
