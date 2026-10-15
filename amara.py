"""ÅMARA — an original ASCII music film. Playback needs only Python's stdlib."""
from __future__ import annotations

import argparse
import bisect
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
import unicodedata

ROOT = Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
TAU = math.tau
PALETTE = [
    (7, 11, 20), (40, 55, 72), (83, 114, 140), (45, 220, 234),
    (238, 246, 255), (156, 115, 255), (251, 204, 90), (255, 68, 112),
    (112, 151, 176), (95, 245, 163),
    (246, 247, 246), (216, 224, 226), (158, 170, 174),
    (45, 53, 57), (83, 130, 130),
    (18, 15, 31), (32, 27, 46), (113, 104, 131),
    (184, 180, 194), (193, 220, 224), (57, 61, 90), (92, 91, 113),
    (66, 60, 82), (149, 140, 166), (221, 214, 230),
    (87, 74, 111), (148, 181, 209), (222, 239, 248),
    (210, 174, 236), (30, 23, 43), (131, 126, 153),
    (5, 21, 28), (10, 43, 51), (205, 236, 245),
    (39, 9, 29), (99, 28, 75), (229, 112, 183),
    (249, 208, 158), (70, 158, 183), (16, 7, 11),
    (22, 55, 50), (80, 225, 191), (53, 93, 105),
    (198, 97, 69), (116, 53, 128),
]
from cinema import Director, EXTRAS, RECONNECT_START
SHOTS = EXTRAS[:]


def cell_width(s):
    return sum(0 if unicodedata.combining(ch) else
               2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def clip(s, width):
    out, used = [], 0
    for ch in s:
        n = cell_width(ch)
        if used + n > width:
            break
        out.append(ch)
        used += n
    return "".join(out)


def wrap(s, width):
    """Wrap English at words and Chinese at cells, without breaking wide glyphs."""
    result = []
    while cell_width(s) > width:
        head = clip(s, width)
        cut = len(head)
        space = head.rfind(" ")
        if space > len(head) // 2:
            cut = space
        result.append(s[:cut].rstrip())
        s = s[cut:].lstrip()
    return result + ([s] if s else [])


class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.chars = [[" "] * width for _ in range(height)]
        self.colors = [[0] * width for _ in range(height)]
        self.backgrounds = [None] * height

    def put(self, x, y, char, color=4):
        x, y = round(x), round(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.chars[y][x] = char
            self.colors[y][x] = color

    def text(self, x, y, text, color=4):
        x, y = round(x), round(y)
        for char in text:
            n = cell_width(char)
            if 0 <= x and x + n <= self.w and 0 <= y < self.h:
                self.put(x, y, char, color)
                if n == 2:
                    self.chars[y][x + 1] = ""
                    self.colors[y][x + 1] = color
            x += n

    def center(self, y, text, color=4):
        text = clip(text, self.w - 4)
        self.text((self.w - cell_width(text)) // 2, y, text, color)

    def line(self, x0, y0, x1, y1, char=None, color=3):
        dx, dy = x1 - x0, y1 - y0
        if char is None:
            char = "-" if abs(dx) > 2 * abs(dy) else "|" if abs(dy) > abs(dx) else "\\" if dx * dy > 0 else "/"
        steps = max(1, math.ceil(max(abs(dx), abs(dy))))
        for i in range(steps + 1):
            self.put(x0 + dx * i / steps, y0 + dy * i / steps, char, color)

    def box(self, x, y, w, h, color=3):
        self.line(x, y, x+w, y, "-", color)
        self.line(x, y+h, x+w, y+h, "-", color)
        self.line(x, y, x, y+h, "|", color)
        self.line(x+w, y, x+w, y+h, "|", color)
        for xx in [x, x+w]:
            for yy in [y, y+h]:
                self.put(xx, yy, "+", color)

    def ellipse(self, cx, cy, rx, ry, color=3, phase=0, char=".", steps=180):
        for i in range(steps):
            a = TAU * i / steps
            self.put(cx + rx * math.cos(a), cy + ry * math.sin(a + phase), char, color)

    def plain(self):
        return "\n".join("".join(row) for row in self.chars)

    def ansi(self, color=True):
        rows = []
        for y in range(self.h):
            row, prev = [], -1
            if color:
                bg=PALETTE[self.backgrounds[y]] if self.backgrounds[y] is not None else (7,11,20)
                row.append(f"\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m")
            for x in range(self.w):
                ch, c = self.chars[y][x], self.colors[y][x]
                if not ch:
                    continue
                if color and c != prev:
                    r, g, b = PALETTE[c]
                    row.append(f"\x1b[38;2;{r};{g};{b}m")
                    prev = c
                row.append(ch)
            rows.append("".join(row))
        return "\r\n".join(rows)


class Film:
    def __init__(self):
        global SHOTS
        self.analysis=json.loads((ROOT/'assets/analysis.json').read_text('utf-8'))
        self.subtitles=json.loads((ROOT/'subtitles.json').read_text('utf-8'))['cues']
        self.starts=[q['start'] for q in self.subtitles]
        self.duration=self.analysis['duration']
        self.director=Director(self.subtitles,self.duration)
        SHOTS=[(q['start'],q['kind'],q['action']) for q in self.director.shots]
        self.shot_starts=[q[0] for q in SHOTS]

    def cue(self,t):
        i=bisect.bisect_right(self.starts,t)-1
        return self.subtitles[i] if i>=0 and t<self.subtitles[i]['end'] else None

    def features(self,t):
        index=max(0,t/self.analysis['hop_seconds'])
        a=min(int(index),len(self.analysis['energy'])-1)
        b,f=min(a+1,len(self.analysis['energy'])-1),index%1
        return tuple(self.analysis[k][a]*(1-f)+self.analysis[k][b]*f
                     for k in ['energy','bass','high','onset'])

    def shot(self,t):
        return max(0,bisect.bisect_right(self.shot_starts,t)-1)

    def frame(self,t,width=160,height=46,offset=0,paused=False):
        t=max(0,min(self.duration,t))
        c=Canvas(width,height)
        cue=self.cue(t-offset)
        if t>=190:
            zh=['这个系统发生了严重错误。']
            en=wrap('A serious error has occurred in this system.',width-4)
        elif t>=RECONNECT_START and self.director.shot(t)['kind']=='chaos_filament':
            zh=['正在重连……']
            en=['RECONNECTING...']
        else:
            zh=wrap(cue['zh'],width-4) if cue else []
            en=wrap(cue['en'],width-4) if cue else []
        caption_h=max(4,len(zh)+len(en)+2)
        art=Canvas(width,height-caption_h-1)
        self.director.render(art,t,self.features(t))
        for y in range(art.h):
            c.chars[y]=art.chars[y]
            c.colors[y]=art.colors[y]
            c.backgrounds[y]=art.backgrounds[y]
        divider=height-caption_h-1
        c.line(0,divider,width-1,divider,'-',7 if t>=190 else 2)
        row=divider+1
        for line in zh:
            c.center(row,line,4);row+=1
        for line in en:
            c.center(row,line,6 if t<190 else 7);row+=1
        clock=f"{int(t)//60:02}:{t%60:05.2f} / {int(self.duration)//60:02}:{self.duration%60:05.2f}"
        c.text(1,height-1,clock+'  '+('PAUSED' if paused else 'PLAY'),8)
        controls='SPACE pause  <- -> seek  R restart  Q quit' if width>=104 else 'SPACE  A/D seek  R  Q'
        c.text(width-1-len(controls),height-1,controls,8)
        return c


class SilentClock:
    def __init__(self,duration):
        self.duration,self.paused=duration,True
        self._at,self._start=0.0,time.perf_counter()
    def position(self):
        return min(self.duration,self._at+(0 if self.paused else time.perf_counter()-self._start))
    def play(self,start=0):
        self._at,self._start,self.paused=start,time.perf_counter(),False
    def pause(self):
        self._at=self.position()
        self.paused=True
    def resume(self):
        self._start,self.paused=time.perf_counter(),False
    def seek(self,t):
        self._at,self._start=max(0,min(self.duration,t)),time.perf_counter()
    def close(self):
        self.pause()


class Terminal:
    def __init__(self):
        self._saved=[]
    def __enter__(self):
        if os.name=="nt":
            import ctypes
            from ctypes import wintypes
            self.kernel=ctypes.WinDLL("kernel32",use_last_error=True)
            self.kernel.GetStdHandle.argtypes=[wintypes.DWORD]
            self.kernel.GetStdHandle.restype=wintypes.HANDLE
            self.kernel.GetConsoleMode.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
            self.kernel.SetConsoleMode.argtypes=[wintypes.HANDLE,wintypes.DWORD]
            for n in [-11,-10]:
                handle=self.kernel.GetStdHandle(n & 0xffffffff)
                mode=wintypes.DWORD()
                if self.kernel.GetConsoleMode(handle,ctypes.byref(mode)):
                    self._saved.append((handle,mode.value))
                    value=mode.value|4 if n==-11 else (mode.value|0x80)&~0x40
                    self.kernel.SetConsoleMode(handle,value)
        sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[48;2;7;11;20m\x1b[37m\x1b[2J\x1b[H")
        sys.stdout.flush()
        return self
    def __exit__(self,*args):
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        for handle,mode in self._saved:
            self.kernel.SetConsoleMode(handle,mode)
    def key(self):
        if os.name=="nt":
            import msvcrt
            if msvcrt.kbhit():
                char=msvcrt.getwch()
                if char in ["\x00","\xe0"]:
                    return {"K":"left","M":"right","G":"home"}.get(msvcrt.getwch(),"")
                return char.lower()
        return ""


def validate(film):
    import re
    import statistics
    source=next(ROOT.glob("*.lrc"))
    original=[]
    for line in source.read_text("utf-8-sig").splitlines():
        stamps=re.findall(r"\[(\d+):(\d+\.\d+)\]",line)
        if stamps:
            text=re.sub(r"\[[^]]*\]","",line).strip()
            if text and not any(text.startswith(s) for s in ["ÅMARA","词：","曲："]):
                original.append((float(stamps[0][0])*60+float(stamps[0][1]),
                                 float(stamps[-1][0])*60+float(stamps[-1][1]),text))
    lrc_cues=[q for q in film.subtitles if q.get('source')!='provided_mv']
    assert len(original)==len(lrc_cues),"原始 LRC 字幕数量不匹配"
    for raw,cue in zip(original,lrc_cues):
        assert abs(raw[0]-cue["start"])<1e-6 and abs(raw[1]-cue["end"])<1e-6
        assert raw[2]==cue["ja"] and 0<=cue["start"]<cue["end"]<=film.duration
        assert cue["zh"] and cue["en"]
        assert film.cue(cue["start"]+.00001) is cue
        assert film.cue(cue["end"]+.00001) is not cue
    semantic=[q for q in film.director.shots if q['cue'] is not None]
    assert len(semantic)==len(film.subtitles)
    assert len({q['kind'] for q in semantic})==len(film.subtitles)
    for i,cue in enumerate(film.subtitles):
        assert 0<=cue['start']<cue['end']<=film.duration
        assert cue['ja'] and cue['zh'] and cue['en']
        if i:
            assert film.subtitles[i-1]['end']<=cue['start'],"字幕存在重叠"
        assert film.cue(cue['start']+.00001) is cue
        assert film.cue(cue['end']+.00001) is not cue
        assert film.director.shot((cue['start']+cue['end'])/2)['cue']==i
    samples=[]
    for width,height in [(64,20),(80,23),(120,42),(160,50)]:
        for t in [s[0]+.2 for s in SHOTS]+[film.duration-.02]:
            before=time.perf_counter()
            frame=film.frame(t,width,height)
            samples.append((time.perf_counter()-before)*1000)
            assert len(frame.chars)==height
            assert all(cell_width("".join(row))==width for row in frame.chars)
            art_bottom=height-7
            assert all(ord(ch)<128 for row in frame.chars[2:art_bottom] for ch in row)
    report={"音乐时长":round(film.duration,6),"字幕条数":len(film.subtitles),
            "原始LRC条数":len(original),"MV补充条数":len(film.subtitles)-len(original),
            "镜头数":len(SHOTS),"测试画面数":len(samples),
            "渲染中位耗时_ms":round(statistics.median(samples),2),
            "渲染最高耗时_ms":round(max(samples),2),
            "LRC同步与字幕宽度":"通过","画面ASCII校验":"通过",
            "独立歌词动作":len(semantic),"结尾":"严重系统错误"}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


def main(argv=None):
    for stream in [sys.stdout,sys.stderr]:
        if hasattr(stream,"reconfigure"):
            stream.reconfigure(encoding="utf-8",errors="replace")
    parser=argparse.ArgumentParser(description="ÅMARA：同步中英字幕的终端 ASCII MV")
    parser.add_argument("--start",type=float,default=0,help="从指定秒数播放")
    parser.add_argument("--mute",action="store_true",help="静音预览")
    parser.add_argument("--fps",type=int,default=30,help="帧率，默认 30")
    parser.add_argument("--size",nargs=2,type=int,metavar=("WIDTH","HEIGHT"),help="固定字符画尺寸")
    parser.add_argument("--no-color",action="store_true",help="关闭 ANSI 色彩")
    parser.add_argument("--subtitle-offset",type=float,default=0,help="字幕延迟秒数，负值提前")
    parser.add_argument("--snapshot",type=float,help="导出指定秒数的一帧纯文本")
    parser.add_argument("--output",type=Path,help="快照输出路径")
    parser.add_argument("--check",action="store_true",help="验证素材、歌词同步和渲染")
    parser.add_argument("--duration",type=float,help="仅播放指定秒数，用于短预览")
    parser.add_argument("--headless",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    if args.fps<1 or args.fps>60:
        parser.error("帧率需在 1–60 之间")
    if args.size and (args.size[0]<64 or args.size[1]<20):
        parser.error("字符画至少需要 64 列、20 行")
    if args.duration is not None and args.duration<=0:
        parser.error("预览时长需大于零")
    for value in [args.start,args.subtitle_offset,args.snapshot,args.duration]:
        if value is not None and not math.isfinite(value):
            parser.error("时间参数必须是有限数字")
    if getattr(sys,'frozen',False):
        from bundle_runtime import verify_packaged_assets
        assets,_=verify_packaged_assets(ROOT)
    else:
        from prepare_assets import prepare_assets
        assets,_=prepare_assets()
    film=Film()
    if args.check:
        validate(film)
        return 0
    if args.snapshot is not None:
        width,height=args.size or [160,46]
        text=film.frame(args.snapshot,width,height,args.subtitle_offset).plain()+"\n"
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(text,"utf-8")
            print(f"已保存字符画快照：{args.output.resolve()}")
        else:
            print(text)
        return 0
    if not sys.stdout.isatty() and not args.headless:
        name='AMARA-V2.exe' if getattr(sys,'frozen',False) else 'python amara.py'
        print(f"请在 Windows Terminal 或 PowerShell 窗口中运行：{name}")
        print(f"导出画面可使用：{name} --snapshot 125 --output preview.txt")
        return 1
    if args.mute:
        player=SilentClock(film.duration)
    else:
        from audio import AudioPlayer
        player=AudioPlayer(assets)
    if abs(player.duration-film.duration)>.02:
        player.close()
        raise RuntimeError("音频缓存与分析时长不一致，请运行 python prepare_assets.py --force。")
    start=max(0,min(film.duration-.01,args.start))
    run_start=time.perf_counter()
    last_size=None
    terminal=Terminal()
    try:
        with terminal:
            player.play(start)
            while True:
                before=time.perf_counter()
                key=terminal.key()
                if key in ["q","\x1b"]:
                    break
                elif key==" ":
                    player.resume() if player.paused else player.pause()
                elif key in ["left","a"]:
                    player.seek(player.position()-5)
                elif key in ["right","d"]:
                    player.seek(player.position()+5)
                elif key in ["r","home"]:
                    player.seek(0)
                t=player.position()
                if t>=player.duration-.015:
                    break
                if args.duration and time.perf_counter()-run_start>=args.duration:
                    break
                actual=shutil.get_terminal_size((121,43))
                width,height=args.size or [min(240,actual.columns-1),min(80,actual.lines-1)]
                # Fixed --size remains a maximum so a resized window never scrolls.
                if not args.headless:
                    width=min(width,actual.columns-1)
                    height=min(height,actual.lines-1)
                size=(width,height)
                if size!=last_size:
                    sys.stdout.write("\x1b[2J")
                    last_size=size
                if width<64 or height<20:
                    message="请放大终端窗口（至少 65 列 × 21 行）；空格暂停，Q 退出。"
                    sys.stdout.write("\x1b[H"+clip(message,max(1,width)))
                else:
                    frame=film.frame(t,width,height,args.subtitle_offset,player.paused)
                    if not args.headless:
                        sys.stdout.write("\x1b[H"+frame.ansi(not args.no_color))
                sys.stdout.flush()
                time.sleep(max(0,1/args.fps-(time.perf_counter()-before)))
    finally:
        player.close()
    print("ÅMARA 播放已结束。")
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已停止播放。")
    except (RuntimeError,FileNotFoundError,ValueError) as exc:
        print(f"无法播放：{exc}",file=sys.stderr)
        raise SystemExit(1)
