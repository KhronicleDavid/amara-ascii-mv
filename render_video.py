"""Render the actual ASCII film as a 1080p music video, without screen capture.

Example: python render_video.py --output outputs/AMARA-ASCII-MV-1080p.mp4
The terminal artwork is unchanged; video subtitles are typeset more generously
and playback controls are omitted. Rendering never uses a real-time clock.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone,timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import numpy as np
from PIL import Image,ImageDraw,ImageFont

from amara import Film,PALETTE,ROOT
from render_previews import CharacterRenderer,MONO_PATH,CJK_PATH,BACKGROUND


class VideoComposer:
    """Vectorized glyph composition, identical to the preview renderer's ink."""
    def __init__(self,film,columns=192,rows=50):
        self.film,self.columns,self.rows=film,columns,rows
        self.reference=CharacterRenderer(10,21,18)
        self.atlas=np.zeros((128,21,10),dtype=np.uint16)
        for code in range(33,127):
            self.atlas[code]=np.asarray(self.reference.glyph(chr(code)))
        self.palette=np.asarray(PALETTE,dtype=np.uint16)
        self._colored_tiles={}
        self.zh_font=ImageFont.truetype(str(CJK_PATH),32)
        self.en_font=ImageFont.truetype(str(MONO_PATH),24)
        self._subtitle_cache={}

    def layout(self,t):
        c=self.film.frame(t,self.columns,self.rows)
        # Read the divider and captions from the actual player, including the
        # reconnect and final error messages. Do not maintain another timeline.
        divider=next(y for y in range(c.h-2,-1,-1) if all(ch=='-' for ch in c.chars[y]))
        lines=tuple(''.join(row).strip() for row in c.chars[divider+1:c.h-2])
        lines=tuple(line for line in lines if line)
        return c,divider,lines

    def artwork(self,c,art_h):
        codes=np.frombuffer(''.join(''.join(row) for row in c.chars[:art_h]).encode('ascii'),dtype=np.uint8).reshape(art_h,c.w)
        colors=np.asarray(c.colors[:art_h])
        backgrounds=np.asarray([v if v is not None else 0 for v in c.backgrounds[:art_h]])
        ink=np.empty((art_h,c.w,21,10,3),dtype=np.uint8)
        # Blend each glyph/ink/paper combination once. Frames then assemble
        # small cached RGB tiles instead of millions of per-pixel divisions.
        for bg in np.unique(backgrounds):
            bg=int(bg)
            if bg not in self._colored_tiles:
                alpha=self.atlas[None,:,:,:,None]
                foreground=self.palette[:,None,None,None,:]
                self._colored_tiles[bg]=((foreground*alpha+self.palette[bg]*(255-alpha)+127)//255).astype(np.uint8)
            rows=np.flatnonzero(backgrounds==bg)
            ink[rows]=self._colored_tiles[bg][colors[rows],codes[rows]]
        return ink.transpose(0,2,1,3,4).reshape(art_h*21,c.w*10,3)

    def caption(self,lines,width,height):
        key=(lines,width,height)
        if key not in self._subtitle_cache:
            panel=Image.new('RGB',(width,height),BACKGROUND)
            draw=ImageDraw.Draw(panel)
            if lines:
                fonts=[self.zh_font]+[self.en_font]*(len(lines)-1)
                pitch=40 if len(lines)<=2 else min(36,(height-12)//len(lines))
                top=max(5,(height-pitch*len(lines))//2-2)
                for i,(line,font) in enumerate(zip(lines,fonts)):
                    color=PALETTE[4] if i==0 else PALETTE[6]
                    assert draw.textlength(line,font=font)<width-24,'Video subtitle would be cropped'
                    draw.text((width/2,top+i*pitch),line,font=font,anchor='mt',fill=color)
            self._subtitle_cache[key]=np.asarray(panel).copy()
        return self._subtitle_cache[key]

    def frame(self,t):
        c,art_h,lines=self.layout(t)
        art=self.artwork(c,art_h)
        width,height=1920,1080
        if art.shape[1]!=width:raise ValueError('1080p export uses 192 columns')
        result=np.empty((height,width,3),dtype=np.uint8);result[:]=BACKGROUND
        assert art.shape[0]<=height-110
        result[:art.shape[0]]=art
        result[art.shape[0]]=PALETTE[7 if t>=190 else 2]
        rest=height-art.shape[0]-1
        result[art.shape[0]+1:]=self.caption(lines,width,rest)
        return result

    def verify_ink(self,t):
        c,art_h,_=self.layout(t)
        reference=np.asarray(self.reference.render(c))[:art_h*21]
        actual=self.artwork(c,art_h)
        assert np.array_equal(reference,actual),f'Glyph composition mismatch at {t}'


def find_ffmpeg(explicit):
    if explicit:
        path=Path(explicit).resolve()
        if not path.is_file():raise FileNotFoundError(path)
        return str(path)
    path=shutil.which('ffmpeg')
    if path:return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise RuntimeError('请先安装 requirements-render.txt，或用 --ffmpeg 指定完整的 FFmpeg。') from exc


def ffescape(s):return s.replace('\\','\\\\').replace('=','\\=').replace(';','\\;').replace('#','\\#').replace('\n',' ')

def write_chapters(film,start,end,path):
    lines=[';FFMETADATA1','title=ÅMARA · ASCII Music Video','artist=sasakure.UK / KAITO / 初音ミク',
           'comment=Original procedural ASCII animation; bilingual Chinese and English subtitles.']
    extras={'initialize':'文明模拟启动','title':'ÅMARA','gate_launch':'文明闸门',
            'braid_interlude':'判定网络','metabolism':'脊骨神经体',
            'chaos_filament':'混沌 / 丝线 / RECONNECT','unknown_flood':'未知文字侵入',
            'geometry_break':'坐标瓦解','crash_dump':'错误转储','fatal':'严重系统错误'}
    for q in film.director.shots:
        a=max(start,q['start']);b=min(end,q['end'])
        if b<=a:continue
        title=film.subtitles[q['cue']]['zh'] if q['cue'] is not None else extras.get(q['kind'],'间奏')
        lines.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round((a-start)*1000)}',f'END={round((b-start)*1000)}','title='+ffescape(title)])
    path.write_text('\n'.join(lines)+'\n','utf-8')


def srt_stamp(t):
    n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'

def write_srt(film,start,end,path):
    cues=[(c['start'],c['end'],c['zh'],c['en']) for c in film.subtitles]
    cues.extend([(120.70,121.821,'正在重连……','RECONNECTING...'),
                 (190.,film.duration,'这个系统发生了严重错误。','A serious error has occurred in this system.')])
    lines=[];index=0
    for a,b,zh,en in sorted(cues):
        a=max(start,a);b=min(end,b)
        if b<=a:continue
        index+=1;lines.extend([str(index),f'{srt_stamp(a-start)} --> {srt_stamp(b-start)}',zh,en,''])
    path.write_text('\n'.join(lines),'utf-8-sig')


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main(argv=None):
    parser=argparse.ArgumentParser(description='渲染带原音乐与中英字幕的完整ASCII MV')
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/AMARA-ASCII-MV-1080p.mp4')
    parser.add_argument('--ffmpeg')
    parser.add_argument('--fps',type=int,default=30)
    parser.add_argument('--start',type=float,default=0.)
    parser.add_argument('--duration',type=float)
    parser.add_argument('--encoder',choices=['libx264','h264_nvenc'],default='libx264')
    parser.add_argument('--samples-only',action='store_true')
    args=parser.parse_args(argv)
    film=Film();composer=VideoComposer(film)
    samples=[0.,34.,63.6,86.,103.,116.78,120.8,135.2,152.,168.6,181.,193.]
    output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    sample_dir=output.parent/'video-frames';sample_dir.mkdir(exist_ok=True)
    for t in samples:
        composer.verify_ink(t)
        Image.fromarray(composer.frame(t)).save(sample_dir/f'frame-{t:07.3f}.png')
    print('12个画面样本已生成；快速合成与实际终端字形逐像素一致。',flush=True)
    if args.samples_only:return 0
    if output.exists():raise FileExistsError('成品已存在，请指定新的 --output：'+str(output))
    if not 1<=args.fps<=60:raise ValueError('fps必须在1至60之间')
    start=max(0.,args.start);end=min(film.duration,start+args.duration) if args.duration is not None else film.duration
    if end<=start:raise ValueError('渲染区间为空')
    # MP4 rounds the video track to a whole frame; retain the exact audio span.
    length=end-start;frames=max(1,math.floor(length*args.fps+.5))
    ffmpeg=find_ffmpeg(args.ffmpeg)
    handle,temp=tempfile.mkstemp(prefix=output.stem+'-',suffix='.partial.mp4',dir=output.parent);os.close(handle)
    temp=Path(temp);meta=output.with_suffix('.chapters.ffmetadata');write_chapters(film,start,end,meta)
    log_path=output.with_suffix('.render.log')
    command=[ffmpeg,'-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pixel_format','rgb24',
             '-video_size','1920x1080','-framerate',str(args.fps),'-i','pipe:0',
             '-ss',f'{start:.9f}','-i',str(ROOT/'assets/amara.wav'),'-f','ffmetadata','-i',str(meta),
             '-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2','-c:v',args.encoder]
    if args.encoder=='libx264':command+=['-preset','fast','-crf','17']
    else:command+=['-preset','p6','-tune','hq','-rc','vbr','-cq','17','-b:v','0']
    command+=['-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','48000',
              '-t',f'{length:.9f}','-movflags','+faststart','-max_muxing_queue_size','2048',str(temp)]
    began=time.perf_counter();last_log=began
    with log_path.open('wb') as log:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        try:
            for i in range(frames):
                t=min(end-1e-9,start+i/args.fps)
                process.stdin.write(composer.frame(t).tobytes())
                now=time.perf_counter()
                if now-last_log>=10 or i+1==frames:
                    done=(i+1)/frames;elapsed=now-began
                    print(json.dumps({'完成':f'{done:.1%}','歌曲秒':round(t,3),'已用秒':round(elapsed,1),
                                      '预计剩余秒':round(elapsed/max(done,1e-8)*(1-done))},ensure_ascii=False),flush=True)
                    last_log=now
            process.stdin.close()
            code=process.wait()
            if code:raise RuntimeError(f'FFmpeg退出码{code}，见{log_path}')
        except BaseException:
            if process.poll() is None:process.kill();process.wait()
            raise
    temp.rename(output)
    write_srt(film,start,end,output.with_suffix('.bilingual.srt'))
    report={'title':'ÅMARA · ASCII Music Video','resolution':[1920,1080],'fps':args.fps,'frames':frames,
            'source_start':start,'source_end':end,'source_duration':length,'encoder':args.encoder,
            'baked_bilingual_subtitles':True,'chapters':True,'terminal_controls_omitted':True,
            'actual_ascii_glyph_composition_verified':len(samples),'render_seconds':round(time.perf_counter()-began,2),
            'file':output.name,'bytes':output.stat().st_size,'sha256':digest(output),
            'created_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
            'source_sha256':{n:digest(ROOT/n) for n in ['amara.py','cinema.py','revised_scenes.py','kinetic_scenes.py','subtitles.json','render_video.py','render_previews.py']}}
    output.with_suffix('.render.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
