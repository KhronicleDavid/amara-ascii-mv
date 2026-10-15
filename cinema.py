"""V2 original direction: a civilization executes what it cannot understand.

All geometry and glyph materials are generated here. No frames of either
reference music video are converted, traced, loaded, or reused at playback.
"""
from __future__ import annotations
import bisect
import math
from revised_scenes import render_revision

TAU = math.tau
CHAOS_START = 112.218
FILAMENT_COLLAPSE = 113.0
FILAMENT_SETTLED = 116.78
RECONNECT_START = 120.70
LETTERS = {
 'A':['01110','11011','11011','11111','11011','11011','11011'],
 'B':['11110','11011','11011','11110','11011','11011','11110'],
 'C':['01111','11000','11000','11000','11000','11000','01111'],
 'D':['11110','11011','11011','11011','11011','11011','11110'],
 'E':['11111','11000','11000','11110','11000','11000','11111'],
 'F':['11111','11000','11000','11110','11000','11000','11000'],
 'G':['01111','11000','11000','11011','11011','11011','01111'],
 'H':['11011','11011','11011','11111','11011','11011','11011'],
 'I':['11111','00100','00100','00100','00100','00100','11111'],
 'J':['00111','00011','00011','00011','11011','11011','01110'],
 'K':['11011','11010','11100','11100','11010','11011','11011'],
 'L':['11000','11000','11000','11000','11000','11000','11111'],
 'M':['11011','11111','11111','10101','10101','11011','11011'],
 'N':['11011','11111','11111','11111','11011','11011','11011'],
 'O':['01110','11011','11011','11011','11011','11011','01110'],
 'P':['11110','11011','11011','11110','11000','11000','11000'],
 'Q':['01110','11011','11011','11011','11111','01110','00011'],
 'R':['11110','11011','11011','11110','11100','11010','11011'],
 'S':['01111','11000','11000','01110','00011','00011','11110'],
 'T':['11111','00100','00100','00100','00100','00100','00100'],
 'U':['11011','11011','11011','11011','11011','11011','01110'],
 'V':['11011','11011','11011','11011','11011','01010','00100'],
 'W':['11011','11011','10101','10101','11111','11111','11011'],
 'X':['11011','11011','01010','00100','01010','11011','11011'],
 'Y':['11011','11011','01010','00100','00100','00100','00100'],
 'Z':['11111','00011','00110','01100','11000','11000','11111'],
 '0':['01110','11011','11111','11011','11011','11011','01110'],
 '1':['00100','01100','00100','00100','00100','00100','01110'],
 '9':['01110','11011','11011','01111','00011','00011','01110'],
 '?':['01110','11011','00011','00110','00100','00000','00100'],
 ':':['00000','00100','00100','00000','00100','00100','00000'],
 '/':['00001','00011','00110','01100','11000','10000','00000'],
 '.':['00000','00000','00000','00000','00000','00110','00110'],
 ' ':['00000']*7,
}

# Separate lettering keeps the central word legible without altering the
# existing giant titles in other scenes.
RECONNECT_FONT = {
 'R':['11110','10001','10001','11110','10100','10010','10001'],
 'E':['11111','10000','10000','11110','10000','10000','11111'],
 'C':['01111','10000','10000','10000','10000','10000','01111'],
 'O':['01110','10001','10001','10001','10001','10001','01110'],
 'N':['10001','11001','11001','10101','10011','10011','10001'],
 'T':['11111','00100','00100','00100','00100','00100','00100'],
}

# Every supplied line has an individual semantic action and its own shot.
CUE_SCENES = [
 ('unknown_boot','未知文字逐列侵入，覆盖初始化结果'),
 ('unknown_pulse','横贯屏幕的九个 X 拉开整个世界'),
 ('devour_worlds','十二个微缩城市被逐个拖入中央吞噬口'),
 ('dragged_core','牵引束将发光的心拖过巨大的行星表面'),
 ('flay_language','语言膜被从下向上解缝，十七条铭文带逐节卷曲，字形脱落并露出空白基底'),
 ('fire_cage','枪击冲击贯穿画面，未知栅栏闭合囚禁'),
 ('moon_row','划桨推动小舟穿过覆盖屏幕的月暗与数据海'),
 ('peel_fantasy','镜面幻想壳被分叉的斜刃切开，五十块镜片绕独立铰链张开，缝中仍是未知符号'),
 ('reverse_wave','反向声波击退来自画面两侧的审判波'),
 ('reality_stack','真实城市与虚构代码争夺同一坐标'),
 ('road_unmapped','向前延伸的道路逐条断裂在未知边界'),
 ('fiction_fold','刻着异文的双叶地图沿中央脊骨合拢，把城市实体包入虚构内部'),
 ('causal_void','因果节点展开却无法连接到任何终点'),
 ('k_stutter','问句卡在双轮印刷机构中，失败压印翻成独立纸卡，随后散落为 k 碎屑'),
 ('tension_weave','巨大的无缝导体互相扣合，呼叫沿羁绊传播，震颤的回声返回下方见证者'),
 ('thought_mill','刻印器把思考逐字压进整屏堡垒'),
 ('delete_name','NAME 被逐列抹除，姓名索引归零'),
 ('meteor_tears','流星与泪的两股洪流将记忆向下掳走'),
 ('glass_cover','巨大玻璃心脏被多层透明封膜笼罩'),
 ('veil_cut','中央遮幕撕开，织线绕各自锚点回弹卷曲，后面仍有不能穿透的第二层记录'),
 ('voice_revolt','玻璃中的生命逆着扩音器的声流穿出'),
 ('reality_slice','同一座立体城市被切成九张带厚度的断面，各自绕不同枢轴翻转，暴露不一致的内部'),
 ('vanishing_future','七扇未来玻璃窗错时合拢，窗内的预演逐个熄灭，只剩无法窥视的细缝'),
 ('fiction_spiral','连续铭文纸带卷成三圈空间漏斗，内壁持续收紧，把观察者围入虚构'),
 ('erased_path','八条预测纸带持续吐出，逆向擦除波把未来记录剥走，纸带成为空白与碎屑'),
 ('reality_swap','两座相反材质的城市房间绕共同转轴交换前后，立面透视与编码随之改变'),
 ('no_exit','巨幅七瓣观测光阑闭合，探测粒子被边界反射，镜头再也看不见那之后'),
 ('wide_x_1','九个 X 巨幅横贯，压过文明解释界面'),
 ('inscription_scan','巨幅石刻倾向读者，双束扫描逐字捕捉；笔画绕轴翻起并逃出识别框'),
 ('decoder_city','二十四栋立体建筑把数据送入光学译码器，异文在万向环内旋转，输出孔逐个落空'),
 ('decode_failure','九级实体译码节点依次失去连接，导线回缩，端点放电，识别单元自行翻散'),
 ('wide_x_2','第二波巨大 X 斜向剪断识别页面'),
 ('palimpsest','三张厚重记录页绕不同书脊翻开，装订线被扯断，每一层暴露互不相同的铭文'),
 ('civilization_grid','文明建筑被机械压床向下碾入电路模具，楼体压扁、基板放电、碎屑从两侧喷出'),
 ('overload','输入沿光学反馈树递归分叉，接收光阑从中心到边缘逐级炸裂，反馈成为放电碎屑'),
 ('living_bus','电路从左右接通，文明脉冲与有机脉冲互相侵入'),
 ('offer_hand','机械臂把电路花束递向透明异形，花瓣被光学扫描，光点进入折射的全息表皮'),
 ('star_gullet','上下巨颚收拢，星流被咽入未知体内'),
 ('toxin_corridor','电路圣堂深处张开喷口，青绿梦毒沿导轨向镜头涌出，污染前景电路'),
 ('festival_rupture','再生光冠围绕机械人形点亮，身体先行碎裂，裂纹穿过三层祭仪；六十块光冠构件多轴翻转、迎面飞散，四十八块祭坛和悬索随后断裂'),
 ('heaven_crawl','夜沿实体穹顶的肋骨与分叉接缝蔓延，逐块吞掉马赛克光面，侵入天国通路'),
 ('wide_x_3','第三波 X 盖住全部庆典，开始接管屏幕'),
 ('strata_text','钻头向下掘开八层倾斜文字地层，断面向两侧翻落，越深入越露出互异铭文'),
 ('civil_dissolve','文明的建筑分解为不能归类的碎字符'),
 ('rejected','理解请求被巨大 REJECTED 盖印退回'),
 ('wide_x_4','第四波未知文字直接撞穿屏幕坐标'),
 ('semantic_collision','两套解释立在垂直字笼中合拢相撞，笔画脱扣，冲击环与独立多面碎片同时炸出'),
 ('civil_suspend','紫红神经巨眼内三十九个铭文锚定原位，旋转光束逐个检视，笔画翻起、反冲并长回互不兼容的新形'),
 ('circuit_seizure','最终电路反向放电，脉冲自激并烧毁连接'),
 ('bouquet_transfer','双机械臂从传输祭坛向上献花，全息花瓣沿光束崩解，透明接收体的网格逐层错位'),
 ('star_collapse','整片星域被反转压缩，光坠入负空间'),
 ('nightmare_artery','斜切的神经数据回廊扭曲，紫红梦毒从偏置喷口喷出并向前景电子结构扩散'),
 ('rebirth_shear','再生桥片尝试抬升接回，失败从远端传来；桥面逐节屈曲翻落，圣堂拱肋从拱心向内折断，无法重建'),
 ('heaven_invert','天国实体拱肋绕柱脚倒扣，拱心失去支撑，阶梯与碎石沿不同深度坠入黑夜'),
]
EXTRAS = [
 (0.0,'initialize','文明模拟开始逐列生成，读取未知输入'),
 (7.698,'title','侵入的字符重新排列成占满屏幕的 AMARA'),
 (12.8,'gate_launch','文明闸门打开，镜头冲入无限结构'),
 (55.285,'braid_interlude','判定网络收紧成覆盖屏幕的束缚织物'),
 (78.638,'metabolism','巨幅脊骨神经体悬过白色旷野，铜色神经传递脉冲，与人影接通后触发绯红反馈'),
 (CHAOS_START,'chaos_filament','前段直接衔接翻卷撕裂的混沌；01:53起由慢到快压缩，01:56.780收成单根丝线；02:00.700中央英文RECONNECT闪烁，周围断线、双向数据包与握手链路逐步恢复，直到下一句歌词'),
 (173.218,'unknown_flood','未知 X 从铭文变成满屏执行权限'),
 (178.0,'geometry_break','三维坐标网的焊点沿三个轴逐级断开，格室各自扭转外翻，连接回缩后变成漂离的错误节点'),
 (184.0,'crash_dump','文明状态倾泻成无法保存的错误转储'),
 (190.0,'fatal','严重系统错误占据屏幕，停止重启'),
]

def make_shots(cues,duration):
    originals=[q for q in cues if q.get('source')!='provided_mv']
    assert len(originals)==len(CUE_SCENES)
    shots=[]
    index=0
    for i,q in enumerate(cues):
        if q.get('source')=='provided_mv':
            assert q.get('scene')=='lightless_plain'
            k,a='lightless_plain','苍白旷野逐渐消散，人影抵抗侵蚀，仍保留自身轮廓'
        else:
            k,a=CUE_SCENES[index]
            index+=1
        shots.append(dict(start=q['start'],end=q['end'],kind=k,action=a,cue=i))
    shots.extend(dict(start=s,kind=k,action=a,cue=None) for s,k,a in EXTRAS)
    shots.sort(key=lambda q:q['start'])
    for i,q in enumerate(shots):
        q.setdefault('end',shots[i+1]['start'] if i+1<len(shots) else duration)
    return shots

def hash01(x,y,seed=0):
    n=(x*374761393+y*668265263+seed*1442695041)&0xffffffff
    n=((n^(n>>13))*1274126177)&0xffffffff
    return ((n^(n>>16))&65535)/65535

def ease(p):
    return p*p*(3-2*p)

class Director:
    def __init__(self,cues,duration):
        self.shots=make_shots(cues,duration)
        self.starts=[q['start'] for q in self.shots]

    def shot(self,t):
        return self.shots[max(0,bisect.bisect_right(self.starts,t)-1)]

    def block_text(self,c,text,x,y,w,h,color=4,material='01',reveal=1,shift=0,font=None):
        """Fractional scaling uses the entire requested width, even at 64 cols."""
        letters=LETTERS if font is None else font
        cols=len(text)*6-1
        for yy in range(max(0,int(y)),min(c.h,math.ceil(y+h))):
            gy=min(6,max(0,int((yy-y)/h*7)))
            for xx in range(max(0,int(x)),min(c.w,math.ceil(x+w))):
                gx=int((xx-x)/w*cols)
                letter,pos=divmod(gx,6)
                if pos<5 and letter<len(text) and gx/cols<=reveal:
                    if letters.get(text[letter],LETTERS['?'])[gy][pos]=='1':
                        glyph=material[(xx+yy*3+shift)%len(material)]
                        c.put(xx,yy,glyph,color)

    def field(self,c,t,mode=0,brightness=1):
        tick=int(t*8)
        for y in range(c.h):
            for x in range(c.w):
                u,v=x/c.w,y/c.h
                if mode==0:
                    val=.5+.28*math.sin(x*.11+math.sin(y*.3)+t*.25)+.21*math.cos(y*.19-x*.03)
                    ch=' .:;=+*01'[min(8,int(val*8))]
                elif mode==1:
                    n=hash01(x//3,y,tick//3)
                    ch='0123456789ABCDEF'[(x+y*7+tick)%16] if n>.34 else ' '
                    val=n
                elif mode==2:
                    val=(math.sin(u*32+v*16-t*.7)+math.cos(v*23+u*4+t*.3)+2)/4
                    ch=' .,:;=xX#@'[min(9,int(val*9))]
                else:
                    val=hash01(x,y,tick)
                    ch=' .:+01/|#'[min(8,int(val*9))]
                c.put(x,y,ch,2 if val>.82 and brightness>0 else 1)

    def city(self,c,t,variant=0,cx=0,cy=0,width=None,height=None):
        width=width or c.w; height=height or c.h
        base=cy+height*.86
        for i in range(max(4,int(width)//8)):
            xx=cx+i*8-(t*2%8 if variant else 0)
            bh=height*(.28+.57*hash01(i,variant,17))
            bw=5+i%3
            for y in range(max(0,int(base-bh)),min(c.h,int(base))):
                for x in range(max(0,int(xx)),min(c.w,int(xx+bw))):
                    ch='|' if x in [int(xx),int(xx+bw)-1] else '=' if (y-int(base-bh))%5==0 else '01'[int(x+y+t)%2]
                    c.put(x,y,ch,3 if x%3==0 else 2)
            c.line(xx,base-bh,xx+bw,base-bh,'_',4)
        for i in range(8):
            y=base+((i+t*.7)%8)**2/64*height*.14
            c.line(cx,y,cx+width,y,'-',2)

    def orb(self,c,t,cx,cy,rx,ry,palette=3,scar=0):
        for yy in range(max(0,int(cy-ry)),min(c.h,math.ceil(cy+ry))):
            dy=(yy-cy)/ry
            for xx in range(max(0,int(cx-rx)),min(c.w,math.ceil(cx+rx))):
                dx=(xx-cx)/rx; d=dx*dx+dy*dy
                if d<=1:
                    z=math.sqrt(1-d); lon=math.atan2(dx,z)+t*.21
                    light=max(0,min(1,z*.8-dx*.25-dy*.2))
                    material=' .:-=+*#@'[min(8,int(light*8))]
                    if abs(math.sin(lon*18+dy*7))<.14:
                        material='01'[xx%2]
                    if scar and abs(dx-dy*.4)<scar:
                        material='X'; light=.7
                    c.put(xx,yy,material,palette if light>.58 else 2 if light>.22 else 1)

    def heart(self,c,t,cx,cy,rx,ry,covered=0):
        for y in range(max(0,int(cy-ry)),min(c.h,int(cy+ry+1))):
            yy=-(y-cy)/ry*1.25
            for x in range(max(0,int(cx-rx)),min(c.w,int(cx+rx+1))):
                xx=(x-cx)/rx*1.25
                d=(xx*xx+yy*yy-1)**3-xx*xx*yy**3
                if d<0:
                    facet=math.sin(xx*11+yy*14+t*.2)*math.cos(xx*6-yy*8)
                    glyph='/\\[]01.:*'[int(abs(facet)*8)%9]
                    color=4 if facet>.5 else 3 if facet>-.4 else 2
                    if y<cy-ry+covered*ry*2:
                        glyph='X' if (x+y)%7==0 else '=';color=5
                    c.put(x,y,glyph,color)

    def rays(self,c,cx,cy,t,color=3,count=28):
        for i in range(count):
            a=i*TAU/count+t*.09
            c.line(cx+math.cos(a)*c.w*.13,cy+math.sin(a)*c.h*.16,
                   cx+math.cos(a)*c.w,cy+math.sin(a)*c.h,color=color)

    def tunnel(self,c,t,p,poison=False,organic=False):
        cx=c.w*(.5+.07*math.sin(t*.6));cy=c.h*.42
        for i in range(19):
            z=((i+t*2.3)%19)/19; f=z*z
            w,h=c.w*f,c.h*f
            skew=math.sin(i*.8+t)*c.w*.055*f if organic else 0
            c.box(cx-w*.5+skew,cy-h*.5,w,h,9 if poison and i%3==0 else 3 if i%3==0 else 2)
            if i%2==0:
                c.text(cx-w*.48+skew,cy-h*.45,'/ 0x'+format(i*83,'04X')+' /',5)
        for i in range(17):
            x=i*c.w/16;c.line(cx,cy,x,c.h,'/',2)
        if poison:
            for i in range(16):
                a=i*2.399+t*.9
                d=(.08+(i*.17+p*.9)%1.2)
                x=cx+math.cos(a)*c.w*.5*d;y=cy+math.sin(a)*c.h*.6*d
                c.text(x,y,'~0~x~' if organic else '::TOX::',7 if organic else 9)

    def wide_x(self,c,t,p,variant=0):
        self.field(c,t,1 if variant%2 else 2)
        for y in range(c.h):
            if y%5==0:
                shift=int(math.sin(y+t*3)*5*(variant+1))
                c.text(shift,y,('X0/X1::'*(c.w//7+2))[:c.w],5)
        bands={
            0:[(.22,.54,4)],
            1:[(.04,.40,5),(.56,.40,4)],
            2:[(.34,.33,4)],
            3:[(-.10,.44,5),(.26,.44,4),(.62,.44,5)],
            4:[(.12,.74,4)],
            5:[(-.15,.65,5),(.49,.65,4)],
            6:[(.08,.80,4)],
        }[variant]
        for i,(y,h,color) in enumerate(bands):
            yy=c.h*y+math.sin(t+i)*(.7 if variant<3 else 1.6)
            self.block_text(c,'XXXXXXXXX',-2,yy,c.w+4,c.h*h,color,'X',
                            reveal=max(.04,p) if variant==0 else 1)
        if variant==1:
            gap=c.h*.37*p
            c.line(0,c.h*.5-gap,c.w,c.h*.5-gap,'=',4)
            c.line(0,c.h*.5+gap,c.w,c.h*.5+gap,'=',4)
        if variant in [2,4]:
            c.text(0,int(c.h*.5),'X'*c.w,4)
        # X's reach both screen edges; the center band becomes a censor bar.
        if variant in [3,5,6]:
            y=int(c.h*(.2+.55*p))
            c.text(0,y,'X'*c.w,7)
            c.text(0,min(c.h-1,y+1),'X'*c.w,4)

    def branches(self,c,x,y,length,angle,depth,t,color=9):
        if depth==0:return
        a=angle+math.sin(t*.8+depth)*.08
        xx=x+math.cos(a)*length*2;yy=y+math.sin(a)*length
        c.line(x,y,xx,yy,color=color if depth<4 else 2)
        if depth==1:c.put(xx,yy,'@',6)
        self.branches(c,xx,yy,length*.71,a-.45,depth-1,t,color)
        self.branches(c,xx,yy,length*.7,a+.55,depth-1,t+1,color)

    def flower(self,c,x,y,r,t,fracture=0):
        for i in range(7):
            a=i*TAU/7+t*.09
            px=x+math.cos(a)*r*1.45+fracture*math.cos(a)*r*3
            py=y+math.sin(a)*r*.7+fracture*math.sin(a)*r
            c.ellipse(px,py,r*.9,r*.4,6 if i%2 else 4,char='*',steps=45)
        c.ellipse(x,y,r*.55,r*.25,6,char='@',steps=25)

    def lightless_plain(self,c,t,p,features):
        """Paper-white horizon and a solitary surviving outline, drawn in ASCII."""
        w,h=c.w,c.h
        c.backgrounds=[10]*h
        c.chars=[[' ']*w for _ in range(h)]
        c.colors=[[13]*w for _ in range(h)]
        horizon=h*.77
        # The scale comes from the entire empty world, rather than a framed prop.
        for y in range(int(horizon)-1,h):
            for x in range(w):
                depth=max(0,(y-horizon)/(h-horizon))
                ripple=math.sin(x*.10-t*.9+y*.65)+math.cos(x*.055+y*.83+t*.35)
                if hash01(x,y,7)>.52+p*.2:
                    char='.' if ripple<.2 else '~' if depth<.38 else ':'
                    c.put(x,y,char,11 if depth>.25 else 12)
        for x in range(w):
            y=horizon+math.sin(x*.05+t*.18)*.35
            if x%3:c.put(x,y,'_',11)
        # One original outline: back-facing observer, coat and two planted legs.
        cx=w*.5+math.sin(t*.55)*.3
        top=h*.44
        head_w=max(2,w*.022)
        head_h=max(1,h*.04)
        c.ellipse(cx,top,head_w,head_h,14,char='=',steps=50)
        c.line(cx-head_w*.8,top,cx+head_w*.95,top+head_h,'~',14)
        shoulders=top+head_h+1
        waist=horizon-h*.095
        coat_w=max(3,w*.024)
        for y in range(int(shoulders),int(waist)+1):
            fraction=(y-shoulders)/max(1,waist-shoulders)
            width=coat_w*(.7+.3*fraction)
            for x in range(round(cx-width),round(cx+width)+1):
                c.put(x,y,'/' if x<cx else '\\',11)
            flap=math.sin(t*1.6+fraction*2)*(.5+fraction*.4)
            c.put(cx-width,y,'/',13)
            c.put(cx+width+flap,y,'\\',13)
            if y%2==0:c.put(cx+fraction*1.3,y,'|',12)
        c.line(cx-coat_w,waist,cx+coat_w+1,waist,'_',13)
        for x in [cx-coat_w*.48,cx+coat_w*.45]:
            c.line(x,waist+1,x,horizon,'|',13)
            c.put(x+1,horizon,'_',13)
        # Residual data is carried away while the figure holds its position.
        for i in range(12):
            x=(i*23.4+t*(2+i%3))%w
            y=horizon-2-(i%4)*.55
            if hash01(i,2)>.28+p*.45:
                c.text(x,y,'.' if i%3 else '::',11)
        c.center(h*.93,'H I K A R I   N A K U   M O   A R E',13)
        fade=max(0,min(1,(t-44.5)/.65))
        if fade:
            for y in range(h):
                for x in range(w):
                    if hash01(x,y,18)<fade:c.put(x,y,' ',13)

    def chaos_filament(self,c,t,features):
        """Turbulent sheets accelerate into a filament, then attempt reconnect."""
        w,h=c.w,c.h
        cy=(h-1)//2
        c.backgrounds=[15]*h
        if t>=RECONNECT_START:
            self.reconnect(c,t)
            return
        a=t-CHAOS_START
        energy,bass,high,onset=features
        if t<FILAMENT_SETTLED:
            contraction=max(0,min(1,(t-FILAMENT_COLLAPSE)/
                                    (FILAMENT_SETTLED-FILAMENT_COLLAPSE)))
            # A quartic trajectory starts almost stationary and continuously
            # increases inward speed. The whole volume reaches zero at 116.78.
            squeeze=1-contraction**4
            top=round(cy*(1-squeeze))
            bottom=round(cy+(h-1-cy)*squeeze)
            for row in range(top,bottom+1):
                source_y=cy+(row-cy)/max(.01,squeeze)
                shade=math.sin(source_y*.53+a*5)+math.sin(source_y*.91-a*3.4)
                c.backgrounds[row]=25 if shade>.55 else 22
            tick=int(a*30)
            # Large folded vortices and torn curtains, with much smaller grain
            # inside them. The different scales make chaos a moving volume,
            # rather than an even layer of random punctuation.
            for y in range(h):
                slab=y//max(2,h//8)
                tear=(hash01(slab,tick//4,23)-.5)*w*.21
                drift=math.sin(y*.29+a*4.2)*w*.035
                ny=(y/max(1,h-1)-.5)*1.5-.19*math.cos(a*1.3)
                for x in range(w):
                    u=x+tear+drift
                    v=y+math.sin(x*.052-a*2.9)*h*.13
                    nx=(u/max(1,w-1)-.5)*2+.16*math.sin(a*.8)
                    radius=math.hypot(nx,ny)
                    theta=math.atan2(ny,nx)
                    fold=math.sin(radius*12-theta*3-a*6.1+
                                  math.sin(u*.075-v*.13+a*3)*2.4)
                    curtain=math.sin(u*.91+math.sin(v*.4+a*3.2)*3.9+a*8.3)
                    cross=math.sin(u*.53-v*1.73+a*8.8)
                    grain=hash01(x,y,tick)
                    intensity=.5+.29*fold+.14*curtain+.09*cross
                    intensity+=.055*energy+.04*(grain-.5)
                    if fold>.38:
                        glyph='#%MW'[(x+y+tick//2)%4]
                    elif abs(curtain)>.42:
                        glyph='|/\\I'[(y+x//3+tick//3)%4]
                    elif cross>.45:
                        glyph='+=#*'[(x+2*y+tick)%4]
                    else:
                        glyph='.:;=/\\|+'[min(7,int(grain*8))]
                    color=4 if intensity>.77 else 27 if intensity>.65 else 26 if intensity>.48 else 30 if intensity>.31 else 29
                    if fold>.82 and cross<0:color=28
                    if grain>.975:color=4
                    if grain<.025:glyph=' '
                    target_y=cy+(y-cy)*squeeze
                    c.put(x,target_y,glyph,color)
            # Long competing folds stay legible inside the dense texture.
            # The same accelerating inward mapping captures all of them.
            for strand in range(9):
                for x in range(w):
                    phase=x*.043+a*(2.1+strand%4*.35)+strand*1.7
                    source_y=((strand+.5)*h/9+
                              math.sin(phase)*h*.19+
                              math.cos(phase*1.7+a)*h*.08)%max(1,h-1)
                    glyph='/' if math.cos(phase)>0 else '\\'
                    if contraction>.9:glyph='-'
                    c.put(x,cy+(source_y-cy)*squeeze,glyph,4 if strand%3 else 28)
            if contraction>.985:
                self.filament(c,t,cy)
        else:
            # Low-contrast dust leaves nearly all of the space silent. No
            # secondary traces: only one line survives the dimensional collapse.
            for y in range(h):
                if y==cy:continue
                for x in range(w):
                    n=hash01(x,y,37)
                    if n>.976:
                        c.put(x,y,'.',16)
            self.filament(c,t,cy)

    def reconnect(self,c,t):
        """A dominant English title surrounded by links rebuilding in motion."""
        w,h=c.w,c.h
        elapsed=t-RECONNECT_START
        tick=int(elapsed/.14)
        p=max(0,min(1,elapsed/max(.1,self.shot(t)['end']-RECONNECT_START)))
        phase=min(3,int(p*4))
        inverted=tick%2==0
        bg,ink=(10,13) if inverted else (15,4)
        accent,muted=(14,12) if inverted else (3,8)
        trace=12 if inverted else 20
        c.backgrounds=[bg]*h
        c.colors=[[ink]*w for _ in range(h)]
        title_h=max(7,round(h*.36))
        title_y=(h-title_h)//2
        title_bottom=title_y+title_h
        states=['LINK LOST','RETRY','HANDSHAKE','RESYNC']
        attempt=1+min(2,int(p*3))
        c.center(0,f'{states[phase]}  /  ATTEMPT {attempt:02}',accent)

        # Independent channels send packets toward a shrinking interruption.
        # Their end points join rather than merely changing a status label.
        lanes=max(1,min(4,(title_y-1)//3))
        send=['CARRIER / SEARCH','TX / SYN SENT','CLOCK / DRIFT','ROUTE / RETRY']
        receive=['REMOTE / SCAN','RX / WAIT ACK','CLOCK / UNLOCK','ROUTE / MISSING']
        if phase>=2:
            send=['CARRIER / FOUND','TX / ACK RECEIVED','CLOCK / SYNC','ROUTE / RESOLVE']
            receive=['REMOTE / FOUND','RX / ACK SENT','CLOCK / LOCK','ROUTE / JOINING']
        for lane in range(lanes):
            y=2+lane*3
            yy=y+(lane%2)
            gap=max(0,round(w*.18*(1-p)-lane))
            left=(w-gap)//2
            right=(w+gap)//2
            c.line(0,y,w*.20,y,'.',trace)
            c.line(w*.20,y,w*.25,yy,color=trace)
            c.line(w*.25,yy,left,yy,'-',muted)
            c.line(right,yy,w*.75,yy,'-',muted)
            c.line(w*.75,yy,w*.80,y,color=trace)
            c.line(w*.80,y,w-1,y,'.',trace)
            c.put(left,yy,']' if gap else '+',accent)
            c.put(right,yy,'[' if gap else '+',accent)
            c.text(1,y-1,send[lane] if w>=104 else 'TX / SYN',accent)
            label=receive[lane] if w>=104 else 'RX / ACK' if phase>=2 else 'RX / WAIT'
            c.text(w-len(label)-1,y-1,label,accent)
            packet='[SYN]' if phase<2 else '[ACK]'
            px=3+(elapsed*(27+lane*11))%max(1,left-10)
            qx=right+2+(-elapsed*(33+lane*7))%max(1,w-right-10)
            c.text(px,yy,packet,ink)
            c.text(qx,yy,'[ACK]' if phase>=2 else '<..>',ink)
            if gap>4:c.center(yy,'. .',trace)

        # The lower routing graph starts fragmented; returned acknowledgments
        # progressively close its links before the next circuit lyric.
        room=h-title_bottom
        if room>=8:
            gy=title_bottom+3
            nodes=[(round(w*f),gy+i%2) for i,f in enumerate([.035,.27,.5,.73,.965])]
            names=['LOCAL','RETRY','HANDSHAKE','SYNC','REMOTE']
            for i,((x0,y0),(x1,y1)) in enumerate(zip(nodes,nodes[1:])):
                gap=max(0,(.82-p-i*.06))*.14*w
                mid=(x0+x1)/2
                c.line(x0,y0,mid-gap/2,(y0+y1)/2,'-',trace)
                c.line(mid+gap/2,(y0+y1)/2,x1,y1,'-',trace)
                if gap>2:
                    c.put(mid-gap/2,(y0+y1)/2,'>',accent)
                    c.put(mid+gap/2,(y0+y1)/2,'<',accent)
                packet=((elapsed*1.7+i*.23)%1)
                if phase>=2:packet=1-packet
                c.put(x0+(x1-x0)*packet,y0+(y1-y0)*packet,'*',ink)
            for (x,y),name in zip(nodes,names):
                c.box(x-2,y-1,4,2,accent)
                c.put(x,y,'+' if phase>=2 else '?',ink)
                c.text(x-len(name)//2,y+2,name,muted)
            if room>=13:
                c.text(1,h-6,'CARRIER A / PHASE TRACK',muted)
                c.text(w-25,h-6,'CARRIER B / PHASE TRACK',muted)
                length=max(8,round(w*.32))
                wave='_/-\\_'
                drift=int(elapsed*24)
                for x in range(length):
                    c.put(x+1,h-5,wave[(x+drift)%len(wave)],accent)
                    c.put(w-length-1+x,h-5,
                          wave[(x+drift+3-phase)%len(wave)],accent)
                c.center(h-4,['NO CARRIER ...','SYN >>> RETRY',
                              'SYN >>> ACK <<<','PHASE LOCK / RESYNC'][phase],muted)
            fill=round(p*max(8,w//5))
            bar='['+'='*fill+'.'*(max(8,w//5)-fill)+']'
            c.center(h-2,bar+f'  {round(p*100):02}% / {states[phase]}',accent)
            c.text(1,h-1,f'SYN >>>   RETRY {attempt:02}',muted)
            right_label='<<< ACK / SYNC' if phase>=2 else 'ACK ... / WAIT'
            c.text(w-len(right_label)-1,h-1,right_label,muted)
        else:
            c.center(title_bottom+1,states[phase],accent)
            c.line(0,h-1,w-1,h-1,'.',trace)
            c.text(0,h-1,'TX >>>',accent)
            c.text(w-6,h-1,'<<< RX',accent)

        # Paint the headline last to keep every letter clear of moving packets.
        self.block_text(c,'RECONNECT',w*.02,title_y,w*.96,title_h,
                        ink,'#',font=RECONNECT_FONT)

    def filament(self,c,t,cy):
        """A single near-straight, edge-to-edge thread, with sub-cell flutter."""
        tick=int((t-FILAMENT_COLLAPSE)*13)
        for x in range(c.w):
            grain=hash01(x//2,tick,41)
            glyph='_' if grain>.92 else '.' if grain<.045 else '-'
            shimmer=math.sin(x*.14-t*2.2)+math.sin(x*.043+t*.9)
            color=4 if shimmer>.15 else 18 if shimmer>-.9 else 17
            if hash01(x,tick,51)>.992:color=19
            c.put(x,cy,glyph,color)

    def render(self,c,t,features):
        shot=self.shot(t);kind=shot['kind'];local=t-shot['start']
        p=ease(max(0,min(1,local/max(.14,shot['end']-shot['start']))))
        energy,bass,high,onset=features
        w,h=c.w,c.h;cx,cy=w*.5,h*.5
        if kind=='lightless_plain':
            self.lightless_plain(c,t,p,features)
            return shot
        if kind=='chaos_filament':
            self.chaos_filament(c,t,features)
            return shot
        if render_revision(c,t,shot,features):
            return shot
        self.field(c,t,0 if t<61 else 2 if t<139 else 3)

        if kind in ['unknown_boot','unknown_pulse','wide_x_1','wide_x_2','wide_x_3','wide_x_4','unknown_flood']:
            v=['unknown_boot','unknown_pulse','wide_x_1','wide_x_2','wide_x_3','wide_x_4','unknown_flood'].index(kind)
            self.wide_x(c,t,p,v)
            if kind=='unknown_flood':
                for y in range(h):
                    if y%6==0:c.text(0,y,'XXXXXXXXX/'*(w//10+1),7)
        elif kind=='initialize':
            self.field(c,t,1)
            for y in range(h):
                c.text(0,y,('READ / EXEC /'+format(y*127,'08X')+' / ')*(w//26+1),3)
            self.block_text(c,'BOOT',w*.05,h*.2,w*.9,h*.6,4,'01',reveal=min(1,local*3))
            for x in range(int(w*p),w):
                for y in range(h):c.put(x,y,' ',0)
        elif kind=='title':
            self.field(c,t,1)
            self.block_text(c,'AMARA',0,h*.13,w,h*.57,6,'01#',reveal=min(1,local/.9))
            c.center(h*.79,'DAIMIRAI DENNOU / sasakure.UK',4)
            c.center(h*.88,'CIVILIZATION MODEL : EXECUTING UNKNOWN INPUT',3)
        elif kind in ['gate_launch','architecture']:
            self.tunnel(c,t,p)
            if kind=='architecture':
                for side in [0,1]:
                    for i in range(6):
                        x=side*w*.8-i*w*.025 if side else i*w*.025
                        c.line(x,0,cx,h*.42,color=4)
                        c.text(x,h*.2+i*3,'||01||'*(int(w)//48+1),3)
            if kind=='gate_launch':
                self.block_text(c,'ENTER',w*.15,h*.3,w*.7,h*.3,4,'<>')
        elif kind=='devour_worlds':
            for j in range(3):
                for i in range(4):
                    q=j*4+i;fall=max(0,min(1,p*1.55-q*.05))
                    shrink=1-fall*.92
                    x=(i+.5)*w/4;y=(j+.5)*h/3
                    x=x+(cx-x)*fall;y=y+(cy-y)*fall
                    bw,bh=w*.235*shrink,h*.31*shrink
                    c.box(x-bw/2,y-bh/2,bw,bh,3)
                    self.city(c,t,q,x-bw/2,y-bh/2,bw,bh)
            radius=w*(.08+.13*p)
            for y in range(h):
                for x in range(w):
                    if ((x-cx)/radius)**2+((y-cy)/(h*(.1+.22*p)))**2<1:
                        c.put(x,y,'X' if (x+y)%9==0 else ' ',7)
            c.center(h*.06,'WORLD[0000..FFFF] / CONSUMED',4)
        elif kind=='dragged_core':
            self.orb(c,t,w*.73,cy,w*.58,h*.78,3,.035)
            hx=w*(.12+.42*p);hy=h*(.62-.19*p)
            for i in range(15):
                c.line(0,h*(.1+i*.057),hx,hy,'-',5)
            self.heart(c,t,hx,hy,w*.12,h*.27)
            c.text(w*.58,h*.85,'CORE / UNDER TRACTION',6)
        elif kind=='fire_cage':
            self.block_text(c,'SOMETHING',0,h*.35,w,h*.3,5,'XX')
            for i in range(19):
                x=i*w/18;c.line(x+math.sin(t*14+i)*bass*2,0,x,h,'|',4 if i%3 else 7)
            for i in range(8):c.line(0,i*h/7,w,i*h/7,'=',2)
            for i in range(4):
                rr=((local*5+i)%4)/4
                c.ellipse(w*(.2+i*.2),h*.5,w*.38*rr,h*.55*rr,7,char='#')
            c.center(h*.85,'CAPTURED / NO KNOWN JAILER',6)
        elif kind=='moon_row':
            self.orb(c,t,w*.15,h*.2,w*.56,h*.94,2)
            for y in range(h):
                for x in range(w):
                    if ((x-w*.28)/(w*.54))**2+((y-h*.16)/(h*.94))**2<1:c.put(x,y,' ',0)
            for i in range(13):
                y=h*.45+i*h*.043
                c.text(-int(t*7)%9-9,y,'~.:~~:.'*(w//7+3),3 if i%3==0 else 2)
            x=w*(.2+.56*p);y=h*.64
            c.line(x-w*.09,y,x+w*.09,y,'_',4)
            c.line(x-w*.09,y,x-w*.05,y+h*.1,color=4)
            c.line(x+w*.09,y,x+w*.05,y+h*.1,color=4)
            c.line(x-w*.05,y+h*.1,x+w*.05,y+h*.1,'_',4)
            c.line(x,y-2,x+math.cos(t*4)*w*.1,y+2,color=6)
        elif kind in ['reverse_wave','voice_revolt']:
            for side in [0,1]:
                for i in range(9):c.ellipse(w*side,cy,w*(.05+i*.08),h*(.09+i*.09),2,char=')' if side else '(')
            for i in range(8):
                for x in range(w):
                    a=x/w*TAU*3+t*(3 if kind=='voice_revolt' else -4)
                    y=cy+math.sin(a)*(h*.18*(1+bass))+i-4
                    c.put(x,y,'~' if i%2 else '=',6 if i==3 else 3)
            self.block_text(c,'DEFY',w*.18,h*.25,w*.64,h*.42,4,'><')
        elif kind=='reality_stack':
            self.city(c,t,0)
            self.block_text(c,'REALITY',0,0,w,h*.34,4,'01')
            self.block_text(c,'FICTION',0,h*.62,w,h*.35,5,'/X')
            y=int(h*p);c.line(0,y,w,y,'=',7)
        elif kind in ['road_unmapped','causal_void']:
            v=['road_unmapped','causal_void'].index(kind)
            for i in range(23):
                x=(i+.5)*w/23
                limit=h*(.12+.65*hash01(i,v,12))
                c.line(cx,h,x,limit,'/',3 if i%2 else 5)
                c.box(x-2,limit-1,4,2,7)
                c.text(x-1,limit,'?',4)
                c.put(cx+(x-cx)*p,h+(limit-h)*p,'*',6)
            if v==1:
                self.block_text(c,'NULL',0,h*.04,w,h*.33,4,'0')
            else:c.center(h*.08,'BEYOND / UNMAPPED',6)
        elif kind=='braid_interlude':
            for i in range(36):
                for x in range(w):
                    y=(i+.5)*h/36+math.sin(x/w*TAU*3+t*2+i*.24)*(1+p*2)
                    c.put(x,y,'/' if i%2 else '\\',3 if i%3 else 5)
            for i in range(16):
                x=cx+(i-7.5)*w*(.065-.045*p)
                c.line(x,0,cx,h*.5,'|',4);c.line(cx,h*.5,x,h,'|',4)
            c.center(h*.08,'SEAMLESS / TENSION INCREASING',6)
        elif kind=='thought_mill':
            self.city(c,t,15)
            for i in range(8):
                y=i*h/7;c.line(0,y,w,y,'=',4)
            self.block_text(c,'THOUGHT',0,h*.19,w,h*.42,6,'[]',reveal=p)
            x=w*p;c.line(x,0,x,h,'#',7)
            c.text(1,h*.84,'INSCRIBED / INSCRIBED / INSCRIBED',4)
        elif kind=='delete_name':
            self.block_text(c,'NAME',w*.03,h*.15,w*.94,h*.6,4,'01')
            for x in range(int(w*p)):
                for y in range(h):c.put(x,y,'0' if y%4==0 else '.',2)
            c.center(h*.86,'NAME INDEX = NULL',7)
        elif kind=='meteor_tears':
            self.city(c,t,16,cy=p*h*.6)
            for i in range(100):
                x=(i*37.3+t*38)%w;y=(i*17.23+t*(12 if i%2 else 28))%h
                c.line(x-4,y-2,x,y,'/',4 if i%2 else 3)
            for i in range(13):
                y=(i*11+local*22)%h
                c.ellipse(w*.72,y,w*.11,h*.13,3,char='o',steps=32)
            c.center(h*.07,'MEMORY / SWEPT AWAY',6)
        elif kind=='glass_cover':
            self.heart(c,t,cx,cy,w*.48,h*.57,p)
            for i in range(10):
                y=h*(p+i*.1)%h;c.line(0,y,w,y,'_',4 if i==0 else 5)
        elif kind=='civil_dissolve':
            self.city(c,t,31)
            for x in range(0,w,8):c.line(x,0,x,h,'|',2)
            for y in range(0,h,4):c.line(0,y,w,y,'-',2)
            for y in range(h):
                for x in range(w):
                    if hash01(x,y,5)<p:c.put(x,y,'?X/01'[int(hash01(x,y,1)*5)%5],5)
        elif kind=='rejected':
            self.field(c,t,3)
            for i in range(4):
                c.text(0,i*h/4,'[FAILED] / [UNKNOWN] / '*(w//22+1),5)
            self.block_text(c,'REJECTED',-w*.01,h*(-.4+.61*p),w*1.02,h*.53,7,'X#')
            for i in range(13):
                x=i*w/12;c.line(x,0,w-x,h,'/',4 if i%4==0 else 2)
        elif kind in ['living_bus','circuit_seizure']:
            variant=kind=='circuit_seizure'
            for i in range(24):
                y=(i+.5)*h/24
                for x in range(w):
                    if not variant and abs(x-cx)<w*.5*(1-p):continue
                    phase=x/w*TAU*(3 if variant else 1.3)+t*(5 if variant else 2)+i*.23
                    yy=y+math.sin(phase)*h*.12*(.3+bass)*(1+p if variant else 1)
                    c.put(x,yy,'01+-'[x%4],7 if variant and i%3==0 else 9 if i%2 else 3)
            for i in range(10):
                x=w*(i+.5)/10
                c.line(x,0,x,h,'|',6 if i%3==0 else 2)
            self.block_text(c,'PULSE' if not variant else 'SEIZE',w*.09,h*.3,w*.82,h*.4,4,'#1')
            if variant:
                for i in range(8):c.line(0,i*h/7,w,h-i*h/7,'X',7)
                for i in range(int(p*15)):
                    x=(i*29+int(t*13))%w
                    c.line(x,0,x,h,' ',0)
                    c.line(x+1,0,x+1,h,'X',7)
        elif kind in ['star_gullet','star_collapse']:
            variant=kind=='star_collapse'
            for i in range(180):
                a=i*2.399+t*.2
                d=(.1+hash01(i,3)*.9)*(1-.88*p)
                x=cx+math.cos(a)*w*.65*d;y=cy+math.sin(a)*h*.66*d
                c.line(x,y,x+math.cos(a)*4,y+math.sin(a)*2,'*' if i%7==0 else '.',6 if i%7==0 else 4)
            if not variant:
                jaw=h*(.02+.32*p)
                for x in range(w):
                    teeth=(x//4)%2*3
                    for y in range(int(jaw+teeth)):
                        c.put(x,y,'/\\X#'[(x+y)%4],7 if y>jaw-2 else 2)
                        c.put(x,h-1-y,'/\\X#'[(x+y)%4],7 if y>jaw-2 else 2)
                c.text(w*.34,h*.03,'STAR / INGESTION',6)
            else:
                self.rays(c,cx,cy,t,5,45)
                for y in range(h):
                    for x in range(w):
                        if ((x-cx)/(w*(.07+p*.2)))**2+((y-cy)/(h*(.1+p*.3)))**2<1:c.put(x,y,' ',0)
                c.ellipse(cx,cy,w*(.07+p*.2),h*(.1+p*.3),7,char='X')
        elif kind=='crash_dump':
            self.field(c,t,1)
            for y in range(h):
                addr=(y*4096+int(local*98001))&0xffffffff
                payload=' '.join(format((addr+i*0x9E37)&65535,'04X') for i in range(w//5))
                c.text(0,y,f'{addr:08X}  '+payload,7 if y%5==0 else 3)
            self.block_text(c,'FATAL',0,h*.26,w,h*.5,4,'X')
        elif kind=='fatal':
            for y in range(h):
                for x in range(w):c.put(x,y,' ',0)
            self.block_text(c,'SYSTEM',w*.03,h*.08,w*.94,h*.32,7,'#X')
            self.block_text(c,'ERROR',w*.03,h*.46,w*.94,h*.33,4,'#X')
            c.center(h*.86,'AMARA / UNRECOVERABLE CIVILIZATION STATE',7)
            c.center(h*.95,'RESTART FAILED.  NO VALID RESTORE POINT.',8)
        else:
            raise ValueError('未实现分镜：'+kind)

        return shot
