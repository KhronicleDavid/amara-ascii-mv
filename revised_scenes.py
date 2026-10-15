"""Original procedural revisions: resonance, neural remains and failed vision.

Only standard-library math and Canvas primitives are used during playback.
The supplied MV informs scale and movement; no reference pixels are sampled.
"""
from __future__ import annotations
import math

TAU=math.tau

def clamp(x):
    return max(0,min(1,x))

def smooth(x):
    x=clamp(x)
    return x*x*(3-2*x)

def noise(x,y,seed=0):
    n=(int(x)*374761393+int(y)*668265263+int(seed)*1442695041)&0xffffffff
    n=((n^(n>>13))*1274126177)&0xffffffff
    return ((n^(n>>16))&65535)/65535

def ground(c,t,level=.80):
    """A chalk plain with a low, unframed horizon."""
    line=round(c.h*level)
    for y in range(line,c.h):
        c.backgrounds[y]=10 if y>line else 11
        for x in range(c.w):
            v=math.sin(x*.093+y*.71+t*.2)+math.cos(x*.13-y*.49)
            if noise(x,y,11)>.57:
                c.put(x,y,'.' if v<.3 else '_',11 if y>line+2 else 12)

def pilgrim(c,x,floor,scale=1,color=4):
    """A small armored witness makes the overhead structures feel immense."""
    height=max(5,c.h*.22*scale)
    top=floor-height
    head=max(1,c.w*.013*scale)
    c.ellipse(x,top+1,head,1,color,char='=',steps=32)
    c.line(x-head,top+1,x+head,top+1,'_',3)
    for i in range(2,max(3,round(height*.72))):
        width=max(1,head*(.65+i/height*.8))
        c.line(x-width,top+i,x+width,top+i,'/',color)
        c.put(x-width,top+i,'/',8)
        c.put(x+width,top+i,'\\',color)
    for dx in [-head*.45,head*.45]:
        c.line(x+dx,top+height*.69,x+dx,floor,'|',8)
        c.put(x+dx+1,floor,'_',13 if c.backgrounds[min(c.h-1,round(floor))]==10 else color)

def circuits(c,t,color=42):
    """Dim printed traces, not a readable dashboard behind the scene."""
    for y in range(c.h):
        for x in range(c.w):
            value=noise(x//4,y//2,18)
            if x%13==0 and value>.26:c.put(x,y,'|',color)
            elif y%6==0 and value>.40:c.put(x,y,'-',color)
            elif (x+y*7)%31==0:c.put(x,y,':' if int(t*4+x)%3 else '+',color)

def polygon(c,points,color=4,char=None):
    for a,b in zip(points,points[1:]+points[:1]):
        c.line(*a,*b,char,color)

def nerve(c,x,y,dx,dy,depth,t,color):
    if depth<=0:return
    x1=x+dx;y1=y+dy
    c.line(x,y,x1,y1,color=color)
    c.put(x1,y1,'+' if depth>1 else '.',37)
    turn=math.sin(t+depth)*.18
    nerve(c,x1,y1,dx*.65-dy*(.5+turn),dy*.55+dx*.10,depth-1,t+.8,color)
    nerve(c,x1,y1,dx*.7+dy*.42,dy*.44-dx*.13,depth-1,t-.5,color)

def bonds(c,t,local,p,features):
    w,h=c.w,c.h
    energy,bass,high,onset=features
    c.backgrounds=[31]*h
    # A large blue ceramic membrane gives the conductor a physical volume;
    # the fine surface currents are continuous with the brighter linked ropes.
    for y in range(h):
        for x in range(w):
            dx=(x-w*.5)/(w*.66);dy=(y-h*.14)/(h*.77)
            radius=dx*dx+dy*dy
            if radius<1:
                folds=math.sin(dx*14+dy*8+t*.55)+math.cos(dy*19-dx*6-t*.32)
                char='/\\:=|+'[int(abs(folds)*4)%6]
                col=38 if folds>1.2 else 42 if folds>.05 else 32
                c.put(x,y,char,col)
    # A continuous interlocked conductor occupies more space than the window.
    # Pulses run around both halves and return to the witness through the knot.
    for layer in range(14):
        phase=layer*.12
        for i in range(380):
            a=i/380*TAU
            travel=(a/TAU-local*.33)%1
            glow=travel<.10+.04*energy
            shake=math.sin(a*23+local*21+layer*.8)*(.25+bass*.7)
            x=w*.5+w*(.54+.009*layer)*math.sin(a)+w*.08*math.sin(3*a+phase)
            y=h*.40+h*(.37+.008*layer)*math.sin(2*a+phase)+shake
            depth=math.cos(a+phase)
            glyph='=' if abs(math.cos(a))>.5 else '/' if math.cos(2*a)>0 else '\\'
            color=4 if glow else 3 if depth>.25 else 38 if depth>-.35 else 42
            c.put(x,y,glyph,color)
    knot_y=h*.44
    for side in [-1,1]:
        nx=w*(.5+side*.25);ny=h*.22
        for radius in range(5):
            c.ellipse(nx,ny,w*(.025+radius*.014),h*(.035+radius*.018),
                      4 if radius==0 else 38,char=':',steps=90)
        for i in range(7):
            x=w*.5+(nx-w*.5)*i/7
            y=knot_y+(ny-knot_y)*i/7+math.sin(local*18-i)*bass
            c.line(x,y,x+(nx-w*.5)/7,y+(ny-knot_y)/7,color=3)
            if (i-int(local*7))%7==0:c.put(x,y,'*',4)
    # An emitted call climbs the tether; a wider, delayed echo comes back.
    c.line(w*.5,h*.84,w*.5,knot_y,'|',38)
    for delay in [0,.48,.94]:
        q=(local*.72-delay)%1
        y=h*.82-q*h*.40
        c.ellipse(w*.5,y,w*(.015+.035*q),h*.027,4 if delay==0 else 3,
                  char='-',steps=70)
    pilgrim(c,w*.5,h*.95,.95)

def neural_spine(c,t,local,p,features):
    w,h=c.w,c.h
    energy,bass,high,onset=features
    c.backgrounds=[39]*h
    ground(c,t,.80)
    surge=smooth((local-11.5)/1.7)
    zoom=1+surge*.24
    # A suspended vertebral machine continues far beyond the right edge.
    # Bone plates and the copper nervous system have independent motion.
    for i in range(34):
        u=i/29
        x=w*(-.055+u*1.12)*zoom
        y=h*(.27-.22*u+.08*math.sin(u*TAU-local*.15))
        thick=h*(.10+.035*math.sin(u*2.7))
        width=w*.029*zoom
        # Chalk-white mass inside each plate, separated by dark articulated
        # joints. This reads as vertebrae rather than a row of thin antennae.
        for yy in range(round(y-thick*1.26),round(y+thick*.35)+1):
            for xx in range(round(x-width*.7),round(x+width*.7)+1):
                dx=(xx-x)/(width*.72)
                dy=(yy-y+thick*.38)/(thick*.90)
                if dx*dx+dy*dy<1:
                    c.put(xx,yy,'MW#'[(xx+yy)%3],4 if dx<.1 else 33)
        for offset in [3,2,1,0]:
            c.line(x-width,y+thick*.50+offset,x+width,y+thick*.30+offset,'#',42 if offset>1 else 8)
        for shell in range(3):
            ry=thick*(.65+shell*.11)
            for j in range(50):
                a=-1.7+j/49*3.4
                xx=x+math.sin(a)*width
                yy=y-math.cos(a)*ry
                pulse=(u-local*.115)%1<.07
                color=4 if shell==0 or pulse else 33 if shell==1 else 8
                if surge>.5 and pulse:color=36
                c.put(xx,yy,'/' if a<0 else '\\',color)
        c.line(x,y,x+w*.012,y-thick*1.45,'|',4)
        if i%5==2:
            dx=w*(.055+.02*math.sin(i))
            nerve(c,x,y+thick*.48,dx,h*.06+math.sin(local*.4+i),4,t+i,43 if surge<.5 else 36)
    # A small cluster of sense organs hangs from the foremost vertebrae.
    for i in range(5):
        x=w*(.038+i*.027);y=h*(.26+.04*math.sin(i*2.1+local*.2))
        c.line(w*.17,h*.30,x,y,color=43)
        c.ellipse(x,y,w*(.013 if i else .026),h*(.024 if i else .047),4,char='o',steps=45)
        c.put(x,y,'-' if int(local*.6+i)%3 else '+',38)
    for i in range(42):
        x=(i*31.7+local*3)%w
        y=h*(.10+.47*noise(i,2,17))+math.sin(local+i)*.4
        if noise(i,1)>.36:c.put(x,y,'.',8)
    pilgrim(c,w*(.51+.012*math.sin(local*.2)),h*.80,1.05)
    # The witness becomes part of the neural circuit before the reality cuts.
    if p>.45:
        q=clamp((p-.45)/.35)
        for i in range(3):
            x=w*.51+math.sin(i+local*.6)*w*.015
            c.line(x,h*.57,x+w*.018,h*(.57-.28*q),'|',38 if i else 37)
    if surge:
        for y in range(round(h*.77)):
            for x in range(w):
                if noise(x//3,y,int(local*19))<surge*.19:
                    c.put(x,y,'/|+=*'[int(noise(x,y,5)*5)%5],36 if (x+y)%4 else 4)

def future_windows(c,t,local,p,features):
    w,h=c.w,c.h
    c.backgrounds=[31]*h
    circuits(c,t,32)
    # Future images inhabit full-height glass leaves. Their hinges close at
    # different moments, leaving slits instead of a shared road to question boxes.
    for i in range(7):
        center=(i+.5)*w/7
        q=smooth((p-i*.055)/.68)
        half=w*.064*max(.015,math.cos(q*math.pi*.5))
        top=h*(.03+.045*(i%3));bottom=h*(.96-.025*(i%2))
        for y in range(round(top),round(bottom)+1):
            for x in range(max(0,round(center-half)),min(w,round(center+half)+1)):
                n=noise((x-center)*3,y,i+13)
                glow=.5+.5*math.sin((y+i*7)*.32-local*3+i)
                ch='.:|=+/01'[int(n*8)%8]
                c.put(x,y,ch,3 if glow>.67 and q<.7 else 38 if q<.82 else 42)
        polygon(c,[(center-half,top),(center+half,top+q*h*.08),
                   (center+half,bottom),(center-half,bottom-q*h*.08)],4 if q<.65 else 38)
        for band in range(4):
            yy=top+(bottom-top)*(band+.5)/4
            c.line(center-half,yy,center+half,yy,'-',5 if q<.5 else 42)
        if q>.95:c.line(center,top,center,bottom,'|',8)
    for i in range(23):
        x=(i*.073*w+local*18)%w;y=(i*.17*h+local*4)%h
        if p>.4:c.put(x,y,'.',38)

def prediction_ribbons(c,t,local,p,features):
    w,h=c.w,c.h
    c.backgrounds=[15]*h
    # Eight timelines emerge from a printer, but a reverse-moving erasure
    # front strips their predictions before they can reach the other side.
    erasure=w*(1.04-.90*smooth(p))
    for ribbon in range(8):
        base=(ribbon+.5)*h/8
        for x in range(w):
            wave=math.sin(x/w*TAU*1.3-local*1.2+ribbon*.8)
            y=base+wave*h*.035
            for dy in [-1,0,1]:
                c.put(x,y+dy,'=' if dy else '#',18 if dy else 4)
            if x<erasure:
                c.put(x,y,'<>01{}'[int(x+local*24+ribbon*3)%6],13)
            elif noise(x,ribbon,8)<p*.7:
                c.put(x,y,' ',0)
                c.put(x,y+1,' ',0)
            if x==round(erasure):c.put(x,y,'|',7)
        if p>.3:
            for piece in range(5):
                x=erasure+piece*w*.11+local*3
                y=base+math.sin(piece+local*3)*h*.05
                c.text(x,y,'..' if piece%2 else '/_',8)
    for cy in [h*.24,h*.76]:
        c.ellipse(w*.035,cy,w*.095,h*.16,8,char=':',steps=120)
        c.ellipse(w*.035,cy,w*.06,h*.105,4,char='=',steps=100)
        for i in range(8):
            a=i*TAU/8+local*2
            c.line(w*.035,cy,w*.035+math.cos(a)*w*.085,cy+math.sin(a)*h*.14,color=38)

def observation_shutter(c,t,local,p,features):
    w,h=c.w,c.h
    c.backgrounds=[0]*h
    opening=.65*(1-smooth(p))+.012
    for y in range(h):
        for x in range(w):
            dx=(x-w*.5)/(w*.52);dy=(y-h*.5)/(h*.66)
            r=math.hypot(dx,dy);a=math.atan2(dy,dx)+local*.43
            sector=int((a/TAU*7)%7)
            edge=opening*(1+.15*math.cos(a*7))
            if r>edge:
                blade=math.sin(a*7+r*8)
                char='|/\\=[]'[int(abs(blade)*6)%6]
                col=18 if blade>.82 else 38 if blade>.23 else 42 if blade>-.45 else 1
                c.put(x,y,char,col)
                if abs(r-edge)<.045:c.put(x,y,'/',4)
            else:
                n=noise(x,y,int(local*9))
                c.put(x,y,'*' if n>.96 else '.' if n>.64 else ' ',3)
    # Probes reflect off the closing boundary; none makes it through.
    for i in range(24):
        a=i*TAU/24+local*.25
        d=.77-(local*.7+i*.13)%1*.17
        x=w*.5+math.cos(a)*w*.52*d;y=h*.5+math.sin(a)*h*.66*d
        c.put(x,y,'+' if i%3 else '*',4 if i%2 else 3)

def hologram(c,t,cx,cy,rx,ry,fracture=0):
    w,h=c.w,c.h
    for y in range(h):
        for x in range(w):
            u=(x-cx)/rx;v=(y-cy)/ry
            a=math.atan2(v,u);r=math.hypot(u,v)
            skin=1+.23*math.sin(a*3+.3)+.10*math.cos(a*5+t*.15)
            if abs(r-skin)<.065:
                c.put(x+fracture*math.sin(y*.8+t*8),y,'/\\:|'[(x+y)%4],3 if y%3 else 4)
            elif r<skin:
                band=y+math.sin(u*2.6+t*.3)*ry*.11
                if abs(math.sin(a*13+r*8))<.08 or abs(math.sin(band*math.pi/5))<.12:
                    c.put(x,y,'.' if y%5 else '-',38 if fracture<1 else 36)
    for side in [-1,1]:
        ex=cx+side*rx*.28;ey=cy-ry*.28
        c.ellipse(ex,ey,rx*.09,ry*.043,4,char='.',steps=50)
        c.line(ex,ey-ry*.035,ex,ey+ry*.035,'|',3)
        c.line(cx+side*rx*.62,cy-ry*.54,cx+side*rx*.77,cy-ry*1.10,color=38)

def wire_flower(c,x,y,rx,ry,t,index=0,split=0):
    for petal in range(5):
        a=petal*TAU/5+t*.15+index*.3
        px=x+math.cos(a)*(rx*.55+split*rx*2)
        py=y+math.sin(a)*(ry*.55+split*ry*2)
        points=[]
        for k in range(5):
            b=a+(k/4-.5)*2.7
            points.append((px+math.cos(b)*rx*.62,py+math.sin(b)*ry*.65))
        polygon(c,points,4 if petal%2 else 3)
        c.put(points[2][0],points[2][1],'+',6)
        c.line(x,y,px,py,':',38)
    c.ellipse(x,y,rx*.26,ry*.30,6,char='@',steps=24)
    c.text(x-1,y,'01' if index%2 else '10',4)

def robot_link(c,a,b,width):
    for i in range(-width,width+1):
        c.line(a[0],a[1]+i,b[0],b[1]+i,'=' if abs(i)==width else '/',4 if abs(i)==width else 42)
    for x,y in [a,b]:
        c.ellipse(x,y,width*2+1,width+1,3,char='o',steps=45)
        c.put(x,y,'+',4)

def bouquet(c,t,local,p,features,corrupt=False):
    w,h=c.w,c.h
    c.backgrounds=[34 if corrupt else 31]*h
    circuits(c,t,35 if corrupt else 32)
    move=smooth((p-.05)/.70)
    if not corrupt:
        hologram(c,t,w*.77,h*.37,w*.34,h*.62)
        shoulder=(-w*.1,h*.91)
        elbow=(w*(.17+.10*move),h*(.91-.12*move))
        wrist=(w*(.31+.23*move),h*(.73-.17*move))
        robot_link(c,shoulder,elbow,max(1,round(h*.032)))
        robot_link(c,elbow,wrist,max(1,round(h*.025)))
        for i in range(3):
            c.line(wrist[0]-w*.025,wrist[1]+i,wrist[0]+w*.06,wrist[1]+i-1,'=',4)
        base=(wrist[0]+w*.035,wrist[1]-1)
        for i in range(5):
            x=base[0]+w*(.025+(i-2)*.047)
            y=base[1]-h*(.20+.085*(1-abs(i-2)/2))
            c.line(*base,x,y,color=41)
            c.line((base[0]+x)/2,(base[1]+y)/2,(base[0]+x)/2+w*.022,(base[1]+y)/2-h*.025,color=3)
            wire_flower(c,x,y,w*.041,h*.066,t,i)
        scan_x=base[0]-w*.12+(local*.17%1)*w*.28
        c.line(scan_x,base[1]-h*.30,scan_x,base[1]+h*.10,'|',38)
        if p>.62:
            for i in range(26):
                q=(p-.62)*2+i/26
                x=base[0]+q*w*.24;y=base[1]-h*.18+math.sin(i*2+t)*h*.08
                c.put(x,y,'+' if i%3 else '*',3)
    else:
        # The second offering is a vertical, two-arm transfer altar. Its flowers
        # disperse up the beam while the receiver's mesh loses registration.
        hologram(c,t,w*.50,h*.11,w*.48,h*.58,max(0,p-.5)*8)
        base=(w*.50,h*(.80-.22*move))
        for side in [-1,1]:
            a=(w*(.5+side*.60),h*.93)
            b=(w*(.5+side*.23),h*.83)
            dest=(base[0]+side*w*.045,base[1]+h*.05)
            robot_link(c,a,b,max(1,round(h*.03)))
            robot_link(c,b,dest,max(1,round(h*.023)))
        for i in range(6):
            c.ellipse(w*.5,h*.86,w*(.12+i*.036),h*(.026+i*.009),5 if i%2 else 3,
                      phase=t*.15,char=':',steps=120)
        split=smooth((p-.56)/.40)
        for i in range(5):
            x=base[0]+(i-2)*w*.057
            y=base[1]-h*(.20+.075*(1-abs(i-2)/2))
            if split<.72:c.line(*base,x,y,color=41)
            wire_flower(c,x,y-split*h*.21,w*.047,h*.073,t,i,split)
        for x in [w*.40,w*.50,w*.60]:
            c.line(x,h*.04,x,base[1],'|',36 if split>.5 else 38)
        for i in range(70):
            if noise(i,2)<split:
                x=w*.5+(noise(i,1)-.5)*w*.37
                y=(base[1]-i*.73-local*9)%max(1,h*.68)
                c.put(x,y,'+01*'[i%4],36 if i%3 else 4)

def poison_hall(c,t,local,p,features,second=False):
    w,h=c.w,c.h
    c.backgrounds=[34 if second else 31]*h
    cx=w*(.68 if second else .50);cy=h*(.27 if second else .39)
    # Etched, closely layered electronics form the two walls. Their reflective
    # edges stay visible behind the expanding poison front.
    for y in range(h):
        depth=abs(y-cy)/h
        edge=w*(.16+.25*depth)
        for x in range(w):
            distance=abs(x-cx)
            if distance>edge:
                pin=(x+int(y*.65))%17
                if pin<3:
                    c.put(x,y,'|' if pin else '[',36 if second else 38)
                elif y%4==0:
                    c.put(x,y,'=',35 if second else 42)
                elif noise(x,y,4)>.87:
                    c.put(x,y,'+',43 if second else 3)
    # Slanted PCB wings and segmented lintels create a hall, rather than a
    # stack of generic boxes. The second hall is viewed from an oblique angle.
    for depth in range(1,13):
        z=((depth+local*1.9)%13)/13
        scale=.025+z*z*1.3
        left=cx-w*.60*scale;right=cx+w*.60*scale
        top=cy-h*.60*scale;bottom=cy+h*.75*scale
        skew=w*.15*scale if second else 0
        col=36 if second and depth%3==0 else 3 if not second and depth%3==0 else 42
        polygon(c,[(left+skew,top),(left-w*.08*scale,bottom),
                   (right-w*.05*scale,bottom+h*.05*scale),(right+skew,top)],col)
        for side in [-1,1]:
            x=cx+side*w*.50*scale
            c.line(x,top,x+skew,bottom,'|',col)
            for pin in range(5):
                yy=top+(bottom-top)*(pin+.5)/5
                c.line(x-side*w*.06*scale,yy,x+side*w*.025*scale,yy,'=',col)
        for floor in range(3):
            yy=cy+h*(.3+floor*.18)*scale
            c.line(left,yy,right,yy,'_',35 if second else 32)
    for rail in range(9):
        c.line(cx,cy,rail*w/8,h,'/' if rail<4 else '\\',35 if second else 42)
    polygon(c,[(cx-w*.08,cy-h*.09),(cx+w*.085,cy-h*.11),
               (cx+w*.11,cy+h*.06),(cx,cy+h*.13),(cx-w*.11,cy+h*.045)],4)
    # Dream poison has a travelling front, fine turbulence and direction.
    # It visibly leaves the distant mouth and invades the foreground electronics.
    front=.07+smooth(p)*1.38
    for y in range(h):
        for x in range(w):
            dx=(x-cx)/(w*.66);dy=(y-cy)/(h*.83)
            radius=math.hypot(dx,dy)
            plume=math.sin(dx*17+dy*9-local*9)+math.sin(dy*22-dx*5+local*7)
            if radius<front and noise(x,y,int(local*16))>.44:
                if plume>.2 or abs(radius-front)<.09:
                    glyph='~:;+=*'[int(abs(plume)*3+x)%6]
                    col=36 if second else 41
                    if plume>1.32:col=4
                    elif plume<.45:col=5 if second else 9
                    c.put(x,y,glyph,col)
    for i in range(110):
        a=i*2.399+local*(.7 if not second else -1.1)
        d=(i*.019+local*.69)%1.25
        if d>front:continue
        x=cx+math.cos(a)*w*.68*d;y=cy+math.sin(a)*h*.84*d
        c.line(x-math.cos(a)*d*4,y-math.sin(a)*d*2,x,y,'~',36 if second else 41)

SCENES={
    'tension_weave':bonds,
    'metabolism':neural_spine,
    'vanishing_future':future_windows,
    'erased_path':prediction_ribbons,
    'no_exit':observation_shutter,
    'offer_hand':bouquet,
    'bouquet_transfer':lambda c,t,l,p,f:bouquet(c,t,l,p,f,True),
    'toxin_corridor':poison_hall,
    'nightmare_artery':lambda c,t,l,p,f:poison_hall(c,t,l,p,f,True),
}

# Physical actions replace the previous row-offset treatments, including the
# moving inscription bands in civil_suspend. Registration stays in one place.
from kinetic_scenes import SCENES as KINETIC_SCENES
SCENES.update(KINETIC_SCENES)

def render_revision(c,t,shot,features):
    fn=SCENES.get(shot['kind'])
    if fn is None:return False
    local=t-shot['start']
    p=clamp(local/max(.01,shot['end']-shot['start']))
    fn(c,t,local,p,features)
    return True
