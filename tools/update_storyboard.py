"""Regenerate the scene table without overwriting the repository README."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from amara import Film

def stamp(t):return f'{int(t)//60:02}:{t%60:06.3f}'

def main():
    film=Film()
    title='ÅMARA V2：无法理解的输入，已经开始执行'
    intro='文明试图把未知文字识别、解释并执行，世界因此生成，也因此失控。语言被剥离，姓名被删除，现实判定逐次失败；献花进入了这个系统，却不能修复它。最后的再生失步，天国倒置，未知字符获得整屏权限，所有可见层崩溃，终局明确显示严重系统错误。'
    lines=['# '+title,'',intro,'',f'{len(film.subtitles)}条同步中英字幕、{len(film.director.shots)}个分镜。重复歌词采用不同构图与动作结果。','',
           '| 起止时间 | 中译歌词 / 段落 | 明确语义动作 |','|---|---|---|']
    for q in film.director.shots:
        lyric=film.subtitles[q['cue']]['zh'] if q['cue'] is not None else '间奏 / 尾奏'
        lines.append(f"| {stamp(q['start'])}–{stamp(q['end'])} | {lyric} | {q['action']} |")
    (ROOT/'storyboard-v2.md').write_text('\n'.join(lines)+'\n','utf-8')
    payload={'version':2,'revision':'physical-fracture-inscription-revision4','title':title,'premise':intro,'shots':film.director.shots}
    (ROOT/'storyboard-v2.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),'utf-8')
    print('已更新分镜表，保留README。')

if __name__=='__main__':main()
