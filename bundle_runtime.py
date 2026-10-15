"""Validate embedded release resources without any source-directory dependency."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


def verify_packaged_assets(root: Path):
    root=root.resolve()
    try:
        manifest=json.loads((root/'bundle_manifest.json').read_text('utf-8'))
        required={'assets/amara.wav','assets/analysis.json','subtitles.json','lyrics.lrc'}
        if manifest.get('bundle_version')!=1 or set(manifest['files'])!=required:
            raise ValueError('资源清单不完整')
        for name,entry in manifest['files'].items():
            path=(root/name).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError('内嵌资源缺失')
            if path.stat().st_size!=entry['size']:
                raise ValueError('内嵌资源长度错误')
            digest=hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):
                    digest.update(block)
            if digest.hexdigest()!=entry['sha256']:
                raise ValueError('内嵌资源校验失败')
        analysis=json.loads((root/'assets/analysis.json').read_text('utf-8'))
        from prepare_assets import _cache_errors,ASSET_VERSION
        errors=_cache_errors(analysis,root/'assets/amara.wav',{'version':ASSET_VERSION})
        if errors:
            raise ValueError('; '.join(errors))
        cues=json.loads((root/'subtitles.json').read_text('utf-8'))['cues']
        if len(cues)!=manifest['lyrics_count']:
            raise ValueError('字幕资源不完整')
    except (OSError,ValueError,TypeError,KeyError) as exc:
        raise RuntimeError('播放包资源缺失或损坏，请重新解压完整播放包。') from exc
    return root/'assets/amara.wav',root/'assets/analysis.json'
