"""Build the current V2 as an offline, self-contained Windows x64 release."""
from __future__ import annotations
import hashlib
from datetime import datetime
from importlib.metadata import distribution
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            result.update(block)
    return result.hexdigest()


def build():
    if sys.platform!='win32' or sys.maxsize<=2**32:
        raise RuntimeError('此构建脚本需要 64 位 Windows Python。')
    from prepare_assets import prepare_assets
    from amara import Film
    wav,analysis_path=prepare_assets()
    film=Film()
    built_at=datetime.now().astimezone().isoformat(timespec='seconds')
    source_hashes={name:digest(ROOT/name) for name in
                   ['amara.py','cinema.py','revised_scenes.py','kinetic_scenes.py','audio.py','bundle_runtime.py','prepare_assets.py']}
    work=ROOT/'work/release_build'
    work.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='v2-',dir=work)).resolve()
    assert stage.is_relative_to(work.resolve())
    data=stage/'resources'
    (data/'assets').mkdir(parents=True)
    shutil.copy2(wav,data/'assets/amara.wav')
    analysis=json.loads(analysis_path.read_text('utf-8'))
    analysis['meta']={k:v for k,v in analysis['meta'].items()
                      if k not in {'source_path','source_size','source_mtime_ns'}}
    (data/'assets/analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,separators=(',',':'))+'\n','utf-8')
    shutil.copy2(ROOT/'subtitles.json',data/'subtitles.json')
    shutil.copy2(next(ROOT.glob('*.lrc')),data/'lyrics.lrc')
    names=['assets/amara.wav','assets/analysis.json','subtitles.json','lyrics.lrc']
    manifest={'bundle_version':1,'application':'AMARA','edition':'V2',
              'revision':'physical-fracture-inscription-revision4','built_at':built_at,
              'source_sha256':source_hashes,
              'duration':film.duration,'lyrics_count':len(film.subtitles),
              'shot_count':len(film.director.shots),
              'files':{name:{'size':(data/name).stat().st_size,'sha256':digest(data/name)} for name in names}}
    (data/'bundle_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    from bundle_runtime import verify_packaged_assets
    verify_packaged_assets(data)

    command=[sys.executable,'-m','PyInstaller','--onefile','--console','--noconfirm',
             '--name','AMARA-V2','--distpath',str(stage/'binary'),
             '--workpath',str(stage/'build'),'--specpath',str(stage/'spec'),
             '--paths',str(ROOT)]
    for name in names+['bundle_manifest.json']:
        target=str(Path(name).parent)
        command.extend(['--add-data',str(data/name)+':'+target])
    # FLAC analysis and picture-generation libraries are not playback dependencies.
    for module in ['numpy','soundfile','PIL','scipy','cv2','matplotlib','pytest','tkinter']:
        command.extend(['--exclude-module',module])
    command.append(str(ROOT/'amara.py'))
    log=stage/'build.log'
    print('正在构建 Windows 独立播放器……',flush=True)
    with log.open('w',encoding='utf-8') as output:
        result=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('独立播放器构建失败，日志：'+str(log))

    output=ROOT/'dist'
    package=output/'AMARA-V2'
    package.mkdir(parents=True,exist_ok=True)
    exe=stage/'binary/AMARA-V2.exe'
    shutil.copy2(exe,output/'AMARA-V2.exe')
    shutil.copy2(exe,package/'AMARA-V2.exe')
    launcher='\r\n'.join([
        '@echo off','setlocal','cd /d "%~dp0"','chcp 65001 >nul',
        'title AMARA V2 - ASCII Music Film','"%~dp0AMARA-V2.exe" %*',
        'set "AMARA_EXIT=%errorlevel%"','if not "%AMARA_EXIT%"=="0" pause',
        'exit /b %AMARA_EXIT%',''])
    (package/'播放MV.cmd').write_bytes(launcher.encode('ascii'))
    instructions=f'''ÅMARA V2 · 终端字符动画 MV · 最新修订版
构建时间：{built_at}

使用方法
1. 将整个 ZIP 解压到任意本地文件夹。
2. 双击“播放MV.cmd”或“AMARA-V2.exe”。
3. 将终端窗口最大化；约 160 列 × 47 行或更大效果更好。

支持 Windows 10 / 11 的 64 位系统。无需安装 Python，无需联网。
播放器内部包含音乐、{len(film.subtitles)} 段中英字幕、{len(film.director.shots)} 个分镜与音乐分析数据。
单独转发 AMARA-V2.exe 也可播放；ZIP 同时附有说明和预览。

本次更新
34–45 秒：苍白旷野、人影与原 MV 补充歌词。
1:52.218 直接进入混沌，从 1:53 起由慢到快压缩，1:56.780 收成丝线。
丝线保持到 2:00.700，随后中央英文巨字 RECONNECT 闪烁。
周围的断线、双向数据包、重试、握手与时钟同步动态变化，2:01.821 接入下一句歌词。
同步字幕包含原 LRC 的 54 条及依据用户提供的原 MV 补入的 1 条。
本版还重做了无缝羁绊、脊骨神经体间奏、三种未知未来、机械与全息献花、电子梦毒回廊，以及神经圣堂中的未知铭文。
另有22处实体动作修订：再生庆典的机械人形、光冠、祭坛先后破碎；识读段改为石刻扫描、翻页、译码链断裂与文明压毁。语言剥离、现实切片、天国倒扣与尾奏坐标解体也有各自的空间变化。

操作
Space：暂停 / 恢复
左箭头 / A：后退 5 秒
右箭头 / D：前进 5 秒
R：从头开始
Q / Esc / Ctrl+C：退出

作品
全长 3 分 15.507 秒，默认 30 fps，同步中英歌词与信号。
V2 立意：文明执行了无法理解的输入，语言、记忆、现实判定和再生逐步失控，最后发生严重系统错误。
剧情中的 SYSTEM ERROR 是 MV 的终局画面。

词曲：sasakure.UK
演唱：KAITO / 初音ミク
音乐与原歌词保留原作者权利；ASCII 视觉与中英翻译为本项目制作。

高级用法（在终端中运行）
AMARA-V2.exe --start 112.218
AMARA-V2.exe --start 120.5
AMARA-V2.exe --start 173.218
AMARA-V2.exe --mute
AMARA-V2.exe --subtitle-offset 0.15
AMARA-V2.exe --check
AMARA-V2.exe --snapshot 175.5 --output unknown.txt
'''
    (package/'使用说明.txt').write_text(instructions,encoding='utf-8-sig')
    if (ROOT/'previews/v2/cover.png').is_file():
        shutil.copy2(ROOT/'previews/v2/cover.png',package/'预览.png')
    for source,name in [
        ('previews/segment_34_45/frame-40.0.png','旷野预览.png'),
        ('previews/reconnect_english/frame-121.700.png','重连预览.png'),
        ('previews/reconnect_english/preview.gif','重连预览.gif'),
        ('previews/scenes_revision_3/contact-sheet.png','重做场景总览.png'),
        ('previews/scenes_revision_4/contact-sheet.png','实体动作重做总览.png'),
        ('previews/scenes_revision_4/festival_rupture.gif','再生庆典支离破碎.gif'),
    ]:
        shutil.copy2(ROOT/source,package/name)
    licenses=package/'运行组件声明'
    licenses.mkdir(exist_ok=True)
    shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',licenses/'Python-LICENSE.txt')
    pyi=distribution('pyinstaller')
    copying=next(pyi.locate_file(f) for f in pyi.files if str(f).endswith('licenses/COPYING.txt'))
    shutil.copy2(copying,licenses/'PyInstaller-COPYING.txt')
    (licenses/'说明.txt').write_text('本包包含 Python 运行时与 PyInstaller 引导程序。\n对应的原始许可证与组件声明随包保留。\n',encoding='utf-8-sig')
    entries=sorted(p for p in package.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
    (package/'SHA256SUMS.txt').write_text('\n'.join(digest(p)+'  '+p.relative_to(package).as_posix() for p in entries)+'\n','utf-8')
    archive=output/'AMARA-V2-Windows-x64.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as packed:
        for p in sorted(package.rglob('*')):
            if p.is_file():packed.write(p,Path('AMARA-V2')/p.relative_to(package))
    (output/'SHA256SUMS.txt').write_text(digest(archive)+'  '+archive.name+'\n'+digest(output/'AMARA-V2.exe')+'  AMARA-V2.exe\n','utf-8')
    report={'edition':'V2','platform':'Windows x64','exe':str(output/'AMARA-V2.exe'),
            'revision':manifest['revision'],'built_at':built_at,
            'source_sha256':source_hashes,'lyrics_count':len(film.subtitles),
            'shot_count':len(film.director.shots),
            'zip':str(archive),'exe_bytes':exe.stat().st_size,'zip_bytes':archive.stat().st_size,
            'sha256_zip':digest(archive),'build_log':str(log),
            'embedded_music':True,'external_python_required':False}
    (output/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    for stream in [sys.stdout,sys.stderr]:
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8',errors='replace')
    build()
