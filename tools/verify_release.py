"""Exercise the shipped EXE after extracting outside the project directory."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def verify():
    output=ROOT/'dist'
    archive=output/'AMARA-V2-Windows-x64.zip'
    temp_parent=Path(tempfile.gettempdir()).resolve()
    isolated=Path(tempfile.mkdtemp(prefix='AMARA 独立测试 ',dir=temp_parent)).resolve()
    assert isolated.is_relative_to(temp_parent) and isolated.name.startswith('AMARA 独立测试 ')
    checks=[]
    from amara import Film
    source_film=Film()
    build_report=json.loads((output/'build-report.json').read_text('utf-8'))
    for name,expected in build_report['source_sha256'].items():
        assert sha(ROOT/name)==expected,'源码在打包后发生变化：'+name
    assert sha(archive)==build_report['sha256_zip']
    with zipfile.ZipFile(archive) as packaged:
        assert packaged.testzip() is None
        for name in packaged.namelist():
            assert (isolated/name).resolve().is_relative_to(isolated)
        packaged.extractall(isolated)
    folder=isolated/'AMARA-V2'
    for line in (folder/'SHA256SUMS.txt').read_text('utf-8').splitlines():
        expected,name=line.split('  ',1)
        assert sha(folder/name)==expected,name
    assert not list(folder.rglob('*.flac')) and not list(folder.rglob('*.py'))
    assert not (folder/'assets').exists()
    env=os.environ.copy()
    env.pop('PYTHONPATH',None)
    env.pop('PYTHONHOME',None)
    windows_root=Path(os.environ.get('SystemRoot','C:/Windows'))
    env['PATH']=str(windows_root/'System32')
    extraction=isolated/'临时缓存'
    extraction.mkdir()
    env['TEMP']=env['TMP']=str(extraction)
    exe=folder/'AMARA-V2.exe'

    def run(label,args,command=None):
        process=subprocess.run((command or [str(exe)])+args,cwd=folder,env=env,
                               capture_output=True,timeout=60,
                               creationflags=subprocess.CREATE_NO_WINDOW)
        stdout=process.stdout.decode('utf-8',errors='replace')
        stderr=process.stderr.decode('utf-8',errors='replace')
        if process.returncode:
            raise RuntimeError(label+' 失败：'+stdout+'\n'+stderr+'\n测试目录：'+str(isolated))
        checks.append({'name':label,'passed':True,'returncode':process.returncode})
        print(label+'：通过',flush=True)
        return stdout

    status=run('脱离原目录的素材与全片结构检查',['--check'])
    parsed=json.loads(status)
    assert parsed['镜头数']==len(source_film.director.shots)
    assert parsed['字幕条数']==len(source_film.subtitles)
    assert parsed['原始LRC条数']==54 and parsed['MV补充条数']==1
    assert parsed['独立歌词动作']==parsed['字幕条数']
    run('独立文件导出实际动画画面',['--snapshot','175.5','--output','smoke-frame.txt'])
    text=(folder/'smoke-frame.txt').read_text('utf-8')
    assert len(text.splitlines())==46 and '02:55.50' in text
    # Compare actual frozen output with the current source at every revised
    # cut, not just with a generic scene or the reported version number.
    revised_samples=[(34.0,'旷野与MV补充字幕'),(40.0,'旷野人影'),
                     (44.5,'白场隐去'),(112.218,'直接进入混沌'),
                     (116.6,'加速压缩'),(116.78,'丝线到位'),
                     (120.699,'丝线保持至切点'),(120.70,'英文重连开始'),
                     (121.30,'RECONNECT与握手装饰'),(121.821,'下一句歌词接入'),
                     (193.0,'严重系统错误终局'),
                     (63.6,'无缝导体的震颤回应'),(86.0,'脊骨神经体间奏'),
                     (94.3,'未来窗格熄灭'),(97.7,'预测纸带擦除'),
                     (101.1,'观测光阑封闭'),(126.6,'机械电路献花'),
                     (132.0,'青绿电子梦毒'),(151.5,'神经圣堂与未知铭文'),
                     (160.0,'全息献花传输'),(165.3,'斜切紫红梦毒回廊'),
                     (25.9,'语言膜卷曲剥离'),(31.5,'镜片切开'),
                     (49.8,'虚构地图折叠'),(53.9,'压印卡顿'),
                     (76.4,'织线撕裂回弹'),(92.7,'立体城市断面'),
                     (96.1,'铭文漏斗'),(99.5,'房间交换前后'),
                     (102.9,'石刻逃出扫描框'),(104.3,'城市接入光学译码'),
                     (105.7,'实体识别链断裂'),(107.5,'记录页翻开'),
                     (109.3,'机械压床碾毁文明'),(111.0,'递归光阑炸裂'),
                     (134.0,'完整再生光冠'),(135.2,'多轴碎裂庆典'),
                     (138.0,'夜沿穹顶蔓延'),(141.8,'文字地层开掘'),
                     (146.7,'互斥解释相撞'),(168.6,'重建桥与圣堂内塌'),
                     (172.0,'穹顶倒扣'),(181.0,'三维坐标网解体')]
    for t,label in revised_samples:
        snapshot=f'revision-{t:.3f}.txt'
        run('最新修订画面：'+label,['--snapshot',str(t),'--output',snapshot])
        assert (folder/snapshot).read_text('utf-8')==source_film.frame(t,160,46).plain()+'\n',label
    run('独立播放器静音短播放',['--mute','--headless','--start','190','--duration','0.15'])
    run('独立播放器原生音频短播放',['--headless','--start','120.6','--duration','0.45'])
    cmd=str(windows_root/'System32/cmd.exe')
    run('中文启动器与带空格目录',['--mute','--headless','--duration','0.15'],[cmd,'/c','播放MV.cmd'])
    assert not list(extraction.glob('_MEI*')),'播放器退出后尚有内嵌资源缓存'
    report={'edition':'V2','checks':checks,'zip_integrity':True,
            'revision':build_report['revision'],'built_at':build_report['built_at'],
            'latest_revision_frames_match_source':len(revised_samples),
            'lyrics_count':parsed['字幕条数'],'shot_count':parsed['镜头数'],
            'file_hashes_verified':True,'isolated_from_workspace':True,
            'python_removed_from_path':True,'external_music_required':False,
            'embedded_resources_cleaned_on_exit':True,
            'zip_bytes':archive.stat().st_size,'sha256_zip':sha(archive)}
    (output/'verification-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    # Delete only this freshly created, verified temporary test directory.
    assert isolated.resolve().is_relative_to(temp_parent) and isolated.name.startswith('AMARA 独立测试 ')
    shutil.rmtree(isolated)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    import sys
    for stream in [sys.stdout,sys.stderr]:
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8',errors='replace')
    verify()
