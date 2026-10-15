"""Decode the exported film and verify frames, audio alignment and duration."""
from pathlib import Path
import argparse,json,math,subprocess,sys,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from render_video import VideoComposer,Film,find_ffmpeg,CJK_PATH,digest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('video',type=Path);parser.add_argument('--ffmpeg');args=parser.parse_args()
    video=args.video.resolve();ffmpeg=find_ffmpeg(args.ffmpeg);film=Film();composer=VideoComposer(film)
    target=video.parent/'video-qa';target.mkdir(exist_ok=True)
    cap=cv2.VideoCapture(str(video));assert cap.isOpened()
    width=round(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps=cap.get(cv2.CAP_PROP_FPS);count=round(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    assert (width,height)==(1920,1080) and abs(fps-30)<.001 and count==math.floor(film.duration*30+.5)
    frame_report=[];pictures=[]
    for t in [10.,34.,86.,103.,116.78,120.70,135.2,152.,168.6,181.,193.]:
        index=round(t*fps);actual_t=index/fps
        cap.set(cv2.CAP_PROP_POS_FRAMES,index);ok,raw=cap.read();assert ok
        actual=cv2.cvtColor(raw,cv2.COLOR_BGR2RGB);expected=composer.frame(actual_t)
        error=float(np.abs(actual.astype(np.int16)-expected).mean())
        assert error<8,(actual_t,error)
        im=Image.fromarray(actual);im.save(target/f'decoded-{actual_t:07.3f}.png')
        pictures.append((actual_t,im))
        frame_report.append({'source_second':round(actual_t,6),'frame':index,'mean_RGB_error':round(error,3)})
    cap.release();print('11个成片切点已比对当前字符源帧。',flush=True)
    decode=subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,timeout=180)
    assert decode.returncode==0 and not decode.stderr.decode('utf-8','replace').strip(),decode.stderr.decode('utf-8','replace')
    print('完整视频与音轨解码通过。',flush=True)
    audio=subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-i',str(video),'-map','0:a:0','-ac','1','-ar','48000','-f','f32le','pipe:1'],capture_output=True,check=True,timeout=60)
    rendered=np.frombuffer(audio.stdout,dtype=np.float32)
    with wave.open(str(ROOT/'assets/amara.wav'),'rb') as wav:
        rate=wav.getframerate();channels=wav.getnchannels()
        original=np.frombuffer(wav.readframes(wav.getnframes()),dtype=np.int16).reshape(-1,channels).astype(np.float32).mean(axis=1)/32768
    assert abs(len(rendered)/rate-film.duration)<1/fps+.001
    audio_report=[];pad=round(rate*.04);length=round(rate*.20)
    for t in [5.,34.,63.6,103.,113.,120.7,133.114,170.432,190.]:
        offset=round(t*rate)
        template=np.ascontiguousarray(original[offset:offset+length].reshape(1,-1))
        search=np.ascontiguousarray(rendered[offset-pad:offset+length+pad].reshape(1,-1))
        corr=cv2.matchTemplate(search,template,cv2.TM_CCORR_NORMED)
        best=int(np.argmax(corr));shift=(best-pad)/rate*1000;score=float(corr.flat[best])
        assert abs(shift)<=2 and score>.97,(t,shift,score)
        audio_report.append({'source_second':t,'offset_ms':round(shift,4),'correlation':round(score,6)})
    print('9段音频相关比对通过，同步误差不超过2毫秒。',flush=True)
    metadata=subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-i',str(video),'-f','ffmetadata','pipe:1'],capture_output=True,check=True)
    text=metadata.stdout.decode('utf-8');chapters=text.count('[CHAPTER]');assert chapters==65
    report={'video':video.name,'resolution':[width,height],'fps':fps,'video_frames':count,'video_duration':count/fps,
            'song_duration':film.duration,'decoded_audio_duration':len(rendered)/rate,'chapters':chapters,
            'full_audio_and_video_decode_passed':True,'frame_comparisons':frame_report,'audio_alignment':audio_report,
            'max_audio_alignment_error_ms':max(abs(x['offset_ms']) for x in audio_report),
            'file_sha256':digest(video),'result':'passed'}
    video.with_suffix('.verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    font=ImageFont.truetype(str(CJK_PATH),20);sheet=Image.new('RGB',(1320,285*math.ceil(len(pictures)/2)),(7,11,20));draw=ImageDraw.Draw(sheet)
    for i,(t,im) in enumerate(pictures):
        x=i%2*660;y=i//2*285;draw.text((x+8,y+3),f'{t:.3f}s · 成片解码',font=font,fill='white')
        sheet.paste(im.resize((640,240),Image.Resampling.LANCZOS),(x+10,y+33))
    sheet.save(target/'contact-sheet.png')
    print(json.dumps({k:v for k,v in report.items() if k not in ['frame_comparisons','audio_alignment']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
